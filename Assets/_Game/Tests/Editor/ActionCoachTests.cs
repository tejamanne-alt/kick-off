using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Holiday;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The coach at the top of a level (UI/ActionCoach): every how-to and step it can show is written in every language and
    /// fits its card, every action the level builder can place has one, the builder's plan (Editor/CoachPlan) gives the
    /// right how-to for each obstacle, and keepy-uppy's steps follow the ball.
    /// </summary>
    public class ActionCoachTests
    {
        static IEnumerable<CoachCatalog.Entry> Everything() { return CoachCatalog.Actions.Concat(CoachCatalog.Steps); }

        [Test]
        public void EveryHowToAndStepIsWrittenInEveryLanguage()
        {
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (var e in Everything())
                    foreach (string key in new[] { e.TitleKey, e.TextKey })
                        Assert.IsTrue(table.ContainsKey(key) && table[key].Length > 0, code + ": " + key);
                Assert.IsTrue(table.ContainsKey("settings.coachTips"), code + ": settings.coachTips");
                foreach (var status in new[] { "challenge.status.juggle", "challenge.status.targets", "challenge.status.slalom" })
                    Assert.IsTrue(table.ContainsKey(status) && table[status].Contains("{0}") && table[status].Contains("{2}"), code + ": " + status);
                Assert.IsTrue(table["challenge.status.slalom"].Contains("{3}"), code + ": the slalom's line shows its time");
            }
        }

        [Test]
        public void TheTextsFitTheCard()
        {
            // The card's text runs two or three lines beside the picture on the narrowest card (620 wide) and shrinks a little to
            // fit; the title is one line, and once a move is learned it is all the card shows, so it names the control.
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (var e in Everything())
                {
                    Assert.LessOrEqual(table[e.TitleKey].Length, 36, code + ": " + e.TitleKey);
                    Assert.LessOrEqual(table[e.TextKey].Length, 140, code + ": " + e.TextKey);
                }
            }
        }

        [Test]
        public void EveryActionTheBuilderPlacesHasAHowTo()
        {
            var ids = CoachCatalog.Actions.Select(a => a.id).ToList();
            foreach (string action in CoachPlan.Actions) Assert.Contains(action, ids, action + " has a how-to");
            foreach (string id in ids) Assert.Contains(id, CoachPlan.Actions, id + " can be placed");
            Assert.AreEqual(ids.Count, ids.Distinct().Count(), "no action is listed twice");
            var steps = CoachCatalog.Steps.Select(s => s.id).ToList();
            Assert.IsEmpty(steps.Intersect(ids).ToList(), "a step's id is not an action's");
        }

        [Test]
        public void ThePlanGivesEachObstacleItsHowTo()
        {
            var audit = new LevelFeasibility();
            audit.AddWall(10f, 0.6f, 0.3f, "wall");          // a kerb
            audit.AddWall(20f, 0.4f, 0.9f, "wall");          // a wall to chip over
            audit.AddPad(30f, 0f);
            audit.AddWall(32f, 0.4f, 1.6f, "wall");          // tall, with a trampoline just before: the trampoline's how-to
            audit.AddWall(45f, 0.4f, 1.6f, "wall");          // tall, nothing before: lob it, double jump
            audit.AddHole(50f, 51.5f, 0f, "Pit");            // one jump
            audit.AddHole(60f, 62.6f, 0f, "Water");          // a double jump
            audit.AddHole(70f, 80f, 0f, "Water");            // too wide: its bridge says how
            audit.AddBarrier(90f, 2f, 0.7f, "PlankTrestles");
            audit.AddWall(100f, 3.3f, 1.55f, "parked car");
            audit.AddWall(104f, 3.3f, 1.55f, "parked car");  // two in a row: one spot
            var plan = new CoachPlan();
            plan.Mark("fountain", 109f, 111f);
            audit.AddPad(112f, 0f);                          // after the fountain: only the kid's bounce
            plan.Mark("crossing", 125f, 120f);               // either order

            var spots = plan.Build(audit, JumpReach.Defaults);
            var actions = spots.Select(s => s.action).ToList();
            Assert.AreEqual("kerb chip springboard chiphigh gap gapdouble slide car fountain bounce crossing", string.Join(" ", actions.ToArray()),
                string.Join(", ", spots.Select(s => s.ToString()).ToArray()));
            var cars = spots.First(s => s.action == "car");
            Assert.AreEqual(98.35f, cars.from, 0.01f);
            Assert.AreEqual(105.65f, cars.to, 0.01f);
            var crossing = spots.First(s => s.action == "crossing");
            Assert.IsTrue(crossing.from < crossing.to);
            for (int i = 1; i < spots.Count; i++) Assert.LessOrEqual(spots[i - 1].from, spots[i].from, "sorted along the level");
        }

        [Test]
        public void ThePlanKnowsTheStepTheCratesAndTheGapsLimits()
        {
            var audit = new LevelFeasibility();
            audit.AddWall(10f, 2f, 0.8f, "step");
            audit.AddWall(11.25f, 0.5f, 1.0f, "high wall (1.8 m, seen from the 0.8 m step)");
            audit.AddWall(20f, 1.42f, 1.42f, "crate stack");
            audit.AddWall(30f, 1f, 1f, "something else");
            float plain = JumpReach.SafePlainGap(JumpReach.Defaults), wide = JumpReach.SafeWideGap(JumpReach.Defaults);
            audit.AddHole(40f, 40f + plain, 0f, "Pit");
            audit.AddHole(50f, 50f + wide, 0f, "Pit");
            var spots = new CoachPlan().Build(audit, JumpReach.Defaults);
            Assert.AreEqual("highwall crates gap gapdouble", string.Join(" ", spots.Select(s => s.action).ToArray()),
                string.Join(", ", spots.Select(s => s.ToString()).ToArray()));
        }

        [Test]
        public void TheGroundsStepsUpAreHowTosExceptOnTheBeachsSlopes()
        {
            var audit = new LevelFeasibility();
            audit.AddSpan(0f, 10f, 0f);
            audit.AddSpan(10f, 20f, 0.6f);    // a step: chip it up, jump
            audit.AddSpan(20f, 30f, 0.9f);    // a kerb's height
            audit.AddSpan(30f, 40f, 0f);      // down: nothing to do
            audit.AddSpan(40f, 50f, 1.2f);
            audit.AddRamp(37f, 0f, 40f, 1.2f); // a ramp leads up this one
            Assert.AreEqual("stepup kerb", string.Join(" ", new CoachPlan().Build(audit, JumpReach.Defaults).Select(s => s.action).ToArray()));
            Assert.AreEqual(0, new CoachPlan().Build(audit, JumpReach.Defaults, true).Count, "the beach's sand slopes up its steps");
        }

        [Test]
        public void KeepyUppysStepsFollowTheBall()
        {
            Assert.AreEqual("juggle1", CoachCatalog.JuggleStep(true, new Vector2(0.2f, 0f), true), "at the feet: pop it up from KICK");
            Assert.AreEqual("jugglefetch", CoachCatalog.JuggleStep(true, new Vector2(3f, 0f), false), "away on the ground: fetch it");
            Assert.AreEqual("juggle2", CoachCatalog.JuggleStep(false, new Vector2(0.3f, 0.9f), false), "in the air near the kid: tap");
            Assert.AreEqual("jugglemove", CoachCatalog.JuggleStep(false, new Vector2(-2f, 0.9f), false), "in the air off to the side: get under it");
            Assert.AreEqual("aim", CoachCatalog.TargetStep(true));
            Assert.AreEqual("targetfetch", CoachCatalog.TargetStep(false));
            Assert.AreEqual("low", CoachCatalog.SlalomStep(true, false));
            Assert.AreEqual("hoop", CoachCatalog.SlalomStep(true, true));
            Assert.AreEqual("finish", CoachCatalog.SlalomStep(false, false));
        }

        [Test]
        public void TheLearnedMovesAreForgottenWithTheProgress()
        {
            // Every how-to is in the catalog Reset progress walks through (ActionCoach.ResetLearned).
            foreach (string action in CoachPlan.Actions)
            {
                CoachCatalog.Entry entry;
                Assert.IsTrue(CoachCatalog.TryFind(action, out entry), action);
            }
        }
    }
}
