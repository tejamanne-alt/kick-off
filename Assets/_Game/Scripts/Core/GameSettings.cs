using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Player preferences that outlive a level, stored in PlayerPrefs.
    /// The Settings screen edits these; systems read them live.
    /// </summary>
    public static class GameSettings
    {
        public static event System.Action Changed;

        /// <summary>Off = cozy mode: no school bell, no pressure.</summary>
        public static bool BellTimerEnabled
        {
            get { return GetBool("settings.bellTimer", true); }
            set { SetBool("settings.bellTimer", value); }
        }

        public static float MusicVolume
        {
            get { return PlayerPrefs.GetFloat("settings.music", 0.7f); }
            set { PlayerPrefs.SetFloat("settings.music", Mathf.Clamp01(value)); Save(); }
        }

        public static float SfxVolume
        {
            get { return PlayerPrefs.GetFloat("settings.sfx", 0.9f); }
            set { PlayerPrefs.SetFloat("settings.sfx", Mathf.Clamp01(value)); Save(); }
        }

        public static bool HapticsEnabled
        {
            get { return GetBool("settings.haptics", true); }
            set { SetBool("settings.haptics", value); }
        }

        public static bool ScreenShakeEnabled
        {
            get { return GetBool("settings.shake", true); }
            set { SetBool("settings.shake", value); }
        }

        /// <summary>Mirror the touch layout: kick and jump on the left, walk arrows on the right.</summary>
        public static bool LeftHanded
        {
            get { return GetBool("settings.leftHanded", false); }
            set { SetBool("settings.leftHanded", value); }
        }

        /// <summary>High-contrast trajectory colours (blue/orange instead of white/red).</summary>
        public static bool ColorblindAim
        {
            get { return GetBool("settings.colorblindAim", false); }
            set { SetBool("settings.colorblindAim", value); }
        }

        /// <summary>Who walks to school: "boy" or "girl".</summary>
        public static string Character
        {
            get { return PlayerPrefs.GetString("settings.character", "boy") == "girl" ? "girl" : "boy"; }
            set { PlayerPrefs.SetString("settings.character", value == "girl" ? "girl" : "boy"); Save(); }
        }

        public static string Language
        {
            get { return PlayerPrefs.GetString("settings.language", ""); }
            set { PlayerPrefs.SetString("settings.language", value); Save(); }
        }

        static bool GetBool(string key, bool fallback)
        {
            return PlayerPrefs.GetInt(key, fallback ? 1 : 0) == 1;
        }

        static void SetBool(string key, bool value)
        {
            PlayerPrefs.SetInt(key, value ? 1 : 0);
            Save();
        }

        static void Save()
        {
            PlayerPrefs.Save();
            if (Changed != null) Changed();
        }
    }
}
