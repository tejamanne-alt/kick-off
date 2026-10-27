using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Gentle breathing scale to draw the eye (next level, affordable item).</summary>
    public class UIPulse : MonoBehaviour
    {
        public float amount = 0.06f;
        public float speed = 3f;

        void Update()
        {
            transform.localScale = Vector3.one * (1f + Mathf.Sin(Time.unscaledTime * speed) * amount);
        }
    }
}
