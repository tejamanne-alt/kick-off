using DribbleToSchool.Levels;

namespace DribbleToSchool.Progression
{
    /// <summary>Which levels can be played: the first one, and any level whose predecessor is completed.</summary>
    public static class LevelUnlocks
    {
        public static bool IsUnlocked(LevelCatalog catalog, LevelDefinition level)
        {
            int index = catalog.levels.IndexOf(level);
            if (index <= 0) return true;
            return SaveSystem.IsCompleted(catalog.levels[index - 1].levelId);
        }

        /// <summary>The level the player should play next: the first unlocked, uncompleted one.</summary>
        public static LevelDefinition NextToPlay(LevelCatalog catalog)
        {
            foreach (var l in catalog.levels)
            {
                if (!SaveSystem.IsCompleted(l.levelId) && IsUnlocked(catalog, l)) return l;
            }
            return catalog.levels.Count > 0 ? catalog.levels[catalog.levels.Count - 1] : null;
        }

        public static int StarsInChapter(LevelCatalog catalog, int chapter)
        {
            int total = 0;
            foreach (var l in catalog.LevelsInChapter(chapter)) total += SaveSystem.StarsFor(l.levelId);
            return total;
        }

        public static int TotalStars(LevelCatalog catalog)
        {
            int total = 0;
            foreach (var l in catalog.levels) total += SaveSystem.StarsFor(l.levelId);
            return total;
        }
    }
}
