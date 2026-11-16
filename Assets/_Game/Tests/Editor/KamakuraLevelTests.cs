using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Kamakura's own levels (GeneratedContent.CityLevels, built by KamakuraLevels while LevelBuildKit.Kamakura is set): every
    /// Kamakura model they place is in the game, every stop they end at has its set piece, and what their hazards say is in
    /// every language. (CityRoutesTests checks that none of them is in the original town's table.)
    /// </summary>
    public class KamakuraLevelTests
    {
        const string Scripts = "Assets/_Game/Scripts/Editor/";
        const string Models = "Assets/_Game/Art/Models/Kamakura/Kamakura.json";

        [Test]
        public void EveryKamakuraModelTheLevelsPlaceIsInstalled()
        {
            var root = MiniJson.Parse(File.ReadAllText(Models)) as Dictionary<string, object>;
            Assert.IsNotNull(root, "Kamakura.json does not parse");
            var installed = (Dictionary<string, object>)root["models"];
            var used = new HashSet<string>();
            foreach (string file in new[] { "KamakuraLevels.cs", "StreetBuilder.Kamakura.cs", "LevelBuildKit.Kamakura.cs" })
                foreach (Match m in Regex.Matches(File.ReadAllText(Scripts + file), "\"(Km[A-Z][A-Za-z]+)\""))
                    used.Add(m.Groups[1].Value);
            Assert.Greater(used.Count, 30, "KM1-1 places the kit's models by name");
            var missing = used.Where(m => !installed.ContainsKey(m)).ToList();
            Assert.IsEmpty(missing, "placed but not in Art/Models/Kamakura: " + string.Join(", ", missing));
        }

        [Test]
        public void EveryCityStopALevelEndsAtHasItsSetPiece()
        {
            // KM1-1 ends at Hase Station (Levels/CityRoutes), which StreetBuilder.StopFront builds as Kamakura's.
            var to = CityRoutes.Kamakura.To("KM1-1");
            Assert.IsNotNull(to, "KM1-1 is on a Kamakura route");
            CollectionAssert.Contains(StreetBuilder.CitySetPieces, to.id);
            // The cities' set pieces are their own list, beside the original town's (RouteTableTests checks those).
            Assert.IsEmpty(StreetBuilder.CitySetPieces.Intersect(StreetBuilder.SetPieces));
        }

        [Test]
        public void TheTramsLoseMessageIsInEveryLanguage()
        {
            foreach (string lang in new[] { "en", "es" })
                Assert.IsTrue(StringTables.For(lang).ContainsKey("lose.tram"), "lose.tram is missing in " + lang);
        }
    }
}
