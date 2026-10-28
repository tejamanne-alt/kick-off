using UnityEngine;

namespace DribbleToSchool.Art
{
    /// <summary>Street furniture for the hazards: a front-view car, pedestrian signal figures and a fountain jet.</summary>
    public static partial class ProceduralArt
    {
        /// <summary>
        /// A small car seen from the front (driving toward the camera), tintable body.
        /// Baked at 115 px per unit it is about 1.9 units (1.7 m) wide and 1.6 tall, wheels on y = 4.
        /// </summary>
        public static PixelCanvas CarFront()
        {
            var c = new PixelCanvas(240, 196);
            Color body = Grey(0.96f), glass = new Color(0.5f, 0.6f, 0.72f), dark = new Color(0.16f, 0.16f, 0.18f);
            c.FillRoundRect(14, 4, 54, 46, 10, dark);                                   // wheels
            c.FillRoundRect(186, 4, 226, 46, 10, dark);
            c.FillRoundRect(8, 28, 232, 112, 24, body);                                 // lower body
            c.FillPolygon(new[] { new Vector2(30, 108), new Vector2(210, 108), new Vector2(188, 184), new Vector2(52, 184) }, body); // cabin
            c.FillPolygon(new[] { new Vector2(42, 114), new Vector2(198, 114), new Vector2(180, 174), new Vector2(60, 174) }, glass); // windscreen
            c.FillPolygon(new[] { new Vector2(130, 118), new Vector2(150, 118), new Vector2(116, 170), new Vector2(98, 170) }, Color.Lerp(glass, White, 0.35f)); // glint
            c.FillRoundRect(0, 112, 22, 126, 5, body);                                  // mirrors
            c.FillRoundRect(218, 112, 240, 126, 5, body);
            c.Shade((x, y) => y < 52 ? 1f : 0f, Grey(0.76f));                           // bumper in shadow
            c.FillRoundRect(22, 74, 66, 96, 8, new Color(1f, 0.95f, 0.7f));             // headlights
            c.FillRoundRect(174, 74, 218, 96, 8, new Color(1f, 0.95f, 0.7f));
            c.FillRoundRect(84, 64, 156, 92, 6, Grey(0.3f));                            // grille
            for (float y = 70; y < 90; y += 6) c.FillRect(88, y, 152, y + 2, Grey(0.45f));
            c.FillRect(96, 34, 144, 52, White);                                         // number plate
            c.FillRect(100, 40, 140, 46, Grey(0.4f));
            c.Ink(Ink, 2.5f, 41);
            return c;
        }

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
    }
}
