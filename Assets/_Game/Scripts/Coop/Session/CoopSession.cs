using System;
using System.Collections.Generic;
using DribbleToSchool.Coop.Net;

namespace DribbleToSchool.Coop
{
    public enum SessionRole : byte { None, Host, Client }

    /// <summary>How this phone stands with the session.</summary>
    public enum ConnectionState : byte
    {
        /// <summary>In no session.</summary>
        Idle,
        /// <summary>The host: advertising the lobby and accepting players.</summary>
        Hosting,
        /// <summary>Joining a host found by the scan (waiting for its welcome).</summary>
        Connecting,
        /// <summary>In a host's lobby or race.</summary>
        Joined,
        /// <summary>Lost the host: looking for it (or for whoever took over) and taking over if it's this phone's turn.</summary>
        Reconnecting,
    }

    public enum NoticeType : byte
    {
        PlayerJoined, PlayerLeft, PlayerLost, PlayerBack, PlayerOut, PlayerFinished, NewHost,
        SelectionChanged, RaceOver,
        /// <summary>This phone lost the host and is trying to get back in.</summary>
        ConnectionLost,
        /// <summary>Back in the session after losing it.</summary>
        Reconnected,
        /// <summary>This phone took over as the host (the old one is gone).</summary>
        YouAreHost,
        /// <summary>This phone's run no longer counts: it was away longer than the grace period.</summary>
        YouAreOut,
        RadioOff, RadioOn,
        /// <summary>The host turned this phone away (<see cref="CoopNotice.code"/> is the <see cref="RejectReason"/>).</summary>
        Rejected,
        /// <summary>The lobby is gone (the host closed it, or it could not be found again before a race).</summary>
        LobbyClosed,
        HostFailed, ConnectFailed,
    }

    public struct CoopNotice
    {
        public NoticeType type;
        /// <summary>The player it is about (a copy as they were then), or null.</summary>
        public CoopPlayer player;
        public int code;
    }

    /// <summary>A lobby the scan heard (the Join list).</summary>
    public sealed class CoopRoom
    {
        public string address;
        public RoomBeacon beacon;
        public int rssi;
        public double lastSeenMs;
    }

    /// <summary>The session's timings, in milliseconds (docs/COOP.md, "Resilience").</summary>
    public static class CoopTiming
    {
        public const double PingInterval = 500;
        public const double FastPingInterval = 150;
        /// <summary>Nothing heard from the other end for this long: the connection is treated as lost (BLE's own timeout can be longer).</summary>
        public const double HeartbeatTimeout = 3500;
        public const double HelloTimeout = 6000;
        public const double ProfileInterval = 1000;
        public const double ProgressInterval = 500;
        public const double MotionInterval = 100;
        public const double SnapshotInterval = 1000;
        public const double SnapshotMinGap = 120;
        /// <summary>A player who drops out of the lobby keeps their seat this long.</summary>
        public const double LobbyGrace = 10000;
        /// <summary>A racing player whose connection is lost has this long to come back before being disqualified.</summary>
        public const double RaceGrace = 20000;
        /// <summary>A player who lost the host first tries this long to find the same host again before anyone takes over.</summary>
        public const double ReconnectWindow = 4000;
        /// <summary>Then each candidate in turn (by slot) takes over this much later than the one before.</summary>
        public const double MigrationStep = 4000;
        /// <summary>A phone scans this long (radio on) before it may take over, so it finds a host that is already there.</summary>
        public const double ScanBeforeHost = 2000;
        /// <summary>Before a race, a lost lobby is looked for this long.</summary>
        public const double LobbyReconnect = 8000;
        public const double StartCountdown = 3000;
        public const double LoadTimeout = 15000;
        /// <summary>From everyone loaded to GO (shown as 3, 2, 1).</summary>
        public const double RaceCountdown = 3500;
        public const double RoomExpiry = 4000;
        public const double ConnectRetry = 1500;
        public const double LeaveFlush = 400;
        /// <summary>After a change of host, players losing and finding the connection again are not announced one by one.</summary>
        public const double QuietAfterMigration = 6000;
    }

    /// <summary>
    /// One phone's side of a co-op lobby and race, over any <see cref="ICoopLink"/>. The host keeps the lobby (who is in it,
    /// the stage, the race) and sends it to everyone; each phone runs its own kid in its own copy of the level and reports
    /// where it is and when it got to school, so the race never waits on the radio: a phone that loses the connection keeps
    /// playing and catches up when it is back. The race clock is the host's, shared through pings, so the start (3, 2, 1, GO)
    /// is the same instant on every phone and every finish time is measured from it.
    ///
    /// Resilience (docs/COOP.md): a racing player out of touch for <see cref="CoopTiming.RaceGrace"/> is disqualified and
    /// listed last; the race goes on for everyone else. A player who got to school keeps their time and place even after
    /// leaving. When the host goes (switched off, out of range, left), the others first look for it, then the next player by
    /// slot takes over as host with the same session (a higher epoch) and everyone joins them; finished times live on every
    /// phone, so nothing is lost. Pure C# (no Unity): Tests/Editor/CoopSessionTests run whole races on an in-memory radio.
    /// </summary>
    public sealed class CoopSession
    {
        sealed class Peer
        {
            public int id;
            public readonly Reassembler rx = new Reassembler();
            public int txNumber;
            public double connectedAt;
            public double lastHeard;
            public uint uid;   // 0 until Hello
            public double rejectedAt = double.PositiveInfinity;
        }

        readonly ICoopLink link;
        readonly ICoopClock clock;
        readonly ByteWriter writer = new ByteWriter(512);
        readonly List<CoopPlayer> players = new List<CoopPlayer>();
        readonly Dictionary<string, CoopRoom> rooms = new Dictionary<string, CoopRoom>();
        readonly Random random;

        // Host role
        readonly Dictionary<int, Peer> peers = new Dictionary<int, Peer>();
        readonly Dictionary<byte, CoopMotion> latestMotions = new Dictionary<byte, CoopMotion>();
        readonly List<KeyValuePair<byte, CoopMotion>> motionsOut = new List<KeyValuePair<byte, CoopMotion>>();
        uint version;
        bool dirty;
        double lastSnapshotAt = double.NegativeInfinity, nextMotionsAt;
        bool motionsFresh;
        double phaseAtLocal;   // Starting: countdown end; Racing: start (both in local ms)
        double loadDeadline;
        bool hostingStarted;
        RoomBeacon advertised;

        // Client role
        readonly Peer host = new Peer();
        readonly ClockSync sync = new ClockSync();
        readonly List<KeyValuePair<byte, CoopMotion>> motionsIn = new List<KeyValuePair<byte, CoopMotion>>();
        bool welcomed, connectPending;
        double connectStartedAt, nextPingAt, nextProfileAt, nextProgressAt, nextMotionAt, lastConnectAttempt = double.NegativeInfinity;
        ushort profileSeq, progressSeq;
        bool profileDirty, progressDirty;
        uint lastVersion;
        bool hasSnapshot;
        uint snapshotPhaseAtHost;
        bool freshJoin;

        // Lost host (client) / migration
        double lostAt, migrateAt = double.PositiveInfinity, scanningSince = double.PositiveInfinity;
        byte lostEpoch;
        int candidateIndex;
        readonly List<uint> candidates = new List<uint>();
        string yieldTarget;
        double quietUntil = double.NegativeInfinity;

        // The local player's own intentions, kept across hosts.
        string myName;
        byte myCharacter;
        bool myReady;
        byte myLoadedRace;
        PlayerStatus myStatus = PlayerStatus.Lobby;
        byte myLeg;
        float myProgress;
        uint myFinishMs;
        CoopMotion myMotion;
        bool myMotionFresh;
        double raceStartLocal;
        bool raceStartKnown, raceStartLocked;

        // Leaving
        double shutdownAt = double.PositiveInfinity;

        // Notices: players as they were when last announced.
        readonly List<CoopPlayer> announced = new List<CoopPlayer>();
        CoopSelection announcedSelection;
        SessionPhase announcedPhase;

        public CoopSession(ICoopLink link, ICoopClock clock, uint uid, string name, byte character, int seed = 0)
        {
            this.link = link;
            this.clock = clock;
            Uid = uid == 0 ? 1u : uid;
            myName = CoopRules.CleanName(name);
            myCharacter = character;
            random = new Random(seed != 0 ? seed : (int)(Uid ^ (uint)Environment.TickCount));
            Radio = link.State;
        }

        // ---------- What the game reads ----------

        public uint Uid { get; private set; }
        public SessionRole Role { get; private set; }
        public ConnectionState Connection { get; private set; }
        public SessionPhase Phase { get; private set; }
        public RadioState Radio { get; private set; }
        public uint SessionId { get; private set; }
        public byte Epoch { get; private set; }
        /// <summary>Which race this is (goes up with every race in the same lobby).</summary>
        public byte RaceId { get; private set; }
        /// <summary>The stage and location chosen in the lobby (may be random).</summary>
        public CoopSelection Selection { get; private set; }
        /// <summary>The stage and location the race runs, random choices resolved (from Loading on).</summary>
        public CoopSelection RaceSelection { get; private set; }
        /// <summary>How many routes and locations there are to choose from (set by the game; random picks among them).</summary>
        public int RouteCount = 6, AddOnCount = 2;
        public IList<CoopPlayer> Players { get { return players; } }
        public ICollection<CoopRoom> Rooms { get { return rooms.Values; } }
        public bool InSession { get { return Role != SessionRole.None; } }
        public bool IsHost { get { return Role == SessionRole.Host; } }
        public double RoundTripMs { get { return IsHost ? 0 : sync.RoundTrip; } }
        public double NowMs { get { return clock.NowMs; } }

        /// <summary>Host: the lobby is being advertised (the radio said hosting started).</summary>
        public bool Advertising { get { return Role == SessionRole.Host && hostingStarted; } }

        /// <summary>This phone's player (null before it has a seat).</summary>
        public CoopPlayer Me { get { return Find(Uid); } }

        /// <summary>The race's start is known (the clock is synced and the host has set it).</summary>
        public bool RaceClockKnown { get { return raceStartKnown; } }
        /// <summary>Milliseconds since GO (negative during the countdown; 0 when not known).</summary>
        public double RaceTimeMs { get { return raceStartKnown ? clock.NowMs - raceStartLocal : 0; } }
        /// <summary>The race has started on this phone (past GO).</summary>
        public bool RaceStarted { get { return raceStartKnown && clock.NowMs >= raceStartLocal && (Phase == SessionPhase.Racing || Phase == SessionPhase.Over); } }
        /// <summary>Starting: milliseconds until the race loads. Racing before GO: until GO. Else 0.</summary>
        public double CountdownMs
        {
            get
            {
                if (Phase == SessionPhase.Starting) return Math.Max(0, StartingEndsLocal - clock.NowMs);
                if (Phase == SessionPhase.Racing && raceStartKnown) return Math.Max(0, raceStartLocal - clock.NowMs);
                return 0;
            }
        }
        /// <summary>This phone's own race status (what it believes; the host's snapshot confirms it).</summary>
        public PlayerStatus MyStatus { get { return myStatus; } }
        public uint MyFinishMs { get { return myFinishMs; } }
        /// <summary>When the connection was lost (Reconnecting), for the HUD's countdown to disqualification.</summary>
        public double LostForMs { get { return Connection == ConnectionState.Reconnecting ? clock.NowMs - lostAt : 0; } }
        /// <summary>Hosting alone after the others were lost (the race goes on; they may come back).</summary>
        public bool Alone
        {
            get
            {
                if (Role != SessionRole.Host || Phase == SessionPhase.Lobby) return false;
                foreach (var p in players) if (p.uid != Uid && p.connected) return false;
                return players.Count > 1;
            }
        }

        public event Action<CoopNotice> Noticed;
        public event Action<SessionPhase> PhaseChanged;

        double StartingEndsLocal { get { return IsHost ? phaseAtLocal : (sync.HasSync ? sync.ToLocal(snapshotPhaseAtHost) : clock.NowMs + CoopTiming.StartCountdown); } }

        public CoopPlayer Find(uint uid)
        {
            foreach (var p in players) if (p.uid == uid) return p;
            return null;
        }

        public CoopPlayer InSlot(int slot)
        {
            foreach (var p in players) if (p.slot == slot) return p;
            return null;
        }

        // ---------- What the game does ----------

        /// <summary>Open a new lobby with this phone as its host (slot 1).</summary>
        public void Host()
        {
            Reset();
            browsing = false;
            link.StopScan();
            Role = SessionRole.Host;
            Phase = SessionPhase.Lobby;
            SessionId = NewSessionId();
            Epoch = 0;
            Selection = new CoopSelection { route = 0, addOn = 0, chosenBy = CoopSelection.Nobody };
            var me = new CoopPlayer { slot = 0, uid = Uid, name = myName, character = myCharacter, isHost = true, connected = true, lastHeardMs = clock.NowMs };
            me.tag = CoopRules.UniqueTag(Uid, players);
            players.Add(me);
            Connection = ConnectionState.Hosting;
            StartHosting();
            dirty = true;
            Announce();
        }

        /// <summary>Look for lobbies nearby (the Join list) without joining one.</summary>
        public void Browse()
        {
            browsing = true;
            if (Role == SessionRole.None) link.StartScan();
        }

        public void StopBrowsing()
        {
            browsing = false;
            if (Role == SessionRole.None) link.StopScan();
        }

        bool browsing;

        /// <summary>Join the lobby at <paramref name="address"/> (from <see cref="Rooms"/>).</summary>
        public void Join(string address)
        {
            Reset();
            browsing = false;
            link.StopScan();
            Role = SessionRole.Client;
            Connection = ConnectionState.Connecting;
            freshJoin = true;
            ConnectTo(address);
        }

        /// <summary>Leave the lobby or the race: the others are told (a finished time is kept), then the radio lets go.</summary>
        public void Leave()
        {
            if (Role == SessionRole.None) return;
            bool race = Phase != SessionPhase.Lobby && Phase != SessionPhase.Starting;
            if (myStatus == PlayerStatus.Racing && race)
            {
                myStatus = PlayerStatus.Left;
                var me = Me;
                if (me != null) { me.status = PlayerStatus.Left; me.outMs = (uint)Math.Max(0, RaceTimeMs); me.connected = false; }
            }
            if (Role == SessionRole.Host)
            {
                var me = Me;
                if (me != null) me.connected = false;
                if (race && players.Count > 1)
                {
                    SendSnapshot(-1);
                    writer.Reset(); CoopMessages.WriteBare(writer, MsgType.HostLeaving); Broadcast();
                }
                else
                {
                    writer.Reset(); CoopMessages.WriteBare(writer, MsgType.Closing); Broadcast();
                }
            }
            else if (welcomed)
            {
                SendProgress();
                writer.Reset(); CoopMessages.WriteBare(writer, MsgType.Leave); SendToHost();
            }
            shutdownAt = clock.NowMs + CoopTiming.LeaveFlush;
            leaving = true;
        }

        bool leaving;

        /// <summary>Leaving has finished (or there was nothing to leave).</summary>
        public bool Left { get { return Role == SessionRole.None; } }

        public void SetName(string name)
        {
            myName = CoopRules.CleanName(name);
            ApplyProfile();
        }

        public void SetCharacter(byte character)
        {
            myCharacter = character;
            ApplyProfile();
        }

        public void SetReady(bool ready)
        {
            myReady = ready;
            ApplyProfile();
        }

        public bool MyReady { get { return myReady; } }

        /// <summary>Choose the next race's stage and location (any player may; the last choice the host gets wins). Readies are reset.</summary>
        public void Select(byte route, byte addOn)
        {
            if (Phase != SessionPhase.Lobby && Phase != SessionPhase.Starting) return;
            if (IsHost) ApplySelect(Me, route, addOn);
            else if (welcomed)
            {
                writer.Reset();
                CoopMessages.Write(writer, new SelectMsg { route = route, addOn = addOn });
                SendToHost();
            }
        }

        /// <summary>The race's first leg is loaded and ready to start (the loading barrier).</summary>
        public void ReportLoaded(byte raceId)
        {
            myLoadedRace = raceId;
            ApplyProfile();
        }

        /// <summary>Which leg of the route this phone's kid is on, and how far along the whole route (0 to 1).</summary>
        public void ReportLeg(int leg, float progress)
        {
            byte l = (byte)Math.Max(0, Math.Min(255, leg));
            bool changed = l != myLeg;
            myLeg = l;
            myProgress = Clamp01(progress);
            if (changed) { progressDirty = true; ApplyProgressToMe(); }
        }

        /// <summary>Where this phone's kid and ball are now (sent ten times a second while racing).</summary>
        public void ReportMotion(CoopMotion m)
        {
            if (!raceStartKnown) return;
            m.raceMs = (uint)Math.Max(0, RaceTimeMs);
            m.leg = myLeg;
            m.progress = myProgress = Clamp01(m.progress);
            myMotion = m;
            myMotionFresh = true;
            if (IsHost && Me != null)
            {
                latestMotions[Me.slot] = m;
                motionsFresh = true;
                Me.progress = myProgress;
            }
        }

        /// <summary>This phone's kid got to school: the time is taken now, from the shared race clock. Returns it (ms).</summary>
        public uint ReportFinished()
        {
            if (myStatus != PlayerStatus.Racing || !RaceStarted) return myFinishMs;
            myStatus = PlayerStatus.Finished;
            myFinishMs = (uint)Math.Max(0, RaceTimeMs);
            myProgress = 1f;
            progressDirty = true;
            ApplyProgressToMe();
            return myFinishMs;
        }

        /// <summary>Host, after a race: back to the lobby for another one with the same players.</summary>
        public void NewRace()
        {
            if (!IsHost || Phase != SessionPhase.Over) return;
            players.RemoveAll(p => !p.connected && p.uid != Uid);
            foreach (var p in players)
            {
                p.ready = false;
                p.status = PlayerStatus.Lobby;
                p.leg = 0; p.progress = 0; p.finishMs = 0; p.outMs = 0; p.place = 0;
                p.track.Clear();
            }
            myReady = false;
            myStatus = PlayerStatus.Lobby;
            raceStartKnown = raceStartLocked = false;
            latestMotions.Clear();
            if (InRaceScanning) { link.StopScan(); InRaceScanning = false; }
            SetPhase(SessionPhase.Lobby);
            dirty = true;
        }

        /// <summary>Call once a frame: handles the radio, the timers and the sending.</summary>
        public void Tick()
        {
            double now = clock.NowMs;
            LinkEvent e;
            int guard = 0;
            while (guard++ < 512 && link.Poll(out e)) Handle(e, now);

            if (leaving && now >= shutdownAt) { Shutdown(); return; }

            ExpireRooms(now);
            if (Role == SessionRole.Host) TickHost(now);
            else if (Role == SessionRole.Client) TickClient(now);
            Announce();
        }

        // ---------- Radio events ----------

        void Handle(LinkEvent e, double now)
        {
            switch (e.type)
            {
                case LinkEventType.Radio: OnRadio(e.state, now); break;
                case LinkEventType.Found: OnFound(e, now); break;
                case LinkEventType.Connected:
                    if (Role == SessionRole.Host) peers[e.peer] = new Peer { id = e.peer, connectedAt = now, lastHeard = now };
                    else if (Role == SessionRole.Client && Connection != ConnectionState.Joined) OnConnectedToHost(now);
                    break;
                case LinkEventType.Disconnected:
                    if (Role == SessionRole.Host) DropPeer(e.peer, now, false);
                    else if (Role == SessionRole.Client && e.peer == 0) OnHostLost(now, false);
                    break;
                case LinkEventType.Data: OnData(e, now); break;
                case LinkEventType.HostStarted: hostingStarted = true; break;
                case LinkEventType.HostFailed:
                    hostingStarted = false;
                    Notice(NoticeType.HostFailed, null, 0);
                    break;
                case LinkEventType.ConnectFailed:
                    if (Role != SessionRole.Client) break;
                    connectPending = false;
                    if (freshJoin && !welcomed)
                    {
                        Notice(NoticeType.ConnectFailed, null, 0);
                        Shutdown();
                    }
                    break;
            }
        }

        void OnRadio(RadioState state, double now)
        {
            var before = Radio;
            Radio = state;
            if (state == before) return;
            if (state != RadioState.On)
            {
                if (before == RadioState.On) Notice(NoticeType.RadioOff, null, (int)state);
                scanningSince = double.PositiveInfinity;
                if (Role == SessionRole.Host)
                {
                    hostingStarted = false;
                    foreach (var id in new List<int>(peers.Keys)) DropPeer(id, now, false);
                }
                else if (Role == SessionRole.Client && Connection != ConnectionState.Reconnecting)
                {
                    if (freshJoin && !welcomed) { Notice(NoticeType.ConnectFailed, null, 0); Shutdown(); }
                    else OnHostLost(now, false);
                }
                return;
            }
            Notice(NoticeType.RadioOn, null, 0);
            if (Role == SessionRole.Host)
            {
                StartHosting();
            }
            else if (Role == SessionRole.Client && Connection == ConnectionState.Reconnecting)
            {
                link.StartScan();
                scanningSince = now;
            }
            else if (Role == SessionRole.None && browsing) link.StartScan();   // (the Join list carries on)
        }

        void OnFound(LinkEvent e, double now)
        {
            // (a lobby of another protocol version is listed too: the Join list says it can't be joined)
            CoopRoom room;
            if (!rooms.TryGetValue(e.address, out room))
            {
                room = new CoopRoom { address = e.address };
                rooms[e.address] = room;
            }
            room.beacon = e.beacon;
            room.rssi = e.rssi;
            room.lastSeenMs = now;

            // A host racing beside another host of the same session (after a split): the one with fewer players steps down.
            if (Role == SessionRole.Host && InRace && e.beacon.sessionId == SessionId && CoopRules.ShouldYieldTo(advertised, e.beacon))
                YieldTo(e.address, now);
        }

        void ExpireRooms(double now)
        {
            List<string> gone = null;
            foreach (var kv in rooms)
                if (now - kv.Value.lastSeenMs > CoopTiming.RoomExpiry) (gone ?? (gone = new List<string>())).Add(kv.Key);
            if (gone != null) foreach (var key in gone) rooms.Remove(key);
        }

        void OnData(LinkEvent e, double now)
        {
            if (e.data == null) return;
            if (Role == SessionRole.Host)
            {
                Peer peer;
                if (!peers.TryGetValue(e.peer, out peer)) return;
                peer.lastHeard = now;
                var message = peer.rx.Add(e.data, e.data.Length);
                if (message != null) OnHostMessage(peer, message, now);
            }
            else if (Role == SessionRole.Client && e.peer == 0)
            {
                host.lastHeard = now;
                var message = host.rx.Add(e.data, e.data.Length);
                if (message != null) OnClientMessage(message, now);
            }
        }

        bool InRace { get { return Phase == SessionPhase.Loading || Phase == SessionPhase.Racing || Phase == SessionPhase.Over; } }

        // ---------- Host ----------

        void StartHosting()
        {
            advertised = MakeBeacon();
            link.StartHost(advertised);
            // During a race the host listens too, to notice another host of the same session after a split.
            if (InRace) link.StartScan();
        }

        RoomBeacon MakeBeacon()
        {
            int connected = 0;
            foreach (var p in players) if (p.connected) connected++;
            var me = Me;
            return new RoomBeacon
            {
                protocol = CoopMessages.Protocol,
                sessionId = SessionId,
                epoch = Epoch,
                players = (byte)connected,
                maxPlayers = CoopRules.MaxPlayers,
                phase = Phase == SessionPhase.Over ? RoomPhase.Over : InRace ? RoomPhase.Racing : RoomPhase.Lobby,
                hostName = me != null ? me.name : "",
            };
        }

        void TickHost(double now)
        {
            var me = Me;
            if (me != null) me.lastHeardMs = now;

            // Players who have not said hello, or have gone quiet.
            foreach (var peer in new List<Peer>(peers.Values))
            {
                if (peer.uid == 0 && (now - peer.connectedAt > CoopTiming.HelloTimeout || now - peer.rejectedAt > 1500)) { link.Kick(peer.id); peers.Remove(peer.id); continue; }
                if (now - peer.lastHeard > CoopTiming.HeartbeatTimeout) { link.Kick(peer.id); DropPeer(peer.id, now, true); }
            }

            // Seats held for players who dropped out, and disqualification after the grace period.
            for (int i = players.Count - 1; i >= 0; i--)
            {
                var p = players[i];
                if (p.connected || p.uid == Uid) continue;
                double away = now - p.lostSinceMs;
                if (!InRace)
                {
                    if (away > CoopTiming.LobbyGrace) { players.RemoveAt(i); dirty = true; }
                }
                else if (p.status == PlayerStatus.Racing && away > CoopTiming.RaceGrace)
                {
                    p.status = PlayerStatus.Disconnected;
                    p.outMs = (uint)Math.Max(0, p.lostSinceMs - raceStartLocal);
                    dirty = true;
                }
            }

            StepPhase(now);

            var beacon = MakeBeacon();
            if (beacon.players != advertised.players || beacon.phase != advertised.phase || beacon.epoch != advertised.epoch || beacon.hostName != advertised.hostName)
            {
                advertised = beacon;
                link.UpdateBeacon(beacon);
            }

            if ((dirty && now - lastSnapshotAt >= CoopTiming.SnapshotMinGap) || now - lastSnapshotAt >= CoopTiming.SnapshotInterval)
                SendSnapshot(-1);

            if (Phase == SessionPhase.Racing && motionsFresh && now >= nextMotionsAt)
            {
                nextMotionsAt = now + CoopTiming.MotionInterval;
                motionsFresh = false;
                motionsOut.Clear();
                foreach (var kv in latestMotions)
                {
                    var p = InSlot(kv.Key);
                    if (p != null && p.status == PlayerStatus.Racing) motionsOut.Add(kv);
                }
                if (motionsOut.Count > 0)
                {
                    writer.Reset();
                    CoopMessages.WriteMotions(writer, motionsOut);
                    Broadcast();
                }
            }
        }

        void StepPhase(double now)
        {
            int connected = 0, ready = 0;
            foreach (var p in players)
            {
                if (!p.connected) continue;
                connected++;
                if (p.ready) ready++;
            }
            switch (Phase)
            {
                case SessionPhase.Lobby:
                    if (connected >= CoopRules.MinPlayers && ready == connected && connected == players.Count)
                    {
                        phaseAtLocal = now + CoopTiming.StartCountdown;
                        SetPhase(SessionPhase.Starting);
                    }
                    break;
                case SessionPhase.Starting:
                    if (connected < CoopRules.MinPlayers || ready != connected || connected != players.Count) SetPhase(SessionPhase.Lobby);
                    else if (now >= phaseAtLocal) BeginLoading(now);
                    break;
                case SessionPhase.Loading:
                    bool all = true;
                    foreach (var p in players)
                        if (p.connected && p.status == PlayerStatus.Racing && p.loadedRace != RaceId) all = false;
                    if (all || now >= loadDeadline)
                    {
                        raceStartLocal = now + CoopTiming.RaceCountdown;
                        raceStartKnown = true;
                        phaseAtLocal = raceStartLocal;
                        SetPhase(SessionPhase.Racing);
                    }
                    break;
                case SessionPhase.Racing:
                    if (!raceStartLocked && now >= raceStartLocal) raceStartLocked = true;
                    if (CoopRules.RaceOver(players)) SetPhase(SessionPhase.Over);
                    break;
                case SessionPhase.Over:
                    // A player disqualified by mistake can't come back, and a new race starts from the lobby (NewRace).
                    break;
            }
        }

        void BeginLoading(double now)
        {
            var s = Selection;
            if (s.route == CoopSelection.Random || s.route >= RouteCount) s.route = (byte)random.Next(Math.Max(1, RouteCount));
            if (s.addOn == CoopSelection.Random || s.addOn >= AddOnCount) s.addOn = (byte)random.Next(Math.Max(1, AddOnCount));
            RaceSelection = s;
            RaceId = (byte)(RaceId == 255 ? 1 : RaceId + 1);
            foreach (var p in players)
            {
                p.status = PlayerStatus.Racing;
                p.leg = 0; p.progress = 0; p.finishMs = 0; p.outMs = 0; p.place = 0;
                p.track.Clear();
            }
            myStatus = PlayerStatus.Racing;
            myLeg = 0; myProgress = 0; myFinishMs = 0;
            raceStartKnown = raceStartLocked = false;
            latestMotions.Clear();
            loadDeadline = now + CoopTiming.LoadTimeout;
            SetPhase(SessionPhase.Loading);
            if (!InRaceScanning) { link.StartScan(); InRaceScanning = true; }
        }

        bool InRaceScanning;

        void SetPhase(SessionPhase phase)
        {
            if (Phase == phase) return;
            Phase = phase;
            dirty = true;
            if (PhaseChanged != null) PhaseChanged(phase);
        }

        void OnHostMessage(Peer peer, byte[] message, double now)
        {
            var r = new ByteReader(message);
            var type = CoopMessages.TypeOf(message);
            if (type == MsgType.Hello)
            {
                HelloMsg hello;
                if (CoopMessages.Read(r, out hello)) OnHello(peer, hello, now);
                return;
            }
            var p = peer.uid != 0 ? Find(peer.uid) : null;
            if (p == null) return;   // nothing but Hello before a seat
            p.lastHeardMs = now;
            switch (type)
            {
                case MsgType.Ping:
                    r.U8();
                    uint sent = r.U32();
                    writer.Reset();
                    CoopMessages.WritePong(writer, sent, HostNow);
                    SendTo(peer);
                    break;
                case MsgType.Profile:
                    ProfileMsg profile;
                    if (!CoopMessages.Read(r, out profile)) break;
                    string name = CoopRules.CleanName(profile.name);
                    bool lobby = Phase == SessionPhase.Lobby || Phase == SessionPhase.Starting;
                    bool ready = lobby ? profile.ready : p.ready;
                    if (name != p.name || profile.character != p.character || ready != p.ready || profile.loadedRace != p.loadedRace)
                    {
                        p.name = name;
                        p.character = profile.character;
                        p.ready = ready;
                        p.loadedRace = profile.loadedRace;
                        dirty = true;
                    }
                    break;
                case MsgType.Progress:
                    ProgressMsg progress;
                    if (CoopMessages.Read(r, out progress)) ApplyProgress(p, progress);
                    break;
                case MsgType.Motion:
                    CoopMotion motion;
                    if (!CoopMessages.ReadMotion(r, out motion) || p.status != PlayerStatus.Racing) break;
                    latestMotions[p.slot] = motion;
                    p.progress = motion.progress;
                    p.track.Add(motion);
                    motionsFresh = true;
                    break;
                case MsgType.Select:
                    SelectMsg select;
                    if (CoopMessages.Read(r, out select)) ApplySelect(p, select.route, select.addOn);
                    break;
                case MsgType.Leave:
                    p.connected = false;
                    p.lostSinceMs = now;
                    p.peer = -1;
                    if (p.status == PlayerStatus.Racing && InRace) { p.status = PlayerStatus.Left; p.outMs = (uint)Math.Max(0, now - raceStartLocal); }
                    if (!InRace) players.Remove(p);
                    peers.Remove(peer.id);
                    link.Kick(peer.id);
                    dirty = true;
                    break;
            }
        }

        uint HostNow { get { return (uint)Math.Max(0, clock.NowMs); } }

        void OnHello(Peer peer, HelloMsg hello, double now)
        {
            if (hello.protocol != CoopMessages.Protocol) { Reject(peer, RejectReason.Version); return; }
            var known = Find(hello.uid);
            if (known == null)
            {
                // A race under way takes nobody new, except a player of this very session this host's copy of the lobby
                // missed (it took over before hearing of them): they were racing, so they race on.
                bool racer = InRace && hello.sessionId == SessionId && SessionId != 0;
                if (Phase != SessionPhase.Lobby && Phase != SessionPhase.Starting && !racer) { Reject(peer, RejectReason.InProgress); return; }
                int slot = CoopRules.FreeSlot(players);
                if (slot < 0) { Reject(peer, RejectReason.Full); return; }
                known = new CoopPlayer { slot = (byte)slot, uid = hello.uid, status = racer ? PlayerStatus.Racing : PlayerStatus.Lobby, loadedRace = racer ? RaceId : (byte)0 };
                known.tag = CoopRules.UniqueTag(hello.uid, players);
                players.Add(known);
                if (Phase == SessionPhase.Starting) SetPhase(SessionPhase.Lobby);
            }
            else if (known.uid == Uid)
            {
                Reject(peer, RejectReason.InProgress);   // (our own id from another phone: a copied install)
                return;
            }
            // A player who was here before gets their seat (and their race) back.
            foreach (var other in peers.Values)
                if (other != peer && other.uid == hello.uid) { link.Kick(other.id); other.uid = 0; }
            peer.uid = hello.uid;
            known.peer = peer.id;
            known.connected = true;
            known.lastHeardMs = now;
            known.name = CoopRules.CleanName(hello.name);
            known.character = hello.character;
            dirty = true;

            writer.Reset();
            CoopMessages.Write(writer, new WelcomeMsg { sessionId = SessionId, epoch = Epoch, slot = known.slot, tag = known.tag });
            SendTo(peer);
            SendSnapshot(peer.id);
        }

        void Reject(Peer peer, RejectReason reason)
        {
            writer.Reset();
            CoopMessages.WriteReject(writer, reason);
            SendTo(peer);
            peer.uid = 0;
            peer.rejectedAt = clock.NowMs;   // the player's phone hangs up once it reads the reason; else it is dropped in a moment
        }

        void ApplySelect(CoopPlayer by, byte route, byte addOn)
        {
            if (by == null || (Phase != SessionPhase.Lobby && Phase != SessionPhase.Starting)) return;
            var s = new CoopSelection { route = route, addOn = addOn, chosenBy = by.slot };
            if (s.Equals(Selection)) return;
            Selection = s;
            // A new stage: everyone looks again before the race starts.
            foreach (var p in players) p.ready = false;
            myReady = false;
            if (Phase == SessionPhase.Starting) SetPhase(SessionPhase.Lobby);
            dirty = true;
        }

        void ApplyProgress(CoopPlayer p, ProgressMsg m)
        {
            if (!InRace || m.raceId != RaceId) return;
            if (m.leg != p.leg) { p.leg = m.leg; dirty = true; }
            if (p.status == PlayerStatus.Racing)
            {
                p.progress = Math.Max(p.progress, m.progress);
                if (m.status == PlayerStatus.Finished)
                {
                    p.status = PlayerStatus.Finished;
                    p.finishMs = m.finishMs;
                    p.progress = 1f;
                    CoopRules.AssignPlaces(players);
                    dirty = true;
                }
                else if (m.status == PlayerStatus.Left)
                {
                    p.status = PlayerStatus.Left;
                    p.outMs = (uint)Math.Max(0, RaceTimeMs);
                    dirty = true;
                }
            }
        }

        /// <summary>Host: a player's connection went (or went quiet). Their seat and race wait for them (the grace period).</summary>
        void DropPeer(int id, double now, bool timedOut)
        {
            Peer peer;
            if (!peers.TryGetValue(id, out peer)) return;
            peers.Remove(id);
            var p = peer.uid != 0 ? Find(peer.uid) : null;
            if (p == null || p.peer != id) return;
            p.connected = false;
            p.peer = -1;
            p.lostSinceMs = now - (timedOut ? CoopTiming.HeartbeatTimeout : 0);
            if (Phase == SessionPhase.Starting) SetPhase(SessionPhase.Lobby);
            dirty = true;
        }

        void SendSnapshot(int onlyPeer)
        {
            var s = new SnapshotMsg
            {
                version = ++version,
                sessionId = SessionId,
                epoch = Epoch,
                phase = Phase,
                raceId = RaceId,
                selection = Selection,
                raceSelection = RaceSelection,
                phaseAtHostMs = (uint)Math.Max(0, Phase == SessionPhase.Starting || Phase == SessionPhase.Racing || Phase == SessionPhase.Over ? phaseAtLocal : 0),
            };
            s.players.AddRange(players);
            writer.Reset();
            CoopMessages.Write(writer, s);
            if (onlyPeer >= 0)
            {
                Peer peer;
                if (peers.TryGetValue(onlyPeer, out peer)) SendTo(peer);
                return;
            }
            dirty = false;
            lastSnapshotAt = clock.NowMs;
            Broadcast();
        }

        void Broadcast()
        {
            foreach (var peer in peers.Values)
                if (peer.uid != 0) SendTo(peer);
        }

        void SendTo(Peer peer)
        {
            foreach (var packet in CoopFraming.Split(writer.Buffer, writer.Length, link.MaxPacket, peer.txNumber++))
                link.Send(peer.id, packet);
        }

        /// <summary>Another host of this session has more players (after a split): hand over and join it.</summary>
        void YieldTo(string address, double now)
        {
            link.StopHost();
            peers.Clear();
            hostingStarted = false;
            Role = SessionRole.Client;
            foreach (var p in players) { p.isHost = false; if (p.uid != Uid) { p.connected = false; } }
            BeginLost(now, true);
            migrateAt = now + CoopTiming.RaceGrace;   // it was told to join the other host: no quick take-over
            yieldTarget = address;
            ConnectTo(address);
        }

        // ---------- Client ----------

        void ConnectTo(string address)
        {
            lastConnectAttempt = clock.NowMs;
            connectStartedAt = clock.NowMs;
            connectPending = true;
            welcomed = false;
            host.rx.Reset();
            host.txNumber = 0;
            host.lastHeard = clock.NowMs;
            link.Connect(address);
        }

        void OnConnectedToHost(double now)
        {
            host.lastHeard = now;
            writer.Reset();
            CoopMessages.Write(writer, new HelloMsg { protocol = CoopMessages.Protocol, uid = Uid, sessionId = SessionId, name = myName, character = myCharacter });
            SendToHost();
        }

        void SendToHost()
        {
            foreach (var packet in CoopFraming.Split(writer.Buffer, writer.Length, link.MaxPacket, host.txNumber++))
                link.Send(0, packet);
        }

        void TickClient(double now)
        {
            // A connection that was never welcomed in time is given up (a fresh join fails; a reconnection tries again).
            if (connectPending && !welcomed && now - connectStartedAt > CoopTiming.HelloTimeout)
            {
                connectPending = false;
                link.Disconnect();
                if (freshJoin) { Notice(NoticeType.ConnectFailed, null, 0); Shutdown(); return; }
            }

            if (Connection == ConnectionState.Joined)
            {
                if (now - host.lastHeard > CoopTiming.HeartbeatTimeout)
                {
                    link.Disconnect();
                    OnHostLost(now, false);
                    return;
                }
                if (now >= nextPingAt)
                {
                    nextPingAt = now + (sync.HasSync && sync.RoundTrip > 0 && SamplesEnough ? CoopTiming.PingInterval : CoopTiming.FastPingInterval);
                    pingsSent++;
                    writer.Reset();
                    CoopMessages.WritePing(writer, (uint)Math.Max(0, now));
                    SendToHost();
                }
                if (profileDirty || now >= nextProfileAt) SendProfile();
                if (InRace && (progressDirty || now >= nextProgressAt)) SendProgress();
                if (Phase == SessionPhase.Racing && myMotionFresh && now >= nextMotionAt && myStatus == PlayerStatus.Racing)
                {
                    nextMotionAt = now + CoopTiming.MotionInterval;
                    myMotionFresh = false;
                    writer.Reset();
                    CoopMessages.WriteMotion(writer, myMotion);
                    SendToHost();
                }
                RefreshRaceStart(now);
            }
            else if (Connection == ConnectionState.Reconnecting) TickLost(now);
        }

        int pingsSent;
        bool SamplesEnough { get { return pingsSent >= 6; } }

        void SendProfile()
        {
            profileDirty = false;
            nextProfileAt = clock.NowMs + CoopTiming.ProfileInterval;
            writer.Reset();
            CoopMessages.Write(writer, new ProfileMsg { seq = ++profileSeq, name = myName, character = myCharacter, ready = myReady, loadedRace = myLoadedRace });
            SendToHost();
        }

        void SendProgress()
        {
            progressDirty = false;
            nextProgressAt = clock.NowMs + CoopTiming.ProgressInterval;
            writer.Reset();
            CoopMessages.Write(writer, new ProgressMsg { seq = ++progressSeq, raceId = RaceId, status = myStatus, leg = myLeg, progress = myProgress, finishMs = myFinishMs });
            SendToHost();
        }

        void OnClientMessage(byte[] message, double now)
        {
            var r = new ByteReader(message);
            switch (CoopMessages.TypeOf(message))
            {
                case MsgType.Welcome:
                    WelcomeMsg welcome;
                    if (!CoopMessages.Read(r, out welcome)) break;
                    bool wasLost = Connection == ConnectionState.Reconnecting;
                    welcomed = true;
                    connectPending = false;
                    freshJoin = false;
                    yieldTarget = null;
                    SessionId = welcome.sessionId;
                    Epoch = welcome.epoch;
                    Connection = ConnectionState.Joined;
                    migrateAt = double.PositiveInfinity;
                    link.StopScan();
                    sync.Reset();
                    pingsSent = 0;
                    nextPingAt = now;
                    lastVersion = 0;
                    hasSnapshot = false;
                    profileDirty = true;
                    progressDirty = true;
                    if (wasLost) Notice(NoticeType.Reconnected, null, 0);
                    break;
                case MsgType.Reject:
                    r.U8();
                    int reason = r.U8();
                    link.Disconnect();
                    if (freshJoin || !InRace)
                    {
                        Notice(NoticeType.Rejected, null, reason);
                        Shutdown();
                    }
                    else
                    {
                        // Turned away by a host that doesn't know us (a split): keep looking, or take over in turn.
                        welcomed = false;
                        connectPending = false;
                    }
                    break;
                case MsgType.Snapshot:
                    SnapshotMsg snapshot;
                    if (CoopMessages.Read(r, out snapshot)) ApplySnapshot(snapshot, now);
                    break;
                case MsgType.Motions:
                    if (!CoopMessages.ReadMotions(r, motionsIn)) break;
                    foreach (var kv in motionsIn)
                    {
                        var p = InSlot(kv.Key);
                        if (p != null && p.uid != Uid) { p.track.Add(kv.Value); p.progress = kv.Value.progress; }
                    }
                    break;
                case MsgType.Pong:
                    r.U8();
                    uint sent = r.U32();
                    uint hostMs = r.U32();
                    if (!r.Failed) sync.AddSample(sent, hostMs, now);
                    break;
                case MsgType.Closing:
                    Notice(NoticeType.LobbyClosed, null, 0);
                    Shutdown();
                    break;
                case MsgType.HostLeaving:
                    link.Disconnect();
                    OnHostLost(now, true);
                    break;
            }
        }

        void ApplySnapshot(SnapshotMsg s, double now)
        {
            if (hasSnapshot && s.version <= lastVersion && s.epoch == Epoch) return;
            hasSnapshot = true;
            lastVersion = s.version;
            SessionId = s.sessionId;
            Epoch = s.epoch;
            bool newRace = s.raceId != RaceId && (s.phase == SessionPhase.Loading || s.phase == SessionPhase.Racing);
            RaceId = s.raceId;
            // A new stage resets everyone's ready (the host does the same to its copy).
            if (announced.Count > 0 && !s.selection.Equals(Selection) && (s.phase == SessionPhase.Lobby || s.phase == SessionPhase.Starting)) myReady = false;
            Selection = s.selection;
            RaceSelection = s.raceSelection;
            snapshotPhaseAtHost = s.phaseAtHostMs;

            // Keep each player's object (their ghost's samples live on it).
            var keep = new List<CoopPlayer>(s.players.Count);
            foreach (var incoming in s.players)
            {
                var p = Find(incoming.uid) ?? new CoopPlayer { uid = incoming.uid };
                p.slot = incoming.slot;
                p.tag = incoming.tag;
                p.name = incoming.name;
                p.character = incoming.character;
                p.isHost = incoming.isHost;
                p.ready = incoming.ready;
                bool wasConnected = p.connected || p.lostSinceMs <= 0;
                p.connected = incoming.connected;
                if (p.connected) p.lastHeardMs = now;
                else if (wasConnected) p.lostSinceMs = now;
                p.loadedRace = incoming.loadedRace;
                p.status = incoming.status;
                p.leg = incoming.leg;
                if (p.uid != Uid || incoming.progress > p.progress) p.progress = incoming.progress;
                p.finishMs = incoming.finishMs;
                p.outMs = incoming.outMs;
                p.place = incoming.place;
                keep.Add(p);
            }
            players.Clear();
            players.AddRange(keep);

            // Who would take over if the host went: every other player still connected, by slot.
            candidates.Clear();
            var order = new List<CoopPlayer>(players);
            order.Sort((a, b) => a.slot.CompareTo(b.slot));
            foreach (var p in order)
                if (!p.isHost && p.connected && p.status != PlayerStatus.Left) candidates.Add(p.uid);

            if (newRace)
            {
                myStatus = PlayerStatus.Racing;
                myLeg = 0; myProgress = 0; myFinishMs = 0;
                raceStartKnown = raceStartLocked = false;
                foreach (var p in players) p.track.Clear();
            }
            var me = Me;
            if (me != null)
            {
                // The host has the last word on whether this phone's run still counts.
                if (me.status == PlayerStatus.Disconnected && myStatus == PlayerStatus.Racing) myStatus = PlayerStatus.Disconnected;
                if (me.status == PlayerStatus.Lobby && s.phase == SessionPhase.Lobby) myStatus = PlayerStatus.Lobby;
            }
            if (s.phase == SessionPhase.Lobby && (Phase == SessionPhase.Over || Phase == SessionPhase.Racing))
            {
                myStatus = PlayerStatus.Lobby;
                myReady = false;
                raceStartKnown = raceStartLocked = false;
            }
            if (s.phase != Phase)
            {
                Phase = s.phase;
                if (PhaseChanged != null) PhaseChanged(Phase);
            }
            if (me != null && me.status == PlayerStatus.Racing && myStatus == PlayerStatus.Finished) progressDirty = true;   // make sure the host has our time
            RefreshRaceStart(now);
        }

        /// <summary>The start time from the host's clock, until the race is under way; then it never moves again.</summary>
        void RefreshRaceStart(double now)
        {
            if (raceStartLocked || (Phase != SessionPhase.Racing && Phase != SessionPhase.Over) || !sync.HasSync || snapshotPhaseAtHost == 0) return;
            raceStartLocal = sync.ToLocal(snapshotPhaseAtHost);
            raceStartKnown = true;
            if (now >= raceStartLocal) raceStartLocked = true;
        }

        // ---------- Losing the host, and taking over ----------

        void OnHostLost(double now, bool graceful)
        {
            if (Role != SessionRole.Client || Connection == ConnectionState.Reconnecting) return;
            BeginLost(now, graceful);
            Notice(NoticeType.ConnectionLost, null, graceful ? 1 : 0);
        }

        void BeginLost(double now, bool graceful)
        {
            Connection = ConnectionState.Reconnecting;
            welcomed = false;
            lostAt = now;
            lostEpoch = Epoch;
            var oldHost = players.Find(p => p.isHost);
            if (oldHost != null && oldHost.uid != Uid)
            {
                oldHost.connected = false;
                oldHost.lostSinceMs = now;
            }
            candidateIndex = candidates.IndexOf(Uid);
            if (candidateIndex < 0) candidateIndex = candidates.Count;
            migrateAt = InRace ? now + (graceful ? 500 : CoopTiming.ReconnectWindow) + candidateIndex * CoopTiming.MigrationStep : double.PositiveInfinity;
            scanningSince = Radio == RadioState.On ? now : double.PositiveInfinity;
            if (Radio == RadioState.On) link.StartScan();
        }

        void TickLost(double now)
        {
            if (Radio == RadioState.On && double.IsPositiveInfinity(scanningSince)) { link.StartScan(); scanningSince = now; }

            // Waiting on a connection attempt?
            bool attempting = connectPending && !welcomed;
            if (!attempting)
            {
                var best = BestRoomForSession(now);
                if (best != null && now - lastConnectAttempt >= CoopTiming.ConnectRetry) { ConnectTo(best.address); return; }
            }

            if (!InRace)
            {
                if (now - lostAt > CoopTiming.LobbyReconnect)
                {
                    Notice(NoticeType.LobbyClosed, null, 0);
                    Shutdown();
                }
                return;
            }

            if (!attempting && now >= migrateAt && Radio == RadioState.On && now - scanningSince >= CoopTiming.ScanBeforeHost)
                TakeOver(now);
        }

        /// <summary>The lobby of this session the scan hears that the others would join: the most players, then the oldest host.</summary>
        CoopRoom BestRoomForSession(double now)
        {
            CoopRoom best = null;
            foreach (var room in rooms.Values)
            {
                if (room.beacon.sessionId != SessionId || now - room.lastSeenMs > CoopTiming.RoomExpiry * 0.6) continue;
                if (room.beacon.epoch < lostEpoch && yieldTarget == null) continue;   // an older host than the one we lost
                if (best == null || CoopRules.ShouldYieldTo(best.beacon, room.beacon)) best = room;
            }
            return best;
        }

        void TakeOver(double now)
        {
            link.Disconnect();
            Role = SessionRole.Host;
            Connection = ConnectionState.Hosting;
            Epoch = (byte)(lostEpoch + 1 + candidateIndex);
            migrateAt = double.PositiveInfinity;
            peers.Clear();
            foreach (var p in players)
            {
                p.isHost = p.uid == Uid;
                p.peer = -1;
                if (p.uid == Uid) { p.connected = true; continue; }
                if (p.connected) { p.connected = false; p.lostSinceMs = lostAt; }
            }
            var me = Me;
            if (me != null)
            {
                me.status = myStatus == PlayerStatus.Lobby ? me.status : myStatus;
                if (myStatus == PlayerStatus.Finished) { me.finishMs = myFinishMs; me.progress = 1f; }
                me.leg = myLeg;
                me.ready = myReady;
                me.loadedRace = myLoadedRace;
            }
            CoopRules.AssignPlaces(players);
            // The race clock: this phone's own start, now in its own clock (the host's clock is the host's local one).
            if (Phase == SessionPhase.Loading) loadDeadline = now + CoopTiming.LoadTimeout;
            if (Phase == SessionPhase.Racing && !raceStartKnown)
            {
                raceStartLocal = now + CoopTiming.RaceCountdown;   // (never synced: start counting from here)
                raceStartKnown = true;
            }
            if (raceStartKnown) phaseAtLocal = raceStartLocal;
            version += 1000;
            quietUntil = now + CoopTiming.QuietAfterMigration;
            InRaceScanning = true;
            StartHosting();
            dirty = true;
            Notice(NoticeType.YouAreHost, null, 0);
        }

        // ---------- Local player ----------

        void ApplyProfile()
        {
            if (IsHost)
            {
                var me = Me;
                if (me == null) return;
                bool lobby = Phase == SessionPhase.Lobby || Phase == SessionPhase.Starting;
                me.name = myName;
                me.character = myCharacter;
                if (lobby) me.ready = myReady;
                me.loadedRace = myLoadedRace;
                dirty = true;
            }
            else profileDirty = true;
        }

        void ApplyProgressToMe()
        {
            if (!IsHost) return;
            var me = Me;
            if (me == null) return;
            me.leg = myLeg;
            if (me.status == PlayerStatus.Racing && myStatus == PlayerStatus.Finished)
            {
                me.status = PlayerStatus.Finished;
                me.finishMs = myFinishMs;
                me.progress = 1f;
                CoopRules.AssignPlaces(players);
            }
            dirty = true;
        }

        // ---------- Notices ----------

        void Notice(NoticeType type, CoopPlayer player, int code)
        {
            if (Noticed != null) Noticed(new CoopNotice { type = type, player = player != null ? player.Clone() : null, code = code });
        }

        /// <summary>What changed since the last frame, as notices (the same on the host and on the players' phones).</summary>
        void Announce()
        {
            bool quiet = clock.NowMs < quietUntil;
            foreach (var p in players)
            {
                CoopPlayer was = null;
                foreach (var a in announced) if (a.uid == p.uid) { was = a; break; }
                if (p.uid == Uid) continue;
                if (was == null) { if (announced.Count > 0) Notice(NoticeType.PlayerJoined, p, 0); continue; }
                if (was.status != p.status)
                {
                    if (p.status == PlayerStatus.Finished) Notice(NoticeType.PlayerFinished, p, p.place);
                    else if (p.status == PlayerStatus.Disconnected) Notice(NoticeType.PlayerOut, p, 0);
                    else if (p.status == PlayerStatus.Left) Notice(NoticeType.PlayerLeft, p, 0);
                }
                if (was.connected && !p.connected && !quiet && p.status != PlayerStatus.Left) Notice(NoticeType.PlayerLost, p, 0);
                if (!was.connected && p.connected && !quiet) Notice(NoticeType.PlayerBack, p, 0);
                if (!was.isHost && p.isHost && announced.Exists(a => a.isHost)) Notice(NoticeType.NewHost, p, 0);
            }
            foreach (var a in announced)
                if (Find(a.uid) == null && a.uid != Uid && a.status != PlayerStatus.Left) Notice(NoticeType.PlayerLeft, a, 0);

            var meNow = Me;
            if (meNow != null)
            {
                CoopPlayer meWas = announced.Find(a => a.uid == Uid);
                if (meWas != null && meWas.status == PlayerStatus.Racing && meNow.status == PlayerStatus.Disconnected) Notice(NoticeType.YouAreOut, meNow, 0);
            }
            if (!announcedSelection.Equals(Selection) && players.Count > 0 && announced.Count > 0) Notice(NoticeType.SelectionChanged, InSlot(Selection.chosenBy), 0);
            if (announcedPhase != Phase && Phase == SessionPhase.Over) Notice(NoticeType.RaceOver, null, 0);

            announced.Clear();
            foreach (var p in players) announced.Add(p.Clone());
            announcedSelection = Selection;
            announcedPhase = Phase;
        }

        // ---------- Lifetime ----------

        void Reset()
        {
            if (Role != SessionRole.None) Shutdown();
            players.Clear();
            peers.Clear();
            announced.Clear();
            latestMotions.Clear();
            sync.Reset();
            welcomed = false;
            hasSnapshot = false;
            lastVersion = 0;
            version = 0;
            RaceId = 0;
            Phase = SessionPhase.Lobby;
            announcedPhase = SessionPhase.Lobby;
            myStatus = PlayerStatus.Lobby;
            myReady = false;
            myLoadedRace = 0;
            raceStartKnown = raceStartLocked = false;
            migrateAt = double.PositiveInfinity;
            yieldTarget = null;
            leaving = false;
            shutdownAt = double.PositiveInfinity;
            InRaceScanning = false;
            freshJoin = false;
            SessionId = 0;
            Epoch = 0;
        }

        /// <summary>Let go of everything at once (no goodbye: use <see cref="Leave"/> for that).</summary>
        public void Shutdown()
        {
            if (Role == SessionRole.Host) link.StopHost();
            else if (Role == SessionRole.Client) link.Disconnect();
            link.StopScan();
            Role = SessionRole.None;
            Connection = ConnectionState.Idle;
            leaving = false;
            shutdownAt = double.PositiveInfinity;
            hostingStarted = false;
            peers.Clear();
            welcomed = false;
        }

        uint NewSessionId()
        {
            uint id = 0;
            while (id == 0) id = (uint)random.Next() ^ ((uint)random.Next() << 16) ^ Uid;
            return id;
        }

        static float Clamp01(float f) { return f < 0f ? 0f : f > 1f ? 1f : f; }
    }
}
