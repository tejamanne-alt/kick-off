using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The game's logo: the "Kick OFF 2" lettering of the app icon and the store banner (white "Kick", red "OFF", a golden
    /// "2", a navy outline and a yellow swoosh), cut out of the banner artwork into Resources/UI/KickOffLogo.png by
    /// tools/logo_from_banner.py, over the tagline on a slanted navy ribbon. If that picture is missing, the logo drawn in
    /// code instead: "KICK OFF" in chunky Lilita One leaning forward (UILogoText) and a sunny "2" on a badge of mown turf
    /// with the centre circle chalked on it, a football flying in on chalk speed lines.
    /// </summary>
    public static class KickOffLogo
    {
        /// <summary>The game's name. A brand: never translated.</summary>
        public const string GameName = "Kick Off 2";

        /// <summary>The logo drawn in code: its size at scale 1, about its centre (badge, lettering, ball and ribbon).</summary>
        public static readonly Vector2 Size = new Vector2(680f, 560f);

        /// <summary>The picture of the lettering's width at scale 1, and the room under it for the ribbon (gap and ribbon).</summary>
        const float PictureWidth = 740f, RibbonBlock = 22f + 58f;

        /// <summary>
        /// Builds the logo centred on its returned root (sized <see cref="Size"/> times
        /// <paramref name="scale"/>; place it like any rect). With <paramref name="animate"/> the lettering breathes gently
        /// (or, drawn in code, the ball spins).
        /// </summary>
        public static RectTransform Build(Transform parent, float scale = 1f, bool tagline = true, bool animate = true)
        {
            var root = UIKit.Rect(parent, "KickOffLogo");
            var picture = Resources.Load<Sprite>(PicturePath);
            if (picture != null)
            {
                // The lettering as on the icon and the banner, with the ribbon under it; the logo's box is exactly that, so
                // whatever is laid out round it (the title screen's buttons, the credits' text) sits where it looks.
                float height = PictureWidth * picture.rect.height / picture.rect.width;
                var box = new Vector2(PictureWidth, height + (tagline ? RibbonBlock : 0f));
                root.sizeDelta = box * scale;
                var content = UIKit.Rect(root, "Art");
                UIKit.Place(content, new Vector2(0.5f, 0.5f), Vector2.zero, box, new Vector2(0.5f, 0.5f));
                content.localScale = Vector3.one * scale;
                var lettering = UIKit.Icon(content, "Lettering", picture, Color.white, PictureWidth);
                lettering.preserveAspect = true;
                UIKit.Place(lettering.rectTransform, new Vector2(0.5f, 1f), Vector2.zero, new Vector2(PictureWidth, height), new Vector2(0.5f, 1f));
                if (animate) lettering.gameObject.AddComponent<UIPulse>().amount = 0.012f;
                if (tagline) Tagline(content, -box.y * 0.5f + 29f);
                return root;
            }

            root.sizeDelta = Size * scale;
            var art = UIKit.Rect(root, "Art");
            UIKit.Place(art, new Vector2(0.5f, 0.5f), new Vector2(0f, 8f), Size, new Vector2(0.5f, 0.5f));
            art.localScale = Vector3.one * scale;

            // Drawn in code (without the picture): the badge and its shadow.
            var badgeShadow = UIKit.Icon(art, "BadgeShadow", ProceduralSprites.Circle, UITheme.Shadow, 530f);
            UIKit.Place(badgeShadow.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(6f, -10f), new Vector2(530f, 530f));
            var badge = UIKit.Icon(art, "Badge", ProceduralSprites.PitchBadge, Color.white, 530f);
            UIKit.Place(badge.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(530f, 530f));

            Word(art, "Kick", "KICK", new Vector2(-40f, 92f));
            Word(art, "Off", "OFF", new Vector2(-105f, -92f));
            // The "2" (as in "to"), a little bigger and tilted forward, in the sunny accent colours.
            var two = Word(art, "Two", "2", new Vector2(165f, -100f), 220, Gold, UITheme.Accent);
            two.rectTransform.localRotation = Quaternion.Euler(0f, 0f, -6f);

            // Chalk speed lines streaming back from the ball, up and to the left.
            var trail = UIKit.Rect(art, "SpeedLines");
            UIKit.Place(trail, new Vector2(0.5f, 0.5f), new Vector2(255f, 178f), Vector2.zero);
            trail.localRotation = Quaternion.Euler(0f, 0f, -28f);
            float[] offsets = { 26f, 0f, -26f };
            float[] lengths = { 150f, 200f, 120f };
            for (int i = 0; i < 3; i++)
            {
                var line = UIKit.Panel(trail, "Line" + i, Color.white, ProceduralSprites.RoundedEdgeSmall);
                UIKit.Place(line.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(-60f, offsets[i]), new Vector2(lengths[i], 16f), new Vector2(1f, 0.5f));
                line.raycastTarget = false;
            }

            var ball = UIKit.Icon(art, "Ball", ProceduralSprites.BallIcon, Color.white, 150f);
            UIKit.Place(ball.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(250f, 175f), new Vector2(150f, 150f));
            ball.rectTransform.localRotation = Quaternion.Euler(0f, 0f, -20f);
            if (animate) ball.gameObject.AddComponent<UISpin>();

            if (tagline) Tagline(art, -225f);
            return root;
        }

        /// <summary>The picture of the lettering (Resources/UI/KickOffLogo.png).</summary>
        const string PicturePath = "UI/KickOffLogo";

        /// <summary>The tagline on a slanted navy ribbon over an accent stripe, centred <paramref name="y"/> from the logo's middle.</summary>
        static void Tagline(RectTransform art, float y)
        {
            var ribbon = UIKit.Rect(art, "Tagline");
            UIKit.Place(ribbon, new Vector2(0.5f, 0.5f), new Vector2(0f, y), new Vector2(600f, 58f));
            var stripe = UIKit.Panel(ribbon, "Stripe", UITheme.Accent, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Stretch(stripe.rectTransform);
            stripe.rectTransform.offsetMin += new Vector2(10f, -8f);
            stripe.rectTransform.offsetMax += new Vector2(10f, -8f);
            stripe.gameObject.AddComponent<UISkew>().skew = 0.3f;
            stripe.raycastTarget = false;
            var band = UIKit.Panel(ribbon, "Band", UITheme.Navy, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Stretch(band.rectTransform);
            band.gameObject.AddComponent<UISkew>().skew = 0.3f;
            band.raycastTarget = false;
            var text = UIKit.Label(band.transform, "Text", Loc.T("menu.tagline").ToUpperInvariant(), 30, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(text.rectTransform);
            text.rectTransform.offsetMin = new Vector2(30f, 2f);
            text.rectTransform.offsetMax = new Vector2(-30f, -2f);
            UIKit.Fit(text, 20);
        }

        /// <summary>The "2"'s face, top: a warm sunshine yellow.</summary>
        static readonly Color Gold = new Color(1f, 0.86f, 0.3f);

        /// <summary>One word of the lettering, centred at <paramref name="centre"/>: white shading to pale sky unless given colours.</summary>
        static Text Word(RectTransform art, string name, string word, Vector2 centre, int size = 200, Color? top = null, Color? bottom = null)
        {
            var text = UIKit.Label(art, name, word, size, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(text.rectTransform, new Vector2(0.5f, 0.5f), centre, new Vector2(760f, 240f * size / 200f));
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            var fx = text.gameObject.AddComponent<UILogoText>();
            fx.skew = 0.14f;
            fx.faceTop = top ?? Color.white;
            fx.faceBottom = bottom ?? new Color(0.8f, 0.9f, 1f);
            fx.innerLine = 4f;
            fx.extrude = 13f;
            fx.outline = 7f;
            fx.extrudeColor = UITheme.Navy;
            fx.outlineColor = new Color(0.08f, 0.09f, 0.15f);
            fx.shadowOffset = new Vector2(6f, -18f);
            return text;
        }
    }
}
