using DribbleToSchool.Ball;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Ball juice: squash-and-stretch along the velocity and on impacts (the
    /// squash root is kept upright while the skin spins with the physics body),
    /// plus a soft shadow on the ground that shrinks as the ball rises.
    /// </summary>
    public class BallVisual : MonoBehaviour
    {
        public BallController ball;
        [Tooltip("Non-rotating root for squash; child of the ball.")]
        public Transform squashRoot;
        public SpriteRenderer shadow;
        public float maxStretch = 0.18f;
        public float shadowMaxDistance = 5f;

        readonly RaycastHit2D[] hits = new RaycastHit2D[4];
        ContactFilter2D filter;
        float impactTime = -10f;
        float impactStrength;
        Vector2 impactNormal = Vector2.up;

        void Awake()
        {
            filter = new ContactFilter2D();
            filter.useTriggers = false;
        }

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
            squashRoot.localScale = new Vector3(along, across, 1f);
            // Children counter-rotate so the skin keeps the body's spin.
            for (int i = 0; i < squashRoot.childCount; i++)
                squashRoot.GetChild(i).rotation = ball.transform.rotation;

            UpdateShadow();
        }

        void UpdateShadow()
        {
            if (shadow == null) return;
            int count = Physics2D.Raycast(ball.Body.position, Vector2.down, filter, hits, shadowMaxDistance);
            float best = float.MaxValue;
            Vector2 point = Vector2.zero;
            for (int i = 0; i < count; i++)
            {
                if (hits[i].rigidbody == ball.Body) continue;
                if (ball.kid != null && hits[i].rigidbody == ball.kid.Body) continue;
                if (hits[i].distance < best) { best = hits[i].distance; point = hits[i].point; }
            }
            if (best == float.MaxValue)
            {
                shadow.enabled = false;
                return;
            }
            shadow.enabled = true;
            float k = 1f - Mathf.Clamp01(best / shadowMaxDistance);
            shadow.transform.position = new Vector3(point.x, point.y + 0.02f, 0f);
            shadow.transform.rotation = Quaternion.identity;
            shadow.transform.localScale = Vector3.one * Mathf.Lerp(0.25f, 0.55f, k);
            Color c = shadow.color;
            c.a = Mathf.Lerp(0.1f, 0.4f, k);
            shadow.color = c;
        }
    }
}
