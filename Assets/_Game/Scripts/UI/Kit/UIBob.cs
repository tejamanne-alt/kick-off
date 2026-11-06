using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Bobs a UI element gently up and down about where it was placed (the map's "PLAY" and "LATE!" tags).</summary>
    public class UIBob : MonoBehaviour
    {
        [Tooltip("How far it moves up and down, in canvas units of its parent.")]
        public float amount = 8f;
        public float speed = 4f;

        RectTransform rect;
        Vector2 home;

        void Start()
        {
            rect = transform as RectTransform;
            if (rect != null) home = rect.anchoredPosition;
        }

        void Update()
        {
            if (rect == null) return;
            rect.anchoredPosition = home + new Vector2(0f, (Mathf.Sin(Time.unscaledTime * speed) * 0.5f + 0.5f) * amount);
        }
    }
}
