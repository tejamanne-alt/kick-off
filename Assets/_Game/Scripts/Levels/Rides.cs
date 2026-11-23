namespace DribbleToSchool.Levels
{
    /// <summary>
    /// The rides between two legs of a route (docs/CITIES.md, "A ride, between legs"): a short scene that plays by itself (12 to
    /// 20 s, skippable) as the kid rides the city's transit from the stop one leg ends at to where the next leg starts. The trip's
    /// clock doesn't run during it. A ride is played only when the trip goes on from the leg before (Next on its results); from the
    /// map the next leg just starts where the ride arrives.
    /// </summary>
    public static class Rides
    {
        /// <summary>Miami's people mover: a free driverless car on its elevated loop, from the Underline round the bay to Biscayne Boulevard.</summary>
        public const string PeopleMover = "peopleMover";

        /// <summary>Every ride, for the builder and the tests.</summary>
        public static readonly string[] All = { PeopleMover };

        /// <summary>The scene a ride plays in ("Ride_peopleMover").</summary>
        public static string SceneOf(string ride) { return "Ride_" + ride; }

        /// <summary>How long a ride lasts before the next leg loads (seconds; Skip ends it at once).</summary>
        public const float Seconds = 15f;

        /// <summary>The string-table key of the line the ride's card shows ("ride.peopleMover").</summary>
        public static string NameKey(string ride) { return "ride." + ride; }
    }
}
