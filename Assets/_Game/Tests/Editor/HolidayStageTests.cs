#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Holiday;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The Holiday Run's world: one stage for each story level in story order, laid end to end, with a
    /// difficulty that climbs along the lap and the school gate at the end of it.
    /// </summary>
    public class HolidayStageTests
    {
        [Test]
        public void ThereIsOneStageForEachStoryLevelInStoryOrder()
        {
            List<bool> challenge;
            List<string> scenes;
            var table = GeneratedContent.LevelTable(out challenge, out scenes);
            var story = table.Where((l, i) => !challenge[i]).ToList();
            var original = HolidayStages.Original;

            Assert.AreEqual(story.Count, original.Length, "stage count");
            for (int i = 0; i < original.Length; i++)
            {
                Assert.AreEqual(story[i].Key, original[i].levelId, "level of stage " + i);
                Assert.AreEqual(story[i].Value, original[i].chapter, "chapter of stage " + i);
                Assert.AreEqual(original[i].chapter, original[i].route, "an original stage's route is its chapter");
            }
            Assert.AreEqual(HolidayStages.Count, HolidayStages.All.Length, "table length");
            Assert.AreSame(HolidayStages.IsKamakura ? HolidayStages.Kamakura : HolidayStages.Original, HolidayStages.All, "the run in play");
        }

        [Test]
        public void KamakurasRunHasOneStageForEachOfItsDribbleLegs()
        {
            // its legs in route order, less the ride (M1) and the errand (M2), which are mini-games, not streets
            var legs = Levels.CityRoutes.Kamakura.Levels
                .Where(id => { var leg = Levels.Routes.LegOf(id); return leg == null || (leg.game != "M1" && leg.game != "M2"); })
                .ToList();
            var km = HolidayStages.Kamakura;
            CollectionAssert.AreEqual(legs, km.Select(s => s.levelId).ToList());
            int previous = 1;
            foreach (var stage in km)
            {
                Assert.AreEqual(Levels.Routes.Of(stage.levelId).id, "KM" + stage.route, stage.levelId + " is on its route");
                Assert.GreaterOrEqual(stage.route, previous, stage.levelId + " goes back a route");
                previous = stage.route;
                // built in a look whose obstacles the original run already lays: Home Street's, the beach's or the park's
                CollectionAssert.Contains(new[] { 1, 3, 5 }, stage.chapter, stage.levelId + "'s look");
                var sameLook = HolidayStages.Original.Where(o => o.chapter == stage.chapter).Aggregate(StageTraits.None, (a, o) => a | o.traits);
                Assert.AreEqual(stage.traits & ~StageTraits.School, stage.traits & sameLook & ~StageTraits.School,
                    stage.levelId + " asks for a trait its look never had in the original run");
            }
            Assert.AreEqual(3, previous, "the day ends on the third route, at school");
        }

        [Test]
        public void ChaptersFollowOneAnother()
        {
            int previous = 1;
            foreach (var stage in HolidayStages.Original)
            {
                Assert.GreaterOrEqual(stage.chapter, previous, stage.levelId + " goes back a chapter");
                Assert.LessOrEqual(stage.chapter, previous + 1, stage.levelId + " skips a chapter");
                previous = stage.chapter;
            }
            Assert.AreEqual(5, previous, "the lap ends in the last chapter");
        }

        [Test]
        public void StagesFollowOnWithoutGapsOrOverlaps()
        {
            for (int i = 0; i < HolidayStages.Count; i++)
            {
                Assert.AreEqual(HolidayStages.StageLength, HolidayStages.EndOf(i) - HolidayStages.StartOf(i), 0.001f, "length of stage " + i);
                if (i + 1 < HolidayStages.Count)
                    Assert.AreEqual(HolidayStages.EndOf(i), HolidayStages.StartOf(i + 1), 0.001f, "stage " + i + " meets the next");
                Assert.AreEqual(i, HolidayStages.StageAt(HolidayStages.StartOf(i) + 0.01f), "just inside the start of stage " + i);
                Assert.AreEqual(i, HolidayStages.StageAt(HolidayStages.EndOf(i) - 0.01f), "just inside the end of stage " + i);
            }
            Assert.AreEqual(0, HolidayStages.StageAt(-100f), "before the first stage");
            Assert.AreEqual(HolidayStages.Count - 1, HolidayStages.StageAt(1e6f), "after the last stage");
        }

        [Test]
        public void SceneNamesAreUniqueAndNumbered()
        {
            var names = new List<string>();
            for (int i = 0; i < HolidayStages.Count; i++) names.Add(HolidayStages.SceneName(i));
            Assert.AreEqual(names.Count, names.Distinct().Count(), "duplicate stage scene names");
            Assert.AreEqual(HolidayStages.ScenePrefix + "01", names[0]);
            Assert.AreEqual(HolidayStages.ScenePrefix + HolidayStages.Count.ToString("00"), names[HolidayStages.Count - 1]);
            Assert.IsFalse(names.Contains(HolidayStages.CoreSceneName), "a stage is named like the core scene");
        }

        [Test]
        public void TheKidStartsInsideTheFirstStageAndTheGateEndsTheLastOne()
        {
            Assert.Greater(HolidayStages.SpawnX, HolidayStages.StartOf(0), "spawn is inside stage 0");
            Assert.Less(HolidayStages.SpawnX, HolidayStages.EndOf(0), "spawn is inside stage 0");
            Assert.Less(HolidayStages.RunIn, HolidayStages.StageLength, "the run-in fits in a stage");

            int last = HolidayStages.Count - 1;
            Assert.IsTrue(HolidayStages.All[last].Has(StageTraits.School), "the last stage has the school");
            Assert.Greater(HolidayStages.GateX, HolidayStages.StartOf(last), "the gate stands in the last stage");
            Assert.Less(HolidayStages.GateX, HolidayStages.EndOf(last), "the gate stands in the last stage");
            for (int i = 0; i < last; i++)
                Assert.IsFalse(HolidayStages.All[i].Has(StageTraits.School), "only the last stage has the school (" + HolidayStages.All[i].levelId + ")");
        }

        [Test]
        public void DifficultyClimbsAlongTheLap()
        {
            var all = HolidayStages.All;
            Assert.Less(all[0].density, all[all.Length - 1].density, "the last stage is the busiest");
            for (int i = 0; i < all.Length; i++)
            {
                Assert.Greater(all[i].density, 0f, all[i].levelId + " density");
                Assert.LessOrEqual(all[i].density, 1f, all[i].levelId + " density");
                // A new chapter may start gentler than the last one ended, but nothing eases off within one.
                if (i > 0 && all[i].chapter == all[i - 1].chapter)
                    Assert.GreaterOrEqual(all[i].density, all[i - 1].density, all[i].levelId + " is easier than the stage before it");
            }
        }

        [Test]
        public void EveryStageHasSomethingToDo()
        {
            foreach (var stage in HolidayStages.All)
            {
                var obstacles = StageTraits.Steps | StageTraits.Crates | StageTraits.Cars | StageTraits.Awnings | StageTraits.Gaps
                    | StageTraits.Cranes;
                Assert.AreNotEqual(StageTraits.None, stage.traits & obstacles, stage.levelId + " has no obstacles to jump or slide");
            }
        }

        [Test]
        public void PowerUpsLastLongEnoughToMatter()
        {
            foreach (PowerUpKind kind in System.Enum.GetValues(typeof(PowerUpKind)))
            {
                Assert.GreaterOrEqual(HolidayRunDirector.Duration(kind), 4f, kind + " is over too soon");
                Assert.LessOrEqual(HolidayRunDirector.Duration(kind), 20f, kind + " lasts too long");
            }
        }
    }
}
#endif
