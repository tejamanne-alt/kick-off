using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Turns a UI element slowly and bobs it up and down (the logo's ball). Runs while paused.</summary>
    public class UISpin : MonoBehaviour
    {
        [Tooltip("Degrees per second; negative turns clockwise.")]
        public float speed = -60f;
        [Tooltip("How far it bobs, in canvas pixels.")]
        public float bob = 8f;
        public float bobPeriod = 1.6f;

        Vector2 basePosition;
        float baseAngle;

        void Start()
        {
            var rt = (RectTransform)transform;
            basePosition = rt.anchoredPosition;
            baseAngle = rt.localEulerAngles.z;
        }

        void Update()
        {
            var rt = (RectTransform)transform;
            float t = Time.unscaledTime;
            rt.localRotation = Quaternion.Euler(0f, 0f, baseAngle + t * speed);
            rt.anchoredPosition = basePosition + Vector2.up * Mathf.Sin(t * Mathf.PI * 2f / bobPeriod) * bob;
        }
    }
}
