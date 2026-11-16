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

        /// <summary>A house still to come from the lane pictures: its walls, and its roof a darker slab over them.</summary>
        static void HouseStandIn(TrackBuilder t, float x, float front, float width, Color walls)
        {
            t.KmStandIn("HouseToCome", x, front, width, 7f, 5.6f, walls);
            t.KmStandIn("HouseToComeRoof", x, front - 0.4f, width + 0.8f, 7.8f, 1.2f, Tiles, false, 5.6f);
        }
    }
}
