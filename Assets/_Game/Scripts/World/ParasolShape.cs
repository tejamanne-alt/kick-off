using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>A beach parasol: a pole and an eight-panel canopy in two alternating colours.</summary>
    public class ParasolShape : ProceduralShape
    {
        public float height = 2.3f;
        public float radius = 1.15f;
        public Color colorA = new Color(0.9f, 0.3f, 0.28f);
        public Color colorB = Color.white;
        [Tooltip("Lean of the pole, degrees about z (planted at an angle in the sand).")]
        public float lean = 6f;

        protected override void Build(MeshBuilder b)
        {
            Quaternion tilt = Quaternion.Euler(0f, 0f, lean);
            Vector3 up = tilt * Vector3.up;
            b.Cylinder(0, up * (height * 0.5f), up, 0.03f, height, new Color(0.85f, 0.85f, 0.85f), Color.white, 0f, Color.white, 8);
            Vector3 apex = up * (height + 0.12f);
            const int panels = 8;
            for (int i = 0; i < panels; i++)
            {
                float a0 = i / (float)panels * Mathf.PI * 2f, a1 = (i + 1) / (float)panels * Mathf.PI * 2f;
                Vector3 p0 = tilt * new Vector3(Mathf.Cos(a0) * radius, height - 0.32f, Mathf.Sin(a0) * radius);
                Vector3 p1 = tilt * new Vector3(Mathf.Cos(a1) * radius, height - 0.32f, Mathf.Sin(a1) * radius);
                Color c = i % 2 == 0 ? colorA : colorB;
                Vector3 outward = (p0 + p1) * 0.5f - up * (height - 0.6f);
                b.Triangle(0, apex, p0, p1, outward, c, Vector2.zero, Vector2.zero, Vector2.zero);
                // The underside, a shade darker.
                b.Triangle(0, apex, p1, p0, -outward, Color.Lerp(c, Color.black, 0.25f), Vector2.zero, Vector2.zero, Vector2.zero);
            }
        }
    }
}
