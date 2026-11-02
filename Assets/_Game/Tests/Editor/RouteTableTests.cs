#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>Every level is a trip home to school along exactly one of the six routes (docs/WORLD_MAP.md).</summary>
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
