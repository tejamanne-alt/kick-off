using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Single place that changes time scale, keeping physics steps in sync so
    /// slow motion stays smooth.
    /// </summary>
    public static class TimeControl
    {
        public const float BaseFixedDeltaTime = 1f / 60f;

        public static void SetSlowMotion(float scale)
        {
            scale = Mathf.Clamp(scale, 0.05f, 1f);
            Time.timeScale = scale;
            Time.fixedDeltaTime = BaseFixedDeltaTime * scale;
        }

        public static void ResetTime()
        {
            SetSlowMotion(1f);
        }
    }
}
