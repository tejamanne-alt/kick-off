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
    /// its kit; the plan dresses every Florida leg but Riverside Street; and nothing that stands on the ground stands in open water.
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
        public void ThePlanDressesEveryFloridaLegButRiversideStreet()
        {
            var legs = Legs();
            foreach (string leg in new[] { "FL1-1", "FL1-2", "FL1-3", "FL1-4", "FL2-2", "FL2-3", "FL2-4", "FL2-5", "FL3-1", "FL3-2", "FL3-3" })
                Assert.IsTrue(legs.ContainsKey(leg), leg + " is not in the plan");
            Assert.IsFalse(legs.ContainsKey("FL2-1"), "FL2-1 keeps Florida's Home Street");
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
        public void MiamiIsAKit()
        {
            CollectionAssert.Contains(LevelBuildKit.Kits, "Miami");
        }
    }
}
