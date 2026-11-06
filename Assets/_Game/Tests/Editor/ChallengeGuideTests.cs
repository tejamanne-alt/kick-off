using System.Collections.Generic;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>Every challenge's guide has its goal, its tips and its other texts in every language.</summary>
    public class ChallengeGuideTests
    {
        static readonly string[] Challenges = { "C01", "C02", "C03", "C04", "C05" };

        [Test]
        public void EveryChallengeHasItsGuideInEveryLanguage()
        {
            var keys = new List<string>(ChallengeGuide.OtherKeys) { "pause.howToPlay" };
            foreach (string id in Challenges) keys.Add("challenge." + id + ".goal");
            foreach (ChallengeGuide.Kind kind in System.Enum.GetValues(typeof(ChallengeGuide.Kind)))
                foreach (var tip in ChallengeGuide.TipsFor(kind)) keys.Add(tip.key);
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in keys)
                    Assert.IsTrue(table.ContainsKey(key) && table[key].Length > 0, code + ": " + key);
                foreach (string key in new[] { "challenge.timeLimit", "challenge.missed" })
                    Assert.IsTrue(table[key].Contains("{0}"), code + ": " + key + " shows its number");
            }
        }

        [Test]
        public void EachKindOfChallengeHasTwoOrThreeTips()
        {
            foreach (ChallengeGuide.Kind kind in System.Enum.GetValues(typeof(ChallengeGuide.Kind)))
            {
                int n = ChallengeGuide.TipsFor(kind).Length;
                Assert.IsTrue(n >= 2 && n <= 3, kind + ": " + n + " tips");
            }
        }
    }
}
