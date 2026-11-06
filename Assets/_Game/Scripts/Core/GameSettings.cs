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

        /// <summary>The sounds of the place (traffic, waves, gulls, diggers...), under the music.</summary>
        /// <summary>The Ambience slider's default: halfway, the place's sounds a backdrop under the music.</summary>
        public const float DefaultAmbienceVolume = 0.5f;

        public static float AmbienceVolume
        {
            get { return PlayerPrefs.GetFloat("settings.ambience", DefaultAmbienceVolume); }
            set { PlayerPrefs.SetFloat("settings.ambience", Mathf.Clamp01(value)); Save(); }
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

        /// <summary>Mirror the touch layout: kick and jump on the left, the walk stick on the right.</summary>
        public static bool LeftHanded
        {
            get { return GetBool("settings.leftHanded", false); }
            set { SetBool("settings.leftHanded", value); }
        }

        /// <summary>The coach's how-tos at the top of the screen in a level (UI/ActionCoach); the first-time tips show either way.</summary>
        public static bool CoachTips
        {
            get { return GetBool("settings.coachTips", true); }
            set { SetBool("settings.coachTips", value); }
        }

        /// <summary>High-contrast trajectory colours (blue/orange instead of white/red).</summary>
        public static bool ColorblindAim
        {
            get { return GetBool("settings.colorblindAim", false); }
            set { SetBool("settings.colorblindAim", value); }
        }

        /// <summary>Who walks to school: the id of one of the <see cref="PlayerRoster"/>'s kids ("boy", "girl", "primaryBoy"...).</summary>
        public static string Character
        {
            get { return PlayerRoster.Normalize(PlayerPrefs.GetString("settings.character", PlayerRoster.DefaultId)); }
            set { PlayerPrefs.SetString("settings.character", PlayerRoster.Normalize(value)); Save(); }
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
