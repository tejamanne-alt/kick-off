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
    /// - Auto touch: when the kid walks into the ball it gets a slightly random
    ///   nudge ahead (in whichever direction the kid is walking). The touch follows the
    ///   pace: at a walk a small one that keeps the ball within a stride, flat out the long
    ///   knock-on the kid chases (the stick's push sets the pace: GameInput.StickPace).
    /// - A foot on the ball: the stick let go with the ball at the feet, the kid holds it
    ///   still under the sole (riding along on moving ground). Pushing on carries on; pushing
    ///   the other way drags it back under the kid as they turn.
    /// - Close control: with KICK held (GameInput.BallControlHeld) the ball is kept a step
    ///   ahead, a little touch every stride, the kid a little slower; letting go kicks nothing.
    /// - Perfect touch: tapping while the ball is in the sweet spot just ahead of
    ///   the feet gives a clean, controlled touch and builds a streak.
    /// - Juggle: tapping while the ball is in the air near the kid pops it up.
    /// - Slide poke: a sliding kid nudges a ball at the feet on along the ground, with no
    ///   hop, so it rolls under the barrier too (and a perfect-touch streak survives it).
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
        /// <summary>True while the kid holds the ball still under a foot (the stick let go with the ball at the feet).</summary>
        public bool IsHeldUnderFoot { get; private set; }
        /// <summary>True while the kid keeps the ball at the feet with KICK held.</summary>
        public bool InCloseControl { get; private set; }

        /// <summary>How hard the kid is going over the ground they stand on: 0 standing, 1 flat out.</summary>
        public float Pace
        {
            get { return kid == null ? 1f : Mathf.Clamp01(Mathf.Abs(kid.SpeedX - kid.GroundVelocity.x) / Mathf.Max(0.1f, kid.RunSpeed)); }
        }

        /// <summary>How much faster than the kid a touch sends the ball: <paramref name="walkFraction"/> of the full lead at a walk, all of it flat out.</summary>
        public static float TouchLead(float fullLead, float walkFraction, float pace)
        {
            return fullLead * Mathf.Lerp(Mathf.Clamp01(walkFraction), 1f, Mathf.Clamp01(pace));
        }

        public float Radius { get { return Circle.radius * Mathf.Abs(transform.lossyScale.x); } }

        /// <summary>Where the ball's centre sits when it rests at the kid's feet.</summary>
        public Vector2 FootPoint { get { return kid.FeetPosition + Vector2.up * Radius; } }

        /// <summary>Ball position relative to the kid's foot point (+x = right).</summary>
        public Vector2 OffsetFromFeet { get { return Body.position - FootPoint; } }

        public bool InKickReach
        {
            get { return kid != null && OffsetFromFeet.magnitude <= tuning.kickReach; }
        }

        /// <summary>How far ahead of the feet a sliding kid's outstretched boot meets the ball.</summary>
        const float SlideBootReach = 0.6f;

        readonly RaycastHit2D[] groundHits = new RaycastHit2D[4];
        ContactFilter2D groundFilter;
        PhysicsMaterial2D runtimeMaterial;
        float nextTouchAllowedTime;
        float nextControlTouchTime;
        int holdDirection = 1;

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
            IgnoreKid();
            if (kid != null) kid.ShapeChanged += IgnoreKid;
        }

        void OnDestroy()
        {
            if (kid != null) kid.ShapeChanged -= IgnoreKid;
        }

        // A ball taken out of play lets go of the kid: full pace, no foot on it.
        void OnDisable()
        {
            IsHeldUnderFoot = false;
            InCloseControl = false;
            if (kid == null) return;
            kid.ControlPace = 1f;
            kid.FootOnBall = false;
        }

        /// <summary>Again whenever the kid's collider changes shape (sliding), to be sure it holds.</summary>
        void IgnoreKid()
        {
            if (kid == null) return;
            foreach (var c in kid.GetComponentsInChildren<Collider2D>())
                Physics2D.IgnoreCollision(Circle, c, true);
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

            // Held at the feet (a foot on it, or KICK held), else the usual touches.
            if (!HoldBall()) TryAutoTouch();
            if (kid != null)
            {
                // (eased, not switched: the ball coming in and out of reach must not jolt the kid's speed)
                kid.ControlPace = Mathf.MoveTowards(kid.ControlPace, InCloseControl ? tuning.controlSpeedFraction : 1f, Time.fixedDeltaTime * 2f);
                kid.FootOnBall = IsHeldUnderFoot && holdDirection == kid.Facing;
            }
        }

        /// <summary>
        /// Keeps the ball at the kid's feet while they hold it, instead of the usual touches; false while it is free.
        /// - Close control (KICK held, the ball in reach): it is kept a step ahead of the feet (nearer at a walk) with a little
        ///   touch every stride, and the kid runs a little slower (KidController.ControlPace); turning, it comes round the
        ///   feet with them. Stopped with KICK held, a foot goes on it.
        /// - A foot on the ball (the stick let go with the ball at the feet): it stays put under the sole, riding along on
        ///   moving ground. Pushing the stick on carries on dribbling (the first touch is a small one: the kid is slow yet);
        ///   pushing it the other way drags the ball back under the kid as they turn.
        /// The ball stays a physics ball: a hold only steers its speed, so a hard knock still takes it away, and nothing holds
        /// it for a moment after a kick (a dog's steal is a kick too, so KICK held never wrestles the dog for it).
        /// </summary>
        bool HoldBall()
        {
            InCloseControl = false;
            var input = GameInput.Instance;
            if (kid == null || !kid.InputEnabled || !CanTouch || !kid.IsGrounded || kid.IsLow || (input != null && input.KickAiming))
            {
                IsHeldUnderFoot = false;
                return false;
            }

            Vector2 offset = OffsetFromFeet;
            float groundVx = kid.GroundVelocity.x;
            bool low = offset.y < Radius * 2.5f;
            bool stopped = kid.IsBraking && Mathf.Abs(kid.SpeedX - groundVx) < tuning.trapSpeedThreshold;

            // Close control: KICK held with the ball in reach.
            if (input != null && input.BallControlHeld && low && offset.magnitude <= tuning.reachRadius)
            {
                InCloseControl = true;
                if (stopped)
                {
                    if (!IsHeldUnderFoot) holdDirection = kid.Facing;
                    IsHeldUnderFoot = true;
                    Steer(FootPoint.x + holdDirection * tuning.soleHoldOffset, groundVx, groundVx);
                    return true;
                }
                IsHeldUnderFoot = false;
                float pace = Pace;
                float lead = Mathf.Lerp(tuning.controlLead.x, tuning.controlLead.y, pace);
                Steer(FootPoint.x + kid.Facing * lead, kid.SpeedX, groundVx);
                // A little touch every stride: the leg swings and the ball taps.
                if (Time.time >= nextControlTouchTime && pace > 0.1f)
                {
                    nextControlTouchTime = Time.time + Mathf.Lerp(tuning.controlTouchInterval.x, tuning.controlTouchInterval.y, pace);
                    GameEvents.Raise(GameEventType.Touch, Body.position, 0.3f);
                }
                return true;
            }

            // A foot on the ball.
            if (IsHeldUnderFoot)
            {
                if (!low || offset.magnitude > tuning.reachRadius)
                {
                    IsHeldUnderFoot = false;     // knocked out from under the foot
                    return false;
                }
                if (kid.IsBraking)
                {
                    Steer(FootPoint.x + holdDirection * tuning.soleHoldOffset, groundVx, groundVx);
                    return true;
                }
                IsHeldUnderFoot = false;
                int way = kid.MoveAxis > 0f ? 1 : -1;
                if (way == holdDirection) return false;   // carry on dribbling
                // A drag-back: the sole rolls the ball back under the kid as they turn, out in front the new way.
                ApplyTouch(groundVx + way * tuning.dragBackSpeed, 0f);
                GameEvents.Raise(GameEventType.Touch, Body.position, 0.4f);
                return true;
            }

            // Stopping with the ball at the feet puts a foot on it (on whichever side of the feet it is).
            if (stopped && low && Mathf.Abs(offset.x) < tuning.autoTouchDistance + Radius)
            {
                holdDirection = offset.x * kid.Facing >= 0f ? kid.Facing : -kid.Facing;
                IsHeldUnderFoot = true;
                if (Mathf.Abs(Body.linearVelocity.x - groundVx) > 0.3f) GameEvents.Raise(GameEventType.Trap, Body.position, 0.4f);
                Steer(FootPoint.x + holdDirection * tuning.soleHoldOffset, groundVx, groundVx);
                return true;
            }
            return false;
        }

        /// <summary>
        /// Steers the ball's speed (never its position: it stays a physics ball) toward a spot by the feet, moving at
        /// <paramref name="baseVx"/>, rolling at its speed over the ground (<paramref name="groundVx"/>).
        /// </summary>
        void Steer(float targetX, float baseVx, float groundVx)
        {
            float pull = Mathf.Clamp((targetX - Body.position.x) * tuning.holdSpring, -tuning.holdMaxPull, tuning.holdMaxPull);
            float grip = 1f - Mathf.Exp(-tuning.holdGrip * Time.fixedDeltaTime);
            Vector2 v = Body.linearVelocity;
            v.x = Mathf.Lerp(v.x, baseVx + pull, grip);
            Body.linearVelocity = v;
            float roll = -(v.x - groundVx) / Mathf.Max(Radius, 0.01f) * Mathf.Rad2Deg;
            Body.angularVelocity = Mathf.Lerp(Body.angularVelocity, roll, grip);
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

            // Work along the direction the kid faces, so dribbling back works the same as forward.
            int dir = kid.Facing;
            float ahead = offset.x * dir;
            float kidSpeed = kid.SpeedX * dir;

            // A stopping kid doesn't push the ball on (with it at the feet, HoldBall has put a foot on it).
            if (kid.IsBraking && Mathf.Abs(kid.SpeedX - kid.GroundVelocity.x) < tuning.trapSpeedThreshold) return;

            if (kidSpeed < 0.5f) return;                     // not walking into the ball
            if (ahead < -Radius * 1.5f) return;               // behind the kid: walking away from it

            if (kid.IsLow)
            {
                // Sliding (or shuffling under a barrier): the outstretched boot, well ahead of the
                // hips, nudges the ball on along the ground with no hop, so it rolls under too.
                if (ahead > SlideBootReach) return;
                ApplyTouch(dir * (kidSpeed + tuning.dribbleLeadSpeed * 0.5f), 0f);
                GameEvents.Raise(GameEventType.Touch, Body.position, 0.4f);
                return;
            }
            if (ahead > tuning.autoTouchDistance) return;     // still comfortably ahead

            // The player missed the rhythm: the kid touches it anyway, a bit sloppily. The touch follows the pace: at a
            // walk a small one that keeps the ball within a stride, flat out the long knock-on.
            float pace = Pace;
            float lead = TouchLead(tuning.dribbleLeadSpeed, tuning.walkLeadFraction, pace) * Random.Range(1f - tuning.autoTouchVariance, 1f + tuning.autoTouchVariance);
            ApplyTouch(dir * (kidSpeed + lead), Mathf.Lerp(tuning.walkTouchLift, tuning.touchLift, pace));
            PerfectStreak = 0;
            GameEvents.Raise(GameEventType.Touch, Body.position, 0.5f);
        }

        void TryManualTouch()
        {
            if (!CanTouch) return;

            Vector2 offset = OffsetFromFeet;
            int dir = kid.Facing;
            float ahead = offset.x * dir;
            float kidSpeed = Mathf.Max(kid.SpeedX * dir, 0f);

            bool airborneNearKid = !IsGrounded
                && Mathf.Abs(offset.x) <= tuning.juggleReachX
                && offset.y > Radius
                && offset.y <= tuning.juggleMaxHeight;

            if (airborneNearKid)
            {
                ApplyTouch(kid.SpeedX * tuning.juggleCarry, tuning.juggleUpSpeed);
                JuggleCount++;
                GameEvents.Raise(GameEventType.Juggle, Body.position, Mathf.Clamp01(JuggleCount / 10f));
                if (Juggled != null) Juggled(JuggleCount);
                return;
            }

            if (offset.magnitude > tuning.reachRadius) return;

            // Perfect = tapped in the sweet spot while the kid is catching up to the ball (the rhythm beat).
            bool closing = kidSpeed > 0.5f && Body.linearVelocity.x * dir < kidSpeed;
            bool perfect = closing && ahead >= tuning.perfectTouchBand.x && ahead <= tuning.perfectTouchBand.y;
            float pace = Pace;
            if (perfect)
            {
                ApplyTouch(dir * (kidSpeed + TouchLead(tuning.dribbleLeadSpeed, tuning.walkLeadFraction, pace)),
                    Mathf.Lerp(Mathf.Min(tuning.walkTouchLift, tuning.perfectTouchLift), tuning.perfectTouchLift, pace));
                PerfectStreak++;
                GameEvents.Raise(GameEventType.PerfectTouch, Body.position, Mathf.Clamp01(PerfectStreak / 8f));
                if (PerfectTouch != null) PerfectTouch(PerfectStreak);
            }
            else
            {
                float lead = TouchLead(tuning.dribbleLeadSpeed, tuning.walkLeadFraction, pace) * Random.Range(1f - tuning.autoTouchVariance, 1f + tuning.autoTouchVariance);
                ApplyTouch(dir * (kidSpeed + lead), Mathf.Lerp(tuning.walkTouchLift, tuning.touchLift, pace));
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
            IsHeldUnderFoot = false;
            InCloseControl = false;
            Body.linearVelocity = velocity;
            kid.FaceTowards(velocity.x);
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
            var trail = GetComponent<TrailRenderer>();
            if (trail != null) trail.Clear();
            PerfectStreak = 0;
            JuggleCount = 0;
            nextTouchAllowedTime = 0f;
            IsHeldUnderFoot = false;
            InCloseControl = false;
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
