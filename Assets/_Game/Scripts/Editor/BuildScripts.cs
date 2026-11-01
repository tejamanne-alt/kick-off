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
    /// DTS_APPLE_TEAM_ID (iOS automatic signing; see AppleSigning).
    /// </summary>
    public static class BuildScripts
    {
        public const string CompanyName = "Astradite";
        public const string ProductName = "Kick Off 2";
        /// <summary>The app's bundle identifier (iOS) and package name (Android). Fixed for good once the app is uploaded.</summary>
        public const string ApplicationId = "com.astradite.kickoff2";
        /// <summary>Google Play's target API level for new apps and updates (Android 16, from 31 August 2026).</summary>
        public const int AndroidTargetApi = 36;
        public const string DefaultVersion = "1.0.0";

        const string IconPath = LevelBuildKit.Root + "/Art/Generated/AppIcon.png";
        const string BuildRoot = "Builds";

        [MenuItem("Kick Off/Build/Apply Store Player Settings")]
        public static void ApplyPlayerSettings()
        {
            // The version and build number stay as they are (Player Settings, or Bump Build Number
            // below) unless DTS_VERSION / DTS_BUILD_NUMBER say otherwise; a fresh project starts at
            // 1.0.0 (1). Both stores refuse a build number they have already seen.
            string version = Env("DTS_VERSION", string.IsNullOrEmpty(PlayerSettings.bundleVersion) || PlayerSettings.bundleVersion == "0.1" ? DefaultVersion : PlayerSettings.bundleVersion);
            int buildNumber = int.Parse(Env("DTS_BUILD_NUMBER", CurrentBuildNumber().ToString()));

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

            // Splash: the game's deep blue sky behind the (required) Unity logo, as the menu's splash.
            PlayerSettings.SplashScreen.backgroundColor = new Color(0.16f, 0.39f, 0.75f);

            // Android
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, ApplicationId);
            PlayerSettings.Android.bundleVersionCode = buildNumber;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel26;
            // Play's current requirement, set explicitly so a build can't quietly target an older SDK
            // (the editor must have the Android 16 SDK platform; Unity Hub installs it with Android Build Support).
            PlayerSettings.Android.targetSdkVersion = (AndroidSdkVersions)AndroidTargetApi;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;

            // iOS
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, ApplicationId);
            PlayerSettings.iOS.buildNumber = buildNumber.ToString();
            PlayerSettings.iOS.targetOSVersionString = "15.0";
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
            AppleSigning.Apply();   // automatic signing with the team, as in Xcode

            ApplyIcon();
            AssetDatabase.SaveAssets();
            Debug.Log("[Build] Player settings applied: " + ApplicationId + " " + version + " (" + buildNumber + ")");
        }

        /// <summary>The build number now in Player Settings (the higher of iOS's and Android's), at least 1.</summary>
        static int CurrentBuildNumber()
        {
            int ios;
            if (!int.TryParse(PlayerSettings.iOS.buildNumber, out ios)) ios = 0;
            return Mathf.Max(1, Mathf.Max(ios, PlayerSettings.Android.bundleVersionCode));
        }

        /// <summary>Raise the build number by one for both stores (do this before every new upload).</summary>
        [MenuItem("Kick Off/Build/Bump Build Number")]
        public static void BumpBuildNumber()
        {
            int next = CurrentBuildNumber() + 1;
            PlayerSettings.iOS.buildNumber = next.ToString();
            PlayerSettings.Android.bundleVersionCode = next;
            AssetDatabase.SaveAssets();
            Debug.Log("[Build] Build number is now " + next + " (version " + PlayerSettings.bundleVersion + ").");
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

        [MenuItem("Kick Off/Build/Android App Bundle (release)")]
        public static void BuildAndroidRelease()
        {
            ApplyPlayerSettings();
            if (!ConfigureAndroidSigning()) return;
            EditorUserBuildSettings.buildAppBundle = true;
            Build(BuildTarget.Android, Path.Combine(BuildRoot, "Android", "KickOff.aab"), BuildOptions.None);
        }

        [MenuItem("Kick Off/Build/Android APK (development)")]
        public static void BuildAndroidDev()
        {
            ApplyPlayerSettings();
            EditorUserBuildSettings.buildAppBundle = false;
            Build(BuildTarget.Android, Path.Combine(BuildRoot, "Android", "KickOff-dev.apk"),
                BuildOptions.Development | BuildOptions.AllowDebugging);
        }

        /// <summary>The Xcode project for real iPhones and iPads: the one to archive and upload.</summary>
        [MenuItem("Kick Off/Build/iOS Xcode Project")]
        public static void BuildIOS()
        {
            ApplyPlayerSettings();
            PlayerSettings.iOS.sdkVersion = iOSSdkVersion.DeviceSDK;
            Build(BuildTarget.iOS, Path.Combine(BuildRoot, "iOS"), BuildOptions.None);
        }

        /// <summary>
        /// A separate Xcode project for the Simulator (Unity builds the Simulator and devices
        /// separately: a device project installs in the Simulator but can't launch there). For
        /// testing and store screenshots only; it can't be uploaded. Player Settings go back to the
        /// device SDK afterwards, so the store build is never affected.
        /// </summary>
        [MenuItem("Kick Off/Build/iOS Simulator Project (testing only)")]
        public static void BuildIOSSimulator()
        {
            BuildForSimulator("iOS-Simulator", null);
        }

        /// <summary>
        /// A Simulator project that takes the store screenshots by itself when it launches (the
        /// ScreenshotTour, compiled in only here through the DTS_SCREENSHOTS define): run it on the
        /// Simulator of each size the store asks for. Never upload this one.
        /// </summary>
        [MenuItem("Kick Off/Build/iOS Screenshot Project (Simulator)")]
        public static void BuildIOSScreenshots()
        {
            BuildForSimulator("iOS-Screenshots", new[] { "DTS_SCREENSHOTS" });
        }

        static void BuildForSimulator(string folder, string[] defines)
        {
            ApplyPlayerSettings();
            PlayerSettings.iOS.sdkVersion = iOSSdkVersion.SimulatorSDK;
            SetSimulatorArchitecture();
            try { Build(BuildTarget.iOS, Path.Combine(BuildRoot, folder), BuildOptions.None, defines); }
            finally
            {
                PlayerSettings.iOS.sdkVersion = iOSSdkVersion.DeviceSDK;
                AssetDatabase.SaveAssets();
            }
        }

        /// <summary>
        /// Build the Simulator app for this Mac's own processor (Apple silicon: arm64), so it runs
        /// natively rather than through Rosetta. Set by name, as the setting's API differs between
        /// Unity versions; if it isn't there, Unity's default stays.
        /// </summary>
        static void SetSimulatorArchitecture()
        {
            var prop = typeof(PlayerSettings.iOS).GetProperty("simulatorSdkArchitecture",
                System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
            if (prop == null || !prop.PropertyType.IsEnum) return;
            bool arm = System.Runtime.InteropServices.RuntimeInformation.OSArchitecture == System.Runtime.InteropServices.Architecture.Arm64;
            string want = arm ? "ARM64" : "X86_64";
            foreach (string name in Enum.GetNames(prop.PropertyType))
                if (string.Equals(name, want, StringComparison.OrdinalIgnoreCase))
                {
                    prop.SetValue(null, Enum.Parse(prop.PropertyType, name), null);
                    return;
                }
        }

        /// <summary>
        /// Sign the bundle with the upload key: from DTS_KEYSTORE_PATH / DTS_KEYSTORE_PASS / DTS_KEY_ALIAS /
        /// DTS_KEY_PASS when set (command-line builds), else the keystore chosen in Player Settings >
        /// Android > Publishing Settings. Play refuses a bundle signed with the debug key, so with no key
        /// (or its passwords not entered this session: Unity forgets them when it closes) this says what
        /// to do and returns false instead of building one.
        /// </summary>
        static bool ConfigureAndroidSigning()
        {
            string keystore = Env("DTS_KEYSTORE_PATH", "");
            if (keystore.Length > 0)
            {
                PlayerSettings.Android.useCustomKeystore = true;
                PlayerSettings.Android.keystoreName = keystore;
                PlayerSettings.Android.keystorePass = Env("DTS_KEYSTORE_PASS", "");
                PlayerSettings.Android.keyaliasName = Env("DTS_KEY_ALIAS", "");
                PlayerSettings.Android.keyaliasPass = Env("DTS_KEY_PASS", "");
                return true;
            }

            string problem = null;
            if (!PlayerSettings.Android.useCustomKeystore || string.IsNullOrEmpty(PlayerSettings.Android.keystoreName))
                problem = "No upload key is set, and Google Play refuses bundles signed with Unity's debug key.\n\n" +
                    "Edit > Project Settings > Player > Android > Publishing Settings: tick Custom Keystore, then Keystore Manager > " +
                    "Keystore... > Create New (save it outside the project and back it up), add a key with the alias \"upload\", " +
                    "and choose it.";
            else if (!File.Exists(PlayerSettings.Android.keystoreName))
                problem = "The keystore in Publishing Settings isn't there any more:\n" + PlayerSettings.Android.keystoreName;
            else if (string.IsNullOrEmpty(PlayerSettings.Android.keyaliasName))
                problem = "Choose the key (alias \"upload\") under Project Key in Player Settings > Android > Publishing Settings.";
            else if (string.IsNullOrEmpty(PlayerSettings.Android.keystorePass) || string.IsNullOrEmpty(PlayerSettings.Android.keyaliasPass))
                problem = "Enter the keystore password and the key password in Player Settings > Android > Publishing Settings " +
                    "(Unity forgets them each time it closes), then build again.";
            if (problem == null) return true;

            if (Application.isBatchMode)
            {
                Debug.LogError("[Build] " + problem.Replace("\n", " "));
                EditorApplication.Exit(1);
            }
            else
            {
                EditorUtility.DisplayDialog("Upload key needed", problem, "OK");
                SettingsService.OpenProjectSettings("Project/Player");
            }
            return false;
        }

        static void Build(BuildTarget target, string location, BuildOptions options, string[] extraDefines = null)
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
                extraScriptingDefines = extraDefines,
            });
            var summary = report.summary;
            if (summary.result == BuildResult.Succeeded)
            {
                Debug.Log("[Build] " + target + " succeeded: " + Path.GetFullPath(location) + " (" + (summary.totalSize / (1024 * 1024)) + " MB)");
                // From the menu, show the result in Finder: the Xcode project itself when there is one.
                if (!Application.isBatchMode)
                {
                    string xcode = Path.Combine(location, "Unity-iPhone.xcodeproj");
                    EditorUtility.RevealInFinder(Directory.Exists(xcode) ? xcode : location);
                }
            }
            else
            {
                Debug.LogError("[Build] " + target + " failed: " + summary.result + " with " + summary.totalErrors + " errors");
                if (Application.isBatchMode) EditorApplication.Exit(1);
                else EditorUtility.DisplayDialog("Build failed", "The " + target + " build failed with " + summary.totalErrors +
                    " error(s). The Console has the details (the first red line is usually the cause).", "OK");
            }
        }

        static string Env(string name, string fallback)
        {
            string v = Environment.GetEnvironmentVariable(name);
            return string.IsNullOrEmpty(v) ? fallback : v;
        }
    }
}
