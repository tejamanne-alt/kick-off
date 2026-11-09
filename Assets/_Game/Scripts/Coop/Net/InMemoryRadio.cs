using System;
using System.Collections.Generic;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>
    /// A pretend Bluetooth for several "phones" in one process: the edit-mode tests and the editor's practice bots run real
    /// co-op sessions on it. It behaves like the BLE links do: hosts advertise and scanners hear them every
    /// <see cref="ScanIntervalMs"/>, packets arrive in order after <see cref="LatencyMs"/>, a phone whose Bluetooth is switched
    /// off loses every connection at once, and two phones that go out of range notice only after the link's supervision
    /// timeout (<see cref="SupervisionTimeoutMs"/>). Calling Disconnect, StopHost or Kick raises no event on the caller's side,
    /// only on the other end (the native links do the same).
    /// </summary>
    public sealed class InMemoryRadio
    {
        readonly ICoopClock clock;
        readonly List<InMemoryLink> devices = new List<InMemoryLink>();
        readonly HashSet<long> outOfRange = new HashSet<long>();

        public double LatencyMs = 25;
        public double ScanIntervalMs = 250;
        public double SupervisionTimeoutMs = 2000;
        /// <summary>The packet size every link reports.</summary>
        public int PacketSize = 20;
        /// <summary>This many connection attempts fail outright before one gets through (as Android's status 133 often does).</summary>
        public int FailConnects;

        public InMemoryRadio(ICoopClock clock)
        {
            this.clock = clock;
        }

        public double Now { get { return clock.NowMs; } }

        public InMemoryLink CreateDevice(string address)
        {
            var link = new InMemoryLink(this, address);
            devices.Add(link);
            return link;
        }

        internal IEnumerable<InMemoryLink> Devices { get { return devices; } }

        static long Pair(InMemoryLink a, InMemoryLink b)
        {
            int x = Math.Min(a.Id, b.Id), y = Math.Max(a.Id, b.Id);
            return ((long)x << 32) | (uint)y;
        }

        internal bool CanHear(InMemoryLink a, InMemoryLink b)
        {
            return a != null && b != null && a.Powered && b.Powered && !outOfRange.Contains(Pair(a, b));
        }

        /// <summary>Switch a phone's Bluetooth on or off. Off drops all its connections (the other ends hear at once).</summary>
        public void SetPower(InMemoryLink link, bool on)
        {
            if (link.Powered == on) return;
            link.Powered = on;
            if (!on) link.DropEverything(0);
            link.Enqueue(new LinkEvent { type = LinkEventType.Radio, state = on ? RadioState.On : RadioState.Off }, 0);
        }

        /// <summary>Put two phones in or out of each other's range. Out of range, both ends notice after the supervision timeout.</summary>
        public void SetRange(InMemoryLink a, InMemoryLink b, bool inRange)
        {
            long key = Pair(a, b);
            if (inRange) { outOfRange.Remove(key); return; }
            if (!outOfRange.Add(key)) return;
            a.DropConnectionWith(b, SupervisionTimeoutMs);
        }

        /// <summary>Take a phone away from every other one (it walked off).</summary>
        public void Isolate(InMemoryLink link)
        {
            foreach (var other in devices)
                if (other != link) SetRange(link, other, false);
        }

        /// <summary>Bring a phone back in range of every other one.</summary>
        public void Rejoin(InMemoryLink link)
        {
            foreach (var other in devices)
                if (other != link) SetRange(link, other, true);
        }

        internal InMemoryLink ByAddress(string address)
        {
            foreach (var d in devices)
                if (d.Address == address) return d;
            return null;
        }
    }

    /// <summary>One phone on an <see cref="InMemoryRadio"/>.</summary>
    public sealed class InMemoryLink : ICoopLink
    {
        static int nextId;

        struct Timed
        {
            public double at;
            public LinkEvent e;
        }

        readonly InMemoryRadio radio;
        readonly List<Timed> queue = new List<Timed>();
        // Host role: my peer number for each connected client, and back.
        readonly Dictionary<int, InMemoryLink> peers = new Dictionary<int, InMemoryLink>();
        int nextPeer = 1;
        double nextScanReport;

        internal InMemoryLink(InMemoryRadio radio, string address)
        {
            this.radio = radio;
            Address = address;
            Id = ++nextId;
            Powered = true;
            Enqueue(new LinkEvent { type = LinkEventType.Radio, state = RadioState.On }, 0);
        }

        public string Address { get; private set; }
        internal int Id { get; private set; }
        internal bool Powered { get; set; }
        public bool Hosting { get; private set; }
        public bool Scanning { get; private set; }
        public RoomBeacon Beacon { get; private set; }
        /// <summary>Client role: the host this phone is connected to (or connecting to), and my peer number there.</summary>
        internal InMemoryLink Host { get; private set; }
        internal int PeerAtHost { get; private set; }
        /// <summary>Packets sent, for tests that check traffic stays modest.</summary>
        public int PacketsSent { get; private set; }

        public RadioState State { get { return Powered ? RadioState.On : RadioState.Off; } }
        public int MaxPacket { get { return radio.PacketSize; } }

        internal void Enqueue(LinkEvent e, double delay)
        {
            queue.Add(new Timed { at = radio.Now + delay, e = e });
        }

        public void StartHost(RoomBeacon beacon)
        {
            if (!Powered)
            {
                Enqueue(new LinkEvent { type = LinkEventType.HostFailed, error = "off" }, 0);
                return;
            }
            Hosting = true;
            Beacon = beacon;
            Enqueue(new LinkEvent { type = LinkEventType.HostStarted }, radio.LatencyMs);
        }

        public void UpdateBeacon(RoomBeacon beacon) { Beacon = beacon; }

        public void StopHost()
        {
            if (!Hosting) return;
            Hosting = false;
            foreach (var kv in new List<KeyValuePair<int, InMemoryLink>>(peers))
                kv.Value.LoseHost(this, radio.LatencyMs);
            peers.Clear();
        }

        public void Kick(int peer)
        {
            InMemoryLink client;
            if (!peers.TryGetValue(peer, out client)) return;
            peers.Remove(peer);
            client.LoseHost(this, radio.LatencyMs);
        }

        public void StartScan() { Scanning = true; nextScanReport = radio.Now; }
        public void StopScan() { Scanning = false; }

        public void Connect(string address)
        {
            if (Host != null) Disconnect();
            var host = radio.ByAddress(address);
            if (radio.FailConnects > 0 || host == null || !host.Hosting || !radio.CanHear(this, host))
            {
                if (radio.FailConnects > 0) radio.FailConnects--;
                Enqueue(new LinkEvent { type = LinkEventType.ConnectFailed, error = "unreachable" }, radio.LatencyMs * 4);
                return;
            }
            int peer = host.nextPeer++;
            host.peers[peer] = this;
            Host = host;
            PeerAtHost = peer;
            host.Enqueue(new LinkEvent { type = LinkEventType.Connected, peer = peer }, radio.LatencyMs * 2);
            Enqueue(new LinkEvent { type = LinkEventType.Connected, peer = 0 }, radio.LatencyMs * 2);
        }

        public void Disconnect()
        {
            if (Host == null) return;
            var host = Host;
            host.peers.Remove(PeerAtHost);
            host.Enqueue(new LinkEvent { type = LinkEventType.Disconnected, peer = PeerAtHost }, radio.LatencyMs);
            Host = null;
            // (no event on this side: the caller knows)
            queue.RemoveAll(t => t.e.type == LinkEventType.Data || t.e.type == LinkEventType.Connected);
        }

        public void Send(int peer, byte[] packet)
        {
            if (packet == null || !Powered) return;
            if (packet.Length > MaxPacket) throw new ArgumentException("packet larger than the link's MaxPacket");
            PacketsSent++;
            if (peer == 0)
            {
                if (Host == null || !radio.CanHear(this, Host)) return;
                Host.Enqueue(new LinkEvent { type = LinkEventType.Data, peer = PeerAtHost, data = (byte[])packet.Clone() }, radio.LatencyMs);
            }
            else
            {
                InMemoryLink client;
                if (!peers.TryGetValue(peer, out client) || !radio.CanHear(this, client)) return;
                client.Enqueue(new LinkEvent { type = LinkEventType.Data, peer = 0, data = (byte[])packet.Clone() }, radio.LatencyMs);
            }
        }

        public bool Poll(out LinkEvent e)
        {
            if (Scanning && Powered && radio.Now >= nextScanReport)
            {
                nextScanReport = radio.Now + radio.ScanIntervalMs;
                foreach (var d in radio.Devices)
                    if (d != this && d.Hosting && radio.CanHear(this, d))
                        queue.Add(new Timed { at = radio.Now, e = new LinkEvent { type = LinkEventType.Found, address = d.Address, beacon = d.Beacon, rssi = -60 } });
            }
            int best = -1;
            for (int i = 0; i < queue.Count; i++)
                if (queue[i].at <= radio.Now && (best < 0 || queue[i].at < queue[best].at)) best = i;
            if (best < 0)
            {
                e = new LinkEvent();
                return false;
            }
            e = queue[best].e;
            queue.RemoveAt(best);
            return true;
        }

        public void Shutdown()
        {
            StopHost();
            Disconnect();
            StopScan();
        }

        /// <summary>The host side went: tell this client after <paramref name="delay"/>.</summary>
        internal void LoseHost(InMemoryLink host, double delay)
        {
            if (Host != host) return;
            Host = null;
            Enqueue(new LinkEvent { type = LinkEventType.Disconnected, peer = 0 }, delay);
        }

        /// <summary>This phone lost its radio: every connection drops, the other ends hear after <paramref name="delay"/>.</summary>
        internal void DropEverything(double delay)
        {
            if (Host != null)
            {
                var host = Host;
                host.peers.Remove(PeerAtHost);
                host.Enqueue(new LinkEvent { type = LinkEventType.Disconnected, peer = PeerAtHost }, delay);
                Host = null;
            }
            foreach (var kv in peers) kv.Value.LoseHost(this, delay);
            peers.Clear();
            Hosting = false;
            Scanning = false;
            queue.RemoveAll(t => t.e.type == LinkEventType.Data);
        }

        /// <summary>Out of range of <paramref name="other"/>: any connection between them drops on both ends after <paramref name="delay"/>.</summary>
        internal void DropConnectionWith(InMemoryLink other, double delay)
        {
            if (Host == other)
            {
                other.peers.Remove(PeerAtHost);
                other.Enqueue(new LinkEvent { type = LinkEventType.Disconnected, peer = PeerAtHost }, delay);
                Host = null;
                Enqueue(new LinkEvent { type = LinkEventType.Disconnected, peer = 0 }, delay);
            }
            else if (other.Host == this) other.DropConnectionWith(this, delay);
        }
    }
}
