using System;
using System.Text;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>What a lobby is doing, as its host's advertisement says.</summary>
    public enum RoomPhase : byte
    {
        Lobby = 0,
        Racing = 1,
        Over = 2,
    }

    /// <summary>
    /// What a host advertises about its lobby, so the Join list can show it before connecting, and so the players of a race
    /// find their session again after the host changes (the same session id, a higher epoch). Eight bytes and a short name:
    /// [protocol][session id x4][epoch][players: count, the host's slot in the high nibble][phase][name, UTF-8]. The slot
    /// settles which of two hosts of one session keeps the race when their player counts and epochs are equal
    /// (CoopRules.ShouldYieldTo). An Android host puts
    /// them in its scan response as service data (Android can't advertise a custom name); an iOS host as its advertised
    /// local name (iOS can't advertise service data), packed into eight characters (<see cref="ToLocalName"/>). A scanner reads either.
    /// </summary>
    public struct RoomBeacon
    {
        public const int FixedBytes = 8;
        /// <summary>The name's room in the advertisement (bytes of UTF-8).</summary>
        public const int MaxNameBytes = 10;

        public byte protocol;
        public uint sessionId;
        /// <summary>Goes up by one each time the session gets a new host.</summary>
        public byte epoch;
        public byte players;
        /// <summary>The host's seat (0 to 3).</summary>
        public byte hostSlot;
        public RoomPhase phase;
        public string hostName;

        public byte[] ToBytes()
        {
            var w = new ByteWriter(24);
            w.U8(protocol);
            w.U32(sessionId);
            w.U8(epoch);
            w.U8((Math.Min(15, (int)players) & 0x0F) | ((Math.Min(15, (int)hostSlot) & 0x0F) << 4));
            w.U8((byte)phase);
            var name = ByteWriter.Utf8Truncate(hostName ?? "", MaxNameBytes);
            w.Raw(name, 0, name.Length);
            return w.ToArray();
        }

        public static bool TryParse(byte[] data, out RoomBeacon beacon)
        {
            beacon = new RoomBeacon();
            if (data == null || data.Length < FixedBytes) return false;
            var r = new ByteReader(data);
            beacon.protocol = (byte)r.U8();
            beacon.sessionId = r.U32();
            beacon.epoch = (byte)r.U8();
            int p = r.U8();
            beacon.players = (byte)(p & 0x0F);
            beacon.hostSlot = (byte)(p >> 4);
            int phase = r.U8();
            if (phase > (int)RoomPhase.Over) return false;
            beacon.phase = (RoomPhase)phase;
            try { beacon.hostName = Encoding.UTF8.GetString(data, FixedBytes, data.Length - FixedBytes); }
            catch (Exception) { beacon.hostName = ""; }
            return !r.Failed && beacon.sessionId != 0;
        }

        /// <summary>The longest session id (24 bits: the iOS advertisement has room for no more).</summary>
        public const uint SessionMask = 0xFFFFFF;
        /// <summary>The highest epoch (6 bits).</summary>
        public const byte MaxEpoch = 63;
        /// <summary>An iOS host's advertised name: "K" and seven characters (iOS gives the name about 8 bytes beside a full service UUID).</summary>
        public const int LocalNameLength = 8;
        const string Base64Url = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

        /// <summary>
        /// The advertised local name an iOS host uses: "K" then 42 bits in seven URL-safe base-64 characters: protocol (3),
        /// session id (24), epoch (6), players (3), the host's slot (2), phase (2). No host name: iOS has no room for it
        /// (the Join list says "A friend's race" and the lobby shows the name once joined).
        /// </summary>
        public string ToLocalName()
        {
            ulong v = (ulong)(protocol & 7);
            v = (v << 24) | (sessionId & SessionMask);
            v = (v << 6) | (ulong)(Math.Min(MaxEpoch, epoch) & 63);
            v = (v << 3) | (ulong)(Math.Min(7, (int)players) & 7);
            v = (v << 2) | (ulong)(hostSlot & 3);
            v = (v << 2) | (ulong)((int)phase & 3);
            var chars = new char[LocalNameLength];
            chars[0] = 'K';
            for (int i = LocalNameLength - 1; i >= 1; i--) { chars[i] = Base64Url[(int)(v & 63)]; v >>= 6; }
            return new string(chars);
        }

        /// <summary>Reads an advertised local name made by <see cref="ToLocalName"/>.</summary>
        public static bool TryParseLocalName(string name, out RoomBeacon beacon)
        {
            beacon = new RoomBeacon();
            if (name == null || name.Length != LocalNameLength || name[0] != 'K') return false;
            ulong v = 0;
            for (int i = 1; i < LocalNameLength; i++)
            {
                int d = Base64Url.IndexOf(name[i]);
                if (d < 0) return false;
                v = (v << 6) | (ulong)d;
            }
            int phase = (int)(v & 3); v >>= 2;
            beacon.hostSlot = (byte)(v & 3); v >>= 2;
            beacon.players = (byte)(v & 7); v >>= 3;
            beacon.epoch = (byte)(v & 63); v >>= 6;
            beacon.sessionId = (uint)(v & SessionMask); v >>= 24;
            beacon.protocol = (byte)(v & 7);
            if (phase > (int)RoomPhase.Over || beacon.sessionId == 0) return false;
            beacon.phase = (RoomPhase)phase;
            beacon.hostName = "";
            return true;
        }
    }
}
