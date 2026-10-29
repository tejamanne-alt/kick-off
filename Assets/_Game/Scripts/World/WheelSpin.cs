using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Rolls a car's wheels as the car moves: each wheel turns about its own axle by the
    /// distance travelled over its radius, in the direction that rolls it along the ground.
    /// </summary>
    public class WheelSpin : MonoBehaviour
    {
        public Transform[] wheels;
        public float radius = 0.32f;

        Vector3 lastPosition;

        void OnEnable()
        {
            lastPosition = transform.position;
        }

        void LateUpdate()
        {
            Vector3 delta = transform.position - lastPosition;
            lastPosition = transform.position;
            if (wheels == null || delta.sqrMagnitude < 1e-8f) return;
            float angle = delta.magnitude / Mathf.Max(radius, 0.05f) * Mathf.Rad2Deg;
            foreach (var wheel in wheels)
            {
                if (wheel == null) continue;
                // Rolling forward along d about axle a needs a spin of sign(d . (a x up)).
                Vector3 axle = wheel.right;
                float sign = Mathf.Sign(Vector3.Dot(delta, Vector3.Cross(axle, Vector3.up)));
                wheel.Rotate(Vector3.right, angle * sign, Space.Self);
            }
        }
    }
}
