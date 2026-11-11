#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.Art;
using DribbleToSchool.Audio;
using DribbleToSchool.Challenges;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Holiday;
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
        public void EveryAddOnHasItsNamesAndItsOwnSceneSuffix()
        {
            var en = StringTables.For("en");
            var ids = new HashSet<string>();
            var suffixes = new HashSet<string>();
            foreach (var a in AddOns.All)
            {
                Assert.IsTrue(ids.Add(a.id), a.id + " is listed twice");
                if (a.sceneSuffix.Length > 0) Assert.IsTrue(suffixes.Add(a.sceneSuffix), a.id + "'s scene suffix is another's");
                Assert.IsTrue(en.ContainsKey(a.nameKey), a.nameKey);
                Assert.IsTrue(en.ContainsKey(a.placeKey), a.placeKey);
            }
            Assert.AreSame(AddOns.Florida, AddOns.ById(AddOns.FloridaId));
            Assert.AreSame(AddOns.Florida, AddOns.OfScene("L12_LowTide" + AddOns.FloridaSuffix));
        }

        [Test]
        public void FloridaHasHomeStreetAndTheBeachSoFarAndItsOwnMusic()
        {
            var fl = AddOns.Florida;
            Assert.IsTrue(fl.available);
            Assert.IsTrue(fl.needsEveryLevel, "Florida is unlocked like California, by finishing every level");
            Assert.AreEqual(MusicCountry.Florida, fl.music);
            Assert.IsTrue(fl.Partial);
            for (int chapter = 1; chapter <= 5; chapter++)
                Assert.AreEqual(chapter == 1 || chapter == 3, fl.HasChapter(chapter), "chapter " + chapter);
            for (int chapter = 1; chapter <= 5; chapter++)
            {
                Assert.IsTrue(AddOns.Original.HasChapter(chapter));
                Assert.IsTrue(AddOns.California.HasChapter(chapter));
            }
            Assert.IsFalse(AddOns.California.Partial);
        }

        [Test]
        public void EveryCountrysMusicIsItsOwn()
        {
            // The loops differ by country: Florida's beach isn't California's surf rock or the original's J-pop.
            var fl = MusicGenerator.Generate(Soundscape.Beach, MusicCountry.Florida);
            var ca = MusicGenerator.Generate(Soundscape.Beach, MusicCountry.California);
            var jp = MusicGenerator.Generate(Soundscape.Beach, MusicCountry.Japan);
            Assert.AreNotEqual(fl.Length, ca.Length);
            Assert.AreNotEqual(fl.Length, jp.Length);
        }

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

        [Test]
        public void EveryStoryLevelHasASticker()
        {
            List<bool> challenge;
            List<string> scenes;
            var levels = GeneratedContent.LevelTable(out challenge, out scenes);
            for (int i = 0; i < levels.Count; i++)
            {
                if (challenge[i]) continue;
                foreach (string code in Loc.Languages)
                    foreach (string part in new[] { "", ".text", ".hint" })
                        Assert.IsTrue(StringTables.For(code).ContainsKey("sticker." + levels[i].Key + part), code + ": sticker." + levels[i].Key + part);
            }
        }

        [Test]
        public void StickerRewardsAreEarnedNotSold()
        {
            var rewards = CosmeticsTable.Rows().Where(r => r.unlock != CosmeticUnlock.Coins).ToList();
            Assert.IsNotEmpty(rewards);
            foreach (var r in rewards) Assert.AreEqual(0, r.price, "a sticker reward has no price: " + r.id);
            for (int chapter = 1; chapter <= 5; chapter++)
                Assert.AreEqual(1, rewards.Count(r => r.unlock == CosmeticUnlock.StickerSet && r.unlockValue == chapter), "one set reward for chapter " + chapter);
            Assert.IsTrue(rewards.Any(r => r.unlock == CosmeticUnlock.StickerCount && r.unlockValue == 23), "the full album earns something");
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
        public void MusicLoopsForEverySoundscape()
        {
            // Every country's loops (the original's, California's and Florida's), for every place.
            foreach (MusicCountry country in System.Enum.GetValues(typeof(MusicCountry)))
                foreach (var scape in Soundscapes.All)
                {
                    float[] music = MusicGenerator.Generate(scape, country);
                    string what = country + " " + scape;
                    Assert.AreEqual(0, music.Length % MusicGenerator.Channels, what + " is not whole stereo frames");
                    Assert.Greater(music.Length / MusicGenerator.Channels, Synth.SampleRate * 20, what + " too short");
                    Assert.IsFalse(music.Any(v => float.IsNaN(v) || Mathf.Abs(v) > 1f), what + " invalid samples");
                }
        }

        [Test]
        public void EveryRouteHasItsOwnMusicAndAmbience()
        {
            var seen = new HashSet<Soundscape>();
            foreach (var route in RouteTable.All)
            {
                var scape = Soundscapes.For(route.id, route.chapter);
                Assert.AreNotEqual(Soundscape.Menu, scape, route.id);
                Assert.IsTrue(seen.Add(scape), route.id + " shares its soundscape with another route");
            }
        }

        [Test]
        public void AmbienceSitsUnderTheMusicAndNeverClips()
        {
            foreach (var scape in Soundscapes.All)
            {
                var pack = AmbienceGenerator.Generate(scape);
                Assert.AreEqual(0, pack.bed.Length % AmbienceGenerator.Channels, scape + " bed is not whole stereo frames");
                Assert.Greater(pack.bed.Length / AmbienceGenerator.Channels, Synth.SampleRate * 10, scape + " bed too short");
                Assert.IsFalse(pack.bed.Any(v => float.IsNaN(v) || Mathf.Abs(v) > 1f), scape + " bed invalid samples");
                double sum = 0;
                foreach (float v in pack.bed) sum += v * v;
                Assert.Less(System.Math.Sqrt(sum / pack.bed.Length), MusicGenerator.Loudness, scape + " bed is as loud as the music");
                Assert.Greater(pack.cues.Length, 0, scape + " has no cues");
                foreach (var cue in pack.cues)
                {
                    Assert.AreEqual(0, cue.clip.Length % 2, scape + "/" + cue.name);
                    Assert.IsFalse(cue.clip.Any(v => float.IsNaN(v) || Mathf.Abs(v) > 1f), scape + "/" + cue.name + " invalid samples");
                    Assert.LessOrEqual(cue.minGap, cue.maxGap, scape + "/" + cue.name);
                    Assert.Less(cue.volume, 1f, scape + "/" + cue.name + " should sit under the music");
                }
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
        public void BoxFacesPointOutward()
        {
            // Every face of a procedural box must wind so its normal points away from the centre,
            // or the 3D street would show holes where back-faces are culled.
            var b = new World.MeshBuilder();
            b.Box(0, new Vector3(-1f, -2f, -3f), new Vector3(1f, 2f, 3f), Color.white, World.MeshBuilder.Faces.All);
            var tris = b.Submeshes[0];
            Assert.AreEqual(36, tris.Count);
            for (int t = 0; t < tris.Count; t += 3)
            {
                Vector3 a = b.Vertices[tris[t]], c1 = b.Vertices[tris[t + 1]], c2 = b.Vertices[tris[t + 2]];
                Vector3 n = Vector3.Cross(c1 - a, c2 - a);
                Vector3 centre = (a + c1 + c2) / 3f;
                Assert.Greater(Vector3.Dot(n, centre), 0f, "triangle " + t / 3 + " faces inward");
                Assert.Greater(Vector3.Dot(b.Normals[tris[t]], centre), 0f, "normal of triangle " + t / 3 + " points inward");
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

        // ---------- Holiday Run ----------

        [Test]
        public void HolidayStagesFollowTheStoryInOrder()
        {
            Assert.AreEqual(23, HolidayStages.Count);
            Assert.AreEqual(HolidayStages.Count, HolidayStages.All.Length, "the table and the count agree");

            // One stage for each story level, in story order, in the chapter the level table puts it in.
            List<bool> challenge;
            List<string> scenes;
            var levels = GeneratedContent.LevelTable(out challenge, out scenes);
            int previousChapter = 1;
            for (int i = 0; i < HolidayStages.Count; i++)
            {
                var stage = HolidayStages.All[i];
                Assert.AreEqual("L" + (i + 1).ToString("00"), stage.levelId, "stage " + i + " stands for the story level of that number");
                int at = levels.FindIndex(l => l.Key == stage.levelId);
                Assert.GreaterOrEqual(at, 0, stage.levelId + " is in the level table");
                Assert.IsFalse(challenge[at], stage.levelId + " is a story level, not a challenge");
                Assert.AreEqual(levels[at].Value, stage.chapter, stage.levelId + " is in the chapter the level table gives it");
                Assert.GreaterOrEqual(stage.chapter, previousChapter, "chapters never go back (stage " + i + ")");
                previousChapter = stage.chapter;
                Assert.GreaterOrEqual(stage.density, 0f, stage.levelId + " density");
                Assert.LessOrEqual(stage.density, 1f, stage.levelId + " density");
            }
            Assert.AreEqual(HolidayStages.Count, HolidayStages.All.Select(s => s.levelId).Distinct().Count(), "duplicate level ids");
            Assert.AreEqual(1, HolidayStages.All[0].chapter, "the day starts in chapter 1");
            Assert.AreEqual(5, HolidayStages.All[HolidayStages.Count - 1].chapter, "and ends in chapter 5");
            for (int chapter = 1; chapter <= 5; chapter++)
            {
                int c = chapter;
                Assert.IsTrue(HolidayStages.All.Any(s => s.chapter == c), "a stage in chapter " + chapter);
            }
        }

        [Test]
        public void HolidayStageScenesAreUniqueAndTwoDigit()
        {
            List<bool> challenge;
            List<string> scenes;
            GeneratedContent.LevelTable(out challenge, out scenes);

            var names = new List<string>();
            for (int i = 0; i < HolidayStages.Count; i++)
            {
                string name = HolidayStages.SceneName(i);
                Assert.IsTrue(name.StartsWith(HolidayStages.StageScenePrefix), name + " has the stage prefix");
                string number = name.Substring(HolidayStages.StageScenePrefix.Length);
                Assert.AreEqual(2, number.Length, name + " ends in two digits");
                Assert.AreEqual(i + 1, int.Parse(number), name + " counts from one");
                Assert.IsFalse(scenes.Contains(name), name + " is also a story scene name");
                names.Add(name);
            }
            Assert.AreEqual(names.Count, names.Distinct().Count(), "duplicate stage scene names");
            Assert.IsFalse(names.Contains(HolidayStages.CoreSceneName), "the core scene is not one of the stages");
        }

        [Test]
        public void HolidayStageLookupsClamp()
        {
            Assert.AreEqual(0, HolidayStages.StageAt(-1000f));
            Assert.AreEqual(0, HolidayStages.StageAt(HolidayStages.FirstStageX));
            Assert.AreEqual(HolidayStages.Count - 1, HolidayStages.StageAt(HolidayStages.LapLength + 5000f));
            for (int i = 0; i < HolidayStages.Count; i++)
            {
                Assert.AreEqual(i, HolidayStages.StageAt(HolidayStages.StartOf(i) + 0.01f), "just inside the start of stage " + i);
                Assert.AreEqual(i, HolidayStages.StageAt(HolidayStages.EndOf(i) - 0.01f), "just inside the end of stage " + i);
            }
            Assert.AreEqual(5, HolidayStages.StageAt(HolidayStages.StartOf(5)), "a stage begins on its start");

            Assert.AreEqual(0f, HolidayStages.LapProgress(-50f), 0.0001f);
            Assert.AreEqual(0f, HolidayStages.LapProgress(HolidayStages.FirstStageX), 0.0001f);
            Assert.AreEqual(0.5f, HolidayStages.LapProgress(HolidayStages.FirstStageX + HolidayStages.LapLength * 0.5f), 0.0001f);
            Assert.AreEqual(1f, HolidayStages.LapProgress(HolidayStages.FirstStageX + HolidayStages.LapLength), 0.0001f);
            Assert.AreEqual(1f, HolidayStages.LapProgress(HolidayStages.LapLength + 5000f), 0.0001f);

            // The kid starts in the first stage, and the school gate stands in the last.
            Assert.AreEqual(0, HolidayStages.StageAt(HolidayStages.SpawnX));
            Assert.AreEqual(HolidayStages.Count - 1, HolidayStages.StageAt(HolidayStages.GateX));
        }

        [Test]
        public void HolidayRunTextsExistInEveryLanguage()
        {
            // The keys the director, the HUD and the title screen use. (The parity test checks the tables match each other.)
            var keys = new List<string>
            {
                "menu.holiday", "menu.holiday.best", "lose.crash", "hud.ready", "hud.go", "hud.jump", "hud.kick",
                "pause.title", "pause.resume", "pause.settings",
                "holiday.nearMiss", "holiday.smash", "holiday.multiplier", "holiday.shieldSaved", "holiday.revived", "holiday.dayDone",
            };
            foreach (PowerUpKind kind in System.Enum.GetValues(typeof(PowerUpKind)))
                keys.Add("holiday.powerup." + kind.ToString().ToLowerInvariant());
            for (int chapter = 1; chapter <= 5; chapter++) keys.Add("chapter." + chapter);

            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in keys) Assert.IsTrue(table.ContainsKey(key), code + ": " + key);
                // The texts the director and the title screen fill in with a number.
                foreach (string key in new[] { "holiday.nearMiss", "holiday.smash", "holiday.multiplier", "holiday.dayDone", "menu.holiday.best" })
                    Assert.IsTrue(table[key].Contains("{0}"), code + ": " + key + " has a number to show");
            }
        }

        // The mission tests run on a throwaway SaveData and a seeded Random, never on the player's save.

        static HolidayMissionRecord Record(string id, int target, int progress = 0)
        {
            return new HolidayMissionRecord { id = id, target = target, progress = progress };
        }

        /// <summary>A run that did more of everything than any mission asks for.</summary>
        static RunStats HugeRun()
        {
            return new RunStats
            {
                jumps = 100000, doubleJumps = 100000, slides = 100000, nearMisses = 100000, smashes = 100000, powerUps = 100000,
                coins = 100000, obstacles = 100000, stagesReached = 100000, days = 100000, maxMultiplier = 5, distance = 100000, score = 100000,
            };
        }

        static void AssertThreeDistinctPlayable(IList<MissionView> missions, string context)
        {
            Assert.AreEqual(HolidayMissions.ActiveCount, missions.Count, context + ": three missions");
            Assert.AreEqual(missions.Count, missions.Select(m => m.id).Distinct().Count(), context + ": three different kinds");
            foreach (var m in missions)
            {
                Assert.Greater(m.target, 0, context + ": " + m.id + " target");
                Assert.GreaterOrEqual(m.progress, 0, context + ": " + m.id + " progress");
                Assert.LessOrEqual(m.progress, m.target, context + ": " + m.id + " progress");
                Assert.IsFalse(string.IsNullOrEmpty(m.text), context + ": " + m.id + " text");
                Assert.IsFalse(m.text.StartsWith("holiday.m."), context + ": " + m.id + " text is translated (" + m.text + ")");
            }
        }

        [Test]
        public void HolidayMissionDefinitionsAreWellFormed()
        {
            var defs = HolidayMissions.Definitions;
            Assert.GreaterOrEqual(defs.Count, 12, "a pool of about twelve");
            Assert.AreEqual(defs.Count, defs.Select(d => d.id).Distinct().Count(), "duplicate mission ids");
            foreach (var def in defs)
            {
                Assert.AreEqual(3, def.targets.Length, def.id + " has three tiers");
                Assert.AreEqual(3, def.rewards.Length, def.id + " pays for three tiers");
                for (int tier = 0; tier < 3; tier++)
                {
                    Assert.Greater(def.targets[tier], tier == 0 ? 0 : def.targets[tier - 1], def.id + ": each tier asks for more");
                    Assert.GreaterOrEqual(def.rewards[tier], 50, def.id + ": reward");
                    Assert.LessOrEqual(def.rewards[tier], 250, def.id + ": reward");
                    if (tier > 0) Assert.GreaterOrEqual(def.rewards[tier], def.rewards[tier - 1], def.id + ": a harder tier pays at least as much");
                }
                Assert.GreaterOrEqual(def.stat(new RunStats()), 0, def.id + " reads an empty run");
                foreach (string code in Loc.Languages)
                {
                    var table = StringTables.For(code);
                    Assert.IsTrue(table.ContainsKey(def.textKey), code + ": " + def.textKey);
                    Assert.IsTrue(table[def.textKey].Contains("{0}"), code + ": " + def.textKey + " shows the target");
                    if (def.singularKey != null) Assert.IsTrue(table.ContainsKey(def.singularKey), code + ": " + def.singularKey);
                }
            }
        }

        [Test]
        public void HolidayMissionsAreThreeDistinctKinds()
        {
            for (int seed = 0; seed < 30; seed++)
            {
                var data = new SaveData();
                var active = HolidayMissions.Active(data, new System.Random(seed));
                AssertThreeDistinctPlayable(active, "seed " + seed);
                foreach (var m in active)
                {
                    Assert.AreEqual(0, m.progress, "a new mission starts at nothing");
                    Assert.IsFalse(m.done);
                    Assert.GreaterOrEqual(m.reward, 50);
                    Assert.LessOrEqual(m.reward, 250);
                }
                // Asking again changes nothing: the same three, as saved.
                var again = HolidayMissions.Active(data, new System.Random(seed + 1000));
                for (int i = 0; i < active.Count; i++) Assert.AreEqual(active[i].id, again[i].id, "the missions are kept in the save");
            }
        }

        [Test]
        public void HolidayMissionsMendAnEmptyOrDamagedList()
        {
            var damaged = new List<List<HolidayMissionRecord>>
            {
                null,
                new List<HolidayMissionRecord>(),
                new List<HolidayMissionRecord> { null, null, null },
                new List<HolidayMissionRecord> { Record("no.such.kind", 5), Record("", 5), Record(null, 5) },
                new List<HolidayMissionRecord> { Record("slides", 15, 3), Record("slides", 40, 9) },
                new List<HolidayMissionRecord> { Record("coins", 0), Record("jumps", -4, -2) },
                new List<HolidayMissionRecord> { Record("coins", 30), Record("jumps", 40), Record("slides", 15), Record("stage", 6), Record("days", 1) },
            };
            for (int i = 0; i < damaged.Count; i++)
            {
                var data = new SaveData { holidayMissions = damaged[i], holidayMissionTally = i % 2 == 0 ? null : new List<HolidayMissionTally> { null } };
                AssertThreeDistinctPlayable(HolidayMissions.Active(data, new System.Random(i)), "damaged list " + i);
            }

            // What is good in a list is kept, with its progress.
            var kept = new SaveData { holidayMissions = new List<HolidayMissionRecord> { null, Record("slides", 15, 3), Record("slides", 40, 9), Record("coins", 30, 12) } };
            var active = HolidayMissions.Active(kept, new System.Random(1));
            Assert.AreEqual("slides", active[0].id);
            Assert.AreEqual(3, active[0].progress, "the first of two missions of one kind stays");
            Assert.AreEqual("coins", active[1].id);
            Assert.AreEqual(12, active[1].progress);
        }

        [Test]
        public void AFinishedMissionIsPaidAndReplacedInPlace()
        {
            var data = new SaveData
            {
                holidayMissions = new List<HolidayMissionRecord> { Record("distance", 600), Record("slides", 15, 5), Record("jumps", 40) },
            };
            var completed = new List<MissionView>();
            int paid = HolidayMissions.Apply(data, new RunStats { distance = 700, slides = 4, jumps = 12 }, completed, new System.Random(3));

            var distance = HolidayMissions.Definitions.First(d => d.id == "distance");
            Assert.AreEqual(1, completed.Count, "only the distance mission is finished");
            Assert.AreEqual("distance", completed[0].id);
            Assert.IsTrue(completed[0].done);
            Assert.AreEqual(distance.rewards[0], paid, "it pays its first tier");
            Assert.AreEqual(paid, completed[0].reward);
            Assert.AreEqual(0, data.coins, "paying is the caller's: the wallet is not touched here");

            Assert.AreEqual(3, data.holidayMissions.Count);
            Assert.AreEqual(3, data.holidayMissions.Select(r => r.id).Distinct().Count(), "still three different kinds");
            Assert.AreNotEqual("distance", data.holidayMissions[0].id, "another kind takes its place");
            Assert.AreEqual(0, data.holidayMissions[0].progress);
            Assert.AreEqual("slides", data.holidayMissions[1].id, "the others stay where they were");
            Assert.AreEqual(9, data.holidayMissions[1].progress, "slides add up from one run to the next: 5 + 4");
            Assert.AreEqual(12, data.holidayMissions[2].progress);
            Assert.AreEqual(1, data.holidayMissionTally.Count(t => t.id == "distance" && t.done == 1), "the finish is counted");
        }

        [Test]
        public void SeveralMissionsCanFinishInOneRun()
        {
            for (int seed = 0; seed < 20; seed++)
            {
                var data = new SaveData();
                var rng = new System.Random(seed);
                var before = HolidayMissions.Active(data, rng).Select(m => m.id).ToList();
                var completed = new List<MissionView>();
                int paid = HolidayMissions.Apply(data, HugeRun(), completed, rng);

                Assert.AreEqual(3, completed.Count, "all three are finished by a run that did everything");
                Assert.AreEqual(completed.Sum(m => m.reward), paid, "the rewards add up");
                AssertThreeDistinctPlayable(HolidayMissions.Active(data, rng), "after seed " + seed);
                foreach (var m in HolidayMissions.Active(data, rng))
                    Assert.IsFalse(before.Contains(m.id), "the new missions are other kinds than the finished ones (seed " + seed + ")");
            }
        }

        [Test]
        public void EveryFinishOfAKindIsCounted()
        {
            var data = new SaveData { holidayMissions = new List<HolidayMissionRecord> { Record("coins", 30), Record("jumps", 40), Record("slides", 15) } };
            var rng = new System.Random(11);
            for (int times = 1; times <= 4; times++)
            {
                data.holidayMissions[0] = Record("coins", 30);   // the same kind comes round again
                HolidayMissions.Apply(data, new RunStats { coins = 100000 }, null, rng);
                Assert.AreEqual(times, data.holidayMissionTally.First(t => t.id == "coins").done, "coins finished " + times + " time(s)");
            }
            Assert.AreEqual(1, data.holidayMissionTally.Count, "one tally for one kind");
        }

        [Test]
        public void MissionsAskForMoreEachTimeAKindIsFinished()
        {
            foreach (var def in HolidayMissions.Definitions)
            {
                for (int done = 0; done < 6; done++)
                {
                    int expectedTarget = def.targets[System.Math.Min(done, def.targets.Length - 1)];
                    bool seen = false;
                    // Draw until this kind comes up (the draws are seeded, so it is the same every time).
                    for (int seed = 0; seed < 300 && !seen; seed++)
                    {
                        var data = new SaveData();
                        data.holidayMissionTally.Add(new HolidayMissionTally { id = def.id, done = done });
                        foreach (var m in HolidayMissions.Active(data, new System.Random(seed)))
                        {
                            if (m.id != def.id) continue;
                            seen = true;
                            Assert.AreEqual(expectedTarget, m.target, def.id + " after " + done + " finished");
                        }
                    }
                    Assert.IsTrue(seen, def.id + " never came up");
                }
            }
        }

        [Test]
        public void PreviewCountsTheRunWithoutChangingTheSave()
        {
            var data = new SaveData();
            var rng = new System.Random(7);
            HolidayMissions.Active(data, rng);   // the first look sets the three missions up
            string before = JsonUtility.ToJson(data);

            var preview = HolidayMissions.Preview(data, HugeRun(), rng);
            Assert.AreEqual(before, JsonUtility.ToJson(data), "Preview leaves the save exactly as it was");
            Assert.AreEqual(3, preview.Count);
            foreach (var m in preview)
            {
                Assert.IsTrue(m.done, m.id + " would be finished by a run that did everything");
                Assert.AreEqual(m.target, m.progress);
            }

            var quiet = HolidayMissions.Preview(data, new RunStats(), rng);
            Assert.AreEqual(before, JsonUtility.ToJson(data));
            foreach (var m in quiet) Assert.IsFalse(m.done, m.id + " with a run that did nothing");

            // What Preview showed is what Apply then does.
            var completed = new List<MissionView>();
            HolidayMissions.Apply(data, HugeRun(), completed, rng);
            Assert.AreEqual(preview.Select(m => m.id).OrderBy(id => id).ToList(), completed.Select(m => m.id).OrderBy(id => id).ToList());
        }

        [Test]
        public void BestRunMissionsKeepTheBestAndTotalOnesAddUp()
        {
            var data = new SaveData
            {
                holidayMissions = new List<HolidayMissionRecord> { Record("distance", 2800), Record("slides", 100), Record("jumps", 300) },
            };
            var rng = new System.Random(5);
            HolidayMissions.Apply(data, new RunStats { distance = 400, slides = 5, jumps = 30 }, null, rng);
            HolidayMissions.Apply(data, new RunStats { distance = 300, slides = 7, jumps = 10 }, null, rng);
            Assert.AreEqual(400, data.holidayMissions[0].progress, "a shorter run doesn't take the best back");
            Assert.AreEqual(12, data.holidayMissions[1].progress, "slides add up over the runs");
            Assert.AreEqual(40, data.holidayMissions[2].progress, "so do jumps");

            HolidayMissions.Apply(data, new RunStats { distance = 900 }, null, rng);
            Assert.AreEqual(900, data.holidayMissions[0].progress, "a longer run raises it");

            // Which kinds count which way is part of each definition.
            var best = HolidayMissions.Definitions.Where(d => d.measure == MissionMeasure.BestRun).Select(d => d.id).OrderBy(id => id).ToList();
            Assert.AreEqual(new List<string> { "coins", "distance", "multiplier", "obstacles", "stage" }, best);
        }

        [Test]
        public void AMissionForOneIsWordedInTheSingular()
        {
            var data = new SaveData { holidayMissions = new List<HolidayMissionRecord> { Record("days", 1), Record("days", 2), Record("coins", 30) } };
            var active = HolidayMissions.Active(data, new System.Random(2));
            var days = active.First(m => m.id == "days");
            Assert.AreEqual(Loc.T("holiday.m.days.one"), days.text);
            Assert.IsFalse(days.text.Contains("{0}"));
        }

        // ---------- The way to school ----------

        [Test]
        public void TripsSurviveTheSaveFile()
        {
            // The trips are written with JsonUtility like the rest of the save (Progression/SchoolTrips; never the player's file here).
            var data = new SaveData();
            data.trips.Add(new TripRecord { routeId = "market", legTimes = new List<float> { 61.5f, 70f, -1f, -1f, -1f }, onTime = true, bestTripTime = 351.25f });
            var back = JsonUtility.FromJson<SaveData>(JsonUtility.ToJson(data));
            Assert.AreEqual(1, back.trips.Count);
            Assert.AreEqual("market", back.trips[0].routeId);
            Assert.AreEqual(5, back.trips[0].legTimes.Count);
            Assert.AreEqual(61.5f, back.trips[0].legTimes[0], 0.0001f);
            Assert.AreEqual(-1f, back.trips[0].legTimes[4], 0.0001f);
            Assert.IsTrue(back.trips[0].onTime);
            Assert.AreEqual(351.25f, back.trips[0].bestTripTime, 0.0001f);

            // A save written before the trips (version 1, no list at all) comes back with an empty one, ready for the upgrade.
            var old = JsonUtility.FromJson<SaveData>("{\"version\":1,\"coins\":5,\"levels\":[{\"levelId\":\"L05\",\"completed\":true}]}");
            Assert.AreEqual(1, old.version);
            Assert.IsTrue(old.IsCompleted("L05"));
            SchoolTrips.Upgrade(old);
            Assert.IsTrue(SchoolTrips.OnTime(old, "street"));
        }
    }
}
#endif
