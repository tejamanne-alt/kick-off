using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>UI sprites drawn in code: rounded panels, circles, stars, coins, a padlock.</summary>
    public static class ProceduralSprites
    {
        static Sprite rounded, roundedSmall, circle, star, coin, lockIcon, gradient, arrow, pause, ring, softDisc, softEdgeDisc, ballIcon, slideIcon;

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

        /// <summary>
        /// Slide button: the jump chevron turned to point down, a little smaller, over a short
        /// rounded bar for the ground: "get down low".
        /// </summary>
        public static Sprite SlideIcon
        {
            get
            {
                return slideIcon != null ? slideIcon : (slideIcon = MakeShape(96, (u, v) =>
                {
                    // The ArrowUp chevron flipped and scaled about a centre above the bar.
                    const float scale = 0.72f;
                    float cu = u / scale, cv = (0.2f - v) / scale;
                    bool outer = cv > -0.6f && cv < 0.75f - Mathf.Abs(cu) * 1.35f;
                    bool inner = cv > -0.6f && cv < 0.15f - Mathf.Abs(cu) * 1.35f;
                    bool chevron = outer && !inner && Mathf.Abs(cu) < 0.95f;
                    // The ground: a bar with round ends below the chevron's point.
                    float bx = Mathf.Max(0f, Mathf.Abs(u) - 0.58f), by = v + 0.7f;
                    bool bar = bx * bx + by * by < 0.1f * 0.1f;
                    return chevron || bar ? 1f : 0f;
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

        /// <summary>Thin circle outline (ripples, rims).</summary>
        public static Sprite Ring
        {
            get
            {
                return ring != null ? ring : (ring = MakeShape(160, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    return Mathf.Clamp01((0.06f - Mathf.Abs(r - 0.92f)) * 80f);
                }));
            }
        }

        /// <summary>
        /// A disc of frosted glass: even in the middle, slightly brighter just inside the edge,
        /// and fading out softly at the rim instead of having a border.
        /// </summary>
        public static Sprite SoftEdgeDisc
        {
            get
            {
                return softEdgeDisc != null ? softEdgeDisc : (softEdgeDisc = MakeShape(160, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float fade = Mathf.Clamp01((1f - r) / 0.12f);
                    float lip = Mathf.Clamp01(1f - Mathf.Abs(r - 0.86f) / 0.1f) * 0.35f;
                    return fade * fade * (3f - 2f * fade) * (0.75f + lip);
                }));
            }
        }

        /// <summary>Blurry disc for drop shadows and glows.</summary>
        public static Sprite SoftDisc
        {
            get
            {
                return softDisc != null ? softDisc : (softDisc = MakeShape(96, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float k = Mathf.Clamp01((1f - r) / 0.45f);
                    return k * k * (3f - 2f * k);
                }));
            }
        }

        /// <summary>Full-colour football icon: white with dark patches and an ink rim (kick button).</summary>
        public static Sprite BallIcon
        {
            get
            {
                if (ballIcon != null) return ballIcon;
                const int size = 128;
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                Color ink = new Color(0.12f, 0.12f, 0.16f);
                var centres = new Vector2[6];
                centres[0] = new Vector2(0.08f, 0.06f);
                for (int i = 0; i < 5; i++)
                {
                    float a = i * Mathf.PI * 0.4f + 0.5f;
                    centres[i + 1] = centres[0] + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 0.78f;
                }
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                        float r = Mathf.Sqrt(u * u + v * v);
                        Color c = Color.white;
                        for (int i = 0; i < centres.Length; i++)
                        {
                            Vector2 d = new Vector2(u, v) - centres[i];
                            // Pentagonal patches, squashed toward the rim like on a sphere.
                            float ang = Mathf.Atan2(d.y, d.x);
                            float seg = Mathf.PI * 0.4f;
                            float edge = Mathf.Cos(seg * 0.5f) / Mathf.Cos(Mathf.Repeat(ang + 0.3f, seg) - seg * 0.5f);
                            float patch = (i == 0 ? 0.3f : 0.24f) * edge;
                            if (d.magnitude < patch) c = ink;
                        }
                        // Cel shading: a shadow crescent at the lower right, a highlight top left.
                        float shade = Vector2.Dot(new Vector2(u, v), new Vector2(0.6f, -0.8f));
                        if (shade > 0.45f && c != ink) c = new Color(0.82f, 0.86f, 0.95f);
                        if (Vector2.Distance(new Vector2(u, v), new Vector2(-0.38f, 0.42f)) < 0.14f && c != ink) c = Color.white;
                        c = Color.Lerp(c, ink, Mathf.Clamp01((r - 0.86f) / 0.05f));
                        c.a = Mathf.Clamp01((1f - r) * size * 0.5f);
                        tex.SetPixel(x, y, c);
                    }
                }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                ballIcon = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return ballIcon;
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
