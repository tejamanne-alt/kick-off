using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Recolours a kit model (tools/blender kit_*.py) when it loads: every vertex whose part id
    /// (UV channel 2, x) has a tint takes that colour, keeping its brightness relative to the
    /// part's base colour, so the shading and wear baked into the model survive. Identical
    /// recolours of the same mesh are shared, so a street of tinted houses costs one copy each.
    /// </summary>
    public class ModelTint : MonoBehaviour
    {
        [Tooltip("Base colour of parts 1, 2 and 3 (sRGB, as in the kit manifest).")]
        public Color[] baseColors = new Color[3];
        [Tooltip("New colour for parts 1, 2 and 3; alpha 0 leaves a part as it is.")]
        public Color[] tints = new Color[3];

        // Recoloured copies, per source mesh and then per set of tints.
        static readonly Dictionary<Mesh, Dictionary<string, Mesh>> Cache = new Dictionary<Mesh, Dictionary<string, Mesh>>();

        void Awake()
        {
            var filter = GetComponent<MeshFilter>();
            if (filter != null && filter.sharedMesh != null) filter.sharedMesh = Tinted(filter.sharedMesh);
        }

        Mesh Tinted(Mesh source)
        {
            if (!source.isReadable) return source;
            var key = new System.Text.StringBuilder();
            bool any = false;
            for (int p = 0; p < 3; p++)
            {
                if (tints == null || p >= tints.Length || tints[p].a <= 0f) continue;
                any = true;
                key.Append('|').Append(p).Append(ColorUtility.ToHtmlStringRGB(tints[p]));
            }
            if (!any) return source;
            Dictionary<string, Mesh> copies;
            if (!Cache.TryGetValue(source, out copies)) Cache[source] = copies = new Dictionary<string, Mesh>();
            Mesh mesh;
            if (copies.TryGetValue(key.ToString(), out mesh) && mesh != null) return mesh;

            mesh = Instantiate(source);
            mesh.name = source.name + " (tint)";
            var colors = mesh.colors;
            var parts = new List<Vector2>();
            mesh.GetUVs(1, parts);
            if (colors.Length == 0 || parts.Count != colors.Length) return source;
            for (int i = 0; i < colors.Length; i++)
            {
                int p = Mathf.RoundToInt(parts[i].x) - 1;
                if (p < 0 || p >= 3 || p >= tints.Length || tints[p].a <= 0f) continue;
                Color from = p < baseColors.Length ? baseColors[p] : Color.white, to = tints[p], c = colors[i];
                float k = (c.r + c.g + c.b) / Mathf.Max(0.01f, from.r + from.g + from.b);
                colors[i] = new Color(Mathf.Clamp01(to.r * k), Mathf.Clamp01(to.g * k), Mathf.Clamp01(to.b * k), c.a);
            }
            mesh.colors = colors;
            copies[key.ToString()] = mesh;
            return mesh;
        }
    }
}
