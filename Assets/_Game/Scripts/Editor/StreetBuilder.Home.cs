using DribbleToSchool.Art;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The kid's front door and the seam behind it: every story level starts at home (docs/WORLD_MAP.md, "Every level starts
    /// at home"). <see cref="HomeFront"/> is the one house and garden the levels (and the map) share. A level whose own street
    /// is another chapter's is dressed in two passes of the Holiday Run's stage scenery side by side, the home street (chapter 1)
    /// up to the seam and the route's own street from it (<see cref="SceneryWithSeam"/>); a chapter-1 level is one street.
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>The depth of the front wall of the kid's house (the gardens of the street's other houses are 1.6 to 3 behind the walls).</summary>
        public const float HomeHouseZ = PropertyZ + 2.5f;

        /// <summary>The plot the home front fills, from the gate: the street's own houses and walls keep out of it (a QuietArea).</summary>
        public const float HomePlotLeft = -3.6f, HomePlotRight = 7.6f;

        // ---------------------------------------------------------------- the home front

        /// <summary>
        /// The kid's house and its front garden, built from the kits with <paramref name="gx"/> as the gate and the doorstep (the kid
        /// starts there): the Buildings kit's HouseGable in <see cref="HomeInfo"/>'s colours, its door right behind the gate; a picket
        /// fence along the street with a garden gate (open) between two pillars, one with the house number and a pot on each; hedges
        /// at the ends; a path to the doorstep; flower beds, a bush and pots; the boy's bike on the lawn; the bins; a post box on the footpath;
        /// a tree behind the roof. Without a kit model a piece is left out (the house falls back to the painted one).
        /// </summary>
        public static void HomeFront(Transform parent, float gx, float gy)
        {
            var rng = new System.Random(2024);
            float wallZ = PropertyZ + 0.15f;                         // the property line, where the street's fences and walls stand
            float houseX = gx - HomeInfo.DoorFromMiddle;             // the front door is under the gate
            float houseZ = HomeHouseZ;
            float plotA = gx + HomePlotLeft + 0.1f, plotB = gx + HomePlotRight - 0.1f;
            float gateL = gx - 0.75f, gateR = gx + 0.75f;            // the gateway: 1 m between the pillars' faces

            // The house, with its door in the colour of the map's.
            if (Model(parent, "Buildings", HomeInfo.HouseModel, houseX, gy, houseZ, 0f, 1f, HomeInfo.WallColor, HomeInfo.DoorColor, HomeInfo.RoofColor) != null)
                ContactShadow(parent, houseX - 3.5f, houseX + 3.5f, gy, houseZ - 0.45f, houseZ);
            else
                Building(parent, houseX, gy, houseZ, ProceduralArt.FacadeKind.HouseGable, House3D.RoofStyle.GableToStreet, 7f, 2.6f, HomeInfo.WallColor, HomeInfo.RoofColor);

            // The path from the gate to the doorstep (the kit's two steps reach 0.6 m out from the wall).
            Patch(parent, "GardenPath", gx - 0.65f, gx + 0.65f, gy, wallZ + 0.25f, houseZ - 0.62f, new Color(0.88f, 0.86f, 0.82f),
                Art.surfaces[ProceduralArt.Surface.Paving], 0.014f);

            // The fence along the street, the gate between two pillars, a pillar at each end of the plot.
            if (Row(parent, "Street", "PicketFence2", plotA + 0.25f, gateL - 0.25f, gy, wallZ))
                Row(parent, "Street", "PicketFence2", gateR + 0.25f, plotB - 0.25f, gy, wallZ);
            else
            {
                var wallMat = Art.surfaces[ProceduralArt.Surface.BlockWall];
                BlockWall(parent, plotA + 0.25f, gateL - 0.25f, gy, wallMat, false, false);
                BlockWall(parent, gateR + 0.25f, plotB - 0.25f, gy, wallMat, false, false);
            }
            foreach (float px in new[] { plotA, gateL, gateR, plotB })
                Model(parent, "Street", "WallPillar", px, gy, wallZ);
            foreach (float px in new[] { gateL, gateR })
                Model(parent, "Street", "PotA", px, gy + 1.95f, wallZ, rng.Next(360));
            Plaque(parent, HomeInfo.HouseNumber, gateL, gy + 1.3f, wallZ - 0.25f);

            // The gate itself, a short picket panel swung open into the garden on the right pillar's hinge.
            const float leaf = 0.95f, open = 75f * Mathf.Deg2Rad;
            var gate = Model(parent, "Street", "PicketFence2", gateR - 0.25f - leaf * 0.5f * Mathf.Cos(open), gy, wallZ + leaf * 0.5f * Mathf.Sin(open), 75f);
            if (gate != null) gate.localScale = new Vector3(leaf / 2f, 1f, 1f);

            // Hedges behind the fence at either end of the plot, flowers and shrubs in the beds either side of the path.
            Row(parent, "Plants", "HedgeBlock2", plotA + 0.4f, gateL - 0.6f, gy, wallZ + 0.55f, HedgeGreen);
            Row(parent, "Plants", "HedgeBlock2", plotB - 2.6f, plotB - 0.4f, gy, wallZ + 0.55f, HedgeGreen);
            float[] bedX = { -0.95f, -1.25f, 1.2f, 1.8f, 2.6f }, bedZ = { 2.9f, 3.25f, 3.0f, 3.1f, 2.95f };
            for (int i = 0; i < bedX.Length; i++)
                Model(parent, "Plants", "FlowerPatch", gx + bedX[i], gy, bedZ[i], Rand(rng, 0f, 360f), Rand(rng, 1.1f, 1.5f));
            Plant(parent, "BushRound", null, gx - 2.1f, gy, houseZ - 0.05f, 1f, 1f, -60, rng);

            // By the door, besides the two pots the model brings: a group of pots on the right, clear of the window.
            Model(parent, "Street", "PotGroup", gx + 2.2f, gy, houseZ - 0.6f, -12f, 1f, Petals[0]);

            // Life in the garden: the boy's green bicycle on its stand (the kit's if his isn't there) and the bins on the lawn to the
            // right, a post box on the footpath by the gate.
            if (LevelBuildKit.OwnBicycle(parent, new Vector3(gx + 3.9f, gy, 3.1f)) == null)
                Model(parent, "Street", "Bicycle", gx + 3.9f, gy, 3.1f, 0f, 1f, BikeColors[1]);
            Model(parent, "Street", "BinPair", gx + 6.6f, gy, 3.5f, -8f, 1f, BinColors[0], BinColors[1]);
            Model(parent, "Street", "PostBox", gx - 1.55f, gy, PoleZ - 0.1f);

            // A tree behind the roof.
            Plant(parent, "Broadleaf", null, houseX + 1.2f, gy, houseZ + 8.5f, 1.15f, 1f, -70, rng);
        }

        /// <summary>A small enamel plate with a number (or a word) on it, facing the street, at (x, y, z).</summary>
        static void Plaque(Transform parent, string text, float x, float y, float z)
        {
            var plate = Solid(parent, "HouseNumberPlate", new Vector3(x, y, z), new Vector3(0.3f, 0.22f, 0.04f), new Color(0.97f, 0.96f, 0.92f));
            var textGo = new GameObject("Number");
            textGo.transform.SetParent(plate.transform, false);
            textGo.transform.localPosition = new Vector3(0f, 0f, -0.03f);
            var mesh = textGo.AddComponent<TextMesh>();
            mesh.text = text;
            mesh.font = LevelBuildKit.SignFont;
            mesh.fontSize = 48;
            mesh.characterSize = 0.032f;
            mesh.anchor = TextAnchor.MiddleCenter;
            mesh.alignment = TextAlignment.Center;
            mesh.color = new Color(0.2f, 0.25f, 0.4f);
            var renderer = textGo.GetComponent<MeshRenderer>();
            if (LevelBuildKit.SignFont != null) renderer.sharedMaterial = LevelBuildKit.SignFont.material;
            renderer.sortingOrder = 6;
        }

        // ---------------------------------------------------------------- two streets, one seam

        /// <summary>
        /// A level that starts at home and goes on in another chapter's street (the track has a seam): the route's own street from the
        /// seam to well past the level's end (a Holiday Run stage's scenery, with the distant land too: a level has no core scene),
        /// and the home street, the first chapter's, from well behind the front door to the seam. Each builds exactly its own stretch
        /// (its lots, shops, poles and animals fit and stop at the seam), the road's surface eases from one into the other with ragged
        /// patches and the beach has its few props at the edge (the stages' seam dressing), and each pass restores the chapter after it.
        /// </summary>
        static void SceneryWithSeam(LevelBuildKit.TrackBuilder track, Transform root)
        {
            int own = LevelBuildKit.Chapter;
            float seam = track.SeamX;
            int seed = own * 131 + Mathf.RoundToInt(track.MaxX);

            Pass(track, root, "the route's street", new StageSpec
            {
                stage = -1,
                from = seam,
                to = track.MaxX + 50f,
                seed = seed,
                prevChapter = HomeChapter,
                // (The home street's last lot and the route's first are the lead-in's to dress: no stage-style cross-fade of the lots.)
                firstLotX = float.NegativeInfinity,
                endStreetFrom = float.PositiveInfinity,
                polesBefore = own == 4,
                flocks = true,
                level = true,
            });
            NameCritters("Critters");

            // The home street is built as chapter 1 but lit by the level's own sun: its near trees' shade follows that.
            lightSun = ChapterTheme.For(own).mood.sunDirection;
            try
            {
                LevelBuildKit.AsChapter(HomeChapter, () => Pass(track, root, "the home street", new StageSpec
                {
                    stage = -1,
                    from = track.MinX - 50f,
                    to = seam,
                    seed = seed + 0x1F3,
                    nextChapter = own,
                    firstLotX = float.NegativeInfinity,
                    endStreetFrom = float.PositiveInfinity,
                    flocks = false,
                }));
            }
            finally { lightSun = null; }
            NameCritters("Critters (home street)");
        }

        const int HomeChapter = HomeLeadInRules.HomeChapter;

        /// <summary>
        /// Does [a, b] stand across the seam? The two streets are built in separate passes, each to its side of it, so nothing wide
        /// (a building of the back rows, a far row) is put across the joint, where the other pass has its own.
        /// </summary>
        static bool AcrossSeam(LevelBuildKit.TrackBuilder track, float a, float b)
        {
            return track.HasSeam && b > track.SeamX - 0.3f && a < track.SeamX + 0.3f;
        }

        /// <summary>One stretch's scenery; a failure is logged and the level is still built (as the Holiday Run's stages are).</summary>
        static void Pass(LevelBuildKit.TrackBuilder track, Transform root, string what, StageSpec spec)
        {
            try
            {
                StageScenery(track, root, spec);
            }
            catch (System.Exception e)
            {
                Debug.LogError("[Kick Off] " + track.AuditName + ": couldn't build the scenery of " + what + ": " + e);
            }
        }

        /// <summary>Names the animals' holder the pass just made (each pass makes its own, at the scene's root) and lets go of it, so a failed pass cannot rename the last one's.</summary>
        static void NameCritters(string name)
        {
            if (critters != null) critters.name = name;
            critters = null;
        }
    }
}
