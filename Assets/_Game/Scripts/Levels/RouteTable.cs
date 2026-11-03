using System.Collections.Generic;

namespace DribbleToSchool.Levels
{
    /// <summary>What a stop on the way to school is, for the map's glyph and the level builder's set piece.</summary>
    public enum StopKind
    {
        /// <summary>The kid's house: where every route starts.</summary>
        Home,
        /// <summary>The school: where every route ends.</summary>
        School,
        /// <summary>Someone's house and front garden (granny, a friend).</summary>
        House,
        /// <summary>A shop or a café with its name over the door.</summary>
        Shop,
        /// <summary>A bus stop: a shelter, a bench and the stop's sign.</summary>
        Bus,
        /// <summary>The church on the hill.</summary>
        Church,
        /// <summary>The railway station's ticket hall.</summary>
        Station,
        /// <summary>Something on the sand: the surf school's hut, the lifeguard tower.</summary>
        Beach,
        /// <summary>The building site's office cabin.</summary>
        Site,
        /// <summary>Something in the park: the bandstand, the boathouse, the allotments.</summary>
        Park,
    }

    /// <summary>
    /// A place on the way to school where one level ends and the next one on the same route starts (docs/WORLD_MAP.md,
    /// "Every route is one trip, a level is a leg of it"). The kid's house and the school are stops too: the first level of a
    /// route starts at home, the last ends at the school, and every level between runs from one stop to the next.
    /// </summary>
    public sealed class Stop
    {
        /// <summary>Short id ("busStop"); also the suffix of its string key ("stop.busStop"), except home's and the school's.</summary>
        public readonly string id;
        public readonly StopKind kind;
        /// <summary>
        /// Its name as the levels write it on boards and signs, in English in every language like all the levels' signs
        /// ("Bus stop", "Granny's house").
        /// </summary>
        public readonly string signName;

        public Stop(string id, StopKind kind, string signName)
        {
            this.id = id;
            this.kind = kind;
            this.signName = signName;
        }

        /// <summary>The string-table key of its name ("stop.busStop"; "place.home" and "place.school" for the two ends).</summary>
        public string NameKey
        {
            get
            {
                if (kind == StopKind.Home) return "place.home";
                if (kind == StopKind.School) return "place.school";
                return "stop." + id;
            }
        }

        /// <summary>
        /// The string-table key of the phrase that follows "Made it to" ("stop.busStop.to": "the bus stop", in Spanish "a la parada
        /// del bus"); null for home and the school (the school's results keep their own lines).
        /// </summary>
        public string ToKey { get { return kind == StopKind.Home || kind == StopKind.School ? null : "stop." + id + ".to"; } }

        public bool IsHome { get { return kind == StopKind.Home; } }
        public bool IsSchool { get { return kind == StopKind.School; } }
    }

    /// <summary>
    /// One way from home to school, played as a run of levels: the route's first level starts at the kid's front door,
    /// each level ends at a stop on the way (the bus stop, granny's house, the station...) where the next level on the route
    /// starts, and the route's last level ends at the school's arch. The map draws the routes with their levels and stops;
    /// the levels build the stop they start at and the one they end at, and the route's own street lies between.
    /// </summary>
    public sealed class Route
    {
        /// <summary>Short id, also the suffix of the string key ("route.beach").</summary>
        public readonly string id;
        /// <summary>The chapter the route's levels belong to (chapters stay the unit of the paywall and the Holiday Run's stages).</summary>
        public readonly int chapter;
        /// <summary>The story levels along the route, in the order they are played.</summary>
        public readonly string[] levels;
        /// <summary>The optional ball-skill challenge on the route (a gold node beside it), or null.</summary>
        public readonly string challenge;
        /// <summary>
        /// The stops between the levels (ids in <see cref="RouteTable.Stops"/>), one fewer than the levels: levels[i] ends at stops[i]
        /// and levels[i + 1] starts there. Home comes before the first level and the school after the last.
        /// </summary>
        public readonly string[] stops;

        public Route(string id, int chapter, string[] levels, string challenge, string[] stops)
        {
            this.id = id;
            this.chapter = chapter;
            this.levels = levels;
            this.challenge = challenge;
            this.stops = stops;
        }

        /// <summary>The string-table key of the route's name ("route.beach").</summary>
        public string NameKey { get { return "route." + id; } }
    }

    /// <summary>
    /// The six routes from home to the one school: the general street, the market, the beach, the
    /// railway underpass, the building site's shortcut and the park. Each story level (L01 to L23) is on
    /// exactly one, as one leg of the trip; each chapter's challenge sits on one of its routes. See docs/WORLD_MAP.md.
    /// </summary>
    public static class RouteTable
    {
        /// <summary>Where every route starts: the kid's front door.</summary>
        public static readonly Stop Home = new Stop("home", StopKind.Home, "Home");
        /// <summary>Where every route ends: the school's gate.</summary>
        public static readonly Stop School = new Stop("school", StopKind.School, "School");

        /// <summary>Every stop between two levels, each on one route (the order is the routes', then the levels').</summary>
        public static readonly Stop[] Stops =
        {
            // Home Street: Elm Street's bus stop, granny's bungalow at the foot of Hill Road, the church at its top, a friend's house in Garden Lane.
            new Stop("busStop", StopKind.Bus, "Bus stop"),
            new Stop("granny", StopKind.House, "Granny's house"),
            new Stop("church", StopKind.Church, "Church"),
            new Stop("samsHouse", StopKind.House, "Sam's house"),
            // Market Street: the bakery on the square, the post office, the flower shop, the library.
            new Stop("bakery", StopKind.Shop, "Bakery"),
            new Stop("postOffice", StopKind.Shop, "Post office"),
            new Stop("florist", StopKind.Shop, "Flower shop"),
            new Stop("library", StopKind.Shop, "Library"),
            // Seaside Road: the surf school's hut, the lifeguard tower, the beach cafe.
            new Stop("surfSchool", StopKind.Beach, "Surf school"),
            new Stop("lifeguard", StopKind.Beach, "Lifeguard tower"),
            new Stop("beachCafe", StopKind.Shop, "Beach cafe"),
            // The Underpass: the railway station between its two tunnels.
            new Stop("station", StopKind.Station, "Station"),
            // The building site's shortcut: the site office.
            new Stop("siteOffice", StopKind.Site, "Site office"),
            // Park Path: the bandstand, the park cafe, the boathouse on the pond, grandpa's allotment by the railway.
            new Stop("bandstand", StopKind.Park, "Bandstand"),
            new Stop("parkCafe", StopKind.Shop, "Park cafe"),
            new Stop("boathouse", StopKind.Park, "Boathouse"),
            new Stop("allotment", StopKind.Park, "Grandpa's garden"),
        };

        /// <summary>In the order the story unlocks them (chapter 4's levels alternate: the underpass has L15 and L18, the site L16 and L17).</summary>
        public static readonly Route[] All =
        {
            new Route("street", 1, new[] { "L01", "L02", "L03", "L04", "L05" }, "C01", new[] { "busStop", "granny", "church", "samsHouse" }),
            new Route("market", 2, new[] { "L06", "L07", "L08", "L09", "L10" }, "C02", new[] { "bakery", "postOffice", "florist", "library" }),
            new Route("beach", 3, new[] { "L11", "L12", "L13", "L14" }, "C03", new[] { "surfSchool", "lifeguard", "beachCafe" }),
            new Route("underpass", 4, new[] { "L15", "L18" }, null, new[] { "station" }),
            new Route("site", 4, new[] { "L16", "L17" }, "C04", new[] { "siteOffice" }),
            new Route("park", 5, new[] { "L19", "L20", "L21", "L22", "L23" }, "C05", new[] { "bandstand", "parkCafe", "boathouse", "allotment" }),
        };

        /// <summary>The stop called <paramref name="id"/> (home and the school included), or null.</summary>
        public static Stop StopById(string id)
        {
            if (id == Home.id) return Home;
            if (id == School.id) return School;
            foreach (var stop in Stops)
                if (stop.id == id) return stop;
            return null;
        }

        /// <summary>Where a story level starts: home for the first level of its route, else the stop the level before it ended at. Null for a challenge or an unknown id.</summary>
        public static Stop From(string levelId)
        {
            Route route;
            int i = LegIndex(levelId, out route);
            if (i < 0) return null;
            return i == 0 ? Home : StopById(route.stops[i - 1]);
        }

        /// <summary>Where a story level ends: the school for the last level of its route, else the stop the next level starts at. Null for a challenge or an unknown id.</summary>
        public static Stop To(string levelId)
        {
            Route route;
            int i = LegIndex(levelId, out route);
            if (i < 0) return null;
            return i == route.levels.Length - 1 ? School : StopById(route.stops[i]);
        }

        /// <summary>The position of a story level along its route (0 for the first), or -1 for a challenge or an unknown id.</summary>
        public static int LegIndex(string levelId, out Route route)
        {
            foreach (var r in All)
                for (int i = 0; i < r.levels.Length; i++)
                    if (r.levels[i] == levelId)
                    {
                        route = r;
                        return i;
                    }
            route = null;
            return -1;
        }

        /// <summary>The route a level (a story level or a challenge) is on, or null for an unknown id.</summary>
        public static Route Of(string levelId)
        {
            foreach (var route in All)
            {
                if (route.challenge == levelId) return route;
                foreach (string id in route.levels)
                    if (id == levelId) return route;
            }
            return null;
        }

        /// <summary>The routes of one chapter (chapter 4 has two).</summary>
        public static List<Route> InChapter(int chapter)
        {
            var list = new List<Route>();
            foreach (var route in All)
                if (route.chapter == chapter) list.Add(route);
            return list;
        }

        /// <summary>The position of the route in <see cref="All"/>, or -1.</summary>
        public static int IndexOf(string routeId)
        {
            for (int i = 0; i < All.Length; i++)
                if (All[i].id == routeId) return i;
            return -1;
        }
    }
}
