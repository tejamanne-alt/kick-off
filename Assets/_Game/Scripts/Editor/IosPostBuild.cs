#if UNITY_IOS
using System.IO;
using UnityEditor;
using UnityEditor.Callbacks;
using UnityEditor.iOS.Xcode;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Finishes the exported Xcode project's Info.plist so uploads don't stall:
    /// - ITSAppUsesNonExemptEncryption = NO: the game makes no network calls, so
    ///   App Store Connect skips the export-compliance question on every build.
    /// - UIRequiresFullScreen = YES: required for a landscape-only iPad app
    ///   (otherwise App Store validation asks for every orientation).
    /// </summary>
    public static class IosPostBuild
    {
        [PostProcessBuild(100)]
        public static void OnPostprocessBuild(BuildTarget target, string pathToBuiltProject)
        {
            if (target != BuildTarget.iOS) return;
            string plistPath = Path.Combine(pathToBuiltProject, "Info.plist");
            var plist = new PlistDocument();
            plist.ReadFromFile(plistPath);
            plist.root.SetBoolean("ITSAppUsesNonExemptEncryption", false);
            plist.root.SetBoolean("UIRequiresFullScreen", true);
            plist.WriteToFile(plistPath);
        }
    }
}
#endif
