using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// Storybook morning behind the menus: warm sky gradient, sun, drifting
    /// clouds, rolling hills and a little row of houses.
    /// </summary>
    public static class MenuBackdrop
    {
        public static void Build(RectTransform root)
        {
            var bg = UIKit.Stretch(UIKit.Rect(root, "Backdrop"));

            var sky = bg.gameObject.AddComponent<Image>();
            sky.color = UITheme.SkyBottom;
            var top = UIKit.Icon(bg, "SkyTop", ProceduralSprites.VerticalGradient, UITheme.SkyTop, 10f);
            top.preserveAspect = false;
            UIKit.Stretch(top.rectTransform);

            for (int i = 0; i < 5; i++) Cloud(bg, i);

            Hill(bg, 0.15f, 1500f, 340f, new Color(0.6f, 0.8f, 0.55f));
            Hill(bg, 0.75f, 1700f, 300f, new Color(0.52f, 0.74f, 0.5f));
            Houses(bg);
            Hill(bg, 0.45f, 2400f, 150f, new Color(0.45f, 0.68f, 0.45f));
        }

        static void Cloud(RectTransform parent, int index)
        {
            var cloud = UIKit.Rect(parent, "Cloud" + index);
            float y = 0.6f + (index % 3) * 0.1f;
            UIKit.Place(cloud, new Vector2(0f, y), new Vector2(index * 450f, 0f), new Vector2(300f, 120f), new Vector2(0.5f, 0.5f));
            // Cel-shaded puffs: a pale blue shadow disc under each white one.
            Color shadow = new Color(0.74f, 0.86f, 0.97f), white = Color.white;
            Puff(cloud, new Vector2(-84f, -16f), 140f, shadow);
            Puff(cloud, new Vector2(-4f, 8f), 180f, shadow);
            Puff(cloud, new Vector2(80f, -18f), 130f, shadow);
            Puff(cloud, new Vector2(-76f, -6f), 124f, white);
            Puff(cloud, new Vector2(6f, 20f), 160f, white);
            Puff(cloud, new Vector2(88f, -8f), 114f, white);
            var drift = cloud.gameObject.AddComponent<UIDrift>();
            drift.speed = 18f + index * 7f;
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

        static void Houses(RectTransform parent)
        {
            var row = UIKit.Rect(parent, "Houses");
            row.anchorMin = new Vector2(0f, 0f);
            row.anchorMax = new Vector2(1f, 0f);
            row.pivot = new Vector2(0.5f, 0f);
            row.sizeDelta = new Vector2(0f, 300f);
            row.anchoredPosition = new Vector2(0f, 120f);

            Color[] walls =
            {
                new Color(0.96f, 0.85f, 0.7f), new Color(0.9f, 0.7f, 0.6f), new Color(0.85f, 0.85f, 0.75f),
                new Color(0.95f, 0.78f, 0.55f), new Color(0.8f, 0.75f, 0.85f),
            };
            for (int i = 0; i < 7; i++)
            {
                float x = 0.06f + i * 0.145f;
                float h = 170f + (i * 37 % 80);
                var wall = UIKit.Panel(row, "House" + i, walls[i % walls.Length], ProceduralSprites.RoundedSmall);
                UIKit.Place(wall.rectTransform, new Vector2(x, 0f), Vector2.zero, new Vector2(170f, h), new Vector2(0.5f, 0f));
                var roof = UIKit.Panel(wall.transform, "Roof", new Color(0.75f, 0.38f, 0.32f), ProceduralSprites.RoundedSmall);
                UIKit.Place(roof.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -10f), new Vector2(200f, 50f), new Vector2(0.5f, 0f));
                for (int w = 0; w < 2; w++)
                {
                    var win = UIKit.Panel(wall.transform, "Window", new Color(1f, 0.95f, 0.7f), ProceduralSprites.RoundedSmall);
                    UIKit.Place(win.rectTransform, new Vector2(0.3f + w * 0.4f, 0.65f), Vector2.zero, new Vector2(42f, 48f), new Vector2(0.5f, 0.5f));
                }
            }
        }
    }
}
