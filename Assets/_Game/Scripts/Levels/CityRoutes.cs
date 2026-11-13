using System.Collections.Generic;

namespace DribbleToSchool.Levels
{
    /// <summary>What a leg of a city's route is (docs/CITIES.md, "How a route plays").</summary>
    public enum LegKind
    {
        /// <summary>A street with its hazards, coins, stickers and a target time, ending at a stop.</summary>
        Dribble,
        /// <summary>A mini-game in place of a dribble (M1 the ride, M2 the errand, M3 the pick-up).</summary>
        MiniGame,
        /// <summary>A dribble with a twist in it (M4 drop and come back, M5 wait and cross).</summary>
        Twist,
    }

    /// <summary>One leg of a city's route: its level id, what kind of leg it is, and its mini-game or twist ("M1".."M5", or null).</summary>
    public sealed class Leg
    {
        public readonly string levelId;
        public readonly LegKind kind;
        public readonly string game;

        public Leg(string levelId, LegKind kind, string game = null)
        {
            this.levelId = levelId;
            this.kind = kind;
            this.game = game;
        }

        /// <summary>The string-table key of the level's name ("level.KM1-1").</summary>
        public string NameKey { get { return "level." + levelId; } }
    }

    /// <summary>
    /// A city's own routes from home to school (docs/CITIES.md): the routes, their legs and the stops between them, in the
    /// same <see cref="Route"/> and <see cref="Stop"/> shapes as the original town's <see cref="RouteTable"/>. A route's
    /// <c>chapter</c> here is its number in the city (1 to 3). Its map is the layout named by <see cref="layoutResource"/>.
    /// </summary>
    public sealed class CityRouteSet
    {
        /// <summary>The city's id (Progression/Cities: Kamakura's is "original").</summary>
        public readonly string cityId;
        /// <summary>The map's layout (TownMapLayout's format), under Resources once the map screen shows it (KM-L90).</summary>
        public readonly string layoutResource;
        public readonly Route[] routes;
        public readonly Stop[] stops;
        readonly Dictionary<string, Leg> legs = new Dictionary<string, Leg>();

        public CityRouteSet(string cityId, string layoutResource, Route[] routes, Stop[] stops, Leg[] legs)
        {
            this.cityId = cityId;
            this.layoutResource = layoutResource;
            this.routes = routes;
            this.stops = stops;
            foreach (var leg in legs) this.legs[leg.levelId] = leg;
        }

        /// <summary>The leg called <paramref name="levelId"/>, or null.</summary>
        public Leg LegOf(string levelId)
        {
            Leg leg;
            return legs.TryGetValue(levelId, out leg) ? leg : null;
        }

        /// <summary>Every level of every route, in route order.</summary>
        public IEnumerable<string> Levels
        {
            get
            {
                foreach (var route in routes)
                    foreach (string level in route.levels) yield return level;
            }
        }

        /// <summary>The stop called <paramref name="id"/> (home and the school included), or null.</summary>
        public Stop StopById(string id)
        {
            if (id == RouteTable.Home.id) return RouteTable.Home;
            if (id == RouteTable.School.id) return RouteTable.School;
            foreach (var stop in stops)
                if (stop.id == id) return stop;
            return null;
        }

        /// <summary>The position of a level along its route (0 for the first), or -1 for an unknown id.</summary>
        public int LegIndex(string levelId, out Route route)
        {
            foreach (var r in routes)
                for (int i = 0; i < r.levels.Length; i++)
                    if (r.levels[i] == levelId)
                    {
                        route = r;
                        return i;
                    }
            route = null;
            return -1;
        }

        /// <summary>Where a level starts: home for its route's first, else the stop the level before it ended at.</summary>
        public Stop From(string levelId)
        {
            Route route;
            int i = LegIndex(levelId, out route);
            if (i < 0) return null;
            return i == 0 ? RouteTable.Home : StopById(route.stops[i - 1]);
        }

        /// <summary>Where a level ends: the school for its route's last, else the stop the next level starts at.</summary>
        public Stop To(string levelId)
        {
            Route route;
            int i = LegIndex(levelId, out route);
            if (i < 0) return null;
            return i == route.levels.Length - 1 ? RouteTable.School : StopById(route.stops[i]);
        }

        /// <summary>The route a level is on, or null.</summary>
        public Route Of(string levelId)
        {
            Route route;
            return LegIndex(levelId, out route) >= 0 ? route : null;
        }
    }

    /// <summary>
    /// The cities' own routes (docs/CITIES.md), beside the original town's six (<see cref="RouteTable"/>), which the game plays
    /// until a city switches to its own (Kamakura: KM-L99 in docs/KAMAKURA_BUILD.md). Nothing reads these yet but the tests
    /// and the tools; the level ids never change once saved.
    /// </summary>
    public static class CityRoutes
    {
        /// <summary>
        /// Kamakura's three routes, as the map plan draws them (review/kamakura/map/KamakuraMapLayout.json, written and checked
        /// by tools/city_map/kamakura.py): the Enoden (by tram), the Shonan Coast (by the sea) and the Temple Hills (in the
        /// June rain).
        /// </summary>
        public static readonly CityRouteSet Kamakura = new CityRouteSet(
            Progression.Cities.KamakuraId, "KamakuraMapLayout",
            new[]
            {
                new Route("KM1", 1, new[] { "KM1-1", "KM1-2", "KM1-3", "KM1-4" }, null,
                    new[] { "hase", "kamakuraStation", "shrineSideGate" }),
                new Route("KM2", 2, new[] { "KM2-1", "KM2-2", "KM2-3", "KM2-4", "KM2-5" }, null,
                    new[] { "boardwalk", "grandmasShop", "lifeguardTower", "greatTorii" }),
                new Route("KM3", 3, new[] { "KM3-1", "KM3-2", "KM3-3" }, null,
                    new[] { "trailSign", "genjiyama" }),
            },
            new[]
            {
                // The Enoden: Hase's tram stop, the end of the line at Kamakura Station, the shrine's side gate at the top of Komachi-dori.
                new Stop("hase", StopKind.Station, "Hase Station"),
                new Stop("kamakuraStation", StopKind.Station, "Kamakura Station"),
                new Stop("shrineSideGate", StopKind.Shrine, "Shrine side gate"),
                // The Shonan Coast: the boardwalk out of the tunnel, Grandma's whitebait shop, the lifeguard tower, the great torii at the avenue's foot.
                new Stop("boardwalk", StopKind.Beach, "Boardwalk"),
                new Stop("grandmasShop", StopKind.Shop, "Grandma's shop"),
                new Stop("lifeguardTower", StopKind.Beach, "Lifeguard tower"),
                new Stop("greatTorii", StopKind.Shrine, "Great torii"),
                // The Temple Hills: the trail sign at the top of the hydrangea steps, Genjiyama park on the ridge.
                new Stop("trailSign", StopKind.Park, "Trail sign"),
                new Stop("genjiyama", StopKind.Park, "Genjiyama park"),
            },
            new[]
            {
                new Leg("KM1-1", LegKind.Dribble), new Leg("KM1-2", LegKind.MiniGame, "M1"),
                new Leg("KM1-3", LegKind.Dribble), new Leg("KM1-4", LegKind.Dribble),
                new Leg("KM2-1", LegKind.Dribble), new Leg("KM2-2", LegKind.Dribble),
                new Leg("KM2-3", LegKind.MiniGame, "M2"), new Leg("KM2-4", LegKind.Twist, "M4"),
                new Leg("KM2-5", LegKind.Dribble),
                new Leg("KM3-1", LegKind.Dribble), new Leg("KM3-2", LegKind.Dribble), new Leg("KM3-3", LegKind.Dribble),
            });

        /// <summary>Every city that has its own routes so far.</summary>
        public static readonly CityRouteSet[] All = { Kamakura };

        /// <summary>The routes of the city called <paramref name="cityId"/>, or null if it has none of its own yet.</summary>
        public static CityRouteSet For(string cityId)
        {
            foreach (var set in All)
                if (set.cityId == cityId) return set;
            return null;
        }
    }
}
