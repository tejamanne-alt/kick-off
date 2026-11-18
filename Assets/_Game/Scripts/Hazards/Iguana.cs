using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A green iguana basking on a seawall or a warm kerb (FL2-1, FL1-4: they sun themselves all along Miami's waterways). When
    /// the kid comes near it scuttles off along the footpath to its other spot, fast and low, and a ball in its way is knocked
    /// back. Then it basks there until the kid comes near again. Wait a moment for it to go, or chip the ball over it.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Iguana : HazardBase
    {
        [Tooltip("Its two basking spots along the footpath (x).")]
        public float spotA = -2f, spotB = 2f;
        public float groundY;
        public float dashSpeed = 4.5f;
        [Tooltip("The kid this close sets it off.")]
        public float wakeRange = 3.2f;
        public Vector2 knockVelocity = new Vector2(-3f, 2.5f);
        public Transform visual;

        float x, to, lastKnock = -10f;
        bool dashing, atA;
        Collider2D body;

        public bool IsDashing { get { return dashing; } }

        void Awake()
        {
            body = GetComponent<Collider2D>();
            body.isTrigger = true;
            ResetState();
        }

        public override void ResetState()
        {
            x = spotA;
            atA = true;
            dashing = false;
            Place();
        }

        void Update()
        {
            if (!IsLive) return;
            var kid = Kid;
            if (!dashing && kid != null && Mathf.Abs(kid.transform.position.x - x) < wakeRange)
            {
                dashing = true;
                to = atA ? spotB : spotA;
            }
            // Basking, it is still: it is placed only while it runs and as it stops (docs/LEARNINGS.md B8).
            if (!dashing) return;
            x = Mathf.MoveTowards(x, to, dashSpeed * Time.deltaTime);
            if (Mathf.Abs(x - to) < 0.01f)
            {
                dashing = false;
                atA = !atA;
            }
            Place();
        }

        void Place()
        {
            transform.position = new Vector3(x, groundY, 0f);
            body.enabled = dashing;
            if (visual == null) return;
            float facing = dashing ? Mathf.Sign(to - x + 0.0001f) : atA ? 1f : -1f;
            visual.localRotation = Quaternion.Euler(0f, facing >= 0f ? 90f : -90f, dashing ? Mathf.Sin(Time.time * 30f) * 8f : 0f);
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            BallController ball;
            if (!IsLive || !dashing || !TryGetBall(other, out ball) || Time.time - lastKnock < 0.5f) return;
            lastKnock = Time.time;
            float dir = Mathf.Sign(to - x + 0.0001f);
            ball.Kick(new Vector2(dir * Mathf.Abs(knockVelocity.x), knockVelocity.y));
            GameEvents.Raise(GameEventType.PedestrianBump, transform.position, 0.5f);
        }
    }
}
