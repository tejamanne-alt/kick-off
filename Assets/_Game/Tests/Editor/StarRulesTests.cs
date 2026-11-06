using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>A story level's stars: one per goal, the third for collecting every coin and the sticker.</summary>
    public class StarRulesTests
    {
        [Test]
        public void TheThirdGoalIsEveryCoinAndTheSticker()
        {
            Assert.IsTrue(StarRules.CollectedEverything(17, 17, true, true));
            Assert.IsFalse(StarRules.CollectedEverything(13, 17, true, true), "a coin missed");
            Assert.IsFalse(StarRules.CollectedEverything(17, 17, true, false), "the sticker missed");
            Assert.IsTrue(StarRules.CollectedEverything(17, 17, false, false), "no sticker in the level: the coins are enough");
            Assert.IsTrue(StarRules.CollectedEverything(0, 0, false, false), "nothing to collect");
        }

        [Test]
        public void EachGoalIsAStarOfItsOwn()
        {
            Assert.AreEqual(1, StarRules.Stars(false, false), "got there with the ball");
            Assert.AreEqual(2, StarRules.Stars(true, false), "and in time");
            Assert.AreEqual(2, StarRules.Stars(false, true), "collecting everything earns its star even when slow");
            Assert.AreEqual(3, StarRules.Stars(true, true));
        }

        [Test]
        public void TheGoalsTextShowsTheCoinsInEveryLanguage()
        {
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in new[] { "results.coinsSticker", "results.allCoins" })
                {
                    Assert.IsTrue(table.ContainsKey(key), code + ": " + key);
                    Assert.IsTrue(table[key].Contains("{0}") && table[key].Contains("{1}"), code + ": " + key + " shows coins found of all");
                }
            }
        }
    }
}
