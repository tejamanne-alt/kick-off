using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Rain puddles (or a patch of soft, loose sand) lying on the ground over an area: one big,
    /// irregular puddle with a soft wet edge and a band of reflected sky along its far side, and a
    /// few smaller ones scattered round it. Flat, a hair above the ground. Built in world space
    /// (keep the object at the origin). The water is the deep slate of the street it mirrors, not
    /// a pale blue: with a dark ring round a pale fill a puddle read as a sticker on the paving
    /// (docs/LEARNINGS.md E15).
    /// </summary>
    public class PuddleShape : ProceduralShape
    {
        public float fromX, toX = 4f, zFrom = -1.2f, zTo = 1.2f, groundY;
        public int seed = 1;
        public Color water = new Color(0.36f, 0.43f, 0.51f);
        public Color sky = new Color(0.64f, 0.74f, 0.86f);
        [Tooltip("The wet edge: a little darker than dry paving, so it reads as damp, not as an outline.")]
        public Color rim = new Color(0.62f, 0.62f, 0.63f);
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
            Fan(b, c, rx * 1.06f + 0.05f, rz * 1.08f + 0.04f, outline, groundY + 0.004f, rim);   // wet edge
            Fan(b, c, rx, rz, outline, groundY + 0.008f, water);
            if (reflective)
            {
                // The sky caught along the far side (seen low across the water, it is the sky beyond that shows), and a
                // fainter glint nearer the middle.
                Vector2 hc = c + new Vector2(-rx * 0.1f, rz * 0.5f);
                Fan(b, hc, rx * 0.72f, rz * 0.26f * size, outline, groundY + 0.011f, sky);
                Fan(b, c + new Vector2(rx * 0.2f, rz * 0.05f), rx * 0.3f, rz * 0.1f * size, outline, groundY + 0.012f, Color.Lerp(water, sky, 0.5f));
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
