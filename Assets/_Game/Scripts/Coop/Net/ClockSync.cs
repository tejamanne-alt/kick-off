using System;

namespace DribbleToSchool.Coop.Net
{
    /// <summary>
    /// Estimates the host's clock from ping round trips, the way NTP does: a ping leaves at the local time t0, the host stamps
    /// it with its own time h, and the reply arrives at t1. If the trip was symmetric, the host's clock read h at about
    /// (t0 + t1) / 2, so offset = h - (t0 + t1) / 2. Of the last few samples the one with the shortest round trip is the most
    /// trustworthy (the least time spent queued in either direction), so that one's offset is used. Every player then counts
    /// the start of the race from the same instant whatever the radio's delay, within a few milliseconds.
    /// </summary>
    public sealed class ClockSync
    {
        public const int Window = 12;

        readonly double[] offsets = new double[Window];
        readonly double[] trips = new double[Window];
        int count, next;

        /// <summary>At least one sample has come back.</summary>
        public bool HasSync { get { return count > 0; } }
        /// <summary>Samples in the window (since the last reset or clock jump).</summary>
        public int Samples { get { return count; } }
        /// <summary>
        /// How many times one of the two clocks was seen to jump (a sample no honest round trip explains): the window is
        /// started again from that sample, and anything anchored to the old offset should be checked.
        /// </summary>
        public int Jumps { get; private set; }
        /// <summary>Host time minus local time, in milliseconds (0 before the first sample).</summary>
        public double Offset { get; private set; }
        /// <summary>The best round trip in the window, in milliseconds.</summary>
        public double RoundTrip { get; private set; }
        /// <summary>The latest round trip, in milliseconds.</summary>
        public double LastRoundTrip { get; private set; }

        public void Reset()
        {
            count = next = 0;
            Jumps = 0;
            Offset = 0;
            RoundTrip = LastRoundTrip = 0;
        }

        /// <summary>A pong: the ping left at <paramref name="sentLocal"/>, the host stamped <paramref name="hostTime"/>, it is back at <paramref name="nowLocal"/>.</summary>
        public void AddSample(double sentLocal, double hostTime, double nowLocal)
        {
            double trip = nowLocal - sentLocal;
            if (trip < 0 || trip > 10000) return;   // a stale or impossible reply
            LastRoundTrip = trip;
            double offset = hostTime - (sentLocal + nowLocal) * 0.5;
            // An honest sample's offset is out by at most half its round trip, and so is the best one's: further apart than
            // that, a clock jumped (a phone slept, say), and the old samples describe a clock that is gone.
            if (count > 0 && Math.Abs(offset - Offset) > (trip + RoundTrip) * 0.5 + 50)
            {
                count = next = 0;
                Jumps++;
            }
            offsets[next] = offset;
            trips[next] = trip;
            next = (next + 1) % Window;
            if (count < Window) count++;

            int best = 0;
            for (int i = 1; i < count; i++)
                if (trips[i] < trips[best]) best = i;
            Offset = offsets[best];
            RoundTrip = trips[best];
        }

        public double ToHost(double local) { return local + Offset; }
        public double ToLocal(double host) { return host - Offset; }
    }

    /// <summary>A clock in milliseconds that only goes forward (the session's notion of now).</summary>
    public interface ICoopClock
    {
        double NowMs { get; }
    }

    /// <summary>
    /// The real clock: a Stopwatch, monotonic and unaffected by the time of day being changed, that also counts the time the
    /// phone slept. (A Stopwatch stands still while the phone sleeps, on iOS and on Android: a racer who pressed the power
    /// button would otherwise have that time left off their race.) Sleep shows as the time of day moving on further than
    /// the Stopwatch between two reads; that gap, beyond a second, is added. A time of day set back is ignored, and one set
    /// forward only makes this phone's own clock run late, never early.
    /// </summary>
    public sealed class StopwatchClock : ICoopClock
    {
        const double SleepThreshold = 1000;
        const double MaxSleep = 6 * 3600 * 1000.0;

        readonly System.Diagnostics.Stopwatch watch = System.Diagnostics.Stopwatch.StartNew();
        double lastWatch;
        DateTime lastWall = DateTime.UtcNow;
        double slept;

        public double NowMs
        {
            get
            {
                double w = watch.Elapsed.TotalMilliseconds;
                var wall = DateTime.UtcNow;
                double hidden = (wall - lastWall).TotalMilliseconds - (w - lastWatch);
                if (hidden > SleepThreshold && hidden < MaxSleep) slept += hidden;
                lastWatch = w;
                lastWall = wall;
                return w + slept;
            }
        }
    }

    /// <summary>A clock tests move by hand.</summary>
    public sealed class ManualClock : ICoopClock
    {
        public double NowMs { get; set; }
        public void Advance(double ms) { NowMs += Math.Max(0, ms); }
    }
}
