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
        [Tooltip("Speed while the brake is held (0 = full stop).")]
        public float brakeSpeed = 0f;
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
    }
}
