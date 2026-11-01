using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// What lies behind the menus. Normally the live 3D street (MenuStage) shows through, and this
    /// adds only a faint wash of sky at the top so the header reads. In a menu scene built
    /// without the stage it paints the game's daylight flat instead: the deep blue sky paling to
    /// the horizon, drifting cumulus with cool shaded bellies, and green hills.
    /// </summary>
    public static class MenuBackdrop
    {
        public static void Build(RectTransform root, bool liveStage)
        {
            var bg = UIKit.Stretch(UIKit.Rect(root, "Backdrop"));
            if (liveStage)
            {
                var wash = UIKit.Icon(bg, "HeaderWash", ProceduralSprites.VerticalGradient, new Color(UITheme.SkyTop.r, UITheme.SkyTop.g, UITheme.SkyTop.b, 0.35f), 10f);
                wash.preserveAspect = false;
                wash.rectTransform.anchorMin = new Vector2(0f, 0.8f);
                wash.rectTransform.anchorMax = Vector2.one;
                wash.rectTransform.offsetMin = wash.rectTransform.offsetMax = Vector2.zero;
                return;
            }

            var sky = bg.gameObject.AddComponent<Image>();
            sky.color = UITheme.SkyBottom;
            var top = UIKit.Icon(bg, "SkyTop", ProceduralSprites.VerticalGradient, UITheme.SkyTop, 10f);
            top.preserveAspect = false;
            UIKit.Stretch(top.rectTransform);

            for (int i = 0; i < 5; i++) Cloud(bg, i);

            Hill(bg, 0.2f, 1700f, 260f, new Color(0.44f, 0.62f, 0.4f));
            Hill(bg, 0.8f, 1900f, 230f, new Color(0.38f, 0.57f, 0.36f));
            Hill(bg, 0.5f, 2600f, 120f, new Color(0.33f, 0.52f, 0.32f));
        }

        static void Cloud(RectTransform parent, int index)
        {
            var cloud = UIKit.Rect(parent, "Cloud" + index);
            float y = 0.58f + (index % 3) * 0.11f;
            UIKit.Place(cloud, new Vector2(0f, y), new Vector2(index * 450f, 0f), new Vector2(300f, 120f), new Vector2(0.5f, 0.5f));
            // Cel-shaded puffs: a cool blue belly under bright white tops, with a flat base.
            Color shade = new Color(0.8f, 0.88f, 0.98f), white = Color.white;
            Puff(cloud, new Vector2(-90f, -18f), 140f, shade);
            Puff(cloud, new Vector2(-4f, 2f), 186f, shade);
            Puff(cloud, new Vector2(84f, -20f), 132f, shade);
            Puff(cloud, new Vector2(-80f, -4f), 120f, white);
            Puff(cloud, new Vector2(4f, 22f), 160f, white);
            Puff(cloud, new Vector2(90f, -6f), 110f, white);
            var drift = cloud.gameObject.AddComponent<UIDrift>();
            drift.speed = 14f + index * 6f;
        }

        static void Puff(RectTransform parent, Vector2 pos, float size, Color color)
        {
            var p = UIKit.Icon(parent, "Puff", ProceduralSprites.Circle, color, size);
            UIKit.Place(p.rectTransform, new Vector2(0.5f, 0.5f), pos, new Vector2(size, size * 0.8f), new Vector2(0.5f, 0.5f));
        }

        /// <summary>A wide ellipse peeking <paramref name="visible"/> pixels above the bottom edge.</summary>
        static void Hill(RectTransform parent, float anchorX, float size, float visible, Color color)
        {
            var hill = UIKit.Icon(parent, "Hill", ProceduralSprites.Circle, color, size);
            hill.preserveAspect = false;
            UIKit.Place(hill.rectTransform, new Vector2(anchorX, 0f), new Vector2(0f, visible - size * 0.5f),
                new Vector2(size * 1.4f, size), new Vector2(0.5f, 0.5f));
        }
    }
}
