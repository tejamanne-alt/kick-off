using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Recolours an imported character model for the shop's outfits. The model marks each
    /// vertex's part in its second UV channel (x: 0 skin and fixed parts, 1 shirt, 2 shorts or
    /// trousers); its vertex colours are the default outfit, so shading baked into them (hems,
    /// folds) carries over to the new colours. Works on a copy of the mesh.
    /// </summary>
    [RequireComponent(typeof(SkinnedMeshRenderer))]
    public class ModelOutfit : MonoBehaviour, IOutfit
    {
        [Tooltip("The shirt and shorts colours the model was made with.")]
        public Color defaultShirt = new Color(0.97f, 0.97f, 0.99f);
        public Color defaultLegwear = new Color(0.2f, 0.22f, 0.4f);

        Mesh mesh;
        Color[] original;
        Vector2[] parts;

        public void SetOutfit(Color shirt, Color legwear)
        {
            var smr = GetComponent<SkinnedMeshRenderer>();
            if (smr.sharedMesh == null) return;
            if (mesh == null)
            {
                if (!smr.sharedMesh.isReadable) return;
                mesh = Instantiate(smr.sharedMesh);
                mesh.name = smr.sharedMesh.name + " (outfit)";
                original = mesh.colors;
                var uv2 = new System.Collections.Generic.List<Vector2>();
                mesh.GetUVs(1, uv2);
                parts = uv2.ToArray();
                smr.sharedMesh = mesh;
            }
            if (original == null || parts == null || parts.Length != original.Length) return;
            var colors = new Color[original.Length];
            for (int i = 0; i < colors.Length; i++)
            {
                int part = Mathf.RoundToInt(parts[i].x);
                Color c = original[i];
                if (part == 1) c = Recolor(c, defaultShirt, shirt);
                else if (part == 2) c = Recolor(c, defaultLegwear, legwear);
                colors[i] = c;
            }
            mesh.colors = colors;
        }

        /// <summary>Keeps how much lighter or darker this vertex is than the default colour.</summary>
        static Color Recolor(Color c, Color from, Color to)
        {
            float k = (c.r + c.g + c.b) / Mathf.Max(0.01f, from.r + from.g + from.b);
            return new Color(Mathf.Clamp01(to.r * k), Mathf.Clamp01(to.g * k), Mathf.Clamp01(to.b * k), c.a);
        }

        void OnDestroy()
        {
            if (mesh != null) Destroy(mesh);
        }
    }
}
