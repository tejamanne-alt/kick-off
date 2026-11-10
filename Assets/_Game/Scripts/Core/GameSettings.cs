using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Player preferences that outlive a level, stored in PlayerPrefs.
    /// The Settings screen edits these; systems read them live.
    ///
    /// Each value is read from PlayerPrefs once and then kept here: several are read every frame (the music and ambience
    /// volumes, the chosen kid on the menu, the coach's tips in a level), and on Android every PlayerPrefs read is a call
    /// through JNI into Java. A setter writes PlayerPrefs and forgets the kept value, so the next read is exactly what
    /// PlayerPrefs stores. Nothing else writes these keys (Reset progress wipes save.json, not the settings); anything
    /// that ever does must go through these properties, or the kept values go stale.
    /// </summary>
    public static class GameSettings
    {
        public static event System.Action Changed;

        // The values as last read from PlayerPrefs (null: not read yet, or set since).
        static bool? bellTimer, haptics, shake, leftHanded, coachTips, colorblindAim;
        static float? music, ambience, sfx;
        static int? bagColour;
        static string character, language;

        /// <summary>Off = cozy mode: no school bell, no pressure.</summary>
        public static bool BellTimerEnabled
        {
            get { return GetBool(ref bellTimer, "settings.bellTimer", true); }
            set { SetBool(ref bellTimer, "settings.bellTimer", value); }
        }

        public static float MusicVolume
        {
            get { return GetFloat(ref music, "settings.music", 0.7f); }
            set { PlayerPrefs.SetFloat("settings.music", Mathf.Clamp01(value)); music = null; Save(); }
        }

        /// <summary>The sounds of the place (traffic, waves, gulls, diggers...), under the music.</summary>
        /// <summary>The Ambience slider's default: halfway, the place's sounds a backdrop under the music.</summary>
        public const float DefaultAmbienceVolume = 0.5f;

        public static float AmbienceVolume
        {
            get { return GetFloat(ref ambience, "settings.ambience", DefaultAmbienceVolume); }
            set { PlayerPrefs.SetFloat("settings.ambience", Mathf.Clamp01(value)); ambience = null; Save(); }
        }

        public static float SfxVolume
        {
            get { return GetFloat(ref sfx, "settings.sfx", 0.9f); }
            set { PlayerPrefs.SetFloat("settings.sfx", Mathf.Clamp01(value)); sfx = null; Save(); }
        }

        public static bool HapticsEnabled
        {
            get { return GetBool(ref haptics, "settings.haptics", true); }
            set { SetBool(ref haptics, "settings.haptics", value); }
        }

        public static bool ScreenShakeEnabled
        {
            get { return GetBool(ref shake, "settings.shake", true); }
            set { SetBool(ref shake, "settings.shake", value); }
        }

        /// <summary>Mirror the touch layout: kick and jump on the left, the walk stick on the right.</summary>
        public static bool LeftHanded
        {
            get { return GetBool(ref leftHanded, "settings.leftHanded", false); }
            set { SetBool(ref leftHanded, "settings.leftHanded", value); }
        }

        /// <summary>The coach's how-tos at the top of the screen in a level (UI/ActionCoach); the first-time tips show either way.</summary>
        public static bool CoachTips
        {
            get { return GetBool(ref coachTips, "settings.coachTips", true); }
            set { SetBool(ref coachTips, "settings.coachTips", value); }
        }

        /// <summary>High-contrast trajectory colours (blue/orange instead of white/red).</summary>
        public static bool ColorblindAim
        {
            get { return GetBool(ref colorblindAim, "settings.colorblindAim", false); }
            set { SetBool(ref colorblindAim, "settings.colorblindAim", value); }
        }

        /// <summary>Who walks to school: the id of one of the <see cref="PlayerRoster"/>'s kids ("girl", "backpackBoy", "primaryBoy"...).</summary>
        public static string Character
        {
            get
            {
                // The stored id is kept as stored, and checked against the roster on every read, as before.
                if (character == null) character = PlayerPrefs.GetString("settings.character", PlayerRoster.DefaultId);
                return PlayerRoster.Normalize(character);
            }
            set { PlayerPrefs.SetString("settings.character", PlayerRoster.Normalize(value)); character = null; Save(); }
        }

        /// <summary>The colour the kids' bags are worn in: an index into Cosmetics/Bags.Colours (0, the bag's own colours).</summary>
        public static int BagColour
        {
            get
            {
                if (!bagColour.HasValue) bagColour = PlayerPrefs.GetInt("settings.bagColour", 0);
                return bagColour.Value;
            }
            set { PlayerPrefs.SetInt("settings.bagColour", Mathf.Max(0, value)); bagColour = null; Save(); }
        }

        public static string Language
        {
            get
            {
                if (language == null) language = PlayerPrefs.GetString("settings.language", "");
                return language;
            }
            set { PlayerPrefs.SetString("settings.language", value); language = null; Save(); }
        }

        /// <summary>
        /// Forget the kept values, so the next reads go to PlayerPrefs. Unity runs it as each play session starts: in the
        /// editor with domain reload turned off (Enter Play Mode Options) the statics would otherwise carry over from the
        /// last session and miss a Clear All PlayerPrefs in between.
        /// </summary>
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Forget()
        {
            bellTimer = haptics = shake = leftHanded = coachTips = colorblindAim = null;
            music = ambience = sfx = null;
            bagColour = null;
            character = language = null;
        }

        static bool GetBool(ref bool? kept, string key, bool fallback)
        {
            if (!kept.HasValue) kept = PlayerPrefs.GetInt(key, fallback ? 1 : 0) == 1;
            return kept.Value;
        }

        static void SetBool(ref bool? kept, string key, bool value)
        {
            PlayerPrefs.SetInt(key, value ? 1 : 0);
            kept = null;
            Save();
        }

        static float GetFloat(ref float? kept, string key, float fallback)
        {
            if (!kept.HasValue) kept = PlayerPrefs.GetFloat(key, fallback);
            return kept.Value;
        }

        static void Save()
        {
            PlayerPrefs.Save();
            if (Changed != null) Changed();
        }
    }
}
