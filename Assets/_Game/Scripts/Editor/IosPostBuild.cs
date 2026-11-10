#if UNITY_IOS
using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Callbacks;
using UnityEditor.iOS.Xcode;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Finishes the exported Xcode project so uploads don't stall and Xcode builds without warnings:
    /// - Info.plist: ITSAppUsesNonExemptEncryption = NO (the game makes no network calls, so App Store Connect skips the
    ///   export-compliance question on every build) and UIRequiresFullScreen = YES (required for a landscape-only iPad
    ///   app; otherwise App Store validation asks for every orientation).
    /// - UnityFramework: Unity's own trampoline code (UnityAppController, UnityRendering) uses properties that Unity
    ///   itself marks deprecated; those warnings are Unity's, not the game's, so the target doesn't report deprecations.
    /// - Co-op over Bluetooth (Coop/, Plugins/iOS/DTSCoopBLE.mm): NSBluetoothAlwaysUsageDescription (iOS asks the player
    ///   with it the first time the co-op screen opens; without it the app is killed when Bluetooth starts), CoreBluetooth
    ///   linked into UnityFramework, and the plugin compiled with ARC (it is written for it).
    /// - The project is marked as checked against this Xcode ("Update to recommended settings": Unity writes an old
    ///   LastUpgradeCheck), and every Run Script phase that names no inputs or outputs (GameAssembly's IL2CPP step) is
    ///   marked to run on every build, which it must: Xcode would otherwise warn that it "will be run during every build".
    /// - GameAssembly (the IL2CPP code, a static library): every target and configuration builds for at least
    ///   BuildScripts.IosMinimumVersion (below it, Xcode's libc++ warns "The selected platform is no longer supported" on
    ///   every file), and libtool doesn't warn about the IL2CPP files that hold no code ("'x.o' has no symbols": an empty
    ///   assembly's file, which is expected), with -no_warning_for_no_symbols (docs/LEARNINGS.md A13).
    /// </summary>
    public static class IosPostBuild
    {
        /// <summary>A language's InfoPlist.strings, holding the Bluetooth question (a strings file: "key" = "value";).</summary>
        static void WriteInfoPlistStrings(string pathToBuiltProject, string language, string bluetoothUsage)
        {
            string folder = Path.Combine(pathToBuiltProject, language + ".lproj");
            Directory.CreateDirectory(folder);
            string value = bluetoothUsage.Replace("\\", "\\\\").Replace("\"", "\\\"");
            string text = "/* Written by Editor/IosPostBuild.cs */\n\"NSBluetoothAlwaysUsageDescription\" = \"" + value + "\";\n";
            File.WriteAllText(Path.Combine(folder, "InfoPlist.strings"), text, new System.Text.UTF8Encoding(false));
        }

        /// <summary>The Xcode version the project counts as upgraded for (26.0 as Xcode writes it; any later Xcode asks again).</summary>
        const string XcodeVersion = "2600";

        /// <summary>What iOS shows when it asks the player to allow Bluetooth (the co-op mode's first use).</summary>
        const string BluetoothUsage = "Kick Off 2 uses Bluetooth to find friends' phones nearby and race them to school in Co-op.";
        /// <summary>The same in Spanish, the game's other language (es.lproj/InfoPlist.strings).</summary>
        const string BluetoothUsageEs = "Kick Off 2 usa el Bluetooth para encontrar los móviles de tus amigos cerca y echar carreras hasta el cole en Cooperativo.";
        /// <summary>The languages the game speaks (Localization/StringTables), declared so iOS uses them for its own text too.</summary>
        static readonly string[] Languages = { "en", "es" };

        [PostProcessBuild(100)]
        public static void OnPostprocessBuild(BuildTarget target, string pathToBuiltProject)
        {
            if (target != BuildTarget.iOS) return;
            string plistPath = Path.Combine(pathToBuiltProject, "Info.plist");
            var plist = new PlistDocument();
            plist.ReadFromFile(plistPath);
            plist.root.SetBoolean("ITSAppUsesNonExemptEncryption", false);
            plist.root.SetBoolean("UIRequiresFullScreen", true);
            plist.root.SetString("NSBluetoothAlwaysUsageDescription", BluetoothUsage);
            var languages = plist.root.CreateArray("CFBundleLocalizations");
            foreach (string language in Languages) languages.AddString(language);
            plist.WriteToFile(plistPath);
            // The Bluetooth question in each language: iOS reads a language's InfoPlist.strings over Info.plist's text.
            WriteInfoPlistStrings(pathToBuiltProject, "en", BluetoothUsage);
            WriteInfoPlistStrings(pathToBuiltProject, "es", BluetoothUsageEs);

            string projectPath = PBXProject.GetPBXProjectPath(pathToBuiltProject);
            var project = new PBXProject();
            project.ReadFromFile(projectPath);
            string framework = project.GetUnityFrameworkTargetGuid();
            project.SetBuildProperty(framework, "GCC_WARN_ABOUT_DEPRECATED_FUNCTIONS", "NO");
            project.SetBuildProperty(framework, "CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS", "NO");
            project.AddBuildProperty(framework, "WARNING_CFLAGS", "-Wno-deprecated-declarations");
            project.AddFrameworkToProject(framework, "CoreBluetooth.framework", false);
            // (each .lproj as a folder reference: copied into the app as it is, so iOS finds es.lproj/InfoPlist.strings)
            string app = project.GetUnityMainTargetGuid();
            foreach (string language in Languages)
            {
                string folder = language + ".lproj";
                if (string.IsNullOrEmpty(project.FindFileGuidByProjectPath(folder)))
                    project.AddFileToBuild(app, project.AddFolderReference(folder, folder, PBXSourceTree.Source));   // (relative to the Xcode project)
            }
            string plugin = project.FindFileGuidByProjectPath("Libraries/Plugins/iOS/DTSCoopBLE.mm");
            if (!string.IsNullOrEmpty(plugin))
                project.SetCompileFlagsForFile(framework, plugin, new System.Collections.Generic.List<string> { "-fobjc-arc" });
            else
                // (the plugin refuses to compile without ARC, so the build fails loudly rather than leaking: but say why here)
                UnityEngine.Debug.LogWarning("[IosPostBuild] Libraries/Plugins/iOS/DTSCoopBLE.mm not found in the Xcode project: "
                    + "co-op Bluetooth needs it compiled with -fobjc-arc (set it on the file's build phase by hand).");
            // GameAssembly's libtool: no warning for the IL2CPP files with no code (on the project too, which every static
            // library target inherits, in case a Unity version names the target otherwise)
            const string NoSymbolsFlag = "-no_warning_for_no_symbols";
            project.AddBuildProperty(project.ProjectGuid(), "OTHER_LIBTOOLFLAGS", NoSymbolsFlag);
            string gameAssembly = TargetByName(project, "GameAssembly");
            if (!string.IsNullOrEmpty(gameAssembly)) project.AddBuildProperty(gameAssembly, "OTHER_LIBTOOLFLAGS", NoSymbolsFlag);
            project.WriteToFile(projectPath);

            // What the PBXProject API can't set, in the project file's text.
            string text = File.ReadAllText(projectPath);
            text = Regex.Replace(text, @"LastUpgradeCheck = \d+;", "LastUpgradeCheck = " + XcodeVersion + ";");
            text = Regex.Replace(text, @"LastSwiftUpdateCheck = \d+;", "LastSwiftUpdateCheck = " + XcodeVersion + ";");
            text = Regex.Replace(text, @"(isa = PBXShellScriptBuildPhase;)(?!\s*alwaysOutOfDate)", "$1\n\t\t\talwaysOutOfDate = 1;");
            // every target's and configuration's deployment target at least the minimum (GameAssembly's included)
            text = Regex.Replace(text, @"IPHONEOS_DEPLOYMENT_TARGET = ""?([0-9.]+)""?;", m =>
                BuildScripts.OlderThan(m.Groups[1].Value, BuildScripts.IosMinimumVersion)
                    ? "IPHONEOS_DEPLOYMENT_TARGET = " + BuildScripts.IosMinimumVersion + ";" : m.Value);
            File.WriteAllText(projectPath, text);
        }

        /// <summary>
        /// A native target's GUID by its name (null if none). Called by reflection: PBXProject.TargetGuidByName is the API's
        /// only lookup by name, and some Unity versions mark it deprecated (for Unity's own two targets), which would put a
        /// warning in every compile.
        /// </summary>
        static string TargetByName(PBXProject project, string name)
        {
            var lookup = typeof(PBXProject).GetMethod("TargetGuidByName", new[] { typeof(string) });
            return lookup == null ? null : lookup.Invoke(project, new object[] { name }) as string;
        }
    }
}
#endif
