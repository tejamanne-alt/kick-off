using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>
    /// Character parts in an anime cel style: flat colour, one hard shadow tone and a
    /// thin dark line. Drawn at 512 px per unit for a teenager about 1.55 units tall
    /// (feet at body y -0.6). Every part faces right; light comes from the front-top,
    /// so shadows sit on the back (left) side. Shirt, trousers and hair are drawn in
    /// light greys so they can be tinted.
    /// </summary>
    public static partial class ProceduralArt
    {
        public const float PartPixelsPerUnit = 512f;

        static readonly Color Line = new Color(0.16f, 0.12f, 0.15f);
        static readonly Color Skin = new Color(0.98f, 0.84f, 0.72f);
        static readonly Color SkinShadow = new Color(0.9f, 0.68f, 0.58f);
        const float LineWidth = 4f;

        /// <summary>Import scale per part: the head and hair are drawn a little larger.</summary>
        public static float PartPpu(string name)
        {
            if (name == "Head" || name == "Hair") return 450f;
            if (name == "Bag") return 620f;
            return PartPixelsPerUnit;
        }

        /// <summary>Names of every character part, for baking.</summary>
        public static readonly string[] PartNames =
        {
            "Head", "Hair", "Torso", "Hips", "Thigh", "Shin", "Shoe", "UpperArm", "Forearm", "Sleeve", "Strap", "Bag",
        };

        public static PixelCanvas Part(string name)
        {
            switch (name)
            {
                case "Head": return Head();
                case "Hair": return Hair();
                case "Torso": return Torso();
                case "Hips": return Hips();
                case "Thigh": return Trouser(72, 210, 30, 25, 11, false);
                case "Shin": return Shin();
                case "Shoe": return Shoe();
                case "UpperArm": return Limb(48, 150, 16, Skin, SkinShadow, 12);
                case "Forearm": return Forearm();
                case "Sleeve": return Sleeve();
                case "Strap": return Strap();
                case "Bag": return Bag();
                default: return new PixelCanvas(4, 4);
            }
        }

        /// <summary>Hard-edged shadow on the back (left) part of whatever is painted.</summary>
        static void BackShadow(PixelCanvas c, float edgeX, Color shadow)
        {
            c.Shade((x, y) => x < edgeX ? 1f : 0f, shadow);
        }

        static PixelCanvas Limb(int w, int h, float half, Color fill, Color shadow, int seed)
        {
            var c = new PixelCanvas(w, h);
            float cx = w * 0.5f;
            c.FillRoundRect(cx - half, 4, cx + half, h - 4, half, fill);
            BackShadow(c, cx - half * 0.35f, shadow);
            c.Ink(Line, LineWidth * 0.8f, seed);
            return c;
        }

        static PixelCanvas Head()
        {
            // Three-quarter view facing right: neck at the bottom centre of the canvas.
            var c = new PixelCanvas(128, 144);
            c.FillRect(46, 0, 74, 40, Skin);                                   // neck
            c.FillEllipse(62, 82, 46, 54, Skin);                               // cranium
            c.FillPolygon(new[]                                                 // jaw and chin
            {
                new Vector2(22, 70), new Vector2(40, 34), new Vector2(76, 16), new Vector2(98, 24),
                new Vector2(108, 44), new Vector2(110, 66), new Vector2(104, 80),
            }, Skin);
            c.FillPolygon(new[] { new Vector2(106, 58), new Vector2(116, 52), new Vector2(108, 46) }, Skin); // nose tip
            // Shadows: the back of the head and under the jaw onto the neck.
            c.Shade((x, y) => x < 36 || (y < 30 && x < 80) ? 1f : 0f, SkinShadow);
            c.FillEllipse(42, 66, 8, 12, Skin);                                // ear
            c.FillEllipse(43, 65, 4, 7, SkinShadow);
            c.Ink(Line, LineWidth, 21);
            // Face details on top of the outline pass so they stay crisp.
            c.FillEllipse(88, 72, 7, 11, new Color(0.13f, 0.1f, 0.13f));      // eye
            c.FillEllipse(88, 76, 5, 5, new Color(0.3f, 0.22f, 0.25f));
            c.FillCircle(90, 79, 2.6f, White);                                 // highlight
            c.Line(new Vector2(78, 89), new Vector2(98, 88), 3.2f, new Color(0.15f, 0.12f, 0.14f)); // upper lid
            c.Line(new Vector2(80, 98), new Vector2(100, 97), 3f, new Color(0.25f, 0.18f, 0.18f));  // brow
            c.Line(new Vector2(96, 33), new Vector2(104, 35), 2.2f, new Color(0.6f, 0.35f, 0.32f)); // mouth
            c.FillEllipse(96, 52, 7, 4, new Color(1f, 0.6f, 0.55f, 0.35f));    // blush
            return c;
        }

        static PixelCanvas Hair()
        {
            // Messy dark spikes: a cap over the top and back of the head (the cranium sits at
            // (80, 84) on this canvas) with bangs falling over the forehead; the face stays clear.
            var c = new PixelCanvas(176, 168);
            Color hair = Grey(0.85f);
            const float cx = 80f, cy = 84f;
            c.Fill((x, y) =>
            {
                float dx = (x - cx + 4f) / 54f, dy = (y - cy - 6f) / 60f;
                if (dx * dx + dy * dy > 1f) return 0f;
                // Hairline: high over the face, dropping down the back of the head.
                float hairline = x > cx - 14f ? cy + 6f + (x - cx) * 0.22f : cy - 30f;
                return y > hairline ? 1f : 0f;
            }, hair);
            var spikes = new[]
            {
                // Back and crown spikes (tip first).
                new[] { new Vector2(8, 66), new Vector2(30, 98), new Vector2(34, 58) },
                new[] { new Vector2(6, 112), new Vector2(26, 128), new Vector2(30, 92) },
                new[] { new Vector2(24, 156), new Vector2(40, 132), new Vector2(60, 144) },
                new[] { new Vector2(70, 166), new Vector2(60, 140), new Vector2(92, 142) },
                new[] { new Vector2(118, 162), new Vector2(94, 142), new Vector2(124, 128) },
                new[] { new Vector2(156, 134), new Vector2(120, 132), new Vector2(132, 108) },
                // Bangs over the forehead, pointing down and forward.
                new[] { new Vector2(146, 92), new Vector2(118, 120), new Vector2(136, 104) },
                new[] { new Vector2(130, 86), new Vector2(104, 114), new Vector2(122, 110) },
                new[] { new Vector2(112, 90), new Vector2(92, 112), new Vector2(110, 112) },
                new[] { new Vector2(96, 94), new Vector2(80, 112), new Vector2(96, 114) },
                // Nape
                new[] { new Vector2(34, 36), new Vector2(30, 66), new Vector2(50, 58) },
            };
            foreach (var sp in spikes) c.FillPolygon(sp, hair);
            c.Shade((x, y) => x < 54 || y < 76 ? 1f : 0f, Grey(0.6f));         // shadow side
            c.Ink(Line, LineWidth, 22);
            c.Line(new Vector2(64, 132), new Vector2(104, 126), 5f, Grey(1f)); // shine
            c.Line(new Vector2(56, 122), new Vector2(76, 120), 4f, Grey(1f));
            return c;
        }

        static PixelCanvas Torso()
        {
            var c = new PixelCanvas(160, 288);
            Color shirt = Grey(0.97f);
            c.FillPolygon(new[]
            {
                new Vector2(12, 6), new Vector2(148, 6), new Vector2(144, 226), new Vector2(128, 266),
                new Vector2(100, 280), new Vector2(60, 280), new Vector2(32, 268), new Vector2(16, 230),
            }, shirt);
            BackShadow(c, 56, Grey(0.8f));
            c.Shade((x, y) => y < 22 ? 1f : 0f, Grey(0.86f));                 // untucked hem
            c.Line(new Vector2(80, 40), new Vector2(96, 110), 3f, Grey(0.82f)); // creases
            c.Line(new Vector2(118, 60), new Vector2(124, 130), 2.5f, Grey(0.84f));
            c.Ink(Line, LineWidth, 23);
            // Open collar
            c.FillPolygon(new[] { new Vector2(96, 282), new Vector2(136, 262), new Vector2(118, 238) }, shirt);
            c.FillPolygon(new[] { new Vector2(96, 282), new Vector2(72, 270), new Vector2(92, 244) }, Grey(0.9f));
            c.Line(new Vector2(96, 282), new Vector2(118, 238), 3f, Line);
            c.Line(new Vector2(118, 238), new Vector2(136, 262), 3f, Line);
            c.Line(new Vector2(96, 282), new Vector2(92, 244), 3f, Line);
            c.Line(new Vector2(116, 228), new Vector2(116, 40), 2.2f, Grey(0.78f)); // button placket
            return c;
        }

        static PixelCanvas Hips()
        {
            var c = new PixelCanvas(128, 80);
            c.FillRoundRect(12, 4, 116, 76, 14, Grey(0.95f));
            BackShadow(c, 44, Grey(0.74f));
            c.FillRect(12, 62, 116, 72, Grey(0.4f));                           // belt
            c.Ink(Line, LineWidth, 24);
            return c;
        }

        static PixelCanvas Shin()
        {
            return Trouser(68, 200, 25, 26, 25, true);
        }

        /// <summary>A trouser segment tapering from <paramref name="halfTop"/> to <paramref name="halfBottom"/>, with an optional hem.</summary>
        static PixelCanvas Trouser(int w, int h, float halfTop, float halfBottom, int seed, bool hem)
        {
            var c = new PixelCanvas(w, h);
            float cx = w * 0.5f;
            Color cloth = Grey(0.95f);
            c.FillPolygon(new[]
            {
                new Vector2(cx - halfBottom, 10), new Vector2(cx + halfBottom, 10),
                new Vector2(cx + halfTop, h - halfTop), new Vector2(cx - halfTop, h - halfTop),
            }, cloth);
            c.FillCircle(cx, h - halfTop, halfTop - 0.5f, cloth);               // rounded joint end
            c.FillCircle(cx, 10 + halfBottom * 0.6f, halfBottom - 0.5f, cloth);
            if (hem) c.FillRect(cx - halfBottom - 2, 4, cx + halfBottom + 2, 22, cloth);
            BackShadow(c, cx - Mathf.Min(halfTop, halfBottom) * 0.35f, Grey(0.74f));
            c.Line(new Vector2(cx + 2, h * 0.55f), new Vector2(cx + 8, h * 0.75f), 2.5f, Grey(0.82f)); // fold
            c.Ink(Line, LineWidth * 0.8f, seed);
            return c;
        }

        static PixelCanvas Shoe()
        {
            // White sneaker, toe to the right.
            var c = new PixelCanvas(128, 60);
            Color upper = new Color(0.96f, 0.96f, 0.97f);
            c.FillPolygon(new[]
            {
                new Vector2(8, 12), new Vector2(120, 12), new Vector2(124, 24), new Vector2(104, 38),
                new Vector2(70, 50), new Vector2(40, 56), new Vector2(14, 52), new Vector2(6, 34),
            }, upper);
            c.FillRoundRect(4, 2, 124, 16, 7, new Color(0.62f, 0.64f, 0.68f));  // sole
            BackShadow(c, 32, new Color(0.78f, 0.8f, 0.86f));
            c.Ink(Line, LineWidth * 0.8f, 26);
            for (int i = 0; i < 3; i++)                                         // laces
                c.Line(new Vector2(58 + i * 12, 46 - i * 4), new Vector2(66 + i * 12, 40 - i * 4), 2.5f, new Color(0.7f, 0.72f, 0.78f));
            c.FillRect(20, 18, 46, 22, new Color(0.35f, 0.45f, 0.75f));          // side stripe
            return c;
        }

        static PixelCanvas Forearm()
        {
            var c = new PixelCanvas(48, 160);
            c.FillRoundRect(9, 36, 39, 156, 15, Skin);
            c.FillEllipse(24, 28, 16, 24, Skin);                               // hand
            c.FillEllipse(34, 40, 6, 9, Skin);                                  // thumb
            BackShadow(c, 18, SkinShadow);
            c.Ink(Line, LineWidth * 0.8f, 27);
            return c;
        }

        static PixelCanvas Sleeve()
        {
            var c = new PixelCanvas(84, 96);
            c.FillPolygon(new[]
            {
                new Vector2(16, 92), new Vector2(68, 92), new Vector2(80, 12), new Vector2(4, 12),
            }, Grey(0.97f));
            c.FillRoundRect(14, 64, 70, 94, 18, Grey(0.97f));
            BackShadow(c, 30, Grey(0.8f));
            c.Shade((x, y) => y < 22 ? 1f : 0f, Grey(0.88f));
            c.Ink(Line, LineWidth * 0.8f, 28);
            return c;
        }

        static PixelCanvas Strap()
        {
            // Bag strap across the chest (front shoulder to back hip) and a loose tie. Same frame as the torso.
            var c = new PixelCanvas(160, 288);
            Color strap = new Color(0.2f, 0.26f, 0.48f);
            c.Line(new Vector2(124, 272), new Vector2(22, 36), 20f, strap);
            c.Line(new Vector2(124, 272), new Vector2(22, 36), 6f, new Color(0.3f, 0.38f, 0.62f));
            Color tie = new Color(0.78f, 0.2f, 0.24f);
            c.FillPolygon(new[] { new Vector2(100, 250), new Vector2(114, 250), new Vector2(112, 236), new Vector2(102, 236) }, tie);
            c.FillPolygon(new[] { new Vector2(102, 236), new Vector2(112, 236), new Vector2(120, 160), new Vector2(108, 148), new Vector2(100, 162) }, tie);
            c.Ink(Line, LineWidth * 0.75f, 29);
            return c;
        }

        static PixelCanvas Bag()
        {
            // School messenger bag, flap at the front.
            var c = new PixelCanvas(132, 104);
            Color body = new Color(0.2f, 0.28f, 0.52f);
            c.FillRoundRect(6, 6, 126, 96, 14, body);
            c.FillPolygon(new[] { new Vector2(6, 96), new Vector2(126, 96), new Vector2(122, 42), new Vector2(10, 46) }, new Color(0.26f, 0.36f, 0.64f)); // flap
            c.Shade((x, y) => x < 34 ? 1f : 0f, new Color(0.14f, 0.18f, 0.36f));
            c.FillRect(58, 26, 72, 62, new Color(0.82f, 0.84f, 0.9f));           // buckle strap
            c.Ink(Line, LineWidth, 30);
            c.Line(new Vector2(14, 48), new Vector2(118, 44), 2.5f, new Color(0.45f, 0.55f, 0.8f)); // flap edge shine
            return c;
        }
    }
}
