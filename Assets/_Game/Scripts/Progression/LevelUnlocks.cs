using System;
using System.Collections.Generic;
using DribbleToSchool.Levels;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// Which levels can be played: the first one, and any story level whose predecessor is completed, as long as that predecessor
    /// did not end a stage whose trip to school has never been on time (<see cref="SchoolTrips"/>; cozy mode skips that part).
    /// </summary>
    public static class LevelUnlocks
    {
        /// <summary>
        /// Story levels unlock when the previous story level is done and, if that level is the last leg of its route, the route's
        /// trip has got to school on time at least once (or cozy mode is on). Challenges unlock once the first story level of their
        /// chapter is done.
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
            var previous = PreviousStory(catalog, level);
            return StoryOpen(level.levelId, previous != null ? previous.levelId : null, SaveSystem.Data, Cozy);
        }

        /// <summary>The story level the player should play next: the first unlocked, uncompleted one, or the start of a stage to walk again.</summary>
        public static LevelDefinition NextToPlay(LevelCatalog catalog)
        {
            var story = new List<string>();
            foreach (var l in catalog.levels)
                if (l != null && !l.isChallenge) story.Add(l.levelId);
            string id = NextToPlay(story, SaveSystem.Data, Cozy, levelId =>
            {
                var def = catalog.FindById(levelId);
                return def != null && Store.Monetization.IsChapterUnlocked(def.chapter);
            });
            return id != null ? catalog.FindById(id) : null;
        }

        /// <summary>Cozy mode (the school bell turned off): stages open without an on-time trip.</summary>
        static bool Cozy { get { return !Core.GameSettings.BellTimerEnabled; } }

        /// <summary>The story level before <paramref name="level"/> in the catalog (challenges skipped), or null for the first.</summary>
        static LevelDefinition PreviousStory(LevelCatalog catalog, LevelDefinition level)
        {
            int index = catalog.levels.IndexOf(level);
            for (int i = index - 1; i >= 0; i--)
            {
                var prev = catalog.levels[i];
                if (prev != null && !prev.isChallenge) return prev;
            }
            return null;
        }

        // ---------- The rule on plain data (the tests use these without Unity's assets) ----------

        /// <summary>
        /// Can the story level <paramref name="levelId"/> be played, given the story level before it in the catalog
        /// (<paramref name="previousStoryId"/>, null for the first)? The paywall is not part of this.
        /// A level already finished stays open (turning cozy mode off later never locks a level that was played).
        /// </summary>
        public static bool StoryOpen(string levelId, string previousStoryId, SaveData data, bool cozy)
        {
            if (previousStoryId == null) return true;
            if (data.IsCompleted(levelId)) return true;
            if (!data.IsCompleted(previousStoryId)) return false;
            return cozy || !SchoolTrips.HoldsBack(data, previousStoryId);
        }

        /// <summary>
        /// The route whose trip to school holds <paramref name="levelId"/> back: the level before it is done, but it ended a stage
        /// that has never got to school on time. Null if the level is open or locked for another reason.
        /// </summary>
        public static Route HeldBackBy(string levelId, string previousStoryId, SaveData data, bool cozy)
        {
            if (previousStoryId == null || cozy || data.IsCompleted(levelId) || !data.IsCompleted(previousStoryId)) return null;
            return SchoolTrips.HoldsBack(data, previousStoryId) ? RouteTable.Of(previousStoryId) : null;
        }

        /// <summary>
        /// The story level to play next, from the story levels in catalog order (<paramref name="story"/>): the first one not yet
        /// finished that can be played. If a late trip holds that one back, the first leg of the stage to walk again instead.
        /// <paramref name="chapterOpen"/> says whether a level's chapter is paid for (null: every one is). The last level if all are done.
        /// </summary>
        public static string NextToPlay(IList<string> story, SaveData data, bool cozy, Func<string, bool> chapterOpen)
        {
            string last = null;
            for (int i = 0; i < story.Count; i++)
            {
                string id = story[i];
                last = id;
                if (data.IsCompleted(id)) continue;
                if (chapterOpen != null && !chapterOpen(id)) continue;
                string previous = i > 0 ? story[i - 1] : null;
                if (StoryOpen(id, previous, data, cozy)) return id;
                var route = HeldBackBy(id, previous, data, cozy);
                if (route != null) return route.levels[0];
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
