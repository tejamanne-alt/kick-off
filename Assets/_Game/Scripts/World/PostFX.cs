using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The camera's finishing pass (Shaders/PostFX.shader): a faint bloom on the brightest
    /// highlights, then the grade of the anime look (docs/ART_DIRECTION.md), measured against the
    /// reference shots: a neutral white balance (no yellow cast), a toe that sinks the darkest tones
    /// into deep, cool shadow, a little contrast, a shoulder that keeps whites just below pure white,
    /// vibrance (quiet colours lifted a touch, strong ones left alone), a split tone (cool shadows,
    /// faintly mauve mid-greys) and a light vignette. The bloom runs on a quarter-size chain so it
    /// stays cheap on phones; turn it off with <see cref="bloom"/>.
    ///
    /// With the comic halftone filter chosen in Settings (Progression/AddOns.Filter, live: read every
    /// frame) the grade feeds two more passes instead: the comic look (punchier colour in cel bands, the
    /// shade as halftone dots, hatching in the deepest shade, an ink line from the camera's depth and
    /// normals) and the print (the colour plates slipping out of register toward the edges, warm paper,
    /// a faint grain). Every model in the scene goes through it, the people and the ball included. Their
    /// painted eyes stay clear: ToonCharacter marks them in the picture's alpha, and the ink line draws no
    /// creases across them (only their outline), and their plates slip half as far. The depth and normals
    /// texture is asked for only while the filter is on (an extra pass over the opaque scene).
    ///
    /// The pencil sketch filter (pass 6, one full-screen pass) draws the picture on warm paper instead: a faint
    /// wash of its colour (the people and the ball keep theirs), pencil hatching by tone, the sky left open, and
    /// the outline drawn twice with a wandering offset, from the same depth, normals and figure mask.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class PostFX : MonoBehaviour
    {
        public Shader shader;
        public bool bloom = true;
        [Range(0f, 1f)] public float threshold = 0.9f;
        [Range(0f, 2f)] public float bloomIntensity = 0.12f;
        public Color bloomTint = Color.white;
        [Tooltip("White balance: multiplies the image first (a hair of blue keeps whites from going cream).")]
        public Color balance = new Color(1f, 1f, 1.01f);
        [Tooltip("Tones below this sink toward toeFloor of themselves: deep shadows, untouched mid-tones.")]
        [Range(0.05f, 0.6f)] public float toeEnd = 0.28f;
        [Range(0f, 1f)] public float toeFloor = 0.7f;
        [Range(0.5f, 1.5f)] public float contrast = 1.1f;
        [Tooltip("Above this the highlights ease toward the white point instead of clipping.")]
        [Range(0.5f, 1f)] public float shoulder = 0.84f;
        [Range(0.6f, 1f)] public float whitePoint = 0.972f;
        [Tooltip("Saturation of strong colours.")]
        [Range(0f, 2f)] public float saturation = 1f;
        [Tooltip("Saturation of greys and soft colours (vibrance).")]
        [Range(0f, 2f)] public float vibrance = 1.12f;
        [Tooltip("Added to the shadows (cool).")]
        public Color shadowTint = new Color(0f, 0f, 0.006f);
        [Tooltip("Added to the mid-tones (faintly mauve greys).")]
        public Color midTint = new Color(0.006f, -0.004f, 0.002f);
        [Tooltip("Added to the highlights.")]
        public Color highlightTint = new Color(0f, 0f, 0f);
        [Range(0f, 1f)] public float vignette = 0.12f;

        [Header("Comic halftone filter (sizes in pixels at 1080 lines; they scale with the screen)")]
        [Tooltip("Force the filter on here whatever Settings say (for looking at it in the editor).")]
        public bool forceComic;
        [Range(0.5f, 2.5f)] public float comicSaturation = 1.4f;
        [Range(0.8f, 1.5f)] public float comicContrast = 1.15f;
        [Tooltip("Brightness steps of the street's cel bands.")]
        [Range(2f, 8f)] public float bands = 4f;
        [Tooltip("0 smooth, 1 hard steps.")]
        [Range(0f, 1f)] public float bandMix = 0.7f;
        [Range(4f, 16f)] public float dotPeriod = 8.5f;
        [Tooltip("Dots start below this brightness.")]
        [Range(0.3f, 1f)] public float dotReach = 0.66f;
        [Range(0.2f, 0.75f)] public float dotSize = 0.6f;
        [Range(0f, 1f)] public float dotStrength = 1f;
        [Tooltip("How much of the dots the people and the ball take.")]
        [Range(0f, 1f)] public float characterDots = 1f;
        [Range(0f, 1f)] public float hatchStrength = 0.55f;
        [Range(0.5f, 3f)] public float inkWidth = 1.3f;
        [Range(0f, 1f)] public float inkStrength = 0.9f;
        [Tooltip("The ink line has thinned away by this distance (m).")]
        public float inkFar = 90f;
        [Tooltip("A depth jump of this fraction of the distance starts a line.")]
        [Range(0.005f, 0.3f)] public float depthEdge = 0.05f;
        [Tooltip("A turn of the surface of this much (1 - cos) starts a crease.")]
        [Range(0.05f, 1f)] public float normalEdge = 0.3f;
        public Color inkColor = new Color(0.06f, 0.05f, 0.12f);
        [Tooltip("How far the red and blue plates slip at the frame's corners.")]
        [Range(0f, 10f)] public float slip = 4f;
        [Tooltip("The paper (rgb) and how much of it shows through (a).")]
        public Color paper = new Color(0.88f, 0.75f, 0.5f, 0.04f);
        [Range(0f, 0.1f)] public float grain = 0.04f;

        [Header("Pencil sketch filter (sizes in pixels at 1080 lines)")]
        [Tooltip("Force the sketch on here whatever Settings say (for looking at it in the editor).")]
        public bool forceSketch;
        [Tooltip("How much of the picture's colour is washed onto the paper (0.12 pencil, 0.6 coloured pencil).")]
        [Range(0f, 1f)] public float sketchWash = 0.12f;
        [Tooltip("The people and the ball keep this much of their colour, so the kid is easy to find.")]
        [Range(0f, 1f)] public float figureWash = 0.75f;
        [Range(3f, 16f)] public float hatchSpacing = 7f;
        [Range(0f, 1f)] public float sketchHatch = 0.62f;
        [Tooltip("How far the doubled outline wanders.")]
        [Range(0f, 8f)] public float lineJitter = 3.2f;
        [Range(0f, 1f)] public float sketchLine = 0.92f;
        public Color graphite = new Color(0.17f, 0.17f, 0.2f);
        public Color sketchPaper = new Color(0.965f, 0.945f, 0.9f);

        Material material;
        Camera cam;
        bool askedForNormals;
        const int Levels = 4;
        const int GradePass = 3, ComicPass = 4, PrintPass = 5, SketchPass = 6;
        static Texture2D noise;
        readonly RenderTexture[] chain = new RenderTexture[Levels];

        static readonly int ThresholdId = Shader.PropertyToID("_Threshold");
        static readonly int KneeId = Shader.PropertyToID("_Knee");
        static readonly int BloomTexId = Shader.PropertyToID("_BloomTex");
        static readonly int BloomIntensityId = Shader.PropertyToID("_BloomIntensity");
        static readonly int BloomTintId = Shader.PropertyToID("_BloomTint");
        static readonly int BalanceId = Shader.PropertyToID("_Balance");
        static readonly int ToeEndId = Shader.PropertyToID("_ToeEnd");
        static readonly int ToeFloorId = Shader.PropertyToID("_ToeFloor");
        static readonly int ContrastId = Shader.PropertyToID("_Contrast");
        static readonly int ShoulderId = Shader.PropertyToID("_Shoulder");
        static readonly int WhitePointId = Shader.PropertyToID("_WhitePoint");
        static readonly int SaturationId = Shader.PropertyToID("_Saturation");
        static readonly int VibranceId = Shader.PropertyToID("_Vibrance");
        static readonly int ShadowTintId = Shader.PropertyToID("_ShadowTint");
        static readonly int MidTintId = Shader.PropertyToID("_MidTint");
        static readonly int HighlightTintId = Shader.PropertyToID("_HighlightTint");
        static readonly int VignetteId = Shader.PropertyToID("_Vignette");
        static readonly int MaskOnId = Shader.PropertyToID("_MaskOn");
        static readonly int ComicSatId = Shader.PropertyToID("_ComicSat");
        static readonly int ComicContrastId = Shader.PropertyToID("_ComicContrast");
        static readonly int BandsId = Shader.PropertyToID("_Bands");
        static readonly int BandMixId = Shader.PropertyToID("_BandMix");
        static readonly int DotPeriodId = Shader.PropertyToID("_DotPeriod");
        static readonly int DotReachId = Shader.PropertyToID("_DotReach");
        static readonly int DotSizeId = Shader.PropertyToID("_DotSize");
        static readonly int DotStrengthId = Shader.PropertyToID("_DotStrength");
        static readonly int CharacterDotsId = Shader.PropertyToID("_CharacterDots");
        static readonly int HatchStrengthId = Shader.PropertyToID("_HatchStrength");
        static readonly int InkWidthId = Shader.PropertyToID("_InkWidth");
        static readonly int InkStrengthId = Shader.PropertyToID("_InkStrength");
        static readonly int InkFarId = Shader.PropertyToID("_InkFar");
        static readonly int DepthEdgeId = Shader.PropertyToID("_DepthEdge");
        static readonly int NormalEdgeId = Shader.PropertyToID("_NormalEdge");
        static readonly int InkColorId = Shader.PropertyToID("_InkColor");
        static readonly int SlipEdgeId = Shader.PropertyToID("_SlipEdge");
        static readonly int PaperColorId = Shader.PropertyToID("_PaperColor");
        static readonly int GrainId = Shader.PropertyToID("_Grain");
        static readonly int NoiseTexId = Shader.PropertyToID("_NoiseTex");
        static readonly int SketchWashId = Shader.PropertyToID("_SketchWash");
        static readonly int FigureWashId = Shader.PropertyToID("_FigureWash");
        static readonly int HatchSpacingId = Shader.PropertyToID("_HatchSpacing");
        static readonly int SketchHatchId = Shader.PropertyToID("_SketchHatch");
        static readonly int LineJitterId = Shader.PropertyToID("_LineJitter");
        static readonly int SketchLineId = Shader.PropertyToID("_SketchLine");
        static readonly int GraphiteId = Shader.PropertyToID("_Graphite");
        static readonly int SketchPaperId = Shader.PropertyToID("_Paper");

        /// <summary>The comic halftone filter is on: chosen in Add-ons &amp; Filters, or forced here.</summary>
        public bool ComicOn { get { return !forceSketch && (forceComic || Progression.AddOns.Filter == Progression.AddOns.ComicFilter); } }

        /// <summary>The pencil sketch filter is on: chosen in Add-ons &amp; Filters, or forced here.</summary>
        public bool SketchOn { get { return forceSketch || (!forceComic && Progression.AddOns.Filter == Progression.AddOns.SketchFilter); } }

        // The filters' lines need the camera's depth and normals; asked for only while one is on,
        // and only the flag this script added is taken back.
        void LateUpdate()
        {
            if (cam == null) cam = GetComponent<Camera>();
            bool want = ComicOn || SketchOn;
            if (want && (cam.depthTextureMode & DepthTextureMode.DepthNormals) == 0)
            {
                cam.depthTextureMode |= DepthTextureMode.DepthNormals;
                askedForNormals = true;
            }
            else if (!want && askedForNormals)
            {
                cam.depthTextureMode &= ~DepthTextureMode.DepthNormals;
                askedForNormals = false;
            }
        }

        void OnDisable()
        {
            if (askedForNormals && cam != null) cam.depthTextureMode &= ~DepthTextureMode.DepthNormals;
            askedForNormals = false;
            if (material != null) Destroy(material);
            material = null;
        }

        void OnRenderImage(RenderTexture source, RenderTexture destination)
        {
            if (shader == null) shader = Shader.Find("Hidden/DribbleToSchool/PostFX");
            if (shader == null || !shader.isSupported) { Graphics.Blit(source, destination); return; }
            if (material == null) material = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };

            material.SetFloat(ThresholdId, threshold);
            material.SetFloat(KneeId, 0.2f);
            material.SetFloat(BloomIntensityId, bloom ? bloomIntensity : 0f);
            material.SetColor(BloomTintId, bloomTint);
            // The grade's colours go in as plain vectors: never colour-space converted, and a tint may be negative.
            material.SetVector(BalanceId, balance);
            material.SetFloat(ToeEndId, toeEnd);
            material.SetFloat(ToeFloorId, toeFloor);
            material.SetFloat(ContrastId, contrast);
            material.SetFloat(ShoulderId, shoulder);
            material.SetFloat(WhitePointId, Mathf.Max(whitePoint, shoulder + 0.01f));
            material.SetFloat(SaturationId, saturation);
            material.SetFloat(VibranceId, vibrance);
            material.SetVector(ShadowTintId, shadowTint);
            material.SetVector(MidTintId, midTint);
            material.SetVector(HighlightTintId, highlightTint);
            material.SetFloat(VignetteId, vignette);

            RenderTexture bloomTex = null;
            if (bloom && bloomIntensity > 0f)
            {
                int w = source.width / 4, h = source.height / 4;
                var format = source.format;
                for (int i = 0; i < Levels; i++)
                {
                    chain[i] = RenderTexture.GetTemporary(Mathf.Max(1, w), Mathf.Max(1, h), 0, format);
                    w /= 2; h /= 2;
                }
                Graphics.Blit(source, chain[0], material, 0);
                for (int i = 1; i < Levels; i++) Graphics.Blit(chain[i - 1], chain[i], material, 1);
                for (int i = Levels - 1; i > 0; i--) Graphics.Blit(chain[i], chain[i - 1], material, 2);
                bloomTex = chain[0];
            }
            material.SetTexture(BloomTexId, bloomTex != null ? bloomTex : (Texture)Texture2D.blackTexture);
            if (ComicOn && HasNormals())
            {
                SetComic(source);
                var comic = RenderTexture.GetTemporary(source.width, source.height, 0, source.format);
                comic.filterMode = FilterMode.Bilinear;
                Graphics.Blit(source, comic, material, ComicPass);
                Graphics.Blit(comic, destination, material, PrintPass);
                RenderTexture.ReleaseTemporary(comic);
            }
            else if (SketchOn && HasNormals())
            {
                SetComic(source);    // the mask, and the ink line's sizes and thresholds the outline shares
                SetSketch(source);
                Graphics.Blit(source, destination, material, SketchPass);
            }
            else
            {
                Graphics.Blit(source, destination, material, GradePass);
            }
            for (int i = 0; i < Levels; i++)
            {
                if (chain[i] != null) RenderTexture.ReleaseTemporary(chain[i]);
                chain[i] = null;
            }
        }

        // The depth and normals are drawn from the frame after the flag is set: until then, the plain grade.
        void SetSketch(RenderTexture source)
        {
            material.SetTexture(NoiseTexId, Noise());
            material.SetFloat(InkStrengthId, 1f);
            material.SetFloat(SketchWashId, sketchWash);
            material.SetFloat(FigureWashId, figureWash);
            material.SetFloat(HatchSpacingId, hatchSpacing);
            material.SetFloat(SketchHatchId, sketchHatch);
            material.SetFloat(LineJitterId, lineJitter);
            material.SetFloat(SketchLineId, sketchLine);
            material.SetVector(GraphiteId, graphite);
            material.SetVector(SketchPaperId, sketchPaper);
        }

        /// <summary>The sketch's noise: 256 x 256 random values, filtered and repeating (value noise when sampled), made once.</summary>
        static Texture2D Noise()
        {
            if (noise != null) return noise;
            const int N = 256;
            noise = new Texture2D(N, N, TextureFormat.RGBA32, false, true)
            {
                wrapMode = TextureWrapMode.Repeat, filterMode = FilterMode.Bilinear, hideFlags = HideFlags.HideAndDontSave, name = "SketchNoise",
            };
            var rng = new System.Random(1234);
            var px = new Color32[N * N];
            for (int i = 0; i < px.Length; i++)
            {
                byte v = (byte)rng.Next(256);
                px[i] = new Color32(v, v, v, 255);
            }
            noise.SetPixels32(px);
            noise.Apply(false, true);
            return noise;
        }

        bool HasNormals()
        {
            return cam != null && (cam.depthTextureMode & DepthTextureMode.DepthNormals) != 0;
        }

        void SetComic(RenderTexture source)
        {
            // Sizes are tuned at 1080 lines and scale with the picture, so the dots look the same on every phone.
            float scale = source.height / 1080f;
            // The character mask rides in alpha; a picture without alpha (an RGB HDR buffer) has none, so
            // everything is drawn like the street there.
            bool alpha = source.format != RenderTextureFormat.RGB111110Float && source.format != RenderTextureFormat.RGB565;
            material.SetFloat(MaskOnId, alpha ? 1f : 0f);
            material.SetFloat(ComicSatId, comicSaturation);
            material.SetFloat(ComicContrastId, comicContrast);
            material.SetFloat(BandsId, bands);
            material.SetFloat(BandMixId, bandMix);
            material.SetFloat(DotPeriodId, Mathf.Max(3f, dotPeriod * scale));
            material.SetFloat(DotReachId, dotReach);
            material.SetFloat(DotSizeId, dotSize);
            material.SetFloat(DotStrengthId, dotStrength);
            material.SetFloat(CharacterDotsId, characterDots);
            material.SetFloat(HatchStrengthId, hatchStrength);
            material.SetFloat(InkWidthId, Mathf.Max(0.75f, inkWidth * scale));
            material.SetFloat(InkStrengthId, inkStrength);
            material.SetFloat(InkFarId, Mathf.Max(1f, inkFar));
            material.SetFloat(DepthEdgeId, depthEdge);
            material.SetFloat(NormalEdgeId, normalEdge);
            material.SetVector(InkColorId, inkColor);
            material.SetFloat(SlipEdgeId, slip * scale);
            material.SetVector(PaperColorId, paper);
            material.SetFloat(GrainId, grain);
        }
    }
}
