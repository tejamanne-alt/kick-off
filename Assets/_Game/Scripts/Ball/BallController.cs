using System;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using DribbleToSchool.Tuning;
using UnityEngine;
using Random = UnityEngine.Random;

namespace DribbleToSchool.Ball
{
    /// <summary>
    /// A real physics ball that the kid dribbles.
    ///
    /// - Auto touch: when the kid catches up with the ball it gets a slightly
    ///   random nudge ahead, so the run keeps flowing without input.
    /// - Perfect touch: tapping while the ball is in the sweet spot just ahead of
    ///   the feet gives a clean, controlled touch and builds a streak.
    /// - Juggle: tapping while the ball is in the air near the kid pops it up.
    /// - Kick: driven by KickAimer through Kick().
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(CircleCollider2D))]
    public class BallController : MonoBehaviour
    {
        public BallTuning tuning;
        public KidController kid;

        /// <summary>Raised with the current perfect-touch streak.</summary>
        public event Action<int> PerfectTouch;
        /// <summary>Raised with the current juggle count.</summary>
        public event Action<int> Juggled;
        public event Action Kicked;
        /// <summary>Raised on impacts with the world: contact normal and 0..1 strength.</summary>
        public event Action<Vector2, float> Bounced;

        public Rigidbody2D Body { get; private set; }
        public CircleCollider2D Circle { get; private set; }
        public bool IsGrounded { get; private set; }
        public int PerfectStreak { get; private set; }
        public int JuggleCount { get; private set; }

        public float Radius { get { return Circle.radius * Mathf.Abs(transform.lossyScale.x); } }

        /// <summary>Where the ball's centre sits when it rests at the kid's feet.</summary>
        public Vector2 FootPoint { get { return kid.FeetPosition + Vector2.up * Radius; } }

        /// <summary>Ball position relative to the kid's foot point (+x = ahead).</summary>
        public Vector2 OffsetFromFeet { get { return Body.position - FootPoint; } }

        public bool InKickReach
        {
            get { return kid != null && OffsetFromFeet.magnitude <= tuning.kickReach; }
        }

        readonly RaycastHit2D[] groundHits = new RaycastHit2D[4];
        ContactFilter2D groundFilter;
        PhysicsMaterial2D runtimeMaterial;
        float nextTouchAllowedTime;

        void Awake()
        {
            Body = GetComponent<Rigidbody2D>();
            Circle = GetComponent<CircleCollider2D>();
            groundFilter = new ContactFilter2D();
            groundFilter.useTriggers = false;
            runtimeMaterial = new PhysicsMaterial2D("BallRuntime");
            ApplyTuning();
        }

        void Start()
        {
            // The kid never physically shoves the ball; touches are applied by code.
            if (kid != null)
            {
                foreach (var c in kid.GetComponentsInChildren<Collider2D>())
                    Physics2D.IgnoreCollision(Circle, c, true);
            }
        }

        /// <summary>Push tuning values onto the rigidbody and material. Safe to call at runtime.</summary>
        public void ApplyTuning()
        {
            Body.mass = tuning.mass;
            Body.gravityScale = tuning.gravityScale;
            Body.linearDamping = tuning.linearDamping;
            Body.angularDamping = tuning.angularDamping;
            Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            Body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;

            runtimeMaterial.bounciness = tuning.bounciness;
            runtimeMaterial.friction = tuning.friction;
            // Re-assign so the physics engine picks up the new values.
            Circle.sharedMaterial = null;
            Circle.sharedMaterial = runtimeMaterial;
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input != null && input.TouchPressed && kid != null && kid.InputEnabled)
                TryManualTouch();
        }

        void FixedUpdate()
        {
            CheckGround();

            if (IsGrounded)
            {
                JuggleCount = 0;
                Vector2 v = Body.linearVelocity;
                v.x *= Mathf.Clamp01(1f - tuning.rollingResistance * Time.fixedDeltaTime);
                Body.linearVelocity = v;
            }

            TryAutoTouch();
        }

        void CheckGround()
        {
            IsGrounded = false;
            float distance = Radius + 0.08f;
            int count = Physics2D.Raycast(Body.position, Vector2.down, groundFilter, groundHits, distance);
            for (int i = 0; i < count; i++)
            {
                Rigidbody2D rb = groundHits[i].rigidbody;
                if (rb == Body) continue;
                if (kid != null && rb == kid.Body) continue;
                IsGrounded = true;
                return;
            }
        }

        bool CanTouch { get { return kid != null && Time.time >= nextTouchAllowedTime; } }

        void TryAutoTouch()
        {
            if (!CanTouch || !kid.IsGrounded) return;
            // Hold the ball still under the finger while a kick is being lined up.
            if (GameInput.Instance != null && GameInput.Instance.KickAiming) return;

            Vector2 offset = OffsetFromFeet;
            if (offset.magnitude > tuning.reachRadius) return;
            if (offset.y > Radius * 2.5f) return; // too high: that's a juggle, not a dribble

            float kidSpeed = kid.SpeedX;

            if (kid.IsBraking && kidSpeed < tuning.trapSpeedThreshold)
            {
                // Kid is stopping: trap the ball under the foot instead of pushing it away.
                if (Mathf.Abs(Body.linearVelocity.x) > 0.3f && offset.x < tuning.autoTouchDistance + Radius)
                {
                    Vector2 v = Body.linearVelocity;
                    v.x *= tuning.trapDamping;
                    Body.linearVelocity = v;
                    Body.angularVelocity *= tuning.trapDamping;
                    nextTouchAllowedTime = Time.time + tuning.touchCooldown;
                    GameEvents.Raise(GameEventType.Trap, Body.position, 0.4f);
                }
                return;
            }

            if (offset.x > tuning.autoTouchDistance) return; // still comfortably ahead

            // The player missed the rhythm: the kid touches it anyway, a bit sloppily.
            float lead = tuning.dribbleLeadSpeed * Random.Range(1f - tuning.autoTouchVariance, 1f + tuning.autoTouchVariance);
            ApplyTouch(Mathf.Max(kidSpeed, 0f) + lead, tuning.touchLift);
            PerfectStreak = 0;
            GameEvents.Raise(GameEventType.Touch, Body.position, 0.5f);
        }

        void TryManualTouch()
        {
            if (!CanTouch) return;

            Vector2 offset = OffsetFromFeet;
            float kidSpeed = Mathf.Max(kid.SpeedX, 0f);

            bool airborneNearKid = !IsGrounded
                && Mathf.Abs(offset.x) <= tuning.juggleReachX
                && offset.y > Radius
                && offset.y <= tuning.juggleMaxHeight;

            if (airborneNearKid)
            {
                ApplyTouch(kidSpeed * tuning.juggleCarry, tuning.juggleUpSpeed);
                JuggleCount++;
                GameEvents.Raise(GameEventType.Juggle, Body.position, Mathf.Clamp01(JuggleCount / 10f));
                if (Juggled != null) Juggled(JuggleCount);
                return;
            }

            if (offset.magnitude > tuning.reachRadius) return;

            // Perfect = tapped in the sweet spot while the kid is catching up to the ball (the rhythm beat).
            bool closing = Body.linearVelocity.x < kid.SpeedX;
            bool perfect = closing && offset.x >= tuning.perfectTouchBand.x && offset.x <= tuning.perfectTouchBand.y;
            if (perfect)
            {
                ApplyTouch(kidSpeed + tuning.dribbleLeadSpeed, tuning.perfectTouchLift);
                PerfectStreak++;
                GameEvents.Raise(GameEventType.PerfectTouch, Body.position, Mathf.Clamp01(PerfectStreak / 8f));
                if (PerfectTouch != null) PerfectTouch(PerfectStreak);
            }
            else
            {
                float lead = tuning.dribbleLeadSpeed * Random.Range(1f - tuning.autoTouchVariance, 1f + tuning.autoTouchVariance);
                ApplyTouch(kidSpeed + lead, tuning.touchLift);
                PerfectStreak = 0;
                GameEvents.Raise(GameEventType.Touch, Body.position, 0.6f);
            }
        }

        void ApplyTouch(float speedX, float speedY)
        {
            Body.linearVelocity = new Vector2(speedX, speedY);
            // Roll naturally in the direction of travel (degrees per second).
            Body.angularVelocity = -speedX / Mathf.Max(Radius, 0.01f) * Mathf.Rad2Deg;
            nextTouchAllowedTime = Time.time + tuning.touchCooldown;
        }

        /// <summary>Kick the ball with an exact launch velocity (world units/sec).</summary>
        public void Kick(Vector2 velocity)
        {
            Body.linearVelocity = velocity;
            // A bit of backspin on lofted kicks, topspin on low drives.
            float loft = Mathf.Clamp01(velocity.y / Mathf.Max(velocity.magnitude, 0.01f));
            float spinDirection = Mathf.Sign(velocity.x) * (loft > 0.3f ? 1f : -1f);
            Body.angularVelocity = spinDirection * tuning.kickSpin * velocity.magnitude;
            nextTouchAllowedTime = Time.time + tuning.postKickNoTouchTime;
            PerfectStreak = 0;
            GameEvents.Raise(GameEventType.Kick, Body.position, velocity.magnitude / Mathf.Max(tuning.maxKickSpeed, 0.01f));
            if (Kicked != null) Kicked();
        }

        void OnCollisionEnter2D(Collision2D collision)
        {
            float speed = collision.relativeVelocity.magnitude;
            if (speed < 1.2f) return;
            Vector2 normal = collision.contactCount > 0 ? collision.GetContact(0).normal : Vector2.up;
            float strength = Mathf.Clamp01(speed / 12f);
            if (Bounced != null) Bounced(normal, strength);
            GameEvents.Raise(GameEventType.BallBounce, collision.contactCount > 0 ? collision.GetContact(0).point : Body.position, strength);
        }

        public void ResetTo(Vector2 position)
        {
            Body.position = position;
            transform.position = position;
            Body.linearVelocity = Vector2.zero;
            Body.angularVelocity = 0f;
            PerfectStreak = 0;
            JuggleCount = 0;
            nextTouchAllowedTime = 0f;
        }

        void OnDrawGizmosSelected()
        {
            if (kid == null || tuning == null) return;
            Vector3 foot = kid.feet != null ? kid.feet.position : kid.transform.position;
            Gizmos.color = new Color(1f, 1f, 0f, 0.6f);
            Gizmos.DrawWireSphere(foot, tuning.reachRadius);
            Gizmos.color = new Color(0f, 1f, 0f, 0.6f);
            Gizmos.DrawLine(foot + Vector3.right * tuning.perfectTouchBand.x, foot + Vector3.right * tuning.perfectTouchBand.y);
        }
    }
}
