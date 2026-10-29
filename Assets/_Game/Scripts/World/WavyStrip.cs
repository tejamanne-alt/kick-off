using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A flat band on the ground with a wavy edge toward the camera (see <see cref="Shoreline"/>):
    /// wet sand where the waves reach, a line of foam along the shore, wave crests out at sea.
    /// Built in world space (keep the object at the origin).
    /// </summary>
    public class WavyStrip : ProceduralShape
    {
        public float fromX, toX = 10f, frontZ, backZ = 1f, y;
        [Tooltip("Shape the ends like a swash (curling back toward the sea) up to this z; 0 = straight ends.")]
        public float seaZ;
        public float phase;
        public Color color = Color.white;

        protected override void Build(MeshBuilder b)
        {
            float x0 = seaZ != 0f ? fromX - 3f : fromX, x1 = seaZ != 0f ? toX + 3f : toX;
            int n = Mathf.Max(2, Mathf.CeilToInt((x1 - x0) / 0.3f));
            float step = (x1 - x0) / n;
            for (int i = 0; i < n; i++)
            {
                float a = x0 + i * step, c = a + step;
                float za = Edge(a), zc = Edge(c);
                if (za >= backZ - 0.01f && zc >= backZ - 0.01f) continue;
                b.Quad(0, new Vector3(a, y, za), new Vector3(a, y, backZ), new Vector3(c, y, backZ), new Vector3(c, y, zc), Vector3.up, color);
            }
        }

        float Edge(float x)
        {
            if (seaZ != 0f) return Mathf.Min(Shoreline.Front(x, fromX, toX, frontZ, seaZ, phase), backZ);
            return frontZ + 0.25f * Mathf.Sin(x * 0.7f + phase) + 0.12f * Mathf.Sin(x * 1.9f + phase * 2f);
        }
    }
}
