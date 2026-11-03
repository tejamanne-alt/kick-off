using System.Collections;
using DribbleToSchool.Audio;
using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Levels;
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
    /// tutorial hints (a dismissable banner at the top), the pause menu and the animated results screen.
    /// </summary>
    public class GameHud : MonoBehaviour
    {
        public LevelManager level;
        public KidController kid;
        public BallController ball;
        public KickAimer aimer;
        public DevTuningPanel tuning;

        static readonly Color Late = new Color(0.95f, 0.4f, 0.35f);
        static readonly Color WalkColor = Color.white;
        static readonly Color KickReady = new Color(0.3f, 0.82f, 0.42f);
        static readonly Color SlideColor = new Color(0.58f, 0.4f, 0.92f);

        RectTransform root;
        Text titleText, timeText, bellText, coinText, streakText, statusText;
        Image fade;
        RectTransform jumpRect, slideRect, kickRect, leftRect, rightRect, aimKnob, aimBar, aimFill, hintCard;
        TouchButton jumpButton, slideButton, kickButton, leftButton, rightButton;
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
            // A story level is one leg of a route: under its name, where it starts and where it ends (Granny's house » Church).
            var leg = level.level != null && !level.level.isChallenge ? LegOf(level.level.levelId) : null;
            float legRoom = leg != null ? 34f : 0f;
            var info = UIKit.Card(root, "Info", UITheme.Paper);
            UIKit.Place((RectTransform)info.transform.parent, new Vector2(0f, 1f), new Vector2(30f, -30f), new Vector2(660f, 200f + legRoom), new Vector2(0f, 1f));
            var t = info.transform;
            titleText = Text(t, "Title", 34, new Vector2(30f, -38f), new Vector2(600f, 50f), TextAnchor.MiddleLeft);
            if (leg != null)
            {
                // The trip from home so far joins it on a later leg ("Home » Bakery · Trip 2:15"; UpdateInfo).
                legText = Text(t, "Leg", 26, new Vector2(30f, -74f), new Vector2(600f, 34f), TextAnchor.MiddleLeft);
                legText.color = UITheme.InkSoft;
                legText.text = legBase = leg;
                UIKit.Fit(legText, 20);
            }
            timeText = Text(t, "Time", 46, new Vector2(30f, -95f - legRoom), new Vector2(220f, 60f), TextAnchor.MiddleLeft);
            bellText = Text(t, "Bell", 34, new Vector2(250f, -95f - legRoom), new Vector2(390f, 60f), TextAnchor.MiddleLeft);
            statusText = Text(t, "Status", 32, new Vector2(250f, -95f - legRoom), new Vector2(390f, 60f), TextAnchor.MiddleLeft);
            coinText = UIKit.CoinAmount(t, "Coins", 0, 38, UITheme.Ink);
            UIKit.Place((RectTransform)coinText.transform.parent, new Vector2(0f, 1f), new Vector2(30f, -158f - legRoom), new Vector2(220f, 50f), new Vector2(0f, 0.5f));
            streakText = Text(t, "Streak", 32, new Vector2(250f, -158f - legRoom), new Vector2(390f, 50f), TextAnchor.MiddleLeft);

            // Pause button (top-right)
            var pause = UIKit.Button(root, "Pause", "", UITheme.Paper, () => level.TogglePause());
            pauseRect = (RectTransform)pause.transform;
            UIKit.Place(pauseRect, new Vector2(1f, 1f), new Vector2(-40f, -40f), new Vector2(130f, 130f), new Vector2(1f, 1f));
            UIKit.MakeRound(pause);
            UIKit.Icon(pause.transform.Find("Face"), "Icon", ProceduralSprites.Pause, UITheme.Navy, 64f);

            if (tuning != null && DevTuningPanel.Available)
            {
                var tune = UIKit.Button(root, "Tune", "Tune", UITheme.Blue, () => tuning.visible = !tuning.visible, 28);
                tuneRect = (RectTransform)tune.transform;
                UIKit.Place(tuneRect, new Vector2(1f, 1f), new Vector2(-190f, -60f), new Vector2(130f, 80f), new Vector2(1f, 1f));
            }

            // Touch controls: tinted glass discs with a thin coloured rim and soft white icons, one
            // colour per action (jump blue, slide violet, kick orange then green) so they read on sight.
            // Where they sit is GameInput's: a fan round the right thumb's rest, never in a row.
            jumpButton = TouchButton.Create(root, "JumpButton", UITheme.Blue, true);
            jumpButton.AddIcon(ProceduralSprites.ArrowUp, 0.42f, 0f, 0.6f);
            jumpButton.AddLabel(Loc.T("hud.jump"), 28);
            jumpRect = (RectTransform)jumpButton.transform;

            // Slide button, left of jump: the chevron turned down over a line of ground.
            slideButton = TouchButton.Create(root, "SlideButton", SlideColor, true);
            slideButton.AddIcon(ProceduralSprites.SlideIcon, 0.44f, 0f, 0.6f);
            slideButton.AddLabel(Loc.T("hud.slide"), 28);
            slideRect = (RectTransform)slideButton.transform;

            // Walk buttons: the chevron turned to point back / forward.
            leftButton = TouchButton.Create(root, "LeftButton", WalkColor, false);
            leftButton.AddIcon(ProceduralSprites.ArrowUp, 0.42f, 90f);
            leftRect = (RectTransform)leftButton.transform;
            rightButton = TouchButton.Create(root, "RightButton", WalkColor, false);
            rightButton.AddIcon(ProceduralSprites.ArrowUp, 0.42f, -90f);
            // A flick down on this arrow slides without letting go: a small slide glyph under the arrow says so.
            rightButton.AddIcon(ProceduralSprites.SlideIcon, 0.2f, 0f, 0.2f, new Color(1f, 1f, 1f, 0.3f));
            rightRect = (RectTransform)rightButton.transform;

            // Kick button: a ball, and a knob that follows the aiming drag.
            kickButton = TouchButton.Create(root, "KickButton", UITheme.Accent, true);
            kickButton.AddIcon(ProceduralSprites.BallIcon, 0.4f, 0f, 0.6f, new Color(1f, 1f, 1f, 0.45f));
            kickButton.AddLabel(Loc.T("hud.kick"), 28);
            kickRect = (RectTransform)kickButton.transform;
            aimKnob = UIKit.Icon(kickButton.Content, "AimKnob", ProceduralSprites.SoftEdgeDisc, new Color(1f, 1f, 1f, 0.55f), 70f).rectTransform;

            // Aim meter
            var aimBg = UIKit.Panel(root, "AimMeter", new Color(0f, 0f, 0f, 0.35f), ProceduralSprites.RoundedSmall);
            aimBar = aimBg.rectTransform;
            UIKit.Place(aimBar, new Vector2(0.5f, 1f), new Vector2(0f, -196f), new Vector2(560f, 44f));
            aimFillImage = UIKit.Panel(aimBar, "Fill", UITheme.Green, ProceduralSprites.RoundedSmall);
            aimFill = aimFillImage.rectTransform;
            aimFill.anchorMin = new Vector2(0f, 0f);
            aimFill.anchorMax = new Vector2(0f, 1f);
            aimFill.pivot = new Vector2(0f, 0.5f);
            aimFill.offsetMin = new Vector2(6f, 6f);
            aimFill.offsetMax = new Vector2(6f, -6f);
            tooFar = UIKit.Title(root, "TooFar", Loc.T("hud.tooFar"), 38, Color.white);
            UIKit.Place(tooFar.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -256f), new Vector2(1200f, 60f));

            // Messages
            toast = UIKit.Title(root, "Toast", "", 64, Color.white);
            UIKit.Place(toast.rectTransform, new Vector2(0.5f, 0.74f), Vector2.zero, new Vector2(1600f, 100f));
            bigText = UIKit.Title(root, "Big", "", 150, Color.white);
            UIKit.Place(bigText.rectTransform, new Vector2(0.5f, 0.55f), Vector2.zero, new Vector2(1600f, 220f));

            // Tutorial hint: a slim banner across the top, between the info card and the pause
            // button, clear of the play area. Tap it (or its ×) to dismiss; it also fades on its own.
            var hint = UIKit.Card(root, "Hint", new Color(1f, 1f, 1f, 0.92f));
            hintCard = (RectTransform)hint.transform.parent;
            hintCard.anchorMin = new Vector2(0f, 1f);
            hintCard.anchorMax = new Vector2(1f, 1f);
            hintCard.pivot = new Vector2(0.5f, 1f);
            hintCard.offsetMin = new Vector2(720f, -150f);
            hintCard.offsetMax = new Vector2(-200f, -34f);
            hintText = UIKit.Label(hint.transform, "Text", "", 30, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Stretch(hintText.rectTransform, 18f);
            hintText.rectTransform.offsetMin = new Vector2(28f, 10f);
            hintText.rectTransform.offsetMax = new Vector2(-96f, -10f);
            hintText.resizeTextForBestFit = true;
            hintText.resizeTextMinSize = 20;
            hintText.resizeTextMaxSize = 30;
            hintText.verticalOverflow = VerticalWrapMode.Truncate;
            foreach (var g in hintCard.GetComponentsInChildren<Graphic>()) g.raycastTarget = false;
            hint.raycastTarget = true;
            var close = UIKit.Label(hint.transform, "Close", "\u00D7", 52, UITheme.InkSoft, TextAnchor.MiddleCenter, true);
            UIKit.Place(close.rectTransform, new Vector2(1f, 0.5f), new Vector2(-48f, 2f), new Vector2(80f, 80f));
            var dismiss = hint.gameObject.AddComponent<Button>();
            dismiss.transition = Selectable.Transition.None;
            dismiss.onClick.AddListener(DismissHint);
            hintCard.gameObject.SetActive(false);

            // Respawn fade on top of everything but the modals.
            fade = UIKit.Icon(root, "Fade", null, new Color(0f, 0f, 0f, 0f), 10f);
            UIKit.Stretch(fade.rectTransform);
            fade.preserveAspect = false;
        }

        /// <summary>"Granny's house » Church": where a story level starts and where it ends (Levels/RouteTable), or null if it is on no route.</summary>
        static string LegOf(string levelId)
        {
            var from = RouteTable.From(levelId);
            var to = RouteTable.To(levelId);
            if (from == null || to == null) return null;
            return Loc.F("leg.fromTo", Loc.T(from.NameKey), Loc.T(to.NameKey));
        }

        /// <summary>Where this level ends, if that is a stop on the way rather than the school (the results then say so).</summary>
        Stop Destination
        {
            get
            {
                var to = level.level != null && !level.level.isChallenge ? RouteTable.To(level.level.levelId) : null;
                return to != null && !to.IsSchool ? to : null;
            }
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
            hintUntil = Time.unscaledTime + 8f;
        }

        void DismissHint()
        {
            hintCard.gameObject.SetActive(false);
            GameEvents.Raise(GameEventType.UIClick, Vector2.zero, 0.3f);
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

        // The leg line with the trip so far (rebuilt once a second while it shows), and the pace's colour once it gets close.
        Text legText;
        string legBase;
        int shownTrip = -1;
        static readonly Color Hurry = new Color(0.85f, 0.55f, 0.1f);

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

            if (legText != null)
            {
                int trip = level.ShowsTrip ? Mathf.FloorToInt(level.TripTime) : -1;
                if (trip != shownTrip)
                {
                    shownTrip = trip;
                    legText.text = trip < 0 ? legBase : Loc.F("leg.trip", legBase, FormatTime(trip, false));
                }
            }

            // The slot beside the clock: the school bell for the whole trip on a timed last leg, else this leg's own target.
            bool challenge = level.Objective != null;
            bool bell = !challenge && level.BellEnabled;
            bool pace = !challenge && !bell && level.PaceEnabled;
            statusText.gameObject.SetActive(challenge);
            bellText.gameObject.SetActive(bell || pace);
            if (challenge)
            {
                if (Time.unscaledTime >= nextStatusRefresh)
                {
                    nextStatusRefresh = Time.unscaledTime + 0.1f;
                    statusText.text = level.Objective.StatusText;
                }
            }
            else if (bell)
            {
                bool late = level.BellRung;
                int bellKey = late ? -1 : Mathf.CeilToInt(level.BellTimeLeft);
                if (bellKey != shownBell)
                {
                    shownBell = bellKey;
                    bellText.text = late ? Loc.T("hud.late") : Loc.F("hud.bellIn", FormatTime(level.BellTimeLeft, false));
                    bellText.color = late ? Late : level.BellTimeLeft <= 10f ? Hurry : UITheme.Ink;
                }
            }
            else if (pace)
            {
                // A target, not a bell: it never rings and never says late, only "Behind" once the leg takes longer.
                bool behind = level.PaceBehind;
                int paceKey = behind ? -2 : 1000000 + Mathf.CeilToInt(level.PaceTimeLeft);
                if (paceKey != shownBell)
                {
                    shownBell = paceKey;
                    bellText.text = behind ? Loc.T("hud.behind") : Loc.F("hud.target", FormatTime(level.PaceTimeLeft, false));
                    bellText.color = behind || level.PaceTimeLeft <= 10f ? Hurry : UITheme.Ink;
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
            slideRect.gameObject.SetActive(show);
            kickRect.gameObject.SetActive(show);
            leftRect.gameObject.SetActive(show);
            rightRect.gameObject.SetActive(show);
            bool aiming = aimer != null && aimer.IsAiming;
            if (show)
            {
                PlaceButton(jumpRect, input.JumpButtonNormalized);
                jumpButton.SetState(input.JumpHeld, false);
                // Slide glows while the kid is low under something (tap it again to keep sliding on).
                PlaceButton(slideRect, input.SlideButtonNormalized);
                slideButton.SetState(input.SlideHeld, kid != null && kid.IsLow && !kid.IsSliding);
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
            // A tap on the hint dismisses it rather than counting as a game touch.
            if (hintCard.gameObject.activeSelf) GameInput.UIBlockers.Add(ScreenRect(hintCard));
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
            UIKit.Header(card.transform, Loc.T("pause.title"), 460f);

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

        /// <summary>Has this sticker earned a Locker Room reward? (The menu hands it out.)</summary>
        bool StickerRewardWaiting()
        {
            var applier = Object.FindAnyObjectByType<Cosmetics.CosmeticApplier>();
            return applier != null && level.catalog != null && Cosmetics.StickerRewards.Pending(level.catalog, applier.catalog).Count > 0;
        }

        // The results card's rows, top to bottom: the stars hang from the header, the lines start clear of them.
        const float StarsY = -210f, LinesTop = -350f, LineStep = 52f, NoteHeight = 76f, NoteStep = 84f, BottomBlock = 345f;
        static readonly Color NoteLate = new Color(0.82f, 0.25f, 0.2f);

        void ShowResults()
        {
            var r = level.Result;
            var stop = Destination;

            // What the card says, worked out first so it can be as tall as it needs (never taller than the screen).
            var texts = new string[6];
            var dones = new bool[6];
            int count = 0;
            string note = null;
            Color noteColor = UITheme.InkSoft;
            string heading;
            bool late = !r.isChallenge && r.onRoute && r.timedTrip && !r.tripOnTime;
            if (r.isChallenge)
            {
                heading = Loc.T(r.stars > 0 ? "results.challengeDone" : "results.challengeFail");
                var o = level.Objective;
                texts[count] = Loc.F("results.score", r.scoreText); dones[count++] = true;
                for (int i = 0; o != null && i < o.starThresholds.Length && i < 3; i++)
                {
                    string need = Loc.F(o.lowerIsBetter ? "results.under" : "results.reach", o.FormatScore(o.starThresholds[i]));
                    texts[count] = new string('*', i + 1) + "  " + need; dones[count++] = r.stars > i;
                }
            }
            else
            {
                int target = level.level != null ? level.level.perfectStreakTarget : 0;
                string streakCoins = Loc.F("results.streakCoins", target, r.coins, r.totalCoins);
                if (!r.onRoute)
                {
                    // Off the routes (the test track): the level's own bell, as it always was.
                    heading = Loc.T(r.beforeBell ? "results.made" : "results.late");
                    texts[count] = Loc.T("results.reached"); dones[count++] = true;
                    texts[count] = Loc.F("results.beforeBell", FormatTime(r.tripBell, false)); dones[count++] = r.beforeBell;
                    texts[count] = streakCoins; dones[count++] = r.stars >= 3;
                }
                else if (!r.lastLeg)
                {
                    // A stop on the way: this leg's pace, and the trip so far against the school bell (no bell rings here).
                    string to = stop != null ? Loc.T(stop.ToKey) : Loc.T("place.school.to");
                    heading = Loc.F("results.madeTo", to);
                    texts[count] = Loc.F("results.reachedTo", to); dones[count++] = true;
                    if (!r.cozy) { texts[count] = Loc.F("results.pace", to, FormatTime(r.paceTarget, false)); dones[count++] = r.paceMet; }
                    texts[count] = streakCoins; dones[count++] = r.stars >= 3;
                    if (r.cozy) { texts[count] = Loc.T("results.cozy"); dones[count++] = true; }
                    else if (r.tripContinuous && r.tripBell > 0f)
                    {
                        // Green while the trip is within the legs' targets so far: on track for the bell.
                        texts[count] = Loc.F("results.tripSoFar", FormatTime(Mathf.Ceil(r.tripTime), false), FormatTime(r.tripBell, false));
                        dones[count++] = r.tripTime <= r.tripTarget;
                    }
                    else note = Loc.T("results.untimedNote");
                }
                else
                {
                    // At school: the whole trip against the bell, or (played on its own) this leg's pace.
                    heading = Loc.T(r.timedTrip ? r.tripOnTime ? "results.madeOnTime" : "results.lateSchool" : "results.made");
                    texts[count] = Loc.T("results.reached"); dones[count++] = true;
                    if (r.timedTrip)
                    {
                        texts[count] = Loc.F("results.tripBeforeBell", FormatTime(Mathf.Ceil(r.tripTime), false), FormatTime(r.tripBell, false));
                        dones[count++] = r.tripOnTime;
                    }
                    else if (!r.cozy)
                    {
                        texts[count] = Loc.F("results.pace", Loc.T("place.school.to"), FormatTime(r.paceTarget, false));
                        dones[count++] = r.paceMet;
                    }
                    texts[count] = streakCoins; dones[count++] = r.stars >= 3;
                    if (r.cozy) { texts[count] = Loc.T("results.cozy"); dones[count++] = true; }
                    if (late)
                    {
                        note = Loc.T(r.nextLocked ? "results.lateNote" : "results.lateAgain");
                        noteColor = NoteLate;
                    }
                    else if (!r.cozy && !r.timedTrip) note = Loc.T(r.nextLocked ? "results.untimedLocked" : "results.untimedNote");
                }
            }

            float contentBottom = -LinesTop + count * LineStep + (note != null ? NoteStep : 0f) + 54f;
            var card = UIKit.Modal(root, "Results", new Vector2(1150f, Mathf.Clamp(contentBottom + BottomBlock, 920f, 1000f)), out resultsModal);
            UIKit.Header(card.transform, heading, 760f);

            // Stars pop in one by one, each about its centre, the middle one a little lower.
            for (int i = 0; i < 3; i++)
            {
                bool got = i < r.stars;
                var star = UIKit.Icon(card.transform, "Star" + i, ProceduralSprites.Star, got ? UITheme.Gold : new Color(0f, 0f, 0f, 0.12f), 150f);
                UIKit.Place(star.rectTransform, new Vector2(0.5f, 1f), new Vector2((i - 1) * 175f, StarsY - (i == 1 ? 18f : 0f)), new Vector2(150f, 150f), new Vector2(0.5f, 0.5f));
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

            float y = LinesTop;
            for (int i = 0; i < count; i++) Line(card.transform, ref y, dones[i], texts[i]);
            if (note != null)
            {
                var noteText = UIKit.Label(card.transform, "Note", note, 28, noteColor, TextAnchor.MiddleCenter, true);
                UIKit.Place(noteText.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, y - 4f), new Vector2(960f, NoteHeight));
                UIKit.Fit(noteText, 22);
                y -= NoteStep;
            }

            var stats = UIKit.Label(card.transform, "Stats", Loc.F("results.time", FormatTime(r.time, true)) + "     " + Loc.F("results.lost", r.ballsLost),
                30, UITheme.InkSoft, TextAnchor.MiddleCenter, true);
            UIKit.Place(stats.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, y - 10f), new Vector2(1000f, 44f));

            if (level.level != null && r.stars > 0)
            {
                var coins = UIKit.CoinAmount(card.transform, "Earned", 0, 64, new Color(0.85f, 0.55f, 0.1f));
                UIKit.Place((RectTransform)coins.transform.parent, new Vector2(0.5f, 0f), new Vector2(0f, 250f), new Vector2(400f, 80f));
                var countUp = coins.gameObject.AddComponent<UICountUp>();
                countUp.target = r.coinsEarned;
                countUp.delay = 0.6f + r.stars * 0.3f;

                string extras = "";
                if (r.newStars > 0) extras += Loc.F("results.newStars", r.newStars) + "    ";
                if (r.stickerIsNew) extras += Loc.T(StickerRewardWaiting() ? "results.stickerReward" : "results.newSticker");
                else if (r.stickerFound) extras += Loc.T("results.oldSticker");
                var ex = UIKit.Label(card.transform, "Extras", extras, 32, new Color(0.8f, 0.35f, 0.55f), TextAnchor.MiddleCenter, true);
                UIKit.Place(ex.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 190f), new Vector2(1050f, 44f));
            }

            // The buttons. When a route's last leg leaves the next stage shut (late, or untimed and never on time), the way on is to walk
            // the whole trip again from home: that is the main button, and Next only stays if the next level can be played anyway.
            bool fromHome = !r.isChallenge && r.onRoute && r.lastLeg && !r.cozy && (late || r.nextLocked) && level.TripStart != null;
            var nextLevel = level.NextLevel;
            bool showNext = !fromHome || (!r.nextLocked && nextLevel != null);
            int buttons = 2 + (fromHome ? 1 : 0) + (showNext ? 1 : 0);
            float width = buttons > 3 ? 250f : 300f, step = buttons > 3 ? 270f : 340f;
            int slot = 0;
            var retry = UIKit.Button(card.transform, "Retry", Loc.T("results.retry"), UITheme.Blue, () => level.BeginRun(), 40);
            PlaceResultButton(retry, slot++, buttons, width, step);
            var map = UIKit.Button(card.transform, "Map", Loc.T("results.map"), UITheme.Paper, () => level.QuitToMap(), 40, UITheme.Ink);
            PlaceResultButton(map, slot++, buttons, width, step);
            if (showNext)
            {
                var next = UIKit.Button(card.transform, "Next", Loc.T(nextLevel != null ? "results.next" : "results.finish"), fromHome ? UITheme.Green : UITheme.Accent,
                    () => level.LoadNextLevel(), 44);
                PlaceResultButton(next, slot++, buttons, width, step);
                if (r.stars > 0 && !fromHome) next.gameObject.AddComponent<UIPulse>().amount = 0.04f;
            }
            if (fromHome)
            {
                var home = UIKit.Button(card.transform, "FromHome", Loc.T("results.fromHome"), UITheme.Accent, () => level.LoadTripStart(), 44);
                PlaceResultButton(home, slot++, buttons, width, step);
                home.gameObject.AddComponent<UIPulse>().amount = 0.04f;
            }
        }

        /// <summary>The results' buttons in a row along the bottom of the card, centred, <paramref name="step"/> apart.</summary>
        static void PlaceResultButton(Button button, int slot, int count, float width, float step)
        {
            float x = (slot - (count - 1) * 0.5f) * step;
            UIKit.Place((RectTransform)button.transform, new Vector2(0.5f, 0f), new Vector2(x, 85f), new Vector2(width, 110f));
        }

        void Line(Transform parent, ref float y, bool done, string text)
        {
            // The dot is centred on its line; a long line (a translation) shrinks to fit rather than run into the next.
            var dot = UIKit.Icon(parent, "Tick", ProceduralSprites.Circle, done ? UITheme.Green : new Color(0f, 0f, 0f, 0.15f), 26f);
            UIKit.Place(dot.rectTransform, new Vector2(0.5f, 1f), new Vector2(-440f, y - 9f), new Vector2(26f, 26f));
            var label = UIKit.Label(parent, "Line", text, 32, done ? UITheme.Ink : UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(label.rectTransform, new Vector2(0.5f, 1f), new Vector2(40f, y), new Vector2(880f, 44f));
            UIKit.Fit(label, 22);
            y -= LineStep;
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
