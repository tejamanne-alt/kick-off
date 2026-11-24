#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Holiday;
using DribbleToSchool.Levels;
using DribbleToSchool.Progression;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Florida's Holiday Run (v148, Holiday/HolidayStages.Florida): its nine legs as one lap, in route order and in each leg's look,
    /// with none of Kamakura's own furniture, a fair layout on every stage, and each stage's part of its leg's Miami district where
    /// the leg has it (the home at the start, the school gate at the leg's goal).
    /// </summary>
    public class FloridaHolidayRunTests
    {
        [SetUp]
        public void UseFloridasLap() { HolidayStages.Active = HolidayStages.Florida; }

        [TearDown]
        public void BackToKamakura() { HolidayStages.Active = HolidayStages.Kamakura; }

        [Test]
        public void EveryCityWithAHolidayRunHasItsOwnLap()
        {
            foreach (var city in Cities.All)
                Assert.AreEqual(city.holidayRun, HolidayStages.LapOf(city.id) != null, city.id);
            Assert.AreSame(HolidayStages.Florida, HolidayStages.LapOf(Cities.FloridaId));
            Assert.AreSame(HolidayStages.Kamakura, HolidayStages.LapOf(Cities.KamakuraId));
            Assert.IsTrue(HolidayStages.IsFlorida);
            Assert.AreEqual(HolidayStages.Kamakura.stages.Length, HolidayStages.MaxCount, "the HUD's tables fit the longest lap");
            HolidayStages.Active = null;
            Assert.AreSame(HolidayStages.Kamakura, HolidayStages.Active, "no lap is Kamakura's");
        }

        [Test]
        public void OneStageForEachFloridaLegInRouteOrderInItsLook()
        {
            var legs = RouteTable.Florida.SelectMany(r => r.levels).ToList();
            Assert.AreEqual(legs.Count, HolidayStages.Count);
            for (int i = 0; i < legs.Count; i++)
            {
                Assert.AreEqual(legs[i], HolidayStages.All[i].levelId, "stage " + i);
                Assert.AreEqual(GeneratedContent.LookOf(legs[i]), HolidayStages.All[i].chapter, legs[i] + "'s look");
            }
        }

        [Test]
        public void ItsScenesAreItsOwn()
        {
            var names = new HashSet<string>();
            for (int i = 0; i < HolidayStages.Count; i++) Assert.IsTrue(names.Add(HolidayStages.SceneName(i)));
            Assert.AreEqual("HolidayRun_FL_S01", names.First());
            Assert.IsFalse(names.Contains(HolidayStages.CoreSceneName));
            HolidayStages.Active = HolidayStages.Kamakura;
            for (int i = 0; i < HolidayStages.Count; i++) Assert.IsFalse(names.Contains(HolidayStages.SceneName(i)), "a Kamakura stage's name");
            Assert.AreNotEqual(HolidayStages.Florida.coreSceneName, HolidayStages.CoreSceneName);
            var paths = HolidayRunBuilder.ScenePaths();
            Assert.AreEqual(2 + HolidayStages.Kamakura.stages.Length + HolidayStages.Florida.stages.Length, paths.Count, "both laps are built");
            Assert.AreEqual(paths.Count, paths.Distinct().Count());
            Assert.AreSame(HolidayStages.Kamakura, HolidayStages.Active, "listing the scenes leaves Kamakura's lap active");
        }

        [Test]
        public void NoneOfKamakurasOwnFurnitureAndTheSchoolAtTheEnd()
        {
            var kamakuras = StageTraits.Tide | StageTraits.SoftSand | StageTraits.Seagulls | StageTraits.Tunnel | StageTraits.Cranes
                | StageTraits.Swings | StageTraits.Pond | StageTraits.Cars | StageTraits.Crossing;
            int last = HolidayStages.Count - 1;
            for (int i = 0; i <= last; i++)
            {
                var st = HolidayStages.All[i];
                Assert.AreEqual(StageTraits.None, st.traits & kamakuras, st.levelId);
                Assert.AreEqual(i == last, st.Has(StageTraits.School), st.levelId + ": only the last stage has the school");
                Assert.AreNotEqual(3, st.chapter, st.levelId + ": no Florida leg is in the beach's look");
                if (i > 0) Assert.Greater(st.density, HolidayStages.All[i - 1].density, st.levelId + " is harder than the stage before");
            }
        }

        [Test]
        public void EveryLayoutOfEveryStageFollowsTheRules()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                for (int v = 0; v < HolidayPatterns.Variants; v++)
                {
                    var problems = HolidayPatterns.Validate(plan, v);
                    Assert.IsEmpty(problems, string.Join("\n", problems.ToArray()));
                }
            }
        }

        [Test]
        public void ItsBarriersAreTheMiamiKits()
        {
            var miami = new HashSet<string>(HolidayPatterns.FloridaSlideLooks());
            int slides = 0;
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                foreach (var layout in plan.layouts)
                    foreach (var it in layout)
                    {
                        if (it.kind != PatternKind.Slide) continue;
                        slides++;
                        Assert.IsTrue(miami.Contains(it.look), it.look + " in " + HolidayStages.All[stage].levelId + " has no Miami model");
                        Assert.Greater(HolidayPatterns.SlideLengthAny(it.look), 0f, it.look);
                    }
            }
            Assert.Greater(slides, 0, "the lap has barriers to slide under");
        }

        [Test]
        public void EachStageShowsItsLegWhereTheLegHasIt()
        {
            int last = HolidayStages.Count - 1;
            // The kid starts at the home's gate, where the first leg has it (x 0 of its street).
            float shift0 = HolidayStages.StartOf(0) - HolidayRunBuilder.FloridaPlanStart(0);
            Assert.AreEqual(0f, HolidayStages.SpawnX - shift0, 1e-4f);
            // The school gate stands at the last leg's goal (Museum Park's).
            float shiftLast = HolidayStages.StartOf(last) - HolidayRunBuilder.FloridaPlanStart(last);
            Assert.AreEqual(106f, HolidayStages.GateX - shiftLast, 1e-4f);
            // Each stage's 120 m are within its leg's street (FloridaLevels: from x -8).
            for (int i = 0; i <= last; i++)
            {
                float a = HolidayRunBuilder.FloridaPlanStart(i);
                Assert.GreaterOrEqual(a, -8f, HolidayStages.All[i].levelId);
                Assert.LessOrEqual(a + HolidayStages.StageLength, 130f, HolidayStages.All[i].levelId);
            }
        }

        [Test]
        public void TheFarPartIsTheCoreScenesAndTheNearPartTheStages()
        {
            var stage = StreetBuilder.MiamiWindow.Stage(10f, 0f, 120f);
            var far = StreetBuilder.MiamiWindow.Distance(10f, 0f, 120f);
            var whole = StreetBuilder.MiamiWindow.Whole(float.NegativeInfinity, float.PositiveInfinity);
            Assert.IsTrue(stage.Takes(4f) && !stage.Takes(StreetBuilder.FarZ + 1f));
            Assert.IsTrue(!far.Takes(4f) && far.Takes(StreetBuilder.FarZ + 1f));
            Assert.IsTrue(whole.Takes(4f) && whole.Takes(2000f) && !whole.Cut && stage.Cut);
            float z0 = 50f, z1 = 2400f;
            Assert.IsTrue(stage.Band(ref z0, ref z1));
            Assert.AreEqual(StreetBuilder.FarZ, z1);
            z0 = 50f; z1 = 2400f;
            Assert.IsTrue(far.Band(ref z0, ref z1));
            Assert.AreEqual(StreetBuilder.FarZ, z0);
            z0 = 200f; z1 = 2400f;
            Assert.IsFalse(stage.Band(ref z0, ref z1), "nothing of the distance in a stage");
        }
    }
}
#endif
