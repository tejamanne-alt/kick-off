namespace DribbleToSchool.Coop.Net
{
    /// <summary>The phone's Bluetooth, as far as the game is concerned.</summary>
    public enum RadioState : byte
    {
        /// <summary>Not known yet (the native side is still starting).</summary>
        Unknown = 0,
        /// <summary>This device has no Bluetooth LE, or can't be a host (some Android phones can't advertise).</summary>
        Unsupported = 1,
        /// <summary>The player has not allowed the game to use Bluetooth (or nearby devices, on Android 12 and up).</summary>
        Unauthorized = 2,
        /// <summary>Bluetooth is switched off.</summary>
        Off = 3,
        /// <summary>Ready to host, scan and connect.</summary>
        On = 4,
    }

    public enum LinkEventType : byte
    {
        /// <summary>The radio changed state (<see cref="LinkEvent.state"/>).</summary>
        Radio = 1,
        /// <summary>Scanning found (or heard again) a host: <see cref="LinkEvent.address"/>, <see cref="LinkEvent.beacon"/>, <see cref="LinkEvent.rssi"/>.</summary>
        Found = 2,
        /// <summary>Host role: a player's phone connected (<see cref="LinkEvent.peer"/>). Client role: connected to the host (peer 0).</summary>
        Connected = 3,
        /// <summary>The connection to <see cref="LinkEvent.peer"/> is gone (peer 0: the host, in the client role).</summary>
        Disconnected = 4,
        /// <summary>A packet from <see cref="LinkEvent.peer"/>.</summary>
        Data = 5,
        /// <summary>Hosting started (advertising and accepting players).</summary>
        HostStarted = 6,
        /// <summary>Hosting could not start (<see cref="LinkEvent.error"/>).</summary>
        HostFailed = 7,
        /// <summary>A connection attempt to a host failed (<see cref="LinkEvent.error"/>).</summary>
        ConnectFailed = 8,
        /// <summary>The link's packet size changed (<see cref="LinkEvent.rssi"/> holds the new payload size).</summary>
        PacketSize = 9,
    }

    /// <summary>Something that happened on the link (see <see cref="LinkEventType"/>).</summary>
    public struct LinkEvent
    {
        public LinkEventType type;
        public int peer;
        public string address;
        public byte[] data;
        public RoomBeacon beacon;
        public int rssi;
        public RadioState state;
        public string error;
    }

    /// <summary>
    /// The radio under a co-op session: Bluetooth LE on a phone (Coop/Transport: CoreBluetooth on iOS, android.bluetooth.le
    /// on Android), or an in-memory radio for the editor's bots and the tests (<see cref="InMemoryRadio"/>). The host is a
    /// GATT server that advertises; each other player connects to it as a client (a star: BLE has no mesh between phones of
    /// both kinds). A link moves raw packets of at most <see cref="MaxPacket"/> bytes, in order, per connection; the session
    /// does everything else (framing, messages, timeouts, the clock).
    /// </summary>
    public interface ICoopLink
    {
        RadioState State { get; }

        /// <summary>The largest packet the link carries now (bytes of payload; at least 20).</summary>
        int MaxPacket { get; }

        /// <summary>Start advertising <paramref name="beacon"/> and accepting players. Answered by HostStarted or HostFailed.</summary>
        void StartHost(RoomBeacon beacon);
        /// <summary>Change what the advertisement says (players, phase).</summary>
        void UpdateBeacon(RoomBeacon beacon);
        /// <summary>Stop advertising and drop every player.</summary>
        void StopHost();
        /// <summary>Host role: drop one player's connection.</summary>
        void Kick(int peer);

        /// <summary>Look for hosts (Found events) until <see cref="StopScan"/>. Works beside hosting.</summary>
        void StartScan();
        void StopScan();
        /// <summary>Client role: connect to the host at <paramref name="address"/> (one at a time). Answered by Connected or ConnectFailed.</summary>
        void Connect(string address);
        /// <summary>Client role: leave the host.</summary>
        void Disconnect();

        /// <summary>Send one packet: to the host (peer 0) in the client role, or to a player's peer in the host role.</summary>
        void Send(int peer, byte[] packet);

        /// <summary>The next thing that happened, if any (call until false, once a frame).</summary>
        bool Poll(out LinkEvent e);

        /// <summary>Let go of the radio (the session is over).</summary>
        void Shutdown();
    }
}
