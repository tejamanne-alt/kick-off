using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>
    /// Draws cosmetic sprites from their colours and pattern: hand-inked balls,
    /// waving-ready flags, outfit and trail swatches. Results are cached.
    /// </summary>
    public static class CosmeticArt
    {
        static readonly Dictionary<string, Sprite> cache = new Dictionary<string, Sprite>();
        static readonly Color Ink = new Color(0.16f, 0.13f, 0.12f);

        /// <summary>Sprite for any cosmetic, suitable for the shop grid.</summary>
        public static Sprite Icon(CosmeticItem item)
        {
            switch (item.category)
            {
                case CosmeticCategory.Ball: return BallSprite(item);
                case CosmeticCategory.Flag: return FlagSprite(item);
                case CosmeticCategory.Outfit: return OutfitSprite(item);
                default: return TrailSprite(item);
            }
        }

        /// <summary>128 px ball, 1 world unit across at 128 PPU.</summary>
        public static Sprite BallSprite(CosmeticItem item)
        {
            return Cached("ball:" + item.id, () => DrawBall(item, 128));
        }

        public static Sprite FlagSprite(CosmeticItem item)
        {
            return Cached("flag:" + item.id, () => DrawFlag(item, 96, 64));
        }

        public static Sprite OutfitSprite(CosmeticItem item)
        {
            return Cached("outfit:" + item.id, () => DrawOutfit(item, 96));
        }

        public static Sprite TrailSprite(CosmeticItem item)
        {
            return Cached("trail:" + item.id, () => DrawTrail(item, 128, 64));
        }

        /// <summary>Colour along a trail (0 = at the ball, 1 = tail end).</summary>
        public static Color TrailColor(CosmeticItem item, float t)
        {
            if (item.pattern == CosmeticPattern.Rainbow)
                return Color.HSVToRGB(Mathf.Repeat(t * 0.85f, 1f), 0.65f, 1f);
            return Color.Lerp(item.primary, item.secondary, t);
        }

        static Sprite Cached(string key, System.Func<Sprite> make)
        {
            Sprite s;
            if (cache.TryGetValue(key, out s) && s != null) return s;
            s = make();
            cache[key] = s;
            return s;
        }

        static Sprite ToSprite(Texture2D tex, float ppu)
        {
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.filterMode = FilterMode.Bilinear;
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), ppu);
        }

        // ---------- Ball ----------

        static Sprite DrawBall(CosmeticItem item, int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            var pixels = new Color[size * size];
            for (int py = 0; py < size; py++)
            {
                for (int px = 0; px < size; px++)
                {
                    // uv in [-1, 1], y up
                    float u = (px + 0.5f) / size * 2f - 1f;
                    float v = (py + 0.5f) / size * 2f - 1f;
                    float r = Mathf.Sqrt(u * u + v * v);
                    float edge = Mathf.Clamp01((1f - r) * size * 0.5f);   // anti-aliased disc
                    if (edge <= 0f) { pixels[py * size + px] = Color.clear; continue; }

                    Color c = BallPattern(item, u, v, r);

                    // Soft light from the top-left, darker bottom-right.
                    float light = Mathf.Clamp01(0.55f + 0.45f * (-u * 0.5f + v * 0.7f) * (1f - r * 0.3f));
                    c = Color.Lerp(c * 0.72f, c, light);
                    // Highlight
                    float hl = Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(-0.35f, 0.4f)) / 0.35f);
                    c = Color.Lerp(c, Color.white, hl * hl * 0.35f);
                    // Inked outline
                    float ink = Mathf.Clamp01((r - 0.9f) / 0.06f);
                    c = Color.Lerp(c, Ink, ink);
                    c.a = edge;
                    pixels[py * size + px] = c;
                }
            }
            tex.SetPixels(pixels);
            return ToSprite(tex, size);
        }

        static Color BallPattern(CosmeticItem item, float u, float v, float r)
        {
            Color p = item.primary, s = item.secondary, a = item.accent;
            switch (item.pattern)
            {
                case CosmeticPattern.Classic:
                {
                    if (Pentagon(u, v, 0f, 0f, 0.3f)) return s;
                    for (int k = 0; k < 5; k++)
                    {
                        float ang = Mathf.Deg2Rad * (90f + 72f * k);
                        if (Pentagon(u, v, Mathf.Cos(ang) * 0.78f, Mathf.Sin(ang) * 0.78f, 0.24f)) return s;
                    }
                    // Seams
                    float seam = Mathf.Abs(Mathf.Sin(Mathf.Atan2(v, u) * 5f + 1.57f)) < 0.05f && r > 0.32f && r < 0.62f ? 1f : 0f;
                    return Color.Lerp(p, s, seam * 0.6f);
                }
                case CosmeticPattern.Retro:
                {
                    float panel = Mathf.Abs(Mathf.Sin(u * 5f)) < 0.08f || Mathf.Abs(Mathf.Sin(v * 5f + 0.5f)) < 0.08f ? 1f : 0f;
                    return Color.Lerp(p, s, panel * 0.8f);
                }
                case CosmeticPattern.Stripes:
                    return Mathf.Sin(v * Mathf.PI * 3f) > 0f ? p : s;
                case CosmeticPattern.Diagonal:
                    return Mathf.Sin((u + v) * Mathf.PI * 2.5f) > 0f ? p : s;
                case CosmeticPattern.Dots:
                {
                    float gx = Mathf.Repeat(u * 2.5f + 0.5f, 1f) - 0.5f;
                    float gy = Mathf.Repeat(v * 2.5f + 0.5f, 1f) - 0.5f;
                    return gx * gx + gy * gy < 0.06f ? s : p;
                }
                case CosmeticPattern.Rings:
                    return Mathf.Sin(r * Mathf.PI * 5f) > 0f ? p : s;
                case CosmeticPattern.Planet:
                {
                    // Tilted ring across the middle plus soft bands.
                    float ringV = v - u * 0.35f;
                    if (Mathf.Abs(ringV) < 0.09f) return a;
                    return Mathf.Sin(v * 9f + Mathf.Sin(u * 4f)) > 0.3f ? Color.Lerp(p, s, 0.5f) : p;
                }
                case CosmeticPattern.Fruit:
                {
                    // Leaf near the top, dimpled peel.
                    float lx = u - 0.12f, ly = v - 0.72f;
                    if ((lx * lx) / 0.04f + (ly * ly) / 0.012f < 1f) return a;
                    float dimple = Mathf.PerlinNoise(u * 9f + 10f, v * 9f + 10f);
                    return Color.Lerp(p, s, dimple * 0.35f);
                }
                case CosmeticPattern.Star:
                    return InStar(u, v, 0.6f, 0.26f) ? s : p;
                case CosmeticPattern.Neon:
                {
                    float glow = Mathf.Clamp01(1f - Mathf.Abs(r - 0.72f) / 0.12f);
                    float line = Mathf.Abs(u * 0.8f - v * 0.5f) < 0.05f ? 1f : 0f;
                    Color c = Color.Lerp(p, s, glow);
                    return Color.Lerp(c, a, line);
                }
                default:
                    return p;
            }
        }

        static bool Pentagon(float u, float v, float cx, float cy, float radius)
        {
            float dx = u - cx, dy = v - cy;
            float ang = Mathf.Atan2(dy, dx) - Mathf.PI * 0.5f;
            float seg = Mathf.PI * 2f / 5f;
            float local = Mathf.Repeat(ang, seg) - seg * 0.5f;
            float d = Mathf.Sqrt(dx * dx + dy * dy) * Mathf.Cos(local);
            return d < radius * Mathf.Cos(seg * 0.5f);
        }

        static bool InStar(float u, float v, float outer, float inner)
        {
            float ang = Mathf.Atan2(v, u) - Mathf.PI * 0.5f;
            float seg = Mathf.PI * 2f / 5f;
            float t = Mathf.Abs(Mathf.Repeat(ang, seg) - seg * 0.5f) / (seg * 0.5f);
            float limit = Mathf.Lerp(outer, inner, 1f - t);
            return Mathf.Sqrt(u * u + v * v) < limit;
        }

        // ---------- Flag ----------

        static Sprite DrawFlag(CosmeticItem item, int w, int h)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var pixels = new Color[w * h];
            for (int py = 0; py < h; py++)
            {
                for (int px = 0; px < w; px++)
                {
                    float u = (px + 0.5f) / w;      // 0..1 left to right
                    float v = (py + 0.5f) / h;      // 0..1 bottom to top
                    Color c = FlagPattern(item, u, v);
                    // Gentle cloth shading and inked border.
                    c *= 0.9f + 0.1f * Mathf.Sin(u * Mathf.PI * 3f);
                    bool border = px < 2 || py < 2 || px >= w - 2 || py >= h - 2;
                    if (border) c = Ink;
                    c.a = 1f;
                    pixels[py * w + px] = c;
                }
            }
            tex.SetPixels(pixels);
            return ToSprite(tex, w);
        }

        static Color FlagPattern(CosmeticItem item, float u, float v)
        {
            Color p = item.primary, s = item.secondary, a = item.accent;
            switch (item.pattern)
            {
                case CosmeticPattern.VerticalTri: return u < 1f / 3f ? p : u < 2f / 3f ? s : a;
                case CosmeticPattern.HorizontalTri: return v > 2f / 3f ? p : v > 1f / 3f ? s : a;
                case CosmeticPattern.HorizontalBi: return v > 0.5f ? p : s;
                case CosmeticPattern.NordicCross:
                    return (Mathf.Abs(u - 0.38f) < 0.08f || Mathf.Abs(v - 0.5f) < 0.11f) ? s : p;
                case CosmeticPattern.CenterDot:
                {
                    float dx = (u - 0.5f) * 1.5f, dy = v - 0.5f;
                    return dx * dx + dy * dy < 0.07f ? s : p;
                }
                case CosmeticPattern.BandsWithDot:
                {
                    float dx = (u - 0.5f) * 1.5f, dy = v - 0.5f;
                    float d = Mathf.Sqrt(dx * dx + dy * dy);
                    if (Mathf.Abs(d - 0.12f) < 0.025f) return new Color(0.1f, 0.2f, 0.55f);
                    return v > 2f / 3f ? p : v > 1f / 3f ? s : a;
                }
                case CosmeticPattern.Stripes: return Mathf.Sin(v * Mathf.PI * 7f) > 0f ? p : s;
                case CosmeticPattern.Star: return InStar((u - 0.5f) * 3f, (v - 0.5f) * 2f, 0.6f, 0.25f) ? s : p;
                default: return p;
            }
        }

        // ---------- Outfit (shirt + shorts swatch) ----------

        static Sprite DrawOutfit(CosmeticItem item, int size)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            var pixels = new Color[size * size];
            for (int py = 0; py < size; py++)
            {
                for (int px = 0; px < size; px++)
                {
                    float u = (px + 0.5f) / size, v = (py + 0.5f) / size;
                    Color c = Color.clear;
                    bool torso = u > 0.3f && u < 0.7f && v > 0.38f && v < 0.82f;
                    bool sleeves = v > 0.62f && v < 0.82f && ((u > 0.14f && u <= 0.3f) || (u >= 0.7f && u < 0.86f));
                    bool shorts = v > 0.16f && v <= 0.38f && u > 0.3f && u < 0.7f && !(Mathf.Abs(u - 0.5f) < 0.025f && v < 0.3f);
                    bool collar = v > 0.76f && v < 0.82f && Mathf.Abs(u - 0.5f) < 0.07f;
                    if (torso || sleeves)
                    {
                        c = item.primary;
                        if (item.pattern == CosmeticPattern.Stripes && Mathf.Sin(u * Mathf.PI * 14f) > 0.2f) c = item.accent;
                    }
                    if (collar) c = item.accent;
                    if (shorts) c = item.secondary;
                    pixels[py * size + px] = c;
                }
            }
            tex.SetPixels(pixels);
            return ToSprite(tex, size);
        }

        // ---------- Trail swatch ----------

        static Sprite DrawTrail(CosmeticItem item, int w, int h)
        {
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var pixels = new Color[w * h];
            for (int py = 0; py < h; py++)
            {
                for (int px = 0; px < w; px++)
                {
                    float t = 1f - (px + 0.5f) / w;              // 0 at the right (ball side)
                    float centre = 0.5f + Mathf.Sin(t * 5f) * 0.12f;
                    float half = Mathf.Lerp(0.32f, 0.04f, t);
                    float d = Mathf.Abs((py + 0.5f) / h - centre);
                    Color c = item.pattern == CosmeticPattern.None ? Color.clear : TrailColor(item, t);
                    c.a = item.pattern == CosmeticPattern.None ? 0f : Mathf.Clamp01((half - d) * h * 0.5f) * (1f - t * 0.6f);
                    pixels[py * w + px] = c;
                }
            }
            tex.SetPixels(pixels);
            return ToSprite(tex, w);
        }
    }
}
