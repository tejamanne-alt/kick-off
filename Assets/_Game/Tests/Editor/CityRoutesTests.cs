#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// A city's own routes (Levels/CityRoutes) are its design (docs/CITIES.md) and its map plan
    /// (review/kamakura/map/KamakuraMapLayout.json): every route a trip from home to school in legs, each leg's stops on
    /// the map, each name in every language, and nothing shared with the original town's routes the game plays now.
    /// </summary>
    public class CityRoutesTests
    {
        static readonly CityRouteSet Kamakura = CityRoutes.Kamakura;

        static string RepoFile(string path) { return Path.Combine(Path.GetDirectoryName(Application.dataPath), path); }

        [Test]
        public void KamakuraIsFoundByItsCityIdAndOnlyItHasRoutesSoFar()
        {
            Assert.AreSame(Kamakura, CityRoutes.For(Progression.Cities.KamakuraId));
            Assert.IsNull(CityRoutes.For(Progression.Cities.FloridaId));
        }

        [Test]
        public void KamakuraHasThreeRoutesOfFourFiveAndThreeLegs()
        {
            Assert.AreEqual(new[] { "KM1", "KM2", "KM3" }, System.Array.ConvertAll(Kamakura.routes, r => r.id));
            Assert.AreEqual(new[] { 4, 5, 3 }, System.Array.ConvertAll(Kamakura.routes, r => r.levels.Length));
            for (int i = 0; i < Kamakura.routes.Length; i++)
                Assert.AreEqual(i + 1, Kamakura.routes[i].chapter, "a city's route's chapter is its number");
        }

        [Test]
        public void EveryRouteRunsFromHomeThroughItsStopsToSchool()
        {
            var used = new HashSet<string>();
            foreach (var route in Kamakura.routes)
            {
                Assert.AreEqual(route.levels.Length - 1, route.stops.Length, route.id + ": one stop between each two legs");
                Assert.IsTrue(Kamakura.From(route.levels[0]).IsHome, route.id + " starts at home");
                Assert.IsTrue(Kamakura.To(route.levels[route.levels.Length - 1]).IsSchool, route.id + " ends at school");
                for (int i = 0; i < route.stops.Length; i++)
                {
                    var stop = Kamakura.StopById(route.stops[i]);
                    Assert.IsNotNull(stop, "no stop called " + route.stops[i]);
                    Assert.IsTrue(used.Add(stop.id), stop.id + " is on two routes");
                    Assert.AreSame(stop, Kamakura.To(route.levels[i]), route.levels[i] + " ends at " + stop.id);
                    Assert.AreSame(stop, Kamakura.From(route.levels[i + 1]), route.levels[i + 1] + " starts at " + stop.id);
                    Assert.AreSame(route, Kamakura.Of(route.levels[i]));
                }
            }
            Assert.AreEqual(Kamakura.stops.Length, used.Count, "every stop is on a route");
        }

        [Test]
        public void NoLevelOrStopIsSharedWithTheOriginalTown()
        {
            var isChallenge = new List<bool>();
            var scenes = new List<string>();
            var table = GeneratedContent.LevelTable(out isChallenge, out scenes);
            var town = new HashSet<string>();
            foreach (var entry in table) town.Add(entry.Key);
            foreach (string level in Kamakura.Levels)
            {
                Assert.IsFalse(town.Contains(level), level + " is also one of the original town's levels");
                Assert.IsNull(RouteTable.Of(level), level + " is on one of the original town's routes");
            }
            foreach (var stop in Kamakura.stops)
                Assert.IsNull(RouteTable.StopById(stop.id), stop.id + " is also one of the original town's stops");
        }

        [Test]
        public void EveryLegIsAsDocsCitiesDesignsIt()
        {
            string cities = File.ReadAllText(RepoFile("docs/CITIES.md"));
            var designed = new Dictionary<string, KeyValuePair<string, string>>();
            foreach (Match m in Regex.Matches(cities, @"\*\*(KM\d-\d) ([^*]+)\*\* \(([^)]*)\)"))
                designed[m.Groups[1].Value] = new KeyValuePair<string, string>(m.Groups[2].Value, m.Groups[3].Value);
            var english = StringTables.For("en");
            foreach (string level in Kamakura.Levels)
            {
                Assert.IsTrue(designed.ContainsKey(level), level + " is not in docs/CITIES.md");
                var leg = Kamakura.LegOf(level);
                Assert.IsNotNull(leg, level + " has no leg");
                string kind = designed[level].Value;
                var expected = kind.StartsWith("mini-game") ? LegKind.MiniGame : kind.StartsWith("twist") ? LegKind.Twist : LegKind.Dribble;
                Assert.AreEqual(expected, leg.kind, level + " is a " + kind);
                if (leg.game != null) StringAssert.Contains(leg.game, kind, level + "'s game");
                Assert.AreEqual(designed[level].Key, english[leg.NameKey], level + "'s name");
            }
            Assert.AreEqual(designed.Count, new List<string>(Kamakura.Levels).Count, "docs/CITIES.md designs exactly these legs");
        }

        [Test]
        public void EveryRouteStopAndLevelIsNamedInEveryLanguage()
        {
            foreach (string code in new[] { "en", "es" })
            {
                var table = StringTables.For(code);
                foreach (var route in Kamakura.routes) Assert.IsTrue(table.ContainsKey(route.NameKey), code + ": " + route.NameKey);
                foreach (var stop in Kamakura.stops)
                {
                    Assert.IsTrue(table.ContainsKey(stop.NameKey), code + ": " + stop.NameKey);
                    Assert.IsTrue(table.ContainsKey(stop.ToKey), code + ": " + stop.ToKey);
                }
                foreach (string level in Kamakura.Levels) Assert.IsTrue(table.ContainsKey("level." + level), code + ": level." + level);
            }
        }

        [Test]
        public void TheMapPlanHasEveryRouteNodeAndStopOnItsRoute()
        {
            string path = RepoFile("review/kamakura/map/KamakuraMapLayout.json");
            Assert.IsTrue(File.Exists(path), "the map plan (tools/city_map/kamakura.py writes it)");
            var layout = JsonUtility.FromJson<TownMapLayout>(File.ReadAllText(path));
            Assert.AreEqual(new[] { "KM1", "KM2", "KM3" }, System.Array.ConvertAll(layout.routes, r => r.id));
            var nodes = new HashSet<string>();
            foreach (var node in layout.nodes) Assert.IsTrue(nodes.Add(node.id), "two nodes for " + node.id);
            foreach (string level in Kamakura.Levels) Assert.IsTrue(nodes.Contains(level), level + " has no node on the map");
            Assert.AreEqual(nodes.Count, new List<string>(Kamakura.Levels).Count, "a node for every level and nothing else");
            var stops = new Dictionary<string, string>();
            foreach (var stop in layout.stops) stops[stop.id] = stop.route;
            foreach (var route in Kamakura.routes)
                foreach (string id in route.stops)
                    Assert.AreEqual(route.id, stops.ContainsKey(id) ? stops[id] : null, id + " is on " + route.id + " on the map");
            Assert.AreEqual(Kamakura.stops.Length, stops.Count, "the map's stops are the routes' stops");
        }
    }
}
#endif
