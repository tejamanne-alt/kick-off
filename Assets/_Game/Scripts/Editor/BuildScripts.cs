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
        /// <summary>
        /// The oldest iOS the game runs on. Xcode's C++ library no longer supports anything older: a target below it compiles
        /// with "The selected platform is no longer supported by libc++" on every IL2CPP file (docs/LEARNINGS.md A13).
        /// </summary>
        public const string IosMinimumVersion = "15.0";

        /// <summary>Is version a (as "15.0" or "16") older than b? Unparseable counts as older, so it gets raised.</summary>
        public static bool OlderThan(string a, string b)
        {
            System.Version va, vb;
            if (!System.Version.TryParse(WithMinor(a), out va)) return true;
            if (!System.Version.TryParse(WithMinor(b), out vb)) return false;
            return va < vb;
        }

        static string WithMinor(string v)
        {
            v = (v ?? "").Trim();
            return v.Length > 0 && v.IndexOf('.') < 0 ? v + ".0" : v;
        }

        /// <summary>Raises Player Settings' iOS target to <see cref="IosMinimumVersion"/> (never lowers it).</summary>
        public static void ApplyIosMinimum()
        {
            if (OlderThan(PlayerSettings.iOS.targetOSVersionString, IosMinimumVersion))
                PlayerSettings.iOS.targetOSVersionString = IosMinimumVersion;
        }

        const string IconPath = LevelBuildKit.Root + "/Art/Generated/AppIcon.png";
        // The app icon's art (tools/blender/app_icon.py and app_icon_compose.py render it from the game's models; README there).
        const string IconArt = LevelBuildKit.Root + "/Art/Icon/AppIcon.png";
        const string IconBack = LevelBuildKit.Root + "/Art/Icon/AppIconBackground.png";
        const string IconFront = LevelBuildKit.Root + "/Art/Icon/AppIconForeground.png";
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
            PlayerSettings.SplashScreen.backgroundColor = new Color(0.22f, 0.43f, 0.69f);

            // Android
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, ApplicationId);
            PlayerSettings.Android.bundleVersionCode = buildNumber;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel26;
            // Play's current requirement, set explicitly so a build can't quietly target an older SDK
            // (the editor must have the Android 16 SDK platform; Unity Hub installs it with Android Build Support).
            PlayerSettings.Android.targetSdkVersion = (AndroidSdkVersions)AndroidTargetApi;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            ApplyAndroidPerformanceSettings();

            // iOS
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, ApplicationId);
            PlayerSettings.iOS.buildNumber = buildNumber.ToString();
            ApplyIosMinimum();
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
            AppleSigning.Apply();   // automatic signing with the team, as in Xcode

            ApplyIcon();
            AssetDatabase.SaveAssets();
            Debug.Log("[Build] Player settings applied: " + ApplicationId + " " + version + " (" + buildNumber + ")");
        }

        /// <summary>
        /// The Android settings that decide how smoothly the game runs on a mid-range phone (docs/PERFORMANCE.md). They live
        /// in ProjectSettings, which is not in git, so they are set here on every build rather than left to whatever a
        /// machine's fresh project generated:
        /// - Optimized Frame Pacing (Swappy): each frame is shown for an even number of the panel's refreshes, instead of an
        ///   irregular mix of 25, 33 and 42 ms on a 120 Hz panel when 60 is missed;
        /// - Blit Type Auto: no extra full-screen copy at the end of every frame;
        /// - frame timing stats (the governor and an on-device overlay can read the GPU's time);
        /// - GPU skinning, batched, for the 60k-triangle kids and the passers-by;
        /// - incremental garbage collection (no long stop-the-world pauses);
        /// - every graphics tier without HDR and without screen-space cascaded shadows: the camera renders to an 8-bit target,
        ///   and the sun's shadows are read straight from the shadow map, so no depth pre-pass of the whole scene and no
        ///   full-screen shadow-collect pass each frame.
        /// Settings whose API names moved between Unity versions are set by reflection and logged if they are not found.
        /// </summary>
        static void ApplyAndroidPerformanceSettings()
        {
            SetStaticBool(typeof(PlayerSettings.Android), "optimizedFramePacing", true);
            PlayerSettings.Android.blitType = AndroidBlitType.Auto;
            PlayerSettings.enableFrameTimingStats = true;
            PlayerSettings.gcIncremental = true;
            SetStaticEnum(typeof(PlayerSettings), "meshDeformation", "GPUBatched");
            ApplyTierSettings(BuildTargetGroup.Android);
        }

        /// <summary>HDR and screen-space (cascaded) shadows off in every graphics tier of the platform (Built-in pipeline).</summary>
        static void ApplyTierSettings(BuildTargetGroup group)
        {
            try
            {
                var editorGraphics = typeof(UnityEditor.Rendering.EditorGraphicsSettings);
                var flags = System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static;
                var get = editorGraphics.GetMethod("GetTierSettings", flags, null, new[] { typeof(BuildTargetGroup), typeof(UnityEngine.Rendering.GraphicsTier) }, null);
                if (get == null) { Debug.LogWarning("[Build] EditorGraphicsSettings.GetTierSettings not found: set HDR and Cascaded Shadows off in Graphics > Tier Settings by hand."); return; }
                var set = editorGraphics.GetMethod("SetTierSettings", flags, null, new[] { typeof(BuildTargetGroup), typeof(UnityEngine.Rendering.GraphicsTier), get.ReturnType }, null);
                if (set == null) { Debug.LogWarning("[Build] EditorGraphicsSettings.SetTierSettings not found."); return; }
                foreach (UnityEngine.Rendering.GraphicsTier tier in Enum.GetValues(typeof(UnityEngine.Rendering.GraphicsTier)))
                {
                    object settings = get.Invoke(null, new object[] { group, tier });
                    SetField(settings, "hdr", false);
                    SetField(settings, "cascadedShadowMaps", false);
                    set.Invoke(null, new object[] { group, tier, settings });
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Build] Tier settings not applied: " + e.Message);
            }
        }

        static void SetField(object boxed, string name, object value)
        {
            var field = boxed.GetType().GetField(name);
            if (field != null) { field.SetValue(boxed, value); return; }
            var property = boxed.GetType().GetProperty(name);
            if (property != null && property.CanWrite) property.SetValue(boxed, value);
            else Debug.LogWarning("[Build] " + boxed.GetType().Name + "." + name + " not found.");
        }

        static void SetStaticBool(Type type, string property, bool value)
        {
            var p = type.GetProperty(property, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
            if (p == null || p.PropertyType != typeof(bool) || !p.CanWrite) { Debug.LogWarning("[Build] " + type.Name + "." + property + " not found."); return; }
            p.SetValue(null, value);
        }

        static void SetStaticEnum(Type type, string property, string value)
        {
            var p = type.GetProperty(property, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
            if (p == null || !p.PropertyType.IsEnum || !p.CanWrite) { Debug.LogWarning("[Build] " + type.Name + "." + property + " not found."); return; }
            try { p.SetValue(null, Enum.Parse(p.PropertyType, value)); }
            catch (Exception e) { Debug.LogWarning("[Build] " + type.Name + "." + property + " = " + value + ": " + e.Message); }
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

        /// <summary>
        /// The app icon: the rendered art (the kid running to school after the ball, Assets/_Game/Art/Icon) as the icon for every
        /// platform, scaled by Unity to every size iOS and Android ask for; on Android also the adaptive icon's two layers (the sky
        /// and the pitch behind, the kid, the ball and the "2" in front, inside the part every launcher's mask keeps) for launchers
        /// from Android 8, which otherwise shrink a square icon onto a white disc. Without the art, the procedural icon as before.
        /// </summary>
        static void ApplyIcon()
        {
            var icon = IconTexture(IconArt, false);
            if (icon == null)
            {
                BakeProceduralIcon();
                return;
            }
            PlayerSettings.SetIcons(NamedBuildTarget.Unknown, new[] { icon }, IconKind.Any);
            var back = IconTexture(IconBack, false);
            var front = IconTexture(IconFront, true);
            // The Android icon kinds by name (Adaptive, Round, Legacy), so this compiles without Android Build Support installed.
            foreach (var kind in AndroidIcons<PlatformIconKind[]>("GetSupportedIconKinds", "GetSupportedIconKindsForPlatform") ?? new PlatformIconKind[0])
            {
                bool adaptive = kind.ToString().IndexOf("Adaptive", StringComparison.OrdinalIgnoreCase) >= 0;
                if (adaptive && (back == null || front == null)) continue;
                var icons = AndroidIcons<PlatformIcon[]>("GetPlatformIcons", "GetPlatformIcons", kind);
                if (icons == null) continue;
                foreach (var platformIcon in icons)
                {
                    if (adaptive) platformIcon.SetTextures(back, front);
                    else platformIcon.SetTexture(icon, 0);
                }
                AndroidIcons<object>("SetPlatformIcons", "SetPlatformIcons", kind, icons);
            }
        }

        /// <summary>
        /// Calls one of PlayerSettings' platform-icon methods for Android: its Unity 6 form (<paramref name="modern"/>, taking a
        /// NamedBuildTarget) if this editor has it, else the older one (<paramref name="older"/>, taking a BuildTargetGroup). They
        /// were renamed between versions, so they are found by name rather than compiled against.
        /// </summary>
        static T AndroidIcons<T>(string modern, string older, params object[] rest) where T : class
        {
            var forms = new[] { new { name = modern, target = (object)NamedBuildTarget.Android }, new { name = older, target = (object)BuildTargetGroup.Android } };
            foreach (var form in forms)
            {
                var args = new object[rest.Length + 1];
                args[0] = form.target;
                Array.Copy(rest, 0, args, 1, rest.Length);
                var types = args.Select(a => a.GetType()).ToArray();
                var method = typeof(PlayerSettings).GetMethods(System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static)
                    .FirstOrDefault(m => m.Name == form.name && m.GetParameters().Length == types.Length
                                         && m.GetParameters().Select((p, i) => p.ParameterType.IsAssignableFrom(types[i])).All(ok => ok));
                if (method != null) return method.Invoke(null, args) as T;
            }
            Debug.LogWarning("[Build] PlayerSettings has no " + modern + " or " + older + ": the Android icons keep the default icon.");
            return null;
        }

        /// <summary>An icon picture from the project, imported as the icon slots want it (full size, uncompressed, no mipmaps), or null if it is missing.</summary>
        static Texture2D IconTexture(string path, bool transparent)
        {
            if (!File.Exists(Path.Combine(Directory.GetParent(Application.dataPath).FullName, path))) return null;
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer != null && (importer.textureType != TextureImporterType.Default || importer.mipmapEnabled || importer.alphaIsTransparency != transparent
                || importer.textureCompression != TextureImporterCompression.Uncompressed || importer.npotScale != TextureImporterNPOTScale.None))
            {
                importer.textureType = TextureImporterType.Default;
                importer.mipmapEnabled = false;
                importer.alphaIsTransparency = transparent;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.npotScale = TextureImporterNPOTScale.None;
                importer.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        /// <summary>Bake the procedural icon and set it as the default icon for every platform (when the rendered art is missing).</summary>
        static void BakeProceduralIcon()
        {
            LevelBuildKit.EnsureFolder(Path.GetDirectoryName(IconPath).Replace('\\', '/'));
            string full = Path.Combine(Directory.GetParent(Application.dataPath).FullName, IconPath);
            File.WriteAllBytes(full, ProceduralArt.AppIcon(1024).ToPng());
            var icon = IconTexture(IconPath, false);
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

        /// <summary>
        /// Build the game as a plain APK and install and launch it on the Android phone plugged in by USB
        /// (USB debugging on). Signed with Unity's debug key, so it needs no upload key; uninstall it
        /// before installing a Play Store version of the game, and the other way round (Android won't
        /// replace an app signed with a different key). Its version code always goes up (<see cref="TestVersionCode"/>),
        /// so it installs over any test build before it, keeping the game's progress.
        /// </summary>
        [MenuItem("Kick Off/Build/Android: Run on Connected Phone (USB)")]
        public static void BuildAndroidRunOnPhone()
        {
            ApplyPlayerSettings();
            EditorUserBuildSettings.buildAppBundle = false;
            bool custom = PlayerSettings.Android.useCustomKeystore;
            PlayerSettings.Android.useCustomKeystore = false;
            try { WithTestVersionCode(() => Build(BuildTarget.Android, Path.Combine(BuildRoot, "Android", "KickOff-test.apk"), BuildOptions.AutoRunPlayer)); }
            finally { PlayerSettings.Android.useCustomKeystore = custom; }
        }

        [MenuItem("Kick Off/Build/Android APK (development)")]
        public static void BuildAndroidDev()
        {
            ApplyPlayerSettings();
            EditorUserBuildSettings.buildAppBundle = false;
            WithTestVersionCode(() => Build(BuildTarget.Android, Path.Combine(BuildRoot, "Android", "KickOff-dev.apk"),
                BuildOptions.Development | BuildOptions.AllowDebugging));
        }

        /// <summary>
        /// The version code of a test APK: the minutes since 2025 (plus 100000), so every test build is newer than the one
        /// before it and installs over it. Android refuses an APK whose version code is lower than the installed one's
        /// (INSTALL_FAILED_VERSION_DOWNGRADE), and the store build number alone can go back (it lives in this checkout's
        /// Player Settings, which aren't in the repository). Never below the store build number.
        /// </summary>
        public static int TestVersionCode()
        {
            var since = DateTime.UtcNow - new DateTime(2025, 1, 1, 0, 0, 0, DateTimeKind.Utc);
            return Math.Max(CurrentBuildNumber(), 100000 + (int)Math.Max(0, since.TotalMinutes));
        }

        /// <summary>Runs a test build with <see cref="TestVersionCode"/>, then puts the store build number back.</summary>
        static void WithTestVersionCode(Action build)
        {
            int storeCode = PlayerSettings.Android.bundleVersionCode;
            int testCode = TestVersionCode();
            PlayerSettings.Android.bundleVersionCode = testCode;
            Debug.Log("[Build] Test APK version code " + testCode + " (the store build number stays " + storeCode + ").");
            try { build(); }
            finally
            {
                PlayerSettings.Android.bundleVersionCode = storeCode;
                AssetDatabase.SaveAssets();
            }
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
                try { WriteSizeReport(report, location); }
                catch (Exception e) { Debug.LogWarning("[Build] No size report: " + e.Message); }
                // From the menu, show the result in Finder: the Xcode project itself when there is one.
                if (!Application.isBatchMode && (options & BuildOptions.AutoRunPlayer) == 0)
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

        /// <summary>
        /// What the build is made of, biggest first: the packed size of every kind of asset (textures, meshes, audio...) and
        /// of the 60 biggest source assets, written beside the build (BuildSize.txt) and summarised in the Console. What isn't
        /// an asset (the compiled code and Unity's own libraries) is the rest of the total.
        /// </summary>
        static void WriteSizeReport(BuildReport report, string location)
        {
            var bySource = new System.Collections.Generic.Dictionary<string, ulong>();
            var byType = new System.Collections.Generic.Dictionary<string, ulong>();
            ulong assets = 0;
            foreach (var packed in report.packedAssets)
            {
                foreach (var info in packed.contents)
                {
                    string source = string.IsNullOrEmpty(info.sourceAssetPath) ? "(made by Unity or by code: " + packed.shortPath + ")" : info.sourceAssetPath;
                    string type = info.type != null ? info.type.Name : "Other";
                    ulong size;
                    bySource.TryGetValue(source, out size);
                    bySource[source] = size + info.packedSize;
                    byType.TryGetValue(type, out size);
                    byType[type] = size + info.packedSize;
                    assets += info.packedSize;
                }
            }
            ulong total = report.summary.totalSize;
            long file = File.Exists(location) ? new FileInfo(location).Length : -1;
            var text = new System.Text.StringBuilder();
            text.AppendLine("Build size report: " + report.summary.platform + ", " + DateTime.Now.ToString("yyyy-MM-dd HH:mm"));
            text.AppendLine("Build output: " + Mb(total) + (file >= 0 ? "; the file itself (compressed): " + Mb((ulong)file) : ""));
            text.AppendLine("Assets, packed (before the APK's compression): " + Mb(assets) + "; the rest (code, Unity's libraries): " + Mb(total > assets ? total - assets : 0));
            text.AppendLine();
            text.AppendLine("By kind:");
            foreach (var kv in byType.OrderByDescending(k => k.Value))
                text.AppendLine("  " + Mb(kv.Value).PadLeft(10) + "  " + kv.Key);
            text.AppendLine();
            text.AppendLine("Biggest assets:");
            foreach (var kv in bySource.OrderByDescending(k => k.Value).Take(60))
                text.AppendLine("  " + Mb(kv.Value).PadLeft(10) + "  " + kv.Key);
            string reportPath = Path.Combine(Path.GetDirectoryName(Path.GetFullPath(location)) ?? BuildRoot, "BuildSize.txt");
            File.WriteAllText(reportPath, text.ToString());
            string top = string.Join(", ", byType.OrderByDescending(k => k.Value).Take(4).Select(k => k.Key + " " + Mb(k.Value)).ToArray());
            Debug.Log("[Build] Size: " + top + ". The full list: " + reportPath);
        }

        static string Mb(ulong bytes) { return (bytes / (1024.0 * 1024.0)).ToString("0.0") + " MB"; }

        static string Env(string name, string fallback)
        {
            string v = Environment.GetEnvironmentVariable(name);
            return string.IsNullOrEmpty(v) ? fallback : v;
        }
    }
}
