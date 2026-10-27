using System;
using System.Collections.Generic;
using System.IO;
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
        public const int Version = 3;

        const string ScenesDir = LevelBuildKit.Root + "/Scenes";
        const string LevelsDir = LevelBuildKit.Root + "/Levels";
        const string VersionFile = ScenesDir + "/GeneratedContentVersion.txt";
        const string TestTrackScene = ScenesDir + "/Phase1_TestTrack.unity";
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

        public static void BuildAll()
        {
            LevelBuildKit.LoadShared();
            LevelBuildKit.EnsureFolder(ScenesDir + "/Levels");
            LevelBuildKit.EnsureFolder(LevelsDir);

            var catalog = LevelBuildKit.LoadOrCreateAsset<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
            var defs = new List<LevelDefinition>();
            foreach (var spec in Levels) defs.Add(LoadOrCreateLevel(spec));
            catalog.levels = defs;
            EditorUtility.SetDirty(catalog);
            AssetDatabase.SaveAssets();

            DeleteStaleScenes();

            var buildScenes = new List<EditorBuildSettingsScene>();
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

            EditorSceneManager.OpenScene(Levels[0].ScenePath);
            Debug.Log("[Dribble To School] Built " + Levels.Length + " levels + test track. Level 1 is open - press Play.");
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
