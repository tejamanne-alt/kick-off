#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Every story level is one leg of a trip from home to school along exactly one of the six routes: the route's first level
    /// starts at home, its last ends at the school, and each level between runs from one stop to the next (docs/WORLD_MAP.md).
    /// </summary>
    public class RouteTableTests
    {
        [Test]
        public void ThereAreSixRoutesWithUniqueIds()
        {
            Assert.AreEqual(6, RouteTable.All.Length);
            var ids = new HashSet<string>();
            foreach (var route in RouteTable.All) Assert.IsTrue(ids.Add(route.id), "route id used twice: " + route.id);
        }

        [Test]
        public void EveryStoryLevelIsOnExactlyOneRoute()
        {
            var isChallenge = new List<bool>();
            var scenes = new List<string>();
            var table = GeneratedContent.LevelTable(out isChallenge, out scenes);
            var seen = new Dictionary<string, string>();
            foreach (var route in RouteTable.All)
                foreach (string level in route.levels)
                {
                    Assert.IsFalse(seen.ContainsKey(level), level + " is on two routes: " + (seen.ContainsKey(level) ? seen[level] : "") + " and " + route.id);
                    seen[level] = route.id;
                }
            for (int i = 0; i < table.Count; i++)
            {
                if (isChallenge[i]) continue;
                Assert.IsTrue(seen.ContainsKey(table[i].Key), table[i].Key + " is on no route");
            }
            int story = 0;
            foreach (bool challenge in isChallenge) if (!challenge) story++;
            Assert.AreEqual(story, seen.Count, "the routes list exactly the story levels");
        }

        [Test]
        public void EveryRouteStaysInItsChapterAndEveryChallengeIsOnTheRouteOfItsChapter()
        {
            var isChallenge = new List<bool>();
            var scenes = new List<string>();
            var table = GeneratedContent.LevelTable(out isChallenge, out scenes);
            var chapterOf = new Dictionary<string, int>();
            foreach (var entry in table) chapterOf[entry.Key] = entry.Value;
            foreach (var route in RouteTable.All)
            {
                foreach (string level in route.levels)
                    Assert.AreEqual(route.chapter, chapterOf[level], level + " is in chapter " + chapterOf[level] + " but its route " + route.id + " is chapter " + route.chapter);
                if (route.challenge != null)
                    Assert.AreEqual(route.chapter, chapterOf[route.challenge], route.challenge + " is not in the chapter of route " + route.id);
            }
            // Each challenge belongs to a route (so the map can put its gold node beside it).
            for (int i = 0; i < table.Count; i++)
                if (isChallenge[i]) Assert.IsNotNull(RouteTable.Of(table[i].Key), table[i].Key + " is on no route");
        }

        [Test]
        public void AChapterWithTwoRoutesSplitsItsLevelsBetweenThem()
        {
            Assert.AreEqual(2, RouteTable.InChapter(4).Count);
            Assert.AreEqual(1, RouteTable.InChapter(1).Count);
            Assert.AreEqual("underpass", RouteTable.Of("L15").id);
            Assert.AreEqual("site", RouteTable.Of("L16").id);
            Assert.AreEqual("site", RouteTable.Of("L17").id);
            Assert.AreEqual("underpass", RouteTable.Of("L18").id);
            Assert.AreEqual("beach", RouteTable.Of("C03").id);
            Assert.IsNull(RouteTable.Of("L99"));
        }

        [Test]
        public void EveryRouteRunsFromHomeThroughItsStopsToSchool()
        {
            var seen = new Dictionary<string, string>();
            foreach (var route in RouteTable.All)
            {
                Assert.IsNotNull(route.stops, route.id + " has no stops");
                Assert.AreEqual(route.levels.Length - 1, route.stops.Length, route.id + ": one stop between each two levels");
                foreach (string id in route.stops)
                {
                    Assert.IsNotNull(RouteTable.StopById(id), route.id + ": unknown stop " + id);
                    Assert.IsFalse(seen.ContainsKey(id), id + " is on two routes: " + (seen.ContainsKey(id) ? seen[id] : "") + " and " + route.id);
                    seen[id] = route.id;
                }
                Assert.AreSame(RouteTable.Home, RouteTable.From(route.levels[0]), route.levels[0] + " is the first level of " + route.id + ": it starts at home");
                Assert.AreSame(RouteTable.School, RouteTable.To(route.levels[route.levels.Length - 1]), route.id + "'s last level ends at the school");
                for (int i = 0; i + 1 < route.levels.Length; i++)
                {
                    var end = RouteTable.To(route.levels[i]);
                    Assert.IsFalse(end.IsHome || end.IsSchool, route.levels[i] + " is not the last level of " + route.id + ": it ends at a stop on the way");
                    Assert.AreSame(end, RouteTable.From(route.levels[i + 1]), route.levels[i + 1] + " starts where " + route.levels[i] + " ended");
                }
                foreach (string level in route.levels)
                    Assert.AreNotSame(RouteTable.From(level), RouteTable.To(level), level + " goes somewhere");
            }
            Assert.AreEqual(RouteTable.Stops.Length, seen.Count, "every stop is on a route");
            Assert.IsNull(RouteTable.From("C01"), "a challenge is no leg");
            Assert.IsNull(RouteTable.To("L99"));
            Assert.AreEqual("bakery", RouteTable.To("L06").id);
            Assert.AreEqual("station", RouteTable.From("L18").id);
        }

        [Test]
        public void EveryStopHasAUniqueIdANameInEveryLanguageAndASetPiece()
        {
            var ids = new HashSet<string> { RouteTable.Home.id, RouteTable.School.id };
            foreach (var stop in RouteTable.Stops)
            {
                Assert.IsTrue(ids.Add(stop.id), "stop id used twice: " + stop.id);
                Assert.IsFalse(stop.IsHome || stop.IsSchool, stop.id + ": home and the school are the routes' ends, not stops between levels");
                Assert.IsFalse(string.IsNullOrEmpty(stop.signName), stop.id + " has no English name for the levels' signs");
                Assert.Less(stop.signName.Length, 20, stop.id + ": the name is too long for the route sign");
                Assert.Contains(stop.id, StreetBuilder.SetPieces, stop.id + " has no set piece in StreetBuilder.StopFront");
                foreach (string code in Loc.Languages)
                {
                    var table = StringTables.For(code);
                    Assert.IsTrue(table.ContainsKey(stop.NameKey) && !string.IsNullOrEmpty(table[stop.NameKey]), code + ": " + stop.NameKey);
                    Assert.IsTrue(table.ContainsKey(stop.ToKey) && !string.IsNullOrEmpty(table[stop.ToKey]), code + ": " + stop.ToKey);
                }
            }
            Assert.AreEqual(RouteTable.Stops.Length, StreetBuilder.SetPieces.Length, "a set piece for a stop that is on no route");
            Assert.AreEqual("place.home", RouteTable.Home.NameKey);
            Assert.AreEqual("place.school", RouteTable.School.NameKey);
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in new[] { "leg.fromTo", "results.madeTo", "results.reachedTo" })
                    Assert.IsTrue(table.ContainsKey(key), code + ": " + key);
                Assert.IsTrue(table["results.madeTo"].Contains("{0}") && table["results.reachedTo"].Contains("{0}") && table["leg.fromTo"].Contains("{1}"), code + ": the leg strings name the places");
            }
        }

        [Test]
        public void EveryRouteIsNamedInEveryLanguage()
        {
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (var route in RouteTable.All)
                    Assert.IsTrue(table.ContainsKey(route.NameKey) && !string.IsNullOrEmpty(table[route.NameKey]), code + ": " + route.NameKey);
                Assert.IsTrue(table.ContainsKey("place.home"), code + ": place.home");
                Assert.IsTrue(table.ContainsKey("place.school"), code + ": place.school");
            }
        }
    }
}
#endif
