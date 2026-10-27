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
    }
}
