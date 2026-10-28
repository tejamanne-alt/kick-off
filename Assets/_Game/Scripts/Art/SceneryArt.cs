using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Backgrounds in a bright anime look: saturated blue skies, big cumulus clouds with
    /// hard cel shadows, and scenery painted in flat colour with one shadow tone and no
    /// outlines. Light comes from the upper right, so shadows fall to the lower left.
    /// Layers: sky gradient, clouds, a tileable far strip, large mid props, an optional
    /// tileable line of utility poles with sagging wires, and a near strip.
    /// </summary>
    public static partial class ProceduralArt
    {
        // ===================== Sky =====================

        /// <summary>Vertical sky gradient (stretched over the view).</summary>
        public static PixelCanvas Sky(Color top, Color bottom)
        {
            var c = new PixelCanvas(8, 256);
            for (int y = 0; y < 256; y++)
            {
                float t = Mathf.Pow(y / 255f, 0.8f);
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
            return c;
        }

        /// <summary>
        /// A towering cumulus: a lumpy base row with two to four puff towers rising from it.
        /// Puffs are painted top-down, each as a blue shadow disc with a white lit disc nudged
        /// toward the light, so every lump in front shows its own hard-edged shadow crescent.
        /// The flat underside gets a deeper band. Seed % 3 == 2 gives a low cloud bank instead.
        /// </summary>
        public static PixelCanvas Cloud(int seed)
        {
            const int w = 512, h = 288;
            var c = new PixelCanvas(w, h);
            var rng = new System.Random(seed);
            bool bank = seed % 3 == 2;
            const float baseY = 40f;
            var puffs = new List<Vector3>();
            int n = bank ? 22 : 13;
            for (int i = 0; i < n; i++)
            {
                float t = (i + 0.5f) / n;
                float r = bank ? Rand(rng, 18f, 28f) : Rand(rng, 30f, 44f) * (0.75f + 0.25f * Mathf.Sin(Mathf.PI * t));
                puffs.Add(new Vector3(36f + t * 440f + rng.Next(-10, 10), baseY + r * 0.55f, r));
            }
            int towers = bank ? 0 : 2 + rng.Next(3);
            for (int k = 0; k < towers; k++)
            {
                float tx = Rand(rng, 120f, 392f), top = baseY + Rand(rng, 80f, 190f), r0 = Rand(rng, 46f, 66f);
                float y = baseY + r0 * 0.7f;
                for (int j = 0; y < top && r0 * (1f - j * 0.1f) > 14f; j++)
                {
                    float r = r0 * (1f - j * 0.1f);
                    puffs.Add(new Vector3(tx + Rand(rng, -0.35f, 0.35f) * r, y, r));
                    if (rng.NextDouble() < 0.6) puffs.Add(new Vector3(tx + Rand(rng, -0.9f, 0.9f) * r, y - r * 0.2f, r * Rand(rng, 0.5f, 0.75f)));
                    y += r * 0.62f;
                }
            }
            // Small bumps along the upper edge of the bigger puffs.
            int count = puffs.Count;
            for (int i = 0; i < count; i++)
            {
                Vector3 p = puffs[i];
                if (p.z < 24f) continue;
                for (int k = 0; k < 2; k++)
                {
                    float a = Mathf.Deg2Rad * Rand(rng, 30f, 150f);
                    puffs.Add(new Vector3(p.x + Mathf.Cos(a) * p.z * 0.82f, p.y + Mathf.Sin(a) * p.z * 0.78f, p.z * Rand(rng, 0.26f, 0.4f)));
                }
            }
            puffs.Sort((p, q) => q.y.CompareTo(p.y));   // top first, so lower lumps sit in front

            Color shadow = new Color(0.74f, 0.86f, 0.97f);
            foreach (var p in puffs)
            {
                Vector3 q = p;
                c.Fill((x, y) => y >= baseY && (x - q.x) * (x - q.x) + (y - q.y) * (y - q.y) <= q.z * q.z ? 1f : 0f, shadow,
                    (int)(q.x - q.z) - 1, (int)Mathf.Max(baseY, q.y - q.z) - 1, (int)(q.x + q.z) + 1, (int)(q.y + q.z) + 1);
                float lx = q.x + q.z * 0.13f, ly = q.y + q.z * 0.22f, lr = q.z * 0.8f;
                c.Fill((x, y) => y >= baseY + 6f && (x - lx) * (x - lx) + (y - ly) * (y - ly) <= lr * lr ? 1f : 0f, White,
                    (int)(lx - lr) - 1, (int)Mathf.Max(baseY, ly - lr) - 1, (int)(lx + lr) + 1, (int)(ly + lr) + 1);
            }
            c.Shade((x, y) => y < baseY + 12f + Mathf.Sin(x * 0.045f + seed) * 4f ? 1f : 0f, new Color(0.6f, 0.75f, 0.92f));
            return c;
        }

        static float Rand(System.Random rng, float min, float max) { return min + (float)rng.NextDouble() * (max - min); }
        static Color Lighten(Color c, float k) { return Color.Lerp(c, White, k); }

        /// <summary>
        /// Anime foliage: a cluster of leafy clumps, each with a dark underside and a lit top
        /// nudged toward the light, plus a few bright flecks.
        /// </summary>
        static void Foliage(PixelCanvas c, float cx, float cy, float rx, float ry, Color light, Color dark, int seed, int clumps = 36, bool wrap = false)
        {
            var rng = new System.Random(seed);
            var list = new List<Vector3>();
            float size = (rx + ry) * 0.5f;
            for (int i = 0; i < clumps; i++)
            {
                float a = (float)rng.NextDouble() * Mathf.PI * 2f, d = Mathf.Sqrt((float)rng.NextDouble());
                list.Add(new Vector3(cx + Mathf.Cos(a) * rx * d, cy + Mathf.Sin(a) * ry * d, size * Rand(rng, 0.16f, 0.28f)));
            }
            list.Sort((p, q) => p.y.CompareTo(q.y));
            System.Action<System.Action<float>> draw = action => { if (wrap) c.Wrapped(action); else action(0f); };
            foreach (var p in list) { Vector3 q = p; draw(o => c.FillCircle(q.x + o, q.y, q.z, dark)); }
            foreach (var p in list)
            {
                Vector3 q = p;
                // Clumps on the lit (upper right) side of the tree catch more light.
                float side = Mathf.Clamp01(0.5f + (q.x - cx) / (rx * 2f) + (q.y - cy) / (ry * 2f));
                Color lit = Color.Lerp(Color.Lerp(dark, light, 0.55f), light, side);
                draw(o => c.FillCircle(q.x + o + q.z * 0.18f, q.y + q.z * 0.26f, q.z * 0.74f, lit));
                if (rng.NextDouble() < 0.35)
                    draw(o => c.FillCircle(q.x + o + q.z * 0.34f, q.y + q.z * 0.46f, q.z * 0.28f, Lighten(light, 0.35f)));
            }
        }

        static void Trunk(PixelCanvas c, Vector2 from, Vector2 to, float width, Color bark)
        {
            c.Line(from, to, width, bark);
            c.Line(from + new Vector2(width * 0.2f, 0f), to + new Vector2(width * 0.2f, 0f), width * 0.45f, Lighten(bark, 0.18f));
        }

        /// <summary>Aluminium-framed sliding window with a small metal eave above it.</summary>
        static void Window(PixelCanvas c, float x0, float y0, float x1, float y1, bool eave = true)
        {
            Color frame = new Color(0.86f, 0.87f, 0.89f), glass = new Color(0.36f, 0.43f, 0.53f);
            c.FillRect(x0, y0, x1, y1, frame);
            c.FillRect(x0 + 6, y0 + 6, x1 - 6, y1 - 6, glass);
            float mx = (x0 + x1) * 0.5f;
            c.FillRect(mx - 3, y0 + 6, mx + 3, y1 - 6, frame);
            // Sky reflection streak
            c.FillPolygon(new[] { new Vector2(x0 + 10, y0 + 8), new Vector2(x0 + 22, y0 + 8), new Vector2(mx - 6, y1 - 8), new Vector2(mx - 18, y1 - 8) }, new Color(0.55f, 0.63f, 0.72f));
            c.FillRect(x0 + 6, y1 - 14, x1 - 6, y1 - 6, new Color(0.28f, 0.33f, 0.42f));   // shade from the eave
            if (eave)
            {
                c.FillRect(x0 - 12, y1 + 4, x1 + 12, y1 + 16, new Color(0.5f, 0.53f, 0.58f));
                for (float x = x0 - 8; x < x1 + 10; x += 10) c.FillRect(x, y1 + 4, x + 2, y1 + 16, new Color(0.4f, 0.43f, 0.48f));
                c.FillRect(x0 - 12, y1 + 14, x1 + 12, y1 + 18, new Color(0.88f, 0.89f, 0.9f));
            }
        }

        // ===================== Far layer (tileable) =====================

        public static PixelCanvas Far(SceneryStyle style, Color color, int seed)
        {
            const int w = 512, h = 256;
            var c = new PixelCanvas(w, h);
            var rng = new System.Random(seed);
            float ph = (float)rng.NextDouble() * 6f;
            switch (style)
            {
                case SceneryStyle.Beach:
                {
                    // Sea from the horizon (deep blue) to the shallows (turquoise), with foam dashes.
                    const float horizon = 150f;
                    for (int y = 0; y < horizon; y++)
                    {
                        float t = Mathf.Pow(y / horizon, 1.4f);
                        c.FillRect(0, y, w, y + 1, Color.Lerp(new Color(0.3f, 0.74f, 0.86f), new Color(0.11f, 0.37f, 0.7f), t));
                    }
                    for (int i = 0; i < 70; i++)
                    {
                        float y = horizon * Mathf.Pow((float)rng.NextDouble(), 1.6f);
                        float len = Mathf.Lerp(46f, 8f, y / horizon) * Rand(rng, 0.5f, 1.2f);
                        float x = (float)rng.NextDouble() * w;
                        float th = Mathf.Lerp(3f, 1.2f, y / horizon);
                        c.Wrapped(o => c.Line(new Vector2(x + o, y), new Vector2(x + o + len, y), th, new Color(1f, 1f, 1f, 0.85f)));
                    }
                    c.FillRect(0, 0, w, 6, new Color(0.92f, 0.97f, 1f));               // shore foam
                    // A wooded headland on the horizon
                    c.Fill((x, y) =>
                    {
                        if (x > 220) return 0f;
                        float top = horizon + 34f * Mathf.Sin(Mathf.Clamp01(x / 220f) * Mathf.PI) * (x < 110 ? 1f : 0.8f);
                        return y >= horizon - 2 && y <= top ? 1f : 0f;
                    }, new Color(0.2f, 0.42f, 0.38f));
                    Foliage(c, 80, horizon + 22, 70, 14, new Color(0.34f, 0.56f, 0.44f), new Color(0.2f, 0.42f, 0.38f), seed, 22);
                    return c;
                }
                case SceneryStyle.City:
                {
                    Color back = new Color(0.62f, 0.7f, 0.84f), front = new Color(0.5f, 0.58f, 0.72f);
                    Skyline(c, rng, back, 110, 210, 34, 70, false);
                    Skyline(c, rng, front, 50, 130, 26, 54, true);
                    c.FillRect(0, 42, w, 56, new Color(0.56f, 0.62f, 0.72f));          // elevated expressway
                    c.FillRect(0, 54, w, 58, new Color(0.7f, 0.75f, 0.82f));
                    for (int i = 0; i < 4; i++) c.FillRect(i * 128 + 60, 0, i * 128 + 72, 42, new Color(0.52f, 0.58f, 0.68f));
                    return c;
                }
                case SceneryStyle.Market:
                {
                    Color back = new Color(0.66f, 0.74f, 0.86f), front = new Color(0.78f, 0.8f, 0.86f);
                    Skyline(c, rng, back, 90, 170, 40, 80, false);
                    int x = 0;
                    while (x < w)
                    {
                        int bw = Mathf.Min(40 + rng.Next(40), w - x), bh = 46 + rng.Next(50);
                        c.FillRect(x + 2, 0, x + bw - 2, bh, front);
                        c.FillRect(x + 2, bh - 10, x + bw - 2, bh, Lighten(front, 0.2f));
                        Color sign = new[] { new Color(0.85f, 0.5f, 0.5f), new Color(0.5f, 0.66f, 0.85f), new Color(0.9f, 0.8f, 0.5f) }[rng.Next(3)];
                        c.FillRect(x + 8, bh - 28, x + bw - 8, bh - 18, Color.Lerp(sign, back, 0.35f));
                        x += bw;
                    }
                    return c;
                }
                case SceneryStyle.Park:
                {
                    c.FillBelow(x => 120f + Mathf.Sin(x / w * Mathf.PI * 2f + ph) * 18f + Mathf.Sin(x / w * Mathf.PI * 6f) * 6f, new Color(0.6f, 0.75f, 0.85f));
                    c.FillRect(0, 0, w, 50, new Color(0.33f, 0.52f, 0.46f));
                    for (int i = 0; i < 8; i++)
                    {
                        float x = i * 64f + rng.Next(-10, 10);
                        bool cherry = i % 4 == 1;
                        Foliage(c, x, 62 + rng.Next(0, 16), 40, 30,
                            cherry ? new Color(0.98f, 0.82f, 0.88f) : new Color(0.5f, 0.7f, 0.56f),
                            cherry ? new Color(0.86f, 0.62f, 0.72f) : new Color(0.33f, 0.52f, 0.46f), seed + i, 18, true);
                    }
                    return c;
                }
                default:
                {
                    // Suburb: misty mountains, a band of trees and a row of distant rooftops.
                    c.FillBelow(px => 150f + Mathf.Sin(px / w * Mathf.PI * 2f + ph) * 22f + Mathf.Sin(px / w * Mathf.PI * 6f + ph * 2f) * 10f, new Color(0.62f, 0.75f, 0.89f));
                    c.FillRect(0, 0, w, 56, new Color(0.42f, 0.58f, 0.64f));
                    for (int i = 0; i < 9; i++)
                        Foliage(c, i * 57f + rng.Next(0, 20), 64 + rng.Next(0, 18), 34, 22, new Color(0.52f, 0.68f, 0.7f), new Color(0.42f, 0.58f, 0.64f), seed + i, 14, true);
                    int x = 0;
                    while (x < w)
                    {
                        int bw = Mathf.Min(30 + rng.Next(28), w - x), bh = 24 + rng.Next(24);
                        Color wall = rng.NextDouble() < 0.5 ? new Color(0.86f, 0.9f, 0.95f) : new Color(0.78f, 0.84f, 0.9f);
                        Color roof = rng.NextDouble() < 0.7 ? new Color(0.42f, 0.5f, 0.62f) : new Color(0.72f, 0.48f, 0.46f);
                        c.FillRect(x + 2, 0, x + bw - 2, bh, wall);
                        c.FillPolygon(new[] { new Vector2(x, bh), new Vector2(x + bw, bh), new Vector2(x + bw * 0.5f, bh + 13) }, roof);
                        c.FillRect(x + bw * 0.3f, bh * 0.4f, x + bw * 0.55f, bh * 0.7f, Color.Lerp(wall, roof, 0.5f));
                        x += bw + rng.Next(0, 10);
                    }
                    return c;
                }
            }
        }

        static void Skyline(PixelCanvas c, System.Random rng, Color color, int minH, int maxH, int minW, int maxW, bool windows)
        {
            int x = 0;
            while (x < c.Width)
            {
                int bw = Mathf.Min(minW + rng.Next(maxW - minW), c.Width - x), bh = minH + rng.Next(maxH - minH);
                Color bc = Color.Lerp(color, White, (float)rng.NextDouble() * 0.12f);
                c.FillRect(x + 1, 0, x + bw - 1, bh, bc);
                c.FillRect(x + 1, 0, x + bw * 0.3f, bh, Color.Lerp(bc, new Color(0.3f, 0.36f, 0.5f), 0.12f));   // shadow side
                if (windows)
                    for (int wy = 10; wy < bh - 8; wy += 12)
                        for (int wx = x + 6; wx < x + bw - 8; wx += 9)
                            c.FillRect(wx, wy, wx + 4, wy + 6, Lighten(bc, 0.25f));
                x += bw;
            }
        }

        // ===================== Utility poles (tileable) =====================

        /// <summary>
        /// One concrete utility pole per tile with a crossarm, a transformer and wires that sag
        /// across to the next pole, so the strip tiles into an endless pole line.
        /// </summary>
        public static PixelCanvas PoleLine(int seed)
        {
            const int w = 512, h = 512;
            var c = new PixelCanvas(w, h);
            const float px = 256f;
            Color wire = new Color(0.14f, 0.14f, 0.18f);
            float[] anchorsX = { -56f, 56f, -40f, 0f };
            float[] anchorsY = { 436f, 436f, 380f, 470f };
            float[] sags = { 46f, 52f, 40f, 60f };
            for (int i = 0; i < anchorsX.Length; i++)
            {
                float ax = px + anchorsX[i], ay = anchorsY[i], sag = sags[i];
                c.Fill((x, y) =>
                {
                    float t = ((x - ax) % w + w) % w / w;
                    float wy = ay - sag * 4f * t * (1f - t);
                    return Mathf.Abs(y - wy) < 1.4f ? 1f : 0f;
                }, wire);
            }
            Color con = new Color(0.74f, 0.73f, 0.7f), conSh = new Color(0.6f, 0.6f, 0.6f);
            c.FillPolygon(new[] { new Vector2(px - 11, 0), new Vector2(px + 11, 0), new Vector2(px + 7, 478), new Vector2(px - 7, 478) }, con);
            c.FillPolygon(new[] { new Vector2(px - 11, 0), new Vector2(px - 3, 0), new Vector2(px - 2, 478), new Vector2(px - 7, 478) }, conSh);
            for (int i = 0; i < 6; i++)                                            // yellow-black guard
                c.FillRect(px - 12, 30 + i * 9, px + 12, 34 + i * 9, i % 2 == 0 ? new Color(0.95f, 0.78f, 0.2f) : new Color(0.15f, 0.15f, 0.15f));
            c.FillRect(px - 70, 430, px + 70, 438, new Color(0.45f, 0.45f, 0.48f));    // crossarm
            c.FillRect(px - 54, 374, px + 54, 380, new Color(0.45f, 0.45f, 0.48f));
            c.FillRoundRect(px + 10, 300, px + 40, 360, 8, new Color(0.66f, 0.68f, 0.7f)); // transformer
            c.FillRect(px + 10, 300, px + 18, 360, new Color(0.54f, 0.56f, 0.6f));
            foreach (float ix in new[] { -56f, 56f })
                c.FillRect(px + ix - 3, 438, px + ix + 3, 446, White);           // insulators
            c.FillRect(px - 43, 380, px - 37, 388, White);
            return c;
        }

        // ===================== Mid layer props =====================

        /// <summary>One of three large scenery props for the chapter, standing on the canvas bottom.</summary>
        public static PixelCanvas MidProp(SceneryStyle style, int variant, Color tint)
        {
            switch (style)
            {
                case SceneryStyle.Market: return variant == 2 ? VendingCorner() : Shop(variant);
                case SceneryStyle.Beach: return variant == 0 ? LifeguardTower() : variant == 1 ? Parasol() : Rocks();
                case SceneryStyle.City: return variant == 0 ? Overpass() : variant == 1 ? Apartments() : CraneProp();
                case SceneryStyle.Park: return variant == 0 ? School() : Tree(variant == 1);
                default: return variant == 0 ? House() : variant == 1 ? WallAndTrees() : Bungalow();
            }
        }

        static readonly Color Leaf = new Color(0.55f, 0.78f, 0.38f), LeafDark = new Color(0.22f, 0.45f, 0.3f);
        static readonly Color Bark = new Color(0.45f, 0.33f, 0.26f);

        static PixelCanvas House()
        {
            var c = new PixelCanvas(512, 512);
            Color wall = new Color(0.95f, 0.94f, 0.9f), shade = new Color(0.78f, 0.81f, 0.87f), roof = new Color(0.32f, 0.35f, 0.42f);
            Foliage(c, 70, 380, 70, 100, Leaf, LeafDark, 3, 30);                       // tree behind
            Trunk(c, new Vector2(70, 0), new Vector2(60, 300), 16, Bark);
            c.FillRect(80, 0, 400, 300, wall);
            c.FillPolygon(new[] { new Vector2(80, 300), new Vector2(400, 300), new Vector2(240, 412) }, wall);
            System.Func<float, float> slope = x => x < 240f ? 300f + (x - 80f) / 160f * 112f : 300f + (400f - x) / 160f * 112f;
            c.Shade((x, y) => x >= 80 && x <= 400 && y > slope(x) - 26f && y <= slope(x) ? 1f : 0f, shade);   // under the eaves
            c.Shade((x, y) => x >= 80 && x < 108 && y < 300 ? 1f : 0f, shade);         // side turning away
            c.Line(new Vector2(60, 286), new Vector2(240, 426), 16, roof);
            c.Line(new Vector2(240, 426), new Vector2(420, 286), 16, roof);
            c.Line(new Vector2(62, 280), new Vector2(240, 418), 3, new Color(0.62f, 0.4f, 0.32f));
            c.Line(new Vector2(240, 418), new Vector2(418, 280), 3, new Color(0.62f, 0.4f, 0.32f));
            Window(c, 195, 318, 285, 366);
            Window(c, 250, 120, 378, 192);
            c.FillRect(100, 0, 168, 196, new Color(0.46f, 0.34f, 0.26f));            // doorway
            c.FillRect(108, 0, 160, 188, new Color(0.38f, 0.28f, 0.22f));
            for (float x = 112; x < 160; x += 9) c.FillRect(x, 0, x + 2, 188, new Color(0.5f, 0.38f, 0.3f));
            c.FillRect(168, 0, 192, 236, new Color(0.62f, 0.3f, 0.24f));             // brick pillar
            for (float y = 6; y < 236; y += 12) c.FillRect(168, y, 192, y + 2, new Color(0.5f, 0.24f, 0.2f));
            c.FillRect(214, 60, 238, 108, new Color(0.85f, 0.86f, 0.86f));           // meter box
            c.FillRoundRect(292, 0, 362, 56, 4, new Color(0.9f, 0.91f, 0.92f));       // AC unit
            c.FillCircle(316, 28, 18, new Color(0.35f, 0.37f, 0.4f));
            c.FillCircle(316, 28, 6, new Color(0.7f, 0.72f, 0.74f));
            c.FillRect(394, 0, 400, 296, new Color(0.62f, 0.64f, 0.66f));            // downpipe
            c.Line(new Vector2(240, 426), new Vector2(240, 500), 4, new Color(0.35f, 0.35f, 0.38f)); // TV antenna
            c.Line(new Vector2(200, 486), new Vector2(286, 486), 3, new Color(0.35f, 0.35f, 0.38f));
            c.Line(new Vector2(214, 470), new Vector2(272, 470), 3, new Color(0.35f, 0.35f, 0.38f));
            c.FillRoundRect(120, 0, 150, 36, 6, new Color(0.8f, 0.48f, 0.32f));      // pot plants
            Foliage(c, 135, 46, 18, 16, Leaf, LeafDark, 5, 8);
            c.FillRoundRect(368, 0, 392, 30, 5, new Color(0.8f, 0.48f, 0.32f));
            Foliage(c, 380, 38, 14, 12, Leaf, LeafDark, 6, 7);
            return c;
        }

        static PixelCanvas WallAndTrees()
        {
            var c = new PixelCanvas(512, 512);
            // Cloud-pruned garden pine and a big leafy tree behind a concrete block wall.
            Trunk(c, new Vector2(330, 0), new Vector2(320, 260), 22, Bark);
            Foliage(c, 320, 330, 170, 130, Leaf, LeafDark, 11, 60);
            Color pine = new Color(0.2f, 0.42f, 0.3f), pineLit = new Color(0.38f, 0.6f, 0.4f);
            c.Line(new Vector2(110, 0), new Vector2(130, 120), 12, Bark);
            c.Line(new Vector2(130, 120), new Vector2(100, 220), 10, Bark);
            c.Line(new Vector2(100, 220), new Vector2(124, 330), 8, Bark);
            foreach (var pad in new[] { new Vector3(150, 140, 46), new Vector3(80, 210, 40), new Vector3(140, 260, 36), new Vector3(118, 340, 30) })
            {
                c.FillEllipse(pad.x, pad.y, pad.z * 1.4f, pad.z * 0.6f, pine);
                c.FillEllipse(pad.x + 6, pad.y + 6, pad.z * 1.2f, pad.z * 0.42f, pineLit);
            }
            Color block = new Color(0.75f, 0.74f, 0.71f), joint = new Color(0.64f, 0.63f, 0.6f);
            c.FillRect(0, 0, 512, 168, block);
            for (int row = 0; row < 4; row++)
            {
                float y = row * 40f;
                c.FillRect(0, y, 512, y + 2, joint);
                for (float x = row % 2 == 0 ? 0 : 32; x < 512; x += 64) c.FillRect(x, y, x + 2, y + 40, joint);
            }
            c.FillRect(0, 160, 512, 176, new Color(0.84f, 0.83f, 0.8f));               // capping
            c.Shade((x, y) =>                                                        // dappled tree shadow on the wall
            {
                if (y > 160 || y < 60) return 0f;
                float n = Mathf.PerlinNoise(x * 0.025f, y * 0.04f);
                return n > 0.55f ? 0.5f : 0f;
            }, new Color(0.45f, 0.48f, 0.55f));
            // Ivy spilling over the wall
            Foliage(c, 430, 170, 70, 26, Leaf, LeafDark, 13, 18);
            return c;
        }

        static PixelCanvas Bungalow()
        {
            var c = new PixelCanvas(512, 512);
            Trunk(c, new Vector2(430, 0), new Vector2(420, 250), 18, Bark);
            Foliage(c, 420, 320, 90, 120, new Color(0.62f, 0.82f, 0.42f), LeafDark, 17, 34);
            Color wall = new Color(0.88f, 0.89f, 0.9f);
            c.FillRect(30, 0, 340, 250, wall);
            for (float x = 34; x < 340; x += 9) c.FillRect(x, 0, x + 2, 250, new Color(0.78f, 0.79f, 0.82f)); // corrugated siding
            c.FillPolygon(new[] { new Vector2(10, 244), new Vector2(360, 284), new Vector2(360, 298), new Vector2(10, 258) }, new Color(0.3f, 0.32f, 0.38f));
            c.Shade((x, y) => y < 250 && y > 222 + (x - 10) / 350f * 40f - 6f ? 1f : 0f, new Color(0.7f, 0.73f, 0.8f));
            Window(c, 80, 90, 130, 200, false);
            c.FillRect(180, 0, 214, 260, new Color(0.62f, 0.3f, 0.24f));             // brick column
            for (float y = 6; y < 260; y += 12) c.FillRect(180, y, 214, y + 2, new Color(0.5f, 0.24f, 0.2f));
            c.FillRect(240, 120, 300, 170, new Color(0.86f, 0.86f, 0.86f));           // breaker box
            c.FillRoundRect(350, 0, 410, 70, 8, new Color(0.3f, 0.66f, 0.68f));       // bin
            c.FillRect(346, 64, 414, 78, new Color(0.24f, 0.56f, 0.6f));
            return c;
        }

        static PixelCanvas Shop(int variant)
        {
            var c = new PixelCanvas(512, 512);
            Color[] walls = { new Color(0.95f, 0.9f, 0.82f), new Color(0.86f, 0.9f, 0.94f) };
            Color[] awnings = { new Color(0.25f, 0.45f, 0.75f), new Color(0.78f, 0.25f, 0.25f) };
            Color wall = walls[variant % 2], awn = awnings[variant % 2];
            c.FillRect(30, 0, 482, 430, wall);
            c.FillRect(30, 0, 70, 430, Color.Lerp(wall, new Color(0.6f, 0.65f, 0.75f), 0.3f));   // shadow side
            for (int i = 0; i < 3; i++) Window(c, 100 + i * 120, 320, 180 + i * 120, 386);
            c.FillRoundRect(300, 296, 350, 318, 4, new Color(0.9f, 0.9f, 0.92f));    // AC unit
            c.FillRect(30, 244, 482, 294, Color.Lerp(awn, White, 0.75f));            // sign band
            for (int i = 0; i < 6; i++) c.FillRect(90 + i * 56, 256, 126 + i * 56, 282, Mul(awn, 0.8f));   // lettering
            c.FillPolygon(new[] { new Vector2(20, 244), new Vector2(492, 244), new Vector2(504, 200), new Vector2(8, 200) }, awn);
            if (variant == 0)
                for (int i = 0; i < 12; i++) c.FillPolygon(new[] { new Vector2(20 + i * 40, 244), new Vector2(40 + i * 40, 244), new Vector2(32 + i * 40, 200), new Vector2(12 + i * 40, 200) }, White);
            c.FillRect(40, 186, 472, 200, new Color(0.3f, 0.3f, 0.34f, 0.6f));       // awning shadow
            if (variant == 0)
            {
                c.FillRect(60, 0, 300, 186, new Color(0.42f, 0.5f, 0.6f));            // shop window
                for (int i = 0; i < 9; i++)
                    c.FillCircle(84 + i * 26, 30 + (i % 3) * 30, 11, new[] { new Color(1f, 0.6f, 0.2f), new Color(0.9f, 0.3f, 0.3f), new Color(0.95f, 0.85f, 0.3f), new Color(0.5f, 0.75f, 0.3f) }[i % 4]);
                c.FillRect(320, 0, 400, 180, new Color(0.36f, 0.26f, 0.2f));          // door
            }
            else
            {
                c.FillRect(60, 0, 452, 186, new Color(0.22f, 0.2f, 0.22f));          // open front behind a half-raised shutter
                c.FillRect(60, 110, 452, 186, new Color(0.78f, 0.79f, 0.8f));
                for (float y = 114; y < 186; y += 8) c.FillRect(60, y, 452, y + 2, new Color(0.66f, 0.67f, 0.7f));
                for (int i = 0; i < 4; i++)                                         // noren curtain
                    c.FillRect(170 + i * 42, 66, 208 + i * 42, 110, new Color(0.18f, 0.24f, 0.45f));
            }
            c.FillRect(450, 250, 476, 420, new Color(0.95f, 0.85f, 0.4f));            // vertical sign
            for (int i = 0; i < 5; i++) c.FillRect(456, 270 + i * 30, 470, 288 + i * 30, new Color(0.7f, 0.25f, 0.2f));
            return c;
        }

        static PixelCanvas VendingCorner()
        {
            var c = new PixelCanvas(512, 512);
            Trunk(c, new Vector2(420, 0), new Vector2(410, 260), 18, Bark);
            Foliage(c, 410, 330, 100, 120, Leaf, LeafDark, 21, 36);
            VendingMachine(c, 80, new Color(0.85f, 0.22f, 0.24f));
            VendingMachine(c, 214, new Color(0.25f, 0.45f, 0.78f));
            c.FillRoundRect(344, 0, 380, 70, 6, new Color(0.25f, 0.55f, 0.35f));     // recycling bin
            c.FillRect(340, 64, 384, 76, new Color(0.2f, 0.45f, 0.3f));
            return c;
        }

        static void VendingMachine(PixelCanvas c, float x, Color body)
        {
            c.FillRoundRect(x, 0, x + 126, 270, 6, body);
            c.FillRect(x, 0, x + 18, 270, Mul(body, 0.82f));
            c.FillRect(x + 14, 130, x + 112, 254, new Color(0.88f, 0.93f, 0.97f));
            for (int row = 0; row < 3; row++)
                for (int i = 0; i < 6; i++)
                    c.FillRoundRect(x + 20 + i * 15, 140 + row * 38, x + 30 + i * 15, 166 + row * 38, 3,
                        new[] { new Color(0.9f, 0.5f, 0.2f), new Color(0.3f, 0.6f, 0.9f), new Color(0.4f, 0.75f, 0.4f), new Color(0.95f, 0.85f, 0.3f) }[(i + row) % 4]);
            c.FillRect(x + 20, 40, x + 106, 64, new Color(0.15f, 0.15f, 0.18f));     // dispenser
        }

        static PixelCanvas LifeguardTower()
        {
            var c = new PixelCanvas(512, 512);
            Color wood = new Color(0.94f, 0.92f, 0.86f), red = new Color(0.86f, 0.28f, 0.26f);
            c.Line(new Vector2(170, 0), new Vector2(200, 230), 12, wood);
            c.Line(new Vector2(330, 0), new Vector2(300, 230), 12, wood);
            c.Line(new Vector2(180, 80), new Vector2(320, 160), 6, Mul(wood, 0.85f));
            c.Line(new Vector2(320, 80), new Vector2(180, 160), 6, Mul(wood, 0.85f));
            c.FillRect(170, 226, 330, 244, wood);
            c.FillRect(190, 244, 310, 330, wood);
            c.FillRect(190, 244, 214, 330, Mul(wood, 0.85f));
            c.FillRect(226, 270, 290, 316, new Color(0.36f, 0.43f, 0.53f));
            c.FillPolygon(new[] { new Vector2(172, 330), new Vector2(328, 330), new Vector2(250, 382) }, red);
            c.Line(new Vector2(250, 382), new Vector2(250, 440), 3, Grey(0.4f));
            c.FillPolygon(new[] { new Vector2(250, 440), new Vector2(290, 428), new Vector2(250, 416) }, new Color(0.95f, 0.85f, 0.3f));
            for (int i = 0; i < 7; i++) c.Line(new Vector2(350, i * 32), new Vector2(316, 226 * (i + 1) / 8f), 4, Mul(wood, 0.8f));
            return c;
        }

        static PixelCanvas Parasol()
        {
            var c = new PixelCanvas(512, 512);
            c.Line(new Vector2(250, 0), new Vector2(262, 230), 6, Grey(0.85f));
            Color a = new Color(0.95f, 0.45f, 0.4f);
            for (int i = 0; i < 6; i++)
            {
                float a0 = Mathf.PI * i / 6f, a1 = Mathf.PI * (i + 1) / 6f;
                c.FillPolygon(new[] { new Vector2(262, 236), new Vector2(262 + Mathf.Cos(a0) * 130, 236 + Mathf.Sin(a0) * 50), new Vector2(262 + Mathf.Cos(a1) * 130, 236 + Mathf.Sin(a1) * 50) }, i % 2 == 0 ? a : White);
            }
            c.FillRoundRect(140, 0, 220, 50, 8, new Color(0.3f, 0.6f, 0.85f));        // cool box
            c.FillRect(140, 40, 220, 50, White);
            c.FillPolygon(new[] { new Vector2(260, 0), new Vector2(400, 0), new Vector2(390, 8), new Vector2(270, 8) }, new Color(0.95f, 0.8f, 0.35f)); // towel
            return c;
        }

        static PixelCanvas Rocks()
        {
            var c = new PixelCanvas(512, 512);
            Color rock = new Color(0.68f, 0.66f, 0.64f), rockSh = new Color(0.5f, 0.5f, 0.54f);
            foreach (var r in new[] { new Vector3(160, 50, 80), new Vector3(260, 40, 60), new Vector3(330, 30, 44) })
            {
                c.FillEllipse(r.x, r.y, r.z * 1.2f, r.z, rock);
                Vector3 q = r;
                c.Shade((x, y) => (x - q.x - q.z * 0.25f) * (x - q.x - q.z * 0.25f) / (q.z * q.z * 1.2f) + (y - q.y - q.z * 0.3f) * (y - q.y - q.z * 0.3f) / (q.z * q.z) > 0.8f ? 1f : 0f, rockSh);
            }
            c.Line(new Vector2(330, 16), new Vector2(470, 30), 18, new Color(0.72f, 0.62f, 0.5f));   // driftwood
            c.Line(new Vector2(400, 24), new Vector2(430, 60), 8, new Color(0.72f, 0.62f, 0.5f));
            return c;
        }

        static PixelCanvas Overpass()
        {
            var c = new PixelCanvas(512, 512);
            Color con = new Color(0.78f, 0.78f, 0.8f), sh = new Color(0.58f, 0.6f, 0.66f);
            c.FillRect(200, 0, 312, 380, con);
            c.FillRect(200, 0, 236, 380, sh);
            c.FillRect(0, 380, 512, 450, con);                                      // deck
            c.FillRect(0, 380, 512, 400, sh);
            c.FillRect(0, 450, 512, 462, Grey(0.86f));
            for (float x = 4; x < 512; x += 20) c.FillRect(x, 462, x + 4, 490, Grey(0.7f)); // railing
            c.FillRect(0, 488, 512, 494, Grey(0.7f));
            c.FillRect(220, 120, 300, 220, new Color(0.9f, 0.55f, 0.5f));             // poster
            c.FillCircle(260, 170, 26, new Color(0.4f, 0.7f, 0.9f));
            return c;
        }

        static PixelCanvas Apartments()
        {
            var c = new PixelCanvas(512, 512);
            Color wall = new Color(0.92f, 0.88f, 0.82f);
            c.FillRect(50, 0, 460, 500, wall);
            c.FillRect(50, 0, 120, 500, Color.Lerp(wall, new Color(0.6f, 0.65f, 0.75f), 0.35f));
            for (int floor = 0; floor < 5; floor++)
            {
                float y = 40 + floor * 92;
                for (int i = 0; i < 3; i++) Window(c, 140 + i * 105, y, 210 + i * 105, y + 52, false);
                c.FillRect(120, y - 8, 460, y + 4, Grey(0.86f));                    // balcony slab
                for (float x = 124; x < 460; x += 12) c.FillRect(x, y + 4, x + 3, y + 28, Grey(0.7f));
                c.FillRect(120, y + 26, 460, y + 30, Grey(0.7f));
            }
            return c;
        }

        static PixelCanvas CraneProp()
        {
            var c = new PixelCanvas(512, 512);
            Color y = new Color(0.95f, 0.72f, 0.25f), yd = new Color(0.8f, 0.56f, 0.18f);
            c.FillRect(230, 0, 270, 470, y);
            for (int i = 0; i < 22; i++) c.Line(new Vector2(230, i * 21), new Vector2(270, i * 21 + 21), 4, yd);
            c.FillRect(40, 460, 500, 484, y);
            for (int i = 0; i < 22; i++) c.Line(new Vector2(40 + i * 21, 460), new Vector2(61 + i * 21, 484), 4, yd);
            c.Line(new Vector2(420, 460), new Vector2(420, 300), 3, Grey(0.25f));
            c.FillRect(400, 270, 440, 300, Grey(0.5f));
            c.FillRect(60, 420, 120, 460, Grey(0.45f));
            c.FillRect(200, 0, 300, 30, Grey(0.6f));
            return c;
        }

        static PixelCanvas School()
        {
            var c = new PixelCanvas(512, 512);
            Color wall = new Color(0.95f, 0.94f, 0.9f), shade = new Color(0.78f, 0.8f, 0.86f);
            c.FillRect(0, 0, 512, 340, wall);
            c.FillRect(0, 330, 512, 346, Grey(0.82f));
            for (int floor = 0; floor < 3; floor++)
                for (int i = 0; i < 5; i++)
                    Window(c, 16 + i * 102, 40 + floor * 100, 96 + i * 102, 100 + floor * 100, false);
            c.Shade((x, y) => y > 310 && y < 330 ? 1f : 0f, shade);
            c.FillRect(200, 340, 312, 452, wall);                                   // clock tower
            c.FillRect(200, 340, 222, 452, shade);
            c.FillRect(194, 450, 318, 462, Grey(0.82f));
            c.FillCircle(256, 396, 34, White);
            c.FillCircle(256, 396, 30, new Color(0.96f, 0.96f, 0.94f));
            c.Line(new Vector2(256, 396), new Vector2(256, 418), 4, Line);
            c.Line(new Vector2(256, 396), new Vector2(272, 396), 4, Line);
            c.FillRect(0, 0, 512, 14, Grey(0.7f));
            return c;
        }

        static PixelCanvas Tree(bool cherry)
        {
            var c = new PixelCanvas(512, 512);
            Trunk(c, new Vector2(256, 0), new Vector2(246, 240), 26, Bark);
            c.Line(new Vector2(250, 180), new Vector2(170, 280), 12, Bark);
            c.Line(new Vector2(250, 200), new Vector2(340, 300), 12, Bark);
            if (cherry) Foliage(c, 256, 330, 190, 130, new Color(1f, 0.84f, 0.9f), new Color(0.88f, 0.55f, 0.68f), 31, 70);
            else Foliage(c, 256, 330, 180, 140, Leaf, LeafDark, 33, 64);
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
                    // Planters and parked bicycles along the shopfronts.
                    for (int i = 0; i < 2; i++)
                    {
                        float x = 20 + i * 128;
                        c.FillRect(x, 0, x + 56, 26, new Color(0.62f, 0.5f, 0.42f));
                        Foliage(c, x + 28, 36, 30, 16, Leaf, LeafDark, seed + i, 12);
                        float bx = x + 84;
                        Color frame = i == 0 ? new Color(0.3f, 0.55f, 0.75f) : new Color(0.85f, 0.4f, 0.4f);
                        foreach (float wx in new[] { bx, bx + 40 })
                        {
                            c.Fill((px, py) => { float d = Mathf.Sqrt((px - wx) * (px - wx) + (py - 18) * (py - 18)); return d < 17 && d > 13.5f ? 1f : 0f; }, Grey(0.2f));
                        }
                        c.Line(new Vector2(bx, 18), new Vector2(bx + 18, 40), 3, frame);
                        c.Line(new Vector2(bx + 18, 40), new Vector2(bx + 40, 18), 3, frame);
                        c.Line(new Vector2(bx + 18, 40), new Vector2(bx + 36, 40), 3, frame);
                        c.Line(new Vector2(bx + 36, 40), new Vector2(bx + 40, 18), 3, frame);
                    }
                    break;
                case SceneryStyle.City:
                    // White site hoarding with green stripes.
                    c.FillRect(0, 0, w, 70, new Color(0.93f, 0.94f, 0.93f));
                    c.FillRect(0, 44, w, 52, new Color(0.3f, 0.6f, 0.4f));
                    c.FillRect(0, 56, w, 60, new Color(0.3f, 0.6f, 0.4f));
                    for (int i = 0; i < 4; i++) c.FillRect(i * 64, 0, i * 64 + 3, 70, Grey(0.78f));
                    break;
                case SceneryStyle.Beach:
                    c.FillBelow(x => 16f + Mathf.Sin(x / w * Mathf.PI * 4f) * 6f, color);
                    for (int i = 0; i < 30; i++)
                    {
                        float x = (float)rng.NextDouble() * w;
                        float lean = rng.Next(-8, 8), top = 38 + rng.Next(0, 26);
                        c.Wrapped(o => c.Line(new Vector2(x + o, 12), new Vector2(x + o + lean, top), 2.5f, new Color(0.5f, 0.66f, 0.36f)));
                    }
                    break;
                case SceneryStyle.Park:
                    Foliage(c, w * 0.5f, 34, w * 0.6f, 26, new Color(0.5f, 0.74f, 0.4f), new Color(0.24f, 0.46f, 0.3f), seed, 40, true);
                    c.FillRect(0, 0, w, 20, new Color(0.24f, 0.46f, 0.3f));
                    for (int i = 0; i < 14; i++)
                    {
                        float fx = (float)rng.NextDouble() * w, fy = 30 + (float)rng.NextDouble() * 30;
                        c.Wrapped(o => c.FillCircle(fx + o, fy, 2.5f, new Color(1f, 0.82f, 0.88f)));
                    }
                    break;
                default:
                    // Roadside weeds and low clipped bushes.
                    Foliage(c, w * 0.5f, 30, w * 0.6f, 22, Leaf, LeafDark, seed, 34, true);
                    c.FillRect(0, 0, w, 18, LeafDark);
                    for (int i = 0; i < 40; i++)
                    {
                        float x = (float)rng.NextDouble() * w, top = 40 + rng.Next(0, 24), lean = rng.Next(-6, 6);
                        c.Wrapped(o => c.Line(new Vector2(x + o, 20), new Vector2(x + o + lean, top), 2f, Lighten(Leaf, 0.1f)));
                    }
                    break;
            }
            return c;
        }
    }
}
