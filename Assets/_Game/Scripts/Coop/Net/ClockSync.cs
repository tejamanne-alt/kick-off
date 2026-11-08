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
        /// <summary>Host time minus local time, in milliseconds (0 before the first sample).</summary>
        public double Offset { get; private set; }
        /// <summary>The best round trip in the window, in milliseconds.</summary>
        public double RoundTrip { get; private set; }
        /// <summary>The latest round trip, in milliseconds.</summary>
        public double LastRoundTrip { get; private set; }

        public void Reset()
        {
            count = next = 0;
            Offset = 0;
            RoundTrip = LastRoundTrip = 0;
        }

        /// <summary>A pong: the ping left at <paramref name="sentLocal"/>, the host stamped <paramref name="hostTime"/>, it is back at <paramref name="nowLocal"/>.</summary>
        public void AddSample(double sentLocal, double hostTime, double nowLocal)
        {
            double trip = nowLocal - sentLocal;
            if (trip < 0 || trip > 10000) return;   // a stale or impossible reply
            LastRoundTrip = trip;
            offsets[next] = hostTime - (sentLocal + nowLocal) * 0.5;
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

    /// <summary>The real clock: a Stopwatch, monotonic and unaffected by the time of day being changed.</summary>
    public sealed class StopwatchClock : ICoopClock
    {
        readonly System.Diagnostics.Stopwatch watch = System.Diagnostics.Stopwatch.StartNew();
        public double NowMs { get { return watch.Elapsed.TotalMilliseconds; } }
    }

    /// <summary>A clock tests move by hand.</summary>
    public sealed class ManualClock : ICoopClock
    {
        public double NowMs { get; set; }
        public void Advance(double ms) { NowMs += Math.Max(0, ms); }
    }
}
