using System;
using System.Collections.Generic;
using System.Text;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// The co-op mode's rules that need no radio: what a player may be called, the tag that tells two players of the same name
    /// apart, and the order of the standings. Pure C#, tested offline (Tests/Editor/CoopSessionTests).
    /// </summary>
    public static class CoopRules
    {
        public const int MaxPlayers = 4;
        /// <summary>Two players at least to race: a lobby of one can't start.</summary>
        public const int MinPlayers = 2;
        public const int MaxNameLength = 14;
        public const int TagLength = 4;

        /// <summary>Letters and digits a tag is made of: no 0/O or 1/I/L, so it reads the same on any screen.</summary>
        const string TagAlphabet = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";

        /// <summary>
        /// A name as other phones will show it: trimmed, inner spaces squeezed to one, without control characters or "#" (so a
        /// name can't pretend to carry someone else's tag), at most <see cref="MaxNameLength"/> characters (never half of an
        /// emoji). Empty means "use the default", Player 1, Player 2...
        /// </summary>
        public static string CleanName(string raw)
        {
            if (string.IsNullOrEmpty(raw)) return "";
            var sb = new StringBuilder(raw.Length);
            bool space = false;
            foreach (char c in raw)
            {
                if (char.IsControl(c) || c == '#' || c == '​' || c == '﻿') continue;
                if (char.IsWhiteSpace(c))
                {
                    space = sb.Length > 0;
                    continue;
                }
                if (space) { sb.Append(' '); space = false; }
                sb.Append(c);
            }
            string s = sb.ToString();
            if (s.Length > MaxNameLength)
            {
                int cut = MaxNameLength;
                if (char.IsHighSurrogate(s[cut - 1])) cut--;
                s = s.Substring(0, cut).TrimEnd();
            }
            return s;
        }

        /// <summary>The name shown for a player: what they typed, or the default for their slot ("Player 2").</summary>
        public static string DisplayName(CoopPlayer p, string defaultFormat)
        {
            if (p == null) return "";
            if (!string.IsNullOrEmpty(p.name)) return p.name;
            return string.Format(defaultFormat ?? "Player {0}", p.slot + 1);
        }

        /// <summary>"Hana #K7QX".</summary>
        public static string FullName(CoopPlayer p, string defaultFormat)
        {
            return DisplayName(p, defaultFormat) + " #" + (p != null ? p.tag : "");
        }

        /// <summary>
        /// The tag for an install id, tried as <paramref name="attempt"/> 0, 1, 2... until one is free in the lobby. The same
        /// phone gets the same tag every time (attempt 0) unless someone in the lobby already has it.
        /// </summary>
        public static string TagFor(uint uid, int attempt)
        {
            // A small integer hash (xorshift-multiply) so neighbouring ids give unrelated tags.
            uint h = uid ^ (uint)(attempt * 0x9E3779B9);
            h ^= h >> 16; h *= 0x7FEB352D; h ^= h >> 15; h *= 0x846CA68B; h ^= h >> 16;
            var chars = new char[TagLength];
            for (int i = 0; i < TagLength; i++)
            {
                chars[i] = TagAlphabet[(int)(h % (uint)TagAlphabet.Length)];
                h /= (uint)TagAlphabet.Length;
                if (h == 0) h = uid * 2654435761u + (uint)i;
            }
            return new string(chars);
        }

        /// <summary>A tag for <paramref name="uid"/> that nobody else in <paramref name="players"/> has.</summary>
        public static string UniqueTag(uint uid, IList<CoopPlayer> players)
        {
            for (int attempt = 0; attempt < 64; attempt++)
            {
                string tag = TagFor(uid, attempt);
                bool taken = false;
                foreach (var p in players)
                    if (p.uid != uid && p.tag == tag) { taken = true; break; }
                if (!taken) return tag;
            }
            return TagFor(uid, 64);
        }

        /// <summary>The lowest slot nobody has, or -1 when the lobby is full.</summary>
        public static int FreeSlot(IList<CoopPlayer> players)
        {
            for (int slot = 0; slot < MaxPlayers; slot++)
            {
                bool taken = false;
                foreach (var p in players)
                    if (p.slot == slot) { taken = true; break; }
                if (!taken) return slot;
            }
            return -1;
        }

        /// <summary>
        /// The standings: first everyone who got to school, quickest first; then everyone still on the way, furthest first;
        /// last everyone disqualified or gone (furthest first, then whoever stayed in longest). Players in the lobby come
        /// after, by slot.
        /// </summary>
        public static List<CoopPlayer> Standings(IEnumerable<CoopPlayer> players)
        {
            var list = new List<CoopPlayer>(players);
            list.Sort(CompareStanding);
            return list;
        }

        static int Group(CoopPlayer p)
        {
            switch (p.status)
            {
                case PlayerStatus.Finished: return 0;
                case PlayerStatus.Racing: return 1;
                case PlayerStatus.Disconnected:
                case PlayerStatus.Left: return 2;
                default: return 3;
            }
        }

        public static int CompareStanding(CoopPlayer a, CoopPlayer b)
        {
            int ga = Group(a), gb = Group(b);
            if (ga != gb) return ga.CompareTo(gb);
            int c = 0;
            switch (ga)
            {
                case 0: c = a.finishMs.CompareTo(b.finishMs); break;
                case 1: c = b.progress.CompareTo(a.progress); break;
                case 2:
                    c = b.progress.CompareTo(a.progress);
                    if (c == 0) c = b.outMs.CompareTo(a.outMs);
                    break;
            }
            return c != 0 ? c : a.slot.CompareTo(b.slot);
        }

        /// <summary>Gives every finished player their place (1 for the quickest), and everyone else 0.</summary>
        public static void AssignPlaces(IList<CoopPlayer> players)
        {
            var finished = new List<CoopPlayer>();
            foreach (var p in players)
            {
                if (p.status == PlayerStatus.Finished) finished.Add(p);
                else p.place = 0;
            }
            finished.Sort(CompareStanding);
            for (int i = 0; i < finished.Count; i++) finished[i].place = (byte)(i + 1);
        }

        /// <summary>The race is over when nobody is still on the way (everyone finished, was disqualified or left).</summary>
        public static bool RaceOver(IEnumerable<CoopPlayer> players)
        {
            bool any = false;
            foreach (var p in players)
            {
                if (p.status == PlayerStatus.Lobby) continue;
                any = true;
                if (p.status == PlayerStatus.Racing) return false;
            }
            return any;
        }

        /// <summary>
        /// Should the host of a lobby advertising <paramref name="mine"/> hand over to another host of the same session that
        /// advertises <paramref name="theirs"/>? The one with more players connected keeps the race; on a tie the older host
        /// (the lower epoch, usually the original) does. Both sides apply the same rule, so exactly one of them steps down.
        /// </summary>
        public static bool ShouldYieldTo(Net.RoomBeacon mine, Net.RoomBeacon theirs)
        {
            if (theirs.sessionId != mine.sessionId || theirs.epoch == mine.epoch) return false;
            if (theirs.players != mine.players) return theirs.players > mine.players;
            return theirs.epoch < mine.epoch;
        }

        /// <summary>Race time as the HUD shows it: 1:05.3 (or 0:42).</summary>
        public static string FormatTime(double ms, bool tenths)
        {
            if (ms < 0) ms = 0;
            int totalTenths = (int)Math.Floor(ms / 100.0);
            int minutes = totalTenths / 600;
            int seconds = (totalTenths / 10) % 60;
            return tenths ? string.Format("{0}:{1:00}.{2}", minutes, seconds, totalTenths % 10) : string.Format("{0}:{1:00}", minutes, seconds);
        }
    }
}
