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

        SkinnedMeshRenderer smr;
        Mesh mesh;
        Color[] original;
        Vector2[] parts;
        // The accent (the tie) can be taken off: its vertices all collapse to one point on the chest.
        // The mesh's vertices are kept as last set and only the tie's are changed in place (a copy of every
        // vertex for each change was 1.2 MB of garbage for a 100k-vertex kid).
        Vector3[] vertices;
        Vector3[] accentRest;   // where each of the tie's vertices is when it is on
        int[] accentVertices;
        Vector3 accentAnchor;
        bool accentHidden, wantAccentHidden;

        // What the mesh's colours were last made from, so that asking for the same again (a passer-by drawing the
        // clothes they already wear, the same outfit set twice) costs nothing: working out and uploading
        // every vertex's colour of a 100k-vertex kid is a frame's work on a phone. The default* colours are left
        // out: they are the model's own, set when the level is built, and never change in play.
        enum Made { Nothing, Original, Outfit }
        Made made;
        Color madeShirt, madeLegwear, madeHair, madeAccent;
        bool madeAccented;

        // One buffer for every model's colours, reused (the mesh copies it): a new Color[] for each Dress was 1.6 MB
        // of garbage for a 100k-vertex kid. As Color32 the colours also take a quarter of the upload and of the GPU's
        // vertex reads, and come out within 1/255 of the float ones (Color to Color32 rounds to the nearest step).
        static readonly System.Collections.Generic.List<Color32> colorBuffer = new System.Collections.Generic.List<Color32>();

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
            if (smr == null) smr = GetComponent<SkinnedMeshRenderer>();
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
                made = Made.Original;   // the copy has the model's own colours
                FindAccent();
            }
            if (original == null || parts == null || parts.Length != original.Length) return;
            bool same = made == Made.Outfit && shirt.Equals(madeShirt) && legwear.Equals(madeLegwear) && currentHair.Equals(madeHair)
                && accented == madeAccented && (!accented || currentAccent.Equals(madeAccent));
            if (!same)
            {
                var colors = colorBuffer;
                colors.Clear();
                if (colors.Capacity < original.Length) colors.Capacity = original.Length;
                for (int i = 0; i < original.Length; i++)
                {
                    int part = Mathf.RoundToInt(parts[i].x);
                    Color c = original[i];
                    if (part == 1) c = Recolor(c, defaultShirt, shirt);
                    else if (part == 2) c = Recolor(c, defaultLegwear, legwear);
                    else if (part == 3 && currentHair != default(Color)) c = Recolor(c, defaultHair, currentHair);
                    else if (part == 4 && accented) c = Recolor(c, defaultAccent, currentAccent);
                    colors.Add(c);
                }
                mesh.SetColors(colors);
                made = Made.Outfit;
                madeShirt = shirt; madeLegwear = legwear; madeHair = currentHair;
                madeAccented = accented; madeAccent = currentAccent;
            }
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
            vertices = mesh.vertices;
            accentVertices = found.ToArray();
            accentRest = new Vector3[accentVertices.Length];
            Vector3 sum = Vector3.zero;
            for (int j = 0; j < accentVertices.Length; j++)
            {
                accentRest[j] = vertices[accentVertices[j]];
                sum += accentRest[j];
            }
            accentAnchor = sum / accentVertices.Length;
        }

        /// <summary>Put the accent on or take it off, as the outfit wants (only when that changes).</summary>
        void ShowAccent()
        {
            if (mesh == null || vertices == null || accentVertices == null || wantAccentHidden == accentHidden) return;
            // Only the tie's vertices differ between on and off, so the rest of the kept copy is already right.
            for (int j = 0; j < accentVertices.Length; j++)
                vertices[accentVertices[j]] = wantAccentHidden ? accentAnchor : accentRest[j];
            mesh.vertices = vertices;
            accentHidden = wantAccentHidden;
        }

        public void ResetOutfit()
        {
            dressed = accented = false;
            wantAccentHidden = false;
            if (mesh != null && original != null && made != Made.Original)
            {
                // The model's own colours, through the same 8-bit buffer as Dress so the mesh keeps one vertex format
                // (switching between float and 8-bit colours re-lays out the whole vertex buffer).
                var colors = colorBuffer;
                colors.Clear();
                if (colors.Capacity < original.Length) colors.Capacity = original.Length;
                for (int i = 0; i < original.Length; i++) colors.Add(original[i]);
                mesh.SetColors(colors);
                made = Made.Original;
            }
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
