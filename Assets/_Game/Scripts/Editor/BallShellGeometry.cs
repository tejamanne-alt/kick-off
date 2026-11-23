using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The geometry of the ball shells (LevelBuildKit.BallShells, docs/LEARNINGS.md E18), pure so the tests can run it: where a
    /// model's surfaces cross the ball's plane (a slab |z| &lt;= <see cref="Slab"/> round z 0), as cells of a grid in the street's x
    /// and y, and those cells merged into as few boxes as possible.
    /// </summary>
    public static class BallShellGeometry
    {
        /// <summary>Half the depth of the ball's plane: the ball's radius (0.115) and a margin.</summary>
        public const float Slab = 0.17f;
        /// <summary>The grid's cell, in metres.</summary>
        public const float Cell = 0.05f;

        /// <summary>A box of cells, from (x0, y0) to (x1, y1) inclusive.</summary>
        public struct CellBox
        {
            public int x0, y0, x1, y1;
            public CellBox(int x0, int y0, int x1, int y1) { this.x0 = x0; this.y0 = y0; this.x1 = x1; this.y1 = y1; }
            public override string ToString() { return "(" + x0 + "," + y0 + ")-(" + x1 + "," + y1 + ")"; }
        }

        /// <summary>
        /// The part of a triangle (world positions) inside the slab, as a polygon (0 to 5 corners): the triangle clipped by the
        /// planes z = -<see cref="Slab"/> and z = +<see cref="Slab"/>.
        /// </summary>
        public static List<Vector3> ClipToSlab(Vector3 a, Vector3 b, Vector3 c, float slab = Slab)
        {
            var poly = new List<Vector3> { a, b, c };
            poly = ClipAgainst(poly, slab, true);
            if (poly.Count == 0) return poly;
            return ClipAgainst(poly, -slab, false);
        }

        /// <summary>One Sutherland-Hodgman pass: keep the side z &lt;= plane (below) or z &gt;= plane.</summary>
        static List<Vector3> ClipAgainst(List<Vector3> poly, float plane, bool below)
        {
            var output = new List<Vector3>();
            for (int i = 0; i < poly.Count; i++)
            {
                Vector3 p = poly[i], q = poly[(i + 1) % poly.Count];
                bool pIn = below ? p.z <= plane : p.z >= plane;
                bool qIn = below ? q.z <= plane : q.z >= plane;
                if (pIn) output.Add(p);
                if (pIn != qIn)
                {
                    float t = (plane - p.z) / (q.z - p.z);
                    output.Add(Vector3.Lerp(p, q, t));
                }
            }
            return output;
        }

        /// <summary>
        /// Mark the cells a polygon in the grid's plane covers: each cell whose middle is inside it, and every cell its edges pass
        /// through (a surface seen edge-on, like a box's top, is a line in the plane: it has no inside, only its edge).
        /// </summary>
        public static void Rasterize(List<Vector2> poly, HashSet<Vector2Int> cells, float cell = Cell)
        {
            if (poly.Count == 0) return;
            for (int i = 0; i < poly.Count; i++)
            {
                Vector2 p = poly[i], q = poly[(i + 1) % poly.Count];
                float length = Vector2.Distance(p, q);
                int steps = Mathf.Max(1, Mathf.CeilToInt(length / (cell * 0.5f)));
                for (int s = 0; s <= steps; s++)
                {
                    Vector2 m = Vector2.Lerp(p, q, s / (float)steps);
                    cells.Add(new Vector2Int(Mathf.FloorToInt(m.x / cell), Mathf.FloorToInt(m.y / cell)));
                }
            }
            if (poly.Count < 3) return;
            float minX = float.MaxValue, minY = float.MaxValue, maxX = float.MinValue, maxY = float.MinValue;
            foreach (var p in poly)
            {
                minX = Mathf.Min(minX, p.x); maxX = Mathf.Max(maxX, p.x);
                minY = Mathf.Min(minY, p.y); maxY = Mathf.Max(maxY, p.y);
            }
            for (int iy = Mathf.FloorToInt(minY / cell); iy <= Mathf.FloorToInt(maxY / cell); iy++)
                for (int ix = Mathf.FloorToInt(minX / cell); ix <= Mathf.FloorToInt(maxX / cell); ix++)
                    if (Inside(poly, new Vector2((ix + 0.5f) * cell, (iy + 0.5f) * cell)))
                        cells.Add(new Vector2Int(ix, iy));
        }

        static bool Inside(List<Vector2> poly, Vector2 p)
        {
            bool inside = false;
            for (int i = 0, j = poly.Count - 1; i < poly.Count; j = i++)
            {
                Vector2 a = poly[i], b = poly[j];
                if ((a.y > p.y) != (b.y > p.y) && p.x < (b.x - a.x) * (p.y - a.y) / (b.y - a.y) + a.x) inside = !inside;
            }
            return inside;
        }

        /// <summary>The cells as boxes: runs along each row, then runs of the same width stacked up the rows.</summary>
        public static List<CellBox> Merge(IEnumerable<Vector2Int> cells)
        {
            var rows = new SortedDictionary<int, List<int>>();
            foreach (var c in cells)
            {
                List<int> row;
                if (!rows.TryGetValue(c.y, out row)) rows[c.y] = row = new List<int>();
                row.Add(c.x);
            }
            var open = new Dictionary<long, CellBox>();      // the boxes still growing upward, by their run (x0, x1)
            var done = new List<CellBox>();
            int lastY = int.MinValue;
            foreach (var kv in rows)
            {
                int y = kv.Key;
                var xs = kv.Value;
                xs.Sort();
                var runs = new List<Vector2Int>();
                for (int i = 0; i < xs.Count; i++)
                {
                    if (i > 0 && xs[i] == xs[i - 1]) continue;
                    if (runs.Count > 0 && xs[i] == runs[runs.Count - 1].y + 1) runs[runs.Count - 1] = new Vector2Int(runs[runs.Count - 1].x, xs[i]);
                    else runs.Add(new Vector2Int(xs[i], xs[i]));
                }
                var next = new Dictionary<long, CellBox>();
                foreach (var r in runs)
                {
                    long key = ((long)r.x << 32) ^ (uint)r.y;
                    CellBox box;
                    if (y == lastY + 1 && open.TryGetValue(key, out box)) { box.y1 = y; open.Remove(key); }
                    else box = new CellBox(r.x, y, r.y, y);
                    next[key] = box;
                }
                done.AddRange(open.Values);
                open = next;
                lastY = y;
            }
            done.AddRange(open.Values);
            return done;
        }
    }
}
