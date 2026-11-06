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

        Material material;
        const int Levels = 4;
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

        void OnDisable()
        {
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
            Graphics.Blit(source, destination, material, 3);
            for (int i = 0; i < Levels; i++)
            {
                if (chain[i] != null) RenderTexture.ReleaseTemporary(chain[i]);
                chain[i] = null;
            }
        }
    }
}
