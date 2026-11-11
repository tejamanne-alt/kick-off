using DribbleToSchool.Art;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The Florida add-on's Home Street (chapter 1's &lt;scene&gt;_FL scenes, and the home street before every Florida level's seam),
    /// after the user's references (review/florida/refs, F1-1 to F1-5): concrete-block ranch houses in faded pastels with bright
    /// doors, awnings and screened porches; Old Florida frame cottages with porches, swings and picket fences; great live oaks hung
    /// with Spanish moss over the footpath, sabal palms, rural mailboxes at the kerb; a canal running back from the street under a
    /// bascule drawbridge (LevelBuildKit.Drawbridge), its docks and boat lifts. The street's own lots are the usual suburb's
    /// (StreetBuilder.SuburbHouses), with Florida's houses, trees and mailboxes (<see cref="FloridaHouses"/>, <see cref="StreetOaks"/>);
    /// here are the set pieces: the kid's own ranch house, and the stops' Florida looks (Granny's cottage and Sam's ranch are
    /// <see cref="FrontGarden"/>'s, the Mission church and the bus shelter below).
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>The kid's Florida house (the Florida kit's RanchFL): seafoam block, the red front door of the map's house, a pale metal roof.</summary>
        public static class HomeInfoFL
        {
            public const string HouseModel = "RanchFL";
            /// <summary>The front door's place on the model, from the middle of its front (to the left, by the picture window).</summary>
            public const float DoorFromMiddle = -1.2f;
            public static readonly Color WallColor = new Color(0.70f, 0.86f, 0.82f);
            public static readonly Color DoorColor = new Color(0.80f, 0.22f, 0.17f);
            public static readonly Color RoofColor = new Color(0.88f, 0.87f, 0.84f);
        }

        /// <summary>The Florida home's plot from the gate: the ranch is 12 m wide with its awning.</summary>
        static readonly Vector2 HomePlotFL = new Vector2(-5.6f, 7.8f);

        /// <summary>How far Granny's cottage stands back of the other stops' houses, for its porch and steps (2.2 m).</summary>
        const float CottageSetbackFL = 2.3f;

        /// <summary>How much further back a deep-garden lot's house stands (<see cref="FrontGardenFL"/>).</summary>
        const float GardenDepth = 3.2f;
        /// <summary>Where the live oaks stand between the rows, and where the back row begins (both clear of the deep gardens' houses).</summary>
        const float OakRowFL = 20.5f, BackRowFL = 24f;

        /// <summary>About one Florida lot in three is a deep garden (by its place, so the street's other draws are untouched).</summary>
        static bool GardenLot(float x)
        {
            return Scramble(Mathf.Abs(Mathf.RoundToInt(x * 7f)) + 17) % 3 == 0;
        }

        /// <summary>A kit house's front door, from the middle of its front (its manifest's first door), or 0.</summary>
        static float DoorOffset(string kit, string model)
        {
            var info = LevelBuildKit.KitInfo(kit, model);
            object doors;
            if (info == null || !info.TryGetValue("doors", out doors)) return 0f;
            var list = doors as System.Collections.Generic.List<object>;
            var door = list != null && list.Count > 0 ? list[0] as System.Collections.Generic.Dictionary<string, object> : null;
            object center;
            if (door == null || !door.TryGetValue("center", out center)) return 0f;
            var c = center as System.Collections.Generic.List<object>;
            return c != null && c.Count > 0 ? System.Convert.ToSingle(c[0]) : 0f;
        }

        /// <summary>
        /// A deep front garden on a Florida lot (x to x + lot, the gate at <paramref name="gate"/>, the house of half-width
        /// <paramref name="half"/> centred on <paramref name="cx"/> with its front wall at <paramref name="z"/>): a mown lawn from the
        /// sidewalk to the porch, a walk from the gate to the door, flower beds along the front, an island bed with a saw palmetto
        /// (or a young sabal) in the lawn, flowering shrubs at the corners. Its own random draws, so the street's are untouched.
        /// </summary>
        static void FrontGardenFL(Transform root, string house, float x, float lot, float gate, float gy, float cx, float half, float z)
        {
            var rng = new System.Random(Mathf.RoundToInt(x * 13f) + 977);
            float front = z + LevelBuildKit.KitMin("Florida", house).z;      // the porch's or the steps' front
            float lawnA = PropertyZ + 0.45f, mid = (lawnA + front) * 0.5f;
            Patch(root, "Lawn", x + 0.3f, x + lot - 0.3f, gy, lawnA, front - 0.05f, new Color(0.56f, 0.74f, 0.36f), Art.surfaces[ProceduralArt.Surface.Grass], 0.012f);

            // The walk: in at the gate, across, and up to the door.
            Color walkColor = new Color(0.9f, 0.89f, 0.86f);
            var concrete = Art.surfaces[ProceduralArt.Surface.Concrete];
            float g = gate + 0.7f, door = cx + DoorOffset("Florida", house);
            Patch(root, "Walk", g - 0.55f, g + 0.55f, gy, PropertyZ + 0.2f, mid + 0.55f, walkColor, concrete, 0.016f);
            Patch(root, "Walk", Mathf.Min(g, door) - 0.55f, Mathf.Max(g, door) + 0.55f, gy, mid - 0.55f, mid + 0.55f, walkColor, concrete, 0.017f);
            Patch(root, "Walk", door - 0.55f, door + 0.55f, gy, mid - 0.55f, front + 0.02f, walkColor, concrete, 0.016f);

            // Beds along the front, either side of the door.
            int beds = 0;
            for (float bx = cx - half + 0.7f; bx < cx + half - 0.6f && beds < 4; bx += Rand(rng, 1.4f, 2.2f))
            {
                if (Mathf.Abs(bx - door) < 1.1f) continue;
                Model(root, "Plants", "FlowerPatch", bx, gy, front - 0.45f, Rand(rng, 0f, 360f), Rand(rng, 1.1f, 1.4f), null, Petals[rng.Next(Petals.Length)]);
                beds++;
            }
            // An island bed in the lawn, on the side away from the walk.
            float ix = Mathf.Clamp(door > cx ? cx - half * 0.5f : cx + half * 0.5f, x + 1.6f, x + lot - 1.6f);
            if (Mathf.Abs(ix - g) > 1.8f && Mathf.Abs(ix - door) > 1.6f)
            {
                bool palm = rng.NextDouble() < 0.35;
                Plant(root, palm ? "PalmSabal" : "SawPalmetto", null, ix, gy, mid, palm ? Rand(rng, 0.5f, 0.6f) : Rand(rng, 1.1f, 1.35f), 1f, -60, rng);
                for (int k = 0; k < 3; k++)
                {
                    float a = (k / 3f + Rand(rng, 0f, 0.1f)) * Mathf.PI * 2f;
                    Model(root, "Plants", "FlowerPatch", ix + Mathf.Cos(a) * 0.9f, gy, mid + Mathf.Sin(a) * 0.6f, Rand(rng, 0f, 360f), Rand(rng, 1f, 1.25f), null, Petals[rng.Next(Petals.Length)]);
                }
            }
            // Flowering shrubs (hibiscus) at the corners by the sidewalk, clear of the gate.
            foreach (float sx in new[] { x + 0.9f, x + lot - 0.9f })
                if (Mathf.Abs(sx - g) > 1.4f)
                    Plant(root, "ShrubFlowering", null, sx, gy, lawnA + 0.55f, Rand(rng, 1.1f, 1.4f), 1f, -60, rng);
        }

        /// <summary>
        /// The kid's Florida house and its yard, with <paramref name="gx"/> as the doorstep (the kid starts on the footpath in front
        /// of it): the ranch with its door over the walk, an open lawn as Florida's front yards are, beds under the picture window,
        /// a young sabal, the bike and the bins, the mailbox at the kerb, the house number by the door and a live oak behind the roof.
        /// </summary>
        static void HomeFrontFL(Transform parent, float gx, float gy)
        {
            var rng = new System.Random(2024);
            float wallZ = PropertyZ + 0.15f, houseZ = HomeHouseZ;     // (the parent stands on the top step at HomeHouseZ, as at the other home)
            float houseX = gx - HomeInfoFL.DoorFromMiddle;
            float half = LevelBuildKit.KitSize("Florida", HomeInfoFL.HouseModel).x * 0.5f;
            if (Model(parent, "Florida", HomeInfoFL.HouseModel, houseX, gy, houseZ, 0f, 1f, HomeInfoFL.WallColor, HomeInfoFL.DoorColor, HomeInfoFL.RoofColor) == null) return;
            ContactShadow(parent, houseX - half, houseX + half, gy, houseZ - 0.45f, houseZ);

            // The walk from the footpath to the steps.
            float steps = -LevelBuildKit.KitMin("Florida", HomeInfoFL.HouseModel).z + 0.02f;
            Patch(parent, "FrontWalk", gx - 0.65f, gx + 0.65f, gy, wallZ - 0.2f, houseZ - steps, new Color(0.9f, 0.89f, 0.86f),
                Art.surfaces[ProceduralArt.Surface.Concrete], 0.014f);
            Plaque(parent, HomeInfo.HouseNumber, gx - 0.95f, gy + 1.9f, houseZ - 0.05f);

            // Beds under the picture window, hibiscus by the corners, pots by the walk; a young sabal at the left of the lawn.
            float[] bedX = { -1.7f, -2.4f, -3.1f, -3.7f }, bedZ = { 3.5f, 3.75f, 3.45f, 3.7f };
            for (int i = 0; i < bedX.Length; i++)
                Model(parent, "Plants", "FlowerPatch", gx + bedX[i], gy, bedZ[i], Rand(rng, 0f, 360f), Rand(rng, 1.1f, 1.4f), null, Petals[(i + 1) % Petals.Length]);
            Plant(parent, "ShrubFlowering", null, gx - 4.6f, gy, houseZ - 0.3f, 1.15f, 1f, -60, rng);
            Plant(parent, "ShrubFlowering", null, gx + 6.9f, gy, houseZ - 0.4f, 1.05f, 1f, -60, rng);
            Model(parent, "Street", "PotGroup", gx + 1.1f, gy, wallZ + 0.6f, -12f, 1f, Petals[0]);
            Plant(parent, "PalmSabal", null, gx - 4.3f, gy, wallZ + 1.0f, 0.7f, 1f, -60, rng);

            // The bike on the lawn, the bins out by the drive, the mailbox at the kerb by the walk.
            Model(parent, "Street", "Bicycle", gx + 3.9f, gy, 3.1f, 0f, 1f, BikeColors[1]);
            Model(parent, "Street", "BinPair", gx + 6.6f, gy, 3.0f, -8f, 1f, BinColors[0], BinColors[1]);
            Model(parent, "Florida", "MailboxPostFL", gx - 1.55f, gy, PoleZ + 0.05f);

            // A live oak behind the roof, its moss over the ridge.
            Plant(parent, LevelBuildKit.HasKitModel("Plants", "LiveOak") ? "LiveOak" : "Broadleaf", null, houseX + 2.2f, gy, houseZ + 11f, 1.05f, 1f, -70, rng);
        }

        /// <summary>
        /// St Mary's in Florida: a Spanish Mission church (the Florida kit's ChurchFL) of white stucco under red tile, its bell tower
        /// at the left; a low stucco wall with tile coping along the street and its gateway on the footpath, a path to the doors,
        /// sabal palms, a bench and the notice board.
        /// </summary>
        static void MissionChurchFL(Transform p, float gx, float gy, System.Random rng)
        {
            float front = 7.0f, wallZ = PropertyZ + 0.15f;
            Color stucco = new Color(0.96f, 0.95f, 0.91f), tile = new Color(0.72f, 0.38f, 0.27f);
            var min = LevelBuildKit.KitMin("Florida", "ChurchFL");
            Model(p, "Florida", "ChurchFL", gx, gy, front);
            ContactShadow(p, gx + min.x, gx + LevelBuildKit.KitSize("Florida", "ChurchFL").x * 0.5f, gy, front - 0.45f, front);   // (the tower is on the left)

            float a = gx + ChurchPlotLeft + 0.2f, b = gx + ChurchPlotRight - 0.2f;
            foreach (var run in new[] { new Vector2(a, gx - 0.9f), new Vector2(gx + 0.9f, b) })
            {
                float len = run.y - run.x, mid = (run.x + run.y) * 0.5f;
                Solid(p, "ChurchyardWall", new Vector3(mid, gy + 0.4f, wallZ), new Vector3(len, 0.8f, 0.34f), stucco, Art.surfaces[ProceduralArt.Surface.Concrete]);
                Solid(p, "WallCoping", new Vector3(mid, gy + 0.85f, wallZ), new Vector3(len + 0.05f, 0.1f, 0.44f), tile);
            }
            foreach (float px in new[] { gx - 0.9f, gx + 0.9f })
            {
                Solid(p, "GatePier", new Vector3(px, gy + 0.65f, wallZ), new Vector3(0.46f, 1.3f, 0.46f), stucco);
                Solid(p, "PierCap", new Vector3(px, gy + 1.34f, wallZ), new Vector3(0.56f, 0.1f, 0.56f), tile);
            }
            Patch(p, "ChurchPath", gx - 0.85f, gx + 0.85f, gy, wallZ + 0.25f, front + min.z, new Color(0.88f, 0.85f, 0.8f), Art.surfaces[ProceduralArt.Surface.Paving], 0.014f);
            Patch(p, "Churchyard", a, b, gy, wallZ + 0.25f, front + 0.5f, new Color(0.6f, 0.76f, 0.42f), Art.surfaces[ProceduralArt.Surface.Grass], 0.01f);
            Plant(p, "PalmSabalTall", null, gx + 5.8f, gy, front + 2.2f, 1.0f, 1f, -70, rng);
            Plant(p, "PalmSabal", null, gx + 6.3f, gy, front - 3.0f, 0.85f, 1f, -60, rng);
            Plant(p, "ShrubFlowering", null, gx - 6.5f, gy, wallZ + 1.1f, 1.2f, 1f, -60, rng);
            Model(p, "Street", "Bench", gx + 3.4f, gy, front - 2.6f, 0f, 0.95f);
            PostBoard(p, "ST MARY'S\nCHURCH", gx - 2.4f, gy, wallZ + 0.55f, 0.04f, new Color(0.62f, 0.24f, 0.18f), new Color(0.98f, 0.94f, 0.82f));
        }

        /// <summary>
        /// The Florida bus stop: the Florida kit's shelter (a flat aluminium roof and a bench) at the back of the footpath, the
        /// stop's blue sign on its pole, a bin, a sabal and sea grape behind.
        /// </summary>
        static void BusStopFL(Transform p, float gx, float gy, System.Random rng)
        {
            float sx = gx + 1.7f;
            Model(p, "Florida", "BusShelterFL", sx, gy, PoleZ + 0.35f);
            float px = gx - 0.75f, pz = PoleZ - 0.05f;
            Color blue = new Color(0.12f, 0.32f, 0.62f);
            Solid(p, "StopPole", new Vector3(px, gy + 1.35f, pz), new Vector3(0.07f, 2.7f, 0.07f), new Color(0.6f, 0.62f, 0.64f));
            NameBoard(p, "BUS STOP", new Vector3(px, gy + 2.4f, pz - 0.06f), 0.03f, blue, Color.white);
            Model(p, "Florida", "TrashFL", gx + 4.2f, gy, PoleZ + 0.15f);
            Row(p, "Plants", "HedgeBlock2", gx - 1.5f, gx + 5.6f, gy, PropertyZ + 1.9f, HedgeGreen);
            Plant(p, "PalmSabal", null, gx + 5.2f, gy, PropertyZ + 3.4f, 0.85f, 1f, -60, rng);
        }
    }
}
