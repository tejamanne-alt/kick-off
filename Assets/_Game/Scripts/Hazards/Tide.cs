using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// The sea washing up the beach and back over a stretch of sand. The lose-zone trigger
    /// rises and falls with the tide; the wash (TideWash) runs up from the water's edge and
    /// over the kid's path at high water. Cross while the water is out.
    /// </summary>
    public class Tide : HazardBase
    {
        [Tooltip("World y offset at low tide (relative to the start position).")]
        public float lowOffset = -1f;
        [Tooltip("World y offset at high tide.")]
        public float highOffset = 0f;
        public float period = 6f;
        public float phaseOffset;
        [Tooltip("Optional: a water visual that sloshes gently sideways as the tide moves.")]
        public Transform surface;
        [Tooltip("The wave running up the beach, driven by the tide.")]
        public World.TideWash wash;

        public bool IsHigh { get; private set; }

        Vector3 start;
        Vector3 surfaceStart;
        float time;

        void Awake()
        {
            start = transform.position;
            if (surface != null) surfaceStart = surface.localPosition;
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
            if (wash != null) wash.Level = s;
            if (surface != null)
                surface.localPosition = surfaceStart + Vector3.right * Mathf.Sin(time * 1.4f) * 0.18f;
        }
    }
}
