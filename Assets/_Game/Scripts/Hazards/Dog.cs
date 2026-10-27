using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A playful dog that wanders its patch and chases a low ball, nosing it back
    /// toward the kid. Chip the ball over its head! It never hurts anyone.
    /// </summary>
    public class Dog : HazardBase
    {
        public float minX = -3f;
        public float maxX = 3f;
        public float wanderSpeed = 1f;
        public float chaseSpeed = 4.5f;
        [Tooltip("How far the dog notices the ball.")]
        public float noticeRange = 4f;
        [Tooltip("Only chases a ball lower than this above the dog's feet.")]
        public float maxBallHeight = 1f;
        public float stealDistance = 0.55f;
        public Vector2 stealVelocity = new Vector2(-4.5f, 3.5f);
        public float stealCooldown = 1.2f;
        public Transform visual;

        public bool IsChasing { get; private set; }
        public event System.Action<Dog> StoleBall;

        Vector3 startPosition;
        int direction = 1;
        float nextStealTime;
        Vector3 visualBaseScale = Vector3.one;

        void Awake()
        {
            startPosition = transform.position;
            if (visual != null) visualBaseScale = visual.localScale;
        }

        public override void ResetState()
        {
            transform.position = startPosition;
            direction = 1;
            IsChasing = false;
            nextStealTime = 0f;
        }

        void Update()
        {
            if (Level == null || Level.State == Core.LevelState.Paused) return;
            var ball = Ball;
            Vector3 p = transform.position;

            IsChasing = false;
            if (ball != null && Time.time >= nextStealTime)
            {
                Vector2 b = ball.transform.position;
                bool low = b.y - p.y <= maxBallHeight;
                bool inPatch = b.x >= minX - 1f && b.x <= maxX + 1f;
                if (low && inPatch && Mathf.Abs(b.x - p.x) <= noticeRange)
                {
                    IsChasing = true;
                    direction = b.x > p.x ? 1 : -1;
                    p.x = Mathf.MoveTowards(p.x, Mathf.Clamp(b.x, minX, maxX), chaseSpeed * Time.deltaTime);
                    if (Mathf.Abs(b.x - p.x) <= stealDistance && IsLive) Steal(ball);
                }
            }

            if (!IsChasing)
            {
                p.x += direction * wanderSpeed * Time.deltaTime;
                if (p.x >= maxX || p.x <= minX)
                {
                    p.x = Mathf.Clamp(p.x, minX, maxX);
                    direction = -direction;
                }
            }

            transform.position = p;

            if (visual != null)
            {
                Vector3 s = visualBaseScale;
                s.x = Mathf.Abs(s.x) * direction;
                float speed = IsChasing ? chaseSpeed : wanderSpeed;
                s.y = visualBaseScale.y * (1f + Mathf.Sin(Time.time * speed * 5f) * 0.05f);
                visual.localScale = s;
            }
        }

        void Steal(Ball.BallController ball)
        {
            nextStealTime = Time.time + stealCooldown;
            Vector2 v = stealVelocity;
            // Always nose it back toward the kid.
            var kid = Kid;
            if (kid != null && kid.transform.position.x > transform.position.x) v.x = Mathf.Abs(v.x);
            else v.x = -Mathf.Abs(v.x);
            ball.Kick(v);
            Core.GameEvents.Raise(Core.GameEventType.DogSteal, transform.position);
            if (StoleBall != null) StoleBall(this);
        }
    }
}
