using System.IO;
using UnityEditor.Android;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Adds the VIBRATE permission to the Android build's manifest, which the game's haptics
    /// (Audio/Haptics, through Android's own vibrator) need. Unity used to add it whenever the
    /// code referenced Handheld.Vibrate, from the vibration module that newer editors no longer have.
    /// </summary>
    public class AndroidVibratePermission : IPostGenerateGradleAndroidProject
    {
        const string Permission = "android.permission.VIBRATE";

        public int callbackOrder { get { return 0; } }

        public void OnPostGenerateGradleAndroidProject(string path)
        {
            string manifest = Path.Combine(path, "src", "main", "AndroidManifest.xml");
            if (!File.Exists(manifest)) return;
            string xml = File.ReadAllText(manifest);
            if (xml.Contains(Permission)) return;
            int manifestTag = xml.IndexOf("<manifest");
            int close = manifestTag >= 0 ? xml.IndexOf('>', manifestTag) : -1;
            if (close < 0) return;
            xml = xml.Insert(close + 1, "\n  <uses-permission android:name=\"" + Permission + "\" />");
            File.WriteAllText(manifest, xml);
        }
    }
}
