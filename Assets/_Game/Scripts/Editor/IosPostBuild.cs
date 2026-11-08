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
    /// </summary>
    public static class IosPostBuild
    {
        /// <summary>The Xcode version the project counts as upgraded for (26.0 as Xcode writes it; any later Xcode asks again).</summary>
        const string XcodeVersion = "2600";

        /// <summary>What iOS shows when it asks the player to allow Bluetooth (the co-op mode's first use).</summary>
        const string BluetoothUsage = "Kick Off 2 uses Bluetooth to find friends' phones nearby and race them to school in Co-op.";

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
            plist.WriteToFile(plistPath);

            string projectPath = PBXProject.GetPBXProjectPath(pathToBuiltProject);
            var project = new PBXProject();
            project.ReadFromFile(projectPath);
            string framework = project.GetUnityFrameworkTargetGuid();
            project.SetBuildProperty(framework, "GCC_WARN_ABOUT_DEPRECATED_FUNCTIONS", "NO");
            project.SetBuildProperty(framework, "CLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS", "NO");
            project.AddBuildProperty(framework, "WARNING_CFLAGS", "-Wno-deprecated-declarations");
            project.AddFrameworkToProject(framework, "CoreBluetooth.framework", false);
            string plugin = project.FindFileGuidByProjectPath("Libraries/Plugins/iOS/DTSCoopBLE.mm");
            if (!string.IsNullOrEmpty(plugin))
                project.SetCompileFlagsForFile(framework, plugin, new System.Collections.Generic.List<string> { "-fobjc-arc" });
            project.WriteToFile(projectPath);

            // What the PBXProject API can't set, in the project file's text.
            string text = File.ReadAllText(projectPath);
            text = Regex.Replace(text, @"LastUpgradeCheck = \d+;", "LastUpgradeCheck = " + XcodeVersion + ";");
            text = Regex.Replace(text, @"LastSwiftUpdateCheck = \d+;", "LastSwiftUpdateCheck = " + XcodeVersion + ";");
            text = Regex.Replace(text, @"(isa = PBXShellScriptBuildPhase;)(?!\s*alwaysOutOfDate)", "$1\n\t\t\talwaysOutOfDate = 1;");
            File.WriteAllText(projectPath, text);
        }
    }
}
#endif
