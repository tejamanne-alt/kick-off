using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// A band of light sweeping across a masked graphic every few seconds: the rainbow sheen on a
    /// holo sticker, the glint on a gold one. Sits on a child of a Mask, slanted, and slides from
    /// one side of the parent to the other. Runs while paused.
    /// </summary>
    public class UISheen : MonoBehaviour
    {
        public float period = 2.8f;
        [Tooltip("Fraction of the period spent sweeping; the rest is a pause.")]
        public float sweep = 0.45f;
        public float offset;

        void Update()
        {
            var rt = (RectTransform)transform;
            var parent = rt.parent as RectTransform;
            if (parent == null) return;
            float w = parent.rect.width;
            float t = Mathf.Repeat(Time.unscaledTime / period + offset, 1f) / Mathf.Max(0.05f, sweep);
            float x = Mathf.Lerp(-w * 1.1f, w * 1.1f, Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(t)));
            rt.anchoredPosition = new Vector2(x, 0f);
        }
    }
}
