using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A surface made of free-form quads and triangles (sand dunes, channel banks): each face is
    /// given by its corners in this object's space, faces up or toward the camera, and is shaded
    /// flat. Textures come from the material's world-space projection, so no UVs are needed.
    /// </summary>
    public class PatchShape : ProceduralShape
    {
        [System.Serializable]
        public struct Patch
        {
            public Vector3 a, b, c, d;
            [Tooltip("True for a triangle (a, b, c); d is ignored.")]
            public bool triangle;
            public Color color;
        }

        public List<Patch> patches = new List<Patch>();

        public void AddQuad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Color color)
        {
            patches.Add(new Patch { a = a, b = b, c = c, d = d, color = color });
        }

        public void AddTriangle(Vector3 a, Vector3 b, Vector3 c, Color color)
        {
            patches.Add(new Patch { a = a, b = b, c = c, triangle = true, color = color });
        }

        protected override void Build(MeshBuilder b)
        {
            foreach (var p in patches)
            {
                Vector3 n = Vector3.Cross(p.b - p.a, p.c - p.a);
                if (n.sqrMagnitude < 1e-10f) continue;
                n.Normalize();
                // Every face here looks up or toward the camera (-z).
                if (n.y < -0.01f || (Mathf.Abs(n.y) <= 0.01f && n.z > 0f)) n = -n;
                if (p.triangle) b.Triangle(0, p.a, p.b, p.c, n, p.color, Vector2.zero, Vector2.zero, Vector2.zero);
                else b.Quad(0, p.a, p.b, p.c, p.d, n, p.color);
            }
        }
    }
}
