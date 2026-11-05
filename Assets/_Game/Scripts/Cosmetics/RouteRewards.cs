using System;
using System.Collections.Generic;
using DribbleToSchool.Levels;
using DribbleToSchool.Progression;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>
    /// What walking to school is worth. A route is walked when every story level on it is complete: the kid has gone from home
    /// all the way to the school's gate that way. Each route walked earns its medal (on its chip on the map, and celebrated once:
    /// UI/SchoolRewardPanel); walking three of the six earns a Locker Room flag, and walking every one earns the Top of the Class
    /// trophy with an exclusive ball and trail (CosmeticUnlock.SchoolRoutes, set in Editor/CosmeticsTable). Like the sticker
    /// rewards, everything is worked out from the levels in the save, so an older save gets what it has earned the first time
    /// the menu checks; the save only remembers what has been celebrated (SaveData.schoolMedals, schoolTrophy).
    /// </summary>
    public static class RouteRewards
    {
        /// <summary>How many ways there are to school (the trophy wants every one).</summary>
        public static int RouteCount { get { return RouteTable.All.Length; } }

        /// <summary>Is every story level on <paramref name="route"/> complete, by <paramref name="completed"/>?</summary>
        public static bool IsWalked(Route route, Func<string, bool> completed)
        {
            if (route == null || route.levels == null || route.levels.Length == 0) return false;
            foreach (string id in route.levels)
                if (!completed(id)) return false;
            return true;
        }

        public static bool IsWalked(Route route) { return IsWalked(route, SaveSystem.IsCompleted); }

        /// <summary>How many routes are walked all the way to school, by <paramref name="completed"/>.</summary>
        public static int Walked(Func<string, bool> completed)
        {
            int n = 0;
            foreach (var route in RouteTable.All)
                if (IsWalked(route, completed)) n++;
            return n;
        }

        public static int Walked() { return Walked(SaveSystem.IsCompleted); }

        /// <summary>Every way to school walked: the trophy.</summary>
        public static bool AllWalked() { return Walked() >= RouteCount; }

        /// <summary>The routes walked whose medal has not been celebrated yet, in the routes' order.</summary>
        public static List<Route> NewMedals()
        {
            var list = new List<Route>();
            var seen = SaveSystem.Data.schoolMedals;
            foreach (var route in RouteTable.All)
                if (IsWalked(route) && (seen == null || !seen.Contains(route.id))) list.Add(route);
            return list;
        }

        /// <summary>Every way walked and the trophy not celebrated yet.</summary>
        public static bool TrophyIsNew() { return AllWalked() && !SaveSystem.Data.schoolTrophy; }

        /// <summary>Remember <paramref name="medals"/> (and the trophy) as celebrated, so they are not again; saves.</summary>
        public static void MarkCelebrated(List<Route> medals, bool trophy)
        {
            var data = SaveSystem.Data;
            if (data.schoolMedals == null) data.schoolMedals = new List<string>();
            if (medals != null)
                foreach (var route in medals)
                    if (!data.schoolMedals.Contains(route.id)) data.schoolMedals.Add(route.id);
            if (trophy) data.schoolTrophy = true;
            SaveSystem.Save();
        }

        /// <summary>Has walking to school earned this item?</summary>
        public static bool IsEarned(CosmeticItem item) { return item != null && item.IsRouteReward && Walked() >= item.unlockValue; }

        /// <summary>How many more routes this item needs walked (0 once earned).</summary>
        public static int StillNeeded(CosmeticItem item) { return item == null || !item.IsRouteReward ? 0 : Math.Max(0, item.unlockValue - Walked()); }

        /// <summary>Every reward for walking to school, by how many routes it needs.</summary>
        public static List<CosmeticItem> All(CosmeticCatalog cosmetics)
        {
            var list = new List<CosmeticItem>();
            if (cosmetics == null) return list;
            foreach (var item in cosmetics.items) if (item != null && item.IsRouteReward) list.Add(item);
            list.Sort((a, b) => a.unlockValue.CompareTo(b.unlockValue));
            return list;
        }

        /// <summary>The next reward still to walk for (the fewest routes), or null once all are earned.</summary>
        public static CosmeticItem Next(CosmeticCatalog cosmetics)
        {
            foreach (var item in All(cosmetics)) if (!IsEarned(item)) return item;
            return null;
        }

        /// <summary>Earned but not yet in the save: what the next <see cref="GrantEarned"/> hands out.</summary>
        public static List<CosmeticItem> Pending(CosmeticCatalog cosmetics)
        {
            var list = new List<CosmeticItem>();
            foreach (var item in All(cosmetics))
                if (!SaveSystem.Owns(item.id) && IsEarned(item)) list.Add(item);
            return list;
        }

        /// <summary>Give the player every reward their walks to school have earned and they don't own yet, save, and return them.</summary>
        public static List<CosmeticItem> GrantEarned(CosmeticCatalog cosmetics)
        {
            var granted = Pending(cosmetics);
            if (granted.Count == 0) return granted;
            foreach (var item in granted) SaveSystem.Grant(item.id);
            SaveSystem.Save();
            return granted;
        }
    }
}
