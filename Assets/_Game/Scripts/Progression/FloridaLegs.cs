using System.Collections.Generic;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// Save version 3: Florida's routes lost their mini-game legs (v128, at the user's request: FL1-2 The Metrobus, FL2-2 Uncle
    /// Rey's Boat, FL2-4 The Drugstore), and the legs after them took their numbers, so a route's legs are numbered 1, 2, 3 again
    /// (FL1-3 Brickell Avenue is now FL1-2, FL1-4 Bayfront FL1-3, FL2-3 The Riverwalk FL2-2, FL2-5 Downpour FL2-3). An older save's
    /// records, stickers and trip times move with their legs; the removed legs' records are dropped.
    /// Pure logic on <see cref="SaveData"/>, so the tests can run it without Unity.
    /// </summary>
    public static class FloridaLegs
    {
        /// <summary>The save version that renumbered Florida's legs (<see cref="SaveData.CurrentVersion"/> from then on).</summary>
        public const int RenumberedVersion = 3;

        /// <summary>Old leg id to new, for the legs that were kept and moved; a removed leg maps to null.</summary>
        static readonly Dictionary<string, string> Renamed = new Dictionary<string, string>
        {
            { "FL1-2", null }, { "FL1-3", "FL1-2" }, { "FL1-4", "FL1-3" },
            { "FL2-2", null }, { "FL2-3", "FL2-2" }, { "FL2-4", null }, { "FL2-5", "FL2-3" },
        };

        /// <summary>For each route that changed, which of its old legs' times the new legs keep, in order.</summary>
        static readonly Dictionary<string, int[]> KeptLegs = new Dictionary<string, int[]>
        {
            { "fl1", new[] { 0, 2, 3 } },
            { "fl2", new[] { 0, 2, 4 } },
        };

        /// <summary>The new id of an old leg id: itself if it didn't change, null if its leg was removed.</summary>
        public static string NewId(string oldId)
        {
            if (oldId == null) return null;
            string id;
            return Renamed.TryGetValue(oldId, out id) ? id : oldId;
        }

        /// <summary>Moves an older save's Florida records onto the renumbered legs (once: a version 3 save is left alone).</summary>
        public static void Upgrade(SaveData data)
        {
            if (data == null || data.version >= RenumberedVersion) return;
            if (data.levels != null)
            {
                var levels = new List<LevelRecord>();
                foreach (var record in data.levels)
                {
                    if (record == null) continue;
                    string id = NewId(record.levelId);
                    if (id == null) continue;
                    record.levelId = id;
                    levels.Add(record);
                }
                data.levels = levels;
            }
            if (data.stickers != null)
            {
                var stickers = new List<string>();
                foreach (string old in data.stickers)
                {
                    string id = NewId(old);
                    if (id != null && !stickers.Contains(id)) stickers.Add(id);
                }
                data.stickers = stickers;
            }
            if (data.trips != null)
            {
                foreach (var trip in data.trips)
                {
                    int[] kept;
                    if (trip == null || trip.legTimes == null || !KeptLegs.TryGetValue(trip.routeId ?? "", out kept)) continue;
                    var times = new List<float>();
                    foreach (int leg in kept) times.Add(leg < trip.legTimes.Count ? trip.legTimes[leg] : SchoolTrips.NotWalked);
                    trip.legTimes = times;
                }
            }
        }
    }
}
