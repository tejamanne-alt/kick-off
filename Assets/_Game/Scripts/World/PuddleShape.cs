using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Rain puddles (or a patch of soft, loose sand) lying on the ground over an area: one big,
    /// irregular puddle with a darker wet rim and a pale streak of reflected sky, and a few
    /// smaller ones scattered round it. Flat, a hair above the ground. Built in world space
    /// (keep the object at the origin).
    /// </summary>
    public class PuddleShape : ProceduralShape
    {
        public float fromX, toX = 4f, zFrom = -1.2f, zTo = 1.2f, groundY;
        public int seed = 1;
        public Color water = new Color(0.56f, 0.68f, 0.82f);
        public Color sky = new Color(0.8f, 0.88f, 0.96f);
        public Color rim = new Color(0.5f, 0.5f, 0.53f);
        [Tooltip("Off: no sky reflection (for soft sand).")]
        public bool reflective = true;

        protected override void Build(MeshBuilder b)
        {
            var rng = new System.Random(seed);
            float cx = (fromX + toX) * 0.5f, cz = (zFrom + zTo) * 0.5f;
            float rx = (toX - fromX) * 0.5f, rz = (zTo - zFrom) * 0.5f;
            Blob(b, rng, new Vector2(cx, cz), rx * 0.86f, rz * 0.72f, 1f);
            int extra = 2 + rng.Next(3);
            for (int i = 0; i < extra; i++)
            {
                float side = i % 2 == 0 ? -1f : 1f;
                float x = cx + side * rx * (0.75f + (float)rng.NextDouble() * 0.35f);
                float z = cz + ((float)rng.NextDouble() * 2f - 1f) * rz * 0.6f;
                float r = 0.2f + (float)rng.NextDouble() * 0.35f;
                Blob(b, rng, new Vector2(x, z), r * 1.3f, r, 0.6f);
            }
        }

        void Blob(MeshBuilder b, System.Random rng, Vector2 c, float rx, float rz, float size)
        {
            const int n = 44;
            float p1 = (float)rng.NextDouble() * 6.28f, p2 = (float)rng.NextDouble() * 6.28f, p3 = (float)rng.NextDouble() * 6.28f;
            var outline = new float[n];
            for (int i = 0; i < n; i++)
            {
                float a = i / (float)n * Mathf.PI * 2f;
                outline[i] = 1f + 0.13f * Mathf.Sin(3f * a + p1) + 0.08f * Mathf.Sin(5f * a + p2) + 0.05f * Mathf.Sin(9f * a + p3);
            }
            Fan(b, c, rx * 1.1f + 0.08f, rz * 1.12f + 0.06f, outline, groundY + 0.004f, rim);   // wet edge
            Fan(b, c, rx, rz, outline, groundY + 0.008f, water);
            if (reflective)
            {
                // Sky caught in the far half of the puddle.
                Vector2 hc = c + new Vector2(-rx * 0.15f, rz * 0.3f);
                Fan(b, hc, rx * 0.55f, rz * 0.32f * size, outline, groundY + 0.011f, sky);
            }
        }

        static void Fan(MeshBuilder b, Vector2 c, float rx, float rz, float[] outline, float y, Color color)
        {
            int hub = b.Vertex(new Vector3(c.x, y, c.y), Vector3.up, color, new Vector2(0.5f, 0.5f));
            int start = b.Vertices.Count;
            int n = outline.Length;
            for (int i = 0; i < n; i++)
            {
                float a = i / (float)n * Mathf.PI * 2f;
                b.Vertex(new Vector3(c.x + Mathf.Cos(a) * rx * outline[i], y, c.y + Mathf.Sin(a) * rz * outline[i]), Vector3.up, color, new Vector2(0.5f, 0.5f));
            }
            for (int i = 0; i < n; i++) b.Tri(0, hub, start + i, start + (i + 1) % n);
        }
    }
}
