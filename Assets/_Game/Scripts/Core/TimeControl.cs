using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Single place that changes time scale, keeping physics steps in sync so
    /// slow motion stays smooth. Pause wins over slow motion and restores it after.
    /// </summary>
    public static class TimeControl
    {
        public const float BaseFixedDeltaTime = 1f / 60f;

        static float slowMotion = 1f;

        public static bool IsPaused { get; private set; }

        public static void SetSlowMotion(float scale)
        {
            slowMotion = Mathf.Clamp(scale, 0.05f, 1f);
            Apply();
        }

        public static void SetPaused(bool paused)
        {
            IsPaused = paused;
            Apply();
        }

        /// <summary>Back to normal speed and unpaused.</summary>
        public static void ResetTime()
        {
            IsPaused = false;
            slowMotion = 1f;
            Apply();
        }

        static void Apply()
        {
            Time.timeScale = IsPaused ? 0f : slowMotion;
            Time.fixedDeltaTime = BaseFixedDeltaTime * slowMotion;
        }
    }
}
