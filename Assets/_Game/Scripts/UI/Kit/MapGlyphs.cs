using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// The two small pictures the map screen draws itself (the town is a rendered picture): a house for home and a flagged
    /// school building for the goal, as flat shapes with a <see cref="MapPainter"/>. They are used on the pins over the
    /// picture and on the ends of the level strip. <paramref name="s"/> is the glyph's width.
    /// </summary>
    public static class MapGlyphs
    {
        public static readonly Color Ink = new Color(0.17f, 0.19f, 0.27f);

        /// <summary>A house: pitched roof, walls, a door and a window, all in <paramref name="fill"/> on <paramref name="door"/>-coloured details.</summary>
        public static void House(MapPainter p, Vector2 c, float s, Color fill, Color door)
        {
            float h = s * 0.5f;
            p.Polygon(new[] { c + new Vector2(-s * 0.56f, -h * 0.04f), c + new Vector2(s * 0.56f, -h * 0.04f), c + new Vector2(0f, -h * 1.02f) }, fill);          // roof
            p.Polygon(new[] { c + new Vector2(-s * 0.4f, -h * 0.04f), c + new Vector2(s * 0.4f, -h * 0.04f), c + new Vector2(s * 0.4f, h * 0.9f), c + new Vector2(-s * 0.4f, h * 0.9f) }, fill);   // walls
            p.Polygon(new[] { c + new Vector2(-s * 0.11f, h * 0.34f), c + new Vector2(s * 0.11f, h * 0.34f), c + new Vector2(s * 0.11f, h * 0.9f), c + new Vector2(-s * 0.11f, h * 0.9f) }, door);       // door
            p.Polygon(new[] { c + new Vector2(s * 0.17f, h * 0.2f), c + new Vector2(s * 0.32f, h * 0.2f), c + new Vector2(s * 0.32f, h * 0.45f), c + new Vector2(s * 0.17f, h * 0.45f) }, door);        // window
        }

        /// <summary>The school: a wide building with a tower, a flag, a door and windows.</summary>
        public static void School(MapPainter p, Vector2 c, float s, Color fill, Color detail)
        {
            float h = s * 0.5f;
            p.Polygon(new[] { c + new Vector2(-s * 0.5f, h * 0.9f), c + new Vector2(s * 0.5f, h * 0.9f), c + new Vector2(s * 0.5f, -h * 0.1f), c + new Vector2(-s * 0.5f, -h * 0.1f) }, fill);        // wings
            p.Polygon(new[] { c + new Vector2(-s * 0.2f, h * 0.9f), c + new Vector2(s * 0.2f, h * 0.9f), c + new Vector2(s * 0.2f, -h * 0.55f), c + new Vector2(-s * 0.2f, -h * 0.55f) }, fill);       // tower
            p.Polygon(new[] { c + new Vector2(-s * 0.25f, -h * 0.55f), c + new Vector2(s * 0.25f, -h * 0.55f), c + new Vector2(0f, -h * 0.95f) }, fill);                                           // tower roof
            p.Stroke(new[] { c + new Vector2(0f, -h * 0.95f), c + new Vector2(0f, -h * 1.3f) }, s * 0.05f, fill, false, true);                                                                       // flag pole
            p.Polygon(new[] { c + new Vector2(0f, -h * 1.3f), c + new Vector2(s * 0.24f, -h * 1.18f), c + new Vector2(0f, -h * 1.06f) }, fill);                                                      // flag
            p.Polygon(new[] { c + new Vector2(-s * 0.08f, h * 0.9f), c + new Vector2(s * 0.08f, h * 0.9f), c + new Vector2(s * 0.08f, h * 0.35f), c + new Vector2(-s * 0.08f, h * 0.35f) }, detail);    // door
            for (int i = 0; i < 2; i++)
            {
                float x = (i == 0 ? -1f : 1f) * s * 0.36f;
                p.Polygon(new[] { c + new Vector2(x - s * 0.06f, h * 0.15f), c + new Vector2(x + s * 0.06f, h * 0.15f), c + new Vector2(x + s * 0.06f, h * 0.5f), c + new Vector2(x - s * 0.06f, h * 0.5f) }, detail);
            }
        }

        /// <summary>A map pin: a round head in <paramref name="colour"/> with a white rim and a point at <paramref name="tip"/>; the head's centre is returned.</summary>
        public static Vector2 Pin(MapPainter p, Vector2 tip, float headRadius, Color colour)
        {
            Vector2 head = tip + new Vector2(0f, -headRadius * 1.75f);
            p.Polygon(new[] { tip + new Vector2(0f, 3f), head + new Vector2(-headRadius * 0.62f, headRadius * 0.7f), head + new Vector2(headRadius * 0.62f, headRadius * 0.7f) }, Color.white);
            p.Disc(head, headRadius + 6f, Ink);
            p.Disc(head, headRadius + 3.5f, Color.white);
            p.Disc(head, headRadius, colour);
            p.Polygon(new[] { tip + new Vector2(0f, -headRadius * 0.3f), head + new Vector2(-headRadius * 0.5f, headRadius * 0.55f), head + new Vector2(headRadius * 0.5f, headRadius * 0.55f) }, colour);
            return head;
        }
    }
}
