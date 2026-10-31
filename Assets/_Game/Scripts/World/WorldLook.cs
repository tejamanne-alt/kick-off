using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The shared light and atmosphere of the 3D street (Shaders/DtsLook.cginc): the sun's
    /// direction and colour, the colour shade takes on from the sky and the ground bounce, the
    /// distance haze (lighter toward the sun) and the sky dome's colours. Lives on the camera.
    /// It also keeps a directional light pointed along the sun so the world casts soft shadows; the
    /// shaders do their own lighting and use the light only for those shadows.
    /// </summary>
    [ExecuteAlways]
    public class WorldLook : MonoBehaviour
    {
        [Header("Sun")]
        [Tooltip("Direction toward the sun (up, to the right and toward the camera).")]
        public Vector3 sunDirection = new Vector3(0.45f, 0.8f, -0.4f);
        [Tooltip("Sunlight tint on lit faces: clear daylight, a hair warm against the cool shade.")]
        public Color sunColor = new Color(1f, 0.97f, 0.92f);
        [Tooltip("Where the sun sits in the sky, seen from the camera: high, so only its glow shows at the top of the view.")]
        public Vector3 skySunDirection = new Vector3(-0.4f, 0.9f, 1f);
        public Color sunDisc = new Color(1f, 0.99f, 0.95f);
        [Range(0f, 1f)] public float sunDiscSize = 0.5f;
        public Color sunGlow = new Color(1f, 0.97f, 0.9f);
        [Range(0f, 1f)] public float sunGlowInHaze = 0.3f;

        [Header("Shade")]
        [Tooltip("The colour shade sides take from the sky above: cool and clear.")]
        public Color ambientSky = new Color(0.52f, 0.56f, 0.66f);
        [Tooltip("The bounce from the ground on downward-facing shade.")]
        public Color ambientGround = new Color(0.62f, 0.6f, 0.58f);

        [Header("Sky")]
        public Color skyZenith = new Color(0.2f, 0.43f, 0.72f);
        public Color skyHorizon = new Color(0.62f, 0.79f, 0.92f);

        [Header("Haze")]
        public Color hazeColor = new Color(0.68f, 0.78f, 0.88f);
        [Range(0f, 1f)] public float hazeStrength = 0.6f;
        public float hazeStart = 40f;
        public float hazeEnd = 700f;

        [Header("Shadows")]
        public bool castShadows = true;
        [Range(0f, 1f)] public float shadowStrength = 0.85f;
        public float shadowDistance = 45f;

        static readonly int LightDirId = Shader.PropertyToID("_DtsLightDir");
        static readonly int FogColorId = Shader.PropertyToID("_DtsFogColor");
        static readonly int FogRangeId = Shader.PropertyToID("_DtsFogRange");
        static readonly int SunColorId = Shader.PropertyToID("_DtsSunColor");
        static readonly int AmbientSkyId = Shader.PropertyToID("_DtsAmbientSky");
        static readonly int AmbientGroundId = Shader.PropertyToID("_DtsAmbientGround");
        static readonly int SunGlowId = Shader.PropertyToID("_DtsSunGlow");
        static readonly int SkySunDirId = Shader.PropertyToID("_DtsSkySunDir");
        static readonly int SkyZenithId = Shader.PropertyToID("_DtsSkyZenith");
        static readonly int SkyHorizonId = Shader.PropertyToID("_DtsSkyHorizon");
        static readonly int SunDiscId = Shader.PropertyToID("_DtsSunDisc");

        Light sunLight;

        void OnEnable() { Apply(); }
        void OnValidate() { Apply(); }

        void Update()
        {
            if (!Application.isPlaying) Apply();
        }

        public void Apply()
        {
            Shader.SetGlobalVector(LightDirId, sunDirection.normalized);
            Shader.SetGlobalColor(SunColorId, Opaque(sunColor));
            Shader.SetGlobalColor(AmbientSkyId, Opaque(ambientSky));
            Shader.SetGlobalColor(AmbientGroundId, Opaque(ambientGround));
            Shader.SetGlobalColor(FogColorId, new Color(hazeColor.r, hazeColor.g, hazeColor.b, hazeStrength));
            Shader.SetGlobalVector(FogRangeId, new Vector4(hazeStart, hazeEnd, 0f, 0f));
            Shader.SetGlobalColor(SunGlowId, new Color(sunGlow.r, sunGlow.g, sunGlow.b, sunGlowInHaze));
            Shader.SetGlobalVector(SkySunDirId, skySunDirection.normalized);
            Shader.SetGlobalColor(SkyZenithId, Opaque(skyZenith));
            Shader.SetGlobalColor(SkyHorizonId, Opaque(skyHorizon));
            Shader.SetGlobalColor(SunDiscId, new Color(sunDisc.r, sunDisc.g, sunDisc.b, sunDiscSize));
            ApplyShadows();
        }

        static Color Opaque(Color c) { return new Color(c.r, c.g, c.b, 1f); }

        /// <summary>A directional light along the sun, only for shadows (the shaders light themselves).</summary>
        void ApplyShadows()
        {
            if (sunLight == null)
            {
                var existing = transform.Find("SunShadows");
                sunLight = existing != null ? existing.GetComponent<Light>() : null;
            }
            if (sunLight == null)
            {
                if (!castShadows) return;
                var go = new GameObject("SunShadows");
                go.transform.SetParent(transform, false);
                sunLight = go.AddComponent<Light>();
            }
            sunLight.type = LightType.Directional;
            sunLight.transform.rotation = Quaternion.LookRotation(-sunDirection.normalized, Vector3.up);
            sunLight.color = Color.white;
            sunLight.intensity = 0.01f;            // the shaders ignore its light, so keep legacy shaders from blowing out
            sunLight.shadows = castShadows ? LightShadows.Soft : LightShadows.None;
            sunLight.shadowStrength = shadowStrength;
            sunLight.shadowBias = 0.06f;
            sunLight.shadowNormalBias = 0.5f;
            if (Application.isPlaying)
            {
                QualitySettings.shadowDistance = shadowDistance;
                QualitySettings.shadowCascades = 2;
                QualitySettings.shadowProjection = ShadowProjection.StableFit;
            }
        }
    }
}
