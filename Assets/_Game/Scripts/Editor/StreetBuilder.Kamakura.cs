using System.Collections.Generic;
using DribbleToSchool.Art;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's own look (the user's brief, docs/KAMAKURA_BRIEF.md): the original town's chapters dressed as the Shonan coast's
    /// seaside temple town rather than a generic one. Its homes are the Kamakura kit's two-storey timber-and-mortar houses under
    /// grey kawara or dark metal roofs, behind concrete block walls, dark-stained board fences and hedges, with tiny front gardens
    /// of pots; its shops have noren, wooden signboards and lanterns; its temples and shrines, street things, tram and little
    /// vehicles are the KamakuraStreet kit's; its trees are Japan's (black pines by the sea, camphors and cedars on the hills,
    /// cherries in full green leaf, bamboo, hydrangeas, azaleas, a persimmon); its birds the black kites over the beach and the
    /// crows. Every choice falls back to the original town's model where the new one isn't there, so a build without the new kits
    /// is the town as it was. Florida's and the old California skin's streets never see any of it.
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>Every model Kamakura's look places, by kit (the tests check each kit has them).</summary>
        public static readonly string[] KamakuraModelsUsed =
        {
            "HouseTileKM", "HouseMetalKM", "HouseOldKM", "HouseShedKM", "HouseCarportKM", "BungalowKM", "ApartmentKM", "BoardFenceKM",
            "BlockWallKM", "GateKM", "ShopSembeiKM", "ShopSobaKM", "ShopWagashiKM", "ShopSouvenirKM", "ShopFishKM", "ShopKissaKM",
            "ShopTeaKM", "NoboriKM",
        };
        public static readonly string[] KamakuraStreetModelsUsed =
        {
            "ToriiKM", "TempleGateKM", "StoneLanternKM", "StoneStepsKM", "MossWallKM", "EmaRackKM", "ShrineHallKM", "PhoneBoothKM",
            "VendingKM", "VendingKM2", "PotShelfKM", "LaundryPoleKM", "CorrugatedShedKM", "TramKM", "TramPoleKM", "CrossingSignalKM",
            "CrossingBarKM", "TrackKM", "KeiCarKM", "ScooterKM",
        };
        public static readonly string[] KamakuraPlantsUsed = { "BlackPine", "Camphor", "Cedar", "CherryLeaf", "Bamboo", "Hydrangea", "Azalea", "Persimmon", "GardenPine" };
        public static readonly string[] KamakuraAnimalsUsed = { "BlackKite", "Crow" };

        /// <summary>Kamakura's own look is on: the original town's streets (not Florida's) with the Kamakura kit imported.</summary>
        public static bool KM
        {
            get { return !LevelBuildKit.Florida && !CA && LevelBuildKit.HasKitModel("Kamakura", "HouseTileKM"); }
        }

        /// <summary>The kit a Kamakura model is in: its homes and shops in Kamakura, its street things in KamakuraStreet.</summary>
        static string KamakuraKitOf(string model)
        {
            if (LevelBuildKit.HasKitModel("Kamakura", model)) return "Kamakura";
            if (LevelBuildKit.HasKitModel("KamakuraStreet", model)) return "KamakuraStreet";
            return "Kamakura";
        }

        /// <summary>The models of <paramref name="wanted"/> that are there (in their kit), else <paramref name="fallback"/>.</summary>
        static string[] Have(string kit, string[] wanted, string[] fallback)
        {
            var list = new List<string>();
            foreach (var m in wanted)
                if (LevelBuildKit.HasKitModel(kit, m)) list.Add(m);
            return list.Count > 0 ? list.ToArray() : fallback;
        }

        // ---------------------------------------------------------------- the homes

        static readonly string[] HomeHousesKMWanted = { "HouseTileKM", "HouseMetalKM", "HouseOldKM", "HouseShedKM", "HouseCarportKM", "BungalowKM", "ApartmentKM" };
        static string[] HomeHousesKM { get { return Have("Kamakura", HomeHousesKMWanted, HomeHousesTown); } }
        static string[] BackRowKM { get { return Have("Kamakura", new[] { "HouseTileKM", "HouseMetalKM", "HouseOldKM", "ApartmentKM", "HouseShedKM" }, null); } }

        /// <summary>Kamakura's walls: beige and white mortar, salt-bloomed grey, a pale sand.</summary>
        static readonly Color[] KMWalls =
        {
            new Color(0.86f, 0.8f, 0.68f), new Color(0.92f, 0.91f, 0.88f), new Color(0.78f, 0.77f, 0.74f), new Color(0.88f, 0.84f, 0.76f),
        };

        static bool IsKM(string model) { return model != null && model.EndsWith("KM"); }

        /// <summary>A Kamakura home with its front wall on z (its walls in one of Kamakura's mortars), and its contact shadow.</summary>
        static bool KamakuraHouse(Transform root, string model, float x, float gy, float z)
        {
            float w = LevelBuildKit.KitSize("Kamakura", model).x;
            Color wall = KMWalls[Scramble(Mathf.Abs(Mathf.RoundToInt(x * 7f + z * 13f)) + 5) % KMWalls.Length];
            if (w < 1f || Model(root, "Kamakura", model, x, gy, z, 0f, 1f, wall) == null) return false;
            ContactShadow(root, x - w * 0.5f, x + w * 0.5f, gy, z - 0.45f, z);
            return true;
        }

        /// <summary>
        /// A Kamakura lot's front: a concrete block wall, a dark-stained board fence or a hedge, with its gate; false where the
        /// Kamakura kit hasn't got them (the town's block wall then).
        /// </summary>
        static bool KamakuraFront(Transform root, System.Random rng, float a, float gate, float b, float gy)
        {
            if (!LevelBuildKit.HasKitModel("Kamakura", "BlockWallKM")) return false;
            double f = rng.NextDouble();
            string wall = f < 0.55 ? "BlockWallKM" : f < 0.85 && LevelBuildKit.HasKitModel("Kamakura", "BoardFenceKM") ? "BoardFenceKM" : null;
            ContactShadow(root, a, b, gy, PropertyZ - 0.3f, PropertyZ + 0.02f);
            if (wall == null)
            {
                if (gate - a > 1.6f) Row(root, "Plants", "HedgeBlock2", a + 0.2f, gate - 0.2f, gy, PropertyZ + 0.4f, HedgeGreen);
                if (b - gate > 3.6f) Row(root, "Plants", "HedgeBlock2", gate + 1.6f, b - 0.2f, gy, PropertyZ + 0.4f, HedgeGreen);
            }
            else
            {
                if (gate - a > 0.6f) Row(root, "Kamakura", wall, a, gate, gy, PropertyZ + 0.15f);
                if (b - gate > 2.4f) Row(root, "Kamakura", wall, gate + 1.8f, b, gy, PropertyZ + 0.15f);
                wallTops.Add(new Vector3(a + 0.4f, gate - 0.4f, gy + (wall == "BlockWallKM" ? 1.2f : 1.8f)));
            }
            Model(root, "Kamakura", "GateKM", gate + 0.9f, gy, PropertyZ + 0.15f);
            return true;
        }

        /// <summary>
        /// The life at a Kamakura gate and in its front garden: a stand of pots and bonsai with a morning glory, a laundry pole
        /// in the yard, a bicycle, a corrugated shed beside the house.
        /// </summary>
        static void KamakuraGarden(Transform root, System.Random rng, float x, float lot, float gate, float gy, float houseZ, float houseHalf, float cx)
        {
            double d = rng.NextDouble();
            if (d < 0.6) Model(root, "KamakuraStreet", "PotShelfKM", gate + 0.9f + Rand(rng, -0.3f, 0.3f), gy, PropertyZ + 0.75f, Rand(rng, -8f, 8f));
            float yard = x + lot - (cx + houseHalf);
            if (yard > 2.6f && rng.NextDouble() < 0.5)
                Model(root, "KamakuraStreet", rng.NextDouble() < 0.5 ? "LaundryPoleKM" : "CorrugatedShedKM", x + lot - yard * 0.5f, gy, houseZ + 1.2f, Rand(rng, -5f, 5f));
            float side = (cx - houseHalf) - x;
            if (side > 2.2f && rng.NextDouble() < 0.5)
                Plant(root, rng.NextDouble() < 0.5 ? "Hydrangea" : "Azalea", null, x + side * 0.5f, gy, PropertyZ + 0.9f, Rand(rng, 0.9f, 1.2f), 1f, -60, rng);
        }

        /// <summary>Back-garden trees over the roofs: a persimmon, cherries in leaf, a camphor, a black pine, bamboo.</summary>
        static string[] KMBackTrees { get { return Have("Plants", new[] { "Persimmon", "CherryLeaf", "Camphor", "BlackPine", "CherryLeaf", "Bamboo", "Persimmon" }, null); } }
        /// <summary>Side-yard plants: a garden pine, hydrangeas, an azalea, a little bamboo.</summary>
        static string[] KMSideTrees { get { return Have("Plants", new[] { "GardenPine", "Hydrangea", "Azalea", "Bamboo", "GardenPine", "Hydrangea" }, null); } }
        /// <summary>Woods and the hills' trees: camphors, cedars, black pines, cherries in leaf, bamboo.</summary>
        static string[] KMWoodTrees { get { return Have("Plants", new[] { "Camphor", "Cedar", "CherryLeaf", "Camphor", "BlackPine", "Cedar", "Bamboo" }, null); } }

        /// <summary>
        /// A painted facade's kind as one of Kamakura's own buildings (the far rows and the back rows): its houses, flats and
        /// shops; false for the kinds that stay the town's (the warehouse, the school) or without the kit.
        /// </summary>
        static bool KamakuraBuilding(Transform parent, float x, float gy, float z, ProceduralArt.FacadeKind facade, int seed)
        {
            string[] pick;
            switch (facade)
            {
                case ProceduralArt.FacadeKind.HouseGable: pick = new[] { "HouseTileKM", "HouseOldKM", "HouseShedKM" }; break;
                case ProceduralArt.FacadeKind.HouseLong: pick = new[] { "HouseMetalKM", "HouseCarportKM", "HouseTileKM" }; break;
                case ProceduralArt.FacadeKind.Bungalow: pick = new[] { "BungalowKM", "HouseOldKM" }; break;
                case ProceduralArt.FacadeKind.Apartment: pick = new[] { "ApartmentKM" }; break;
                case ProceduralArt.FacadeKind.Shop0:
                case ProceduralArt.FacadeKind.Shop1: pick = MarketFrontsKMWanted; break;
                default: return false;
            }
            string model = pick[Scramble(seed) % pick.Length];
            float width = LevelBuildKit.KitSize("Kamakura", model).x;
            if (width < 0.1f || !LevelBuildKit.HasKitModel("Kamakura", model)) return false;
            float scale = Mathf.Clamp(ProceduralArt.FacadeSize(facade).x / width, 0.85f, 1.15f);
            return Model(parent, "Kamakura", model, x, gy, z, 0f, scale, KMWalls[Scramble(seed + 3) % KMWalls.Length]) != null;
        }

        // ---------------------------------------------------------------- the shops

        static readonly string[] MarketFrontsKMWanted =
        {
            "ShopSembeiKM", "ShopSobaKM", "ShopWagashiKM", "ShopSouvenirKM", "ShopFishKM", "ShopKissaKM", "ShopTeaKM", "ShopSouvenirKM",
        };
        static string[] MarketFrontsKM
        {
            get
            {
                var shops = Have("Kamakura", MarketFrontsKMWanted, null);
                if (shops == null) return MarketFrontsTown;
                // (a convenience store too: Kamakura has them, and the town's is Japanese)
                var all = new List<string>(shops);
                if (LevelBuildKit.HasKitModel("Buildings", "ShopKonbini")) all.Add("ShopKonbini");
                return all.ToArray();
            }
        }

        /// <summary>A Kamakura shop at the back of the footpath, and what stands by it: a nobori banner, a drinks machine, a scooter, bicycles.</summary>
        static bool KamakuraShopFront(Transform root, System.Random rng, string model, float cx, float gy, float w)
        {
            float z = PropertyZ + 0.6f;
            if (Model(root, "Kamakura", model, cx, gy, z) == null) return false;
            ContactShadow(root, cx - w * 0.5f, cx + w * 0.5f, gy, z - 0.45f, z);
            double d = rng.NextDouble();
            if (d < 0.35) Model(root, "Kamakura", "NoboriKM", cx - w * 0.5f + 0.5f, gy, PropertyZ + 0.25f, Rand(rng, -10f, 10f));
            else if (d < 0.55) Model(root, "KamakuraStreet", rng.NextDouble() < 0.5 ? "VendingKM" : "VendingKM2", cx + w * 0.5f - 0.6f, gy, PropertyZ + 0.45f);
            else if (d < 0.7) Model(root, "KamakuraStreet", "ScooterKM", cx + w * 0.5f - 0.9f, gy, PropertyZ + 0.35f, 180f + Rand(rng, -6f, 6f));
            else if (d < 0.8) Model(root, "Street", "Bicycle", cx + Rand(rng, -1.5f, 1.5f), gy, PropertyZ + 0.3f, 180f + Rand(rng, -6f, 6f), 1f, BikeColors[rng.Next(BikeColors.Length)]);
            return true;
        }

        // ---------------------------------------------------------------- the temple grounds (the park and the school's surroundings)

        /// <summary>
        /// A temple ground's things behind the park's path, between x0 and x1: now and then a torii with stone lanterns either
        /// side and stone steps up behind it, a temple gate in the trees beyond, moss-covered stone walls, a rack of prayer
        /// plaques, a little shrine hall far back.
        /// </summary>
        static void KamakuraTempleGrounds(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, IEnumerable<Vector2> clearings)
        {
            if (!LevelBuildKit.HasKitModel("KamakuraStreet", "ToriiKM")) return;
            float skip;
            for (float x = Lo(x0, 10f) + Rand(rng, 10f, 30f); x < Hi(x1, 10f); x += Rand(rng, 45f, 70f))
            {
                if (Blocked(track, x - 6f, x + 6f, out skip)) continue;
                bool inClearing = false;
                foreach (var c in clearings) if (x + 13f > c.x && x - 13f < c.y) inClearing = true;
                if (inClearing) continue;
                float gy = GroundAt(track, x);
                Model(root, "KamakuraStreet", "ToriiKM", x, gy, PropertyZ + 2.2f);
                foreach (float s in new[] { -1f, 1f })
                    Model(root, "KamakuraStreet", "StoneLanternKM", x + s * 3.4f, gy, PropertyZ + 1.6f);
                Model(root, "KamakuraStreet", "StoneStepsKM", x, gy, PropertyZ + 3.4f);
                foreach (float s in new[] { -1f, 1f })
                    for (int k = 0; k < 2; k++)
                        Model(root, "KamakuraStreet", "MossWallKM", x + s * (5.4f + k * 4f), gy, PropertyZ + 3.9f);
                if (rng.NextDouble() < 0.6) Model(root, "KamakuraStreet", "TempleGateKM", x + Rand(rng, -2f, 2f), gy, Rand(rng, 14f, 18f));
                else Model(root, "KamakuraStreet", "ShrineHallKM", x + Rand(rng, -3f, 3f), gy, Rand(rng, 16f, 20f));
                if (rng.NextDouble() < 0.5) Model(root, "KamakuraStreet", "EmaRackKM", x + Rand(rng, 6f, 9f), gy, PropertyZ + 2.4f);
            }
        }

        // ---------------------------------------------------------------- the crows

        /// <summary>
        /// Jungle crows, everywhere in Kamakura: one or two on the garden walls' tops and the footpath's back edge, taking off when
        /// the kid runs at them (the Animals kit's Crow, flying on the black kite's wings painted black). Not on the beach.
        /// </summary>
        static void KamakuraCrows(LevelBuildKit.TrackBuilder track, System.Random rng, float x0, float x1, int chapter)
        {
            if (chapter == 3 || !LevelBuildKit.HasKitModel("Animals", "Crow") || !LevelBuildKit.HasKitModel("Animals", "BlackKite")) return;
            Color black = new Color(0.08f, 0.08f, 0.1f);
            float skip;
            for (float x = x0 + Rand(rng, 10f, 30f); x < x1; x += Rand(rng, 30f, 55f))
            {
                if (Blocked(track, x - 2f, x + 2f, out skip)) continue;
                Vector3 span;
                if (!SpanAt(track, x, out span)) continue;
                float z = Rand(rng, 1.1f, 1.4f);
                var crow = Bird("Crow", 1f, 0.75f, black, black, x, span.z, z, rng.NextDouble() < 0.5 ? Rand(rng, -20f, 20f) : 180f + Rand(rng, -20f, 20f), rng, "BlackKite");
                if (crow == null) continue;
                crow.roam = 0.6f;
                crow.zMin = 1.0f;
                crow.zMax = 1.45f;
                crow.walkSpeed = Rand(rng, 0.3f, 0.45f);
                crow.startle = Rand(rng, 2.6f, 3.6f);
                crow.flightSpeed = Rand(rng, 3.5f, 5f);
                crow.flightZMin = -0.9f;
                crow.flightZMax = -0.3f;
                float a = Mathf.Max(x - 0.7f, span.x + 0.25f), b = Mathf.Min(x + 0.7f, span.y - 0.25f);
                crow.ground = new[] { span.z, span.z };
                crow.groundFrom = Mathf.Min(a, x);
                crow.groundStep = Mathf.Max(0.01f, Mathf.Max(b, x) - crow.groundFrom);
            }
        }

        // ---------------------------------------------------------------- the tram (chapter 4: the station and the line)

        /// <summary>
        /// Kamakura's little tram line behind the street: the single track on its ballast, catenary poles every 30 m, and a
        /// two-car tram standing at it; level crossings' signals and bars where a side street crosses the line.
        /// </summary>
        static void KamakuraTramLine(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float z)
        {
            if (!LevelBuildKit.HasKitModel("KamakuraStreet", "TrackKM")) return;
            var line = new GameObject("TramLine").transform;
            line.SetParent(root, false);
            float a = Lo(x0, 20f), b = Hi(x1, 20f);
            Row(line, "KamakuraStreet", "TrackKM", a, b, GroundAt(track, (a + b) * 0.5f), z);
            for (float x = Mathf.Ceil(a / 30f) * 30f; x < b; x += 30f)
                Model(line, "KamakuraStreet", "TramPoleKM", x, GroundAt(track, x), z + 1.8f);   // (its bracket reaches 1.8 m over the track)
            if (rng.NextDouble() < 0.7)
            {
                float tx = a + (b - a) * Rand(rng, 0.25f, 0.75f);
                Model(line, "KamakuraStreet", "TramKM", tx, GroundAt(track, tx) + 0.32f, z);   // (on the rails: TrackKM's Attach.RailTop)
            }
        }

        /// <summary>A level crossing's warning signals and bars either side of a side street crossing the tram line at z.</summary>
        static void KamakuraLevelCrossing(Transform root, Vector2 area, float gy, float z)
        {
            if (!LevelBuildKit.HasKitModel("KamakuraStreet", "CrossingSignalKM")) return;
            Model(root, "KamakuraStreet", "CrossingSignalKM", area.x - 0.6f, gy, z - 1.6f);
            Model(root, "KamakuraStreet", "CrossingSignalKM", area.y + 0.6f, gy, z + 1.6f, 180f);
            Model(root, "KamakuraStreet", "CrossingBarKM", area.x - 0.3f, gy, z - 2.2f, -90f);
            Model(root, "KamakuraStreet", "CrossingBarKM", area.y + 0.3f, gy, z + 2.2f, 90f);
        }
    }
}
