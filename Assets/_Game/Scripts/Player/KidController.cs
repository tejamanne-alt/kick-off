using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Tuning;
using UnityEngine;

namespace DribbleToSchool.Player
{
    /// <summary>
    /// The kid auto-runs to the right. The player only brakes and jumps;
    /// the ball is never carried, it is dribbled (see BallController).
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class KidController : MonoBehaviour
    {
        public PlayerTuning tuning;
        [Tooltip("Point at the bottom of the kid's collider. Used for ground checks and dribbling.")]
        public Transform feet;
        public Vector2 groundCheckSize = new Vector2(0.4f, 0.1f);
        [Tooltip("Off = the kid stands still unless pushed (juggling challenges).")]
        public bool autoRun = true;

        public Rigidbody2D Body { get; private set; }
        public bool IsGrounded { get; private set; }
        public bool IsBraking { get; private set; }
        public bool InputEnabled { get; set; }
        public float SpeedX { get { return Body.linearVelocity.x; } }
        public Vector2 FeetPosition { get { return feet != null ? (Vector2)feet.position : Body.position; } }
        /// <summary>Product of all active speed modifiers (puddles, sand...).</summary>
        public float SpeedMultiplier { get; private set; }
        /// <summary>Velocity of the moving surface under the kid, if any.</summary>
        public Vector2 GroundVelocity { get; private set; }
        /// <summary>Raised when the kid lands, with the downward speed at impact.</summary>
        public event System.Action<float> Landed;
        /// <summary>Raised when the kid leaves the ground by jumping.</summary>
        public event System.Action Jumped;

        readonly Collider2D[] groundHits = new Collider2D[8];
        ContactFilter2D groundFilter;
        float lastGroundedTime = -10f;
        float lastJumpPressedTime = -10f;
        bool jumping;
        bool wasGrounded;
        float lastFallSpeed;
        readonly List<object> speedModifierOwners = new List<object>();
        readonly List<float> speedModifierValues = new List<float>();

        void Awake()
        {
            Body = GetComponent<Rigidbody2D>();
            InputEnabled = true;
            SpeedMultiplier = 1f;
            groundFilter = new ContactFilter2D();
            groundFilter.useTriggers = false;
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
                return;
            }

            IsBraking = input.BrakeHeld;
            if (input.JumpPressed) lastJumpPressedTime = Time.time;

            // Variable jump height: letting go early cuts the rise short.
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

            float target = !InputEnabled || !autoRun ? 0f : IsBraking ? tuning.brakeSpeed : tuning.runSpeed * SpeedMultiplier;
            target += GroundVelocity.x;
            float rate = Mathf.Abs(target) > Mathf.Abs(v.x) ? tuning.acceleration : tuning.deceleration;
            if (!IsGrounded) rate *= tuning.airControl;
            v.x = Mathf.MoveTowards(v.x, target, rate * Time.fixedDeltaTime);

            bool canJump = Time.time - lastGroundedTime <= tuning.coyoteTime;
            bool wantsJump = Time.time - lastJumpPressedTime <= tuning.jumpBufferTime;
            if (InputEnabled && canJump && wantsJump)
            {
                v.y = tuning.jumpVelocity + Mathf.Max(0f, GroundVelocity.y);
                jumping = true;
                lastJumpPressedTime = -10f;
                lastGroundedTime = -10f;
                if (Jumped != null) Jumped();
                GameEvents.Raise(GameEventType.Jump, FeetPosition, 0.5f);
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
                if (hit.attachedRigidbody == Body) continue;
                if (hit.attachedRigidbody != null && hit.attachedRigidbody.GetComponent<BallController>() != null) continue;
                IsGrounded = true;
                var surface = hit.GetComponentInParent<IMovingSurface>();
                if (surface != null) GroundVelocity = surface.SurfaceVelocity;
                return;
            }
        }

        /// <summary>Throw the kid upward (springboards). Counts as a jump that can't be cut short.</summary>
        public void Launch(float upwardSpeed)
        {
            Vector2 v = Body.linearVelocity;
            v.y = upwardSpeed;
            Body.linearVelocity = v;
            jumping = false;
            lastGroundedTime = -10f;
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
