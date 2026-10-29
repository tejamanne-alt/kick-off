using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Where a wave's front edge lies on the beach (z, toward the camera is smaller) at x: wavy,
    /// and curling back toward the sea beyond the ends of the stretch it washes over, so a
    /// swash reads as a tongue of sea rather than a band across the beach.
    /// </summary>
    public static class Shoreline
    {
        public static float Front(float x, float fromX, float toX, float frontZ, float seaZ, float time)
        {
            float z = frontZ + 0.35f * Mathf.Sin(x * 0.9f + time * 0.7f) + 0.18f * Mathf.Sin(x * 2.3f - time * 1.1f) + 0.1f * Mathf.Sin(x * 5.1f + time * 0.4f);
            float outside = x < fromX ? fromX - x : x > toX ? x - toX : 0f;
            z += outside * outside * 1.6f;
            return Mathf.Min(z, seaZ - 0.05f);
        }
    }
}
