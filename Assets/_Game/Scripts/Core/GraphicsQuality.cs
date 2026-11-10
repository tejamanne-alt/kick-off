using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Core
{
    /// <summary>How much the phone is asked to draw: Low, Medium or High (docs/PERFORMANCE.md).</summary>
    public enum GraphicsTier { Low = 0, Medium = 1, High = 2 }

    /// <summary>
    /// The game's graphics budget, chosen per device and corrected by what the device really manages.
    ///
    /// Before the first scene loads it pins the settings that are not in git (ProjectSettings is generated on each machine):
    /// vSync off so the frame-rate target and Android's frame pacing decide the cadence, a short physics catch-up after a
    /// hitch, reused collision callbacks, and texture uploads spread over frames. It then picks a tier: from the GPU and the
    /// memory the first time, from what the frame-rate governor (<see cref="FramePacer"/>) learnt in earlier sessions after
    /// that. Each tier sets
    /// - the 3D picture's resolution on Android (<see cref="TargetLines"/>: 720, 864 or 1080 lines, never above the panel;
    ///   the panel's own scaler stretches it for free, and the UI is laid out by its CanvasScaler as before);
    /// - the sun's shadows (<see cref="ApplyShadows"/>): soft, two cascades and 35 m on High; hard, one cascade and 25 m on
    ///   Medium; none on Low, where the contact and blob shadows still ground everyone;
    /// - the bloom (<see cref="Bloom"/>: High only; at 0.12 over the brightest highlights it is barely seen and costs a
    ///   chain of passes);
    /// - and the frame rate the governor starts from (60).
    /// Every camera that draws the 3D world renders without HDR and without MSAA (<see cref="ConfigureCamera"/>): the grade
    /// works in 0..1 anyway, and an FP16 target doubles every pass's memory traffic on a phone.
    ///
    /// The governor watches the frame time; when 60 is out of reach for several seconds it steps the tier down (shadows and
    /// bloom at once, the resolution at the next scene load) and, at Low, the frame rate down to an even divisor of the
    /// panel (40 on a 120 Hz panel, else 30). What it learns is kept, so the next session starts where this one settled; after
    /// a few sessions at a lowered tier it tries one step up again, so a hot afternoon does not lower the game for good.
    /// </summary>
    public static class GraphicsQuality
    {
        const string TierKey = "graphics.autoTier";
        const string TierBootsKey = "graphics.autoTierBoots";
        const string FpsKey = "graphics.autoFps";
        const int RetryUpAfterBoots = 5;

        /// <summary>The tier in use.</summary>
        public static GraphicsTier Tier { get; private set; } = GraphicsTier.High;

        /// <summary>The tier the device was given before any correction (from its GPU and memory).</summary>
        public static GraphicsTier DeviceTier { get; private set; } = GraphicsTier.High;

        /// <summary>The frame rate asked for (60, or 40 / 30 once the governor has stepped down at Low).</summary>
        public static int TargetFrameRate { get; private set; } = 60;

        /// <summary>Raised when the tier or the frame rate changes (WorldLook re-applies its shadows, PostFX its bloom).</summary>
        public static event System.Action Changed;

        /// <summary>The 3D picture's height, in lines, for each tier (Android); never more than the panel has.</summary>
        public static int TargetLines(GraphicsTier tier)
        {
            switch (tier)
            {
                case GraphicsTier.Low: return 720;
                case GraphicsTier.Medium: return 864;
                default: return 1080;
            }
        }

        /// <summary>The bloom on the brightest highlights: High only.</summary>
        public static bool Bloom { get { return Tier == GraphicsTier.High; } }

        /// <summary>
        /// The ratio of the picture's resolution to the panel's (1 when nothing was scaled). Touch distances measured in pixels
        /// scale by it: <see cref="TouchDpi"/>.
        /// </summary>
        public static float RenderScale { get; private set; } = 1f;

        /// <summary>Screen.dpi in the picture's pixels: the panel's dots per inch times <see cref="RenderScale"/>.</summary>
        public static float TouchDpi
        {
            get
            {
                float dpi = Screen.dpi > 0f ? Screen.dpi : 160f;
                return dpi * Mathf.Clamp(RenderScale, 0.3f, 1f);
            }
        }

        static bool booted;
        static int nativeShort, nativeLong;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Boot()
        {
            if (booted) return;
            booted = true;

            QualitySettings.vSyncCount = 0;                // the target frame rate and Android's frame pacing decide the cadence
            Time.maximumDeltaTime = 0.1f;                  // after a hitch, at most six catch-up physics steps, not twenty
            Physics2D.reuseCollisionCallbacks = true;      // no new Collision2D per bounce
            QualitySettings.asyncUploadTimeSlice = 4;      // ms a frame for streaming textures and meshes to the GPU
            QualitySettings.asyncUploadBufferSize = 16;    // MB, kept for the session: the largest texture (the coast atlas, ~10 MB) fits, and Unity grows it for a bigger one
            QualitySettings.asyncUploadPersistentBuffer = true;

            nativeShort = Mathf.Min(Screen.width, Screen.height);
            nativeLong = Mathf.Max(Screen.width, Screen.height);
#if UNITY_ANDROID && !UNITY_EDITOR
            // The panel's own size: the window may already have been scaled by an earlier session's choice.
            if (Display.main != null && Display.main.systemWidth > 0 && Display.main.systemHeight > 0)
            {
                nativeShort = Mathf.Min(Display.main.systemWidth, Display.main.systemHeight);
                nativeLong = Mathf.Max(Display.main.systemWidth, Display.main.systemHeight);
            }
#endif

            DeviceTier = DetectTier();
            Tier = DeviceTier;
            if (PlayerPrefs.HasKey(TierKey))
            {
                var learnt = (GraphicsTier)Mathf.Clamp(PlayerPrefs.GetInt(TierKey), 0, 2);
                if (learnt < DeviceTier)
                {
                    int boots = PlayerPrefs.GetInt(TierBootsKey, 0) + 1;
                    if (boots >= RetryUpAfterBoots)
                    {
                        // try one step up again; the governor steps back down if it still can't keep up
                        learnt = (GraphicsTier)Mathf.Min((int)learnt + 1, (int)DeviceTier);
                        boots = 0;
                        PlayerPrefs.SetInt(TierKey, (int)learnt);
                        PlayerPrefs.DeleteKey(FpsKey);
                    }
                    PlayerPrefs.SetInt(TierBootsKey, boots);
                }
                Tier = learnt < DeviceTier ? learnt : DeviceTier;
            }
            TargetFrameRate = Tier == GraphicsTier.Low ? Mathf.Clamp(PlayerPrefs.GetInt(FpsKey, 60), 30, 60) : 60;

            ApplyResolution();
            ApplyFrameRate();
            ApplyShadows(null, 35f);
            // A new resolution recreates the window's surface (a hitch, maybe a black frame): only as a whole scene
            // loads, never as the Holiday Run streams its next stage in (an additive load in the middle of a run).
            SceneManager.sceneLoaded += (scene, mode) =>
            {
                if (mode == LoadSceneMode.Single) ApplyResolution();
                ApplyFrameRate();
            };
            Debug.Log("[Graphics] " + SystemInfo.graphicsDeviceName + ", " + SystemInfo.systemMemorySize + " MB: device tier " + DeviceTier +
                ", tier " + Tier + ", " + TargetFrameRate + " fps, " + Screen.width + "x" + Screen.height);
        }

        /// <summary>
        /// The device's tier from its GPU and memory. High: recent flagship GPUs (Adreno 7xx/8xx, Mali G710 and later,
        /// Immortalis, Xclipse, Apple) with 6 GB or more; Low: under 4 GB, under six cores, or older GPUs (Adreno 5xx, 60x and
        /// 61x, Mali T and G5x, the first Mali-G71/G72, the one- to four-core Mali G6x/G7x, PowerVR); Medium otherwise (most
        /// mid-range phones, the Nord CE5's Mali-G615 MC6 among them). A wrong guess upward is corrected by the governor.
        /// </summary>
        static GraphicsTier DetectTier()
        {
#if UNITY_EDITOR || UNITY_STANDALONE || UNITY_IOS
            return GraphicsTier.High;
#else
            string gpu = (SystemInfo.graphicsDeviceName ?? "").ToLowerInvariant();
            int memory = SystemInfo.systemMemorySize;
            int cores = SystemInfo.processorCount;
            if (memory > 0 && memory < 3800) return GraphicsTier.Low;
            if (cores > 0 && cores < 6) return GraphicsTier.Low;
            if (gpu.Contains("powervr") || gpu.Contains("adreno (tm) 5") || gpu.Contains("adreno (tm) 60") || gpu.Contains("adreno (tm) 61")
                || gpu.Contains("mali-g5") || gpu.Contains("mali-t") || gpu.Contains("mali-g71 ") || gpu.Contains("mali-g72 ")
                || ((gpu.Contains("mali-g6") || gpu.Contains("mali-g7")) && (gpu.Contains("mc1") || gpu.Contains("mc2") || gpu.Contains("mc3") || gpu.Contains("mc4"))))
                return GraphicsTier.Low;
            // (Mali-G710 and later, not the 2016-17 Mali-G71 and G72 whose names they start with)
            bool flagship = gpu.Contains("adreno (tm) 7") || gpu.Contains("adreno (tm) 8") || gpu.Contains("immortalis")
                || gpu.Contains("mali-g710") || gpu.Contains("mali-g715") || gpu.Contains("mali-g720") || gpu.Contains("mali-g725")
                || gpu.Contains("mali-g9") || gpu.Contains("xclipse") || gpu.Contains("apple");
            if (flagship && memory >= 5800) return GraphicsTier.High;
            return GraphicsTier.Medium;
#endif
        }

        /// <summary>Android: the 3D picture at the tier's lines (the panel scales it up). Elsewhere nothing changes.</summary>
        static void ApplyResolution()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            if (nativeShort <= 0 || nativeLong <= 0) return;
            int lines = Mathf.Min(TargetLines(Tier), nativeShort);
            float scale = lines / (float)nativeShort;
            int width = Mathf.RoundToInt(nativeLong * scale), height = lines;
            // landscape only: the long side across
            if (Mathf.Abs(Mathf.Max(Screen.width, Screen.height) - width) > 2 || Mathf.Abs(Mathf.Min(Screen.width, Screen.height) - height) > 2)
                Screen.SetResolution(width, height, FullScreenMode.FullScreenWindow);
            RenderScale = scale;
#else
            RenderScale = 1f;
#endif
        }

        /// <summary>The frame-rate target (the levels and the menus call it as they start).</summary>
        public static void ApplyFrameRate()
        {
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = TargetFrameRate;
        }

        /// <summary>Every camera that draws the 3D world: no HDR target, no MSAA (the grade works in 0..1; see the summary).</summary>
        public static void ConfigureCamera(Camera cam)
        {
            if (cam == null) return;
            cam.allowHDR = false;
            cam.allowMSAA = false;
        }

        /// <summary>
        /// The sun's shadows for the tier: soft, high resolution, two cascades out to <paramref name="highDistance"/> on High;
        /// hard, medium resolution, one cascade to 25 m on Medium; none on Low. The light may be null (quality settings only).
        /// </summary>
        public static void ApplyShadows(Light sun, float highDistance)
        {
            switch (Tier)
            {
                case GraphicsTier.High:
                    QualitySettings.shadows = ShadowQuality.All;
                    QualitySettings.shadowResolution = ShadowResolution.High;
                    QualitySettings.shadowDistance = highDistance;
                    QualitySettings.shadowCascades = 2;
                    if (sun != null) { sun.shadows = LightShadows.Soft; sun.shadowResolution = UnityEngine.Rendering.LightShadowResolution.High; }
                    break;
                case GraphicsTier.Medium:
                    QualitySettings.shadows = ShadowQuality.HardOnly;
                    QualitySettings.shadowResolution = ShadowResolution.Medium;
                    QualitySettings.shadowDistance = Mathf.Min(highDistance, 25f);
                    QualitySettings.shadowCascades = 1;
                    if (sun != null) { sun.shadows = LightShadows.Hard; sun.shadowResolution = UnityEngine.Rendering.LightShadowResolution.Medium; }
                    break;
                default:
                    QualitySettings.shadows = ShadowQuality.Disable;
                    QualitySettings.shadowCascades = 1;
                    if (sun != null) sun.shadows = LightShadows.None;
                    break;
            }
            QualitySettings.shadowProjection = ShadowProjection.StableFit;
        }

        /// <summary>
        /// The governor's step down: one tier (its shadows and bloom at once, its resolution at the next scene load), or at
        /// Low the frame rate to the panel's next even divisor. Remembered for the next session. Returns false when there is
        /// nothing left to lower.
        /// </summary>
        public static bool StepDown()
        {
            if (Tier > GraphicsTier.Low)
            {
                Tier = (GraphicsTier)((int)Tier - 1);
                PlayerPrefs.SetInt(TierKey, (int)Tier);
                PlayerPrefs.SetInt(TierBootsKey, 0);
                PlayerPrefs.Save();
                ApplyShadows(null, 35f);
                Debug.Log("[Graphics] stepped down to " + Tier);
                if (Changed != null) Changed();
                return true;
            }
            int lower = LowerFrameRate(TargetFrameRate);
            if (lower >= TargetFrameRate) return false;
            TargetFrameRate = lower;
            PlayerPrefs.SetInt(FpsKey, lower);
            PlayerPrefs.Save();
            ApplyFrameRate();
            Debug.Log("[Graphics] frame rate down to " + lower);
            if (Changed != null) Changed();
            return true;
        }

        /// <summary>The next lower frame rate that is an even share of the panel's refresh (120 Hz: 40 then 30; 90 Hz: 45 then 30; 60 Hz: 30).</summary>
        static int LowerFrameRate(int from)
        {
            int hz = Mathf.RoundToInt((float)Screen.currentResolution.refreshRateRatio.value);
            if (hz <= 0) hz = 60;
            int best = from;
            for (int k = 1; k <= 8; k++)
            {
                int rate = Mathf.RoundToInt(hz / (float)k);
                if (rate < 30 || rate >= from) continue;
                if (best == from || rate > best) best = rate;
            }
            return best == from && from > 30 ? 30 : best;
        }
    }

    /// <summary>
    /// The frame-rate governor (<see cref="GraphicsQuality"/>): every two seconds it counts the frames that came late for the
    /// target (over 1.3 frame times; with frame pacing a missed 60 shows as 25 or 33 ms). When over a fifth of the frames are
    /// late in three windows running, it steps the quality down one notch. It ignores the first seconds after a scene loads
    /// (the music and ambience are made then, and shaders compile), paused time and the app in the background.
    /// </summary>
    public sealed class FramePacer : MonoBehaviour
    {
        const float Window = 2f;
        const float SettleAfterLoad = 6f;
        const float LateFactor = 1.3f;
        const float LateShare = 0.2f;
        const int BadWindows = 3;

        int frames, late, bad;
        float windowEnd, quietUntil;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Create()
        {
            var go = new GameObject("FramePacer");
            DontDestroyOnLoad(go);
            go.hideFlags = HideFlags.HideInHierarchy;
            go.AddComponent<FramePacer>();
        }

        void OnEnable()
        {
            SceneManager.sceneLoaded += OnSceneLoaded;
            Settle();
        }

        void OnDisable() { SceneManager.sceneLoaded -= OnSceneLoaded; }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode) { Settle(); }

        void OnApplicationPause(bool paused) { if (!paused) Settle(); }

        void Settle()
        {
            quietUntil = Time.unscaledTime + SettleAfterLoad;
            frames = late = bad = 0;
            windowEnd = quietUntil + Window;
        }

        void Update()
        {
            float now = Time.unscaledTime;
            if (now < quietUntil) return;
            float budget = 1f / Mathf.Max(GraphicsQuality.TargetFrameRate, 1);
            frames++;
            if (Time.unscaledDeltaTime > budget * LateFactor) late++;
            if (now < windowEnd) return;
            bool slow = frames > 10 && late > frames * LateShare;
            frames = late = 0;
            windowEnd = now + Window;
            bad = slow ? bad + 1 : 0;
            if (bad < BadWindows) return;
            bad = 0;
            if (GraphicsQuality.StepDown()) Settle();
        }
    }
}
