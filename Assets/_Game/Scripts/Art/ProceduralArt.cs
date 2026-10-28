using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Storybook art drawn in code: everything gets watercolour grain and a
    /// wobbly ink outline so it reads as one hand-drawn world. Tintable pieces
    /// are drawn in light greys so SpriteRenderer colours show through.
    /// </summary>
    public static partial class ProceduralArt
    {
        static readonly Color Ink = ChapterTheme.Ink;
        static readonly Color White = Color.white;

        static Color Grey(float v) { return new Color(v, v, v, 1f); }
        static Color Mul(Color c, float k) { return new Color(c.r * k, c.g * k, c.b * k, c.a); }

        // ===================== Tiles & blocks =====================

        /// <summary>Tintable paper block with an inked rim (9-slice border 12 px).</summary>
        public static PixelCanvas Block()
        {
            var c = new PixelCanvas(64, 64);
            c.FillRoundRect(1, 1, 63, 63, 7, White);
            // Soft inner shading toward the bottom edge.
            c.Shade((x, y) => y < 14 ? 0.22f : 0f, Grey(0.6f));       // hard cel shadow along the bottom
            c.Grain(0.04f, 3);
            c.Ink(Ink, 2f, 5);
            return c;
        }

        /// <summary>Wooden crate (not tinted).</summary>
        public static PixelCanvas Crate()
        {
            var c = new PixelCanvas(64, 64);
            Color wood = new Color(0.82f, 0.6f, 0.36f), dark = new Color(0.62f, 0.42f, 0.24f);
            c.FillRoundRect(1, 1, 63, 63, 4, wood);
            for (int i = 0; i < 4; i++) c.FillRect(2, 2 + i * 15, 62, 3 + i * 15, dark);
            c.Line(new Vector2(8, 8), new Vector2(56, 56), 6, dark);
            c.FillRect(2, 2, 10, 62, Mul(wood, 0.9f));
            c.FillRect(54, 2, 62, 62, Mul(wood, 0.9f));
            c.Grain(0.18f, 11, 0.12f);
            c.Ink(Ink, 2.6f, 7);
            return c;
        }

        /// <summary>Tileable tintable ground fill with speckles and pebbles.</summary>
        public static PixelCanvas GroundFill()
        {
            var c = new PixelCanvas(128, 128);
            c.Clear(White);
            var rng = new System.Random(42);
            for (int i = 0; i < 26; i++)
            {
                float x = rng.Next(0, 128), y = rng.Next(8, 120), r = 1.5f + (float)rng.NextDouble() * 3f;
                c.Wrapped(o => c.FillEllipse(x + o, y, r * 1.4f, r, Grey(0.78f)));
            }
            c.Grain(0.16f, 9, 0.05f, true);
            return c;
        }

        /// <summary>Tileable strip drawn along the top of the ground. Baked in colour.</summary>
        public static PixelCanvas GroundEdge(EdgeStyle style, Color edge, Color fill)
        {
            const int w = 256, h = 48;
            var c = new PixelCanvas(w, h);
            var rng = new System.Random((int)style * 31 + 7);
            float baseY = 20f;
            switch (style)
            {
                case EdgeStyle.Grass:
                case EdgeStyle.ParkPath:
                    c.FillBelow(x => baseY + Mathf.Sin(x / w * Mathf.PI * 2f * 3f) * 2f, edge);
                    c.Grain(0.1f, (int)style, 0.06f, true);
                    c.Ink(Ink, 2f, 3, true);
                    // Blades go on after the ink so they stay soft and light.
                    for (int i = 0; i < 70; i++)
                    {
                        float x = (float)rng.NextDouble() * w;
                        float hgt = 5f + (float)rng.NextDouble() * 10f;
                        float lean = ((float)rng.NextDouble() - 0.5f) * 6f;
                        Color blade = Mul(edge, 0.82f + (float)rng.NextDouble() * 0.3f);
                        c.Wrapped(o => c.Line(new Vector2(x + o, baseY - 3f), new Vector2(x + o + lean, baseY + hgt), 2.5f, blade));
                    }
                    if (style == EdgeStyle.ParkPath)
                        for (int i = 0; i < 6; i++)
                        {
                            float fx = (float)rng.NextDouble() * w;
                            c.Wrapped(o => c.FillCircle(fx + o, baseY + 8f, 3f, new Color(1f, 0.85f, 0.4f)));
                        }
                    return c;
                case EdgeStyle.Cobbles:
                    for (int i = 0; i < 16; i++)
                    {
                        float x = i * 16f + 1f;
                        c.FillRoundRect(x, 4f, x + 14f, baseY + 2f, 4f, Mul(edge, 0.9f + (float)rng.NextDouble() * 0.2f));
                    }
                    break;
                case EdgeStyle.Sand:
                    c.FillBelow(x => baseY + Mathf.Sin(x / w * Mathf.PI * 2f * 2f) * 3f, edge);
                    for (int i = 0; i < 40; i++)
                    {
                        float sx = (float)rng.NextDouble() * w, sy = (float)rng.NextDouble() * baseY;
                        c.Wrapped(o => c.FillCircle(sx + o, sy, 1.2f, Mul(edge, 0.85f)));
                    }
                    for (int i = 0; i < 3; i++)
                    {
                        float sx = (float)rng.NextDouble() * w;
                        c.Wrapped(o => c.FillEllipse(sx + o, baseY + 1f, 5f, 3f, new Color(1f, 0.75f, 0.7f)));   // shells
                    }
                    break;
                case EdgeStyle.Road:
                    // Asphalt with a white concrete kerb along the top and the odd weed in the joints.
                    c.FillRect(0, 2, w, baseY - 4f, fill);
                    c.FillRect(0, baseY - 6f, w, baseY + 3f, edge);
                    c.FillRect(0, baseY - 6f, w, baseY - 3f, Mul(edge, 0.82f));     // kerb face shadow
                    for (int i = 0; i < 4; i++) c.FillRect(i * 64f + 30f, baseY - 6f, i * 64f + 31.5f, baseY + 3f, Mul(edge, 0.7f));
                    for (int i = 0; i < 3; i++)
                    {
                        float gx = i * 85f + rng.Next(0, 30);
                        for (int b = 0; b < 4; b++)
                        {
                            float lean = b * 2.5f - 4f;
                            c.Wrapped(o => c.Line(new Vector2(gx + o + b * 2f, baseY + 2f), new Vector2(gx + o + b * 2f + lean, baseY + 9f + b % 2 * 3f), 2f, new Color(0.45f, 0.65f, 0.35f)));
                        }
                    }
                    c.Grain(0.05f, (int)style, 0.06f, true);
                    c.Ink(new Color(Ink.r, Ink.g, Ink.b, 0.5f), 1.5f, 3, true);
                    return c;
                case EdgeStyle.Concrete:
                    c.FillRect(0, 2, w, baseY + 2f, edge);
                    for (int i = 0; i < 4; i++) c.FillRect(i * 64f, 2, i * 64f + 2f, baseY + 2f, Mul(edge, 0.7f));
                    c.FillRect(0, baseY - 2f, w, baseY + 2f, new Color(0.95f, 0.8f, 0.2f));   // painted kerb line
                    break;
            }
            c.Grain(0.12f, (int)style, 0.06f, true);
            c.Ink(Ink, 2f, 3, true);
            return c;
        }

        public static PixelCanvas Dog()
        {
            var c = new PixelCanvas(192, 128);
            Color fur = Grey(0.96f), dark = Grey(0.7f);
            c.FillRoundRect(40, 40, 140, 84, 20, fur);
            c.FillCircle(150, 86, 26, fur);
            c.FillEllipse(170, 78, 18, 12, fur);
            c.FillCircle(186, 80, 5, Ink);
            c.FillEllipse(138, 104, 9, 18, dark);   // ear
            c.FillCircle(156, 94, 4, Ink);
            c.Line(new Vector2(42, 70), new Vector2(16, 98), 9, fur);   // tail
            for (int i = 0; i < 2; i++)
            {
                c.FillRoundRect(52 + i * 6, 4, 66 + i * 6, 48, 6, i == 0 ? dark : fur);
                c.FillRoundRect(112 + i * 6, 4, 126 + i * 6, 48, 6, i == 0 ? dark : fur);
            }
            c.Grain(0.1f, 8);
            c.Ink(Ink, 3f, 8);
            return c;
        }

        public static PixelCanvas Seagull()
        {
            var c = new PixelCanvas(160, 96);
            c.FillEllipse(80, 44, 44, 18, White);
            c.FillCircle(122, 54, 14, White);
            c.FillPolygon(new[] { new Vector2(132, 56), new Vector2(156, 50), new Vector2(132, 48) }, new Color(1f, 0.72f, 0.2f));
            c.FillCircle(124, 58, 3, Ink);
            c.FillPolygon(new[] { new Vector2(60, 50), new Vector2(100, 52), new Vector2(70, 92) }, Grey(0.82f));
            c.FillPolygon(new[] { new Vector2(40, 44), new Vector2(14, 52), new Vector2(40, 36) }, Grey(0.85f));
            c.Ink(Ink, 2.5f, 9);
            return c;
        }

        /// <summary>Side view car body; tintable body, fixed windows and wheels.</summary>
        /// <summary>
        /// A small city car facing right, tintable body. Baked at 115 px per unit it is 3.4 units
        /// (3 m) long with the wheels on the canvas line y = 4, the bonnet at 0.95 and the roof at 1.55.
        /// </summary>
        public static PixelCanvas Car()
        {
            var c = new PixelCanvas(400, 200);
            Color body = Grey(0.96f), glass = new Color(0.55f, 0.66f, 0.78f), dark = new Color(0.18f, 0.18f, 0.2f);
            c.FillRoundRect(6, 30, 394, 113, 26, body);
            c.FillPolygon(new[] { new Vector2(62, 110), new Vector2(300, 110), new Vector2(262, 182), new Vector2(96, 182) }, body);
            c.Shade((x, y) => y < 62 ? 1f : 0f, Grey(0.78f));                          // lower body in shadow
            c.FillPolygon(new[] { new Vector2(84, 116), new Vector2(172, 116), new Vector2(172, 172), new Vector2(106, 172) }, glass);
            c.FillPolygon(new[] { new Vector2(182, 116), new Vector2(284, 116), new Vector2(254, 172), new Vector2(182, 172) }, glass);
            c.FillPolygon(new[] { new Vector2(196, 120), new Vector2(214, 120), new Vector2(196, 160) }, Lighten(glass, 0.35f)); // glint
            c.FillRect(176, 40, 179, 108, Grey(0.8f));                                 // door line
            c.FillRect(150, 92, 168, 96, Grey(0.6f));                                  // handle
            c.FillRoundRect(368, 78, 392, 96, 5, new Color(1f, 0.93f, 0.6f));         // headlight
            c.FillRoundRect(8, 78, 22, 96, 4, new Color(0.9f, 0.3f, 0.28f));          // tail light
            c.FillRect(6, 30, 394, 40, Grey(0.5f));                                    // bumper line
            for (int i = 0; i < 2; i++)
            {
                float x = 88 + i * 224;
                c.FillCircle(x, 38, 36, Grey(0.85f));                                   // arch
                c.FillCircle(x, 36, 32, dark);
                c.FillCircle(x, 36, 14, Grey(0.75f));
            }
            c.Ink(Ink, 2.5f, 10);
            return c;
        }

        // ===================== App icon =====================

        /// <summary>
        /// Square app icon (no transparency, stores add their own mask): a warm
        /// sunrise, rolling hill, a big inked ball mid-bounce with speed lines,
        /// and a little school flag.
        /// </summary>
        public static PixelCanvas AppIcon(int size = 512)
        {
            var c = new PixelCanvas(size, size);
            float s = size / 512f;
            Color top = new Color(0.98f, 0.7f, 0.42f), bottom = new Color(1f, 0.9f, 0.62f);
            for (int y = 0; y < size; y++)
            {
                Color col = Color.Lerp(bottom, top, y / (float)size);
                for (int x = 0; x < size; x++) c.Set(x, y, col);
            }
            c.FillCircle(380 * s, 380 * s, 90 * s, new Color(1f, 0.95f, 0.72f));   // sun
            c.FillBelow(x => (120 + Mathf.Sin(x / size * Mathf.PI * 1.4f + 0.4f) * 40) * s, new Color(0.47f, 0.74f, 0.42f));
            c.FillBelow(x => (70 + Mathf.Sin(x / size * Mathf.PI * 2f + 2f) * 18) * s, new Color(0.38f, 0.64f, 0.36f));

            // School flag on a pole (right)
            c.FillRect(400 * s, 120 * s, 408 * s, 300 * s, new Color(0.35f, 0.28f, 0.24f));
            c.FillPolygon(new[] { new Vector2(408 * s, 300 * s), new Vector2(470 * s, 280 * s), new Vector2(408 * s, 258 * s) }, new Color(0.9f, 0.35f, 0.35f));

            c.Grain(0.08f, 21, 0.02f);

            // Speed lines
            for (int i = 0; i < 3; i++)
                c.Line(new Vector2((50 + i * 14) * s, (318 - i * 46) * s), new Vector2((150 + i * 14) * s, (318 - i * 46) * s), 14 * s, new Color(1f, 1f, 1f, 0.9f));

            // The ball on its own layer so it gets a proper ink outline.
            var layer = new PixelCanvas(size, size);
            Vector2 ball = new Vector2(262 * s, 262 * s);
            float r = 125 * s;
            System.Func<float, float, bool> inBall = (x, y) => (x - ball.x) * (x - ball.x) + (y - ball.y) * (y - ball.y) <= r * r;
            layer.FillCircle(ball.x, ball.y, r, Color.white);
            layer.Fill((x, y) => inBall(x, y) && InPentagon(x, y, ball.x, ball.y, r * 0.3f, 15f) ? 1f : 0f, Ink);
            for (int k = 0; k < 5; k++)
            {
                float ang = Mathf.Deg2Rad * (90 + 72 * k + 15);
                float px = ball.x + Mathf.Cos(ang) * r * 0.86f, py = ball.y + Mathf.Sin(ang) * r * 0.86f;
                layer.Fill((x, y) => inBall(x, y) && InPentagon(x, y, px, py, r * 0.27f, 15f + 36f) ? 1f : 0f, Ink);
            }
            // Seams from the centre patch to the outer ones.
            for (int k = 0; k < 5; k++)
            {
                float ang = Mathf.Deg2Rad * (90 + 72 * k + 51);
                layer.Line(ball + new Vector2(Mathf.Cos(ang), Mathf.Sin(ang)) * r * 0.32f,
                           ball + new Vector2(Mathf.Cos(ang), Mathf.Sin(ang)) * r * 0.62f, 4f * s, new Color(0.55f, 0.55f, 0.6f));
            }
            layer.Shade((x, y) =>
            {
                float dx = (x - ball.x) / r, dy = (y - ball.y) / r;
                return Mathf.Clamp01((dx - dy) * 0.45f) * 0.4f;
            }, new Color(0.55f, 0.6f, 0.75f));
            layer.Shade((x, y) => Mathf.Clamp01(1f - Vector2.Distance(new Vector2(x, y), ball + new Vector2(-0.4f, 0.45f) * r) / (r * 0.35f)) * 0.6f, Color.white);
            layer.Ink(Ink, 7f * s, 4);
            c.Stamp(layer);
            return c;
        }

        /// <summary>Point inside a regular pentagon centred at (cx, cy), rotated by <paramref name="rotationDeg"/>.</summary>
        static bool InPentagon(float x, float y, float cx, float cy, float radius, float rotationDeg)
        {
            float dx = x - cx, dy = y - cy;
            float ang = Mathf.Atan2(dy, dx) - rotationDeg * Mathf.Deg2Rad;
            float seg = Mathf.PI * 2f / 5f;
            float local = Mathf.Repeat(ang, seg) - seg * 0.5f;
            return Mathf.Sqrt(dx * dx + dy * dy) * Mathf.Cos(local) < radius * Mathf.Cos(seg * 0.5f);
        }

        // ===================== Particles & small things =====================

        public static PixelCanvas Puff()
        {
            var c = new PixelCanvas(64, 64);
            c.Fill((x, y) =>
            {
                float dx = x - 32, dy = y - 32;
                float d = Mathf.Sqrt(dx * dx + dy * dy) / 30f;
                return Mathf.Clamp01(1f - d * d);
            }, White);
            return c;
        }

        public static PixelCanvas Spark()
        {
            var c = new PixelCanvas(64, 64);
            c.FillPolygon(new[] { new Vector2(32, 2), new Vector2(38, 26), new Vector2(62, 32), new Vector2(38, 38), new Vector2(32, 62), new Vector2(26, 38), new Vector2(2, 32), new Vector2(26, 26) }, White);
            return c;
        }

        public static PixelCanvas Drop()
        {
            var c = new PixelCanvas(32, 48);
            c.FillCircle(16, 16, 12, White);
            c.FillPolygon(new[] { new Vector2(5, 20), new Vector2(27, 20), new Vector2(16, 46) }, White);
            return c;
        }

        public static PixelCanvas Shadow()
        {
            var c = new PixelCanvas(64, 32);
            c.Fill((x, y) =>
            {
                float dx = (x - 32) / 30f, dy = (y - 16) / 14f;
                float d = dx * dx + dy * dy;
                return Mathf.Clamp01(1f - d) * 0.9f;
            }, Ink);
            return c;
        }
    }
}
