namespace DribbleToSchool.Store
{
    /// <summary>
    /// Business model switches (Option A from the game brief: free first
    /// chapter, one-time "Full Game" unlock, no ads).
    ///
    /// RequireUnlock is OFF by default so the whole game is playable while the
    /// store isn't configured. Turn it on once Unity IAP and the store products
    /// are set up (see docs/RELEASE.md), or ship as a paid app and leave it off.
    /// </summary>
    public static class Monetization
    {
        /// <summary>Gate chapters after FreeChapters behind the Full Game purchase.</summary>
        public static readonly bool RequireUnlock = false;

        /// <summary>Chapters playable without buying anything.</summary>
        public static readonly int FreeChapters = 1;

        /// <summary>Non-consumable product id; create the same id in App Store Connect and Google Play Console.</summary>
        public const string FullGameProductId = "dribbletoschool.fullgame";

        /// <summary>Shown when the store can't provide a localized price.</summary>
        public const string FallbackPrice = "$3.99";

        public static bool IsChapterUnlocked(int chapter)
        {
            if (!RequireUnlock || chapter <= FreeChapters) return true;
            return Progression.SaveSystem.Data.fullGameUnlocked;
        }
    }
}
