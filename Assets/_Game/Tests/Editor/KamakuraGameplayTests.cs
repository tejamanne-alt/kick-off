using System.Collections.Generic;
using System.IO;
using System.Linq;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.MiniGames;
using DribbleToSchool.Progression;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Kamakura played as its own city (docs/KAMAKURA_BUILD.md KM-L99): its twelve legs are built, the routes in play find
    /// them, the errand's bento rides along the Shonan Coast to school (Progression/Errands), and the mini-games' rules hold
    /// (MiniGames/MiniGameRules: the ride, the errand, the kite thief).
    /// </summary>
    public class KamakuraGameplayTests
    {
        // ------------------------------------------------------------------ the legs and the routes

        [Test]
        public void EveryKamakuraLegIsBuiltInItsOwnScene()
        {
            var built = GeneratedContent.CityLevelTable();
            foreach (string id in CityRoutes.Kamakura.Levels)
            {
                var entry = built.FirstOrDefault(e => e.Key == id);
                Assert.IsNotNull(entry.Key, id + " has no scene in GeneratedContent.CityLevels");
                StringAssert.StartsWith(id + "_", entry.Value);
                StringAssert.EndsWith("_KM", entry.Value);
            }
            Assert.AreEqual(12, built.Count, "Kamakura's twelve legs");
        }

        [Test]
        public void RoutesFindALegByItsIdInEitherTable()
        {
            Route route;
            Assert.AreEqual(1, Routes.LegIndex("KM1-2", out route));
            Assert.AreEqual("KM1", route.id);
            Assert.AreEqual("hase", Routes.From("KM1-2").id);
            Assert.AreEqual("kamakuraStation", Routes.To("KM1-2").id);
            Assert.AreEqual(RouteTable.School.id, Routes.To("KM2-5").id);
            Assert.AreEqual(RouteTable.Home.id, Routes.From("KM3-1").id);
            // the original town's levels answer as they always have
            Assert.AreEqual(RouteTable.LegIndex("L02", out route), Routes.LegIndex("L02", out route));
            Assert.AreSame(RouteTable.Of("L02"), Routes.Of("L02"));
            Assert.AreEqual("M2", Routes.LegOf("KM2-3").game);
            Assert.IsNull(Routes.LegOf("L02"));
        }

        [Test]
        public void RoutesFindARouteByItsIdWhateverCityPlays()
        {
            Assert.IsNotNull(Routes.ById("KM2"));
            Assert.IsNotNull(Routes.ById(RouteTable.All[0].id));
            Assert.IsNull(Routes.ById("nowhere"));
        }

        [Test]
        public void KamakurasMapAndSetPicturesAreInResources()
        {
            foreach (string path in new[]
            {
                "Assets/_Game/Resources/KamakuraMapLayout.json", "Assets/_Game/Resources/UI/KamakuraMap.jpg",
                "Assets/_Game/Resources/UI/Kamakura/ride_car.png", "Assets/_Game/Resources/UI/Kamakura/ride_town.jpg",
                "Assets/_Game/Resources/UI/Kamakura/ride_stations.jpg", "Assets/_Game/Resources/UI/Kamakura/errand_counter.jpg",
                "Assets/_Game/Resources/UI/Kamakura/errand_folds.jpg",
            })
                Assert.IsTrue(File.Exists(path), path + " is missing");
            Assert.AreEqual(CityRoutes.Kamakura.layoutResource + ".json", Path.GetFileName("Assets/_Game/Resources/KamakuraMapLayout.json"));
        }

        [Test]
        public void TheMiniGamesWordsAreInEveryLanguage()
        {
            var en = StringTables.For("en");
            var keys = en.Keys.Where(k => k.StartsWith("mini.") || k.StartsWith("station.")).ToList();
            Assert.Greater(keys.Count, 30);
            foreach (string lang in new[] { "es" })
            {
                var table = StringTables.For(lang);
                var missing = keys.Where(k => !table.ContainsKey(k)).ToList();
                Assert.IsEmpty(missing, lang + " lacks " + string.Join(", ", missing));
            }
            foreach (string station in RideRules.Stations) Assert.IsTrue(en.ContainsKey("station." + station), station);
        }

        // ------------------------------------------------------------------ the errand's bento (Progression/Errands)

        static SaveData Fresh()
        {
            return new SaveData { carrying = "", badges = new List<string>() };
        }

        [Test]
        public void TheBentoRidesAlongTheCoastAfterTheErrand()
        {
            var data = Fresh();
            Errands.Wrapped(data);
            Assert.IsTrue(Errands.BentoWhole(data));
            Assert.IsFalse(Errands.LegStarts(data, "KM2-4"), "it rides on to the rocks");
            Assert.IsFalse(Errands.LegStarts(data, "KM2-5"), "and up the avenue");
            Assert.IsTrue(Errands.CarriesBento(data));
        }

        [Test]
        public void ATripFromHomeOrAnotherRouteStartsWithNothingCarried()
        {
            var data = Fresh();
            Errands.Wrapped(data);
            Assert.IsTrue(Errands.LegStarts(data, "KM2-1"), "a trip from home");
            Assert.AreEqual("", data.carrying);
            Errands.Wrapped(data);
            Assert.IsTrue(Errands.LegStarts(data, "KM1-3"), "another route");
            Errands.Wrapped(data);
            Assert.IsTrue(Errands.LegStarts(data, "KM2-3"), "the errand itself gives it anew");
        }

        [Test]
        public void AWholeBentoAtSchoolIsDeliveredOnce()
        {
            var data = Fresh();
            Errands.Wrapped(data);
            Assert.IsFalse(Errands.LegEnds(data, "KM2-4"), "the great torii is not school");
            Assert.IsTrue(Errands.CarriesBento(data));
            Assert.IsTrue(Errands.LegEnds(data, "KM2-5"));
            Assert.IsTrue(Errands.HasDelivered(data));
            Assert.AreEqual("", data.carrying, "handed over at school");
            Errands.Wrapped(data);
            Assert.IsTrue(Errands.LegEnds(data, "KM2-5"));
            Assert.AreEqual(1, data.badges.Count(b => b == Errands.DeliveredBadge), "the badge is kept once");
        }

        [Test]
        public void ABentoWithoutItsRiceBallIsNotDelivered()
        {
            var data = Fresh();
            Errands.Wrapped(data);
            Assert.IsTrue(Errands.LostRiceBall(data));
            Assert.IsFalse(Errands.LostRiceBall(data), "it can only be lost once");
            Assert.IsTrue(Errands.CarriesBento(data));
            Assert.IsFalse(Errands.LegEnds(data, "KM2-5"));
            Assert.IsFalse(Errands.HasDelivered(data));
            Assert.AreEqual("", data.carrying);
        }

        [Test]
        public void SavingTheRiceBallOnAReplayMakesTheBentoWholeAgain()
        {
            var data = Fresh();
            Assert.IsFalse(Errands.SavedRiceBall(data), "nothing carried, nothing changes");
            Errands.Wrapped(data);
            Assert.IsFalse(Errands.SavedRiceBall(data), "already whole");
            Errands.LostRiceBall(data);
            Assert.IsFalse(Errands.LegStarts(data, "KM2-4"), "the replay keeps the bento");
            Assert.IsTrue(Errands.SavedRiceBall(data));
            Assert.IsTrue(Errands.BentoWhole(data));
            Assert.IsTrue(Errands.LegEnds(data, "KM2-5"));
        }

        // ------------------------------------------------------------------ the ride (M1)

        [Test]
        public void TheCardTapIsGoodOnlyInTheGreen()
        {
            Assert.IsFalse(RideRules.CardTapGood(0.2f));
            Assert.IsTrue(RideRules.CardTapGood(0.8f));
            Assert.IsFalse(RideRules.CardTapGood(0.99f));
        }

        [Test]
        public void StopIsRightOnlyForKamakura()
        {
            Assert.AreEqual("kamakura", RideRules.Stations[RideRules.Destination]);
            for (int i = 0; i < RideRules.Stations.Length; i++)
                Assert.AreEqual(i == RideRules.Destination, RideRules.StopIsRight(i));
        }

        [Test]
        public void HoldingKickTakesMostOfABrakesPush()
        {
            var loose = new RideRules.Ball();
            var held = new RideRules.Ball();
            for (int i = 0; i < 30; i++)
            {
                RideRules.Step(ref loose, 0f, 0f, true, false, 1f / 30f);
                RideRules.Step(ref held, 0f, 0f, true, true, 1f / 30f);
            }
            Assert.Greater(loose.offset, held.offset * 2f);
            Assert.IsTrue(RideRules.Steady(held));
        }

        [Test]
        public void LeaningAgainstTheSwayKeepsTheBallSteady()
        {
            var still = new RideRules.Ball();
            var leaning = new RideRules.Ball();
            int steadyStill = 0, steadyLeaning = 0;
            for (int i = 0; i < 300; i++)
            {
                float t = i / 30f, sway = RideRules.Sway(t);
                RideRules.Step(ref still, sway, 0f, false, false, 1f / 30f);
                RideRules.Step(ref leaning, sway, sway * 0.5f, false, false, 1f / 30f);
                if (RideRules.Steady(still)) steadyStill++;
                if (RideRules.Steady(leaning)) steadyLeaning++;
            }
            Assert.Greater(steadyLeaning, steadyStill);
        }

        [Test]
        public void TheRidePaysWhatItCan()
        {
            Assert.AreEqual(0, RideRules.SteadyPay(0.3f));
            Assert.AreEqual(RideRules.SteadyCoins, RideRules.SteadyPay(0.95f));
            Assert.AreEqual(RideRules.SteadyCoins + RideRules.StopCoins + RideRules.SeatCoins, RideRules.PossibleCoins);
        }

        // ------------------------------------------------------------------ the errand (M2)

        [Test]
        public void GrandmasOrderFoldsNearAndFarBeforeTheSides()
        {
            for (int seed = 0; seed < 20; seed++)
            {
                var order = ErrandRules.Order(seed);
                Assert.AreEqual(4, order.Distinct().Count());
                CollectionAssert.AreEquivalent(new[] { ErrandRules.Corner.Near, ErrandRules.Corner.Far }, order.Take(2));
                CollectionAssert.AreEquivalent(new[] { ErrandRules.Corner.Left, ErrandRules.Corner.Right }, order.Skip(2));
                Assert.IsTrue(ErrandRules.FoldIsRight(order, 0, order[0]));
                Assert.IsFalse(ErrandRules.FoldIsRight(order, 0, order[1]));
            }
        }

        [Test]
        public void TheKnotIsPulledTightOnlyInTheGold()
        {
            Assert.IsTrue(ErrandRules.PullIsGood(0.5f));
            Assert.IsFalse(ErrandRules.PullIsGood(0.1f));
            for (float t = 0f; t < 3f; t += 0.05f)
            {
                float m = ErrandRules.KnotMarker(t);
                Assert.GreaterOrEqual(m, 0f);
                Assert.LessOrEqual(m, 1f);
            }
            Assert.AreEqual(ErrandRules.PossibleCoins, ErrandRules.Pay(0, 0));
            Assert.AreEqual(1, ErrandRules.Pay(10, 10), "never nothing: the bento is wrapped");
        }

        // ------------------------------------------------------------------ the kite thief (M4)

        [Test]
        public void TheWaveGivesTimeToRunBack()
        {
            Assert.Greater(KiteRules.TimeToGetBack(16f), KiteRules.TimeToGetBack(4f));
            Assert.Greater(KiteRules.TimeToGetBack(16f), 16f / 6f, "time for a kid dribbling at a run");
            Assert.IsTrue(KiteRules.Reached(40.5f, 40f));
            Assert.IsFalse(KiteRules.Reached(42f, 40f));
        }
    }
}
