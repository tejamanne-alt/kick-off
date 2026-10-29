using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>A traffic cone on its square base: orange with two reflective white bands.</summary>
    public class ConeShape : ProceduralShape
    {
        public float height = 0.7f;
        public Color orange = new Color(1f, 0.45f, 0.12f);

        protected override void Build(MeshBuilder b)
        {
            Color white = new Color(0.97f, 0.97f, 0.95f);
            b.Box(0, new Vector3(-0.2f, 0f, -0.2f), new Vector3(0.2f, 0.04f, 0.2f), Color.Lerp(orange, Color.black, 0.25f));
            // Bands bottom to top, each a slice of the same taper.
            float[] cuts = { 0f, 0.36f, 0.5f, 0.64f, 0.76f, 1f };
            Color[] colors = { orange, white, orange, white, orange };
            float r0 = 0.15f, r1 = 0.025f;
            for (int i = 0; i < colors.Length; i++)
            {
                float a = cuts[i], c = cuts[i + 1];
                b.Frustum(0, new Vector3(0f, 0.04f + a * height, 0f), Mathf.Lerp(r0, r1, a), Mathf.Lerp(r0, r1, c), (c - a) * height, colors[i], i == colors.Length - 1);
            }
        }
    }
}
