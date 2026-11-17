using System.Collections.Generic;
using DribbleToSchool.Art;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's lane (the original town's first level, L01, while <see cref="LevelBuildKit.KamakuraLane"/> is set), after the
    /// user's KM1-1 lane pictures: the Kamakura kit's houses in the kit's own look (the old wooden home, the wooden house with
    /// its big windows, the beige stucco house, the newer white house with its carport, the rice shop) behind block walls,
    /// dark board fences and bamboo fences; the next streets over in the same houses; and Kamakura's trees everywhere a tree
    /// is planted (<see cref="KamakuraTree"/>: black pines, ginkgos, persimmons, cherries, the clipped garden pines). The set
    /// pieces (the vending corner, the shrine, the level crossing) are the layout's (LevelBuildKit.Kamakura).
    /// </summary>
    public static partial class StreetBuilder
    {
        static bool KM { get { return LevelBuildKit.KamakuraLane; } }

        /// <summary>The lane's houses, dealt along it (the rice shop at most once a street, by its own draw).</summary>
        static readonly string[] KamakuraHouses = { "HouseKM", "HomeOldKM", "HouseWoodKM", "HouseWhiteKM", "HouseKM", "HouseWoodKM" };
        /// <summary>The houses behind and in the next street over.</summary>
        static readonly string[] KamakuraBackHouses = { "HouseKM", "HouseWoodKM", "HouseWhiteKM", "HomeOldKM", "HouseKM", "HouseWhiteKM" };
        /// <summary>Kamakura's trees for the gardens and the bands behind.</summary>
        static readonly string[] KamakuraTrees = { "BlackPine", "Ginkgo", "Persimmon", "BlackPine", "CherryBlossom", "Ginkgo" };

        /// <summary>Every Kamakura kit model the lane and its set pieces place (KamakuraKitTests checks the kit has them).</summary>
        public static readonly string[] KamakuraModelsUsed =
        {
            "HouseKM", "HomeOldKM", "HouseWoodKM", "HouseWhiteKM", "RiceShopKM", "CarportKM", "FenceBoardKM", "FenceBambooKM",
            "ShrineKM", "ToriiKM", "RecycleKM", "MirrorKM", "CrossingSignalKM", "CrossingBarrierKM", "CrossingArmKM",
            "CrossingArmRoadKM", "TramKM", "StationSignKM", "TicketGateKM",
        };

        /// <summary>The Plants kit's trees the lane plants (KamakuraKitTests).</summary>
        public static readonly string[] KamakuraPlantsUsed = { "BlackPine", "Ginkgo", "Persimmon", "CherryBlossom", "GardenPine" };

        // Each house's own range of paint (walls, door, roof), so the lane isn't one house repeated: the stucco in beige, white,
        // grey-blue and cream; the boards in their dark browns; the white house's metal roof in grey, blue-grey or brown.
        static readonly Color[] KmStucco = { new Color(0.91f, 0.85f, 0.72f), new Color(0.95f, 0.94f, 0.91f), new Color(0.82f, 0.85f, 0.86f), new Color(0.93f, 0.88f, 0.78f) };
        static readonly Color[] KmDoors = { new Color(0.40f, 0.30f, 0.24f), new Color(0.30f, 0.32f, 0.36f), new Color(0.55f, 0.28f, 0.22f), new Color(0.42f, 0.34f, 0.28f) };
        static readonly Color[] KmBoards = { new Color(0.34f, 0.25f, 0.19f), new Color(0.30f, 0.23f, 0.18f), new Color(0.40f, 0.30f, 0.22f), new Color(0.36f, 0.29f, 0.24f) };
        static readonly Color[] KmWhite = { new Color(0.95f, 0.95f, 0.93f), new Color(0.88f, 0.88f, 0.86f), new Color(0.90f, 0.87f, 0.82f) };
        static readonly Color[] KmMetal = { new Color(0.30f, 0.31f, 0.33f), new Color(0.26f, 0.33f, 0.40f), new Color(0.40f, 0.26f, 0.22f) };

        /// <summary>
        /// Kamakura's tree in place of a generic one (none of the lane's trees is a broadleaf of the north or a fir): the
        /// broadleaf trees become ginkgos, black pines, persimmons and cherries, the conifers black pines (a small one a clipped
        /// garden pine), the birch a persimmon. Chosen by the tree's place, so the street's own draws are untouched.
        /// </summary>
        static string KamakuraTree(string model, float x, float z)
        {
            if (!KM) return model;
            int h = Scramble(Mathf.Abs(Mathf.RoundToInt(x * 7f + z * 13f)) + 31);
            switch (model)
            {
                case "Broadleaf": case "BroadleafLarge": case "BroadleafWide": case "BroadleafSmall": case "BroadleafYoung":
                    return KamakuraTrees[h % KamakuraTrees.Length];
                case "ConiferTall": case "ConiferMid": return "BlackPine";
                case "ConiferSmall": return "GardenPine";
                case "Birch": return "Persimmon";
                default: return model;
            }
        }

        /// <summary>A Kamakura house with its front wall on z, in its own range of paint; its half-width (0 if the kit hasn't it).</summary>
        static float KmHouse(Transform root, string model, float x, float gy, float z, System.Random rng)
        {
            Color? wall = null, door = null, roof = null;
            switch (model)
            {
                case "HouseKM": wall = KmStucco[rng.Next(KmStucco.Length)]; door = KmDoors[rng.Next(KmDoors.Length)]; break;
                case "HomeOldKM": case "HouseWoodKM": wall = KmBoards[rng.Next(KmBoards.Length)]; break;
                case "HouseWhiteKM": wall = KmWhite[rng.Next(KmWhite.Length)]; roof = KmMetal[rng.Next(KmMetal.Length)]; break;
            }
            float w = LevelBuildKit.KitSize("Kamakura", model).x;
            if (w < 1f || Model(root, "Kamakura", model, x, gy, z, 0f, 1f, wall, door, roof) == null) return 0f;
            ContactShadow(root, x - w * 0.5f, x + w * 0.5f, gy, z - 0.45f, z);
            return w * 0.5f;
        }

        /// <summary>How far back a Kamakura house's front wall stands: its porch, steps or balcony clear of the lot's wall.</summary>
        static float KmSetback(string model, System.Random rng)
        {
            float forward = -LevelBuildKit.KitMin("Kamakura", model).z;
            return PropertyZ + 1.2f + Mathf.Max(0f, forward) + Rand(rng, 0f, 1f);
        }

        /// <summary>
        /// The lane's lots (the suburb's, StreetBuilder.Suburb, in Kamakura's look): a block wall with its gate, or a dark board
        /// fence, or a bamboo fence along the front; the house (the white one with its carport beside it when the lot has room);
        /// pots or a bicycle at the gate; a pine or a persimmon in the side yard; a tree over the roof. Then the row behind.
        /// </summary>
        static void KamakuraSuburb(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            var wallMat = Art.surfaces[ProceduralArt.Surface.BlockWall];
            var houses = new Deck(KamakuraHouses, rng);
            bool riceShop = false;
            for (float x = x0; x < x1;)
            {
                float lot = NextLot(track, rng, x, x1, 9.5f, 13f), skip;
                if (Blocked(track, x, x + lot, out skip)) { FillGap(track, root, rng, x, BlockStart(track, x, x + lot)); x = skip; continue; }
                if (LotEndsAtStep(track, root, rng, ref x, ref lot, 7.5f)) continue;
                float cx = x + lot * 0.5f, gy = GroundAt(track, cx);

                // The front: mostly block walls (their pierced blocks and pillars), else a dark board fence or a bamboo one.
                float gate = Rand(rng, x + 2f, x + lot - 4f);
                double front = rng.NextDouble();
                if (front < 0.55)
                {
                    BlockWall(root, x + 0.1f, gate, gy, wallMat, true, true);
                    BlockWall(root, gate + 2.2f, x + lot - 0.1f, gy, wallMat, true, false);
                }
                else
                {
                    string fence = front < 0.8 ? "FenceBoardKM" : "FenceBambooKM";
                    ContactShadow(root, x + 0.1f, x + lot - 0.1f, gy, PropertyZ - 0.25f, PropertyZ + 0.02f);
                    if (gate - x > 1.2f) Row(root, "Kamakura", fence, x + 0.1f, gate, gy, PropertyZ + 0.15f);
                    if (x + lot - gate > 2.8f) Row(root, "Kamakura", fence, gate + 1.6f, x + lot - 0.1f, gy, PropertyZ + 0.15f);
                }
                double life = rng.NextDouble();
                if (life < 0.22 && gate - x > 3.4f) Model(root, "Street", "Bicycle", Rand(rng, x + 1.2f, gate - 1f), gy, PropertyZ - 0.32f, 180f + Rand(rng, -6f, 6f), 1f, BikeColors[rng.Next(BikeColors.Length)]);
                else if (life < 0.6) Model(root, "Street", "PotGroup", gate + 0.55f, gy, PropertyZ + 0.6f, Rand(rng, -20f, 20f), 1f, Petals[rng.Next(Petals.Length)]);

                // The house: the rice shop once in a while (never twice), else the next of the lane's that fits the lot.
                string house = null;
                if (!riceShop && rng.NextDouble() < 0.2 && LevelBuildKit.KitSize("Kamakura", "RiceShopKM").x <= lot - 0.8f) { house = "RiceShopKM"; riceShop = true; }
                if (house == null) house = houses.Next(m => LevelBuildKit.KitSize("Kamakura", m).x <= lot - 0.8f);
                if (house == null) { FillGap(track, root, rng, x, x + lot); x += lot; continue; }
                float z = KmSetback(house, rng);
                float half = KmHouse(root, house, cx, gy, z, rng);
                if (house == "HouseWhiteKM" && x + lot - (cx + half) > 3.3f)
                    Model(root, "Kamakura", "CarportKM", cx + half + 1.65f, gy, z + 0.4f);

                // Trees: one in the back garden over the roof, a pine or a persimmon in the side yard if there's room.
                if (rng.NextDouble() < 0.75)
                    Plant(root, KamakuraTrees[rng.Next(KamakuraTrees.Length)], null, cx + Rand(rng, -half, half), gy, z + 9f + Rand(rng, 0f, 3f), Rand(rng, 0.85f, 1.15f), 1f, -70, rng);
                float gap = (cx - half) - x;
                if (gap > 1.8f && rng.NextDouble() < 0.6)
                    Plant(root, rng.NextDouble() < 0.6 ? "GardenPine" : "Persimmon", null, x + gap * 0.5f, gy, PropertyZ + 1.4f + Rand(rng, 0f, 1.2f), Rand(rng, 0.7f, 0.9f), 1f, -60, rng);
                x += lot;
            }
            // The row behind (never on a side street or the railway).
            var back = new Deck(KamakuraBackHouses, rng);
            for (float x = Lo(x0, 20f); x < Hi(x1, 20f); x += Rand(rng, 11f, 14f))
            {
                string house = back.Next(m => true);
                if (house == null) break;
                float half = LevelBuildKit.KitSize("Kamakura", house).x * 0.5f + 0.3f;
                if (OverlapsBackRow(track, x - half, x + half)) continue;
                KmHouse(root, house, x, GroundAt(track, x), Rand(rng, 20f, 24f), rng);
            }
            DistantHills(track, root, x0, x1);
        }

        /// <summary>The depth behind Kamakura's lane: a band of its trees, the next street over in its houses, a far band of trees.</summary>
        static void KamakuraDepth(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            TreeBand(track, root, rng, x0, x1, 30f, 37f, KamakuraTrees, 4.5f, 8f);
            var deck = new Deck(KamakuraBackHouses, rng);
            for (float x = Lo(x0, 40f); x < Hi(x1, 40f); x += Rand(rng, 12f, 16f))
            {
                string house = deck.Next(m => true);
                if (house == null) break;
                float half = LevelBuildKit.KitSize("Kamakura", house).x * 0.5f + 0.3f;
                if (OnSideStreetRange(track, x - half, x + half)) continue;
                KmHouse(root, house, x, GroundAt(track, x), Rand(rng, 40f, 46f), rng);
            }
            TreeBand(track, root, rng, x0, x1, 56f, 70f, KamakuraTrees, 4f, 8f);
        }

        /// <summary>Does [a, b] run over the railway (no building stands on its track or its platform, front or back)?</summary>
        static bool OnRailway(LevelBuildKit.TrackBuilder track, float a, float b)
        {
            foreach (var area in track.Railways)
                if (b > area.x - 0.6f && a < area.y + 0.6f) return true;
            return false;
        }
    }
}
