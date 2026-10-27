using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Player preferences that outlive a level. Phase 7 adds the full settings
    /// screen; for now the pause menu exposes the bell timer toggle.
    /// </summary>
    public static class GameSettings
    {
        const string BellTimerKey = "settings.bellTimer";

        /// <summary>Off = cozy mode: no school bell, no pressure.</summary>
        public static bool BellTimerEnabled
        {
            get { return PlayerPrefs.GetInt(BellTimerKey, 1) == 1; }
            set
            {
                PlayerPrefs.SetInt(BellTimerKey, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }
    }
}
