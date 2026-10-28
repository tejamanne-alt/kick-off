using System.Collections;
using DribbleToSchool.Audio;
using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.Tutorial;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The in-level HUD (uGUI, built from code): info card, pause button,
    /// touch-control visuals, aim meter, toasts, countdown, respawn fade,
    /// tutorial hints, the pause menu and the animated results screen.
    /// </summary>
    public class GameHud : MonoBehaviour
    {
        public LevelManager level;
        public KidController kid;
        public BallController ball;
        public KickAimer aimer;
        public DevTuningPanel tuning;

        static readonly Color Late = new Color(0.95f, 0.4f, 0.35f);
        static readonly Color WalkColor = new Color(0.2f, 0.27f, 0.45f);
        static readonly Color KickReady = new Color(0.3f, 0.82f, 0.42f);

        RectTransform root;
        Text titleText, timeText, bellText, coinText, streakText, statusText;
        Image fade;
        RectTransform jumpRect, kickRect, leftRect, rightRect, aimKnob, aimBar, aimFill, hintCard;
        TouchButton jumpButton, kickButton, leftButton, rightButton;
        Image aimFillImage;
        float tooFarUntil;
        Text tooFar, toast, bigText, hintText;
        RectTransform pauseRect, tuneRect;
        GameObject pauseModal, resultsModal;
        float toastUntil, hintUntil, goUntil;

        // Text is only rebuilt when the value behind it changes (no per-frame garbage).
        int shownTenths = -1, shownBell = int.MinValue, shownCoins = -1, shownTotal = -1, shownStreak = -1, shownJuggles = -1;
        float nextStatusRefresh;
        LevelState lastState = (LevelState)(-1);

        void Start()
        {
            Build();
            ball.PerfectTouch += OnPerfectTouch;
            ball.Juggled += OnJuggled;
            level.CheckpointReached += OnCheckpoint;
            level.BallLost += OnBallLost;
            level.BellRang += OnBellRang;
            GameEvents.Raised += OnGameEvent;
            TutorialHint.Shown += OnHint;
        }

        void OnDestroy()
        {
            if (ball != null) { ball.PerfectTouch -= OnPerfectTouch; ball.Juggled -= OnJuggled; }
            if (level != null)
            {
                level.CheckpointReached -= OnCheckpoint;
                level.BallLost -= OnBallLost;
                level.BellRang -= OnBellRang;
            }
            GameEvents.Raised -= OnGameEvent;
            TutorialHint.Shown -= OnHint;
            GameInput.UIBlockers.Clear();
        }

        // ---------- Build ----------

        void Build()
        {
            var canvas = UIKit.CreateCanvas("HUD", 10);
            root = (RectTransform)canvas.transform;

            // Info card (top-left)
            var info = UIKit.Card(root, "Info", new Color(1f, 0.97f, 0.9f, 0.94f));
            UIKit.Place((RectTransform)info.transform.parent, new Vector2(0f, 1f), new Vector2(30f, -30f), new Vector2(660f, 200f), new Vector2(0f, 1f));
            var t = info.transform;
            titleText = Text(t, "Title", 34, new Vector2(30f, -38f), new Vector2(600f, 50f), TextAnchor.MiddleLeft);
            timeText = Text(t, "Time", 46, new Vector2(30f, -95f), new Vector2(220f, 60f), TextAnchor.MiddleLeft);
            bellText = Text(t, "Bell", 34, new Vector2(250f, -95f), new Vector2(390f, 60f), TextAnchor.MiddleLeft);
            statusText = Text(t, "Status", 32, new Vector2(250f, -95f), new Vector2(390f, 60f), TextAnchor.MiddleLeft);
            coinText = UIKit.CoinAmount(t, "Coins", 0, 38, UITheme.Ink);
            UIKit.Place((RectTransform)coinText.transform.parent, new Vector2(0f, 1f), new Vector2(30f, -158f), new Vector2(220f, 50f), new Vector2(0f, 0.5f));
            streakText = Text(t, "Streak", 32, new Vector2(250f, -158f), new Vector2(390f, 50f), TextAnchor.MiddleLeft);

            // Pause button (top-right)
            var pause = UIKit.Button(root, "Pause", "", UITheme.Paper, () => level.TogglePause());
            pauseRect = (RectTransform)pause.transform;
            UIKit.Place(pauseRect, new Vector2(1f, 1f), new Vector2(-40f, -40f), new Vector2(130f, 130f), new Vector2(1f, 1f));
            MakeRound(pause);
            UIKit.Icon(pause.transform.Find("Face"), "Icon", ProceduralSprites.Pause, UITheme.Ink, 64f);

            if (tuning != null && DevTuningPanel.Available)
            {
                var tune = UIKit.Button(root, "Tune", "Tune", UITheme.Blue, () => tuning.visible = !tuning.visible, 28);
                tuneRect = (RectTransform)tune.transform;
                UIKit.Place(tuneRect, new Vector2(1f, 1f), new Vector2(-190f, -60f), new Vector2(130f, 80f), new Vector2(1f, 1f));
            }

            // Touch controls: glossy key caps that push in when held (see TouchButton).
            jumpButton = TouchButton.Create(root, "JumpButton", UITheme.Blue, 0.82f, true);
            jumpButton.AddIcon(ProceduralSprites.ArrowUp, Color.white, 0.42f, 0f, 0.6f);
            jumpButton.AddLabel(Loc.T("hud.jump"), 34);
            jumpRect = (RectTransform)jumpButton.transform;

            // Walk buttons: the chevron turned to point back / forward, on quieter glass caps.
            leftButton = TouchButton.Create(root, "LeftButton", WalkColor, 0.5f, false);
            leftButton.AddIcon(ProceduralSprites.ArrowUp, Color.white, 0.46f, 90f);
            leftRect = (RectTransform)leftButton.transform;
            rightButton = TouchButton.Create(root, "RightButton", WalkColor, 0.5f, false);
            rightButton.AddIcon(ProceduralSprites.ArrowUp, Color.white, 0.46f, -90f);
            rightRect = (RectTransform)rightButton.transform;

            // Kick button: a ball icon, and a knob that follows the aiming drag.
            kickButton = TouchButton.Create(root, "KickButton", UITheme.Accent, 0.82f, true);
            kickButton.AddIcon(ProceduralSprites.BallIcon, Color.white, 0.44f, 0f, 0.6f);
            kickButton.AddLabel(Loc.T("hud.kick"), 34);
            kickRect = (RectTransform)kickButton.transform;
            aimKnob = UIKit.Icon(kickButton.Content, "AimKnob", ProceduralSprites.Circle, new Color(1f, 1f, 1f, 0.9f), 70f).rectTransform;
            UIKit.Icon(aimKnob, "Gloss", ProceduralSprites.Gloss, new Color(1f, 1f, 1f, 0.6f), 60f);
            var knobRim = aimKnob.gameObject.AddComponent<Outline>();
            knobRim.effectColor = new Color(0f, 0f, 0f, 0.25f);
            knobRim.effectDistance = new Vector2(2f, -2f);
            aimKnob.gameObject.AddComponent<Shadow>().effectColor = new Color(0f, 0f, 0f, 0.35f);

            // Aim meter
            var aimBg = UIKit.Panel(root, "AimMeter", new Color(0f, 0f, 0f, 0.35f), ProceduralSprites.RoundedSmall);
            aimBar = aimBg.rectTransform;
            UIKit.Place(aimBar, new Vector2(0.5f, 1f), new Vector2(0f, -170f), new Vector2(560f, 44f));
            aimFillImage = UIKit.Panel(aimBar, "Fill", UITheme.Green, ProceduralSprites.RoundedSmall);
            aimFill = aimFillImage.rectTransform;
            aimFill.anchorMin = new Vector2(0f, 0f);
            aimFill.anchorMax = new Vector2(0f, 1f);
            aimFill.pivot = new Vector2(0f, 0.5f);
            aimFill.offsetMin = new Vector2(6f, 6f);
            aimFill.offsetMax = new Vector2(6f, -6f);
            tooFar = UIKit.Title(root, "TooFar", Loc.T("hud.tooFar"), 38, Color.white);
            UIKit.Place(tooFar.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -230f), new Vector2(1200f, 60f));

            // Messages
            toast = UIKit.Title(root, "Toast", "", 64, Color.white);
            UIKit.Place(toast.rectTransform, new Vector2(0.5f, 0.74f), Vector2.zero, new Vector2(1600f, 100f));
            bigText = UIKit.Title(root, "Big", "", 150, Color.white);
            UIKit.Place(bigText.rectTransform, new Vector2(0.5f, 0.55f), Vector2.zero, new Vector2(1600f, 220f));

            // Tutorial hint card (bottom-centre, doesn't block touches)
            var hint = UIKit.Card(root, "Hint", new Color(1f, 0.97f, 0.88f, 0.96f));
            hintCard = (RectTransform)hint.transform.parent;
            // Sits above the touch buttons so it never covers them.
            UIKit.Place(hintCard, new Vector2(0.5f, 0f), new Vector2(0f, 320f), new Vector2(1100f, 170f), new Vector2(0.5f, 0f));
            hintText = UIKit.Label(hint.transform, "Text", "", 36, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(hintText.rectTransform, 24f);
            foreach (var g in hintCard.GetComponentsInChildren<Graphic>()) g.raycastTarget = false;
            hintCard.gameObject.SetActive(false);

            // Respawn fade on top of everything but the modals.
            fade = UIKit.Icon(root, "Fade", null, new Color(0f, 0f, 0f, 0f), 10f);
            UIKit.Stretch(fade.rectTransform);
            fade.preserveAspect = false;
        }

        Text Text(Transform parent, string name, int size, Vector2 pos, Vector2 sizeDelta, TextAnchor align)
        {
            var t = UIKit.Label(parent, name, "", size, UITheme.Ink, align, true);
            UIKit.Place(t.rectTransform, new Vector2(0f, 1f), pos, sizeDelta, new Vector2(0f, 0.5f));
            return t;
        }

        static void PlaceButton(RectTransform rect, Rect normalized)
        {
            rect.anchorMin = new Vector2(normalized.x, normalized.y);
            rect.anchorMax = new Vector2(normalized.xMax, normalized.yMax);
            rect.offsetMin = rect.offsetMax = Vector2.zero;
        }

        static void MakeRound(Button button)
        {
            foreach (var img in button.GetComponentsInChildren<Image>())
            {
                if (img.name == "Face" || img.name == "Shadow" || img.name == "Base") { img.sprite = ProceduralSprites.Circle; img.type = Image.Type.Simple; }
                if (img.name == "Shine") img.gameObject.SetActive(false);
            }
        }

        // ---------- Events ----------

        void OnPerfectTouch(int streak) { Toast(streak > 1 ? Loc.F("toast.perfectN", streak) : Loc.T("toast.perfect"), UITheme.Gold); }
        void OnJuggled(int count) { Toast(Loc.F("toast.juggle", count), UITheme.Gold); }
        void OnCheckpoint(Checkpoint cp) { Toast(Loc.T("toast.checkpoint"), new Color(0.55f, 1f, 0.6f)); }
        void OnBallLost(string reason) { Toast(Loc.T(reason), Late); }
        void OnBellRang() { Toast(Loc.T("toast.bell"), Late); }

        void OnGameEvent(GameEventType type, Vector2 position, float intensity)
        {
            switch (type)
            {
                case GameEventType.DogSteal: Toast(Loc.T("toast.dog"), UITheme.Gold); break;
                case GameEventType.SeagullHit: Toast(Loc.T("toast.squawk"), Color.white); break;
                case GameEventType.PedestrianBump: Toast(Loc.T("toast.oops"), Color.white); break;
                case GameEventType.GateOpened: Toast(Loc.T("toast.gate"), new Color(0.55f, 1f, 0.6f)); break;
                case GameEventType.Sticker: Toast(Loc.T("toast.sticker"), new Color(1f, 0.6f, 0.8f)); break;
            }
        }

        void OnHint(string id)
        {
            hintText.text = Loc.T("tut." + id);
            hintCard.gameObject.SetActive(true);
            var pop = hintCard.GetComponent<UIPopIn>();
            if (pop == null) pop = UIKit.PopIn(hintCard.gameObject);
            pop.Play();
            hintUntil = Time.unscaledTime + 5.5f;
        }

        void Toast(string text, Color color)
        {
            toast.text = text;
            toast.color = color;
            toast.transform.localScale = Vector3.one * 1.25f;
            toastUntil = Time.unscaledTime + 1.2f;
        }

        // ---------- Per frame ----------

        void Update()
        {
            if (root == null) return;
            UpdateInfo();
            UpdateStateScreens();
            UpdateControls();
            UpdateMessages();
            UpdateBlockers();
        }

        void UpdateInfo()
        {
            if (titleText.text.Length == 0)
                titleText.text = level.level != null ? Loc.T("level." + level.level.levelId, level.level.displayName) : Loc.T("level.test");

            int tenths = Mathf.FloorToInt(level.ElapsedTime * 10f);
            if (tenths != shownTenths)
            {
                shownTenths = tenths;
                timeText.text = FormatTime(tenths / 10f, true);
            }

            bool challenge = level.Objective != null;
            statusText.gameObject.SetActive(challenge);
            bellText.gameObject.SetActive(!challenge && level.BellEnabled);
            if (challenge)
            {
                if (Time.unscaledTime >= nextStatusRefresh)
                {
                    nextStatusRefresh = Time.unscaledTime + 0.1f;
                    statusText.text = level.Objective.StatusText;
                }
            }
            else if (level.BellEnabled)
            {
                bool late = level.BellRung;
                int bellKey = late ? -1 : Mathf.CeilToInt(level.BellTimeLeft);
                if (bellKey != shownBell)
                {
                    shownBell = bellKey;
                    bellText.text = late ? Loc.T("hud.late") : Loc.F("hud.bellIn", FormatTime(level.BellTimeLeft, false));
                    bellText.color = late ? Late : level.BellTimeLeft <= 10f ? new Color(0.85f, 0.55f, 0.1f) : UITheme.Ink;
                }
            }

            if (level.CoinsCollected != shownCoins || level.TotalCoins != shownTotal)
            {
                shownCoins = level.CoinsCollected;
                shownTotal = level.TotalCoins;
                coinText.text = shownCoins + "/" + shownTotal;
            }

            if (ball.PerfectStreak != shownStreak || ball.JuggleCount != shownJuggles)
            {
                shownStreak = ball.PerfectStreak;
                shownJuggles = ball.JuggleCount;
                streakText.text = shownStreak > 0 ? Loc.F("hud.perfect", shownStreak)
                    : shownJuggles > 0 ? Loc.F("hud.juggles", shownJuggles) : "";
            }
        }

        void UpdateStateScreens()
        {
            var state = level.State;
            if (state == lastState) return;

            if (lastState == LevelState.Paused)
            {
                if (pauseModal != null) Destroy(pauseModal);
                foreach (var name in new[] { "Settings", "ConfirmReset" })
                {
                    var leftover = root.Find(name);
                    if (leftover != null) Destroy(leftover.gameObject);
                }
            }
            if (state == LevelState.Paused) ShowPause();
            if (state == LevelState.Complete) ShowResults();
            if (state == LevelState.Intro && resultsModal != null) Destroy(resultsModal);
            if (lastState == LevelState.Intro && state == LevelState.Playing) goUntil = Time.unscaledTime + 0.6f;
            lastState = state;
        }

        void UpdateControls()
        {
            var input = GameInput.Instance;
            bool playing = level.State == LevelState.Playing;
            bool show = playing && input != null;
            jumpRect.gameObject.SetActive(show);
            kickRect.gameObject.SetActive(show);
            leftRect.gameObject.SetActive(show);
            rightRect.gameObject.SetActive(show);
            bool aiming = aimer != null && aimer.IsAiming;
            if (show)
            {
                PlaceButton(jumpRect, input.JumpButtonNormalized);
                jumpButton.SetState(input.JumpHeld, false);
                PlaceButton(leftRect, input.LeftButtonNormalized);
                leftButton.SetState(input.LeftHeld, false);
                PlaceButton(rightRect, input.RightButtonNormalized);
                rightButton.SetState(input.RightHeld, false);

                // The kick button turns green and glows while the ball is close enough to kick.
                PlaceButton(kickRect, input.KickButtonNormalized);
                kickButton.SetColor(ball.InKickReach ? KickReady : UITheme.Accent);
                kickButton.SetState(aiming || input.KickHeld, ball.InKickReach && !aiming);

                if (input.KickTapped && !ball.InKickReach) tooFarUntil = Time.unscaledTime + 1.2f;
                aimKnob.gameObject.SetActive(aiming);
                if (aiming)
                {
                    float scale = Mathf.Max(0.01f, root.lossyScale.x);
                    Vector2 drag = input.KickDrag / scale;
                    aimKnob.anchoredPosition = Vector2.ClampMagnitude(drag, 240f);
                }
            }

            aimBar.gameObject.SetActive(aiming);
            tooFar.gameObject.SetActive((aiming && !ball.InKickReach) || Time.unscaledTime < tooFarUntil);
            if (aiming)
            {
                float width = (aimBar.rect.width - 12f) * Mathf.Max(0.02f, aimer.AimPower);
                aimFill.sizeDelta = new Vector2(width, aimFill.sizeDelta.y);
                aimFillImage.color = aimer.AimIsValid ? Color.Lerp(UITheme.Green, UITheme.Red, aimer.AimPower) : UITheme.Locked;
            }
        }

        void UpdateMessages()
        {
            fade.color = new Color(0.05f, 0.04f, 0.08f, level.FadeAmount);

            float tLeft = toastUntil - Time.unscaledTime;
            toast.gameObject.SetActive(tLeft > 0f);
            if (tLeft > 0f)
            {
                Color c = toast.color;
                c.a = Mathf.Clamp01(tLeft / 0.3f);
                toast.color = c;
                toast.transform.localScale = Vector3.Lerp(toast.transform.localScale, Vector3.one, 1f - Mathf.Exp(-14f * Time.unscaledDeltaTime));
            }

            if (level.State == LevelState.Intro)
            {
                bigText.gameObject.SetActive(true);
                bigText.text = level.Objective != null && level.IntroTimeLeft > 0.35f
                    ? Loc.T("level." + (level.level != null ? level.level.levelId : "test"), level.Objective.challengeName)
                    : level.IntroTimeLeft > 0.35f ? Loc.T("hud.ready") : Loc.T("hud.go");
            }
            else if (Time.unscaledTime < goUntil)
            {
                bigText.gameObject.SetActive(true);
                bigText.text = Loc.T("hud.go");
                bigText.transform.localScale = Vector3.one * (1f + (goUntil - Time.unscaledTime) * 0.5f);
            }
            else
            {
                bigText.gameObject.SetActive(false);
                bigText.transform.localScale = Vector3.one;
            }

            if (hintCard.gameObject.activeSelf && Time.unscaledTime > hintUntil) hintCard.gameObject.SetActive(false);
        }

        void UpdateBlockers()
        {
            GameInput.UIBlockers.Clear();
            GameInput.UIBlockers.Add(ScreenRect(pauseRect));
            if (tuneRect != null) GameInput.UIBlockers.Add(ScreenRect(tuneRect));
            if (tuning != null && tuning.visible) GameInput.UIBlockers.Add(tuning.ScreenRect);
        }

        static Rect ScreenRect(RectTransform rt)
        {
            var corners = new Vector3[4];
            rt.GetWorldCorners(corners);   // overlay canvas: world space == screen pixels
            return Rect.MinMaxRect(corners[0].x, corners[0].y, corners[2].x, corners[2].y);
        }

        // ---------- Pause ----------

        void ShowPause()
        {
            var card = UIKit.Modal(root, "Pause", new Vector2(720f, 900f), out pauseModal);
            var title = UIKit.Title(card.transform, "Title", Loc.T("pause.title"), 70, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -80f), new Vector2(600f, 100f));

            float y = -200f;
            PauseButton(card.transform, ref y, "pause.resume", UITheme.Green, () => level.Resume());
            PauseButton(card.transform, ref y, "pause.checkpoint", UITheme.Blue, () => { level.Resume(); level.RespawnAtCheckpoint(); });
            PauseButton(card.transform, ref y, "pause.restart", UITheme.Accent, () => level.BeginRun());
            PauseButton(card.transform, ref y, "pause.settings", new Color(0.6f, 0.5f, 0.8f), () => SettingsPanel.Open(root, null));
            PauseButton(card.transform, ref y, "pause.quit", UITheme.Red, () => level.QuitToMap());
            if (DevTuningPanel.Available && level.NextLevel != null)
                PauseButton(card.transform, ref y, "pause.skip", UITheme.Locked, () => level.LoadNextLevel());
        }

        static void PauseButton(Transform parent, ref float y, string key, Color color, UnityEngine.Events.UnityAction action)
        {
            var b = UIKit.Button(parent, key, Loc.T(key), color, action, 40);
            UIKit.Place((RectTransform)b.transform, new Vector2(0.5f, 1f), new Vector2(0f, y), new Vector2(520f, 100f));
            y -= 120f;
        }

        // ---------- Results ----------

        void ShowResults()
        {
            var r = level.Result;
            var card = UIKit.Modal(root, "Results", new Vector2(1150f, 920f), out resultsModal);

            string heading = r.isChallenge
                ? Loc.T(r.stars > 0 ? "results.challengeDone" : "results.challengeFail")
                : Loc.T(r.beforeBell ? "results.made" : "results.late");
            var title = UIKit.Title(card.transform, "Title", heading, 68, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -80f), new Vector2(1050f, 100f));

            // Stars pop in one by one.
            for (int i = 0; i < 3; i++)
            {
                bool got = i < r.stars;
                var star = UIKit.Icon(card.transform, "Star" + i, ProceduralSprites.Star, got ? UITheme.Gold : new Color(0f, 0f, 0f, 0.12f), 150f);
                UIKit.Place(star.rectTransform, new Vector2(0.5f, 1f), new Vector2((i - 1) * 175f, -225f - (i == 1 ? 20f : 0f)), new Vector2(150f, 150f));
                if (got)
                {
                    var o = star.gameObject.AddComponent<Outline>();
                    o.effectColor = new Color(0.6f, 0.4f, 0.05f, 0.9f);
                    o.effectDistance = new Vector2(4f, -4f);
                    var pop = UIKit.PopIn(star.gameObject, 0.35f + i * 0.3f);
                    pop.fromScale = 2.2f;
                }
            }
            StartCoroutine(StarChimes(r.stars));

            float y = -360f;
            if (r.isChallenge && level.Objective != null)
            {
                var o = level.Objective;
                Line(card.transform, ref y, true, Loc.F("results.score", r.scoreText));
                for (int i = 0; i < o.starThresholds.Length && i < 3; i++)
                {
                    string need = Loc.F(o.lowerIsBetter ? "results.under" : "results.reach", o.FormatScore(o.starThresholds[i]));
                    Line(card.transform, ref y, r.stars > i, new string('*', i + 1) + "  " + need);
                }
            }
            else
            {
                int target = level.level != null ? level.level.perfectStreakTarget : 0;
                Line(card.transform, ref y, true, Loc.T("results.reached"));
                Line(card.transform, ref y, r.beforeBell, Loc.F("results.beforeBell", FormatTime(level.BellTime, false)));
                Line(card.transform, ref y, r.stars >= 3, Loc.F("results.streakCoins", target, r.coins, r.totalCoins));
            }

            var stats = UIKit.Label(card.transform, "Stats", Loc.F("results.time", FormatTime(r.time, true)) + "     " + Loc.F("results.lost", r.ballsLost),
                30, UITheme.InkSoft, TextAnchor.MiddleCenter, true);
            UIKit.Place(stats.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, y - 10f), new Vector2(1000f, 44f));

            if (level.level != null && r.stars > 0)
            {
                var coins = UIKit.CoinAmount(card.transform, "Earned", 0, 64, new Color(0.85f, 0.55f, 0.1f));
                UIKit.Place((RectTransform)coins.transform.parent, new Vector2(0.5f, 0f), new Vector2(0f, 250f), new Vector2(400f, 80f));
                var count = coins.gameObject.AddComponent<UICountUp>();
                count.target = r.coinsEarned;
                count.delay = 0.6f + r.stars * 0.3f;

                string extras = "";
                if (r.newStars > 0) extras += Loc.F("results.newStars", r.newStars) + "    ";
                if (r.stickerIsNew) extras += Loc.T("results.newSticker");
                else if (r.stickerFound) extras += Loc.T("results.oldSticker");
                var ex = UIKit.Label(card.transform, "Extras", extras, 32, new Color(0.8f, 0.35f, 0.55f), TextAnchor.MiddleCenter, true);
                UIKit.Place(ex.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 190f), new Vector2(1050f, 44f));
            }

            float bx = 0f;
            var retry = UIKit.Button(card.transform, "Retry", Loc.T("results.retry"), UITheme.Blue, () => level.BeginRun(), 40);
            UIKit.Place((RectTransform)retry.transform, new Vector2(0.5f, 0f), new Vector2(bx - 340f, 85f), new Vector2(300f, 110f));
            var map = UIKit.Button(card.transform, "Map", Loc.T("results.map"), UITheme.Paper, () => level.QuitToMap(), 40, UITheme.Ink);
            UIKit.Place((RectTransform)map.transform, new Vector2(0.5f, 0f), new Vector2(bx, 85f), new Vector2(300f, 110f));
            var next = UIKit.Button(card.transform, "Next", Loc.T(level.NextLevel != null ? "results.next" : "results.finish"), UITheme.Accent,
                () => level.LoadNextLevel(), 44);
            UIKit.Place((RectTransform)next.transform, new Vector2(0.5f, 0f), new Vector2(bx + 340f, 85f), new Vector2(300f, 110f));
            if (r.stars > 0) next.gameObject.AddComponent<UIPulse>().amount = 0.04f;
        }

        void Line(Transform parent, ref float y, bool done, string text)
        {
            var dot = UIKit.Icon(parent, "Tick", ProceduralSprites.Circle, done ? UITheme.Green : new Color(0f, 0f, 0f, 0.15f), 26f);
            UIKit.Place(dot.rectTransform, new Vector2(0.5f, 1f), new Vector2(-440f, y), new Vector2(26f, 26f));
            var label = UIKit.Label(parent, "Line", text, 32, done ? UITheme.Ink : UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(label.rectTransform, new Vector2(0.5f, 1f), new Vector2(40f, y), new Vector2(880f, 44f));
            y -= 52f;
        }

        IEnumerator StarChimes(int stars)
        {
            for (int i = 0; i < stars; i++)
            {
                float until = Time.unscaledTime + (i == 0 ? 0.45f : 0.3f);
                while (Time.unscaledTime < until) yield return null;
                AudioDirector.Play(Sfx.Perfect, 0.8f, 1f + i * 0.25f);
                Haptics.Impact(Haptics.Strength.Light);
            }
        }

        static string FormatTime(float seconds, bool tenths)
        {
            seconds = Mathf.Max(0f, seconds);
            int minutes = (int)(seconds / 60f);
            float rest = seconds - minutes * 60f;
            return tenths
                ? string.Format("{0}:{1:00.0}", minutes, rest)
                : string.Format("{0}:{1:00}", minutes, Mathf.FloorToInt(rest));
        }
    }
}
