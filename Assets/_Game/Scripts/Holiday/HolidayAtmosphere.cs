using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// Carries the light and the atmosphere from one chapter's mood to the next as the kid runs from
    /// the home street to the market, the beach, the building site and the park (the moods are
    /// ChapterTheme.mood, the same ones the story levels use). A blend spans the stretch of street
    /// round each chapter boundary, so the change is gradual: the sun swings a little, the shade and
    /// the haze take on the new colours. Nothing is touched while the kid is inside a chapter.
    /// </summary>
    public class HolidayAtmosphere : MonoBehaviour
    {
        public WorldLook look;
        public Transform follow;
        [Tooltip("Half the length of street over which one chapter's light turns into the next's (metres).")]
        public float blendHalfLength = 36f;

        readonly ChapterTheme.Mood[] moods = new ChapterTheme.Mood[6];   // 1..5
        int appliedChapter = -1;
        float appliedBlend = -1f;

        void Awake()
        {
            for (int chapter = 1; chapter <= 5; chapter++) moods[chapter] = ChapterTheme.For(chapter).mood;
        }

        void Start()
        {
            Evaluate(true);
        }

        void LateUpdate()
        {
            Evaluate(false);
        }

        void Evaluate(bool force)
        {
            if (look == null) return;
            float x = follow != null ? follow.position.x : HolidayStages.SpawnX;
            int stage = HolidayStages.StageAt(x);
            int chapter = HolidayStages.All[stage].chapter;

            // The nearest chapter boundary, behind or ahead of the kid.
            float blend = 0f;
            int from = chapter, to = chapter;
            if (stage + 1 < HolidayStages.Count && HolidayStages.All[stage + 1].chapter != chapter)
            {
                float boundary = HolidayStages.EndOf(stage);
                float t = (x - (boundary - blendHalfLength)) / (2f * blendHalfLength);
                if (t > 0f) { from = chapter; to = HolidayStages.All[stage + 1].chapter; blend = t; }
            }
            if (blend <= 0f && stage > 0 && HolidayStages.All[stage - 1].chapter != chapter)
            {
                float boundary = HolidayStages.StartOf(stage);
                float t = (x - (boundary - blendHalfLength)) / (2f * blendHalfLength);
                if (t < 1f) { from = HolidayStages.All[stage - 1].chapter; to = chapter; blend = t; }
            }
            blend = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(blend));
            if (blend <= 0.001f) { blend = 0f; to = from; }
            else if (blend >= 0.999f) { blend = 0f; from = to; }

            // Steady inside a chapter: apply once, and again only when the chapter changes.
            if (!force && blend == 0f && appliedBlend == 0f && appliedChapter == from) return;
            if (!force && blend > 0f && Mathf.Abs(blend - appliedBlend) < 0.004f) return;
            appliedChapter = from;
            appliedBlend = blend;
            Apply(moods[Mathf.Clamp(from, 1, 5)], moods[Mathf.Clamp(to, 1, 5)], blend);
        }

        void Apply(ChapterTheme.Mood a, ChapterTheme.Mood b, float t)
        {
            look.sunDirection = Vector3.Lerp(a.sunDirection, b.sunDirection, t).normalized;
            look.skySunDirection = Vector3.Lerp(a.skySunDirection, b.skySunDirection, t).normalized;
            look.sunColor = Color.Lerp(a.sun, b.sun, t);
            look.sunGlow = Color.Lerp(a.glow, b.glow, t);
            look.ambientSky = Color.Lerp(a.ambientSky, b.ambientSky, t);
            look.ambientGround = Color.Lerp(a.ambientGround, b.ambientGround, t);
            look.castShadow = Color.Lerp(a.castShadow, b.castShadow, t);
            look.skyZenith = Color.Lerp(a.zenith, b.zenith, t);
            look.skyHorizon = Color.Lerp(a.horizon, b.horizon, t);
            look.hazeColor = Color.Lerp(a.haze, b.haze, t);
            look.hazeStart = Mathf.Lerp(a.hazeStart, b.hazeStart, t);
            look.hazeEnd = Mathf.Lerp(a.hazeEnd, b.hazeEnd, t);
            look.hazeStrength = Mathf.Lerp(a.hazeStrength, b.hazeStrength, t);
            look.Apply();
        }
    }
}
