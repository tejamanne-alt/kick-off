using System;
using System.Collections.Generic;

namespace DribbleToSchool.Progression
{
    /// <summary>Best result for one level. JsonUtility-friendly (no dictionaries).</summary>
    [Serializable]
    public class LevelRecord
    {
        public string levelId;
        public bool completed;
        public int bestStars;
        public float bestTime;
        public int bestCoins;
        public bool allCoins;
    }

    /// <summary>Everything that persists between sessions. Bump <see cref="CurrentVersion"/> on breaking changes.</summary>
    [Serializable]
    public class SaveData
    {
        public const int CurrentVersion = 1;

        public int version = CurrentVersion;
        public int coins;
        public List<LevelRecord> levels = new List<LevelRecord>();
        public List<string> stickers = new List<string>();
        public List<string> ownedCosmetics = new List<string>();
        public string equippedBall = "ball_classic";
        public string equippedFlag = "flag_none";
        public string equippedOutfit = "outfit_school";
        public string equippedTrail = "trail_none";
        public bool fullGameUnlocked;

        // Lifetime stats (achievements later)
        public int totalPerfectTouches;
        public int totalJuggles;
        public int totalCoinsEarned;
        public int levelsCompleted;

        // Holiday Run (the endless mode). Missions are kept by HolidayMissions in holidayMissions.
        public int holidayBestScore;
        public int holidayBestDistance;
        public int holidayRuns;
        public int holidayDays;
        public int holidayTotalDistance;
        public List<HolidayMissionRecord> holidayMissions = new List<HolidayMissionRecord>();
        /// <summary>How many missions of each kind have been finished: the next one of that kind asks for more.</summary>
        public List<HolidayMissionTally> holidayMissionTally = new List<HolidayMissionTally>();
    }

    /// <summary>One of the Holiday Run's active missions as saved: its id, how far it has got and what it needs.</summary>
    [Serializable]
    public class HolidayMissionRecord
    {
        public string id;
        public int target;
        public int progress;
    }

    /// <summary>The number of finished Holiday Run missions of one kind. Old saves simply have none.</summary>
    [Serializable]
    public class HolidayMissionTally
    {
        public string id;
        public int done;
    }
}
