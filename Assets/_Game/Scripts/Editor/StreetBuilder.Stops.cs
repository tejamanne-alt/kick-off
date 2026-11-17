using System;
using DribbleToSchool.Art;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The stops on the way to school (Levels/RouteTable.Stops): where one level of a route ends and the next one starts
    /// (docs/WORLD_MAP.md, "Every route is one trip, a level is a leg of it"). Each stop is one set piece, built the same at
    /// the end of the level that arrives there and at the start of the level that leaves from it, so the two levels meet: the
    /// bus stop's shelter, granny's bungalow and garden, the church on the hill, a friend's house, the shops of Market Street
    /// with their names over the doors, the surf school and the lifeguard tower on the sand, the railway station, the site
    /// office, and in the park the bandstand, the cafe, the boathouse and grandpa's allotment. <c>gx</c> is the stop's door or
    /// gate, where the kid starts or finishes on the footpath. Built from the art kits; a piece a kit hasn't got is left out
    /// (the buildings fall back to the painted ones). The people at some stops are added by the track builder
    /// (LevelBuildKit.Stops.cs), which has the character rig.
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>The stops <see cref="StopFront"/> has a set piece for (a test checks it against Levels/RouteTable.Stops).</summary>
        public static readonly string[] SetPieces =
        {
            "busStop", "granny", "church", "samsHouse", "bakery", "postOffice", "florist", "library", "surfSchool", "lifeguard", "beachCafe",
            "station", "siteOffice", "bandstand", "parkCafe", "boathouse", "allotment",
        };

        /// <summary>The plot a stop's set piece fills, from its door: the street's own lots keep out of it (a QuietArea).</summary>
        public const float StopPlotLeft = -4.6f, StopPlotRight = 7.6f;

        /// <summary>The church and its churchyard are wider than the other stops.</summary>
        public const float ChurchPlotLeft = -7.6f, ChurchPlotRight = 7.4f;

        /// <summary>The plot of <paramref name="stop"/>'s set piece around its door (left and right of it, in metres).</summary>
        public static Vector2 StopPlot(Stop stop)
        {
            return stop != null && stop.kind == StopKind.Church ? new Vector2(ChurchPlotLeft, ChurchPlotRight) : new Vector2(StopPlotLeft, StopPlotRight);
        }

        /// <summary>How far behind the footpath a stop's building stands (its front wall's z), by chapter: shops are built near the pavement.</summary>
        static float StopFrontZ(Stop stop)
        {
            switch (stop.kind)
            {
                case StopKind.House: return HomeHouseZ;
                case StopKind.Shop: return LevelBuildKit.Chapter == 3 ? 4.6f : LevelBuildKit.Chapter == 5 ? 4.2f : PropertyZ + 1.3f;
                case StopKind.Station: return PropertyZ + 1.6f;
                default: return PropertyZ + 2.2f;
            }
        }

        /// <summary>
        /// The set piece of <paramref name="stop"/> with its door (or gate, or sign) at <paramref name="gx"/>, the footpath at
        /// <paramref name="gy"/>. Each piece is deterministic, so the two levels that share a stop build the same thing.
        /// </summary>
        public static void StopFront(LevelBuildKit.TrackBuilder track, Transform parent, Stop stop, float gx, float gy)
        {
            if (stop == null) return;
            var rng = new System.Random(Seed(stop.id));
            Func<float, float, float> ground = (x, z) => LevelBuildKit.Chapter == 3 ? GroundAt(track, x, z) : gy;
            switch (stop.id)
            {
                case "busStop": BusStop(parent, gx, gy, rng); break;
                case "granny": GrannysHouse(parent, gx, gy, rng); break;
                case "church": Church(parent, gx, gy, rng); break;
                case "samsHouse": SamsHouse(parent, gx, gy, rng); break;
                case "bakery":
                    ShopStop(parent, stop, gx, ground, "ShopCafe", 1.925f, new Color(0.98f, 0.92f, 0.8f), new Color(0.62f, 0.38f, 0.22f), new Color(0.42f, 0.3f, 0.26f),
                        "BAKERY", new Color(0.62f, 0.38f, 0.22f), new Color(1f, 0.95f, 0.85f));
                    Model(parent, "Street", "SignBoardA", gx - 1.3f, gy, 2.55f, -20f);
                    Model(parent, "Street", "Bench", gx + 3.4f, gy, 2.55f);
                    Model(parent, "Street", "Planter1", gx - 2.6f, gy, 2.45f, 0f, 1f, null, Petals[2]);
                    Model(parent, "Street", "Bicycle", gx + 5.6f, gy, 2.6f, 8f, 1f, BikeColors[2]);
                    break;
                case "postOffice":
                    ShopStop(parent, stop, gx, ground, "ShopTall", 0.875f, new Color(0.97f, 0.94f, 0.86f), new Color(0.82f, 0.18f, 0.16f), new Color(0.34f, 0.36f, 0.42f),
                        "POST OFFICE", new Color(0.82f, 0.18f, 0.16f), new Color(1f, 0.86f, 0.25f));
                    Model(parent, "Street", "PostBox", gx - 1.5f, gy, PoleZ - 0.1f);
                    Model(parent, "Street", "BikeRack", gx + 3.4f, gy, 2.5f);
                    Model(parent, "Street", "Bicycle", gx + 3.0f, gy, 2.45f, 0f, 1f, new Color(0.82f, 0.18f, 0.16f));
                    break;
                case "florist":
                    ShopStop(parent, stop, gx, ground, "ShopFlorist", 2.55f, new Color(0.95f, 0.97f, 0.93f), new Color(0.36f, 0.58f, 0.42f), new Color(0.3f, 0.34f, 0.36f),
                        "FLOWERS", new Color(0.36f, 0.58f, 0.42f), Color.white);
                    // Buckets of flowers out front, under the window.
                    for (int i = 0; i < 4; i++)
                    {
                        float fx = gx - 3.6f + i * 1.1f;
                        Model(parent, "Street", i % 2 == 0 ? "PotGroup" : "PotA", fx, gy, 2.55f, Rand(rng, 0f, 360f), 1f, Petals[i % Petals.Length]);
                        Model(parent, "Plants", "FlowerPatch", fx, gy + 0.35f, 2.6f, Rand(rng, 0f, 360f), 0.9f);
                    }
                    Model(parent, "Street", "SignBoardA", gx + 1.3f, gy, 2.5f, 15f);
                    break;
                case "library":
                    ShopStop(parent, stop, gx, ground, "ShopBooks", 0f, new Color(0.85f, 0.78f, 0.68f), new Color(0.24f, 0.36f, 0.6f), new Color(0.3f, 0.32f, 0.38f),
                        "LIBRARY", new Color(0.24f, 0.36f, 0.6f), Color.white);
                    Model(parent, "Street", "BikeRack", gx - 3.0f, gy, 2.5f);
                    Model(parent, "Street", "Bicycle", gx - 3.4f, gy, 2.45f, 0f, 1f, BikeColors[0]);
                    Model(parent, "Street", "Bicycle", gx - 2.5f, gy, 2.55f, 180f, 1f, BikeColors[3]);
                    Model(parent, "Street", "Bench", gx + 2.8f, gy, 2.55f);
                    Model(parent, "Street", "Planter2", gx + 5.2f, gy, 2.45f, 0f, 1f, null, Petals[4]);
                    break;
                case "beachCafe":
                    BeachKiosk(parent, gx, ground);
                    CafeTables(parent, gx, ground, rng, true);
                    break;
                case "parkCafe":
                    ShopStop(parent, stop, gx, ground, "ShopCafe", 1.925f, new Color(0.96f, 0.95f, 0.88f), new Color(0.3f, 0.5f, 0.32f), new Color(0.34f, 0.3f, 0.28f),
                        "PARK CAFE", new Color(0.3f, 0.5f, 0.32f), Color.white);
                    CafeTables(parent, gx, ground, rng, false);
                    break;
                case "surfSchool": SurfSchool(parent, gx, ground, rng); break;
                case "lifeguard": LifeguardStop(parent, gx, ground); break;
                case "station": Station(parent, gx, gy); break;
                case "siteOffice": SiteOffice(parent, gx, gy, rng); break;
                case "bandstand": Bandstand(parent, gx, gy, rng); break;
                case "boathouse": Boathouse(parent, gx, gy, rng); break;
                case "allotment": Allotment(parent, gx, gy, rng); break;
                default:
                    Debug.LogWarning("[Kick Off] No set piece for the stop \"" + stop.id + "\": only its sign is built.");
                    PostBoard(parent, stop.signName.ToUpperInvariant(), gx - 1.2f, gy, 2.3f, 0.07f, new Color(0.25f, 0.3f, 0.4f), Color.white);
                    break;
            }
        }

        /// <summary>A seed from the stop's id that is the same on every machine (string hashes are not).</summary>
        static int Seed(string id)
        {
            int h = 17;
            foreach (char c in id) h = unchecked(h * 31 + c);
            return h & 0x7fffffff;
        }

        // ---------------------------------------------------------------- name boards

        /// <summary>
        /// A painted name board: a plate in <paramref name="plate"/> with the text across it in <paramref name="ink"/>, its middle at
        /// <paramref name="center"/>, facing the street. <paramref name="charSize"/> is the lettering's TextMesh size (0.06 is the
        /// levels' signboards, about 0.135 m a letter).
        /// </summary>
        public static GameObject NameBoard(Transform parent, string text, Vector3 center, float charSize, Color plate, Color ink)
        {
            string[] lines = text.Split('\n');
            int longest = 0;
            foreach (var l in lines) longest = Mathf.Max(longest, l.Length);
            var size = new Vector3(longest * charSize * 2.25f + charSize * 6f, lines.Length * charSize * 5f + charSize * 3.5f, 0.08f);
            var board = Solid(parent, "NameBoard_" + lines[0], center, size, plate).gameObject;
            // A thin darker frame round it.
            Solid(board.transform, "Frame", center + new Vector3(0f, 0f, 0.02f), new Vector3(size.x + 0.08f, size.y + 0.08f, 0.06f), Color.Lerp(plate, Color.black, 0.35f));
            var textGo = new GameObject("Text");
            textGo.transform.SetParent(board.transform, false);
            textGo.transform.position = center + new Vector3(0f, 0f, -0.05f);
            var mesh = textGo.AddComponent<TextMesh>();
            mesh.text = text;
            mesh.font = LevelBuildKit.SignFont;
            mesh.fontSize = 48;
            mesh.characterSize = charSize;
            mesh.anchor = TextAnchor.MiddleCenter;
            mesh.alignment = TextAlignment.Center;
            mesh.color = ink;
            var renderer = textGo.GetComponent<MeshRenderer>();
            if (LevelBuildKit.SignFont != null) renderer.sharedMaterial = LevelBuildKit.SignFont.material;
            renderer.sortingOrder = 6;
            return board;
        }

        /// <summary>A name board on two posts planted at (x, gy, z), its bottom 1.3 m up.</summary>
        static void PostBoard(Transform parent, string text, float x, float gy, float z, float charSize, Color plate, Color ink)
        {
            var board = NameBoard(parent, text, new Vector3(x, gy + 1.6f, z), charSize, plate, ink);
            var size = board.GetComponent<Box3D>().size;
            float top = gy + 1.6f - size.y * 0.5f;
            foreach (float dx in new[] { -size.x * 0.5f + 0.15f, size.x * 0.5f - 0.15f })
                Solid(parent, "BoardPost", new Vector3(x + dx, (gy + top) * 0.5f, z + 0.08f), new Vector3(0.09f, top - gy + 0.05f, 0.09f), new Color(0.4f, 0.3f, 0.22f));
            board.transform.position = new Vector3(x, top + size.y * 0.5f, z);
        }

        // ---------------------------------------------------------------- Home Street

        /// <summary>
        /// Elm Street's bus stop: a glass-backed shelter with a bench and the timetable at the back of the footpath, the stop's
        /// round sign on its pole at the kerb side of the shelter, a bin, and a hedge behind.
        /// </summary>
        static void BusStop(Transform p, float gx, float gy, System.Random rng)
        {
            if (FL && LevelBuildKit.HasKitModel("Florida", "BusShelterFL")) { BusStopFL(p, gx, gy, rng); return; }
            Color frame = new Color(0.22f, 0.38f, 0.34f), glass = new Color(0.78f, 0.88f, 0.92f);
            float sx = gx + 1.7f, z0 = PoleZ + 0.1f, z1 = PropertyZ + 1.15f, h = 2.35f, half = 1.75f;
            foreach (float dx in new[] { -half, half })
                foreach (float z in new[] { z0, z1 })
                    Solid(p, "ShelterPost", new Vector3(sx + dx, gy + h * 0.5f, z), new Vector3(0.08f, h, 0.08f), frame);
            Solid(p, "ShelterRoof", new Vector3(sx, gy + h + 0.05f, (z0 + z1) * 0.5f), new Vector3(half * 2f + 0.3f, 0.1f, z1 - z0 + 0.35f), frame);
            Solid(p, "ShelterBack", new Vector3(sx, gy + 1.3f, z1), new Vector3(half * 2f, 1.9f, 0.04f), glass);
            Solid(p, "ShelterSide", new Vector3(sx + half, gy + 1.3f, (z0 + z1) * 0.5f + 0.15f), new Vector3(0.04f, 1.9f, z1 - z0 - 0.3f), glass);
            NameBoard(p, "BUS STOP", new Vector3(sx, gy + h - 0.12f, z0 - 0.13f), 0.045f, frame, Color.white);
            if (Model(p, "Street", "Bench", sx - 0.2f, gy, z1 - 0.45f) == null)
                Solid(p, "ShelterSeat", new Vector3(sx - 0.2f, gy + 0.45f, z1 - 0.35f), new Vector3(1.6f, 0.08f, 0.4f), new Color(0.6f, 0.45f, 0.3f));
            NameBoard(p, "TIMES", new Vector3(sx - 1.1f, gy + 1.55f, z1 - 0.06f), 0.02f, Color.white, new Color(0.2f, 0.25f, 0.4f));

            // The stop's sign: a round plate on a pole, red rim, white face.
            float px = gx - 0.75f, pz = PoleZ - 0.05f;
            Solid(p, "StopPole", new Vector3(px, gy + 1.4f, pz), new Vector3(0.07f, 2.8f, 0.07f), new Color(0.55f, 0.57f, 0.6f));
            Disc(p, "StopPlateRim", new Vector3(px, gy + 2.55f, pz - 0.06f), 0.36f, new Color(0.85f, 0.2f, 0.18f));
            Disc(p, "StopPlate", new Vector3(px, gy + 2.55f, pz - 0.09f), 0.29f, Color.white);
            Lettering(p, "BUS", new Vector3(px, gy + 2.55f, pz - 0.12f), 0.035f, new Color(0.2f, 0.25f, 0.45f));

            Model(p, "Street", "Bin", gx + 4.0f, gy, PoleZ + 0.1f);
            Row(p, "Plants", "HedgeBlock2", gx - 1.5f, gx + 5.6f, gy, z1 + 0.7f, HedgeGreen);
            Plant(p, "Broadleaf", null, gx + 5.0f, gy, z1 + 4.5f, 1.1f, 1f, -70, rng);
        }

        /// <summary>A flat disc facing the street (a round sign, a clock face).</summary>
        static void Disc(Transform p, string name, Vector3 center, float radius, Color color)
        {
            var go = new GameObject(name);
            go.transform.SetParent(p, false);
            go.transform.position = center;
            var shape = go.AddComponent<CylinderShape>();
            shape.axis = Vector3.forward;
            shape.radius = radius;
            shape.length = 0.04f;
            shape.sideColor = Color.Lerp(color, Color.black, 0.2f);
            shape.endColor = color;
            shape.segments = 28;
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            shape.Rebuild();
        }

        /// <summary>Text with no plate of its own, facing the street.</summary>
        static void Lettering(Transform p, string text, Vector3 at, float charSize, Color ink)
        {
            var textGo = new GameObject("Lettering_" + text);
            textGo.transform.SetParent(p, false);
            textGo.transform.position = at;
            var mesh = textGo.AddComponent<TextMesh>();
            mesh.text = text;
            mesh.font = LevelBuildKit.SignFont;
            mesh.fontSize = 48;
            mesh.characterSize = charSize;
            mesh.anchor = TextAnchor.MiddleCenter;
            mesh.alignment = TextAlignment.Center;
            mesh.color = ink;
            var renderer = textGo.GetComponent<MeshRenderer>();
            if (LevelBuildKit.SignFont != null) renderer.sharedMaterial = LevelBuildKit.SignFont.material;
            renderer.sortingOrder = 6;
        }

        /// <summary>
        /// A house behind a front garden, its door under the gate at <paramref name="gx"/> (the kit's door is
        /// <paramref name="doorFromMiddle"/> from the middle of its front): a picket fence along the street with an open gateway
        /// between two pillars, a path to the door, hedges at the ends of the plot. What the garden holds is the caller's.
        /// </summary>
        static void FrontGarden(Transform p, float gx, float gy, string model, float doorFromMiddle, Color wall, Color trim, Color roof, Color fence,
            string kit = "Buildings", float setback = 0f)
        {
            float wallZ = PropertyZ + 0.15f, houseZ = HomeHouseZ + setback;
            float plotA = gx + StopPlotLeft + 0.2f, plotB = gx + StopPlotRight - 0.2f;
            float gateL = gx - 0.75f, gateR = gx + 0.75f;
            float houseX = gx - doorFromMiddle;
            float halfW = kit == "Buildings" ? 3.4f : LevelBuildKit.KitSize(kit, model).x * 0.5f;
            if (Model(p, kit, model, houseX, gy, houseZ, 0f, 1f, wall, trim, roof) != null)
                ContactShadow(p, houseX - halfW, houseX + halfW, gy, houseZ - 0.45f, houseZ);
            else
                Building(p, houseX, gy, houseZ, ProceduralArt.FacadeKind.Bungalow, House3D.RoofStyle.GableSideways, 7f, 2.2f, wall, roof);
            float steps = kit == "Buildings" ? 0.62f : -LevelBuildKit.KitMin(kit, model).z + 0.02f;
            Patch(p, "GardenPath", gx - 0.6f, gx + 0.6f, gy, wallZ + 0.25f, Mathf.Max(wallZ + 0.5f, houseZ - steps), new Color(0.88f, 0.86f, 0.82f), Art.surfaces[ProceduralArt.Surface.Paving], 0.014f);
            if (Row(p, "Street", "PicketFence2", plotA + 0.25f, gateL - 0.25f, gy, wallZ, fence))
                Row(p, "Street", "PicketFence2", gateR + 0.25f, plotB - 0.25f, gy, wallZ, fence);
            else
            {
                var wallMat = Art.surfaces[ProceduralArt.Surface.BlockWall];
                BlockWall(p, plotA + 0.25f, gateL - 0.25f, gy, wallMat, false, false);
                BlockWall(p, gateR + 0.25f, plotB - 0.25f, gy, wallMat, false, false);
            }
            foreach (float px in new[] { plotA, gateL, gateR, plotB })
                Model(p, "Street", "WallPillar", px, gy, wallZ);
        }

        /// <summary>
        /// Granny's house at the foot of Hill Road: a pastel bungalow behind a white picket fence, a garden full of flowers and
        /// roses, a bench under the window, her cat on the gatepost, and a little painted sign. Granny waits at the gate (the
        /// track builder adds her).
        /// </summary>
        static void GrannysHouse(Transform p, float gx, float gy, System.Random rng)
        {
            // (Florida: an Old Florida frame cottage, pink with a green door, its porch and swing where the bench was.)
            bool fl = FL && LevelBuildKit.HasKitModel("Florida", "CottageFL");
            if (fl) FrontGarden(p, gx, gy, "CottageFL", 0f, new Color(0.95f, 0.76f, 0.8f), new Color(0.36f, 0.58f, 0.44f), new Color(0.78f, 0.79f, 0.8f), new Color(0.98f, 0.98f, 0.96f),
                "Florida", CottageSetbackFL);
            else FrontGarden(p, gx, gy, "Bungalow", 0.625f, new Color(0.96f, 0.9f, 0.94f), new Color(0.36f, 0.58f, 0.44f), new Color(0.72f, 0.42f, 0.34f), new Color(0.98f, 0.98f, 0.96f));
            float wallZ = PropertyZ + 0.15f;
            float[] bedX = { -3.6f, -2.7f, -1.6f, 1.4f, 2.3f, 3.4f, 4.6f, 5.7f }, bedZ = { 2.9f, 3.3f, 2.85f, 2.9f, 3.35f, 2.9f, 3.2f, 2.85f };
            for (int i = 0; i < bedX.Length; i++)
                Model(p, "Plants", "FlowerPatch", gx + bedX[i], gy, bedZ[i], Rand(rng, 0f, 360f), Rand(rng, 1.1f, 1.5f), null, Petals[i % Petals.Length]);
            Model(p, "Plants", "ShrubFlowering", gx - 3.2f, gy, HomeHouseZ - 0.4f, Rand(rng, 0f, 360f), 1.1f);
            Model(p, "Plants", "ShrubFlowering", gx + 3.5f, gy, HomeHouseZ - 0.3f, Rand(rng, 0f, 360f), 1f);
            if (!fl) Model(p, "Street", "Bench", gx - 2.4f, gy, HomeHouseZ - 1.0f, 0f, 0.95f);     // (the cottage has its porch swing)
            Model(p, "Street", "PotGroup", gx + 1.1f, gy, HomeHouseZ - 0.7f, 10f, 1f, Petals[4]);
            // Her cat on the left gatepost, and her sign on the right one.
            Model(p, "Animals", "Cat", gx - 0.75f, gy + 1.95f, wallZ, 200f, 0.9f, new Color(0.95f, 0.62f, 0.3f));
            NameBoard(p, "Granny's", new Vector3(gx + 0.75f, gy + 1.35f, wallZ - 0.3f), 0.022f, new Color(0.98f, 0.95f, 0.85f), new Color(0.45f, 0.3f, 0.55f));
            if (fl && LevelBuildKit.HasKitModel("Plants", "LiveOak")) Plant(p, "LiveOak", null, gx + 5.4f, gy, HomeHouseZ + 9.5f, 0.95f, 1f, -70, rng);
            else Plant(p, "BroadleafWide", null, gx + 6.2f, gy, HomeHouseZ + 6.5f, 1.05f, 1f, -70, rng);
        }

        /// <summary>
        /// Sam's house in Garden Lane: a flat-roofed family house in bright paint, bikes and a ball on the lawn, the number on the
        /// gatepost. Sam waits at the gate with a backpack on (the track builder adds Sam).
        /// </summary>
        static void SamsHouse(Transform p, float gx, float gy, System.Random rng)
        {
            // (Florida: a little block ranch in butter yellow with a teal door.)
            bool fl = FL && LevelBuildKit.HasKitModel("Florida", "RanchSmallFL");
            if (fl) FrontGarden(p, gx, gy, "RanchSmallFL", 0.125f, new Color(0.96f, 0.88f, 0.6f), new Color(0.2f, 0.5f, 0.56f), new Color(0.86f, 0.86f, 0.84f), new Color(0.96f, 0.97f, 0.98f),
                "Florida", 0.4f);
            else FrontGarden(p, gx, gy, "HouseFlat", -2.55f, new Color(0.78f, 0.88f, 0.95f), new Color(0.98f, 0.78f, 0.25f), new Color(0.3f, 0.32f, 0.36f), new Color(0.96f, 0.97f, 0.98f));
            float wallZ = PropertyZ + 0.15f;
            Plaque(p, "12", gx - 0.75f, gy + 1.3f, wallZ - 0.25f);
            Model(p, "Street", "Bicycle", gx + 2.6f, gy, 3.05f, -10f, 1f, BikeColors[1]);
            Model(p, "Street", "Bicycle", gx + 3.5f, gy, 3.2f, 5f, 0.85f, BikeColors[0]);
            // A football left on the lawn.
            var ball = new GameObject("LawnBall");
            ball.transform.SetParent(p, false);
            ball.transform.position = new Vector3(gx - 2.0f, gy + 0.11f, 3.0f);
            var sphere = ball.AddComponent<SphereShape>();
            sphere.radius = 0.11f;
            ball.GetComponent<MeshRenderer>().sharedMaterial = Art.ball;
            sphere.Rebuild();
            Model(p, "Plants", "BushRound", gx - 3.4f, gy, 3.6f, Rand(rng, 0f, 360f), 0.9f, SummerLeaves[1]);
            Model(p, "Street", "PotGroup", gx + 5.8f, gy, HomeHouseZ - 0.6f, -12f, 1f, Petals[2]);
            if (fl) Plant(p, "PalmSabal", null, gx + 6.6f, gy, HomeHouseZ + 1.2f, 0.75f, 1f, -60, rng);
        }

        /// <summary>
        /// St Mary's at the top of Hill Road: a stone church with a gable to the street, an arched door, a round window and tall
        /// windows, a square tower with a clock, a belfry and a slate spire with a cross; a low churchyard wall with its gateway
        /// on the footpath, a path to the door, dark conifers, a bench and the notice board.
        /// </summary>
        static void Church(Transform p, float gx, float gy, System.Random rng)
        {
            if (FL && LevelBuildKit.HasKitModel("Florida", "ChurchFL")) { MissionChurchFL(p, gx, gy, rng); return; }
            Color stone = new Color(0.86f, 0.83f, 0.76f), trim = new Color(0.7f, 0.67f, 0.6f), slate = new Color(0.33f, 0.36f, 0.43f);
            Color glass = new Color(0.36f, 0.46f, 0.74f), wood = new Color(0.4f, 0.25f, 0.16f);
            float front = 7.0f, wallZ = PropertyZ + 0.15f;
            const float width = 7.4f, wallH = 6.2f, depth = 13f;

            // The nave: a gable to the street, plain stone walls, a slate roof.
            var nave = new GameObject("Nave");
            nave.transform.SetParent(p, false);
            nave.transform.position = new Vector3(gx, gy, front);
            var house = nave.AddComponent<House3D>();
            house.width = width;
            house.wallHeight = wallH;
            house.depth = depth;
            house.roof = House3D.RoofStyle.GableToStreet;
            house.roofHeight = 4.2f;
            house.wallColor = stone;
            house.roofColor = slate;
            house.trimColor = trim;
            nave.GetComponent<MeshRenderer>().sharedMaterials = new[] { Art.solid, Art.solid, Art.surfaces[ProceduralArt.Surface.RoofTiles] };
            house.Rebuild();
            ContactShadow(p, gx - width * 0.5f, gx + width * 0.5f, gy, front - 0.45f, front);

            // The front: an arched door, a round window over it, two tall windows.
            Solid(p, "ChurchDoor", new Vector3(gx, gy + 1.35f, front - 0.04f), new Vector3(1.5f, 2.7f, 0.08f), wood);
            Disc(p, "DoorArch", new Vector3(gx, gy + 2.7f, front - 0.04f), 0.75f, wood);
            Solid(p, "DoorStep", new Vector3(gx, gy + 0.08f, front - 0.45f), new Vector3(2.2f, 0.16f, 0.9f), trim);
            Disc(p, "RoseWindowRim", new Vector3(gx, gy + 6.4f, front - 0.04f), 0.95f, trim);
            Disc(p, "RoseWindow", new Vector3(gx, gy + 6.4f, front - 0.08f), 0.78f, glass);
            foreach (float dx in new[] { -2.3f, 2.3f })
            {
                Solid(p, "TallWindow", new Vector3(gx + dx, gy + 3.4f, front - 0.04f), new Vector3(0.62f, 2.4f, 0.06f), glass);
                Disc(p, "TallWindowArch", new Vector3(gx + dx, gy + 4.6f, front - 0.04f), 0.31f, glass);
                Solid(p, "Sill", new Vector3(gx + dx, gy + 2.15f, front - 0.08f), new Vector3(0.85f, 0.1f, 0.14f), trim);
            }

            // The tower on the left, a little in front of the nave: belfry, clock, spire and cross.
            float tx = gx - width * 0.5f - 1.7f, tz = front + 0.6f;
            const float towerW = 3.2f, towerH = 13f;
            Solid(p, "Tower", new Vector3(tx, gy + towerH * 0.5f, tz + towerW * 0.5f), new Vector3(towerW, towerH, towerW), stone);
            Solid(p, "TowerBand", new Vector3(tx, gy + towerH - 0.2f, tz + towerW * 0.5f), new Vector3(towerW + 0.2f, 0.4f, towerW + 0.2f), trim);
            foreach (float dx in new[] { -0.6f, 0.6f })
            {
                Solid(p, "Belfry", new Vector3(tx + dx, gy + towerH - 1.9f, tz - 0.03f), new Vector3(0.5f, 1.6f, 0.06f), new Color(0.18f, 0.18f, 0.22f));
                Disc(p, "BelfryArch", new Vector3(tx + dx, gy + towerH - 1.1f, tz - 0.03f), 0.25f, new Color(0.18f, 0.18f, 0.22f));
            }
            Disc(p, "ClockRim", new Vector3(tx, gy + 8.4f, tz - 0.04f), 0.78f, trim);
            Disc(p, "Clock", new Vector3(tx, gy + 8.4f, tz - 0.08f), 0.66f, new Color(0.97f, 0.96f, 0.9f));
            var hour = Solid(p, "HourHand", new Vector3(tx + 0.12f, gy + 8.47f, tz - 0.12f), new Vector3(0.05f, 0.34f, 0.02f), new Color(0.15f, 0.15f, 0.2f));
            hour.transform.rotation = Quaternion.Euler(0f, 0f, -60f);     // ten to eight: not long until the bell
            var minute = Solid(p, "MinuteHand", new Vector3(tx - 0.16f, gy + 8.62f, tz - 0.13f), new Vector3(0.04f, 0.5f, 0.02f), new Color(0.15f, 0.15f, 0.2f));
            minute.transform.rotation = Quaternion.Euler(0f, 0f, 60f);
            var spireGo = new GameObject("Spire");
            spireGo.transform.SetParent(p, false);
            spireGo.transform.position = new Vector3(tx, gy + towerH, tz + towerW * 0.5f);
            spireGo.transform.rotation = Quaternion.Euler(0f, 45f, 0f);
            var spire = spireGo.AddComponent<SpireShape>();
            spire.radius = towerW * 0.5f * 1.414f + 0.15f;
            spire.height = 6.5f;
            spire.sides = 4;
            spire.color = slate;
            spireGo.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            spire.Rebuild();
            Color gold = new Color(0.95f, 0.78f, 0.3f);
            Solid(p, "CrossUpright", new Vector3(tx, gy + towerH + 6.5f + 0.5f, tz + towerW * 0.5f), new Vector3(0.12f, 1.0f, 0.12f), gold);
            Solid(p, "CrossBar", new Vector3(tx, gy + towerH + 6.5f + 0.68f, tz + towerW * 0.5f), new Vector3(0.6f, 0.12f, 0.12f), gold);

            // The churchyard: a low stone wall with its gateway, the path, conifers, a bench and the notice board.
            float a = gx + ChurchPlotLeft + 0.2f, b = gx + ChurchPlotRight - 0.2f;
            foreach (var run in new[] { new Vector2(a, gx - 0.9f), new Vector2(gx + 0.9f, b) })
            {
                float len = run.y - run.x, mid = (run.x + run.y) * 0.5f;
                Solid(p, "ChurchyardWall", new Vector3(mid, gy + 0.42f, wallZ), new Vector3(len, 0.84f, 0.38f), stone, Art.surfaces[ProceduralArt.Surface.BlockWall]);
                Solid(p, "WallCoping", new Vector3(mid, gy + 0.88f, wallZ), new Vector3(len + 0.05f, 0.1f, 0.48f), trim);
            }
            foreach (float px in new[] { gx - 0.9f, gx + 0.9f })
                Solid(p, "GatePier", new Vector3(px, gy + 0.65f, wallZ), new Vector3(0.48f, 1.3f, 0.48f), trim);
            Patch(p, "ChurchPath", gx - 0.75f, gx + 0.75f, gy, wallZ + 0.25f, front - 0.9f, new Color(0.86f, 0.84f, 0.8f), Art.surfaces[ProceduralArt.Surface.Paving], 0.014f);
            Patch(p, "Churchyard", a, b, gy, wallZ + 0.25f, front + 0.5f, new Color(0.62f, 0.78f, 0.45f), Art.surfaces[ProceduralArt.Surface.Grass], 0.01f);
            Plant(p, "ConiferTall", null, gx + 5.6f, gy, front + 2.5f, 1.1f, 1f, -70, rng);
            Plant(p, "ConiferMid", null, gx - 6.6f, gy, front - 2.6f, 1f, 1f, -70, rng);
            Plant(p, "ConiferMid", null, gx + 6.2f, gy, front - 3.2f, 0.9f, 1f, -70, rng);
            Model(p, "Street", "Bench", gx + 3.4f, gy, front - 2.6f, 0f, 0.95f);
            PostBoard(p, "ST MARY'S\nCHURCH", gx - 2.4f, gy, wallZ + 0.55f, 0.04f, new Color(0.22f, 0.3f, 0.5f), new Color(0.98f, 0.92f, 0.7f));
        }

        // ---------------------------------------------------------------- shops and cafes

        /// <summary>
        /// A shop of the Buildings kit with its door at <paramref name="gx"/> (the kit's door is <paramref name="doorFromMiddle"/>
        /// from its middle), painted for the stop, and the stop's name on a board over the door.
        /// </summary>
        static void ShopStop(Transform p, Stop stop, float gx, Func<float, float, float> ground, string model, float doorFromMiddle,
            Color wall, Color trim, Color roof, string board, Color plate, Color ink)
        {
            float z = StopFrontZ(stop);
            float houseX = gx - doorFromMiddle, gy = ground(gx, z);
            Vector3 size = LevelBuildKit.KitSize("Buildings", model);
            if (Model(p, "Buildings", model, houseX, gy, z, 0f, 1f, wall, trim, roof) != null)
                ContactShadow(p, houseX - size.x * 0.5f, houseX + size.x * 0.5f, gy, z - 0.45f, z);
            else
                Building(p, houseX, gy, z, ProceduralArt.FacadeKind.Shop0, House3D.RoofStyle.Flat, 8f, 0f, wall, roof);
            NameBoard(p, board, new Vector3(gx, gy + 3.85f, z - 0.12f), 0.075f, plate, ink);
            // Paving to the door from the footpath (on the sand and in the park there is no pavement of its own).
            if (LevelBuildKit.Chapter == 3 || LevelBuildKit.Chapter == 5)
                Patch(p, "Forecourt", gx - 1.2f, gx + 1.2f, Mathf.Min(gy, ground(gx, PathHalf)), PathHalf + 0.1f, z - 0.3f, new Color(0.9f, 0.86f, 0.78f),
                    Art.surfaces[LevelBuildKit.Chapter == 3 ? ProceduralArt.Surface.Paving : ProceduralArt.Surface.Gravel], 0.02f);
        }

        /// <summary>Tables out front for a cafe: under parasols on the sand, or picnic tables on the lawn, and its chalkboard.</summary>
        static void CafeTables(Transform p, float gx, Func<float, float, float> ground, System.Random rng, bool beach)
        {
            Color[] canopy = { new Color(0.9f, 0.3f, 0.28f), new Color(0.25f, 0.5f, 0.85f), new Color(1f, 0.75f, 0.2f) };
            float[] tx = { -3.2f, 3.6f, 5.6f };
            for (int i = 0; i < tx.Length; i++)
            {
                float x = gx + tx[i], z = 2.9f + (i % 2) * 0.5f;
                Model(p, "Leisure", "PicnicTable", x, ground(x, z), z, i * 23f);
                if (beach || i == 1)
                    Model(p, "Leisure", "Parasol", x, ground(x, z) - 0.05f, z, Rand(rng, 0f, 360f), 1f, canopy[i % canopy.Length]);
            }
            Model(p, "Street", "SignBoardA", gx - 1.3f, ground(gx - 1.3f, 2.4f), 2.4f, -18f);
            if (beach)
            {
                Model(p, "Leisure", "CoolBox", gx + 1.5f, ground(gx + 1.5f, 3.1f), 3.1f, 30f);
                Plant(p, "Palm", null, gx + 7.0f, ground(gx + 7f, 5.5f), 5.5f, 1.1f, 1f, -70, rng);
            }
            else
            {
                Model(p, "Street", "Bin", gx + 1.6f, ground(gx + 1.6f, 2.3f), 2.3f);
                Plant(p, "BroadleafLarge", null, gx - 5.5f, ground(gx - 5.5f, 7f), 7f, 1.1f, 1f, -70, rng);
            }
        }

        // ---------------------------------------------------------------- the beach

        /// <summary>
        /// The beach cafe: a kiosk on the dry sand with its serving hatch, an awning and its name (a small building: the Buildings
        /// kit's shops are 8 m deep and would stand in the sea, which starts about 9.6 m behind the footpath).
        /// </summary>
        static void BeachKiosk(Transform p, float gx, Func<float, float, float> ground)
        {
            float hx = gx + 0.4f, hz = 3.3f, gy = ground(hx, hz);
            Color white = new Color(0.97f, 0.97f, 0.95f), teal = new Color(0.2f, 0.62f, 0.72f);
            // (Florida: the weathered snack shack with its hatch propped up, in the café's teal)
            bool shack = FL && Model(p, "Florida", "ShackFL", hx, gy, hz, 0f, 1f, null, new Color(0.42f, 0.72f, 0.78f)) != null;
            if (!shack && Model(p, "Buildings", "Garage", hx, gy, hz, 0f, 1.15f, white, teal, new Color(0.85f, 0.42f, 0.32f)) == null)
            {
                Solid(p, "Kiosk", new Vector3(hx, gy + 1.4f, hz + 2.4f), new Vector3(3.6f, 2.8f, 4.8f), white);
                Solid(p, "KioskRoof", new Vector3(hx, gy + 2.9f, hz + 2.4f), new Vector3(4f, 0.2f, 5.2f), teal);
            }
            if (!shack) Model(p, "Street", "Awning", hx, gy + 2.2f, hz - 0.05f, 0f, 1.5f, teal);
            NameBoard(p, "BEACH CAFE", new Vector3(hx, gy + 3.75f, hz - 0.15f), 0.06f, teal, Color.white);
            foreach (float dx in new[] { -1.4f, 1.4f })
                Solid(p, "BoardPost", new Vector3(hx + dx, gy + 1.85f, hz - 0.1f), new Vector3(0.1f, 3.7f, 0.1f), new Color(0.45f, 0.34f, 0.24f));
        }

        /// <summary>The surf school on the sand: its hut with the name over the door, the board rack, towels and a flag.</summary>
        static void SurfSchool(Transform p, float gx, Func<float, float, float> ground, System.Random rng)
        {
            // The hut is 5 m deep: at 3.6 m behind the footpath it ends well before the water's edge.
            float hx = gx + 1.6f, hz = 3.6f, gy = ground(hx, hz);
            Color white = new Color(0.97f, 0.97f, 0.95f), blue = new Color(0.18f, 0.5f, 0.78f);
            bool shack = FL && Model(p, "Florida", "ShackFL", hx, gy, hz, 0f, 1f, null, new Color(0.30f, 0.56f, 0.80f)) != null;
            if (!shack && Model(p, "Buildings", "Garage", hx, gy, hz, 0f, 1f, white, blue, new Color(0.85f, 0.42f, 0.32f)) == null)
            {
                Solid(p, "SurfHut", new Vector3(hx, gy + 1.4f, hz + 2f), new Vector3(3.2f, 2.8f, 4f), white);
                Solid(p, "SurfHutRoof", new Vector3(hx, gy + 2.9f, hz + 2f), new Vector3(3.6f, 0.2f, 4.4f), blue);
            }
            NameBoard(p, "SURF SCHOOL", new Vector3(hx, gy + 3.85f, hz - 0.15f), 0.06f, blue, Color.white);
            Solid(p, "BoardPost", new Vector3(hx - 1.3f, gy + 1.9f, hz - 0.1f), new Vector3(0.1f, 3.8f, 0.1f), new Color(0.45f, 0.34f, 0.24f));
            Solid(p, "BoardPost", new Vector3(hx + 1.3f, gy + 1.9f, hz - 0.1f), new Vector3(0.1f, 3.8f, 0.1f), new Color(0.45f, 0.34f, 0.24f));
            float rx = gx - 2.4f, rz = 3.4f;
            Model(p, "Barriers", "SurfRack", rx, ground(rx, rz), rz, 0f, 0.9f);
            Color[] towels = { new Color(0.95f, 0.55f, 0.6f), new Color(1f, 0.85f, 0.35f) };
            for (int i = 0; i < 2; i++)
            {
                float x = gx + 4.4f + i * 1.3f, z = 3.0f + i * 0.4f;
                Model(p, "Leisure", "BeachTowel", x, ground(x, z), z, Rand(rng, -20f, 20f), 1f, towels[i]);
            }
            Model(p, "Street", "BannerFlag", gx + 3.8f, ground(gx + 3.8f, 2.6f), 2.6f, 0f, 1f, blue, Color.white);
        }

        /// <summary>The lifeguard tower on the sand with its rescue boards and the red and yellow flags.</summary>
        static void LifeguardStop(Transform p, float gx, Func<float, float, float> ground)
        {
            float tx = gx + 2.0f, tz = 4.6f;
            LifeguardTower(p, tx, ground(tx, tz), tz);
            Model(p, "Barriers", "RescueBoardStand", gx - 1.8f, ground(gx - 1.8f, 3.6f), 3.6f);
            Color red = new Color(0.9f, 0.2f, 0.18f), yellow = new Color(1f, 0.82f, 0.2f);
            foreach (float dx in new[] { -0.9f, 4.6f })
                Model(p, "Street", "BannerFlag", gx + dx, ground(gx + dx, 2.5f), 2.5f, 0f, 1f, red, yellow);
            PostBoard(p, "LIFEGUARD", gx + 4.9f, ground(gx + 4.9f, 3.4f), 3.4f, 0.055f, red, Color.white);
        }

        // ---------------------------------------------------------------- the town's middle

        /// <summary>
        /// The railway station's ticket hall on Station Road: a brick hall with its wide doorway at <paramref name="gx"/>, STATION
        /// in big letters and a clock over it, the railway's red band along the front (the red of the map's train), benches and a
        /// bike rack.
        /// </summary>
        static void Station(Transform p, float gx, float gy)
        {
            float z = PropertyZ + 1.6f, hx = gx + 2.2f;
            Color brick = new Color(0.74f, 0.44f, 0.36f), cream = new Color(0.95f, 0.9f, 0.8f), slate = new Color(0.33f, 0.35f, 0.42f);
            Vector3 size = LevelBuildKit.KitSize("Buildings", "Warehouse");
            if (Model(p, "Buildings", "Warehouse", hx, gy, z, 0f, 1f, brick, cream, slate) != null)
                ContactShadow(p, hx - size.x * 0.5f, hx + size.x * 0.5f, gy, z - 0.45f, z);
            else
                Building(p, hx, gy, z, ProceduralArt.FacadeKind.Warehouse, House3D.RoofStyle.Flat, 8f, 0f, brick, slate);
            Color red = new Color(0.80f, 0.18f, 0.16f);
            Solid(p, "RailwayBand", new Vector3(hx, gy + 5.25f, z - 0.07f), new Vector3(11f, 0.22f, 0.05f), red);
            NameBoard(p, "STATION", new Vector3(gx, gy + 4.55f, z - 0.14f), 0.1f, red, Color.white);
            float cx = gx + 3.4f;
            Disc(p, "StationClockRim", new Vector3(cx, gy + 4.55f, z - 0.12f), 0.48f, new Color(0.2f, 0.22f, 0.28f));
            Disc(p, "StationClock", new Vector3(cx, gy + 4.55f, z - 0.16f), 0.4f, Color.white);
            var hand = Solid(p, "ClockHand", new Vector3(cx + 0.07f, gy + 4.6f, z - 0.2f), new Vector3(0.04f, 0.22f, 0.02f), new Color(0.15f, 0.15f, 0.2f));
            hand.transform.rotation = Quaternion.Euler(0f, 0f, -60f);
            Solid(p, "ClockMinute", new Vector3(cx, gy + 4.7f, z - 0.21f), new Vector3(0.03f, 0.32f, 0.02f), new Color(0.15f, 0.15f, 0.2f));
            Model(p, "Street", "Bench", gx + 4.4f, gy, z - 0.8f);
            Model(p, "Street", "BikeRack", gx - 4.0f, gy, z - 0.7f);
            Model(p, "Street", "Bicycle", gx - 4.3f, gy, z - 0.75f, 0f, 1f, BikeColors[3]);
            Model(p, "Street", "StreetLamp", gx - 1.9f, gy, PoleZ);
        }

        /// <summary>
        /// The building site's office: the cabin behind the site fence, the sliding gate run back open at <paramref name="gx"/>, a
        /// portable loo, a cement mixer and a wheelbarrow, and the board at the gate.
        /// </summary>
        static void SiteOffice(Transform p, float gx, float gy, System.Random rng)
        {
            float wallZ = PropertyZ + 0.25f;
            Color yellow = new Color(0.98f, 0.78f, 0.2f), blue = new Color(0.22f, 0.4f, 0.68f);
            Model(p, "Works", "SiteCabin", gx + 2.8f, gy, 4.4f, 0f, 1f, blue, Color.white);
            NameBoard(p, "SITE OFFICE", new Vector3(gx + 1.4f, gy + 2.15f, 2.9f), 0.04f, Color.white, blue);
            Row(p, "Works", "SiteFence", gx + StopPlotLeft + 0.2f, gx - 1.3f, gy, wallZ, yellow);
            Row(p, "Works", "SiteFence", gx + 6.8f, gx + StopPlotRight - 0.2f, gy, wallZ, yellow);
            Model(p, "Works", "SlidingGate", gx - 2.6f, gy, wallZ + 0.5f, 90f);
            Model(p, "Works", "PortaLoo", gx + 6.6f, gy, 4.6f, -15f, 1f, blue);
            Model(p, "Works", "CementMixer", gx - 2.4f, gy, 3.5f, 30f, 1f, new Color(0.95f, 0.5f, 0.15f));
            Model(p, "Works", "Wheelbarrow", gx + 0.9f, gy, 2.9f, -25f);
            Model(p, "Street", "TrafficCone", gx - 1.1f, gy, PoleZ - 0.1f, Rand(rng, 0f, 90f));
        }

        // ---------------------------------------------------------------- the park

        /// <summary>The park's bandstand on its lawn, with benches round it, a lamp, flower beds and its board.</summary>
        static void Bandstand(Transform p, float gx, float gy, System.Random rng)
        {
            float bx = gx + 2.0f, bz = 5.0f;
            if (Model(p, "Leisure", "Gazebo", bx, gy, bz, 0f, 1.1f, new Color(0.97f, 0.97f, 0.95f), new Color(0.3f, 0.5f, 0.42f)) == null)
            {
                Solid(p, "BandstandFloor", new Vector3(bx, gy + 0.3f, bz), new Vector3(4.4f, 0.6f, 4.4f), new Color(0.9f, 0.88f, 0.84f));
                Solid(p, "BandstandRoof", new Vector3(bx, gy + 3.4f, bz), new Vector3(4.8f, 0.3f, 4.8f), new Color(0.3f, 0.5f, 0.42f));
            }
            Model(p, "Street", "Bench", gx - 1.9f, gy, 3.1f, 15f);
            Model(p, "Street", "Bench", gx + 5.8f, gy, 3.1f, -15f);
            Model(p, "Leisure", "ParkLamp", gx - 0.8f, gy, PoleZ + 0.2f);
            for (int i = 0; i < 5; i++)
                Model(p, "Plants", "FlowerPatch", gx - 3.6f + i * 2.4f, gy, 7.8f + (i % 2) * 0.5f, Rand(rng, 0f, 360f), 1.3f, null, Petals[i % Petals.Length]);
            PostBoard(p, "BANDSTAND", gx + 4.1f, gy, 2.4f, 0.045f, new Color(0.3f, 0.5f, 0.42f), Color.white);
        }

        /// <summary>The boathouse on the duck pond: a wooden shed with its name, the pond with a raft, reeds and a bench.</summary>
        static void Boathouse(Transform p, float gx, float gy, System.Random rng)
        {
            float hx = gx + 1.2f, hz = 5.0f;
            Color wood = new Color(0.62f, 0.44f, 0.3f), green = new Color(0.25f, 0.42f, 0.32f);
            if (Model(p, "Buildings", "Garage", hx, gy, hz, 0f, 1.25f, wood, green, green) == null)
                Solid(p, "Boathouse", new Vector3(hx, gy + 1.6f, hz + 2.5f), new Vector3(4f, 3.2f, 5f), wood);
            NameBoard(p, "BOATHOUSE", new Vector3(hx, gy + 3.95f, hz - 0.12f), 0.05f, green, new Color(0.98f, 0.94f, 0.8f));
            foreach (float dx in new[] { -1.55f, 1.55f })
                Solid(p, "BoardPost", new Vector3(hx + dx, gy + 2.0f, hz - 0.08f), new Vector3(0.1f, 4.0f, 0.1f), wood);
            float px = gx + 5.6f, pz = 4.6f;
            Model(p, "Leisure", "DuckPond", px, gy, pz, 0f, 1.2f);
            Model(p, "Leisure", "Raft", px + 0.3f, gy + 0.05f, pz + 0.2f, 20f, 0.8f);
            for (int i = 0; i < 4; i++)
                Model(p, "Plants", "Reeds", px - 2.6f + i * 1.7f, gy, pz + 2.0f + (i % 2) * 0.3f, Rand(rng, 0f, 360f), 1f);
            Model(p, "Street", "Bench", gx - 2.6f, gy, 3.0f, 10f);
        }

        /// <summary>Grandpa's allotment by the railway: a green shed, rows of vegetables, a wheelbarrow, a low fence and the gate's board.</summary>
        static void Allotment(Transform p, float gx, float gy, System.Random rng)
        {
            float wallZ = PropertyZ + 0.15f;
            Color shed = new Color(0.4f, 0.58f, 0.42f);
            if (Model(p, "Buildings", "Garage", gx + 4.6f, gy, 5.6f, 0f, 1f, shed, new Color(0.95f, 0.93f, 0.85f), new Color(0.3f, 0.3f, 0.32f)) == null)
                Solid(p, "Shed", new Vector3(gx + 4.6f, gy + 1.2f, 7.5f), new Vector3(3f, 2.4f, 3.6f), shed);
            Patch(p, "VegetableBeds", gx - 4.2f, gx + 2.6f, gy, 2.6f, 7.0f, new Color(0.55f, 0.42f, 0.32f), Art.surfaces[ProceduralArt.Surface.Gravel], 0.012f);
            for (int row = 0; row < 3; row++)
                for (float x = gx - 3.8f; x < gx + 2.4f; x += 0.9f)
                {
                    float z = 3.1f + row * 1.4f;
                    if (row == 1) Model(p, "Plants", "BushRound", x, gy, z, Rand(rng, 0f, 360f), 0.42f, SummerLeaves[rng.Next(SummerLeaves.Length)]);
                    else Model(p, "Plants", row == 0 ? "GrassTuft" : "FlowerPatch", x, gy, z, Rand(rng, 0f, 360f), 1.2f, row == 0 ? (Color?)new Color(0.42f, 0.66f, 0.3f) : Petals[2]);
                }
            Model(p, "Works", "Wheelbarrow", gx + 1.8f, gy, 2.7f, 25f);
            Row(p, "Street", "PicketFence2", gx + StopPlotLeft + 0.2f, gx - 0.9f, gy, wallZ, new Color(0.62f, 0.5f, 0.38f));
            Row(p, "Street", "PicketFence2", gx + 0.9f, gx + StopPlotRight - 0.2f, gy, wallZ, new Color(0.62f, 0.5f, 0.38f));
            PostBoard(p, "ALLOTMENTS", gx - 2.4f, gy, wallZ + 0.5f, 0.04f, new Color(0.4f, 0.58f, 0.42f), Color.white);
            Plant(p, "Birch", null, gx + 7.2f, gy, 8.5f, 1f, 1f, -70, rng);
        }
    }
}
