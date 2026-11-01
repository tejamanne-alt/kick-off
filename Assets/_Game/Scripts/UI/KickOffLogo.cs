using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The game's logo, built from code: "KICK OFF" in chunky Lilita One leaning forward, white
    /// shading to pale sky with a navy extrusion and a thick ink outline (UILogoText), on a
    /// badge of mown turf with the centre circle chalked on it (where a match kicks off), a
    /// football flying in on chalk speed lines, and the tagline on a slanted navy ribbon.
    /// </summary>
    public static class KickOffLogo
    {
        /// <summary>The game's name. A brand: never translated.</summary>
        public const string GameName = "Kick Off";

        /// <summary>The logo's size at scale 1, about its centre (badge, lettering, ball and ribbon).</summary>
        public static readonly Vector2 Size = new Vector2(680f, 560f);

        /// <summary>
        /// Builds the logo centred on its returned root (sized <see cref="Size"/> times
        /// <paramref name="scale"/>; place it like any rect). The ball spins when <paramref name="animate"/>.
        /// </summary>
        public static RectTransform Build(Transform parent, float scale = 1f, bool tagline = true, bool animate = true)
        {
            var root = UIKit.Rect(parent, "KickOffLogo");
            root.sizeDelta = Size * scale;
            var art = UIKit.Rect(root, "Art");
            UIKit.Place(art, new Vector2(0.5f, 0.5f), new Vector2(0f, 8f), Size, new Vector2(0.5f, 0.5f));
            art.localScale = Vector3.one * scale;

            // The badge and its shadow.
            var badgeShadow = UIKit.Icon(art, "BadgeShadow", ProceduralSprites.Circle, UITheme.Shadow, 530f);
            UIKit.Place(badgeShadow.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(6f, -10f), new Vector2(530f, 530f));
            var badge = UIKit.Icon(art, "Badge", ProceduralSprites.PitchBadge, Color.white, 530f);
            UIKit.Place(badge.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(530f, 530f));

            Word(art, "Kick", "KICK", new Vector2(-40f, 92f));
            Word(art, "Off", "OFF", new Vector2(-80f, -92f));

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

            if (tagline)
            {
                var ribbon = UIKit.Rect(art, "Tagline");
                UIKit.Place(ribbon, new Vector2(0.5f, 0.5f), new Vector2(0f, -225f), new Vector2(600f, 58f));
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
            return root;
        }

        /// <summary>One word of the lettering, centred at <paramref name="centre"/>.</summary>
        static void Word(RectTransform art, string name, string word, Vector2 centre)
        {
            var text = UIKit.Label(art, name, word, 200, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(text.rectTransform, new Vector2(0.5f, 0.5f), centre, new Vector2(760f, 240f));
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            var fx = text.gameObject.AddComponent<UILogoText>();
            fx.skew = 0.14f;
            fx.faceTop = Color.white;
            fx.faceBottom = new Color(0.8f, 0.9f, 1f);
            fx.innerLine = 4f;
            fx.extrude = 13f;
            fx.outline = 7f;
            fx.extrudeColor = UITheme.Navy;
            fx.outlineColor = new Color(0.08f, 0.09f, 0.15f);
            fx.shadowOffset = new Vector2(6f, -18f);
        }
    }
}
