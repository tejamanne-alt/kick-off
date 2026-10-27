using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Counts a number up over time (coins earned). Works while paused.</summary>
    [RequireComponent(typeof(Text))]
    public class UICountUp : MonoBehaviour
    {
        public int target;
        public float duration = 0.8f;
        public float delay = 0.3f;
        public string format = "+{0}";

        Text text;
        float start;

        void OnEnable()
        {
            text = GetComponent<Text>();
            start = Time.unscaledTime + delay;
            text.text = string.Format(format, 0);
        }

        void Update()
        {
            float t = Mathf.Clamp01((Time.unscaledTime - start) / duration);
            float eased = 1f - (1f - t) * (1f - t);
            text.text = string.Format(format, Mathf.RoundToInt(target * eased));
            if (t >= 1f) enabled = false;
        }
    }
}
