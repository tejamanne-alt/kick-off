using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Gentle breathing scale to draw the eye (next level, affordable item).</summary>
    public class UIPulse : MonoBehaviour
    {
        public float amount = 0.06f;
        public float speed = 3f;

        UIButtonFx fx;

        void Awake()
        {
            fx = GetComponent<UIButtonFx>();
        }

        void Update()
        {
            float s = 1f + Mathf.Sin(Time.unscaledTime * speed) * amount;
            // On a button, let the press animation own the scale and just feed it the pulse.
            if (fx != null) fx.pulse = s;
            else transform.localScale = Vector3.one * s;
        }
    }
}
