using DribbleToSchool.Localization;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>The map's tags (PLAY, TRY AGAIN, LATE!) and its late-trip banner have their texts in every language.</summary>
    public class MapIndicatorTests
    {
        [Test]
        public void TheMapsTagsAndBannerExistInEveryLanguage()
        {
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in new[] { "map.play", "map.tryAgain", "map.late", "map.lateBanner", "map.lateNote", "map.notNow", "results.fromHome" })
                    Assert.IsTrue(table.ContainsKey(key) && table[key].Length > 0, code + ": " + key);
                // The banner names the late route and the level it holds back.
                Assert.IsTrue(table["map.lateBanner"].Contains("{0}") && table["map.lateBanner"].Contains("{1}"), code + ": map.lateBanner");
                // A tag is a word or two: short enough to sit over a node.
                foreach (string key in new[] { "map.play", "map.tryAgain", "map.late" })
                    Assert.LessOrEqual(table[key].Length, 12, code + ": " + key);
            }
        }
    }
}
