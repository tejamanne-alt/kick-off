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
        /// <summary>A dock on the water: a timber jetty with its cleats and bollards (Florida's river).</summary>
        Dock,
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
        /// <summary>
        /// The city whose route this is (Progression.Cities' ids: "original" for Kamakura, "florida"...). Each city has its own
        /// routes from its own home to its own school (docs/CITIES.md).
        /// </summary>
        public readonly string city;
        /// <summary>
        /// Where the leg after each stop starts, when a ride takes the kid on from that stop (one per stop, null where the next leg
        /// starts at the stop itself), or null when no leg of the route has a ride before it.
        /// </summary>
        public readonly string[] arrive;
        /// <summary>
        /// The ride played between a stop and the next leg (one per stop: a Rides id, or null), or null when the route has none:
        /// a short scene that plays by itself (docs/CITIES.md, "A ride, between legs").
        /// </summary>
        public readonly string[] rides;

        public Route(string id, int chapter, string[] levels, string challenge, string[] stops)
            : this(id, chapter, levels, challenge, stops, KamakuraId, null, null) { }

        public Route(string id, int chapter, string[] levels, string challenge, string[] stops, string city, string[] arrive, string[] rides)
        {
            this.id = id;
            this.chapter = chapter;
            this.levels = levels;
            this.challenge = challenge;
            this.stops = stops;
            this.city = city;
            this.arrive = arrive;
            this.rides = rides;
        }

        /// <summary>Kamakura's id (Progression.Cities.KamakuraId: the original town's, from before the cities).</summary>
        public const string KamakuraId = "original";

        /// <summary>The stop leg <paramref name="leg"/> starts at (0: home): the stop before it, or where a ride from there arrives.</summary>
        public string StartOf(int leg)
        {
            if (leg <= 0) return null;
            if (arrive != null && leg - 1 < arrive.Length && !string.IsNullOrEmpty(arrive[leg - 1])) return arrive[leg - 1];
            return stops[leg - 1];
        }

        /// <summary>The ride played before leg <paramref name="leg"/> (between the stop before it and its start), or null.</summary>
        public string RideBefore(int leg)
        {
            if (leg <= 0 || rides == null || leg - 1 >= rides.Length) return null;
            return string.IsNullOrEmpty(rides[leg - 1]) ? null : rides[leg - 1];
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

        /// <summary>
        /// Florida's stops (Miami: docs/CITIES.md, "Florida (Miami), USA"). A mini-game leg is played at one stop, so it starts and
        /// ends there (Uncle Rey's dock, the drugstore); the people mover takes the kid from the Underline's station to Biscayne
        /// Boulevard between two legs.
        /// </summary>
        public static readonly Stop[] FloridaStops =
        {
            // FL1 Calle Ocho Bus: the bus stop on Calle Ocho, the stop on Brickell Avenue where the bus is left, Bayfront Park.
            new Stop("calleOcho", StopKind.Bus, "Calle Ocho bus stop"),
            new Stop("brickell", StopKind.Bus, "Brickell Avenue"),
            new Stop("bayfront", StopKind.Park, "Bayfront Park"),
            // FL2 The River Way: Uncle Rey's dock on the Miami River, the corner drugstore downtown.
            new Stop("reysDock", StopKind.Dock, "Uncle Rey's dock"),
            new Stop("drugstore", StopKind.Shop, "Drugstore"),
            // FL3 Under the Line: the station on the elevated line, the people mover's stop on Biscayne Boulevard, Museum Park.
            new Stop("underline", StopKind.Station, "Underline station"),
            new Stop("biscayne", StopKind.Station, "Biscayne station"),
            new Stop("museumPark", StopKind.Park, "Museum Park"),
        };

        /// <summary>Florida's id (Progression.Cities.FloridaId).</summary>
        public const string FloridaId = "florida";
        /// <summary>Kamakura's id (Progression.Cities.KamakuraId).</summary>
        public const string KamakuraIdOfTown = Route.KamakuraId;

        /// <summary>
        /// Florida's three routes from the ranch house in Little Havana to Bayside Elementary downtown (docs/CITIES.md): FL1 by the
        /// Metrobus along Calle Ocho, FL2 along the Miami River (Uncle Rey's boat, the drugstore, a downpour), FL3 under the
        /// elevated line and round the bay on the people mover. Their levels are the city's own (FL1-1...), not the original town's.
        /// The chapter is the city's: every Florida level is chapter <see cref="FloridaChapter"/>.
        /// </summary>
        public static readonly Route[] Florida =
        {
            new Route("fl1", FloridaChapter, new[] { "FL1-1", "FL1-2", "FL1-3", "FL1-4" }, null,
                new[] { "calleOcho", "brickell", "bayfront" }, FloridaId, null, null),
            new Route("fl2", FloridaChapter, new[] { "FL2-1", "FL2-2", "FL2-3", "FL2-4", "FL2-5" }, null,
                new[] { "reysDock", "reysDock", "drugstore", "drugstore" }, FloridaId, null, null),
            new Route("fl3", FloridaChapter, new[] { "FL3-1", "FL3-2", "FL3-3" }, null,
                new[] { "underline", "museumPark" }, FloridaId, new[] { "biscayne", null }, new[] { Rides.PeopleMover, null }),
        };

        /// <summary>The chapter number of Florida's levels (after Kamakura's five): the paywall's and the catalog's unit.</summary>
        public const int FloridaChapter = 6;

        /// <summary>A city's routes (its id as Progression.Cities has it): Kamakura's for an unknown id.</summary>
        public static Route[] ForCity(string cityId)
        {
            return cityId == FloridaId ? Florida : All;
        }

        static Route[] Concat(Route[] a, Route[] b)
        {
            var list = new Route[a.Length + b.Length];
            a.CopyTo(list, 0);
            b.CopyTo(list, a.Length);
            return list;
        }

        /// <summary>
        /// Kamakura's routes (the original town's), in the order the story unlocks them (chapter 4's levels alternate: the underpass has
        /// L15 and L18, the site L16 and L17). Other cities' are in <see cref="Florida"/>; <see cref="Every"/> has them all.
        /// </summary>
        public static readonly Route[] All =
        {
            new Route("street", 1, new[] { "L01", "L02", "L03", "L04", "L05" }, "C01", new[] { "busStop", "granny", "church", "samsHouse" }),
            new Route("market", 2, new[] { "L06", "L07", "L08", "L09", "L10" }, "C02", new[] { "bakery", "postOffice", "florist", "library" }),
            new Route("beach", 3, new[] { "L11", "L12", "L13", "L14" }, "C03", new[] { "surfSchool", "lifeguard", "beachCafe" }),
            new Route("underpass", 4, new[] { "L15", "L18" }, null, new[] { "station" }),
            new Route("site", 4, new[] { "L16", "L17" }, "C04", new[] { "siteOffice" }),
            new Route("park", 5, new[] { "L19", "L20", "L21", "L22", "L23" }, "C05", new[] { "bandstand", "parkCafe", "boathouse", "allotment" }),
        };

        /// <summary>Every city's routes, Kamakura's first (after <see cref="All"/> and <see cref="Florida"/>: static fields start in order).</summary>
        public static readonly Route[] Every = Concat(All, Florida);

        /// <summary>The stop called <paramref name="id"/> (home and the school included), or null.</summary>
        public static Stop StopById(string id)
        {
            if (id == Home.id) return Home;
            if (id == School.id) return School;
            foreach (var stop in Stops)
                if (stop.id == id) return stop;
            foreach (var stop in FloridaStops)
                if (stop.id == id) return stop;
            return null;
        }

        /// <summary>Where a story level starts: home for the first level of its route, else the stop the level before it ended at. Null for a challenge or an unknown id.</summary>
        public static Stop From(string levelId)
        {
            Route route;
            int i = LegIndex(levelId, out route);
            if (i < 0) return null;
            return i == 0 ? Home : StopById(route.StartOf(i));
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
            foreach (var r in Every)
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
            foreach (var route in Every)
            {
                if (route.challenge == levelId) return route;
                foreach (string id in route.levels)
                    if (id == levelId) return route;
            }
            return null;
        }

        /// <summary>The routes of one chapter (chapter 4 has two; Florida's chapter has its three).</summary>
        public static List<Route> InChapter(int chapter)
        {
            var list = new List<Route>();
            foreach (var route in Every)
                if (route.chapter == chapter) list.Add(route);
            return list;
        }

        /// <summary>The ride played before a story level (a Rides id: the route's ride from the stop before it), or null.</summary>
        public static string RideBefore(string levelId)
        {
            Route route;
            int i = LegIndex(levelId, out route);
            return i > 0 ? route.RideBefore(i) : null;
        }

        /// <summary>A route of any city by its id, or null.</summary>
        public static Route ById(string routeId)
        {
            foreach (var route in Every)
                if (route.id == routeId) return route;
            return null;
        }

        /// <summary>
        /// The number a level's node shows on the map: its leg along its route for a city's own levels ("FL2-3": 3), the original
        /// town's number otherwise ("L07": 7); "!" for a challenge.
        /// </summary>
        public static string NodeNumber(string levelId)
        {
            if (string.IsNullOrEmpty(levelId)) return "";
            if (levelId[0] == 'C') return "!";
            int dash = levelId.LastIndexOf('-');
            if (dash >= 0 && dash + 1 < levelId.Length) return levelId.Substring(dash + 1);
            return levelId.TrimStart('L').TrimStart('0');
        }

        /// <summary>The position of the route in <see cref="All"/> (Kamakura's), or -1.</summary>
        public static int IndexOf(string routeId)
        {
            for (int i = 0; i < All.Length; i++)
                if (All[i].id == routeId) return i;
            return -1;
        }
    }
}

