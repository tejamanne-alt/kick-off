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
    /// run depends on hold for every layout of every stage. The scenes themselves are built from these.
    /// </summary>
    public class HolidayPatternsTests
    {
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
        public void TheThreeLayoutsOfAStageHoldTheSameObstacles()
        {
            // Comparable difficulty: the same kinds of things in the same numbers, in different places.
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

        static string Census(List<PatternItem> items)
        {
            var counts = new SortedDictionary<string, int>();
            foreach (var i in items)
            {
                if (i.kind == PatternKind.Coin || i.kind == PatternKind.CoinRow || i.kind == PatternKind.CoinArc || i.kind == PatternKind.PowerUp) continue;
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
