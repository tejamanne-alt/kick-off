using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using DribbleToSchool.EditorTools;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Florida's own districts need their kit and their plan: every Miami model the game places is in the Miami kit (its FBX and
    /// its manifest entry); every model the plan (Art/Models/Miami/MiamiDistricts.json, tools/blender/miami_plan.py) places is in
    /// its kit; the plan dresses every Florida leg with Florida's own models only; and nothing that stands on the ground stands in open water.
    /// </summary>
    public class MiamiKitTests
    {
        const string Models = "Assets/_Game/Art/Models/";

        static bool InKit(string kit, string model)
        {
            string manifest = Models + kit + "/" + kit + ".json";
            return File.Exists(Models + kit + "/" + model + ".fbx") && File.Exists(manifest) &&
                   Regex.IsMatch(File.ReadAllText(manifest), "\"" + model + "\"\\s*:");
        }

        static Dictionary<string, object> Legs()
        {
            Assert.IsTrue(File.Exists(StreetBuilder.MiamiPlanFile), "the plan is missing: run tools/blender/miami_plan.py");
            var root = MiniJson.Parse(File.ReadAllText(StreetBuilder.MiamiPlanFile)) as Dictionary<string, object>;
            Assert.IsNotNull(root, "the plan is not a JSON object");
            return (Dictionary<string, object>)root["legs"];
        }

        [Test]
        public void EveryMiamiModelTheGamePlacesIsInTheKit()
        {
            foreach (string model in StreetBuilder.MiamiModelsUsed)
                Assert.IsTrue(InKit("Miami", model), model + " is not in the Miami kit (its FBX or its Miami.json entry)");
            Assert.IsTrue(File.Exists(Models + "Miami/MiamiAtlas.png"), "the kit's atlas is missing");
        }

        [Test]
        public void EveryModelThePlanPlacesIsInItsKit()
        {
            var missing = new HashSet<string>();
            foreach (var leg in Legs())
                foreach (var item in (List<object>)((Dictionary<string, object>)leg.Value)["items"])
                {
                    var it = (List<object>)item;
                    string kit = (string)it[0], model = (string)it[1];
                    if (!InKit(kit, model)) missing.Add(kit + "/" + model);
                }
            CollectionAssert.IsEmpty(missing, "the plan places models its kits haven't got");
        }

        [Test]
        public void ThePlanDressesEveryFloridaLeg()
        {
            var legs = Legs();
            foreach (string leg in new[] { "FL1-1", "FL1-2", "FL1-3", "FL2-1", "FL2-2", "FL2-3", "FL3-1", "FL3-2", "FL3-3" })
                Assert.IsTrue(legs.ContainsKey(leg), leg + " is not in the plan");
        }

        [Test]
        public void NothingOnTheGroundStandsInOpenWater()
        {
            foreach (var leg in Legs())
            {
                var plan = (Dictionary<string, object>)leg.Value;
                object w;
                if (!plan.TryGetValue("water", out w)) continue;
                var water = (Dictionary<string, object>)w;
                double from = (double)water["from"], to = (double)water["to"], z = (double)water["z"];
                var land = plan.ContainsKey("land") ? (List<object>)plan["land"] : new List<object>();
                foreach (var item in (List<object>)plan["items"])
                {
                    var it = (List<object>)item;
                    if (it.Count > 6) continue;     // given its own height: afloat, or on a piling
                    double x = (double)it[2], iz = (double)it[3];
                    if (x < from || x > to || iz <= z + 0.2) continue;
                    bool onLand = false;
                    foreach (var l in land)
                    {
                        var d = (Dictionary<string, object>)l;
                        if (x >= (double)d["from"] && x <= (double)d["to"] && iz >= (double)d["z0"] && iz <= (double)d["z1"]) onLand = true;
                    }
                    Assert.IsTrue(onLand, leg.Key + ": " + it[1] + " at x " + x + ", z " + iz + " stands in the water");
                }
            }
        }

        [Test]
        public void TheRoyalPalmAndTheBanyanAreInThePlantsKit()
        {
            foreach (string model in new[] { "PalmRoyal", "Banyan" })
                Assert.IsTrue(InKit("Plants", model), model + " is not in the Plants kit");
        }

        [Test]
        public void ThePlanPlacesOnlyFloridasOwnModels()
        {
            // Nothing of the original town's in a Florida leg (docs/LEARNINGS.md D9): the Miami and Florida kits, Florida's own trees,
            // and the wooden utility pole (the coast's; the town's poles are concrete).
            var foreign = new HashSet<string>();
            foreach (var leg in Legs())
                foreach (var item in (List<object>)((Dictionary<string, object>)leg.Value)["items"])
                {
                    var it = (List<object>)item;
                    string kit = (string)it[0], model = (string)it[1];
                    bool own = kit == "Miami" || kit == "Florida" ||
                               kit == "Plants" && System.Array.IndexOf(StreetBuilder.FloridaPlants, model) >= 0 ||
                               kit == "Street" && model == "UtilityPoleWood";
                    if (!own) foreign.Add(leg.Key + ": " + kit + "/" + model);
                }
            CollectionAssert.IsEmpty(foreign, "the plan places models that aren't Florida's own");
        }

        [Test]
        public void EverySlideUnderInAFloridaLegHasItsMiamiLook()
        {
            // LevelBuildKit.SlideUnder builds a Florida leg's slide-under as <look>MIA from the Miami kit, with the look's own solid.
            string layouts = File.ReadAllText("Assets/_Game/Scripts/Editor/FloridaLevels.cs");
            var looks = new HashSet<string>();
            foreach (Match m in Regex.Matches(layouts, @"SlideLook\.(\w+)")) looks.Add(m.Groups[1].Value);
            Assert.IsNotEmpty(looks, "no slide-unders found in FloridaLevels.cs");
            foreach (string look in looks)
                Assert.IsTrue(InKit("Miami", look + "MIA"), "FloridaLevels uses SlideLook." + look + " but the Miami kit has no " + look + "MIA");
        }

        [Test]
        public void EveryFloridaStopHasItsMiamiSetPiece()
        {
            foreach (var stop in Levels.RouteTable.FloridaStops)
                CollectionAssert.Contains(StreetBuilder.MiamiStops, stop.id, stop.id + " has no Miami set piece (StreetBuilder.MiamiStop)");
        }

        [Test]
        public void ThePelicanIsInTheAnimalsKit()
        {
            Assert.IsTrue(InKit("Animals", "Pelican"), "Florida's pelicans fly the Animals kit's Pelican (with its WingL and WingR)");
        }

        [Test]
        public void EveryFloridaLegSoundsLikeMiami()
        {
            // Florida's six places (Havana, MiamiRiver, Bay, Downtown, Underline, MuseumPark), never one of Kamakura's beds.
            var kamakura = new[] { Audio.Soundscape.Menu, Audio.Soundscape.Street, Audio.Soundscape.Market, Audio.Soundscape.Beach,
                                   Audio.Soundscape.Underpass, Audio.Soundscape.Site, Audio.Soundscape.Park };
            foreach (string leg in new[] { "FL1-1", "FL1-2", "FL1-3", "FL2-1", "FL2-2", "FL2-3", "FL3-1", "FL3-2", "FL3-3" })
                CollectionAssert.DoesNotContain(kamakura, Audio.Soundscapes.ForFloridaLeg(leg), leg + " plays one of Kamakura's soundscapes");
        }

        [Test]
        public void MiamiIsAKit()
        {
            CollectionAssert.Contains(LevelBuildKit.Kits, "Miami");
        }

        [Test]
        public void NothingBehindTheLaneReachesOverTheBall()
        {
            // A Deco block's 3 m canvas arcade, set with its wall at 2.35 m, hung 0.7 m in front of the ball on Biscayne Boulevard
            // and downtown, and the ball flew up through it (docs/LEARNINGS.md E17). The plan keeps every model clear, and the
            // builder's guard would move it if not.
            UnityEngine.Vector3 min = LevelBuildKit.KitMin("Miami", "DecoArcadeMIA"), max = LevelBuildKit.KitMax("Miami", "DecoArcadeMIA");
            Assert.Less(min.z, -2.5f, "the arcade's canvas reaches about 3 m forward of its wall");
            float moved = StreetBuilder.ClearOfTheBall(2.35f, min, max, 0f, 1f);
            Assert.AreEqual(StreetBuilder.BallClear - min.z, moved, 1e-3f, "pushed back until its canopy is clear of the ball");
            Assert.AreEqual(StreetBuilder.BallClear + max.z, StreetBuilder.ClearOfTheBall(2.35f, min, max, 180f, 1f), 1e-3f, "turned round, its back is what comes forward");
            Assert.AreEqual(-1.6f, StreetBuilder.ClearOfTheBall(-1.6f, min, max, 0f, 1f), "at the kerb (a lamp, a signal) it is left where it is");

            foreach (var leg in Legs())
                foreach (var item in (List<object>)((Dictionary<string, object>)leg.Value)["items"])
                {
                    var it = (List<object>)item;
                    string kit = (string)it[0], model = (string)it[1];
                    if (kit == "Plants" || kit == "Animals" || kit == "Terrain") continue;
                    float z = (float)(double)it[3];
                    float clear = StreetBuilder.ClearOfTheBall(z, LevelBuildKit.KitMin(kit, model), LevelBuildKit.KitMax(kit, model), (float)(double)it[4], (float)(double)it[5]);
                    Assert.AreEqual(z, clear, 0.01f, leg.Key + ": " + model + " at x " + it[2] + " reaches over the ball's lane: run tools/blender/miami_plan.py");
                }
        }

        /// <summary>The legs that end at the school (the last of each route), with their crossing's open area beside the school.</summary>
        static readonly Dictionary<string, UnityEngine.Vector2> SchoolCrossings = new Dictionary<string, UnityEngine.Vector2>
        {
            { "FL1-3", new UnityEngine.Vector2(77.2f, 84.8f) },    // Bayfront: Crossing(78, 84), widened 0.8 m
            { "FL2-3", new UnityEngine.Vector2(99.2f, 106.8f) },   // Downpour: Crossing(100, 106)
            { "FL3-3", new UnityEngine.Vector2(88.2f, 95.8f) },    // Museum Park: Crossing(89, 95)
        };

        [Test]
        public void EveryRoutesLastLegHasThePortRoadBesideTheSchool()
        {
            // v140: on land, Bayfront's side street still read as a road out of the bay; it leads to the port's gate: the quay along
            // the water's edge beside it, cranes, ships alongside, the container yard past the fence (docs/LEARNINGS.md E20). v142:
            // every route's last leg has it, as Bayfront does (E21).
            foreach (var kv in SchoolCrossings) PortBesideTheSchool(kv.Key, kv.Value);
        }

        static void PortBesideTheSchool(string leg, UnityEngine.Vector2 road)
        {
            var plan = (Dictionary<string, object>)Legs()[leg];
            Assert.IsTrue(plan.ContainsKey("boxes"), leg + "'s plan builds its port");
            var names = new Dictionary<string, int>();
            var street = new List<UnityEngine.Vector2> { road };
            float quayFace = float.NaN, gateZ = float.NaN, gateBottom = 0f;
            foreach (var item in (List<object>)plan["boxes"])
            {
                var bx = (Dictionary<string, object>)item;
                string n = (string)bx["n"];
                int k;
                names[n] = names.TryGetValue(n, out k) ? k + 1 : 1;
                var c = Vec(bx["c"]);
                var size = Vec(bx["s"]);
                Assert.IsFalse(StreetBuilder.ShapeInSideStreet(street, c, size), leg + ": the port's " + n + " at x " + c.x + " stands in the side street");
                if (n == "QuayWall") quayFace = c.x + size.x * 0.5f;
                if (n == "GateSign") { gateZ = c.z; gateBottom = c.y - size.y * 0.5f; }
            }
            foreach (var part in new[] { "QuayWall", "CraneBoom", "CraneLeg", "Container", "GateSign", "GateBooth", "FencePost" })
                Assert.IsTrue(names.ContainsKey(part), leg + ": the port has its " + part);
            Assert.GreaterOrEqual(names["CraneBoom"], 2, leg + ": cranes along the quay");
            Assert.GreaterOrEqual(names["Container"], 60, leg + ": a yard of container stacks");
            var water = (Dictionary<string, object>)plan["water"];
            Assert.AreEqual((double)water["to"], quayFace, 0.05, leg + ": the quay's face is the water's edge");
            Assert.Less(quayFace, road.x, leg + ": the quay is beside the road, the water on its far side");
            Assert.Less(gateZ, 70f, leg + ": the gate stands across the side street before its end (StreetBuilder.CrossingStreet: z 70)");
            Assert.GreaterOrEqual(gateBottom, 4.5f, leg + ": the gate's sign is clear over the street");
            int alongside = 0;
            foreach (var item in (List<object>)plan["items"])
            {
                var it = (List<object>)item;
                if ((string)it[1] == "FreighterMIA" && (double)it[2] < (double)water["to"] && (double)it[3] < 72.0) alongside++;
            }
            Assert.Greater(alongside, 0, leg + ": a freighter moored at the quay beside the street");
            bool yard = false;
            foreach (var item in (List<object>)plan["land"])
            {
                var l = (Dictionary<string, object>)item;
                object surf;
                if (l.TryGetValue("surface", out surf) && (string)surf == "Concrete") yard = true;
            }
            Assert.IsTrue(yard, leg + ": the quay and the yard are concrete, not lawn");
        }

        [Test]
        public void TheGroundReachesTheHorizonUnderEveryTower()
        {
            // v142: the street's own ground ended 90 m back and the towers stood up to 490 m back on the sky; across the bay the far
            // shore was a hairline 0.9 m over the water. From the strips' back to 2,400 m, across the width the camera sees at each
            // distance (0.7 of it either side), every point is land or water, and nothing standing is off the ground (E21).
            foreach (var kv in Legs())
            {
                string leg = kv.Key;
                var plan = (Dictionary<string, object>)kv.Value;
                var lands = new List<float[]>();
                object o;
                if (plan.TryGetValue("land", out o))
                    foreach (var item in (List<object>)o)
                    {
                        var l = (Dictionary<string, object>)item;
                        lands.Add(new[] { (float)(double)l["from"], (float)(double)l["to"], (float)(double)l["z0"], (float)(double)l["z1"] });
                    }
                float[] water = null;
                if (plan.TryGetValue("water", out o))
                {
                    var w = (Dictionary<string, object>)o;
                    water = new[] { (float)(double)w["from"], (float)(double)w["to"], (float)(double)w["z"], w.ContainsKey("z1") ? (float)(double)w["z1"] : 2400f };
                }
                System.Func<float, float, bool> onLand = (x, z) => lands.Exists(l => l[0] <= x && x <= l[1] && l[2] <= z && z <= l[3]);
                System.Func<float, float, bool> inWater = (x, z) => water != null && water[0] <= x && x <= water[1] && water[2] <= z && z <= water[3];
                float back = plan.ContainsKey("back") ? (float)(double)plan["back"] : StreetBuilder.BackZ;
                string strips = (string)plan["strips"];
                if (water != null && (strips == "promenade" || strips == "park")) back = UnityEngine.Mathf.Min(water[2], back);
                for (float z = back + 1f; z < 2399f; z += z < 300f ? 25f : 100f)
                {
                    float half = 0.7f * (z + 10f);
                    for (float x = -70f - half; x <= 150f + half; x += 25f)   // (every leg runs from -70 to at least 150)
                        Assert.IsTrue(onLand(x, z) || inWater(x, z), leg + ": no ground at x " + x + " z " + z);
                }
                foreach (var item in (List<object>)plan["items"])
                {
                    var it = (List<object>)item;
                    if (it.Count > 6) continue;
                    float x = (float)(double)it[2], z = (float)(double)it[3];
                    if (z > back + 0.5f) Assert.IsTrue(onLand(x, z), leg + ": " + it[1] + " at x " + x + " z " + z + " stands off the ground");
                }
            }
        }

        static UnityEngine.Vector3 Vec(object o)
        {
            var v = (List<object>)o;
            return new UnityEngine.Vector3((float)(double)v[0], (float)(double)v[1], (float)(double)v[2]);
        }

        [Test]
        public void TheSweepersCabIsSolidForTheKidAndADoubleJumpClearsIt()
        {
            // v140: the ball shells (E18) are the ball's only, and the kid walked from the sweeper's back into its cab.
            var size = LevelBuildKit.KitSize("Miami", "SweeperMIA");
            Assert.AreEqual(size.y, LevelBuildKit.TrackBuilder.SweeperCabTop, 0.03f, "the cab's collider reaches the kit cab's roof");
            string src = File.ReadAllText(Path.Combine(UnityEngine.Application.dataPath, "_Game/Scripts/Editor/LevelBuildKit.FloridaCity.cs"));
            int at = src.IndexOf("public void Sweeper(");
            Assert.Greater(at, 0);
            string body = src.Substring(at, src.IndexOf("\n            }", at) - at);
            StringAssert.Contains("AddComponent<BoxCollider2D>()", body, "the cab has a collider of its own on the sweeper's body");
            StringAssert.Contains("SweeperCabTop", body);
            // From the 1.2 m back the kid double-jumps over the cab (the way past it); from the street it is too tall.
            var reach = Holiday.JumpReach.Defaults;
            Assert.Greater(Holiday.JumpReach.DoubleJump(reach).apex, LevelBuildKit.TrackBuilder.SweeperCabTop - 1.2f + 0.3f, "a double jump from the back clears the cab");
        }

        [Test]
        public void NothingOfADistrictStandsInOrCoversASideStreet()
        {
            // A coffee kiosk and a tower's podium stood across Biscayne Boulevard's side street, and Bayfront's came out of the bay
            // under the school's lawn (v139, docs/LEARNINGS.md E19).
            var cut = StreetBuilder.Without(0f, 100f, new List<UnityEngine.Vector2> { new UnityEngine.Vector2(40f, 46f) });
            Assert.AreEqual(2, cut.Count, "the land in two pieces round the street");
            Assert.AreEqual(40f, cut[0].y, 1e-4f);
            Assert.AreEqual(46f, cut[1].x, 1e-4f);

            string levels = File.ReadAllText(Path.Combine(UnityEngine.Application.dataPath, "_Game/Scripts/Editor/FloridaLevels.cs"));
            var legs = Legs();
            foreach (var leg in new[] { new[] { "FL1-3", "Bayfront" }, new[] { "FL3-2", "BiscayneBoulevard" }, new[] { "FL2-3", "Downpour" }, new[] { "FL3-3", "MuseumPark" } })
            {
                int at = levels.IndexOf("public static void " + leg[1] + "(");
                Assert.Greater(at, 0, leg[1]);
                int end = levels.IndexOf("public static void ", at + 10);
                var m = Regex.Match(levels.Substring(at, (end > 0 ? end : levels.Length) - at), @"t\.Crossing\((-?[\d.]+)f, (-?[\d.]+)f");
                Assert.IsTrue(m.Success, leg[1] + " has its crossing");
                var street = new UnityEngine.Vector2(float.Parse(m.Groups[1].Value, System.Globalization.CultureInfo.InvariantCulture) - 0.8f, float.Parse(m.Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture) + 0.8f);
                var streets = new List<UnityEngine.Vector2> { street };
                var plan = (Dictionary<string, object>)legs[leg[0]];
                foreach (var item in (List<object>)plan["items"])
                {
                    var it = (List<object>)item;
                    Assert.IsFalse(StreetBuilder.InSideStreet(streets, (string)it[0], (string)it[1], (float)(double)it[2], (float)(double)it[3], (float)(double)it[5], (float)(double)it[4]),
                        leg[0] + ": " + it[1] + " at x " + it[2] + " stands in the side street");
                }
                object w;
                if (plan.TryGetValue("water", out w))
                {
                    var water = (Dictionary<string, object>)w;
                    Assert.IsFalse((double)water["to"] > street.x && (double)water["from"] < street.y, leg[0] + ": the side street runs into the water");
                }
            }
        }

        [Test]
        public void TheLevelIdIsReadBeforeTheNewSceneUnloadsTheDefinition()
        {
            // Read after EditorSceneManager.NewScene, the definition had been unloaded and LevelId was always empty: no Florida leg
            // ever found its district, v124 to v130 (docs/LEARNINGS.md A19).
            string src = File.ReadAllText(Path.Combine(UnityEngine.Application.dataPath, "_Game/Scripts/Editor/LevelBuildKit.cs"));
            int build = src.IndexOf("public static void BuildScene(");
            Assert.Greater(build, 0, "BuildScene not found");
            int newScene = src.IndexOf("EditorSceneManager.NewScene(", build);
            int read = src.IndexOf("def.levelId", build);
            Assert.Greater(newScene, 0);
            Assert.Greater(read, 0);
            Assert.Less(read, newScene, "BuildScene must read the definition's level id before it makes the new scene");
            Assert.IsFalse(Regex.IsMatch(src.Substring(newScene, 2000), @"LevelId\s*=\s*def\b"), "LevelId set from def after the new scene");
        }
    }
}
