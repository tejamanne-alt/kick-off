using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Grey-box layouts. Units are metres; the kid runs ~4.2 m/s, jumps ~1.4 m
    /// high and ~2.4 m far, so gaps stay at or under 2 m and walls the kid
    /// must climb stay under 1 m (higher walls come with a step).
    /// </summary>
    public static class GreyboxLevels
    {
        /// <summary>Phase 1 playground: every mechanic once, back to back.</summary>
        public static void TestTrack(TrackBuilder t)
        {
            t.Walls(-10f, 115f);
            t.Start(0f);
            t.Ground(-10f, 34f);
            t.Sign("Test Track\nEvery mechanic, back to back", new Vector2(3f, 3.4f));

            t.Wall(18f, 0.3f, 0f, 0.6f);
            t.Sign("Kerb - jump!", new Vector2(18f, 2.2f));
            t.Wall(27f, 0.9f);
            t.Sign("Chip it over:\ndrag back from the ball", new Vector2(25.5f, 3f));

            t.Checkpoint(29.5f);
            t.Pit(34f, 36f);
            t.Sign("Mind the gap", new Vector2(35f, 2.6f));
            t.Ground(36f, 80f);

            t.CrateStack(44f);
            t.Sign("Kick the crates\n(or chip over)", new Vector2(42f, 3.2f));

            t.Checkpoint(48.5f);
            t.Ramp(new Vector2(52f, 0f), new Vector2(58f, 1.5f));
            t.Platform(58f, 70f, 1.5f);

            t.Awning(75f, 2.6f);
            t.Sign("Bounce it off the awning", new Vector2(75f, 4.2f));

            t.StepAndHighWall(80.6f);
            t.Sign("Step up, brake, chip over", new Vector2(80.5f, 3.6f));
            t.Ground(80f, 115f);

            t.Checkpoint(86f);
            t.Sign("Kick it up and juggle:\ntap while it's in the air", new Vector2(92f, 3.2f));
            t.Goal(105.5f);
        }

        /// <summary>L01: tutorial. One idea at a time, generous bell.</summary>
        public static void OutTheDoor(TrackBuilder t)
        {
            t.Walls(-8f, 78f);
            t.Start(0f);
            t.Ground(-8f, 52f);
            t.Sign("The kid runs by himself.\nKeep the ball close!", new Vector2(4f, 3.2f));
            t.Sign("Tap the RIGHT side just as\nyou catch up with the ball:\nPerfect touch!", new Vector2(13f, 3.4f));
            t.Sign("Hold the LEFT side to brake", new Vector2(21f, 3f));

            t.Wall(27f, 0.3f, 0f, 0.6f);
            t.Sign("Kerb! Jump\n(button or swipe up)", new Vector2(27f, 2.6f));

            t.Checkpoint(31f);
            t.Wall(37f, 0.8f);
            t.Sign("Touch the ball, drag back,\nlet go: chip it over!", new Vector2(35f, 3.2f));

            t.Checkpoint(45f);
            t.Pit(52f, 53.5f);
            t.Sign("Chip it across,\nthen jump after it", new Vector2(50f, 3f));
            t.Ground(53.5f, 78f);

            t.Goal(70f);
        }

        /// <summary>L02: crates, a puddle, a raised walkway.</summary>
        public static void CornerShop(TrackBuilder t)
        {
            t.Walls(-8f, 108f);
            t.Start(0f);
            t.Ground(-8f, 22f);
            t.CrateStack(12f);
            t.Sign("Delivery crates!\nKick them out of the way", new Vector2(10f, 3.4f));

            t.Water(22f, 24f);
            t.Sign("Puddle - chip it over", new Vector2(21f, 2.6f));
            t.Ground(24f, 64f);

            t.Checkpoint(28f);
            t.Ramp(new Vector2(34f, 0f), new Vector2(40f, 1.5f));
            t.Platform(40f, 50f, 1.5f);
            t.Crate(45f, 1.85f);
            t.Sign("Shop steps", new Vector2(40f, 3.6f));

            t.Checkpoint(54f);
            t.Wall(58f, 0.9f);
            t.Water(64f, 66f);
            t.Ground(66f, 108f);

            t.CrateStack(74f);
            t.Checkpoint(80f);
            t.Awning(88f, 2.6f);
            t.Sign("Bounce it off the shop awning", new Vector2(88f, 4.2f));
            t.Wall(92f, 0.3f, 0f, 0.6f);

            t.Goal(100f);
        }

        /// <summary>L03: up and over the hill, then a juggling stretch to the gate.</summary>
        public static void UpTheHill(TrackBuilder t)
        {
            t.Walls(-8f, 128f);
            t.Start(0f);
            t.Ground(-8f, 20f);
            t.Sign("Up the hill!", new Vector2(10f, 3f));

            // Stairs up to a plateau with a gap in it.
            t.Ground(20f, 23f, 0.6f);
            t.Ground(23f, 26f, 1.2f);
            t.Ground(26f, 32f, 1.8f);
            t.Pit(32f, 34f, 1.8f);
            t.Sign("Big gap!", new Vector2(33f, 4.4f));
            t.Ground(34f, 44f, 1.8f);
            t.Checkpoint(36f, 1.8f);

            // Down the other side.
            t.Ramp(new Vector2(44f, 1.8f), new Vector2(50f, 0f));
            t.Ground(44f, 66f);
            t.Checkpoint(52f);
            t.StepAndHighWall(58f);
            t.Sign("Step up, brake, chip over", new Vector2(58f, 3.6f));

            t.Water(66f, 68f);
            t.Ground(68f, 128f);
            t.Checkpoint(71f);
            t.CrateStack(78f);

            t.Sign("Nearly there! Kick it up\nand juggle to the gate", new Vector2(90f, 3.2f));
            t.Wall(100f, 0.3f, 0f, 0.6f);
            t.Checkpoint(103f);
            t.Wall(108f, 0.9f);

            t.Goal(120f);
        }
    }
}
