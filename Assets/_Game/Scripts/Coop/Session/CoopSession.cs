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
        /// <summary>A race start that was guessed, or fixed before a clock jumped, is checked against this many fresh samples...</summary>
        public const int ReanchorSamples = 3;
        /// <summary>...and moved when it is out by more than this (less is a few milliseconds of estimate: left alone).</summary>
        public const double ReanchorBeyond = 1000;
        public const double RoomExpiry = 4000;
        public const double ConnectRetry = 1500;
        public const double LeaveFlush = 400;
        /// <summary>After a change of host, players losing and finding the connection again are not announced one by one.</summary>
        public const double QuietAfterMigration = 6000;
        /// <summary>
        /// A host whose own Bluetooth is off (or whose app is in the background) this long during a race stops being the host:
        /// the others take over, and it joins them when it is back (it never judges the others for its own absence).
        /// </summary>
        public const double HostDeafGrace = 3000;
        /// <summary>A frame longer than this (a scene loading, the app frozen) is this phone's own stall, not the others' silence.</summary>
        public const double StallThreshold = 400;
        /// <summary>At most this much of one stall is forgiven (longer is the app in the background: really away).</summary>
        public const double StallForgiveMax = 10000;
        /// <summary>The longest quiet a Busy message may announce.</summary>
        public const double MaxBusy = 15000;
        /// <summary>A host that keeps advertising but doesn't answer this many attempts in a row is given up on.</summary>
        public const int ZombieAttempts = 2;
        /// <summary>... for this long at most (or until its advertisement changes: it is running again).</summary>
        public const double GiveUpFor = 30000;
        /// <summary>A first join is tried this many times (Android's first connection often fails with status 133).</summary>
        public const int JoinAttempts = 3;
        public const double JoinRetryDelay = 600;
        /// <summary>During a race the host listens for another host of its session (after a split) this long, this often.</summary>
        public const double SplitScanFor = 4000;
        public const double SplitScanEvery = 12000;
    }

    /// <summary>
    /// One phone's side of a co-op lobby and race, over any <see cref="ICoopLink"/>. The host keeps the lobby (who is in it,
    /// the stage, the race) and sends it to everyone; each phone runs its own kid in its own copy of the level and reports
    /// where it is and when it got to school, so the race never waits on the radio: a phone that loses the connection keeps
    /// playing and catches up when it is back. The race clock is the host's, shared through pings, so the start (3, 2, 1, GO)
    /// is the same instant on every phone and every finish time is measured from it.
    ///
    /// Resilience (docs/COOP.md): a racing player out of touch for <see cref="CoopTiming.RaceGrace"/> is disqualified and
    /// listed last; the race goes on for everyone else. Results are sticky and merged from every phone (CoopRules.MergeResult):
    /// a finish survives the finisher leaving and the host changing. When the host goes (switched off, out of range, left,
    /// in the background), the others first look for it, then the next player by slot takes over as host with the same session
    /// (a higher epoch) and everyone joins them. A phone's own stalls (a scene loading) never count against the others.
    /// Pure C# (no Unity): Tests/Editor/CoopSessionTests run whole races, and storms of failures, on an in-memory radio.
    ///
    /// The class is split by role: this file (the shared state, what the game calls, the radio's events, notices),
    /// CoopSession.Host.cs and CoopSession.Client.cs.
    /// </summary>
    public sealed partial class CoopSession
    {
        sealed class Peer
        {
            public int id;
            public readonly Reassembler rx = new Reassembler();
            public int txNumber;
            public double connectedAt;
            public double lastHeard;
            /// <summary>The other end said it would be quiet until then (Busy: loading a scene).</summary>
            public double quietUntil = double.NegativeInfinity;
            public uint uid;   // 0 until Hello
            public uint tagSeed;   // (from Hello: what a removed player's install is known by)
            public double rejectedAt = double.PositiveInfinity;

            public bool TimedOut(double now)
            {
                return now - lastHeard > CoopTiming.HeartbeatTimeout && now > quietUntil;
            }
        }

        /// <summary>What a player looked like when last announced (to tell what changed; no allocation per frame).</summary>
        struct Announced
        {
            public uint uid;
            public PlayerStatus status;
            public bool connected, isHost;
        }

        readonly ICoopLink link;
        readonly ICoopClock clock;
        readonly ByteWriter writer = new ByteWriter(512);
        readonly List<CoopPlayer> players = new List<CoopPlayer>();
        readonly Dictionary<string, CoopRoom> rooms = new Dictionary<string, CoopRoom>();
        readonly Random random;
        double lastTickAt = double.NaN;
        bool browsing;
        bool leaving;
        double shutdownAt = double.PositiveInfinity;

        // The local player's own intentions, kept across hosts.
        string myName;
        byte myCharacter;
        bool myReady;
        byte myLoadedRace;
        PlayerStatus myStatus = PlayerStatus.Lobby;
        byte myLeg;
        float myProgress;
        uint myFinishMs, myOutMs;
        CoopMotion myMotion;
        bool myMotionFresh;
        double raceStartLocal;
        bool raceStartKnown, raceStartLocked;
        /// <summary>
        /// The race start agrees with the host's clock: it came from it, and nothing since (a start guessed while taking over,
        /// a reconnection, a clock seen to jump) has put it in doubt. <see cref="jumpsAtLock"/>: the sync's jumps when it was checked.
        /// </summary>
        bool raceStartTrusted = true;
        int jumpsAtLock;

        // Notices.
        readonly List<Announced> announced = new List<Announced>(CoopRules.MaxPlayers * 2);
        bool announcedAny;
        CoopSelection announcedSelection;
        SessionPhase announcedPhase;
        double quietUntil = double.NegativeInfinity;

        /// <param name="uid">This phone's player id for this run of the app (fresh each launch: a backed-up copy of the game
        /// on a second phone must never share it).</param>
        /// <param name="tagSeed">What its tag is made from, kept on the phone (0: from <paramref name="uid"/>).</param>
        public CoopSession(ICoopLink link, ICoopClock clock, uint uid, string name, byte character, int seed = 0, uint tagSeed = 0)
        {
            this.link = link;
            this.clock = clock;
            Uid = uid == 0 ? 1u : uid;
            TagSeed = tagSeed != 0 ? tagSeed : Uid;
            myName = CoopRules.CleanName(name);
            myCharacter = character;
            random = new Random(seed != 0 ? seed : (int)(Uid ^ (uint)Environment.TickCount));
            Radio = link.State;
        }

        // ---------- What the game reads ----------

        public uint Uid { get; private set; }
        public uint TagSeed { get; private set; }
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
        /// <summary>
        /// Whether a location has a route's streets (route, location; set by the game: Florida has only the beach so far). Random
        /// choices only pick a pair that fits, and a chosen location that doesn't fit the route runs in the first (the original).
        /// Null: every location has every route.
        /// </summary>
        public Func<int, int, bool> LocationFits;
        /// <summary>
        /// A fingerprint of what the race refers to by index (the kids, routes and locations; set by the game). A phone whose
        /// fingerprint differs is turned away as another version (0 on either side: not checked).
        /// </summary>
        public uint ContentHash;
        public IList<CoopPlayer> Players { get { return players; } }
        public ICollection<CoopRoom> Rooms { get { return rooms.Values; } }
        public bool InSession { get { return Role != SessionRole.None; } }
        public bool IsHost { get { return Role == SessionRole.Host; } }
        /// <summary>Scanning for the Join list.</summary>
        public bool Browsing { get { return browsing && Role == SessionRole.None; } }
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
        public bool MyReady { get { return myReady; } }
        /// <summary>When the connection was lost (Reconnecting), for the HUD's countdown to being listed out.</summary>
        public double LostForMs { get { return Connection == ConnectionState.Reconnecting ? clock.NowMs - lostAt : 0; } }
        /// <summary>
        /// The others list this phone last: it has been out of touch longer than the grace period (or the lobby says so). Its
        /// run carries on, and counts again as soon as it is back in touch (before the next race).
        /// </summary>
        public bool ListedOut
        {
            get
            {
                if (myStatus != PlayerStatus.Racing || !InRace) return false;
                if (Connection == ConnectionState.Reconnecting && clock.NowMs - lostAt > CoopTiming.RaceGrace) return true;
                var me = Me;
                return me != null && me.status == PlayerStatus.Disconnected && Connection != ConnectionState.Joined;
            }
        }
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
        /// <summary>Leaving has finished (or there was nothing to leave).</summary>
        public bool Left { get { return Role == SessionRole.None; } }
        /// <summary>Leave was called and the goodbye is on its way (the session ends in a moment).</summary>
        public bool Leaving { get { return leaving; } }
        /// <summary>
        /// This phone's kid is at school, but no snapshot from the host has listed the finish yet: leaving now (or the app
        /// closing) could lose it, as no other phone knows of it. (A host's own finish is in what it sends.)
        /// </summary>
        public bool FinishUnconfirmed { get { return myStatus == PlayerStatus.Finished && Role == SessionRole.Client && !hostHasMyFinish; } }
        bool hostHasMyFinish;

        public event Action<CoopNotice> Noticed;
        public event Action<SessionPhase> PhaseChanged;

        public CoopPlayer Find(uint uid)
        {
            for (int i = 0; i < players.Count; i++) if (players[i].uid == uid) return players[i];
            return null;
        }

        public CoopPlayer InSlot(int slot)
        {
            for (int i = 0; i < players.Count; i++) if (players[i].slot == slot) return players[i];
            return null;
        }

        bool InRace { get { return Phase == SessionPhase.Loading || Phase == SessionPhase.Racing || Phase == SessionPhase.Over; } }

        // ---------- What the game does ----------

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

        /// <summary>Leave the lobby or the race: the others are told (a finished time is kept), then the radio lets go.</summary>
        public void Leave()
        {
            if (Role == SessionRole.None || leaving) return;
            bool race = InRace;
            if (myStatus == PlayerStatus.Racing && race)
            {
                myStatus = PlayerStatus.Left;
                myOutMs = (uint)Math.Max(0, RaceTimeMs);
                var me = Me;
                if (me != null) { me.status = PlayerStatus.Left; me.outMs = myOutMs; }
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

        public void SetName(string name)
        {
            myName = CoopRules.CleanName(name);
            ApplyProfile();
        }

        public void SetCharacter(byte character)
        {
            if (character == myCharacter) return;
            myCharacter = character;
            ApplyProfile();
        }

        public void SetReady(bool ready)
        {
            myReady = ready;
            ApplyProfile();
        }

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
            if (myStatus == PlayerStatus.Racing) myProgress = Clamp01(progress);
            if (changed) { progressDirty = true; ApplyProgressToMe(); }
        }

        /// <summary>Where this phone's kid and ball are now (sent ten times a second while racing).</summary>
        public void ReportMotion(CoopMotion m)
        {
            if (!raceStartKnown || myStatus != PlayerStatus.Racing) return;
            m.raceMs = (uint)Math.Max(0, RaceTimeMs);
            m.leg = myLeg;
            m.progress = myProgress = Clamp01(m.progress);
            myMotion = m;
            myMotionFresh = true;
            var me = IsHost ? Me : null;
            if (me != null)
            {
                latestMotions[me.slot] = m;
                motionsFresh = true;
                me.progress = myProgress;
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

        /// <summary>
        /// This phone is about to go quiet for up to <paramref name="ms"/> (loading the next scene): the other end is told, so
        /// it doesn't take the silence for a lost connection. This phone forgives its own stall in any case (Tick).
        /// </summary>
        public void ExpectSilence(double ms)
        {
            ms = Math.Max(0, Math.Min(CoopTiming.MaxBusy, ms));
            writer.Reset();
            CoopMessages.WriteBusy(writer, ms);
            if (IsHost) Broadcast();
            else if (welcomed) SendToHost();
        }

        /// <summary>
        /// The app went to the background (or came back). A host in the background is no host (iOS stops its radio, Android
        /// keeps advertising a lobby nobody answers), so it stops hosting at once; back within <see cref="CoopTiming.HostDeafGrace"/>
        /// it carries on, later it hands the race over and joins whoever took it. A player's phone needs nothing: its silence
        /// is handled like any other.
        /// </summary>
        public void SetAppPaused(bool paused)
        {
            if (appPaused == paused) return;
            appPaused = paused;
            double now = clock.NowMs;
            if (paused) pausedAt = now;
            if (Role != SessionRole.Host) return;
            if (KeepHostingWhilePaused)
            {
                // Back from a short pause (Control Center pulled down, a notification): nothing changed. Back from a long one:
                // the others have taken the race over meanwhile, or will: hand it over.
                if (!paused && InRace && now - pausedAt > CoopTiming.HostDeafGrace)
                {
                    deafSince = pausedAt;
                    StepDown(now);
                }
                return;
            }
            if (paused)
            {
                link.StopHost();
                GoDeaf(now);
            }
            else RecoverHearing(now);
        }

        /// <summary>
        /// iOS: a pause doesn't stop hosting at once. iOS pauses the game for Control Center or a notification too, while
        /// the radio carries on; stopping would drop every player for a glance. (An app that really goes to the background
        /// is suspended, its radio with it: the others take over as for any lost host.) Android: the plugin would keep
        /// advertising a lobby nobody answers, so a paused host stops at once (the default).
        /// </summary>
        public bool KeepHostingWhilePaused;

        bool appPaused;
        double pausedAt;

        /// <summary>Call once a frame: handles the radio, the timers and the sending.</summary>
        public void Tick()
        {
            double now = clock.NowMs;
            // A long frame is this phone's own stall (a scene loading): the others' silence during it doesn't count.
            if (!double.IsNaN(lastTickAt))
            {
                double gap = now - lastTickAt;
                if (gap > CoopTiming.StallThreshold) Forgive(Math.Min(gap, CoopTiming.StallForgiveMax));
            }
            lastTickAt = now;

            LinkEvent e;
            int guard = 0;
            while (guard++ < 1024 && link.Poll(out e)) Handle(e, now);

            if (leaving && now >= shutdownAt) { Shutdown(); return; }

            ExpireRooms(now);
            if (Role == SessionRole.Host) TickHost(now);
            else if (Role == SessionRole.Client) TickClient(now);
            Announce();
        }

        /// <summary>Shifts every "last heard" and "lost since" by the length of this phone's own stall.</summary>
        void Forgive(double stall)
        {
            foreach (var peer in peers.Values) { peer.lastHeard += stall; peer.connectedAt += stall; }
            foreach (var p in players) if (!p.connected) p.lostSinceMs += stall;
            host.lastHeard += stall;
            connectStartedAt += stall;
            if (Connection == ConnectionState.Reconnecting)
            {
                lostAt += stall;
                migrateAt += stall;
                scanningSince += stall;
            }
            foreach (var room in rooms.Values) room.lastSeenMs += stall;
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
                    else if (Role == SessionRole.Client && e.peer == 0) { if (welcomed) OnHostLost(now, false); else ConnectAttemptFailed(now); }
                    break;
                case LinkEventType.Data: OnData(e, now); break;
                case LinkEventType.HostStarted: hostingStarted = true; break;
                case LinkEventType.HostFailed:
                    hostingStarted = false;
                    Notice(NoticeType.HostFailed, null, 0);
                    // A lobby nobody could find, with nobody in it: there is no lobby. (A race carries on: the others
                    // still have it, and this phone's run counts.)
                    if (Role == SessionRole.Host && Phase == SessionPhase.Lobby && peers.Count == 0) Reset();
                    break;
                case LinkEventType.ConnectFailed:
                    if (Role == SessionRole.Client) ConnectAttemptFailed(now);
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
                splitScanning = false;
                if (Role == SessionRole.Host) GoDeaf(now);
                else if (Role == SessionRole.Client && Connection != ConnectionState.Reconnecting)
                {
                    if (freshJoin && !welcomed) { Notice(NoticeType.ConnectFailed, null, 0); Shutdown(); }
                    else OnHostLost(now, false);
                }
                return;
            }
            if (before != RadioState.Unknown) Notice(NoticeType.RadioOn, null, 0);
            if (Role == SessionRole.Host) RecoverHearing(now);
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
            // An Android host's address can change while it advertises (privacy rotation): the same host heard under an
            // older address is one room, not two.
            expired.Clear();
            foreach (var kv in rooms)
            {
                var b = kv.Value.beacon;
                if (kv.Value != room && b.sessionId == e.beacon.sessionId && b.epoch == e.beacon.epoch && b.hostSlot == e.beacon.hostSlot
                    && kv.Key != joinAddress && kv.Key != attemptAddress)
                    expired.Add(kv.Key);
            }
            foreach (var key in expired) rooms.Remove(key);

            // A host racing beside another host of the same session (after a split): one of the two steps down.
            if (Role == SessionRole.Host && InRace && e.beacon.sessionId == SessionId && CoopRules.ShouldYieldTo(advertised, e.beacon)
                && !GivenUpOn(e.address))
                YieldTo(e.address, now);
        }

        readonly List<string> expired = new List<string>();

        void ExpireRooms(double now)
        {
            expired.Clear();
            foreach (var kv in rooms)
                if (now - kv.Value.lastSeenMs > CoopTiming.RoomExpiry) expired.Add(kv.Key);
            foreach (var key in expired) rooms.Remove(key);
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

        void SetPhase(SessionPhase phase)
        {
            if (Phase == phase) return;
            Phase = phase;
            dirty = true;
            if (PhaseChanged != null) PhaseChanged(phase);
        }

        // ---------- Notices ----------

        void Notice(NoticeType type, CoopPlayer player, int code)
        {
            if (Noticed != null) Noticed(new CoopNotice { type = type, player = player != null ? player.Clone() : null, code = code });
        }

        int AnnouncedIndex(uint uid)
        {
            for (int i = 0; i < announced.Count; i++) if (announced[i].uid == uid) return i;
            return -1;
        }

        /// <summary>What changed since the last frame, as notices (the same on the host and on the players' phones).</summary>
        void Announce()
        {
            bool quiet = clock.NowMs < quietUntil;
            bool hadHost = false;
            for (int i = 0; i < announced.Count; i++) if (announced[i].isHost) hadHost = true;
            for (int i = 0; i < players.Count; i++)
            {
                var p = players[i];
                int w = AnnouncedIndex(p.uid);
                if (p.uid == Uid) continue;
                if (w < 0) { if (announcedAny) Notice(NoticeType.PlayerJoined, p, 0); continue; }
                var was = announced[w];
                if (was.status != p.status)
                {
                    if (p.status == PlayerStatus.Finished) Notice(NoticeType.PlayerFinished, p, p.place);
                    else if (p.status == PlayerStatus.Disconnected) Notice(NoticeType.PlayerOut, p, 0);
                    else if (p.status == PlayerStatus.Left) Notice(NoticeType.PlayerLeft, p, 0);
                    else if (p.status == PlayerStatus.Racing && was.status == PlayerStatus.Disconnected) Notice(NoticeType.PlayerBack, p, 1);
                }
                if (was.connected && !p.connected && !quiet && p.status != PlayerStatus.Left) Notice(NoticeType.PlayerLost, p, 0);
                if (!was.connected && p.connected && !quiet) Notice(NoticeType.PlayerBack, p, 0);
                if (!was.isHost && p.isHost && hadHost) Notice(NoticeType.NewHost, p, 0);
            }
            for (int i = 0; i < announced.Count; i++)
            {
                var a = announced[i];
                if (a.uid != Uid && Find(a.uid) == null && a.status != PlayerStatus.Left)
                    Notice(NoticeType.PlayerLeft, new CoopPlayer { uid = a.uid, status = PlayerStatus.Left }, 0);
            }
            if (!announcedSelection.Equals(Selection) && announcedAny) Notice(NoticeType.SelectionChanged, InSlot(Selection.chosenBy), 0);
            if (announcedPhase != Phase && Phase == SessionPhase.Over) Notice(NoticeType.RaceOver, null, 0);

            announced.Clear();
            for (int i = 0; i < players.Count; i++)
            {
                var p = players[i];
                announced.Add(new Announced { uid = p.uid, status = p.status, connected = p.connected, isHost = p.isHost });
            }
            announcedAny = players.Count > 0;
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
            announcedAny = false;
            latestMotions.Clear();
            sync.Reset();
            jumpsAtLock = 0;
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
            myFinishMs = myOutMs = 0;
            raceStartKnown = raceStartLocked = false;
            raceStartTrusted = true;
            migrateAt = double.PositiveInfinity;
            deafSince = double.PositiveInfinity;
            yieldTarget = null;
            leaving = false;
            shutdownAt = double.PositiveInfinity;
            splitScanning = false;
            freshJoin = false;
            joinAttempts = 0;
            failedAttempts.Clear();
            removedUids.Clear();
            removedSeeds.Clear();
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
            connectPending = false;
            retryJoinAt = double.PositiveInfinity;
            if (browsing) link.StartScan();   // (back to the Join list)
        }

        uint NewSessionId()
        {
            // (24 bits: the iOS beacon carries no more)
            uint id = 0;
            while (id == 0) id = ((uint)random.Next() ^ ((uint)random.Next() << 16) ^ Uid) & RoomBeacon.SessionMask;
            return id;
        }

        static float Clamp01(float f) { return f < 0f ? 0f : f > 1f ? 1f : f; }
    }
}
