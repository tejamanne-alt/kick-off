using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Grey-box level HUD (IMGUI, no art needed): timer and bell clock, countdown,
    /// toasts, respawn fade, pause menu, results with stars, touch zones and a
    /// live tuning panel. The real UI is built in Phase 7.
    /// </summary>
    public class LevelHud : MonoBehaviour
    {
        public LevelManager level;
        public KidController kid;
        public BallController ball;
        public KickAimer aimer;
        [Tooltip("UI is designed for this screen height and scaled to fit.")]
        public float referenceHeight = 720f;

        static readonly Color Gold = new Color(1f, 0.82f, 0.25f);
        static readonly Color Late = new Color(1f, 0.45f, 0.35f);
        static readonly Rect PauseButton = new Rect(-200f, 10f, 90f, 44f);   // x measured from the right edge
        static readonly Rect TuningButton = new Rect(-100f, 10f, 90f, 44f);
        const float PanelWidth = 380f;

        bool showTuning;
        Vector2 tuningScroll;
        string toastText;
        Color toastColor;
        float toastUntil;
        float scale = 1f;
        Texture2D circleTexture;

        GUIStyle label, bigLabel, hugeLabel, centerLabel, box, button;

        void OnEnable()
        {
            ball.PerfectTouch += OnPerfectTouch;
            ball.Juggled += OnJuggled;
            level.CheckpointReached += OnCheckpoint;
            level.BallLost += OnBallLost;
            level.BellRang += OnBellRang;
            GameEvents.Raised += OnGameEvent;
        }

        void OnDisable()
        {
            ball.PerfectTouch -= OnPerfectTouch;
            ball.Juggled -= OnJuggled;
            level.CheckpointReached -= OnCheckpoint;
            level.BallLost -= OnBallLost;
            level.BellRang -= OnBellRang;
            GameEvents.Raised -= OnGameEvent;
            GameInput.UIBlockers.Clear();
        }

        void OnDestroy()
        {
            if (circleTexture != null) Destroy(circleTexture);
        }

        void OnPerfectTouch(int streak) { Toast(streak > 1 ? "Perfect touch  x" + streak : "Perfect touch!", Gold); }
        void OnJuggled(int count) { Toast("Juggle " + count, Gold); }
        void OnCheckpoint(Checkpoint cp) { Toast("Checkpoint!", new Color(0.5f, 1f, 0.6f)); }
        void OnBallLost(string reason) { Toast(reason, Late); }
        void OnBellRang() { Toast("BRRRING! The bell! Keep going!", Late); }

        void OnGameEvent(GameEventType type, Vector2 position, float intensity)
        {
            switch (type)
            {
                case GameEventType.DogSteal: Toast("Woof! The dog wants to play", Gold); break;
                case GameEventType.PedestrianBump: Toast("Oops - sorry!", Color.white); break;
                case GameEventType.GateOpened: Toast("Gate open!", new Color(0.5f, 1f, 0.6f)); break;
            }
        }

        void Toast(string text, Color color)
        {
            toastText = text;
            toastColor = color;
            toastUntil = Time.unscaledTime + 1.1f;
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

            DrawFade(w, h);
            DrawTopBar(w);
            DrawTouchZones(w, h);
            DrawAim(w);
            DrawToast(w);
            DrawIntro(w, h);
            DrawTopButtons(w);
            if (showTuning) DrawTuningPanel(h);

            if (level.State == LevelState.Paused) DrawPause(w, h);
            if (level.State == LevelState.Complete) DrawResults(w, h);
        }

        void RegisterBlockers(float w)
        {
            GameInput.UIBlockers.Clear();
            GameInput.UIBlockers.Add(ToScreen(FromRight(PauseButton, w)));
            GameInput.UIBlockers.Add(ToScreen(FromRight(TuningButton, w)));
            if (showTuning) GameInput.UIBlockers.Add(ToScreen(new Rect(0f, 0f, PanelWidth, referenceHeight)));
        }

        // ---------- In-run HUD ----------

        void DrawFade(float w, float h)
        {
            if (level.FadeAmount <= 0f) return;
            GUI.color = new Color(0f, 0f, 0f, level.FadeAmount);
            GUI.DrawTexture(new Rect(0f, 0f, w, h), Texture2D.whiteTexture);
            GUI.color = Color.white;
        }

        void DrawTopBar(float w)
        {
            float x = showTuning ? PanelWidth + 10f : 10f;
            string name = level.level != null ? level.level.levelId + "  " + level.level.displayName : "Test Track";
            GUI.color = new Color(0f, 0f, 0f, 0.35f);
            GUI.DrawTexture(new Rect(x - 6f, 4f, 560f, 88f), Texture2D.whiteTexture);
            GUI.color = Color.white;
            GUI.Label(new Rect(x, 8f, 600f, 28f), name, label);
            GUI.Label(new Rect(x, 34f, 200f, 28f), FormatTime(level.ElapsedTime), label);

            if (level.BellEnabled)
            {
                bool late = level.BellRung;
                bool close = !late && level.BellTimeLeft <= 10f;
                GUI.color = late ? Late : close ? Gold : Color.white;
                string bell = late ? "LATE!" : "Bell in " + FormatTime(level.BellTimeLeft, false);
                GUI.Label(new Rect(x + 110f, 34f, 220f, 28f), bell, label);
                GUI.color = Color.white;
            }

            GUI.Label(new Rect(x, 60f, 700f, 28f),
                string.Format("Perfect x{0} (best {1})    Juggles {2}    Balls lost {3}",
                    ball.PerfectStreak, level.BestPerfectStreak, ball.JuggleCount, level.BallsLost), label);
        }

        void DrawTouchZones(float w, float h)
        {
            var input = GameInput.Instance;
            if (input == null || level.State != LevelState.Playing) return;

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
                    "A/Shift brake   Space jump   F touch/juggle   Drag from ball to kick   Esc pause   R restart   Tab tuning", centerLabel);
                GUI.color = Color.white;
            }
        }

        void DrawAim(float w)
        {
            if (aimer == null || !aimer.IsAiming) return;

            Rect bar = new Rect(w * 0.5f - 150f, 96f, 300f, 22f);
            GUI.Box(bar, GUIContent.none, box);
            GUI.color = aimer.AimIsValid ? Color.Lerp(Color.green, Color.red, aimer.AimPower) : Color.gray;
            GUI.DrawTexture(new Rect(bar.x + 3f, bar.y + 3f, (bar.width - 6f) * aimer.AimPower, bar.height - 6f), Texture2D.whiteTexture);
            GUI.color = Color.white;

            if (!ball.InKickReach)
                GUI.Label(new Rect(0f, 122f, w, 30f), "Too far from the ball - get closer to kick", centerLabel);
        }

        void DrawToast(float w)
        {
            if (string.IsNullOrEmpty(toastText) || Time.unscaledTime > toastUntil) return;
            Color c = toastColor;
            c.a = Mathf.Clamp01((toastUntil - Time.unscaledTime) / 0.3f);
            GUI.color = c;
            GUI.Label(new Rect(0f, 150f, w, 50f), toastText, bigLabel);
            GUI.color = Color.white;
        }

        void DrawIntro(float w, float h)
        {
            if (level.State != LevelState.Intro) return;
            string text = level.IntroTimeLeft > 0.35f ? "Ready..." : "GO!";
            GUI.Label(new Rect(0f, h * 0.35f, w, 90f), text, hugeLabel);
        }

        void DrawTopButtons(float w)
        {
            if (level.State != LevelState.Complete
                && GUI.Button(FromRight(PauseButton, w), level.State == LevelState.Paused ? "Resume" : "Pause", button))
                level.TogglePause();
            if (GUI.Button(FromRight(TuningButton, w), showTuning ? "Close" : "Tuning", button)) showTuning = !showTuning;
        }

        // ---------- Menus ----------

        void DrawPause(float w, float h)
        {
            Rect panel = CenteredPanel(w, h, 420f, 380f);
            GUI.Box(panel, GUIContent.none, box);
            GUI.Label(new Rect(panel.x, panel.y + 15f, panel.width, 50f), "Paused", bigLabel);

            float bx = panel.x + 60f;
            float bw = panel.width - 120f;
            float y = panel.y + 80f;
            if (GUI.Button(new Rect(bx, y, bw, 48f), "Resume", button)) level.Resume();
            y += 58f;
            if (GUI.Button(new Rect(bx, y, bw, 48f), "Back to checkpoint", button))
            {
                level.Resume();
                level.RespawnAtCheckpoint();
            }
            y += 58f;
            if (GUI.Button(new Rect(bx, y, bw, 48f), "Restart level", button)) level.BeginRun();
            y += 58f;
            bool bellOn = GameSettings.BellTimerEnabled;
            string bellLabel = bellOn ? "School bell: ON" : "School bell: OFF (cozy)";
            if (GUI.Button(new Rect(bx, y, bw, 48f), bellLabel, button)) GameSettings.BellTimerEnabled = !bellOn;
            y += 58f;
            if (level.NextLevel != null && GUI.Button(new Rect(bx, y, bw, 40f), "Skip to next level (dev)", button))
                level.LoadNextLevel();
        }

        void DrawResults(float w, float h)
        {
            LevelResult r = level.Result;
            Rect panel = CenteredPanel(w, h, 560f, 420f);
            GUI.Box(panel, GUIContent.none, box);

            GUI.Label(new Rect(panel.x, panel.y + 15f, panel.width, 50f),
                r.beforeBell ? "Made it to school!" : "Made it... a bit late!", bigLabel);

            // Stars
            float size = 56f;
            float sx = panel.x + panel.width * 0.5f - (size * 3f + 20f) * 0.5f;
            for (int i = 0; i < 3; i++)
            {
                GUI.color = i < r.stars ? Gold : new Color(1f, 1f, 1f, 0.2f);
                GUI.DrawTexture(new Rect(sx + i * (size + 10f), panel.y + 75f, size, size), CircleTexture());
            }
            GUI.color = Color.white;

            int target = level.level != null ? level.level.perfectStreakTarget : 0;
            float ly = panel.y + 150f;
            Check(panel, ref ly, true, "Reached school with the ball");
            Check(panel, ref ly, r.beforeBell, "Before the bell (" + FormatTime(level.BellTime, false) + ")");
            Check(panel, ref ly, r.beforeBell && r.bestPerfectStreak >= target,
                "Perfect-touch streak of " + target + " (best " + r.bestPerfectStreak + ")");

            GUI.Label(new Rect(panel.x, ly + 6f, panel.width, 28f),
                string.Format("Time {0}    Balls lost {1}", FormatTime(r.time), r.ballsLost), centerLabel);

            float by = panel.y + panel.height - 70f;
            if (GUI.Button(new Rect(panel.x + 40f, by, 220f, 50f), "Retry", button)) level.BeginRun();
            string next = level.NextLevel != null ? "Next level" : "Play again";
            if (GUI.Button(new Rect(panel.x + panel.width - 260f, by, 220f, 50f), next, button)) level.LoadNextLevel();
        }

        void Check(Rect panel, ref float y, bool done, string text)
        {
            GUI.color = done ? Color.white : new Color(1f, 1f, 1f, 0.45f);
            GUI.Label(new Rect(panel.x + 70f, y, panel.width - 100f, 28f), (done ? "[x]  " : "[  ]  ") + text, label);
            GUI.color = Color.white;
            y += 30f;
        }

        // ---------- Tuning ----------

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

        // ---------- Helpers ----------

        static string FormatTime(float seconds, bool tenths = true)
        {
            seconds = Mathf.Max(0f, seconds);
            int minutes = (int)(seconds / 60f);
            float rest = seconds - minutes * 60f;
            return tenths
                ? string.Format("{0}:{1:00.0}", minutes, rest)
                : string.Format("{0}:{1:00}", minutes, Mathf.FloorToInt(rest));
        }

        static Rect CenteredPanel(float w, float h, float pw, float ph)
        {
            return new Rect(w * 0.5f - pw * 0.5f, h * 0.5f - ph * 0.5f, pw, ph);
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

        Texture2D CircleTexture()
        {
            if (circleTexture != null) return circleTexture;
            const int size = 64;
            circleTexture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            float r = size * 0.5f;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(r, r));
                    circleTexture.SetPixel(x, y, new Color(1f, 1f, 1f, Mathf.Clamp01(r - d)));
                }
            }
            circleTexture.Apply();
            return circleTexture;
        }

        void EnsureStyles()
        {
            if (label != null) return;
            label = new GUIStyle(GUI.skin.label) { fontSize = 18 };
            label.normal.textColor = Color.white;
            centerLabel = new GUIStyle(label) { alignment = TextAnchor.MiddleCenter };
            bigLabel = new GUIStyle(label) { fontSize = 32, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter };
            hugeLabel = new GUIStyle(bigLabel) { fontSize = 64 };
            box = new GUIStyle(GUI.skin.box) { fontSize = 22, alignment = TextAnchor.MiddleCenter };
            button = new GUIStyle(GUI.skin.button) { fontSize = 18 };
        }
    }
}
