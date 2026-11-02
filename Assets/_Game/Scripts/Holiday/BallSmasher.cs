using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// On the ball of a Holiday Run: a kick that hits a crate, a sandcastle or a stack of cones hard
    /// enough smashes it (for coins), and the ball goes on through the burst with most of its speed.
    /// A dribble only bumps it.
    /// </summary>
    public class BallSmasher : MonoBehaviour
    {
        [Tooltip("How fast (m/s) the ball must be going to smash something.")]
        public float minSpeed = 6f;
        [Tooltip("How much of its speed the ball keeps going through the burst.")]
        [Range(0f, 1f)] public float keepSpeed = 0.85f;

        Rigidbody2D body;
        Vector2 velocityBefore;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
        }

        void FixedUpdate()
        {
            // The velocity of the last step: by the time a collision is reported the impact has already slowed the ball.
            if (body != null) velocityBefore = body.linearVelocity;
        }

        void OnCollisionEnter2D(Collision2D collision)
        {
            var crate = collision.collider != null ? collision.collider.GetComponentInParent<RunBreakable>() : null;
            if (crate == null || crate.Smashed) return;
            if (velocityBefore.magnitude < minSpeed && collision.relativeVelocity.magnitude < minSpeed) return;
            Vector2 point = collision.contactCount > 0 ? collision.GetContact(0).point : (Vector2)transform.position;
            crate.Smash(point);
            if (body != null) body.linearVelocity = velocityBefore * keepSpeed;
        }
    }
}
