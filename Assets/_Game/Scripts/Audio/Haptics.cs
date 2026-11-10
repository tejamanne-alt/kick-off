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
    /// amplitude before that (pulses closer than 35 ms are thinned out there: see MinPulseGap).
    /// No-op in the editor and when disabled in Settings.
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
        // android.os.VibrationEffect (API 26+), looked up once: a JNI class lookup on every pulse cost a kick or a
        // landing a little main-thread time each.
        static AndroidJavaClass effectClass;
        // The effects already made, kept for the app's life: a VibrationEffect is immutable, so the same one can be
        // played again, and there are only a handful (one per predefined effect, one per duration and amplitude used).
        static readonly System.Collections.Generic.Dictionary<int, AndroidJavaObject> predefined =
            new System.Collections.Generic.Dictionary<int, AndroidJavaObject>();
        static readonly System.Collections.Generic.Dictionary<int, AndroidJavaObject> oneShots =
            new System.Collections.Generic.Dictionary<int, AndroidJavaObject>();

        // android.os.VibrationEffect predefined effects (API 29+).
        const int EffectClick = 0, EffectTick = 2, EffectHeavyClick = 5;

        // Pulses closer together than this can't be told apart, and each is a synchronous Binder call into the
        // system's vibrator service; a later pulse in the window is dropped unless it is stronger than the last one
        // played (a heavy bump right after a light tap still comes through, as it did when it cut the tap short).
        const float MinPulseGap = 0.035f;
        static float lastPulseTime = -1f;
        static int lastPulseAmplitude;

        /// <summary>True when a pulse of this strength should be dropped (see <see cref="MinPulseGap"/>); else records it.</summary>
        static bool TooSoon(int amplitude)
        {
            float now = Time.unscaledTime;
            if (now - lastPulseTime < MinPulseGap && amplitude <= lastPulseAmplitude) return true;
            lastPulseTime = now;
            lastPulseAmplitude = amplitude;
            return false;
        }

        /// <summary>A system click effect where available (crisper than a timed buzz), else a short vibration.</summary>
        static void AndroidEffect(int effect, int fallbackMs, int fallbackAmplitude)
        {
            if (!EnsureVibrator() || TooSoon(fallbackAmplitude)) return;
            if (sdk < 29)
            {
                OneShot(fallbackMs, fallbackAmplitude);
                return;
            }
            try
            {
                AndroidJavaObject e;
                if (!predefined.TryGetValue(effect, out e))
                {
                    e = effectClass.CallStatic<AndroidJavaObject>("createPredefined", effect);
                    if (e != null) predefined[effect] = e;
                }
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
                if (effectClass == null && vibrator != null && sdk >= 26)
                    effectClass = new AndroidJavaClass("android.os.VibrationEffect");
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Haptics] " + e.Message);
            }
            return vibrator != null && (sdk < 26 || effectClass != null);
        }

        static void AndroidVibrate(int ms, int amplitude)
        {
            if (!EnsureVibrator() || TooSoon(amplitude)) return;
            OneShot(ms, amplitude);
        }

        /// <summary>A short vibration: with its amplitude on API 26+, a plain timed buzz before that.</summary>
        static void OneShot(int ms, int amplitude)
        {
            try
            {
                if (sdk >= 26)
                {
                    int key = ms * 256 + amplitude;   // amplitude is 1-255
                    AndroidJavaObject effect;
                    if (!oneShots.TryGetValue(key, out effect))
                    {
                        effect = effectClass.CallStatic<AndroidJavaObject>("createOneShot", (long)ms, amplitude);
                        if (effect != null) oneShots[key] = effect;
                    }
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
