using DribbleToSchool.Cosmetics;
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
            var title = UIKit.Title(root, "GameTitle", "Dribble\nto School", UITheme.SizeHero, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 0.7f), Vector2.zero, new Vector2(1400f, 320f));
            title.lineSpacing = 0.85f;
            UIKit.PopIn(title.gameObject);

            ballIcon = UIKit.Icon(root, "Ball", null, Color.white, 130f);
            UIKit.Place(ballIcon.rectTransform, new Vector2(0.5f, 0.7f), new Vector2(470f, 40f), new Vector2(130f, 130f));
            ballIcon.gameObject.AddComponent<UIBounce>();

            var play = UIKit.Button(root, "Play", "PLAY", UITheme.Accent, () => Controller.Show(FrontEndScreenId.Map), 64);
            UIKit.Place((RectTransform)play.transform, new Vector2(0.5f, 0.36f), Vector2.zero, new Vector2(460f, 150f));
            UIKit.PopIn(play.gameObject, 0.15f);

            var shop = UIKit.Button(root, "Shop", "Locker Room", UITheme.Blue, () => Controller.Show(FrontEndScreenId.Shop));
            UIKit.Place((RectTransform)shop.transform, new Vector2(0.5f, 0.2f), Vector2.zero, new Vector2(400f, 110f));
            UIKit.PopIn(shop.gameObject, 0.25f);

            starsLabel = UIKit.Label(root, "Stars", "", UITheme.SizeBody, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(starsLabel.rectTransform, new Vector2(0.5f, 0.07f), Vector2.zero, new Vector2(800f, 60f));
        }

        public override void OnShow()
        {
            var catalog = Controller.levels;
            int total = catalog != null ? catalog.levels.Count * 3 : 0;
            int got = catalog != null ? LevelUnlocks.TotalStars(catalog) : 0;
            starsLabel.text = "Stars collected: " + got + " / " + total;

            var equipped = Controller.cosmetics != null ? Controller.cosmetics.Find(SaveSystem.Data.equippedBall) : null;
            if (equipped != null) ballIcon.sprite = CosmeticArt.BallSprite(equipped);
        }
    }
}
