using System.IO;
using UnityEditor.Android;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Adds what the co-op mode's Bluetooth needs to the Android build's manifest (Plugins/Android/DtsCoopBle.java):
    /// on Android 12 and up the "nearby devices" permissions (scan, without deriving a location from it; connect;
    /// advertise, for hosting), and before that the old Bluetooth permissions and fine location, which scanning needed.
    /// Bluetooth LE is declared as a feature the game uses but doesn't require, so phones without it can still install
    /// and play everything but Co-op. The player is asked at run time, the first time the co-op screen opens.
    /// </summary>
    public class AndroidBluetoothPermissions : IPostGenerateGradleAndroidProject
    {
        static readonly string[] Lines =
        {
            "<uses-permission android:name=\"android.permission.BLUETOOTH\" android:maxSdkVersion=\"30\" />",
            "<uses-permission android:name=\"android.permission.BLUETOOTH_ADMIN\" android:maxSdkVersion=\"30\" />",
            "<uses-permission android:name=\"android.permission.ACCESS_FINE_LOCATION\" android:maxSdkVersion=\"30\" />",
            "<uses-permission android:name=\"android.permission.BLUETOOTH_SCAN\" android:usesPermissionFlags=\"neverForLocation\" />",
            "<uses-permission android:name=\"android.permission.BLUETOOTH_CONNECT\" />",
            "<uses-permission android:name=\"android.permission.BLUETOOTH_ADVERTISE\" />",
            "<uses-feature android:name=\"android.hardware.bluetooth_le\" android:required=\"false\" />",
        };

        public int callbackOrder { get { return 1; } }

        public void OnPostGenerateGradleAndroidProject(string path)
        {
            string manifest = Path.Combine(path, "src", "main", "AndroidManifest.xml");
            if (!File.Exists(manifest)) return;
            string xml = File.ReadAllText(manifest);
            int manifestTag = xml.IndexOf("<manifest");
            int close = manifestTag >= 0 ? xml.IndexOf('>', manifestTag) : -1;
            if (close < 0) return;
            string insert = "";
            foreach (string line in Lines)
            {
                // (by name, so a permission Unity or another plugin declared already isn't declared twice)
                int name = line.IndexOf("android:name=\"");
                string key = line.Substring(name, line.IndexOf('"', name + 14) - name + 1);
                if (!xml.Contains(key)) insert += "\n  " + line;
            }
            if (insert.Length == 0) return;
            xml = xml.Insert(close + 1, insert);
            File.WriteAllText(manifest, xml);
        }
    }
}
