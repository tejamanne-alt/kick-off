using System.IO;
using System.Text.RegularExpressions;
using DribbleToSchool.EditorTools;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Kamakura's own look (the user's brief, docs/KAMAKURA_BRIEF.md; StreetBuilder.Kamakura) needs its kits: every model it places
    /// is in its kit (the FBX and the manifest entry), the two kits are in LevelBuildKit.Kits, and the slide-unders of chapter 4's
    /// tram and the black kite keep the rigs the game drives.
    /// </summary>
    public class KamakuraKitTests
    {
        const string Models = "Assets/_Game/Art/Models/";

        static bool InKit(string kit, string model)
        {
            string manifest = Models + kit + "/" + kit + ".json";
            return File.Exists(Models + kit + "/" + model + ".fbx") && File.Exists(manifest) &&
                   Regex.IsMatch(File.ReadAllText(manifest), "\"" + model + "\"\\s*:");
        }

        [Test]
        public void EveryKamakuraHomeAndShopIsInTheKamakuraKit()
        {
            foreach (string model in StreetBuilder.KamakuraModelsUsed)
                Assert.IsTrue(InKit("Kamakura", model), model + " is not in the Kamakura kit");
        }

        [Test]
        public void EveryKamakuraStreetThingIsInTheKamakuraStreetKit()
        {
            foreach (string model in StreetBuilder.KamakuraStreetModelsUsed)
                Assert.IsTrue(InKit("KamakuraStreet", model), model + " is not in the KamakuraStreet kit");
        }

        [Test]
        public void KamakurasTreesAndBirdsAreInTheirKits()
        {
            foreach (string model in StreetBuilder.KamakuraPlantsUsed)
                Assert.IsTrue(InKit("Plants", model), model + " is not in the Plants kit");
            foreach (string model in StreetBuilder.KamakuraAnimalsUsed)
                Assert.IsTrue(InKit("Animals", model), model + " is not in the Animals kit");
        }

        [Test]
        public void TheKamakuraKitsAreKits()
        {
            CollectionAssert.Contains(LevelBuildKit.Kits, "Kamakura");
            CollectionAssert.Contains(LevelBuildKit.Kits, "KamakuraStreet");
        }

        [Test]
        public void TheBlackKiteAndTheCrowHaveTheirRigs()
        {
            // (the swoop flaps the kite's WingL and WingR as it does the gull's; the ground bird pecks with the crow's Head)
            string manifest = File.ReadAllText(Models + "Animals/Animals.json");
            int kite = manifest.IndexOf("\"BlackKite\"", System.StringComparison.Ordinal), crow = manifest.IndexOf("\"Crow\"", System.StringComparison.Ordinal);
            Assert.GreaterOrEqual(kite, 0, "no BlackKite in Animals.json");
            Assert.GreaterOrEqual(crow, 0, "no Crow in Animals.json");
            string kiteEntry = manifest.Substring(kite, System.Math.Min(4000, manifest.Length - kite));
            StringAssert.Contains("WingL", kiteEntry);
            StringAssert.Contains("WingR", kiteEntry);
            string crowEntry = manifest.Substring(crow, System.Math.Min(4000, manifest.Length - crow));
            StringAssert.Contains("Head", crowEntry);
        }
    }
}
