using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's levels (docs/KAMAKURA_BUILD.md, Step 7), built by GeneratedContent.CityLevels while LevelBuildKit.Kamakura is
    /// set. Each places the Kamakura kit's models by its proposed layout (review/kamakura/levels/&lt;id&gt;/layout.json, approved
    /// with the user's go-ahead: its x is this layout's x, the front door at -12; its "front" the z of a model's street face,
    /// which <see cref="TrackBuilder.KmModel"/> moves back to the game's wider footpath), and stands in for what is still to come
    /// (the lane's houses, its block wall and fences) with plain boxes in their colours.
    /// </summary>
    public static class KamakuraLevels
    {
        static readonly Color BlockWall = new Color(0.66f, 0.66f, 0.63f), Boards = new Color(0.4f, 0.32f, 0.25f);
        static readonly Color Mortar = new Color(0.86f, 0.84f, 0.8f), Timber = new Color(0.36f, 0.28f, 0.22f), Cream = new Color(0.88f, 0.82f, 0.7f);
        static readonly Color Tiles = new Color(0.32f, 0.33f, 0.35f);

        /// <summary>
        /// KM1-1 Hase Lanes (dribble; docs/KAMAKURA_BUILD.md, BUILD KM-L11): out of the home's gate past its pots and the
        /// persimmon, the vending corner, the block wall with the cat on it, the first-graders walking to school, the little
        /// shrine up its steps, the parked delivery scooter, the level crossing (the bells, the barriers, the tram), and Hase
        /// Station's ticket gate: the stop. The lane's houses are stand-ins until they are built from the user's lane pictures
        /// (refs/photo/KM1-1a to e).
        /// </summary>
        public static void HaseLanes(TrackBuilder t)
        {
            t.Walls(-8f, 84f);
            t.Start(0f);
            t.Ground(-8f, 84f);

            // The home's garden (the home itself is built at the door, -12: StreetBuilder.HomeFrontKM): the pots in front of its
            // fence either side of the gate (KM-G26 to G33), the air conditioner's outdoor unit, the letterbox by the gate, the
            // bicycle, the persimmon over the fence's end and the neighbour's clipped hedge.
            t.KmModel("KmAirConditioner", -17.8f, 1.2f);
            t.KmModel("KmShrubPlanter", -16.6f, 1.1f);
            t.KmModel("KmHydrangeaPlanter", -15.6f, 1.1f);
            t.KmModel("KmPotPinkFlowers", -14.8f, 1.1f);
            t.KmModel("KmPotWhiteDaisies", -14.3f, 1.1f);
            t.KmModel("KmMorningGloryPot", -13.7f, 1.1f);
            t.KmModel("KmLetterbox", -10.0f, 1.15f);
            t.KmModel("KmBonsaiTerracotta", -9.2f, 1.1f);
            t.KmModel("KmBonsaiBlueBowl", -8.4f, 1.1f);
            t.KmModel("KmStoneStandFlowers", -7.6f, 1.1f);
            t.KmModel("KmBicycle", -4.4f, 1.1f);
            t.KmModel("KmPersimmonTree", -0.8f, 2.6f);
            t.KmModel("KmHedgeClipped", 0.6f, 1.3f);

            // The vending corner: the transformer pole, the convex mirror at the kerb, the red and the blue machines, the bins.
            t.KmModel("KmPoleTransformer", 3f, 1.15f);
            t.KmModel("KmMirror", 5f, 0.85f);
            t.KmModel("KmVendingRed", 6.7f, 1.25f);
            t.KmModel("KmVendingBlue", 7.8f, 1.25f);
            t.KmModel("KmRecyclingBins", 9.2f, 1.3f);

            // The block wall the cat sits on (a stand-in until its KM-T plate is built), the garden pine leaning over it, the
            // mossy stone at its foot, and the houses behind it (stand-ins until KM1-1a and b's houses are built).
            t.KmStandIn("BlockWall", 21f, 1.4f, 22f, 0.2f, 1.6f, BlockWall, true);
            t.KmModel("KmGardenPine", 18f, 2.2f);
            t.KmModel("KmMossyStone", 26f, 0.8f);                // against the wall's foot, just behind the footpath's edge (1.55 m)
            HouseStandIn(t, 15.5f, 5f, 9f, Mortar);
            HouseStandIn(t, 27f, 5f, 10f, Timber);

            // The little shrine up its steps and its torii, the house behind its lane (a stand-in), the parked scooter.
            t.KmModel("KmToriiSmall", 36f, 2.4f);
            t.KmModel("KmShrineSmall", 36f, 4.2f);
            HouseStandIn(t, 42f, 9f, 6f, Cream);
            t.KmModel("KmScooter", 45f, 0.95f);

            // The beige house and its fence (a stand-in), the plain pole with its street lamp, the crossing's control cabinet.
            t.KmModel("KmHouseBeige", 49f, 3.4f);
            t.KmStandIn("WoodenFence", 49f, 1.4f, 6f, 0.12f, 1.7f, Boards);
            t.KmModel("KmPolePlain", 54f, 1.15f);
            t.KmModel("KmStreetLamp", 54.6f, 1.1f);
            t.KmModel("KmControlCabinet", 57.2f, 1.4f);

            // The wire gantry over the tracks, the pole by the station, the hydrangeas along the station's fence, the pines behind.
            t.KmModel("KmWireGantry", 63f, 4.5f);
            t.KmModel("KmPolePlain", 70f, 1.15f);
            t.KmModel("KmHydrangeaBlue", 71.6f, 1.3f);
            t.KmModel("KmHydrangeaPink", 87f, 1.3f);
            t.KmModel("KmHydrangeaViolet", 88.6f, 1.3f);
            t.KmModel("KmBlackPine", 91f, 4f);

            // The play: a kerb where the side lane comes out by the vending corner, the first-graders walking to school in a
            // line (get past them without the ball touching one), coins up the shrine's steps, the level crossing (wait for the
            // tram), and Hase Station's ticket gate: the stop.
            t.CoinRow(-6f, -1f, 0.5f, 4);
            t.Wall(12.5f, 0.25f, 0f, 0.6f);
            t.CoinArc(11.3f, 13.7f, 0.6f, 1.2f, 3);
            t.Checkpoint(16f);
            t.FirstGraderLine(22f, 33f, 5);
            t.CoinRow(18f, 21f, 0.5f, 3);
            t.CoinArc(35f, 37.5f, 0.8f, 1.2f, 3);
            t.Checkpoint(40f);
            t.CoinRow(43f, 48f, 0.5f, 4);
            t.Checkpoint(53f);
            t.LevelCrossing(59.5f, 66.5f);
            t.CoinRow(67.5f, 71.5f, 0.5f, 3);
            t.Goal(73.6f);
        }

        // ------------------------------------------------------------------ the other eleven legs (docs/CITIES.md, Kamakura)
        // Each lays its lane from the user's lane pictures (TrackBuilder.KmLane: tools/blender/km_lanes.py), from x0 at the first
        // picture's left edge, and places its play where the pictures show what it is about. A lane picture is 29.49 m wide in
        // KM1-3 and KM1-4 (the 4128 px pictures), 27.15 m in the others; x in a picture = x0 + width * (its pixel / its width).

        static readonly Color CoatNavy = new Color(0.2f, 0.25f, 0.4f), CoatRed = new Color(0.72f, 0.24f, 0.22f),
            CoatGreen = new Color(0.3f, 0.48f, 0.34f), CoatBeige = new Color(0.78f, 0.7f, 0.56f), CoatDark = new Color(0.16f, 0.16f, 0.18f),
            UmbrellaBlue = new Color(0.25f, 0.42f, 0.72f), UmbrellaRose = new Color(0.78f, 0.42f, 0.55f);
        static readonly Color ShibaTan = new Color(0.82f, 0.55f, 0.28f), TanukiBrown = new Color(0.42f, 0.34f, 0.26f);

        /// <summary>
        /// KM1-2 Ride the Enoden (mini-game M1): out of Hase Station's ticket gate to the platform, where the card reader opens
        /// the ride (TrackBuilder.RideGate: MiniGames/TramRide); the ride ends the leg at Kamakura Station.
        /// </summary>
        public static void RideTheEnoden(TrackBuilder t)
        {
            t.Walls(-8f, 16f);
            t.Start(0f);
            t.Ground(-8f, 16f);
            t.CoinRow(-4f, 0f, 0.5f, 3);
            t.RideGate(2.5f);
            t.Goal(10f);
        }

        /// <summary>
        /// KM1-3 Komachi-dori (dribble): out of Kamakura Station (KM1-3a) under the red gateway, along the shops (KM1-3b: the
        /// soft-serve stand, the croquette and rice-cracker shops, the souvenir shop) among the sightseers, a black kite diving
        /// at the snacks, the rickshaw going slowly by the pickle shop (KM1-3d), to the shrine's side gate: the stop.
        /// </summary>
        public static void KomachiDori(TrackBuilder t)
        {
            t.Walls(-8f, 75f);
            t.Start(0f);
            t.Ground(-8f, 75f);
            t.KmLane("KM1-3", -20f);

            t.CoinRow(1f, 6f, 0.5f, 4);
            t.Checkpoint(10f);
            t.CoinArc(12f, 15f, 0.6f, 1.3f, 3);          // under the gateway
            t.Pedestrian(18f, 26f, CoatNavy, 0f, 0.9f);    // sightseers along the shops
            t.Pedestrian(22f, 31f, CoatBeige, 0f, 1.0f);
            t.Pedestrian(27f, 36f, CoatRed, 0f, 0.8f);
            t.Seagull(24f, 38f, 2.6f);                     // the black kite diving at a snack
            t.CoinRow(19f, 24f, 0.5f, 4);
            t.Checkpoint(39f);
            t.Pedestrian(44f, 54f, CoatDark, 0f, 0.5f);    // the rickshaw puller, slow: ride behind him
            t.CoinRow(40f, 44f, 0.5f, 4);
            t.Checkpoint(56f);
            t.CoinArc(57f, 61f, 0.6f, 1.2f, 3);
            t.Goal(64.5f);
        }

        /// <summary>
        /// KM1-4 The Shrine Bridge (dribble): from the shrine's side gate along its stone wall (KM1-4a: the basin pavilion, the
        /// lanterns, the lotus pond and its arched bridge), past the steps up to the vermilion hall (KM1-4b), across the side
        /// road at the zebra crossing (KM1-4c; M5, wait then cross), past the shop and the house to the school's fence: school.
        /// </summary>
        public static void ShrineBridge(TrackBuilder t)
        {
            t.Walls(-8f, 80f);
            t.Start(0f);
            t.Ground(-8f, 80f);
            t.KmLane("KM1-4", -16f);

            t.CoinRow(0f, 4f, 0.5f, 4);
            t.CoinArc(5f, 11f, 0.6f, 1.6f, 4);           // past the pond's arched bridge
            t.Checkpoint(14f);
            t.Pedestrian(18f, 28f, CoatBeige, 0f, 0.8f);   // a worshipper off the steps
            t.CoinRow(28f, 34f, 0.5f, 4);
            t.Checkpoint(40f);
            t.Crossing(48.8f, 53.2f);                      // the zebra crossing over the side road
            t.CoinRow(55f, 60f, 0.5f, 4);
            t.Goal(70f);
        }

        /// <summary>
        /// KM2-1 Down to Yuigahama (dribble): out of the home's gate along the surfers' lane (KM2-1a, b), past the surf shop at
        /// the embankment (c), a Shiba on its patch before the coast road, through the dim tunnel under it (d: DarkZone), out
        /// to the surf hut and onto the boardwalk (e): the stop.
        /// </summary>
        public static void DownToYuigahama(TrackBuilder t)
        {
            t.Walls(-8f, 132f);
            t.Start(0f);
            t.Ground(-8f, 132f);
            t.KmModel("KmLetterbox", -10f, 1.15f);
            t.KmModel("KmPotPinkFlowers", -14.8f, 1.1f);
            t.KmModel("KmBonsaiTerracotta", -9.2f, 1.1f);
            t.KmLane("KM2-1", -6f);

            t.CoinRow(2f, 7f, 0.5f, 4);
            t.Checkpoint(20f);
            t.Pedestrian(28f, 40f, CoatGreen, 0f, 0.9f);   // a neighbour with a surfboard
            t.CoinArc(42f, 46f, 0.6f, 1.3f, 3);
            t.Checkpoint(50f);
            t.CoinRow(55f, 61f, 0.5f, 4);
            t.Dog(70f, 80f, ShibaTan);                     // the Shiba on its patch: chip the ball over
            t.Checkpoint(84f);
            t.Tunnel(86.5f, 95.5f);                        // under the coast road, dark inside
            t.CoinRow(87.5f, 94.5f, 0.5f, 5);
            t.Checkpoint(100f);
            t.CoinArc(108f, 112f, 0.6f, 1.3f, 3);
            t.Goal(124f);
        }

        /// <summary>
        /// KM2-2 Yuigahama Morning (dribble, on the sand): past the surfboards stuck in the sand (KM2-2a) as the tide washes up
        /// over the path, the fishing boats on their rollers (b), the gulls, the lifeguard tower and the litter sacks (c), along
        /// the sea wall (d) and up to the beach road and Grandma's shop (e): the stop.
        /// </summary>
        public static void YuigahamaMorning(TrackBuilder t)
        {
            t.Walls(-8f, 122f);
            t.Start(0f);
            t.Ground(-8f, 122f);
            t.KmLane("KM2-2", -16f);

            t.CoinRow(0f, 3f, 0.5f, 3);
            t.Tide(4f, 16f, 6f, 0f);                       // the wave washes up over the path: wait for it, or run
            t.Seagull(16f, 30f, 2.6f);
            t.Tide(22f, 34f, 6f, 2.5f);
            t.CoinArc(17f, 21f, 0.6f, 1.4f, 3);
            t.Checkpoint(36f);
            t.Seagull(48f, 62f, 2.8f, 1.2f);
            t.CoinRow(46f, 52f, 0.5f, 4);
            t.Checkpoint(66f);
            t.CoinRow(70f, 80f, 0.5f, 6);
            t.Checkpoint(92f);
            t.CoinArc(96f, 100f, 0.6f, 1.3f, 3);
            t.Goal(113f);
        }

        /// <summary>
        /// KM2-3 Grandma's Whitebait Shop (mini-game M2): the beach road's frontage as the photographic KM2-3 has it
        /// (tools/blender/km_whitebait.py: the neighbour's houses and their pots, the drying rack, Grandma's shop, the fish boxes,
        /// the scooter, the low sea wall's steps), the errand at her counter (TrackBuilder.ErrandCounter: MiniGames/BentoErrand),
        /// then on past the steps to the promenade: the stop (the lifeguard tower's). The bento then rides on the backpack.
        /// </summary>
        public static void GrandmasShop(TrackBuilder t)
        {
            t.Walls(-8f, 22f);
            t.Start(0f);
            t.Ground(-8f, 22f);
            const float dx = 2f;                            // the shop's middle at x 2: the kid walks up to it
            t.KmModel("KmShopPines", -5.09f + dx, 9f);
            t.KmModel("KmPromenadeView", 6.34f + dx, 5.6f);
            t.KmModel("KmShopNeighbour", -6.28f + dx, 2f);
            t.KmModel("KmPotPinkFlowers", -8.57f + dx, 1.7f);
            t.KmModel("KmHydrangeaPlanter", -8.01f + dx, 1.7f);
            t.KmModel("KmHydrangeaPlanter", -7.47f + dx, 1.7f);
            t.KmModel("KmHydrangeaPlanter", -6.77f + dx, 1.7f);
            t.KmModel("KmPotWhiteDaisies", -6.29f + dx, 1.7f);
            t.KmModel("KmBonsaiBlueBowl", -5.75f + dx, 1.7f);
            t.KmModel("KmHydrangeaPlanter", -5.09f + dx, 1.7f);
            t.KmModel("KmPoleTransformer", -4.47f + dx, 1.7f);
            t.KmModel("KmDryingRack", -2.28f + dx, 1.2f);
            t.KmModel("KmGrandmaShop", 0f + dx, 2f);
            t.KmModel("KmFishBoxes", 2.47f + dx, 2f);
            t.KmModel("KmCrates", 3.1f + dx, 2f);
            t.KmModel("KmScooter", 4.23f + dx, 1.3f);
            t.KmModel("KmSeaWallSteps", 7.4f + dx, 2.3f);
            t.KmModel("KmNoParkingSign", 7.66f + dx, 1.2f);
            t.KmModel("KmBusStopSign", 8.56f + dx, 1.2f);

            t.CoinRow(-6f, -1f, 0.5f, 4);
            t.ErrandCounter(0f + dx);
            t.BentoOnBack();
            t.Checkpoint(7f);
            t.CoinArc(8f, 11f, 0.6f, 1.2f, 3);
            t.Goal(15f);
        }

        /// <summary>
        /// KM2-4 The Kite Thief (twist M4): from the beach's end (KM2-4a) over the rock shelves (b) to the tide pools (c), where
        /// a black kite takes the rice ball off the bento and drops it on the rocks behind (TrackBuilder.KiteThief: back for it
        /// before the wave), then on under the leaning pine (d) to the great wooden torii (e): the stop.
        /// </summary>
        public static void KiteThief(TrackBuilder t)
        {
            t.Walls(-8f, 122f);
            t.Start(0f);
            t.Ground(-8f, 122f);
            t.KmLane("KM2-4", -16f);

            t.CoinRow(1f, 6f, 0.5f, 4);
            t.Checkpoint(20f);
            t.CoinArc(24f, 28f, 0.6f, 1.4f, 3);
            t.CoinRow(30f, 36f, 0.5f, 4);
            t.KiteThief(56f, 40f);
            t.BentoOnBack();
            t.Checkpoint(62f);
            t.Seagull(70f, 84f, 2.8f);                     // gulls over the waves
            t.CoinRow(72f, 78f, 0.5f, 4);
            t.Checkpoint(90f);
            t.CoinArc(96f, 100f, 0.6f, 1.3f, 3);
            t.Goal(110f);
        }

        /// <summary>
        /// KM2-5 Wakamiya-oji (dribble): up the avenue from the beach along the raised path between the stone lanterns (KM2-5a),
        /// past the bakery and the vending machines (b), the pottery and sweets shops and the side road (c), the crossing
        /// with the volunteer's yellow flag (d; M5), under the red torii to the school's gate (e): school. The bento delivered.
        /// </summary>
        public static void WakamiyaOji(TrackBuilder t)
        {
            t.Walls(-8f, 124f);
            t.Start(0f);
            t.Ground(-8f, 124f);
            t.KmLane("KM2-5", -16f);

            t.CoinRow(0f, 5f, 0.5f, 4);
            t.Checkpoint(12f);
            t.Pedestrian(18f, 30f, CoatBeige, 0f, 0.9f);   // shops waking up
            t.CoinArc(31f, 35f, 0.6f, 1.3f, 3);
            t.Checkpoint(38f);
            t.Pedestrian(42f, 54f, CoatNavy, 0f, 1f);
            t.Crossing(61.2f, 64.8f, 1.5f);                // the side road
            t.Checkpoint(68f);
            t.Crossing(76.2f, 82.6f);                      // the crossing volunteer's flag
            t.CoinRow(84f, 90f, 0.5f, 4);
            t.Checkpoint(92f);
            t.BentoOnBack();
            t.CoinArc(100f, 104f, 0.6f, 1.3f, 3);
            t.Goal(114.5f);
        }

        /// <summary>
        /// KM3-1 Hydrangea Steps (dribble, in the June rain): out of the home's gate to the temple's back gate (KM3-1a), along
        /// the stone steps between the banks of hydrangeas (b), puddles in the worn stones, umbrellas, the stone lantern (c),
        /// the rest hut (d), into the cedars to the trail sign (e): the stop.
        /// </summary>
        public static void HydrangeaSteps(TrackBuilder t)
        {
            t.Walls(-8f, 132f);
            t.Start(0f);
            t.Ground(-8f, 132f);
            t.KmModel("KmLetterbox", -10f, 1.15f);
            t.KmModel("KmHydrangeaBlue", -16.2f, 1.3f);
            t.KmLane("KM3-1", -6f);

            t.CoinRow(2f, 6f, 0.5f, 4);
            t.Puddle(8f, 10f);
            t.Checkpoint(22f);
            t.Puddle(30f, 32.5f);
            t.Pedestrian(36f, 46f, UmbrellaBlue, 0f, 0.7f);
            t.CoinArc(47f, 51f, 0.6f, 1.3f, 3);
            t.Checkpoint(52f);
            t.Puddle(58f, 60f);
            t.Pedestrian(64f, 74f, UmbrellaRose, 0f, 0.8f);
            t.Checkpoint(80f);
            t.CoinRow(82f, 88f, 0.5f, 4);
            t.Checkpoint(105f);
            t.Puddle(110f, 112.5f);
            t.CoinArc(116f, 120f, 0.6f, 1.3f, 3);
            t.Goal(127f);
        }

        /// <summary>
        /// KM3-2 The Hiking Trail (dribble, in the rain): over the wooded ridge, tree roots across the path (KM3-2a), the
        /// footbridge over the gully (b), the cave tomb cut in the rock (c) and a raccoon dog crossing, the rail fence (d), out
        /// into Genjiyama park by its bench and sign (e): the stop.
        /// </summary>
        public static void HikingTrail(TrackBuilder t)
        {
            t.Walls(-8f, 122f);
            t.Start(0f);
            t.Ground(-8f, 122f);
            t.KmLane("KM3-2", -16f);

            t.CoinRow(0f, 3f, 0.5f, 3);
            t.Wall(5f, 0.25f, 0f, 0.5f);                    // a root across the path
            t.Puddle(8f, 10.5f);
            t.Checkpoint(14f);
            t.CoinArc(16f, 24f, 0.6f, 1.6f, 5);           // over the footbridge
            t.Wall(30f, 0.3f, 0f, 0.5f);
            t.Checkpoint(36f);
            t.Puddle(40f, 42f);
            t.Dog(56f, 64f, TanukiBrown);                  // the raccoon dog crossing the path
            t.Checkpoint(68f);
            t.Wall(72f, 0.25f, 0f, 0.5f);
            t.CoinRow(76f, 82f, 0.5f, 4);
            t.Checkpoint(92f);
            t.Puddle(96f, 98f);
            t.CoinArc(100f, 104f, 0.6f, 1.3f, 3);
            t.Goal(112f);
        }

        /// <summary>
        /// KM3-3 Genjiyama Down to School (dribble, in the rain): across the park's lawn by the statue (KM3-3a), past the temple
        /// bell rung for the morning (b: its boom shakes the drops loose, a gust to time), through the bamboo grove creaking in
        /// the wind (c), down the stone steps (d) to the school's gate (e): school.
        /// </summary>
        public static void GenjiyamaToSchool(TrackBuilder t)
        {
            t.Walls(-8f, 124f);
            t.Start(0f);
            t.Ground(-8f, 124f);
            t.KmLane("KM3-3", -16f);

            t.CoinRow(0f, 5f, 0.5f, 4);
            t.Checkpoint(10f);
            t.Wind(13f, 23f, 0f, 4f, new Vector2(-5f, 0f), 3f);    // the bell's boom: a gust to time
            t.CoinArc(14f, 22f, 0.6f, 1.5f, 4);
            t.Checkpoint(26f);
            t.Wind(40f, 64f, 0f, 4f, new Vector2(-3.5f, 0f), 2.4f); // the wind in the bamboo
            t.CoinRow(44f, 60f, 0.5f, 6);
            t.Checkpoint(66f);
            t.Puddle(70f, 72f);
            t.CoinRow(76f, 84f, 0.5f, 4);
            t.Checkpoint(90f);
            t.Puddle(96f, 98f);
            t.CoinArc(100f, 104f, 0.6f, 1.3f, 3);
            t.Goal(114f);
        }

        /// <summary>A house still to come from the lane pictures: its walls, and its roof a darker slab over them.</summary>
        static void HouseStandIn(TrackBuilder t, float x, float front, float width, Color walls)
        {
            t.KmStandIn("HouseToCome", x, front, width, 7f, 5.6f, walls);
            t.KmStandIn("HouseToComeRoof", x, front - 0.4f, width + 0.8f, 7.8f, 1.2f, Tiles, false, 5.6f);
        }
    }
}
