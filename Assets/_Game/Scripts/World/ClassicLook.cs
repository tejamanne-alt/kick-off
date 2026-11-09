using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The classic cartoon filter's look (Settings, Add-ons &amp; Filters): the values both its camera pass
    /// (<see cref="PostFX"/>, Shaders/PostFX passes 7 to 9) and the menus' pictures (UI/CartoonPicture) are drawn with, so
    /// the street and the UI match. Matched to the classic Road Runner shorts the review sent (review/cartoon: the boards
    /// and classic_port.py, the reference these numbers come from): inked cels over a painted background.
    ///
    /// Two settings were reviewed: <see cref="Classic"/> (shipped) and <see cref="CalmerLook"/> (gentler colour: less
    /// saturation and orange, softer warm shadows, a paler sky). <see cref="Calmer"/> switches between them everywhere.
    /// Colours are display (gamma) values, set as plain vectors (never colour-space converted).
    /// </summary>
    public sealed class ClassicLook
    {
        /// <summary>Draw the calmer setting instead of the classic one (the camera and the menus' pictures alike).</summary>
        public static bool Calmer = false;

        // crisp detail: of what the smoothing takes away, weak texture goes and strong detail comes back
        public float coreFrom = 0.035f, coreTo = 0.09f, sharpen = 0.55f, finish = 0.35f;
        // the cels (the people, the ball, the things the kid plays with)
        public float celCoreFrom = 0.08f, celCoreTo = 0.16f, celBands = 3f, celBandSoft = 0.22f, celBandMix = 0.6f, celSaturation = 1.3f;
        public float celLine = 3.4f, celLineFar = 1.5f;
        public Vector4 celInk = new Vector4(0.11f, 0.06f, 0.045f, 1f);
        // the painted scenery
        public float saturation = 1.35f, vibrance = 1.8f, bands = 4f, bandSoft = 0.32f, bandMix = 0.6f, shadowReach = 0.45f;
        public Vector4 warm = new Vector4(1.1f, 0.97f, 0.8f, 1f);
        public Vector4 shadowWarm = new Vector4(1.05f, 0.86f, 0.72f, 1f);
        public float strokeEdge = 0.16f, strokeDark = 0.6f, strokeStrength = 0.75f;
        public float formEdge = 0.05f, formDark = 0.62f, formStrength = 0.8f;
        public float brush = 0.025f, brushLength = 26f;
        // the sky, the clouds, the print
        public Vector4 skyTop = new Vector4(62f / 255f, 190f / 255f, 222f / 255f, 1f);
        public Vector4 skyLow = new Vector4(168f / 255f, 228f / 255f, 236f / 255f, 1f);
        public Vector4 cloudShade = new Vector4(0.86f, 0.9f, 0.95f, 1f);
        public float grain = 0.012f, vignette = 0.2f;

        /// <summary>The classic setting (shipped).</summary>
        public static readonly ClassicLook Classic = new ClassicLook();

        /// <summary>The calmer setting: the same cels and painted scenery, gentler colour.</summary>
        public static readonly ClassicLook CalmerLook = new ClassicLook
        {
            celSaturation = 1.2f, saturation = 1.22f, vibrance = 1.15f,
            warm = new Vector4(1.07f, 0.98f, 0.86f, 1f), shadowWarm = new Vector4(1.03f, 0.9f, 0.8f, 1f),
            skyTop = new Vector4(78f / 255f, 186f / 255f, 222f / 255f, 1f), skyLow = new Vector4(176f / 255f, 228f / 255f, 237f / 255f, 1f),
            vignette = 0.15f,
        };

        /// <summary>The setting in use.</summary>
        public static ClassicLook Active { get { return Calmer ? CalmerLook : Classic; } }

        static readonly int CoreFromId = Shader.PropertyToID("_CoreFrom");
        static readonly int CoreToId = Shader.PropertyToID("_CoreTo");
        static readonly int CelCoreFromId = Shader.PropertyToID("_CelCoreFrom");
        static readonly int CelCoreToId = Shader.PropertyToID("_CelCoreTo");
        static readonly int SharpenId = Shader.PropertyToID("_Sharpen");
        static readonly int FinishId = Shader.PropertyToID("_Finish");
        static readonly int CelSatId = Shader.PropertyToID("_CelSat");
        static readonly int CelBandsId = Shader.PropertyToID("_CelBands");
        static readonly int CelBandSoftId = Shader.PropertyToID("_CelBandSoft");
        static readonly int CelBandMixId = Shader.PropertyToID("_CelBandMix");
        static readonly int CelLineId = Shader.PropertyToID("_CelLine");
        static readonly int CelLineFarId = Shader.PropertyToID("_CelLineFar");
        static readonly int CelInkId = Shader.PropertyToID("_CelInk");
        static readonly int BgSatId = Shader.PropertyToID("_BgSat");
        static readonly int BgVibranceId = Shader.PropertyToID("_BgVibrance");
        static readonly int BgBandsId = Shader.PropertyToID("_BgBands");
        static readonly int BgBandSoftId = Shader.PropertyToID("_BgBandSoft");
        static readonly int BgBandMixId = Shader.PropertyToID("_BgBandMix");
        static readonly int ShadowReachId = Shader.PropertyToID("_ShadowReach");
        static readonly int WarmId = Shader.PropertyToID("_Warm");
        static readonly int ShadowWarmId = Shader.PropertyToID("_ShadowWarm");
        static readonly int StrokeEdgeId = Shader.PropertyToID("_StrokeEdge");
        static readonly int StrokeDarkId = Shader.PropertyToID("_StrokeDark");
        static readonly int StrokeStrengthId = Shader.PropertyToID("_StrokeStrength");
        static readonly int FormEdgeId = Shader.PropertyToID("_FormEdge");
        static readonly int FormDarkId = Shader.PropertyToID("_FormDark");
        static readonly int FormStrengthId = Shader.PropertyToID("_FormStrength");
        static readonly int BrushId = Shader.PropertyToID("_Brush");
        static readonly int BrushLengthId = Shader.PropertyToID("_BrushLength");
        static readonly int SkyTopId = Shader.PropertyToID("_SkyTop");
        static readonly int SkyLowId = Shader.PropertyToID("_SkyLow");
        static readonly int CloudShadeId = Shader.PropertyToID("_CloudShade");
        static readonly int GrainId = Shader.PropertyToID("_ClassicGrain");
        static readonly int VignetteId = Shader.PropertyToID("_ClassicVignette");

        /// <summary>Set every value on <paramref name="m"/> (the camera's PostFX material or a picture's material).</summary>
        public void Apply(Material m)
        {
            m.SetFloat(CoreFromId, coreFrom);
            m.SetFloat(CoreToId, coreTo);
            m.SetFloat(CelCoreFromId, celCoreFrom);
            m.SetFloat(CelCoreToId, celCoreTo);
            m.SetFloat(SharpenId, sharpen);
            m.SetFloat(FinishId, finish);
            m.SetFloat(CelSatId, celSaturation);
            m.SetFloat(CelBandsId, celBands);
            m.SetFloat(CelBandSoftId, celBandSoft);
            m.SetFloat(CelBandMixId, celBandMix);
            m.SetFloat(CelLineId, celLine);
            m.SetFloat(CelLineFarId, celLineFar);
            m.SetVector(CelInkId, celInk);
            m.SetFloat(BgSatId, saturation);
            m.SetFloat(BgVibranceId, vibrance);
            m.SetFloat(BgBandsId, bands);
            m.SetFloat(BgBandSoftId, bandSoft);
            m.SetFloat(BgBandMixId, bandMix);
            m.SetFloat(ShadowReachId, shadowReach);
            m.SetVector(WarmId, warm);
            m.SetVector(ShadowWarmId, shadowWarm);
            m.SetFloat(StrokeEdgeId, strokeEdge);
            m.SetFloat(StrokeDarkId, strokeDark);
            m.SetFloat(StrokeStrengthId, strokeStrength);
            m.SetFloat(FormEdgeId, formEdge);
            m.SetFloat(FormDarkId, formDark);
            m.SetFloat(FormStrengthId, formStrength);
            m.SetFloat(BrushId, brush);
            m.SetFloat(BrushLengthId, brushLength);
            m.SetVector(SkyTopId, skyTop);
            m.SetVector(SkyLowId, skyLow);
            m.SetVector(CloudShadeId, cloudShade);
            m.SetFloat(GrainId, grain);
            m.SetFloat(VignetteId, vignette);
        }
    }
}
