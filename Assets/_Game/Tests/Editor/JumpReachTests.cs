#if UNITY_INCLUDE_TESTS
using DribbleToSchool.Core;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Hazards;
using DribbleToSchool.Holiday;
using DribbleToSchool.Tuning;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The Holiday Run's gaps and walls are held to what the kid can really do (Holiday/JumpReach.cs). These tests pin the
    /// reach model to the real numbers: PlayerTuning's defaults, the engine's gravity, the game's physics step, the trampoline's
    /// launch and the playtested figures, so a retuned jump fails here instead of silently making a trench impossible.
    /// </summary>
    public class JumpReachTests
    {
        [Test]
        public void TheDesignNumbersAreThePlayerTuningDefaults()
        {
            var tuning = ScriptableObject.CreateInstance<PlayerTuning>();
            try
            {
                var asset = JumpReach.From(tuning);
                var design = JumpReach.Defaults;
                Assert.AreEqual(design.runSpeed, asset.runSpeed, 1e-4f, "runSpeed");
                Assert.AreEqual(design.gravityScale, asset.gravityScale, 1e-4f, "gravityScale");
                Assert.AreEqual(design.fallGravityMultiplier, asset.fallGravityMultiplier, 1e-4f, "fallGravityMultiplier");
                Assert.AreEqual(design.jumpVelocity, asset.jumpVelocity, 1e-4f, "jumpVelocity");
                Assert.AreEqual(design.airJumpVelocity, asset.airJumpVelocity, 1e-4f, "airJumpVelocity");
                Assert.AreEqual(design.airJumps, asset.airJumps, "airJumps");
                Assert.AreEqual(design.coyoteTime, asset.coyoteTime, 1e-4f, "coyoteTime");
                Assert.AreEqual(design.slideDuration, asset.slideDuration, 1e-4f, "slideDuration");
                Assert.AreEqual(design.slideSpeedBoost, asset.slideSpeedBoost, 1e-4f, "slideSpeedBoost");
                Assert.AreEqual(design.slideFriction, asset.slideFriction, 1e-4f, "slideFriction");
                Assert.AreEqual(design.slideMinSpeed, asset.slideMinSpeed, 1e-4f, "slideMinSpeed");
                Assert.AreEqual(design.slideHeight, asset.slideHeight, 1e-4f, "slideHeight");
            }
            finally
            {
                Object.DestroyImmediate(tuning);
            }
        }

        [Test]
        public void ThePhysicsAndTheTrampolineAreWhatTheModelAssumes()
        {
            Assert.AreEqual(-JumpReach.Defaults.gravity, Physics2D.gravity.y, 1e-3f, "Physics2D gravity");
            Assert.AreEqual(JumpReach.Defaults.step, TimeControl.BaseFixedDeltaTime, 1e-6f, "the physics step");
            var go = new GameObject("reach-test", typeof(BoxCollider2D));
            try
            {
                var board = go.AddComponent<Springboard>();
                Assert.AreEqual(JumpReach.Defaults.springboardSpeed, board.kidLaunchSpeed, 1e-4f, "Springboard.kidLaunchSpeed");
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void FlightsMatchThePlaytestedNumbers()
        {
            var m = JumpReach.Defaults;
            var single = JumpReach.SingleJump(m);
            var dbl = JumpReach.DoubleJump(m);
            var longest = JumpReach.LongestJump(m);
            // Worked out by hand from KidController: a single jump flies 2.38 m (0.57 s) and clears 1.3 m; a double jump pressed at
            // the top 3.71 m and 2.07 m; the longest one, the second press as late as allowed, 4.13 m but low.
            Assert.AreEqual(2.38f, single.distance, 2.38f * 0.05f, "single jump distance");
            Assert.AreEqual(1.3f, single.apex, 0.06f, "single jump height");
            Assert.AreEqual(3.71f, dbl.distance, 3.71f * 0.05f, "double jump distance");
            Assert.AreEqual(2.07f, dbl.apex, 0.07f, "double jump height");
            Assert.AreEqual(4.13f, longest.distance, 4.13f * 0.05f, "longest flight");
            Assert.Less(longest.apex, 1.6f, "the longest flight is a low one");
            // At the turbo's speed the reach is 3.2 m and 5.0 m.
            Assert.AreEqual(3.21f, JumpReach.Of(m, m.runSpeed * 1.35f, JumpReach.JumpKind.Single).distance, 0.16f, "turbo single");
            Assert.AreEqual(5.01f, JumpReach.Of(m, m.runSpeed * 1.35f, JumpReach.JumpKind.Double).distance, 0.25f, "turbo double");
            Assert.AreEqual(0.42f, JumpReach.CoyoteRun(m), 0.01f, "coyote run-off");
        }

        [Test]
        public void TheSafeLimitsAreTheDesignLimits()
        {
            var m = JumpReach.Defaults;
            Assert.AreEqual(2.0f, JumpReach.SafePlainGap(m), 0.051f, "plain gap");
            Assert.AreEqual(3.2f, JumpReach.SafeWideGap(m), 0.051f, "wide gap");
            Assert.AreEqual(2.6f, JumpReach.MinWideGap(m), 0.051f, "narrowest wide gap");
            Assert.AreEqual(1.4f, JumpReach.ComfortablePlainMin(m), 0.051f);
            Assert.AreEqual(1.9f, JumpReach.ComfortablePlainMax(m), 0.051f);
            Assert.AreEqual(2.7f, JumpReach.ComfortableWideMin(m), 0.051f);
            Assert.AreEqual(3.1f, JumpReach.ComfortableWideMax(m), 0.051f);
            Assert.AreEqual(0.5f, JumpReach.SafeLowWall(m), 0.026f, "low wall");
            Assert.AreEqual(1.0f, JumpReach.SafeMidWall(m), 0.026f, "mid wall");
            Assert.AreEqual(1.7f, JumpReach.SafeTallWall(m), 0.026f, "tall wall");
            Assert.AreEqual(1.8f, JumpReach.MaxWall(m), 0.026f, "highest wall");
            Assert.AreEqual(6f, JumpReach.RunUp, "run-up");
            Assert.AreEqual(4f, JumpReach.Landing, "landing");
            // And the patterns use them.
            Assert.AreEqual(JumpReach.SafePlainGap(m), HolidayPatterns.PlainGapMax, 1e-4f);
            Assert.AreEqual(JumpReach.SafeWideGap(m), HolidayPatterns.WideGapMax, 1e-4f);
            Assert.AreEqual(JumpReach.MaxWall(m), HolidayPatterns.WallMax, 1e-4f);
        }

        [Test]
        public void AJumpTunedUpOrDownMovesTheLimits()
        {
            // The limits follow the numbers: a floatier kid may cross more, a heavier one less.
            var higher = JumpReach.Defaults;
            higher.jumpVelocity = 10f;
            var lower = JumpReach.Defaults;
            lower.jumpVelocity = 7.5f;
            Assert.Greater(JumpReach.SafePlainGap(higher), JumpReach.SafePlainGap(JumpReach.Defaults));
            Assert.Less(JumpReach.SafePlainGap(lower), JumpReach.SafePlainGap(JumpReach.Defaults) - 0.2f, "a weaker jump makes today's 2.0 m gaps too wide");
            Assert.Less(JumpReach.SafeMidWall(lower), JumpReach.SafeMidWall(JumpReach.Defaults));
            Assert.Greater(JumpReach.SafeWideGap(higher), JumpReach.SafeWideGap(JumpReach.Defaults));
        }

        [Test]
        public void SlideBarriersAreSomethingASlideGetsUnder()
        {
            var m = JumpReach.Defaults;
            // The kid's low body is 0.5 m; the clear height under every barrier is the track builder's constant.
            Assert.AreEqual(LevelBuildKit.TrackBuilder.SlideGap, HolidayPatterns.SlideClearance, 1e-4f, "barrier clearance");
            Assert.GreaterOrEqual(LevelBuildKit.TrackBuilder.SlideGap, JumpReach.MinSlideClearance(m), "the slide fits under the barriers");
            // A slide carries about 2.9 m; a longer barrier is finished in the low shuffle.
            Assert.AreEqual(2.9f, JumpReach.SlideDistance(m), 0.3f, "slide distance");
            for (int chapter = 1; chapter <= 5; chapter++)
                foreach (string look in HolidayPatterns.SlideLooks(chapter))
                    Assert.LessOrEqual(HolidayPatterns.SlideLength(chapter, look), JumpReach.MaxSlideBarrier(m), look + " is longer than a slide carries the kid");
        }

        [Test]
        public void TheTunnelAndTheCraneAreOutOfTheWayOfTheJumps()
        {
            var m = JumpReach.Defaults;
            // A double jump (the head of the kid at the top of it) fits under the underpass's deck with room to spare...
            Assert.Less(JumpReach.DoubleJumpHeadroom(m) + 0.3f, HolidayPatterns.TunnelHeight, "tunnel deck against a double jump");
            // ...and the crane's load hangs above even a trampoline's throw with the air jump.
            Assert.Less(JumpReach.SpringHeadroom(m) + 0.2f, HolidayPatterns.CraneHang, "crane load against a trampoline throw");
        }

        [Test]
        public void ACoinOnTheDoubleJumpArcIsReachable()
        {
            var m = JumpReach.Defaults;
            float[] xs, ys;
            JumpReach.Path(m, m.runSpeed, JumpReach.JumpKind.Double, 7, out xs, out ys);
            float top = 0f;
            foreach (float y in ys) top = System.Math.Max(top, y);
            // The detour's coins hang 0.9 m over the feet along it, its star 1.25 m over the top of it.
            Assert.LessOrEqual(top + 0.9f, JumpReach.HighestCoin(m), "detour coins");
            Assert.LessOrEqual(JumpReach.DoubleJump(m).apex + 1.25f, JumpReach.HighestCoin(m), "the star");
            // Only a double jump gets that high: a single jump's head stays under it.
            Assert.Greater(JumpReach.DoubleJump(m).apex + 1.25f - 0.45f, JumpReach.SingleJump(m).apex + m.bodyHeight, "the star is out of a single jump's reach");
        }
    }
}
#endif
