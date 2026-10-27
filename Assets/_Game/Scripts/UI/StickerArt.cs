using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Die-cut sticker for each level: a white-bordered badge in the chapter's
    /// colour with a little motif (ball, star, heart, sun, wave...).
    /// </summary>
    public static class StickerArt
    {
        static readonly Dictionary<string, Sprite> cache = new Dictionary<string, Sprite>();

        public static Sprite For(string levelId, Color chapterColor)
        {
            Sprite s;
            if (cache.TryGetValue(levelId, out s) && s != null) return s;
            int seed = levelId.GetHashCode();
            const int size = 160;
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            int motif = Mathf.Abs(seed) % 6;
            Color accent = Color.HSVToRGB(Mathf.Repeat(Mathf.Abs(seed) * 0.137f, 1f), 0.45f, 1f);
            Color ink = new Color(0.2f, 0.15f, 0.14f);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    // Scalloped die-cut edge
                    float ang = Mathf.Atan2(v, u);
                    float r = Mathf.Sqrt(u * u + v * v);
                    float edge = 0.93f + Mathf.Sin(ang * 10f) * 0.03f;
                    Color c = Color.clear;
                    if (r < edge) c = Color.white;
                    if (r < edge - 0.1f) c = chapterColor;
                    if (r < edge - 0.1f && Motif(motif, u, v)) c = accent;
                    if (r < edge - 0.1f && r > edge - 0.14f) c = Color.Lerp(chapterColor, ink, 0.4f);
                    float aa = Mathf.Clamp01((edge - r) * size * 0.5f);
                    if (c.a > 0f) c.a = aa;
                    // Glossy highlight
                    float hl = Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(-0.35f, 0.45f)) / 0.35f);
                    c = Color.Lerp(c, Color.white, hl * 0.35f * c.a);
                    tex.SetPixel(x, y, c);
                }
            }
            tex.Apply();
            s = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
            cache[levelId] = s;
            return s;
        }

        static bool Motif(int motif, float u, float v)
        {
            switch (motif)
            {
                case 0: return u * u + v * v < 0.18f && Mathf.Abs(Mathf.Sin(Mathf.Atan2(v, u) * 5f)) > 0.6f;   // ball
                case 1:   // star
                {
                    float ang = Mathf.Atan2(v, u) - Mathf.PI * 0.5f;
                    float seg = Mathf.PI * 2f / 5f;
                    float t = Mathf.Abs(Mathf.Repeat(ang, seg) - seg * 0.5f) / (seg * 0.5f);
                    return Mathf.Sqrt(u * u + v * v) < Mathf.Lerp(0.5f, 0.22f, 1f - t);
                }
                case 2:   // heart
                {
                    float x = u * 1.6f, y = v * 1.6f + 0.3f;
                    float a = x * x + y * y - 0.6f;
                    return a * a * a - x * x * y * y * y < 0f;
                }
                case 3: return u * u + v * v < 0.12f || (Mathf.Abs(Mathf.Sin(Mathf.Atan2(v, u) * 6f)) > 0.85f && u * u + v * v < 0.35f);   // sun
                case 4: return Mathf.Abs(v - Mathf.Sin(u * 6f) * 0.12f) < 0.09f || Mathf.Abs(v + 0.28f - Mathf.Sin(u * 6f + 1f) * 0.12f) < 0.07f;   // waves
                default: return Mathf.Abs(u) < 0.12f && Mathf.Abs(v) < 0.5f || Mathf.Abs(v) < 0.12f && Mathf.Abs(u) < 0.5f;   // plus
            }
        }
    }
}
