using System.Collections.Generic;

namespace DribbleToSchool.Levels
{
    /// <summary>
    /// One way from home to school: every story level is a trip from the kid's front door to the
    /// school gate along one of these routes (the map draws them, every level starts with the home
    /// front and ends at the school's arch, and the route's own street is what lies between).
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

        public Route(string id, int chapter, string[] levels, string challenge)
        {
            this.id = id;
            this.chapter = chapter;
            this.levels = levels;
            this.challenge = challenge;
        }

        /// <summary>The string-table key of the route's name ("route.beach").</summary>
        public string NameKey { get { return "route." + id; } }
    }

    /// <summary>
    /// The six routes from home to the one school: the general street, the market, the beach, the
    /// railway underpass, the building site's shortcut and the park. Each story level (L01 to L23) is on
    /// exactly one; each chapter's challenge sits on one of its routes. See docs/WORLD_MAP.md.
    /// </summary>
    public static class RouteTable
    {
        /// <summary>In the order the story unlocks them (chapter 4's levels alternate: the underpass has L15 and L18, the site L16 and L17).</summary>
        public static readonly Route[] All =
        {
            new Route("street", 1, new[] { "L01", "L02", "L03", "L04", "L05" }, "C01"),
            new Route("market", 2, new[] { "L06", "L07", "L08", "L09", "L10" }, "C02"),
            new Route("beach", 3, new[] { "L11", "L12", "L13", "L14" }, "C03"),
            new Route("underpass", 4, new[] { "L15", "L18" }, null),
            new Route("site", 4, new[] { "L16", "L17" }, "C04"),
            new Route("park", 5, new[] { "L19", "L20", "L21", "L22", "L23" }, "C05"),
        };

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
