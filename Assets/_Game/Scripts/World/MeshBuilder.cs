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
