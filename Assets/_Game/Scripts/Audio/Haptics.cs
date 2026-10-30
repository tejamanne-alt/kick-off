using DribbleToSchool.Core;
using UnityEngine;
#if UNITY_IOS && !UNITY_EDITOR
using System.Runtime.InteropServices;
#endif

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Light taps for kicks, perfect touches and landings, and a crisp click when a
    /// button goes down. iOS uses the Taptic Engine (Plugins/iOS/DTSHaptics.mm);
    /// Android uses the system click effects on API 29+ and short vibrations with
    /// amplitude before that. No-op in the editor and when disabled in Settings.
    /// </summary>
    public static class Haptics
    {
        /// <summary>Soft is a dull, cushioned tap; Rigid a short, hard click (iOS 13+, else Light).</summary>
        public enum Strength { Light, Medium, Heavy, Soft, Rigid }

        /// <summary>A button going down: a crisp click, firmer for the main actions.</summary>
        public static void Press(bool primary)
        {
            if (!GameSettings.HapticsEnabled) return;
#if UNITY_IOS && !UNITY_EDITOR
            DTS_HapticImpactIntensity((int)Strength.Rigid, primary ? 1f : 0.7f);
#elif UNITY_ANDROID && !UNITY_EDITOR
            AndroidEffect(primary ? EffectClick : EffectTick, primary ? 14 : 8, primary ? 150 : 80);
#endif
        }

        /// <summary>A button coming back up: a faint, soft tap.</summary>
        public static void Release()
        {
            if (!GameSettings.HapticsEnabled) return;
#if UNITY_IOS && !UNITY_EDITOR
            DTS_HapticImpactIntensity((int)Strength.Soft, 0.45f);
#elif UNITY_ANDROID && !UNITY_EDITOR
            AndroidEffect(EffectTick, 5, 35);
#endif
        }

        public static void Impact(Strength strength)
        {
            if (!GameSettings.HapticsEnabled) return;
#if UNITY_IOS && !UNITY_EDITOR
            DTS_HapticImpact((int)strength);
#elif UNITY_ANDROID && !UNITY_EDITOR
            switch (strength)
            {
                case Strength.Medium: AndroidVibrate(22, 140); break;
                case Strength.Heavy: AndroidEffect(EffectHeavyClick, 40, 255); break;
                case Strength.Soft: AndroidVibrate(10, 50); break;
                case Strength.Rigid: AndroidEffect(EffectClick, 12, 150); break;
                default: AndroidVibrate(12, 60); break;
            }
#endif
        }

        public static void Success()
        {
            if (!GameSettings.HapticsEnabled) return;
#if UNITY_IOS && !UNITY_EDITOR
            DTS_HapticSuccess();
#elif UNITY_ANDROID && !UNITY_EDITOR
            AndroidVibrate(30, 180);
#endif
        }

        public static void Selection()
        {
            if (!GameSettings.HapticsEnabled) return;
#if UNITY_IOS && !UNITY_EDITOR
            DTS_HapticSelection();
#elif UNITY_ANDROID && !UNITY_EDITOR
            AndroidVibrate(8, 40);
#endif
        }

#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")] static extern void DTS_HapticImpact(int style);
        [DllImport("__Internal")] static extern void DTS_HapticImpactIntensity(int style, float intensity);
        [DllImport("__Internal")] static extern void DTS_HapticSuccess();
        [DllImport("__Internal")] static extern void DTS_HapticSelection();
#endif

#if UNITY_ANDROID && !UNITY_EDITOR
        static AndroidJavaObject vibrator;
        static int sdk = -1;

        // android.os.VibrationEffect predefined effects (API 29+).
        const int EffectClick = 0, EffectTick = 2, EffectHeavyClick = 5;

        /// <summary>A system click effect where available (crisper than a timed buzz), else a short vibration.</summary>
        static void AndroidEffect(int effect, int fallbackMs, int fallbackAmplitude)
        {
            if (!EnsureVibrator()) return;
            if (sdk < 29)
            {
                AndroidVibrate(fallbackMs, fallbackAmplitude);
                return;
            }
            try
            {
                using (var effectClass = new AndroidJavaClass("android.os.VibrationEffect"))
                using (var e = effectClass.CallStatic<AndroidJavaObject>("createPredefined", effect))
                    vibrator.Call("vibrate", e);
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning("[Haptics] " + ex.Message);
            }
        }

        static bool EnsureVibrator()
        {
            try
            {
                if (vibrator == null)
                {
                    using (var player = new AndroidJavaClass("com.unity3d.player.UnityPlayer"))
                    using (var activity = player.GetStatic<AndroidJavaObject>("currentActivity"))
                        vibrator = activity.Call<AndroidJavaObject>("getSystemService", "vibrator");
                    using (var version = new AndroidJavaClass("android.os.Build$VERSION"))
                        sdk = version.GetStatic<int>("SDK_INT");
                }
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Haptics] " + e.Message);
            }
            return vibrator != null;
        }

        static void AndroidVibrate(int ms, int amplitude)
        {
            if (!EnsureVibrator()) return;
            try
            {
                if (sdk >= 26)
                {
                    using (var effectClass = new AndroidJavaClass("android.os.VibrationEffect"))
                    using (var effect = effectClass.CallStatic<AndroidJavaObject>("createOneShot", (long)ms, amplitude))
                        vibrator.Call("vibrate", effect);
                }
                else
                {
                    vibrator.Call("vibrate", (long)ms);
                }
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Haptics] " + e.Message);
            }
        }
#endif
    }
}
