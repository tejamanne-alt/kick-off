using DribbleToSchool.Levels;

namespace DribbleToSchool.Progression
{
    /// <summary>Which levels can be played: the first one, and any level whose predecessor is completed.</summary>
    public static class LevelUnlocks
    {
        /// <summary>
        /// Story levels unlock when the previous story level is done. Challenges
        /// unlock once the first story level of their chapter is done.
        /// </summary>
        public static bool IsUnlocked(LevelCatalog catalog, LevelDefinition level)
        {
            if (!Store.Monetization.IsChapterUnlocked(level.chapter)) return false;
            if (level.isChallenge)
            {
                foreach (var l in catalog.LevelsInChapter(level.chapter))
                {
                    if (!l.isChallenge) return SaveSystem.IsCompleted(l.levelId);
                }
                return true;
            }

            int index = catalog.levels.IndexOf(level);
            for (int i = index - 1; i >= 0; i--)
            {
                var prev = catalog.levels[i];
                if (prev != null && !prev.isChallenge) return SaveSystem.IsCompleted(prev.levelId);
            }
            return true;
        }

        /// <summary>The story level the player should play next: the first unlocked, uncompleted one.</summary>
        public static LevelDefinition NextToPlay(LevelCatalog catalog)
        {
            LevelDefinition last = null;
            foreach (var l in catalog.levels)
            {
                if (l.isChallenge) continue;
                last = l;
                if (!SaveSystem.IsCompleted(l.levelId) && IsUnlocked(catalog, l)) return l;
            }
            return last;
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
