using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.FrontEnd;
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
        public const int Version = 4;

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
            public Action<TrackBuilder> layout;

            public LevelSpec(int chapter, string id, string name, string scene, float bell, int streak, Action<TrackBuilder> layout)
            {
                this.chapter = chapter; this.id = id; this.name = name; this.scene = scene;
                this.bell = bell; this.streak = streak; this.layout = layout;
            }

            public string ScenePath { get { return ScenesDir + "/Levels/" + scene + ".unity"; } }
        }

        static readonly LevelSpec[] Levels =
        {
            // Chapter 1: Home Street
            new LevelSpec(1, "L01", "Out the Door", "L01_OutTheDoor", 50f, 3, GreyboxLevels.OutTheDoor),
            new LevelSpec(1, "L02", "Parked Cars", "L02_ParkedCars", 55f, 3, GreyboxLevels.ParkedCars),
            new LevelSpec(1, "L03", "Up the Hill", "L03_UpTheHill", 80f, 4, GreyboxLevels.UpTheHill),
            new LevelSpec(1, "L04", "Garden Gate", "L04_GardenGate", 60f, 3, GreyboxLevels.GardenGate),
            new LevelSpec(1, "L05", "Puddle Lane", "L05_PuddleLane", 80f, 4, GreyboxLevels.PuddleLane),
            // Chapter 2: Market and Crossings
            new LevelSpec(2, "L06", "Market Morning", "L06_MarketMorning", 60f, 4, GreyboxLevels.MarketMorning),
            new LevelSpec(2, "L07", "First Crossing", "L07_FirstCrossing", 70f, 3, GreyboxLevels.FirstCrossing),
            new LevelSpec(2, "L08", "Corner Shop", "L08_CornerShop", 70f, 4, GreyboxLevels.CornerShop),
            new LevelSpec(2, "L09", "Fruit Stalls", "L09_FruitStalls", 75f, 5, GreyboxLevels.FruitStalls),
            new LevelSpec(2, "L10", "Rush Hour", "L10_RushHour", 95f, 6, GreyboxLevels.RushHour),
        };

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

            Debug.Log("[Dribble To School] Generated content is missing or out of date (v" + Version + "). Building levels...");
            BuildAll();
        }

        [MenuItem("Dribble To School/Rebuild All Levels")]
        static void RebuildFromMenu()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            BuildAll();
        }

        [MenuItem("Dribble To School/Open Level 1")]
        static void OpenFirstLevel()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(Levels[0].ScenePath);
        }

        [MenuItem("Dribble To School/Open Menu (FrontEnd)")]
        static void OpenFrontEnd()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(FrontEndScene);
        }

        [MenuItem("Dribble To School/Reset Save Data")]
        static void ResetSave()
        {
            Progression.SaveSystem.ResetProgress();
            Debug.Log("[Dribble To School] Save data reset: " + Progression.SaveSystem.FilePath);
        }

        [MenuItem("Dribble To School/Give 1000 Coins (testing)")]
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
                LevelBuildKit.BuildScene(Levels[i].ScenePath, defs[i], catalog, Levels[i].layout);
                buildScenes.Add(new EditorBuildSettingsScene(Levels[i].ScenePath, true));
            }
            LevelBuildKit.BuildScene(TestTrackScene, null, catalog, GreyboxLevels.TestTrack);
            buildScenes.Add(new EditorBuildSettingsScene(TestTrackScene, true));

            EditorBuildSettings.scenes = buildScenes.ToArray();
            LevelBuildKit.ConfigurePlayerSettings();
            WriteVersion();
            AssetDatabase.SaveAssets();

            EditorSceneManager.OpenScene(FrontEndScene);
            Debug.Log("[Dribble To School] Built the menu, " + Levels.Length + " levels and the test track. The menu is open - press Play.");
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
                EditorUtility.SetDirty(item);
                catalog.items.Add(item);
            }
            EditorUtility.SetDirty(catalog);
            return catalog;
        }

        static void BuildFrontEndScene(LevelCatalog catalog, CosmeticCatalog cosmetics)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = LevelBuildKit.SkyColor;
            camGo.AddComponent<AudioListener>();

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
            return true;
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
