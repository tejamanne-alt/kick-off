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
    /// A leg the plan doesn't list (Riverside Street, FL2-1) keeps Florida's Home Street (StreetBuilder.FloridaHome).
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>Every Miami kit model the game places itself (the plan's are checked from the plan): the tests check the kit has each.</summary>
        public static readonly string[] MiamiModelsUsed =
        {
            "VentanitaMIA", "StopSignMIA", "CoffeeKioskMIA", "BollardMIA", "LineCoilMIA", "PharmacyMIA",
            // LevelBuildKit.FloridaCity: the animals, the scooters, the domino table, the arcades, the sweeper, the mini-games' sets
            "RoosterMIA", "HenMIA", "IguanaMIA", "ScooterMIA", "ScooterUpMIA", "DominoTableMIA", "DecoArcadeMIA", "DecoArcade2MIA",
            "SweeperMIA", "BusMIA", "BusNearMIA", "FishingBoatMIA", "DrugstoreAisleMIA",
        };

        /// <summary>The plan, beside the Miami kit.</summary>
        public const string MiamiPlanFile = LevelBuildKit.ModelsDir + "/Miami/MiamiDistricts.json";

        static Dictionary<string, object> miamiLegs;
        static string miamiLegsSource;

        /// <summary>The plan of the Florida leg being built, or null (not Florida's, not in the plan, or the plan is missing).</summary>
        static Dictionary<string, object> MiamiPlan
        {
            get
            {
                string leg = LevelBuildKit.LevelId;
                if (!LevelBuildKit.Florida || string.IsNullOrEmpty(leg)) return null;
                if (miamiLegs == null || miamiLegsSource != MiamiPlanFile)
                {
                    miamiLegsSource = MiamiPlanFile;
                    miamiLegs = new Dictionary<string, object>();
                    try
                    {
                        if (File.Exists(MiamiPlanFile))
                        {
                            var root = MiniJson.Parse(File.ReadAllText(MiamiPlanFile)) as Dictionary<string, object>;
                            object legs;
                            if (root != null && root.TryGetValue("legs", out legs) && legs is Dictionary<string, object>)
                                miamiLegs = (Dictionary<string, object>)legs;
                        }
                    }
                    catch (Exception e) { Debug.LogWarning("[Kick Off] " + MiamiPlanFile + " could not be read: " + e.Message); }
                }
                object plan;
                return miamiLegs.TryGetValue(leg, out plan) ? plan as Dictionary<string, object> : null;
            }
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
            // The Metrobus's street slides past its windows: the bus builds it on its own moving strip (MiamiStreetStrip).
            if (MiamiStr(MiamiPlan, "district", "") == "bus") return;
            Miami(track, root, x0, x1);
            string kind = MiamiStr(MiamiPlan, "strips", "street");
            if (kind == "street" || kind == "havana") CanopyShadows(track, root, new System.Random(seed + 173), x0, x1);
            Wildlife(track, root, new System.Random(seed + 389), x0, x1);
        }

        /// <summary>
        /// Florida's stops from the Miami kit, with the door (or the sign) at <paramref name="gx"/>: the Metrobus stops (the aluminium
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
        /// The leg's district on a strip that moves (the street past the Metrobus's windows): the plan's models from
        /// <paramref name="from"/> for <paramref name="length"/> metres, twice over end to end so the strip can wrap, leaving out any
        /// that would stand across either end (it would overlap its own copy). Not static: the whole strip slides. Returns how many
        /// were placed (0: no plan, or the kit isn't there).
        /// </summary>
        public static int MiamiStreetStrip(Transform strip, float from, float length, float groundY)
        {
            var plan = MiamiPlan;
            object o;
            if (plan == null || !plan.TryGetValue("items", out o) || !(o is List<object>)) return 0;
            int placed = 0;
            foreach (var item in (List<object>)o)
            {
                var it = item as List<object>;
                if (it == null || it.Count < 6) continue;
                string kit = (string)it[0], model = (string)it[1];
                float x = (float)(double)it[2], z = (float)(double)it[3], yaw = (float)(double)it[4], scale = (float)(double)it[5];
                float half = LevelBuildKit.KitSize(kit, model).x * 0.5f * scale;
                if (x - half < from || x + half > from + length) continue;
                float y = it.Count > 6 ? (float)(double)it[6] : groundY;
                for (int copy = 0; copy < 2; copy++)
                    if (Model(strip, kit, model, x + copy * length, y, z, yaw, scale) != null) placed++;
            }
            return placed;
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
            if (plan.TryGetValue("land", out o) && o is List<object>)
                foreach (var item in (List<object>)o)
                {
                    var l = item as Dictionary<string, object>;
                    float a = Mathf.Max(MiamiNum(l, "from", x0), ClipLo), b = Mathf.Min(MiamiNum(l, "to", x1), ClipHi);
                    float z0 = MiamiNum(l, "z0", 4.6f), z1 = MiamiNum(l, "z1", 120f);
                    if (b <= a) continue;
                    var land = Solid(group, "Land", new Vector3((a + b) * 0.5f, -0.1f, (z0 + z1) * 0.5f), new Vector3(b - a, 0.2f, z1 - z0),
                        new Color(0.95f, 0.98f, 0.9f), Art.surfaces[ProceduralArt.Surface.Grass]);
                    land.faces = MeshBuilder.Faces.Top;
                    land.Rebuild();
                }
            int placed = 0;
            if (plan.TryGetValue("items", out o) && o is List<object>)
                foreach (var item in (List<object>)o)
                {
                    var it = item as List<object>;
                    if (it == null || it.Count < 6) continue;
                    float x = (float)(double)it[2];
                    if (x < x0 || x > x1 || x < ClipLo || x > ClipHi) continue;
                    float z = (float)(double)it[3], yaw = (float)(double)it[4], scale = (float)(double)it[5];
                    float y = it.Count > 6 ? (float)(double)it[6] : GroundAt(track, x);
                    if (Model(group, (string)it[0], (string)it[1], x, y, z, yaw, scale) != null) placed++;
                }
            group.gameObject.AddComponent<StaticBatcher>();
            if (placed == 0) Debug.LogWarning("[Kick Off] " + LevelBuildKit.LevelId + ": nothing of its district was placed (is the Miami kit imported?)");
        }
    }
}
