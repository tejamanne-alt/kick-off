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
            foreach (var leg in new[] { new[] { "FL1-3", "Bayfront" }, new[] { "FL3-2", "BiscayneBoulevard" } })
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
                    Assert.IsFalse(StreetBuilder.InSideStreet(streets, (string)it[0], (string)it[1], (float)(double)it[2], (float)(double)it[3], (float)(double)it[5]),
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
