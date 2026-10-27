using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Grey-box HUD for Phase 1 (IMGUI, no art needed): stats, jump button,
    /// kick power meter, feedback toasts and a live tuning panel.
    /// The real HUD is built in Phase 7.
    /// </summary>
    public class DevHud : MonoBehaviour
    {
        public TestTrackSession session;
        public KidController kid;
        public BallController ball;
        public KickAimer aimer;
        [Tooltip("UI is designed for this screen height and scaled to fit.")]
        public float referenceHeight = 720f;

        bool showTuning;
        Vector2 tuningScroll;
        string toastText;
        float toastUntil;
        float scale = 1f;

        GUIStyle label, bigLabel, centerLabel, box, button;

        static readonly Rect ResetButton = new Rect(-200f, 10f, 90f, 44f);   // x from right edge
        static readonly Rect TuningButton = new Rect(-100f, 10f, 90f, 44f);
        const float PanelWidth = 380f;

        void OnEnable()
        {
            ball.PerfectTouch += OnPerfectTouch;
            ball.Juggled += OnJuggled;
        }

        void OnDisable()
        {
            ball.PerfectTouch -= OnPerfectTouch;
            ball.Juggled -= OnJuggled;
            GameInput.UIBlockers.Clear();
        }

        void OnPerfectTouch(int streak) { Toast(streak > 1 ? "Perfect touch  x" + streak : "Perfect touch!"); }
        void OnJuggled(int count) { Toast("Juggle " + count); }

        void Toast(string text)
        {
            toastText = text;
            toastUntil = Time.unscaledTime + 0.9f;
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input != null && input.DebugTogglePressed) showTuning = !showTuning;
        }

        void OnGUI()
        {
            scale = Screen.height / referenceHeight;
            GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));
            float w = Screen.width / scale;
            float h = referenceHeight;
            EnsureStyles();

            if (Event.current.type == EventType.Layout) RegisterBlockers(w);

            DrawStats();
            DrawTouchZones(w, h);
            DrawAim(w);
            DrawToast(w);
            DrawTopButtons(w);
            if (showTuning) DrawTuningPanel(h);
            if (session.Finished) DrawFinish(w, h);
        }

        void RegisterBlockers(float w)
        {
            GameInput.UIBlockers.Clear();
            GameInput.UIBlockers.Add(ToScreen(FromRight(ResetButton, w)));
            GameInput.UIBlockers.Add(ToScreen(FromRight(TuningButton, w)));
            if (showTuning) GameInput.UIBlockers.Add(ToScreen(new Rect(0f, 0f, PanelWidth, referenceHeight)));
        }

        void DrawStats()
        {
            string text = string.Format("Time {0:0.0}s    Perfect x{1} (best {2})    Juggles {3}    Resets {4}",
                session.ElapsedTime, ball.PerfectStreak, session.BestPerfectStreak, ball.JuggleCount, session.Resets);
            float x = showTuning ? PanelWidth + 10f : 10f;
            GUI.Label(new Rect(x, 10f, 900f, 30f), text, label);
        }

        void DrawTouchZones(float w, float h)
        {
            var input = GameInput.Instance;
            if (input == null) return;

            Rect jump = ToGui(input.JumpButtonScreenRect);
            GUI.color = new Color(1f, 1f, 1f, input.JumpHeld ? 0.8f : 0.45f);
            GUI.Box(jump, "JUMP", box);

            GUI.color = new Color(1f, 1f, 1f, input.BrakeHeld ? 0.7f : 0.25f);
            GUI.Label(new Rect(10f, h - 40f, 300f, 30f), "HOLD HERE = BRAKE", label);
            GUI.color = Color.white;

            if (!Application.isMobilePlatform)
            {
                GUI.color = new Color(1f, 1f, 1f, 0.6f);
                GUI.Label(new Rect(0f, h - 40f, w, 30f),
                    "A/Shift brake   Space jump   F touch/juggle   Drag from ball to kick   R reset   Tab tuning", centerLabel);
                GUI.color = Color.white;
            }
        }

        void DrawAim(float w)
        {
            if (aimer == null || !aimer.IsAiming) return;

            Rect bar = new Rect(w * 0.5f - 150f, 50f, 300f, 22f);
            GUI.Box(bar, GUIContent.none, box);
            GUI.color = aimer.AimIsValid ? Color.Lerp(Color.green, Color.red, aimer.AimPower) : Color.gray;
            GUI.DrawTexture(new Rect(bar.x + 3f, bar.y + 3f, (bar.width - 6f) * aimer.AimPower, bar.height - 6f), Texture2D.whiteTexture);
            GUI.color = Color.white;

            if (!ball.InKickReach)
                GUI.Label(new Rect(0f, 78f, w, 30f), "Too far from the ball - get closer to kick", centerLabel);
        }

        void DrawToast(float w)
        {
            if (string.IsNullOrEmpty(toastText) || Time.unscaledTime > toastUntil) return;
            float alpha = Mathf.Clamp01((toastUntil - Time.unscaledTime) / 0.3f);
            GUI.color = new Color(1f, 0.95f, 0.5f, alpha);
            GUI.Label(new Rect(0f, 110f, w, 50f), toastText, bigLabel);
            GUI.color = Color.white;
        }

        void DrawTopButtons(float w)
        {
            if (GUI.Button(FromRight(ResetButton, w), "Reset", button)) session.ResetRun();
            if (GUI.Button(FromRight(TuningButton, w), showTuning ? "Close" : "Tuning", button)) showTuning = !showTuning;
        }

        void DrawFinish(float w, float h)
        {
            Rect panel = new Rect(w * 0.5f - 260f, h * 0.5f - 110f, 520f, 220f);
            GUI.Box(panel, GUIContent.none, box);
            GUI.Label(new Rect(panel.x, panel.y + 20f, panel.width, 50f), "Made it to school!", bigLabel);
            GUI.Label(new Rect(panel.x, panel.y + 85f, panel.width, 30f),
                string.Format("Time {0:0.0}s    Best perfect streak {1}    Resets {2}",
                    session.ElapsedTime, session.BestPerfectStreak, session.Resets), centerLabel);
            if (GUI.Button(new Rect(panel.x + panel.width * 0.5f - 100f, panel.y + 140f, 200f, 50f), "Run again", button))
                session.ResetRun();
        }

        void DrawTuningPanel(float h)
        {
            GUI.Box(new Rect(0f, 0f, PanelWidth, h), GUIContent.none, box);
            GUILayout.BeginArea(new Rect(10f, 10f, PanelWidth - 20f, h - 20f));
            tuningScroll = GUILayout.BeginScrollView(tuningScroll);

            var p = kid.tuning;
            var b = ball.tuning;
            GUI.changed = false;

            GUILayout.Label("KID", label);
            p.runSpeed = Slider("Run speed", p.runSpeed, 1f, 9f);
            p.acceleration = Slider("Acceleration", p.acceleration, 2f, 40f);
            p.jumpVelocity = Slider("Jump velocity", p.jumpVelocity, 4f, 16f);
            p.gravityScale = Slider("Gravity", p.gravityScale, 1f, 6f);
            p.jumpCutMultiplier = Slider("Short-hop cut", p.jumpCutMultiplier, 0f, 1f);
            p.fallGravityMultiplier = Slider("Fall gravity x", p.fallGravityMultiplier, 1f, 3f);

            GUILayout.Space(8f);
            GUILayout.Label("BALL", label);
            b.gravityScale = Slider("Gravity", b.gravityScale, 0.5f, 4f);
            b.bounciness = Slider("Bounciness", b.bounciness, 0f, 1f);
            b.friction = Slider("Friction", b.friction, 0f, 1f);
            b.rollingResistance = Slider("Rolling resistance", b.rollingResistance, 0f, 2f);
            b.linearDamping = Slider("Air drag", b.linearDamping, 0f, 1f);

            GUILayout.Space(8f);
            GUILayout.Label("DRIBBLE", label);
            b.reachRadius = Slider("Reach", b.reachRadius, 0.3f, 1.5f);
            b.dribbleLeadSpeed = Slider("Lead speed", b.dribbleLeadSpeed, 0.2f, 4f);
            b.touchLift = Slider("Touch lift", b.touchLift, 0f, 4f);
            b.autoTouchVariance = Slider("Auto-touch sloppiness", b.autoTouchVariance, 0f, 0.5f);
            b.perfectTouchBand.x = Slider("Perfect band min", b.perfectTouchBand.x, 0f, 1f);
            b.perfectTouchBand.y = Slider("Perfect band max", b.perfectTouchBand.y, b.perfectTouchBand.x, 1.5f);
            b.juggleUpSpeed = Slider("Juggle pop", b.juggleUpSpeed, 2f, 10f);

            GUILayout.Space(8f);
            GUILayout.Label("KICK", label);
            b.minKickSpeed = Slider("Min kick speed", b.minKickSpeed, 0f, 10f);
            b.maxKickSpeed = Slider("Max kick speed", b.maxKickSpeed, b.minKickSpeed, 25f);
            b.maxDragDistance = Slider("Full-power drag", b.maxDragDistance, 0.5f, 5f);
            b.kickReach = Slider("Kick reach", b.kickReach, 0.3f, 2f);
            b.aimTimeScale = Slider("Aim slow-mo", b.aimTimeScale, 0.1f, 1f);
            b.previewDuration = Slider("Preview seconds", b.previewDuration, 0.1f, 1.5f);

            if (GUI.changed)
            {
                kid.ApplyTuning();
                ball.ApplyTuning();
#if UNITY_EDITOR
                UnityEditor.EditorUtility.SetDirty(p);
                UnityEditor.EditorUtility.SetDirty(b);
#endif
            }

            GUILayout.Space(8f);
            GUILayout.Label(Application.isEditor
                ? "Editor: changes are saved to the tuning assets."
                : "Device: changes last until the app closes.", label);

            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        float Slider(string name, float value, float min, float max)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(name + "  " + value.ToString("0.00"), label, GUILayout.Width(190f));
            value = GUILayout.HorizontalSlider(value, min, max, GUILayout.Width(150f), GUILayout.Height(28f));
            GUILayout.EndHorizontal();
            return value;
        }

        Rect FromRight(Rect r, float width)
        {
            return new Rect(width + r.x, r.y, r.width, r.height);
        }

        /// <summary>GUI rect (top-left origin, scaled) to screen rect (bottom-left origin, pixels).</summary>
        Rect ToScreen(Rect r)
        {
            return new Rect(r.x * scale, Screen.height - (r.y + r.height) * scale, r.width * scale, r.height * scale);
        }

        /// <summary>Screen rect (bottom-left origin, pixels) to GUI rect (top-left origin, scaled).</summary>
        Rect ToGui(Rect r)
        {
            return new Rect(r.x / scale, (Screen.height - r.y - r.height) / scale, r.width / scale, r.height / scale);
        }

        void EnsureStyles()
        {
            if (label != null) return;
            label = new GUIStyle(GUI.skin.label) { fontSize = 18 };
            label.normal.textColor = Color.white;
            centerLabel = new GUIStyle(label) { alignment = TextAnchor.MiddleCenter };
            bigLabel = new GUIStyle(label) { fontSize = 34, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
            box = new GUIStyle(GUI.skin.box) { fontSize = 22, alignment = TextAnchor.MiddleCenter };
            button = new GUIStyle(GUI.skin.button) { fontSize = 18 };
        }
    }
}
