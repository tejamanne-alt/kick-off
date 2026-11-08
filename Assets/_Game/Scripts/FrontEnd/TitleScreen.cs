using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The launch screen. The left column holds the logo, PLAY, HOLIDAY RUN (the endless mode) beside CO-OP (racing friends
    /// nearby over Bluetooth, FrontEnd/CoopScreen) and the
    /// Locker Room, Stickers and Settings buttons; the rest of the screen is the live street, where
    /// the menu's camera puts the chosen teen juggling (tap them, or the player card in the corner,
    /// to switch between the boy and the girl). Credits and the stars collected sit along the bottom
    /// left. Sizes are in the 1080-tall canvas inside the safe area, so the column fits from 4:3 to 21:9.
    /// </summary>
    public class TitleScreen : FrontEndScreen
    {
        /// <summary>Width of the left column (canvas pixels): the logo and the buttons.</summary>
        const float Column = 740f;

        /// <summary>The height the left column is laid out for (the canvas is 1080 units tall).</summary>
        const float DesignHeight = 1080f;

        /// <summary>HOLIDAY RUN and CO-OP share PLAY's row below it: each this wide, their centres this far either side of the column's.</summary>
        const float ModeWidth = 330f, ModeHalfStep = 172f;

        /// <summary>HOLIDAY RUN's button: turquoise, a holiday sea beside PLAY's sunny orange.</summary>
        static readonly Color HolidayColor = new Color(0.16f, 0.72f, 0.82f);
        /// <summary>CO-OP's button: a friendly violet beside HOLIDAY RUN.</summary>
        static readonly Color CoopColor = new Color(0.55f, 0.38f, 0.88f);

        Text starsLabel;
        Text holidayLabel, holidayBest;
        RectTransform teenSpot;
        Image playerPortrait;
        Text playerName;

        protected override void Build(RectTransform root)
        {
            // The left column is laid out for the full 1080-unit height (logo, PLAY, HOLIDAY RUN, the three buttons,
            // credits and stars), and shrinks from its top left corner when the safe area is shorter (a phone's home bar),
            // so its rows can never overlap or run off the bottom.
            var column = UIKit.Rect(root, "Column");
            column.anchorMin = column.anchorMax = new Vector2(0f, 1f);
            column.pivot = new Vector2(0f, 1f);
            column.anchoredPosition = Vector2.zero;
            column.sizeDelta = new Vector2(Column + 40f, DesignHeight);
            column.gameObject.AddComponent<UIFitHeight>().designHeight = DesignHeight;

            var logo = KickOffLogo.Build(column, 0.86f);
            UIKit.Place(logo, new Vector2(0f, 1f), new Vector2(Column * 0.5f + 20f, -300f), logo.sizeDelta, new Vector2(0.5f, 0.5f));
            UIKit.PopIn(logo.gameObject);

            var play = UIKit.Button(column, "Play", Loc.T("menu.play"), UITheme.Accent, () => Controller.Show(FrontEndScreenId.Map), 68);
            UIKit.Place((RectTransform)play.transform, new Vector2(0f, 1f), new Vector2(Column * 0.5f + 20f, -604f), new Vector2(450f, 136f), new Vector2(0.5f, 0.5f));
            UIKit.PopIn(play.gameObject, 0.15f);
            play.gameObject.AddComponent<UIPulse>().amount = 0.025f;

            // HOLIDAY RUN and CO-OP side by side under PLAY. HOLIDAY RUN's label is built by hand below, so that the best distance
            // can sit on the button once there is one.
            var holiday = UIKit.Button(column, "Holiday", "", HolidayColor, StartHolidayRun, 42);
            UIKit.Place((RectTransform)holiday.transform, new Vector2(0f, 1f), new Vector2(Column * 0.5f + 20f - ModeHalfStep, -744f), new Vector2(ModeWidth, 112f), new Vector2(0.5f, 0.5f));
            UIKit.PopIn(holiday.gameObject, 0.19f);
            var holidayPulse = holiday.gameObject.AddComponent<UIPulse>();
            holidayPulse.amount = 0.018f;
            holidayPulse.speed = 2.4f;   // not in step with PLAY's breathing
            BuildHolidayText(holiday.transform.Find("Face"));

            // CO-OP: up to four friends nearby over Bluetooth, racing to school (FrontEnd/CoopScreen).
            var coop = UIKit.Button(column, "Coop", Loc.T("menu.coop"), CoopColor, () => Controller.Show(FrontEndScreenId.Coop), 42);
            UIKit.Place((RectTransform)coop.transform, new Vector2(0f, 1f), new Vector2(Column * 0.5f + 20f + ModeHalfStep, -744f), new Vector2(ModeWidth, 112f), new Vector2(0.5f, 0.5f));
            UIKit.PopIn(coop.gameObject, 0.21f);
            var coopPulse = coop.gameObject.AddComponent<UIPulse>();
            coopPulse.amount = 0.018f;
            coopPulse.speed = 2.1f;

            // Secondary row under HOLIDAY RUN: Locker Room, Stickers, Add-ons & Filters (UI/AddOnsPanel), Settings.
            float w = 176f, gap = 12f, x0 = 20f + (Column - (w * 4f + gap * 3f)) * 0.5f;
            var shop = UIKit.Button(column, "Shop", Loc.T("menu.locker"), UITheme.Blue, () => Controller.Show(FrontEndScreenId.Shop), 32);
            UIKit.Place((RectTransform)shop.transform, new Vector2(0f, 1f), new Vector2(x0, -880f), new Vector2(w, 88f), new Vector2(0f, 0.5f));
            UIKit.PopIn(shop.gameObject, 0.22f);
            var album = UIKit.Button(column, "Album", Loc.T("menu.album"), UITheme.Blue, () => Controller.Show(FrontEndScreenId.Album), 32);
            UIKit.Place((RectTransform)album.transform, new Vector2(0f, 1f), new Vector2(x0 + w + gap, -880f), new Vector2(w, 88f), new Vector2(0f, 0.5f));
            UIKit.PopIn(album.gameObject, 0.27f);
            // Orange like its old row in Settings: the streets of another country, and the filters over the picture.
            var addOns = UIKit.Button(column, "AddOns", Loc.T("menu.addons"), new Color(0.95f, 0.55f, 0.25f), () => AddOnsPanel.Open(Controller.CanvasRoot, null), 28);
            UIKit.Place((RectTransform)addOns.transform, new Vector2(0f, 1f), new Vector2(x0 + (w + gap) * 2f, -880f), new Vector2(w, 88f), new Vector2(0f, 0.5f));
            UIKit.PopIn(addOns.gameObject, 0.3f);
            var settings = UIKit.Button(column, "Settings", Loc.T("menu.settings"), UITheme.Blue, Controller.OpenSettings, 32);
            UIKit.Place((RectTransform)settings.transform, new Vector2(0f, 1f), new Vector2(x0 + (w + gap) * 3f, -880f), new Vector2(w, 88f), new Vector2(0f, 0.5f));
            UIKit.PopIn(settings.gameObject, 0.34f);

            // Bottom left: credits, and the stars collected on a little card.
            var credits = UIKit.Button(column, "Credits", Loc.T("menu.credits"), UITheme.Paper, Controller.OpenCredits, 30, UITheme.Ink);
            UIKit.Place((RectTransform)credits.transform, Vector2.zero, new Vector2(40f, 44f), new Vector2(200f, 74f), Vector2.zero);
            var starsCard = UIKit.Card(column, "Stars", UITheme.Paper);
            var starsRoot = (RectTransform)starsCard.transform.parent;
            UIKit.Place(starsRoot, Vector2.zero, new Vector2(262f, 44f), new Vector2(440f, 74f), Vector2.zero);
            var star = UIKit.Icon(starsCard.transform, "Star", ProceduralSprites.Star, UITheme.Gold, 50f);
            UIKit.Place(star.rectTransform, new Vector2(0f, 0.5f), new Vector2(18f, 0f), new Vector2(50f, 50f), new Vector2(0f, 0.5f));
            var starLine = star.gameObject.AddComponent<Outline>();
            starLine.effectColor = new Color(0.45f, 0.28f, 0.02f, 0.9f);
            starLine.effectDistance = new Vector2(2f, -2f);
            starsLabel = UIKit.Label(starsCard.transform, "Count", "", 30, UITheme.Ink, TextAnchor.MiddleLeft, true);
            starsLabel.rectTransform.anchorMin = Vector2.zero;
            starsLabel.rectTransform.anchorMax = Vector2.one;
            starsLabel.rectTransform.offsetMin = new Vector2(80f, 4f);
            starsLabel.rectTransform.offsetMax = new Vector2(-16f, -4f);
            UIKit.Fit(starsLabel, 22);

            // Where the teen stands: the rest of the screen right of the column, above the bottom row.
            teenSpot = UIKit.Rect(root, "TeenSpot");
            teenSpot.anchorMin = Vector2.zero;
            teenSpot.anchorMax = Vector2.one;
            teenSpot.offsetMin = new Vector2(Column + 20f, 170f);
            teenSpot.offsetMax = new Vector2(0f, -235f);

            // Tap the teen to choose who walks to school; or the player card in the corner.
            var tap = UIKit.Rect(root, "TeenTap");
            var tapImage = tap.gameObject.AddComponent<Image>();
            tapImage.color = Color.clear;
            tap.gameObject.AddComponent<Button>().onClick.AddListener(OpenPicker);
            tap.gameObject.AddComponent<StageTapZone>();
            BuildPlayerCard(root);
        }

        /// <summary>
        /// The lap runs through every chapter, so where chapters are sold (Monetization.RequireUnlock) the endless
        /// mode is part of the full game: the unlock panel opens first, and the run starts once it is bought.
        /// </summary>
        void StartHolidayRun()
        {
            int lastChapter = Holiday.HolidayStages.All[Holiday.HolidayStages.Count - 1].chapter;
            if (!Store.Monetization.IsChapterUnlocked(lastChapter))
            {
                UI.UnlockPanel.Open(Controller.CanvasRoot, FrontEndController.OpenHolidayRun);
                return;
            }
            FrontEndController.OpenHolidayRun();
        }

        /// <summary>
        /// The two lines on HOLIDAY RUN: its name, and under it (once a run has been made) the best distance.
        /// Built like UIKit.Button's own label, so it looks like the other buttons.
        /// </summary>
        void BuildHolidayText(Transform face)
        {
            holidayLabel = UIKit.Label(face, "Label", Loc.T("menu.holiday"), 42, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Fit(holidayLabel, 28);
            DropShadow(holidayLabel, 3f);
            holidayBest = UIKit.Label(face, "Best", "", 26, new Color(1f, 1f, 1f, 0.92f), TextAnchor.MiddleCenter, true);
            UIKit.Fit(holidayBest, 18);
            DropShadow(holidayBest, 2f);
            ShowHolidayBest();
        }

        /// <summary>The dark drop under white lettering that UIKit.Button gives its labels.</summary>
        static void DropShadow(Text text, float depth)
        {
            var shadow = text.gameObject.AddComponent<Shadow>();
            shadow.effectColor = new Color(0f, 0.02f, 0.12f, 0.35f);
            shadow.effectDistance = new Vector2(0f, -depth);
        }

        /// <summary>The label fills the button until there is a best distance to show; then it takes the top and the distance the bottom.</summary>
        void ShowHolidayBest()
        {
            if (holidayBest == null) return;   // the screen was rebuilt (language change)
            int best = Progression.SaveSystem.Data.holidayBestDistance;
            bool played = best > 0;
            holidayBest.text = played ? Loc.F("menu.holiday.best", best.ToString("N0")) : "";
            holidayBest.gameObject.SetActive(played);
            var label = holidayLabel.rectTransform;
            label.anchorMin = new Vector2(0f, played ? 0.36f : 0f);
            label.anchorMax = Vector2.one;
            label.offsetMin = new Vector2(14f, played ? 2f : 6f);
            label.offsetMax = new Vector2(-14f, -4f);
            var line = holidayBest.rectTransform;
            line.anchorMin = Vector2.zero;
            line.anchorMax = new Vector2(1f, 0.38f);
            line.offsetMin = new Vector2(14f, 8f);
            line.offsetMax = new Vector2(-14f, 0f);
        }

        /// <summary>A white card in the bottom right corner: the chosen teen's portrait and name, tap to change.</summary>
        void BuildPlayerCard(RectTransform root)
        {
            var button = UIKit.Button(root, "Player", "", UITheme.Paper, OpenPicker);
            UIKit.Place((RectTransform)button.transform, new Vector2(1f, 0f), new Vector2(-40f, 44f), new Vector2(330f, 104f), new Vector2(1f, 0f));
            var face = button.transform.Find("Face");
            var disc = UIKit.Icon(face, "Disc", ProceduralSprites.CircleEdge, UITheme.SkyBottom, 84f);
            UIKit.Place(disc.rectTransform, new Vector2(0f, 0.5f), new Vector2(12f, 0f), new Vector2(84f, 84f), new Vector2(0f, 0.5f));
            var mask = UIKit.Rect(disc.transform, "Mask");
            UIKit.Stretch(mask, 5f);
            mask.gameObject.AddComponent<RectMask2D>();
            playerPortrait = UIKit.Icon(mask, "Portrait", null, Color.white, 80f);
            playerPortrait.rectTransform.anchorMin = new Vector2(0f, 0f);
            playerPortrait.rectTransform.anchorMax = new Vector2(1f, 1f);
            playerPortrait.rectTransform.offsetMin = new Vector2(-6f, -10f);
            playerPortrait.rectTransform.offsetMax = new Vector2(6f, 6f);

            var caption = UIKit.Label(face, "Caption", Loc.T("menu.player"), 24, UITheme.InkSoft, TextAnchor.LowerLeft, true);
            caption.rectTransform.anchorMin = new Vector2(0f, 0.52f);
            caption.rectTransform.anchorMax = new Vector2(1f, 1f);
            caption.rectTransform.offsetMin = new Vector2(110f, 0f);
            caption.rectTransform.offsetMax = new Vector2(-50f, -12f);
            UIKit.Fit(caption, 18);
            playerName = UIKit.Label(face, "Name", "", 38, UITheme.Ink, TextAnchor.UpperLeft, true);
            playerName.rectTransform.anchorMin = new Vector2(0f, 0f);
            playerName.rectTransform.anchorMax = new Vector2(1f, 0.56f);
            playerName.rectTransform.offsetMin = new Vector2(110f, 8f);
            playerName.rectTransform.offsetMax = new Vector2(-50f, 0f);
            UIKit.Fit(playerName, 26);
            var arrow = UIKit.Label(face, "Arrow", ">", 44, UITheme.Accent, TextAnchor.MiddleCenter, true);
            UIKit.Place(arrow.rectTransform, new Vector2(1f, 0.5f), new Vector2(-28f, 2f), new Vector2(40f, 60f), new Vector2(0.5f, 0.5f));
            GameSettings.Changed += RefreshPlayer;
            RefreshPlayer();
        }

        void OpenPicker()
        {
            PlayerPicker.Open(Controller.CanvasRoot);
        }

        void RefreshPlayer()
        {
            if (playerName == null) return;   // the screen was rebuilt (language change)
            string id = GameSettings.Character;
            playerName.text = Loc.T(PlayerRoster.Get(id).nameKey);
            var portrait = PlayerPicker.Portrait(id);
            playerPortrait.sprite = portrait != null ? portrait : ProceduralSprites.BallIcon;
            playerPortrait.preserveAspect = true;
        }

        public override void OnShow()
        {
            var catalog = Controller.levels;
            int total = catalog != null ? catalog.levels.Count * 3 : 0;
            int got = catalog != null ? Progression.LevelUnlocks.TotalStars(catalog) : 0;
            starsLabel.text = Loc.F("menu.stars", got, total);
            RefreshPlayer();
            ShowHolidayBest();
        }

        public override void FrameStage(MenuStage stage)
        {
            stage.Frame(MenuShot.Title, ViewportRect(teenSpot));
        }

        public override void OnDestroyed()
        {
            GameSettings.Changed -= RefreshPlayer;
            playerName = null;
        }
    }
}
