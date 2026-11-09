using System;
using System.Collections.Generic;
using DribbleToSchool.Coop.Net;

namespace DribbleToSchool.Coop
{
    /// <summary>The host's side: the lobby, the race's phases, the players' reports, the snapshots and the motions relay.</summary>
    public sealed partial class CoopSession
    {
        readonly Dictionary<int, Peer> peers = new Dictionary<int, Peer>();
        readonly List<Peer> scratchPeers = new List<Peer>();
        readonly Dictionary<byte, CoopMotion> latestMotions = new Dictionary<byte, CoopMotion>();
        readonly List<KeyValuePair<byte, CoopMotion>> motionsOut = new List<KeyValuePair<byte, CoopMotion>>();
        readonly List<CoopPlayer> knownIn = new List<CoopPlayer>();
        uint version;
        bool dirty;
        double lastSnapshotAt = double.NegativeInfinity, nextMotionsAt;
        bool motionsFresh;
        double phaseAtLocal;   // Starting: countdown end; Racing: start (both in local ms)
        double loadDeadline;
        bool hostingStarted;
        RoomBeacon advertised;
        /// <summary>Since when this host can't hear anyone (its Bluetooth off, or its app in the background); +inf when it can.</summary>
        double deafSince = double.PositiveInfinity;
        bool splitScanning;
        double splitScanUntil, nextSplitScan;

        bool Deaf { get { return Radio != RadioState.On || appPaused; } }

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
            me.tag = CoopRules.UniqueTag(TagSeed, Uid, players);
            players.Add(me);
            Connection = ConnectionState.Hosting;
            StartHosting();
            dirty = true;
            Announce();
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
            myFinishMs = myOutMs = 0;
            raceStartKnown = raceStartLocked = false;
            raceStartTrusted = true;
            latestMotions.Clear();
            StopSplitScan();
            SetPhase(SessionPhase.Lobby);
            dirty = true;
        }

        void StartHosting()
        {
            advertised = MakeBeacon();
            link.StartHost(advertised);
            nextSplitScan = clock.NowMs + 1000;   // (during a race: listen for another host of this session soon)
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
                hostSlot = me != null ? me.slot : (byte)0,
                phase = Phase == SessionPhase.Over ? RoomPhase.Over : InRace ? RoomPhase.Racing : RoomPhase.Lobby,
                hostName = me != null ? me.name : "",
            };
        }

        void TickHost(double now)
        {
            var me = Me;
            if (me != null) me.lastHeardMs = now;

            // A host that can't hear anyone for a while in a race stops being the host (see HostDeafGrace).
            if (Deaf)
            {
                if (InRace && now - deafSince > CoopTiming.HostDeafGrace) { StepDown(now); return; }
            }
            else
            {
                // Players who have not said hello, or have gone quiet.
                scratchPeers.Clear();
                scratchPeers.AddRange(peers.Values);
                foreach (var peer in scratchPeers)
                {
                    if (peer.uid == 0 && (now - peer.connectedAt > CoopTiming.HelloTimeout || now - peer.rejectedAt > 1500)) { link.Kick(peer.id); peers.Remove(peer.id); continue; }
                    if (peer.TimedOut(now)) { link.Kick(peer.id); DropPeer(peer.id, now, true); }
                }

                // Seats held for players who dropped out, and disqualification after the grace period (never while deaf: a host
                // that can't hear is in no position to judge).
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
                TickSplitScan(now);
            }

            StepPhase(now);

            var beacon = MakeBeacon();
            if (beacon.players != advertised.players || beacon.phase != advertised.phase || beacon.epoch != advertised.epoch
                || beacon.hostName != advertised.hostName || beacon.hostSlot != advertised.hostSlot)
            {
                advertised = beacon;
                if (!Deaf) link.UpdateBeacon(beacon);
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

        /// <summary>During a race, now and then, listen for another host of this session (two halves of a split lobby).</summary>
        void TickSplitScan(double now)
        {
            if (!InRace) { StopSplitScan(); return; }
            if (!splitScanning && now >= nextSplitScan)
            {
                splitScanning = true;
                splitScanUntil = now + CoopTiming.SplitScanFor;
                link.StartScan();
            }
            else if (splitScanning && now >= splitScanUntil) StopSplitScan();
        }

        void StopSplitScan()
        {
            if (!splitScanning) return;
            splitScanning = false;
            nextSplitScan = clock.NowMs + CoopTiming.SplitScanEvery;
            link.StopScan();
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
                    // A player listed out who turns up still racing reopens the race (results stay open until NewRace).
                    foreach (var p in players)
                        if (p.status == PlayerStatus.Racing) { SetPhase(SessionPhase.Racing); break; }
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
            myLeg = 0; myProgress = 0; myFinishMs = myOutMs = 0;
            raceStartKnown = raceStartLocked = false;
            raceStartTrusted = true;
            latestMotions.Clear();
            loadDeadline = now + CoopTiming.LoadTimeout;
            nextSplitScan = now + CoopTiming.SplitScanEvery;
            SetPhase(SessionPhase.Loading);
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
            if (type == MsgType.Busy) { peer.quietUntil = now + CoopMessages.ReadBusy(r); return; }
            var p = peer.uid != 0 ? Find(peer.uid) : null;
            if (p == null) return;   // nothing but Hello before a seat
            p.lastHeardMs = now;
            switch (type)
            {
                case MsgType.Ping:
                    r.U8();
                    uint sent = r.U32();
                    if (r.Failed) break;
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
                case MsgType.Known:
                    if (CoopMessages.ReadKnown(r, knownIn)) MergeKnown(knownIn, now);
                    break;
                case MsgType.Motion:
                    CoopMotion motion;
                    if (!CoopMessages.ReadMotion(r, out motion) || p.status != PlayerStatus.Racing) break;
                    latestMotions[p.slot] = motion;
                    p.progress = Clamp01(motion.progress);
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
            if (hello.protocol != CoopMessages.Protocol || (hello.contentHash != 0 && ContentHash != 0 && hello.contentHash != ContentHash))
            {
                Reject(peer, RejectReason.Version);
                return;
            }
            // Removed by this host: not back into this lobby (by this launch's id, or the install's tag seed after a relaunch).
            if (removedUids.Contains(hello.uid) || (hello.tagSeed != 0 && removedSeeds.Contains(hello.tagSeed)))
            {
                Reject(peer, RejectReason.Removed);
                return;
            }
            peer.tagSeed = hello.tagSeed;
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
                known.tag = CoopRules.UniqueTag(hello.tagSeed != 0 ? hello.tagSeed : hello.uid, hello.uid, players);
                players.Add(known);
                if (Phase == SessionPhase.Starting) SetPhase(SessionPhase.Lobby);
            }
            else if (known.uid == Uid)
            {
                Reject(peer, RejectReason.InProgress);   // (our own id from another phone: a copied install)
                return;
            }
            // A player who was here before gets their seat (and their race) back: listed out for being away, they race on
            // (their own report then says how far they got, or that they finished).
            if (known.status == PlayerStatus.Disconnected && InRace) known.status = PlayerStatus.Racing;
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

        readonly HashSet<uint> removedUids = new HashSet<uint>(), removedSeeds = new HashSet<uint>();

        /// <summary>
        /// Host, in the lobby: send a player away (someone nearby who joined uninvited, a name that shouldn't be shown). They
        /// are told, their seat is freed, and they can't join this lobby again. False when there is no such player here, or
        /// a race is under way (a race's players are only ever listed out or left).
        /// </summary>
        public bool RemovePlayer(uint uid)
        {
            if (Role != SessionRole.Host || InRace || uid == Uid || leaving) return false;
            var p = Find(uid);
            if (p == null) return false;
            removedUids.Add(uid);
            Peer peer;
            if (p.peer >= 0 && peers.TryGetValue(p.peer, out peer))
            {
                if (peer.tagSeed != 0) removedSeeds.Add(peer.tagSeed);
                Reject(peer, RejectReason.Removed);
            }
            players.Remove(p);
            if (Phase == SessionPhase.Starting) SetPhase(SessionPhase.Lobby);
            dirty = true;
            return true;
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
            if (p.status == PlayerStatus.Racing) p.progress = Math.Max(p.progress, Clamp01(m.progress));
            uint outMs = m.status == PlayerStatus.Left && m.outMs == 0 ? (uint)Math.Max(0, RaceTimeMs) : m.outMs;
            if (CoopRules.MergeResult(p, m.status, m.finishMs, outMs))
            {
                CoopRules.AssignPlaces(players);
                dirty = true;
            }
        }

        /// <summary>
        /// A phone that (re)joined told us every finish it knows: one this host missed (it took over before the finish reached
        /// it, say) is merged in, so a winner who has since gone stays the winner.
        /// </summary>
        void MergeKnown(List<CoopPlayer> known, double now)
        {
            if (!InRace) return;
            bool changed = false;
            foreach (var k in known)
            {
                if (k.status != PlayerStatus.Finished) continue;   // (only finishes are relayed: see SendKnown)
                var p = Find(k.uid);
                if (p == null)
                {
                    // Someone this host never heard of (it took over from an old copy of the lobby): give them a seat, as gone.
                    int slot = InSlot(k.slot) == null ? k.slot : CoopRules.FreeSlot(players);
                    if (slot < 0) continue;
                    p = new CoopPlayer { uid = k.uid, slot = (byte)slot, name = CoopRules.CleanName(k.name), character = k.character, connected = false, lostSinceMs = now, status = PlayerStatus.Racing };
                    p.tag = CoopRules.UniqueTag(k.uid, players);
                    players.Add(p);
                    changed = true;
                }
                changed |= CoopRules.MergeResult(p, k.status, k.finishMs, k.outMs);
            }
            if (!changed) return;
            CoopRules.AssignPlaces(players);
            dirty = true;
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

        /// <summary>This host can't hear anyone (its Bluetooth went off, or its app went to the background).</summary>
        void GoDeaf(double now)
        {
            hostingStarted = false;
            if (double.IsPositiveInfinity(deafSince)) deafSince = now;
            splitScanning = false;
            scratchPeers.Clear();
            scratchPeers.AddRange(peers.Values);
            foreach (var peer in scratchPeers) DropPeer(peer.id, now, false);
        }

        /// <summary>
        /// Hearing again within the grace period: host again, and the players lost meanwhile get a fresh grace period (it was
        /// this host that was away, not them).
        /// </summary>
        void RecoverHearing(double now)
        {
            if (Deaf) return;
            if (InRace && now - deafSince > CoopTiming.HostDeafGrace) { StepDown(now); return; }
            foreach (var p in players)
                if (!p.connected && p.uid != Uid && p.lostSinceMs >= deafSince - 1) p.lostSinceMs = now;
            deafSince = double.PositiveInfinity;
            StartHosting();
        }

        /// <summary>
        /// Away too long to stay the host: hand the race to the others (who will have taken over, or will) and look for them
        /// as a player. This phone is last in line to take over again.
        /// </summary>
        void StepDown(double now)
        {
            link.StopHost();
            StopSplitScan();
            peers.Clear();
            hostingStarted = false;
            double since = double.IsPositiveInfinity(deafSince) ? now : deafSince;
            deafSince = double.PositiveInfinity;
            candidates.Clear();
            var order = new List<CoopPlayer>(players);
            order.Sort((a, b) => a.slot.CompareTo(b.slot));
            foreach (var p in order)
            {
                p.isHost = false;
                if (p.uid != Uid && p.status != PlayerStatus.Left) candidates.Add(p.uid);
            }
            Role = SessionRole.Client;
            BeginLost(since, false);
            Notice(NoticeType.ConnectionLost, null, 0);
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

        /// <summary>Another host of this session should keep the race (after a split): hand over and join it.</summary>
        void YieldTo(string address, double now)
        {
            link.StopHost();
            StopSplitScan();
            peers.Clear();
            hostingStarted = false;
            Role = SessionRole.Client;
            foreach (var p in players) { p.isHost = false; if (p.uid != Uid) p.connected = false; }
            BeginLost(now, true);
            migrateAt = now + CoopTiming.RaceGrace;   // it was told to join the other host: no quick take-over
            yieldTarget = address;
            ConnectTo(address);
        }

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
            if (CoopRules.MergeResult(me, myStatus, myFinishMs, myOutMs)) CoopRules.AssignPlaces(players);
            dirty = true;
        }
    }
}
