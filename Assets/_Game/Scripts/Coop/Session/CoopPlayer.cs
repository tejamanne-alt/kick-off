using System.Collections.Generic;

namespace DribbleToSchool.Coop
{
    /// <summary>Where a player is in the co-op race.</summary>
    public enum PlayerStatus : byte
    {
        /// <summary>In the lobby (no race yet, or between races).</summary>
        Lobby = 0,
        /// <summary>On the way to school.</summary>
        Racing = 1,
        /// <summary>Got to school: has a time and a place, kept even after leaving.</summary>
        Finished = 2,
        /// <summary>Lost the connection for longer than the grace period while racing: disqualified, listed last.</summary>
        Disconnected = 3,
        /// <summary>Left the race before getting to school (Leave race): listed last, like a disconnection.</summary>
        Left = 4,
    }

    /// <summary>What the lobby is doing (the host decides, every phone shows it).</summary>
    public enum SessionPhase : byte
    {
        /// <summary>Choosing the stage, getting ready.</summary>
        Lobby = 0,
        /// <summary>Everyone is ready: a short countdown before the race loads (anyone un-readying stops it).</summary>
        Starting = 1,
        /// <summary>Every phone loads the route's first leg; the race waits for them all (or for the timeout).</summary>
        Loading = 2,
        /// <summary>The race: counting down to the start time, then running.</summary>
        Racing = 3,
        /// <summary>Nobody is still on the way: the final standings.</summary>
        Over = 4,
    }

    /// <summary>
    /// One moment of a player's run as the other phones draw it (their ghost): which leg, where the kid and the ball are, how
    /// the kid moves. Stamped with the sender's race clock, which every phone shares, so ghosts are drawn a little in the past
    /// and smoothly between samples.
    /// </summary>
    public struct CoopMotion
    {
        public const int Grounded = 1, Low = 2, FacingRight = 4, InPlay = 8, Celebrating = 16;

        public uint raceMs;
        public byte leg;
        public byte flags;
        /// <summary>How far along the whole route (0 to 1), for the race bar.</summary>
        public float progress;
        public float x, y;
        /// <summary>Velocity in metres a second (sent in centimetres).</summary>
        public float vx, vy;
        /// <summary>The ball's offset from the kid in metres (sent in centimetres).</summary>
        public float ballDx, ballDy;

        public bool Has(int flag) { return (flags & flag) != 0; }

        public static CoopMotion Lerp(CoopMotion a, CoopMotion b, float t)
        {
            var m = t < 0.5f ? a : b;
            m.x = a.x + (b.x - a.x) * t;
            m.y = a.y + (b.y - a.y) * t;
            m.vx = a.vx + (b.vx - a.vx) * t;
            m.vy = a.vy + (b.vy - a.vy) * t;
            m.ballDx = a.ballDx + (b.ballDx - a.ballDx) * t;
            m.ballDy = a.ballDy + (b.ballDy - a.ballDy) * t;
            m.progress = a.progress + (b.progress - a.progress) * t;
            return m;
        }
    }

    /// <summary>
    /// The last few motions of one player, oldest first, for drawing their ghost in the past (entity interpolation, as
    /// online games draw other players): <see cref="Sample"/> finds the two samples around a moment and blends them, and
    /// carries a sample on along its velocity for a short while if the next one is late.
    /// </summary>
    public sealed class MotionTrack
    {
        public const int Capacity = 24;
        /// <summary>How long a ghost may be carried on past its last sample before it waits there.</summary>
        public const float MaxExtrapolationMs = 250f;

        readonly List<CoopMotion> samples = new List<CoopMotion>(Capacity);

        public int Count { get { return samples.Count; } }
        public CoopMotion Latest { get { return samples[samples.Count - 1]; } }

        public void Clear() { samples.Clear(); }

        public void Add(CoopMotion m)
        {
            if (samples.Count > 0)
            {
                var last = samples[samples.Count - 1];
                if (m.raceMs < last.raceMs) return;   // older than what we have (a repeat)
                if (m.raceMs == last.raceMs) { samples[samples.Count - 1] = m; return; }
                if (m.leg != last.leg) samples.Clear();   // a new leg: no blending across scenes
            }
            samples.Add(m);
            if (samples.Count > Capacity) samples.RemoveAt(0);
        }

        /// <summary>Where the player was at race time <paramref name="raceMs"/> (false when nothing is known yet).</summary>
        public bool Sample(double raceMs, out CoopMotion m)
        {
            m = new CoopMotion();
            if (samples.Count == 0) return false;
            if (raceMs <= samples[0].raceMs) { m = samples[0]; return true; }
            if (raceMs > samples[samples.Count - 1].raceMs) return Extrapolate(raceMs, out m);
            for (int i = samples.Count - 1; i > 0; i--)
            {
                var a = samples[i - 1];
                if (a.raceMs > raceMs) continue;
                var b = samples[i];
                float span = b.raceMs - a.raceMs;
                float t = span > 0f ? (float)((raceMs - a.raceMs) / span) : 1f;
                m = CoopMotion.Lerp(a, b, t < 0f ? 0f : t > 1f ? 1f : t);
                return true;
            }
            m = samples[samples.Count - 1];
            return true;
        }

        /// <summary>Past the newest sample: carry it on along its velocity, for a little while only.</summary>
        bool Extrapolate(double raceMs, out CoopMotion m)
        {
            m = samples[samples.Count - 1];
            float ahead = (float)(raceMs - m.raceMs);
            if (ahead > MaxExtrapolationMs) ahead = MaxExtrapolationMs;
            float s = ahead / 1000f;
            m.x += m.vx * s;
            if (!m.Has(CoopMotion.Grounded)) m.y += m.vy * s;
            return true;
        }
    }

    /// <summary>
    /// One player in a co-op lobby, as the host keeps them and every phone sees them. The name is what the player typed (empty
    /// for the default "Player 2"); the tag is four characters the host gives each phone from its install id, shown after the
    /// name ("Hana #K7QX") so two players who type the same name can always be told apart.
    /// </summary>
    public sealed class CoopPlayer
    {
        public byte slot;
        public uint uid;
        public string tag = "";
        public string name = "";
        public byte character;
        public bool isHost;
        public bool ready;
        public bool connected = true;
        /// <summary>The race this phone has loaded its first leg for (the loading barrier).</summary>
        public byte loadedRace;
        public PlayerStatus status;
        public byte leg;
        /// <summary>How far along the whole route, 0 at the front door to 1 at the school gate.</summary>
        public float progress;
        /// <summary>The race time at the school gate, in milliseconds (Finished only).</summary>
        public uint finishMs;
        /// <summary>The race time when the player dropped out or left (Disconnected and Left).</summary>
        public uint outMs;
        /// <summary>1 for the winner, 2 for the next... (Finished only; 0 otherwise).</summary>
        public byte place;

        // ---- What the phone running the session keeps for itself (not sent) ----
        /// <summary>Host: when anything was last heard from this player. Everyone: when they were last seen connected.</summary>
        public double lastHeardMs;
        /// <summary>When the connection was lost (the grace period runs from here).</summary>
        public double lostSinceMs;
        /// <summary>Host: the link's peer for this player (-1 for the host itself or when offline).</summary>
        public int peer = -1;
        /// <summary>Recent motions, for the ghost.</summary>
        public readonly MotionTrack track = new MotionTrack();

        public bool IsOut { get { return status == PlayerStatus.Disconnected || status == PlayerStatus.Left; } }
        public bool StillRacing { get { return status == PlayerStatus.Racing; } }

        public CoopPlayer Clone()
        {
            var p = (CoopPlayer)MemberwiseClone();
            return p;
        }

        public override string ToString()
        {
            return "P" + (slot + 1) + " " + (string.IsNullOrEmpty(name) ? "(default)" : name) + " #" + tag + " " + status;
        }
    }

    /// <summary>The stage and location of the next race and who chose them (any player can; the host keeps the latest choice).</summary>
    public struct CoopSelection
    {
        /// <summary>The route (Levels/RouteTable.All), or <see cref="Random"/>.</summary>
        public byte route;
        /// <summary>The location (Progression/Cities.All), or <see cref="Random"/>.</summary>
        public byte addOn;
        /// <summary>The slot of the player who chose, or <see cref="Nobody"/> for the host's default.</summary>
        public byte chosenBy;

        public const byte Random = 255;
        public const byte Nobody = 255;

        public bool Equals(CoopSelection o) { return route == o.route && addOn == o.addOn && chosenBy == o.chosenBy; }
    }
}
