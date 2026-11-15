using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.EditorTools;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The Kamakura kit (tools/blender/km_views.py, installed by kit_buildings_km.py --install): every model in its manifest
    /// has its FBX and its own texture, and keeps its triangle budget (docs/PERFORMANCE.md: a street prop 1,500, a vehicle
    /// 4,000).
    /// </summary>
    public class KamakuraKitTests
    {
        const string Dir = "Assets/_Game/Art/Models/Kamakura/";

        [Test]
        public void KamakuraIsAKit()
        {
            CollectionAssert.Contains(LevelBuildKit.Kits, "Kamakura");
        }

        [Test]
        public void EveryModelHasItsFbxItsTextureAndKeepsItsBudget()
        {
            var root = MiniJson.Parse(File.ReadAllText(Dir + "Kamakura.json")) as Dictionary<string, object>;
            Assert.IsNotNull(root, "Kamakura.json does not parse");
            var models = root["models"] as Dictionary<string, object>;
            Assert.IsNotNull(models, "Kamakura.json has no models");
            Assert.GreaterOrEqual(models.Count, 17, "KM1-1's approved props and the tram");
            foreach (var kv in models)
            {
                var info = (Dictionary<string, object>)kv.Value;
                Assert.IsTrue(File.Exists(Dir + kv.Key + ".fbx"), kv.Key + ".fbx is missing");
                Assert.IsTrue(info.ContainsKey("texture") && File.Exists(Dir + (string)info["texture"]),
                    kv.Key + "'s texture is missing");
                double tris = Convert.ToDouble(info["tris"]), budget = Convert.ToDouble(info["budget"]);
                Assert.LessOrEqual(tris, budget, kv.Key + " is over its budget");
                Assert.LessOrEqual(budget, kv.Key.StartsWith("KmTram") ? 4000 : 1500, kv.Key + "'s budget is over its kind's");
            }
        }
    }
}
