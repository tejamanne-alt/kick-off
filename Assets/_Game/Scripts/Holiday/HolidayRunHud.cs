using System;
using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// The Holiday Run's screen (uGUI built from code, the sibling of the story levels' GameHud): the score
    /// card with the combo ring, the stage ribbon that settles into a tag over a thin day bar, the power-up
    /// timers, toasts, Ready / GO / OOPS, the touch buttons, the pause button, and the pause and results
    /// menus (HolidayRunPanels). It only reads the director and calls its actions.
    ///
    /// Layout is in the 1080-tall canvas. The cards sit in the safe area; the touch buttons are placed from
    /// GameInput's own rects. The corners keep to fixed sizes: the score card top left, the pause button
    /// and the power-up timers top right. The middle strip (the ribbon, the tag, the day bar and, under
    /// them, the chapter banner) is as wide as the room beside the score card allows, so on a 4:3 tablet it
    /// narrows to still clear it. Toasts hang above the kid, clear of the KICK button that sits right of
    /// the middle. Texts are rebuilt only when the number behind them changes, so nothing is allocated per frame.
    /// </summary>
    public class HolidayRunHud : MonoBehaviour
    {
        public HolidayRunDirector director;

        // ---- look ----

        /// <summary>The chapters' colours, as the chapter map has them (Editor/GeneratedContent.Chapters).</summary>
        static readonly Color[] ChapterColors =
        {
            new Color(0.97f, 0.55f, 0.27f), new Color(0.9f, 0.42f, 0.42f), new Color(0.3f, 0.68f, 0.85f),
            new Color(0.55f, 0.48f, 0.72f), new Color(0.42f, 0.7f, 0.4f),
        };

        /// <summary>The combo chip's colour for x1 .. x5: quiet at first, warmer as it builds.</summary>
        static readonly Color[] ComboColors =
        {
            new Color(0.6f, 0.68f, 0.8f), UITheme.Green, new Color(0.3f, 0.6f, 1f), UITheme.Epic, UITheme.Accent,
        };

        static readonly string[] ComboLabels = { "x1", "x2", "x3", "x4", "x5" };
        static readonly string[] StageNumbers = Numbers(HolidayStages.Count);

        static readonly Color KickReady = new Color(0.3f, 0.82f, 0.42f);
        static readonly Color BestGold = new Color(0.86f, 0.56f, 0.06f);
        static readonly Color ChipDisc = new Color(0.1f, 0.16f, 0.34f, 0.92f);
        static readonly Color OopsColor = new Color(1f, 0.5f, 0.45f);

        // ---- layout (canvas pixels) ----

        const float Margin = 30f;
        const float CardWidth = 500f, CardHeight = 214f, ComboSize = 104f;
        const float PauseSize = 118f;
        const float ChipSize = 92f, ChipGap = 14f;
        const float TagHeight = 58f, RibbonHeight = 104f, BarHeight = 24f, BarGap = 14f;
        /// <summary>
        /// The middle strip (ribbon, tag, day bar) is 540 px wide on a phone, and narrows to as little as 320 on a 4:3
        /// tablet to keep <see cref="StripGap"/> clear of the score card on its left.
        /// </summary>
        const float StripMin = 320f, StripMax = 540f, StripGap = 30f;
        /// <summary>The chapter banner hangs under the day bar, the width of the middle strip.</summary>
        const float BannerTop = Margin + RibbonHeight + BarGap + BarHeight + 12f, BannerHeight = 116f;
        /// <summary>
        /// Toast lines hang from this far down the screen, <see cref="ToastStep"/> apart, centred this far across it
        /// (over the kid): below the score card even on a 4:3 screen, left of the KICK button, above the kid's head.
        /// </summary>
        const float ToastTop = 330f, ToastStep = 62f, ToastWidth = 560f, ToastHeight = 66f, ToastAcross = 0.3f;

        // ---- timing (seconds) ----

        const float RibbonHold = 3f, RibbonFold = 0.4f, RibbonLife = RibbonHold + RibbonFold;
        const float BannerLife = 3.2f, SplashLife = 2.4f, ToastLife = 1.5f, HintLife = 4.5f;
        const int ToastLines = 3, MaxQueuedToasts = 12;

        /// <summary>One power-up timer: a disc with the icon, ringed by what is left.</summary>
        sealed class PowerChip
        {
            public PowerUpKind kind;
            public RectTransform root;
            public Image fill;
            public CanvasGroup group;
            public float popStart = -10f;
            public bool shown;
            public float duration;
        }

        struct ToastItem { public int line; public float born, life; }
        struct PendingToast { public string text; public Color color; public float life; }

        // ---- the built screen ----

        RectTransform root, safe;
        RunPhase shownPhase = (RunPhase)(-1);

        // controls
        RectTransform controls;
        CanvasGroup controlsGroup;
        TouchButton jumpButton, kickButton;
        RectTransform jumpRect, kickRect;
        Text jumpLabel, kickLabel;
        // the left thumb's walk stick, and the kick's aim (as in the levels)
        StickView stick;
        RectTransform aimKnob, aimBar, aimFill;
        Image aimFillImage;
        Text tooFar;
        float tooFarUntil;

        // balls left
        RectTransform ballsRow;
        Image[] ballIcons;
        int shownBalls = -1;
        float ballsPop = -100f;

        // score card
        Text scoreText, distanceText, coinText, bestText, comboText;
        RectTransform coinRow, comboChip;
        Image comboFill, newBestChip;
        Text newBestLabel;

        // power-ups
        readonly PowerChip[] chips = new PowerChip[3];

        // stage tag, ribbon, day bar, chapter banner, day splash
        RectTransform tagRect, ribbonRect, bannerRect, barRect, markerRect, splashRect, pauseRect;
        Image tagCard, tagDayChip, ribbonBand, ribbonStripe, bannerBand, bannerStripe;
        Text tagNumber, tagName, tagDay, ribbonNumber, ribbonStage, ribbonName, bannerCaption, bannerTitle, splashTitle, splashSub;
        CanvasGroup ribbonGroup, bannerGroup;
        readonly Image[] segments = new Image[HolidayStages.Count];

        // messages
        readonly Text[] toastTexts = new Text[ToastLines];
        readonly ToastItem[] toasts = new ToastItem[ToastLines];   // [0] is the newest
        readonly Queue<PendingToast> toastQueue = new Queue<PendingToast>();
        int toastCount;
        Text bigText, quietText;
        Image fade;

        GameObject pauseModal, resultsModal;

        // ---- what is shown (text is only rebuilt when these change) ----

        int shownScore = -1, shownMetres = -1, shownCoins = -1, shownCombo, shownBest = -1, shownStage = -1, shownDay = -1, chipMask = -1, lastScore;
        float displayedScore, nextScoreText, lastFade = -1f, lastBarTop = -1f, lastMarker = -1f;
        bool lastFadeDark;
        float stripWidth;
        int shownScreenWidth, shownScreenHeight;
        Rect shownSafeArea;
        bool shownBeating;
        string shownBig, shownQuiet, textReady, textGo, textGetReady, textOops;

        // ---- animation clocks (unscaled seconds) ----

        float scorePop = -10f, coinPop = -10f, comboPop = -10f;
        float ribbonStart = -100f, bannerStart = -100f, splashStart = -100f, goUntil, crashStart = -10f;
        float pendingAt = -1f;
        int pendingStage, pendingDay;
        float ribbonPresence;

        static readonly Vector3[] corners = new Vector3[4];

        void Start()
        {
            if (director == null) director = HolidayRunDirector.Current;
            if (director == null) director = FindAnyObjectByType<HolidayRunDirector>();
            if (director == null)
            {
                Debug.LogError("[Holiday Run] The HUD needs its director: rebuild the Holiday Run.");
                enabled = false;
                return;
            }

            Build();
            director.PhaseChanged += OnPhaseChanged;
            director.StageChanged += OnStageChanged;
            director.DayStarted += OnDayStarted;
            director.Toast += OnToast;
            director.Hint += OnHint;
            director.PowerUpCollected += OnPowerUp;
            Loc.Changed += OnLanguageChanged;
            // The Controls page's tour button plays the tour here and now.
            ControlsTour.Replay = ReplayTour;
            // The director's own Start has already chosen the first phase (it runs before this one).
            OnPhaseChanged(director.Phase);
        }

        void ReplayTour()
        {
            var level = director.level;
            if (level == null) return;
            if (level.State == LevelState.Paused) level.Resume();
            ControlsTour.Begin(root, level, pauseRect);
        }

        void OnDestroy()
        {
            if (director != null)
            {
                director.PhaseChanged -= OnPhaseChanged;
                director.StageChanged -= OnStageChanged;
                director.DayStarted -= OnDayStarted;
                director.Toast -= OnToast;
                director.Hint -= OnHint;
                director.PowerUpCollected -= OnPowerUp;
            }
            Loc.Changed -= OnLanguageChanged;
            if (ControlsTour.Replay == (System.Action)ReplayTour) ControlsTour.Replay = null;
            GameInput.UIBlockers.Clear();
        }

        // ================================================================ build

        void Build()
        {
            var canvas = UIKit.CreateCanvas("HolidayHUD", 10);
            root = (RectTransform)canvas.transform;
            CacheTexts();
            stripWidth = StripWidth();
            shownScreenWidth = Screen.width;
            shownScreenHeight = Screen.height;
            shownSafeArea = Screen.safeArea;

            // The touch buttons go first (underneath) and fill the whole screen: GameInput gives their
            // rects in screen terms, and they keep clear of notches themselves.
            BuildControls();

            // Everything else keeps inside the safe area.
            safe = UIKit.Stretch(UIKit.Rect(root, "SafeArea"));
            safe.gameObject.AddComponent<UISafeArea>();
            BuildCard();
            BuildBalls();
            BuildPowerUps();
            BuildTag();
            BuildDayBar();
            BuildRibbon();
            BuildBanner();
            BuildToasts();
            BuildAim();
            BuildPauseButton();

            BuildCentreText();
            BuildFade();
            BuildSplash();
        }

        void CacheTexts()
        {
            textReady = Loc.T("hud.ready");
            textGo = Loc.T("hud.go");
            textGetReady = Loc.T("holiday.getReady");
            textOops = Loc.T("holiday.oops");
        }

        void BuildControls()
        {
            controls = UIKit.Stretch(UIKit.Rect(root, "Controls"));
            controlsGroup = controls.gameObject.AddComponent<CanvasGroup>();
            controlsGroup.alpha = 0f;
            controlsGroup.interactable = false;
            controlsGroup.blocksRaycasts = false;
            controls.gameObject.SetActive(false);

            // The same stick and glass discs as the story levels, one colour per action; where they sit is GameInput's.
            stick = StickView.Create(controls, "WalkStick");

            jumpButton = TouchButton.Create(controls, "JumpButton", UITheme.Blue, true);
            jumpButton.AddIcon(ProceduralSprites.JumpIcon, 0.46f, 0f, 0.58f);
            jumpLabel = jumpButton.AddLabel(Loc.T("hud.jump"), 28);
            UIKit.Fit(jumpLabel, 14);
            jumpRect = (RectTransform)jumpButton.transform;

            kickButton = TouchButton.Create(controls, "KickButton", UITheme.Accent, true);
            kickButton.AddIcon(ProceduralSprites.BallIcon, 0.4f, 0f, 0.6f, new Color(1f, 1f, 1f, 0.45f));
            kickLabel = kickButton.AddLabel(Loc.T("hud.kick"), 28);
            UIKit.Fit(kickLabel, 14);
            kickRect = (RectTransform)kickButton.transform;
            // The knob that follows the aiming drag.
            aimKnob = UIKit.Icon(kickButton.Content, "AimKnob", ProceduralSprites.SoftEdgeDisc, new Color(1f, 1f, 1f, 0.55f), 70f).rectTransform;
            aimKnob.gameObject.SetActive(false);
        }

        /// <summary>The aim meter and the "too far" line shown while a kick is aimed (as in the levels), just under the stage banner.</summary>
        void BuildAim()
        {
            var bar = UIKit.Panel(safe, "AimMeter", new Color(0f, 0f, 0f, 0.3f), ProceduralSprites.RoundedSmall);
            aimBar = bar.rectTransform;
            UIKit.Place(aimBar, new Vector2(0.5f, 1f), new Vector2(0f, -318f), new Vector2(520f, 40f));
            aimFillImage = UIKit.Panel(aimBar, "Fill", UITheme.Green, ProceduralSprites.RoundedSmall);
            aimFill = aimFillImage.rectTransform;
            aimFill.anchorMin = new Vector2(0f, 0f);
            aimFill.anchorMax = new Vector2(0f, 1f);
            aimFill.pivot = new Vector2(0f, 0.5f);
            aimFill.offsetMin = new Vector2(6f, 6f);
            aimFill.offsetMax = new Vector2(6f, -6f);
            aimBar.gameObject.SetActive(false);
            tooFar = UIKit.Title(safe, "TooFar", Loc.T("hud.tooFar"), 36, Color.white);
            UIKit.Place(tooFar.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -366f), new Vector2(1100f, 56f));
            tooFar.gameObject.SetActive(false);
        }

        /// <summary>The balls left, as little footballs under the score card (the dimmed ones are gone).</summary>
        void BuildBalls()
        {
            int count = Mathf.Clamp(director.MaxBalls, 0, 8);
            ballsRow = UIKit.Rect(safe, "Balls");
            UIKit.Place(ballsRow, new Vector2(0f, 1f), new Vector2(Margin + 8f, -(Margin + CardHeight + 12f)), new Vector2(Mathf.Max(60f, count * 56f), 50f), new Vector2(0f, 1f));
            ballIcons = new Image[count];
            for (int i = 0; i < count; i++)
            {
                var icon = UIKit.Icon(ballsRow, "Ball" + i, ProceduralSprites.BallIcon, Color.white, 46f);
                var rt = icon.rectTransform;
                rt.anchorMin = rt.anchorMax = new Vector2(0f, 0.5f);
                rt.pivot = new Vector2(0f, 0.5f);
                rt.sizeDelta = new Vector2(46f, 46f);
                rt.anchoredPosition = new Vector2(i * 56f, 0f);
                ballIcons[i] = icon;
            }
            ballsRow.gameObject.SetActive(count > 0);
        }

        /// <summary>The card at the top left: score, combo ring, distance, coins, and the best score to beat.</summary>
        void BuildCard()
        {
            var face = UIKit.Card(safe, "Card", UITheme.Paper);
            var card = (RectTransform)face.transform.parent;
            UIKit.Place(card, new Vector2(0f, 1f), new Vector2(Margin, -Margin), new Vector2(CardWidth, CardHeight), new Vector2(0f, 1f));
            var t = face.transform;

            scoreText = UIKit.Label(t, "Score", "0", 78, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(scoreText.rectTransform, new Vector2(0f, 1f), new Vector2(24f, -8f), new Vector2(340f, 104f), new Vector2(0f, 1f));
            UIKit.Fit(scoreText, 44);

            // The combo: a chip with a ring that fills toward the next step.
            comboChip = UIKit.Rect(t, "Combo");
            UIKit.Place(comboChip, new Vector2(1f, 1f), new Vector2(-20f, -12f), new Vector2(ComboSize, ComboSize), new Vector2(1f, 1f));
            UIKit.Stretch(UIKit.Icon(comboChip, "Disc", ProceduralSprites.CircleEdge, ChipDisc, ComboSize).rectTransform);
            UIKit.Stretch(UIKit.Icon(comboChip, "Track", Art.Ring, new Color(1f, 1f, 1f, 0.2f), ComboSize).rectTransform, 5f);
            comboFill = UIKit.Icon(comboChip, "Fill", Art.Ring, ComboColors[0], ComboSize);
            UIKit.Stretch(comboFill.rectTransform, 5f);
            MakeRadial(comboFill, true);
            comboText = UIKit.Label(comboChip, "Value", ComboLabels[0], 44, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(comboText.rectTransform, 14f);
            UIKit.Fit(comboText, 26);

            distanceText = UIKit.Label(t, "Distance", "0 m", 38, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(distanceText.rectTransform, new Vector2(0f, 1f), new Vector2(24f, -110f), new Vector2(210f, 48f), new Vector2(0f, 1f));
            UIKit.Fit(distanceText, 24);

            coinText = UIKit.CoinAmount(t, "Coins", 0, 38, UITheme.Ink);
            coinRow = (RectTransform)coinText.transform.parent;
            UIKit.Place(coinRow, new Vector2(0f, 1f), new Vector2(250f, -110f), new Vector2(220f, 48f), new Vector2(0f, 1f));
            coinRow.GetComponent<HorizontalLayoutGroup>().childAlignment = TextAnchor.MiddleLeft;

            bestText = UIKit.Label(t, "Best", "", 28, UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(bestText.rectTransform, new Vector2(0f, 1f), new Vector2(24f, -164f), new Vector2(290f, 40f), new Vector2(0f, 1f));
            UIKit.Fit(bestText, 18);

            // Shown once this run is past the best score.
            newBestChip = UIKit.Panel(t, "NewBest", UITheme.Gold, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Place(newBestChip.rectTransform, new Vector2(1f, 1f), new Vector2(-18f, -164f), new Vector2(176f, 40f), new Vector2(1f, 1f));
            newBestChip.raycastTarget = false;
            newBestLabel = UIKit.Label(newBestChip.transform, "Text", Loc.T("holiday.newBest"), 24, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(newBestLabel.rectTransform, 4f);
            UIKit.Fit(newBestLabel, 14);
            var pulse = newBestChip.gameObject.AddComponent<UIPulse>();
            pulse.amount = 0.05f;
            pulse.speed = 6f;
            newBestChip.gameObject.SetActive(false);
        }

        /// <summary>A ring that fills like a clock from the top, the way the timers drain.</summary>
        static void MakeRadial(Image image, bool clockwise)
        {
            image.preserveAspect = false;
            image.type = Image.Type.Filled;
            image.fillMethod = Image.FillMethod.Radial360;
            image.fillOrigin = (int)Image.Origin360.Top;
            image.fillClockwise = clockwise;
            image.fillAmount = 0f;
        }

        /// <summary>The three timers under the pause button, side by side from the right, and only while their power-up is on.</summary>
        void BuildPowerUps()
        {
            var kinds = new[] { PowerUpKind.Magnet, PowerUpKind.Shield, PowerUpKind.Turbo };
            for (int i = 0; i < kinds.Length; i++)
            {
                var chip = new PowerChip { kind = kinds[i], duration = Mathf.Max(0.1f, HolidayRunDirector.Duration(kinds[i])) };
                Color color = PowerUp.ColorOf(chip.kind);
                chip.root = UIKit.Rect(safe, "PowerUp_" + chip.kind);
                UIKit.Place(chip.root, new Vector2(1f, 1f), Vector2.zero, new Vector2(ChipSize, ChipSize), new Vector2(1f, 1f));
                chip.group = chip.root.gameObject.AddComponent<CanvasGroup>();
                UIKit.Stretch(UIKit.Icon(chip.root, "Disc", ProceduralSprites.CircleEdge, ChipDisc, ChipSize).rectTransform);
                UIKit.Stretch(UIKit.Icon(chip.root, "Track", Art.Ring, new Color(color.r, color.g, color.b, 0.25f), ChipSize).rectTransform, 5f);
                chip.fill = UIKit.Icon(chip.root, "Fill", Art.Ring, color, ChipSize);
                UIKit.Stretch(chip.fill.rectTransform, 5f);
                MakeRadial(chip.fill, true);
                var icon = UIKit.Icon(chip.root, "Icon", PowerUp.IconOf(chip.kind), Color.Lerp(color, Color.white, 0.15f), ChipSize * 0.5f);
                icon.rectTransform.anchoredPosition = Vector2.zero;
                chip.root.gameObject.SetActive(false);
                chips[i] = chip;
            }
        }

        /// <summary>
        /// The width of the middle strip: all the room between the score card and its mirror image on the other
        /// side of the screen's middle, up to <see cref="StripMax"/>. (The canvas is 1080 tall and as wide as the
        /// screen's shape makes it: 1440 at 4:3, 1920 at 16:9.)
        /// </summary>
        static float StripWidth()
        {
            float width = Mathf.Max(1, Screen.width), height = Mathf.Max(1, Screen.height);
            float canvasWidth = UIKit.ReferenceResolution.y * width / height;
            float safeWidth = canvasWidth * Mathf.Clamp01(Screen.safeArea.width / width);
            return Mathf.Clamp(safeWidth - 2f * (Margin + CardWidth + StripGap), StripMin, StripMax);
        }

        /// <summary>
        /// A strip across the top middle, <paramref name="top"/> pixels down and <paramref name="height"/> tall.
        /// Its pivot is the top middle, so scaling it (the ribbon's pop) keeps it hanging from the same place.
        /// </summary>
        void TopCentre(RectTransform rt, float top, float height)
        {
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.sizeDelta = new Vector2(stripWidth, height);
            rt.anchoredPosition = new Vector2(0f, -top);
        }

        /// <summary>The screen changed shape (a window resized, a phone turned over): size the middle strip again.</summary>
        void ResizeStrip()
        {
            shownScreenWidth = Screen.width;
            shownScreenHeight = Screen.height;
            shownSafeArea = Screen.safeArea;
            stripWidth = StripWidth();
            tagRect.sizeDelta = new Vector2(stripWidth, tagRect.sizeDelta.y);
            ribbonRect.sizeDelta = new Vector2(stripWidth, ribbonRect.sizeDelta.y);
            barRect.sizeDelta = new Vector2(stripWidth, barRect.sizeDelta.y);
            bannerRect.sizeDelta = new Vector2(stripWidth, bannerRect.sizeDelta.y);
        }

        /// <summary>The small tag that says which stage this is: the number, the name, and the day once past the first.</summary>
        void BuildTag()
        {
            tagRect = UIKit.Rect(safe, "StageTag");
            TopCentre(tagRect, Margin, TagHeight);
            tagCard = UIKit.Card(tagRect, "Card", Color.white);
            UIKit.Stretch((RectTransform)tagCard.transform.parent);
            var t = tagCard.transform;

            var badge = UIKit.Icon(t, "Badge", ProceduralSprites.CircleEdge, Color.white, 42f);
            UIKit.Place(badge.rectTransform, new Vector2(0f, 0.5f), new Vector2(10f, 0f), new Vector2(42f, 42f), new Vector2(0f, 0.5f));
            tagNumber = UIKit.Label(badge.transform, "Number", "1", 26, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(tagNumber.rectTransform, 2f);
            UIKit.Fit(tagNumber, 16);

            // Two lines are allowed, for the longer names in Spanish on a narrow screen.
            tagName = UIKit.Label(t, "Name", "", 30, Color.white, TextAnchor.MiddleLeft, true);
            UIKit.Stretch(tagName.rectTransform);
            tagName.rectTransform.offsetMin = new Vector2(60f, 3f);
            tagName.rectTransform.offsetMax = new Vector2(-88f, -3f);
            UIKit.Fit(tagName, 16);
            AddDrop(tagName);

            tagDayChip = UIKit.Panel(t, "Day", UITheme.Gold, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Place(tagDayChip.rectTransform, new Vector2(1f, 0.5f), new Vector2(-8f, 0f), new Vector2(76f, 34f), new Vector2(1f, 0.5f));
            tagDayChip.raycastTarget = false;
            tagDay = UIKit.Label(tagDayChip.transform, "Text", "", 22, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(tagDay.rectTransform, 2f);
            UIKit.Fit(tagDay, 12);
            tagDayChip.gameObject.SetActive(false);
        }

        /// <summary>The day in 23 ticks, one a stage in its chapter's colour, with the kid's place on them and the school at the end.</summary>
        void BuildDayBar()
        {
            barRect = UIKit.Rect(safe, "DayBar");
            TopCentre(barRect, Margin + TagHeight + BarGap, BarHeight);
            var back = UIKit.Panel(barRect, "Back", new Color(0.05f, 0.09f, 0.24f, 0.5f), ProceduralSprites.RoundedSmall);
            UIKit.Stretch(back.rectTransform);
            back.raycastTarget = false;

            var track = UIKit.Rect(barRect, "Track");
            UIKit.Stretch(track);
            track.offsetMin = new Vector2(8f, 6f);
            track.offsetMax = new Vector2(-44f, -6f);
            for (int i = 0; i < segments.Length; i++)
            {
                var segment = UIKit.Icon(track, "Stage" + i, null, Color.white, 10f);
                var rt = segment.rectTransform;
                rt.anchorMin = new Vector2(i / (float)segments.Length, 0f);
                rt.anchorMax = new Vector2((i + 1) / (float)segments.Length, 1f);
                rt.offsetMin = new Vector2(1f, 0f);
                rt.offsetMax = new Vector2(-1f, 0f);
                segments[i] = segment;
            }

            // The kid's place: the ball, riding on the ticks.
            var marker = UIKit.Icon(track, "Kid", ProceduralSprites.BallIcon, Color.white, 32f);
            markerRect = marker.rectTransform;
            markerRect.anchorMin = markerRect.anchorMax = new Vector2(0f, 0.5f);
            markerRect.anchoredPosition = Vector2.zero;
            var school = UIKit.Icon(barRect, "School", Art.School, Color.white, 34f);
            UIKit.Place(school.rectTransform, new Vector2(1f, 0.5f), new Vector2(-6f, 2f), new Vector2(34f, 34f), new Vector2(1f, 0.5f));
        }

        /// <summary>The big stage ribbon that pops in over the tag: the stage, its name, the day, in the chapter's colour.</summary>
        void BuildRibbon()
        {
            ribbonRect = UIKit.Rect(safe, "StageRibbon");
            TopCentre(ribbonRect, Margin, RibbonHeight);
            ribbonGroup = ribbonRect.gameObject.AddComponent<CanvasGroup>();
            ribbonGroup.blocksRaycasts = false;

            ribbonStripe = Band(ribbonRect, "Stripe", 12f, -9f);
            ribbonBand = Band(ribbonRect, "Band", 0f, 0f);

            var badge = UIKit.Icon(ribbonRect, "Badge", ProceduralSprites.CircleEdge, Color.white, 68f);
            UIKit.Place(badge.rectTransform, new Vector2(0f, 0.5f), new Vector2(22f, 0f), new Vector2(68f, 68f), new Vector2(0f, 0.5f));
            ribbonNumber = UIKit.Label(badge.transform, "Number", "1", 42, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(ribbonNumber.rectTransform, 4f);
            UIKit.Fit(ribbonNumber, 22);

            ribbonStage = UIKit.Label(ribbonRect, "Stage", "", 26, new Color(1f, 1f, 1f, 0.9f), TextAnchor.MiddleLeft, true);
            Between(ribbonStage.rectTransform, 0.62f, 0.95f);
            UIKit.Fit(ribbonStage, 14);
            AddDrop(ribbonStage);
            ribbonName = UIKit.Label(ribbonRect, "Name", "", 46, Color.white, TextAnchor.MiddleLeft, true);
            Between(ribbonName.rectTransform, 0.04f, 0.66f);
            UIKit.Fit(ribbonName, 22);
            AddDrop(ribbonName);
            ribbonRect.gameObject.SetActive(false);
        }

        /// <summary>The line across a ribbon between two heights (0 bottom, 1 top), clear of the number badge.</summary>
        static void Between(RectTransform rt, float from, float to)
        {
            rt.anchorMin = new Vector2(0f, from);
            rt.anchorMax = new Vector2(1f, to);
            rt.offsetMin = new Vector2(104f, 0f);
            rt.offsetMax = new Vector2(-26f, 0f);
        }

        /// <summary>A slanted band (UIKit.Header's ribbon), offset by (<paramref name="dx"/>, <paramref name="dy"/>) for the stripe behind it.</summary>
        static Image Band(RectTransform parent, string name, float dx, float dy)
        {
            var band = UIKit.Panel(parent, name, Color.white, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Stretch(band.rectTransform);
            band.rectTransform.offsetMin += new Vector2(dx, dy);
            band.rectTransform.offsetMax += new Vector2(dx, dy);
            band.gameObject.AddComponent<UISkew>().skew = 0.32f;
            band.raycastTarget = false;
            return band;
        }

        /// <summary>The chapter's name, under the day bar when a chapter begins.</summary>
        void BuildBanner()
        {
            bannerRect = UIKit.Rect(safe, "ChapterBanner");
            TopCentre(bannerRect, BannerTop, BannerHeight);
            bannerGroup = bannerRect.gameObject.AddComponent<CanvasGroup>();
            bannerGroup.blocksRaycasts = false;
            bannerStripe = Band(bannerRect, "Stripe", 14f, -10f);
            bannerBand = Band(bannerRect, "Band", 0f, 0f);

            bannerCaption = UIKit.Label(bannerRect, "Caption", "", 30, new Color(1f, 1f, 1f, 0.9f), TextAnchor.MiddleCenter, true);
            bannerCaption.rectTransform.anchorMin = new Vector2(0f, 0.66f);
            bannerCaption.rectTransform.anchorMax = new Vector2(1f, 0.97f);
            bannerCaption.rectTransform.offsetMin = new Vector2(40f, 0f);
            bannerCaption.rectTransform.offsetMax = new Vector2(-40f, 0f);
            UIKit.Fit(bannerCaption, 18);
            AddDrop(bannerCaption);
            bannerTitle = UIKit.Label(bannerRect, "Title", "", 74, Color.white, TextAnchor.MiddleCenter, true);
            bannerTitle.rectTransform.anchorMin = new Vector2(0f, 0.03f);
            bannerTitle.rectTransform.anchorMax = new Vector2(1f, 0.70f);
            bannerTitle.rectTransform.offsetMin = new Vector2(40f, 0f);
            bannerTitle.rectTransform.offsetMax = new Vector2(-40f, 0f);
            UIKit.Fit(bannerTitle, 26);
            AddDrop(bannerTitle);
            bannerRect.gameObject.SetActive(false);
        }

        /// <summary>Lettering that reads over any background: a dark drop under it.</summary>
        static void AddDrop(Text text)
        {
            var shadow = text.gameObject.AddComponent<Shadow>();
            shadow.effectColor = new Color(0f, 0.02f, 0.12f, 0.45f);
            shadow.effectDistance = new Vector2(0f, -3f);
        }

        void BuildToasts()
        {
            for (int i = 0; i < ToastLines; i++)
            {
                var toast = UIKit.Title(safe, "Toast" + i, "", 52, Color.white);
                UIKit.Place(toast.rectTransform, new Vector2(ToastAcross, 1f), new Vector2(0f, -ToastTop - i * ToastStep), new Vector2(ToastWidth, ToastHeight), new Vector2(0.5f, 1f));
                UIKit.Fit(toast, 30);   // a long one in Spanish gets smaller rather than wider than the room beside the card
                toast.gameObject.SetActive(false);
                toastTexts[i] = toast;
            }
        }

        void BuildPauseButton()
        {
            var pause = UIKit.Button(safe, "Pause", "", UITheme.Paper, director.TogglePause);
            pauseRect = (RectTransform)pause.transform;
            UIKit.Place(pauseRect, new Vector2(1f, 1f), new Vector2(-Margin, -Margin), new Vector2(PauseSize, PauseSize), new Vector2(1f, 1f));
            UIKit.MakeRound(pause);
            UIKit.Icon(pause.transform.Find("Face"), "Icon", ProceduralSprites.Pause, UITheme.Navy, 60f);
        }

        void BuildCentreText()
        {
            bigText = UIKit.Title(root, "Big", "", 150, Color.white);
            UIKit.Place(bigText.rectTransform, new Vector2(0.5f, 0.52f), Vector2.zero, new Vector2(1600f, 220f));
            bigText.gameObject.SetActive(false);

            // While the first stages load: not a countdown, just a quiet word.
            quietText = UIKit.Label(root, "GetReady", "", 56, new Color(1f, 1f, 1f, 0.95f), TextAnchor.MiddleCenter, true);
            UIKit.Place(quietText.rectTransform, new Vector2(0.5f, 0.52f), Vector2.zero, new Vector2(1200f, 90f));
            var outline = quietText.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(0.05f, 0.08f, 0.2f, 0.8f);
            outline.effectDistance = new Vector2(3f, -3f);
            quietText.gameObject.SetActive(false);
        }

        /// <summary>The white the screen goes to between one day and the next.</summary>
        void BuildFade()
        {
            fade = UIKit.Icon(root, "Fade", null, new Color(1f, 1f, 1f, 0f), 10f);
            UIKit.Stretch(fade.rectTransform);
            fade.preserveAspect = false;
            fade.enabled = false;
        }

        /// <summary>"DAY 2" across the screen as a new day begins, on top of the fading white.</summary>
        void BuildSplash()
        {
            splashRect = UIKit.Rect(root, "DaySplash");
            UIKit.Place(splashRect, new Vector2(0.5f, 0.5f), new Vector2(0f, 40f), new Vector2(1300f, 360f));
            splashTitle = UIKit.Title(splashRect, "Title", "", 180, Color.white);
            UIKit.Place(splashTitle.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, 40f), new Vector2(1300f, 260f));
            splashSub = UIKit.Label(splashRect, "Sub", "", 54, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(splashSub.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, -110f), new Vector2(1200f, 80f));
            var outline = splashSub.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(0.05f, 0.08f, 0.2f, 0.85f);
            outline.effectDistance = new Vector2(3f, -3f);
            splashRect.gameObject.SetActive(false);
        }

        // ================================================================ events

        void OnPhaseChanged(RunPhase phase)
        {
            var previous = shownPhase;
            shownPhase = phase;
            float now = Time.unscaledTime;

            if (previous == RunPhase.Paused && phase != RunPhase.Paused) ClosePause();
            if (previous == RunPhase.Results && phase != RunPhase.Results) CloseResults();
            // The pause button has nothing to do once the run is over (the results menu is the way out).
            pauseRect.gameObject.SetActive(phase != RunPhase.Crashed && phase != RunPhase.Results);

            switch (phase)
            {
                case RunPhase.Ready:
                    ClearAnnouncements();
                    break;
                case RunPhase.Running:
                    // Off the start line (not back from a pause or a revive): GO!, then say where we are.
                    if (previous == RunPhase.Ready)
                    {
                        goUntil = now + 0.6f;
                        pendingStage = director.StageIndex;
                        pendingDay = director.Day;
                        pendingAt = now + 0.7f;
                    }
                    break;
                case RunPhase.Paused:
                    pauseModal = HolidayRunPanels.OpenPause(root, director);
                    break;
                case RunPhase.Crashed:
                    crashStart = now;
                    break;
                case RunPhase.Results:
                    int chimes;
                    resultsModal = HolidayRunPanels.OpenResults(root, director, out chimes);
                    StartCoroutine(HolidayRunPanels.Chimes(resultsModal, chimes));
                    break;
            }
        }

        void OnStageChanged(int stage, int day)
        {
            // Across the white of a new day the ribbon would be hidden: wait for the screen to clear.
            pendingStage = stage;
            pendingDay = day;
            pendingAt = Time.unscaledTime + (director.Fade > 0.05f ? 0.5f : 0f);
        }

        void OnDayStarted(int day)
        {
            splashStart = Time.unscaledTime;
            splashTitle.text = Loc.F("holiday.day", day);
            splashSub.text = Loc.T("holiday.dayFaster");
            splashRect.gameObject.SetActive(true);
        }

        void OnToast(string text, Color color)
        {
            AddToast(text, color, ToastLife);
        }

        /// <summary>A how-to-play tip (the first run only): a toast that stays long enough to read.</summary>
        void OnHint(string text)
        {
            AddToast(text, new Color(1f, 0.95f, 0.72f), HintLife);
        }

        void AddToast(string text, Color color, float life)
        {
            if (string.IsNullOrEmpty(text)) return;
            if (toastCount < ToastLines && toastQueue.Count == 0) ShowToast(text, color, Time.unscaledTime, life);
            else if (toastQueue.Count < MaxQueuedToasts) toastQueue.Enqueue(new PendingToast { text = text, color = color, life = life });
        }

        void OnPowerUp(PowerUpKind kind)
        {
            int index = (int)kind;
            if (index >= 0 && index < chips.Length) chips[index].popStart = Time.unscaledTime;
        }

        /// <summary>The language changed (from Settings in the pause menu): redo the words that were built already.</summary>
        void OnLanguageChanged()
        {
            CacheTexts();
            jumpLabel.text = Loc.T("hud.jump");
            kickLabel.text = Loc.T("hud.kick");
            tooFar.text = Loc.T("hud.tooFar");
            newBestLabel.text = Loc.T("holiday.newBest");
            shownBest = shownStage = -1;   // the best line, the tag and the day bar are rebuilt next frame
            shownBig = shownQuiet = null;
            if (pauseModal != null)
            {
                // Rebuilt in the same place in the stack, below the settings panel that is still open.
                int index = pauseModal.transform.GetSiblingIndex();
                Destroy(pauseModal);
                pauseModal = HolidayRunPanels.OpenPause(root, director);
                pauseModal.transform.SetSiblingIndex(index);
            }
        }

        void ClosePause()
        {
            if (pauseModal != null) Destroy(pauseModal);
            pauseModal = null;
            // The settings panel (and its erase-progress question) are opened on top of the pause menu.
            foreach (string name in new[] { "Settings", "ConfirmReset", "ControlsGuide" })
            {
                var leftover = root.Find(name);
                if (leftover != null) Destroy(leftover.gameObject);
            }
        }

        void CloseResults()
        {
            if (resultsModal != null) Destroy(resultsModal);
            resultsModal = null;
        }

        /// <summary>A new run: nothing of the last one is left on the screen.</summary>
        void ClearAnnouncements()
        {
            pendingAt = -1f;
            ribbonStart = bannerStart = splashStart = -100f;
            goUntil = 0f;
            ribbonPresence = 0f;
            ribbonRect.gameObject.SetActive(false);
            bannerRect.gameObject.SetActive(false);
            splashRect.gameObject.SetActive(false);
            for (int i = 0; i < ToastLines; i++) toastTexts[i].gameObject.SetActive(false);
            toastCount = 0;
            toastQueue.Clear();
            displayedScore = 0f;
            lastScore = 0;
            shownCombo = 0;
        }

        // ================================================================ per frame

        void Update()
        {
            if (root == null || director == null) return;
            float now = Time.unscaledTime, dt = Time.unscaledDeltaTime;
            if (Screen.width != shownScreenWidth || Screen.height != shownScreenHeight || Screen.safeArea != shownSafeArea) ResizeStrip();
            // A first run (nothing played yet): the guided tour of the controls at the start line, once the street is in.
            var held = director.level;
            if (held != null && held.State == LevelState.Intro && !held.Held && !director.Loading && ControlsTour.ShouldStart)
                ControlsTour.Begin(root, held, pauseRect);
            UpdateCard(now, dt);
            UpdateStage();
            UpdatePowerUps(now);
            UpdateAnnouncements(now);
            UpdateToasts(now, dt);
            UpdateCentreText(now);
            UpdateFade();
            UpdateControls(dt);
            UpdateBalls(now);
            UpdateBlockers();
        }

        void UpdateCard(float now, float dt)
        {
            // The score counts up toward the real one, a little behind it, so a bonus rolls in rather than jumps.
            int score = director.Score;
            if (score < displayedScore) displayedScore = score;
            else if (score > displayedScore)
            {
                if (score - lastScore >= 90) scorePop = now;
                displayedScore = Mathf.MoveTowards(displayedScore, score, Mathf.Max(40f, (score - displayedScore) * 9f) * dt);
            }
            lastScore = score;
            int shown = Mathf.RoundToInt(displayedScore);
            if (shown != shownScore && (now >= nextScoreText || shown == score))
            {
                shownScore = shown;
                nextScoreText = now + 0.04f;   // at most 25 new numbers a second
                scoreText.text = Num(shown);
            }
            SetScale(scoreText.rectTransform, 1f + 0.14f * (1f - Ease(Since(scorePop, 0.3f))));

            int metres = (int)director.Distance;
            if (metres != shownMetres)
            {
                shownMetres = metres;
                distanceText.text = Num(metres) + " m";
            }

            int coins = director.Coins;
            if (coins != shownCoins)
            {
                if (shownCoins >= 0 && coins > shownCoins) coinPop = now;
                shownCoins = coins;
                coinText.text = Num(coins);
            }
            SetScale(coinRow, 1f + 0.18f * (1f - Ease(Since(coinPop, 0.3f))));

            // The combo chip: x1 to x5, its ring filling toward the next step.
            int combo = Mathf.Clamp(director.Multiplier, 1, ComboColors.Length);
            if (combo != shownCombo)
            {
                if (shownCombo > 0 && combo > shownCombo) comboPop = now;
                shownCombo = combo;
                comboText.text = ComboLabels[combo - 1];
                comboFill.color = ComboColors[combo - 1];
            }
            comboFill.fillAmount = Mathf.Clamp01(director.MultiplierProgress);
            float comboScale = 1f + 0.3f * (1f - Ease(Since(comboPop, 0.4f)));
            if (combo >= ComboColors.Length) comboScale += 0.04f * Mathf.Sin(now * 6f);   // at the top: a restless chip
            SetScale(comboChip, comboScale);

            // The best score to beat. It is read from the save as well, because the director only
            // reads it once, when the scene starts, and a run in the same scene must beat the last one.
            int best = Mathf.Max(director.BestScore, SaveSystem.Data.holidayBestScore);
            if (best != shownBest)
            {
                shownBest = best;
                bestText.text = best > 0 ? Loc.F("holiday.best", Num(best)) : "";
            }
            bool beating = best > 0 && director.NewBest && score > best;
            if (beating != shownBeating)
            {
                shownBeating = beating;
                bestText.color = beating ? BestGold : UITheme.InkSoft;
                newBestChip.gameObject.SetActive(beating);
            }
        }

        void UpdateStage()
        {
            int stage = Mathf.Clamp(director.StageIndex, 0, HolidayStages.Count - 1), day = director.Day;
            if (stage != shownStage || day != shownDay)
            {
                shownStage = stage;
                shownDay = day;
                RefreshDayBar();
                RefreshTag();
            }

            float t = Mathf.Clamp01((stage + Mathf.Clamp01(director.StageProgress)) / HolidayStages.Count);
            if (Mathf.Abs(t - lastMarker) > 0.0005f)
            {
                lastMarker = t;
                markerRect.anchorMin = markerRect.anchorMax = new Vector2(t, 0.5f);
            }

            // The day bar hangs under the ribbon while it is up, and under the small tag after.
            float top = Margin + Mathf.Lerp(TagHeight, RibbonHeight, ribbonPresence) + BarGap;
            if (Mathf.Abs(top - lastBarTop) > 0.25f)
            {
                lastBarTop = top;
                barRect.anchoredPosition = new Vector2(0f, -top);
            }
        }

        /// <summary>The ticks the kid has passed are bright, this stage's is almost, the rest are dim.</summary>
        void RefreshDayBar()
        {
            for (int i = 0; i < segments.Length; i++)
            {
                Color color = ChapterColors[ChapterOf(i) - 1];
                color.a = i < shownStage ? 1f : i == shownStage ? 0.9f : 0.32f;
                segments[i].color = color;
            }
        }

        void RefreshTag()
        {
            tagCard.color = Color.Lerp(ChapterColors[ChapterOf(shownStage) - 1], UITheme.Navy, 0.5f);
            tagNumber.text = StageNumbers[shownStage];
            tagName.text = StageName(shownStage);
            bool later = shownDay > 1;
            tagDayChip.gameObject.SetActive(later);
            if (later) tagDay.text = Loc.F("holiday.day", shownDay);
        }

        void UpdatePowerUps(float now)
        {
            var phase = director.Phase;
            bool live = phase == RunPhase.Running || phase == RunPhase.Paused || phase == RunPhase.Crashed;
            int mask = 0;
            for (int i = 0; i < chips.Length; i++)
            {
                var chip = chips[i];
                float left = TimeLeft(chip.kind);
                bool on = live && left > 0f;
                if (on) mask |= 1 << i;
                if (on != chip.shown)
                {
                    chip.shown = on;
                    chip.root.gameObject.SetActive(on);
                }
                if (!on) continue;
                chip.fill.fillAmount = Mathf.Clamp01(left / chip.duration);
                // The shield flickers over its last three seconds, like the glow round the kid.
                bool flicker = chip.kind == PowerUpKind.Shield && left <= 3f && Mathf.Repeat(now * 6f, 1f) < 0.35f;
                chip.group.alpha = flicker ? 0.3f : 1f;
                SetScale(chip.root, 1f + 0.35f * (1f - Ease(Since(chip.popStart, 0.35f))));
            }
            if (mask != chipMask)
            {
                chipMask = mask;
                int slot = 0;
                for (int i = 0; i < chips.Length; i++)
                {
                    if ((mask & (1 << i)) == 0) continue;
                    chips[i].root.anchoredPosition = new Vector2(-Margin - slot * (ChipSize + ChipGap), -(Margin + PauseSize + 26f));
                    slot++;
                }
            }
        }

        float TimeLeft(PowerUpKind kind)
        {
            switch (kind)
            {
                case PowerUpKind.Shield: return director.ShieldLeft;
                case PowerUpKind.Turbo: return director.TurboLeft;
                default: return director.MagnetLeft;
            }
        }

        // ================================================================ the stage ribbon, chapter banner and day splash

        void UpdateAnnouncements(float now)
        {
            if (pendingAt >= 0f && now >= pendingAt)
            {
                pendingAt = -1f;
                Announce(pendingStage, pendingDay, now);
            }

            // The ribbon pops in, holds, then folds away into the small tag underneath.
            float age = now - ribbonStart;
            bool ribbonOn = age >= 0f && age < RibbonLife;
            if (ribbonRect.gameObject.activeSelf != ribbonOn) ribbonRect.gameObject.SetActive(ribbonOn);
            ribbonPresence = 0f;
            if (ribbonOn)
            {
                float fold = Mathf.Clamp01((age - RibbonHold) / RibbonFold);
                float alpha = Mathf.Clamp01(age / 0.12f) * (1f - fold);
                ribbonPresence = 1f - fold;
                ribbonGroup.alpha = alpha;
                SetScale(ribbonRect, Mathf.LerpUnclamped(0.6f, 1f, EaseOutBack(age / 0.35f)) * (1f - 0.18f * fold));
            }

            // The chapter's name, for a little longer than the ribbon.
            age = now - bannerStart;
            bool bannerOn = age >= 0f && age < BannerLife;
            if (bannerRect.gameObject.activeSelf != bannerOn) bannerRect.gameObject.SetActive(bannerOn);
            if (bannerOn)
            {
                bannerGroup.alpha = Mathf.Clamp01(age / 0.12f) * Mathf.Clamp01((BannerLife - age) / 0.5f);
                SetScale(bannerRect, Mathf.LerpUnclamped(0.75f, 1f, EaseOutBack(age / 0.4f)));
            }

            // "DAY 2": big, shrinking onto the screen, then gone.
            age = now - splashStart;
            bool splashOn = age >= 0f && age < SplashLife;
            if (splashRect.gameObject.activeSelf != splashOn) splashRect.gameObject.SetActive(splashOn);
            if (splashOn)
            {
                float alpha = Mathf.Clamp01(age / 0.1f) * Mathf.Clamp01((SplashLife - age) / 0.5f);
                SetAlpha(splashTitle, alpha);
                SetAlpha(splashSub, alpha);
                SetScale(splashRect, Mathf.LerpUnclamped(1.6f, 1f, EaseOutBack(age / 0.4f)));
            }
        }

        /// <summary>Show the ribbon for this stage, and the chapter's banner when it is the first stage of a chapter.</summary>
        void Announce(int stage, int day, float now)
        {
            if (stage < 0 || stage >= HolidayStages.Count) return;
            int chapter = ChapterOf(stage);
            Color color = ChapterColors[chapter - 1];

            ribbonStripe.color = color;
            ribbonBand.color = Color.Lerp(color, UITheme.Navy, 0.55f);
            ribbonNumber.text = StageNumbers[stage];
            string label = Loc.F("holiday.stage", stage + 1);
            ribbonStage.text = day > 1 ? label + "   ·   " + Loc.F("holiday.day", day) : label;
            ribbonName.text = StageName(stage);
            ribbonStart = now;
            ribbonPresence = 1f;

            bool firstOfChapter = stage == 0 || ChapterOf(stage - 1) != chapter;
            if (firstOfChapter)
            {
                bannerStripe.color = color;
                bannerBand.color = Color.Lerp(color, UITheme.Navy, 0.45f);
                bannerCaption.text = Loc.F("holiday.chapterN", chapter);
                bannerTitle.text = Loc.T("chapter." + chapter).ToUpperInvariant();
                bannerStart = now;
            }
        }

        static int ChapterOf(int stage)
        {
            return Mathf.Clamp(HolidayStages.All[Mathf.Clamp(stage, 0, HolidayStages.Count - 1)].chapter, 1, ChapterColors.Length);
        }

        static string StageName(int stage)
        {
            return Loc.T("level." + HolidayStages.All[Mathf.Clamp(stage, 0, HolidayStages.Count - 1)].levelId).ToUpperInvariant();
        }

        // ================================================================ toasts

        /// <summary>
        /// Put a message on the first free line and push the older ones down (the newest is on top). When every
        /// line is busy the message waits in the queue, so none is lost.
        /// </summary>
        void ShowToast(string text, Color color, float now, float life)
        {
            int line = -1;
            for (int k = 0; k < ToastLines && line < 0; k++)
            {
                bool used = false;
                for (int i = 0; i < toastCount; i++)
                    if (toasts[i].line == k) used = true;
                if (!used) line = k;
            }
            if (line < 0) return;
            for (int i = toastCount; i > 0; i--) toasts[i] = toasts[i - 1];
            toasts[0] = new ToastItem { line = line, born = now, life = life };
            toastCount++;

            var label = toastTexts[line];
            label.text = text;
            label.color = color;
            label.rectTransform.anchoredPosition = new Vector2(0f, -ToastTop);
            label.gameObject.SetActive(true);
        }

        void UpdateToasts(float now, float dt)
        {
            // The oldest is the last in the list: when its time is up its line is free for the next.
            while (toastCount > 0 && now - toasts[toastCount - 1].born >= toasts[toastCount - 1].life)
            {
                toastTexts[toasts[toastCount - 1].line].gameObject.SetActive(false);
                toastCount--;
            }
            while (toastCount < ToastLines && toastQueue.Count > 0)
            {
                var next = toastQueue.Dequeue();
                ShowToast(next.text, next.color, now, next.life);
            }

            float follow = 1f - Mathf.Exp(-16f * dt);
            for (int i = 0; i < toastCount; i++)
            {
                var label = toastTexts[toasts[i].line];
                float age = now - toasts[i].born;
                var rt = label.rectTransform;
                rt.anchoredPosition = Vector2.Lerp(rt.anchoredPosition, new Vector2(0f, -ToastTop - i * ToastStep), follow);
                SetScale(rt, 1f + 0.3f * (1f - Ease(Since(toasts[i].born, 0.18f))));
                SetAlpha(label, Mathf.Clamp01((toasts[i].life - age) / 0.3f));
            }
        }

        // ================================================================ Ready, GO, OOPS

        void UpdateCentreText(float now)
        {
            string big = null, quiet = null;
            Color bigColor = Color.white;
            float scale = 1f;
            switch (director.Phase)
            {
                case RunPhase.Ready:
                    if (director.level != null && director.level.Held) break;   // the controls tour is on
                    if (director.Loading) quiet = textGetReady;
                    else big = director.IntroTimeLeft > 0.35f ? textReady : textGo;
                    break;
                case RunPhase.Running:
                    if (now < goUntil)
                    {
                        big = textGo;
                        scale = 1f + (goUntil - now) * 0.5f;
                    }
                    break;
                case RunPhase.Crashed:
                    big = textOops;
                    bigColor = OopsColor;
                    scale = 1f + 0.5f * (1f - Ease(Since(crashStart, 0.3f)));
                    break;
            }

            if (big != shownBig)
            {
                shownBig = big;
                bigText.gameObject.SetActive(big != null);
                if (big != null) bigText.text = big;
            }
            if (big != null)
            {
                if (bigText.color != bigColor) bigText.color = bigColor;
                SetScale(bigText.rectTransform, scale);
            }
            if (quiet != shownQuiet)
            {
                shownQuiet = quiet;
                quietText.gameObject.SetActive(quiet != null);
                if (quiet != null) quietText.text = quiet;
            }
        }

        /// <summary>White across the day change; dark for the moment a lost ball goes back to the checkpoint (as in a level).</summary>
        void UpdateFade()
        {
            float white = Mathf.Clamp01(director.Fade);
            float dark = director.level != null ? Mathf.Clamp01(director.level.FadeAmount) : 0f;
            float amount = Mathf.Max(white, dark);
            bool isDark = dark > white;
            if (Mathf.Abs(amount - lastFade) < 0.002f && isDark == lastFadeDark) return;
            lastFade = amount;
            lastFadeDark = isDark;
            fade.color = isDark ? new Color(0.05f, 0.04f, 0.08f, amount) : new Color(1f, 1f, 1f, amount);
            fade.enabled = amount > 0.002f;
        }

        // ================================================================ the touch buttons

        void UpdateControls(float dt)
        {
            var input = GameInput.Instance;
            var level = director.level;
            // Shown while running, and while the controls tour holds the run (the player tries them under its light).
            bool show = input != null && level != null && (level.Held || (director.Phase == RunPhase.Running && level.State == LevelState.Playing));
            controlsGroup.alpha = Mathf.MoveTowards(controlsGroup.alpha, show ? 1f : 0f, dt * 5f);
            bool visible = controlsGroup.alpha > 0.001f;
            if (controls.gameObject.activeSelf != visible) controls.gameObject.SetActive(visible);
            if (!show)
            {
                // A finger still down when the run ended must not leave a button looking pressed.
                jumpButton.SetState(false, false);
                kickButton.SetState(false, false);
                stick.Release();
                aimKnob.gameObject.SetActive(false);
                aimBar.gameObject.SetActive(false);
                tooFar.gameObject.SetActive(false);
                return;
            }

            var kid = director.kid;
            var ball = director.ball;
            var aimer = director.aimer;
            PlaceButton(jumpRect, input.JumpButtonNormalized);
            jumpButton.SetState(input.JumpHeld, false);
            stick.Show(input.StickRingNormalized, input.StickKnob, input.StickKnobScale, input.StickActive, input.MoveAxis, input.SlideHeld);

            // The kick button turns green and glows while the ball is close enough to kick.
            bool aiming = aimer != null && aimer.IsAiming;
            bool inReach = ball != null && ball.InKickReach;
            PlaceButton(kickRect, input.KickButtonNormalized);
            kickButton.SetColor(inReach ? KickReady : UITheme.Accent);
            kickButton.SetState(aiming || input.KickHeld, inReach && !aiming);

            if (input.KickTapped && !inReach) tooFarUntil = Time.unscaledTime + 1.2f;
            aimKnob.gameObject.SetActive(aiming);
            if (aiming)
            {
                float scale = Mathf.Max(0.01f, root.lossyScale.x);
                aimKnob.anchoredPosition = Vector2.ClampMagnitude(input.KickDrag / scale, 240f);
            }
            aimBar.gameObject.SetActive(aiming);
            tooFar.gameObject.SetActive((aiming && !inReach) || Time.unscaledTime < tooFarUntil);
            if (aiming)
            {
                float width = (aimBar.rect.width - 12f) * Mathf.Max(0.02f, aimer.AimPower);
                aimFill.sizeDelta = new Vector2(width, aimFill.sizeDelta.y);
                aimFillImage.color = aimer.AimIsValid ? Color.Lerp(UITheme.Green, UITheme.Red, aimer.AimPower) : UITheme.Locked;
            }
        }

        /// <summary>The footballs under the card: the ones still to lose are solid, the lost ones faint; the one just lost pops.</summary>
        void UpdateBalls(float now)
        {
            if (ballIcons == null || ballIcons.Length == 0) return;
            int left = director.BallsLeft;
            if (left != shownBalls)
            {
                if (shownBalls >= 0 && left < shownBalls) ballsPop = now;
                shownBalls = left;
            }
            float pop = 1f - Ease(Since(ballsPop, 0.4f));
            for (int i = 0; i < ballIcons.Length; i++)
            {
                bool have = i < left;
                ballIcons[i].color = new Color(1f, 1f, 1f, have ? 1f : 0.25f);
                SetScale(ballIcons[i].rectTransform, i == left && pop > 0f ? 1f + 0.5f * pop : 1f);
            }
        }

        static void PlaceButton(RectTransform rect, Rect normalized)
        {
            rect.anchorMin = new Vector2(normalized.x, normalized.y);
            rect.anchorMax = new Vector2(normalized.xMax, normalized.yMax);
            rect.offsetMin = rect.offsetMax = Vector2.zero;
        }

        /// <summary>A touch that starts on the pause button is the button's, not a jump.</summary>
        void UpdateBlockers()
        {
            GameInput.UIBlockers.Clear();
            if (pauseRect.gameObject.activeInHierarchy) GameInput.UIBlockers.Add(ScreenRect(pauseRect));
        }

        static Rect ScreenRect(RectTransform rt)
        {
            rt.GetWorldCorners(corners);   // overlay canvas: world space == screen pixels
            return Rect.MinMaxRect(corners[0].x, corners[0].y, corners[2].x, corners[2].y);
        }

        // ================================================================ small helpers

        static string Num(int n)
        {
            return n.ToString("N0");
        }

        static string[] Numbers(int count)
        {
            var numbers = new string[count];
            for (int i = 0; i < count; i++) numbers[i] = (i + 1).ToString();
            return numbers;
        }

        /// <summary>0..1 over <paramref name="seconds"/> since <paramref name="start"/>.</summary>
        static float Since(float start, float seconds)
        {
            return Mathf.Clamp01((Time.unscaledTime - start) / seconds);
        }

        /// <summary>1 at the start, easing to 0 (for a pop that settles).</summary>
        static float Ease(float t)
        {
            return t * (2f - t);
        }

        /// <summary>A springy 0..1 that overshoots a little on the way (the same ease as UIPopIn).</summary>
        static float EaseOutBack(float t)
        {
            if (t <= 0f) return 0f;
            if (t >= 1f) return 1f;
            const float s = 1.70158f;
            return 1f + (s + 1f) * Mathf.Pow(t - 1f, 3f) + s * Mathf.Pow(t - 1f, 2f);
        }

        static void SetScale(RectTransform rt, float scale)
        {
            if (Mathf.Abs(rt.localScale.x - scale) > 0.001f) rt.localScale = Vector3.one * scale;
        }

        /// <summary>Fade a text through its colour (rather than a CanvasGroup), which the logo lettering's many layers need to fade as one.</summary>
        static void SetAlpha(Text text, float alpha)
        {
            Color c = text.color;
            if (Mathf.Abs(c.a - alpha) < 0.004f) return;
            c.a = alpha;
            text.color = c;
        }

        // ================================================================ shapes the kit doesn't have

        /// <summary>The few sprites this screen draws for itself, made once.</summary>
        static class Art
        {
            static Sprite ring, school;

            /// <summary>A thick ring, for the combo and power-up timers (it fills like a clock).</summary>
            public static Sprite Ring
            {
                get
                {
                    return ring != null ? ring : (ring = Shape(128, (u, v) =>
                    {
                        float r = Mathf.Sqrt(u * u + v * v);
                        return Mathf.Clamp01((0.98f - r) * 30f) * Mathf.Clamp01((r - 0.72f) * 30f);
                    }));
                }
            }

            /// <summary>The school at the end of the day: a low building with a tower and a pitched roof, door, windows and clock cut out.</summary>
            public static Sprite School
            {
                get
                {
                    return school != null ? school : (school = Shape(96, (u, v) =>
                    {
                        bool body = Mathf.Abs(u) < 0.9f && v > -0.8f && v < -0.05f;
                        bool tower = Mathf.Abs(u) < 0.3f && v >= -0.05f && v < 0.45f;
                        bool roof = v >= 0.45f && v < 0.95f && Mathf.Abs(u) < (0.95f - v) * 0.7f;
                        if (!body && !tower && !roof) return 0f;
                        bool door = Mathf.Abs(u) < 0.15f && v < -0.35f;
                        bool window = Mathf.Abs(Mathf.Abs(u) - 0.58f) < 0.14f && v > -0.5f && v < -0.22f;
                        bool clock = u * u + (v - 0.2f) * (v - 0.2f) < 0.11f * 0.11f;
                        return door || window || clock ? 0f : 1f;
                    }));
                }
            }

            /// <summary>A white shape from an alpha function over (-1..1, -1..1), smoothed by 2x2 supersampling.</summary>
            static Sprite Shape(int size, Func<float, float, float> alpha)
            {
                var texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
                var pixels = new Color32[size * size];
                float d = 0.5f / size;
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                        float a = (alpha(u - d, v - d) + alpha(u + d, v - d) + alpha(u - d, v + d) + alpha(u + d, v + d)) * 0.25f;
                        pixels[y * size + x] = new Color32(255, 255, 255, (byte)Mathf.RoundToInt(Mathf.Clamp01(a) * 255f));
                    }
                }
                texture.SetPixels32(pixels);
                texture.wrapMode = TextureWrapMode.Clamp;
                texture.Apply();
                return Sprite.Create(texture, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect);
            }
        }
    }
}
