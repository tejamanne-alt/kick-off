using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Repaints a car made in Blender (tools/blender/car.py). The model marks its body paint
    /// with part id 1 in its second UV channel and paints it in <see cref="basePaint"/>; this
    /// swaps that for <see cref="paint"/>, keeping each vertex's brightness relative to the base
    /// so baked shading survives. Grime and panel lines live in the texture, so they stay too.
    /// Works on a copy of the mesh.
    /// </summary>
    [RequireComponent(typeof(MeshFilter))]
    public class CarPaint : MonoBehaviour
    {
        public Color basePaint = new Color(0.8f, 0.47f, 0.35f);
        public Color paint = new Color(0.8f, 0.47f, 0.35f);

        Mesh mesh;

        void Awake()
        {
            var filter = GetComponent<MeshFilter>();
            var source = filter.sharedMesh;
            if (source == null || !source.isReadable) return;
            if (Approximately(paint, basePaint)) return;
            mesh = Instantiate(source);
            mesh.name = source.name + " (paint)";
            var colors = mesh.colors;
            var parts = new System.Collections.Generic.List<Vector2>();
            mesh.GetUVs(1, parts);
            if (colors.Length == 0 || parts.Count != colors.Length) { Destroy(mesh); mesh = null; return; }
            float baseSum = Mathf.Max(0.01f, basePaint.r + basePaint.g + basePaint.b);
            for (int i = 0; i < colors.Length; i++)
            {
                if (parts[i].x < 0.5f) continue;
                Color c = colors[i];
                float k = (c.r + c.g + c.b) / baseSum;
                colors[i] = new Color(Mathf.Clamp01(paint.r * k), Mathf.Clamp01(paint.g * k), Mathf.Clamp01(paint.b * k), c.a);
            }
            mesh.colors = colors;
            filter.sharedMesh = mesh;
        }

        static bool Approximately(Color a, Color b)
        {
            return Mathf.Abs(a.r - b.r) + Mathf.Abs(a.g - b.g) + Mathf.Abs(a.b - b.b) < 0.01f;
        }

        void OnDestroy()
        {
            if (mesh != null) Destroy(mesh);
        }
    }
}
