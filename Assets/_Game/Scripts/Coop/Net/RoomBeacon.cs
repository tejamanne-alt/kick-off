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
    /// [protocol][session id x4][epoch][players: count, max in the high nibble][phase][name, UTF-8]. An Android host puts
    /// them in its scan response as service data (Android can't advertise a custom name); an iOS host as its advertised
    /// local name (iOS can't advertise service data), in hex followed by the name. A scanner reads either.
    /// </summary>
    public struct RoomBeacon
    {
        public const int FixedBytes = 8;
        /// <summary>The name's room in the advertisement (bytes of UTF-8).</summary>
        public const int MaxNameBytes = 10;
        /// <summary>What an iOS host's advertised name starts with, before the hex.</summary>
        public const string NamePrefix = "K2";

        public byte protocol;
        public uint sessionId;
        /// <summary>Goes up by one each time the session gets a new host.</summary>
        public byte epoch;
        public byte players;
        public byte maxPlayers;
        public RoomPhase phase;
        public string hostName;

        public byte[] ToBytes()
        {
            var w = new ByteWriter(24);
            w.U8(protocol);
            w.U32(sessionId);
            w.U8(epoch);
            w.U8((Math.Min(15, (int)players) & 0x0F) | ((Math.Min(15, (int)maxPlayers) & 0x0F) << 4));
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
            beacon.maxPlayers = (byte)(p >> 4);
            int phase = r.U8();
            if (phase > (int)RoomPhase.Over) return false;
            beacon.phase = (RoomPhase)phase;
            try { beacon.hostName = Encoding.UTF8.GetString(data, FixedBytes, data.Length - FixedBytes); }
            catch (Exception) { beacon.hostName = ""; }
            return !r.Failed && beacon.sessionId != 0;
        }

        /// <summary>The advertised local name an iOS host uses: "K2", the fixed bytes in hex, then the name.</summary>
        public string ToLocalName()
        {
            var bytes = ToBytes();
            var sb = new StringBuilder(NamePrefix);
            for (int i = 0; i < FixedBytes; i++) sb.Append(bytes[i].ToString("x2"));
            sb.Append(Encoding.UTF8.GetString(bytes, FixedBytes, bytes.Length - FixedBytes));
            return sb.ToString();
        }

        /// <summary>Reads an advertised local name made by <see cref="ToLocalName"/>.</summary>
        public static bool TryParseLocalName(string name, out RoomBeacon beacon)
        {
            beacon = new RoomBeacon();
            if (string.IsNullOrEmpty(name) || !name.StartsWith(NamePrefix) || name.Length < NamePrefix.Length + FixedBytes * 2) return false;
            var fixedBytes = new byte[FixedBytes];
            for (int i = 0; i < FixedBytes; i++)
            {
                int hi = Hex(name[NamePrefix.Length + i * 2]), lo = Hex(name[NamePrefix.Length + i * 2 + 1]);
                if (hi < 0 || lo < 0) return false;
                fixedBytes[i] = (byte)((hi << 4) | lo);
            }
            var nameBytes = Encoding.UTF8.GetBytes(name.Substring(NamePrefix.Length + FixedBytes * 2));
            var all = new byte[FixedBytes + nameBytes.Length];
            Array.Copy(fixedBytes, all, FixedBytes);
            Array.Copy(nameBytes, 0, all, FixedBytes, nameBytes.Length);
            return TryParse(all, out beacon);
        }

        static int Hex(char c)
        {
            if (c >= '0' && c <= '9') return c - '0';
            if (c >= 'a' && c <= 'f') return c - 'a' + 10;
            if (c >= 'A' && c <= 'F') return c - 'A' + 10;
            return -1;
        }
    }
}
