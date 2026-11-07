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
        /// <summary>2: the trips to school (<see cref="trips"/>); older saves are upgraded by <see cref="SchoolTrips.Upgrade"/>.</summary>
        public const int CurrentVersion = 2;

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

        /// <summary>The trip to school along each route that has been walked (Progression/SchoolTrips). Version 1 saves had none.</summary>
        public List<TripRecord> trips = new List<TripRecord>();

        // Walking to school (Cosmetics/RouteRewards): the routes whose arrival has been celebrated with their medal, and
        // whether the trophy for every way has (both are worked out from the levels; these only stop a second celebration).
        public List<string> schoolMedals = new List<string>();
        public bool schoolTrophy;

        /// <summary>The add-on chosen in Settings (Progression/AddOns: "original", "california"...); empty in older saves.</summary>
        public string addOn = "";
        /// <summary>The filter chosen in Settings (Progression/AddOns.Filters).</summary>
        public string filter = "original";
        /// <summary>Older saves' California switch (before the add-ons): read once by AddOns.Selected.</summary>
        public bool californiaSkin;

        /// <summary>The saved result of a level, or null if it has never been finished.</summary>
        public LevelRecord Level(string levelId)
        {
            if (levels == null) return null;
            foreach (var r in levels)
                if (r != null && r.levelId == levelId) return r;
            return null;
        }

        /// <summary>Has this level been finished at least once?</summary>
        public bool IsCompleted(string levelId)
        {
            var r = Level(levelId);
            return r != null && r.completed;
        }
    }

    /// <summary>One of the Holiday Run's active missions as saved: its id, how far it has got and what it needs.</summary>
    [Serializable]
    public class HolidayMissionRecord
    {
        public string id;
        public int target;
        public int progress;
    }

    /// <summary>
    /// The trip to school along one route (Levels/RouteTable): the seconds each leg took in the trip being walked, and
    /// whether the kid has ever got from home to school on it before the bell. JsonUtility-friendly (lists, no dictionaries).
    /// </summary>
    [Serializable]
    public class TripRecord
    {
        public string routeId;
        /// <summary>One entry a leg, in the route's order: the seconds it took in this trip, or -1 if it has not been walked in it yet.</summary>
        public List<float> legTimes = new List<float>();
        /// <summary>Has the whole trip ever been walked before the bell? Kept once earned: it opens the next stage.</summary>
        public bool onTime;
        /// <summary>The quickest whole trip from home to school that was timed, in seconds (0 = none yet).</summary>
        public float bestTripTime;
    }

    /// <summary>The number of finished Holiday Run missions of one kind. Old saves simply have none.</summary>
    [Serializable]
    public class HolidayMissionTally
    {
        public string id;
        public int done;
    }
}
