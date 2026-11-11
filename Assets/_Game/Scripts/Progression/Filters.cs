namespace DribbleToSchool.Progression
{
    /// <summary>
    /// The filters: a look over the whole picture, drawn by World/PostFX, chosen in Filters (UI/FiltersPanel: on the title screen
    /// and in the pause menu). The original look, the comic halftone (a printed comic: cel bands, halftone dots, an ink line,
    /// colour plates out of register, paper), the pencil sketch (pencil lines and hatching on paper, the kids kept in colour)
    /// and the classic cartoon (inked cels over a painted background: World/ClassicLook). A filter applies at once, in every
    /// scene and every city, and to the menus' pictures and buttons (<see cref="Changed"/>). Each city's light and grade come
    /// before the filter's passes, so every filter works in every city as it is.
    /// </summary>
    public static class Filters
    {
        public const string Original = "original";
        public const string Comic = "comic";
        public const string Sketch = "sketch";
        public const string Classic = "classic";

        /// <summary>Every filter, in the order Filters lists them (saved by id: SaveData.filter).</summary>
        public static readonly string[] All = { Original, Comic, Sketch, Classic };

        /// <summary>Raised when the filter is changed (the menus' pictures and buttons follow it at once).</summary>
        public static event System.Action Changed;

        /// <summary>The classic cartoon filter is chosen.</summary>
        public static bool ClassicOn { get { return Chosen == Classic; } }

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
