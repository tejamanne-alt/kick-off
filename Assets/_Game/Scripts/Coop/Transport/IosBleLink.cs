using System.Collections.Generic;
using System.Runtime.InteropServices;
using DribbleToSchool.Coop.Net;

namespace DribbleToSchool.Coop.Transport
{
    /// <summary>
    /// The co-op link on an iPhone or iPad: CoreBluetooth through Plugins/iOS/DTSCoopBLE.mm. Creating it starts Bluetooth,
    /// which asks the player for permission the first time (Info.plist's NSBluetoothAlwaysUsageDescription, set by
    /// Editor/IosPostBuild). The host advertises its lobby's beacon as its local name (iOS can't advertise service data).
    /// </summary>
    public sealed class IosBleLink : ICoopLink
    {
#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")] static extern void DTSCoop_Init();
        [DllImport("__Internal")] static extern void DTSCoop_StartHost(string localName, int gen);
        [DllImport("__Internal")] static extern void DTSCoop_UpdateBeacon(string localName);
        [DllImport("__Internal")] static extern void DTSCoop_StopHost();
        [DllImport("__Internal")] static extern void DTSCoop_Kick(int peer);
        [DllImport("__Internal")] static extern void DTSCoop_StartScan();
        [DllImport("__Internal")] static extern void DTSCoop_StopScan();
        [DllImport("__Internal")] static extern void DTSCoop_Connect(string address, int gen);
        [DllImport("__Internal")] static extern void DTSCoop_Disconnect();
        [DllImport("__Internal")] static extern void DTSCoop_Send(int peer, byte[] data, int length);
        [DllImport("__Internal")] static extern int DTSCoop_Poll(byte[] buffer, int capacity);
        [DllImport("__Internal")] static extern void DTSCoop_Shutdown();
        [DllImport("__Internal")] static extern void DTSCoop_OpenSettings();
#else
        // (in the editor and on other platforms there is no CoreBluetooth: the calls do nothing)
        static void DTSCoop_Init() { }
        static void DTSCoop_StartHost(string localName, int gen) { }
        static void DTSCoop_UpdateBeacon(string localName) { }
        static void DTSCoop_StopHost() { }
        static void DTSCoop_Kick(int peer) { }
        static void DTSCoop_StartScan() { }
        static void DTSCoop_StopScan() { }
        static void DTSCoop_Connect(string address, int gen) { }
        static void DTSCoop_Disconnect() { }
        static void DTSCoop_Send(int peer, byte[] data, int length) { }
        static int DTSCoop_Poll(byte[] buffer, int capacity) { return 0; }
        static void DTSCoop_Shutdown() { }
        static void DTSCoop_OpenSettings() { }
#endif

        readonly byte[] pollBuffer = new byte[65536];
        readonly List<LinkEvent> pending = new List<LinkEvent>();
        readonly LinkEventFilter filter = new LinkEventFilter();
        int next;
        RadioState state = RadioState.Unknown;
        int maxPacket = CoopFraming.MinPacket;

        public IosBleLink()
        {
            DTSCoop_Init();
        }

        public RadioState State { get { return state; } }
        public int MaxPacket { get { return maxPacket; } }

        // (each hosting run and connection attempt gets a number its events carry: see LinkEventFilter)
        public void StartHost(RoomBeacon beacon) { DTSCoop_StartHost(beacon.ToLocalName(), filter.StartHost()); }
        public void UpdateBeacon(RoomBeacon beacon) { DTSCoop_UpdateBeacon(beacon.ToLocalName()); }
        public void StopHost() { filter.StopHost(); DTSCoop_StopHost(); }
        public void Kick(int peer) { filter.Kick(peer); DTSCoop_Kick(peer); }
        public void StartScan() { DTSCoop_StartScan(); }
        public void StopScan() { DTSCoop_StopScan(); }
        public void Connect(string address) { DTSCoop_Connect(address ?? "", filter.Connect()); }
        public void Disconnect() { filter.Disconnect(); DTSCoop_Disconnect(); }

        public void Send(int peer, byte[] packet)
        {
            if (packet != null && packet.Length > 0) DTSCoop_Send(peer, packet, packet.Length);
        }

        public bool Poll(out LinkEvent e)
        {
            while (true)
            {
                if (next >= pending.Count)
                {
                    pending.Clear();
                    next = 0;
                    int n = DTSCoop_Poll(pollBuffer, pollBuffer.Length);
                    if (n > 0) NativeEvents.Decode(pollBuffer, n, pending);
                }
                if (next >= pending.Count)
                {
                    e = new LinkEvent();
                    return false;
                }
                e = pending[next++];
                if (!filter.Pass(ref e)) continue;
                if (e.type == LinkEventType.Radio) state = e.state;
                else if (e.type == LinkEventType.PacketSize) maxPacket = System.Math.Max(CoopFraming.MinPacket, e.rssi);
                return true;
            }
        }

        public void Shutdown()
        {
            filter.StopHost();
            filter.Disconnect();
            DTSCoop_Shutdown();
        }

        /// <summary>The game's page in the Settings app (to allow Bluetooth after saying no).</summary>
        public static void OpenSettings() { DTSCoop_OpenSettings(); }
    }
}
