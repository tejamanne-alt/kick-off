using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Walking to school (Cosmetics/RouteRewards): a route counts once every story level on it is done, the Locker Room's prizes
    /// for it are never sold and need three and then all six routes, and every text of the celebration is in every language.
    /// </summary>
    public class RouteRewardsTests
    {
        [Test]
        public void ARouteIsWalkedOnceEveryStoryLevelOnItIsDone()
        {
            var done = new HashSet<string>();
            Assert.AreEqual(0, RouteRewards.Walked(done.Contains));
            var park = RouteTable.All.First(r => r.id == "park");
            foreach (string id in park.levels.Take(park.levels.Length - 1)) done.Add(id);
            Assert.IsFalse(RouteRewards.IsWalked(park, done.Contains), "the last leg to school is still to walk");
            done.Add(park.levels[park.levels.Length - 1]);
            Assert.IsTrue(RouteRewards.IsWalked(park, done.Contains));
            Assert.AreEqual(1, RouteRewards.Walked(done.Contains));
            done.Add(park.challenge);   // the challenge is a detour, not a leg: it changes nothing
            Assert.AreEqual(1, RouteRewards.Walked(done.Contains));
            foreach (var route in RouteTable.All) foreach (string id in route.levels) done.Add(id);
            Assert.AreEqual(RouteRewards.RouteCount, RouteRewards.Walked(done.Contains), "every way walked: the trophy");
            Assert.AreEqual(6, RouteRewards.RouteCount);
        }

        [Test]
        public void ThePrizesForWalkingToSchoolAreNeverSold()
        {
            var rows = CosmeticsTable.Rows().Where(r => r.unlock == CosmeticUnlock.SchoolRoutes).ToList();
            Assert.AreEqual(3, rows.Count, "a flag at three ways, a ball and a trail at all six");
            foreach (var row in rows)
            {
                Assert.AreEqual(0, row.price, row.id + " is earned, not bought");
                Assert.IsTrue(row.unlockValue >= 1 && row.unlockValue <= RouteRewards.RouteCount, row.id);
            }
            Assert.AreEqual(2, rows.Count(r => r.unlockValue == RouteRewards.RouteCount), "two prizes come with the trophy");
            Assert.AreEqual(1, rows.Count(r => r.unlockValue == 3));
            var ids = CosmeticsTable.Rows().Select(r => r.id).ToList();
            Assert.AreEqual(ids.Count, ids.Distinct().Count(), "every item id is its own");
        }

        [Test]
        public void TheCelebrationIsWrittenInEveryLanguage()
        {
            var keys = new List<string>(SchoolRewardPanel.Keys)
            {
                "shop.toMap", "shop.walkOne", "shop.walkMore", "shop.routesShort", "results.medal", "results.allWalked", "hud.ballAway",
            };
            foreach (var route in RouteTable.All) keys.Add(route.NameKey);
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in keys)
                    Assert.IsTrue(table.ContainsKey(key) && table[key].Length > 0, code + ": " + key);
                Assert.IsTrue(table["school.progress"].Contains("{0}") && table["school.progress"].Contains("{1}"), code + ": the progress shows both numbers");
                Assert.IsTrue(table["school.nextReward"].Contains("{1}"), code + ": the next reward is named");
                Assert.IsTrue(table["shop.walkMore"].Contains("{0}"), code);
            }
        }
    }
}
