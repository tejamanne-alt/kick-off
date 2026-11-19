namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Where the kid is, for the ears: each route to school has its own music and its own ambience
    /// (MusicGenerator, AmbienceGenerator). Chapter 4 has two: the railway underpass and the building site.
    /// Florida has its own places, after Kamakura's (new values go at the end, so the old ones keep their numbers):
    /// Little Havana, the Miami River, the bay, downtown, the Underline and Museum Park.
    /// </summary>
    public enum Soundscape { Menu, Street, Market, Beach, Underpass, Site, Park, Havana, MiamiRiver, Bay, Downtown, Underline, MuseumPark }

    public static class Soundscapes
    {
        public static readonly Soundscape[] All =
        {
            Soundscape.Menu, Soundscape.Street, Soundscape.Market, Soundscape.Beach,
            Soundscape.Underpass, Soundscape.Site, Soundscape.Park,
            Soundscape.Havana, Soundscape.MiamiRiver, Soundscape.Bay, Soundscape.Downtown, Soundscape.Underline, Soundscape.MuseumPark,
        };

        /// <summary>
        /// The soundscape of one of Florida's legs (its routes cross several kinds of place), all of them Florida's own,
        /// none shared with Kamakura: Little Havana's street, the river (its street, the Riverwalk), the bay at Bayfront,
        /// downtown (Brickell's towers, the downpour downtown, the boulevard), the Underline under the line overhead, and Museum
        /// Park. Menu for a level that isn't Florida's.
        /// </summary>
        public static Soundscape ForFloridaLeg(string levelId)
        {
            switch (levelId)
            {
                case "FL1-1": return Soundscape.Havana;
                case "FL1-2": return Soundscape.Downtown;
                case "FL1-3": return Soundscape.Bay;
                case "FL2-1": return Soundscape.MiamiRiver;
                case "FL2-2": return Soundscape.MiamiRiver;
                case "FL2-3": return Soundscape.Downtown;
                case "FL3-1": return Soundscape.Underline;
                case "FL3-2": return Soundscape.Downtown;
                case "FL3-3": return Soundscape.MuseumPark;
                default: return Soundscape.Menu;
            }
        }

        /// <summary>
        /// The place whose music loop plays in a soundscape. Florida's own places have their own ambience, but play
        /// Florida's music for the kind of place they are: Little Havana the market's salsa, the river and the bay the
        /// beach's soca, downtown the street's son, the Underline the underpass's night groove, Museum Park the park's
        /// one-drop. Kamakura's places are their own.
        /// </summary>
        public static Soundscape MusicOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Havana: return Soundscape.Market;
                case Soundscape.MiamiRiver: return Soundscape.Beach;
                case Soundscape.Bay: return Soundscape.Beach;
                case Soundscape.Downtown: return Soundscape.Street;
                case Soundscape.Underline: return Soundscape.Underpass;
                case Soundscape.MuseumPark: return Soundscape.Park;
                default: return scape;
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
