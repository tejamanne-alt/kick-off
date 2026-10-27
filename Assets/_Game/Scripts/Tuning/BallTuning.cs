using UnityEngine;

namespace DribbleToSchool.Tuning
{
    /// <summary>
    /// Every number that shapes how the ball feels. Edit the asset (or use the
    /// in-game Tuning panel) instead of touching code.
    /// </summary>
    [CreateAssetMenu(menuName = "Dribble To School/Ball Tuning", fileName = "BallTuning")]
    public class BallTuning : ScriptableObject
    {
        [Header("Body")]
        public float mass = 0.45f;
        public float gravityScale = 1.6f;
        public float linearDamping = 0.05f;
        public float angularDamping = 0.4f;
        [Range(0f, 1f)] public float bounciness = 0.5f;
        [Range(0f, 1f)] public float friction = 0.4f;
        [Tooltip("Extra horizontal slow-down per second while the ball rolls on the ground.")]
        public float rollingResistance = 0.45f;

        [Header("Dribble")]
        [Tooltip("Max distance from the kid's feet at which the ball can be touched.")]
        public float reachRadius = 0.8f;
        [Tooltip("When the ball is closer than this (ahead of the feet) the kid touches it automatically.")]
        public float autoTouchDistance = 0.25f;
        [Tooltip("How much faster than the kid the ball travels after a touch.")]
        public float dribbleLeadSpeed = 1.6f;
        [Tooltip("Random +/- spread on automatic touches. Perfect touches have none.")]
        [Range(0f, 0.5f)] public float autoTouchVariance = 0.25f;
        [Tooltip("Upward speed given by a normal touch (a little hop).")]
        public float touchLift = 1.2f;
        [Tooltip("Upward speed given by a perfect touch (lower = tighter control).")]
        public float perfectTouchLift = 0.6f;
        public float touchCooldown = 0.18f;
        [Tooltip("Distance ahead of the feet (min, max) that counts as a perfect touch, while the kid is catching up to the ball.")]
        public Vector2 perfectTouchBand = new Vector2(0.25f, 0.55f);
        [Tooltip("Kid speed below which a braking kid traps the ball instead of pushing it.")]
        public float trapSpeedThreshold = 0.6f;
        [Range(0f, 1f)] public float trapDamping = 0.15f;

        [Header("Juggle")]
        [Tooltip("Horizontal reach for juggling (ball in the air).")]
        public float juggleReachX = 0.9f;
        [Tooltip("Highest point above the feet where the kid can still juggle.")]
        public float juggleMaxHeight = 1.8f;
        public float juggleUpSpeed = 5.5f;
        [Tooltip("Fraction of the kid's speed the ball keeps when juggled.")]
        [Range(0f, 1.5f)] public float juggleCarry = 1f;

        [Header("Kick")]
        [Tooltip("Max distance from the feet at which a kick can be taken.")]
        public float kickReach = 1.1f;
        public float minKickSpeed = 3f;
        public float maxKickSpeed = 14f;
        [Tooltip("Finger drag (world units) below which nothing happens.")]
        public float minDragDistance = 0.3f;
        [Tooltip("Finger drag (world units) that gives full power.")]
        public float maxDragDistance = 2.5f;
        [Tooltip("Backspin in degrees/sec applied per unit of kick speed.")]
        public float kickSpin = 40f;
        [Tooltip("Seconds after a kick before the kid can touch the ball again.")]
        public float postKickNoTouchTime = 0.35f;
        [Tooltip("Time scale while aiming (1 = no slow motion).")]
        [Range(0.1f, 1f)] public float aimTimeScale = 0.5f;

        [Header("Trajectory Preview")]
        [Tooltip("Only the first part of the flight is previewed so the kick still takes skill.")]
        public float previewDuration = 0.5f;
        [Range(2, 40)] public int previewDots = 12;
    }
}
