using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Springy scale-and-fade entrance when the element is enabled. Works while the game is paused.</summary>
    [RequireComponent(typeof(CanvasGroup))]
    public class UIPopIn : MonoBehaviour
    {
        public float delay;
        public float duration = 0.35f;
        public float fromScale = 0.6f;

        CanvasGroup group;
        float startTime;

        void Awake()
        {
            group = GetComponent<CanvasGroup>();
        }

        void OnEnable()
        {
            startTime = Time.unscaledTime + delay;
            Apply(0f);
        }

        void Update()
        {
            float t = Mathf.Clamp01((Time.unscaledTime - startTime) / duration);
            Apply(t);
            if (t >= 1f) enabled = false;
        }

        void Apply(float t)
        {
            // Back-out ease: overshoots slightly, then settles.
            const float s = 1.70158f;
            float e = t <= 0f ? 0f : 1f + (s + 1f) * Mathf.Pow(t - 1f, 3f) + s * Mathf.Pow(t - 1f, 2f);
            transform.localScale = Vector3.one * Mathf.LerpUnclamped(fromScale, 1f, e);
            if (group != null) group.alpha = Mathf.Clamp01(t * 2f);
        }

        /// <summary>Restart the entrance (e.g. when re-showing a cached panel).</summary>
        public void Play()
        {
            enabled = true;
            OnEnable();
        }
    }
}
