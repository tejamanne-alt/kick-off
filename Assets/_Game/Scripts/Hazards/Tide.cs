using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Sea water that washes in and out over a stretch of sand. Moves its whole
    /// object (water visual + lose-zone trigger) between low and high water.
    /// Cross while the tide is out.
    /// </summary>
    public class Tide : HazardBase
    {
        [Tooltip("World y offset at low tide (relative to the start position).")]
        public float lowOffset = -1f;
        [Tooltip("World y offset at high tide.")]
        public float highOffset = 0f;
        public float period = 6f;
        public float phaseOffset;

        public bool IsHigh { get; private set; }

        Vector3 start;
        float time;

        void Awake()
        {
            start = transform.position;
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Apply();
        }

        void Update()
        {
            time += Time.deltaTime;
            Apply();
        }

        void Apply()
        {
            // Smooth swell: lingers a little at each end.
            float s = 0.5f - 0.5f * Mathf.Cos(time / period * Mathf.PI * 2f);
            s = s * s * (3f - 2f * s);
            transform.position = start + Vector3.up * Mathf.Lerp(lowOffset, highOffset, s);
            IsHigh = s > 0.5f;
        }
    }
}
