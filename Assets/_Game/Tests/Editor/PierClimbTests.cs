#if UNITY_INCLUDE_TESTS
using System;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Player;
using DribbleToSchool.World;
using NUnit.Framework;
using UnityEngine;
using Climb = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The pier the course climbs (Low Tide in California: TrackBuilder.PierClimb): its flights are as gentle as the beach's
    /// dunes, the climb can be done and could not be without its steps, and the kid keeps to a slope (KidController) rather
    /// than sliding back down it. Pure rules (no scene).
    /// </summary>
    public class PierClimbTests
    {
        static PierStairs.Plan Flight()
        {
            return PierStairs.PlanFor(Climb.ClimbRise, Climb.ClimbGoing, Climb.ClimbRiser, Climb.ClimbSplitOver);
        }

        [Test]
        public void TheCourseFlightsAreAsGentleAsTheBeachsDunes()
        {
            var p = Flight();
            Assert.AreEqual(0, p.afterMid, "one even slope each way: no mid-landing");
            Assert.AreEqual(Climb.ClimbRise, p.riser * p.risers, 0.0001f, "the steps add up to the climb");
            double slope = Math.Atan(p.riser / Climb.ClimbGoing) * 180.0 / Math.PI;
            Assert.LessOrEqual((float)slope, 22f, "no steeper than the dunes' steepest (SandField)");
            Assert.GreaterOrEqual((float)slope, 18f, "and still a flight of stairs");
            Assert.AreEqual(p.risers * Climb.ClimbGoing, Climb.ClimbRun, 0.0001f, "the walking line meets the sand a tread past the last step");
            Assert.AreEqual(2f * Climb.ClimbRun + Climb.ClimbLanding, Climb.PierClimbLength, 0.0001f);
        }

        [Test]
        public void TheClimbCanBeDoneAndNotWithoutItsSteps()
        {
            float foot = 48.6f, top = foot + Climb.ClimbRun, topEnd = top + Climb.ClimbLanding, end = topEnd + Climb.ClimbRun;
            var level = new LevelFeasibility();
            level.AddSpan(-8f, 110f, 0f);
            level.AddRamp(foot, 0f, top, Climb.ClimbRise);
            level.AddLedge(top, topEnd, Climb.ClimbRise, 0f);
            level.AddRamp(topEnd, Climb.ClimbRise, end, 0f);
            Assert.IsEmpty(level.Check(), "up the steps, over and down");

            var noSteps = new LevelFeasibility();
            noSteps.AddSpan(-8f, 110f, 0f);
            noSteps.AddLedge(top, topEnd, Climb.ClimbRise, 0f);
            Assert.IsNotEmpty(noSteps.Check(), "the deck alone is out of a double jump's reach");
        }

        [Test]
        public void TheKidKeepsToASlope()
        {
            var up21 = new Vector2(-0.358f, 0.934f);    // a 21 degree slope rising to the right (the pier's steps)
            Assert.IsTrue(KidController.IsWalkableSlope(up21));
            Assert.AreEqual(4.2f * 0.383f, KidController.AlongSlope(4.2f, up21), 0.01f, "running right: up it at the stick's pace");
            Assert.AreEqual(-4.2f * 0.383f, KidController.AlongSlope(-4.2f, up21), 0.01f, "running left: down it");
            Assert.AreEqual(0f, KidController.AlongSlope(0f, up21), 0.0001f, "standing: still, not sliding");
            Assert.AreEqual(KidController.SlopeRise(4.2f, up21), KidController.SlopeRise(-4.2f, up21), 0.0001f);

            Assert.IsFalse(KidController.IsWalkableSlope(Vector2.up), "the flat is not a slope");
            Assert.AreEqual(0f, KidController.SlopeRise(4.2f, Vector2.up), 0.0001f);
            Assert.IsFalse(KidController.IsWalkableSlope(new Vector2(-0.8f, 0.6f)), "53 degrees: a wall, not a slope");
            Assert.AreEqual(0f, KidController.SlopeRise(4.2f, new Vector2(-0.8f, 0.6f)), 0.0001f);
        }
    }
}
#endif
