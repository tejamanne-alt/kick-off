#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The town map's data (docs/WORLD_MAP.md): Resources/TownMapLayout.json, as written for the rendered picture
    /// Resources/UI/TownMap.jpg, must follow the agreed contract: the frame and its core, every story level and challenge
    /// with a node, nodes and places in the core's inner area and apart from each other, story nodes on their own route in
    /// play order and challenges beside theirs, six routes from the house to the school that keep apart, names that do not
    /// run into routes, nodes or each other, route colours that tell apart, and every string in both languages. Each test
    /// lists every offender, not just the first, so that a new picture's layout can be fixed in one go.
    /// </summary>
    public class TownMapTests
    {
        // The agreed numbers (docs/WORLD_MAP.md "The layout file").
        const float InnerLeft = 120f, InnerRight = 2280f, InnerTop = 170f, InnerBottom = 1130f;   // inside the core, from its corner
        const float NodeApart = 190f;
        const float StoryOnRoute = 12f;
        const float ChallengeNear = 130f, ChallengeFar = 260f;
        const float RouteEndReach = 25f, RouteMinLength = 1200f;
        const float RoutesApart = 90f, NearTheEnds = 320f;
        const float LabelFromRoute = 30f, LabelOffOtherRoutes = 1f, LabelFromThings = 6f;

        static TownMapLayout Load()
        {
            TownMap.Reload();
            Assert.IsTrue(TownMap.Available, "TownMapLayout.json was not read (" + TownMap.Source + "): " + TownMap.Problem);
            return TownMap.Layout;
        }

        static string Join(List<string> problems)
        {
            var sb = new StringBuilder();
            foreach (string p in problems) sb.Append("\n  ").Append(p);
            return sb.ToString();
        }

        static void NoProblems(List<string> problems, string what)
        {
            Assert.AreEqual(0, problems.Count, what + ":" + Join(problems));
        }

        static List<KeyValuePair<string, int>> Table(out List<bool> isChallenge)
        {
            List<string> scenes;
            return GeneratedContent.LevelTable(out isChallenge, out scenes);
        }

        static Vector2 InCore(Vector2 p)
        {
            return p - new Vector2(TownMap.Core.x, TownMap.Core.y);
        }

        static bool InInnerArea(Vector2 p)
        {
            Vector2 c = InCore(p);
            return c.x >= InnerLeft && c.x <= InnerRight && c.y >= InnerTop && c.y <= InnerBottom;
        }

        // ------------------------------------------------------------------ the frame and the picture

        [Test]
        public void TheLayoutHasTheAgreedFrameAndCore()
        {
            var layout = Load();
            Assert.AreEqual(3200, layout.width);
            Assert.AreEqual(1800, layout.height);
            Assert.AreEqual("UI/TownMap", layout.image);
            Assert.AreEqual(400f, layout.core.x);
            Assert.AreEqual(225f, layout.core.y);
            Assert.AreEqual(2400f, layout.core.w);
            Assert.AreEqual(1350f, layout.core.h);
        }

        [Test]
        public void ThePictureIsThereAt3200By1800()
        {
            Load();
            string path = Application.dataPath + "/_Game/Resources/UI/TownMap.jpg";
            Assert.IsTrue(File.Exists(path), "the picture is missing: " + path);
            int w, h;
            Assert.IsTrue(JpegSize(File.ReadAllBytes(path), out w, out h), "TownMap.jpg is not a readable JPEG");
            Assert.AreEqual(3200, w, "the picture's width");
            Assert.AreEqual(1800, h, "the picture's height");
        }

        /// <summary>The size in the first start-of-frame marker of a JPEG.</summary>
        static bool JpegSize(byte[] data, out int width, out int height)
        {
            width = height = 0;
            if (data.Length < 4 || data[0] != 0xFF || data[1] != 0xD8) return false;
            int i = 2;
            while (i + 9 < data.Length)
            {
                if (data[i] != 0xFF) { i++; continue; }
                byte marker = data[i + 1];
                if (marker == 0xFF) { i++; continue; }
                if (marker >= 0xC0 && marker <= 0xCF && marker != 0xC4 && marker != 0xC8 && marker != 0xCC)
                {
                    height = (data[i + 5] << 8) | data[i + 6];
                    width = (data[i + 7] << 8) | data[i + 8];
                    return true;
                }
                int length = (data[i + 2] << 8) | data[i + 3];
                i += 2 + length;
            }
            return false;
        }

        // ------------------------------------------------------------------ nodes

        [Test]
        public void EveryStoryLevelAndChallengeHasExactlyOneNode()
        {
            Load();
            List<bool> isChallenge;
            var table = Table(out isChallenge);
            var seen = new HashSet<string>();
            var problems = new List<string>();
            foreach (var node in TownMap.Nodes)
                if (!seen.Add(node.levelId)) problems.Add(node.levelId + " has two nodes");
            foreach (var entry in table)
                if (TownMap.Node(entry.Key) == null) problems.Add(entry.Key + " has no node");
            foreach (var node in TownMap.Nodes)
            {
                bool known = false;
                foreach (var entry in table) if (entry.Key == node.levelId) known = true;
                if (!known) problems.Add("the map has a node for " + node.levelId + ", which is not a level");
            }
            NoProblems(problems, "nodes and levels");
            Assert.AreEqual(28, table.Count, "23 story levels and 5 challenges");
            Assert.AreEqual(table.Count, TownMap.Nodes.Length);
        }

        [Test]
        public void EveryNodeSaysWhichSideItsNameIsOn()
        {
            var layout = Load();
            var problems = new List<string>();
            foreach (var node in layout.nodes)
                if (node.label != "below" && node.label != "above" && node.label != "left" && node.label != "right")
                    problems.Add(node.id + " has the name side \"" + node.label + "\" (below, above, left or right)");
            NoProblems(problems, "name sides");
        }

        [Test]
        public void NodesAndPlacesAreInTheCoresInnerAreaAndTheRestOfTheMapInsideTheCore()
        {
            Load();
            var problems = new List<string>();
            foreach (var node in TownMap.Nodes)
                if (!InInnerArea(node.pos)) problems.Add("node " + node.levelId + " at " + node.pos + " is outside the core's inner area");
            foreach (string id in new[] { "home", "school" })
                if (!InInnerArea(TownMap.Place(id))) problems.Add("place " + id + " at " + TownMap.Place(id) + " is outside the core's inner area");
            foreach (var d in TownMap.Districts)
                if (!TownMap.Core.Contains(d.pos)) problems.Add("district " + d.id + " is outside the core");
            foreach (var r in TownMap.Routes)
                foreach (var p in r.points)
                    if (!TownMap.Core.Contains(p)) { problems.Add("route " + r.id + " leaves the core at " + p); break; }
            NoProblems(problems, "positions");
        }

        [Test]
        public void NodeDiscsAreAtLeast190PixelsApart()
        {
            Load();
            var problems = new List<string>();
            var nodes = TownMap.Nodes;
            for (int i = 0; i < nodes.Length; i++)
                for (int j = i + 1; j < nodes.Length; j++)
                {
                    float d = Vector2.Distance(nodes[i].pos, nodes[j].pos);
                    if (d < NodeApart) problems.Add(nodes[i].levelId + " and " + nodes[j].levelId + " are " + Mathf.RoundToInt(d) + " px apart (at least " + NodeApart + ")");
                }
            NoProblems(problems, "node spacing");
        }

        [Test]
        public void StoryNodesLieOnTheirOwnRouteInPlayingOrder()
        {
            Load();
            var problems = new List<string>();
            foreach (var route in RouteTable.All)
            {
                var line = TownMap.Route(route.id).points;
                float last = -1f;
                foreach (string id in route.levels)
                {
                    var node = TownMap.Node(id);
                    if (node == null) continue;
                    float off = TownMap.DistanceTo(line, node.pos);
                    if (off > StoryOnRoute) problems.Add(id + " is " + Mathf.RoundToInt(off) + " px off its route " + route.id + " (at most " + StoryOnRoute + ")");
                    float at = TownMap.DistanceAlong(line, node.pos);
                    if (at <= last) problems.Add(id + " comes before the level before it along " + route.id);
                    last = at;
                }
            }
            NoProblems(problems, "story nodes");
        }

        [Test]
        public void ChallengeNodesSitBesideTheirRoute()
        {
            Load();
            var problems = new List<string>();
            foreach (var route in RouteTable.All)
            {
                if (route.challenge == null) continue;
                var node = TownMap.Node(route.challenge);
                if (node == null) continue;
                float off = TownMap.DistanceTo(TownMap.Route(route.id).points, node.pos);
                if (off < ChallengeNear || off > ChallengeFar) problems.Add(route.challenge + " is " + Mathf.RoundToInt(off) + " px from its route " + route.id + " (" + ChallengeNear + " to " + ChallengeFar + ")");
            }
            NoProblems(problems, "challenge nodes");
        }

        // ------------------------------------------------------------------ routes

        [Test]
        public void TheSixRoutesAreRouteTablesInItsOrder()
        {
            Load();
            Assert.AreEqual(RouteTable.All.Length, TownMap.Routes.Length);
            for (int i = 0; i < RouteTable.All.Length; i++) Assert.AreEqual(RouteTable.All[i].id, TownMap.Routes[i].id, "route " + i);
        }

        [Test]
        public void EveryRouteRunsFromHomeToSchoolAndIsLongEnough()
        {
            Load();
            var problems = new List<string>();
            foreach (var route in TownMap.Routes)
            {
                var p = route.points;
                float atHome = Vector2.Distance(p[0], TownMap.Home), atSchool = Vector2.Distance(p[p.Length - 1], TownMap.School);
                if (atHome > RouteEndReach) problems.Add(route.id + " starts " + Mathf.RoundToInt(atHome) + " px from home (at most " + RouteEndReach + ")");
                if (atSchool > RouteEndReach) problems.Add(route.id + " ends " + Mathf.RoundToInt(atSchool) + " px from the school (at most " + RouteEndReach + ")");
                if (route.length < RouteMinLength) problems.Add(route.id + " is only " + Mathf.RoundToInt(route.length) + " px long (at least " + RouteMinLength + ")");
                for (int i = 0; i + 1 < p.Length; i++)
                    if (Vector2.Distance(p[i], p[i + 1]) < 0.5f) { problems.Add(route.id + " has a zero-length segment at point " + i); break; }
            }
            NoProblems(problems, "routes");
        }

        [Test]
        public void RoutesStayAtLeast90PixelsApartExceptNearTheTwoEnds()
        {
            Load();
            var problems = new List<string>();
            var routes = TownMap.Routes;
            for (int i = 0; i < routes.Length; i++)
                for (int j = i + 1; j < routes.Length; j++)
                {
                    float worst = float.MaxValue;
                    Vector2 at = Vector2.zero;
                    for (float d = 0f; d < routes[i].length; d += 10f)
                    {
                        Vector2 p = TownMap.At(routes[i].points, d);
                        if (Vector2.Distance(p, TownMap.Home) < NearTheEnds || Vector2.Distance(p, TownMap.School) < NearTheEnds) continue;
                        float gap = TownMap.DistanceTo(routes[j].points, p);
                        if (gap < worst) { worst = gap; at = p; }
                    }
                    if (worst < RoutesApart) problems.Add(routes[i].id + " and " + routes[j].id + " come within " + Mathf.RoundToInt(worst) + " px of each other at " + at + " (at least " + RoutesApart + " beyond " + NearTheEnds + " px of home and the school)");
                }
            NoProblems(problems, "route spacing");
        }

        // ------------------------------------------------------------------ names

        [Test]
        public void LevelNamesHaveRoomBesideTheirNode()
        {
            var layout = Load();
            if (layout.placeholder)
            {
                // The stand-in layout is made from abstract diagonal streets: a 300 x 56 name beside a node on a road that runs at
                // 21 to 34 degrees always touches its own route, so the rule needs the real picture's grid of roads.
                Assert.Ignore("placeholder layout: the names' clearance is checked on the real one");
                return;
            }
            // Only the focused route's levels are named (ChapterMapScreen.BuildNode), over every route line, while every node is
            // drawn. So a name keeps clear of its own route's line and names, stays off the other routes' centre lines, and keeps
            // clear of every node.
            var problems = new List<string>();
            var nodes = TownMap.Nodes;
            var boxes = new Rect[nodes.Length];
            var routeOf = new string[nodes.Length];
            for (int i = 0; i < nodes.Length; i++)
            {
                boxes[i] = TownMap.LabelRect(nodes[i]);
                var route = RouteTable.Of(nodes[i].levelId);
                routeOf[i] = route != null ? route.id : null;
            }
            for (int i = 0; i < nodes.Length; i++)
            {
                Rect box = boxes[i];
                string who = nodes[i].levelId + "'s name (" + nodes[i].side + ")";
                if (box.xMin < TownMap.Core.xMin || box.xMax > TownMap.Core.xMax || box.yMin < TownMap.Core.yMin || box.yMax > TownMap.Core.yMax) problems.Add(who + " sticks out of the core");
                foreach (var route in TownMap.Routes)
                {
                    float gap = TownMap.DistanceToLine(box, route.points);
                    bool own = route.id == routeOf[i];
                    float need = own ? LabelFromRoute : LabelOffOtherRoutes;
                    if (gap < need)
                        problems.Add(who + (own ? " is " + Mathf.RoundToInt(gap) + " px from its own route " + route.id + " (at least " + LabelFromRoute + ")" : " crosses the " + route.id + " route's line"));
                }
                for (int j = 0; j < nodes.Length; j++)
                {
                    if (j == i) continue;
                    float disc = TownMap.DistanceToRect(box, nodes[j].pos) - TownMap.NodeRadius;
                    if (disc < LabelFromThings) problems.Add(who + " runs into the node of " + nodes[j].levelId);
                    if (j > i && routeOf[i] == routeOf[j] && TownMap.GapBetween(box, boxes[j]) < LabelFromThings) problems.Add(who + " runs into the name of " + nodes[j].levelId);
                }
            }
            NoProblems(problems, "level names");
        }

        /// <summary>The routes that follow a street of that name: every level on them has a route sign saying "via" it.</summary>
        static readonly string[] StreetRoutes = { "street", "market", "beach" };
        const float StreetNameOnRoute = 60f;

        [Test]
        public void TheStreetsTheRoutesFollowAreNamedAsTheLevelsSignsNameThem()
        {
            var layout = Load();
            if (layout.placeholder)
            {
                Assert.Ignore("placeholder layout: its street names are stand-ins");
                return;
            }
            // The levels' signs are English in every language (the route sign reads "via " + the English name), and so are the
            // map's street names.
            var english = StringTables.For("en");
            var problems = new List<string>();
            foreach (string id in StreetRoutes)
            {
                string name = english[RouteTable.All[RouteTable.IndexOf(id)].NameKey];
                var line = TownMap.Route(id).points;
                float nearest = float.MaxValue;
                foreach (var street in TownMap.Streets)
                    if (street.name == name) nearest = Mathf.Min(nearest, TownMap.DistanceTo(line, street.pos));
                if (nearest == float.MaxValue) problems.Add("no street is named \"" + name + "\", the road the " + id + " route's levels say they take");
                else if (nearest > StreetNameOnRoute) problems.Add("\"" + name + "\" is written " + Mathf.RoundToInt(nearest) + " px from the " + id + " route (at most " + StreetNameOnRoute + ")");
            }
            NoProblems(problems, "street names");
        }

        [Test]
        public void PlacesHaveRoomRoundThem()
        {
            Load();
            var problems = new List<string>();
            foreach (string id in new[] { "home", "school" })
                foreach (var node in TownMap.Nodes)
                {
                    float d = Vector2.Distance(node.pos, TownMap.Place(id));
                    if (d < 120f) problems.Add(node.levelId + " is " + Mathf.RoundToInt(d) + " px from " + id + " (the marker needs 120)");
                }
            NoProblems(problems, "places");
        }

        // ------------------------------------------------------------------ colours and strings

        static float Lab(float t)
        {
            return t > 0.008856f ? Mathf.Pow(t, 1f / 3f) : 7.787f * t + 16f / 116f;
        }

        static Vector3 ToLab(Color c)
        {
            float r = Mathf.Pow(c.r, 2.2f), g = Mathf.Pow(c.g, 2.2f), b = Mathf.Pow(c.b, 2.2f);
            float x = (0.4124f * r + 0.3576f * g + 0.1805f * b) / 0.95047f, y = 0.2126f * r + 0.7152f * g + 0.0722f * b, z = (0.0193f * r + 0.1192f * g + 0.9505f * b) / 1.08883f;
            return new Vector3(116f * Lab(y) - 16f, 500f * (Lab(x) - Lab(y)), 200f * (Lab(y) - Lab(z)));
        }

        [Test]
        public void TheSixRouteColoursTellApart()
        {
            var field = typeof(GeneratedContent).GetField("Chapters", BindingFlags.NonPublic | BindingFlags.Static);
            Assert.IsNotNull(field, "GeneratedContent.Chapters moved: update this test");
            var chapters = (ChapterInfo[])field.GetValue(null);
            var colours = new Dictionary<string, Color>();
            foreach (var route in RouteTable.All)
            {
                Color chapter = Color.white;
                foreach (var info in chapters) if (info.number == route.chapter) chapter = info.color;
                colours[route.id] = TownMap.RouteColor(route.id, chapter);
            }
            var problems = new List<string>();
            var ids = new List<string>(colours.Keys);
            for (int i = 0; i < ids.Count; i++)
                for (int j = i + 1; j < ids.Count; j++)
                {
                    float delta = (ToLab(colours[ids[i]]) - ToLab(colours[ids[j]])).magnitude;
                    if (delta < 20f) problems.Add(ids[i] + " and " + ids[j] + " differ by only " + Mathf.RoundToInt(delta) + " (Lab)");
                }
            NoProblems(problems, "route colours");
        }

        [Test]
        public void EveryStringTheMapUsesExistsInBothLanguages()
        {
            Load();
            var problems = new List<string>();
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in TownMap.LocKeys())
                    if (!table.ContainsKey(key) || string.IsNullOrEmpty(table[key])) problems.Add(code + ": " + key);
            }
            Assert.Greater(TownMap.Districts.Length, 0, "the layout names its districts");
            NoProblems(problems, "strings");
        }
    }
}
#endif
