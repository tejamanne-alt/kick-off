using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The launch screen. The left column holds the logo, PLAY and the Locker Room, Stickers and
    /// Settings buttons; the rest of the screen is the live street, where the menu's camera puts
    /// the chosen teen juggling (tap them, or the player card in the corner, to switch between the
    /// boy and the girl). Credits and the stars collected sit along the bottom left. Sizes are in
    /// the 1080-tall canvas inside the safe area, so the column fits from 4:3 to 21:9.
    /// </summary>
    public class TitleScreen : FrontEndScreen
    {
        /// <summary>Width of the left column (canvas pixels): the logo and the buttons.</summary>
        const float Column = 740f;

        Text starsLabel;
        RectTransform teenSpot;
        Image playerPortrait;
        Text playerName;

        protected override void Build(RectTransform root)
        {
            var logo = KickOffLogo.Build(root, 0.86f);
            UIKit.Place(logo, new Vector2(0f, 1f), new Vector2(Column * 0.5f + 20f, -300f), logo.sizeDelta, new Vector2(0.5f, 0.5f));
            UIKit.PopIn(logo.gameObject);

            var play = UIKit.Button(root, "Play", Loc.T("menu.play"), UITheme.Accent, () => Controller.Show(FrontEndScreenId.Map), 68);
            UIKit.Place((RectTransform)play.transform, new Vector2(0f, 1f), new Vector2(Column * 0.5f + 20f, -640f), new Vector2(450f, 136f), new Vector2(0.5f, 0.5f));
            UIKit.PopIn(play.gameObject, 0.15f);
            play.gameObject.AddComponent<UIPulse>().amount = 0.025f;

            // Secondary row under PLAY.
            float w = 222f, gap = 16f, x0 = 20f + (Column - (w * 3f + gap * 2f)) * 0.5f;
            var shop = UIKit.Button(root, "Shop", Loc.T("menu.locker"), UITheme.Blue, () => Controller.Show(FrontEndScreenId.Shop), 34);
            UIKit.Place((RectTransform)shop.transform, new Vector2(0f, 1f), new Vector2(x0, -790f), new Vector2(w, 96f), new Vector2(0f, 0.5f));
            UIKit.PopIn(shop.gameObject, 0.22f);
            var album = UIKit.Button(root, "Album", Loc.T("menu.album"), UITheme.Blue, () => Controller.Show(FrontEndScreenId.Album), 34);
            UIKit.Place((RectTransform)album.transform, new Vector2(0f, 1f), new Vector2(x0 + w + gap, -790f), new Vector2(w, 96f), new Vector2(0f, 0.5f));
            UIKit.PopIn(album.gameObject, 0.27f);
            var settings = UIKit.Button(root, "Settings", Loc.T("menu.settings"), UITheme.Blue, Controller.OpenSettings, 34);
            UIKit.Place((RectTransform)settings.transform, new Vector2(0f, 1f), new Vector2(x0 + (w + gap) * 2f, -790f), new Vector2(w, 96f), new Vector2(0f, 0.5f));
            UIKit.PopIn(settings.gameObject, 0.32f);

            // Bottom left: credits, and the stars collected on a little card.
            var credits = UIKit.Button(root, "Credits", Loc.T("menu.credits"), UITheme.Paper, Controller.OpenCredits, 30, UITheme.Ink);
            UIKit.Place((RectTransform)credits.transform, Vector2.zero, new Vector2(40f, 44f), new Vector2(200f, 74f), Vector2.zero);
            var starsCard = UIKit.Card(root, "Stars", UITheme.Paper);
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
            playerName.text = Loc.T("settings." + id);
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
