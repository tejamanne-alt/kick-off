#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>The playable kids: the list that the picker, the level builders and the menu camera all read.</summary>
    public class PlayerRosterTests
    {
        [Test]
        public void EveryKidHasItsOwnIdAndModel()
        {
            var ids = new HashSet<string>();
            var models = new HashSet<string>();
            foreach (var info in PlayerRoster.All)
            {
                Assert.IsFalse(string.IsNullOrEmpty(info.id));
                Assert.IsFalse(string.IsNullOrEmpty(info.model));
                Assert.IsTrue(ids.Add(info.id), "id used twice: " + info.id);
                Assert.IsTrue(models.Add(info.model), "model used twice: " + info.model);
            }
        }

        [Test]
        public void HanaKeepsHerIdAndIsTheDefaultNowRenIsGone()
        {
            Assert.AreEqual("girl", PlayerRoster.All[0].id);
            Assert.AreEqual("Girl", PlayerRoster.All[0].model);
            Assert.AreEqual("girl", PlayerRoster.DefaultId);
            // Ren ("boy") was removed: a save that picked him plays Hana.
            Assert.AreEqual(-1, PlayerRoster.IndexOf("boy"));
            Assert.AreEqual("girl", PlayerRoster.Normalize("boy"));
        }

        [Test]
        public void AnUnknownOrMissingSavedIdFallsBackToTheDefault()
        {
            Assert.AreEqual(PlayerRoster.DefaultId, PlayerRoster.Normalize("nobody"));
            Assert.AreEqual(PlayerRoster.DefaultId, PlayerRoster.Normalize(""));
            Assert.AreEqual(PlayerRoster.DefaultId, PlayerRoster.Normalize(null));
            Assert.AreEqual("girl", PlayerRoster.Normalize("girl"));
            Assert.AreEqual(PlayerRoster.DefaultId, PlayerRoster.Get("nobody").id);
        }

        [Test]
        public void ThereAreTwoTeensAndFourPrimarySchoolKids()
        {
            Assert.AreEqual(2, PlayerRoster.Of(SchoolLevel.High).Count);
            Assert.AreEqual(4, PlayerRoster.Of(SchoolLevel.Primary).Count);
            int boys = 0, girls = 0;
            foreach (var info in PlayerRoster.Of(SchoolLevel.Primary))
            {
                if (info.id.Contains("Boy")) boys++;
                if (info.id.Contains("Girl")) girls++;
            }
            Assert.AreEqual(2, boys, "two primary-school boys");
            Assert.AreEqual(2, girls, "two primary-school girls");
        }

        [Test]
        public void PrimarySchoolKidsAreShorterThanTheTeens()
        {
            float shortestTeen = float.MaxValue, tallestKid = 0f;
            foreach (var info in PlayerRoster.Of(SchoolLevel.High)) shortestTeen = Mathf.Min(shortestTeen, info.height);
            foreach (var info in PlayerRoster.Of(SchoolLevel.Primary)) tallestKid = Mathf.Max(tallestKid, info.height);
            Assert.Less(tallestKid, shortestTeen - 0.2f);
            foreach (var info in PlayerRoster.Of(SchoolLevel.Primary))
            {
                Assert.Greater(info.height, 1.2f, info.id);
                Assert.Less(info.height, 1.4f, info.id);
            }
        }

        [Test]
        public void EveryKidHasPlausibleSizes()
        {
            foreach (var info in PlayerRoster.All)
            {
                Assert.Greater(info.neckHeight, 0.8f, info.id);
                Assert.Less(info.neckHeight, info.height, info.id + ": the neck is below the top of the head");
                // The Head bone sits at 80 to 88 % of a standing kid (a bigger head puts it lower); the game puts it at neckHeight.
                float ratio = info.neckHeight / info.height;
                Assert.Greater(ratio, 0.78f, info.id);
                Assert.Less(ratio, 0.9f, info.id);
            }
        }

        [Test]
        public void EveryKidHasItsModelColoursAtlasAndPortrait()
        {
            string game = Path.Combine(Application.dataPath, "_Game");
            foreach (var info in PlayerRoster.All)
            {
                string models = Path.Combine(game, "Art/Models");
                Assert.IsTrue(File.Exists(Path.Combine(models, info.model + ".fbx")), info.id + ": Art/Models/" + info.model + ".fbx");
                Assert.IsTrue(File.Exists(Path.Combine(models, info.model + ".json")), info.id + ": Art/Models/" + info.model + ".json");
                Assert.IsTrue(File.Exists(Path.Combine(models, info.model + "Atlas.png")), info.id + ": Art/Models/" + info.model + "Atlas.png");
                Assert.IsTrue(File.Exists(Path.Combine(game, "Resources/" + info.PortraitPath + ".png")), info.id + ": Resources/" + info.PortraitPath + ".png");
            }
        }

        [Test]
        public void EveryKidAndSchoolIsNamedInEveryLanguage()
        {
            var keys = new List<string> { "player.high", "player.primary", "player.title", "player.change" };
            foreach (var info in PlayerRoster.All) keys.Add(info.nameKey);
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in keys)
                    Assert.IsTrue(table.ContainsKey(key) && !string.IsNullOrEmpty(table[key]), code + ": " + key);
            }
        }

        [Test]
        public void EveryKidHasADifferentName()
        {
            var names = new HashSet<string>();
            foreach (var info in PlayerRoster.All)
                Assert.IsTrue(names.Add(StringTables.For("en")[info.nameKey]), "two kids are both called " + StringTables.For("en")[info.nameKey]);
        }
    }
}
#endif
