using DribbleToSchool.Ball;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// A surface the ball can land on but the kid can't climb to (the top of a gate, the deck
    /// over an underpass). The ball resting on it is out of reach.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class BallTrap : MonoBehaviour, IBallStrander
    {
        float lastRest = -10f;
        Collider2D trapCollider;

        void Awake()
        {
            trapCollider = GetComponent<Collider2D>();
        }

        void OnCollisionStay2D(Collision2D collision)
        {
            if (collision.rigidbody == null || collision.rigidbody.GetComponent<BallController>() == null) return;
            // Resting on top: the contact pushes the ball up.
            for (int i = 0; i < collision.contactCount; i++)
            {
                if (collision.GetContact(i).normal.y < -0.5f)
                {
                    lastRest = Time.time;
                    return;
                }
            }
        }

        public bool Strands(Vector2 ball, Vector2 kid)
        {
            return Time.time - lastRest < 0.15f && trapCollider != null && trapCollider.enabled
                && ball.y > trapCollider.bounds.max.y - 0.05f;
        }
    }
}
