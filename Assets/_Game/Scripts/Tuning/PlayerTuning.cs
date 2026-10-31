using UnityEngine;

namespace DribbleToSchool.Tuning
{
    /// <summary>
    /// Movement feel for the kid. Edit the asset (or use the in-game Tuning panel).
    /// </summary>
    [CreateAssetMenu(menuName = "Dribble To School/Player Tuning", fileName = "PlayerTuning")]
    public class PlayerTuning : ScriptableObject
    {
        [Header("Run")]
        [Tooltip("Auto-run speed to the right.")]
        public float runSpeed = 4.2f;
        public float acceleration = 14f;
        public float deceleration = 22f;
        [Tooltip("Multiplier on acceleration while in the air.")]
        [Range(0f, 1f)] public float airControl = 0.5f;

        [Header("Jump")]
        public float gravityScale = 3f;
        [Tooltip("Take-off speed. Holding jump keeps it; releasing early cuts it.")]
        public float jumpVelocity = 9f;
        [Tooltip("Upward speed is multiplied by this when jump is released early (short hop).")]
        [Range(0f, 1f)] public float jumpCutMultiplier = 0.45f;
        public float fallGravityMultiplier = 1.4f;
        public float maxFallSpeed = 18f;
        [Tooltip("Grace time to still jump after running off a ledge.")]
        public float coyoteTime = 0.1f;
        [Tooltip("A jump pressed this long before landing still counts.")]
        public float jumpBufferTime = 0.12f;

        [Header("Double Jump")]
        [Tooltip("Extra jumps in the air (press JUMP again). 0 turns the double jump off.")]
        [Range(0, 2)] public int airJumps = 1;
        [Tooltip("Take-off speed of the air jump; holding jump keeps it, releasing early cuts it like the first jump. " +
            "At 7 a double jump from the ground peaks about 2.2 m up, under the 2.4 m gates.")]
        public float airJumpVelocity = 7f;
        [Tooltip("A trampoline launch gives the air jump back (bounce, then jump again in the air).")]
        public bool airJumpAfterSpringboard = true;

        [Header("Slide")]
        [Tooltip("How long a slide lasts before the kid gets up (later if something is overhead).")]
        public float slideDuration = 0.7f;
        [Tooltip("Speed at the start of a slide, as a multiple of the run speed (or of the current speed if faster).")]
        public float slideSpeedBoost = 1.3f;
        [Tooltip("How fast the slide loses speed (units per second, per second).")]
        public float slideFriction = 3.5f;
        [Tooltip("Slowest a slide goes; also the speed of the low shuffle while something is overhead.")]
        public float slideMinSpeed = 2.2f;
        [Tooltip("Height of the kid's collider while sliding (standing it is 1.2). Fits under a 0.85 gap with room to spare.")]
        public float slideHeight = 0.5f;
        [Tooltip("Time after getting up before the next slide can start.")]
        public float slideCooldown = 0.2f;
        [Tooltip("A slide pressed this long before landing still counts.")]
        public float slideBufferTime = 0.12f;
    }
}
