using System.Collections.Generic;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// What an errand gives the kid rides along to school (docs/CITIES.md, "What an errand gives you rides along"): Uncle Rey's
    /// science project from his boat (FL2-2) on the backpack down the Riverwalk, through the drugstore and the downpour. Getting it
    /// to school unharmed is the trip's Delivered badge (coins, and the errand counted in <see cref="SaveData.delivered"/>). It is
    /// never needed to finish. A trip started again from home, or a route left for another, drops it (Errands.Drop).
    /// Pure logic on <see cref="SaveData"/>, so the tests can run it without Unity.
    /// </summary>
    public static class Errands
    {
        /// <summary>The model of the Everglades on a board that Uncle Rey hands over (FL2 The River Way).</summary>
        public const string ScienceProject = "scienceProject";

        /// <summary>Coins for a delivery (the first one of each errand; later ones give the same again).</summary>
        public const int DeliveredBonus = 60;

        /// <summary>Which errand's item is delivered at the end of which route (route id to item).</summary>
        static readonly Dictionary<string, string> ByRoute = new Dictionary<string, string> { { "fl2", ScienceProject } };

        /// <summary>The item an errand on this route gives (null if the route has none).</summary>
        public static string ItemOf(string routeId)
        {
            string item;
            return routeId != null && ByRoute.TryGetValue(routeId, out item) ? item : null;
        }

        /// <summary>The errand is done: its item rides on the backpack from here, unharmed.</summary>
        public static void Pick(SaveData data, string item)
        {
            if (data == null) return;
            data.carrying = item ?? "";
            data.carryingSpoiled = false;
        }

        /// <summary>The item was harmed (the project got wet in the downpour): no Delivered badge on this trip.</summary>
        public static void Spoil(SaveData data)
        {
            if (data != null && !string.IsNullOrEmpty(data.carrying)) data.carryingSpoiled = true;
        }

        /// <summary>Nothing carried any more (a new trip from home).</summary>
        public static void Drop(SaveData data)
        {
            if (data == null) return;
            data.carrying = "";
            data.carryingSpoiled = false;
        }

        /// <summary>Carrying this item, still unharmed.</summary>
        public static bool CarryingUnharmed(SaveData data, string item)
        {
            return data != null && !string.IsNullOrEmpty(item) && data.carrying == item && !data.carryingSpoiled;
        }

        /// <summary>
        /// At school at the end of <paramref name="routeId"/>: true (and the item delivered, counted, no longer carried) when the
        /// route's errand item arrives unharmed. Whatever was carried is put down either way.
        /// </summary>
        public static bool Arrive(SaveData data, string routeId)
        {
            if (data == null) return false;
            string item = ItemOf(routeId);
            bool ok = item != null && CarryingUnharmed(data, item);
            if (ok)
            {
                if (data.delivered == null) data.delivered = new List<string>();
                if (!data.delivered.Contains(item)) data.delivered.Add(item);
            }
            Drop(data);
            return ok;
        }
    }
}
