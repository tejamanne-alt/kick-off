using System.Collections.Generic;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The California skin of the streets (the Coast kit, tools/blender/kit_buildings_cal.py), built
    /// into each level's California scene (LevelBuildKit.California) and only there: stucco
    /// villas under hipped terracotta roofs, single-storey ranch houses, Craftsman houses with deep
    /// front porches, white beach condos, beach-town shops, tall fan palms on the skyline and date
    /// palms along the streets, and a seaside pier on piles running out from the beach.
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>
        /// True while a level's California scene is being built: the streets take the Coast kit's
        /// houses, palms, hedges and pier. Otherwise every street is built exactly as before.
        /// </summary>
        static bool CA { get { return (LevelBuildKit.California || LevelBuildKit.Florida) && LevelBuildKit.HasKitModel("Coast", "VillaStucco"); } }

        /// <summary>The street's utility pole: wooden on a California street, the original concrete one otherwise.</summary>
        static string PoleModel { get { return CA && LevelBuildKit.HasKitModel("Street", "UtilityPoleWood") ? "UtilityPoleWood" : "UtilityPole"; } }

        /// <summary>The Coast kit's houses and shops.</summary>
        static readonly HashSet<string> CoastModels = new HashSet<string>
        {
            "VillaStucco", "VillaRanch", "CraftsmanPorch", "BeachCondo", "ShopBeach", "ShopMission", "PierSpan", "PierEnd",
        };

        /// <summary>The kit a building model lives in: the Coast kit's California models, else the Buildings kit.</summary>
        public static string KitOf(string model)
        {
            if (model != null && FloridaHouses.Contains(model)) return "Florida";
            return model != null && CoastModels.Contains(model) ? "Coast" : "Buildings";
        }

        /// <summary>
        /// How far a Coast house stands back from the usual garden depth, for what it puts in front of
        /// its front wall: the ranch's garage comes forward 0.9, the Craftsman's porch 2.7.
        /// </summary>
        static float CoastSetback(string model)
        {
            switch (model)
            {
                case "CraftsmanPorch": return 2.2f;
                case "VillaRanch": return 1.0f;
                case "VillaStucco": return 0.4f;
                case "CottageFL": return 2.3f;          // (Florida: the cottage's porch and steps, the ranch's steps)
                case "RanchFL": return 0.7f;
                case "RanchSmallFL": return 0.4f;
                case "BeachCondo": return 0.6f;
                default: return 0f;
            }
        }

        static readonly Color Terracotta = new Color(0.72f, 0.4f, 0.28f);

        // Paint schemes (wall, accent, roof), sRGB: the muted, sun-softened tones of real California
        // stucco under weathered clay; white, pale blue or putty siding over charcoal shingles for the
        // Craftsman houses. (The kit paints the weathering; these only set the colour.)
        static readonly Paint[] VillaPaints =
        {
            new Paint(new Color(0.87f, 0.81f, 0.7f), new Color(0.36f, 0.27f, 0.2f), Terracotta),                          // beige, walnut
            new Paint(new Color(0.84f, 0.77f, 0.66f), new Color(0.3f, 0.38f, 0.42f), new Color(0.66f, 0.36f, 0.26f)),      // tan, slate blue
            new Paint(new Color(0.9f, 0.87f, 0.8f), new Color(0.24f, 0.33f, 0.28f), new Color(0.74f, 0.44f, 0.31f)),       // warm white, green
            new Paint(new Color(0.86f, 0.76f, 0.66f), new Color(0.4f, 0.28f, 0.22f), new Color(0.68f, 0.38f, 0.28f)),      // sand peach
            new Paint(new Color(0.91f, 0.9f, 0.87f), new Color(0.2f, 0.25f, 0.32f), new Color(0.7f, 0.4f, 0.29f)),         // white, navy
            new Paint(new Color(0.8f, 0.76f, 0.68f), new Color(0.32f, 0.24f, 0.19f), new Color(0.62f, 0.36f, 0.27f)),      // greige
        };
        static readonly Paint[] CraftsmanPaints =
        {
            new Paint(new Color(0.92f, 0.92f, 0.9f), new Color(0.28f, 0.35f, 0.42f), new Color(0.32f, 0.33f, 0.36f)),      // white, slate
            new Paint(new Color(0.76f, 0.82f, 0.84f), new Color(0.56f, 0.2f, 0.18f), new Color(0.34f, 0.35f, 0.38f)),      // pale blue, red door
            new Paint(new Color(0.86f, 0.82f, 0.74f), new Color(0.22f, 0.33f, 0.28f), new Color(0.38f, 0.34f, 0.31f)),     // putty, green
            new Paint(new Color(0.78f, 0.76f, 0.68f), new Color(0.28f, 0.28f, 0.3f), new Color(0.31f, 0.31f, 0.34f)),      // sage grey
        };
        static readonly Paint[] CondoPaints =
        {
            new Paint(new Color(0.92f, 0.92f, 0.9f), new Color(0.36f, 0.5f, 0.58f), new Color(0.56f, 0.55f, 0.54f)),
            new Paint(new Color(0.88f, 0.86f, 0.81f), new Color(0.28f, 0.31f, 0.35f), new Color(0.56f, 0.55f, 0.54f)),
            new Paint(new Color(0.86f, 0.88f, 0.89f), new Color(0.22f, 0.42f, 0.5f), new Color(0.56f, 0.55f, 0.54f)),
        };
        static readonly Paint[] BeachShopPaints =
        {
            new Paint(new Color(0.9f, 0.85f, 0.75f), new Color(0.2f, 0.5f, 0.56f), new Color(0.56f, 0.55f, 0.54f)),       // teal awning
            new Paint(new Color(0.9f, 0.89f, 0.86f), new Color(0.8f, 0.38f, 0.28f), new Color(0.56f, 0.55f, 0.54f)),       // coral awning
            new Paint(new Color(0.87f, 0.8f, 0.66f), new Color(0.22f, 0.32f, 0.54f), new Color(0.56f, 0.55f, 0.54f)),      // navy awning
            new Paint(new Color(0.86f, 0.88f, 0.86f), new Color(0.88f, 0.66f, 0.2f), new Color(0.56f, 0.55f, 0.54f)),      // sunflower awning
        };
        static readonly Paint[] MissionPaints =
        {
            new Paint(new Color(0.88f, 0.82f, 0.72f), new Color(0.3f, 0.22f, 0.17f), Terracotta),
            new Paint(new Color(0.85f, 0.78f, 0.69f), new Color(0.22f, 0.28f, 0.24f), new Color(0.68f, 0.36f, 0.25f)),
            new Paint(new Color(0.9f, 0.88f, 0.83f), new Color(0.34f, 0.19f, 0.15f), new Color(0.74f, 0.42f, 0.29f)),
        };

        static Paint[] CoastPaints(string model)
        {
            switch (model)
            {
                case "CraftsmanPorch": return CraftsmanPaints;
                case "BeachCondo": return CondoPaints;
                case "ShopBeach": return BeachShopPaints;
                case "ShopMission": return MissionPaints;
                default: return VillaPaints;
            }
        }

        /// <summary>A Coast kit house or shop at (x, gy, z), painted from its schemes, with a contact shadow. False without the kit.</summary>
        static bool CoastHouse(Transform root, string model, float x, float gy, float z)
        {
            if (!LevelBuildKit.HasKitModel("Coast", model)) return false;
            var schemes = CoastPaints(model);
            var p = schemes[Scramble(Mathf.Abs(Mathf.RoundToInt(x * 7f + z * 13f))) % schemes.Length];
            if (Model(root, "Coast", model, x, gy, z, 0f, 1f, p.wall, p.trim, p.roof) == null) return false;
            float w = LevelBuildKit.KitSize("Coast", model).x;
            ContactShadow(root, x - w * 0.5f, x + w * 0.5f, gy, z - 0.45f, z);
            return true;
        }

        /// <summary>
        /// A row of Coast houses far back (zMin to zMax), across the whole level: the next street over,
        /// its hipped tile roofs and stucco walls showing between the trees.
        /// </summary>
        static void CoastFarRow(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float zMin, float zMax, params string[] models)
        {
            if (!LevelBuildKit.HasKitModel("Coast", "VillaStucco")) return;
            var deck = new Deck(models, rng);
            for (float x = Lo(x0, 40f); x < Hi(x1, 40f);)
            {
                string m = deck.Next(_ => true);
                if (m == null) return;
                float width = LevelBuildKit.KitSize("Coast", m).x;
                float step = StepWithin(track, x, x + width);
                if (!float.IsNaN(step)) { x = step + 0.5f; continue; }   // a building stands on one level
                if (!OnSideStreetRange(track, x, x + width) && (chunk == null || x + width <= x1))
                {
                    float cx = x + width * 0.5f;
                    if (FloridaHouses.Contains(m)) FloridaHouse(root, m, cx, GroundAt(track, cx), Rand(rng, zMin, zMax));
                    else CoastHouse(root, m, cx, GroundAt(track, cx), Rand(rng, zMin, zMax));
                }
                x += width + Rand(rng, 1.5f, 5f);
            }
        }

        /// <summary>
        /// The California skyline: tall, slim fan palms standing alone and in twos and threes far back
        /// (zMin to zMax), their small crowns well above the roofs.
        /// </summary>
        static void PalmSkyline(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float zMin, float zMax, float spacingMin, float spacingMax)
        {
            if (!LevelBuildKit.HasKitModel("Plants", "PalmFan")) return;
            for (float x = Lo(x0, 40f); x < Hi(x1, 40f); x += Rand(rng, spacingMin, spacingMax))
            {
                if (chunk != null && x > x1) break;
                int n = rng.NextDouble() < 0.45 ? 1 : rng.Next(2, 4);
                float z = Rand(rng, zMin, zMax);
                for (int k = 0; k < n; k++)
                {
                    float px = x + k * Rand(rng, 2.2f, 4.5f), pz = z + Rand(rng, -3f, 3f);
                    if (OnSideStreetRange(track, px - 1f, px + 1f)) continue;
                    Plant(root, "PalmFan", null, px, GroundAt(track, px), pz, Rand(rng, 0.85f, 1.25f), 1f, -70, rng);
                }
            }
        }

        /// <summary>
        /// Palms along the street at depth z, every so often between spacingMin and spacingMax: date palms
        /// (or young fan palms) whose crowns sit in the view over the gardens and shopfronts.
        /// </summary>
        static void StreetPalms(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float z, float spacingMin, float spacingMax,
            float clearFrom = float.NaN, float clearTo = float.NaN)
        {
            if (!LevelBuildKit.HasKitModel("Plants", "PalmDate")) return;
            float skip;
            for (float x = x0 + Rand(rng, 2f, spacingMax); x < x1 - 1f; x += Rand(rng, spacingMin, spacingMax))
            {
                if (Blocked(track, x - 1.2f, x + 1.2f, out skip) || OnSideStreetRange(track, x - 1.5f, x + 1.5f)) continue;
                if (x > clearFrom - 1.2f && x < clearTo + 1.2f) continue;     // (the pier's stairs and their paths)
                bool fan = rng.NextDouble() < 0.35;
                float pz = z + Rand(rng, -0.3f, 0.3f);
                Plant(root, fan ? "PalmFan" : "PalmDate", null, x, GroundAt(track, x, pz), pz,
                    fan ? Rand(rng, 0.42f, 0.5f) : Rand(rng, 0.62f, 0.8f), 1f, -60, rng);
            }
        }

        /// <summary>The pier's deck over the sea (Coast/PierSpan), and how far its landing reaches in front of it.</summary>
        const float PierDeck = 4.8f, PierLandingDepth = 1.9f;

        /// <summary>How far a pier's stairs and their paths reach either side of its centre line (at the longest drop: sand at sea level).</summary>
        static float PierReach
        {
            get { return PierStairs.Reach(PierWidth, PierDeck); }
        }

        static float PierWidth
        {
            get
            {
                float w = LevelBuildKit.KitSize("Coast", "PierSpan").x;
                return w < 1f ? 6f : w;
            }
        }

        /// <summary>
        /// A seaside pier running straight out from the beach at x: twelve-metre spans on concrete piles
        /// from depth zStart out to sea, and the end platform with its roundhouse. Its deck stands 4.8
        /// over the water (sea level gy). The way up is at the beach end: a landing at deck height in front of
        /// the first span and a flight of stairs down to the sand on each side (World/PierStairs), with a
        /// boardwalk path from each foot toward the lane.
        /// </summary>
        static void Pier(LevelBuildKit.TrackBuilder track, Transform root, float x, float seaY, float zStart, int spans)
        {
            if (!LevelBuildKit.HasKitModel("Coast", "PierSpan")) return;
            float length = LevelBuildKit.KitSize("Coast", "PierSpan").z;
            if (length < 1f) length = 12f;
            var pier = new GameObject("Pier").transform;
            pier.SetParent(root, false);
            var p = new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.3f, 0.48f, 0.62f), new Color(0.3f, 0.5f, 0.66f));
            for (int i = 0; i < spans; i++)
                Model(pier, "Coast", "PierSpan", x, seaY, zStart + i * length, 0f, 1f, p.wall, p.trim, p.roof);
            Model(pier, "Coast", "PierEnd", x, seaY, zStart + spans * length, 0f, 1f, p.wall, p.trim, p.roof);
            PierStairsUp(track, pier, x, seaY + PierDeck, zStart);
        }

        /// <summary>
        /// The pier the course climbs (TrackBuilder.PierClimb): its deck at the climb's height over the lane (the piles go
        /// deeper into the sand: the deck stands lower over the water than the pier behind a beach), its near end just behind
        /// the lane, and its stairs across the lane carrying the kid up one flight, over the landing and down the other
        /// (World/PierStairs on the course: the flights' nosings lie on the climb's slopes, so what is drawn is what the kid
        /// and the ball move on).
        /// </summary>
        static void PierOnCourse(LevelBuildKit.TrackBuilder track, Transform root, LevelBuildKit.TrackBuilder.PierClimbSpec climb, int spans)
        {
            if (!LevelBuildKit.HasKitModel("Coast", "PierSpan")) return;
            float length = LevelBuildKit.KitSize("Coast", "PierSpan").z;
            if (length < 1f) length = 12f;
            float x = climb.Centre, deck = climb.groundTop + climb.rise, depth = PierLandingDepth, zStart = depth * 0.5f;
            var pier = new GameObject("Pier").transform;
            pier.SetParent(root, false);
            var p = new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.3f, 0.48f, 0.62f), new Color(0.3f, 0.5f, 0.66f));
            for (int i = 0; i < spans; i++)
                Model(pier, "Coast", "PierSpan", x, deck - PierDeck, zStart + i * length, 0f, 1f, p.wall, p.trim, p.roof);
            Model(pier, "Coast", "PierEnd", x, deck - PierDeck, zStart + spans * length, 0f, 1f, p.wall, p.trim, p.roof);

            var go = new GameObject("PierStairs");
            go.transform.SetParent(pier, false);
            go.transform.position = new Vector3(x, deck, zStart);
            var stairs = go.AddComponent<PierStairs>();
            stairs.onCourse = true;
            stairs.width = PierWidth;
            stairs.landingWidth = climb.Landing;
            stairs.depth = depth;
            stairs.going = climb.going;
            stairs.riser = climb.riserAim;
            stairs.splitOver = LevelBuildKit.TrackBuilder.ClimbSplitOver;
            stairs.dropLeft = stairs.dropRight = climb.rise;
            stairs.landingDrop = deck - GroundAt(track, x, 0f);
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            stairs.Rebuild();
        }

        /// <summary>
        /// The pier's stairs: measured against the sand where each flight lands (a flight's length depends on its drop,
        /// so the foot is found in a few passes), and a path of boards on the sand from each foot toward the lane.
        /// review/pier_stairs/ renders the same from pier_stairs.py.
        /// </summary>
        static void PierStairsUp(LevelBuildKit.TrackBuilder track, Transform pier, float x, float deck, float zStart)
        {
            float width = PierWidth, depth = PierLandingDepth, hw = width * 0.5f, zMid = zStart - depth * 0.5f;
            var go = new GameObject("PierStairs");
            go.transform.SetParent(pier, false);
            go.transform.position = new Vector3(x, deck, zStart);
            var stairs = go.AddComponent<PierStairs>();
            stairs.width = width;
            stairs.depth = depth;
            stairs.landingDrop = deck - GroundAt(track, x, zMid);
            var runs = new float[2];
            for (int k = 0; k < 2; k++)
            {
                float s = k == 0 ? -1f : 1f;
                float run = PierStairs.PlanFor(deck - GroundAt(track, x + s * (hw + 7f), zMid)).run, drop = 0f;
                for (int pass = 0; pass < 2; pass++)
                {
                    drop = deck - GroundAt(track, x + s * (hw + run), zMid);
                    run = PierStairs.PlanFor(drop).run;
                }
                if (k == 0) stairs.dropLeft = drop;
                else stairs.dropRight = drop;
                runs[k] = run;
            }
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            stairs.Rebuild();

            // The paths: boards across, a little apart, from each foot's pad to the back of the lane.
            const float laneBack = 2.2f;
            for (int k = 0; k < 2; k++)
            {
                float cx = x + (k == 0 ? -1f : 1f) * (hw + runs[k] + 0.5f);
                for (float z = zStart - depth - 0.2f; z - 0.18f > laneBack; z -= 0.28f)
                {
                    float g = Mathf.Max(GroundAt(track, cx - 0.65f, z - 0.09f), GroundAt(track, cx + 0.65f, z - 0.09f));
                    Solid(pier, "PathBoard", new Vector3(cx, g + 0.01f, z - 0.09f), new Vector3(1.3f, 0.05f, 0.18f), PierStairs.Boards);
                }
            }
        }
    }
}
