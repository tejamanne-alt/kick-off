#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.Art;
using DribbleToSchool.Audio;
using DribbleToSchool.Challenges;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.Store;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Edit-mode tests for logic and content integrity (Window > General > Test Runner > EditMode).
    /// None of them touch the player's save file.
    /// </summary>
    public class GameLogicTests
    {
        // ---------- Localization ----------

        [Test]
        public void EveryLanguageHasTheSameKeys()
        {
            var en = StringTables.For("en");
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                var missing = en.Keys.Where(k => !table.ContainsKey(k)).ToList();
                var extra = table.Keys.Where(k => !en.ContainsKey(k)).ToList();
                Assert.IsEmpty(missing, code + " is missing: " + string.Join(", ", missing));
                Assert.IsEmpty(extra, code + " has unknown keys: " + string.Join(", ", extra));
            }
        }

        [Test]
        public void UnknownKeyFallsBack()
        {
            Assert.AreEqual("fallback", Loc.T("no.such.key", "fallback"));
            Assert.AreEqual("no.such.key", Loc.T("no.such.key"));
        }

        [Test]
        public void EveryLevelHasATranslatedName()
        {
            List<bool> challenge;
            List<string> scenes;
            foreach (var level in GeneratedContent.LevelTable(out challenge, out scenes))
                foreach (string code in Loc.Languages)
                    Assert.IsTrue(StringTables.For(code).ContainsKey("level." + level.Key), code + ": level." + level.Key);
        }

        // ---------- Content tables ----------

        [Test]
        public void LevelTableIsConsistent()
        {
            List<bool> challenge;
            List<string> scenes;
            var levels = GeneratedContent.LevelTable(out challenge, out scenes);
            Assert.AreEqual(23, challenge.Count(c => !c), "story levels");
            Assert.AreEqual(5, challenge.Count(c => c), "challenges");
            Assert.AreEqual(levels.Count, levels.Select(l => l.Key).Distinct().Count(), "duplicate level ids");
            Assert.AreEqual(scenes.Count, scenes.Distinct().Count(), "duplicate scene names");
            for (int chapter = 1; chapter <= 5; chapter++)
                Assert.AreEqual(1, levels.Where((l, i) => l.Value == chapter && challenge[i]).Count(), "one challenge in chapter " + chapter);
        }

        [Test]
        public void CosmeticIdsAreUniqueAndDefaultsExist()
        {
            var rows = CosmeticsTable.Rows();
            Assert.AreEqual(rows.Length, rows.Select(r => r.id).Distinct().Count(), "duplicate cosmetic ids");
            var defaults = new SaveData();
            foreach (string id in new[] { defaults.equippedBall, defaults.equippedFlag, defaults.equippedOutfit, defaults.equippedTrail })
            {
                var row = rows.FirstOrDefault(r => r.id == id);
                Assert.AreEqual(id, row.id, "default cosmetic missing: " + id);
                Assert.AreEqual(0, row.price, "default cosmetic must be free: " + id);
            }
        }

        // ---------- Rules ----------

        [Test]
        public void ChallengeStarsHigherIsBetter()
        {
            var go = new GameObject("test");
            var c = go.AddComponent<AccuracyChallenge>();
            c.starThresholds = new[] { 3, 5, 7 };
            Assert.AreEqual(0, c.StarsFor(2));
            Assert.AreEqual(1, c.StarsFor(3));
            Assert.AreEqual(2, c.StarsFor(6));
            Assert.AreEqual(3, c.StarsFor(9));
            Object.DestroyImmediate(go);
        }

        [Test]
        public void ChallengeStarsLowerIsBetter()
        {
            var go = new GameObject("test");
            var c = go.AddComponent<AccuracyChallenge>();
            c.lowerIsBetter = true;
            c.starThresholds = new[] { 400, 280, 220 };
            Assert.AreEqual(0, c.StarsFor(450));
            Assert.AreEqual(1, c.StarsFor(300));
            Assert.AreEqual(3, c.StarsFor(220));
            Object.DestroyImmediate(go);
        }

        [Test]
        public void NextLevelSkipsChallenges()
        {
            var catalog = ScriptableObject.CreateInstance<LevelCatalog>();
            var a = Level("L01", 1, false);
            var c = Level("C01", 1, true);
            var b = Level("L02", 2, false);
            catalog.levels = new List<LevelDefinition> { a, c, b };
            Assert.AreSame(b, catalog.NextAfter(a));
            Assert.IsNull(catalog.NextAfter(c), "challenges return to the map");
            Assert.IsNull(catalog.NextAfter(b));
            Object.DestroyImmediate(catalog);
            Object.DestroyImmediate(a);
            Object.DestroyImmediate(b);
            Object.DestroyImmediate(c);
        }

        [Test]
        public void FirstChapterIsAlwaysFree()
        {
            Assert.IsTrue(Monetization.IsChapterUnlocked(1));
        }

        static LevelDefinition Level(string id, int chapter, bool challenge)
        {
            var l = ScriptableObject.CreateInstance<LevelDefinition>();
            l.levelId = id;
            l.chapter = chapter;
            l.isChallenge = challenge;
            return l;
        }

        // ---------- Generated audio & art ----------

        [Test]
        public void SoundEffectsAreCleanAndNeverClip()
        {
            foreach (var kv in SoundBank.BuildAll())
            {
                Assert.Greater(kv.Value.Length, 0, kv.Key.ToString());
                foreach (float v in kv.Value)
                {
                    Assert.IsFalse(float.IsNaN(v) || float.IsInfinity(v), kv.Key + " has invalid samples");
                    Assert.LessOrEqual(Mathf.Abs(v), 0.91f, kv.Key + " clips");
                }
            }
        }

        [Test]
        public void MusicLoopsForEveryChapter()
        {
            for (int chapter = 0; chapter <= 5; chapter++)
            {
                float[] music = MusicGenerator.Generate(chapter);
                Assert.Greater(music.Length, Synth.SampleRate * 10, "chapter " + chapter + " too short");
                Assert.IsFalse(music.Any(v => float.IsNaN(v) || Mathf.Abs(v) > 1f), "chapter " + chapter + " invalid samples");
            }
        }

        [Test]
        public void BlockSpriteIsSolidInsideAndClearAtCorners()
        {
            var block = ProceduralArt.Block();
            Assert.Greater(block.Get(32, 32).a, 0.99f);
            Assert.Less(block.Get(0, 0).a, 0.5f);
        }

        [Test]
        public void GroundEdgesTileSeamlessly()
        {
            for (int chapter = 1; chapter <= 5; chapter++)
            {
                var t = ChapterTheme.For(chapter);
                var edge = ProceduralArt.GroundEdge(t.edge, t.groundEdge, t.groundFill);
                int mismatches = 0;
                for (int y = 0; y < edge.Height; y++)
                    if (Mathf.Abs(edge.Get(0, y).a - edge.Get(edge.Width - 1, y).a) > 0.5f) mismatches++;
                Assert.LessOrEqual(mismatches, edge.Height / 8, "chapter " + chapter + " edge seam");
            }
        }

        [Test]
        public void PoleWiresTileSeamlessly()
        {
            var poles = ProceduralArt.PoleLine(1);
            int mismatches = 0;
            for (int y = 0; y < poles.Height; y++)
                if (Mathf.Abs(poles.Get(0, y).a - poles.Get(poles.Width - 1, y).a) > 0.5f) mismatches++;
            Assert.LessOrEqual(mismatches, 4, "wires should meet at the tile edges");
        }

        [Test]
        public void EveryCharacterPartHasPaint()
        {
            foreach (string name in ProceduralArt.PartNames)
            {
                var part = ProceduralArt.Part(name);
                int painted = 0;
                for (int y = 0; y < part.Height; y += 2)
                    for (int x = 0; x < part.Width; x += 2)
                        if (part.Get(x, y).a > 0.5f) painted++;
                Assert.Greater(painted, part.Width * part.Height / 4 / 20, name + " looks empty");
            }
        }
    }
}
#endif
