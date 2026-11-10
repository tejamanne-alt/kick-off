using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Android;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Every Android APK gets a version code newer than any APK before it (<see cref="BuildScripts.TestVersionCode"/>), however
    /// it is built (docs/LEARNINGS.md A14). The Kick Off > Build menu's APK builds did this already; an APK from Unity's own
    /// Build button carried the store build number, a small number, and Android refused to install it over a test build
    /// already on the phone (INSTALL_FAILED_VERSION_DOWNGRADE, shown on the phone as "App not installed").
    ///
    /// Written into the generated Gradle project (launcher/build.gradle), so Player Settings' store build number is never
    /// touched, even by a build that fails. App bundles (.aab, the store uploads) keep the store build number.
    /// </summary>
    public class AndroidApkVersionCode : IPostGenerateGradleAndroidProject
    {
        public int callbackOrder { get { return 2; } }

        public void OnPostGenerateGradleAndroidProject(string path)
        {
            if (EditorUserBuildSettings.buildAppBundle) return;
            // (path is the unityLibrary module; the version code is the launcher's, beside it)
            string launcher = Path.GetFullPath(Path.Combine(path, "..", "launcher"));
            string gradle = Path.Combine(launcher, "build.gradle");
            if (!File.Exists(gradle)) gradle = Path.Combine(launcher, "build.gradle.kts");
            if (!File.Exists(gradle))
            {
                Debug.LogWarning("[Build] launcher/build.gradle not found: the APK keeps version code " +
                    PlayerSettings.Android.bundleVersionCode + ". If the phone has a newer test build, uninstall it first.");
                return;
            }
            int code = BuildScripts.TestVersionCode();
            string text = File.ReadAllText(gradle);
            var versionCode = new Regex(@"(\bversionCode\s*=?\s*)\d+");
            if (!versionCode.IsMatch(text))
            {
                Debug.LogWarning("[Build] No versionCode in " + gradle + ": the APK keeps version code " + PlayerSettings.Android.bundleVersionCode + ".");
                return;
            }
            File.WriteAllText(gradle, versionCode.Replace(text, m => m.Groups[1].Value + code, 1));
            Debug.Log("[Build] APK version code " + code + " (newer than every APK before it; the store build number stays " +
                PlayerSettings.Android.bundleVersionCode + ").");
        }
    }
}
