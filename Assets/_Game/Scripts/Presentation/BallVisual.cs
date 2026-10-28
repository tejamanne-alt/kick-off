using DribbleToSchool.Ball;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Ball juice: squash-and-stretch along the velocity and on impacts (the
    /// squash root is kept upright while the 3D ball spins with the physics body).
    /// Its shadow is a GroundShadow.
    /// </summary>
    public class BallVisual : MonoBehaviour
    {
        public BallController ball;
        [Tooltip("Non-rotating root for squash; child of the ball.")]
        public Transform squashRoot;
        public float maxStretch = 0.18f;

        float impactTime = -10f;
        float impactStrength;
        Vector2 impactNormal = Vector2.up;

        void OnEnable() { if (ball != null) ball.Bounced += Impact; }
        void OnDisable() { if (ball != null) ball.Bounced -= Impact; }

        public void Impact(Vector2 normal, float strength)
        {
            impactTime = Time.time;
            impactStrength = Mathf.Clamp01(strength);
            impactNormal = normal.sqrMagnitude > 0.01f ? normal.normalized : Vector2.up;
        }

        void LateUpdate()
        {
            if (ball == null || squashRoot == null) return;
            Vector2 v = ball.Body.linearVelocity;

            // Impact squash flattens along the contact normal; speed stretches along velocity.
            float it = Mathf.Clamp01((Time.time - impactTime) / 0.14f);
            float squash = (1f - it) * impactStrength * 0.3f;
            float stretch = Mathf.Clamp01(v.magnitude / 18f) * maxStretch;

            Vector2 axis = squash > stretch ? impactNormal : (v.sqrMagnitude > 0.01f ? v.normalized : Vector2.up);
            float along = squash > stretch ? 1f - squash : 1f + stretch;
            float across = squash > stretch ? 1f + squash * 0.8f : 1f - stretch * 0.5f;

            float angle = Mathf.Atan2(axis.y, axis.x) * Mathf.Rad2Deg;
            squashRoot.rotation = Quaternion.Euler(0f, 0f, angle);
            squashRoot.localScale = new Vector3(along, across, across);
            // Children counter-rotate so the skin keeps the body's spin.
            for (int i = 0; i < squashRoot.childCount; i++)
                squashRoot.GetChild(i).rotation = ball.transform.rotation;
        }
    }
}
