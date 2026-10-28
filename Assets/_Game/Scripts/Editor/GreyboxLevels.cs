using DribbleToSchool.Challenges;
using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Grey-box layouts. Units are metres; the kid runs ~4.2 m/s, jumps ~1.4 m
    /// high and ~2.4 m far, so gaps stay at or under 2 m and walls the kid
    /// must climb stay under 1 m (higher ones come with a step or springboard).
    /// Each chapter introduces one idea, then mixes it with what came before.
    /// </summary>
    public static class GreyboxLevels
    {
        static readonly Color CarRed = new Color(0.85f, 0.3f, 0.3f);
        static readonly Color CarBlue = new Color(0.3f, 0.5f, 0.85f);
        static readonly Color CarGreen = new Color(0.35f, 0.7f, 0.45f);
        static readonly Color CarYellow = new Color(0.95f, 0.8f, 0.3f);
        static readonly Color CarPurple = new Color(0.6f, 0.45f, 0.8f);
        static readonly Color CoatA = new Color(0.55f, 0.35f, 0.6f);
        static readonly Color CoatB = new Color(0.3f, 0.55f, 0.55f);
        static readonly Color CoatC = new Color(0.75f, 0.5f, 0.3f);
        static readonly Color CoatD = new Color(0.4f, 0.4f, 0.7f);
        static readonly Color DogBrown = new Color(0.6f, 0.42f, 0.28f);
        static readonly Color DogWhite = new Color(0.92f, 0.9f, 0.85f);
        static readonly Color DogBlack = new Color(0.25f, 0.22f, 0.22f);

        // ===================== Test track =====================

        /// <summary>Phase 1 playground: every core mechanic once, back to back.</summary>
        public static void TestTrack(TrackBuilder t)
        {
            t.Walls(-10f, 115f);
            t.Start(0f);
            t.Ground(-10f, 34f);
            t.Sign("Test Track\nEvery mechanic, back to back", new Vector2(3f, 3.4f));

            t.Wall(18f, 0.3f, 0f, 0.6f);
            t.Sign("Kerb - jump!", new Vector2(18f, 2.2f));
            t.Wall(27f, 0.9f);
            t.Sign("Chip it over:\ndrag up from KICK", new Vector2(25.5f, 3f));

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
            t.Sign("Step up, stop, chip over", new Vector2(80.5f, 3.6f));
            t.Ground(80f, 115f);

            t.Checkpoint(86f);
            t.Sign("Kick it up and juggle:\ntap while it's in the air", new Vector2(92f, 3.2f));
            t.Goal(105.5f);
        }

        // ===================== Chapter 1: Home Street =====================

        /// <summary>L01: tutorial. One idea at a time, generous bell.</summary>
        public static void OutTheDoor(TrackBuilder t)
        {
            t.Walls(-8f, 78f);
            t.Start(0f);
            t.Hint(1.5f, "dribble");
            t.Hint(18f, "brake");
            t.Hint(24f, "jump");
            t.Hint(33f, "kick");
            t.Ground(-8f, 52f);
            t.Sign("Hold the arrows to walk.\nKeep the ball close!", new Vector2(4f, 3.2f));
            t.Sign("Tap the screen just as\nyou catch up with the ball:\nPerfect touch!", new Vector2(13f, 3.4f));
            t.Sign("Let go of the arrows to stop -\nthe ball stops at your feet", new Vector2(21f, 3f));

            t.Wall(27f, 0.3f, 0f, 0.6f);
            t.Sign("Kerb! Jump\n(button or swipe up)", new Vector2(27f, 2.6f));

            t.Checkpoint(31f);
            t.Wall(37f, 0.8f);
            t.Sign("Drag from KICK the way the\nball should go: chip it over!", new Vector2(35f, 3.2f));

            t.Checkpoint(45f);
            t.Pit(52f, 53.5f);
            t.Sign("Chip it across,\nthen jump after it", new Vector2(50f, 3f));
            t.Ground(53.5f, 78f);

            t.CoinRow(6f, 12f, 0.5f, 4);
            t.CoinArc(25.8f, 28.2f, 0.6f, 1.2f, 3);
            t.CoinArc(35.5f, 38.5f, 1.2f, 1.2f, 3);
            t.CoinArc(51.5f, 54f, 0.7f, 1.3f, 3);
            t.CoinRow(58f, 64f, 0.5f, 3);
            t.Sticker(new Vector2(41f, 3.2f));
            t.Goal(70f);
        }

        /// <summary>L02: parked cars to hop onto and chip over.</summary>
        public static void ParkedCars(TrackBuilder t)
        {
            t.Walls(-8f, 92f);
            t.Start(0f);
            t.Ground(-8f, 58f);
            t.Sign("Parked cars ahead!\nHop onto the bonnet,\nchip the ball over the roof", new Vector2(6f, 3.4f));

            t.ParkedCar(16f, CarRed);
            t.Checkpoint(22f);
            t.Wall(28f, 0.3f, 0f, 0.6f);

            t.ParkedCar(36f, CarBlue);
            t.ParkedCar(40f, CarGreen);
            t.Sign("Two in a row!", new Vector2(38f, 3.4f));

            t.Checkpoint(46f);
            t.Wall(52f, 0.9f);
            t.Pit(58f, 59.5f);
            t.Ground(59.5f, 92f);

            t.ParkedCar(68f, CarYellow);
            t.Checkpoint(73f);
            t.Wall(78f, 0.3f, 0f, 0.6f);
            t.CoinRow(5f, 10f, 0.5f, 3);
            t.CoinRow(15.3f, 16.8f, 1.95f, 2);
            t.CoinArc(34.5f, 41.5f, 1.9f, 0.8f, 5);
            t.CoinArc(57.5f, 60f, 0.7f, 1.3f, 3);
            t.CoinRow(67.3f, 68.8f, 1.95f, 2);
            t.Sticker(new Vector2(38f, 4.2f));
            t.Goal(84f);
        }

        /// <summary>L03: up and over the hill, then a juggling stretch to the gate.</summary>
        public static void UpTheHill(TrackBuilder t)
        {
            t.Walls(-8f, 128f);
            t.Start(0f);
            t.Ground(-8f, 20f);
            t.Sign("Up the hill!\nJump each step, chip the ball up", new Vector2(10f, 3.2f));

            t.Ground(20f, 23f, 0.6f);
            t.Ground(23f, 26f, 1.2f);
            t.Ground(26f, 32f, 1.8f);
            t.Pit(32f, 34f, 1.8f);
            t.Sign("Big gap!", new Vector2(33f, 4.4f));
            t.Ground(34f, 44f, 1.8f);
            t.Checkpoint(36f, 1.8f);

            t.Ramp(new Vector2(44f, 1.8f), new Vector2(50f, 0f));
            t.Ground(44f, 66f);
            t.Checkpoint(52f);
            t.StepAndHighWall(58f);
            t.Sign("Step up, stop, chip over", new Vector2(58f, 3.6f));

            t.Water(66f, 68f);
            t.Ground(68f, 128f);
            t.Checkpoint(71f);
            t.CrateStack(78f);

            t.Sign("Nearly there! Kick it up\nand juggle to the gate", new Vector2(90f, 3.2f));
            t.Wall(100f, 0.3f, 0f, 0.6f);
            t.Checkpoint(103f);
            t.Wall(108f, 0.9f);

            t.CoinRow(21.5f, 30.5f, 2.6f, 4);
            t.CoinArc(31.5f, 34.5f, 2.6f, 1.2f, 3);
            t.CoinRow(46f, 49f, 1.6f, 3);
            t.CoinArc(57f, 60f, 1.4f, 1.5f, 3);
            t.CoinRow(86f, 96f, 2.2f, 5);
            t.Sticker(new Vector2(37f, 5f));
            t.Goal(120f);
        }

        /// <summary>L04: locked gates opened by kicking the ball at a button.</summary>
        public static void GardenGate(TrackBuilder t)
        {
            t.Walls(-8f, 96f);
            t.Start(0f);
            t.Hint(8f, "gate");
            t.Ground(-8f, 96f);
            t.Sign("Locked gate!\nKick the ball at the red button", new Vector2(7f, 3.6f));

            t.SwitchAndGate(new Vector2(14f, 2.2f), 18f);
            t.Checkpoint(22f);
            t.Wall(27f, 0.9f);

            t.Checkpoint(33f);
            t.Wall(40f, 0.6f);
            t.SwitchAndGate(new Vector2(44f, 2.8f), 47f);
            t.Sign("Higher this time", new Vector2(42f, 4.2f));

            t.ParkedCar(55f, CarYellow);
            t.Checkpoint(62f);
            t.SwitchAndGate(new Vector2(70f, 0.3f), 74f);
            t.Sign("A low one - a hard dribble does it", new Vector2(69f, 3f));

            t.Wall(80f, 0.3f, 0f, 0.6f);
            t.CoinRow(4f, 10f, 0.5f, 3);
            t.CoinRow(19f, 23f, 0.5f, 3);
            t.CoinArc(26f, 28f, 1.1f, 1f, 3);
            t.CoinRow(48f, 52f, 0.5f, 3);
            t.CoinRow(75f, 79f, 0.5f, 3);
            t.Sticker(new Vector2(44f, 5f));
            t.Goal(88f);
        }

        /// <summary>L05: chapter finale with puddles plus everything so far.</summary>
        public static void PuddleLane(TrackBuilder t)
        {
            t.Walls(-8f, 120f);
            t.Start(0f);
            t.Hint(7f, "puddle");
            t.Ground(-8f, 48f);
            t.Sign("Rainy morning.\nPuddles slow everything down", new Vector2(5f, 3.2f));

            t.Puddle(10f, 13f);
            t.Wall(18f, 0.3f, 0f, 0.6f);
            t.Puddle(22f, 26f);
            t.Checkpoint(29f);
            t.ParkedCar(36f, CarPurple);

            t.Pit(48f, 49.8f);
            t.Ground(49.8f, 78f);
            t.Checkpoint(53f);
            t.SwitchAndGate(new Vector2(62f, 2.4f), 66f);
            t.Puddle(70f, 74f);

            t.Water(78f, 80f);
            t.Ground(80f, 120f);
            t.Checkpoint(84f);
            t.Wall(90f, 0.9f);
            t.Puddle(94f, 97f);
            t.ParkedCar(102f, CarRed);
            t.CoinRow(10.5f, 12.5f, 0.6f, 3);
            t.CoinRow(22.5f, 25.5f, 0.6f, 3);
            t.CoinRow(35.3f, 36.8f, 1.95f, 2);
            t.CoinArc(47.5f, 50.3f, 0.7f, 1.3f, 3);
            t.CoinRow(70.5f, 73.5f, 0.6f, 3);
            t.CoinArc(77.5f, 80.5f, 0.7f, 1.3f, 3);
            t.Sticker(new Vector2(102f, 3.6f));
            t.Goal(112f);
        }

        // ===================== Chapter 2: Market and Crossings =====================

        /// <summary>L06: people in the way of the ball.</summary>
        public static void MarketMorning(TrackBuilder t)
        {
            t.Walls(-8f, 100f);
            t.Start(0f);
            t.Hint(9f, "pedestrian");
            t.Ground(-8f, 100f);
            t.Sign("Busy market! The ball bounces\noff people - chip over them\nor wait for a gap", new Vector2(6f, 3.4f));

            t.Pedestrian(14f, 20f, CoatA);
            t.CrateStack(26f);
            t.Checkpoint(30f);
            t.Pedestrian(36f, 42f, CoatB, 0f, 1.3f);
            t.Awning(48f, 2.6f);
            t.Pedestrian(52f, 56f, CoatC);
            t.Checkpoint(60f);
            t.CrateStack(66f);
            t.Crate(70f, 0.35f);
            t.Pedestrian(74f, 82f, CoatD, 0f, 0.9f);
            t.CoinRow(8f, 12f, 0.5f, 3);
            t.CoinArc(25.5f, 27.5f, 1.6f, 1f, 3);
            t.CoinRow(44f, 52f, 3.2f, 4);
            t.CoinArc(65.5f, 70.5f, 1.6f, 1f, 4);
            t.CoinRow(84f, 88f, 0.5f, 3);
            t.Sticker(new Vector2(48f, 4.6f));
            t.Goal(92f);
        }

        /// <summary>L07: traffic lights. Stop and wait for green.</summary>
        public static void FirstCrossing(TrackBuilder t)
        {
            t.Walls(-8f, 90f);
            t.Start(0f);
            t.Hint(10f, "crossing");
            t.Ground(-8f, 90f);
            t.Sign("Zebra crossing ahead.\nWait for GREEN -\nlet go of the arrows to stop", new Vector2(6f, 3.4f));

            t.Crossing(16f, 21f, 0f);
            t.Checkpoint(24f);
            t.Pedestrian(30f, 34f, CoatB);
            t.Crossing(42f, 47f, 2f);
            t.Checkpoint(50f);
            t.CrateStack(56f);
            t.Crossing(64f, 69f, 4f);
            t.CoinRow(17f, 20f, 0.5f, 3);
            t.CoinRow(43f, 46f, 0.5f, 3);
            t.CoinArc(55.5f, 57.5f, 1.6f, 1f, 3);
            t.CoinRow(65f, 68f, 0.5f, 3);
            t.CoinRow(72f, 78f, 0.5f, 3);
            t.Sticker(new Vector2(18.5f, 3.8f));
            t.Goal(82f);
        }

        /// <summary>L08: crates, a puddle, a raised walkway and shoppers.</summary>
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
            t.Pedestrian(30f, 33f, CoatC);
            t.Ramp(new Vector2(34f, 0f), new Vector2(40f, 1.5f));
            t.Platform(40f, 50f, 1.5f);
            t.Crate(45f, 1.85f);
            t.Sign("Shop steps", new Vector2(40f, 3.6f));

            t.Checkpoint(54f);
            t.Wall(58f, 0.9f);
            t.Water(64f, 66f);
            t.Ground(66f, 108f);

            t.CrateStack(74f);
            t.Checkpoint(78f);
            t.Pedestrian(80f, 85f, CoatA);
            t.Awning(88f, 2.6f);
            t.Sign("Bounce it off the shop awning", new Vector2(88f, 4.2f));
            t.Wall(92f, 0.3f, 0f, 0.6f);

            t.CoinArc(11.5f, 13.5f, 1.6f, 1f, 3);
            t.CoinArc(21.5f, 24.5f, 0.7f, 1.3f, 3);
            t.CoinRow(41f, 49f, 2f, 4);
            t.CoinArc(63.5f, 66.5f, 0.7f, 1.3f, 3);
            t.CoinRow(86f, 90f, 3.4f, 3);
            t.Sticker(new Vector2(45f, 4.4f));
            t.Goal(100f);
        }

        /// <summary>L09: springboards made of fruit crates, awnings, a stall roof.</summary>
        public static void FruitStalls(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Hint(9f, "springboard");
            t.Ground(-8f, 110f);
            t.Sign("Fruit crates make great springboards!\nRoll the ball onto one, then jump on", new Vector2(6f, 3.4f));

            t.Springboard(14f);
            t.Wall(17f, 1.6f);
            t.Checkpoint(22f);

            t.Awning(28f, 2.6f);
            t.Awning(33f, 3.2f);
            t.Pedestrian(36f, 40f, CoatD);
            t.CrateStack(45f);
            t.Checkpoint(50f);

            t.Springboard(56f);
            t.Platform(58f, 66f, 2.2f);
            t.Sign("Up onto the stall roof!", new Vector2(58f, 4.4f));
            t.Pedestrian(70f, 75f, CoatA);
            t.Checkpoint(78f);
            t.Crossing(84f, 89f, 1f);
            t.CoinRow(14f, 17f, 2.4f, 3);
            t.CoinRow(27f, 34f, 3.8f, 4);
            t.CoinArc(44.5f, 46.5f, 1.6f, 1f, 3);
            t.CoinRow(59f, 65f, 2.7f, 4);
            t.CoinRow(85f, 88f, 0.5f, 3);
            t.Sticker(new Vector2(56f, 5.6f));
            t.Goal(100f);
        }

        /// <summary>L10: chapter finale. Rush hour: everything at once.</summary>
        public static void RushHour(TrackBuilder t)
        {
            t.Walls(-8f, 130f);
            t.Start(0f);
            t.Ground(-8f, 130f);
            t.Sign("Rush hour!\nStay calm, keep the ball close", new Vector2(5f, 3.2f));

            t.Pedestrian(10f, 16f, CoatB);
            t.Crossing(22f, 27f, 0f);
            t.Checkpoint(30f);
            t.CrateStack(36f);
            t.Pedestrian(40f, 46f, CoatC, 0f, 1.4f);
            t.Springboard(52f);
            t.Wall(55f, 1.6f);

            t.Checkpoint(60f);
            t.Crossing(66f, 71f, 3f);
            t.Puddle(76f, 79f);
            t.Pedestrian(82f, 88f, CoatA);
            t.Checkpoint(92f);
            t.Awning(98f, 2.6f);
            t.ParkedCar(104f, CarBlue);
            t.Crossing(110f, 115f, 5f);
            t.CoinRow(23f, 26f, 0.5f, 3);
            t.CoinArc(35.5f, 37.5f, 1.6f, 1f, 3);
            t.CoinRow(52f, 55f, 2.6f, 3);
            t.CoinRow(67f, 70f, 0.5f, 3);
            t.CoinRow(76.5f, 78.5f, 0.6f, 3);
            t.CoinRow(103.3f, 104.8f, 1.95f, 2);
            t.CoinRow(111f, 114f, 0.5f, 3);
            t.Sticker(new Vector2(98f, 4.6f));
            t.Goal(122f);
        }

        // ===================== Chapter 3: The Beach =====================

        /// <summary>L11: sand slows everything; a raised boardwalk with gaps.</summary>
        public static void Boardwalk(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Ground(-8f, 20f);
            t.Sign("The beach! Sand slows the ball -\nkeep your touches light", new Vector2(5f, 3.2f));
            t.Sand(8f, 18f);

            t.Ground(20f, 32f, 0.9f);
            t.Pit(32f, 33.8f, 0.9f);
            t.Ground(33.8f, 46f, 0.9f);
            t.Checkpoint(36f, 0.9f);

            t.Ground(46f, 62f);
            t.Sand(48f, 58f);
            t.Ground(62f, 74f, 0.9f);
            t.Checkpoint(64f, 0.9f);
            t.Pit(74f, 75.8f, 0.9f);
            t.Ground(75.8f, 88f, 0.9f);
            t.Ground(88f, 110f);
            t.Checkpoint(90f);
            t.Sand(94f, 98f);

            t.CoinRow(9f, 17f, 0.6f, 4);
            t.CoinArc(31.5f, 34.3f, 1.6f, 1.2f, 3);
            t.CoinRow(50f, 56f, 0.6f, 3);
            t.CoinArc(73.5f, 76.3f, 1.6f, 1.2f, 3);
            t.CoinRow(80f, 86f, 1.5f, 3);
            t.Sticker(new Vector2(75f, 4.6f));
            t.Goal(102f);
        }

        /// <summary>L12: the tide washes in and out; cross on low water.</summary>
        public static void LowTide(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Hint(13f, "tide");
            t.Ground(-8f, 110f);
            t.Sign("Low tide! Cross the wet sand\nwhen the water goes out", new Vector2(5f, 3.2f));

            t.Sand(10f, 14f);
            t.Tide(18f, 24f, 6f, 0f);
            t.Checkpoint(27f);
            t.Sand(30f, 34f);
            t.Tide(38f, 45f, 7f, 2f);
            t.Checkpoint(48f);
            t.Wall(52f, 0.6f, 0f, 0.8f);
            t.Sign("Sandcastle!", new Vector2(52f, 2.4f));
            t.Tide(58f, 62f, 5f, 1f);
            t.Tide(66f, 72f, 6f, 3f);
            t.Checkpoint(75f);
            t.Sand(78f, 84f);
            t.Tide(88f, 93f, 6f, 0f);

            t.CoinRow(19f, 23f, 0.6f, 3);
            t.CoinRow(39f, 44f, 0.6f, 3);
            t.CoinArc(51f, 53f, 1.4f, 1f, 3);
            t.CoinRow(67f, 71f, 0.6f, 3);
            t.CoinRow(89f, 92f, 0.6f, 3);
            t.Sticker(new Vector2(62f, 4.2f));
            t.Goal(102f);
        }

        /// <summary>L13: seagulls swoop at the ball; a gusty sea breeze.</summary>
        public static void SeagullBay(TrackBuilder t)
        {
            t.Walls(-8f, 115f);
            t.Start(0f);
            t.Hint(8f, "seagull");
            t.Ground(-8f, 115f);
            t.Sign("Seagulls swoop low -\nkeep the ball close!", new Vector2(5f, 3.4f));

            t.Seagull(30f, 4f, 2.2f, 0f);
            t.Sand(14f, 20f);
            t.Checkpoint(24f);
            t.Wind(28f, 45f, 0f, 5f, new Vector2(-5f, 0f), 4f);
            t.Sign("Sea breeze!", new Vector2(32f, 4f));
            t.Wall(40f, 0.9f);
            t.Checkpoint(48f);
            t.Seagull(60f, 32f, 2f, 1.5f);
            t.Tide(52f, 57f, 6f, 1f);
            t.Wall(66f, 0.6f, 0f, 0.8f);
            t.Seagull(90f, 62f, 2.4f, 0.5f);
            t.Checkpoint(72f);
            t.Springboard(78f);
            t.Wall(81f, 1.6f);
            t.Seagull(112f, 86f, 2.6f, 2f);

            t.CoinRow(15f, 19f, 0.6f, 3);
            t.CoinRow(30f, 38f, 0.5f, 4);
            t.CoinArc(39f, 41f, 1.4f, 1f, 3);
            t.CoinRow(78f, 81f, 2.6f, 3);
            t.CoinRow(88f, 96f, 0.5f, 4);
            t.Sticker(new Vector2(81f, 5f));
            t.Goal(106f);
        }

        /// <summary>L14: chapter finale on the sand.</summary>
        public static void SandcastleSprint(TrackBuilder t)
        {
            t.Walls(-8f, 130f);
            t.Start(0f);
            t.Ground(-8f, 28f);
            t.Sign("Sandcastle Sprint!\nEverything the beach can throw at you", new Vector2(5f, 3.4f));
            t.Sand(6f, 12f);
            t.Wall(16f, 0.6f, 0f, 0.9f);
            t.Wall(16f, 1f, 0f, 0.35f);

            t.Pit(28f, 29.6f);
            t.Ground(29.6f, 44f, 0.6f);
            t.Checkpoint(32f, 0.6f);
            t.Seagull(52f, 30f, 2.8f, 0f);
            t.Ground(44f, 130f);
            t.Tide(48f, 54f, 6f, 2f);
            t.Checkpoint(57f);
            t.Wind(60f, 75f, 0f, 5f, new Vector2(-6f, 0f), 5f);
            t.Sand(62f, 70f);
            t.Wall(73f, 0.9f);
            t.Checkpoint(78f);
            t.Tide(82f, 86f, 5f, 0f);
            t.Seagull(104f, 80f, 2.2f, 1f);
            t.Springboard(92f);
            t.Platform(94f, 100f, 2f);
            t.Checkpoint(104f);
            t.Tide(108f, 112f, 6f, 3f);

            t.CoinArc(15f, 17f, 1.5f, 1f, 3);
            t.CoinArc(27.6f, 30.2f, 1f, 1.2f, 3);
            t.CoinRow(63f, 69f, 0.6f, 3);
            t.CoinRow(95f, 99f, 2.6f, 3);
            t.CoinRow(109f, 111f, 0.6f, 2);
            t.Sticker(new Vector2(97f, 5.2f));
            t.Goal(122f);
        }

        // ===================== Chapter 4: Underpass & Construction =====================

        /// <summary>L15: dark tunnels and puddles.</summary>
        public static void TheUnderpass(TrackBuilder t)
        {
            t.Walls(-8f, 105f);
            t.Start(0f);
            t.Hint(10f, "tunnel");
            t.Ground(-8f, 105f);
            t.Sign("Into the underpass -\nit's dark in there!", new Vector2(5f, 3.2f));

            t.Tunnel(14f, 34f);
            t.Puddle(20f, 23f);
            t.Wall(28f, 0.3f, 0f, 0.6f);
            t.Checkpoint(37f);
            t.Ramp(new Vector2(42f, 0f), new Vector2(48f, 1.5f));
            t.Platform(48f, 56f, 1.5f);
            t.Ramp(new Vector2(56f, 1.5f), new Vector2(62f, 0f));
            t.Tunnel(64f, 86f);
            t.Puddle(70f, 74f);
            t.CrateStack(79f);
            t.Checkpoint(89f);

            t.CoinRow(16f, 26f, 0.5f, 5);
            t.CoinRow(49f, 55f, 2f, 4);
            t.CoinRow(66f, 76f, 0.5f, 4);
            t.Sticker(new Vector2(52f, 5f));
            t.Goal(98f);
        }

        /// <summary>L16: rolling pipes down the building-site slopes.</summary>
        public static void BuildingSite(TrackBuilder t)
        {
            t.Walls(-8f, 115f);
            t.Start(0f);
            t.Hint(12f, "pipes");
            t.Ground(-8f, 115f);
            t.Sign("Building site! Pipes roll\ndown the slope - jump them", new Vector2(5f, 3.4f));

            t.Ramp(new Vector2(18f, 0f), new Vector2(28f, 2.5f));
            t.Platform(28f, 34f, 2.5f);
            t.Pipes(new Vector2(33f, 3.2f), 4f, 5f);
            t.Ramp(new Vector2(34f, 2.5f), new Vector2(40f, 0f));
            t.Checkpoint(42f);
            t.CrateStack(48f);
            t.CrateStack(52f);
            t.Ramp(new Vector2(58f, 0f), new Vector2(66f, 2f));
            t.Platform(66f, 72f, 2f);
            t.Pipes(new Vector2(71f, 2.8f), 3.5f, 50f, 0.5f);
            t.Ramp(new Vector2(72f, 2f), new Vector2(78f, 0f));
            t.Checkpoint(80f);
            t.SwitchAndGate(new Vector2(88f, 2.6f), 92f);
            t.Puddle(95f, 98f);

            t.CoinArc(20f, 27f, 1.5f, 1.5f, 4);
            t.CoinRow(29f, 33f, 3.1f, 3);
            t.CoinArc(47.5f, 53f, 1.8f, 1f, 4);
            t.CoinRow(67f, 71f, 2.6f, 3);
            t.CoinRow(93f, 99f, 0.5f, 3);
            t.Sticker(new Vector2(31f, 6f));
            t.Goal(106f);
        }

        /// <summary>L17: ride crane platforms across open pits.</summary>
        public static void Cranes(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Hint(15f, "platform");
            t.Ground(-8f, 20f);
            t.Sign("Ride the crane platforms across.\nChip the ball on first!", new Vector2(5f, 3.4f));

            t.Pit(20f, 30f);
            t.MovingPlatform(new Vector2(22f, -0.175f), 2.6f, new Vector2(6f, 0f));
            t.Ground(30f, 44f);
            t.Checkpoint(32f);
            t.Pit(44f, 52f);
            t.MovingPlatform(new Vector2(45.5f, 0.6f), 2.6f, new Vector2(5f, 0f), 1.3f);
            t.Ground(52f, 64f);
            t.Checkpoint(55f);
            t.Pit(64f, 70f);
            t.MovingPlatform(new Vector2(66.5f, -0.175f), 2.6f, new Vector2(0f, 2.2f), 1f);
            t.Sign("Going up!", new Vector2(66.5f, 4.6f));
            t.Ground(70f, 82f, 2f);
            t.Checkpoint(73f, 2f);
            t.Pit(82f, 90f, 2f);
            t.MovingPlatform(new Vector2(84f, 1.825f), 2.6f, new Vector2(4f, 0f));
            t.Ground(90f, 110f);
            t.Checkpoint(93f);

            t.CoinRow(22f, 28f, 1f, 4);
            t.CoinRow(46f, 50f, 1.8f, 3);
            t.CoinRow(66.5f, 66.5f, 3f, 1);
            t.CoinRow(74f, 80f, 2.5f, 3);
            t.CoinRow(85f, 88f, 2.8f, 3);
            t.Sticker(new Vector2(67f, 6f));
            t.Goal(102f);
        }

        /// <summary>L18: chapter finale through tunnels, pipes and cranes.</summary>
        public static void TunnelRun(TrackBuilder t)
        {
            t.Walls(-8f, 135f);
            t.Start(0f);
            t.Ground(-8f, 48f);
            t.Sign("Tunnel Run!", new Vector2(5f, 3f));
            t.Tunnel(10f, 40f, 0f, 3.4f);
            t.Pipes(new Vector2(38f, 0.6f), 3.2f, 8f, 1f);
            t.Puddle(18f, 21f);
            t.Checkpoint(42f);
            t.Pit(48f, 56f);
            t.MovingPlatform(new Vector2(50f, -0.175f), 2.6f, new Vector2(4f, 0f));
            t.Ground(56f, 135f);
            t.Checkpoint(58f);
            t.Ramp(new Vector2(62f, 0f), new Vector2(68f, 1.6f));
            t.Platform(68f, 76f, 1.6f);
            t.Ramp(new Vector2(76f, 1.6f), new Vector2(82f, 0f));
            t.Tunnel(84f, 112f, 0f, 3.4f);
            t.CrateStack(92f);
            t.Puddle(98f, 101f);
            t.Pipes(new Vector2(110f, 0.6f), 4f, 86f, 2f);
            t.Checkpoint(114f);
            t.SwitchAndGate(new Vector2(120f, 2.4f), 124f);

            t.CoinRow(12f, 16f, 0.5f, 3);
            t.CoinRow(26f, 34f, 1.6f, 4);
            t.CoinRow(50f, 54f, 1f, 3);
            t.CoinRow(69f, 75f, 2.1f, 3);
            t.CoinRow(102f, 108f, 0.5f, 3);
            t.Sticker(new Vector2(72f, 5f));
            t.Goal(128f);
        }

        // ===================== Chapter 5: Park & School =====================

        /// <summary>L19: dogs in the park.</summary>
        public static void ParkGates(TrackBuilder t)
        {
            t.Walls(-8f, 105f);
            t.Start(0f);
            t.Hint(8f, "dog");
            t.Ground(-8f, 105f);
            t.Sign("The park! Dogs chase low balls -\nchip it over their heads", new Vector2(5f, 3.4f));

            t.Dog(14f, 22f, DogBrown);
            t.Checkpoint(26f);
            t.SwitchAndGate(new Vector2(32f, 2.4f), 36f);
            t.Dog(42f, 52f, DogWhite);
            t.Wall(56f, 0.9f);
            t.Checkpoint(60f);
            t.Dog(66f, 76f, DogBlack);
            t.Puddle(80f, 83f);

            t.CoinArc(14f, 22f, 0.8f, 1.6f, 5);
            t.CoinRow(37f, 40f, 0.5f, 3);
            t.CoinArc(42f, 52f, 0.8f, 1.8f, 5);
            t.CoinArc(66f, 76f, 0.8f, 1.6f, 5);
            t.Sticker(new Vector2(47f, 4.5f));
            t.Goal(96f);
        }

        /// <summary>L20: fountains lift the ball; springboards lift the kid.</summary>
        public static void FountainSquare(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Hint(8f, "fountain");
            t.Ground(-8f, 110f);
            t.Sign("Fountains push the ball up -\ndribble into the spray!", new Vector2(5f, 3.4f));

            t.Fountain(13f, 0f, 4f, 18f);
            t.Springboard(15f);
            t.Wall(17f, 1.6f);
            t.Checkpoint(21f);
            t.Dog(30f, 38f, DogBrown);
            t.Checkpoint(42f);
            t.Fountain(50f, 0f, 4f, 18f);
            t.Springboard(52f);
            t.Wall(54f, 1.6f);
            t.Water(60f, 62f);
            t.Checkpoint(65f);
            t.Fountain(72f, 0f, 6f, 14f);
            t.Dog(80f, 88f, DogWhite);

            t.CoinRow(13f, 13f, 3f, 1);
            t.CoinRow(15f, 17f, 2.6f, 2);
            t.CoinArc(29f, 39f, 0.8f, 1.6f, 5);
            t.CoinRow(50f, 54f, 2.8f, 3);
            t.CoinRow(72f, 72f, 2f, 1);
            t.CoinRow(72f, 72f, 3.5f, 1);
            t.CoinRow(72f, 72f, 5f, 1);
            t.Sticker(new Vector2(72f, 6.5f));
            t.Goal(100f);
        }

        /// <summary>L21: swings across the sandpit.</summary>
        public static void Playground(TrackBuilder t)
        {
            t.Walls(-8f, 110f);
            t.Start(0f);
            t.Hint(16f, "swing");
            t.Ground(-8f, 22f);
            t.Sign("Playground! Chip the ball across,\nthen jump on the swing", new Vector2(5f, 3.4f));

            t.Pit(22f, 30f);
            t.Swing(new Vector2(26f, 4.2f), 3.6f, 35f, 3f);
            t.Ground(30f, 52f);
            t.Checkpoint(32f);
            t.Springboard(38f);
            t.Platform(40f, 46f, 2.4f);
            t.Sign("Climbing frame", new Vector2(43f, 4.3f));
            t.Dog(47f, 51f, DogBlack);
            t.Pit(52f, 62f);
            t.Swing(new Vector2(55f, 4.4f), 3.8f, 35f, 3.2f, 1f);
            t.Swing(new Vector2(59.5f, 4.4f), 3.8f, 35f, 3.2f, 0f);
            t.Ground(62f, 110f);
            t.Checkpoint(64f);
            t.Fountain(72f, 0f, 4f, 18f);
            t.Springboard(74f);
            t.Wall(76f, 1.6f);
            t.Checkpoint(80f);
            t.Dog(86f, 94f, DogBrown);

            t.CoinArc(22f, 30f, 1.2f, 2f, 5);
            t.CoinRow(41f, 45f, 2.9f, 3);
            t.CoinArc(52f, 62f, 1.2f, 2f, 5);
            t.CoinArc(86f, 94f, 0.8f, 1.6f, 4);
            t.Sticker(new Vector2(43f, 5.6f));
            t.Goal(102f);
        }

        /// <summary>L22: lily pads and stepping stones over the duck pond.</summary>
        public static void DuckPond(TrackBuilder t)
        {
            t.Walls(-8f, 115f);
            t.Start(0f);
            t.Ground(-8f, 18f);
            t.Sign("Duck pond! Lily pads and stepping stones", new Vector2(5f, 3f));

            t.Water(18f, 28f);
            t.MovingPlatform(new Vector2(20f, -0.175f), 2.2f, new Vector2(5f, 0f), 1.4f);
            t.Ground(28f, 46f);
            t.Checkpoint(30f);
            t.Dog(34f, 42f, DogWhite);
            t.Water(46f, 48f);
            t.Ground(48f, 70f);
            t.Fountain(54f, 0f, 4f, 18f);
            t.Springboard(56f);
            t.Wall(58f, 1.6f);
            t.Checkpoint(61f);
            t.Water(70f, 72f);
            t.Ground(72f, 73.5f);
            t.Water(73.5f, 75.5f);
            t.Ground(75.5f, 77f);
            t.Water(77f, 79f);
            t.Ground(79f, 115f);
            t.Sign("Stepping stones", new Vector2(74.5f, 3f));
            t.Checkpoint(82f);
            t.Dog(88f, 96f, DogBrown);

            t.CoinRow(20f, 26f, 1f, 4);
            t.CoinArc(33f, 43f, 0.8f, 1.6f, 5);
            t.CoinArc(45.5f, 49.5f, 0.7f, 1.3f, 3);
            t.CoinRow(72.7f, 76.2f, 0.6f, 2);
            t.CoinArc(88f, 96f, 0.8f, 1.6f, 4);
            t.Sticker(new Vector2(54f, 5.5f));
            t.Goal(106f);
        }

        /// <summary>L23: the grand finale, all the way to the school steps.</summary>
        public static void TheFinalBell(TrackBuilder t)
        {
            t.Walls(-8f, 160f);
            t.Start(0f);
            t.Ground(-8f, 40f);
            t.Sign("The final run!\nDon't be late for school!", new Vector2(5f, 3.2f));

            t.Dog(10f, 18f, DogBrown);
            t.Crossing(24f, 29f, 0f);
            t.Checkpoint(32f);
            t.Pit(40f, 48f);
            t.Swing(new Vector2(44f, 4.2f), 3.6f, 35f, 3f);
            t.Ground(48f, 90f);
            t.Fountain(54f, 0f, 4f, 18f);
            t.Springboard(56f);
            t.Wall(58f, 1.6f);
            t.Checkpoint(62f);
            t.Pedestrian(66f, 72f, CoatB);
            t.Puddle(74f, 77f);
            t.Tunnel(80f, 96f, 0f, 3.4f);
            t.Ground(90f, 160f);
            t.Checkpoint(98f);
            t.Seagull(122f, 100f, 2.4f, 0f);
            t.SwitchAndGate(new Vector2(106f, 2.4f), 110f);
            t.Dog(114f, 122f, DogBlack);
            t.Checkpoint(126f);
            t.Ramp(new Vector2(130f, 0f), new Vector2(136f, 1.2f));
            t.Platform(136f, 156f, 1.2f);
            t.Sign("School steps!", new Vector2(140f, 3.6f));

            t.CoinArc(10f, 18f, 0.8f, 1.6f, 4);
            t.CoinRow(25f, 28f, 0.5f, 3);
            t.CoinArc(40f, 48f, 1.2f, 2f, 5);
            t.CoinRow(82f, 94f, 0.5f, 5);
            t.CoinArc(114f, 122f, 0.8f, 1.6f, 4);
            t.CoinRow(138f, 146f, 1.7f, 4);
            t.Sticker(new Vector2(58f, 5f));
            t.Goal(150f, 1.2f);
        }

        // ===================== Ball skill challenges =====================

        /// <summary>C01 (Ch1): keepy-uppy.</summary>
        public static void KeepyUppy(TrackBuilder t)
        {
            t.Walls(-6f, 14f);
            t.Start(0f);
            t.Hint(0.5f, "juggle");
            t.Ground(-6f, 14f);
            t.Sign("Kick the ball up (drag up\nfrom KICK), then tap to juggle!", new Vector2(4f, 3.6f));
            t.Challenge<JuggleChallenge>("Keepy-Uppy", "Kick the ball up, then tap each time it drops near you. Best run counts!", 45f, 5, 10, 15);
            t.CoinRow(-2f, 2f, 2.4f, 3);
        }

        /// <summary>C02 (Ch2): hit the shop signs.</summary>
        public static void WindowShopping(TrackBuilder t)
        {
            t.Walls(-8f, 72f);
            t.Start(0f);
            t.Ground(-8f, 72f);
            var c = t.Challenge<AccuracyChallenge>("Window Shopping", "Hit every shop sign with the ball before time runs out!", 60f, 3, 5, 7);
            c.targets = new[]
            {
                t.Target(new Vector2(10f, 1.6f)),
                t.Target(new Vector2(18f, 2.6f)),
                t.Target(new Vector2(26f, 1.2f)),
                t.Target(new Vector2(34f, 3.2f)),
                t.Target(new Vector2(42f, 2f)),
                t.Target(new Vector2(52f, 3.6f)),
                t.Target(new Vector2(62f, 2.4f)),
            };
            t.Pedestrian(28f, 33f, CoatA);
            t.CrateStack(46f);
            t.CoinRow(5f, 65f, 0.5f, 8);
        }

        /// <summary>C03 (Ch3): beach slalom of low gates and hoops.</summary>
        public static void BeachSlalom(TrackBuilder t)
        {
            t.Walls(-8f, 84f);
            t.Start(0f);
            t.Ground(-8f, 84f);
            var c = t.Challenge<SlalomChallenge>("Beach Slalom", "Keep the ball LOW under the bars and LOFT it through the hoops. Fastest time wins!", 0f, 400, 280, 220);
            c.gates = new[]
            {
                t.SlalomGate(10f, SlalomGate.Kind.Low),
                t.SlalomGate(18f, SlalomGate.Kind.Hoop),
                t.SlalomGate(26f, SlalomGate.Kind.Low),
                t.SlalomGate(34f, SlalomGate.Kind.Low),
                t.SlalomGate(42f, SlalomGate.Kind.Hoop),
                t.SlalomGate(50f, SlalomGate.Kind.Low),
                t.SlalomGate(58f, SlalomGate.Kind.Hoop),
                t.SlalomGate(66f, SlalomGate.Kind.Low),
            };
            t.Sand(28f, 32f);
            t.CoinRow(12f, 64f, 0.5f, 8);
            t.Goal(76f);
        }

        /// <summary>C04 (Ch4): targets on the building site, high and low.</summary>
        public static void SiteTargets(TrackBuilder t)
        {
            t.Walls(-8f, 80f);
            t.Start(0f);
            t.Ground(-8f, 80f);
            var c = t.Challenge<AccuracyChallenge>("Site Targets", "Eight targets around the site. Some need a big kick!", 60f, 4, 6, 8);
            c.targets = new[]
            {
                t.Target(new Vector2(8f, 1.4f)),
                t.Target(new Vector2(15f, 3.4f)),
                t.Target(new Vector2(22f, 2.2f)),
                t.Target(new Vector2(30f, 4.2f), false),
                t.Target(new Vector2(38f, 1.6f)),
                t.Target(new Vector2(46f, 3.8f)),
                t.Target(new Vector2(56f, 2.6f)),
                t.Target(new Vector2(66f, 4.6f), false),
            };
            t.Ramp(new Vector2(22f, 0f), new Vector2(28f, 1.6f));
            t.Platform(28f, 32f, 1.6f);
            t.Ramp(new Vector2(32f, 1.6f), new Vector2(36f, 0f));
            t.CrateStack(50f);
            t.MovingPlatform(new Vector2(60f, 1.2f), 2.4f, new Vector2(0f, 1.6f), 1f);
            t.CoinRow(4f, 72f, 0.5f, 8);
        }

        /// <summary>C05 (Ch5): juggling for champions.</summary>
        public static void JuggleChampion(TrackBuilder t)
        {
            t.Walls(-6f, 14f);
            t.Start(0f);
            t.Ground(-6f, 14f);
            t.Sign("Juggle Champion!", new Vector2(4f, 3.6f));
            t.Challenge<JuggleChallenge>("Juggle Champion", "The ultimate keepy-uppy. Can you reach 30?", 60f, 10, 20, 30);
            t.CoinRow(-2f, 2f, 2.4f, 3);
        }
    }
}
