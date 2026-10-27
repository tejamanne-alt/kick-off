using DribbleToSchool.Core;
using UnityEngine;
#if UNITY_IOS && !UNITY_EDITOR
using System.Runtime.InteropServices;
#endif

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Light taps for kicks, perfect touches and landings. iOS uses the Taptic
    /// Engine (Plugins/iOS/DTSHaptics.mm); Android uses short vibrations with
    /// amplitude on API 26+. No-op in the editor and when disabled in Settings.
    /// </summary>
    public static class Haptics
    {
        public enum Strength { Light, Medium, Heavy }

#if UNITY_ANDROID && !UNITY_EDITOR
        // Referencing Handheld.Vibrate makes Unity add the VIBRATE permission on Android.
#pragma warning disable 0649
        static bool forcePermission;
#pragma warning restore 0649
#endif

        public static void Impact(Strength strength)
        {
            if (!GameSettings.HapticsEnabled) return;
#if UNITY_ANDROID && !UNITY_EDITOR
            if (forcePermission) Handheld.Vibrate();
#endif
#if UNITY_IOS && !UNITY_EDITOR
            DTS_HapticImpact((int)strength);
#elif UNITY_ANDROID && !UNITY_EDITOR
            int ms = strength == Strength.Light ? 12 : strength == Strength.Medium ? 22 : 40;
            int amplitude = strength == Strength.Light ? 60 : strength == Strength.Medium ? 140 : 255;
            AndroidVibrate(ms, amplitude);
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
        [DllImport("__Internal")] static extern void DTS_HapticSuccess();
        [DllImport("__Internal")] static extern void DTS_HapticSelection();
#endif

#if UNITY_ANDROID && !UNITY_EDITOR
        static AndroidJavaObject vibrator;
        static int sdk = -1;

        static void AndroidVibrate(int ms, int amplitude)
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
                if (vibrator == null) return;
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
