namespace DribbleToSchool.Progression
{
    /// <summary>
    /// The filters: a look over the whole picture, drawn by World/PostFX, chosen in Filters (UI/FiltersPanel: on the title screen
    /// and in the pause menu). The original look and the comic halftone (a printed comic: cel bands, halftone dots, an ink line,
    /// colour plates out of register, paper). A filter applies at once, in every scene and every city (<see cref="Changed"/>).
    /// Each city's light and grade come before the filter's passes, so the filter works in every city as it is. The pencil
    /// sketch and the classic cartoon were removed in v141 at the user's request: a player who had chosen one of them gets the
    /// original look (<see cref="Chosen"/> reads an unknown id as the original).
    /// </summary>
    public static class Filters
    {
        public const string Original = "original";
        public const string Comic = "comic";

        /// <summary>Every filter, in the order Filters lists them (saved by id: SaveData.filter).</summary>
        public static readonly string[] All = { Original, Comic };

        /// <summary>Raised when the filter is changed (the menus' pictures and buttons follow it at once).</summary>
        public static event System.Action Changed;

        /// <summary>The chosen filter (the original when none, or an unknown one, is saved).</summary>
        public static string Chosen
        {
            get
            {
                string f = SaveSystem.Data.filter;
                return System.Array.IndexOf(All, f) >= 0 ? f : Original;
            }
            set
            {
                if (System.Array.IndexOf(All, value) < 0) return;
                bool changed = SaveSystem.Data.filter != value;
                SaveSystem.Data.filter = value;
                SaveSystem.Save();
                if (changed && Changed != null) Changed();
            }
        }
    }
}
