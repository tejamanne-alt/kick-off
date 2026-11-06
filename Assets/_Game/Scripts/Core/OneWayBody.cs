using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// A pushable thing (a crate) that can be kicked or walked forward but never shoved back past where it started: a pipe
    /// rolling down at it, or the ball coming back, cannot push it into the way behind it (where it could wall the kid in at
    /// the end of a slide-under). It may still topple and fall where it stands.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class OneWayBody : MonoBehaviour
    {
        [Tooltip("How far (m) it may still move back from where it started.")]
        public float backSlack = 0.08f;

        Rigidbody2D body;
        float startX;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            startX = body.position.x;
        }

        void FixedUpdate()
        {
            float limit = startX - backSlack;
            Vector2 p = body.position;
            if (p.x >= limit) return;
            body.position = new Vector2(limit, p.y);
            Vector2 v = body.linearVelocity;
            if (v.x < 0f) body.linearVelocity = new Vector2(0f, v.y);
        }
    }
}
