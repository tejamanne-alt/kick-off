using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// The ball of a Holiday Run. The kid runs by itself, so the ball can't be dribbled by hand: it is
    /// carried along just ahead of the feet, hopping with the stride, and a press of KICK shoots it
    /// forward to smash crates and targets (bouncing off anything else), after which it comes
    /// back to the feet. The scene's BallController is switched off; this drives its body.
    /// While carried the ball is a trigger (coins and pick-ups still count when it touches them, and
    /// it can never be knocked into a pit); in flight it is solid.
    /// </summary>
    public class EndlessBall : MonoBehaviour
    {
        public BallController ball;
        public KidController kid;

        [Header("Dribble")]
        [Tooltip("How far ahead of the feet the ball rolls (metres), at its nearest and furthest.")]
        public Vector2 lead = new Vector2(0.5f, 0.95f);
        [Tooltip("How high it hops off the ground with each stride (metres).")]
        public float hop = 0.14f;
        [Tooltip("How quickly it follows the kid (1/seconds).")]
        public float follow = 30f;

        [Header("Kick")]
        public float kickSpeed = 15f;
        public float kickLift = 2.6f;
        [Tooltip("Longest a shot flies before it is called back (seconds).")]
        public float flightTime = 1.15f;
        public float recallTime = 0.3f;
        public float cooldown = 0.35f;

        enum Mode { Dribble, Flight, Recall }

        Mode mode = Mode.Dribble;
        Rigidbody2D body;
        CircleCollider2D circle;
        float stride, flightLeft, recallElapsed, nextKickTime;
        Vector2 recallFrom, lastVelocity;
        bool wasKickHeld;

        /// <summary>The ball is at the feet and a press of KICK will shoot it.</summary>
        public bool Ready { get { return mode == Mode.Dribble && Time.time >= nextKickTime; } }

        float Radius { get { return circle != null ? circle.radius * Mathf.Abs(transform.lossyScale.x) : LevelRadius; } }
        const float LevelRadius = 0.17f;

        void Awake()
        {
            if (ball == null) ball = GetComponent<BallController>();
            body = GetComponent<Rigidbody2D>();
            circle = GetComponent<CircleCollider2D>();
            // BallController would dribble by itself and lose the ball in a pit: this takes over.
            if (ball != null) ball.enabled = false;
            Carry(true);
        }

        void Start()
        {
            // The kid never physically shoves the ball (BallController sees to that in the levels; here it is off).
            IgnoreKid();
            if (kid != null) kid.ShapeChanged += IgnoreKid;
        }

        void OnDestroy()
        {
            if (kid != null) kid.ShapeChanged -= IgnoreKid;
        }

        /// <summary>Again whenever the kid's collider changes shape (sliding), to be sure it holds.</summary>
        void IgnoreKid()
        {
            if (kid == null || circle == null) return;
            foreach (var c in kid.GetComponentsInChildren<Collider2D>())
                Physics2D.IgnoreCollision(circle, c, true);
        }

        void Update()
        {
            if (kid == null || body == null) return;
            // Frozen with the kid while the world under them loads.
            if (kid.Body != null && body.simulated != kid.Body.simulated) body.simulated = kid.Body.simulated;

            var input = GameInput.Instance;
            bool held = input != null && input.KickHeld;
            bool pressed = (held && !wasKickHeld) || (input != null && input.KickTapped);
            wasKickHeld = held;
            if (pressed && Ready && kid.InputEnabled) Shoot();
        }

        void FixedUpdate()
        {
            if (kid == null || body == null || !body.simulated) return;
            switch (mode)
            {
                case Mode.Dribble: Dribble(Time.fixedDeltaTime); break;
                case Mode.Flight: Fly(Time.fixedDeltaTime); break;
                case Mode.Recall: Recall(Time.fixedDeltaTime); break;
            }
        }

        /// <summary>Where the ball sits in the dribble: ahead of the feet, hopping once a stride.</summary>
        Vector2 DribbleSpot()
        {
            float phase = Mathf.Repeat(stride, Mathf.PI * 2f);
            float ahead = Mathf.Lerp(lead.x, lead.y, 0.5f + 0.5f * Mathf.Sin(phase));
            float up = hop * Mathf.Max(0f, Mathf.Sin(phase * 2f + 1.2f));
            Vector2 feet = kid.FeetPosition;
            return new Vector2(feet.x + ahead * kid.Facing, feet.y + Radius + up);
        }

        void Dribble(float dt)
        {
            stride += Mathf.Abs(kid.SpeedX) * dt * 1.9f * Mathf.PI * 0.5f;
            Vector2 target = DribbleSpot();
            Vector2 p = Vector2.Lerp(body.position, target, 1f - Mathf.Exp(-follow * dt));
            body.position = p;
            body.linearVelocity = Vector2.zero;
            body.angularVelocity = -kid.SpeedX / Mathf.Max(Radius, 0.05f) * Mathf.Rad2Deg;
        }

        void Shoot()
        {
            Carry(false);
            mode = Mode.Flight;
            flightLeft = flightTime;
            nextKickTime = Time.time + cooldown;
            Vector2 v = new Vector2(Mathf.Max(kickSpeed, kid.SpeedX + kickSpeed * 0.7f) * kid.Facing, kickLift);
            body.linearVelocity = v;
            lastVelocity = v;
            body.angularVelocity = -v.x / Mathf.Max(Radius, 0.05f) * Mathf.Rad2Deg;
            GameEvents.Raise(GameEventType.Kick, body.position, 0.8f);
        }

        void Fly(float dt)
        {
            flightLeft -= dt;
            lastVelocity = body.linearVelocity;
            float behind = kid.transform.position.x - body.position.x;
            // Called back when its time is up, when it has dropped toward a pit (never into one), or when
            // the kid has run past it.
            if (flightLeft <= 0f || body.position.y < -0.45f || behind > 2.5f) BeginRecall();
        }

        void BeginRecall()
        {
            mode = Mode.Recall;
            recallElapsed = 0f;
            recallFrom = body.position;
            Carry(true);
        }

        void Recall(float dt)
        {
            recallElapsed += dt;
            float t = Mathf.Clamp01(recallElapsed / Mathf.Max(0.05f, recallTime));
            Vector2 target = DribbleSpot();
            // A little arc up on the way back, then settle into the dribble.
            Vector2 p = Vector2.Lerp(recallFrom, target, t * t * (3f - 2f * t));
            p.y += Mathf.Sin(t * Mathf.PI) * 0.5f;
            body.position = p;
            body.linearVelocity = Vector2.zero;
            if (t >= 1f) mode = Mode.Dribble;
        }

        /// <summary>Carried: a trigger with no gravity. Free: solid, falling.</summary>
        void Carry(bool carried)
        {
            if (circle != null) circle.isTrigger = carried;
            if (body == null) return;
            body.gravityScale = carried ? 0f : (ball != null && ball.tuning != null ? ball.tuning.gravityScale : 3f);
            if (carried) body.linearVelocity = Vector2.zero;
        }

        /// <summary>Back at the kid's feet (a restart, a revive, a new day).</summary>
        public void ResetAt(Vector3 kidPosition)
        {
            if (body == null) body = GetComponent<Rigidbody2D>();
            mode = Mode.Dribble;
            Carry(true);
            Vector2 spot = new Vector2(kidPosition.x + lead.x, kidPosition.y - 0.6f + Radius);
            body.position = spot;
            transform.position = spot;
            body.linearVelocity = Vector2.zero;
            body.angularVelocity = 0f;
            var trail = GetComponent<TrailRenderer>();
            if (trail != null) trail.Clear();
            nextKickTime = 0f;
        }

        void OnCollisionEnter2D(Collision2D collision)
        {
            if (mode != Mode.Flight) return;
            var crate = collision.collider != null ? collision.collider.GetComponentInParent<RunBreakable>() : null;
            if (crate == null || crate.Smashed) return;
            Vector2 point = collision.contactCount > 0 ? collision.GetContact(0).point : body.position;
            crate.Smash(point);
            // The shot goes on through the burst with most of its speed.
            body.linearVelocity = lastVelocity * 0.85f;
        }
    }
}
