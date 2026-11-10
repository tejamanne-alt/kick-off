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
        // Worked out once per mesh copy, so a change of outfit is one multiply per channel a vertex (a passer-by's respawn
        // redressed ~9k vertices in one physics step: docs/PERFORMANCE.md): each vertex's part, its brightness against its
        // part's default colour (Recolor's k), and its own colour as the mesh stores it.
        byte[] vertexPart;
        float[] vertexK;
        Color32[] original32;
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
                Prepare();
            }
            if (original == null || parts == null || parts.Length != original.Length || vertexPart == null) return;
            bool same = made == Made.Outfit && shirt.Equals(madeShirt) && legwear.Equals(madeLegwear) && currentHair.Equals(madeHair)
                && accented == madeAccented && (!accented || currentAccent.Equals(madeAccent));
            if (!same)
            {
                var colors = colorBuffer;
                colors.Clear();
                if (colors.Capacity < original.Length) colors.Capacity = original.Length;
                bool hair = currentHair != default(Color);
                for (int i = 0; i < original.Length; i++)
                {
                    // (the same colours as Recolor, through the same rounding as Color to Color32)
                    switch (vertexPart[i])
                    {
                        case 1: colors.Add(Scaled(shirt, vertexK[i], original32[i].a)); break;
                        case 2: colors.Add(Scaled(legwear, vertexK[i], original32[i].a)); break;
                        case 3: colors.Add(hair ? Scaled(currentHair, vertexK[i], original32[i].a) : original32[i]); break;
                        case 4: colors.Add(accented ? Scaled(currentAccent, vertexK[i], original32[i].a) : original32[i]); break;
                        default: colors.Add(original32[i]); break;
                    }
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
                for (int i = 0; i < original.Length; i++) colors.Add(original32 != null ? original32[i] : (Color32)original[i]);
                mesh.SetColors(colors);
                made = Made.Original;
            }
            ShowAccent();
        }

        /// <summary>
        /// Each vertex's part, its k (how much lighter or darker it is than its part's default colour: the recolour keeps it) and
        /// its own colour, from the mesh copy. The default colours are the model's own, set when the level is built.
        /// </summary>
        void Prepare()
        {
            if (original == null || parts == null || parts.Length != original.Length) return;
            int n = original.Length;
            vertexPart = new byte[n];
            vertexK = new float[n];
            original32 = new Color32[n];
            for (int i = 0; i < n; i++)
            {
                int part = Mathf.RoundToInt(parts[i].x);
                Color c = original[i];
                Color from = part == 1 ? defaultShirt : part == 2 ? defaultLegwear : part == 3 ? defaultHair : defaultAccent;
                vertexPart[i] = (byte)Mathf.Clamp(part, 0, 255);
                vertexK[i] = (c.r + c.g + c.b) / Mathf.Max(0.01f, from.r + from.g + from.b);
                original32[i] = c;
            }
        }

        /// <summary>The recoloured vertex: the new colour times the vertex's k, clamped, with the vertex's own alpha (as Recolor did,
        /// rounded to bytes as Color to Color32 does).</summary>
        static Color32 Scaled(Color to, float k, byte alpha)
        {
            return new Color32(ToByte(to.r * k), ToByte(to.g * k), ToByte(to.b * k), alpha);
        }

        static byte ToByte(float v) { return (byte)Mathf.Round(Mathf.Clamp01(v) * 255f); }

        /// <summary>
        /// The renderer's mesh is being let go (Presentation/LazyRenderer, as the kid is hidden): the recoloured copy goes
        /// too, with everything read from it, so the next Dress copies the mesh loaded then. The colours asked for are
        /// kept; whoever shows the kid again dresses them (CharacterChoice replays the outfit).
        /// </summary>
        public void ForgetMesh()
        {
            if (mesh != null) Destroy(mesh);
            mesh = null;
            original = null;
            parts = null;
            vertexPart = null;
            vertexK = null;
            original32 = null;
            vertices = null;
            accentRest = null;
            accentVertices = null;
            accentHidden = false;
            made = Made.Nothing;
        }

        void OnDestroy()
        {
            if (mesh != null) Destroy(mesh);
        }
    }
}
