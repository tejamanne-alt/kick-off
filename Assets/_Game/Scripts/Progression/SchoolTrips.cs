using System;
using System.Collections.Generic;
using DribbleToSchool.Levels;

namespace DribbleToSchool.Progression
{
    /// <summary>What finishing one leg of a route did to the trip to school (<see cref="SchoolTrips.RecordLeg"/>).</summary>
    public enum TripVerdict
    {
        /// <summary>A leg before the last one: the trip goes on and there is nothing to judge yet.</summary>
        OnTheWay,
        /// <summary>The last leg of a trip walked from home without a break, at school before the bell.</summary>
        OnTime,
        /// <summary>The last leg of a trip walked from home without a break, at school after the bell: the trip starts again from home.</summary>
        Late,
        /// <summary>The last leg, but the legs before it were not all walked in this trip (it was played on its own from the map): no verdict.</summary>
        Untimed,
    }

    /// <summary>
    /// The trip to school along a route (docs/WORLD_MAP.md, "School trips"). Every story level is one leg of a route, and the legs
    /// add up to one walk from home to school. Each leg's own bell time is its target (the pace); the school bell of the whole trip
    /// is the sum of them. A trip is one continuous walk: finishing a route's first leg starts a new trip, finishing a later leg
    /// replaces that leg's time and forgets the legs after it, and finishing the last leg when every leg before it was walked in
    /// this trip judges the whole trip against the bell. A trip that gets to school late is forgotten, so the stage has to be walked
    /// again from home; a trip that gets there on time opens the next stage for good (<see cref="LevelUnlocks"/>).
    /// Pure logic on <see cref="SaveData"/>, so the tests can run it without Unity. Cozy mode (no bell) never calls it.
    /// </summary>
    public static class SchoolTrips
    {
        /// <summary>The time of a leg that has not been walked in the trip being walked.</summary>
        public const float NotWalked = -1f;

        /// <summary>The save version that brought the trips (<see cref="SaveData.CurrentVersion"/> from then on).</summary>
        public const int TripsVersion = 2;

        /// <summary>The saved trip along the route called <paramref name="routeId"/>, or null if it has never been walked.</summary>
        public static TripRecord Find(SaveData data, string routeId)
        {
            if (data == null || data.trips == null) return null;
            foreach (var trip in data.trips)
                if (trip != null && trip.routeId == routeId) return trip;
            return null;
        }

        /// <summary>The saved trip along <paramref name="route"/>, made if it is missing, with one leg time for each of its levels.</summary>
        public static TripRecord Get(SaveData data, Route route)
        {
            if (data.trips == null) data.trips = new List<TripRecord>();
            var trip = Find(data, route.id);
            if (trip == null)
            {
                trip = new TripRecord { routeId = route.id };
                data.trips.Add(trip);
            }
            if (trip.legTimes == null) trip.legTimes = new List<float>();
            int legs = route.levels.Length;
            while (trip.legTimes.Count < legs) trip.legTimes.Add(NotWalked);
            if (trip.legTimes.Count > legs) trip.legTimes.RemoveRange(legs, trip.legTimes.Count - legs);
            return trip;
        }

        /// <summary>
        /// The school bell of the whole trip along <paramref name="route"/>: the sum of its legs' own bell times, as
        /// <paramref name="bellOf"/> gives them for a level id. 0 (no bell) if any leg has none, e.g. a level missing from the catalog.
        /// </summary>
        public static float TripBell(Route route, Func<string, float> bellOf)
        {
            return TargetUpTo(route, route.levels.Length - 1, bellOf);
        }

        /// <summary>The legs' targets added up from home to the end of leg <paramref name="leg"/> (0 if any of them has none).</summary>
        public static float TargetUpTo(Route route, int leg, Func<string, float> bellOf)
        {
            float total = 0f;
            for (int i = 0; i <= leg && i < route.levels.Length; i++)
            {
                float bell = bellOf != null ? bellOf(route.levels[i]) : 0f;
                if (bell <= 0f) return 0f;
                total += bell;
            }
            return total;
        }

        /// <summary>
        /// Were all the legs before leg <paramref name="leg"/> walked in the trip being walked? If so, <paramref name="before"/> is the
        /// time they took together (0 for the first leg, which always starts a trip); if not, the trip is broken and this leg is untimed.
        /// </summary>
        public static bool TimeBefore(SaveData data, Route route, int leg, out float before)
        {
            before = 0f;
            if (leg <= 0) return true;
            var trip = Find(data, route.id);
            if (trip == null || trip.legTimes == null || trip.legTimes.Count < leg) return false;
            for (int i = 0; i < leg; i++)
            {
                float t = trip.legTimes[i];
                if (t < 0f) return false;
                before += t;
            }
            return true;
        }

        /// <summary>
        /// Leg <paramref name="leg"/> of <paramref name="route"/> was finished in <paramref name="seconds"/>. The first leg starts a new
        /// trip; a later one replaces its own time and forgets the legs after it (a trip is one walk, in order). The last leg judges a
        /// trip walked from home without a break against <paramref name="tripBell"/>: on time (at or before the bell) keeps the trip
        /// and marks the route on time for good, with its best time; late forgets the whole trip so the stage starts again from home.
        /// <paramref name="tripTime"/> is the trip so far, this leg included, or -1 when the legs before it were not all walked in it.
        /// </summary>
        public static TripVerdict RecordLeg(SaveData data, Route route, int leg, float seconds, float tripBell, out float tripTime)
        {
            var trip = Get(data, route);
            int last = route.levels.Length - 1;
            if (leg <= 0) Clear(trip);
            trip.legTimes[leg] = seconds;
            for (int i = leg + 1; i <= last; i++) trip.legTimes[i] = NotWalked;

            float before;
            bool continuous = TimeBefore(data, route, leg, out before);
            tripTime = continuous ? before + seconds : -1f;
            if (leg < last) return TripVerdict.OnTheWay;
            if (!continuous || tripBell <= 0f) return TripVerdict.Untimed;

            if (tripTime <= tripBell)
            {
                trip.onTime = true;
                if (trip.bestTripTime <= 0f || tripTime < trip.bestTripTime) trip.bestTripTime = tripTime;
                return TripVerdict.OnTime;
            }
            Clear(trip);
            return TripVerdict.Late;
        }

        /// <summary>
        /// The bell rang before the kid got to school on a timed last leg: the trip is over. It is forgotten at once, so starting the
        /// last leg again (or leaving it) cannot save it; the stage has to be walked again from home. Whether the route has ever been
        /// on time is kept.
        /// </summary>
        public static void MissBell(SaveData data, Route route)
        {
            var trip = Find(data, route.id);
            if (trip != null) Clear(trip);
        }

        /// <summary>Has the trip along the route called <paramref name="routeId"/> ever got to school on time?</summary>
        public static bool OnTime(SaveData data, string routeId)
        {
            var trip = Find(data, routeId);
            return trip != null && trip.onTime;
        }

        /// <summary>
        /// Is <paramref name="levelId"/> the last leg of a route whose trip has never got to school on time? Then the story level after
        /// it stays locked (outside cozy mode) until the whole route is walked from home before the bell.
        /// </summary>
        public static bool HoldsBack(SaveData data, string levelId)
        {
            Route route;
            int leg = RouteTable.LegIndex(levelId, out route);
            return leg >= 0 && leg == route.levels.Length - 1 && !OnTime(data, route.id);
        }

        /// <summary>
        /// Brings a save up to the trips: the list is never null, and a save from before them (version 1) has every route whose last
        /// level it has finished marked on time, so nobody finds a level locked that they could play before the update.
        /// </summary>
        public static void Upgrade(SaveData data)
        {
            if (data.trips == null) data.trips = new List<TripRecord>();
            if (data.version >= TripsVersion) return;
            foreach (var route in RouteTable.All)
            {
                if (route.levels.Length == 0) continue;
                if (data.IsCompleted(route.levels[route.levels.Length - 1])) Get(data, route).onTime = true;
            }
        }

        static void Clear(TripRecord trip)
        {
            for (int i = 0; i < trip.legTimes.Count; i++) trip.legTimes[i] = NotWalked;
        }
    }
}
