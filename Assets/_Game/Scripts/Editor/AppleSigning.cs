using System.Diagnostics;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;
#if UNITY_IOS
using UnityEditor.iOS.Xcode;
#endif
using Debug = UnityEngine.Debug;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The iOS signing every build gets, kept in code since Player Settings aren't in the repository:
    /// Xcode manages signing automatically, for the app's bundle identifier
    /// (<see cref="BuildScripts.ApplicationId"/>), with the Apple developer team. Applied to Player
    /// Settings whenever the editor loads, and written into the exported Xcode project after each iOS
    /// build, so Xcode opens ready to sign and run.
    /// </summary>
    [InitializeOnLoad]
    public class AppleSigning : IPostprocessBuildWithReport
    {
        /// <summary>
        /// The Apple developer Team ID (10 characters: Xcode's Build Settings, Development Team, or
        /// developer.apple.com, Membership details). Empty: read from the "Apple Development"
        /// certificate in this Mac's keychain (its organisational unit is the team).
        /// </summary>
        public const string TeamId = "";

        const string NoTeamKey = "DribbleToSchool.AppleTeamNotFound";

        static AppleSigning()
        {
            EditorApplication.delayCall += Apply;
        }

        /// <summary>Bundle identifier, automatic signing and the team, into the iOS Player Settings.</summary>
        public static void Apply()
        {
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, BuildScripts.ApplicationId);
            PlayerSettings.iOS.appleEnableAutomaticSigning = true;
            string team = Team();
            if (team.Length > 0 && PlayerSettings.iOS.appleDeveloperTeamID != team)
            {
                PlayerSettings.iOS.appleDeveloperTeamID = team;
                Debug.Log("[Signing] iOS builds sign automatically with team " + team + " as " + BuildScripts.ApplicationId + ".");
            }
        }

        /// <summary>
        /// The team to sign with: DTS_APPLE_TEAM_ID (for CI), else <see cref="TeamId"/>, else the one
        /// already in Player Settings, else the keychain's Apple Development certificate. Empty if none.
        /// </summary>
        public static string Team()
        {
            string env = System.Environment.GetEnvironmentVariable("DTS_APPLE_TEAM_ID");
            if (!string.IsNullOrEmpty(env)) return env.Trim();
            if (TeamId.Length > 0) return TeamId;
            if (!string.IsNullOrEmpty(PlayerSettings.iOS.appleDeveloperTeamID)) return PlayerSettings.iOS.appleDeveloperTeamID;
            return KeychainTeam();
        }

        /// <summary>The organisational unit (the Team ID) of the first Apple Development certificate in the login keychain.</summary>
        static string KeychainTeam()
        {
            if (Application.platform != RuntimePlatform.OSXEditor || SessionState.GetBool(NoTeamKey, false)) return "";
            string pem = Run("/usr/bin/security", "find-certificate -c \"Apple Development\" -p", null);
            string subject = pem.Contains("BEGIN CERTIFICATE") ? Run("/usr/bin/openssl", "x509 -noout -subject", pem) : "";
            var match = Regex.Match(subject, @"OU\s*=\s*([A-Z0-9]{10})");
            if (match.Success) return match.Groups[1].Value;
            SessionState.SetBool(NoTeamKey, true);   // don't ask the keychain again this session
            Debug.LogWarning("[Signing] No Apple Development certificate found in the keychain: set AppleSigning.TeamId (or DTS_APPLE_TEAM_ID) so Xcode knows the team.");
            return "";
        }

        static string Run(string file, string arguments, string input)
        {
            try
            {
                var info = new ProcessStartInfo(file, arguments)
                {
                    UseShellExecute = false,
                    RedirectStandardInput = input != null,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                };
                using (var process = Process.Start(info))
                {
                    if (input != null)
                    {
                        process.StandardInput.Write(input);
                        process.StandardInput.Close();
                    }
                    string output = process.StandardOutput.ReadToEnd();
                    process.WaitForExit(5000);
                    return output;
                }
            }
            catch (System.Exception)
            {
                return "";
            }
        }

        public int callbackOrder { get { return 100; } }

        /// <summary>Writes the same signing into the exported Xcode project (both targets), whatever Player Settings say.</summary>
        public void OnPostprocessBuild(BuildReport report)
        {
#if UNITY_IOS
            if (report.summary.platform != BuildTarget.iOS) return;
            string path = PBXProject.GetPBXProjectPath(report.summary.outputPath);
            var project = new PBXProject();
            project.ReadFromFile(path);
            string app = project.GetUnityMainTargetGuid(), framework = project.GetUnityFrameworkTargetGuid();
            string team = Team();
            project.SetBuildProperty(app, "PRODUCT_BUNDLE_IDENTIFIER", BuildScripts.ApplicationId);
            foreach (string target in new[] { app, framework })
            {
                project.SetBuildProperty(target, "CODE_SIGN_STYLE", "Automatic");
                project.SetBuildProperty(target, "PROVISIONING_PROFILE_SPECIFIER", "");
                if (team.Length > 0) project.SetBuildProperty(target, "DEVELOPMENT_TEAM", team);
            }
            project.SetBuildProperty(app, "CODE_SIGN_IDENTITY", "Apple Development");
            project.WriteToFile(path);
            if (team.Length == 0) Debug.LogWarning("[Signing] The Xcode project has no team yet: set AppleSigning.TeamId.");
#endif
        }
    }
}
