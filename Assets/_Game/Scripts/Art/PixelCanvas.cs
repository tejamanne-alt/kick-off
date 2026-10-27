using System;
using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Tiny software rasterizer for procedural storybook art: anti-aliased
    /// shapes, an ink-outline pass and watercolour paper grain. Pixel space,
    /// y up, (0,0) at the bottom-left.
    /// </summary>
    public class PixelCanvas
    {
        public readonly int Width;
        public readonly int Height;
        readonly Color[] px;

        public PixelCanvas(int width, int height)
        {
            Width = width;
            Height = height;
            px = new Color[width * height];
        }

        public Color Get(int x, int y)
        {
            if (x < 0 || y < 0 || x >= Width || y >= Height) return Color.clear;
            return px[y * Width + x];
        }

        public void Set(int x, int y, Color c)
        {
            if (x < 0 || y < 0 || x >= Width || y >= Height) return;
            px[y * Width + x] = c;
        }

        /// <summary>Alpha-composite <paramref name="c"/> over the pixel with extra coverage <paramref name="cover"/>.</summary>
        public void Blend(int x, int y, Color c, float cover)
        {
            if (x < 0 || y < 0 || x >= Width || y >= Height) return;
            float a = Mathf.Clamp01(c.a * cover);
            if (a <= 0f) return;
            int i = y * Width + x;
            Color d = px[i];
            float outA = a + d.a * (1f - a);
            if (outA <= 0f) return;
            px[i] = new Color(
                (c.r * a + d.r * d.a * (1f - a)) / outA,
                (c.g * a + d.g * d.a * (1f - a)) / outA,
                (c.b * a + d.b * d.a * (1f - a)) / outA,
                outA);
        }

        public void Clear(Color c)
        {
            for (int i = 0; i < px.Length; i++) px[i] = c;
        }

        /// <summary>Fill every pixel where <paramref name="coverage"/> returns 0..1 (sampled at pixel centres, 2x2 supersampled).</summary>
        public void Fill(Func<float, float, float> coverage, Color c, int x0 = 0, int y0 = 0, int x1 = -1, int y1 = -1)
        {
            if (x1 < 0) x1 = Width - 1;
            if (y1 < 0) y1 = Height - 1;
            x0 = Mathf.Max(0, x0); y0 = Mathf.Max(0, y0);
            x1 = Mathf.Min(Width - 1, x1); y1 = Mathf.Min(Height - 1, y1);
            for (int y = y0; y <= y1; y++)
            {
                for (int x = x0; x <= x1; x++)
                {
                    float cov = (coverage(x + 0.25f, y + 0.25f) + coverage(x + 0.75f, y + 0.25f)
                               + coverage(x + 0.25f, y + 0.75f) + coverage(x + 0.75f, y + 0.75f)) * 0.25f;
                    if (cov > 0f) Blend(x, y, c, cov);
                }
            }
        }

        /// <summary>Darken/tint pixels that already have paint (never adds paint to empty space).</summary>
        public void Shade(Func<float, float, float> amount, Color c)
        {
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    int i = y * Width + x;
                    Color d = px[i];
                    if (d.a <= 0f) continue;
                    float k = Mathf.Clamp01(amount(x + 0.5f, y + 0.5f)) * c.a;
                    if (k <= 0f) continue;
                    px[i] = new Color(Mathf.Lerp(d.r, c.r, k), Mathf.Lerp(d.g, c.g, k), Mathf.Lerp(d.b, c.b, k), d.a);
                }
            }
        }

        /// <summary>Run a draw call at x offsets 0, -Width and +Width so shapes crossing an edge wrap (tileable art).</summary>
        public void Wrapped(Action<float> drawAtOffset)
        {
            drawAtOffset(0f);
            drawAtOffset(-Width);
            drawAtOffset(Width);
        }

        public void FillRect(float x0, float y0, float x1, float y1, Color c)
        {
            Fill((x, y) => x >= x0 && x <= x1 && y >= y0 && y <= y1 ? 1f : 0f, c,
                Mathf.FloorToInt(x0) - 1, Mathf.FloorToInt(y0) - 1, Mathf.CeilToInt(x1) + 1, Mathf.CeilToInt(y1) + 1);
        }

        public void FillRoundRect(float x0, float y0, float x1, float y1, float r, Color c)
        {
            Fill((x, y) =>
            {
                float cx = Mathf.Clamp(x, x0 + r, x1 - r);
                float cy = Mathf.Clamp(y, y0 + r, y1 - r);
                float dx = x - cx, dy = y - cy;
                return dx * dx + dy * dy <= r * r ? 1f : 0f;
            }, c, Mathf.FloorToInt(x0) - 1, Mathf.FloorToInt(y0) - 1, Mathf.CeilToInt(x1) + 1, Mathf.CeilToInt(y1) + 1);
        }

        public void FillEllipse(float cx, float cy, float rx, float ry, Color c)
        {
            Fill((x, y) =>
            {
                float dx = (x - cx) / rx, dy = (y - cy) / ry;
                return dx * dx + dy * dy <= 1f ? 1f : 0f;
            }, c, Mathf.FloorToInt(cx - rx) - 1, Mathf.FloorToInt(cy - ry) - 1, Mathf.CeilToInt(cx + rx) + 1, Mathf.CeilToInt(cy + ry) + 1);
        }

        public void FillCircle(float cx, float cy, float r, Color c) { FillEllipse(cx, cy, r, r, c); }

        public void FillPolygon(Vector2[] pts, Color c)
        {
            float minX = float.MaxValue, minY = float.MaxValue, maxX = float.MinValue, maxY = float.MinValue;
            foreach (var p in pts)
            {
                minX = Mathf.Min(minX, p.x); minY = Mathf.Min(minY, p.y);
                maxX = Mathf.Max(maxX, p.x); maxY = Mathf.Max(maxY, p.y);
            }
            Fill((x, y) => Inside(pts, x, y) ? 1f : 0f, c,
                Mathf.FloorToInt(minX) - 1, Mathf.FloorToInt(minY) - 1, Mathf.CeilToInt(maxX) + 1, Mathf.CeilToInt(maxY) + 1);
        }

        /// <summary>Fill under a curve y = top(x) (hills, waves, grass).</summary>
        public void FillBelow(Func<float, float> top, Color c, float bottom = 0f)
        {
            Fill((x, y) => y <= top(x) && y >= bottom ? 1f : 0f, c);
        }

        /// <summary>Thick line with round caps.</summary>
        public void Line(Vector2 a, Vector2 b, float thickness, Color c)
        {
            float r = thickness * 0.5f;
            Vector2 ab = b - a;
            float len2 = Mathf.Max(ab.sqrMagnitude, 0.0001f);
            Fill((x, y) =>
            {
                Vector2 p = new Vector2(x, y);
                float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / len2);
                return (p - (a + ab * t)).sqrMagnitude <= r * r ? 1f : 0f;
            }, c, Mathf.FloorToInt(Mathf.Min(a.x, b.x) - r) - 1, Mathf.FloorToInt(Mathf.Min(a.y, b.y) - r) - 1,
               Mathf.CeilToInt(Mathf.Max(a.x, b.x) + r) + 1, Mathf.CeilToInt(Mathf.Max(a.y, b.y) + r) + 1);
        }

        static bool Inside(Vector2[] pts, float x, float y)
        {
            bool inside = false;
            for (int i = 0, j = pts.Length - 1; i < pts.Length; j = i++)
            {
                if ((pts[i].y > y) != (pts[j].y > y) &&
                    x < (pts[j].x - pts[i].x) * (y - pts[i].y) / (pts[j].y - pts[i].y) + pts[i].x)
                    inside = !inside;
            }
            return inside;
        }

        /// <summary>
        /// Hand-drawn ink outline around everything drawn so far: pixels near the
        /// alpha edge get darkened, with a little wobble so lines feel drawn.
        /// </summary>
        public void Ink(Color ink, float thickness, int seed = 0, bool wrapX = false)
        {
            var src = (Color[])px.Clone();
            int r = Mathf.CeilToInt(thickness) + 1;
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    int i = y * Width + x;
                    if (src[i].a < 0.5f) continue;
                    float wobble = thickness * (0.75f + 0.5f * Mathf.PerlinNoise(x * 0.08f + seed, y * 0.08f + seed * 1.7f));
                    float nearest = float.MaxValue;
                    for (int dy = -r; dy <= r; dy++)
                    {
                        for (int dx = -r; dx <= r; dx++)
                        {
                            int sx = x + dx, sy = y + dy;
                            if (wrapX) sx = (sx % Width + Width) % Width;
                            bool outside = sx < 0 || sy < 0 || sx >= Width || sy >= Height || src[sy * Width + sx].a < 0.5f;
                            if (!outside) continue;
                            float d = Mathf.Sqrt(dx * dx + dy * dy);
                            if (d < nearest) nearest = d;
                        }
                    }
                    if (nearest <= wobble)
                    {
                        float k = Mathf.Clamp01(wobble - nearest + 0.5f);
                        Color c = Color.Lerp(src[i], ink, k * ink.a);
                        c.a = src[i].a;
                        px[i] = c;
                    }
                }
            }
        }

        /// <summary>Watercolour paper grain: soft blotches plus fine speckle, multiplied into colour.</summary>
        public void Grain(float amount, int seed = 0, float scale = 0.06f, bool wrapX = false)
        {
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < Width; x++)
                {
                    int i = y * Width + x;
                    Color c = px[i];
                    if (c.a <= 0f) continue;
                    float blotch = Mathf.PerlinNoise(x * scale + seed * 3.1f, y * scale + seed * 1.3f);
                    if (wrapX)
                    {
                        // Cross-fade with the noise one period to the left so the pattern repeats exactly.
                        float other = Mathf.PerlinNoise((x - Width) * scale + seed * 3.1f, y * scale + seed * 1.3f);
                        blotch = Mathf.Lerp(blotch, other, x / (float)Width);
                    }
                    float fine = Hash(wrapX ? x % Width : x, y, seed);
                    float k = 1f - amount * (0.6f * blotch + 0.4f * fine);
                    px[i] = new Color(c.r * k, c.g * k, c.b * k, c.a);
                }
            }
        }

        /// <summary>Alpha-composite another canvas of the same size on top of this one.</summary>
        public void Stamp(PixelCanvas layer)
        {
            int w = Math.Min(Width, layer.Width), h = Math.Min(Height, layer.Height);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    Color c = layer.px[y * layer.Width + x];
                    if (c.a > 0f) Blend(x, y, new Color(c.r, c.g, c.b, 1f), c.a);
                }
        }

        /// <summary>Make the left and right edges blend so the texture tiles horizontally.</summary>
        public void MakeTileableX(int blend)
        {
            var src = (Color[])px.Clone();
            for (int y = 0; y < Height; y++)
            {
                for (int x = 0; x < blend; x++)
                {
                    float t = x / (float)blend;
                    int a = y * Width + x;
                    int b = y * Width + (Width - blend + x);
                    px[a] = Color.Lerp(src[b], src[a], t);
                }
            }
        }

        static float Hash(int x, int y, int seed)
        {
            unchecked
            {
                int h = x * 374761393 + y * 668265263 + seed * 1442695041;
                h = (h ^ (h >> 13)) * 1274126177;
                return ((h ^ (h >> 16)) & 0xFFFF) / 65535f;
            }
        }

        public Texture2D ToTexture(bool repeat = false)
        {
            var tex = new Texture2D(Width, Height, TextureFormat.RGBA32, false);
            tex.SetPixels(px);
            tex.wrapMode = repeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            tex.filterMode = FilterMode.Bilinear;
            tex.Apply();
            return tex;
        }

        public byte[] ToPng()
        {
            var tex = ToTexture();
            byte[] png = tex.EncodeToPNG();
            UnityEngine.Object.DestroyImmediate(tex);
            return png;
        }
    }
}
