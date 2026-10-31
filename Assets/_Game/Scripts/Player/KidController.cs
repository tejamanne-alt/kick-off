using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Tuning;
using UnityEngine;

namespace DribbleToSchool.Player
{
    /// <summary>
    /// The kid walks back and forth with the arrow buttons and jumps (once more in the air: a
    /// double jump), and slides feet first along the ground, low enough to pass under barriers;
    /// the ball is never carried, it is dribbled (see BallController).
    /// </summary>
    /// <remarks>
    /// While sliding, the capsule shrinks to <see cref="PlayerTuning.slideHeight"/> with its bottom
    /// where the feet are, so the kid never sinks into the ground or pops up. It only grows back
    /// once the space a standing kid takes is clear: until then the kid stays low and shuffles on.
    /// </remarks>
    [RequireComponent(typeof(Rigidbody2D))]
    public class KidController : MonoBehaviour
    {
        public PlayerTuning tuning;
        [Tooltip("Point at the bottom of the kid's collider. Used for ground checks and dribbling.")]
        public Transform feet;
        public Vector2 groundCheckSize = new Vector2(0.4f, 0.1f);

        public Rigidbody2D Body { get; private set; }
        public bool IsGrounded { get; private set; }
        /// <summary>No move input: the kid stops and traps a ball rolling at the feet.</summary>
        public bool IsBraking { get; private set; }
        /// <summary>-1..1 move input this frame.</summary>
        public float MoveAxis { get; private set; }
        /// <summary>+1 facing forward (right), -1 facing back (left).</summary>
        public int Facing { get; private set; }
        public bool InputEnabled { get; set; }
        public float SpeedX { get { return Body.linearVelocity.x; } }
        public Vector2 FeetPosition { get { return feet != null ? (Vector2)feet.position : Body.position; } }
        /// <summary>Product of all active speed modifiers (puddles, sand...).</summary>
        public float SpeedMultiplier { get; private set; }
        /// <summary>Velocity of the moving surface under the kid, if any.</summary>
        public Vector2 GroundVelocity { get; private set; }
        /// <summary>In the slide itself: fast and low, feet first.</summary>
        public bool IsSliding { get; private set; }
        /// <summary>The collider is low: sliding, or still under something after the slide.</summary>
        public bool IsLow { get; private set; }
        /// <summary>Air jumps left before the kid lands again.</summary>
        public int AirJumpsLeft { get { return Mathf.Max(0, tuning.airJumps - airJumpsUsed); } }
        /// <summary>Raised when the kid lands, with the downward speed at impact.</summary>
        public event System.Action<float> Landed;
        /// <summary>Raised when the kid leaves the ground by jumping.</summary>
        public event System.Action Jumped;
        /// <summary>Raised when the kid jumps again in the air.</summary>
        public event System.Action DoubleJumped;
        /// <summary>Raised when a slide starts.</summary>
        public event System.Action Slid;
        /// <summary>Raised after the collider changes shape (into a slide and back up), for anything that set up ignored collisions with it.</summary>
        public event System.Action ShapeChanged;

        readonly Collider2D[] groundHits = new Collider2D[8];
        readonly Collider2D[] roomHits = new Collider2D[8];
        readonly RaycastHit2D[] landingHits = new RaycastHit2D[8];
        ContactFilter2D groundFilter;
        float lastGroundedTime = -10f;
        float lastJumpPressedTime = -10f;
        float lastSlidePressedTime = -10f;
        bool jumping;
        bool wasGrounded;
        float lastFallSpeed;
        int airJumpsUsed;
        float slideStartTime = -10f;
        float slideEndTime = -10f;
        float slideSpeed;
        int slideDirection = 1;
        CapsuleCollider2D capsule;
        Vector2 standSize, standOffset;
        CapsuleDirection2D standDirection;
        readonly List<object> speedModifierOwners = new List<object>();
        readonly List<float> speedModifierValues = new List<float>();

        void Awake()
        {
            Body = GetComponent<Rigidbody2D>();
            InputEnabled = true;
            SpeedMultiplier = 1f;
            Facing = 1;
            groundFilter = new ContactFilter2D();
            groundFilter.useTriggers = false;
            capsule = GetComponent<CapsuleCollider2D>();
            if (capsule != null)
            {
                standSize = capsule.size;
                standOffset = capsule.offset;
                standDirection = capsule.direction;
            }
            ApplyTuning();
        }

        /// <summary>Push tuning values onto the rigidbody. Safe to call at runtime.</summary>
        public void ApplyTuning()
        {
            Body.gravityScale = tuning.gravityScale;
            Body.freezeRotation = true;
            Body.interpolation = RigidbodyInterpolation2D.Interpolate;
            Body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input == null || !InputEnabled)
            {
                IsBraking = false;
                MoveAxis = 0f;
                return;
            }

            MoveAxis = input.MoveAxis;
            IsBraking = Mathf.Approximately(MoveAxis, 0f);
            // A slide holds its line; the kid turns once back on their feet.
            if (!IsSliding)
            {
                if (MoveAxis > 0.1f) Facing = 1;
                else if (MoveAxis < -0.1f) Facing = -1;
            }
            if (input.JumpPressed) lastJumpPressedTime = Time.time;
            if (input.SlidePressed) lastSlidePressedTime = Time.time;

            // Variable jump height: letting go early cuts the rise short (the air jump too).
            if (jumping && !input.JumpHeld && Body.linearVelocity.y > 0f)
            {
                Vector2 v = Body.linearVelocity;
                v.y *= tuning.jumpCutMultiplier;
                Body.linearVelocity = v;
                jumping = false;
            }
        }

        void FixedUpdate()
        {
            CheckGround();
            if (IsGrounded) lastGroundedTime = Time.time;
            if (IsGrounded && !wasGrounded)
            {
                if (Landed != null) Landed(lastFallSpeed);
                if (lastFallSpeed > 2f) GameEvents.Raise(GameEventType.Land, FeetPosition, lastFallSpeed / 15f);
            }
            wasGrounded = IsGrounded;

            Vector2 v = Body.linearVelocity;
            if (!IsGrounded) lastFallSpeed = Mathf.Max(0f, -v.y);
            // Back on the ground (not just leaving it, nor riding a lift up): the air jump is back.
            if (IsGrounded && v.y <= Mathf.Max(0f, GroundVelocity.y) + 0.01f) airJumpsUsed = 0;

            bool canJump = Time.time - lastGroundedTime <= tuning.coyoteTime;
            bool wantsJump = Time.time - lastJumpPressedTime <= tuning.jumpBufferTime;
            bool wantsSlide = Time.time - lastSlidePressedTime <= tuning.slideBufferTime;

            // A jump that can happen right now wins over a slide pressed at the same moment.
            if (InputEnabled && wantsSlide && !(wantsJump && canJump) && CanStartSlide())
                StartSlide(v);
            UpdateSlide();

            if (IsSliding)
            {
                // Feet first along the ground, losing speed to friction; pushing back brakes harder.
                bool against = MoveAxis * slideDirection < -0.1f;
                float friction = tuning.slideFriction * (against ? 2.5f : 1f);
                slideSpeed = Mathf.Max(tuning.slideMinSpeed * SpeedMultiplier, slideSpeed - friction * Time.fixedDeltaTime);
                v.x = slideDirection * slideSpeed + GroundVelocity.x;
            }
            else if (IsLow && IsGrounded)
            {
                // Something overhead: shuffle on low, the way the arrows say (or on along the slide).
                float dir = Mathf.Abs(MoveAxis) > 0.1f ? Mathf.Sign(MoveAxis) : slideDirection;
                if (!InputEnabled) dir = 0f;
                if (dir != 0f) Facing = dir > 0f ? 1 : -1;
                float target = dir * tuning.slideMinSpeed * SpeedMultiplier + GroundVelocity.x;
                v.x = Mathf.MoveTowards(v.x, target, tuning.acceleration * Time.fixedDeltaTime);
            }
            else
            {
                float target = InputEnabled ? MoveAxis * tuning.runSpeed * SpeedMultiplier : 0f;
                target += GroundVelocity.x;
                float rate = Mathf.Abs(target) > Mathf.Abs(v.x) ? tuning.acceleration : tuning.deceleration;
                if (!IsGrounded) rate *= tuning.airControl;
                v.x = Mathf.MoveTowards(v.x, target, rate * Time.fixedDeltaTime);
            }

            // Jumping from low (out of a slide) needs room to stand up first.
            bool room = !wantsJump || !IsLow || HeadroomClear();
            if (InputEnabled && canJump && wantsJump && room)
            {
                StandUp();
                v.y = tuning.jumpVelocity + Mathf.Max(0f, GroundVelocity.y);
                jumping = true;
                lastJumpPressedTime = -10f;
                lastGroundedTime = -10f;
                if (Jumped != null) Jumped();
                GameEvents.Raise(GameEventType.Jump, FeetPosition, 0.5f);
            }
            else if (InputEnabled && wantsJump && room && CanAirJump(v.y))
            {
                StandUp();
                v.y = tuning.airJumpVelocity;
                jumping = true;
                airJumpsUsed++;
                lastJumpPressedTime = -10f;
                if (DoubleJumped != null) DoubleJumped();
                GameEvents.Raise(GameEventType.DoubleJump, FeetPosition, 0.6f);
            }
            else if (IsGrounded && v.y <= 0.01f)
            {
                jumping = false;
            }

            Body.gravityScale = v.y < 0f ? tuning.gravityScale * tuning.fallGravityMultiplier : tuning.gravityScale;
            if (v.y < -tuning.maxFallSpeed) v.y = -tuning.maxFallSpeed;

            Body.linearVelocity = v;
        }

        void CheckGround()
        {
            IsGrounded = false;
            GroundVelocity = Vector2.zero;
            int count = Physics2D.OverlapBox(FeetPosition, groundCheckSize, 0f, groundFilter, groundHits);
            for (int i = 0; i < count; i++)
            {
                Collider2D hit = groundHits[i];
                if (!IsSolidToKid(hit)) continue;
                IsGrounded = true;
                var surface = hit.GetComponentInParent<IMovingSurface>();
                if (surface != null) GroundVelocity = surface.SurfaceVelocity;
                return;
            }
        }

        /// <summary>
        /// Something the kid's body actually bumps into: not the kid, not the ball (touches are
        /// applied by code), and not anything that ignores the kid (people the kid slips past).
        /// </summary>
        bool IsSolidToKid(Collider2D hit)
        {
            if (hit == null || hit.attachedRigidbody == Body) return false;
            if (hit.attachedRigidbody != null && hit.attachedRigidbody.GetComponent<BallController>() != null) return false;
            if (capsule != null && Physics2D.GetIgnoreCollision(capsule, hit)) return false;
            if (Physics2D.GetIgnoreLayerCollision(gameObject.layer, hit.gameObject.layer)) return false;
            return true;
        }

        // ---------- Double jump ----------

        /// <summary>
        /// One more jump in the air, once the coyote time for a ground jump is over. It waits while
        /// the kid is still rising faster than it would launch (so it always adds height), and while
        /// the ground is close enough below to land within the jump buffer: that press becomes an
        /// ordinary jump on landing instead of using up the air jump.
        /// </summary>
        bool CanAirJump(float vy)
        {
            if (IsGrounded || airJumpsUsed >= tuning.airJumps) return false;
            if (vy >= tuning.airJumpVelocity) return false;
            float window = tuning.jumpBufferTime - (Time.time - lastJumpPressedTime);
            return !LandingWithin(vy, window);
        }

        bool LandingWithin(float vy, float seconds)
        {
            if (vy > 0f || seconds <= 0f) return false;
            float g = -Physics2D.gravity.y * tuning.gravityScale * tuning.fallGravityMultiplier;
            float distance = -vy * seconds + 0.5f * g * seconds * seconds;
            int count = Physics2D.BoxCast(FeetPosition, groundCheckSize, 0f, Vector2.down, groundFilter, landingHits, distance);
            for (int i = 0; i < count; i++)
            {
                var hit = landingHits[i];
                if (hit.distance <= 0f || hit.normal.y < 0.5f) continue;   // started inside it, or a wall
                if (IsSolidToKid(hit.collider)) return true;
            }
            return false;
        }

        // ---------- Slide ----------

        bool CanStartSlide()
        {
            return IsGrounded && !IsSliding && Time.time - slideEndTime >= tuning.slideCooldown;
        }

        void StartSlide(Vector2 v)
        {
            lastSlidePressedTime = -10f;
            float relative = v.x - GroundVelocity.x;
            // The way the arrows point, else the way the kid is already going, else the way they face.
            if (Mathf.Abs(MoveAxis) > 0.1f) slideDirection = MoveAxis > 0f ? 1 : -1;
            else if (Mathf.Abs(relative) > 0.5f) slideDirection = relative > 0f ? 1 : -1;
            else slideDirection = Facing;
            Facing = slideDirection;
            // Keep the run's speed and add a little: a slide is a lunge, never a brake.
            float along = Mathf.Max(0f, relative * slideDirection);
            slideSpeed = Mathf.Max(along, tuning.runSpeed * SpeedMultiplier) * tuning.slideSpeedBoost;
            slideStartTime = Time.time;
            IsSliding = true;
            SetLow(true);
            if (Slid != null) Slid();
            GameEvents.Raise(GameEventType.Slide, FeetPosition, slideSpeed / 8f);
        }

        /// <summary>Ends the slide on time or when the kid leaves the ground, and stands up once there's room.</summary>
        void UpdateSlide()
        {
            if (IsSliding)
            {
                bool airborne = !IsGrounded && Time.time - lastGroundedTime > tuning.coyoteTime;
                if (Time.time - slideStartTime >= tuning.slideDuration || airborne) EndSlide();
            }
            if (IsLow && !IsSliding && HeadroomClear()) SetLow(false);
        }

        void EndSlide()
        {
            if (!IsSliding) return;
            IsSliding = false;
            slideEndTime = Time.time;
        }

        /// <summary>Out of the slide and up on the feet (the caller has checked there's room).</summary>
        void StandUp()
        {
            EndSlide();
            SetLow(false);
        }

        /// <summary>
        /// Is the space a standing kid takes above the low collider free of anything solid? The box
        /// is a little smaller than the capsule, so a wall or a ceiling the kid would only touch
        /// doesn't count. (The kid is never scaled, so local sizes are world sizes.)
        /// </summary>
        bool HeadroomClear()
        {
            if (capsule == null) return true;
            float bottom = standOffset.y - standSize.y * 0.5f;
            float lowTop = bottom + LowHeight;
            float top = standOffset.y + standSize.y * 0.5f;
            if (top - lowTop < 0.05f) return true;
            var size = new Vector2(Mathf.Max(0.05f, standSize.x - 0.04f), top - lowTop - 0.04f);
            var center = Body.position + new Vector2(standOffset.x, (lowTop + top) * 0.5f);
            int count = Physics2D.OverlapBox(center, size, 0f, groundFilter, roomHits);
            for (int i = 0; i < count; i++)
                if (IsSolidToKid(roomHits[i])) return false;
            return true;
        }

        float LowHeight { get { return Mathf.Clamp(tuning.slideHeight, 0.2f, standSize.y); } }

        /// <summary>
        /// Lower the capsule to the slide height or raise it back, keeping its bottom at the feet.
        /// A capsule no taller than it is wide lies on its side (Unity would otherwise round it up
        /// to a circle as wide as the standing kid, poking into the ground).
        /// </summary>
        void SetLow(bool low)
        {
            if (IsLow == low) return;
            IsLow = low;
            if (capsule == null) return;
            if (low)
            {
                float h = LowHeight;
                float bottom = standOffset.y - standSize.y * 0.5f;
                capsule.direction = standSize.x >= h ? CapsuleDirection2D.Horizontal : CapsuleDirection2D.Vertical;
                capsule.size = new Vector2(standSize.x, h);
                capsule.offset = new Vector2(standOffset.x, bottom + h * 0.5f);
            }
            else
            {
                capsule.direction = standDirection;
                capsule.size = standSize;
                capsule.offset = standOffset;
            }
            if (ShapeChanged != null) ShapeChanged();
        }

        /// <summary>Throw the kid upward (springboards). Counts as a jump that can't be cut short.</summary>
        public void Launch(float upwardSpeed)
        {
            Vector2 v = Body.linearVelocity;
            v.y = upwardSpeed;
            Body.linearVelocity = v;
            jumping = false;
            lastGroundedTime = -10f;
            // A bounce off a trampoline is like touching the ground: the air jump comes back
            // (or, with it turned off, is used up so the launch keeps its designed height).
            airJumpsUsed = tuning.airJumpAfterSpringboard ? 0 : tuning.airJumps;
            EndSlide();   // stands up on the next step, once there's room
        }

        /// <summary>Turn to face a direction (e.g. when kicking backward).</summary>
        public void FaceTowards(float direction)
        {
            if (IsSliding) return;   // a slide holds its line
            if (direction > 0.01f) Facing = 1;
            else if (direction < -0.01f) Facing = -1;
        }

        /// <summary>Apply a speed multiplier until removed by the same owner (e.g. a puddle).</summary>
        public void AddSpeedModifier(object owner, float multiplier)
        {
            RemoveSpeedModifier(owner);
            speedModifierOwners.Add(owner);
            speedModifierValues.Add(multiplier);
            RecalculateSpeedMultiplier();
        }

        public void RemoveSpeedModifier(object owner)
        {
            int index = speedModifierOwners.IndexOf(owner);
            if (index < 0) return;
            speedModifierOwners.RemoveAt(index);
            speedModifierValues.RemoveAt(index);
            RecalculateSpeedMultiplier();
        }

        void RecalculateSpeedMultiplier()
        {
            float m = 1f;
            foreach (float value in speedModifierValues) m *= value;
            SpeedMultiplier = m;
        }

        public void ResetTo(Vector2 position)
        {
            Body.position = position;
            transform.position = position;
            Body.linearVelocity = Vector2.zero;
            jumping = false;
            lastJumpPressedTime = -10f;
            lastSlidePressedTime = -10f;
            IsSliding = false;
            slideEndTime = -10f;
            SetLow(false);
            airJumpsUsed = 0;
            Facing = 1;
            MoveAxis = 0f;
            speedModifierOwners.Clear();
            speedModifierValues.Clear();
            SpeedMultiplier = 1f;
        }

        void OnDrawGizmosSelected()
        {
            Gizmos.color = IsGrounded ? Color.green : Color.red;
            Vector3 feetPos = feet != null ? feet.position : transform.position;
            Gizmos.DrawWireCube(feetPos, groundCheckSize);
        }
    }
}
