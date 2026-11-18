namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Where the kid is, for the ears: each route to school has its own music and its own ambience
    /// (MusicGenerator, AmbienceGenerator). Chapter 4 has two: the railway underpass and the building site.
    /// </summary>
    public enum Soundscape { Menu, Street, Market, Beach, Underpass, Site, Park }

    public static class Soundscapes
    {
        public static readonly Soundscape[] All =
        {
            Soundscape.Menu, Soundscape.Street, Soundscape.Market, Soundscape.Beach,
            Soundscape.Underpass, Soundscape.Site, Soundscape.Park,
        };

        /// <summary>
        /// The soundscape of one of Florida's legs (its routes cross several kinds of place): Little Havana's shops, the bus, Brickell's
        /// towers and cranes, the bay, the ranch street, the river, the drugstore, the downpour downtown, the line overhead, the
        /// boulevard, the park. Menu for a level that isn't Florida's.
        /// </summary>
        public static Soundscape ForFloridaLeg(string levelId)
        {
            switch (levelId)
            {
                case "FL1-1": return Soundscape.Market;
                case "FL1-2": return Soundscape.Street;
                case "FL1-3": return Soundscape.Site;
                case "FL1-4": return Soundscape.Beach;
                case "FL2-1": return Soundscape.Street;
                case "FL2-2": return Soundscape.Beach;
                case "FL2-3": return Soundscape.Beach;
                case "FL2-4": return Soundscape.Market;
                case "FL2-5": return Soundscape.Street;
                case "FL3-1": return Soundscape.Underpass;
                case "FL3-2": return Soundscape.Street;
                case "FL3-3": return Soundscape.Park;
                default: return Soundscape.Menu;
            }
        }

        /// <summary>The soundscape of a route (Levels/RouteTable ids), or of a chapter when the route is unknown.</summary>
        public static Soundscape For(string routeId, int chapter)
        {
            switch (routeId)
            {
                case "street": return Soundscape.Street;
                case "market": return Soundscape.Market;
                case "beach": return Soundscape.Beach;
                case "underpass": return Soundscape.Underpass;
                case "site": return Soundscape.Site;
                case "park": return Soundscape.Park;
            }
            switch (chapter)
            {
                case 1: return Soundscape.Street;
                case 2: return Soundscape.Market;
                case 3: return Soundscape.Beach;
                case 4: return Soundscape.Site;
                case 5: return Soundscape.Park;
                default: return Soundscape.Menu;
            }
        }
    }
}
