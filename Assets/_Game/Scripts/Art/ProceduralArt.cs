using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Storybook art drawn in code: everything gets watercolour grain and a
    /// wobbly ink outline so it reads as one hand-drawn world. Tintable pieces
    /// are drawn in light greys so SpriteRenderer colours show through.
    /// </summary>
    public static class ProceduralArt
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
            c.Shade((x, y) => y < 14 ? (14 - y) / 14f * 0.25f : 0f, Grey(0.6f));
            c.Grain(0.12f, 3);
            c.Ink(Ink, 2.6f, 5);
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

        // ===================== Sky =====================

        /// <summary>Vertical sky gradient (stretched over the view).</summary>
        public static PixelCanvas Sky(Color top, Color bottom)
        {
            var c = new PixelCanvas(8, 256);
            for (int y = 0; y < 256; y++)
            {
                float t = Mathf.SmoothStep(0f, 1f, y / 255f);
                Color col = Color.Lerp(bottom, top, t);
                for (int x = 0; x < 8; x++) c.Set(x, y, col);
            }
            return c;
        }

        public static PixelCanvas Sun(Color color)
        {
            var c = new PixelCanvas(256, 256);
            for (int i = 6; i >= 1; i--)
                c.FillCircle(128, 128, 40 + i * 14, new Color(color.r, color.g, color.b, 0.06f));
            c.FillCircle(128, 128, 56, color);
            c.Grain(0.05f, 2);
            return c;
        }

        public static PixelCanvas Cloud(int seed)
        {
            var c = new PixelCanvas(256, 128);
            var rng = new System.Random(seed);
            int puffs = 4 + rng.Next(3);
            for (int i = 0; i < puffs; i++)
            {
                float x = 50 + i * (150f / puffs) + rng.Next(-10, 10);
                float r = 26 + rng.Next(0, 22);
                c.FillCircle(x, 50 + rng.Next(-6, 14), r, White);
            }
            c.FillRoundRect(30, 28, 226, 60, 20, White);
            c.Shade((x, y) => y < 45 ? (45 - y) / 45f * 0.3f : 0f, new Color(0.75f, 0.8f, 0.95f));
            c.Ink(new Color(0.55f, 0.6f, 0.75f, 0.6f), 2f, seed);
            return c;
        }

        // ===================== Far layer (tileable) =====================

        public static PixelCanvas Far(SceneryStyle style, Color color, int seed)
        {
            const int w = 512, h = 256;
            var c = new PixelCanvas(w, h);
            var rng = new System.Random(seed);
            switch (style)
            {
                case SceneryStyle.Beach:
                    // Sea with a soft horizon and wave crests.
                    c.FillBelow(x => 120f, color);
                    c.FillBelow(x => 70f, Mul(color, 0.9f));
                    for (int i = 0; i < 30; i++)
                    {
                        float x = (float)rng.NextDouble() * w, y = 20 + (float)rng.NextDouble() * 90;
                        c.Wrapped(o => c.Line(new Vector2(x + o, y), new Vector2(x + o + 18, y + 2), 2.5f, new Color(1f, 1f, 1f, 0.7f)));
                    }
                    for (int b = 0; b < 2; b++)
                    {
                        float bx = 100 + b * 230 + rng.Next(-20, 20);
                        c.FillPolygon(new[] { new Vector2(bx - 30, 120), new Vector2(bx + 30, 120), new Vector2(bx + 20, 108), new Vector2(bx - 20, 108) }, new Color(0.9f, 0.5f, 0.4f));
                        c.FillPolygon(new[] { new Vector2(bx, 122), new Vector2(bx, 175), new Vector2(bx + 28, 124) }, White);
                    }
                    break;
                case SceneryStyle.City:
                    for (int x = 0; x < w;)
                    {
                        int bw = Mathf.Min(30 + rng.Next(40), w - x);
                        int bh = 70 + rng.Next(120);
                        Color bc = Mul(color, 0.9f + (float)rng.NextDouble() * 0.15f);
                        c.FillRect(x, 0, x + bw - 3, bh, bc);
                        for (int wy = 12; wy < bh - 10; wy += 16)
                            for (int wx = x + 5; wx < x + bw - 10; wx += 10)
                                if (rng.NextDouble() < 0.6) c.FillRect(wx, wy, wx + 4, wy + 7, Mul(bc, 1.15f));
                        x += bw;
                    }
                    break;
                default:
                    // Rolling hills; parks get round tree tops along the ridge.
                    float phase = (float)rng.NextDouble() * 6f;
                    System.Func<float, float> ridge = x => 110f + Mathf.Sin(x / w * Mathf.PI * 2f + phase) * 30f + Mathf.Sin(x / w * Mathf.PI * 6f + phase * 2f) * 12f;
                    c.FillBelow(ridge, color);
                    if (style == SceneryStyle.Park || style == SceneryStyle.Houses)
                        for (int i = 0; i < 18; i++)
                        {
                            float x = (float)rng.NextDouble() * w;
                            float r = 10f + (float)rng.NextDouble() * 10f;
                            c.Wrapped(o => c.FillCircle(x + o, ridge(x) + 4f, r, Mul(color, 0.88f)));
                        }
                    if (style == SceneryStyle.Market)
                        for (int i = 0; i < 4; i++)
                        {
                            float x = 60 + i * 120 + rng.Next(-20, 20);
                            float top = ridge(x);
                            c.FillRect(x - 10, top - 10, x + 10, top + 60, Mul(color, 0.85f));   // church/tower
                            c.FillPolygon(new[] { new Vector2(x - 14, top + 60), new Vector2(x + 14, top + 60), new Vector2(x, top + 90) }, Mul(color, 0.75f));
                        }
                    break;
            }
            c.Grain(0.1f, seed, 0.03f, true);
            c.Ink(new Color(Ink.r, Ink.g, Ink.b, 0.35f), 1.5f, seed, true);
            return c;
        }

        // ===================== Mid layer props =====================

        /// <summary>One of several scenery props for the chapter (house, shop, palm, crane, tree...).</summary>
        public static PixelCanvas MidProp(SceneryStyle style, int variant, Color tint)
        {
            switch (style)
            {
                case SceneryStyle.Market: return Shop(variant, tint);
                case SceneryStyle.Beach: return variant % 2 == 0 ? Palm(variant) : BeachHut(variant);
                case SceneryStyle.City: return variant % 2 == 0 ? CraneProp(variant) : Pillar(variant);
                case SceneryStyle.Park: return variant == 2 ? School() : Tree(variant, tint);
                default: return variant == 2 ? Tree(variant, new Color(0.45f, 0.68f, 0.42f)) : House(variant, tint);
            }
        }

        static readonly Color[] Walls =
        {
            new Color(0.97f, 0.86f, 0.72f), new Color(0.92f, 0.72f, 0.62f), new Color(0.86f, 0.86f, 0.76f),
            new Color(0.96f, 0.8f, 0.56f), new Color(0.82f, 0.77f, 0.88f),
        };

        static PixelCanvas House(int variant, Color tint)
        {
            var c = new PixelCanvas(256, 256);
            Color wall = Walls[variant % Walls.Length];
            Color roof = new Color(0.78f, 0.4f, 0.34f);
            c.FillRect(40, 0, 216, 150, wall);
            c.FillPolygon(new[] { new Vector2(28, 148), new Vector2(228, 148), new Vector2(128, 230) }, roof);
            c.FillRect(170, 175, 190, 230, Mul(roof, 0.8f));   // chimney
            for (int i = 0; i < 2; i++)
            {
                float x = 70 + i * 90;
                c.FillRoundRect(x, 85, x + 34, 125, 4, new Color(1f, 0.95f, 0.72f));
                c.FillRect(x + 15, 85, x + 19, 125, wall);
            }
            c.FillRoundRect(112, 0, 144, 60, 10, new Color(0.5f, 0.35f, 0.3f));
            c.Grain(0.12f, variant + 20);
            c.Ink(Ink, 2.5f, variant);
            return c;
        }

        static PixelCanvas Shop(int variant, Color tint)
        {
            var c = new PixelCanvas(256, 256);
            Color wall = Walls[(variant + 2) % Walls.Length];
            Color[] awn = { new Color(0.9f, 0.35f, 0.35f), new Color(0.35f, 0.6f, 0.85f), new Color(0.45f, 0.7f, 0.4f) };
            Color a = awn[variant % awn.Length];
            c.FillRect(30, 0, 226, 210, wall);
            c.FillRect(24, 205, 232, 222, Mul(wall, 0.85f));
            c.FillRoundRect(50, 150, 206, 190, 6, White);   // sign
            c.FillRect(70, 166, 186, 174, Mul(a, 0.8f));
            c.FillRect(50, 20, 150, 115, new Color(0.75f, 0.88f, 0.95f));   // window
            c.FillRoundRect(165, 0, 205, 95, 8, new Color(0.5f, 0.35f, 0.3f));
            for (int i = 0; i < 8; i++)
                c.FillPolygon(new[] { new Vector2(30 + i * 24.5f, 140), new Vector2(54.5f + i * 24.5f, 140), new Vector2(42 + i * 24.5f, 118) }, i % 2 == 0 ? a : White);
            for (int i = 0; i < 4; i++) c.FillCircle(70 + i * 22, 30, 9, new[] { new Color(1f, 0.6f, 0.2f), new Color(0.9f, 0.25f, 0.3f), new Color(0.95f, 0.85f, 0.3f), new Color(0.5f, 0.75f, 0.3f) }[i]);
            c.Grain(0.12f, variant + 40);
            c.Ink(Ink, 2.5f, variant + 3);
            return c;
        }

        static PixelCanvas Palm(int variant)
        {
            var c = new PixelCanvas(256, 256);
            Color trunk = new Color(0.68f, 0.5f, 0.32f), leaf = new Color(0.35f, 0.65f, 0.35f);
            float lean = variant % 4 == 0 ? 18f : -14f;
            for (int i = 0; i < 9; i++)
            {
                float t = i / 9f;
                c.FillEllipse(128 + lean * t * t, 10 + t * 175, 13 - t * 4, 12, Mul(trunk, i % 2 == 0 ? 1f : 0.88f));
            }
            Vector2 top = new Vector2(128 + lean, 195);
            for (int i = 0; i < 6; i++)
            {
                float ang = Mathf.Deg2Rad * (20 + i * 28);
                Vector2 tip = top + new Vector2(Mathf.Cos(ang), Mathf.Sin(ang) * 0.55f - 0.35f) * 85f;
                c.FillPolygon(new[] { top, top + (tip - top) * 0.5f + new Vector2(0, 12), tip, top + (tip - top) * 0.5f - new Vector2(0, 6) }, Mul(leaf, 0.9f + i % 2 * 0.15f));
            }
            c.FillCircle(top.x - 6, top.y - 6, 7, new Color(0.5f, 0.35f, 0.2f));
            c.FillCircle(top.x + 6, top.y - 8, 7, new Color(0.5f, 0.35f, 0.2f));
            c.Grain(0.12f, variant + 60);
            c.Ink(Ink, 2.5f, variant + 5);
            return c;
        }

        static PixelCanvas BeachHut(int variant)
        {
            var c = new PixelCanvas(256, 256);
            Color[] stripes = { new Color(0.4f, 0.65f, 0.9f), new Color(0.95f, 0.5f, 0.5f), new Color(0.95f, 0.8f, 0.3f) };
            Color s = stripes[variant % stripes.Length];
            for (int i = 0; i < 8; i++) c.FillRect(60 + i * 17, 0, 77 + i * 17, 150, i % 2 == 0 ? s : White);
            c.FillPolygon(new[] { new Vector2(48, 148), new Vector2(208, 148), new Vector2(128, 205) }, Mul(s, 0.75f));
            c.FillRoundRect(110, 0, 146, 80, 8, White);
            c.Grain(0.1f, variant + 70);
            c.Ink(Ink, 2.5f, variant + 6);
            return c;
        }

        static PixelCanvas CraneProp(int variant)
        {
            var c = new PixelCanvas(256, 256);
            Color y = new Color(0.95f, 0.72f, 0.25f);
            c.FillRect(110, 0, 130, 230, y);
            for (int i = 0; i < 11; i++) c.Line(new Vector2(110, i * 21), new Vector2(130, i * 21 + 21), 3, Mul(y, 0.75f));
            c.FillRect(20, 220, 250, 236, y);
            for (int i = 0; i < 11; i++) c.Line(new Vector2(20 + i * 21, 220), new Vector2(41 + i * 21, 236), 3, Mul(y, 0.75f));
            c.Line(new Vector2(200, 220), new Vector2(200, 140), 2, Ink);
            c.FillRect(188, 120, 212, 140, new Color(0.5f, 0.5f, 0.55f));
            c.FillRect(30, 200, 60, 220, new Color(0.45f, 0.45f, 0.5f));
            c.Grain(0.1f, variant + 80);
            c.Ink(Ink, 2.2f, variant + 7);
            return c;
        }

        static PixelCanvas Pillar(int variant)
        {
            var c = new PixelCanvas(256, 256);
            Color con = new Color(0.66f, 0.66f, 0.7f);
            c.FillRect(0, 200, 256, 240, con);
            c.FillRect(90, 0, 166, 200, Mul(con, 0.92f));
            c.FillRect(100, 60, 156, 120, new Color(0.9f, 0.5f, 0.6f));   // poster / graffiti
            c.FillCircle(128, 90, 18, new Color(0.4f, 0.75f, 0.9f));
            c.Grain(0.14f, variant + 90);
            c.Ink(Ink, 2.5f, variant + 8);
            return c;
        }

        static PixelCanvas Tree(int variant, Color tint)
        {
            var c = new PixelCanvas(256, 256);
            Color leaf = variant % 3 == 1 ? new Color(0.5f, 0.72f, 0.4f) : new Color(0.38f, 0.62f, 0.38f);
            c.FillRoundRect(116, 0, 140, 120, 8, new Color(0.55f, 0.38f, 0.26f));
            var rng = new System.Random(variant * 13 + 1);
            for (int i = 0; i < 7; i++)
                c.FillCircle(128 + rng.Next(-55, 55), 150 + rng.Next(-25, 45), 38 + rng.Next(0, 18), Mul(leaf, 0.9f + (float)rng.NextDouble() * 0.2f));
            for (int i = 0; i < 5; i++)
                c.FillCircle(128 + rng.Next(-50, 50), 150 + rng.Next(-20, 40), 5, new Color(0.95f, 0.45f, 0.4f));
            c.Grain(0.12f, variant + 100);
            c.Ink(Ink, 2.5f, variant + 9);
            return c;
        }

        static PixelCanvas School()
        {
            var c = new PixelCanvas(256, 256);
            Color brick = new Color(0.82f, 0.48f, 0.4f);
            c.FillRect(10, 0, 246, 170, brick);
            c.FillPolygon(new[] { new Vector2(0, 168), new Vector2(256, 168), new Vector2(128, 230) }, new Color(0.45f, 0.4f, 0.5f));
            c.FillCircle(128, 192, 16, White);
            c.Line(new Vector2(128, 192), new Vector2(128, 203), 2, Ink);
            c.Line(new Vector2(128, 192), new Vector2(136, 192), 2, Ink);
            for (int r = 0; r < 2; r++)
                for (int i = 0; i < 5; i++)
                    c.FillRoundRect(28 + i * 44, 50 + r * 60, 56 + i * 44, 90 + r * 60, 4, new Color(1f, 0.95f, 0.75f));
            c.FillRoundRect(108, 0, 148, 45, 10, new Color(0.45f, 0.32f, 0.28f));
            c.Grain(0.12f, 120);
            c.Ink(Ink, 2.5f, 12);
            return c;
        }

        // ===================== Near layer (tileable) =====================

        public static PixelCanvas Near(SceneryStyle style, Color color, int seed)
        {
            const int w = 256, h = 96;
            var c = new PixelCanvas(w, h);
            var rng = new System.Random(seed);
            switch (style)
            {
                case SceneryStyle.Market:
                    // Bunting strings
                    for (int s = 0; s < 2; s++)
                    {
                        float baseY = 70 - s * 12;
                        for (int i = 0; i < 12; i++)
                        {
                            float x = i * 21.3f;
                            float sag = Mathf.Sin(i / 12f * Mathf.PI) * 10f;
                            Color f = new[] { new Color(0.95f, 0.4f, 0.4f), new Color(0.95f, 0.8f, 0.3f), new Color(0.4f, 0.65f, 0.9f), new Color(0.5f, 0.78f, 0.45f) }[(i + s) % 4];
                            c.FillPolygon(new[] { new Vector2(x, baseY - sag), new Vector2(x + 16, baseY - sag), new Vector2(x + 8, baseY - sag - 16) }, f);
                        }
                    }
                    break;
                case SceneryStyle.City:
                    // Site fence with hazard stripes
                    c.FillRect(0, 0, w, 50, color);
                    for (int i = 0; i < 16; i++) c.FillRect(i * 16, 50, i * 16 + 3, 70, Mul(color, 0.7f));
                    for (int i = 0; i < 8; i++)
                        c.FillPolygon(new[] { new Vector2(i * 32, 30), new Vector2(i * 32 + 16, 30), new Vector2(i * 32 + 26, 42), new Vector2(i * 32 + 10, 42) }, new Color(0.95f, 0.8f, 0.2f));
                    break;
                case SceneryStyle.Beach:
                    // Dune grass tufts
                    c.FillBelow(x => 18f + Mathf.Sin(x / w * Mathf.PI * 4f) * 6f, color);
                    for (int i = 0; i < 30; i++)
                    {
                        float x = (float)rng.NextDouble() * w;
                        float lean = rng.Next(-8, 8), top = 40 + rng.Next(0, 25);
                        c.Wrapped(o => c.Line(new Vector2(x + o, 15), new Vector2(x + o + lean, top), 2.5f, new Color(0.55f, 0.65f, 0.35f)));
                    }
                    break;
                default:
                    // Hedges / bushes with flowers
                    for (int i = 0; i < 10; i++)
                    {
                        float bx = i * 25.6f + rng.Next(-4, 4), by = 20 + rng.Next(0, 16), br = 22 + rng.Next(0, 10);
                        Color bc = Mul(color, 0.9f + (float)rng.NextDouble() * 0.2f);
                        c.Wrapped(o => c.FillCircle(bx + o, by, br, bc));
                    }
                    c.FillRect(0, 0, w, 22, color);
                    for (int i = 0; i < 12; i++)
                    {
                        float fx = (float)rng.NextDouble() * w, fy = 25 + (float)rng.NextDouble() * 25;
                        Color fc = new[] { White, new Color(1f, 0.8f, 0.3f), new Color(1f, 0.55f, 0.6f) }[i % 3];
                        c.Wrapped(o => c.FillCircle(fx + o, fy, 3, fc));
                    }
                    break;
            }
            c.Grain(0.12f, seed, 0.06f, true);
            c.Ink(new Color(Ink.r, Ink.g, Ink.b, 0.8f), 2f, seed, true);
            return c;
        }

        // ===================== Characters =====================

        /// <summary>Kid and pedestrian parts. Shirt, shorts and hair are light grey so they can be tinted.</summary>
        public static PixelCanvas Part(string name)
        {
            Color skin = new Color(0.98f, 0.8f, 0.66f);
            switch (name)
            {
                case "Head":
                {
                    var c = new PixelCanvas(128, 128);
                    c.FillCircle(64, 64, 58, skin);
                    c.FillEllipse(100, 52, 10, 8, new Color(1f, 0.6f, 0.55f, 0.6f));   // cheek
                    c.Grain(0.06f, 1);
                    c.Ink(Ink, 3.5f, 1);
                    return c;
                }
                case "Hair":
                {
                    // Messy mop: a cap over the top and back of the head with a tufty fringe at the front (facing right).
                    var c = new PixelCanvas(128, 128);
                    c.Fill((x, y) =>
                    {
                        float dx = x - 64, dy = y - 64;
                        bool head = dx * dx + dy * dy < 63 * 63;
                        bool cap = y > 74 - (x - 64) * 0.18f;
                        bool back = x < 44 && y > 30;
                        return head && (cap || back) ? 1f : 0f;
                    }, Grey(0.95f));
                    c.FillCircle(84, 80, 13, Grey(0.95f));
                    c.FillCircle(100, 76, 12, Grey(0.95f));
                    c.FillCircle(113, 70, 9, Grey(0.95f));
                    c.FillCircle(50, 118, 12, Grey(0.95f));   // tuft on top
                    c.Grain(0.12f, 2);
                    c.Ink(Ink, 3.5f, 2);
                    return c;
                }
                case "Eye":
                {
                    var c = new PixelCanvas(32, 32);
                    c.FillCircle(16, 16, 13, Ink);
                    c.FillCircle(12, 20, 4, White);
                    return c;
                }
                case "Torso":
                {
                    var c = new PixelCanvas(96, 128);
                    c.FillRoundRect(4, 4, 92, 124, 26, Grey(0.97f));
                    c.FillRect(40, 108, 56, 124, Grey(0.85f));   // collar shadow
                    c.Grain(0.1f, 3);
                    c.Ink(Ink, 3f, 3);
                    return c;
                }
                case "Shorts":
                {
                    var c = new PixelCanvas(96, 64);
                    c.FillRoundRect(4, 4, 92, 60, 14, Grey(0.95f));
                    c.FillRect(46, 4, 50, 34, Grey(0.7f));
                    c.Grain(0.1f, 4);
                    c.Ink(Ink, 3f, 4);
                    return c;
                }
                case "Leg":
                {
                    var c = new PixelCanvas(48, 128);
                    c.FillRoundRect(12, 30, 36, 124, 11, skin);
                    c.FillRect(12, 30, 36, 56, White);   // sock
                    c.FillRect(12, 46, 36, 52, new Color(0.4f, 0.55f, 0.85f));
                    c.FillRoundRect(6, 4, 46, 32, 12, new Color(0.25f, 0.25f, 0.3f));   // shoe
                    c.FillRect(6, 4, 46, 9, White);
                    c.Ink(Ink, 3f, 5);
                    return c;
                }
                case "Arm":
                {
                    var c = new PixelCanvas(40, 112);
                    c.FillRoundRect(8, 4, 32, 108, 12, skin);
                    c.Ink(Ink, 3f, 6);
                    return c;
                }
                case "Backpack":
                {
                    var c = new PixelCanvas(64, 96);
                    c.FillRoundRect(4, 4, 60, 92, 16, new Color(0.88f, 0.48f, 0.32f));
                    c.FillRoundRect(12, 14, 52, 46, 8, new Color(0.95f, 0.62f, 0.4f));
                    c.Grain(0.1f, 7);
                    c.Ink(Ink, 3f, 7);
                    return c;
                }
                default:
                    return new PixelCanvas(4, 4);
            }
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
        public static PixelCanvas Car()
        {
            var c = new PixelCanvas(320, 160);
            Color body = Grey(0.96f);
            c.FillRoundRect(8, 32, 312, 100, 22, body);
            c.FillPolygon(new[] { new Vector2(70, 98), new Vector2(240, 98), new Vector2(210, 150), new Vector2(100, 150) }, body);
            c.FillPolygon(new[] { new Vector2(92, 102), new Vector2(150, 102), new Vector2(150, 140), new Vector2(110, 140) }, new Color(0.7f, 0.85f, 0.95f));
            c.FillPolygon(new[] { new Vector2(160, 102), new Vector2(222, 102), new Vector2(200, 140), new Vector2(160, 140) }, new Color(0.7f, 0.85f, 0.95f));
            c.FillRoundRect(290, 62, 312, 76, 4, new Color(1f, 0.92f, 0.5f));
            for (int i = 0; i < 2; i++)
            {
                float x = 76 + i * 168;
                c.FillCircle(x, 34, 30, new Color(0.18f, 0.18f, 0.2f));
                c.FillCircle(x, 34, 13, Grey(0.75f));
            }
            c.Grain(0.08f, 10);
            c.Ink(Ink, 3f, 10);
            return c;
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
