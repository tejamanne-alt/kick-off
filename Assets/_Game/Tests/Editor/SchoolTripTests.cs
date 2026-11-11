#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.Levels;
using DribbleToSchool.Progression;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The trips to school (Progression/SchoolTrips) and the unlock rule they feed (Progression/LevelUnlocks; docs/WORLD_MAP.md,
    /// "School trips"). Every test works on a throwaway SaveData, never on the player's save, and needs no scene or asset.
    /// </summary>
    public class SchoolTripTests
    {
        /// <summary>The story levels in the catalog's order, challenges left out (RouteTableTests checks it against the level table).</summary>
        public static readonly string[] StoryOrder =
        {
            "L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09", "L10", "L11", "L12",
            "L13", "L14", "L15", "L16", "L17", "L18", "L19", "L20", "L21", "L22", "L23",
        };

        /// <summary>Every leg's own target in these tests: a minute, so a route of n legs rings its bell at n minutes.</summary>
        const float LegTarget = 60f;

        static float BellOf(string levelId) { return LegTarget; }

        static Route RouteCalled(string id) { return RouteTable.All[RouteTable.IndexOf(id)]; }

        static void Complete(SaveData data, params string[] levelIds)
        {
            foreach (string id in levelIds)
                if (!data.IsCompleted(id)) data.levels.Add(new LevelRecord { levelId = id, completed = true });
        }

        /// <summary>Finishes leg <paramref name="leg"/> of a route as a run does: the level is completed and the leg recorded.</summary>
        static TripVerdict Finish(SaveData data, Route route, int leg, float seconds)
        {
            Complete(data, route.levels[leg]);
            float tripTime;
            return SchoolTrips.RecordLeg(data, route, leg, seconds, SchoolTrips.TripBell(route, BellOf), out tripTime);
        }

        /// <summary>Walks a whole route from home in the given leg times; returns what the last leg made of the trip.</summary>
        static TripVerdict Walk(SaveData data, Route route, params float[] legTimes)
        {
            var verdict = TripVerdict.OnTheWay;
            for (int i = 0; i < legTimes.Length; i++) verdict = Finish(data, route, i, legTimes[i]);
            return verdict;
        }

        /// <summary>Walks each of these routes from home to school in good time (55 s a leg against 60).</summary>
        static void WalkOnTime(SaveData data, params string[] routeIds)
        {
            foreach (string id in routeIds)
            {
                var route = RouteCalled(id);
                for (int i = 0; i < route.levels.Length; i++) Finish(data, route, i, 55f);
                Assert.IsTrue(SchoolTrips.OnTime(data, id), id + " walked on time");
            }
        }

        static string Next(SaveData data, bool cozy = false)
        {
            return LevelUnlocks.NextToPlay(StoryOrder, data, cozy, null);
        }

        static bool Open(SaveData data, string levelId, bool cozy = false)
        {
            int i = System.Array.IndexOf(StoryOrder, levelId);
            return LevelUnlocks.StoryOpen(levelId, i > 0 ? StoryOrder[i - 1] : null, data, cozy);
        }

        // ---------- The trip ----------

        [Test]
        public void TheTripBellIsTheSumOfTheLegsTargets()
        {
            var street = RouteCalled("street");
            Assert.AreEqual(5 * LegTarget, SchoolTrips.TripBell(street, BellOf), 0.001f);
            Assert.AreEqual(2 * LegTarget, SchoolTrips.TargetUpTo(street, 1, BellOf), 0.001f, "the targets from home to the end of leg 1");
            Assert.AreEqual(0f, SchoolTrips.TripBell(street, id => id == "L03" ? 0f : LegTarget), 0.001f, "a leg without a bell: no trip bell");
            Assert.AreEqual(83f + 58f + 53f + 63f + 83f, SchoolTrips.TripBell(street, id =>
                id == "L01" ? 53f : id == "L02" ? 58f : id == "L03" ? 83f : id == "L04" ? 63f : 83f), 0.001f);
        }

        [Test]
        public void FinishingTheFirstLegStartsANewTrip()
        {
            var data = new SaveData();
            var street = RouteCalled("street");
            Finish(data, street, 0, 40f);
            Finish(data, street, 1, 50f);
            Finish(data, street, 2, 55f);
            Assert.AreEqual(TripVerdict.OnTheWay, Finish(data, street, 0, 45f));
            var trip = SchoolTrips.Find(data, "street");
            Assert.AreEqual(5, trip.legTimes.Count, "one time a leg");
            Assert.AreEqual(45f, trip.legTimes[0], 0.001f);
            for (int i = 1; i < 5; i++) Assert.AreEqual(SchoolTrips.NotWalked, trip.legTimes[i], 0.001f, "leg " + i + " forgotten");
        }

        [Test]
        public void AFinishedLegReplacesItsTimeAndForgetsTheLegsAfterIt()
        {
            var data = new SaveData();
            var street = RouteCalled("street");
            Walk(data, street, 40f, 50f, 55f, 45f);
            float tripTime;
            Complete(data, "L02");
            Assert.AreEqual(TripVerdict.OnTheWay, SchoolTrips.RecordLeg(data, street, 1, 30f, 300f, out tripTime));
            Assert.AreEqual(70f, tripTime, 0.001f, "the trip so far: leg 0 and the new leg 1");
            var legs = SchoolTrips.Find(data, "street").legTimes;
            Assert.AreEqual(40f, legs[0], 0.001f);
            Assert.AreEqual(30f, legs[1], 0.001f);
            Assert.AreEqual(SchoolTrips.NotWalked, legs[2], 0.001f);
            Assert.AreEqual(SchoolTrips.NotWalked, legs[3], 0.001f);
        }

        [Test]
        public void ATripIsContinuousOnlyWhenEveryEarlierLegWasWalked()
        {
            var data = new SaveData();
            var street = RouteCalled("street");
            float before;
            Assert.IsTrue(SchoolTrips.TimeBefore(data, street, 0, out before), "the first leg always starts a trip");
            Assert.AreEqual(0f, before, 0.001f);
            Assert.IsFalse(SchoolTrips.TimeBefore(data, street, 2, out before), "nothing walked yet");

            Walk(data, street, 40f, 50f);
            Assert.IsTrue(SchoolTrips.TimeBefore(data, street, 2, out before));
            Assert.AreEqual(90f, before, 0.001f);
            Assert.IsFalse(SchoolTrips.TimeBefore(data, street, 3, out before), "leg 2 has not been walked in this trip");

            // Leg 2 played on its own still counts once the legs before it are there; leg 3 then follows on.
            Finish(data, street, 2, 55f);
            Assert.IsTrue(SchoolTrips.TimeBefore(data, street, 3, out before));
            Assert.AreEqual(145f, before, 0.001f);
        }

        [Test]
        public void AWholeTripBeforeTheBellIsOnTimeForGood()
        {
            var data = new SaveData();
            var street = RouteCalled("street");
            Assert.AreEqual(TripVerdict.OnTime, Walk(data, street, 70f, 50f, 60f, 55f, 60f), "295 s against a bell at 300 s");
            var trip = SchoolTrips.Find(data, "street");
            Assert.IsTrue(trip.onTime);
            Assert.AreEqual(295f, trip.bestTripTime, 0.001f);

            // A later trip that is late does not take it away (and the best time stays).
            Assert.AreEqual(TripVerdict.Late, Walk(data, street, 70f, 70f, 70f, 70f, 70f));
            Assert.IsTrue(SchoolTrips.OnTime(data, "street"));
            Assert.AreEqual(295f, trip.bestTripTime, 0.001f);

            // A quicker one improves it.
            Assert.AreEqual(TripVerdict.OnTime, Walk(data, street, 50f, 50f, 50f, 50f, 50f));
            Assert.AreEqual(250f, trip.bestTripTime, 0.001f);
        }

        [Test]
        public void ATripThatGetsToSchoolAsTheBellRingsIsOnTime()
        {
            var data = new SaveData();
            Assert.AreEqual(TripVerdict.OnTime, Walk(data, RouteCalled("street"), 60f, 60f, 60f, 60f, 60f));
            var other = new SaveData();
            Assert.AreEqual(TripVerdict.Late, Walk(other, RouteCalled("street"), 60f, 60f, 60f, 60f, 60.1f));
        }

        [Test]
        public void ALateTripIsForgottenAndRetryingTheLastLegCannotFixIt()
        {
            var data = new SaveData();
            var street = RouteCalled("street");
            Assert.AreEqual(TripVerdict.Late, Walk(data, street, 70f, 70f, 70f, 70f, 25f), "305 s against a bell at 300 s");
            var trip = SchoolTrips.Find(data, "street");
            Assert.IsFalse(trip.onTime);
            foreach (float t in trip.legTimes) Assert.AreEqual(SchoolTrips.NotWalked, t, 0.001f, "the whole trip is forgotten");

            // Only the last leg again, however quick: no trip from home, so no verdict and the stage stays shut.
            Assert.AreEqual(TripVerdict.Untimed, Finish(data, street, 4, 5f));
            Assert.IsFalse(SchoolTrips.OnTime(data, "street"));
            Assert.IsFalse(Open(data, "L06"));

            // The whole way again from home, on time: open.
            Assert.AreEqual(TripVerdict.OnTime, Walk(data, street, 55f, 55f, 55f, 55f, 55f));
            Assert.IsTrue(Open(data, "L06"));
        }

        [Test]
        public void TheLastLegPlayedOnItsOwnIsUntimed()
        {
            var data = new SaveData();
            var market = RouteCalled("market");
            Assert.AreEqual(TripVerdict.Untimed, Finish(data, market, 4, 10f));
            Assert.IsFalse(SchoolTrips.OnTime(data, "market"));
            Assert.AreEqual(0f, SchoolTrips.Find(data, "market").bestTripTime, 0.001f);

            // A trip with a hole in it (leg 2 never walked) is untimed too.
            var other = new SaveData();
            Finish(other, market, 0, 30f);
            Finish(other, market, 1, 30f);
            Finish(other, market, 3, 30f);
            float tripTime;
            Complete(other, "L10");
            Assert.AreEqual(TripVerdict.Untimed, SchoolTrips.RecordLeg(other, market, 4, 30f, 300f, out tripTime));
            Assert.AreEqual(-1f, tripTime, 0.001f, "no trip time without every leg");
        }

        [Test]
        public void MissingTheBellForgetsTheTripButKeepsAnEarlierOnTime()
        {
            var data = new SaveData();
            var beach = RouteCalled("beach");
            Walk(data, beach, 50f, 50f, 50f, 50f);
            Assert.IsTrue(SchoolTrips.OnTime(data, "beach"));
            Walk(data, beach, 80f, 80f, 80f);
            SchoolTrips.MissBell(data, beach);
            float before;
            Assert.IsFalse(SchoolTrips.TimeBefore(data, beach, 3, out before), "starting the last leg again after the bell is untimed");
            Assert.IsTrue(SchoolTrips.OnTime(data, "beach"));
            SchoolTrips.MissBell(new SaveData(), beach);
        }

        [Test]
        public void ATripRecordHasOneTimeForEachLegOfItsRoute()
        {
            var data = new SaveData();
            data.trips.Add(new TripRecord { routeId = "site", legTimes = new List<float> { 10f, 20f, 30f, 40f } });
            data.trips.Add(new TripRecord { routeId = "underpass", legTimes = null });
            Assert.AreEqual(2, SchoolTrips.Get(data, RouteCalled("site")).legTimes.Count, "trimmed to the route's two legs");
            Assert.AreEqual(2, SchoolTrips.Get(data, RouteCalled("underpass")).legTimes.Count, "a missing list is made");
            Assert.AreEqual(5, SchoolTrips.Get(data, RouteCalled("park")).legTimes.Count, "a new record");
            Assert.AreEqual(3, data.trips.Count, "one record a route");
            Assert.IsNull(SchoolTrips.Find(new SaveData { trips = null }, "park"));
        }

        // ---------- Unlocking ----------

        [Test]
        public void AStoryLevelNeedsTheOneBeforeIt()
        {
            var data = new SaveData();
            Assert.IsTrue(Open(data, "L01"), "the first level is always open");
            Assert.IsFalse(Open(data, "L02"));
            Finish(data, RouteCalled("street"), 0, 30f);
            Assert.IsTrue(Open(data, "L02"), "within a stage, finishing a leg opens the next one whatever its time");
            Finish(data, RouteCalled("street"), 1, 500f);
            Assert.IsTrue(Open(data, "L03"), "a slow leg does not hold the next leg back");
        }

        [Test]
        public void TheNextStageNeedsATripToSchoolOnTime()
        {
            var data = new SaveData();
            var street = RouteCalled("street");
            Walk(data, street, 70f, 70f, 70f, 70f, 70f);
            Assert.IsTrue(data.IsCompleted("L05"));
            Assert.IsFalse(Open(data, "L06"), "late for school: Market Street stays shut");
            Assert.AreEqual("street", LevelUnlocks.HeldBackBy("L06", "L05", data, false).id);
            Assert.IsNull(LevelUnlocks.HeldBackBy("L07", "L06", data, false), "L07 is shut because L06 is not done, not by a trip");

            Walk(data, street, 60f, 60f, 60f, 60f, 60f);
            Assert.IsTrue(Open(data, "L06"));
            Assert.IsNull(LevelUnlocks.HeldBackBy("L06", "L05", data, false));
        }

        [Test]
        public void CozyModeOpensStagesWithoutATrip()
        {
            var data = new SaveData();
            Complete(data, "L01", "L02", "L03", "L04", "L05");
            Assert.IsFalse(Open(data, "L06"));
            Assert.IsTrue(Open(data, "L06", true));
            Assert.IsNull(LevelUnlocks.HeldBackBy("L06", "L05", data, true));
            Assert.AreEqual("L06", Next(data, true));
        }

        [Test]
        public void ALevelAlreadyFinishedStaysOpen()
        {
            // Played in cozy mode, then the bell turned back on: what was played stays playable.
            var data = new SaveData();
            Complete(data, "L01", "L02", "L03", "L04", "L05", "L06", "L07");
            Assert.IsTrue(Open(data, "L06"));
            Assert.IsTrue(Open(data, "L07"));
            Assert.IsTrue(Open(data, "L08"), "within the stage, the next leg after a finished one");
        }

        [Test]
        public void NextToPlayIsTheFirstOpenLevelOrTheStageToWalkAgain()
        {
            var data = new SaveData();
            Assert.AreEqual("L01", Next(data));
            var street = RouteCalled("street");
            Walk(data, street, 50f, 50f);
            Assert.AreEqual("L03", Next(data));
            Walk(data, street, 70f, 70f, 70f, 70f, 70f);
            Assert.AreEqual("L01", Next(data), "late for school: the map shows the stage to walk again from home");
            Walk(data, street, 60f, 60f, 60f, 60f, 60f);
            Assert.AreEqual("L06", Next(data));

            // A chapter that is not paid for is skipped, as before.
            Assert.AreEqual("L23", LevelUnlocks.NextToPlay(StoryOrder, data, false, id => System.Array.IndexOf(StoryOrder, id) < 5));
        }

        [Test]
        public void ChapterFoursTwoRoutesInterleave()
        {
            // The catalog has L15 (underpass, from home), L16 (site, from home), L17 (site, to school), L18 (underpass, to school).
            var data = new SaveData();
            WalkOnTime(data, "street", "market", "beach");
            Assert.AreEqual("L15", Next(data));
            var underpass = RouteCalled("underpass");
            var site = RouteCalled("site");

            Assert.AreEqual(TripVerdict.OnTheWay, Finish(data, underpass, 0, 50f));
            Assert.IsTrue(Open(data, "L16"), "L15 is the underpass's first leg, not a last one");
            Assert.AreEqual(TripVerdict.OnTheWay, Finish(data, site, 0, 70f));
            Assert.IsTrue(Open(data, "L17"));
            Assert.AreEqual(TripVerdict.Late, Finish(data, site, 1, 70f), "the site's two legs in 140 s against 120 s");
            Assert.IsFalse(Open(data, "L18"), "the site ends at school late: the underpass's last leg waits");
            Assert.AreEqual("L16", Next(data), "walk the site again from home");

            // The underpass's trip is untouched by the site's legs walked in between.
            float before;
            Assert.IsTrue(SchoolTrips.TimeBefore(data, underpass, 1, out before));
            Assert.AreEqual(50f, before, 0.001f);

            Assert.AreEqual(TripVerdict.OnTime, Walk(data, site, 55f, 60f));
            Assert.IsTrue(Open(data, "L18"));
            Assert.AreEqual("L18", Next(data));
            Assert.AreEqual(TripVerdict.OnTime, Finish(data, underpass, 1, 65f), "L15 then L18: 115 s against 120 s");
            Assert.IsTrue(Open(data, "L19"));
            Assert.AreEqual("L19", Next(data));

            // Late along the underpass instead: the park waits, and the map goes back to L15.
            var late = new SaveData();
            WalkOnTime(late, "street", "market", "beach");
            Finish(late, underpass, 0, 80f);
            Walk(late, site, 55f, 55f);
            Assert.AreEqual(TripVerdict.Late, Finish(late, underpass, 1, 60f));
            Assert.IsFalse(Open(late, "L19"));
            Assert.AreEqual("underpass", LevelUnlocks.HeldBackBy("L19", "L18", late, false).id);
            Assert.AreEqual("L15", Next(late));
        }

        // ---------- Old saves ----------

        [Test]
        public void UpgradingAnOldSaveMarksTheRoutesItFinishedOnTime()
        {
            var data = new SaveData { version = 1, trips = null };
            Complete(data, "L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08", "L09", "L10", "L11", "L15", "L16", "L17");
            SchoolTrips.Upgrade(data);
            Assert.IsNotNull(data.trips);
            Assert.IsTrue(SchoolTrips.OnTime(data, "street"));
            Assert.IsTrue(SchoolTrips.OnTime(data, "market"));
            Assert.IsTrue(SchoolTrips.OnTime(data, "site"), "L17 ends the site's trip");
            Assert.IsFalse(SchoolTrips.OnTime(data, "beach"));
            Assert.IsFalse(SchoolTrips.OnTime(data, "underpass"));
            // Everything the old save could play it still can.
            Assert.IsTrue(Open(data, "L06"));
            Assert.IsTrue(Open(data, "L11"));
            Assert.IsTrue(Open(data, "L12"));
            Assert.IsTrue(Open(data, "L18"));
            Assert.AreEqual("L12", Next(data));
        }

        [Test]
        public void ASaveThatAlreadyHasTripsIsNotUpgradedAgain()
        {
            Assert.GreaterOrEqual(SaveData.CurrentVersion, SchoolTrips.TripsVersion);
            var data = new SaveData();
            Assert.AreEqual(SaveData.CurrentVersion, data.version, "a new save starts at the current version");
            Complete(data, "L01", "L02", "L03", "L04", "L05");
            SchoolTrips.Upgrade(data);
            Assert.IsFalse(SchoolTrips.OnTime(data, "street"), "a finished route in a current save still needs its trip");
            Assert.IsEmpty(data.trips);
        }

        [Test]
        public void ACityWithOnlySomeLevelsPointsToTheFirstShortOfThreeStars()
        {
            var stars = new Dictionary<string, int> { { "L11", 3 }, { "L12", 2 }, { "L13", 3 }, { "L14", 1 } };
            var beach = new List<string> { "L11", "L12", "L13", "L14" };
            Assert.AreEqual("L12", LevelUnlocks.FirstShortOfStars(beach, id => stars[id]));
            stars["L12"] = 3; stars["L14"] = 3;
            Assert.AreEqual("L11", LevelUnlocks.FirstShortOfStars(beach, id => stars[id]), "all three-starred: the first");
            Assert.IsNull(LevelUnlocks.FirstShortOfStars(new List<string>(), id => 0));
        }
    }
}
#endif
