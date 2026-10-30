using System;
using System.IO;
using System.Linq;
using DribbleToSchool.Art;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Store-ready player settings and one-click / CI builds.
    ///
    /// CI usage:
    ///   Unity -batchmode -quit -projectPath . -executeMethod DribbleToSchool.EditorTools.BuildScripts.BuildAndroidRelease
    ///   Unity -batchmode -quit -projectPath . -executeMethod DribbleToSchool.EditorTools.BuildScripts.BuildIOS
    ///
    /// Environment overrides: DTS_BUILD_NUMBER, DTS_VERSION,
    /// DTS_KEYSTORE_PATH / DTS_KEYSTORE_PASS / DTS_KEY_ALIAS / DTS_KEY_PASS (Android signing),
    /// DTS_APPLE_TEAM_ID (iOS automatic signing).
    /// </summary>
    public static class BuildScripts
    {
        // Change these to your own studio and app ids before the first store upload.
        public const string CompanyName = "Your Studio";
        public const string ProductName = "Dribble To School";
        public const string ApplicationId = "com.yourstudio.dribbletoschool";
        public const string DefaultVersion = "1.0.0";

        const string IconPath = LevelBuildKit.Root + "/Art/Generated/AppIcon.png";
        const string BuildRoot = "Builds";

        [MenuItem("Dribble To School/Build/Apply Store Player Settings")]
        public static void ApplyPlayerSettings()
        {
            string version = Env("DTS_VERSION", DefaultVersion);
            int buildNumber = int.Parse(Env("DTS_BUILD_NUMBER", "1"));

            PlayerSettings.companyName = CompanyName;
            PlayerSettings.productName = ProductName;
            PlayerSettings.bundleVersion = version;

            // Landscape only.
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.runInBackground = false;

            // Splash: warm paper colour behind the (required) Unity logo.
            PlayerSettings.SplashScreen.backgroundColor = new Color(0.99f, 0.9f, 0.76f);

            // Android
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, ApplicationId);
            PlayerSettings.Android.bundleVersionCode = buildNumber;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel26;
            PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;   // Play requires a recent target API
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;

            // iOS
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, ApplicationId);
            PlayerSettings.iOS.buildNumber = buildNumber.ToString();
            PlayerSettings.iOS.targetOSVersionString = "15.0";
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
            string team = Env("DTS_APPLE_TEAM_ID", "");
            if (team.Length > 0)
            {
                PlayerSettings.iOS.appleEnableAutomaticSigning = true;
                PlayerSettings.iOS.appleDeveloperTeamID = team;
            }

            ApplyIcon();
            AssetDatabase.SaveAssets();
            Debug.Log("[Build] Player settings applied: " + ApplicationId + " " + version + " (" + buildNumber + ")");
        }

        /// <summary>Bake the procedural icon and set it as the default icon for every platform.</summary>
        static void ApplyIcon()
        {
            LevelBuildKit.EnsureFolder(Path.GetDirectoryName(IconPath).Replace('\\', '/'));
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, IconPath);
            File.WriteAllBytes(full, ProceduralArt.AppIcon(1024).ToPng());
            AssetDatabase.ImportAsset(IconPath, ImportAssetOptions.ForceSynchronousImport);
            var importer = AssetImporter.GetAtPath(IconPath) as TextureImporter;
            if (importer != null)
            {
                importer.textureType = TextureImporterType.Default;
                importer.mipmapEnabled = false;
                importer.alphaIsTransparency = false;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.npotScale = TextureImporterNPOTScale.None;
                importer.SaveAndReimport();
            }
            var icon = AssetDatabase.LoadAssetAtPath<Texture2D>(IconPath);
            if (icon != null) PlayerSettings.SetIcons(NamedBuildTarget.Unknown, new[] { icon }, IconKind.Any);
        }

        [MenuItem("Dribble To School/Build/Android App Bundle (release)")]
        public static void BuildAndroidRelease()
        {
            ApplyPlayerSettings();
            ConfigureAndroidSigning();
            EditorUserBuildSettings.buildAppBundle = true;
            Build(BuildTarget.Android, Path.Combine(BuildRoot, "Android", "DribbleToSchool.aab"), BuildOptions.None);
        }

        [MenuItem("Dribble To School/Build/Android APK (development)")]
        public static void BuildAndroidDev()
        {
            ApplyPlayerSettings();
            EditorUserBuildSettings.buildAppBundle = false;
            Build(BuildTarget.Android, Path.Combine(BuildRoot, "Android", "DribbleToSchool-dev.apk"),
                BuildOptions.Development | BuildOptions.AllowDebugging);
        }

        [MenuItem("Dribble To School/Build/iOS Xcode Project")]
        public static void BuildIOS()
        {
            ApplyPlayerSettings();
            Build(BuildTarget.iOS, Path.Combine(BuildRoot, "iOS"), BuildOptions.None);
        }

        static void ConfigureAndroidSigning()
        {
            string keystore = Env("DTS_KEYSTORE_PATH", "");
            if (keystore.Length == 0)
            {
                Debug.LogWarning("[Build] DTS_KEYSTORE_PATH not set: the bundle will use the debug key and can't be uploaded to Play.");
                PlayerSettings.Android.useCustomKeystore = false;
                return;
            }
            PlayerSettings.Android.useCustomKeystore = true;
            PlayerSettings.Android.keystoreName = keystore;
            PlayerSettings.Android.keystorePass = Env("DTS_KEYSTORE_PASS", "");
            PlayerSettings.Android.keyaliasName = Env("DTS_KEY_ALIAS", "");
            PlayerSettings.Android.keyaliasPass = Env("DTS_KEY_PASS", "");
        }

        static void Build(BuildTarget target, string location, BuildOptions options)
        {
            string[] scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            if (scenes.Length == 0)
            {
                GeneratedContent.BuildAll();
                scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray();
            }
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(location)) ?? BuildRoot);

            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = location,
                target = target,
                options = options,
            });
            var summary = report.summary;
            if (summary.result == BuildResult.Succeeded)
                Debug.Log("[Build] " + target + " succeeded: " + location + " (" + (summary.totalSize / (1024 * 1024)) + " MB)");
            else
            {
                Debug.LogError("[Build] " + target + " failed: " + summary.result + " with " + summary.totalErrors + " errors");
                if (Application.isBatchMode) EditorApplication.Exit(1);
            }
        }

        static string Env(string name, string fallback)
        {
            string v = Environment.GetEnvironmentVariable(name);
            return string.IsNullOrEmpty(v) ? fallback : v;
        }
    }
}
