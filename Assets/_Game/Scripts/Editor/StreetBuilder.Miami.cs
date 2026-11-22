using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Florida's own districts (docs/CITIES.md: Little Havana, Brickell, the bayfront, the Miami River, old downtown, the
    /// Underline, Biscayne Boulevard, Museum Park), one for each of Florida's legs: what stands along the leg is read from the
    /// plan tools/blender/miami_plan.py writes (Art/Models/Miami/MiamiDistricts.json), the same file the preview renders
    /// (preview_street.py --miami), so the preview is the game. The plan gives each leg its ground (a street of concrete
    /// sidewalks and an asphalt road, a promenade with water behind its seawall, or a park's lawns), its water and any land the
    /// school stands on, and every model with its place. Nothing of another city's streets is built in a Florida leg.
    /// Every Florida leg is in the plan (Riverside Street, FL2-1, too: its ranch houses and live oaks down to the river).
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>Every Miami kit model the game places itself (the plan's are checked from the plan): the tests check the kit has each.</summary>
        public static readonly string[] MiamiModelsUsed =
        {
            "VentanitaMIA", "StopSignMIA", "CoffeeKioskMIA", "BollardMIA", "LineCoilMIA", "PharmacyMIA",
            // LevelBuildKit.FloridaCity: the animals, the scooters, the domino table, the arcades, the sweeper
            "RoosterMIA", "HenMIA", "IguanaMIA", "ScooterMIA", "ScooterUpMIA", "DominoTableMIA", "DecoArcadeMIA", "DecoArcade2MIA",
            "SweeperMIA",
            // LevelBuildKit: the slide-unders' Miami looks, the work zone, the crate, the crossing's signal, the signs, the
            // checkpoints, the fountain; RideBuilder: the Metromover on its guideway over the bay
            "StallAwningMIA", "ScaffoldGantryMIA", "BoatTrestlesMIA", "AppleBoughMIA", "RollShutterMIA", "PipeRackMIA", "BoomBarrierMIA",
            "OakBoughMIA", "BarricadeMIA", "DrumMIA", "CrateMIA", "PedSignalMIA", "SignBoardMIA", "SignPostsMIA", "CheckpointPoleMIA",
            "CheckpointFlagMIA", "FountainMIA", "MetromoverMIA", "GuidewayMIA", "BayRailMIA", "CruiseShipMIA", "FreighterMIA", "TugMIA",
            "CondoTowerMIA", "OfficeTowerMIA", "CondoTower2MIA",
        };

        /// <summary>The Plants kit's trees the plan may place in Florida: Florida's own (the tests hold the plan to these).</summary>
        public static readonly string[] FloridaPlants = { "PalmRoyal", "PalmSabal", "PalmSabalTall", "LiveOak", "Banyan", "SawPalmetto" };

        /// <summary>The stops <see cref="MiamiStop"/> builds from the Miami kit (all of Florida's: the tests check it).</summary>
        public static readonly string[] MiamiStops = { "calleOcho", "brickell", "bayfront", "reysDock", "drugstore", "underline", "biscayne", "museumPark" };

        /// <summary>The plan, beside the Miami kit.</summary>
        public const string MiamiPlanFile = LevelBuildKit.ModelsDir + "/Miami/MiamiDistricts.json";

        static Dictionary<string, object> miamiLegs;
        static DateTime miamiLegsStamp;

        /// <summary>The plan's legs (empty if the plan is missing or unreadable), read again whenever the file changes.</summary>
        static Dictionary<string, object> MiamiLegs
        {
            get
            {
                // (From the project's own folder, not the process's working directory.)
                string path = Path.Combine(Directory.GetParent(Application.dataPath).FullName, MiamiPlanFile);
                DateTime stamp = File.Exists(path) ? File.GetLastWriteTimeUtc(path) : DateTime.MinValue;
                if (miamiLegs != null && stamp == miamiLegsStamp && stamp != DateTime.MinValue) return miamiLegs;
                miamiLegsStamp = stamp;
                miamiLegs = new Dictionary<string, object>();
                try
                {
                    if (stamp != DateTime.MinValue)
                    {
                        var root = MiniJson.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
                        object legs;
                        if (root != null && root.TryGetValue("legs", out legs) && legs is Dictionary<string, object>)
                            miamiLegs = (Dictionary<string, object>)legs;
                    }
                }
                catch (Exception e) { Debug.LogWarning("[Kick Off] " + MiamiPlanFile + " could not be read: " + e.Message); }
                return miamiLegs;
            }
        }

        /// <summary>The plan of the Florida leg being built, or null (not Florida's, not in the plan, or the plan is missing).</summary>
        static Dictionary<string, object> MiamiPlan
        {
            get
            {
                string leg = LevelBuildKit.LevelId;
                if (!LevelBuildKit.Florida || string.IsNullOrEmpty(leg)) return null;
                object plan;
                return MiamiLegs.TryGetValue(leg, out plan) ? plan as Dictionary<string, object> : null;
            }
        }

        /// <summary>The Florida legs whose district was really built in this build of the levels (GeneratedContent checks every one).</summary>
        public static readonly HashSet<string> MiamiDistrictsBuilt = new HashSet<string>();

        /// <summary>Why the leg being built can't have its district: each thing it needs, and whether it has it (for the error).</summary>
        public static string MiamiDiagnosis()
        {
            string leg = LevelBuildKit.LevelId;
            string path = Path.Combine(Directory.GetParent(Application.dataPath).FullName, MiamiPlanFile);
            return "Florida=" + LevelBuildKit.Florida + ", level id=" + (leg ?? "(none)") + ", plan file " + path
                + (File.Exists(path) ? " found" : " NOT FOUND") + ", legs in it: " + string.Join(" ", new List<string>(MiamiLegs.Keys).ToArray())
                + ", Miami kit (VentanitaMIA) " + (LevelBuildKit.HasKitModel("Miami", "VentanitaMIA") ? "imported" : "NOT IMPORTED");
        }

        /// <summary>Is <paramref name="levelId"/> in the plan, and the Miami kit imported, so its district can be built?</summary>
        public static bool HasMiamiDistrict(string levelId)
        {
            return !string.IsNullOrEmpty(levelId) && LevelBuildKit.HasKitModel("Miami", "VentanitaMIA") && MiamiLegs.ContainsKey(levelId);
        }

        /// <summary>The leg being built is one of Florida's own, dressed from the plan (and the Miami kit is there).</summary>
        public static bool MiamiLeg { get { return MiamiPlan != null && LevelBuildKit.HasKitModel("Miami", "VentanitaMIA"); } }

        static string MiamiStr(Dictionary<string, object> d, string key, string fallback)
        {
            object v;
            return d != null && d.TryGetValue(key, out v) && v is string ? (string)v : fallback;
        }

        static float MiamiNum(Dictionary<string, object> d, string key, float fallback)
        {
            object v;
            return d != null && d.TryGetValue(key, out v) && v is double ? (float)(double)v : fallback;
        }

        /// <summary>Where a promenade's seawall stands (the water's edge behind the lane), when the leg has water.</summary>
        static float MiamiWaterZ
        {
            get
            {
                var plan = MiamiPlan;
                object w;
                return plan != null && plan.TryGetValue("water", out w) ? MiamiNum(w as Dictionary<string, object>, "z", BackZ) : BackZ;
            }
        }

        /// <summary>
        /// A Florida leg's ground, by the plan's kind: "street" (an asphalt road with its kerbs in front, the concrete sidewalk the
        /// kid plays on, concrete lots behind), "havana" (the same with lawns behind: Little Havana's yards), "promenade" (a lawn
        /// in front, paving to the seawall, the water behind), "park" (lawns and a paved path). Null for any other leg.
        /// </summary>
        static List<StripSpec> MiamiStrips()
        {
            if (!MiamiLeg) return null;
            string kind = MiamiStr(MiamiPlan, "strips", "street");
            var white = Color.white;
            var s = new List<StripSpec>();
            switch (kind)
            {
                case "promenade":
                {
                    float wz = MiamiWaterZ;
                    s.Add(new StripSpec(FrontZ, -PathHalf, 0.04f, ProceduralArt.Surface.Grass, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Paving, new Color(1f, 0.98f, 0.95f)));
                    s.Add(new StripSpec(PathHalf, wz, 0f, ProceduralArt.Surface.Paving, new Color(0.97f, 0.95f, 0.92f)));
                    break;
                }
                case "park":
                {
                    float wz = Mathf.Min(MiamiWaterZ, BackZ);
                    s.Add(new StripSpec(FrontZ, -PathHalf, 0.04f, ProceduralArt.Surface.Grass, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Paving, new Color(1f, 0.98f, 0.95f)));
                    s.Add(new StripSpec(PathHalf, wz, 0.04f, ProceduralArt.Surface.Grass, new Color(0.95f, 0.98f, 0.9f)));
                    break;
                }
                default:
                    s.Add(new StripSpec(FrontZ, RoadFar - 0.2f, 0f, ProceduralArt.Surface.Concrete, white));
                    s.Add(new StripSpec(RoadFar - 0.2f, RoadFar, 0f, ProceduralArt.Surface.Kerb, white));
                    s.Add(new StripSpec(RoadFar, RoadNear, -0.14f, ProceduralArt.Surface.Asphalt, white));
                    s.Add(new StripSpec(RoadNear, -PathHalf, 0f, ProceduralArt.Surface.Kerb, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Concrete, new Color(1f, 0.99f, 0.97f)));
                    s.Add(new StripSpec(PathHalf, PropertyZ + 0.6f, 0f, ProceduralArt.Surface.Concrete, white));
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0f, kind == "havana" ? ProceduralArt.Surface.Grass : ProceduralArt.Surface.Concrete,
                        kind == "havana" ? new Color(0.96f, 0.97f, 0.9f) : new Color(0.92f, 0.91f, 0.89f)));
                    break;
            }
            return s;
        }

        /// <summary>
        /// Everything beside a Florida leg's lane: its district from the plan, the dappled shade of the near street trees on a street
        /// (not on a promenade, whose foreground is the open lawn), and the pigeons. None of the chapters' own streets, pole lines,
        /// distant hills or side-street ends: the plan has its own poles, palms and skyline.
        /// </summary>
        static void MiamiScenery(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1, int seed)
        {
            if (!string.IsNullOrEmpty(LevelBuildKit.LevelId)) MiamiDistrictsBuilt.Add(LevelBuildKit.LevelId);
            Miami(track, root, x0, x1);
            string kind = MiamiStr(MiamiPlan, "strips", "street");
            if (kind == "street" || kind == "havana") CanopyShadows(track, root, new System.Random(seed + 173), x0, x1);
            Wildlife(track, root, new System.Random(seed + 389), x0, x1);
        }

        /// <summary>
        /// Florida's stops from the Miami kit, with the door (or the sign) at <paramref name="gx"/>: the bus stops (the aluminium
        /// shelter, the route's sign on its pole, a bench), the coffee window on the bayfront, Uncle Rey's dock (its bollard and a coil
        /// of line), the corner pharmacy, the Metrorail's and the Metromover's station signs (the district's guideway runs overhead),
        /// Museum Park's gate of royal palms. False for any other stop, or without the kit (the caller builds the stand-in).
        /// </summary>
        static bool MiamiStop(Transform p, string id, float gx, float gy)
        {
            if (!LevelBuildKit.Florida || !LevelBuildKit.HasKitModel("Miami", "StopSignMIA")) return false;
            Color navy = new Color(0.1f, 0.25f, 0.5f), teal = new Color(0.13f, 0.6f, 0.6f);
            switch (id)
            {
                case "calleOcho":
                case "brickell":
                    Model(p, "Florida", "BusShelterFL", gx + 1.8f, gy, PropertyZ + 0.8f);
                    Model(p, "Miami", "StopSignMIA", gx - 0.8f, gy, PoleZ + 0.15f);
                    Model(p, "Florida", "TrashFL", gx + 4.3f, gy, PoleZ + 0.2f);
                    if (id == "brickell") Model(p, "Plants", "PalmRoyal", gx + 6.6f, gy, PropertyZ + 1.2f, 30f, 0.9f);
                    return true;
                case "bayfront":
                    Model(p, "Miami", "CoffeeKioskMIA", gx + 1.6f, gy, PropertyZ + 1.1f);
                    Model(p, "Florida", "BenchFL", gx + 4.6f, gy, PoleZ + 0.4f);
                    Model(p, "Florida", "BenchFL", gx - 2.6f, gy, PoleZ + 0.4f);
                    PostBoard(p, "BAYFRONT PARK", gx - 0.9f, gy, PoleZ + 0.3f, 0.06f, navy, Color.white);
                    return true;
                case "reysDock":
                    Model(p, "Florida", "DockFL", gx + 1.5f, gy - 0.9f, PropertyZ + 2f);
                    Model(p, "Miami", "BollardMIA", gx + 3.4f, gy, PropertyZ + 0.4f);
                    Model(p, "Miami", "LineCoilMIA", gx + 2.4f, gy, PropertyZ + 0.6f, 20f);
                    PostBoard(p, "UNCLE REY'S DOCK", gx - 1.2f, gy, 2.3f, 0.06f, navy, Color.white);
                    return true;
                case "drugstore":
                    Model(p, "Miami", "PharmacyMIA", gx + 1.2f, gy, PropertyZ + 1.3f);
                    return true;
                case "underline":
                case "biscayne":
                    // (the district's guideway runs overhead: miami_plan.py) the station's sign, benches and a palm
                    Model(p, "Plants", "PalmRoyal", gx + 5.8f, gy, PropertyZ + 1.0f, 70f, 0.9f);
                    Model(p, "Florida", "BenchFL", gx + 1.4f, gy, PoleZ + 0.4f);
                    PostBoard(p, id == "underline" ? "METRORAIL" : "METROMOVER", gx - 1.2f, gy, PoleZ + 0.3f, 0.06f, teal, Color.white);
                    Model(p, "Florida", "BenchFL", gx + 3.6f, gy, PoleZ + 0.4f);
                    return true;
                case "museumPark":
                    foreach (float dx in new[] { -2.4f, 4.6f })
                        Model(p, "Plants", "PalmRoyal", gx + dx, gy, PropertyZ + 1.0f, dx * 40f, 0.95f);
                    PostBoard(p, "MUSEUM PARK", gx + 1.1f, gy, PoleZ + 0.3f, 0.06f, navy, Color.white);
                    Model(p, "Florida", "BenchFL", gx + 2.6f, gy, PropertyZ + 0.5f);
                    return true;
                default:
                    return false;
            }
        }

        /// <summary>
        /// A Florida leg's scenery from its plan, between x0 and x1: the water behind the seawall (and the seawall), the land the
        /// school stands on, then every model of the district at its place (on the ground there, or at the height the plan gives:
        /// boats on the water, pelicans on their pilings).
        /// </summary>
        static void Miami(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            var plan = MiamiPlan;
            var group = new GameObject("Miami_" + MiamiStr(plan, "district", "district")).transform;
            group.SetParent(root, false);
            object o;
            if (plan.TryGetValue("water", out o))
            {
                var w = o as Dictionary<string, object>;
                float a = Mathf.Max(MiamiNum(w, "from", x0), ClipLo), b = Mathf.Min(MiamiNum(w, "to", x1), ClipHi);
                float z = MiamiNum(w, "z", 4.6f), y = MiamiNum(w, "y", -0.9f);
                if (b > a)
                {
                    var water = Solid(group, "Water", new Vector3((a + b) * 0.5f, y - 0.05f, z + 600f), new Vector3(b - a, 0.1f, 1200f), Color.white,
                        Art.surfaces[ProceduralArt.Surface.Sea]);
                    water.faces = MeshBuilder.Faces.Top;
                    NoShadowCast(water);
                    water.Rebuild();
                    // The seawall: the promenade's edge, its concrete face down into the water.
                    Solid(group, "Seawall", new Vector3((a + b) * 0.5f, (y - 0.4f) * 0.5f, z - 0.17f), new Vector3(b - a, -(y - 0.4f), 0.34f),
                        new Color(0.82f, 0.81f, 0.78f), Art.surfaces[ProceduralArt.Surface.Concrete]);
                }
            }
            // The side streets (a crossing's, a site's exit road): they run from the lane back to SideStreetDepth, and nothing of the
            // district may stand in them or cover them (v139: a coffee kiosk and a tower's podium stood across Biscayne
            // Boulevard's, and the school's lawn covered Bayfront's, docs/LEARNINGS.md E19).
            var streets = new List<Vector2>(track.OpenAreas);
            if (plan.TryGetValue("water", out o))
            {
                var w = o as Dictionary<string, object>;
                foreach (var st in streets)
                    if (st.y > MiamiNum(w, "from", x0) && st.x < MiamiNum(w, "to", x1))
                        Debug.LogError("[Kick Off] " + LevelBuildKit.LevelId + ": the side street at x " + st.x.ToString("F1") + " runs into the "
                            + "district's water: run tools/blender/miami_plan.py (it keeps side streets on land)");
            }
            if (plan.TryGetValue("land", out o) && o is List<object>)
                foreach (var item in (List<object>)o)
                {
                    var l = item as Dictionary<string, object>;
                    float a = Mathf.Max(MiamiNum(l, "from", x0), ClipLo), b = Mathf.Min(MiamiNum(l, "to", x1), ClipHi);
                    float z0 = MiamiNum(l, "z0", 4.6f), z1 = MiamiNum(l, "z1", 120f);
                    if (b <= a) continue;
                    // A lawn, or concrete (the port's quay and yard, v140).
                    bool concrete = MiamiStr(l, "surface", "Grass") == "Concrete";
                    // The land in pieces round each side street (its asphalt shows), and on behind the street's end.
                    float cut = Mathf.Min(z1, SideStreetDepth);
                    foreach (var span in Without(a, b, z0 < cut ? streets : new List<Vector2>()))
                        Land(group, span.x, span.y, z0, z1, concrete);
                    if (z0 < cut && z1 > cut)
                        foreach (var st in streets)
                        {
                            float sa = Mathf.Max(a, st.x), sb = Mathf.Min(b, st.y);
                            if (sb > sa) Land(group, sa, sb, cut, z1, concrete);
                        }
                }
            // Built shapes (v140: Bayfront's port behind its side street, the quay, cranes, gate, fence and container stacks), and
            // their lettering: the plan gives each box, so the preview builds the same.
            int shapes = 0;
            if (plan.TryGetValue("boxes", out o) && o is List<object>)
            {
                var port = new GameObject("Shapes").transform;
                port.SetParent(group, false);
                foreach (var item in (List<object>)o)
                {
                    var bx = item as Dictionary<string, object>;
                    if (bx == null) continue;
                    Vector3 c = MiamiVec(bx, "c"), size = MiamiVec(bx, "s");
                    if (c.x < ClipLo - 60f || c.x > ClipHi + 60f) continue;
                    if (ShapeInSideStreet(streets, c, size))
                    {
                        Debug.LogError("[Kick Off] " + LevelBuildKit.LevelId + ": the plan's " + MiamiStr(bx, "n", "shape") + " at x " + c.x.ToString("F1")
                            + " stands in a side street: run tools/blender/miami_plan.py");
                        continue;
                    }
                    Vector3 rgb = MiamiVec(bx, "rgb");
                    string surf = MiamiStr(bx, "surf", "");
                    var shape = Solid(port, MiamiStr(bx, "n", "Shape"), c, size, new Color(rgb.x, rgb.y, rgb.z),
                        surf == "Concrete" ? Art.surfaces[ProceduralArt.Surface.Concrete] : null);
                    float rz = MiamiNum(bx, "rz", 0f);
                    if (rz != 0f) shape.transform.rotation = Quaternion.Euler(0f, 0f, rz);
                    shapes++;
                }
            }
            if (plan.TryGetValue("labels", out o) && o is List<object>)
                foreach (var item in (List<object>)o)
                {
                    var lb = item as Dictionary<string, object>;
                    if (lb == null) continue;
                    Vector3 rgb = MiamiVec(lb, "rgb");
                    Lettering(group, MiamiStr(lb, "t", ""), MiamiVec(lb, "c"), MiamiNum(lb, "size", 0.1f), new Color(rgb.x, rgb.y, rgb.z));
                }
            int placed = 0, skipped = 0;
            if (plan.TryGetValue("items", out o) && o is List<object>)
                foreach (var item in (List<object>)o)
                {
                    var it = item as List<object>;
                    if (it == null || it.Count < 6) continue;
                    float x = (float)(double)it[2];
                    if (x < x0 || x > x1 || x < ClipLo || x > ClipHi) continue;
                    float z = (float)(double)it[3], yaw = (float)(double)it[4], scale = (float)(double)it[5];
                    float y = it.Count > 6 ? (float)(double)it[6] : GroundAt(track, x);
                    if (InSideStreet(streets, (string)it[0], (string)it[1], x, z, scale, yaw)) { skipped++; continue; }
                    if (Model(group, (string)it[0], (string)it[1], x, y, z, yaw, scale) != null) placed++;
                }
            group.gameObject.AddComponent<StaticBatcher>();
            if (skipped > 0)
                Debug.LogWarning("[Kick Off] " + LevelBuildKit.LevelId + ": " + skipped + " of the district's models stood in a side street and were left out "
                    + "(run tools/blender/miami_plan.py: it keeps them out)");
            if (placed == 0) Debug.LogWarning("[Kick Off] " + LevelBuildKit.LevelId + ": nothing of its district was placed (is the Miami kit imported?)");
        }

        /// <summary>How far back a side street runs from the lane (StreetBuilder.CrossingStreet: to z 70), with a little beyond it.</summary>
        const float SideStreetDepth = 72f;

        /// <summary>
        /// The district's land at the street's level from <paramref name="a"/> to <paramref name="b"/>, z0 to z1: a lawn, or
        /// concrete (a port's quay and yard).
        /// </summary>
        static void Land(Transform group, float a, float b, float z0, float z1, bool concrete = false)
        {
            if (b - a < 0.05f || z1 - z0 < 0.05f) return;
            var land = Solid(group, concrete ? "Yard" : "Land", new Vector3((a + b) * 0.5f, -0.1f, (z0 + z1) * 0.5f), new Vector3(b - a, 0.2f, z1 - z0),
                concrete ? new Color(0.92f, 0.91f, 0.88f) : new Color(0.95f, 0.98f, 0.9f),
                Art.surfaces[concrete ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.Grass]);
            land.faces = MeshBuilder.Faces.Top;
            land.Rebuild();
        }

        /// <summary>The stretch from a to b without the side streets in it, as (from, to) pieces.</summary>
        public static List<Vector2> Without(float a, float b, List<Vector2> streets)
        {
            var pieces = new List<Vector2> { new Vector2(a, b) };
            foreach (var st in streets)
            {
                var next = new List<Vector2>();
                foreach (var p in pieces)
                {
                    if (st.y <= p.x || st.x >= p.y) { next.Add(p); continue; }
                    if (st.x > p.x) next.Add(new Vector2(p.x, st.x));
                    if (st.y < p.y) next.Add(new Vector2(st.y, p.y));
                }
                pieces = next;
            }
            return pieces;
        }

        /// <summary>
        /// Would this plan model, at x and depth z, stand in a side street? Its width from the kit's manifest (the larger of its two
        /// sides, whatever it is turned to), with 0.3 m to spare; only within the street's length (a skyline tower far behind it
        /// stays). The side streets are the level's open areas.
        /// </summary>
        public static bool InSideStreet(List<Vector2> streets, string kit, string model, float x, float z, float scale, float yaw = 0f)
        {
            if (streets.Count == 0) return false;
            Vector3 size = LevelBuildKit.KitSize(kit, model) * scale;
            if (size.x <= 0f) size = new Vector3(2f, 2f, 2f);
            // its footprint as it stands (v140: a freighter moored along the port's quay, end on to the street, is 7 m wide, not 30)
            float c = Mathf.Abs(Mathf.Cos(yaw * Mathf.Deg2Rad)), s = Mathf.Abs(Mathf.Sin(yaw * Mathf.Deg2Rad));
            float halfX = Mathf.Max((c * size.x + s * size.z) * 0.5f, 0.5f), halfZ = Mathf.Max((s * size.x + c * size.z) * 0.5f, 0.5f);
            if (z - halfZ > SideStreetDepth) return false;
            foreach (var st in streets)
                if (x + halfX > st.x - 0.3f && x - halfX < st.y + 0.3f) return true;
            return false;
        }

        /// <summary>
        /// Would a plan's built shape (centre and size) stand in a side street? Only what reaches below 4.5 m counts: a gate's sign
        /// over the street is clear of it.
        /// </summary>
        public static bool ShapeInSideStreet(List<Vector2> streets, Vector3 c, Vector3 size)
        {
            if (c.y - size.y * 0.5f > 4.5f || c.z - size.z * 0.5f > SideStreetDepth) return false;
            foreach (var st in streets)
                if (c.x + size.x * 0.5f > st.x && c.x - size.x * 0.5f < st.y) return true;
            return false;
        }

        /// <summary>A plan entry's [x, y, z] (zero if it is missing).</summary>
        static Vector3 MiamiVec(Dictionary<string, object> d, string key)
        {
            object o;
            var v = d != null && d.TryGetValue(key, out o) ? o as List<object> : null;
            if (v == null || v.Count < 3) return Vector3.zero;
            return new Vector3(Convert.ToSingle(v[0]), Convert.ToSingle(v[1]), Convert.ToSingle(v[2]));
        }
    }
}
