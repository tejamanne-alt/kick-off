using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Collects vertices for procedural meshes: quads, triangles and boxes with flat
    /// normals (for cel shading), per-vertex colour and UVs, in one or more submeshes.
    /// Quads are given as bottom-left, top-left, top-right, bottom-right as seen from
    /// outside, plus a hint of which way "outside" is, so winding is always correct.
    /// </summary>
    public class MeshBuilder
    {
        public readonly List<Vector3> Vertices = new List<Vector3>();
        public readonly List<Vector3> Normals = new List<Vector3>();
        public readonly List<Vector2> Uvs = new List<Vector2>();
        public readonly List<Color> Colors = new List<Color>();
        public readonly List<int>[] Submeshes;

        public MeshBuilder(int submeshCount = 1)
        {
            Submeshes = new List<int>[Mathf.Max(1, submeshCount)];
            for (int i = 0; i < Submeshes.Length; i++) Submeshes[i] = new List<int>();
        }

        /// <summary>A flat quad. <paramref name="outward"/> is any vector pointing out of the visible side.</summary>
        public void Quad(int submesh, Vector3 bl, Vector3 tl, Vector3 tr, Vector3 br, Vector3 outward, Color color,
            Vector2 uvMin, Vector2 uvMax)
        {
            Vector3 n = Vector3.Cross(tl - bl, tr - bl);
            bool flip = Vector3.Dot(n, outward) < 0f;
            n = n.sqrMagnitude > 1e-12f ? n.normalized : outward.normalized;
            if (flip) n = -n;
            int i = Vertices.Count;
            Vertices.Add(bl); Vertices.Add(tl); Vertices.Add(tr); Vertices.Add(br);
            for (int k = 0; k < 4; k++) { Normals.Add(n); Colors.Add(color); }
            Uvs.Add(new Vector2(uvMin.x, uvMin.y)); Uvs.Add(new Vector2(uvMin.x, uvMax.y));
            Uvs.Add(new Vector2(uvMax.x, uvMax.y)); Uvs.Add(new Vector2(uvMax.x, uvMin.y));
            var tris = Submeshes[Mathf.Clamp(submesh, 0, Submeshes.Length - 1)];
            if (!flip) { tris.Add(i); tris.Add(i + 1); tris.Add(i + 2); tris.Add(i); tris.Add(i + 2); tris.Add(i + 3); }
            else { tris.Add(i); tris.Add(i + 2); tris.Add(i + 1); tris.Add(i); tris.Add(i + 3); tris.Add(i + 2); }
        }

        public void Quad(int submesh, Vector3 bl, Vector3 tl, Vector3 tr, Vector3 br, Vector3 outward, Color color)
        {
            Quad(submesh, bl, tl, tr, br, outward, color, Vector2.zero, Vector2.one);
        }

        public void Triangle(int submesh, Vector3 a, Vector3 b, Vector3 c, Vector3 outward, Color color, Vector2 uvA, Vector2 uvB, Vector2 uvC)
        {
            Vector3 n = Vector3.Cross(b - a, c - a);
            bool flip = Vector3.Dot(n, outward) < 0f;
            n = n.sqrMagnitude > 1e-12f ? n.normalized : outward.normalized;
            if (flip) n = -n;
            int i = Vertices.Count;
            Vertices.Add(a); Vertices.Add(b); Vertices.Add(c);
            for (int k = 0; k < 3; k++) { Normals.Add(n); Colors.Add(color); }
            Uvs.Add(uvA); Uvs.Add(uvB); Uvs.Add(uvC);
            var tris = Submeshes[Mathf.Clamp(submesh, 0, Submeshes.Length - 1)];
            if (!flip) { tris.Add(i); tris.Add(i + 1); tris.Add(i + 2); }
            else { tris.Add(i); tris.Add(i + 2); tris.Add(i + 1); }
        }

        /// <summary>A single vertex with its own normal (for smooth, rounded shapes).</summary>
        public int Vertex(Vector3 p, Vector3 n, Color color, Vector2 uv)
        {
            Vertices.Add(p);
            Normals.Add(n.sqrMagnitude > 1e-12f ? n.normalized : Vector3.up);
            Colors.Add(color);
            Uvs.Add(uv);
            return Vertices.Count - 1;
        }

        /// <summary>A triangle over existing vertices, wound to face along their normals.</summary>
        public void Tri(int submesh, int a, int b, int c)
        {
            Vector3 face = Vector3.Cross(Vertices[b] - Vertices[a], Vertices[c] - Vertices[a]);
            var tris = Submeshes[Mathf.Clamp(submesh, 0, Submeshes.Length - 1)];
            tris.Add(a);
            if (Vector3.Dot(face, Normals[a] + Normals[b] + Normals[c]) >= 0f) { tris.Add(b); tris.Add(c); }
            else { tris.Add(c); tris.Add(b); }
        }

        /// <summary>
        /// A smooth sphere. UVs project the front (and, mirrored, the back) onto the texture
        /// square, so a drawing of a ball maps straight onto the side the camera sees.
        /// </summary>
        public void Sphere(int submesh, Vector3 center, float radius, Color color, int lon = 24, int lat = 16)
        {
            Ellipsoid(submesh, center, Vector3.one * radius, color, lon, lat);
        }

        /// <summary>A smooth ellipsoid with the given radii along x, y and z (UVs as for <see cref="Sphere"/>).</summary>
        public void Ellipsoid(int submesh, Vector3 center, Vector3 radii, Color color, int lon = 16, int lat = 10)
        {
            int start = Vertices.Count;
            for (int i = 0; i <= lat; i++)
            {
                float phi = Mathf.Lerp(-Mathf.PI * 0.5f, Mathf.PI * 0.5f, i / (float)lat);
                for (int j = 0; j <= lon; j++)
                {
                    float theta = j / (float)lon * Mathf.PI * 2f;
                    Vector3 d = new Vector3(Mathf.Cos(phi) * Mathf.Cos(theta), Mathf.Sin(phi), Mathf.Cos(phi) * Mathf.Sin(theta));
                    Vector3 n = new Vector3(d.x / radii.x, d.y / radii.y, d.z / radii.z);
                    Vertex(center + Vector3.Scale(d, radii), n, color, new Vector2(d.x * 0.5f + 0.5f, d.y * 0.5f + 0.5f));
                }
            }
            for (int i = 0; i < lat; i++)
            {
                for (int j = 0; j < lon; j++)
                {
                    int a = start + i * (lon + 1) + j, b = a + 1, c = a + lon + 1, d = c + 1;
                    Tri(submesh, a, b, d);
                    Tri(submesh, a, d, c);
                }
            }
        }

        /// <summary>
        /// A cylinder along <paramref name="axis"/> with smooth sides and flat ends. Each end is
        /// a disc of <paramref name="endColor"/> with an inner disc of <paramref name="innerColor"/>
        /// (a pipe's hollow, a coin's face, a hubcap) out to <paramref name="innerRadius"/>.
        /// </summary>
        public void Cylinder(int submesh, Vector3 center, Vector3 axis, float radius, float length, Color sideColor,
            Color endColor, float innerRadius, Color innerColor, int segments = 20)
        {
            axis = axis.normalized;
            Vector3 u = Vector3.Cross(axis, Mathf.Abs(axis.y) < 0.9f ? Vector3.up : Vector3.right).normalized;
            Vector3 v = Vector3.Cross(axis, u);
            Vector3 half = axis * (length * 0.5f);
            int side = Vertices.Count;
            for (int s = 0; s <= segments; s++)
            {
                float a = s / (float)segments * Mathf.PI * 2f;
                Vector3 n = u * Mathf.Cos(a) + v * Mathf.Sin(a);
                Vertex(center - half + n * radius, n, sideColor, new Vector2(s / (float)segments, 0f));
                Vertex(center + half + n * radius, n, sideColor, new Vector2(s / (float)segments, 1f));
            }
            for (int s = 0; s < segments; s++)
            {
                int a = side + s * 2;
                Tri(submesh, a, a + 1, a + 3);
                Tri(submesh, a, a + 3, a + 2);
            }
            foreach (float end in new[] { -1f, 1f })
            {
                Vector3 c = center + half * end, n = axis * end;
                int hub = Vertex(c + n * 0.001f, n, innerColor, new Vector2(0.5f, 0.5f));
                int inner = Vertices.Count;
                for (int s = 0; s <= segments; s++)
                {
                    float a = s / (float)segments * Mathf.PI * 2f;
                    Vector3 r = u * Mathf.Cos(a) + v * Mathf.Sin(a);
                    Vertex(c + n * 0.001f + r * innerRadius, n, innerColor, new Vector2(0.5f, 0.5f));
                    Vertex(c + r * innerRadius, n, endColor, new Vector2(0.5f, 0.5f));
                    Vertex(c + r * radius, n, endColor, new Vector2(0.5f, 0.5f));
                }
                for (int s = 0; s < segments; s++)
                {
                    int a = inner + s * 3, b = a + 3;
                    Tri(submesh, hub, a, b);
                    Tri(submesh, a + 1, b + 1, b + 2);
                    Tri(submesh, a + 1, b + 2, a + 2);
                }
            }
        }

        [System.Flags]
        public enum Faces { None = 0, Front = 1, Back = 2, Top = 4, Bottom = 8, Left = 16, Right = 32, All = 63, NoBottom = 55 }

        /// <summary>
        /// An axis-aligned box. The front face (toward the camera, -z) maps the whole texture
        /// (for facades); the other faces map it per face as well.
        /// </summary>
        public void Box(int submesh, Vector3 min, Vector3 max, Color color, Faces faces = Faces.NoBottom, int frontSubmesh = -1)
        {
            if (frontSubmesh < 0) frontSubmesh = submesh;
            float x0 = min.x, y0 = min.y, z0 = min.z, x1 = max.x, y1 = max.y, z1 = max.z;
            if ((faces & Faces.Front) != 0)
                Quad(frontSubmesh, new Vector3(x0, y0, z0), new Vector3(x0, y1, z0), new Vector3(x1, y1, z0), new Vector3(x1, y0, z0), Vector3.back, color);
            if ((faces & Faces.Back) != 0)
                Quad(submesh, new Vector3(x1, y0, z1), new Vector3(x1, y1, z1), new Vector3(x0, y1, z1), new Vector3(x0, y0, z1), Vector3.forward, color);
            if ((faces & Faces.Top) != 0)
                Quad(submesh, new Vector3(x0, y1, z0), new Vector3(x0, y1, z1), new Vector3(x1, y1, z1), new Vector3(x1, y1, z0), Vector3.up, color);
            if ((faces & Faces.Bottom) != 0)
                Quad(submesh, new Vector3(x0, y0, z1), new Vector3(x0, y0, z0), new Vector3(x1, y0, z0), new Vector3(x1, y0, z1), Vector3.down, color);
            if ((faces & Faces.Left) != 0)
                Quad(submesh, new Vector3(x0, y0, z1), new Vector3(x0, y1, z1), new Vector3(x0, y1, z0), new Vector3(x0, y0, z0), Vector3.left, color);
            if ((faces & Faces.Right) != 0)
                Quad(submesh, new Vector3(x1, y0, z0), new Vector3(x1, y1, z0), new Vector3(x1, y1, z1), new Vector3(x1, y0, z1), Vector3.right, color);
        }

        public void Fill(Mesh mesh)
        {
            mesh.Clear();
            mesh.indexFormat = Vertices.Count > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
            mesh.SetVertices(Vertices);
            mesh.SetNormals(Normals);
            mesh.SetUVs(0, Uvs);
            mesh.SetColors(Colors);
            mesh.subMeshCount = Submeshes.Length;
            for (int i = 0; i < Submeshes.Length; i++) mesh.SetTriangles(Submeshes[i], i);
            mesh.RecalculateBounds();
        }
    }
}
