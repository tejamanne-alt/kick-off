using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Moves something back and forth like waves on a beach: a quick surge toward
    /// <see cref="reach"/> and a slower draw back. Used for the foam at the water's edge and the
    /// lines of breaking crests out at sea.
    /// </summary>
    public class Lapping : MonoBehaviour
    {
        [Tooltip("How far, and which way, each surge carries it.")]
        public Vector3 reach = new Vector3(0f, 0f, -0.4f);
        public float period = 5f;
        [Tooltip("0..1, so neighbouring waves don't move in step.")]
        public float phase;

        Vector3 home;
        // The strip's extent in its own space (the foam's pivot is its parent's origin, not the strip's middle), and how far
        // outside the view it rests: a surge's reach and a metre more, so it never pops at the screen's edge.
        bool hasStrip;
        float fromX, toX, depth, restBeyond;

        void Awake()
        {
            home = transform.localPosition;
            var strip = GetComponent<WavyStrip>();
            if (strip != null)
            {
                hasStrip = true;
                fromX = Mathf.Min(strip.fromX, strip.toX);
                toX = Mathf.Max(strip.fromX, strip.toX);
                // The far edge, where the view is widest: the strip is tested where it can be seen soonest.
                depth = Mathf.Max(strip.frontZ, strip.backZ);
                restBeyond = reach.magnitude + 1f;
            }
        }

        void Update()
        {
            // About 45 crests line a beach level, three in four of them off screen at any time. The pose follows the clock
            // alone, so one left resting out of view is posed exactly right again the frame it comes back.
            if (hasStrip && AmbientView.Valid)
            {
                Vector3 at = transform.position;
                float nearestX = Mathf.Clamp(AmbientView.CameraX, at.x + fromX, at.x + toX);
                if (AmbientView.OutsideBy(nearestX, at.z + depth) > restBeyond) return;
            }
            float t = Mathf.Repeat(Time.time / Mathf.Max(0.1f, period) + phase, 1f);
            float k = t < 0.35f ? Mathf.SmoothStep(0f, 1f, t / 0.35f) : Mathf.SmoothStep(1f, 0f, (t - 0.35f) / 0.65f);
            transform.localPosition = home + reach * k;
        }
    }
}
