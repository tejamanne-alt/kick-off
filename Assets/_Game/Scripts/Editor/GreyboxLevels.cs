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

        // ===================== Chapter 1: Home Street =====================

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
            t.Sign("Step up, brake, chip over", new Vector2(58f, 3.6f));

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
            t.SwitchAndGate(new Vector2(70f, 0.9f), 74f);
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

        /// <summary>L07: traffic lights. Brake and wait for green.</summary>
        public static void FirstCrossing(TrackBuilder t)
        {
            t.Walls(-8f, 90f);
            t.Start(0f);
            t.Ground(-8f, 90f);
            t.Sign("Zebra crossing ahead.\nWait for GREEN -\nhold the left side to brake", new Vector2(6f, 3.4f));

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
    }
}
