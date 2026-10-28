using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Builds smooth, skinned meshes from tubes (limbs, a torso) and ellipsoids (heads,
    /// hands, shoes), with smooth normals for cel shading and outlines, per-vertex colour,
    /// and up to two bone weights per vertex. A tube whose rings blend from one bone to
    /// the next bends like skin at a joint instead of showing a seam.
    /// </summary>
    public class SkinBuilder
    {
        /// <summary>One cross-section of a tube.</summary>
        public struct Ring
        {
            public Vector3 center;
            /// <summary>Cross-section axes: <c>x</c> carries radius rx, <c>z</c> radius rz.</summary>
            public Vector3 x, z;
            public float rx, rz;
            public Color color;
            /// <summary>Bone <c>b0</c> with weight 1 - w1, bone <c>b1</c> with weight w1.</summary>
            public int b0, b1;
            public float w1;
        }

        public readonly List<Vector3> Vertices = new List<Vector3>();
        public readonly List<Vector3> Normals = new List<Vector3>();
        public readonly List<Color> Colors = new List<Color>();
        public readonly List<BoneWeight> Weights = new List<BoneWeight>();
        public readonly List<int> Triangles = new List<int>();

        int Vertex(Vector3 p, Vector3 n, Color c, int b0, int b1, float w1)
        {
            Vertices.Add(p);
            Normals.Add(n.sqrMagnitude > 1e-10f ? n.normalized : Vector3.up);
            Colors.Add(c);
            w1 = Mathf.Clamp01(w1);
            var w = new BoneWeight();
            if (b0 == b1 || w1 <= 0f) { w.boneIndex0 = b0; w.weight0 = 1f; }
            else if (w1 >= 1f) { w.boneIndex0 = b1; w.weight0 = 1f; }
            else if (w1 <= 0.5f) { w.boneIndex0 = b0; w.weight0 = 1f - w1; w.boneIndex1 = b1; w.weight1 = w1; }
            else { w.boneIndex0 = b1; w.weight0 = w1; w.boneIndex1 = b0; w.weight1 = 1f - w1; }
            Weights.Add(w);
            return Vertices.Count - 1;
        }

        /// <summary>A triangle wound so its face points along the vertices' normals.</summary>
        void Tri(int a, int b, int c)
        {
            Vector3 face = Vector3.Cross(Vertices[b] - Vertices[a], Vertices[c] - Vertices[a]);
            Vector3 n = Normals[a] + Normals[b] + Normals[c];
            if (Vector3.Dot(face, n) >= 0f) { Triangles.Add(a); Triangles.Add(b); Triangles.Add(c); }
            else { Triangles.Add(a); Triangles.Add(c); Triangles.Add(b); }
        }

        /// <summary>
        /// A tube through the rings (elliptic cross-sections), optionally closed with a small
        /// dome at either end. Two rings at the same place with different colours make a crisp
        /// colour edge (a sleeve hem, a sock top).
        /// </summary>
        public void Tube(IList<Ring> rings, int segments, bool capStart = true, bool capEnd = true)
        {
            if (rings.Count < 2) return;
            int first = Vertices.Count;
            for (int r = 0; r < rings.Count; r++)
            {
                var ring = rings[r];
                for (int s = 0; s < segments; s++)
                {
                    float a = s / (float)segments * Mathf.PI * 2f;
                    float ca = Mathf.Cos(a), sa = Mathf.Sin(a);
                    Vector3 p = ring.center + ring.x * (ca * ring.rx) + ring.z * (sa * ring.rz);
                    Vector3 n = ring.x * (ca / Mathf.Max(ring.rx, 1e-4f)) + ring.z * (sa / Mathf.Max(ring.rz, 1e-4f));
                    Vertex(p, n, ring.color, ring.b0, ring.b1, ring.w1);
                }
            }
            for (int r = 0; r < rings.Count - 1; r++)
            {
                for (int s = 0; s < segments; s++)
                {
                    int a = first + r * segments + s;
                    int b = first + r * segments + (s + 1) % segments;
                    int c = a + segments, d = b + segments;
                    Tri(a, b, d);
                    Tri(a, d, c);
                }
            }
            if (capStart) Cap(rings[0], rings[1].center, first, segments);
            if (capEnd) Cap(rings[rings.Count - 1], rings[rings.Count - 2].center, first + (rings.Count - 1) * segments, segments);
        }

        void Cap(Ring ring, Vector3 inward, int start, int segments)
        {
            Vector3 outDir = ring.center - inward;
            outDir = outDir.sqrMagnitude > 1e-10f ? outDir.normalized : Vector3.up;
            float bulge = Mathf.Min(ring.rx, ring.rz) * 0.55f;
            int tip = Vertex(ring.center + outDir * bulge, outDir, ring.color, ring.b0, ring.b1, ring.w1);
            for (int s = 0; s < segments; s++)
            {
                int a = start + s, b = start + (s + 1) % segments;
                // The rim's normals point sideways; bias the winding test toward the cap direction.
                Vector3 face = Vector3.Cross(Vertices[b] - Vertices[a], Vertices[tip] - Vertices[a]);
                if (Vector3.Dot(face, outDir) >= 0f) { Triangles.Add(a); Triangles.Add(b); Triangles.Add(tip); }
                else { Triangles.Add(a); Triangles.Add(tip); Triangles.Add(b); }
            }
        }

        public delegate Color ColorFn(Vector3 direction);
        public delegate bool KeepFn(Vector3 direction);

        /// <summary>
        /// A (super)ellipsoid with axes <paramref name="ax"/>, <paramref name="ay"/>, <paramref name="az"/>
        /// and radii <paramref name="radii"/>. <paramref name="roundness"/> 1 is an ellipsoid, lower
        /// is boxier. <paramref name="color"/> and <paramref name="keep"/> get the unit direction in
        /// the ellipsoid's own frame (x, y, z along ax, ay, az), for shine bands and partial shells
        /// such as hair. Vertices below <paramref name="floorY"/> (world y in the mesh's space) are
        /// flattened onto it, for soles.
        /// </summary>
        public void Ellipsoid(Vector3 center, Vector3 ax, Vector3 ay, Vector3 az, Vector3 radii, int bone,
            ColorFn color, KeepFn keep = null, int lon = 18, int lat = 12, float roundness = 1f, float floorY = float.NegativeInfinity)
        {
            int start = Vertices.Count;
            var kept = new bool[(lat + 1) * (lon + 1)];
            for (int i = 0; i <= lat; i++)
            {
                float phi = Mathf.Lerp(-Mathf.PI * 0.5f, Mathf.PI * 0.5f, i / (float)lat);
                for (int j = 0; j <= lon; j++)
                {
                    float theta = j / (float)lon * Mathf.PI * 2f;
                    float cp = Mathf.Cos(phi), sp = Mathf.Sin(phi), ct = Mathf.Cos(theta), st = Mathf.Sin(theta);
                    Vector3 dir = new Vector3(cp * ct, sp, cp * st);
                    Vector3 local = new Vector3(
                        SPow(cp, roundness) * SPow(ct, roundness),
                        SPow(sp, roundness),
                        SPow(cp, roundness) * SPow(st, roundness));
                    Vector3 nLocal = new Vector3(
                        SPow(cp, 2f - roundness) * SPow(ct, 2f - roundness) / radii.x,
                        SPow(sp, 2f - roundness) / radii.y,
                        SPow(cp, 2f - roundness) * SPow(st, 2f - roundness) / radii.z);
                    Vector3 p = center + ax * (local.x * radii.x) + ay * (local.y * radii.y) + az * (local.z * radii.z);
                    Vector3 n = ax * nLocal.x + ay * nLocal.y + az * nLocal.z;
                    if (p.y < floorY)
                    {
                        p.y = floorY;
                        n = Vector3.Lerp(n.normalized, Vector3.down, 0.8f);
                    }
                    kept[i * (lon + 1) + j] = keep == null || keep(dir);
                    Vertex(p, n, color != null ? color(dir) : Color.white, bone, bone, 0f);
                }
            }
            for (int i = 0; i < lat; i++)
            {
                for (int j = 0; j < lon; j++)
                {
                    int a = i * (lon + 1) + j, b = a + 1, c = a + lon + 1, d = c + 1;
                    if (kept[a] && kept[b] && kept[d]) Tri(start + a, start + b, start + d);
                    if (kept[a] && kept[d] && kept[c]) Tri(start + a, start + d, start + c);
                }
            }
        }

        public void Ellipsoid(Vector3 center, Vector3 radii, int bone, Color color, int lon = 14, int lat = 10)
        {
            Ellipsoid(center, Vector3.right, Vector3.up, Vector3.forward, radii, bone, d => color, null, lon, lat);
        }

        static float SPow(float v, float e)
        {
            return Mathf.Sign(v) * Mathf.Pow(Mathf.Abs(v), e);
        }

        /// <summary>Moves every vertex and normal by <paramref name="m"/> (e.g. from rig space to the mesh's space).</summary>
        public void Transform(Matrix4x4 m)
        {
            for (int i = 0; i < Vertices.Count; i++)
            {
                Vertices[i] = m.MultiplyPoint3x4(Vertices[i]);
                Normals[i] = m.MultiplyVector(Normals[i]).normalized;
            }
        }

        public void Fill(Mesh mesh, Matrix4x4[] bindposes)
        {
            mesh.Clear();
            mesh.indexFormat = Vertices.Count > 65000 ? UnityEngine.Rendering.IndexFormat.UInt32 : UnityEngine.Rendering.IndexFormat.UInt16;
            mesh.SetVertices(Vertices);
            mesh.SetNormals(Normals);
            mesh.SetColors(Colors);
            mesh.SetTriangles(Triangles, 0);
            mesh.boneWeights = Weights.ToArray();
            mesh.bindposes = bindposes;
            mesh.RecalculateBounds();
        }
    }
}
