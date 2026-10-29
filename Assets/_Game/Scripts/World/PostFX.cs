using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The camera's finishing pass (Shaders/PostFX.shader): a soft bloom around the brightest
    /// light, a gentle warm grade and a vignette, for the hazy golden-hour look. The bloom runs on
    /// a quarter-size chain so it stays cheap on phones; turn it off with <see cref="bloom"/>.
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class PostFX : MonoBehaviour
    {
        public Shader shader;
        public bool bloom = true;
        [Range(0f, 1f)] public float threshold = 0.78f;
        [Range(0f, 2f)] public float bloomIntensity = 0.55f;
        public Color bloomTint = new Color(1f, 0.9f, 0.78f);
        [Tooltip("Added to the shadows (warm lift).")]
        public Color lift = new Color(0.03f, 0.02f, 0.035f);
        [Tooltip("Multiplies the highlights.")]
        public Color gain = new Color(1.02f, 1f, 0.97f);
        [Range(0.5f, 1.5f)] public float contrast = 1.04f;
        [Range(0f, 2f)] public float saturation = 1.06f;
        [Range(0f, 1f)] public float vignette = 0.22f;

        Material material;
        const int Levels = 4;
        readonly RenderTexture[] chain = new RenderTexture[Levels];

        static readonly int ThresholdId = Shader.PropertyToID("_Threshold");
        static readonly int KneeId = Shader.PropertyToID("_Knee");
        static readonly int BloomTexId = Shader.PropertyToID("_BloomTex");
        static readonly int BloomIntensityId = Shader.PropertyToID("_BloomIntensity");
        static readonly int BloomTintId = Shader.PropertyToID("_BloomTint");
        static readonly int LiftId = Shader.PropertyToID("_Lift");
        static readonly int GainId = Shader.PropertyToID("_Gain");
        static readonly int ContrastId = Shader.PropertyToID("_Contrast");
        static readonly int SaturationId = Shader.PropertyToID("_Saturation");
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
            material.SetColor(LiftId, lift);
            material.SetColor(GainId, gain);
            material.SetFloat(ContrastId, contrast);
            material.SetFloat(SaturationId, saturation);
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
