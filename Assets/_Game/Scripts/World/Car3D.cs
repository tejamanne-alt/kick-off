using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A small hatchback built from a few shapes: a body, a glasshouse with a raked windscreen,
    /// wheels with hubcaps, lights and bumpers. It faces +x with its wheels on y = 0, centred
    /// on its length and width; turn the object to drive it another way.
    /// </summary>
    public class Car3D : ProceduralShape
    {
        public float length = 3.4f;
        public float width = 1.62f;
        public Color paint = new Color(0.9f, 0.35f, 0.3f);

        protected override void Build(MeshBuilder b)
        {
            float l = length * 0.5f, w = width * 0.5f;
            Color dark = new Color(0.12f, 0.12f, 0.14f);
            Color glass = new Color(0.28f, 0.36f, 0.46f);
            Color trim = Color.Lerp(paint, Color.black, 0.35f);
            Color chrome = new Color(0.78f, 0.8f, 0.84f);

            // Lower body with a slightly lower nose, and a skirt line.
            b.Box(0, new Vector3(-l, 0.24f, -w), new Vector3(l, 0.95f, w), paint);
            b.Box(0, new Vector3(-l - 0.06f, 0.22f, -w + 0.05f), new Vector3(-l + 0.05f, 0.5f, w - 0.05f), dark);   // rear bumper
            b.Box(0, new Vector3(l - 0.05f, 0.22f, -w + 0.05f), new Vector3(l + 0.06f, 0.5f, w - 0.05f), dark);     // front bumper
            b.Box(0, new Vector3(-l + 0.02f, 0.24f, -w - 0.01f), new Vector3(l - 0.02f, 0.36f, w + 0.01f), trim, MeshBuilder.Faces.Front | MeshBuilder.Faces.Back);

            // Glasshouse: a raked windscreen and a short sloped tailgate.
            float cb = 0.95f, ct = 1.55f;
            float rearBottom = -l + 0.25f, rearTop = -l + 0.45f, frontTop = 0.55f, frontBottom = 1.05f;
            float wb = w - 0.06f, wt = w - 0.16f;
            Vector3 rb0 = new Vector3(rearBottom, cb, -wb), rb1 = new Vector3(rearBottom, cb, wb);
            Vector3 rt0 = new Vector3(rearTop, ct, -wt), rt1 = new Vector3(rearTop, ct, wt);
            Vector3 ft0 = new Vector3(frontTop, ct, -wt), ft1 = new Vector3(frontTop, ct, wt);
            Vector3 fb0 = new Vector3(frontBottom, cb, -wb), fb1 = new Vector3(frontBottom, cb, wb);
            b.Quad(0, rt0, rt1, ft1, ft0, Vector3.up, paint);                         // roof
            b.Quad(0, fb0, ft0, ft1, fb1, new Vector3(1f, 0.6f, 0f), glass);          // windscreen
            b.Quad(0, rb1, rt1, rt0, rb0, new Vector3(-1f, 0.4f, 0f), glass);         // rear window
            b.Quad(0, rb0, rt0, ft0, fb0, Vector3.back, glass);                       // near side windows
            b.Quad(0, fb1, ft1, rt1, rb1, Vector3.forward, glass);                    // far side windows
            // Pillars between the side windows, in body colour.
            foreach (float z in new[] { -1f, 1f })
            {
                float zb = z * (wb + 0.005f), zt = z * (wt + 0.005f);
                Vector3 outward = new Vector3(0f, 0f, z);
                float mid = (rearBottom + frontBottom) * 0.5f - 0.15f, midTop = (rearTop + frontTop) * 0.5f - 0.15f;
                b.Quad(0, new Vector3(mid - 0.06f, cb, zb), new Vector3(midTop - 0.06f, ct, zt), new Vector3(midTop + 0.06f, ct, zt), new Vector3(mid + 0.06f, cb, zb), outward, paint);
                b.Quad(0, new Vector3(frontBottom - 0.09f, cb, zb), new Vector3(frontTop - 0.04f, ct, zt), new Vector3(frontTop, ct, zt), new Vector3(frontBottom, cb, zb), outward, paint);
                b.Quad(0, new Vector3(rearBottom, cb, zb), new Vector3(rearTop, ct, zt), new Vector3(rearTop + 0.08f, ct, zt), new Vector3(rearBottom + 0.12f, cb, zb), outward, paint);
            }

            // Lights: headlamps at the front, tail lamps at the back.
            foreach (float z in new[] { -1f, 1f })
            {
                b.Box(0, new Vector3(l - 0.02f, 0.66f, z * (w - 0.38f) - 0.15f), new Vector3(l + 0.02f, 0.82f, z * (w - 0.38f) + 0.15f), new Color(1f, 0.96f, 0.82f));
                b.Box(0, new Vector3(-l - 0.02f, 0.66f, z * (w - 0.3f) - 0.12f), new Vector3(-l + 0.02f, 0.84f, z * (w - 0.3f) + 0.12f), new Color(0.85f, 0.15f, 0.15f));
            }
            // Number plates.
            b.Box(0, new Vector3(l + 0.06f, 0.3f, -0.22f), new Vector3(l + 0.08f, 0.44f, 0.22f), Color.white);
            b.Box(0, new Vector3(-l - 0.08f, 0.3f, -0.22f), new Vector3(-l - 0.06f, 0.44f, 0.22f), Color.white);

            // Wheels with hubcaps, tucked into the body.
            float wr = 0.31f;
            foreach (float x in new[] { -l + 0.62f, l - 0.6f })
                foreach (float z in new[] { -1f, 1f })
                    b.Cylinder(0, new Vector3(x, wr, z * (w - 0.1f)), Vector3.forward, wr, 0.24f, dark, dark, wr * 0.55f, chrome, 16);
        }
    }
}
