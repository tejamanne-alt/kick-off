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
        /// emoji), and not a rude word (<see cref="IsPolite"/>: it is a children's game, and the name is shown to the others).
        /// Empty means "use the default", Player 1, Player 2...
        /// </summary>
        public static string CleanName(string raw)
        {
            string s = Tidy(raw);
            return IsPolite(s) ? s : "";
        }

        /// <summary>A name that is something once tidied, but that the filter drops (the player is told, and plays as "Player N").</summary>
        public static bool IsRefused(string raw)
        {
            return Tidy(raw).Length > 0 && CleanName(raw).Length == 0;
        }

        static string Tidy(string raw)
        {
            if (string.IsNullOrEmpty(raw)) return "";
            var sb = new StringBuilder(raw.Length);
            bool space = false;
            foreach (char c in raw)
            {
                // (no "#": a name can't fake a tag; no "<" or ">": names are shown in rich text, which they could restyle)
                if (char.IsControl(c) || c == '#' || c == '<' || c == '>' || c == '\u200B' || c == '\uFEFF') continue;
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

        /// <summary>
        /// Rude words, in English and Spanish, written as <see cref="IsPolite"/> compares them: lower case, letters only, a
        /// doubled letter squeezed to one. These are caught anywhere in a name ("BigXxxFace").
        /// </summary>
        static readonly string[] RudeAnywhere =
        {
            "fuck", "motherf", "bitch", "biatch", "whore", "bastard", "vagina", "dildo", "hitler", "retard", "bulshit",
            "mierda", "pendej", "cabron", "maricon", "chinga", "culero", "gilipol",
        };

        /// <summary>
        /// Rude words that are also parts of ordinary names (Kshitij, Nazir, Wankhede, Scunthorpe, Diputado...), so they are
        /// only caught as a word of their own (or with a plural or gender ending).
        /// </summary>
        static readonly string[] RudeWords =
        {
            "shit", "cunt", "slut", "wank", "twat", "pusy", "penis", "porn", "rapist", "nazi", "niger", "niga", "fagot", "fag",
            "puta", "puto", "joder", "verga", "polas",
        };

        /// <summary>False when a name holds a rude word, however it is spelt (case, accents, 1 for i, 0 for o, repeats).</summary>
        public static bool IsPolite(string name)
        {
            if (string.IsNullOrEmpty(name)) return true;
            var sb = new StringBuilder(name.Length);
            char last = '\0';
            foreach (char raw in name.ToLowerInvariant())
            {
                char c = Plain(raw);
                if (c < 'a' || c > 'z') c = ' ';
                if (c == last) continue;   // fuuuck, puuuta (and runs of spaces)
                sb.Append(c);
                last = c;
            }
            string spaced = sb.ToString();
            string letters = spaced.Replace(" ", "");
            foreach (string word in RudeAnywhere)
                if (letters.Contains(word)) return false;
            foreach (string token in spaced.Split(' '))
            {
                if (token.Length == 0) continue;
                foreach (string word in RudeWords)
                    if (token == word || token == word + "s" || token == word + "es" || token == word + "a" || token == word + "o") return false;
            }
            return true;
        }

        /// <summary>A letter without its accent, and the digits and signs that stand in for letters.</summary>
        static char Plain(char c)
        {
            switch (c)
            {
                case 'á': case 'à': case 'â': case 'ä': case 'ã': case '4': case '@': return 'a';
                case 'é': case 'è': case 'ê': case 'ë': case '3': return 'e';
                case 'í': case 'ì': case 'î': case 'ï': case '1': case '!': case '|': return 'i';
                case 'ó': case 'ò': case 'ô': case 'ö': case 'õ': case '0': return 'o';
                case 'ú': case 'ù': case 'û': case 'ü': return 'u';
                case 'ñ': return 'n';
                case 'ç': return 'c';
                case '5': case '$': return 's';
                case '7': case '+': return 't';
                default: return c;
            }
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

        /// <summary>A tag from <paramref name="seed"/> for player <paramref name="uid"/> that nobody else in <paramref name="players"/> has.</summary>
        public static string UniqueTag(uint seed, uint uid, IList<CoopPlayer> players)
        {
            for (int attempt = 0; attempt < 64; attempt++)
            {
                string tag = TagFor(seed, attempt);
                bool taken = false;
                foreach (var p in players)
                    if (p.uid != uid && p.tag == tag) { taken = true; break; }
                if (!taken) return tag;
            }
            return TagFor(seed ^ uid, 64);
        }

        public static string UniqueTag(uint uid, IList<CoopPlayer> players) { return UniqueTag(uid, uid, players); }

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
            if (theirs.sessionId != mine.sessionId) return false;
            if (theirs.players != mine.players) return theirs.players > mine.players;
            if (theirs.epoch != mine.epoch) return theirs.epoch < mine.epoch;
            // (two players took over at the same epoch: the lower seat keeps it)
            return theirs.hostSlot < mine.hostSlot;
        }

        /// <summary>
        /// A player's own word about their race (their report, or a finish another phone relays) merged into the lobby's.
        /// Every phone runs its own kid against the shared race clock, so a player's run is as good while out of touch as in
        /// it: a runner listed out ("Disconnected") who turns up again is back in the race, or finished with their real time if
        /// they got to school meanwhile, until the host starts the next race (which is the only thing that makes "out" final).
        /// This is what keeps every phone's standings right after a split, where nobody can tell who walked away. Leaving is
        /// final; a finish is never undone. Returns true when it changed anything.
        /// </summary>
        public static bool MergeResult(CoopPlayer p, PlayerStatus status, uint finishMs, uint outMs)
        {
            switch (p.status)
            {
                case PlayerStatus.Racing:
                    if (status == PlayerStatus.Finished) { p.status = status; p.finishMs = finishMs; p.progress = 1f; return true; }
                    if (status == PlayerStatus.Left) { p.status = status; p.outMs = outMs; return true; }
                    return false;
                case PlayerStatus.Disconnected:
                    if (status == PlayerStatus.Finished) { p.status = status; p.finishMs = finishMs; p.progress = 1f; return true; }
                    if (status == PlayerStatus.Racing) { p.status = status; return true; }   // back in the race
                    if (status == PlayerStatus.Left) { p.status = status; p.outMs = outMs; return true; }
                    return false;
                case PlayerStatus.Left:
                    if (status == PlayerStatus.Finished && finishMs <= p.outMs) { p.status = status; p.finishMs = finishMs; p.progress = 1f; return true; }
                    return false;
                case PlayerStatus.Finished:
                    if (status == PlayerStatus.Finished && finishMs < p.finishMs) { p.finishMs = finishMs; return true; }
                    return false;
            }
            return false;
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
