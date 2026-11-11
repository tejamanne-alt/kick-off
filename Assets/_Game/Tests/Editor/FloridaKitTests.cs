using System.IO;
using System.Text.RegularExpressions;
using DribbleToSchool.EditorTools;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The Florida add-on's streets need their kit: every model StreetBuilder.Florida(Home) and LevelBuildKit.Florida(Play) place
    /// is in the Florida kit (its FBX and its manifest entry), and the palms and live oaks it plants are in the Plants kit.
    /// </summary>
    public class FloridaKitTests
    {
        const string Models = "Assets/_Game/Art/Models/";

        [Test]
        public void EveryFloridaModelTheStreetPlacesIsInTheKit()
        {
            string manifest = File.ReadAllText(Models + "Florida/Florida.json");
            foreach (string model in StreetBuilder.FloridaModelsUsed)
            {
                Assert.IsTrue(File.Exists(Models + "Florida/" + model + ".fbx"), model + ".fbx is missing");
                Assert.IsTrue(Regex.IsMatch(manifest, "\"" + model + "\"\\s*:"), model + " is not in Florida.json");
            }
            Assert.IsTrue(File.Exists(Models + "Florida/FloridaAtlas.png"), "the kit's atlas is missing");
        }

        [Test]
        public void TheSabalPalmsAndTheLiveOakAreInThePlantsKit()
        {
            string manifest = File.ReadAllText(Models + "Plants/Plants.json");
            foreach (string model in new[] { "PalmSabal", "PalmSabalTall", "SawPalmetto", "LiveOak" })
            {
                Assert.IsTrue(File.Exists(Models + "Plants/" + model + ".fbx"), model + ".fbx is missing");
                Assert.IsTrue(Regex.IsMatch(manifest, "\"" + model + "\"\\s*:"), model + " is not in Plants.json");
            }
        }

        [Test]
        public void FloridaIsAKit()
        {
            CollectionAssert.Contains(LevelBuildKit.Kits, "Florida");
        }
    }
}
