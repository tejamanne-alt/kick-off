using System.Collections.Generic;

namespace DribbleToSchool.Holiday
{
    /// <summary>One mission as the screens show it.</summary>
    public struct MissionView
    {
        public string id;
        public string text;       // localized: "Run 800 m in one go"
        public int target;
        public int progress;      // 0..target
        public int reward;        // coins
        public bool done;
    }

    /// <summary>
    /// Three missions at a time (from a pool: run so far in one go, collect coins, slide, double jump,
    /// near misses, smash crates, power-ups, reach a stage...), saved in SaveData.holidayMissions.
    /// Finishing one pays coins and a new one takes its place.
    /// </summary>
    public static class HolidayMissions
    {
        /// <summary>The active missions with their saved progress (topped up to three).</summary>
        public static IList<MissionView> Active()
        {
            return new List<MissionView>();
        }

        /// <summary>The active missions as they would stand if the run ended now with these stats (changes nothing).</summary>
        public static IList<MissionView> Preview(RunStats stats)
        {
            return new List<MissionView>();
        }

        /// <summary>
        /// Apply a finished run: update every mission's progress, replace the finished ones and save.
        /// Returns the coins the finished missions paid; <paramref name="completed"/> gets those missions.
        /// </summary>
        public static int Commit(RunStats stats, List<MissionView> completed)
        {
            return 0;
        }
    }
}
