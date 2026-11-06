using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Makes an image glow on and off and swell a little: the halo round the map's next level, or its late one.</summary>
    [RequireComponent(typeof(Graphic))]
    public class UIGlow : MonoBehaviour
    {
        public float minAlpha = 0.3f, maxAlpha = 0.8f;
        public float minScale = 0.94f, maxScale = 1.1f;
        public float speed = 3.2f;

        Graphic graphic;

        void Awake()
        {
            graphic = GetComponent<Graphic>();
        }

        void Update()
        {
            float k = Mathf.Sin(Time.unscaledTime * speed) * 0.5f + 0.5f;
            Color c = graphic.color;
            c.a = Mathf.Lerp(minAlpha, maxAlpha, k);
            graphic.color = c;
            transform.localScale = Vector3.one * Mathf.Lerp(minScale, maxScale, k);
        }
    }
}
