using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.FrontEnd;
using DribbleToSchool.Holiday;
using DribbleToSchool.Levels;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Generates every grey-box scene, level definition and the level catalog.
    /// Runs automatically when the project opens and the generated content is
    /// missing or older than <see cref="Version"/>. Tuning assets are kept;
    /// generated scenes and level definitions are rebuilt from the Levels table.
    /// </summary>
    [InitializeOnLoad]
    public static class GeneratedContent
    {
        /// <summary>Bump when layouts or the scene rig change so scenes regenerate.</summary>
        public const int Version = 57;

        const string ScenesDir = LevelBuildKit.Root + "/Scenes";
        const string LevelsDir = LevelBuildKit.Root + "/Levels";
        const string VersionFile = ScenesDir + "/GeneratedContentVersion.txt";
        const string TestTrackScene = ScenesDir + "/Phase1_TestTrack.unity";
        const string FrontEndScene = ScenesDir + "/" + FrontEndController.SceneName + ".unity";
        const string CosmeticsDir = LevelBuildKit.Root + "/Cosmetics";
        const string AutoBuildKey = "DribbleToSchool.AutoBuildChecked";

        struct LevelSpec
        {
            public int chapter;
            public string id, name, scene;
            public float bell;
            public int streak;
            public bool challenge;
            public Action<TrackBuilder> layout;

            public LevelSpec(int chapter, string id, string name, string scene, float bell, int streak, Action<TrackBuilder> layout)
            {
                this.chapter = chapter; this.id = id; this.name = name; this.scene = scene;
                this.bell = bell; this.streak = streak; this.layout = layout;
                challenge = false;
            }

            /// <summary>An optional ball-skill challenge (no bell; the objective sets the stars).</summary>
            public static LevelSpec Challenge(int chapter, string id, string name, string scene, Action<TrackBuilder> layout)
            {
                var spec = new LevelSpec(chapter, id, name, scene, 0f, 0, layout);
                spec.challenge = true;
                return spec;
            }

            public string ScenePath { get { return ScenesDir + "/Levels/" + scene + ".unity"; } }
        }

        /// <summary>
        /// A story level's bell: the seconds its street takes (as tuned in the table) and the walk from the front door that every story
        /// level starts with now (<see cref="HomeLeadInRules.BellSeconds"/>), so the school bell and the stars mean what they did before.
        /// </summary>
        static float Bell(float streetSeconds)
        {
            return streetSeconds + HomeLeadInRules.BellSeconds;
        }

        static readonly LevelSpec[] Levels =
        {
            // Chapter 1: Home Street
            new LevelSpec(1, "L01", "Out the Door", "L01_OutTheDoor", Bell(50f), 3, GreyboxLevels.OutTheDoor),
            new LevelSpec(1, "L02", "Parked Cars", "L02_ParkedCars", Bell(55f), 3, GreyboxLevels.ParkedCars),
            new LevelSpec(1, "L03", "Up the Hill", "L03_UpTheHill", Bell(80f), 4, GreyboxLevels.UpTheHill),
            new LevelSpec(1, "L04", "Garden Gate", "L04_GardenGate", Bell(60f), 3, GreyboxLevels.GardenGate),
            new LevelSpec(1, "L05", "Puddle Lane", "L05_PuddleLane", Bell(80f), 4, GreyboxLevels.PuddleLane),
            LevelSpec.Challenge(1, "C01", "Keepy-Uppy", "C01_KeepyUppy", GreyboxLevels.KeepyUppy),
            // Chapter 2: Market and Crossings
            new LevelSpec(2, "L06", "Market Morning", "L06_MarketMorning", Bell(60f), 4, GreyboxLevels.MarketMorning),
            new LevelSpec(2, "L07", "First Crossing", "L07_FirstCrossing", Bell(70f), 3, GreyboxLevels.FirstCrossing),
            new LevelSpec(2, "L08", "Corner Shop", "L08_CornerShop", Bell(70f), 4, GreyboxLevels.CornerShop),
            new LevelSpec(2, "L09", "Fruit Stalls", "L09_FruitStalls", Bell(75f), 5, GreyboxLevels.FruitStalls),
            new LevelSpec(2, "L10", "Rush Hour", "L10_RushHour", Bell(95f), 6, GreyboxLevels.RushHour),
            LevelSpec.Challenge(2, "C02", "Window Shopping", "C02_WindowShopping", GreyboxLevels.WindowShopping),
            // Chapter 3: The Beach
            new LevelSpec(3, "L11", "Boardwalk", "L11_Boardwalk", Bell(70f), 4, GreyboxLevels.Boardwalk),
            new LevelSpec(3, "L12", "Low Tide", "L12_LowTide", Bell(75f), 4, GreyboxLevels.LowTide),
            new LevelSpec(3, "L13", "Seagull Bay", "L13_SeagullBay", Bell(80f), 5, GreyboxLevels.SeagullBay),
            new LevelSpec(3, "L14", "Sandcastle Sprint", "L14_SandcastleSprint", Bell(95f), 6, GreyboxLevels.SandcastleSprint),
            LevelSpec.Challenge(3, "C03", "Beach Slalom", "C03_BeachSlalom", GreyboxLevels.BeachSlalom),
            // Chapter 4: Underpass & Construction
            new LevelSpec(4, "L15", "The Underpass", "L15_TheUnderpass", Bell(65f), 4, GreyboxLevels.TheUnderpass),
            new LevelSpec(4, "L16", "Building Site", "L16_BuildingSite", Bell(80f), 5, GreyboxLevels.BuildingSite),
            new LevelSpec(4, "L17", "Cranes", "L17_Cranes", Bell(85f), 4, GreyboxLevels.Cranes),
            new LevelSpec(4, "L18", "Tunnel Run", "L18_TunnelRun", Bell(105f), 6, GreyboxLevels.TunnelRun),
            LevelSpec.Challenge(4, "C04", "Site Targets", "C04_SiteTargets", GreyboxLevels.SiteTargets),
            // Chapter 5: Park & School
            new LevelSpec(5, "L19", "Park Gates", "L19_ParkGates", Bell(65f), 5, GreyboxLevels.ParkGates),
            new LevelSpec(5, "L20", "Fountain Square", "L20_FountainSquare", Bell(75f), 5, GreyboxLevels.FountainSquare),
            new LevelSpec(5, "L21", "Playground", "L21_Playground", Bell(80f), 5, GreyboxLevels.Playground),
            new LevelSpec(5, "L22", "Duck Pond", "L22_DuckPond", Bell(80f), 6, GreyboxLevels.DuckPond),
            new LevelSpec(5, "L23", "The Final Bell", "L23_TheFinalBell", Bell(120f), 7, GreyboxLevels.TheFinalBell),
            LevelSpec.Challenge(5, "C05", "Juggle Champion", "C05_JuggleChampion", GreyboxLevels.JuggleChampion),
        };

        /// <summary>(id, chapter, isChallenge, scene name) for each entry of the level table. Used by tests.</summary>
        public static List<KeyValuePair<string, int>> LevelTable(out List<bool> isChallenge, out List<string> scenes)
        {
            var list = new List<KeyValuePair<string, int>>();
            isChallenge = new List<bool>();
            scenes = new List<string>();
            foreach (var spec in Levels)
            {
                list.Add(new KeyValuePair<string, int>(spec.id, spec.chapter));
                isChallenge.Add(spec.challenge);
                scenes.Add(spec.scene);
            }
            return list;
        }

        /// <summary>The school bell of a level in the table, in seconds (a challenge has none: 0), or -1 for an unknown id. Used by tests.</summary>
        public static float BellTime(string id)
        {
            foreach (var spec in Levels)
                if (spec.id == id) return spec.bell;
            return -1f;
        }

        /// <summary>Does this level of the table start at home (the front door, then the home street)? Every story level does; a challenge does not. Used by tests.</summary>
        public static bool StartsAtHome(string id)
        {
            foreach (var spec in Levels)
                if (spec.id == id) return HomeLeadInRules.StartsAtHome(true, spec.challenge);
            return false;
        }

        static GeneratedContent()
        {
            EditorApplication.delayCall += AutoBuild;
        }

        static void AutoBuild()
        {
            if (SessionState.GetBool(AutoBuildKey, false)) return;
            SessionState.SetBool(AutoBuildKey, true);
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (ReadVersion() >= Version && AllScenesExist()) return;

            Debug.Log("[Kick Off] Generated content is missing or out of date (v" + Version + "). Building levels...");
            BuildAll();
        }

        [MenuItem("Kick Off/Rebuild All Levels")]
        static void RebuildFromMenu()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            BuildAll();
        }

        [MenuItem("Kick Off/Open Level 1")]
        static void OpenFirstLevel()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(Levels[0].ScenePath);
        }

        [MenuItem("Kick Off/Open Menu (FrontEnd)")]
        static void OpenFrontEnd()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(FrontEndScene);
        }

        /// <summary>Rebuild only the menu scene (its 3D stage), keeping the levels as they are.</summary>
        [MenuItem("Kick Off/Rebuild Menu (FrontEnd)")]
        static void RebuildFrontEnd()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            LevelBuildKit.LoadShared();
            var catalog = AssetDatabase.LoadAssetAtPath<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
            var cosmetics = AssetDatabase.LoadAssetAtPath<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset");
            if (catalog == null || cosmetics == null)
            {
                BuildAll();
                return;
            }
            LevelBuildKit.Cosmetics = cosmetics;
            BuildFrontEndScene(catalog, cosmetics);
        }

        /// <summary>
        /// Rebuild only the Holiday Run (its 23 stage scenes and the core scene), keeping the levels and the
        /// menu as they are, and put its scenes in the build settings after the others.
        /// </summary>
        [MenuItem("Kick Off/Rebuild Holiday Run")]
        static void RebuildHolidayRun()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            LevelBuildKit.LoadShared();
            if (LoadCatalog() == null || LoadCosmetics() == null)
            {
                BuildAll();
                return;
            }
            LevelBuildKit.Cosmetics = LoadCosmetics();
            var holiday = HolidayRunBuilder.BuildAll(LoadCatalog, LoadCosmetics);
            var scenes = new List<EditorBuildSettingsScene>();
            foreach (var scene in EditorBuildSettings.scenes)
                if (!scene.path.StartsWith(HolidayRunBuilder.Dir + "/")) scenes.Add(scene);
            foreach (string path in holiday) scenes.Add(new EditorBuildSettingsScene(path, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            AssetDatabase.SaveAssets();
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(FrontEndScene) != null) EditorSceneManager.OpenScene(FrontEndScene);
            Debug.Log("[Kick Off] Built the Holiday Run: its core scene and " + HolidayStages.Count + " stages.");
        }

        static LevelCatalog LoadCatalog() { return AssetDatabase.LoadAssetAtPath<LevelCatalog>(LevelsDir + "/LevelCatalog.asset"); }
        static CosmeticCatalog LoadCosmetics() { return AssetDatabase.LoadAssetAtPath<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset"); }

        [MenuItem("Kick Off/Reset Save Data")]
        static void ResetSave()
        {
            Progression.SaveSystem.ResetProgress();
            Debug.Log("[Kick Off] Save data reset: " + Progression.SaveSystem.FilePath);
        }

        [MenuItem("Kick Off/Give 1000 Coins (testing)")]
        static void GiveCoins()
        {
            Progression.SaveSystem.AddCoins(1000);
            Progression.SaveSystem.Save();
        }

        static readonly ChapterInfo[] Chapters =
        {
            new ChapterInfo { number = 1, title = "Home Street", subtitle = "Out the door and down the road", color = new Color(0.97f, 0.55f, 0.27f) },
            new ChapterInfo { number = 2, title = "Market", subtitle = "Crates, crowds and crossings", color = new Color(0.9f, 0.42f, 0.42f) },
            new ChapterInfo { number = 3, title = "The Beach", subtitle = "Sand, waves and seagulls", color = new Color(0.3f, 0.68f, 0.85f) },
            new ChapterInfo { number = 4, title = "Underpass", subtitle = "Tunnels, pipes and building sites", color = new Color(0.55f, 0.48f, 0.72f) },
            new ChapterInfo { number = 5, title = "Park & School", subtitle = "Dogs, fountains and the final bell", color = new Color(0.42f, 0.7f, 0.4f) },
        };

        public static void BuildAll()
        {
            LevelBuildKit.LoadShared();
            LevelBuildKit.EnsureFolder(ScenesDir + "/Levels");
            LevelBuildKit.EnsureFolder(LevelsDir);
            var cosmetics = BuildCosmetics();
            LevelBuildKit.Cosmetics = cosmetics;

            var catalog = LevelBuildKit.LoadOrCreateAsset<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
            var defs = new List<LevelDefinition>();
            foreach (var spec in Levels) defs.Add(LoadOrCreateLevel(spec));
            catalog.levels = defs;
            catalog.chapters = new List<ChapterInfo>(Chapters);
            EditorUtility.SetDirty(catalog);
            AssetDatabase.SaveAssets();

            DeleteStaleScenes();

            BuildFrontEndScene(catalog, cosmetics);
            var buildScenes = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(FrontEndScene, true) };
            for (int i = 0; i < Levels.Length; i++)
            {
                // Reload shared assets: building the previous scene may have unloaded them.
                var def = AssetDatabase.LoadAssetAtPath<LevelDefinition>(LevelsDir + "/" + Levels[i].id + ".asset");
                catalog = AssetDatabase.LoadAssetAtPath<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
                LevelBuildKit.Cosmetics = AssetDatabase.LoadAssetAtPath<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset");
                LevelBuildKit.BuildScene(Levels[i].ScenePath, def, catalog, Levels[i].layout, Levels[i].chapter);
                buildScenes.Add(new EditorBuildSettingsScene(Levels[i].ScenePath, true));
            }
            LevelBuildKit.BuildScene(TestTrackScene, null, catalog, GreyboxLevels.TestTrack);
            buildScenes.Add(new EditorBuildSettingsScene(TestTrackScene, true));

            // The Holiday Run: its core scene first, then its 23 stages (each loaded into the core as the kid runs).
            foreach (string path in HolidayRunBuilder.BuildAll(LoadCatalog, LoadCosmetics))
                buildScenes.Add(new EditorBuildSettingsScene(path, true));

            EditorBuildSettings.scenes = buildScenes.ToArray();
            BuildScripts.ApplyPlayerSettings();
            WriteVersion();
            AssetDatabase.SaveAssets();

            EditorSceneManager.OpenScene(FrontEndScene);
            Debug.Log("[Kick Off] Built the menu, " + Levels.Length + " levels, the test track and the Holiday Run (its core scene and " + HolidayStages.Count + " stages). The menu is open - press Play.");
        }

        static CosmeticCatalog BuildCosmetics()
        {
            LevelBuildKit.EnsureFolder(CosmeticsDir);
            var catalog = LevelBuildKit.LoadOrCreateAsset<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset");
            catalog.items = new List<CosmeticItem>();
            foreach (var row in CosmeticsTable.Rows())
            {
                var item = LevelBuildKit.LoadOrCreateAsset<CosmeticItem>(CosmeticsDir + "/" + row.id + ".asset");
                item.id = row.id;
                item.displayName = row.name;
                item.category = row.category;
                item.rarity = row.rarity;
                item.price = row.price;
                item.pattern = row.pattern;
                item.primary = row.primary;
                item.secondary = row.secondary;
                item.accent = row.accent;
                item.unlock = row.unlock;
                item.unlockValue = row.unlockValue;
                EditorUtility.SetDirty(item);
                catalog.items.Add(item);
            }
            EditorUtility.SetDirty(catalog);
            return catalog;
        }

        /// <summary>
        /// The menu scene: the live 3D stage (LevelBuildKit.BuildMenuStage: the home street, the
        /// teen juggling, real clouds) behind the menus the FrontEndController builds at runtime.
        /// If the stage can't be built, a plain camera, and the menus draw a flat sky instead.
        /// </summary>
        static void BuildFrontEndScene(LevelCatalog catalog, CosmeticCatalog cosmetics)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            try
            {
                LevelBuildKit.BuildMenuStage(cosmetics);
            }
            catch (Exception e)
            {
                Debug.LogError("[Kick Off] Couldn't build the menu's 3D stage; the menu will use a flat backdrop. " + e);
                scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                var camGo = new GameObject("Main Camera");
                camGo.tag = "MainCamera";
                var cam = camGo.AddComponent<Camera>();
                cam.orthographic = true;
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = LevelBuildKit.SkyColor;
                camGo.AddComponent<AudioListener>();
            }

            var controller = new GameObject("FrontEnd").AddComponent<FrontEndController>();
            controller.levels = catalog;
            controller.cosmetics = cosmetics;
            EditorSceneManager.SaveScene(scene, FrontEndScene);
        }

        static LevelDefinition LoadOrCreateLevel(LevelSpec spec)
        {
            string path = LevelsDir + "/" + spec.id + ".asset";
            var def = AssetDatabase.LoadAssetAtPath<LevelDefinition>(path);
            if (def == null)
            {
                def = ScriptableObject.CreateInstance<LevelDefinition>();
                AssetDatabase.CreateAsset(def, path);
            }
            // The Levels table above is the single source of truth; tune values there.
            def.bellTime = spec.bell;
            def.perfectStreakTarget = spec.streak;
            def.levelId = spec.id;
            def.displayName = spec.name;
            def.sceneName = spec.scene;
            def.chapter = spec.chapter;
            def.isChallenge = spec.challenge;
            EditorUtility.SetDirty(def);
            return def;
        }

        /// <summary>Remove generated level scenes that are no longer in the Levels table.</summary>
        static void DeleteStaleScenes()
        {
            var keep = new HashSet<string>();
            foreach (var spec in Levels) keep.Add(spec.ScenePath);
            foreach (string guid in AssetDatabase.FindAssets("t:Scene", new[] { ScenesDir + "/Levels" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!keep.Contains(path)) AssetDatabase.DeleteAsset(path);
            }
        }

        static bool AllScenesExist()
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(TestTrackScene) == null) return false;
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(FrontEndScene) == null) return false;
            foreach (var spec in Levels)
            {
                if (AssetDatabase.LoadAssetAtPath<SceneAsset>(spec.ScenePath) == null) return false;
            }
            return HolidayRunBuilder.AllScenesExist();
        }

        static int ReadVersion()
        {
            string path = FullPath(VersionFile);
            if (!File.Exists(path)) return 0;
            int v;
            return int.TryParse(File.ReadAllText(path).Trim(), out v) ? v : 0;
        }

        static void WriteVersion()
        {
            File.WriteAllText(FullPath(VersionFile), Version.ToString());
            AssetDatabase.ImportAsset(VersionFile);
        }

        static string FullPath(string assetPath)
        {
            return Path.Combine(Directory.GetParent(Application.dataPath).FullName, assetPath);
        }
    }
}
