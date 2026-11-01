using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>A gentle tilt back and forth with a slow breath of scale, like a sticker held up to the light. Runs while paused.</summary>
    public class UIWobble : MonoBehaviour
    {
        public float angle = 3f;
        public float scale = 0.015f;
        public float speed = 0.9f;

        void Update()
        {
            float t = Time.unscaledTime * speed;
            transform.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(t) * angle);
            transform.localScale = Vector3.one * (1f + Mathf.Sin(t * 1.3f + 1f) * scale);
        }
    }
}
