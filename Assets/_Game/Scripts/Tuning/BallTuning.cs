using UnityEngine;

namespace DribbleToSchool.Tuning
{
    /// <summary>
    /// Every number that shapes how the ball feels. Edit the asset (or use the
    /// in-game Tuning panel) instead of touching code.
    /// </summary>
    [CreateAssetMenu(menuName = "Kick Off/Ball Tuning", fileName = "BallTuning")]
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
        [Tooltip("A stopping kid slower than this (m/s) puts a foot on a ball at the feet instead of pushing it on.")]
        public float trapSpeedThreshold = 0.6f;

        [Header("Close control")]
        [Tooltip("At a walk a touch pushes the ball on by only this part of dribbleLeadSpeed (and of its sloppiness): the slower the kid, the closer the ball stays. Flat out, the whole of it.")]
        [Range(0f, 1f)] public float walkLeadFraction = 0.1f;
        [Tooltip("Upward speed of a touch at a walk (touchLift is a flat-out touch's).")]
        public float walkTouchLift = 0.3f;
        [Tooltip("A foot on the ball (the stick let go with the ball at the feet) holds it this far ahead of the feet.")]
        public float soleHoldOffset = 0.12f;
        [Tooltip("A drag-back (the stick pushed the other way with a foot on the ball) rolls the ball back under the kid at this speed as they turn.")]
        public float dragBackSpeed = 2.4f;
        [Tooltip("With KICK held, the ball is kept this far ahead of the feet: at a walk (x), flat out (y).")]
        public Vector2 controlLead = new Vector2(0.25f, 0.45f);
        [Tooltip("With KICK held, the kid runs at this part of full speed.")]
        [Range(0.3f, 1f)] public float controlSpeedFraction = 0.7f;
        [Tooltip("Seconds between the little touches of close control: at a walk (x), flat out (y).")]
        public Vector2 controlTouchInterval = new Vector2(0.45f, 0.28f);
        [Tooltip("How hard a held ball is pulled to where it should be (per second of distance).")]
        public float holdSpring = 10f;
        [Tooltip("The fastest a held ball is pulled toward that spot, relative to the kid (m/s).")]
        public float holdMaxPull = 3f;
        [Tooltip("How quickly a held ball takes that speed (per second): higher holds tighter.")]
        public float holdGrip = 25f;

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
