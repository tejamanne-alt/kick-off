using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using UnityEngine;

namespace DribbleToSchool.Ball
{
    /// <summary>
    /// Kick button aiming: drag from the kick button in the direction the ball
    /// should fly (forward or back), then release. Drag length sets the power.
    /// Time slows down while aiming so there is room to think on a phone.
    /// A quick tap on the button is a short lofted pass the way the kid faces.
    /// </summary>
    public class KickAimer : MonoBehaviour
    {
        public BallController ball;
        public TrajectoryPreview preview;
        public Camera worldCamera;
        [Tooltip("Power of a quick tap on the kick button (0..1).")]
        [Range(0f, 1f)] public float tapPower = 0.4f;
        [Tooltip("Launch angle of a quick tap, in degrees above the ground.")]
        public float tapAngle = 30f;

        /// <summary>True while a kick is being aimed.</summary>
        public bool IsAiming { get; private set; }
        /// <summary>True while aiming and the ball is close enough to kick.</summary>
        public bool AimIsValid { get; private set; }
        /// <summary>0..1 power of the current aim.</summary>
        public float AimPower { get; private set; }

        // Drag is measured against the un-zoomed view so the aim zoom doesn't change kick power.
        float baseOrthoSize = 5.5f;

        void Start()
        {
            if (worldCamera == null) worldCamera = Camera.main;
            if (worldCamera != null) baseOrthoSize = worldCamera.orthographicSize;
            var input = GameInput.Instance;
            if (input != null && input.worldCamera == null) input.worldCamera = worldCamera;
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input == null) return;
            bool canKick = ball.InKickReach && ball.kid.InputEnabled;

            if (input.KickReleased)
            {
                Vector2 velocity;
                float power;
                if (TryComputeKick(input.KickDrag, out velocity, out power) && canKick)
                    ball.Kick(velocity);
            }
            else if (input.KickTapped && canKick)
            {
                ball.Kick(QuickKick());
            }

            if (input.KickAiming)
            {
                if (!IsAiming) BeginAim();

                Vector2 velocity;
                float power;
                bool hasPower = TryComputeKick(input.KickDrag, out velocity, out power);
                AimPower = power;
                AimIsValid = hasPower && ball.InKickReach;
                if (hasPower)
                    preview.Show(ball.Body.position, velocity, Physics2D.gravity * ball.Body.gravityScale, AimIsValid);
                else
                    preview.Hide();
            }
            else if (IsAiming)
            {
                EndAim();
            }
        }

        Vector2 QuickKick()
        {
            var tuning = ball.tuning;
            float speed = Mathf.Lerp(tuning.minKickSpeed, tuning.maxKickSpeed, tapPower);
            float a = tapAngle * Mathf.Deg2Rad;
            return new Vector2(Mathf.Cos(a) * ball.kid.Facing, Mathf.Sin(a)) * speed;
        }

        bool TryComputeKick(Vector2 dragScreen, out Vector2 velocity, out float power)
        {
            var tuning = ball.tuning;
            float worldPerPixel = 2f * baseOrthoSize / Mathf.Max(1, Screen.height);
            Vector2 drag = dragScreen * worldPerPixel; // the ball goes the way you drag
            // Never drive the ball into the ground: dragging down gives a flat kick.
            drag.y = Mathf.Max(drag.y, 0f);
            float distance = drag.magnitude;

            if (distance < tuning.minDragDistance)
            {
                velocity = Vector2.zero;
                power = 0f;
                return false;
            }

            power = Mathf.Clamp01((distance - tuning.minDragDistance) / Mathf.Max(tuning.maxDragDistance - tuning.minDragDistance, 0.01f));
            float speed = Mathf.Lerp(tuning.minKickSpeed, tuning.maxKickSpeed, power);
            velocity = drag / distance * speed;
            return true;
        }

        void BeginAim()
        {
            IsAiming = true;
            TimeControl.SetSlowMotion(ball.tuning.aimTimeScale);
        }

        void EndAim()
        {
            IsAiming = false;
            AimIsValid = false;
            AimPower = 0f;
            preview.Hide();
            TimeControl.SetSlowMotion(1f);
        }

        void OnDisable()
        {
            if (IsAiming) EndAim();
        }
    }
}
