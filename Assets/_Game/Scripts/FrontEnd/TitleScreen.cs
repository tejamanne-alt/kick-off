using DribbleToSchool.Cosmetics;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>Game title with a bouncing ball, and the main buttons.</summary>
    public class TitleScreen : FrontEndScreen
    {
        Text starsLabel;
        Image ballIcon;

        protected override void Build(RectTransform root)
        {
            var title = UIKit.Title(root, "GameTitle", Loc.T("menu.title"), UITheme.SizeHero, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 0.7f), Vector2.zero, new Vector2(1400f, 320f));
            title.lineSpacing = 0.85f;
            UIKit.PopIn(title.gameObject);

            ballIcon = UIKit.Icon(root, "Ball", null, Color.white, 130f);
            UIKit.Place(ballIcon.rectTransform, new Vector2(0.5f, 0.7f), new Vector2(470f, 40f), new Vector2(130f, 130f));
            ballIcon.gameObject.AddComponent<UIBounce>();

            var play = UIKit.Button(root, "Play", Loc.T("menu.play"), UITheme.Accent, () => Controller.Show(FrontEndScreenId.Map), 64);
            UIKit.Place((RectTransform)play.transform, new Vector2(0.5f, 0.38f), Vector2.zero, new Vector2(460f, 150f));
            UIKit.PopIn(play.gameObject, 0.15f);
            play.gameObject.AddComponent<UIPulse>().amount = 0.025f;

            // Secondary row
            var shop = UIKit.Button(root, "Shop", Loc.T("menu.locker"), UITheme.Blue, () => Controller.Show(FrontEndScreenId.Shop), 40);
            UIKit.Place((RectTransform)shop.transform, new Vector2(0.5f, 0.2f), new Vector2(-380f, 0f), new Vector2(340f, 110f));
            UIKit.PopIn(shop.gameObject, 0.22f);
            var album = UIKit.Button(root, "Album", Loc.T("menu.album"), new Color(0.85f, 0.45f, 0.7f), () => Controller.Show(FrontEndScreenId.Album), 40);
            UIKit.Place((RectTransform)album.transform, new Vector2(0.5f, 0.2f), Vector2.zero, new Vector2(340f, 110f));
            UIKit.PopIn(album.gameObject, 0.27f);
            var settings = UIKit.Button(root, "Settings", Loc.T("menu.settings"), UITheme.Green, Controller.OpenSettings, 40);
            UIKit.Place((RectTransform)settings.transform, new Vector2(0.5f, 0.2f), new Vector2(380f, 0f), new Vector2(340f, 110f));
            UIKit.PopIn(settings.gameObject, 0.32f);

            var credits = UIKit.Button(root, "Credits", Loc.T("menu.credits"), UITheme.Paper, Controller.OpenCredits, 28, UITheme.Ink);
            UIKit.Place((RectTransform)credits.transform, new Vector2(0f, 0f), new Vector2(40f, 40f), new Vector2(200f, 70f), Vector2.zero);

            starsLabel = UIKit.Label(root, "Stars", "", UITheme.SizeBody, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(starsLabel.rectTransform, new Vector2(0.5f, 0.07f), Vector2.zero, new Vector2(900f, 60f));
        }

        public override void OnShow()
        {
            var catalog = Controller.levels;
            int total = catalog != null ? catalog.levels.Count * 3 : 0;
            int got = catalog != null ? LevelUnlocks.TotalStars(catalog) : 0;
            starsLabel.text = Loc.F("menu.stars", got, total);

            var equipped = Controller.cosmetics != null ? Controller.cosmetics.Find(SaveSystem.Data.equippedBall) : null;
            if (equipped != null) ballIcon.sprite = CosmeticArt.BallSprite(equipped);
        }
    }
}
