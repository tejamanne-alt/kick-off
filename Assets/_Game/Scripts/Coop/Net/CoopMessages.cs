using System;
using System.Collections.Generic;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>The first byte of every co-op message.</summary>
    public enum MsgType : byte
    {
        /// <summary>Player to host, on connecting: who I am (install id, name, kid), and the session I was in, if any.</summary>
        Hello = 1,
        /// <summary>Host to player: you're in, at this slot with this tag.</summary>
        Welcome = 2,
        /// <summary>Host to player: you can't join (<see cref="RejectReason"/>).</summary>
        Reject = 3,
        /// <summary>Host to everyone: the whole lobby (phase, stage, every player and their race), versioned.</summary>
        Snapshot = 4,
        /// <summary>Player to host: my name, kid, ready, and the race I've loaded.</summary>
        Profile = 5,
        /// <summary>Player to host: my race: status, leg, how far, my time at the school gate.</summary>
        Progress = 6,
        /// <summary>Player to host: where my kid and ball are now (ten times a second while racing).</summary>
        Motion = 7,
        /// <summary>Host to everyone: every racing player's latest motion.</summary>
        Motions = 8,
        /// <summary>Player to host: a clock ping (and a heartbeat).</summary>
        Ping = 9,
        /// <summary>Host to player: the ping, stamped with the host's clock.</summary>
        Pong = 10,
        /// <summary>Player to host: I choose this stage and location.</summary>
        Select = 11,
        /// <summary>Player to host: I'm leaving (gracefully).</summary>
        Leave = 12,
        /// <summary>Host to everyone: the host closed the lobby (only before a race).</summary>
        Closing = 13,
        /// <summary>Host to everyone: the host is leaving a race in progress: elect the next host now.</summary>
        HostLeaving = 14,
        /// <summary>Either way: I am about to go quiet for a moment (loading the next scene): don't count it as a lost connection.</summary>
        Busy = 15,
        /// <summary>
        /// Player to host, on (re)joining: every result this phone knows (who finished, when; who is out), so a host that took
        /// over without hearing of them learns them. The host merges them (CoopRules' sticky results).
        /// </summary>
        Known = 16,
    }

    public enum RejectReason : byte
    {
        Full = 1,
        /// <summary>A race is under way: only players who were in it can come back.</summary>
        InProgress = 2,
        /// <summary>The two phones run different versions of the co-op protocol: update the game.</summary>
        Version = 3,
        /// <summary>The host removed this player from the lobby (they can't join it again).</summary>
        Removed = 4,
    }

    public struct HelloMsg
    {
        public byte protocol;
        public uint uid;
        public uint sessionId;
        public string name;
        public byte character;
        /// <summary>A fingerprint of the content the race refers to by index (the kids, the routes, the locations): two builds
        /// that list them differently can't race each other (0: not checked).</summary>
        public uint contentHash;
        /// <summary>What this phone's tag is made from (kept on the phone, so friends see the same tag every time).</summary>
        public uint tagSeed;
    }

    public struct WelcomeMsg
    {
        public uint sessionId;
        public byte epoch;
        public byte slot;
        public string tag;
    }

    public struct ProfileMsg
    {
        public ushort seq;
        public string name;
        public byte character;
        public bool ready;
        public byte loadedRace;
    }

    public struct ProgressMsg
    {
        public ushort seq;
        public byte raceId;
        public PlayerStatus status;
        public byte leg;
        public float progress;
        public uint finishMs;
        /// <summary>When this player dropped out or left (Disconnected, Left), as a host told it or as it left.</summary>
        public uint outMs;
    }

    public struct SelectMsg
    {
        public byte route;
        public byte addOn;
    }

    /// <summary>The whole lobby as the host sends it.</summary>
    public sealed class SnapshotMsg
    {
        public uint version;
        public uint sessionId;
        public byte epoch;
        public SessionPhase phase;
        public byte raceId;
        public CoopSelection selection;
        /// <summary>The selection the race actually runs (random choices resolved), from Loading on.</summary>
        public CoopSelection raceSelection;
        /// <summary>Starting: when the countdown ends. Racing: when the race starts (GO). In the host's clock, ms.</summary>
        public uint phaseAtHostMs;
        public readonly List<CoopPlayer> players = new List<CoopPlayer>();
    }

    /// <summary>Encodes and decodes the co-op messages (layouts in docs/COOP.md, "Wire protocol").</summary>
    public static class CoopMessages
    {
        public const byte Protocol = 1;

        public static MsgType TypeOf(byte[] message)
        {
            return message != null && message.Length > 0 ? (MsgType)message[0] : 0;
        }

        // ---------- Hello / Welcome / Reject ----------

        public static void Write(ByteWriter w, HelloMsg m)
        {
            w.U8((byte)MsgType.Hello);
            w.U8(m.protocol);
            w.U32(m.uid);
            w.U32(m.sessionId);
            w.Str(m.name, 42);
            w.U8(m.character);
            w.U32(m.contentHash);
            w.U32(m.tagSeed);
        }

        public static bool Read(ByteReader r, out HelloMsg m)
        {
            m = new HelloMsg();
            r.U8();
            m.protocol = (byte)r.U8();
            m.uid = r.U32();
            m.sessionId = r.U32();
            m.name = r.Str();
            m.character = (byte)r.U8();
            m.contentHash = r.U32();
            m.tagSeed = r.U32();
            return !r.Failed;
        }

        public static void Write(ByteWriter w, WelcomeMsg m)
        {
            w.U8((byte)MsgType.Welcome);
            w.U32(m.sessionId);
            w.U8(m.epoch);
            w.U8(m.slot);
            w.Str(m.tag, 8);
        }

        public static bool Read(ByteReader r, out WelcomeMsg m)
        {
            m = new WelcomeMsg();
            r.U8();
            m.sessionId = r.U32();
            m.epoch = (byte)r.U8();
            m.slot = (byte)r.U8();
            m.tag = r.Str();
            return !r.Failed;
        }

        public static void WriteReject(ByteWriter w, RejectReason reason)
        {
            w.U8((byte)MsgType.Reject);
            w.U8((byte)reason);
        }

        // ---------- Player to host ----------

        public static void Write(ByteWriter w, ProfileMsg m)
        {
            w.U8((byte)MsgType.Profile);
            w.U16(m.seq);
            w.Str(m.name, 42);
            w.U8(m.character);
            w.Bool(m.ready);
            w.U8(m.loadedRace);
        }

        public static bool Read(ByteReader r, out ProfileMsg m)
        {
            m = new ProfileMsg();
            r.U8();
            m.seq = (ushort)r.U16();
            m.name = r.Str();
            m.character = (byte)r.U8();
            m.ready = r.Bool();
            m.loadedRace = (byte)r.U8();
            return !r.Failed;
        }

        public static void Write(ByteWriter w, ProgressMsg m)
        {
            w.U8((byte)MsgType.Progress);
            w.U16(m.seq);
            w.U8(m.raceId);
            w.U8((byte)m.status);
            w.U8(m.leg);
            w.U16(Fraction(m.progress));
            w.U32(m.finishMs);
            w.U32(m.outMs);
        }

        public static bool Read(ByteReader r, out ProgressMsg m)
        {
            m = new ProgressMsg();
            r.U8();
            m.seq = (ushort)r.U16();
            m.raceId = (byte)r.U8();
            int status = r.U8();
            m.status = status <= (int)PlayerStatus.Left ? (PlayerStatus)status : PlayerStatus.Racing;
            m.leg = (byte)r.U8();
            m.progress = r.U16() / 65535f;
            m.finishMs = r.U32();
            m.outMs = r.U32();
            return !r.Failed;
        }

        public static void WriteMotion(ByteWriter w, CoopMotion m)
        {
            w.U8((byte)MsgType.Motion);
            Motion(w, m);
        }

        public static bool ReadMotion(ByteReader r, out CoopMotion m)
        {
            r.U8();
            m = Motion(r);
            return !r.Failed;
        }

        public static void Write(ByteWriter w, SelectMsg m)
        {
            w.U8((byte)MsgType.Select);
            w.U8(m.route);
            w.U8(m.addOn);
        }

        public static bool Read(ByteReader r, out SelectMsg m)
        {
            m = new SelectMsg();
            r.U8();
            m.route = (byte)r.U8();
            m.addOn = (byte)r.U8();
            return !r.Failed;
        }

        public static void WritePing(ByteWriter w, uint sentLocalMs)
        {
            w.U8((byte)MsgType.Ping);
            w.U32(sentLocalMs);
        }

        public static void WritePong(ByteWriter w, uint sentLocalMs, uint hostMs)
        {
            w.U8((byte)MsgType.Pong);
            w.U32(sentLocalMs);
            w.U32(hostMs);
        }

        public static void WriteBare(ByteWriter w, MsgType type)
        {
            w.U8((byte)type);
        }

        /// <summary>Busy: how long the sender expects to be quiet, in milliseconds (at most 65 s).</summary>
        public static void WriteBusy(ByteWriter w, double ms)
        {
            w.U8((byte)MsgType.Busy);
            w.U16((int)Math.Max(0, Math.Min(65535, ms)));
        }

        public static double ReadBusy(ByteReader r)
        {
            r.U8();
            int ms = r.U16();
            return r.Failed ? 0 : ms;
        }

        /// <summary>Known: [count] then a player record each (as in the snapshot).</summary>
        public static void WriteKnown(ByteWriter w, IList<CoopPlayer> players)
        {
            w.U8((byte)MsgType.Known);
            w.U8(players.Count);
            foreach (var p in players) Player(w, p);
        }

        public static bool ReadKnown(ByteReader r, List<CoopPlayer> into)
        {
            into.Clear();
            r.U8();
            int count = r.U8();
            if (count > CoopRules.MaxPlayers * 2) return false;
            for (int i = 0; i < count; i++) into.Add(Player(r));
            return !r.Failed;
        }

        // ---------- Host to everyone ----------

        public static void Write(ByteWriter w, SnapshotMsg s)
        {
            w.U8((byte)MsgType.Snapshot);
            w.U32(s.version);
            w.U32(s.sessionId);
            w.U8(s.epoch);
            w.U8((byte)s.phase);
            w.U8(s.raceId);
            Selection(w, s.selection);
            Selection(w, s.raceSelection);
            w.U32(s.phaseAtHostMs);
            w.U8(s.players.Count);
            foreach (var p in s.players) Player(w, p);
        }

        public static bool Read(ByteReader r, out SnapshotMsg s)
        {
            s = new SnapshotMsg();
            r.U8();
            s.version = r.U32();
            s.sessionId = r.U32();
            s.epoch = (byte)r.U8();
            s.phase = (SessionPhase)r.U8();
            s.raceId = (byte)r.U8();
            s.selection = Selection(r);
            s.raceSelection = Selection(r);
            s.phaseAtHostMs = r.U32();
            int count = r.U8();
            if (count > CoopRules.MaxPlayers) return false;
            for (int i = 0; i < count; i++) s.players.Add(Player(r));
            return !r.Failed && (int)s.phase <= (int)SessionPhase.Over;
        }

        /// <summary>One player as the snapshot (and Known) carries them.</summary>
        static void Player(ByteWriter w, CoopPlayer p)
        {
            w.U8(p.slot);
            w.U32(p.uid);
            w.Str(p.tag, 8);
            w.Str(p.name, 42);
            w.U8(p.character);
            w.U8((p.isHost ? 1 : 0) | (p.ready ? 2 : 0) | (p.connected ? 4 : 0));
            w.U8(p.loadedRace);
            w.U8((byte)p.status);
            w.U8(p.leg);
            w.U16(Fraction(p.progress));
            w.U32(p.finishMs);
            w.U32(p.outMs);
            w.U8(p.place);
        }

        static CoopPlayer Player(ByteReader r)
        {
            var p = new CoopPlayer();
            p.slot = (byte)Math.Min(CoopRules.MaxPlayers - 1, r.U8());
            p.uid = r.U32();
            p.tag = r.Str();
            p.name = r.Str();
            p.character = (byte)r.U8();
            int flags = r.U8();
            p.isHost = (flags & 1) != 0;
            p.ready = (flags & 2) != 0;
            p.connected = (flags & 4) != 0;
            p.loadedRace = (byte)r.U8();
            int status = r.U8();
            p.status = status <= (int)PlayerStatus.Left ? (PlayerStatus)status : PlayerStatus.Lobby;
            p.leg = (byte)r.U8();
            p.progress = r.U16() / 65535f;
            p.finishMs = r.U32();
            p.outMs = r.U32();
            p.place = (byte)r.U8();
            return p;
        }

        /// <summary>Every racing player's latest motion: [count] then [slot, motion] each.</summary>
        public static void WriteMotions(ByteWriter w, IList<KeyValuePair<byte, CoopMotion>> motions)
        {
            w.U8((byte)MsgType.Motions);
            w.U8(motions.Count);
            foreach (var kv in motions)
            {
                w.U8(kv.Key);
                Motion(w, kv.Value);
            }
        }

        public static bool ReadMotions(ByteReader r, List<KeyValuePair<byte, CoopMotion>> into)
        {
            into.Clear();
            r.U8();
            int count = r.U8();
            if (count > CoopRules.MaxPlayers) return false;
            for (int i = 0; i < count; i++)
            {
                byte slot = (byte)r.U8();
                into.Add(new KeyValuePair<byte, CoopMotion>(slot, Motion(r)));
            }
            return !r.Failed;
        }

        // ---------- Parts ----------

        static void Selection(ByteWriter w, CoopSelection s)
        {
            w.U8(s.route);
            w.U8(s.addOn);
            w.U8(s.chosenBy);
        }

        static CoopSelection Selection(ByteReader r)
        {
            return new CoopSelection { route = (byte)r.U8(), addOn = (byte)r.U8(), chosenBy = (byte)r.U8() };
        }

        // 23 bytes: race time, leg, flags, progress, x, y (floats), then centimetres in 16 bits.
        static void Motion(ByteWriter w, CoopMotion m)
        {
            w.U32(m.raceMs);
            w.U8(m.leg);
            w.U8(m.flags);
            w.U16(Fraction(m.progress));
            w.F32(m.x);
            w.F32(m.y);
            w.I16((int)(m.vx * 100f));
            w.I16((int)(m.vy * 100f));
            w.I16((int)(m.ballDx * 100f));
            w.I16((int)(m.ballDy * 100f));
        }

        static CoopMotion Motion(ByteReader r)
        {
            var m = new CoopMotion();
            m.raceMs = r.U32();
            m.leg = (byte)r.U8();
            m.flags = (byte)r.U8();
            m.progress = r.U16() / 65535f;
            m.x = r.F32();
            m.y = r.F32();
            m.vx = r.I16() / 100f;
            m.vy = r.I16() / 100f;
            m.ballDx = r.I16() / 100f;
            m.ballDy = r.I16() / 100f;
            return m;
        }

        static int Fraction(float f)
        {
            if (f <= 0f) return 0;
            if (f >= 1f) return 65535;
            return (int)(f * 65535f + 0.5f);
        }
    }
}
