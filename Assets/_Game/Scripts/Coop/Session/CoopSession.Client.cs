using System;
using System.Collections.Generic;
using DribbleToSchool.Coop.Net;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// A player's side: joining (with retries), the clock sync, the reports to the host, the snapshots from it, and what to
    /// do when the host is lost: look for it, or for whoever took over, and take over in turn.
    /// </summary>
    public sealed partial class CoopSession
    {
        readonly Peer host = new Peer();
        readonly ClockSync sync = new ClockSync();
        readonly List<KeyValuePair<byte, CoopMotion>> motionsIn = new List<KeyValuePair<byte, CoopMotion>>();
        readonly List<CoopPlayer> knownOut = new List<CoopPlayer>();
        bool welcomed, connectPending;
        double connectStartedAt, nextPingAt, nextProfileAt, nextProgressAt, nextMotionAt, lastConnectAttempt = double.NegativeInfinity;
        ushort profileSeq, progressSeq;
        bool profileDirty, progressDirty;
        uint lastVersion;
        bool hasSnapshot;
        uint snapshotPhaseAtHost;
        int pingsSent;

        // Joining.
        bool freshJoin;
        string joinAddress, attemptAddress;
        int joinAttempts;
        double retryJoinAt = double.PositiveInfinity;

        // Lost host / migration.
        double lostAt, migrateAt = double.PositiveInfinity, scanningSince = double.PositiveInfinity;
        byte lostEpoch;
        int candidateIndex;
        readonly List<uint> candidates = new List<uint>();
        string yieldTarget;
        bool toldOut;

        /// <summary>
        /// Hosts that let us connect but never answered (a frozen or backgrounded host still advertising), kept until this phone
        /// is welcomed somewhere: it neither joins them nor hands its own race over to them.
        /// </summary>
        readonly Dictionary<string, Unanswered> failedAttempts = new Dictionary<string, Unanswered>();

        /// <summary>A host's failed attempts, and what it advertised then (a change means it is alive again).</summary>
        struct Unanswered
        {
            public int count;
            public RoomBeacon beacon;
            public double at;
        }

        double StartingEndsLocal { get { return IsHost ? phaseAtLocal : (sync.HasSync ? sync.ToLocal(snapshotPhaseAtHost) : clock.NowMs + CoopTiming.StartCountdown); } }
        bool SamplesEnough { get { return pingsSent >= 6; } }

        /// <summary>Join the lobby at <paramref name="address"/> (from <see cref="Rooms"/>).</summary>
        public void Join(string address)
        {
            Reset();
            browsing = false;
            link.StopScan();
            Role = SessionRole.Client;
            Connection = ConnectionState.Connecting;
            freshJoin = true;
            joinAddress = address;
            joinAttempts = 1;
            ConnectTo(address);
        }

        void ConnectTo(string address)
        {
            lastConnectAttempt = clock.NowMs;
            connectStartedAt = clock.NowMs;
            connectPending = true;
            attemptAddress = address;
            welcomed = false;
            host.rx.Reset();
            host.txNumber = 0;
            host.lastHeard = clock.NowMs;
            host.quietUntil = double.NegativeInfinity;
            link.Connect(address);
        }

        /// <summary>
        /// A connection attempt failed (refused, timed out, dropped before the welcome). A first join tries again a couple of
        /// times (Android's first connection often fails); a reconnection notes the host as unresponsive and moves on.
        /// </summary>
        void ConnectAttemptFailed(double now)
        {
            if (!connectPending && welcomed) return;
            connectPending = false;
            if (freshJoin && !welcomed)
            {
                if (joinAttempts < CoopTiming.JoinAttempts) { joinAttempts++; retryJoinAt = now + CoopTiming.JoinRetryDelay; return; }
                Notice(NoticeType.ConnectFailed, null, 0);
                Shutdown();
                return;
            }
            if (attemptAddress != null)
            {
                Unanswered u;
                failedAttempts.TryGetValue(attemptAddress, out u);
                CoopRoom room;
                if (rooms.TryGetValue(attemptAddress, out room)) u.beacon = room.beacon;
                u.count++;
                u.at = now;
                failedAttempts[attemptAddress] = u;
            }
        }

        void OnConnectedToHost(double now)
        {
            host.lastHeard = now;
            writer.Reset();
            CoopMessages.Write(writer, new HelloMsg { protocol = CoopMessages.Protocol, uid = Uid, sessionId = SessionId, name = myName, character = myCharacter, contentHash = ContentHash, tagSeed = TagSeed });
            SendToHost();
        }

        void SendToHost()
        {
            foreach (var packet in CoopFraming.Split(writer.Buffer, writer.Length, link.MaxPacket, host.txNumber++))
                link.Send(0, packet);
        }

        void TickClient(double now)
        {
            if (now >= retryJoinAt)
            {
                retryJoinAt = double.PositiveInfinity;
                link.Disconnect();
                ConnectTo(joinAddress);
                return;
            }

            // A connection that was never welcomed in time is given up (a first join tries again; a reconnection moves on).
            if (connectPending && !welcomed && now - connectStartedAt > CoopTiming.HelloTimeout)
            {
                link.Disconnect();
                ConnectAttemptFailed(now);
                if (Role == SessionRole.None) return;
            }

            if (Connection == ConnectionState.Joined)
            {
                if (now - host.lastHeard > CoopTiming.HeartbeatTimeout && now > host.quietUntil)
                {
                    link.Disconnect();
                    OnHostLost(now, false);
                    return;
                }
                if (now >= nextPingAt)
                {
                    nextPingAt = now + (sync.HasSync && SamplesEnough ? CoopTiming.PingInterval : CoopTiming.FastPingInterval);
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
            CoopMessages.Write(writer, new ProgressMsg { seq = ++progressSeq, raceId = RaceId, status = myStatus, leg = myLeg, progress = myProgress, finishMs = myFinishMs, outMs = myOutMs });
            SendToHost();
        }

        /// <summary>
        /// Every finish this phone knows, for a host that may have missed some. Only finishes: they come from the finisher's
        /// own phone, so they are facts wherever they are relayed from. Who is out is the host's call (a phone that was cut
        /// off and hosted alone for a while would have counted everyone else as gone), and each player reports their own.
        /// </summary>
        void SendKnown()
        {
            knownOut.Clear();
            foreach (var p in players)
                if (p.status == PlayerStatus.Finished && p.uid != Uid) knownOut.Add(p);
            if (knownOut.Count == 0) return;
            writer.Reset();
            CoopMessages.WriteKnown(writer, knownOut);
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
                    failedAttempts.Clear();
                    toldOut = false;
                    SessionId = welcome.sessionId;
                    Epoch = welcome.epoch;
                    Connection = ConnectionState.Joined;
                    migrateAt = double.PositiveInfinity;
                    link.StopScan();
                    sync.Reset();
                    jumpsAtLock = 0;
                    if (raceStartLocked) raceStartTrusted = false;   // (checked once against this host's clock)
                    pingsSent = 0;
                    nextPingAt = now;
                    lastVersion = 0;
                    hasSnapshot = false;
                    profileDirty = true;
                    progressDirty = true;
                    if (InRace) SendKnown();   // a host that took over may not know every result yet
                    if (wasLost) Notice(NoticeType.Reconnected, null, 0);
                    break;
                case MsgType.Reject:
                    r.U8();
                    int reason = r.U8();
                    link.Disconnect();
                    connectPending = false;
                    if (freshJoin || !InRace)
                    {
                        Notice(NoticeType.Rejected, null, reason);
                        Shutdown();
                    }
                    else ConnectAttemptFailed(now);   // turned away by a host that doesn't know us (a split): keep looking, or take over in turn
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
                        if (p != null && p.uid != Uid && p.status == PlayerStatus.Racing) { p.track.Add(kv.Value); p.progress = Clamp01(kv.Value.progress); }
                    }
                    break;
                case MsgType.Pong:
                    r.U8();
                    uint sent = r.U32();
                    uint hostMs = r.U32();
                    if (!r.Failed) sync.AddSample(sent, hostMs, now);
                    break;
                case MsgType.Busy:
                    host.quietUntil = now + CoopMessages.ReadBusy(r);
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
            if (announcedAny && !s.selection.Equals(Selection) && (s.phase == SessionPhase.Lobby || s.phase == SessionPhase.Starting)) myReady = false;
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
                p.name = CoopRules.CleanName(incoming.name);
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
                // The host's word on how far everyone got (the order of those who dropped out depends on it), except this
                // phone's own bar while it is racing, which never steps back.
                if (p.uid != Uid || incoming.status != PlayerStatus.Racing || incoming.progress > p.progress) p.progress = incoming.progress;
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
                myLeg = 0; myProgress = 0; myFinishMs = myOutMs = 0;
                raceStartKnown = raceStartLocked = false;
                raceStartTrusted = true;
                foreach (var p in players) p.track.Clear();
            }
            var me = Me;
            if (me != null && InRaceOf(s.phase))
            {
                // This phone's own run is the truth about it (it never stopped): until the host's copy agrees (a host that
                // listed it out, or missed its finish), tell it again.
                if (myStatus != me.status && myStatus != PlayerStatus.Lobby) progressDirty = true;
                hostHasMyFinish = me.status == PlayerStatus.Finished;
            }
            if (s.phase == SessionPhase.Lobby && (Phase == SessionPhase.Over || Phase == SessionPhase.Racing || Phase == SessionPhase.Loading))
            {
                myStatus = PlayerStatus.Lobby;
                myReady = false;
                myFinishMs = myOutMs = 0;
                raceStartKnown = raceStartLocked = false;
                raceStartTrusted = true;
            }
            if (me != null && me.status == PlayerStatus.Lobby && s.phase == SessionPhase.Lobby) myStatus = PlayerStatus.Lobby;
            if (s.phase != Phase)
            {
                Phase = s.phase;
                if (PhaseChanged != null) PhaseChanged(Phase);
            }
            RefreshRaceStart(now);
        }

        static bool InRaceOf(SessionPhase phase)
        {
            return phase == SessionPhase.Loading || phase == SessionPhase.Racing || phase == SessionPhase.Over;
        }

        /// <summary>
        /// The start time from the host's clock, until the race is under way; then it doesn't move again (a new host's estimate
        /// would differ by a few milliseconds and make the clock twitch). Except when it was wrong by a second or more: a start
        /// this phone had to guess (it never synced before taking over), or a clock that jumped since it was fixed.
        /// </summary>
        void RefreshRaceStart(double now)
        {
            if ((Phase != SessionPhase.Racing && Phase != SessionPhase.Over) || !sync.HasSync || snapshotPhaseAtHost == 0) return;
            double start = sync.ToLocal(snapshotPhaseAtHost);
            if (raceStartLocked)
            {
                bool doubtful = !raceStartTrusted || sync.Jumps != jumpsAtLock;
                if (!doubtful || sync.Samples < CoopTiming.ReanchorSamples) return;
                jumpsAtLock = sync.Jumps;
                raceStartTrusted = true;
                if (Math.Abs(start - raceStartLocal) < CoopTiming.ReanchorBeyond) return;
                raceStartLocal = start;
                return;
            }
            raceStartLocal = start;
            raceStartKnown = true;
            raceStartTrusted = true;
            if (now >= raceStartLocal)
            {
                raceStartLocked = true;
                jumpsAtLock = sync.Jumps;
            }
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
            connectPending = false;
            lostAt = now;
            lostEpoch = Epoch;
            // (hosts that never answered stay given up on: a frozen host keeps advertising its old, full lobby)
            var oldHost = players.Find(p => p.isHost);
            if (oldHost != null && oldHost.uid != Uid)
            {
                oldHost.connected = false;
                oldHost.lostSinceMs = now;
            }
            candidateIndex = candidates.IndexOf(Uid);
            if (candidateIndex < 0) candidateIndex = candidates.Count;
            migrateAt = InRace ? now + (graceful ? 500 : CoopTiming.ReconnectWindow) + candidateIndex * CoopTiming.MigrationStep : double.PositiveInfinity;
            scanningSince = Radio == RadioState.On ? clock.NowMs : double.PositiveInfinity;
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

            // Away longer than the grace period: the others now list this phone last (until it is back).
            if (!toldOut && myStatus == PlayerStatus.Racing && now - lostAt > CoopTiming.RaceGrace)
            {
                toldOut = true;
                Notice(NoticeType.YouAreOut, Me, 0);
            }

            if (!attempting && now >= migrateAt && Radio == RadioState.On && now - scanningSince >= CoopTiming.ScanBeforeHost
                && BestRoomForSession(now) == null)
                TakeOver(now);
        }

        /// <summary>
        /// A host that let us connect but never answered, twice: given up on, until its advertisement changes (it is running
        /// again: its player count, epoch or phase moves) or for <see cref="CoopTiming.GiveUpFor"/>.
        /// </summary>
        bool GivenUpOn(string address)
        {
            Unanswered u;
            if (address == null || !failedAttempts.TryGetValue(address, out u) || u.count < CoopTiming.ZombieAttempts) return false;
            CoopRoom room;
            bool changed = rooms.TryGetValue(address, out room)
                && (room.beacon.players != u.beacon.players || room.beacon.epoch != u.beacon.epoch || room.beacon.phase != u.beacon.phase);
            if (changed || clock.NowMs - u.at > CoopTiming.GiveUpFor)
            {
                failedAttempts.Remove(address);
                return false;
            }
            return true;
        }

        /// <summary>
        /// The lobby of this session the scan hears that the others would join: the one that would keep the race in a split
        /// (CoopRules.ShouldYieldTo), leaving out hosts older than the one lost and hosts that let us connect but never answered.
        /// </summary>
        CoopRoom BestRoomForSession(double now)
        {
            CoopRoom best = null;
            foreach (var room in rooms.Values)
            {
                if (room.beacon.sessionId != SessionId || now - room.lastSeenMs > CoopTiming.RoomExpiry * 0.6) continue;
                if (room.beacon.epoch < lostEpoch && yieldTarget == null) continue;   // an older host than the one we lost
                if (GivenUpOn(room.address)) continue;
                if (best == null || CoopRules.ShouldYieldTo(best.beacon, room.beacon)) best = room;
            }
            return best;
        }

        void TakeOver(double now)
        {
            link.Disconnect();
            Role = SessionRole.Host;
            Connection = ConnectionState.Hosting;
            // (a higher epoch than any host this phone has heard of, and its turn added, so two takers-over rarely clash;
            // when they do, the split rule settles it by seat)
            byte highest = lostEpoch;
            foreach (var room in rooms.Values)
                if (room.beacon.sessionId == SessionId && room.beacon.epoch > highest) highest = room.beacon.epoch;
            Epoch = (byte)Math.Min(RoomBeacon.MaxEpoch, highest + 1 + candidateIndex);
            migrateAt = double.PositiveInfinity;
            deafSince = double.PositiveInfinity;
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
                CoopRules.MergeResult(me, myStatus, myFinishMs, myOutMs);
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
                raceStartTrusted = false;
            }
            if (raceStartKnown) phaseAtLocal = raceStartLocal;
            version += 1000;
            quietUntil = now + CoopTiming.QuietAfterMigration;
            StartHosting();
            nextSplitScan = now;   // listen at once for a host this phone didn't hear
            dirty = true;
            Notice(NoticeType.YouAreHost, null, 0);
        }
    }
}
