using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The California look of the streets (the Coast kit, tools/blender/kit_buildings_cal.py): stucco
    /// villas under hipped terracotta roofs, single-storey ranch houses, Craftsman houses with deep
    /// front porches, white beach condos, beach-town shops, tall fan palms on the skyline and date
    /// palms along the streets, and a seaside pier on piles running out from the beach.
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>The Coast kit's houses and shops.</summary>
        static readonly HashSet<string> CoastModels = new HashSet<string>
        {
            "VillaStucco", "VillaRanch", "CraftsmanPorch", "BeachCondo", "ShopBeach", "ShopMission", "PierSpan", "PierEnd",
        };

        /// <summary>The kit a building model lives in: the Coast kit's California models, else the Buildings kit.</summary>
        public static string KitOf(string model)
        {
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
                case "BeachCondo": return 0.6f;
                default: return 0f;
            }
        }

        static readonly Color Terracotta = new Color(0.76f, 0.4f, 0.27f);

        // Paint schemes (wall, accent, roof), sRGB: warm stucco under terracotta for the villas; white,
        // pale blue or putty siding over charcoal shingles for the Craftsman houses.
        static readonly Paint[] VillaPaints =
        {
            new Paint(new Color(0.95f, 0.9f, 0.8f), new Color(0.42f, 0.3f, 0.22f), Terracotta),                           // cream, walnut
            new Paint(new Color(0.93f, 0.84f, 0.72f), new Color(0.3f, 0.4f, 0.46f), new Color(0.7f, 0.36f, 0.25f)),        // sand, slate blue
            new Paint(new Color(0.96f, 0.93f, 0.86f), new Color(0.24f, 0.36f, 0.3f), new Color(0.8f, 0.46f, 0.32f)),       // ivory, green
            new Paint(new Color(0.91f, 0.8f, 0.7f), new Color(0.45f, 0.3f, 0.25f), new Color(0.72f, 0.4f, 0.3f)),          // peach
            new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.22f, 0.28f, 0.36f), new Color(0.74f, 0.42f, 0.3f)),      // white, navy
            new Paint(new Color(0.88f, 0.82f, 0.72f), new Color(0.36f, 0.26f, 0.2f), new Color(0.66f, 0.38f, 0.28f)),      // putty
        };
        static readonly Paint[] CraftsmanPaints =
        {
            new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.3f, 0.38f, 0.46f), new Color(0.34f, 0.36f, 0.4f)),       // white, slate
            new Paint(new Color(0.8f, 0.86f, 0.88f), new Color(0.62f, 0.22f, 0.2f), new Color(0.36f, 0.37f, 0.4f)),        // pale blue, red door
            new Paint(new Color(0.9f, 0.86f, 0.78f), new Color(0.24f, 0.36f, 0.3f), new Color(0.4f, 0.36f, 0.33f)),        // putty, green
            new Paint(new Color(0.84f, 0.8f, 0.7f), new Color(0.3f, 0.3f, 0.32f), new Color(0.33f, 0.33f, 0.36f)),         // sage grey
        };
        static readonly Paint[] CondoPaints =
        {
            new Paint(new Color(0.96f, 0.96f, 0.94f), new Color(0.4f, 0.56f, 0.66f), new Color(0.56f, 0.55f, 0.54f)),
            new Paint(new Color(0.93f, 0.91f, 0.86f), new Color(0.3f, 0.34f, 0.38f), new Color(0.56f, 0.55f, 0.54f)),
            new Paint(new Color(0.9f, 0.93f, 0.94f), new Color(0.24f, 0.46f, 0.56f), new Color(0.56f, 0.55f, 0.54f)),
        };
        static readonly Paint[] BeachShopPaints =
        {
            new Paint(new Color(0.97f, 0.92f, 0.82f), new Color(0.2f, 0.58f, 0.66f), new Color(0.56f, 0.55f, 0.54f)),      // teal awning
            new Paint(new Color(0.96f, 0.95f, 0.92f), new Color(0.88f, 0.42f, 0.3f), new Color(0.56f, 0.55f, 0.54f)),      // coral awning
            new Paint(new Color(0.94f, 0.86f, 0.7f), new Color(0.24f, 0.36f, 0.6f), new Color(0.56f, 0.55f, 0.54f)),       // navy awning
            new Paint(new Color(0.92f, 0.94f, 0.92f), new Color(0.96f, 0.72f, 0.2f), new Color(0.56f, 0.55f, 0.54f)),      // sunflower awning
        };
        static readonly Paint[] MissionPaints =
        {
            new Paint(new Color(0.95f, 0.89f, 0.78f), new Color(0.3f, 0.22f, 0.17f), Terracotta),
            new Paint(new Color(0.92f, 0.84f, 0.74f), new Color(0.24f, 0.3f, 0.26f), new Color(0.72f, 0.38f, 0.26f)),
            new Paint(new Color(0.97f, 0.95f, 0.9f), new Color(0.36f, 0.2f, 0.16f), new Color(0.78f, 0.44f, 0.3f)),
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
                    CoastHouse(root, m, cx, GroundAt(track, cx), Rand(rng, zMin, zMax));
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
        static void StreetPalms(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float z, float spacingMin, float spacingMax)
        {
            if (!LevelBuildKit.HasKitModel("Plants", "PalmDate")) return;
            float skip;
            for (float x = x0 + Rand(rng, 2f, spacingMax); x < x1 - 1f; x += Rand(rng, spacingMin, spacingMax))
            {
                if (Blocked(track, x - 1.2f, x + 1.2f, out skip) || OnSideStreetRange(track, x - 1.5f, x + 1.5f)) continue;
                bool fan = rng.NextDouble() < 0.35;
                float pz = z + Rand(rng, -0.3f, 0.3f);
                Plant(root, fan ? "PalmFan" : "PalmDate", null, x, GroundAt(track, x, pz), pz,
                    fan ? Rand(rng, 0.42f, 0.5f) : Rand(rng, 0.62f, 0.8f), 1f, -60, rng);
            }
        }

        /// <summary>
        /// A seaside pier running straight out from the beach at x: twelve-metre spans on concrete piles
        /// from depth zStart out to sea, and the end platform with its roundhouse. Its deck stands 4.8
        /// over the water (sea level gy).
        /// </summary>
        static void Pier(Transform root, float x, float seaY, float zStart, int spans)
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
        }
    }
}
