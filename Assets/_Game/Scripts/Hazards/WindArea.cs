using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Pushes the ball (and a little the kid): sea breeze, tunnel draughts,
    /// fountain updrafts. Can gust on and off.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class WindArea : HazardBase
    {
        [Tooltip("Acceleration applied to the ball (world units/sec^2).")]
        public Vector2 ballAcceleration = new Vector2(-6f, 0f);
        [Range(0f, 1f)] public float kidFactor = 0.15f;
        [Tooltip("0 = steady. Otherwise seconds per on/off gust cycle.")]
        public float gustPeriod;
        [Range(0f, 1f)] public float gustOnFraction = 0.6f;
        [Tooltip("Optional streak visuals that drift with the wind.")]
        public Transform[] streaks;

        public bool IsBlowing { get; private set; }

        float time;
        Bounds area;

        void Awake()
        {
            var col = GetComponent<Collider2D>();
            col.isTrigger = true;
            area = col.bounds;
            IsBlowing = true;
        }

        public override void ResetState() { time = 0f; }

        void Update()
        {
            time += Time.deltaTime;
            IsBlowing = gustPeriod <= 0f || Mathf.Repeat(time, gustPeriod) < gustPeriod * gustOnFraction;

            if (streaks == null) return;
            Vector2 dir = ballAcceleration.normalized;
            float speed = Mathf.Clamp(ballAcceleration.magnitude, 2f, 12f);
            foreach (var s in streaks)
            {
                if (s == null) continue;
                var sr = s.GetComponent<SpriteRenderer>();
                if (sr != null) sr.enabled = IsBlowing;
                Vector3 p = s.position + (Vector3)(dir * speed * Time.deltaTime);
                // Wrap streaks around inside the area.
                if (p.x < area.min.x) p.x = area.max.x;
                if (p.x > area.max.x) p.x = area.min.x;
                if (p.y < area.min.y) p.y = area.max.y;
                if (p.y > area.max.y) p.y = area.min.y;
                s.position = p;
            }
        }

        void OnTriggerStay2D(Collider2D other)
        {
            if (!IsBlowing) return;
            Ball.BallController ball;
            Player.KidController kid;
            if (TryGetBall(other, out ball))
                ball.Body.AddForce(ballAcceleration * ball.Body.mass);
            else if (TryGetKid(other, out kid))
                kid.Body.AddForce(ballAcceleration * kid.Body.mass * kidFactor);
        }
    }
}
