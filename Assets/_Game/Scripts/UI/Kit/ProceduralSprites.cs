using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>UI sprites drawn in code: rounded panels, circles, stars, coins, a padlock.</summary>
    public static class ProceduralSprites
    {
        static Sprite rounded, roundedSmall, circle, star, coin, lockIcon, gradient, arrow, pause;

        /// <summary>Upward chevron (jump button).</summary>
        public static Sprite ArrowUp
        {
            get
            {
                return arrow != null ? arrow : (arrow = MakeShape(96, (u, v) =>
                {
                    // Thick chevron: inside a wide triangle but outside a smaller one shifted down.
                    bool outer = v > -0.6f && v < 0.75f - Mathf.Abs(u) * 1.35f;
                    bool inner = v > -0.6f && v < 0.15f - Mathf.Abs(u) * 1.35f;
                    return outer && !inner && Mathf.Abs(u) < 0.95f ? 1f : 0f;
                }));
            }
        }

        /// <summary>Two rounded bars.</summary>
        public static Sprite Pause
        {
            get
            {
                return pause != null ? pause : (pause = MakeShape(96, (u, v) =>
                    Mathf.Abs(v) < 0.6f && (Mathf.Abs(u - 0.3f) < 0.16f || Mathf.Abs(u + 0.3f) < 0.16f) ? 1f : 0f));
            }
        }

        /// <summary>9-sliced rounded rectangle with a faint hand-drawn inner edge.</summary>
        public static Sprite Rounded
        {
            get { return rounded != null ? rounded : (rounded = MakeRounded(96, 34)); }
        }

        public static Sprite RoundedSmall
        {
            get { return roundedSmall != null ? roundedSmall : (roundedSmall = MakeRounded(48, 16)); }
        }

        public static Sprite Circle
        {
            get { return circle != null ? circle : (circle = MakeShape(128, (u, v) => Disc(u, v, 1f))); }
        }

        public static Sprite Star
        {
            get { return star != null ? star : (star = MakeShape(128, StarAlpha)); }
        }

        public static Sprite Lock
        {
            get { return lockIcon != null ? lockIcon : (lockIcon = MakeShape(96, LockAlpha)); }
        }

        /// <summary>Vertical white-to-clear gradient, tinted by the Image colour.</summary>
        public static Sprite VerticalGradient
        {
            get
            {
                if (gradient != null) return gradient;
                var tex = new Texture2D(4, 64, TextureFormat.RGBA32, false);
                for (int y = 0; y < 64; y++)
                    for (int x = 0; x < 4; x++)
                        tex.SetPixel(x, y, new Color(1f, 1f, 1f, y / 63f));
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                gradient = Sprite.Create(tex, new Rect(0, 0, 4, 64), new Vector2(0.5f, 0.5f), 100f);
                return gradient;
            }
        }

        /// <summary>Full-colour gold coin icon.</summary>
        public static Sprite Coin
        {
            get
            {
                if (coin != null) return coin;
                const int size = 96;
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                Color gold = UITheme.Gold, dark = new Color(0.8f, 0.55f, 0.1f), ink = UITheme.Ink;
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                        float r = Mathf.Sqrt(u * u + v * v);
                        float a = Mathf.Clamp01((1f - r) * size * 0.5f);
                        Color c = gold;
                        if (r > 0.62f && r < 0.7f) c = dark;
                        if (Mathf.Abs(u) < 0.1f && Mathf.Abs(v) < 0.38f) c = dark;   // engraved bar
                        float hl = Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(-0.35f, 0.4f)) / 0.3f);
                        c = Color.Lerp(c, Color.white, hl * 0.5f);
                        c = Color.Lerp(c, ink, Mathf.Clamp01((r - 0.88f) / 0.07f));
                        c.a = a;
                        tex.SetPixel(x, y, c);
                    }
                }
                tex.Apply();
                coin = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return coin;
            }
        }

        delegate float AlphaFn(float u, float v);

        static Sprite MakeShape(int size, AlphaFn fn)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    // 2x2 supersampling for smooth edges
                    float d = 0.5f / size;
                    float a = (fn(u - d, v - d) + fn(u + d, v - d) + fn(u - d, v + d) + fn(u + d, v + d)) * 0.25f;
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
        }

        static Sprite MakeRounded(int size, int radius)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float cx = Mathf.Clamp(x + 0.5f, radius, size - radius);
                    float cy = Mathf.Clamp(y + 0.5f, radius, size - radius);
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(cx, cy));
                    float a = Mathf.Clamp01(radius - d + 0.5f);
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            float b = radius + 2;
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(b, b, b, b));
        }

        static float Disc(float u, float v, float r)
        {
            return Mathf.Clamp01((r - Mathf.Sqrt(u * u + v * v)) * 64f);
        }

        static float StarAlpha(float u, float v)
        {
            float ang = Mathf.Atan2(v, u) - Mathf.PI * 0.5f;
            float seg = Mathf.PI * 2f / 5f;
            float t = Mathf.Abs(Mathf.Repeat(ang, seg) - seg * 0.5f) / (seg * 0.5f);
            float limit = Mathf.Lerp(0.95f, 0.42f, 1f - t);
            // Slightly rounded points
            return Mathf.Clamp01((limit - Mathf.Sqrt(u * u + v * v)) * 40f);
        }

        static float LockAlpha(float u, float v)
        {
            // Body
            if (Mathf.Abs(u) < 0.62f && v > -0.85f && v < 0.1f)
            {
                // keyhole
                if (u * u + (v + 0.3f) * (v + 0.3f) < 0.02f) return 0f;
                if (Mathf.Abs(u) < 0.06f && v > -0.62f && v < -0.3f) return 0f;
                return 1f;
            }
            // Shackle (ring)
            float r = Mathf.Sqrt(u * u + (v - 0.15f) * (v - 0.15f));
            if (v > 0.1f && r > 0.32f && r < 0.5f) return 1f;
            return 0f;
        }
    }
}
