using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// The arithmetic of a picture shown in a view that can be panned and zoomed (the town map, see <see cref="UIMapView"/>):
    /// pure functions of the sizes, so the tests run the same numbers as the screen. The picture is a block of
    /// <c>design</c> pixels (y down) with its pivot in its middle; the view is a rect of <c>view</c> canvas units centred on 0;
    /// a view state is the block's scale and its middle's position in the view (canvas units, y up).
    /// </summary>
    public static class MapViewMath
    {
        /// <summary>The scale at which <paramref name="fit"/> (design pixels) fits whole in a room of <paramref name="room"/> canvas units.</summary>
        public static float FitScale(Vector2 room, Rect fit)
        {
            if (room.x <= 1f || room.y <= 1f || fit.width <= 0f || fit.height <= 0f) return 1f;
            return Mathf.Min(room.x / fit.width, room.y / fit.height);
        }

        /// <summary>
        /// The fitted scale for a view: the one at which <paramref name="fit"/> fits the room, or a little more (up to
        /// <paramref name="slack"/>, a fraction) if that is what it takes for the picture (<paramref name="cover"/>) to fill the
        /// whole view, so the screen shows town to its edges rather than a thin border of the mat.
        /// </summary>
        public static float FitScale(Vector2 room, Rect fit, Vector2 view, Rect cover, float slack)
        {
            float s = FitScale(room, fit);
            if (view.x <= 1f || view.y <= 1f || cover.width <= 0f || cover.height <= 0f) return s;
            float fill = Mathf.Max(view.x / cover.width, view.y / cover.height);
            return Mathf.Max(s, Mathf.Min(fill, s * (1f + Mathf.Max(0f, slack))));
        }

        /// <summary>Where a point of the picture (design pixels, y down) is in the view, for the block at <paramref name="scale"/> and <paramref name="position"/>.</summary>
        public static Vector2 ToView(Vector2 design, Vector2 designPoint, float scale, Vector2 position)
        {
            return position + scale * new Vector2(designPoint.x - design.x * 0.5f, design.y * 0.5f - designPoint.y);
        }

        /// <summary>The point of the picture (design pixels, y down) under a point of the view.</summary>
        public static Vector2 ToDesign(Vector2 design, Vector2 viewPoint, float scale, Vector2 position)
        {
            Vector2 d = (viewPoint - position) / Mathf.Max(scale, 1e-5f);
            return new Vector2(d.x + design.x * 0.5f, design.y * 0.5f - d.y);
        }

        /// <summary>The block's position that puts the picture's <paramref name="designPoint"/> at <paramref name="viewPoint"/>.</summary>
        public static Vector2 PositionFor(Vector2 design, Vector2 designPoint, Vector2 viewPoint, float scale)
        {
            return viewPoint - scale * new Vector2(designPoint.x - design.x * 0.5f, design.y * 0.5f - designPoint.y);
        }

        /// <summary>
        /// The block's position kept so that <paramref name="cover"/> (design pixels: the picture, or the part of it that has to
        /// stay on screen) covers the view where it can: along an axis where it is bigger than the view it may not pull an edge
        /// inside the view's edge; along an axis where it is smaller it stays where <paramref name="centreWhenSmall"/> puts it.
        /// </summary>
        public static Vector2 ClampPosition(Vector2 design, Rect cover, Vector2 view, float scale, Vector2 position, Vector2 centreWhenSmall)
        {
            // The cover's edges in the view at this position (y up: the cover's top, yMin in design, is its upper edge).
            Vector2 lo = ToView(design, new Vector2(cover.xMin, cover.yMax), scale, position);
            Vector2 hi = ToView(design, new Vector2(cover.xMax, cover.yMin), scale, position);
            Vector2 half = view * 0.5f;
            Vector2 p = position;
            if (hi.x - lo.x <= view.x) p.x = centreWhenSmall.x;
            else
            {
                if (lo.x > -half.x) p.x -= lo.x + half.x;
                if (hi.x < half.x) p.x += half.x - hi.x;
            }
            if (hi.y - lo.y <= view.y) p.y = centreWhenSmall.y;
            else
            {
                if (lo.y > -half.y) p.y -= lo.y + half.y;
                if (hi.y < half.y) p.y += half.y - hi.y;
            }
            return p;
        }

        /// <summary>The position after zooming from <paramref name="from"/> to <paramref name="to"/> about a point of the view, which stays put.</summary>
        public static Vector2 ZoomAbout(Vector2 position, float from, float to, Vector2 viewPoint)
        {
            if (from <= 0f) return position;
            return viewPoint + (position - viewPoint) * (to / from);
        }

        /// <summary>
        /// How much the things drawn on the picture (nodes, pins, names, route lines) are scaled against the picture at a zoom
        /// (1 = fitted): they grow on screen as the view zooms in, but more slowly than the picture, so they get bigger and further
        /// apart (easier to tap) without covering the town. Zoomed out of the fit they shrink with it.
        /// </summary>
        public static float ItemScale(float zoom, float grow = 0.4f)
        {
            if (zoom <= 1f) return 1f;
            return Mathf.Pow(zoom, grow - 1f);
        }
    }
}
