using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A summer cumulus cloud in the anime manner: a flat-bottomed bank of rounded puffs with towers
    /// of smaller puffs piled on top, painted (in its vertex colours) bright white where the sun
    /// catches the tops and a clear cyan-blue on the shaded lower parts, with a crisp edge between,
    /// whatever side the sun lights it from. Shape comes from the seed; origin at the middle of the
    /// cloud's base.
    /// </summary>
    public class CloudShape : ProceduralShape
    {
        public int seed = 1;
        public float width = 80f;
        public float height = 36f;

        protected override void Build(MeshBuilder b)
        {
            var rng = new System.Random(seed);
            System.Func<float, float, float> range = (lo, hi) => lo + (float)rng.NextDouble() * (hi - lo);
            Color white = Color.white, belly = new Color(0.92f, 0.94f, 1f);
            float half = width * 0.5f;

            // The base: a row of wide puffs, biggest in the middle.
            int n = Mathf.Clamp(Mathf.RoundToInt(width / (height * 0.45f)), 5, 11);
            for (int i = 0; i < n; i++)
            {
                float t = n == 1 ? 0.5f : i / (float)(n - 1);
                float x = Mathf.Lerp(-half, half, t) + range(-2f, 2f);
                float mid = 1f - Mathf.Abs(t - 0.5f) * 1.2f;
                float r = height * range(0.22f, 0.3f) * (0.65f + 0.5f * mid);
                b.Ellipsoid(0, new Vector3(x, r * 0.5f, range(-r, r) * 0.3f), new Vector3(r * 1.25f, r, r), belly, 14, 9);
            }
            // Towers piled up over the middle, and a few small puffs on the shoulders.
            int towers = 2 + rng.Next(3);
            for (int k = 0; k < towers; k++)
            {
                float cx = range(-half * 0.45f, half * 0.45f);
                float y = height * range(0.3f, 0.45f);
                float r = height * range(0.2f, 0.28f);
                int stack = 2 + rng.Next(3);
                for (int j = 0; j < stack; j++)
                {
                    b.Ellipsoid(0, new Vector3(cx + range(-r, r) * 0.4f, y, range(-r, r) * 0.4f), new Vector3(r * 1.1f, r, r), white, 14, 9);
                    y += r * range(0.7f, 0.95f);
                    r *= range(0.72f, 0.85f);
                    if (y + r > height) break;
                }
            }
            for (int k = 0; k < 5; k++)
            {
                float r = height * range(0.1f, 0.16f);
                b.Ellipsoid(0, new Vector3(range(-half * 0.8f, half * 0.8f), height * range(0.2f, 0.4f), range(-r, r)), new Vector3(r * 1.2f, r, r), white, 12, 8);
            }
            // Flatten the underside, like a real cumulus sitting on a level of air.
            for (int i = 0; i < b.Vertices.Count; i++)
            {
                if (b.Vertices[i].y >= 0f) continue;
                var v = b.Vertices[i];
                b.Vertices[i] = new Vector3(v.x, 0f, v.z);
                b.Normals[i] = Vector3.Lerp(b.Normals[i], Vector3.down, 0.7f).normalized;
            }
            // Paint the light and shade: white on the upper, sunward puffs, cyan-blue lower down and
            // round the far side, with a narrow soft edge between (the painted anime look).
            Color shade = new Color(0.6f, 0.76f, 0.9f), deep = new Color(0.52f, 0.68f, 0.86f);
            for (int i = 0; i < b.Vertices.Count; i++)
            {
                Vector3 v = b.Vertices[i], normal = b.Normals[i];
                float light = v.y / Mathf.Max(1f, height) * 0.9f + normal.y * 0.35f + normal.x * 0.15f - normal.z * 0.1f + 0.05f;
                float k = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.3f, 0.4f, light));
                Color low = Color.Lerp(deep, shade, Mathf.Clamp01(v.y / Mathf.Max(1f, height) * 3f));
                b.Colors[i] = Color.Lerp(low, Color.white, k);
            }
        }
    }
}
