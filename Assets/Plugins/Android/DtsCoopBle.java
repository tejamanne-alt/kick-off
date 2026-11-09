// Bluetooth LE for the co-op mode (called from Coop/Transport/AndroidBleLink.cs; the iOS twin is
// Plugins/iOS/DTSCoopBLE.mm, and both speak the same packed events, docs/COOP.md "Native bridge").
//
// The host is a GATT server that advertises the game's service (its lobby's beacon in the scan response); each other
// player scans for it, connects as a GATT client, subscribes to the host's "to client" characteristic and writes to its
// "to host" one. Android allows one GATT operation in flight at a time, so packets wait in a queue per phone: the host
// serves its players' queues in turn, one notification in flight across the whole server; a player writes to the host one
// packet at a time. A queue that grows too long (a phone that has stopped listening) drops its oldest whole messages,
// never part of one. Everything runs on one handler thread; the game polls the events once a frame.
//
// Each hosting run and each connection attempt carries the number (generation) the game gave it, written into the state
// byte of every event about it, so the game can drop what arrives after it has moved on (Coop/Net/LinkEventFilter.cs).
// Nothing here may throw into the game: the calls from C# only post work to the handler thread, and every piece of work
// there catches what the Bluetooth stack throws (a permission taken away, the stack's process gone, a stack's own bug)
// and logs it.
package com.dribbletoschool.coop;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattServer;
import android.bluetooth.BluetoothGattServerCallback;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothManager;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.BluetoothStatusCodes;
import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseData;
import android.bluetooth.le.AdvertiseSettings;
import android.bluetooth.le.AdvertisingSet;
import android.bluetooth.le.AdvertisingSetCallback;
import android.bluetooth.le.AdvertisingSetParameters;
import android.bluetooth.le.BluetoothLeAdvertiser;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanFilter;
import android.bluetooth.le.ScanRecord;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.ParcelUuid;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@SuppressLint("MissingPermission")   // every call is made only once the game has the permissions (radioState says Unauthorized otherwise)
public final class DtsCoopBle
{
    static final String TAG = "DtsCoopBle";

    static final UUID SERVICE = UUID.fromString("8C5F0001-2B7E-4D5A-9E3B-4B4F32C0FFEE");
    static final UUID TO_CLIENT = UUID.fromString("8C5F0002-2B7E-4D5A-9E3B-4B4F32C0FFEE");
    static final UUID TO_HOST = UUID.fromString("8C5F0003-2B7E-4D5A-9E3B-4B4F32C0FFEE");
    static final UUID CCCD = UUID.fromString("00002902-0000-1000-8000-00805F9B34FB");
    /** The 16-bit key ("KO") the lobby's beacon goes under in the scan response, as a full UUID. */
    static final ParcelUuid BEACON_KEY = ParcelUuid.fromString("00004B4F-0000-1000-8000-00805F9B34FB");

    static final int EV_RADIO = 1, EV_FOUND = 2, EV_CONNECTED = 3, EV_DISCONNECTED = 4, EV_DATA = 5,
        EV_HOST_STARTED = 6, EV_HOST_FAILED = 7, EV_CONNECT_FAILED = 8, EV_PACKET_SIZE = 9;
    static final int RADIO_UNKNOWN = 0, RADIO_UNSUPPORTED = 1, RADIO_UNAUTHORIZED = 2, RADIO_OFF = 3, RADIO_ON = 4;
    /** The framing's packet header (Coop/Net/CoopFraming.cs): bit 7 on a message's last packet, bit 6 on its first. */
    static final int LAST_FLAG = 0x80, FIRST_FLAG = 0x40;
    /** How many packets may wait for one phone before the oldest whole messages are dropped (the session repeats them). */
    static final int QUEUE_LIMIT = 96;
    /** How many events may wait for the game's poll (it polls every frame; this is for a game paused in the background). */
    static final int EVENT_LIMIT = 4096;
    /** Android quietly blocks an app's sixth scan start within 30 s: this many starts at most in any 30 s. */
    static final int SCAN_STARTS = 4;
    static final long SCAN_WINDOW = 30000, SCAN_STOP_DELAY = 1000, SCAN_RETRY = 2000;
    static final long HOST_START_TIMEOUT = 6000, CONNECT_TIMEOUT = 10000;
    static final long ADVERTISE_RETRY_MIN = 1000, ADVERTISE_RETRY_MAX = 8000;
    /** No word that a notification or write went within this long: carry on as if it had. */
    static final long SEND_WATCHDOG = 1000;
    /** The stack said it was busy: try again after this long. */
    static final long BUSY_RETRY = 50;
    static final long DISCOVER_WATCHDOG = 1500;
    static final int SEEN_LIMIT = 256;
    static final byte[] EMPTY = new byte[0];

    static DtsCoopBle instance;

    final Context context;
    final Handler handler;
    final ArrayDeque<byte[]> events = new ArrayDeque<>();   // (guarded by itself: poll comes from the game's thread)
    volatile int radio = RADIO_UNKNOWN;
    volatile int maxPacket = 20;
    volatile boolean locationOff;
    volatile long locationCheckedAt = -1;

    BluetoothManager manager;
    BluetoothAdapter adapter;
    boolean receiverRegistered;

    // Host
    boolean hostWanted, hostAnnounced, hostTimeoutArmed, serviceAdded;
    int hostGen;
    byte[] beacon = EMPTY;
    BluetoothGattServer server;
    ServerCallback serverCb;
    BluetoothGattCharacteristic toClient;
    /** The players, by peer number; in the order they came, which is also the order of their numbers (never reused). */
    final LinkedHashMap<Integer, Central> centrals = new LinkedHashMap<>();
    final Map<String, Central> byAddress = new HashMap<>();
    final Set<String> kicked = new HashSet<>();
    /** MTUs agreed with phones that have no peer number yet (connected, not yet subscribed). */
    final Map<String, Integer> pendingMtu = new HashMap<>();
    int nextPeer = 1;
    boolean notifyInFlight, hostPumpWaiting;
    String inFlightAddress;
    int lastServed;

    // Advertising
    boolean useSets = true, advertising, beaconDirty, responsePending;
    Object advertCallback;   // the SetCallback or LegacyCallback of the advertisement started (or starting); null when none
    AdvertisingSet advertSet;
    long advertiseRetry = ADVERTISE_RETRY_MIN, responseSentAt, legacyStartedAt;

    // Scanning
    boolean scanWanted, scanning;
    BluetoothLeScanner scanner;
    final ArrayDeque<Long> scanStarts = new ArrayDeque<>();
    final Map<String, Seen> seen = new HashMap<>();

    // The client role
    BluetoothGatt gatt;
    ClientCallback gattCb;
    int clientGen;
    BluetoothGattCharacteristic hostWrite;
    BluetoothGattDescriptor cccd;   // (while subscribing)
    boolean linkUp, awaitingMtu, discovering, hostReady, writing, clientPumpWaiting;
    int discoverTries, subscribeTries;
    int hostMtu = 23;
    final OutQueue clientQueue = new OutQueue();

    // The reusable tasks (each made once, so a later posting replaces an earlier one rather than piling up).
    final Runnable refreshTask = guard(this::refreshRadio);
    final Runnable hostTimeoutTask = guard(this::hostTimedOut);
    final Runnable hostRetryTask = guard(this::retryHost);
    final Runnable readvertiseTask = guard(this::readvertise);
    final Runnable hostPumpTask = guard(this::hostPumpTick);
    final Runnable notifyWatchdog = guard(this::notifyTimedOut);
    final Runnable scanStartTask = guard(this::beginScan);
    final Runnable scanStopTask = guard(this::scanStopTick);
    final Runnable connectTimeoutTask = guard(this::connectTimedOut);
    final Runnable clientStepTask = guard(this::clientStep);
    final Runnable subscribeTask = guard(this::writeCccd);
    final Runnable clientPumpTask = guard(this::clientPumpTick);
    final Runnable writeWatchdog = guard(this::writeTimedOut);

    // ---------- What C# calls (from the game's thread: each only posts its work to the handler thread, and none throws) ----------

    public static synchronized DtsCoopBle init(Activity activity)
    {
        try
        {
            if (instance == null) instance = new DtsCoopBle(activity.getApplicationContext());
            instance.post(instance::start);
        }
        catch (Throwable t) { Log.w(TAG, "init", t); }
        return instance;
    }

    DtsCoopBle(Context context)
    {
        this.context = context;
        HandlerThread thread = new HandlerThread("dts-coop-ble");
        thread.start();
        handler = new Handler(thread.getLooper());
    }

    /** gen: the game's number for this hosting run (its events carry gen & 0xFF in the state byte). */
    public void startHost(final byte[] beaconBytes, final int gen) { post(() -> beginRun(beaconBytes, gen)); }
    public void updateBeacon(final byte[] beaconBytes) { post(() -> setBeacon(beaconBytes)); }
    public void stopHost() { post(this::endHost); }
    public void kick(final int peer) { post(() -> kickPeer(peer)); }
    public void startScan() { post(this::wantScan); }
    public void stopScan() { post(this::unwantScan); }
    /** gen: the game's number for this connection attempt (its events carry gen & 0xFF in the state byte). */
    public void connect(final String address, final int gen) { post(() -> connectTo(address, gen)); }
    public void disconnect() { post(this::dropHost); }
    public void send(final int peer, final byte[] data) { if (data != null && data.length > 0) post(() -> sendNow(peer, data)); }
    public int radioState() { return radio; }
    public int maxPacket() { return maxPacket; }
    public void shutdown() { post(this::stopAll); }

    /** Every packed event since the last call, back to back (docs/COOP.md "Native bridge"); null when there are none. */
    public byte[] poll()
    {
        try
        {
            synchronized (events)
            {
                if (events.isEmpty()) return null;
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                int used = 0;
                while (!events.isEmpty())
                {
                    byte[] e = events.peekFirst();
                    if (used + e.length > 65536 && used > 0) break;   // (the rest next frame)
                    out.write(e, 0, e.length);
                    used += e.length;
                    events.pollFirst();
                }
                return out.toByteArray();
            }
        }
        catch (Throwable t)
        {
            Log.w(TAG, "poll", t);
            return null;
        }
    }

    /** The permissions the game must hold to use Bluetooth on this Android version. */
    public static String[] neededPermissions()
    {
        if (Build.VERSION.SDK_INT >= 31)
            return new String[] { Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_ADVERTISE };
        return new String[] { Manifest.permission.ACCESS_FINE_LOCATION };
    }

    /**
     * Below Android 12, scanning finds nothing while Location is off: the Join screen says so. The game asks every frame,
     * so the answer is kept for a second.
     */
    public boolean locationNeededAndOff()
    {
        try
        {
            if (Build.VERSION.SDK_INT >= 31) return false;
            long now = SystemClock.elapsedRealtime();
            long at = locationCheckedAt;
            if (at >= 0 && now - at < 1000) return locationOff;
            LocationManager lm = (LocationManager)context.getSystemService(Context.LOCATION_SERVICE);
            boolean off = false;
            if (lm != null)
            {
                if (Build.VERSION.SDK_INT >= 28) off = !lm.isLocationEnabled();
                else off = !lm.isProviderEnabled(LocationManager.GPS_PROVIDER) && !lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER);
            }
            locationOff = off;
            locationCheckedAt = now;
            return off;
        }
        catch (Throwable t)
        {
            return false;
        }
    }

    public void openSettings(Activity activity)
    {
        try
        {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", activity.getPackageName(), null));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(intent);
        }
        catch (Throwable ignored) { }
    }

    public void openBluetoothSettings(Activity activity)
    {
        try
        {
            Intent intent = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(intent);
        }
        catch (Throwable ignored) { }
    }

    // ---------- The handler thread ----------

    /** Runs r on the handler thread (see guard). */
    void post(Runnable r)
    {
        try { handler.post(guard(r)); }
        catch (Throwable t) { Log.w(TAG, "post", t); }
    }

    /**
     * r, catching whatever it throws: a SecurityException when a permission was taken away, a DeadObjectException (inside
     * a RuntimeException) when Bluetooth's process went, a stack's own NullPointerException. Thrown out of a handler
     * thread, any of them would take the game down.
     */
    Runnable guard(final Runnable r)
    {
        return () ->
        {
            try { r.run(); }
            catch (Throwable t) { trouble("task", t); }
        };
    }

    /** Posts one of the reusable tasks (made with guard) to run after ms, in place of any earlier posting of it. */
    void later(Runnable task, long ms)
    {
        handler.removeCallbacks(task);
        handler.postDelayed(task, Math.max(0, ms));
    }

    void trouble(String what, Throwable t)
    {
        try
        {
            Log.w(TAG, what, t);
            if (t instanceof SecurityException) later(refreshTask, 500);   // (a permission was taken away: the radio state will say so)
        }
        catch (Throwable ignored) { }
    }

    // ---------- Events ----------

    void emit(int type, int peer, int state, int rssi, String address, byte[] data, String name)
    {
        byte[] a = (address != null ? address : "").getBytes(StandardCharsets.UTF_8);
        byte[] d = data != null ? data : EMPTY;
        byte[] n = (name != null ? name : "").getBytes(StandardCharsets.UTF_8);
        ByteArrayOutputStream e = new ByteArrayOutputStream(16 + a.length + d.length + n.length);
        // (little-endian, as Coop/Net/CoopWire.cs's ByteReader reads)
        e.write(type);
        e.write(peer & 0xFF); e.write((peer >> 8) & 0xFF); e.write((peer >> 16) & 0xFF); e.write((peer >> 24) & 0xFF);
        e.write(state & 0xFF);
        e.write(rssi & 0xFF); e.write((rssi >> 8) & 0xFF);
        putBlock(e, a);
        putBlock(e, d);
        putBlock(e, n);
        queue(e.toByteArray());
    }

    static void putBlock(ByteArrayOutputStream e, byte[] b)
    {
        int len = Math.min(b.length, 0xFFFF);
        e.write(len & 0xFF); e.write((len >> 8) & 0xFF);
        e.write(b, 0, len);
    }

    /** An event of a hosting run (peer 0 for the run itself, else a player's). */
    void hostEvent(int type, int peer, String error) { emit(type, peer, hostGen, 0, null, null, error); }

    /** An event of the connection to the host. */
    void clientEvent(int type, String address, String error) { emit(type, 0, clientGen, 0, address, null, error); }

    /**
     * Keeps an event for the game's next poll. A game that hasn't polled for a long while (paused in the background) finds
     * the queue stopped at EVENT_LIMIT: scan reports go first (another comes along), then packets (the session repeats what
     * matters); what says the radio, a connection or a hosting run changed is always kept (they are few, and each counts).
     */
    void queue(byte[] e)
    {
        synchronized (events)
        {
            if (events.size() >= EVENT_LIMIT && !makeRoom(e[0])) return;
            events.addLast(e);
        }
    }

    /** (holding events) Whether an event of this type may be added to a full queue, dropping a less useful one if need be. */
    boolean makeRoom(int type)
    {
        if (removeOldest(EV_FOUND)) return true;
        if (type == EV_FOUND) return false;
        if (removeOldest(EV_DATA)) return true;
        return type != EV_DATA;   // (only the kinds always kept are waiting: this one is kept too, past the limit)
    }

    boolean removeOldest(int type)
    {
        for (Iterator<byte[]> it = events.iterator(); it.hasNext(); )
        {
            if (it.next()[0] != type) continue;
            it.remove();
            return true;
        }
        return false;
    }

    // ---------- The radio ----------

    /** A new link (the game started its co-op side): whatever the last one left running ends, and the radio is announced. */
    void start()
    {
        endHost();
        scanWanted = false;
        endScan();
        dropHost();
        synchronized (events) { events.clear(); }
        if (manager == null)
        {
            manager = (BluetoothManager)context.getSystemService(Context.BLUETOOTH_SERVICE);
            adapter = manager != null ? manager.getAdapter() : null;
        }
        listenForRadio();
        // (the new link starts from Unknown, and Radio events come only on a change)
        if (radio != RADIO_UNKNOWN) emit(EV_RADIO, 0, radio, 0, null, null, null);
        refreshRadio();
        // Permissions may have been granted since the last look: check again in a moment.
        later(refreshTask, 1500);
    }

    void listenForRadio()
    {
        if (receiverRegistered) return;
        IntentFilter filter = new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED);
        BroadcastReceiver receiver = new BroadcastReceiver()
        {
            // (delivered on the handler thread: registered with it below)
            @Override public void onReceive(Context c, Intent intent)
            {
                try { later(refreshTask, 0); }
                catch (Throwable ignored) { }
            }
        };
        try
        {
            // Not exported: the system's broadcast still arrives, other apps' can't.
            if (Build.VERSION.SDK_INT >= 33) context.registerReceiver(receiver, filter, null, handler, Context.RECEIVER_NOT_EXPORTED);
            else context.registerReceiver(receiver, filter, null, handler);
            receiverRegistered = true;
        }
        catch (Throwable t) { trouble("registerReceiver", t); }
    }

    boolean hasPermissions()
    {
        for (String p : neededPermissions())
            if (context.checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) return false;
        return true;
    }

    void refreshRadio()
    {
        handler.removeCallbacks(refreshTask);
        int r;
        try
        {
            if (adapter == null || !context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE)) r = RADIO_UNSUPPORTED;
            else if (!hasPermissions()) r = RADIO_UNAUTHORIZED;
            else if (adapter.getState() != BluetoothAdapter.STATE_ON) r = RADIO_OFF;
            else r = RADIO_ON;
        }
        catch (Throwable t)
        {
            Log.w(TAG, "radio state", t);
            later(refreshTask, 1500);
            return;
        }
        // Permissions can be given at any moment (the game asks while the co-op screen is up), and without the receiver
        // nothing says Bluetooth was switched: look again soon.
        if (r == RADIO_UNAUTHORIZED || !receiverRegistered) later(refreshTask, 1500);
        if (r == radio) return;
        int before = radio;
        radio = r;
        emit(EV_RADIO, 0, r, 0, null, null, null);
        if (before == RADIO_ON) radioLost();
        if (r == RADIO_ON)
        {
            if (hostWanted) beginHost();
            if (scanWanted) beginScan();
        }
    }

    /** Bluetooth went off (or was taken away): every connection, the server, the advertisement and the scan are gone. */
    void radioLost()
    {
        // The players are gone; hosting starts again by itself once the radio is back (hostWanted stays).
        for (Central c : centrals.values()) hostEvent(EV_DISCONNECTED, c.peer, null);
        handler.removeCallbacks(hostTimeoutTask);
        hostTimeoutArmed = false;
        handler.removeCallbacks(hostRetryTask);
        stopAdvertising();
        closeServer();
        scanning = false;
        scanner = null;
        if (gatt != null)
        {
            boolean wasReady = hostReady;
            dropHost();
            clientEvent(wasReady ? EV_DISCONNECTED : EV_CONNECT_FAILED, null, "radio");
        }
        updatePacketSize();
    }

    /** The packet size the game may use: the smallest of the connections' (their MTU less ATT's 3 bytes); 20 with none. */
    void updatePacketSize()
    {
        int size = Integer.MAX_VALUE;
        if (gatt != null && hostReady) size = hostMtu - 3;
        for (Central c : centrals.values()) size = Math.min(size, (c.mtu > 0 ? c.mtu : 23) - 3);
        size = size == Integer.MAX_VALUE ? 20 : Math.max(20, Math.min(512, size));
        if (size == maxPacket) return;
        maxPacket = size;
        emit(EV_PACKET_SIZE, 0, 0, size, null, null, null);
    }

    /** The game is done with the link: everything stops (the receiver stays, for the next link). */
    void stopAll()
    {
        endHost();
        scanWanted = false;
        endScan();
        dropHost();
    }

    // ---------- Outbound queues ----------

    /**
     * Packets waiting for one phone. Past QUEUE_LIMIT the oldest whole messages go (a message: a packet with the framing's
     * first flag and those after it up to the next first flag), never part of one: the rest of a message already on its way
     * stays, and when a message's first packet can't be taken, nor is the rest of it. The session repeats or supersedes
     * everything it sends, so a dropped message is only late.
     */
    static final class OutQueue
    {
        final ArrayDeque<byte[]> packets = new ArrayDeque<>();
        /** Set when a message's first packet was refused, or the message was dropped while still being queued: its other packets are refused too. */
        boolean refusing;

        boolean isEmpty() { return packets.isEmpty(); }
        byte[] poll() { return packets.pollFirst(); }
        /** A packet the stack wouldn't take just now: first in line again. */
        void putBack(byte[] p) { packets.addFirst(p); }
        void clear() { packets.clear(); refusing = false; }

        void offer(byte[] p)
        {
            boolean first = (p[0] & FIRST_FLAG) != 0;
            if (first) refusing = false;
            else if (refusing) return;
            while (packets.size() >= QUEUE_LIMIT && dropOldestMessage()) { }
            if (refusing) return;   // (the message p belongs to was the one dropped)
            if (packets.size() >= QUEUE_LIMIT && first) { refusing = true; return; }
            // (past the limit only for a packet of the one message left, already on its way: better than cutting it)
            packets.addLast(p);
        }

        boolean dropOldestMessage()
        {
            boolean dropping = false, dropped = false, ended = false, more = false;
            for (Iterator<byte[]> it = packets.iterator(); it.hasNext(); )
            {
                byte[] p = it.next();
                boolean first = (p[0] & FIRST_FLAG) != 0;
                if (!dropping)
                {
                    if (!first) continue;   // the rest of a message already on its way: kept
                    dropping = true;
                }
                else if (first) { more = true; break; }   // the next message: kept
                it.remove();
                dropped = true;
                ended = (p[0] & LAST_FLAG) != 0;
            }
            // The message dropped was the last one queued and isn't all there yet: the rest of it, still to come, goes too.
            if (dropped && !more && !ended) refusing = true;
            return dropped;
        }
    }

    // ---------- Host ----------

    /** A phone connected to the server (numbered the first time it subscribes or writes). */
    static final class Central
    {
        final int peer;
        final String address;
        final BluetoothDevice device;
        int mtu;   // 0 until agreed (the default, 23, is used)
        boolean subscribed;
        /** Notifications in a row that the stack never said went (see pumpHost). */
        int stalls;
        final OutQueue queue = new OutQueue();

        Central(int peer, String address, BluetoothDevice device) { this.peer = peer; this.address = address; this.device = device; }
    }

    /** A new hosting run (the game's generation gen): whatever was hosting before ends first, its players with it. */
    void beginRun(byte[] beaconBytes, int gen)
    {
        endHost();
        hostWanted = true;
        hostAnnounced = false;
        hostGen = gen & 0xFF;
        beacon = beaconBytes != null ? beaconBytes : EMPTY;
        advertiseRetry = ADVERTISE_RETRY_MIN;
        if (radio == RADIO_UNSUPPORTED) { failHost("noBluetooth"); return; }
        beginHost();   // (with the radio off, once it is on)
    }

    void setBeacon(byte[] beaconBytes)
    {
        beacon = beaconBytes != null ? beaconBytes : EMPTY;
        if (hostWanted) refreshBeacon();
    }

    void beginHost()
    {
        if (!hostWanted || radio != RADIO_ON || adapter == null || manager == null) return;
        if (!hostAnnounced && !hostTimeoutArmed)
        {
            hostTimeoutArmed = true;
            later(hostTimeoutTask, HOST_START_TIMEOUT);
        }
        // (isMultipleAdvertisementSupported() isn't asked: it says false on phones that advertise perfectly well. No
        // advertiser, or its failure callback, is the answer.)
        if (adapter.getBluetoothLeAdvertiser() == null) { hostTrouble("noAdvertise", true); return; }
        if (server != null)
        {
            if (serviceAdded) startAdvertising();
            return;
        }
        ServerCallback callback = new ServerCallback();
        BluetoothGattServer s = null;
        try { s = manager.openGattServer(context, callback); }
        catch (Throwable t) { trouble("openGattServer", t); }
        if (s == null) { hostTrouble("noServer", true); return; }
        server = s;
        serverCb = callback;
        serviceAdded = false;
        BluetoothGattService service = new BluetoothGattService(SERVICE, BluetoothGattService.SERVICE_TYPE_PRIMARY);
        // Notify only, and write without response only: nothing here is read, and no write waits for an answer.
        toClient = new BluetoothGattCharacteristic(TO_CLIENT, BluetoothGattCharacteristic.PROPERTY_NOTIFY, 0);
        toClient.addDescriptor(new BluetoothGattDescriptor(CCCD, BluetoothGattDescriptor.PERMISSION_READ | BluetoothGattDescriptor.PERMISSION_WRITE));
        BluetoothGattCharacteristic toHost = new BluetoothGattCharacteristic(TO_HOST,
            BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE, BluetoothGattCharacteristic.PERMISSION_WRITE);
        service.addCharacteristic(toClient);
        service.addCharacteristic(toHost);
        boolean ok = false;
        try { ok = s.addService(service); }
        catch (Throwable t) { trouble("addService", t); }
        if (!ok) { closeServer(); hostTrouble("addService", true); return; }
        // (onServiceAdded carries on. Before HostStarted the start timeout watches for it; after, a retry does.)
        if (hostAnnounced) later(hostRetryTask, HOST_START_TIMEOUT);
    }

    /** Stop hosting without a word to the game (it asked, or has been told why). */
    void endHost()
    {
        hostWanted = false;
        handler.removeCallbacks(hostTimeoutTask);
        hostTimeoutArmed = false;
        handler.removeCallbacks(hostRetryTask);
        stopAdvertising();
        closeServer();
    }

    /** Closes the GATT server, if any, and forgets its players (no events: the caller says what the game is told). */
    void closeServer()
    {
        BluetoothGattServer s = server;
        server = null;
        serverCb = null;
        toClient = null;
        serviceAdded = false;
        if (s != null)
        {
            for (Central c : centrals.values()) { try { s.cancelConnection(c.device); } catch (Throwable t) { Log.w(TAG, "cancelConnection", t); } }
            try { s.close(); } catch (Throwable t) { Log.w(TAG, "close server", t); }
        }
        centrals.clear(); byAddress.clear(); kicked.clear(); pendingMtu.clear();
        notifyInFlight = false;
        inFlightAddress = null;
        hostPumpWaiting = false;
        handler.removeCallbacks(hostPumpTask);
        handler.removeCallbacks(notifyWatchdog);
        updatePacketSize();
    }

    void hostTimedOut()
    {
        hostTimeoutArmed = false;
        if (hostWanted && !hostAnnounced) failHost("timeout");
    }

    /** Hosting could not start: the game hears so, and everything of the run is let go. */
    void failHost(String why)
    {
        Log.w(TAG, "hosting failed: " + why);
        hostEvent(EV_HOST_FAILED, 0, why);
        endHost();
    }

    /**
     * Something in hosting failed. Before HostStarted was said for this run, the game hears of it when it can't come right
     * (fatal); anything else is tried again, and the start timeout has the last word. After HostStarted, players may be
     * connected and the trouble may pass: it is tried again, 1, 2, 4, then every 8 s, for as long as the run lasts.
     */
    void hostTrouble(String why, boolean fatal)
    {
        if (!hostWanted) return;
        if (!hostAnnounced && fatal) { failHost(why); return; }
        Log.w(TAG, "hosting: " + why + " (again in " + advertiseRetry + " ms)");
        later(hostRetryTask, advertiseRetry);
        advertiseRetry = Math.min(ADVERTISE_RETRY_MAX, advertiseRetry * 2);
    }

    void retryHost()
    {
        if (!hostWanted || radio != RADIO_ON) return;
        if (server != null && !serviceAdded) closeServer();   // (the service never came: open the server again; no one can be connected to it)
        if (server == null) { beginHost(); return; }
        stopAdvertising();
        startAdvertising();
    }

    void kickPeer(int peer)
    {
        Central c = centrals.remove(peer);
        if (c == null) return;
        byAddress.remove(c.address);
        kicked.add(c.address);   // (until it disconnects or subscribes again, nothing it sends is heard)
        if (c.address.equals(inFlightAddress)) inFlightGone();
        if (server != null) { try { server.cancelConnection(c.device); } catch (Throwable t) { trouble("cancelConnection", t); } }
        updatePacketSize();
        pumpHost();
    }

    /** The player at this phone, numbered (and announced) the first time it subscribes or writes; null for a kicked phone. */
    Central centralFor(BluetoothDevice device, int knownMtu)
    {
        String address = device.getAddress();
        Central c = byAddress.get(address);
        if (c != null) return c;
        if (kicked.contains(address)) return null;
        // (never reused while the game runs: a late event about a player can't be taken for a newer one's)
        c = new Central(nextPeer++, address, device);
        Integer mtu = pendingMtu.remove(address);
        c.mtu = mtu != null ? mtu : knownMtu;
        byAddress.put(address, c);
        centrals.put(c.peer, c);
        hostEvent(EV_CONNECTED, c.peer, null);
        updatePacketSize();
        return c;
    }

    /** A player's connection is gone: its queue goes with it, and the game hears of it. */
    void forget(String address)
    {
        kicked.remove(address);
        Central c = byAddress.remove(address);
        if (c == null) return;
        centrals.remove(c.peer);
        hostEvent(EV_DISCONNECTED, c.peer, null);
        if (address.equals(inFlightAddress)) inFlightGone();
        updatePacketSize();
        pumpHost();
    }

    /** A phone wrote its subscription (on: notify me; off: stop). */
    void subscribed(BluetoothDevice device, boolean on)
    {
        String address = device.getAddress();
        if (!on) { forget(address); return; }   // (unsubscribing: leaving)
        kicked.remove(address);   // subscribing again after a kick: a new connection
        Central c = byAddress.get(address);
        int mtu = 0;
        if (c != null && c.subscribed)
        {
            // Subscribed already: the player's phone dropped and came back without this server hearing of it (Android
            // doesn't always say). Its old connection is gone, so is its number; the new one gets its own. The MTU it
            // agreed (since coming back, as it asks for one before subscribing) carries over.
            mtu = c.mtu;
            forget(address);
            c = null;
        }
        if (c == null) c = centralFor(device, mtu);
        if (c != null) c.subscribed = true;
    }

    void respond(BluetoothDevice device, int requestId, int status, int offset, byte[] value)
    {
        if (server == null) return;
        try { server.sendResponse(device, requestId, status, offset, value); }
        catch (Throwable t) { trouble("sendResponse", t); }
    }

    static boolean isOurCccd(BluetoothGattDescriptor d)
    {
        try { return d != null && CCCD.equals(d.getUuid()) && d.getCharacteristic() != null && TO_CLIENT.equals(d.getCharacteristic().getUuid()); }
        catch (Throwable t) { return false; }
    }

    static boolean isUuid(BluetoothGattCharacteristic c, UUID uuid)
    {
        try { return c != null && uuid.equals(c.getUuid()); }
        catch (Throwable t) { return false; }
    }

    /**
     * One per GATT server: a closed server's callbacks still on their way (they come from the stack's threads, in their
     * own time) find they belong to an old server and do nothing.
     */
    final class ServerCallback extends BluetoothGattServerCallback
    {
        boolean current() { return serverCb == this && server != null; }

        @Override public void onServiceAdded(final int status, BluetoothGattService service)
        {
            post(() ->
            {
                if (!current()) return;
                if (status != BluetoothGatt.GATT_SUCCESS) { closeServer(); hostTrouble("service" + status, true); return; }
                serviceAdded = true;
                handler.removeCallbacks(hostRetryTask);
                startAdvertising();
            });
        }

        @Override public void onConnectionStateChange(final BluetoothDevice device, int status, final int newState)
        {
            post(() ->
            {
                if (!current() || device == null) return;
                // A new connection's MTU is the default until it says otherwise; a lost one's is forgotten.
                pendingMtu.remove(device.getAddress());
                if (newState == BluetoothProfile.STATE_DISCONNECTED) forget(device.getAddress());
            });
        }

        @Override public void onMtuChanged(final BluetoothDevice device, final int mtu)
        {
            post(() ->
            {
                if (!current() || device == null) return;
                Central c = byAddress.get(device.getAddress());
                if (c != null) { c.mtu = mtu; updatePacketSize(); }
                else pendingMtu.put(device.getAddress(), mtu);   // (not subscribed yet: kept for when it does)
            });
        }

        @Override public void onDescriptorWriteRequest(final BluetoothDevice device, final int requestId, BluetoothGattDescriptor descriptor,
                                                       final boolean preparedWrite, final boolean responseNeeded, int offset, byte[] value)
        {
            final boolean ours = isOurCccd(descriptor);
            final byte[] v = value != null ? value.clone() : null;
            post(() ->
            {
                if (!current() || device == null) return;
                if (responseNeeded) respond(device, requestId, ours && !preparedWrite ? BluetoothGatt.GATT_SUCCESS : BluetoothGatt.GATT_WRITE_NOT_PERMITTED, 0, null);
                if (!ours || preparedWrite) return;
                subscribed(device, v != null && v.length > 0 && (v[0] & 1) != 0);
            });
        }

        @Override public void onDescriptorReadRequest(final BluetoothDevice device, final int requestId, final int offset, BluetoothGattDescriptor descriptor)
        {
            // (a central may read its subscription back; unanswered, it would wait for ATT's 30 s timeout)
            final boolean ours = isOurCccd(descriptor);
            post(() ->
            {
                if (!current() || device == null) return;
                if (!ours) { respond(device, requestId, BluetoothGatt.GATT_READ_NOT_PERMITTED, 0, null); return; }
                Central c = byAddress.get(device.getAddress());
                byte[] v = c != null && c.subscribed ? BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE : BluetoothGattDescriptor.DISABLE_NOTIFICATION_VALUE;
                if (offset < 0 || offset > v.length) respond(device, requestId, BluetoothGatt.GATT_INVALID_OFFSET, offset, null);
                else respond(device, requestId, BluetoothGatt.GATT_SUCCESS, offset, Arrays.copyOfRange(v, offset, v.length));
            });
        }

        @Override public void onCharacteristicReadRequest(final BluetoothDevice device, final int requestId, int offset, BluetoothGattCharacteristic characteristic)
        {
            // (neither characteristic can be read; a central that tries anyway is told so rather than left waiting)
            post(() -> { if (current() && device != null) respond(device, requestId, BluetoothGatt.GATT_READ_NOT_PERMITTED, 0, null); });
        }

        @Override public void onCharacteristicWriteRequest(final BluetoothDevice device, final int requestId, BluetoothGattCharacteristic characteristic,
                                                           final boolean preparedWrite, final boolean responseNeeded, int offset, byte[] value)
        {
            final boolean ours = isUuid(characteristic, TO_HOST);
            final byte[] v = value != null ? value.clone() : null;
            post(() ->
            {
                if (!current() || device == null) return;
                if (responseNeeded) respond(device, requestId, ours && !preparedWrite ? BluetoothGatt.GATT_SUCCESS : BluetoothGatt.GATT_WRITE_NOT_PERMITTED, 0, null);
                if (!ours || preparedWrite || v == null) return;
                Central c = centralFor(device, 0);
                if (c == null) return;
                emit(EV_DATA, c.peer, hostGen, 0, null, v, null);
                if (c.stalls > 0) { c.stalls = 0; pumpHost(); }   // (heard from: alive, its queue goes again)
            });
        }

        @Override public void onExecuteWrite(final BluetoothDevice device, final int requestId, boolean execute)
        {
            // (no prepared write is ever taken: nothing to carry out, but the central waits for the answer)
            post(() -> { if (current() && device != null) respond(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null); });
        }

        @Override public void onNotificationSent(final BluetoothDevice device, final int status)
        {
            post(() -> { if (current()) notificationSent(device, status); });
        }
    }

    void sendNow(int peer, byte[] data)
    {
        if (peer == 0)
        {
            if (gatt == null || !hostReady) return;
            clientQueue.offer(data);
            pumpWrites();
            return;
        }
        Central c = centrals.get(peer);
        if (c == null) return;
        c.queue.offer(data);
        pumpHost();
    }

    /**
     * Sends the next packet: the players' queues in turn (so one with a long queue can't hold up the others), one
     * notification in flight across the whole server, the next once the stack says it went (onNotificationSent). A phone
     * whose last two notifications were never answered is passed over until it is heard from again: a connection the stack
     * lost without saying so would otherwise hold every player up for the watchdog's second, packet after packet (its
     * queue fills and drops whole messages meanwhile, and the session times it out).
     */
    void pumpHost()
    {
        if (notifyInFlight || hostPumpWaiting || server == null || toClient == null) return;
        Central pick = null, wrap = null;
        for (Central c : centrals.values())
        {
            if (c.queue.isEmpty() || c.stalls >= 2) continue;
            if (c.peer > lastServed) { pick = c; break; }
            if (wrap == null) wrap = c;
        }
        if (pick == null) pick = wrap;
        if (pick == null) return;
        lastServed = pick.peer;
        byte[] packet = pick.queue.poll();
        if (notifyNow(pick.device, packet))
        {
            notifyInFlight = true;
            inFlightAddress = pick.address;
            later(notifyWatchdog, SEND_WATCHDOG);
        }
        else
        {
            // The stack is busy: again shortly (the next turn is the next player's, so one that won't take a packet
            // doesn't hold up the rest).
            pick.queue.putBack(packet);
            hostPumpLater();
        }
    }

    @SuppressWarnings("deprecation")
    boolean notifyNow(BluetoothDevice device, byte[] packet)
    {
        try
        {
            if (Build.VERSION.SDK_INT >= 33) return server.notifyCharacteristicChanged(device, toClient, false, packet) == BluetoothStatusCodes.SUCCESS;
            toClient.setValue(packet);
            return server.notifyCharacteristicChanged(device, toClient, false);
        }
        catch (Throwable t)
        {
            trouble("notify", t);
            return false;
        }
    }

    void notificationSent(BluetoothDevice device, int status)
    {
        if (device == null) return;
        Central c = byAddress.get(device.getAddress());
        if (c != null) c.stalls = 0;   // (answered, if late: alive)
        if (!notifyInFlight || !device.getAddress().equals(inFlightAddress))
        {
            // (late, for one the watchdog already gave up on: the one in flight now, if any, has its own answer coming)
            pumpHost();
            return;
        }
        notifyInFlight = false;
        inFlightAddress = null;
        handler.removeCallbacks(notifyWatchdog);
        // A failed status (a congested link, mostly) isn't sent again: the packet may well have gone, and sent twice it
        // would garble its message. The next one waits a moment instead.
        if (status != BluetoothGatt.GATT_SUCCESS) hostPumpLater();
        else pumpHost();
    }

    void notifyTimedOut()
    {
        if (!notifyInFlight) return;
        Log.w(TAG, "no onNotificationSent: carrying on");
        Central c = inFlightAddress != null ? byAddress.get(inFlightAddress) : null;
        if (c != null) c.stalls++;
        notifyInFlight = false;
        inFlightAddress = null;
        pumpHost();
    }

    /** The player whose notification is in flight is gone: no answer will come for it. */
    void inFlightGone()
    {
        notifyInFlight = false;
        inFlightAddress = null;
        handler.removeCallbacks(notifyWatchdog);
    }

    void hostPumpLater()
    {
        if (hostPumpWaiting) return;
        hostPumpWaiting = true;
        later(hostPumpTask, BUSY_RETRY);
    }

    void hostPumpTick()
    {
        hostPumpWaiting = false;
        pumpHost();
    }

    // ---------- Advertising ----------

    AdvertisingSetParameters setParameters()
    {
        // Legacy advertising (what every phone that scans can hear), connectable and scannable (the scan response holds the
        // beacon), about every 100 ms at high power: the old API's LOW_LATENCY and TX_POWER_HIGH.
        return new AdvertisingSetParameters.Builder()
            .setLegacyMode(true)
            .setConnectable(true)
            .setScannable(true)
            .setInterval(AdvertisingSetParameters.INTERVAL_LOW)
            .setTxPowerLevel(AdvertisingSetParameters.TX_POWER_HIGH)
            .build();
    }

    static AdvertiseData advertiseData()
    {
        return new AdvertiseData.Builder().addServiceUuid(new ParcelUuid(SERVICE)).setIncludeDeviceName(false).setIncludeTxPowerLevel(false).build();
    }

    AdvertiseData scanResponse()
    {
        return new AdvertiseData.Builder().addServiceData(BEACON_KEY, beacon).setIncludeDeviceName(false).setIncludeTxPowerLevel(false).build();
    }

    /**
     * Starts the advertisement, as an advertising set: its scan response (the beacon) can then change in place, where a
     * restart may come back with a new address and drop the room from the scanners' lists for a moment. The old
     * startAdvertising only on a phone whose stack won't take a set.
     */
    void startAdvertising()
    {
        if (!hostWanted || !serviceAdded || radio != RADIO_ON || adapter == null || advertCallback != null) return;
        BluetoothLeAdvertiser adv = adapter.getBluetoothLeAdvertiser();
        if (adv == null) { hostTrouble("noAdvertise", true); return; }
        beaconDirty = false;
        AdvertiseData data = advertiseData(), response = scanResponse();
        if (useSets)
        {
            SetCallback callback = new SetCallback(adv);
            try
            {
                adv.startAdvertisingSet(setParameters(), data, response, null, null, callback);
                advertCallback = callback;
                return;
            }
            catch (SecurityException | IllegalStateException e)
            {
                // (a permission taken away, or Bluetooth going off: the old API would fare no better)
                trouble("startAdvertisingSet", e);
                forgetSet(adv, callback);
                advertFailed(AdvertiseCallback.ADVERTISE_FAILED_INTERNAL_ERROR);
                return;
            }
            catch (Throwable t)
            {
                Log.w(TAG, "advertising sets unavailable: the old API from now on", t);
                forgetSet(adv, callback);
                useSets = false;
            }
        }
        LegacyCallback callback = new LegacyCallback(adv);
        AdvertiseSettings settings = new AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(true)
            .setTimeout(0)
            .build();
        try
        {
            adv.startAdvertising(settings, data, response, callback);
            advertCallback = callback;
            legacyStartedAt = SystemClock.elapsedRealtime();
        }
        catch (IllegalArgumentException e) { trouble("startAdvertising", e); advertFailed(AdvertiseCallback.ADVERTISE_FAILED_DATA_TOO_LARGE); }
        catch (Throwable t) { trouble("startAdvertising", t); advertFailed(AdvertiseCallback.ADVERTISE_FAILED_INTERNAL_ERROR); }
    }

    /** (the advertiser may have taken the callback before the start threw: let it go, so it isn't kept for nothing) */
    static void forgetSet(BluetoothLeAdvertiser adv, SetCallback callback)
    {
        try { adv.stopAdvertisingSet(callback); }
        catch (Throwable ignored) { }
    }

    void stopAdvertising()
    {
        handler.removeCallbacks(readvertiseTask);
        Object callback = advertCallback;
        advertCallback = null;
        advertSet = null;
        advertising = false;
        responsePending = false;
        try
        {
            if (callback instanceof SetCallback) ((SetCallback)callback).adv.stopAdvertisingSet((SetCallback)callback);
            else if (callback instanceof LegacyCallback) ((LegacyCallback)callback).adv.stopAdvertising((LegacyCallback)callback);
        }
        catch (Throwable t) { Log.w(TAG, "stopAdvertising", t); }
    }

    void advertStarted(AdvertisingSet set)
    {
        advertising = true;
        advertSet = set;
        advertiseRetry = ADVERTISE_RETRY_MIN;
        handler.removeCallbacks(hostRetryTask);
        if (!hostAnnounced)
        {
            hostAnnounced = true;
            handler.removeCallbacks(hostTimeoutTask);
            hostTimeoutArmed = false;
            hostEvent(EV_HOST_STARTED, 0, null);
        }
        if (beaconDirty) refreshBeacon();   // (it changed while the start was under way)
    }

    void advertFailed(int code)
    {
        advertCallback = null;
        advertSet = null;
        advertising = false;
        responsePending = false;
        if (code == AdvertiseCallback.ADVERTISE_FAILED_FEATURE_UNSUPPORTED) hostTrouble("noAdvertise", true);   // this phone can't host; it can still join
        else if (code == AdvertiseCallback.ADVERTISE_FAILED_DATA_TOO_LARGE) hostTrouble("advertise" + code, true);
        else hostTrouble("advertise" + code, false);   // (too many advertisers just now, the stack's own trouble: again)
    }

    /** Puts the current beacon in the advertisement: in place with an advertising set; with the old API only by starting over. */
    void refreshBeacon()
    {
        if (!hostWanted) return;
        if (!advertising)
        {
            // (a start yet to come takes the beacon of the moment; one already under way is updated once it's done)
            beaconDirty = true;
            return;
        }
        long now = SystemClock.elapsedRealtime();
        if (advertSet != null)
        {
            // One change at a time: another while one is on its way goes when that is answered (or 2 s without an answer).
            if (responsePending && now - responseSentAt < 2000)
            {
                beaconDirty = true;
                later(readvertiseTask, 2000 - (now - responseSentAt));
                return;
            }
            beaconDirty = false;
            responsePending = true;
            responseSentAt = now;
            try { advertSet.setScanResponseData(scanResponse()); }
            catch (Throwable t)
            {
                trouble("setScanResponseData", t);
                stopAdvertising();
                startAdvertising();
            }
            return;
        }
        // The old API: a restart is the only way, and some phones refuse restarts more often than once a second.
        long wait = 1000 - (now - legacyStartedAt);
        if (wait > 0)
        {
            beaconDirty = true;
            later(readvertiseTask, wait);
            return;
        }
        stopAdvertising();
        startAdvertising();
    }

    void readvertise()
    {
        if (beaconDirty) refreshBeacon();
    }

    /** One per advertising start: a stopped or replaced one's late callbacks do nothing (or stop what they started). */
    final class SetCallback extends AdvertisingSetCallback
    {
        final BluetoothLeAdvertiser adv;

        SetCallback(BluetoothLeAdvertiser adv) { this.adv = adv; }

        boolean current() { return advertCallback == this; }

        @Override public void onAdvertisingSetStarted(final AdvertisingSet set, int txPower, final int status)
        {
            post(() ->
            {
                if (!current())
                {
                    // Started after hosting moved on (stopped, or started over): it mustn't advertise on.
                    if (status == ADVERTISE_SUCCESS) { try { adv.stopAdvertisingSet(this); } catch (Throwable t) { Log.w(TAG, "stopAdvertisingSet", t); } }
                    return;
                }
                if (status == ADVERTISE_SUCCESS || status == ADVERTISE_FAILED_ALREADY_STARTED) advertStarted(set);
                else advertFailed(status);
            });
        }

        @Override public void onAdvertisingSetStopped(AdvertisingSet set)
        {
            post(() ->
            {
                if (!current()) return;   // (stopped by stopAdvertising: expected)
                // Stopped without being asked (the stack's doing): start again.
                advertCallback = null;
                advertSet = null;
                advertising = false;
                responsePending = false;
                hostTrouble("advertisingStopped", false);
            });
        }

        @Override public void onAdvertisingEnabled(AdvertisingSet set, final boolean enable, final int status)
        {
            post(() ->
            {
                if (!current() || (enable && status == ADVERTISE_SUCCESS)) return;
                // Switched off by the stack (nothing here asks for that): a fresh start.
                stopAdvertising();
                hostTrouble("advertisingDisabled" + status, false);
            });
        }

        @Override public void onScanResponseDataSet(AdvertisingSet set, final int status)
        {
            post(() ->
            {
                if (!current()) return;
                responsePending = false;
                if (status == ADVERTISE_SUCCESS)
                {
                    if (beaconDirty) refreshBeacon();
                    return;
                }
                // Not taken (the advertisement goes on with the old beacon): start it over with the new one.
                Log.w(TAG, "setScanResponseData: " + status);
                stopAdvertising();
                startAdvertising();
            });
        }
    }

    /** The old API's callback (a phone without advertising sets), one per start like SetCallback. */
    final class LegacyCallback extends AdvertiseCallback
    {
        final BluetoothLeAdvertiser adv;

        LegacyCallback(BluetoothLeAdvertiser adv) { this.adv = adv; }

        boolean current() { return advertCallback == this; }

        @Override public void onStartSuccess(AdvertiseSettings settingsInEffect)
        {
            post(() ->
            {
                if (!current()) { try { adv.stopAdvertising(this); } catch (Throwable t) { Log.w(TAG, "stopAdvertising", t); } return; }
                advertStarted(null);
            });
        }

        @Override public void onStartFailure(final int errorCode)
        {
            post(() ->
            {
                if (!current()) return;
                if (errorCode == ADVERTISE_FAILED_ALREADY_STARTED) { advertStarted(null); return; }
                try { adv.stopAdvertising(this); } catch (Throwable ignored) { }   // (lets the stack forget this callback)
                advertFailed(errorCode);
            });
        }
    }

    // ---------- Scanning ----------

    /** A phone heard while scanning: its latest device (connect uses it) and when it was last reported to the game. */
    static final class Seen
    {
        BluetoothDevice device;
        long seenAt, reportedAt;
    }

    void wantScan()
    {
        scanWanted = true;
        handler.removeCallbacks(scanStopTask);   // (a stop asked for a moment ago hasn't happened: the scan just carries on)
        beginScan();
    }

    void unwantScan()
    {
        scanWanted = false;
        // A moment later, so a stop followed by a start (the session does that) costs no start (see beginScan).
        later(scanStopTask, SCAN_STOP_DELAY);
    }

    void scanStopTick()
    {
        if (!scanWanted) endScan();
    }

    /**
     * Android quietly ignores an app that starts scanning a sixth time within 30 s (the scan "starts" and never finds
     * anything). So at most four starts in any 30 s: one more waits until the oldest of them is 30 s old.
     */
    void beginScan()
    {
        handler.removeCallbacks(scanStartTask);
        if (!scanWanted || scanning || radio != RADIO_ON || adapter == null) return;
        long now = SystemClock.elapsedRealtime();
        while (!scanStarts.isEmpty() && now - scanStarts.peekFirst() >= SCAN_WINDOW) scanStarts.pollFirst();
        if (scanStarts.size() >= SCAN_STARTS)
        {
            later(scanStartTask, scanStarts.peekFirst() + SCAN_WINDOW - now + 100);
            return;
        }
        BluetoothLeScanner s = adapter.getBluetoothLeScanner();
        if (s == null) { later(scanStartTask, SCAN_RETRY); return; }
        List<ScanFilter> filters = Collections.singletonList(new ScanFilter.Builder().setServiceUuid(new ParcelUuid(SERVICE)).build());
        ScanSettings settings = new ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build();
        scanStarts.addLast(now);   // (counted whether or not it works: Android counts it)
        try
        {
            s.startScan(filters, settings, scanCallback);
            scanner = s;
            scanning = true;
        }
        catch (Throwable t)
        {
            trouble("startScan", t);
            later(scanStartTask, SCAN_RETRY);
        }
    }

    void endScan()
    {
        handler.removeCallbacks(scanStopTask);
        handler.removeCallbacks(scanStartTask);
        if (!scanning) return;
        scanning = false;
        BluetoothLeScanner s = scanner;
        scanner = null;
        if (s != null && radio == RADIO_ON) { try { s.stopScan(scanCallback); } catch (Throwable t) { Log.w(TAG, "stopScan", t); } }
    }

    final ScanCallback scanCallback = new ScanCallback()
    {
        @Override public void onScanResult(int callbackType, final ScanResult result) { post(() -> found(result)); }

        @Override public void onBatchScanResults(final List<ScanResult> results)
        {
            post(() -> { if (results != null) for (ScanResult r : results) found(r); });
        }

        @Override public void onScanFailed(final int errorCode)
        {
            post(() ->
            {
                if (errorCode == SCAN_FAILED_ALREADY_STARTED) return;   // (scanning already, with this very callback)
                Log.w(TAG, "scan failed: " + errorCode);
                scanning = false;
                scanner = null;
                // (the stack busy, or scanning too often: again in a moment, within the limit)
                later(scanStartTask, SCAN_RETRY);
            });
        }
    };

    void found(ScanResult result)
    {
        if (!scanning || result == null || result.getDevice() == null) return;
        BluetoothDevice device = result.getDevice();
        String address = device.getAddress();
        long now = SystemClock.elapsedRealtime();
        Seen s = seen.get(address);
        if (s == null)
        {
            if (seen.size() >= SEEN_LIMIT) forgetSeen(now);
            s = new Seen();
            s.reportedAt = now - 1000;
            seen.put(address, s);
        }
        s.device = device;
        s.seenAt = now;
        if (now - s.reportedAt < 250) return;   // a few reports a second are plenty
        s.reportedAt = now;
        ScanRecord record = result.getScanRecord();
        byte[] data = record != null ? record.getServiceData(BEACON_KEY) : null;
        String name = record != null ? record.getDeviceName() : null;
        emit(EV_FOUND, 0, 0, result.getRssi(), address, data, name);
    }

    /** (phones' addresses change every few minutes, so the list of those heard would only grow) */
    void forgetSeen(long now)
    {
        for (Iterator<Seen> it = seen.values().iterator(); it.hasNext(); )
            if (now - it.next().seenAt > 60000) it.remove();
        if (seen.size() >= SEEN_LIMIT) seen.clear();
    }

    // ---------- Client ----------

    void connectTo(String address, int gen)
    {
        dropHost();
        clientGen = gen & 0xFF;
        BluetoothDevice device = null;
        try
        {
            if (radio == RADIO_ON && adapter != null && address != null && BluetoothAdapter.checkBluetoothAddress(address))
            {
                // The device from the scan that found the host keeps its address type (a phone's random address, mostly):
                // made from the address alone, it may be taken for a public one and the connection never comes.
                Seen s = seen.get(address);
                device = s != null ? s.device : adapter.getRemoteDevice(address);
            }
        }
        catch (Throwable t) { trouble("getRemoteDevice", t); }
        if (device == null) { clientEvent(EV_CONNECT_FAILED, address, "unavailable"); return; }
        ClientCallback callback = new ClientCallback();
        BluetoothGatt g = null;
        try { g = device.connectGatt(context, false, callback, BluetoothDevice.TRANSPORT_LE); }
        catch (Throwable t) { trouble("connectGatt", t); }
        if (g == null) { clientEvent(EV_CONNECT_FAILED, address, "connectGatt"); return; }
        gatt = g;
        gattCb = callback;
        later(connectTimeoutTask, CONNECT_TIMEOUT);
    }

    /** Hang up on the host (connected or connecting) without telling the game: it asked, or is being told by the caller. */
    void dropHost()
    {
        handler.removeCallbacks(connectTimeoutTask);
        handler.removeCallbacks(clientStepTask);
        handler.removeCallbacks(subscribeTask);
        handler.removeCallbacks(writeWatchdog);
        handler.removeCallbacks(clientPumpTask);
        BluetoothGatt g = gatt;
        gatt = null;
        gattCb = null;
        hostReady = false;
        hostWrite = null;
        cccd = null;
        linkUp = awaitingMtu = discovering = writing = clientPumpWaiting = false;
        discoverTries = subscribeTries = 0;
        hostMtu = 23;
        clientQueue.clear();
        if (g != null) closeGatt(g);
        updatePacketSize();
    }

    static void closeGatt(BluetoothGatt g)
    {
        // (separately: a disconnect that throws mustn't keep the close from happening, or the stack keeps the client slot)
        try { g.disconnect(); } catch (Throwable t) { Log.w(TAG, "disconnect", t); }
        try { g.close(); } catch (Throwable t) { Log.w(TAG, "close", t); }
    }

    /** The connection failed before the host was ready: hang up and tell the game. */
    void hostFailed(String why)
    {
        if (gatt == null) return;
        Log.w(TAG, "connect failed: " + why);
        dropHost();
        clientEvent(EV_CONNECT_FAILED, null, why);
    }

    void connectTimedOut()
    {
        if (gatt != null && !hostReady) hostFailed("timeout");
    }

    void discover()
    {
        if (gatt == null || hostReady) return;
        awaitingMtu = false;
        discovering = true;
        discoverTries++;
        boolean asked = false;
        try { asked = gatt.discoverServices(); }
        catch (Throwable t) { trouble("discoverServices", t); }
        if (!asked) Log.w(TAG, "discoverServices refused");
        later(clientStepTask, DISCOVER_WATCHDOG);   // (no answer in time: asked once more, then given up on)
    }

    /** The MTU's or the discovery's watchdog. */
    void clientStep()
    {
        if (gatt == null || hostReady) return;
        if (awaitingMtu) { discover(); return; }   // (no word on the MTU: carry on with the default)
        if (!discovering) return;
        discovering = false;
        if (discoverTries < 2) discover();
        else hostFailed("discover");
    }

    void servicesDiscovered(BluetoothGatt g, int status)
    {
        if (!discovering) return;   // (an answer to a request already given up on, or a discovery the stack did of itself)
        discovering = false;
        handler.removeCallbacks(clientStepTask);
        BluetoothGattService service = status == BluetoothGatt.GATT_SUCCESS ? g.getService(SERVICE) : null;
        if (service == null)
        {
            // Once more (the first look can come back failed or empty while the link settles), then give up.
            if (discoverTries < 2) { discover(); return; }
            hostFailed(status == BluetoothGatt.GATT_SUCCESS ? "noService" : "discover" + status);
            return;
        }
        BluetoothGattCharacteristic notify = service.getCharacteristic(TO_CLIENT);
        hostWrite = service.getCharacteristic(TO_HOST);
        if (notify == null || hostWrite == null) { hostFailed("noCharacteristics"); return; }
        BluetoothGattDescriptor d = notify.getDescriptor(CCCD);
        if (d == null) { hostFailed("noCccd"); return; }
        g.setCharacteristicNotification(notify, true);
        cccd = d;
        subscribeTries = 0;
        writeCccd();
    }

    @SuppressWarnings("deprecation")
    void writeCccd()
    {
        if (gatt == null || hostReady || cccd == null) return;
        boolean ok = false;
        try
        {
            if (Build.VERSION.SDK_INT >= 33) ok = gatt.writeDescriptor(cccd, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE) == BluetoothStatusCodes.SUCCESS;
            else
            {
                cccd.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);
                ok = gatt.writeDescriptor(cccd);
            }
        }
        catch (Throwable t) { trouble("subscribe", t); }
        if (ok) return;
        // The stack is busy (the MTU exchange still settling, mostly): again shortly, for up to a second.
        if (++subscribeTries < 20) later(subscribeTask, BUSY_RETRY);
        else hostFailed("subscribe");
    }

    void subscribedToHost(int status)
    {
        if (status != BluetoothGatt.GATT_SUCCESS) { hostFailed("subscribe" + status); return; }
        handler.removeCallbacks(connectTimeoutTask);
        handler.removeCallbacks(subscribeTask);
        cccd = null;
        hostReady = true;
        updatePacketSize();
        clientEvent(EV_CONNECTED, null, null);
        pumpWrites();
    }

    /** One per connection attempt: callbacks of a connection let go of (replaced, failed, hung up) do nothing. */
    final class ClientCallback extends BluetoothGattCallback
    {
        boolean current(BluetoothGatt g) { return gattCb == this && g != null && g == gatt; }

        @Override public void onConnectionStateChange(final BluetoothGatt g, final int status, final int newState)
        {
            post(() ->
            {
                if (!current(g))
                {
                    if (g != null && g != gatt) { try { g.close(); } catch (Throwable ignored) { } }   // (closed already, as a rule: no harm)
                    return;
                }
                if (newState == BluetoothProfile.STATE_CONNECTED)
                {
                    if (linkUp) return;
                    linkUp = true;
                    try { g.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH); }
                    catch (Throwable t) { trouble("requestConnectionPriority", t); }
                    boolean asked = false;
                    try { asked = g.requestMtu(247); }
                    catch (Throwable t) { trouble("requestMtu", t); }
                    if (asked)
                    {
                        // onMtuChanged discovers once the MTU is agreed (or the watchdog does, on phones that never say).
                        awaitingMtu = true;
                        later(clientStepTask, DISCOVER_WATCHDOG);
                    }
                    else discover();
                }
                else if (newState == BluetoothProfile.STATE_DISCONNECTED)
                {
                    boolean wasReady = hostReady;
                    dropHost();
                    clientEvent(wasReady ? EV_DISCONNECTED : EV_CONNECT_FAILED, null, "status" + status);
                }
            });
        }

        @Override public void onMtuChanged(final BluetoothGatt g, final int mtu, final int status)
        {
            post(() ->
            {
                if (!current(g)) return;
                if (status == BluetoothGatt.GATT_SUCCESS) hostMtu = Math.max(23, mtu);
                if (awaitingMtu) discover();
                else updatePacketSize();
            });
        }

        @Override public void onServicesDiscovered(final BluetoothGatt g, final int status)
        {
            post(() -> { if (current(g)) servicesDiscovered(g, status); });
        }

        @Override public void onDescriptorWrite(final BluetoothGatt g, BluetoothGattDescriptor descriptor, final int status)
        {
            post(() -> { if (current(g) && !hostReady && cccd != null) subscribedToHost(status); });
        }

        @Override public void onCharacteristicChanged(final BluetoothGatt g, BluetoothGattCharacteristic characteristic, byte[] value)
        {
            // Android 13 and up (the value is this notification's own).
            final byte[] copy = value != null ? value.clone() : null;
            post(() -> { if (current(g) && copy != null) fromHost(copy); });
        }

        @SuppressWarnings("deprecation")
        @Override public void onCharacteristicChanged(final BluetoothGatt g, BluetoothGattCharacteristic characteristic)
        {
            if (Build.VERSION.SDK_INT >= 33) return;   // (the call above has it)
            // Before Android 13 the value lives in the characteristic, and the next notification overwrites it: copy it now.
            byte[] v = null;
            try { v = characteristic != null ? characteristic.getValue() : null; }
            catch (Throwable ignored) { }
            final byte[] copy = v != null ? v.clone() : null;
            post(() -> { if (current(g) && copy != null) fromHost(copy); });
        }

        @Override public void onCharacteristicWrite(final BluetoothGatt g, BluetoothGattCharacteristic characteristic, final int status)
        {
            post(() -> { if (current(g)) written(status); });
        }
    }

    /** A packet from the host. */
    void fromHost(byte[] data) { emit(EV_DATA, 0, clientGen, 0, null, data, null); }

    /** Writes the next packet to the host: one in flight, the next once the stack says it went (onCharacteristicWrite). */
    void pumpWrites()
    {
        if (writing || clientPumpWaiting || gatt == null || hostWrite == null || !hostReady) return;
        byte[] packet = clientQueue.poll();
        if (packet == null) return;
        if (writeNow(packet))
        {
            writing = true;
            later(writeWatchdog, SEND_WATCHDOG);
        }
        else
        {
            clientQueue.putBack(packet);   // the stack is busy: again shortly
            clientPumpLater();
        }
    }

    @SuppressWarnings("deprecation")
    boolean writeNow(byte[] packet)
    {
        try
        {
            if (Build.VERSION.SDK_INT >= 33)
                return gatt.writeCharacteristic(hostWrite, packet, BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE) == BluetoothStatusCodes.SUCCESS;
            hostWrite.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE);
            hostWrite.setValue(packet);
            return gatt.writeCharacteristic(hostWrite);
        }
        catch (Throwable t)
        {
            trouble("write", t);
            return false;
        }
    }

    void written(int status)
    {
        writing = false;
        handler.removeCallbacks(writeWatchdog);
        // (a failed status isn't written again, for the reason notificationSent gives: the next one waits a moment)
        if (status != BluetoothGatt.GATT_SUCCESS) clientPumpLater();
        else pumpWrites();
    }

    void writeTimedOut()
    {
        if (!writing) return;
        Log.w(TAG, "no onCharacteristicWrite: carrying on");
        writing = false;
        pumpWrites();
    }

    void clientPumpLater()
    {
        if (clientPumpWaiting) return;
        clientPumpWaiting = true;
        later(clientPumpTask, BUSY_RETRY);
    }

    void clientPumpTick()
    {
        clientPumpWaiting = false;
        pumpWrites();
    }
}
