using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A rooster or a hen loose in a Little Havana street (FL1-1: Miami's free-roaming chickens). It struts and pecks about its
    /// patch, and when a ball comes rolling at it fast it flutters up out of the way in a squawk of feathers, landing a little
    /// further off. Dribble at it slowly and it only steps aside; a ball that catches it before it is up bounces off it, up and
    /// back. It never hurts anyone: it costs a touch, or a moment.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Rooster : HazardBase
    {
        public float minX = -2f, maxX = 2f;
        public float groundY;
        public float walkSpeed = 0.6f;
        [Tooltip("A ball this close, and coming at it faster than startleSpeed, sets it fluttering.")]
        public float noticeRange = 1.9f, startleSpeed = 2.4f;
        public float flutterHeight = 1.3f, flutterTime = 0.8f, flutterReach = 1.6f;
        public Vector2 bounceVelocity = new Vector2(-2f, 3.2f);
        public Transform visual;
        public float phaseOffset;

        float x, target, wait, time, flutterAt = -10f, flutterFrom, flutterTo, lastBump = -10f;
        Collider2D body;

        /// <summary>Up in the air (fluttering out of the way): the ball passes under it.</summary>
        public bool IsFluttering { get { return time - flutterAt < flutterTime; } }

        void Awake()
        {
            body = GetComponent<Collider2D>();
            body.isTrigger = true;
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            x = Mathf.Lerp(minX, maxX, Mathf.Repeat(phaseOffset * 0.37f, 1f));
            target = x;
            wait = 0.5f;
            flutterAt = -10f;
            Place(0f);
        }

        void Update()
        {
            if (!IsLive) return;
            float dt = Time.deltaTime;
            time += dt;
            // Far off screen it stays where it is (docs/LEARNINGS.md B8): nothing to see, nothing to write.
            var kid = Kid;
            if (kid != null && Mathf.Abs(kid.transform.position.x - x) > 24f && !IsFluttering) return;
            var ball = Ball;
            if (!IsFluttering && ball != null)
            {
                Vector2 to = (Vector2)transform.position - ball.Body.position;
                bool coming = Mathf.Sign(ball.Body.linearVelocity.x) == Mathf.Sign(to.x) && Mathf.Abs(ball.Body.linearVelocity.x) > startleSpeed;
                if (Mathf.Abs(to.x) < noticeRange && Mathf.Abs(to.y) < 1.2f && coming)
                {
                    // Up and away from the ball, along the street.
                    flutterAt = time;
                    flutterFrom = x;
                    flutterTo = Mathf.Clamp(x + Mathf.Sign(to.x) * flutterReach, minX - 1f, maxX + 1f);
                    GameEvents.Raise(GameEventType.PedestrianBump, transform.position, 0.4f);
                }
            }
            if (IsFluttering) x = Mathf.Lerp(flutterFrom, flutterTo, (time - flutterAt) / flutterTime);
            else
            {
                // Strut about the patch: a few steps, a peck or two, another spot.
                wait -= dt;
                if (wait <= 0f && Mathf.Abs(target - x) < 0.05f)
                {
                    target = Random.Range(minX, maxX);
                    wait = Random.Range(0.8f, 2.4f);
                }
                if (wait <= 0f) x = Mathf.MoveTowards(x, target, walkSpeed * dt);
            }
            Place(dt);
        }

        void Place(float dt)
        {
            float y = groundY;
            if (IsFluttering)
            {
                float k = (time - flutterAt) / flutterTime;
                y += Mathf.Sin(k * Mathf.PI) * flutterHeight;
            }
            transform.position = new Vector3(x, y, 0f);
            body.enabled = !IsFluttering;
            if (visual == null) return;
            // Facing the way it goes; a peck (head down and up) now and then while it stands; wings out while it flutters.
            float facing = IsFluttering ? Mathf.Sign(flutterTo - flutterFrom) : Mathf.Sign(target - x + 0.0001f);
            float peck = !IsFluttering && wait > 0f ? Mathf.Max(0f, Mathf.Sin(time * 7f)) * 25f : 0f;
            visual.localRotation = Quaternion.Euler(0f, facing >= 0f ? 90f : -90f, peck);
            visual.localScale = Vector3.one * (IsFluttering ? 1.15f : 1f);
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            BallController ball;
            if (!IsLive || IsFluttering || !TryGetBall(other, out ball) || time - lastBump < 0.5f) return;
            lastBump = time;
            float away = Mathf.Sign(ball.Body.position.x - transform.position.x);
            ball.Kick(new Vector2(away * Mathf.Abs(bounceVelocity.x), bounceVelocity.y));
            GameEvents.Raise(GameEventType.PedestrianBump, transform.position, 0.6f);
            // And it is off, the other way.
            flutterAt = time;
            flutterFrom = x;
            flutterTo = Mathf.Clamp(x - away * flutterReach, minX - 1f, maxX + 1f);
        }
    }
}
