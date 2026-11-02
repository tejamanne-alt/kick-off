using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// A small vector painter for the town map: filled polygons, thick polylines, discs and dashes, collected as one triangle
    /// list in map units (y down) with a feathered edge about a pixel wide, so the whole town costs a few meshes instead of
    /// hundreds of Images and its lines stay smooth at any size. <see cref="UIMapMesh"/> draws what it collects. Pure maths:
    /// nothing here needs a GPU, so the harness can run it and look at the triangles.
    /// </summary>
    public sealed class MapPainter
    {
        public readonly List<Vector2> positions = new List<Vector2>();
        public readonly List<Color32> colors = new List<Color32>();
        public readonly List<int> indices = new List<int>();

        /// <summary>Width of the soft edge, in map units (the map is shown at about 0.8, so this is about a pixel).</summary>
        public float feather = 1.3f;

        /// <summary>Corners sharper than this turn (in degrees) of a thick line get a round join instead of a mitre.</summary>
        const float SharpCorner = 38f;

        public int VertexCount { get { return positions.Count; } }
        public int TriangleCount { get { return indices.Count / 3; } }

        public void Clear()
        {
            positions.Clear();
            colors.Clear();
            indices.Clear();
        }

        // ------------------------------------------------------------------ raw triangles

        int Vertex(Vector2 p, Color c)
        {
            positions.Add(p);
            colors.Add(c);
            return positions.Count - 1;
        }

        void Tri(int a, int b, int c)
        {
            indices.Add(a);
            indices.Add(b);
            indices.Add(c);
        }

        void Quad(int a, int b, int c, int d)
        {
            Tri(a, b, c);
            Tri(a, c, d);
        }

        // ------------------------------------------------------------------ filled shapes

        /// <summary>A filled simple polygon (it may be concave), with a feathered edge.</summary>
        public void Polygon(IList<Vector2> poly, Color color)
        {
            int n = poly.Count;
            if (n < 3) return;
            float area = SignedArea(poly);
            if (Mathf.Abs(area) < 0.01f) return;
            int baseIndex = positions.Count;
            for (int i = 0; i < n; i++) Vertex(poly[i], color);
            var order = new List<int>(n);
            for (int i = 0; i < n; i++) order.Add(area > 0f ? i : n - 1 - i);
            Triangulate(poly, order);
            // The soft edge: a ring of transparent vertices pushed out along the (clamped mitre) vertex normals.
            if (feather <= 0f) return;
            Color clear = color;
            clear.a = 0f;
            float outward = area > 0f ? 1f : -1f;
            int ringBase = positions.Count;
            for (int i = 0; i < n; i++)
            {
                Vector2 prev = poly[(i + n - 1) % n], cur = poly[i], next = poly[(i + 1) % n];
                Vector2 n0 = EdgeNormal(prev, cur) * outward, n1 = EdgeNormal(cur, next) * outward;
                Vector2 m = n0 + n1;
                float len = m.magnitude;
                m = len > 1e-4f ? m / len : n1;
                float k = 1f / Mathf.Max(0.5f, Vector2.Dot(m, n1));
                Vertex(cur + m * (feather * Mathf.Min(k, 2f)), clear);
            }
            for (int i = 0; i < n; i++)
            {
                int j = (i + 1) % n;
                Quad(baseIndex + i, baseIndex + j, ringBase + j, ringBase + i);
            }
        }

        public void Polygon(Vector2[] poly, Color color) { Polygon((IList<Vector2>)poly, color); }

        /// <summary>The edge normal (pointing to the right of the direction a to b, in y-up maths).</summary>
        static Vector2 EdgeNormal(Vector2 a, Vector2 b)
        {
            Vector2 d = b - a;
            float len = d.magnitude;
            if (len < 1e-5f) return Vector2.zero;
            return new Vector2(d.y / len, -d.x / len);
        }

        static float SignedArea(IList<Vector2> poly)
        {
            float a = 0f;
            for (int i = 0, n = poly.Count; i < n; i++)
            {
                Vector2 p = poly[i], q = poly[(i + 1) % n];
                a += p.x * q.y - q.x * p.y;
            }
            return a * 0.5f;
        }

        /// <summary>Ear clipping: appends the triangles of a simple polygon whose vertices (in <paramref name="order"/>, counter-clockwise in y-up maths) are the last added.</summary>
        void Triangulate(IList<Vector2> poly, List<int> order)
        {
            int baseIndex = positions.Count - poly.Count;
            int guard = order.Count * order.Count + 10;
            while (order.Count > 3 && guard-- > 0)
            {
                bool clipped = false;
                int count = order.Count;
                for (int i = 0; i < count; i++)
                {
                    int ia = order[(i + count - 1) % count], ib = order[i], ic = order[(i + 1) % count];
                    Vector2 a = poly[ia], b = poly[ib], c = poly[ic];
                    float cross = (b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x);
                    if (cross <= 1e-4f) continue;                   // a reflex (or flat) corner is not an ear
                    bool empty = true;
                    for (int k = 0; k < count && empty; k++)
                    {
                        int ik = order[k];
                        if (ik == ia || ik == ib || ik == ic) continue;
                        if (InTriangle(poly[ik], a, b, c)) empty = false;
                    }
                    if (!empty) continue;
                    Tri(baseIndex + ia, baseIndex + ib, baseIndex + ic);
                    order.RemoveAt(i);
                    clipped = true;
                    break;
                }
                if (!clipped)
                {
                    // Degenerate input (touching edges): fan the rest rather than lose the shape.
                    for (int i = 1; i + 1 < order.Count; i++) Tri(baseIndex + order[0], baseIndex + order[i], baseIndex + order[i + 1]);
                    return;
                }
            }
            if (order.Count == 3) Tri(baseIndex + order[0], baseIndex + order[1], baseIndex + order[2]);
        }

        static bool InTriangle(Vector2 p, Vector2 a, Vector2 b, Vector2 c)
        {
            float d1 = Side(p, a, b), d2 = Side(p, b, c), d3 = Side(p, c, a);
            bool neg = d1 < -1e-4f || d2 < -1e-4f || d3 < -1e-4f;
            bool pos = d1 > 1e-4f || d2 > 1e-4f || d3 > 1e-4f;
            return !(neg && pos) && !(Mathf.Abs(d1) < 1e-4f && Mathf.Abs(d2) < 1e-4f && Mathf.Abs(d3) < 1e-4f);
        }

        static float Side(Vector2 p, Vector2 a, Vector2 b)
        {
            return (p.x - b.x) * (a.y - b.y) - (a.x - b.x) * (p.y - b.y);
        }

        public void Disc(Vector2 center, float radius, Color color)
        {
            Ellipse(center, radius, radius, 0f, color);
        }

        public void Ellipse(Vector2 center, float rx, float ry, float degrees, Color color)
        {
            int n = Mathf.Clamp(Mathf.CeilToInt(Mathf.Max(rx, ry) * 0.6f), 10, 40);
            var pts = new Vector2[n];
            float cs = Mathf.Cos(degrees * Mathf.Deg2Rad), sn = Mathf.Sin(degrees * Mathf.Deg2Rad);
            for (int i = 0; i < n; i++)
            {
                float a = i * Mathf.PI * 2f / n;
                float x = Mathf.Cos(a) * rx, y = Mathf.Sin(a) * ry;
                pts[i] = center + new Vector2(x * cs - y * sn, x * sn + y * cs);
            }
            Polygon(pts, color);
        }

        /// <summary>A (possibly tilted) rectangle given by its centre and size.</summary>
        public void Rect(Vector2 center, Vector2 size, float degrees, Color color)
        {
            Polygon(RectPoints(center, size, degrees), color);
        }

        public static Vector2[] RectPoints(Vector2 center, Vector2 size, float degrees)
        {
            float cs = Mathf.Cos(degrees * Mathf.Deg2Rad), sn = Mathf.Sin(degrees * Mathf.Deg2Rad);
            float hx = size.x * 0.5f, hy = size.y * 0.5f;
            var pts = new Vector2[4];
            for (int i = 0; i < 4; i++)
            {
                float x = (i == 0 || i == 3) ? -hx : hx, y = i < 2 ? -hy : hy;
                pts[i] = center + new Vector2(x * cs - y * sn, x * sn + y * cs);
            }
            return pts;
        }

        /// <summary>A rectangle with rounded corners.</summary>
        public void RoundRect(Vector2 center, Vector2 size, float radius, float degrees, Color color)
        {
            Polygon(RoundRectPoints(center, size, radius, degrees), color);
        }

        public static Vector2[] RoundRectPoints(Vector2 center, Vector2 size, float radius, float degrees)
        {
            float hx = size.x * 0.5f, hy = size.y * 0.5f;
            float r = Mathf.Min(radius, Mathf.Min(hx, hy));
            int steps = Mathf.Clamp(Mathf.CeilToInt(r * 0.5f), 2, 8);
            var list = new List<Vector2>();
            for (int corner = 0; corner < 4; corner++)
            {
                float cx = (corner == 0 || corner == 3) ? -hx + r : hx - r, cy = corner < 2 ? -hy + r : hy - r;
                float a0 = (corner == 0 ? 180f : corner == 1 ? 270f : corner == 2 ? 0f : 90f);
                for (int s = 0; s <= steps; s++)
                {
                    float a = (a0 + 90f * s / steps) * Mathf.Deg2Rad;
                    list.Add(new Vector2(cx + Mathf.Cos(a) * r, cy + Mathf.Sin(a) * r));
                }
            }
            float cs = Mathf.Cos(degrees * Mathf.Deg2Rad), sn = Mathf.Sin(degrees * Mathf.Deg2Rad);
            var pts = new Vector2[list.Count];
            for (int i = 0; i < pts.Length; i++) pts[i] = center + new Vector2(list[i].x * cs - list[i].y * sn, list[i].x * sn + list[i].y * cs);
            return pts;
        }

        // ------------------------------------------------------------------ thick lines

        /// <summary>
        /// A thick line along <paramref name="pts"/> with a soft edge: a strip of mitred quads, with a round join where it
        /// turns sharply and round caps at the ends (unless <paramref name="roundCaps"/> is off: flat ends for dashes).
        /// </summary>
        public void Stroke(IList<Vector2> pts, float width, Color color, bool closed, bool roundCaps)
        {
            var p = new List<Vector2>(pts.Count);
            for (int i = 0; i < pts.Count; i++)
                if (p.Count == 0 || (pts[i] - p[p.Count - 1]).sqrMagnitude > 0.01f) p.Add(pts[i]);
            if (closed && p.Count > 1 && (p[0] - p[p.Count - 1]).sqrMagnitude <= 0.01f) p.RemoveAt(p.Count - 1);
            float half = width * 0.5f;
            if (p.Count == 1)
            {
                if (roundCaps) Disc(p[0], half, color);
                return;
            }
            if (p.Count == 0) return;
            if (closed) p.Add(p[0]);

            // Runs between sharp corners.
            var run = new List<Vector2>();
            run.Add(p[0]);
            for (int i = 1; i < p.Count; i++)
            {
                run.Add(p[i]);
                bool last = i + 1 == p.Count;
                if (last && !closed) break;
                Vector2 d0 = (p[i] - p[i - 1]).normalized;
                Vector2 d1 = last ? (p[1] - p[0]).normalized : (p[i + 1] - p[i]).normalized;
                if (Vector2.Dot(d0, d1) < Mathf.Cos(SharpCorner * Mathf.Deg2Rad))
                {
                    Strip(run, half, color);
                    Disc(p[i], half, color);
                    run.Clear();
                    run.Add(p[i]);
                }
            }
            if (run.Count > 1) Strip(run, half, color);
            if (closed) Disc(p[0], half, color);            // covers the seam of a closed line
            else if (roundCaps)
            {
                Disc(p[0], half, color);
                Disc(p[p.Count - 1], half, color);
            }
        }

        public void Stroke(IList<Vector2> pts, float width, Color color)
        {
            Stroke(pts, width, color, false, true);
        }

        void Strip(List<Vector2> run, float half, Color color)
        {
            int n = run.Count;
            if (n < 2) return;
            Color clear = color;
            clear.a = 0f;
            int baseIndex = positions.Count;
            for (int i = 0; i < n; i++)
            {
                Vector2 m;
                float k = 1f;
                Vector2 dPrev = i > 0 ? (run[i] - run[i - 1]).normalized : (run[1] - run[0]).normalized;
                Vector2 dNext = i + 1 < n ? (run[i + 1] - run[i]).normalized : dPrev;
                Vector2 n0 = new Vector2(-dPrev.y, dPrev.x), n1 = new Vector2(-dNext.y, dNext.x);
                m = n0 + n1;
                float len = m.magnitude;
                m = len > 1e-4f ? m / len : n1;
                k = 1f / Mathf.Max(0.55f, Vector2.Dot(m, n0));
                float reach = half * k;
                Vertex(run[i] + m * (reach + feather * k), clear);   // left, soft
                Vertex(run[i] + m * reach, color);                    // left
                Vertex(run[i] - m * reach, color);                    // right
                Vertex(run[i] - m * (reach + feather * k), clear);   // right, soft
            }
            for (int i = 0; i + 1 < n; i++)
            {
                int a = baseIndex + i * 4, b = baseIndex + (i + 1) * 4;
                Quad(a, b, b + 1, a + 1);
                Quad(a + 1, b + 1, b + 2, a + 2);
                Quad(a + 2, b + 2, b + 3, a + 3);
            }
        }

        /// <summary>A dashed line (flat dashes <paramref name="dash"/> long with <paramref name="gap"/> between).</summary>
        public void Dashed(IList<Vector2> pts, float width, float dash, float gap, Color color)
        {
            float into = 0f;       // distance into the current dash-or-gap
            bool on = true;
            var current = new List<Vector2>();
            if (pts.Count < 2) return;
            current.Add(pts[0]);
            for (int i = 0; i + 1 < pts.Count; i++)
            {
                Vector2 a = pts[i], b = pts[i + 1];
                float seg = Vector2.Distance(a, b);
                float at = 0f;
                while (seg - at > 1e-3f)
                {
                    float limit = (on ? dash : gap) - into;
                    float step = Mathf.Min(limit, seg - at);
                    at += step;
                    into += step;
                    Vector2 q = Vector2.Lerp(a, b, at / seg);
                    if (on) current.Add(q);
                    if (into >= (on ? dash : gap) - 1e-3f)
                    {
                        if (on && current.Count >= 2) Stroke(current, width, color, false, false);
                        current.Clear();
                        on = !on;
                        into = 0f;
                        if (on) current.Add(q);
                    }
                }
            }
            if (on && current.Count >= 2) Stroke(current, width, color, false, false);
        }

        /// <summary>A ring (an outline of a circle) <paramref name="width"/> thick.</summary>
        public void Ring(Vector2 center, float radius, float width, Color color)
        {
            int n = Mathf.Clamp(Mathf.CeilToInt(radius * 0.6f), 12, 48);
            var pts = new Vector2[n];
            for (int i = 0; i < n; i++)
            {
                float a = i * Mathf.PI * 2f / n;
                pts[i] = center + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * radius;
            }
            Stroke(pts, width, color, true, false);
        }

        /// <summary>A closed outline round <paramref name="poly"/> (for the thin dark line round icons).</summary>
        public void Outline(IList<Vector2> poly, float width, Color color)
        {
            Stroke(poly, width, color, true, false);
        }
    }
}
