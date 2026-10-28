using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>Street furniture for the hazards: pedestrian signal figures and a fountain jet.</summary>
    public static partial class ProceduralArt
    {
        /// <summary>Pedestrian signal figure, white so it can be lit red or green. walking = striding figure.</summary>
        public static PixelCanvas SignalFigure(bool walking)
        {
            var c = new PixelCanvas(64, 64);
            c.FillCircle(32, 54, 7, White);
            if (walking)
            {
                c.Line(new Vector2(31, 44), new Vector2(28, 26), 9, White);                 // body leaning into the stride
                c.Line(new Vector2(28, 26), new Vector2(18, 6), 6, White);
                c.Line(new Vector2(28, 26), new Vector2(42, 8), 6, White);
                c.Line(new Vector2(30, 40), new Vector2(18, 30), 5, White);
                c.Line(new Vector2(31, 40), new Vector2(44, 32), 5, White);
            }
            else
            {
                c.FillRoundRect(24, 22, 40, 46, 5, White);                                 // standing still
                c.Line(new Vector2(28, 22), new Vector2(28, 4), 6, White);
                c.Line(new Vector2(36, 22), new Vector2(36, 4), 6, White);
                c.Line(new Vector2(24, 42), new Vector2(20, 24), 5, White);
                c.Line(new Vector2(40, 42), new Vector2(44, 24), 5, White);
            }
            return c;
        }

        /// <summary>A fountain water jet: a tapering column with a highlight, crowned by a splash. 64 x 256, base at the bottom.</summary>
        public static PixelCanvas WaterJet()
        {
            var c = new PixelCanvas(64, 256);
            Color water = new Color(0.74f, 0.89f, 1f, 0.88f), deep = new Color(0.48f, 0.72f, 0.95f, 0.88f);
            c.FillPolygon(new[] { new Vector2(14, 0), new Vector2(50, 0), new Vector2(42, 222), new Vector2(22, 222) }, water);
            c.Shade((x, y) => x < 26 ? 1f : 0f, deep);
            c.Line(new Vector2(40, 8), new Vector2(36, 214), 4f, new Color(1f, 1f, 1f, 0.9f));
            c.Line(new Vector2(30, 30), new Vector2(29, 120), 2f, new Color(1f, 1f, 1f, 0.6f));
            // Crown where the jet breaks up, spilling to both sides.
            foreach (var p in new[] { new Vector3(32, 230, 16), new Vector3(16, 222, 11), new Vector3(48, 222, 11), new Vector3(32, 246, 9), new Vector3(8, 208, 6), new Vector3(56, 208, 6) })
                c.FillCircle(p.x, p.y, p.z, water);
            c.Shade((x, y) => y > 214 && x < 28 ? 1f : 0f, deep);
            c.FillCircle(38, 236, 5, new Color(1f, 1f, 1f, 0.95f));
            return c;
        }

        /// <summary>
        /// The side street seen running away from the camera: an asphalt trapezoid narrowing to the
        /// back, kerbs along its sides and centre dashes shrinking with distance. 256 x 96, near edge at the bottom.
        /// </summary>
        public static PixelCanvas SideStreet()
        {
            var c = new PixelCanvas(256, 96);
            Color asphalt = new Color(0.36f, 0.36f, 0.4f), far = new Color(0.5f, 0.52f, 0.58f), kerb = new Color(0.84f, 0.84f, 0.82f);
            c.FillPolygon(new[] { new Vector2(0, 0), new Vector2(256, 0), new Vector2(196, 96), new Vector2(60, 96) }, asphalt);
            c.Shade((x, y) => y / 96f * 0.8f, far);                                        // haze with distance
            c.Line(new Vector2(0, 0), new Vector2(60, 96), 5, kerb);
            c.Line(new Vector2(256, 0), new Vector2(196, 96), 5, kerb);
            for (int i = 0; i < 4; i++)
            {
                float y0 = i * 24f + 4f, y1 = y0 + 12f - i * 2f, w0 = 6f - i, w1 = w0 - 0.8f;
                c.FillPolygon(new[] { new Vector2(128 - w0, y0), new Vector2(128 + w0, y0), new Vector2(128 + w1, y1), new Vector2(128 - w1, y1) }, new Color(0.95f, 0.85f, 0.4f));
            }
            return c;
        }

        /// <summary>
        /// Tidewater washing over a stretch of sand: a shallow lens of sea water that tapers to
        /// nothing at both ends, darker in its depth, with a scalloped foam crest and glints.
        /// 256 x 64; the water surface sits 44 px above the bottom.
        /// </summary>
        public static PixelCanvas TideWater()
        {
            var c = new PixelCanvas(256, 64);
            System.Func<float, float> taper = x => { float e = Mathf.Clamp01(Mathf.Min(x, 256f - x) / 48f); return e * e * (3f - 2f * e); };
            System.Func<float, float> surface = x => 44f + Mathf.Sin(x * 0.11f) * 2.5f;
            Color shallow = new Color(0.42f, 0.78f, 0.9f, 0.85f), deep = new Color(0.22f, 0.52f, 0.8f, 0.9f);
            c.Fill((x, y) => y <= surface(x) && y >= 44f - 44f * taper(x) ? 1f : 0f, shallow);
            c.Shade((x, y) => y < 28f ? 1f : 0f, deep);
            // Foam crest along the surface, thinning toward the tapered ends.
            c.Fill((x, y) =>
            {
                float top = surface(x), t = taper(x);
                float band = 3f + 4f * t + Mathf.Abs(Mathf.Sin(x * 0.23f)) * 3f * t;
                return t > 0.05f && y <= top + 1.5f && y >= top - band ? 1f : 0f;
            }, new Color(0.96f, 0.99f, 1f, 0.95f));
            for (int i = 0; i < 6; i++)
            {
                float gx = 50 + i * 30, gy = 18 + (i % 3) * 6;
                c.Line(new Vector2(gx, gy), new Vector2(gx + 14, gy), 2f, new Color(1f, 1f, 1f, 0.55f));
            }
            return c;
        }
    }
}
