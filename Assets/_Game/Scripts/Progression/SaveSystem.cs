using System;
using System.IO;
using UnityEngine;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// Local JSON save in persistentDataPath. Writes go to a temp file first and
    /// are then swapped in, so a crash mid-save never corrupts progress. A
    /// corrupt file is kept as .bak and play continues from a fresh save.
    /// </summary>
    public static class SaveSystem
    {
        const string FileName = "save.json";

        static SaveData data;

        public static event Action Changed;

        public static string FilePath { get { return Path.Combine(Application.persistentDataPath, FileName); } }

        public static SaveData Data
        {
            get
            {
                if (data == null) Load();
                return data;
            }
        }

        public static void Load()
        {
            data = null;
            try
            {
                if (File.Exists(FilePath))
                    data = JsonUtility.FromJson<SaveData>(File.ReadAllText(FilePath));
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Save] Could not read save, starting fresh: " + e.Message);
                TryBackupCorrupt();
            }
            if (data == null) data = new SaveData();
            Migrate(data);
        }

        public static void Save()
        {
            if (data == null) return;
            try
            {
                string tmp = FilePath + ".tmp";
                File.WriteAllText(tmp, JsonUtility.ToJson(data, true));
                if (File.Exists(FilePath)) File.Delete(FilePath);
                File.Move(tmp, FilePath);
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Save] Could not write save: " + e.Message);
            }
            if (Changed != null) Changed();
        }

        /// <summary>Wipe all progress (settings screen / debug).</summary>
        public static void ResetProgress()
        {
            data = new SaveData();
            Migrate(data);
            Save();
        }

        static void Migrate(SaveData d)
        {
            // Defaults every save must have.
            Own(d, d.equippedBall);
            Own(d, d.equippedFlag);
            Own(d, d.equippedOutfit);
            Own(d, d.equippedTrail);
            d.version = SaveData.CurrentVersion;
        }

        static void Own(SaveData d, string id)
        {
            if (!string.IsNullOrEmpty(id) && !d.ownedCosmetics.Contains(id)) d.ownedCosmetics.Add(id);
        }

        static void TryBackupCorrupt()
        {
            try { File.Copy(FilePath, FilePath + ".bak", true); }
            catch (Exception) { }
        }

        // ---------- Queries & mutations ----------

        public static LevelRecord GetRecord(string levelId)
        {
            foreach (var r in Data.levels)
            {
                if (r.levelId == levelId) return r;
            }
            return null;
        }

        static LevelRecord GetOrCreateRecord(string levelId)
        {
            var r = GetRecord(levelId);
            if (r != null) return r;
            r = new LevelRecord { levelId = levelId };
            Data.levels.Add(r);
            return r;
        }

        public static int StarsFor(string levelId)
        {
            var r = GetRecord(levelId);
            return r != null ? r.bestStars : 0;
        }

        public static bool IsCompleted(string levelId)
        {
            var r = GetRecord(levelId);
            return r != null && r.completed;
        }

        /// <summary>Store a finished run and return how many new stars it earned.</summary>
        public static int RecordLevel(string levelId, int stars, float time, int coins, bool allCoins)
        {
            var r = GetOrCreateRecord(levelId);
            int newStars = Mathf.Max(0, stars - r.bestStars);
            if (!r.completed) Data.levelsCompleted++;
            r.completed = true;
            r.bestStars = Mathf.Max(r.bestStars, stars);
            r.bestTime = r.bestTime <= 0f ? time : Mathf.Min(r.bestTime, time);
            r.bestCoins = Mathf.Max(r.bestCoins, coins);
            r.allCoins |= allCoins;
            return newStars;
        }

        public static void AddCoins(int amount)
        {
            if (amount <= 0) return;
            Data.coins += amount;
            Data.totalCoinsEarned += amount;
        }

        public static bool TrySpend(int amount)
        {
            if (Data.coins < amount) return false;
            Data.coins -= amount;
            return true;
        }

        public static bool HasSticker(string id) { return Data.stickers.Contains(id); }

        public static bool AddSticker(string id)
        {
            if (string.IsNullOrEmpty(id) || Data.stickers.Contains(id)) return false;
            Data.stickers.Add(id);
            return true;
        }

        public static bool Owns(string cosmeticId) { return Data.ownedCosmetics.Contains(cosmeticId); }

        public static void Grant(string cosmeticId) { Own(Data, cosmeticId); }
    }
}
