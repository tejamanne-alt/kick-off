// Bluetooth LE for the co-op mode (called from Coop/Transport/AndroidBleLink.cs; the iOS twin is
// Plugins/iOS/DTSCoopBLE.mm, and both speak the same packed events, docs/COOP.md "Native bridge").
//
// The host is a GATT server that advertises the game's service (its lobby's beacon in the scan response); each other
// player scans for it, connects as a GATT client, subscribes to the host's "to client" characteristic and writes to its
// "to host" one. Android allows one GATT operation in flight per connection, so packets wait in a queue per phone and
// go one after another; none is dropped while a connection lasts. Everything runs on one handler thread; the game polls
// the events once a frame.
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
import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseData;
import android.bluetooth.le.AdvertiseSettings;
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

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@SuppressLint("MissingPermission")   // every call is made only once the game has the permissions (radioState says Unauthorized otherwise)
public final class DtsCoopBle
{
    static final UUID SERVICE = UUID.fromString("8C5F0001-2B7E-4D5A-9E3B-4B4F32C0FFEE");
    static final UUID TO_CLIENT = UUID.fromString("8C5F0002-2B7E-4D5A-9E3B-4B4F32C0FFEE");
    static final UUID TO_HOST = UUID.fromString("8C5F0003-2B7E-4D5A-9E3B-4B4F32C0FFEE");
    static final UUID CCCD = UUID.fromString("00002902-0000-1000-8000-00805F9B34FB");
    /** The 16-bit key ("KO") the lobby's beacon goes under in the scan response, as a full UUID. */
    static final ParcelUuid BEACON_KEY = ParcelUuid.fromString("00004B4F-0000-1000-8000-00805F9B34FB");

    static final int EV_RADIO = 1, EV_FOUND = 2, EV_CONNECTED = 3, EV_DISCONNECTED = 4, EV_DATA = 5,
        EV_HOST_STARTED = 6, EV_HOST_FAILED = 7, EV_CONNECT_FAILED = 8, EV_PACKET_SIZE = 9;
    static final int RADIO_UNKNOWN = 0, RADIO_UNSUPPORTED = 1, RADIO_UNAUTHORIZED = 2, RADIO_OFF = 3, RADIO_ON = 4;
    /** How many packets may wait for one phone before the oldest whole messages are dropped (the session repeats them). */
    static final int QUEUE_LIMIT = 96;

    static DtsCoopBle instance;

    final Context context;
    final Handler handler;
    final List<byte[]> events = new ArrayList<>();
    volatile int radio = RADIO_UNKNOWN;
    volatile int maxPacket = 20;

    BluetoothManager manager;
    BluetoothAdapter adapter;
    boolean receiverRegistered;

    // Host
    boolean hostWanted, hostAnnounced, advertising, serviceAdded;
    byte[] beacon = new byte[0];
    BluetoothGattServer server;
    BluetoothGattCharacteristic toClient;
    final Map<String, Integer> peerOf = new HashMap<>();
    final Map<Integer, BluetoothDevice> devices = new HashMap<>();
    final Map<Integer, Integer> mtuOf = new HashMap<>();
    final Map<Integer, ArrayDeque<byte[]>> outbox = new HashMap<>();
    final Map<Integer, Boolean> inFlight = new HashMap<>();
    final java.util.Set<String> kicked = new java.util.HashSet<>();
    int nextPeer = 1;
    long lastAdvertise;

    // Scanning and the client role
    boolean scanWanted, scanning;
    final Map<String, Long> lastReport = new HashMap<>();
    BluetoothGatt gatt;
    BluetoothGattCharacteristic hostWrite;
    boolean hostReady, explicitDisconnect, writing;
    int hostMtu = 23;
    final ArrayDeque<byte[]> writes = new ArrayDeque<>();
    int connectToken;

    // ---------- What C# calls ----------

    public static synchronized DtsCoopBle init(Activity activity)
    {
        if (instance == null) instance = new DtsCoopBle(activity.getApplicationContext());
        instance.post(instance::start);
        return instance;
    }

    DtsCoopBle(Context context)
    {
        this.context = context;
        HandlerThread thread = new HandlerThread("dts-coop-ble");
        thread.start();
        handler = new Handler(thread.getLooper());
    }

    void post(Runnable r) { handler.post(r); }

    public void startHost(final byte[] beaconBytes) { post(() -> { hostWanted = true; hostAnnounced = false; beacon = beaconBytes != null ? beaconBytes : new byte[0]; beginHost(); }); }
    public void updateBeacon(final byte[] beaconBytes) { post(() -> { beacon = beaconBytes != null ? beaconBytes : new byte[0]; if (hostWanted && serviceAdded) advertise(); }); }
    public void stopHost() { post(this::endHost); }
    public void kick(final int peer) { post(() -> kickPeer(peer)); }
    public void startScan() { post(() -> { scanWanted = true; beginScan(); }); }
    public void stopScan() { post(() -> { scanWanted = false; endScan(); }); }
    public void connect(final String address) { post(() -> connectTo(address)); }
    public void disconnect() { post(this::dropHost); }
    public void send(final int peer, final byte[] data) { if (data != null && data.length > 0) post(() -> sendNow(peer, data)); }
    public int radioState() { return radio; }
    public int maxPacket() { return maxPacket; }
    public void shutdown() { post(() -> { endHost(); scanWanted = false; endScan(); dropHost(); }); }

    /** Every packed event since the last call, back to back (docs/COOP.md "Native bridge"). */
    public byte[] poll()
    {
        synchronized (events)
        {
            if (events.isEmpty()) return null;
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            int used = 0;
            Iterator<byte[]> it = events.iterator();
            while (it.hasNext())
            {
                byte[] e = it.next();
                if (used + e.length > 65536 && used > 0) break;
                out.write(e, 0, e.length);
                used += e.length;
                it.remove();
            }
            return out.toByteArray();
        }
    }

    /** The permissions the game must hold to use Bluetooth on this Android version. */
    public static String[] neededPermissions()
    {
        if (Build.VERSION.SDK_INT >= 31)
            return new String[] { Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT, Manifest.permission.BLUETOOTH_ADVERTISE };
        return new String[] { Manifest.permission.ACCESS_FINE_LOCATION };
    }

    /** Below Android 12, scanning finds nothing while Location is off: the Join screen says so. */
    public boolean locationNeededAndOff()
    {
        if (Build.VERSION.SDK_INT >= 31) return false;
        LocationManager lm = (LocationManager)context.getSystemService(Context.LOCATION_SERVICE);
        if (lm == null) return false;
        if (Build.VERSION.SDK_INT >= 28) return !lm.isLocationEnabled();
        return !lm.isProviderEnabled(LocationManager.GPS_PROVIDER) && !lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER);
    }

    public void openSettings(Activity activity)
    {
        try
        {
            Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", activity.getPackageName(), null));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(intent);
        }
        catch (Exception ignored) { }
    }

    public void openBluetoothSettings(Activity activity)
    {
        try
        {
            Intent intent = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS);
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            activity.startActivity(intent);
        }
        catch (Exception ignored) { }
    }

    // ---------- Events ----------

    void emit(int type, int peer, int state, int rssi, String address, byte[] data, String name)
    {
        byte[] a = (address != null ? address : "").getBytes(StandardCharsets.UTF_8);
        byte[] d = data != null ? data : new byte[0];
        byte[] n = (name != null ? name : "").getBytes(StandardCharsets.UTF_8);
        ByteArrayOutputStream e = new ByteArrayOutputStream(16 + a.length + d.length + n.length);
        e.write(type);
        e.write(peer & 0xFF); e.write((peer >> 8) & 0xFF); e.write((peer >> 16) & 0xFF); e.write((peer >> 24) & 0xFF);
        e.write(state);
        e.write(rssi & 0xFF); e.write((rssi >> 8) & 0xFF);
        putBlock(e, a);
        putBlock(e, d);
        putBlock(e, n);
        synchronized (events) { events.add(e.toByteArray()); }
    }

    static void putBlock(ByteArrayOutputStream e, byte[] b)
    {
        int len = Math.min(b.length, 0xFFFF);
        e.write(len & 0xFF); e.write((len >> 8) & 0xFF);
        e.write(b, 0, len);
    }

    void emit(int type, int peer) { emit(type, peer, 0, 0, null, null, null); }

    // ---------- The radio ----------

    void start()
    {
        if (manager == null)
        {
            manager = (BluetoothManager)context.getSystemService(Context.BLUETOOTH_SERVICE);
            adapter = manager != null ? manager.getAdapter() : null;
        }
        if (!receiverRegistered)
        {
            IntentFilter filter = new IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED);
            BroadcastReceiver receiver = new BroadcastReceiver()
            {
                @Override public void onReceive(Context c, Intent intent) { post(DtsCoopBle.this::refreshRadio); }
            };
            if (Build.VERSION.SDK_INT >= 33) context.registerReceiver(receiver, filter, null, handler, Context.RECEIVER_EXPORTED);
            else context.registerReceiver(receiver, filter, null, handler);
            receiverRegistered = true;
        }
        refreshRadio();
        // Permissions may have been granted since the last look: check again a few times while the co-op screen is up.
        handler.postDelayed(this::refreshRadio, 1500);
    }

    boolean hasPermissions()
    {
        for (String p : neededPermissions())
            if (context.checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) return false;
        return true;
    }

    void refreshRadio()
    {
        int r;
        if (adapter == null || !context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE)) r = RADIO_UNSUPPORTED;
        else if (!hasPermissions()) r = RADIO_UNAUTHORIZED;
        else if (adapter.getState() != BluetoothAdapter.STATE_ON) r = RADIO_OFF;
        else r = RADIO_ON;
        if (r == radio)
        {
            if (r == RADIO_UNAUTHORIZED) handler.postDelayed(this::refreshRadio, 1500);
            return;
        }
        int before = radio;
        radio = r;
        emit(EV_RADIO, 0, r, 0, null, null, null);
        if (before == RADIO_ON && r != RADIO_ON) radioLost();
        if (r == RADIO_ON)
        {
            if (hostWanted) beginHost();
            if (scanWanted) beginScan();
        }
        if (r == RADIO_UNAUTHORIZED) handler.postDelayed(this::refreshRadio, 1500);
    }

    /** Bluetooth went off: every connection is gone. */
    void radioLost()
    {
        for (Integer peer : new ArrayList<>(devices.keySet())) emit(EV_DISCONNECTED, peer);
        devices.clear(); peerOf.clear(); outbox.clear(); inFlight.clear(); mtuOf.clear();
        if (server != null) { try { server.close(); } catch (Exception ignored) { } }
        server = null; serviceAdded = false; advertising = false; scanning = false;
        if (gatt != null)
        {
            boolean wasReady = hostReady;
            try { gatt.close(); } catch (Exception ignored) { }
            gatt = null; hostReady = false; writes.clear(); writing = false;
            if (!explicitDisconnect) emit(wasReady ? EV_DISCONNECTED : EV_CONNECT_FAILED, 0);
        }
        updatePacketSize();
    }

    void updatePacketSize()
    {
        int size = 512;
        if (gatt != null && hostReady) size = Math.min(size, hostMtu - 3);
        for (Integer peer : devices.keySet())
        {
            Integer mtu = mtuOf.get(peer);
            size = Math.min(size, (mtu != null ? mtu : 23) - 3);
        }
        size = Math.max(20, size);
        if (size != maxPacket)
        {
            maxPacket = size;
            emit(EV_PACKET_SIZE, 0, 0, size, null, null, null);
        }
    }

    // ---------- Host ----------

    void beginHost()
    {
        if (!hostWanted || radio != RADIO_ON) return;
        BluetoothLeAdvertiser advertiser = adapter.getBluetoothLeAdvertiser();
        if (advertiser == null || !adapter.isMultipleAdvertisementSupported())
        {
            emit(EV_HOST_FAILED, 0, 0, 0, null, null, "noAdvertise");   // this phone can't host; it can still join
            hostWanted = false;
            return;
        }
        if (server == null)
        {
            server = manager.openGattServer(context, serverCallback);
            if (server == null) { emit(EV_HOST_FAILED, 0, 0, 0, null, null, "noServer"); return; }
            BluetoothGattService service = new BluetoothGattService(SERVICE, BluetoothGattService.SERVICE_TYPE_PRIMARY);
            toClient = new BluetoothGattCharacteristic(TO_CLIENT,
                BluetoothGattCharacteristic.PROPERTY_NOTIFY | BluetoothGattCharacteristic.PROPERTY_READ, BluetoothGattCharacteristic.PERMISSION_READ);
            toClient.addDescriptor(new BluetoothGattDescriptor(CCCD, BluetoothGattDescriptor.PERMISSION_READ | BluetoothGattDescriptor.PERMISSION_WRITE));
            BluetoothGattCharacteristic toHost = new BluetoothGattCharacteristic(TO_HOST,
                BluetoothGattCharacteristic.PROPERTY_WRITE | BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE, BluetoothGattCharacteristic.PERMISSION_WRITE);
            service.addCharacteristic(toClient);
            service.addCharacteristic(toHost);
            serviceAdded = false;
            if (!server.addService(service)) emit(EV_HOST_FAILED, 0, 0, 0, null, null, "addService");
            return;
        }
        if (serviceAdded) advertise();
    }

    void advertise()
    {
        BluetoothLeAdvertiser advertiser = adapter != null ? adapter.getBluetoothLeAdvertiser() : null;
        if (advertiser == null) return;
        long now = SystemClock.elapsedRealtime();
        if (advertising && now - lastAdvertise < 1000)
        {
            // Restarting the advertisement too often is refused by some phones: change it a moment later.
            handler.removeCallbacks(readvertise);
            handler.postDelayed(readvertise, 1000 - (now - lastAdvertise));
            return;
        }
        lastAdvertise = now;
        try { advertiser.stopAdvertising(advertiseCallback); } catch (Exception ignored) { }
        AdvertiseSettings settings = new AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(true)
            .setTimeout(0)
            .build();
        AdvertiseData data = new AdvertiseData.Builder().addServiceUuid(new ParcelUuid(SERVICE)).setIncludeDeviceName(false).setIncludeTxPowerLevel(false).build();
        AdvertiseData response = new AdvertiseData.Builder().addServiceData(BEACON_KEY, beacon).setIncludeDeviceName(false).setIncludeTxPowerLevel(false).build();
        advertiser.startAdvertising(settings, data, response, advertiseCallback);
    }

    final Runnable readvertise = () -> { if (hostWanted && serviceAdded) { lastAdvertise = 0; advertise(); } };

    final AdvertiseCallback advertiseCallback = new AdvertiseCallback()
    {
        @Override public void onStartSuccess(AdvertiseSettings settingsInEffect)
        {
            post(() ->
            {
                advertising = true;
                if (!hostAnnounced) { hostAnnounced = true; emit(EV_HOST_STARTED, 0); }
            });
        }

        @Override public void onStartFailure(final int errorCode)
        {
            post(() ->
            {
                if (errorCode == ADVERTISE_FAILED_ALREADY_STARTED) { advertising = true; if (!hostAnnounced) { hostAnnounced = true; emit(EV_HOST_STARTED, 0); } return; }
                advertising = false;
                emit(EV_HOST_FAILED, 0, 0, 0, null, null, "advertise" + errorCode);
            });
        }
    };

    void endHost()
    {
        hostWanted = false;
        handler.removeCallbacks(readvertise);
        BluetoothLeAdvertiser advertiser = adapter != null ? adapter.getBluetoothLeAdvertiser() : null;
        if (advertiser != null && radio == RADIO_ON) { try { advertiser.stopAdvertising(advertiseCallback); } catch (Exception ignored) { } }
        if (server != null)
        {
            for (BluetoothDevice d : devices.values()) { try { server.cancelConnection(d); } catch (Exception ignored) { } }
            try { server.close(); } catch (Exception ignored) { }
        }
        server = null; serviceAdded = false; advertising = false;
        devices.clear(); peerOf.clear(); outbox.clear(); inFlight.clear(); mtuOf.clear(); kicked.clear();
        updatePacketSize();
    }

    void kickPeer(int peer)
    {
        BluetoothDevice d = devices.remove(peer);
        if (d == null) return;
        peerOf.remove(d.getAddress());
        outbox.remove(peer); inFlight.remove(peer); mtuOf.remove(peer);
        kicked.add(d.getAddress());
        if (server != null) { try { server.cancelConnection(d); } catch (Exception ignored) { } }
        updatePacketSize();
    }

    int peerFor(BluetoothDevice device, boolean announce)
    {
        Integer known = peerOf.get(device.getAddress());
        if (known != null) return known;
        if (kicked.contains(device.getAddress())) return 0;
        int peer = nextPeer++;
        peerOf.put(device.getAddress(), peer);
        devices.put(peer, device);
        if (announce) emit(EV_CONNECTED, peer);
        updatePacketSize();
        return peer;
    }

    void forgetDevice(BluetoothDevice device, boolean announce)
    {
        Integer peer = peerOf.remove(device.getAddress());
        kicked.remove(device.getAddress());
        if (peer == null) return;
        devices.remove(peer); outbox.remove(peer); inFlight.remove(peer); mtuOf.remove(peer);
        if (announce) emit(EV_DISCONNECTED, peer);
        updatePacketSize();
    }

    final BluetoothGattServerCallback serverCallback = new BluetoothGattServerCallback()
    {
        @Override public void onServiceAdded(final int status, BluetoothGattService service)
        {
            post(() ->
            {
                if (status != BluetoothGatt.GATT_SUCCESS) { emit(EV_HOST_FAILED, 0, 0, 0, null, null, "service" + status); return; }
                serviceAdded = true;
                if (hostWanted) advertise();
            });
        }

        @Override public void onConnectionStateChange(final BluetoothDevice device, int status, final int newState)
        {
            post(() -> { if (newState == BluetoothProfile.STATE_DISCONNECTED) forgetDevice(device, true); });
        }

        @Override public void onMtuChanged(final BluetoothDevice device, final int mtu)
        {
            post(() ->
            {
                Integer peer = peerOf.get(device.getAddress());
                if (peer != null) { mtuOf.put(peer, mtu); updatePacketSize(); }
                else pendingMtu.put(device.getAddress(), mtu);
            });
        }

        @Override public void onDescriptorWriteRequest(final BluetoothDevice device, final int requestId, BluetoothGattDescriptor descriptor,
                                                       boolean preparedWrite, final boolean responseNeeded, int offset, final byte[] value)
        {
            post(() ->
            {
                if (responseNeeded && server != null) server.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null);
                boolean on = value != null && value.length > 0 && (value[0] & 1) != 0;
                if (on)
                {
                    kicked.remove(device.getAddress());   // subscribing again: a new connection
                    int peer = peerFor(device, true);
                    Integer mtu = pendingMtu.remove(device.getAddress());
                    if (mtu != null && peer != 0) { mtuOf.put(peer, mtu); updatePacketSize(); }
                }
                else forgetDevice(device, true);
            });
        }

        @Override public void onCharacteristicWriteRequest(final BluetoothDevice device, final int requestId, BluetoothGattCharacteristic characteristic,
                                                           boolean preparedWrite, final boolean responseNeeded, int offset, final byte[] value)
        {
            final boolean ours = TO_HOST.equals(characteristic.getUuid());
            post(() ->
            {
                if (responseNeeded && server != null) server.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, 0, null);
                if (!ours || value == null) return;
                int peer = peerFor(device, true);
                if (peer != 0) emit(EV_DATA, peer, 0, 0, null, value.clone(), null);
            });
        }

        @Override public void onNotificationSent(final BluetoothDevice device, int status)
        {
            post(() ->
            {
                Integer peer = peerOf.get(device.getAddress());
                if (peer == null) return;
                inFlight.put(peer, false);
                pump(peer);
            });
        }
    };

    final Map<String, Integer> pendingMtu = new HashMap<>();

    void sendNow(int peer, byte[] data)
    {
        if (peer == 0) { write(data); return; }
        if (!devices.containsKey(peer)) return;
        ArrayDeque<byte[]> q = outbox.get(peer);
        if (q == null) { q = new ArrayDeque<>(); outbox.put(peer, q); }
        q.addLast(data);
        // Too much waiting (a phone that has stopped listening): drop the oldest whole messages (the framing's last flag ends one).
        while (q.size() > QUEUE_LIMIT)
            while (!q.isEmpty()) { byte[] dropped = q.pollFirst(); if (dropped.length > 0 && (dropped[0] & 0x80) != 0) break; }
        pump(peer);
    }

    @SuppressWarnings("deprecation")
    void pump(int peer)
    {
        Boolean busy = inFlight.get(peer);
        if (busy != null && busy) return;
        ArrayDeque<byte[]> q = outbox.get(peer);
        BluetoothDevice device = devices.get(peer);
        if (q == null || q.isEmpty() || device == null || server == null) return;
        byte[] packet = q.pollFirst();
        boolean ok;
        if (Build.VERSION.SDK_INT >= 33) ok = server.notifyCharacteristicChanged(device, toClient, false, packet) == BluetoothGatt.GATT_SUCCESS;
        else
        {
            toClient.setValue(packet);
            ok = server.notifyCharacteristicChanged(device, toClient, false);
        }
        if (ok) inFlight.put(peer, true);
        else
        {
            q.addFirst(packet);   // the stack is busy: try again shortly
            final int p = peer;
            handler.postDelayed(() -> { inFlight.put(p, false); pump(p); }, 8);
            inFlight.put(peer, true);
        }
    }

    // ---------- Scanning ----------

    void beginScan()
    {
        if (!scanWanted || scanning || radio != RADIO_ON) return;
        BluetoothLeScanner scanner = adapter.getBluetoothLeScanner();
        if (scanner == null) return;
        List<ScanFilter> filters = Collections.singletonList(new ScanFilter.Builder().setServiceUuid(new ParcelUuid(SERVICE)).build());
        ScanSettings settings = new ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build();
        try { scanner.startScan(filters, settings, scanCallback); scanning = true; }
        catch (Exception e) { scanning = false; }
    }

    void endScan()
    {
        if (!scanning) return;
        scanning = false;
        BluetoothLeScanner scanner = adapter != null ? adapter.getBluetoothLeScanner() : null;
        if (scanner != null && radio == RADIO_ON) { try { scanner.stopScan(scanCallback); } catch (Exception ignored) { } }
    }

    final ScanCallback scanCallback = new ScanCallback()
    {
        @Override public void onScanResult(int callbackType, final ScanResult result) { post(() -> found(result)); }

        @Override public void onBatchScanResults(final List<ScanResult> results) { post(() -> { for (ScanResult r : results) found(r); }); }

        @Override public void onScanFailed(int errorCode)
        {
            post(() ->
            {
                scanning = false;
                // (scanning too often, or the stack is busy: try again in a moment)
                handler.postDelayed(DtsCoopBle.this::beginScan, 2000);
            });
        }
    };

    void found(ScanResult result)
    {
        String address = result.getDevice().getAddress();
        long now = SystemClock.elapsedRealtime();
        Long last = lastReport.get(address);
        if (last != null && now - last < 250) return;   // a few reports a second are plenty
        lastReport.put(address, now);
        ScanRecord record = result.getScanRecord();
        byte[] data = record != null ? record.getServiceData(BEACON_KEY) : null;
        String name = record != null ? record.getDeviceName() : null;
        emit(EV_FOUND, 0, 0, result.getRssi(), address, data, name);
    }

    // ---------- Client ----------

    void connectTo(final String address)
    {
        dropHost();
        if (radio != RADIO_ON || adapter == null || !BluetoothAdapter.checkBluetoothAddress(address))
        {
            emit(EV_CONNECT_FAILED, 0, 0, 0, address, null, "unavailable");
            return;
        }
        BluetoothDevice device = adapter.getRemoteDevice(address);
        explicitDisconnect = false;
        hostReady = false;
        hostMtu = 23;
        writing = false;
        writes.clear();
        gatt = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE);
        if (gatt == null) { emit(EV_CONNECT_FAILED, 0, 0, 0, address, null, "connectGatt"); return; }
        final int token = ++connectToken;
        final BluetoothGatt attempt = gatt;
        handler.postDelayed(() ->
        {
            if (connectToken != token || hostReady || gatt != attempt) return;
            explicitDisconnect = true;
            try { attempt.disconnect(); attempt.close(); } catch (Exception ignored) { }
            gatt = null;
            emit(EV_CONNECT_FAILED, 0, 0, 0, address, null, "timeout");
        }, 10000);
    }

    /** Hang up on the host without telling the game (it asked). */
    void dropHost()
    {
        if (gatt == null) return;
        explicitDisconnect = true;
        try { gatt.disconnect(); gatt.close(); } catch (Exception ignored) { }
        gatt = null;
        hostReady = false;
        hostWrite = null;
        writes.clear();
        writing = false;
        updatePacketSize();
    }

    void hostFailed(BluetoothGatt g, String why)
    {
        if (g != gatt) return;
        explicitDisconnect = true;
        try { g.disconnect(); g.close(); } catch (Exception ignored) { }
        gatt = null;
        emit(EV_CONNECT_FAILED, 0, 0, 0, null, null, why);
    }

    final BluetoothGattCallback gattCallback = new BluetoothGattCallback()
    {
        @Override public void onConnectionStateChange(final BluetoothGatt g, final int status, final int newState)
        {
            post(() ->
            {
                if (g != gatt) { try { g.close(); } catch (Exception ignored) { } return; }
                if (newState == BluetoothProfile.STATE_CONNECTED)
                {
                    g.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH);
                    if (!g.requestMtu(247)) g.discoverServices();   // onMtuChanged discovers once the MTU is agreed
                }
                else if (newState == BluetoothProfile.STATE_DISCONNECTED)
                {
                    boolean wasReady = hostReady;
                    try { g.close(); } catch (Exception ignored) { }
                    gatt = null; hostReady = false; hostWrite = null; writes.clear(); writing = false;
                    updatePacketSize();
                    if (!explicitDisconnect) emit(wasReady ? EV_DISCONNECTED : EV_CONNECT_FAILED, 0, 0, 0, null, null, "status" + status);
                }
            });
        }

        @Override public void onMtuChanged(final BluetoothGatt g, final int mtu, int status)
        {
            post(() ->
            {
                if (g != gatt) return;
                hostMtu = Math.max(23, mtu);
                if (!hostReady) g.discoverServices();
                else updatePacketSize();
            });
        }

        @SuppressWarnings("deprecation")
        @Override public void onServicesDiscovered(final BluetoothGatt g, final int status)
        {
            post(() ->
            {
                if (g != gatt) return;
                BluetoothGattService service = g.getService(SERVICE);
                if (status != BluetoothGatt.GATT_SUCCESS || service == null) { hostFailed(g, "noService"); return; }
                BluetoothGattCharacteristic notify = service.getCharacteristic(TO_CLIENT);
                hostWrite = service.getCharacteristic(TO_HOST);
                if (notify == null || hostWrite == null) { hostFailed(g, "noCharacteristics"); return; }
                g.setCharacteristicNotification(notify, true);
                BluetoothGattDescriptor cccd = notify.getDescriptor(CCCD);
                if (cccd == null) { hostFailed(g, "noCccd"); return; }
                boolean ok;
                if (Build.VERSION.SDK_INT >= 33) ok = g.writeDescriptor(cccd, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE) == BluetoothGatt.GATT_SUCCESS;
                else { cccd.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE); ok = g.writeDescriptor(cccd); }
                if (!ok) hostFailed(g, "subscribe");
            });
        }

        @Override public void onDescriptorWrite(final BluetoothGatt g, BluetoothGattDescriptor descriptor, final int status)
        {
            post(() ->
            {
                if (g != gatt) return;
                if (status != BluetoothGatt.GATT_SUCCESS) { hostFailed(g, "subscribe" + status); return; }
                if (hostReady) return;
                hostReady = true;
                updatePacketSize();
                emit(EV_CONNECTED, 0);
                pumpWrites();
            });
        }

        @Override public void onCharacteristicChanged(final BluetoothGatt g, BluetoothGattCharacteristic characteristic, final byte[] value)
        {
            // Android 13 and up.
            final byte[] copy = value != null ? value.clone() : null;
            post(() -> { if (g == gatt && copy != null) emit(EV_DATA, 0, 0, 0, null, copy, null); });
        }

        @SuppressWarnings("deprecation")
        @Override public void onCharacteristicChanged(final BluetoothGatt g, BluetoothGattCharacteristic characteristic)
        {
            if (Build.VERSION.SDK_INT >= 33) return;   // (the call above has it)
            byte[] v = characteristic.getValue();
            final byte[] copy = v != null ? v.clone() : null;
            post(() -> { if (g == gatt && copy != null) emit(EV_DATA, 0, 0, 0, null, copy, null); });
        }

        @Override public void onCharacteristicWrite(final BluetoothGatt g, BluetoothGattCharacteristic characteristic, int status)
        {
            post(() -> { if (g != gatt) return; writing = false; pumpWrites(); });
        }
    };

    void write(byte[] data)
    {
        if (gatt == null || !hostReady) return;
        writes.addLast(data);
        while (writes.size() > QUEUE_LIMIT) writes.pollFirst();
        pumpWrites();
    }

    @SuppressWarnings("deprecation")
    void pumpWrites()
    {
        if (writing || gatt == null || hostWrite == null || writes.isEmpty()) return;
        byte[] packet = writes.pollFirst();
        boolean ok;
        if (Build.VERSION.SDK_INT >= 33)
            ok = gatt.writeCharacteristic(hostWrite, packet, BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE) == BluetoothGatt.GATT_SUCCESS;
        else
        {
            hostWrite.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE);
            hostWrite.setValue(packet);
            ok = gatt.writeCharacteristic(hostWrite);
        }
        if (ok) writing = true;
        else
        {
            writes.addFirst(packet);   // busy: try again shortly
            writing = true;
            handler.postDelayed(() -> { writing = false; pumpWrites(); }, 8);
        }
    }
}
