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
