using DribbleToSchool.Levels;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// What an errand gives the kid to carry (docs/CITIES.md, "What an errand gives you rides along"): Grandma's bento, wrapped
    /// at her shop on the Shonan Coast (KM2-3, mini-game M2), rides on the backpack for the rest of the trip. The kite may take
    /// its rice ball on the rocks (KM2-4, M4) unless the kid gets it back before the wave. Getting the bento to school whole is
    /// the trip's Delivered badge; it is never needed to finish. The rules work on a <see cref="SaveData"/>, so they are tested
    /// without a scene.
    /// </summary>
    public static class Errands
    {
        public const string Bento = "bento";
        /// <summary>The bento without its rice ball (the kite got it).</summary>
        public const string BentoNoRice = "bento-norice";
        /// <summary>The badge for getting the bento to school whole on the Shonan Coast.</summary>
        public const string DeliveredBadge = "delivered.KM2";

        /// <summary>The errand leg that gives the bento, and the route it is carried along.</summary>
        public const string ErrandLevel = "KM2-3";
        public const string ErrandRoute = "KM2";

        /// <summary>The kid carries the bento (whole or without its rice ball).</summary>
        public static bool CarriesBento(SaveData data)
        {
            return data != null && (data.carrying == Bento || data.carrying == BentoNoRice);
        }

        /// <summary>The bento is whole (its rice ball still in it).</summary>
        public static bool BentoWhole(SaveData data)
        {
            return data != null && data.carrying == Bento;
        }

        /// <summary>
        /// A level starts: a trip from home begins with nothing carried, and so does any leg off the errand's route (the bento
        /// only rides along the Shonan Coast after Grandma's shop). Returns true if this changed the save.
        /// </summary>
        public static bool LegStarts(SaveData data, string levelId)
        {
            if (data == null || string.IsNullOrEmpty(data.carrying)) return false;
            Route route;
            int leg = Routes.LegIndex(levelId, out route);
            bool keeps = leg > 0 && route != null && route.id == ErrandRoute && AfterErrand(route, leg);
            if (keeps) return false;
            data.carrying = "";
            return true;
        }

        static bool AfterErrand(Route route, int leg)
        {
            for (int i = 0; i < leg; i++)
                if (route.levels[i] == ErrandLevel) return true;
            return false;
        }

        /// <summary>The errand is done (the furoshiki folded and tied): the bento rides on the backpack, whole.</summary>
        public static void Wrapped(SaveData data)
        {
            if (data != null) data.carrying = Bento;
        }

        /// <summary>The kite's rice ball was lost to the wave: the bento goes on without it. True if it was whole.</summary>
        public static bool LostRiceBall(SaveData data)
        {
            if (!BentoWhole(data)) return false;
            data.carrying = BentoNoRice;
            return true;
        }

        /// <summary>
        /// The kid got the rice ball back before the wave: a carried bento is whole again (so a replay of the rocks is a second
        /// chance, and what the backpack shows is what is saved). True if this changed the save.
        /// </summary>
        public static bool SavedRiceBall(SaveData data)
        {
            if (data == null || data.carrying != BentoNoRice) return false;
            data.carrying = Bento;
            return true;
        }

        /// <summary>
        /// The kid reaches the end of <paramref name="levelId"/>. At school, a bento carried there is handed over (nothing is
        /// carried any more), and a whole one is Delivered: its badge is kept (once). True if a whole bento was delivered now.
        /// </summary>
        public static bool LegEnds(SaveData data, string levelId)
        {
            if (data == null || !CarriesBento(data)) return false;
            var to = Routes.To(levelId);
            if (to == null || to.id != RouteTable.School.id) return false;
            bool whole = BentoWhole(data);
            data.carrying = "";
            if (!whole) return false;
            if (data.badges == null) data.badges = new System.Collections.Generic.List<string>();
            if (!data.badges.Contains(DeliveredBadge)) data.badges.Add(DeliveredBadge);
            return true;
        }

        /// <summary>The Delivered badge has been earned.</summary>
        public static bool HasDelivered(SaveData data)
        {
            return data != null && data.badges != null && data.badges.Contains(DeliveredBadge);
        }
    }
}
