using System;
using System.Collections.Generic;
using DribbleToSchool.Coop.Net;
using UnityEngine;

namespace DribbleToSchool.Coop.Transport
{
    /// <summary>
    /// The co-op link on Android: android.bluetooth.le through Plugins/Android/DtsCoopBle.java (one handler thread; the game
    /// polls its events once a frame). Bluetooth needs runtime permissions (nearby devices on Android 12 and up, location
    /// before): <see cref="RequestPermissions"/> asks for them; until they are given the radio reads Unauthorized. The host
    /// puts its lobby's beacon in its scan response as service data (Android can't advertise a custom name). Each hosting
    /// run and connection attempt gets a number the plugin writes into its events, and late events are dropped here
    /// (<see cref="LinkEventFilter"/>, as on iOS). The plugin class is kept from R8 by Editor/AndroidBluetoothPermissions:
    /// it is reached only by name.
    /// </summary>
    public sealed class AndroidBleLink : ICoopLink
    {
        const string PluginClass = "com.dribbletoschool.coop.DtsCoopBle";

        readonly List<LinkEvent> pending = new List<LinkEvent>();
        readonly LinkEventFilter filter = new LinkEventFilter();
        int next;
        RadioState state = RadioState.Unknown;
        int maxPacket = CoopFraming.MinPacket;
        AndroidJavaObject plugin = null;   // (made in the Android player only)
        byte[] unpacked = new byte[4096];

        public AndroidBleLink()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            try
            {
                using (var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
                using (var activity = player.GetStatic<AndroidJavaObject>("currentActivity"))
                using (var cls = new AndroidJavaClass(PluginClass))
                    plugin = cls.CallStatic<AndroidJavaObject>("init", activity);
                if (plugin == null) state = RadioState.Unsupported;   // (the plugin couldn't start: it logged why)
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Co-op] Bluetooth plugin unavailable: " + e.Message);
                state = RadioState.Unsupported;
            }
#else
            state = RadioState.Unsupported;
#endif
        }

        public RadioState State { get { return state; } }
        public int MaxPacket { get { return maxPacket; } }

        void Call(string method, params object[] args)
        {
            if (plugin == null) return;
            try { plugin.Call(method, args); }
            catch (Exception e) { Debug.LogWarning("[Co-op] " + method + ": " + e.Message); }
        }

        static sbyte[] Signed(byte[] b)
        {
            var s = new sbyte[b != null ? b.Length : 0];
            if (b != null) Buffer.BlockCopy(b, 0, s, 0, b.Length);
            return s;
        }

        // (each hosting run and connection attempt gets a number its events carry: see LinkEventFilter. It goes as an int:
        // AndroidJavaObject finds the Java method by the types of the arguments, and a byte would look for startHost(byte[], byte).)
        public void StartHost(RoomBeacon beacon) { Call("startHost", Signed(beacon.ToBytes()), (int)filter.StartHost()); }
        public void UpdateBeacon(RoomBeacon beacon) { Call("updateBeacon", Signed(beacon.ToBytes())); }
        public void StopHost() { filter.StopHost(); Call("stopHost"); }
        public void Kick(int peer) { filter.Kick(peer); Call("kick", peer); }
        public void StartScan() { Call("startScan"); }
        public void StopScan() { Call("stopScan"); }
        public void Connect(string address) { Call("connect", address ?? "", (int)filter.Connect()); }
        public void Disconnect() { filter.Disconnect(); Call("disconnect"); }

        public void Send(int peer, byte[] packet)
        {
            if (packet != null && packet.Length > 0) Call("send", peer, Signed(packet));
        }

        public bool Poll(out LinkEvent e)
        {
            while (true)
            {
                if (next >= pending.Count)
                {
                    pending.Clear();
                    next = 0;
                    if (plugin != null)
                    {
                        sbyte[] packed = null;
                        try { packed = plugin.Call<sbyte[]>("poll"); }
                        catch (Exception ex) { Debug.LogWarning("[Co-op] poll: " + ex.Message); }
                        if (packed != null && packed.Length > 0)
                        {
                            if (unpacked.Length < packed.Length) unpacked = new byte[packed.Length * 2];
                            Buffer.BlockCopy(packed, 0, unpacked, 0, packed.Length);
                            NativeEvents.Decode(unpacked, packed.Length, pending);
                        }
                    }
                }
                if (next >= pending.Count)
                {
                    e = new LinkEvent();
                    return false;
                }
                e = pending[next++];
                if (!filter.Pass(ref e)) continue;
                if (e.type == LinkEventType.Radio) state = e.state;
                else if (e.type == LinkEventType.PacketSize) maxPacket = Math.Max(CoopFraming.MinPacket, e.rssi);
                return true;
            }
        }

        public void Shutdown()
        {
            filter.StopHost();
            filter.Disconnect();
            Call("shutdown");
        }

        /// <summary>Below Android 12, scanning finds nothing while Location is off (the Join screen says so).</summary>
        public bool LocationNeededAndOff
        {
            get
            {
                if (plugin == null) return false;
                try { return plugin.Call<bool>("locationNeededAndOff"); }
                catch (Exception) { return false; }
            }
        }

        /// <summary>Ask for what Bluetooth needs on this Android version; <paramref name="done"/> gets whether all of it was given.</summary>
        public static void RequestPermissions(Action<bool> done)
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            string[] needed;
            try
            {
                using (var cls = new AndroidJavaClass(PluginClass)) needed = cls.CallStatic<string[]>("neededPermissions");
            }
            catch (Exception) { if (done != null) done(false); return; }
            var missing = new List<string>();
            foreach (string p in needed)
                if (!UnityEngine.Android.Permission.HasUserAuthorizedPermission(p)) missing.Add(p);
            if (missing.Count == 0) { if (done != null) done(true); return; }
            int answers = 0;
            bool all = true;
            var callbacks = new UnityEngine.Android.PermissionCallbacks();
            Action<string, bool> answered = (name, granted) =>
            {
                all &= granted;
                if (++answers == missing.Count && done != null) done(all);
            };
            callbacks.PermissionGranted += name => answered(name, true);
            callbacks.PermissionDenied += name => answered(name, false);
            callbacks.PermissionDeniedAndDontAskAgain += name => answered(name, false);
            UnityEngine.Android.Permission.RequestUserPermissions(missing.ToArray(), callbacks);
#else
            if (done != null) done(true);
#endif
        }

        /// <summary>The game's page in Android's settings (to allow Bluetooth after saying no).</summary>
        public void OpenSettings() { WithActivity("openSettings"); }

        /// <summary>Android's Bluetooth settings (to switch it on).</summary>
        public void OpenBluetoothSettings() { WithActivity("openBluetoothSettings"); }

        void WithActivity(string method)
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            if (plugin == null) return;
            try
            {
                using (var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
                using (var activity = player.GetStatic<AndroidJavaObject>("currentActivity"))
                    plugin.Call(method, activity);
            }
            catch (Exception e) { Debug.LogWarning("[Co-op] " + method + ": " + e.Message); }
#endif
        }
    }
}
