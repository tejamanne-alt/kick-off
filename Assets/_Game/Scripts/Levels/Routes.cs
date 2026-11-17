using System.Collections.Generic;

namespace DribbleToSchool.Levels
{
    /// <summary>
    /// The routes in play: Kamakura's own three (<see cref="CityRoutes.Kamakura"/>, docs/KAMAKURA_BUILD.md KM-L99) while Kamakura
    /// is the city chosen, the original town's six (<see cref="RouteTable"/>) in the other cities. A level is found by its id in
    /// either, so the questions about one level (its route, its leg, where it starts and ends) need no city: the ids never
    /// overlap (Kamakura's are KMx-y, the town's Lxx).
    /// </summary>
    public static class Routes
    {
        /// <summary>
        /// Kamakura plays its own routes and legs instead of the original town's 23 levels (KM-L99). False puts every city back
        /// on the original town's routes (one line to turn the switch back).
        /// </summary>
        public static readonly bool KamakuraOwnRoutes = true;

        /// <summary>The city routes in play now (Kamakura's while it is the active city), or null for the original town's.</summary>
        public static CityRouteSet ActiveSet
        {
            get
            {
                if (!KamakuraOwnRoutes) return null;
                var city = Progression.Cities.Active;
                return city != null ? CityRoutes.For(city.id) : null;
            }
        }

        /// <summary>The routes the map shows and the trips walk, in their order.</summary>
        public static Route[] All
        {
            get
            {
                var set = ActiveSet;
                return set != null ? set.routes : RouteTable.All;
            }
        }

        /// <summary>The position of the route called <paramref name="routeId"/> in <see cref="All"/>, or -1.</summary>
        public static int IndexOf(string routeId)
        {
            var all = All;
            for (int i = 0; i < all.Length; i++)
                if (all[i].id == routeId) return i;
            return -1;
        }

        /// <summary>The route called <paramref name="routeId"/>: in play first, then the original town's, then any city's; or null.</summary>
        public static Route ById(string routeId)
        {
            foreach (var route in All)
                if (route.id == routeId) return route;
            foreach (var route in RouteTable.All)
                if (route.id == routeId) return route;
            foreach (var set in CityRoutes.All)
                foreach (var route in set.routes)
                    if (route.id == routeId) return route;
            return null;
        }

        /// <summary>The routes of <see cref="All"/> in a chapter (a city's route is its own chapter).</summary>
        public static List<Route> InChapter(int chapter)
        {
            var list = new List<Route>();
            foreach (var route in All)
                if (route.chapter == chapter) list.Add(route);
            return list;
        }

        /// <summary>The city route set a level belongs to, or null for the original town's levels.</summary>
        public static CityRouteSet SetOf(string levelId)
        {
            if (string.IsNullOrEmpty(levelId)) return null;
            foreach (var set in CityRoutes.All)
                if (set.LegOf(levelId) != null) return set;
            return null;
        }

        /// <summary>The leg a city level is (its kind and mini-game), or null.</summary>
        public static Leg LegOf(string levelId)
        {
            var set = SetOf(levelId);
            return set != null ? set.LegOf(levelId) : null;
        }

        /// <summary>The position of a level along its route (0 for the first), or -1 for an unknown id.</summary>
        public static int LegIndex(string levelId, out Route route)
        {
            var set = SetOf(levelId);
            return set != null ? set.LegIndex(levelId, out route) : RouteTable.LegIndex(levelId, out route);
        }

        /// <summary>Where a level starts.</summary>
        public static Stop From(string levelId)
        {
            var set = SetOf(levelId);
            return set != null ? set.From(levelId) : RouteTable.From(levelId);
        }

        /// <summary>Where a level ends.</summary>
        public static Stop To(string levelId)
        {
            var set = SetOf(levelId);
            return set != null ? set.To(levelId) : RouteTable.To(levelId);
        }

        /// <summary>The route a level is on, or null.</summary>
        public static Route Of(string levelId)
        {
            var set = SetOf(levelId);
            return set != null ? set.Of(levelId) : RouteTable.Of(levelId);
        }

        /// <summary>The stop called <paramref name="id"/>: the active city's first, then the original town's.</summary>
        public static Stop StopById(string id)
        {
            var set = ActiveSet;
            var stop = set != null ? set.StopById(id) : null;
            if (stop != null) return stop;
            stop = RouteTable.StopById(id);
            if (stop != null) return stop;
            foreach (var other in CityRoutes.All)
            {
                stop = other.StopById(id);
                if (stop != null) return stop;
            }
            return null;
        }

        /// <summary>The stops of the routes in play (home and the school not included).</summary>
        public static Stop[] Stops
        {
            get
            {
                var set = ActiveSet;
                return set != null ? set.stops : RouteTable.Stops;
            }
        }

        /// <summary>The map layout and picture of the routes in play (Resources paths, no extension).</summary>
        public static string MapLayout
        {
            get
            {
                var set = ActiveSet;
                return set != null && !string.IsNullOrEmpty(set.layoutResource) ? set.layoutResource : TownMap.LayoutResource;
            }
        }
    }
}
