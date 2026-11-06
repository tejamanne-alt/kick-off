using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Localization;
using DribbleToSchool.Tutorial;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The guided tour of the touch controls, the first time a level starts (and again from the Controls page). It holds
    /// the run before the clock starts (<see cref="LevelManager.Hold"/>), dims the screen and lights one control at a
    /// time with a caption card: the stick (walk, then pull down to slide), JUMP, KICK, a tap anywhere else (the perfect
    /// touch) and the pause button. A ghost thumb acts out each move. The controls stay live under the light, so the
    /// player can try each one: doing it ticks the step off ("Nice!") and moves on. Next and Skip are always there.
    /// The HUD that owns the canvas starts it (GameHud, the Holiday Run's HUD) and shows its controls while the run is held.
    /// </summary>
    public class ControlsTour : MonoBehaviour
    {
        /// <summary>What a step lights up.</summary>
        public enum Target { Stick, Jump, Kick, Screen, Pause }

        /// <summary>What the ghost thumb acts out.</summary>
        public enum Demo { Walk, Slide, Tap, Drag, None }

        /// <summary>One stop of the tour. Its caption is tour.&lt;key&gt;.title and tour.&lt;key&gt;.</summary>
        public struct Step
        {
            public readonly string key;
            public readonly Target target;
            public readonly Demo demo;

            public Step(string key, Target target, Demo demo)
            {
                this.key = key;
                this.target = target;
                this.demo = demo;
            }

            public string TitleKey { get { return "tour." + key + ".title"; } }
            public string BodyKey { get { return "tour." + key; } }
            /// <summary>Whether the player can do this step's move (and so tick it off) rather than only read it.</summary>
            public bool CanTry { get { return target != Target.Pause; } }
        }

        /// <summary>The tour, in order.</summary>
        public static readonly Step[] Steps =
        {
            new Step("walk", Target.Stick, Demo.Walk),
            new Step("slide", Target.Stick, Demo.Slide),
            new Step("jump", Target.Jump, Demo.Tap),
            new Step("kick", Target.Kick, Demo.Drag),
            new Step("touch", Target.Screen, Demo.Tap),
            new Step("pause", Target.Pause, Demo.None),
        };

        /// <summary>Its "seen" flag lives with the tutorial hints', so Reset progress and the store screenshots treat it alike.</summary>
        public const string SeenId = "controls";

        /// <summary>Has the player been through (or skipped) the tour?</summary>
        public static bool Done
        {
            get { return TutorialHint.Seen(SeenId); }
            set
            {
                if (value) TutorialHint.MarkSeen(SeenId);
                else TutorialHint.ResetAll(new[] { SeenId });
            }
        }

        /// <summary>True while a tour is on screen.</summary>
        public static bool Running { get { return current != null; } }

        /// <summary>Should a level that is starting begin with the tour? The first time, and after the Controls page turned it back on.</summary>
        public static bool ShouldStart { get { return current == null && !Done; } }

        /// <summary>
        /// Set by the HUD of a level that is being played: starts the tour there and then (the Controls page's button).
        /// Null on the menus, where the button instead makes the tour play at the start of the next level.
        /// </summary>
        public static System.Action Replay;

        static ControlsTour current;

        static readonly Color DimColor = new Color(0.02f, 0.04f, 0.12f, 0.66f);
        static readonly Color Glow = new Color(1f, 0.85f, 0.35f, 1f);
        static readonly Color Ghost = new Color(1f, 1f, 1f, 0.78f);

        LevelManager level;
        RectTransform root, pauseButton, hole, glowRing, thumb, ripple, card;
        Image[] dim;
        Image[] trail;
        Image thumbImage, rippleImage, glowImage;
        Text counter, title, body, tryIt;
        Button next, skip;
        Text nextLabel;
        int index = -1;
        float stepTime, doneAt = -1f, walked;
        readonly Vector3[] corners = new Vector3[4];

        /// <summary>
        /// Starts the tour over <paramref name="canvas"/> (the HUD's), holding <paramref name="level"/> until it ends.
        /// <paramref name="pauseButton"/> is the HUD's pause button (its last stop).
        /// </summary>
        public static ControlsTour Begin(RectTransform canvas, LevelManager level, RectTransform pauseButton)
        {
            if (current != null || canvas == null || level == null) return current;
            var rt = UIKit.Rect(canvas, "ControlsTour");
            UIKit.Stretch(rt);
            rt.SetAsLastSibling();
            var tour = rt.gameObject.AddComponent<ControlsTour>();
            tour.root = rt;
            tour.level = level;
            tour.pauseButton = pauseButton;
            tour.Build();
            current = tour;
            level.Hold(true);
            tour.Go(0);
            return tour;
        }

        // ---------- Build ----------

        void Build()
        {
            // The dim: a square with a round hole over the control, and four plain panels round it for the rest. None of
            // it takes touches, so a thumb on the lit control reaches the game.
            dim = new Image[5];
            for (int i = 0; i < 4; i++) dim[i] = Plain(root, "Dim" + i, null, DimColor);
            hole = UIKit.Rect(root, "Hole");
            dim[4] = Plain(hole, "Spot", ProceduralSprites.SpotHole, DimColor);
            UIKit.Stretch(dim[4].rectTransform);
            dim[4].type = Image.Type.Simple;
            dim[4].preserveAspect = false;

            glowRing = UIKit.Rect(root, "Glow");
            glowImage = Plain(glowRing, "Ring", ProceduralSprites.Ring, Glow);
            UIKit.Stretch(glowImage.rectTransform);

            // The ghost thumb, its trail (the kick's drag) and the ripple of a tap.
            trail = new Image[5];
            for (int i = 0; i < trail.Length; i++)
            {
                trail[i] = Plain(root, "Trail" + i, ProceduralSprites.SoftEdgeDisc, Ghost);
                trail[i].rectTransform.sizeDelta = Vector2.one * 26f;
            }
            ripple = UIKit.Rect(root, "Ripple");
            rippleImage = Plain(ripple, "Ring", ProceduralSprites.Ring, Color.white);
            UIKit.Stretch(rippleImage.rectTransform);
            thumb = UIKit.Rect(root, "Thumb");
            thumb.sizeDelta = Vector2.one * 112f;
            thumbImage = Plain(thumb, "Disc", ProceduralSprites.SoftEdgeDisc, Ghost);
            UIKit.Stretch(thumbImage.rectTransform);
            var thumbRim = Plain(thumb, "Rim", ProceduralSprites.Ring, new Color(1f, 1f, 1f, 0.9f));
            UIKit.Stretch(thumbRim.rectTransform);
            var sh = thumbImage.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0f, 0.25f);
            sh.effectDistance = new Vector2(0f, -4f);

            // The caption: across the top, clear of the controls along the bottom.
            var face = UIKit.Card(root, "Caption", UITheme.Paper);
            card = (RectTransform)face.transform.parent;
            UIKit.Place(card, new Vector2(0.5f, 1f), new Vector2(0f, -30f), new Vector2(1060f, 330f), new Vector2(0.5f, 1f));
            var t = face.transform;
            counter = UIKit.Label(t, "Counter", "", 24, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Place(counter.rectTransform, new Vector2(0f, 1f), new Vector2(40f, -34f), new Vector2(400f, 36f), new Vector2(0f, 0.5f));
            title = UIKit.Label(t, "Title", "", 46, UITheme.Navy, TextAnchor.MiddleLeft, true);
            UIKit.Place(title.rectTransform, new Vector2(0f, 1f), new Vector2(40f, -80f), new Vector2(980f, 58f), new Vector2(0f, 0.5f));
            UIKit.Fit(title, 30);
            body = UIKit.Label(t, "Body", "", 31, UITheme.Ink, TextAnchor.UpperLeft);
            var b = body.rectTransform;
            b.anchorMin = Vector2.zero;
            b.anchorMax = Vector2.one;
            b.offsetMin = new Vector2(40f, 104f);
            b.offsetMax = new Vector2(-40f, -114f);
            body.resizeTextForBestFit = true;
            body.resizeTextMinSize = 22;
            body.resizeTextMaxSize = 31;
            body.verticalOverflow = VerticalWrapMode.Truncate;
            tryIt = UIKit.Label(t, "TryIt", "", 30, UITheme.Accent, TextAnchor.MiddleLeft, true);
            UIKit.Place(tryIt.rectTransform, new Vector2(0f, 0f), new Vector2(40f, 58f), new Vector2(440f, 60f), new Vector2(0f, 0.5f));
            UIKit.Fit(tryIt, 22);

            next = UIKit.Button(t, "Next", Loc.T("tour.next"), UITheme.Green, OnNext, 36);
            UIKit.Place((RectTransform)next.transform, new Vector2(1f, 0f), new Vector2(-34f, 28f), new Vector2(260f, 84f), new Vector2(1f, 0f));
            nextLabel = next.GetComponentInChildren<Text>();
            skip = UIKit.Button(t, "Skip", Loc.T("tour.skip"), UITheme.Paper, Finish, 30, UITheme.InkSoft);
            UIKit.Place((RectTransform)skip.transform, new Vector2(1f, 0f), new Vector2(-314f, 28f), new Vector2(200f, 84f), new Vector2(1f, 0f));
        }

        static Image Plain(Transform parent, string name, Sprite sprite, Color color)
        {
            var rt = UIKit.Rect(parent, name);
            var image = rt.gameObject.AddComponent<Image>();
            image.sprite = sprite;
            image.color = color;
            image.raycastTarget = false;
            return image;
        }

        // ---------- Steps ----------

        void Go(int step)
        {
            index = step;
            stepTime = 0f;
            doneAt = -1f;
            walked = 0f;
            var s = Steps[step];
            bool last = step == Steps.Length - 1;
            counter.text = Loc.F("tour.step", step + 1, Steps.Length);
            title.text = Loc.T(s.TitleKey);
            title.color = UITheme.Navy;
            body.text = Loc.T(s.BodyKey);
            tryIt.text = s.CanTry ? Loc.T("tour.tryIt") : "";
            nextLabel.text = Loc.T(last ? "tour.go" : "tour.next");
            skip.gameObject.SetActive(!last);
            var pop = card.GetComponent<UIPopIn>();
            if (pop == null) pop = UIKit.PopIn(card.gameObject);
            pop.Play();
        }

        void OnNext()
        {
            if (index >= Steps.Length - 1) Finish();
            else Go(index + 1);
        }

        /// <summary>Ends the tour (done or skipped): it will not start on its own again.</summary>
        void Finish()
        {
            Done = true;
            if (level != null) level.Hold(false);
            if (current == this) current = null;
            Destroy(gameObject);
        }

        void OnDestroy()
        {
            if (current == this)
            {
                current = null;
                if (level != null) level.Hold(false);
            }
        }

        // ---------- Per frame ----------

        void Update()
        {
            var input = GameInput.Instance;
            if (input == null || index < 0) return;
            float dt = Time.unscaledDeltaTime;
            stepTime += dt;
            var s = Steps[index];

            // Where the lit control is, in pixels (the controls move with the screen's shape and handedness).
            Vector2 center;
            float radius;
            Locate(s.target, input, out center, out radius);
            float padded = radius * (s.target == Target.Screen ? 1f : 1.22f);
            Light(center, padded);

            // Tried it? Tick it off, and on after a moment.
            if (doneAt < 0f && s.CanTry && Tried(s, input, dt))
            {
                doneAt = stepTime;
                title.text = Loc.T("tour.nice");
                title.color = UITheme.Green;
                tryIt.text = "";
                GameEvents.Raise(GameEventType.UIClick, Vector2.zero, 0.8f);
            }
            if (doneAt >= 0f && stepTime - doneAt > 0.9f)
            {
                OnNext();
                return;
            }

            // The ghost thumb acts the move out until the player has done it.
            Act(s.demo, center, radius, doneAt >= 0f);
            float pulse = 0.5f + 0.5f * Mathf.Sin(stepTime * 5f);
            glowRing.localScale = Vector3.one * (1f + 0.05f * pulse);
            glowImage.color = new Color(Glow.r, Glow.g, Glow.b, 0.55f + 0.4f * pulse);
        }

        void LateUpdate()
        {
            // A tap on the caption's buttons is not a touch in the game.
            if (card != null) GameInput.UIBlockers.Add(ScreenRect(card));
        }

        /// <summary>Did the player just do this step's move?</summary>
        bool Tried(Step s, GameInput input, float dt)
        {
            switch (s.key)
            {
                case "walk":
                    if (input.MoveAxis != 0f) walked += dt;
                    return walked > 0.35f;
                case "slide": return input.SlidePressed;
                case "jump": return input.JumpPressed;
                case "kick": return input.KickReleased || input.KickTapped;
                case "touch": return input.TouchPressed;
                default: return false;
            }
        }

        void Locate(Target target, GameInput input, out Vector2 center, out float radius)
        {
            float w = Mathf.Max(1f, Screen.width), h = Mathf.Max(1f, Screen.height);
            Rect r;
            switch (target)
            {
                case Target.Stick: r = input.StickHomeNormalized; break;
                case Target.Jump: r = input.JumpButtonNormalized; break;
                case Target.Kick: r = input.KickButtonNormalized; break;
                case Target.Pause:
                    if (pauseButton != null)
                    {
                        Rect p = ScreenRect(pauseButton);
                        center = p.center;
                        radius = Mathf.Max(p.width, p.height) * 0.5f;
                        return;
                    }
                    r = new Rect(0.9f, 0.85f, 0.08f, 0.12f);
                    break;
                default:
                    // Anywhere else: a patch of open screen right of the kid, above the buttons.
                    center = new Vector2(w * 0.62f, h * 0.5f);
                    radius = h * 0.16f;
                    return;
            }
            center = new Vector2(r.center.x * w, r.center.y * h);
            radius = r.width * w * 0.5f;
        }

        /// <summary>Puts the hole of the dim over a circle (pixels), the glow round it.</summary>
        void Light(Vector2 center, float radius)
        {
            float w = Mathf.Max(1f, Screen.width), h = Mathf.Max(1f, Screen.height);
            // The circle fills 80% of the spot sprite's square.
            float half = radius / 0.8f;
            float x0 = (center.x - half) / w, x1 = (center.x + half) / w, y0 = (center.y - half) / h, y1 = (center.y + half) / h;
            Anchor(hole, x0, y0, x1, y1);
            Anchor(dim[0].rectTransform, 0f, 0f, Mathf.Max(0f, x0), 1f);                          // left
            Anchor(dim[1].rectTransform, Mathf.Min(1f, x1), 0f, 1f, 1f);                          // right
            Anchor(dim[2].rectTransform, Mathf.Max(0f, x0), 0f, Mathf.Min(1f, x1), Mathf.Max(0f, y0));  // below
            Anchor(dim[3].rectTransform, Mathf.Max(0f, x0), Mathf.Min(1f, y1), Mathf.Min(1f, x1), 1f);  // above
            float g = radius * 1.04f;
            Anchor(glowRing, (center.x - g) / w, (center.y - g) / h, (center.x + g) / w, (center.y + g) / h);
        }

        static void Anchor(RectTransform rt, float x0, float y0, float x1, float y1)
        {
            rt.anchorMin = new Vector2(x0, y0);
            rt.anchorMax = new Vector2(Mathf.Max(x0, x1), Mathf.Max(y0, y1));
            rt.offsetMin = rt.offsetMax = Vector2.zero;
        }

        // ---------- The ghost thumb ----------

        // Key frames (time in seconds, offset in parts of the control's radius) for the stick's two moves.
        static readonly Vector3[] WalkKeys =
        {
            new Vector3(0f, 0f, 0f), new Vector3(0.35f, 0f, 0f), new Vector3(0.75f, 0.62f, 0f), new Vector3(1.3f, 0.62f, 0f),
            new Vector3(1.65f, 0f, 0f), new Vector3(2.05f, -0.62f, 0f), new Vector3(2.6f, -0.62f, 0f), new Vector3(2.95f, 0f, 0f),
            new Vector3(3.2f, 0f, 0f),
        };
        static readonly Vector3[] SlideKeys =
        {
            new Vector3(0f, 0f, 0f), new Vector3(0.35f, 0f, 0f), new Vector3(0.75f, 0.42f, -0.72f), new Vector3(1.35f, 0.42f, -0.72f),
            new Vector3(1.7f, 0f, 0f), new Vector3(2.1f, -0.42f, -0.72f), new Vector3(2.7f, -0.42f, -0.72f), new Vector3(3.05f, 0f, 0f),
            new Vector3(3.3f, 0f, 0f),
        };

        void Act(Demo demo, Vector2 center, float radius, bool tried)
        {
            float scale = CanvasScale();
            bool show = demo != Demo.None && !tried;
            thumb.gameObject.SetActive(show);
            ripple.gameObject.SetActive(show && demo == Demo.Tap);
            for (int i = 0; i < trail.Length; i++) trail[i].gameObject.SetActive(show && demo == Demo.Drag);
            if (!show) return;

            float thumbSize = Mathf.Clamp(radius * 0.62f / scale, 80f, 130f);
            thumb.sizeDelta = Vector2.one * thumbSize;
            float alpha = 1f;
            Vector2 at = center;
            float press = 1f;
            switch (demo)
            {
                case Demo.Walk:
                case Demo.Slide:
                {
                    var keys = demo == Demo.Walk ? WalkKeys : SlideKeys;
                    float cycle = keys[keys.Length - 1].x;
                    Vector2 off = Path(keys, stepTime % cycle);
                    at = center + off * radius;
                    break;
                }
                case Demo.Tap:
                {
                    float t = stepTime % 1.4f;
                    press = t > 0.25f && t < 0.5f ? 0.82f : 1f;
                    float r = Mathf.Clamp01((t - 0.3f) / 0.7f);
                    SetAt(ripple, center, radius * Mathf.Lerp(0.6f, 1.5f, r) * 2f / scale);
                    rippleImage.color = new Color(1f, 1f, 1f, t > 0.3f ? 0.8f * (1f - r) : 0f);
                    break;
                }
                case Demo.Drag:
                {
                    // Down on KICK, a drag up and forward (the way the ball should go: a chip ahead), let go.
                    float t = stepTime % 2.2f;
                    Vector2 end = center + new Vector2(0.55f, 1f).normalized * radius * 2.6f;
                    float k = Mathf.Clamp01((t - 0.35f) / 0.9f);
                    k = k * k * (3f - 2f * k);
                    at = Vector2.Lerp(center, end, k);
                    press = t > 0.2f && t < 1.45f ? 0.86f : 1f;
                    alpha = t > 1.45f ? Mathf.Clamp01(1f - (t - 1.45f) / 0.4f) : 1f;
                    for (int i = 0; i < trail.Length; i++)
                    {
                        float f = (i + 1f) / (trail.Length + 1f);
                        SetAt(trail[i].rectTransform, Vector2.Lerp(center, at, f), 24f);
                        trail[i].color = new Color(1f, 1f, 1f, k > f * 0.9f ? 0.55f * alpha : 0f);
                    }
                    break;
                }
            }
            SetAt(thumb, at, thumbSize * press);
            thumbImage.color = new Color(Ghost.r, Ghost.g, Ghost.b, Ghost.a * alpha);
        }

        /// <summary>Where a key-framed move is at time <paramref name="t"/>, eased between frames.</summary>
        static Vector2 Path(Vector3[] keys, float t)
        {
            for (int i = 1; i < keys.Length; i++)
            {
                if (t > keys[i].x) continue;
                var a = keys[i - 1];
                var b = keys[i];
                float k = Mathf.Clamp01((t - a.x) / Mathf.Max(0.0001f, b.x - a.x));
                k = k * k * (3f - 2f * k);
                return new Vector2(Mathf.Lerp(a.y, b.y, k), Mathf.Lerp(a.z, b.z, k));
            }
            var lastKey = keys[keys.Length - 1];
            return new Vector2(lastKey.y, lastKey.z);
        }

        /// <summary>Centres <paramref name="rt"/> on a point in pixels, <paramref name="size"/> canvas units across.</summary>
        static void SetAt(RectTransform rt, Vector2 pixels, float size)
        {
            float w = Mathf.Max(1f, Screen.width), h = Mathf.Max(1f, Screen.height);
            var n = new Vector2(pixels.x / w, pixels.y / h);
            rt.anchorMin = rt.anchorMax = n;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = Vector2.one * size;
        }

        /// <summary>Pixels per canvas unit (the canvas matches the screen's height to 1080).</summary>
        static float CanvasScale()
        {
            return Mathf.Max(0.01f, Screen.height / UIKit.ReferenceResolution.y);
        }

        Rect ScreenRect(RectTransform rt)
        {
            rt.GetWorldCorners(corners);   // overlay canvas: world space == screen pixels
            return Rect.MinMaxRect(corners[0].x, corners[0].y, corners[2].x, corners[2].y);
        }
    }
}
