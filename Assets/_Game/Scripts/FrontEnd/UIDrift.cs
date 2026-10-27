using UnityEngine;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>Slides a UI element sideways forever, wrapping around the screen (clouds).</summary>
    public class UIDrift : MonoBehaviour
    {
        public float speed = 20f;

        void Update()
        {
            var rt = (RectTransform)transform;
            var parent = (RectTransform)rt.parent;
            float width = parent.rect.width;
            Vector2 p = rt.anchoredPosition;
            p.x += speed * Time.unscaledDeltaTime;
            if (p.x > width + 300f) p.x = -300f;
            rt.anchoredPosition = p;
        }
    }
}
