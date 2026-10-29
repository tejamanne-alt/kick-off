using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Sets the shared look of the 3D street for the toon shaders: the sun direction and colour,
    /// and the distance haze that fades far scenery into the sky colour. Lives on the camera.
    /// </summary>
    [ExecuteAlways]
    public class WorldLook : MonoBehaviour
    {
        [Tooltip("Direction toward the sun (up, to the right and toward the camera).")]
        public Vector3 sunDirection = new Vector3(0.45f, 0.8f, -0.4f);
        [Tooltip("Sunlight tint on lit faces: a warm morning light against the cool shadows.")]
        public Color sunColor = new Color(1f, 0.95f, 0.86f);
        public Color hazeColor = new Color(0.62f, 0.78f, 0.95f);
        [Range(0f, 1f)] public float hazeStrength = 0.75f;
        public float hazeStart = 28f;
        public float hazeEnd = 190f;

        static readonly int LightDirId = Shader.PropertyToID("_DtsLightDir");
        static readonly int FogColorId = Shader.PropertyToID("_DtsFogColor");
        static readonly int FogRangeId = Shader.PropertyToID("_DtsFogRange");
        static readonly int SunColorId = Shader.PropertyToID("_DtsSunColor");

        void OnEnable() { Apply(); }
        void OnValidate() { Apply(); }

        void Update()
        {
            if (!Application.isPlaying) Apply();
        }

        public void Apply()
        {
            Shader.SetGlobalVector(LightDirId, sunDirection.normalized);
            Shader.SetGlobalColor(FogColorId, new Color(hazeColor.r, hazeColor.g, hazeColor.b, hazeStrength));
            Shader.SetGlobalVector(FogRangeId, new Vector4(hazeStart, hazeEnd, 0f, 0f));
            Shader.SetGlobalColor(SunColorId, new Color(sunColor.r, sunColor.g, sunColor.b, 1f));
        }
    }
}
