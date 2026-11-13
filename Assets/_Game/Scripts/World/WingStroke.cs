using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A small bird's wingbeat as a real one beats (docs/LEARNINGS.md D21): the downstroke, the wing spread, takes a
    /// little more than half the beat and sweeps a little forward; on the upstroke the wing folds at the wrist and
    /// sweeps back, so it rises half closed, and opens again at the top. A wing beaten as one stiff paddle on a sine
    /// read as a toy's. The body rises on each downstroke. GroundBird's take-off and SkyFlock beat the Kamakura kit's
    /// birds with it (AmbientAgent.Part.SetWing); the asset review draws the same (tools/blender/asset_review.py:
    /// wing_stroke). Change the two together.
    /// </summary>
    public static class WingStroke
    {
        /// <summary>The share of a beat the downstroke takes.</summary>
        public const float DownShare = 0.55f;

        /// <summary>The wing at phase (radians, a beat every 2 pi; 0 the top of the beat), for a wing raised up degrees
        /// above level at the top and down below it at the bottom: x its flap (degrees, up positive), y its fold at the
        /// wrist (degrees, the outer wing turned down), z its sweep (degrees, back positive), w the body's rise (-1..1).</summary>
        public static Vector4 At(float phase, float up, float down, float fold, float sweep)
        {
            float u = phase / (2f * Mathf.PI);
            u -= Mathf.Floor(u);
            if (u < DownShare)
            {
                float w = u / DownShare, e = 0.5f - 0.5f * Mathf.Cos(Mathf.PI * w), s = Mathf.Sin(Mathf.PI * w);
                return new Vector4(up + (-down - up) * e, 0f, -0.3f * sweep * s, s);
            }
            float v = (u - DownShare) / (1f - DownShare), ev = 0.5f - 0.5f * Mathf.Cos(Mathf.PI * v), sv = Mathf.Sin(Mathf.PI * v);
            return new Vector4(-down + (up + down) * ev, fold * sv, sweep * sv, -0.4f * sv);
        }
    }
}
