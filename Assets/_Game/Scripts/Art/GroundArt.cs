using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Painterly ground textures for the 3D street (docs/ART_DIRECTION.md): tileable in both
    /// directions, 512 x 512 pixels for 8 x 8 world units (64 px per unit), with soft large-scale
    /// mottling, bevelled and worn edges, moss in the joints and small signs of life (shells in the
    /// sand, flowers in the lawn, fallen leaves on the park path), in a warm, slightly faded palette.
    /// The toon shader adds a world-scale variation on top (_Macro), so the repeat doesn't show.
    /// </summary>
    public static partial class ProceduralArt
    {
        const int GroundSize = 512;

        /// <summary>A square painting surface that wraps in both directions; y up, (0,0) bottom-left.</summary>
        class GroundTile
        {
            public readonly int N;
            readonly Color[] px;

            public GroundTile(int n, Color fill)
            {
                N = n;
                px = new Color[n * n];
                for (int i = 0; i < px.Length; i++) px[i] = fill;
            }

            int Index(int x, int y) { return Wrap(y) * N + Wrap(x); }
            int Wrap(int v) { v %= N; return v < 0 ? v + N : v; }

            public Color this[int x, int y]
            {
                get { return px[Index(x, y)]; }
                set { px[Index(x, y)] = value; }
            }

            /// <summary>Lerp the pixel toward c by k (0..1).</summary>
            public void Mix(int x, int y, Color c, float k)
            {
                if (k <= 0f) return;
                int i = Index(x, y);
                px[i] = Color.Lerp(px[i], c, Mathf.Clamp01(k));
            }

            /// <summary>Multiply the pixel's colour by m (keeps alpha).</summary>
            public void Scale(int x, int y, float m)
            {
                int i = Index(x, y);
                Color c = px[i];
                px[i] = new Color(c.r * m, c.g * m, c.b * m, c.a);
            }

            /// <summary>Tileable value noise, 0..1, with <paramref name="period"/> lattice cells across the tile.</summary>
            public float Noise(float x, float y, int period, int seed)
            {
                float cell = N / (float)period;
                float fx = x / cell, fy = y / cell;
                int x0 = Mathf.FloorToInt(fx), y0 = Mathf.FloorToInt(fy);
                float tx = fx - x0, ty = fy - y0;
                tx = tx * tx * (3f - 2f * tx);
                ty = ty * ty * (3f - 2f * ty);
                float a = Lattice(x0, y0, period, seed), b = Lattice(x0 + 1, y0, period, seed);
                float c = Lattice(x0, y0 + 1, period, seed), d = Lattice(x0 + 1, y0 + 1, period, seed);
                return Mathf.Lerp(Mathf.Lerp(a, b, tx), Mathf.Lerp(c, d, tx), ty);
            }

            static float Lattice(int x, int y, int period, int seed)
            {
                x %= period; if (x < 0) x += period;
                y %= period; if (y < 0) y += period;
                return GroundHash(x, y, seed);
            }

            /// <summary>Fractal (fBm) tileable noise, 0..1.</summary>
            public float Fbm(float x, float y, int period, int octaves, int seed)
            {
                float sum = 0f, amp = 1f, total = 0f;
                for (int o = 0; o < octaves; o++)
                {
                    sum += Noise(x, y, period, seed + o * 31) * amp;
                    total += amp;
                    amp *= 0.5f;
                    period *= 2;
                }
                return sum / total;
            }

            /// <summary>Soft blotches: every pixel leans toward dark or light by fBm noise.</summary>
            public void Mottle(int period, int octaves, int seed, Color dark, Color light, float amount)
            {
                for (int y = 0; y < N; y++)
                    for (int x = 0; x < N; x++)
                    {
                        float n = Fbm(x, y, period, octaves, seed) * 2f - 1f;
                        int i = y * N + x;
                        px[i] = n < 0f ? Color.Lerp(px[i], dark, -n * amount) : Color.Lerp(px[i], light, n * amount);
                    }
            }

            /// <summary>A soft-edged ellipse (wrapping across the edges), mixed in at <paramref name="alpha"/>.</summary>
            public void Blob(float cx, float cy, float rx, float ry, Color c, float alpha, float soft = 1.5f, float angle = 0f)
            {
                float r = Mathf.Max(rx, ry) + soft + 1f;
                float cs = Mathf.Cos(angle), sn = Mathf.Sin(angle);
                for (int y = Mathf.FloorToInt(cy - r); y <= Mathf.CeilToInt(cy + r); y++)
                    for (int x = Mathf.FloorToInt(cx - r); x <= Mathf.CeilToInt(cx + r); x++)
                    {
                        float dx = x + 0.5f - cx, dy = y + 0.5f - cy;
                        float u = (dx * cs + dy * sn) / Mathf.Max(0.01f, rx), v = (-dx * sn + dy * cs) / Mathf.Max(0.01f, ry);
                        float d = (Mathf.Sqrt(u * u + v * v) - 1f) * Mathf.Min(rx, ry);
                        float k = Mathf.Clamp01(0.5f - d / Mathf.Max(0.5f, soft));
                        Mix(x, y, c, k * alpha);
                    }
            }

            /// <summary>A round-capped stroke from a to b (wrapping), mixed in at <paramref name="alpha"/>.</summary>
            public void Stroke(Vector2 a, Vector2 b, float width, Color c, float alpha)
            {
                float half = width * 0.5f;
                int x0 = Mathf.FloorToInt(Mathf.Min(a.x, b.x) - half - 1f), x1 = Mathf.CeilToInt(Mathf.Max(a.x, b.x) + half + 1f);
                int y0 = Mathf.FloorToInt(Mathf.Min(a.y, b.y) - half - 1f), y1 = Mathf.CeilToInt(Mathf.Max(a.y, b.y) + half + 1f);
                Vector2 ab = b - a;
                float len2 = Mathf.Max(1e-4f, ab.sqrMagnitude);
                for (int y = y0; y <= y1; y++)
                    for (int x = x0; x <= x1; x++)
                    {
                        var p = new Vector2(x + 0.5f, y + 0.5f);
                        float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / len2);
                        float d = (p - (a + ab * t)).magnitude - half;
                        Mix(x, y, c, Mathf.Clamp01(0.5f - d) * alpha);
                    }
            }

            /// <summary>A wandering crack: a chain of short strokes from (x, y) heading at <paramref name="angle"/>.</summary>
            public void Crack(System.Random rng, float x, float y, float angle, int steps, float step, float width, Color c, float alpha, float wander = 0.6f)
            {
                var p = new Vector2(x, y);
                for (int i = 0; i < steps; i++)
                {
                    angle += GRand(rng, -wander, wander);
                    var q = p + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * step * GRand(rng, 0.6f, 1.2f);
                    Stroke(p, q, width * GRand(rng, 0.7f, 1.1f), c, alpha);
                    p = q;
                }
            }

            public PixelCanvas ToCanvas()
            {
                var c = new PixelCanvas(N, N);
                for (int y = 0; y < N; y++)
                    for (int x = 0; x < N; x++)
                    {
                        Color p = px[y * N + x];
                        c.Set(x, y, new Color(Mathf.Clamp01(p.r), Mathf.Clamp01(p.g), Mathf.Clamp01(p.b), 1f));
                    }
                return c;
            }
        }

        static float GroundHash(int x, int y, int seed)
        {
            unchecked
            {
                int h = x * 374761393 + y * 668265263 + seed * 1442695041;
                h = (h ^ (h >> 13)) * 1274126177;
                return ((h ^ (h >> 16)) & 0xFFFF) / 65535f;
            }
        }

        static float GRand(System.Random rng, float min, float max) { return min + (float)rng.NextDouble() * (max - min); }

        static Color Shift(Color c, float k) { return new Color(c.r * k, c.g * k, c.b * k, c.a); }

        /// <summary>The painterly version of a ground surface, or null for the surfaces painted elsewhere.</summary>
        static PixelCanvas GroundTexture(Surface surface)
        {
            var rng = new System.Random((int)surface * 131 + 17);
            int seed = (int)surface * 7 + 3;
            switch (surface)
            {
                case Surface.Asphalt: return Asphalt(rng, seed);
                case Surface.Paving: return Slabbed(rng, seed, 64, 64, 2.2f, new Color(0.84f, 0.81f, 0.76f), new Color(0.64f, 0.61f, 0.57f), 0.07f, true);
                case Surface.Kerb: return Slabbed(rng, seed, 64, 512, 2.5f, new Color(0.88f, 0.87f, 0.84f), new Color(0.6f, 0.59f, 0.57f), 0.05f, false);
                case Surface.Concrete: return Concrete(rng, seed);
                case Surface.Cobbles: return Cobbles(rng, seed);
                case Surface.Sand: return Sand(rng, seed);
                case Surface.Gravel: return Gravel(rng, seed);
                case Surface.Grass: return Grass(rng, seed);
                case Surface.Sea: return Water(rng, seed);
                default: return null;
            }
        }

        static PixelCanvas Asphalt(System.Random rng, int seed)
        {
            int n = GroundSize;
            var t = new GroundTile(n, new Color(0.5f, 0.49f, 0.51f));
            t.Mottle(4, 4, seed, new Color(0.43f, 0.43f, 0.46f), new Color(0.58f, 0.56f, 0.55f), 0.6f);
            // Patched repairs: darker, fresher tarmac with ragged edges and a lighter worn seam.
            for (int i = 0; i < 2; i++)
            {
                float x0 = GRand(rng, 0, n), y0 = GRand(rng, 0, n), w = GRand(rng, 50, 130), h = GRand(rng, 34, 90);
                for (int yy = -4; yy < (int)h + 4; yy++)
                    for (int xx = -4; xx < (int)w + 4; xx++)
                    {
                        float edge = Mathf.Min(Mathf.Min(xx, w - xx), Mathf.Min(yy, h - yy));
                        edge += (t.Noise(x0 + xx, y0 + yy, 32, seed + 11 + i) - 0.5f) * 9f;
                        if (edge < -1f) continue;
                        if (edge < 1.2f) t.Mix((int)x0 + xx, (int)y0 + yy, new Color(0.58f, 0.57f, 0.56f), 0.3f);
                        else t.Mix((int)x0 + xx, (int)y0 + yy, new Color(0.44f, 0.44f, 0.47f), 0.3f);
                    }
            }
            // Fine sealed cracks.
            for (int i = 0; i < 4; i++)
                t.Crack(rng, GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 0f, 6.28f), 7, 12f, 1.5f, new Color(0.34f, 0.33f, 0.36f), 0.6f, 0.35f);
            // Oil and damp stains.
            for (int i = 0; i < 6; i++)
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 10, 30), GRand(rng, 6, 16), new Color(0.4f, 0.39f, 0.43f), 0.3f, 8f, GRand(rng, 0f, 3f));
            // Aggregate: light and dark chips.
            for (int i = 0; i < 22000; i++)
            {
                int x = rng.Next(n), y = rng.Next(n);
                bool light = rng.NextDouble() < 0.45;
                t.Mix(x, y, light ? new Color(0.68f, 0.66f, 0.65f) : new Color(0.36f, 0.36f, 0.38f), GRand(rng, 0.2f, 0.5f));
            }
            return t.ToCanvas();
        }

        /// <summary>
        /// Slabs <paramref name="sw"/> x <paramref name="sh"/> pixels in a grid, each its own shade
        /// (some warmer, some cooler), bevelled (lit from the top-left), with dark joints, moss in
        /// places, a few chips and stains.
        /// </summary>
        static PixelCanvas Slabbed(System.Random rng, int seed, int sw, int sh, float joint, Color slab, Color jointColor, float vary, bool moss)
        {
            int n = GroundSize;
            var t = new GroundTile(n, slab);
            int cols = n / sw, rows = n / sh;
            var tone = new float[cols * rows];
            var warm = new float[cols * rows];
            for (int i = 0; i < tone.Length; i++) { tone[i] = 1f + GRand(rng, -vary, vary); warm[i] = GRand(rng, -1f, 1f); }
            Color mossColor = new Color(0.46f, 0.52f, 0.32f);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    int cx = x / sw, cy = y / sh, cell = cy * cols + cx;
                    float fx = x - cx * sw + 0.5f, fy = y - cy * sh + 0.5f;
                    float dl = fx, dr = sw - fx, db = fy, dt = sh - fy;
                    float d = Mathf.Min(Mathf.Min(dl, dr), Mathf.Min(db, dt));
                    Color c = Shift(slab, tone[cell]);
                    c = Color.Lerp(c, warm[cell] > 0f ? new Color(0.9f, 0.82f, 0.7f) : new Color(0.76f, 0.78f, 0.8f), Mathf.Abs(warm[cell]) * 0.12f);
                    float grain = t.Fbm(x, y, 16, 3, seed + cell % 7) - 0.5f;
                    c = Shift(c, 1f + grain * 0.12f);
                    if (d < joint)
                    {
                        float m = moss ? Mathf.Clamp01((t.Noise(x, y, 8, seed + 9) - 0.55f) * 4f) : 0f;
                        c = Color.Lerp(jointColor, mossColor, m * 0.8f);
                    }
                    else if (d < joint + 3f)
                    {
                        // The bevel: brighter on the top and left edges, darker on the bottom and right.
                        float k = 1f - (d - joint) / 3f;
                        bool litSide = (d == dt) || (d == dl);
                        c = Shift(c, litSide ? 1f + 0.1f * k : 1f - 0.16f * k);
                    }
                    t[x, y] = c;
                }
            // Chips on the edges, stains and the odd cracked slab.
            for (int i = 0; i < 18; i++)
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 2f, 5f), GRand(rng, 1.5f, 3f), Shift(jointColor, 1.1f), 0.6f, 1f);
            for (int i = 0; i < 7; i++)
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 8f, 22f), GRand(rng, 6f, 14f), Shift(slab, 0.84f), 0.3f, 7f, GRand(rng, 0f, 3f));
            for (int i = 0; i < 2; i++)
                t.Crack(rng, GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 0f, 6.28f), 4, 10f, 1.4f, Shift(jointColor, 0.9f), 0.7f);
            return t.ToCanvas();
        }

        static PixelCanvas Concrete(System.Random rng, int seed)
        {
            int n = GroundSize;
            var slab = new Color(0.78f, 0.77f, 0.74f);
            var t = new GroundTile(n, slab);
            t.Mottle(4, 4, seed, new Color(0.68f, 0.67f, 0.65f), new Color(0.85f, 0.84f, 0.81f), 0.6f);
            // Panels 4 units square, each a slightly different pour, with saw-cut joints.
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    int px = x / 256, py = y / 256;
                    float k = 1f + (GroundHash(px, py, seed) - 0.5f) * 0.08f;
                    t.Scale(x, y, k);
                    int fx = x % 256, fy = y % 256;
                    if (fx < 2 || fy < 2) t.Mix(x, y, new Color(0.56f, 0.55f, 0.53f), 0.85f);
                    else if (fx < 4 || fy < 4) t.Scale(x, y, 1.05f);
                }
            for (int i = 0; i < 5; i++)    // rust and damp stains
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 10f, 34f), GRand(rng, 8f, 20f),
                    rng.NextDouble() < 0.4 ? new Color(0.74f, 0.62f, 0.5f) : new Color(0.62f, 0.62f, 0.62f), 0.3f, 10f, GRand(rng, 0f, 3f));
            for (int i = 0; i < 3; i++)
                t.Crack(rng, GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 0f, 6.28f), 7, 12f, 1.5f, new Color(0.52f, 0.51f, 0.5f), 0.7f);
            for (int i = 0; i < 5000; i++)
                t.Mix(rng.Next(n), rng.Next(n), rng.NextDouble() < 0.5 ? new Color(0.66f, 0.65f, 0.63f) : new Color(0.88f, 0.87f, 0.85f), GRand(rng, 0.3f, 0.6f));
            return t.ToCanvas();
        }

        /// <summary>
        /// Irregular rounded cobbles: a jittered cell grid, each pixel belongs to the nearest stone;
        /// the gap to the next-nearest is the joint. Each stone is domed (lit top-left) and its own colour.
        /// </summary>
        static PixelCanvas Cobbles(System.Random rng, int seed)
        {
            int n = GroundSize, cells = 24;
            float cell = n / (float)cells;
            var t = new GroundTile(n, new Color(0.42f, 0.38f, 0.34f));
            var centre = new Vector2[cells * cells];
            var colour = new Color[cells * cells];
            Color[] stones = { new Color(0.72f, 0.66f, 0.6f), new Color(0.66f, 0.62f, 0.6f), new Color(0.78f, 0.72f, 0.64f), new Color(0.62f, 0.58f, 0.56f), new Color(0.74f, 0.64f, 0.56f) };
            for (int j = 0; j < cells; j++)
                for (int i = 0; i < cells; i++)
                {
                    centre[j * cells + i] = new Vector2((i + 0.5f + GRand(rng, -0.28f, 0.28f)) * cell, (j + 0.5f + GRand(rng, -0.28f, 0.28f)) * cell);
                    colour[j * cells + i] = Shift(stones[rng.Next(stones.Length)], GRand(rng, 0.92f, 1.06f));
                }
            Color joint = new Color(0.36f, 0.33f, 0.3f), moss = new Color(0.44f, 0.5f, 0.32f);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    var p = new Vector2(x + 0.5f, y + 0.5f);
                    int ci = Mathf.FloorToInt(p.x / cell), cj = Mathf.FloorToInt(p.y / cell);
                    float d1 = float.MaxValue, d2 = float.MaxValue;
                    int best = 0;
                    Vector2 bestOffset = Vector2.zero;
                    for (int dj = -1; dj <= 1; dj++)
                        for (int di = -1; di <= 1; di++)
                        {
                            int ii = ci + di, jj = cj + dj;
                            int wi = ((ii % cells) + cells) % cells, wj = ((jj % cells) + cells) % cells;
                            Vector2 c = centre[wj * cells + wi] + new Vector2((ii - wi) * cell, (jj - wj) * cell);
                            float d = (p - c).sqrMagnitude;
                            if (d < d1) { d2 = d1; d1 = d; best = wj * cells + wi; bestOffset = p - c; }
                            else if (d < d2) d2 = d;
                        }
                    float gap = Mathf.Sqrt(d2) - Mathf.Sqrt(d1);
                    if (gap < 2.6f)
                    {
                        float m = Mathf.Clamp01((t.Noise(x, y, 6, seed + 4) - 0.5f) * 3f);
                        t[x, y] = Color.Lerp(joint, moss, m * 0.7f);
                        continue;
                    }
                    // Dome shading: lighter toward the top-left of each stone, darker at its lower-right rim.
                    Vector2 o = bestOffset / (cell * 0.5f);
                    float light = Mathf.Clamp(-o.x * 0.35f + o.y * 0.35f, -0.5f, 0.5f);
                    float rim = Mathf.Clamp01(1f - (gap - 2.6f) / 5f);
                    Color s = Shift(colour[best], 1f + light * 0.22f - rim * 0.12f);
                    s = Shift(s, 1f + (t.Noise(x, y, 64, seed + 2) - 0.5f) * 0.1f);
                    t[x, y] = s;
                }
            return t.ToCanvas();
        }

        static PixelCanvas Sand(System.Random rng, int seed)
        {
            int n = GroundSize;
            var t = new GroundTile(n, new Color(0.93f, 0.85f, 0.68f));
            t.Mottle(4, 4, seed, new Color(0.86f, 0.76f, 0.58f), new Color(0.98f, 0.92f, 0.78f), 0.6f);
            // Soft wind ripples: crests running across, each lit on one side and shaded on the other.
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float warp = t.Fbm(x, y, 4, 2, seed + 5) * 40f;
                    float phase = (y + warp) / n * 14f * Mathf.PI * 2f;
                    float s = Mathf.Sin(phase), fade = t.Noise(x, y, 4, seed + 8);
                    float k = s > 0f ? 1f + s * 0.06f * fade : 1f + s * 0.09f * fade;
                    t.Scale(x, y, k);
                }
            // Damp, darker patches, pebbles and bits of shell.
            for (int i = 0; i < 4; i++)
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 30, 70), GRand(rng, 20, 40), new Color(0.82f, 0.72f, 0.56f), 0.25f, 20f, GRand(rng, 0f, 3f));
            for (int i = 0; i < 70; i++)
            {
                float x = GRand(rng, 0, n), y = GRand(rng, 0, n);
                bool shell = rng.NextDouble() < 0.5;
                Color c = shell ? (rng.NextDouble() < 0.5 ? new Color(0.99f, 0.92f, 0.88f) : new Color(0.98f, 0.8f, 0.76f)) : new Color(0.62f, 0.58f, 0.54f);
                float r = shell ? GRand(rng, 1.6f, 3f) : GRand(rng, 1.2f, 2.4f);
                t.Blob(x + 0.8f, y - 0.8f, r, r * 0.7f, new Color(0.74f, 0.64f, 0.5f), 0.5f, 1f);
                t.Blob(x, y, r, r * 0.7f, c, 0.95f, 0.8f, GRand(rng, 0f, 3f));
            }
            for (int i = 0; i < 9000; i++)
                t.Mix(rng.Next(n), rng.Next(n), rng.NextDouble() < 0.5 ? new Color(0.8f, 0.7f, 0.54f) : new Color(1f, 0.95f, 0.84f), GRand(rng, 0.25f, 0.55f));
            return t.ToCanvas();
        }

        static PixelCanvas Gravel(System.Random rng, int seed)
        {
            int n = GroundSize;
            var t = new GroundTile(n, new Color(0.76f, 0.68f, 0.56f));
            t.Mottle(4, 3, seed, new Color(0.66f, 0.58f, 0.48f), new Color(0.84f, 0.77f, 0.66f), 0.6f);
            Color[] stones = { new Color(0.84f, 0.78f, 0.68f), new Color(0.7f, 0.64f, 0.56f), new Color(0.9f, 0.86f, 0.78f), new Color(0.62f, 0.58f, 0.54f) };
            for (int i = 0; i < 5200; i++)
            {
                float x = GRand(rng, 0, n), y = GRand(rng, 0, n), r = GRand(rng, 1.4f, 3.2f);
                Color c = stones[rng.Next(stones.Length)];
                t.Blob(x + 0.7f, y - 0.9f, r, r * 0.8f, new Color(0.48f, 0.42f, 0.36f), 0.45f, 1f);
                t.Blob(x, y, r, r * 0.8f, c, 0.9f, 0.8f, GRand(rng, 0f, 3f));
                t.Blob(x - r * 0.3f, y + r * 0.3f, r * 0.35f, r * 0.3f, Shift(c, 1.12f), 0.6f, 0.6f);
            }
            // A few fallen leaves on the park path.
            Color[] leaves = { new Color(0.9f, 0.55f, 0.22f), new Color(0.82f, 0.32f, 0.2f), new Color(0.95f, 0.78f, 0.3f), new Color(0.7f, 0.5f, 0.24f) };
            for (int i = 0; i < 26; i++)
            {
                float x = GRand(rng, 0, n), y = GRand(rng, 0, n), a = GRand(rng, 0f, 3.14f);
                Color c = leaves[rng.Next(leaves.Length)];
                t.Blob(x + 1f, y - 1f, 6f, 3f, new Color(0.45f, 0.38f, 0.3f), 0.35f, 1.2f, a);
                t.Blob(x, y, 6f, 3f, c, 0.95f, 1f, a);
                t.Stroke(new Vector2(x - Mathf.Cos(a) * 5f, y - Mathf.Sin(a) * 5f), new Vector2(x + Mathf.Cos(a) * 5f, y + Mathf.Sin(a) * 5f), 0.8f, Shift(c, 0.75f), 0.6f);
            }
            return t.ToCanvas();
        }

        static PixelCanvas Grass(System.Random rng, int seed)
        {
            int n = GroundSize;
            Color lush = new Color(0.5f, 0.61f, 0.31f), dry = new Color(0.74f, 0.71f, 0.42f), deep = new Color(0.36f, 0.48f, 0.27f);
            var t = new GroundTile(n, Color.Lerp(lush, dry, 0.3f));
            // Big soft patches of lusher and drier grass.
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float a = t.Fbm(x, y, 3, 4, seed), b = t.Fbm(x, y, 8, 2, seed + 40);
                    Color c = Color.Lerp(Color.Lerp(deep, lush, Mathf.Clamp01(a * 1.6f - 0.1f)), dry, Mathf.Clamp01((a - 0.55f) * 2.5f));
                    t[x, y] = Shift(c, 0.94f + b * 0.12f);
                }
            // Clumps of short blades: darker roots, lighter tips, leaning a little each way.
            for (int i = 0; i < 2600; i++)
            {
                float x = GRand(rng, 0, n), y = GRand(rng, 0, n);
                if (t.Noise(x, y, 12, seed + 7) < 0.35f && rng.NextDouble() < 0.6) continue;
                Color baseCol = t[(int)x, (int)y];
                int blades = rng.Next(3, 7);
                for (int k = 0; k < blades; k++)
                {
                    float a = GRand(rng, 1.2f, 1.95f), len = GRand(rng, 5f, 11f);
                    var p0 = new Vector2(x + GRand(rng, -3f, 3f), y + GRand(rng, -2f, 2f));
                    var p1 = p0 + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * len;
                    t.Stroke(p0, p1, GRand(rng, 1.1f, 1.8f), Shift(baseCol, GRand(rng, 0.78f, 0.9f)), 0.7f);
                    t.Stroke(Vector2.Lerp(p0, p1, 0.45f), p1, GRand(rng, 0.9f, 1.3f), Color.Lerp(Shift(baseCol, 1.16f), new Color(0.88f, 0.86f, 0.56f), 0.3f), 0.75f);
                }
            }
            // Clover and a scatter of tiny white and yellow flowers, in little drifts.
            for (int i = 0; i < 26; i++)
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 12f, 26f), GRand(rng, 8f, 16f), new Color(0.36f, 0.5f, 0.28f), 0.3f, 6f, GRand(rng, 0f, 3f));
            for (int d = 0; d < 9; d++)
            {
                float cx = GRand(rng, 0, n), cy = GRand(rng, 0, n);
                Color petal = rng.NextDouble() < 0.6 ? new Color(0.98f, 0.97f, 0.92f) : new Color(1f, 0.86f, 0.36f);
                for (int k = 0; k < 14; k++)
                {
                    float x = cx + GRand(rng, -26f, 26f), y = cy + GRand(rng, -16f, 16f);
                    t.Blob(x, y, 1.9f, 1.6f, petal, 0.95f, 0.7f);
                    t.Blob(x, y, 0.7f, 0.7f, new Color(1f, 0.75f, 0.25f), 0.9f, 0.5f);
                }
            }
            return t.ToCanvas();
        }

        static PixelCanvas Water(System.Random rng, int seed)
        {
            int n = GroundSize;
            Color deep = new Color(0.2f, 0.47f, 0.62f), mid = new Color(0.3f, 0.62f, 0.7f), shallow = new Color(0.48f, 0.78f, 0.78f);
            var t = new GroundTile(n, mid);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float a = t.Fbm(x, y, 3, 4, seed);
                    t[x, y] = a < 0.5f ? Color.Lerp(deep, mid, a * 2f) : Color.Lerp(mid, shallow, (a - 0.5f) * 1.6f);
                }
            // Wavelets: soft arcs running across, a dark trough under a bright crest.
            for (int i = 0; i < 170; i++)
            {
                float x = GRand(rng, 0, n), y = GRand(rng, 0, n), len = GRand(rng, 14f, 44f), bend = GRand(rng, 1.2f, 3.2f);
                float bright = GRand(rng, 0.25f, 0.55f), width = GRand(rng, 1.3f, 2.4f);
                const int segs = 8;
                for (int k = 0; k < segs; k++)
                {
                    float u0 = k / (float)segs - 0.5f, u1 = (k + 1) / (float)segs - 0.5f;
                    var a = new Vector2(x + u0 * len, y + bend * (1f - 4f * u0 * u0));
                    var b = new Vector2(x + u1 * len, y + bend * (1f - 4f * u1 * u1));
                    float taper = 1f - Mathf.Abs(u0 + u1);      // thin at the ends
                    t.Stroke(a + Vector2.down * 2.4f, b + Vector2.down * 2.4f, width * 1.4f * taper + 0.5f, deep, 0.22f);
                    t.Stroke(a, b, width * taper + 0.4f, new Color(0.86f, 0.96f, 0.95f), bright);
                }
            }
            // Glints of sun.
            for (int i = 0; i < 90; i++)
                t.Blob(GRand(rng, 0, n), GRand(rng, 0, n), GRand(rng, 1.5f, 4f), 1f, new Color(1f, 0.98f, 0.9f), 0.8f, 0.8f);
            return t.ToCanvas();
        }

        /// <summary>Repeat a 256 tile 2 x 2 into a 512 tile, so every surface covers 8 x 8 units.</summary>
        static PixelCanvas Repeat2x2(PixelCanvas small)
        {
            var c = new PixelCanvas(small.Width * 2, small.Height * 2);
            for (int y = 0; y < c.Height; y++)
                for (int x = 0; x < c.Width; x++)
                    c.Set(x, y, small.Get(x % small.Width, y % small.Height));
            return c;
        }
    }
}
