using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The comic filter's sound-effect words: while the comic halftone filter is on (Add-ons &amp; Filters on the
    /// title screen), the big moments pop up as comic lettering by where they happen: THWACK! on a hard kick,
    /// NICE TOUCH! on a perfect touch, BOINK! on a juggle (and "10 IN A ROW!" every fifth), WHOOSH! on a
    /// double jump, SKRRT! on a slide, BOING! on a springboard, SPLASH!, SQUAWK! (a gull), WOOF! (a dog),
    /// OOF! (a passer-by), CLICK! (a gate's button), WHOOPS! when the ball is lost, and MADE IT! (GOAL! in
    /// a challenge) at the end. The biggest come with an ink starburst behind them.
    ///
    /// Booted once and kept across scenes; it listens to GameEvents, so it works in the story levels, the
    /// challenges and the Holiday Run alike. Its own overlay canvas sits just under the HUD (the controls
    /// and cards stay on top), takes no touches and never covers the info card or the controls: a word is
    /// kept inside the middle of the screen. Few at once: a quieter word gives way to a louder one that
    /// has just popped, the same word doesn't repeat back to back, and at most three show together.
    /// The words are in the string tables (pop.*); the lettering is UI/ComicLettering on Bangers
    /// (UITheme.Comic) with Resources/Shaders/ComicLettering's halftone.
    /// </summary>
    public class ComicPops : MonoBehaviour
    {
        enum Style { Hot, Cool, Ouch }
        enum Size { Small, Medium, Big, Huge }

        sealed class Pop
        {
            public RectTransform rect, burst;
            public CanvasGroup group;
            public float born, life, spin;
            public int priority;
            public string word;
        }

        static ComicPops instance;
        RectTransform root;
        readonly List<Pop> live = new List<Pop>();
        Material[] materials;
        Sprite burstSprite;
        BallController ball;
        string lastWord;
        float lastWordAt = -10f;

        const int MaxLive = 3;

        /// <summary>The words show: the comic filter is chosen.</summary>
        public static bool On { get { return AddOns.Filter == AddOns.ComicFilter; } }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (instance != null) return;
            var go = new GameObject("ComicPops");
            DontDestroyOnLoad(go);
            instance = go.AddComponent<ComicPops>();
        }

        // The starburst is drawn now, at boot, not on the first THWACK! (a frame's work on a phone).
        void Start() { BurstSprite(); }

        void OnEnable()
        {
            GameEvents.Raised += OnEvent;
            SceneManager.sceneLoaded += OnSceneLoaded;
        }

        void OnDisable()
        {
            GameEvents.Raised -= OnEvent;
            SceneManager.sceneLoaded -= OnSceneLoaded;
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            ball = null;
            for (int i = live.Count - 1; i >= 0; i--) Remove(i);
        }

        BallController Ball()
        {
            if (ball == null) ball = FindAnyObjectByType<BallController>();
            return ball;
        }

        void OnEvent(GameEventType type, Vector2 world, float k)
        {
            if (!On) return;
            switch (type)
            {
                case GameEventType.Kick:
                    if (k >= 0.75f) Show(Loc.T("pop.thwack"), world, Style.Hot, Size.Big, 2, true);
                    else if (k >= 0.45f) Show(Loc.T("pop.thump"), world, Style.Hot, Size.Medium, 1, false);
                    break;
                case GameEventType.PerfectTouch:
                {
                    var b = Ball();
                    int streak = b != null ? b.PerfectStreak : 0;
                    Show(streak > 1 ? Loc.F("pop.niceN", streak) : Loc.T("pop.nice"), world, Style.Hot, Size.Medium, 2, false);
                    break;
                }
                case GameEventType.Juggle:
                {
                    var b = Ball();
                    int count = b != null ? b.JuggleCount : 0;
                    if (count > 0 && count % 5 == 0) Show(Loc.F("pop.boinkN", count), world, Style.Cool, Size.Big, 3, true);
                    else Show(Loc.T("pop.boink"), world, Style.Cool, Size.Small, 0, false);
                    break;
                }
                case GameEventType.DoubleJump: Show(Loc.T("pop.whoosh"), world, Style.Cool, Size.Small, 0, false); break;
                case GameEventType.Slide: Show(Loc.T("pop.skrrt"), world, Style.Hot, Size.Medium, 1, false); break;
                case GameEventType.Springboard: Show(Loc.T("pop.boing"), world, Style.Cool, Size.Medium, 1, false); break;
                case GameEventType.Splash: Show(Loc.T("pop.splash"), world, Style.Cool, Size.Medium, 1, false); break;
                case GameEventType.SeagullHit: Show(Loc.T("pop.squawk"), world, Style.Ouch, Size.Medium, 2, false); break;
                case GameEventType.DogSteal: Show(Loc.T("pop.woof"), world, Style.Ouch, Size.Medium, 2, false); break;
                case GameEventType.PedestrianBump: Show(Loc.T("pop.oof"), world, Style.Ouch, Size.Medium, 1, false); break;
                case GameEventType.SwitchPressed: Show(Loc.T("pop.click"), world, Style.Hot, Size.Small, 1, false); break;
                case GameEventType.BallLost: Show(Loc.T("pop.whoops"), world, Style.Ouch, Size.Big, 3, false); break;
                case GameEventType.Goal:
                {
                    var level = LevelManager.Current;
                    bool challenge = level != null && level.level != null && level.level.isChallenge;
                    Show(Loc.T(challenge ? "pop.goal" : "pop.madeIt"), world, Style.Hot, Size.Huge, 4, true, true);
                    break;
                }
            }
        }

        // ---------- A pop ----------

        void Show(string word, Vector2 world, Style style, Size size, int priority, bool withBurst, bool centred = false)
        {
            float now = Time.unscaledTime;
            // A quieter word gives way to a louder one that has only just popped; no word twice in a row.
            for (int i = 0; i < live.Count; i++)
                if (live[i].priority > priority && now - live[i].born < 0.45f) return;
            if (word == lastWord && now - lastWordAt < 0.6f) return;
            lastWord = word; lastWordAt = now;
            if (!EnsureCanvas()) return;
            while (live.Count >= MaxLive) Remove(0);

            float fontSize = size == Size.Huge ? 190f : size == Size.Big ? 140f : size == Size.Medium ? 104f : 78f;
            var go = new GameObject("Pop", typeof(RectTransform));
            var rect = (RectTransform)go.transform;
            rect.SetParent(root, false);
            rect.sizeDelta = new Vector2(10f, 10f);
            rect.anchoredPosition = centred ? new Vector2(0f, root.rect.height * 0.2f) : ScreenSpot(world, fontSize);
            float tilt = Random.Range(4f, 12f) * (Random.value < 0.75f ? 1f : -0.6f);
            rect.localRotation = Quaternion.Euler(0f, 0f, tilt);
            var group = go.AddComponent<CanvasGroup>();
            group.blocksRaycasts = false; group.interactable = false;

            RectTransform burst = null;
            if (withBurst)
            {
                var bgo = new GameObject("Burst", typeof(RectTransform));
                burst = (RectTransform)bgo.transform;
                burst.SetParent(rect, false);
                float r = fontSize * (word.Length > 6 ? 2.6f : 2.1f);
                burst.sizeDelta = new Vector2(r, r);
                burst.anchoredPosition = new Vector2(-fontSize * 0.15f, -fontSize * 0.05f);
                var img = bgo.AddComponent<Image>();
                img.sprite = BurstSprite();
                img.raycastTarget = false;
            }

            var tgo = new GameObject("Word", typeof(RectTransform));
            var trect = (RectTransform)tgo.transform;
            trect.SetParent(rect, false);
            trect.sizeDelta = new Vector2(1600f, fontSize * 1.6f);
            var text = tgo.AddComponent<Text>();
            text.font = UITheme.Comic;
            text.fontSize = Mathf.RoundToInt(fontSize);
            text.alignment = TextAnchor.MiddleCenter;
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            text.raycastTarget = false;
            text.color = Color.white;
            text.text = word;
            var mat = Material(style);
            if (mat != null) text.material = mat;
            var lettering = tgo.AddComponent<ComicLettering>();
            switch (style)
            {
                case Style.Cool:
                    lettering.top = new Color(1f, 0.99f, 0.93f); lettering.bottom = new Color(0.43f, 0.82f, 0.9f);
                    break;
                case Style.Ouch:
                    lettering.top = new Color(1f, 0.97f, 0.92f); lettering.bottom = new Color(0.96f, 0.45f, 0.6f);
                    break;
            }

            live.Add(new Pop
            {
                rect = rect, burst = burst, group = group, born = now, priority = priority, word = word,
                life = size == Size.Huge ? 1.7f : size == Size.Big ? 1.15f : 0.85f,
                spin = Random.Range(-14f, 14f),
            });
        }

        // Where a world spot is on the overlay, high enough above it that a word clears the kid's head (the
        // faces stay in view), kept clear of the info card and the controls.
        Vector2 ScreenSpot(Vector2 world, float fontSize)
        {
            var cam = Camera.main;
            Vector2 local = Vector2.zero;
            if (cam != null)
            {
                Vector3 screen = cam.WorldToScreenPoint(new Vector3(world.x, world.y, 0f));
                if (screen.z > 0f) RectTransformUtility.ScreenPointToLocalPointInRectangle(root, screen, null, out local);
            }
            Rect r = root.rect;
            local.y += 170f + fontSize * 0.9f;
            local.x = Mathf.Clamp(local.x, -r.width * 0.34f, r.width * 0.34f);
            local.y = Mathf.Clamp(local.y, -r.height * 0.12f, r.height * 0.32f);
            return local;
        }

        void Update()
        {
            float now = Time.unscaledTime;
            for (int i = live.Count - 1; i >= 0; i--)
            {
                var p = live[i];
                if (p.rect == null) { live.RemoveAt(i); continue; }
                float age = now - p.born;
                if (age >= p.life) { Remove(i); continue; }
                // Slam in past full size, settle, hold, then swell a touch as it fades.
                float s;
                if (age < 0.1f) s = Mathf.Lerp(0.3f, 1.25f, 1f - (1f - age / 0.1f) * (1f - age / 0.1f));
                else if (age < 0.2f) s = Mathf.Lerp(1.25f, 1f, (age - 0.1f) / 0.1f);
                else s = 1f;
                float fade = Mathf.InverseLerp(p.life - 0.25f, p.life, age);
                s *= 1f + 0.12f * fade;
                p.rect.localScale = new Vector3(s, s, 1f);
                p.group.alpha = 1f - fade;
                if (p.burst != null) p.burst.localRotation = Quaternion.Euler(0f, 0f, p.spin * age);
            }
        }

        void Remove(int i)
        {
            if (live[i].rect != null) Destroy(live[i].rect.gameObject);
            live.RemoveAt(i);
        }

        // ---------- Made once ----------

        bool EnsureCanvas()
        {
            if (root != null) return true;
            var canvas = UIKit.CreateCanvas("ComicPopsCanvas", 9);   // just under the HUD (10): the controls stay on top
            canvas.additionalShaderChannels |= AdditionalCanvasShaderChannels.TexCoord1;   // the lettering's dots
            var raycaster = canvas.GetComponent<GraphicRaycaster>();
            if (raycaster != null) Destroy(raycaster);   // takes no touches
            canvas.transform.SetParent(transform, false);
            root = (RectTransform)canvas.transform;
            return true;
        }

        Material Material(Style style)
        {
            if (materials == null)
            {
                materials = new Material[3];
                var shader = Resources.Load<Shader>("Shaders/ComicLettering");
                if (shader == null || !shader.isSupported) return null;   // plain gradient letters, no dots
                Color[] dots = { new Color(0.84f, 0.16f, 0.12f), new Color(0.16f, 0.47f, 0.78f), new Color(0.82f, 0.13f, 0.4f) };
                for (int i = 0; i < 3; i++)
                {
                    materials[i] = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
                    materials[i].SetColor("_DotColor", dots[i]);
                }
            }
            return materials[(int)style];
        }

        /// <summary>
        /// An ink starburst: a star polygon of 14 straight spikes of uneven length (straight edges from tip to
        /// notch, sharp points), a yellow fill with a thin ink edge, and the same star at half size as a pale heart.
        /// Drawn once.
        /// </summary>
        Sprite BurstSprite()
        {
            if (burstSprite != null) return burstSprite;
            const int N = 256, Spikes = 14;
            var rng = new System.Random(11);
            var pts = new Vector2[Spikes * 2];
            for (int i = 0; i < pts.Length; i++)
            {
                float a = (i + (float)(rng.NextDouble() - 0.5) * 0.35f) * Mathf.PI * 2f / pts.Length + 0.13f;
                float r = i % 2 == 0 ? (float)(0.8 + rng.NextDouble() * 0.2) : (float)(0.46 + rng.NextDouble() * 0.08);
                pts[i] = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r;
            }
            var px = new Color32[N * N];
            Color32 ink = new Color32(23, 13, 41, 255), gold = new Color32(255, 214, 58, 255), heart = new Color32(255, 248, 214, 255);
            float half = N * 0.5f, edge = 4f / half, aa = 1.2f / half;
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    var p = new Vector2((x + 0.5f - half) / half, (y + 0.5f - half) / half);
                    float d = Distance(pts, p, 1f);                // signed: > 0 inside the star
                    if (d <= -aa) { px[y * N + x] = new Color32(0, 0, 0, 0); continue; }
                    Color32 c = d < edge ? ink : (Distance(pts, p, 0.5f) > 0f ? heart : gold);
                    c.a = (byte)(255 * Mathf.Clamp01((d + aa) / aa));
                    px[y * N + x] = c;
                }
            var tex = new Texture2D(N, N, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, hideFlags = HideFlags.HideAndDontSave };
            tex.SetPixels32(px);
            tex.Apply(false, true);
            burstSprite = Sprite.Create(tex, new Rect(0, 0, N, N), new Vector2(0.5f, 0.5f), 100f);
            return burstSprite;
        }

        /// <summary>Signed distance from p to the star polygon scaled by s: positive inside, negative outside.</summary>
        static float Distance(Vector2[] pts, Vector2 p, float s)
        {
            float best = float.MaxValue;
            bool inside = false;
            for (int i = 0, j = pts.Length - 1; i < pts.Length; j = i++)
            {
                Vector2 a = pts[j] * s, b = pts[i] * s;
                Vector2 ab = b - a;
                float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / Mathf.Max(ab.sqrMagnitude, 1e-8f));
                best = Mathf.Min(best, (a + ab * t - p).magnitude);
                if ((a.y > p.y) != (b.y > p.y) && p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x) inside = !inside;
            }
            return inside ? best : -best;
        }
    }
}
