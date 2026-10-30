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

        void Awake()
        {
            home = transform.localPosition;
        }

        void Update()
        {
            float t = Mathf.Repeat(Time.time / Mathf.Max(0.1f, period) + phase, 1f);
            float k = t < 0.35f ? Mathf.SmoothStep(0f, 1f, t / 0.35f) : Mathf.SmoothStep(1f, 0f, (t - 0.35f) / 0.65f);
            transform.localPosition = home + reach * k;
        }
    }
}
