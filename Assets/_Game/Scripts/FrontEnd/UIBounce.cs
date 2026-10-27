using UnityEngine;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>A ball bouncing in place with squash on landing and a slow spin.</summary>
    public class UIBounce : MonoBehaviour
    {
        public float height = 70f;
        public float period = 0.9f;

        Vector2 basePosition;

        void Start()
        {
            basePosition = ((RectTransform)transform).anchoredPosition;
        }

        void Update()
        {
            float t = Mathf.Repeat(Time.unscaledTime / period, 1f);
            float y = 4f * t * (1f - t);                 // parabola 0..1..0
            float squash = Mathf.Clamp01(1f - y * 6f);   // only near the ground
            var rt = (RectTransform)transform;
            rt.anchoredPosition = basePosition + Vector2.up * y * height;
            rt.localScale = new Vector3(1f + squash * 0.15f, 1f - squash * 0.15f, 1f);
            rt.localRotation = Quaternion.Euler(0f, 0f, -Time.unscaledTime * 120f);
        }
    }
}
