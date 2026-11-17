#if UNITY_INCLUDE_TESTS
using System;
using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Holiday;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Edit-mode tests for the Holiday Run's obstacle layouts (Editor/HolidayPatterns.cs): the rules a fair
    /// run depends on hold for every layout of every stage, and every gap and wall is within what the kid can do
    /// (Holiday/JumpReach.cs). The scenes themselves are built from these.
    /// </summary>
    public class HolidayPatternsTests
    {
        static readonly JumpReach.Motion Reach = JumpReach.Defaults;

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
        public void EveryGapIsOneTheKidCanJump()
        {
            int gaps = 0;
            for (int stage = 0; stage < HolidayStages.Count; stage++)
                foreach (var f in HolidayPatterns.Plan(stage).furniture)
                {
                    if (f.kind != PatternKind.Gap) continue;
                    gaps++;
                    float w = f.x1 - f.x0;
                    string where = "stage " + (stage + 1) + " gap of " + w;
                    if (f.style == 1)
                    {
                        // Wide: a double jump, never wider than one safely crosses, clearly wider than a single jump needs.
                        Assert.LessOrEqual(w, JumpReach.SafeWideGap(Reach) + 1e-3f, where);
                        Assert.GreaterOrEqual(w, JumpReach.MinWideGap(Reach) - 1e-3f, where);
                        Assert.Greater(HolidayStages.All[stage].density, 0.5f, "wide gaps only where it is hard enough: " + where);
                    }
                    else
                    {
                        Assert.LessOrEqual(w, JumpReach.SafePlainGap(Reach) + 1e-3f, where);
                    }
                    // However the kid takes it, the longest jump there is (a double jump pressed late) covers it with room.
                    Assert.Less(w, JumpReach.LongestJump(Reach).distance, where);
                }
            Assert.Greater(gaps, 10, "the plans have gaps");
        }

        [Test]
        public void EveryWallIsOneTheKidCanClimbOrJump()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
                foreach (var layout in HolidayPatterns.Plan(stage).layouts)
                    foreach (var i in layout)
                    {
                        string where = "stage " + (stage + 1) + " " + i.kind + " " + i.h;
                        if (i.kind == PatternKind.Hop) Assert.LessOrEqual(i.h, JumpReach.SafeLowWall(Reach) + 1e-3f, where);
                        if (i.kind == PatternKind.Mid) Assert.LessOrEqual(i.h, JumpReach.SafeMidWall(Reach) + 1e-3f, where);
                        if (i.kind == PatternKind.Tall) Assert.LessOrEqual(i.h, JumpReach.SafeTallWall(Reach) + 1e-3f, where);
                        if (i.kind == PatternKind.Stack) Assert.LessOrEqual(i.h, JumpReach.SafeTallWall(Reach) + 1e-3f, where);
                        if (i.kind == PatternKind.Car) Assert.LessOrEqual(i.h, JumpReach.MaxWall(Reach) + 1e-3f, where);
                        if (i.kind == PatternKind.Hop || i.kind == PatternKind.Mid || i.kind == PatternKind.Tall || i.kind == PatternKind.Stack || i.kind == PatternKind.Car || i.kind == PatternKind.Crate)
                            Assert.LessOrEqual(i.h, JumpReach.MaxWall(Reach) + 1e-3f, "nothing over " + JumpReach.MaxWall(Reach) + ": " + where);
                    }
        }

        [Test]
        public void EveryGapHasARunUpAndALandingWithNothingInThem()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                foreach (var f in plan.furniture.Where(g => g.kind == PatternKind.Gap))
                    for (int v = 0; v < HolidayPatterns.Variants; v++)
                        foreach (var i in plan.layouts[v])
                        {
                            if (i.kind == PatternKind.Coin || i.kind == PatternKind.Star || i.kind == PatternKind.Balloon || i.kind == PatternKind.PowerUp) continue;
                            string where = "stage " + (stage + 1) + " layout " + v + ": " + i.kind + " at " + i.x0 + ".." + i.x1 + " by the gap " + f.x0 + ".." + f.x1;
                            Assert.IsFalse(i.x1 > f.x0 - JumpReach.RunUp && i.x0 < f.x0, "in the run-up: " + where);
                            Assert.IsFalse(i.x0 < f.x1 + JumpReach.Landing && i.x1 > f.x1, "in the landing: " + where);
                        }
            }
        }

        [Test]
        public void TheThreeLayoutsOfAStageHoldTheSameObstacles()
        {
            // Comparable difficulty: the same kinds of things in the same numbers (obstacles, things to smash, street life and
            // targets), in different places.
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                string first = Census(plan.layouts[0]);
                for (int v = 1; v < HolidayPatterns.Variants; v++)
                    Assert.AreEqual(first, Census(plan.layouts[v]), "stage " + (stage + 1) + " layout " + v);
            }
        }

        [Test]
        public void TheLayoutsOfAStageDiffer()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                for (int v = 1; v < HolidayPatterns.Variants; v++)
                    Assert.AreNotEqual(Places(plan.layouts[0]), Places(plan.layouts[v]), "stage " + (stage + 1) + " layouts 0 and " + v);
            }
        }

        [Test]
        public void PlansAreTheSameEveryTime()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
                Assert.AreEqual(Places(HolidayPatterns.Plan(stage).layouts[1]), Places(HolidayPatterns.Plan(stage).layouts[1]), "stage " + (stage + 1));
        }

        [Test]
        public void EverySlideLookIsABarrierOfTheKit()
        {
            for (int chapter = 1; chapter <= 5; chapter++)
                foreach (string look in HolidayPatterns.SlideLooks(chapter))
                    Assert.IsTrue(Enum.IsDefined(typeof(LevelBuildKit.TrackBuilder.SlideLook), look), look);
        }

        [Test]
        public void EveryStageIsFullOfThingsToDo()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                for (int v = 0; v < HolidayPatterns.Variants; v++)
                {
                    var items = plan.layouts[v];
                    string where = "stage " + (stage + 1) + " layout " + v;
                    int demands = items.Count(i => i.kind == PatternKind.Hop || i.kind == PatternKind.Mid || i.kind == PatternKind.Tall || i.kind == PatternKind.Crate || i.kind == PatternKind.Stack ||
                        i.kind == PatternKind.Car || i.kind == PatternKind.Slide || i.kind == PatternKind.Puddle || i.kind == PatternKind.SandPatch || i.kind == PatternKind.Spring)
                        + plan.furniture.Count(f => f.kind == PatternKind.Gap);
                    Assert.GreaterOrEqual(demands, 4, "obstacles in " + where);
                    Assert.LessOrEqual(demands, 10, "obstacles in " + where);
                    Assert.GreaterOrEqual(items.Count(i => i.kind == PatternKind.Crate || i.kind == PatternKind.Stack), 1, "something to smash in " + where);
                    int balloons = items.Count(i => i.kind == PatternKind.Balloon);
                    Assert.IsTrue(balloons >= 2 && balloons <= 4, balloons + " balloons in " + where);
                    Assert.GreaterOrEqual(items.Count(i => i.kind == PatternKind.Walkers || i.kind == PatternKind.DogPatch), 1, "street life in " + where);
                    Assert.GreaterOrEqual(items.Count(i => i.kind == PatternKind.Coin), 40, "coins in " + where);
                }
            }
        }

        [Test]
        public void StreetLifeGrowsWithTheDensity()
        {
            Assert.LessOrEqual(HolidayPatterns.LifeCount(HolidayStages.All[0].density), 2, "the first stage");
            Assert.GreaterOrEqual(HolidayPatterns.LifeCount(HolidayStages.All[HolidayStages.Count - 1].density), 3, "the last stage");
            int previous = 0;
            for (float d = 0.28f; d <= 1f; d += 0.02f)
            {
                int n = HolidayPatterns.LifeCount(d);
                Assert.GreaterOrEqual(n, previous, "more people never come with less density");
                Assert.IsTrue(n >= 1 && n <= 4);
                previous = n;
            }
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                var st = HolidayStages.All[stage];
                for (int v = 0; v < HolidayPatterns.Variants; v++)
                {
                    int beats = plan.layouts[v].Count(i => i.kind == PatternKind.Walkers || i.kind == PatternKind.DogPatch);
                    Assert.AreEqual(plan.life, beats, "stage " + (stage + 1) + " layout " + v);
                    if (st.Has(StageTraits.Pedestrians) && plan.life > 0) Assert.GreaterOrEqual(plan.layouts[v].Count(i => i.kind == PatternKind.Walkers), 1, "people in stage " + (stage + 1));
                    if (st.Has(StageTraits.Dogs) && plan.life > 0) Assert.GreaterOrEqual(plan.layouts[v].Count(i => i.kind == PatternKind.DogPatch), 1, "dogs in stage " + (stage + 1));
                }
            }
        }

        [Test]
        public void ThereIsAPowerUpInEveryTwoStagesWhicheverLayoutsLoad()
        {
            var plans = Enumerable.Range(0, HolidayStages.Count).Select(HolidayPatterns.Plan).ToArray();
            for (int s = 0; s + 1 < HolidayStages.Count; s++)
                for (int a = 0; a < HolidayPatterns.Variants; a++)
                    for (int b = 0; b < HolidayPatterns.Variants; b++)
                        Assert.IsTrue(plans[s].layouts[a].Any(i => i.kind == PatternKind.PowerUp) || plans[s + 1].layouts[b].Any(i => i.kind == PatternKind.PowerUp),
                            "no power-up in stages " + (s + 1) + " (layout " + a + ") and " + (s + 2) + " (layout " + b + ")");
        }

        [Test]
        public void StreetLifeAndPowerUpsStayOffGapsAndSolids()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                for (int v = 0; v < HolidayPatterns.Variants; v++)
                {
                    var items = plan.layouts[v];
                    foreach (var mover in items.Where(i => i.kind == PatternKind.Walkers || i.kind == PatternKind.DogPatch || i.kind == PatternKind.PowerUp))
                    {
                        string where = "stage " + (stage + 1) + " layout " + v + ": " + mover.kind + " at " + mover.x0 + ".." + mover.x1;
                        foreach (var g in plan.furniture.Where(f => f.kind == PatternKind.Gap))
                            Assert.IsFalse(mover.x1 > g.x0 - 1f && mover.x0 < g.x1 + 1f, "over a gap: " + where);
                        foreach (var o in items.Where(i => i != mover && i.x1 > i.x0 && i.kind != PatternKind.Coin && i.kind != PatternKind.Star && i.kind != PatternKind.Balloon
                            && i.kind != PatternKind.Walkers && i.kind != PatternKind.DogPatch && i.kind != PatternKind.PowerUp))
                            Assert.IsFalse(mover.x1 > o.x0 - 1f && mover.x0 < o.x1 + 1f, "on a " + o.kind + ": " + where);
                    }
                }
            }
        }

        [Test]
        public void CoinsHangWhereTheyCanBeGot()
        {
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                for (int v = 0; v < HolidayPatterns.Variants; v++)
                    foreach (var c in plan.layouts[v].Where(i => i.kind == PatternKind.Coin || i.kind == PatternKind.Star))
                    {
                        string where = "stage " + (stage + 1) + " layout " + v + ": " + c.kind + " at " + c.x + ", " + c.y;
                        Assert.GreaterOrEqual(c.y, 0.3f, where);
                        // Where only a trampoline's throw gets (style 1) it may be higher than a double jump reaches; elsewhere not.
                        Assert.LessOrEqual(c.y, JumpReach.HighestCoin(Reach) + (c.style == 1 ? 1.5f : 0f), where);
                        foreach (var g in plan.furniture.Where(f => f.kind == PatternKind.Gap))
                            if (c.x > g.x0 + 0.35f && c.x < g.x1 - 0.35f) Assert.GreaterOrEqual(c.y, 0.95f, "low over a gap: " + where);
                    }
            }
        }

        [Test]
        public void MostStagesHaveACheckpointInTheMiddleWithClearGroundAroundIt()
        {
            int with = 0;
            for (int stage = 0; stage < HolidayStages.Count; stage++)
            {
                var plan = HolidayPatterns.Plan(stage);
                var checkpoint = plan.furniture.FirstOrDefault(f => f.kind == PatternKind.Checkpoint);
                if (checkpoint == null) continue;
                with++;
                Assert.Greater(checkpoint.x, plan.from + 8f + 20f, "stage " + (stage + 1) + ": far from the first checkpoint");
                Assert.Less(checkpoint.x, plan.to - 8f - 10f, "stage " + (stage + 1) + ": well before the end");
                for (int v = 0; v < HolidayPatterns.Variants; v++)
                    foreach (var i in plan.layouts[v])
                    {
                        if (i.kind == PatternKind.Coin || i.kind == PatternKind.Star || i.kind == PatternKind.Balloon) continue;
                        Assert.IsFalse(i.x1 > checkpoint.x - HolidayPatterns.CheckpointBefore && i.x0 < checkpoint.x + HolidayPatterns.CheckpointAfter,
                            "stage " + (stage + 1) + " layout " + v + ": " + i.kind + " by the checkpoint");
                    }
            }
            Assert.GreaterOrEqual(with, HolidayStages.Count - 3, "the stages with a middle checkpoint");
        }

        [Test]
        public void TheBigNumbersMatchTheKitsAndTheHazards()
        {
            // The stack is the crate pyramid of the story levels (two crates and one on top: 1.42 high and wide).
            Assert.AreEqual(1.42f, HolidayPatterns.StackHeight, 0.01f);
            Assert.AreEqual(1.42f, HolidayPatterns.StackWidth, 0.01f);
            Assert.LessOrEqual(HolidayPatterns.StackHeight, JumpReach.SafeTallWall(Reach));
            // A parked car is 3.3 m long and 1.55 high (LevelBuildKit.TrackBuilder.ParkedCar).
            Assert.LessOrEqual(HolidayPatterns.CarHeight, JumpReach.MaxWall(Reach));
        }

        static string Census(List<PatternItem> items)
        {
            var counts = new SortedDictionary<string, int>();
            foreach (var i in items)
            {
                if (i.kind == PatternKind.Coin || i.kind == PatternKind.CoinRow || i.kind == PatternKind.CoinArc || i.kind == PatternKind.Star || i.kind == PatternKind.PowerUp) continue;
                int n;
                counts.TryGetValue(i.kind.ToString(), out n);
                counts[i.kind.ToString()] = n + 1;
            }
            return string.Join(" ", counts.Select(kv => kv.Key + kv.Value).ToArray());
        }

        static string Places(List<PatternItem> items)
        {
            return string.Join(" ", items.Select(i => i.kind + "@" + i.x.ToString("0.00") + i.look).ToArray());
        }
    }
}
#endif
