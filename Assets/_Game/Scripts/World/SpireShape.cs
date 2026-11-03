using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A pointed roof on a tower: a pyramid of <see cref="sides"/> faces (four for a church spire) standing on its base,
    /// <see cref="radius"/> from the middle to a corner. Turn the object 45 degrees about y for a square spire whose faces
    /// look at the street.
    /// </summary>
    public class SpireShape : ProceduralShape
    {
        public float radius = 2f;
        public float height = 5f;
        [Range(3, 16)] public int sides = 4;
        public Color color = new Color(0.32f, 0.35f, 0.42f);

        protected override void Build(MeshBuilder b)
        {
            int n = Mathf.Clamp(sides, 3, 16);
            Vector3 apex = Vector3.up * height;
            for (int i = 0; i < n; i++)
            {
                float a0 = i / (float)n * Mathf.PI * 2f, a1 = (i + 1) / (float)n * Mathf.PI * 2f;
                Vector3 p0 = new Vector3(Mathf.Cos(a0), 0f, Mathf.Sin(a0)) * radius;
                Vector3 p1 = new Vector3(Mathf.Cos(a1), 0f, Mathf.Sin(a1)) * radius;
                // Each face flat, so the toon light breaks crisply at the ridges.
                Vector3 outward = Vector3.Cross(p0 - apex, p1 - apex).normalized;
                if (Vector3.Dot(outward, (p0 + p1) * 0.5f) < 0f) outward = -outward;
                b.Triangle(0, p1, p0, apex, outward, color, new Vector2(1f, 0f), new Vector2(0f, 0f), new Vector2(0.5f, 1f));
            }
        }
    }
}
