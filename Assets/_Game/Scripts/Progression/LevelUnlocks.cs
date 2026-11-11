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
            // An add-on with only some chapters built (Florida: the beach) keeps the others' levels locked.
            if (NotInTown(level)) return false;
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

        /// <summary>
        /// The level's chapter isn't in the active add-on's streets yet (Florida has only the beach): it stays locked while that
        /// add-on is chosen, and the map says so when it is tapped.
        /// </summary>
        public static bool NotInTown(LevelDefinition level)
        {
            return level != null && !Cities.InTown(level.chapter);
        }

        /// <summary>
        /// The route whose late trip to school holds <paramref name="level"/> back (the map says so when the level is tapped), or
        /// null if it is open or locked for another reason (the level before not done yet, the chapter not unlocked).
        /// </summary>
        public static Route HeldBackBy(LevelCatalog catalog, LevelDefinition level)
        {
            if (level == null || level.isChallenge || !Store.Monetization.IsChapterUnlocked(level.chapter)) return null;
            var previous = PreviousStory(catalog, level);
            return HeldBackBy(level.levelId, previous != null ? previous.levelId : null, SaveSystem.Data, Cozy);
        }

        /// <summary>
        /// The first story level a late trip to school holds back (the map marks it and says why), with the route that was late;
        /// null if no level is held back.
        /// </summary>
        public static LevelDefinition FirstHeldBack(LevelCatalog catalog, out Route late)
        {
            late = null;
            if (catalog == null) return null;
            foreach (var level in catalog.levels)
            {
                if (level == null || level.isChallenge || SaveSystem.IsCompleted(level.levelId)) continue;
                late = HeldBackBy(catalog, level);
                if (late != null) return level;
            }
            return null;
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
                return def != null && Store.Monetization.IsChapterUnlocked(def.chapter) && Cities.InTown(def.chapter);
            });
            var next = id != null ? catalog.FindById(id) : null;
            // Everything done (an add-on needs every level finished) and the last level isn't in this add-on's streets:
            // the first of its levels still short of three stars, or else its first.
            if (next != null && NotInTown(next))
            {
                var inTown = new List<string>();
                foreach (string s in story)
                {
                    var def = catalog.FindById(s);
                    if (def != null && !NotInTown(def)) inTown.Add(s);
                }
                string pick = FirstShortOfStars(inTown, SaveSystem.StarsFor);
                next = pick != null ? catalog.FindById(pick) : null;
            }
            return next;
        }

        /// <summary>The first of <paramref name="levels"/> with fewer than three stars, else the first; null if there are none.</summary>
        public static string FirstShortOfStars(IList<string> levels, Func<string, int> stars)
        {
            foreach (string id in levels)
                if (stars(id) < 3) return id;
            return levels.Count > 0 ? levels[0] : null;
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
