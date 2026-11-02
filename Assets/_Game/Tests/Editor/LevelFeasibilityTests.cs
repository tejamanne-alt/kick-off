#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.EditorTools;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The build-time check that a level can be done (Editor/LevelFeasibility.cs): the holes, steps, walls, barriers and
    /// roofs of a level are held to what the kid can do. These run the check on small made-up levels.
    /// </summary>
    public class LevelFeasibilityTests
    {
        static LevelFeasibility Level(float holeFrom, float holeTo, float top = 0f)
        {
            var f = new LevelFeasibility();
            f.AddSpan(-8f, holeFrom, top);
            f.AddHole(holeFrom, holeTo, top, "Pit");
            f.AddSpan(holeTo, holeTo + 30f, top);
            return f;
        }

        [Test]
        public void AHoleOneJumpCrossesIsFine()
        {
            Assert.IsEmpty(Level(10f, 11.5f).Check());
            Assert.IsEmpty(Level(10f, 12f).Check());
        }

        [Test]
        public void AHoleADoubleJumpCrossesIsFineAndIsNoted()
        {
            var notes = new List<string>();
            Assert.IsEmpty(Level(10f, 12.9f).Check(notes));
            Assert.AreEqual(1, notes.Count, "a note that it wants a double jump");
            Assert.IsEmpty(Level(10f, 13.2f).Check());
        }

        [Test]
        public void AHoleWiderThanADoubleJumpNeedsABridge()
        {
            Assert.IsNotEmpty(Level(10f, 13.5f).Check(), "3.5 m, no bridge");
            Assert.IsNotEmpty(Level(10f, 18f).Check(), "8 m, no bridge");
        }

        [Test]
        public void ABridgeMustReachBothBanks()
        {
            // A platform that slides 6 m: 10 to 18 is bridged when it comes within a jump of both banks...
            var ok = Level(10f, 18f);
            ok.AddSliding(12f, -0.175f, 2.6f, 4f, 0f);   // covers 10.7 to 17.3 (it comes within 0.7 m of both banks)
            Assert.IsEmpty(ok.Check());
            // ...and not when it stops 3 m short of the far one.
            var shortOfIt = Level(10f, 18f);
            shortOfIt.AddSliding(12f, -0.175f, 2.6f, 1f, 0f);   // covers 10.7 to 14.3
            Assert.IsNotEmpty(shortOfIt.Check());
        }

        [Test]
        public void ABridgeFromAFarOffPlaceIsNoBridge()
        {
            var f = Level(10f, 18f);
            f.AddSliding(16f, -0.175f, 2.6f, 0f, 0f);   // sits in the middle of the far side: 5.7 m from the near bank
            Assert.IsNotEmpty(f.Check());
        }

        [Test]
        public void ALiftWhoseTopIsOutOfAJumpOfTheFarBankFails()
        {
            // The builder's lift going up to the loading dock: 6 m hole, the far ground 2 m up.
            var f = new LevelFeasibility();
            f.AddSpan(-8f, 64f, 0f);
            f.AddHole(64f, 70f, 0f, "Pit");
            f.AddSpan(70f, 82f, 2f);
            f.AddSliding(67f, -0.175f, 2.6f, 0f, 2.2f);   // covers 65.7 to 68.3, tops out at 2.2: within 1.7 m of both banks
            Assert.IsEmpty(f.Check(), string.Join("; ", f.Check().ToArray()));
            var off = new LevelFeasibility();
            off.AddSpan(-8f, 64f, 0f);
            off.AddHole(64f, 70f, 0f, "Pit");
            off.AddSpan(70f, 82f, 2f);
            off.AddSliding(66.5f, -0.175f, 2.6f, 0f, 2.2f);   // covers 65.2 to 67.8: 2.2 m short of the far bank
            Assert.IsNotEmpty(off.Check());
        }

        [Test]
        public void ASwingNeedsADoubleJumpButCountsAsABridge()
        {
            var f = new LevelFeasibility();
            f.AddSpan(-8f, 22f, 0f);
            f.AddHole(22f, 30f, 0f, "Water");
            f.AddSpan(30f, 52f, 0f);
            f.AddSwing(26f, 4.2f, 3.6f, 35f);   // the seat reaches 23.2 to 28.8
            Assert.IsEmpty(f.Check());
        }

        [Test]
        public void StepsWallsPlatformsBarriersAndRoofs()
        {
            var f = new LevelFeasibility();
            f.AddSpan(0f, 10f, 0f);
            f.AddSpan(10f, 20f, 0.6f);
            f.AddSpan(20f, 30f, 2.4f);   // a 1.8 m step, no ramp
            Assert.AreEqual(1, f.Check().Count, "the 1.8 m step");
            f.AddRamp(14f, 0.6f, 20f, 2.4f);
            Assert.IsEmpty(f.Check(), "with a ramp up it is fine");

            var w = new LevelFeasibility();
            w.AddWall(5f, 0.4f, 1.0f, "wall");
            w.AddWall(9f, 0.4f, 1.7f, "wall");
            Assert.IsEmpty(w.Check(), "walls up to 1.7 m");
            w.AddWall(13f, 0.4f, 1.9f, "wall");
            Assert.AreEqual(1, w.Check().Count, "a wall 1.9 m high");

            var p = new LevelFeasibility();
            p.AddLedge(40f, 46f, 2.4f, 0f);
            Assert.AreEqual(1, p.Check().Count, "a platform 2.4 m up and nothing to get there with");
            p.AddPad(38f, 0f);
            Assert.IsEmpty(p.Check(), "a trampoline two metres before it throws the kid onto it");
            var far = new LevelFeasibility();
            far.AddLedge(40f, 46f, 2.4f, 0f);
            far.AddPad(25f, 0f);
            Assert.AreEqual(1, far.Check().Count, "a trampoline fifteen metres away does not");

            var b = new LevelFeasibility();
            b.AddBarrier(10f, 2.6f, 0.85f, "PlankTrestles");
            b.AddBarrier(20f, 6f, 0.85f, "Hangar");
            b.AddBarrier(30f, 2f, 0.6f, "Low");
            Assert.AreEqual(2, b.Check().Count, "one too long, one too low");

            var r = new LevelFeasibility();
            r.AddRoof(10f, 30f, 3.8f);
            Assert.IsEmpty(r.Check());
            r.AddRoof(40f, 60f, 2.8f);
            Assert.AreEqual(1, r.Check().Count, "a roof under a double jump's head");
        }
    }
}
#endif
