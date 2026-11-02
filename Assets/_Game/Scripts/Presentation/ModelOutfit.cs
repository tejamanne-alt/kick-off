using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Recolours an imported character model for the shop's outfits. The model marks each
    /// vertex's part in its second UV channel (x: 0 skin and fixed parts, 1 shirt, 2 shorts or
    /// trousers, 3 hair, 4 the tie); its vertex colours are the default outfit, so shading baked into
    /// them (hems, the tie's stripes, the hair's shine) carries over to the new colours. Works on a
    /// copy of the mesh. Pedestrians are dressed when they load (dressOnStart).
    /// </summary>
    [RequireComponent(typeof(SkinnedMeshRenderer))]
    public class ModelOutfit : MonoBehaviour, IOutfit, IAccentOutfit
    {
        [Tooltip("The shirt and shorts colours the model was made with.")]
        public Color defaultShirt = new Color(0.97f, 0.97f, 0.99f);
        public Color defaultLegwear = new Color(0.2f, 0.22f, 0.4f);
        public Color defaultHair = new Color(0.13f, 0.1f, 0.12f);
        [Tooltip("The tie's colour (the school uniform's red); models without a tie have no part 4.")]
        public Color defaultAccent = new Color(0.78f, 0.2f, 0.24f);

        [Header("Dress on start (pedestrians)")]
        public bool dressOnStart;
        public Color shirt = Color.white;
        public Color legwear = Color.gray;
        public Color hair = new Color(0.13f, 0.1f, 0.12f);

        Color currentHair;
        Color currentShirt, currentLegwear, currentAccent;
        bool dressed, accented;

        Mesh mesh;
        Color[] original;
        Vector2[] parts;
        // The accent (the tie) can be taken off: its vertices all collapse to one point on the chest.
        Vector3[] restVertices;
        int[] accentVertices;
        Vector3 accentAnchor;
        bool accentHidden, wantAccentHidden;

        void Start()
        {
            if (!dressOnStart) return;
            currentHair = hair;
            SetOutfit(shirt, legwear);
        }

        public void SetOutfit(Color shirt, Color legwear)
        {
            currentShirt = shirt;
            currentLegwear = legwear;
            dressed = true;
            Dress();
        }

        /// <summary>
        /// The tie's colour (a shop outfit's third colour). Applies at once, over whatever outfit is on.
        /// A colour with no opacity at all takes the tie off (an outfit with no tie, such as the Holiday one).
        /// </summary>
        public void SetAccent(Color accent)
        {
            currentAccent = accent;
            accented = true;
            wantAccentHidden = accent.a < 0.01f;
            Dress();
        }

        void Dress()
        {
            Color shirt = dressed ? currentShirt : defaultShirt, legwear = dressed ? currentLegwear : defaultLegwear;
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
                FindAccent();
            }
            if (original == null || parts == null || parts.Length != original.Length) return;
            var colors = new Color[original.Length];
            for (int i = 0; i < colors.Length; i++)
            {
                int part = Mathf.RoundToInt(parts[i].x);
                Color c = original[i];
                if (part == 1) c = Recolor(c, defaultShirt, shirt);
                else if (part == 2) c = Recolor(c, defaultLegwear, legwear);
                else if (part == 3 && currentHair != default(Color)) c = Recolor(c, defaultHair, currentHair);
                else if (part == 4 && accented) c = Recolor(c, defaultAccent, currentAccent);
                colors[i] = c;
            }
            mesh.colors = colors;
            ShowAccent();
        }

        /// <summary>Remember where the accent's vertices are, and the one point they collapse to when it is taken off.</summary>
        void FindAccent()
        {
            if (parts == null) return;
            var found = new System.Collections.Generic.List<int>();
            for (int i = 0; i < parts.Length; i++)
                if (Mathf.RoundToInt(parts[i].x) == 4) found.Add(i);
            if (found.Count == 0) return;
            restVertices = mesh.vertices;
            accentVertices = found.ToArray();
            Vector3 sum = Vector3.zero;
            foreach (int i in accentVertices) sum += restVertices[i];
            accentAnchor = sum / accentVertices.Length;
        }

        /// <summary>Put the accent on or take it off, as the outfit wants (only when that changes).</summary>
        void ShowAccent()
        {
            if (mesh == null || restVertices == null || accentVertices == null || wantAccentHidden == accentHidden) return;
            var vertices = (Vector3[])restVertices.Clone();
            if (wantAccentHidden)
                foreach (int i in accentVertices) vertices[i] = accentAnchor;
            mesh.vertices = vertices;
            accentHidden = wantAccentHidden;
        }

        public void ResetOutfit()
        {
            dressed = accented = false;
            wantAccentHidden = false;
            if (mesh != null && original != null) mesh.colors = original;
            ShowAccent();
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
