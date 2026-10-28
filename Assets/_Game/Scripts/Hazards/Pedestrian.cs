using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Walks back and forth on the pavement, pausing now and then. The ball bounces
    /// off them (the kid slips past). Hit by the ball, they hop in surprise.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class Pedestrian : HazardBase
    {
        public float minX = -2f;
        public float maxX = 2f;
        public float walkSpeed = 1.1f;
        [Tooltip("Pause at each end of the walk.")]
        public float pauseTime = 0.8f;
        [Tooltip("Optional visual root that hops and turns around.")]
        public Transform visual;

        /// <summary>Raised when the ball bumps into this pedestrian.</summary>
        public event System.Action<Pedestrian> Bumped;

        Rigidbody2D body;
        Vector2 startPosition;
        int direction = 1;
        float pauseUntil;
        float hopTime = -10f;
        Vector3 visualBasePosition;
        float facing = 1f;

        public bool IsWalking { get { return Time.time >= pauseUntil; } }
        public int Direction { get { return direction; } }

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            startPosition = body.position;
            if (visual != null) visualBasePosition = visual.localPosition;
        }

        void Start()
        {
            // People only get in the ball's way; the kid slips past in front of them.
            var kid = Kid;
            if (kid == null) return;
            var own = GetComponentsInChildren<Collider2D>();
            foreach (var kc in kid.GetComponentsInChildren<Collider2D>())
                foreach (var c in own) Physics2D.IgnoreCollision(c, kc, true);
        }

        void FixedUpdate()
        {
            if (!IsWalking) return;
            Vector2 p = body.position;
            p.x += direction * walkSpeed * Time.fixedDeltaTime;
            if (p.x >= maxX || p.x <= minX)
            {
                p.x = Mathf.Clamp(p.x, minX, maxX);
                direction = -direction;
                pauseUntil = Time.time + pauseTime;
            }
            body.MovePosition(p);
        }

        void Update()
        {
            if (visual == null) return;
            // Face the walking direction (turning through facing the camera) and bob while
            // walking; hop when bumped.
            facing = Mathf.MoveTowards(facing, direction, Time.deltaTime * 4f);
            visual.localRotation = Quaternion.Euler(0f, Presentation.CharacterRig.FacingYaw(facing), 0f);
            float bob = IsWalking ? Mathf.Abs(Mathf.Sin(Time.time * walkSpeed * 6f)) * 0.04f : 0f;
            float hop = Mathf.Max(0f, Mathf.Sin(Mathf.Clamp01((Time.time - hopTime) / 0.35f) * Mathf.PI)) * 0.3f;
            visual.localPosition = visualBasePosition + Vector3.up * (bob + hop);
        }

        void OnCollisionEnter2D(Collision2D collision)
        {
            Ball.BallController ball;
            if (!TryGetBall(collision.collider, out ball)) return;
            hopTime = Time.time;
            pauseUntil = Time.time + pauseTime;
            Core.GameEvents.Raise(Core.GameEventType.PedestrianBump, transform.position, collision.relativeVelocity.magnitude / 10f);
            if (Bumped != null) Bumped(this);
        }

        public override void ResetState()
        {
            body.position = startPosition;
            transform.position = startPosition;
            direction = 1;
            facing = 1f;
            pauseUntil = 0f;
        }
    }
}
