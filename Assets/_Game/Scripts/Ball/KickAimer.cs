using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using UnityEngine;

namespace DribbleToSchool.Ball
{
    /// <summary>
    /// Slingshot kick: touch the ball, drag back, release.
    /// Drag direction (reversed) sets the angle, drag length sets the power.
    /// Time slows down while aiming so there is room to think on a phone.
    /// </summary>
    public class KickAimer : MonoBehaviour
    {
        public BallController ball;
        public TrajectoryPreview preview;
        public Camera worldCamera;

        /// <summary>True while a kick is being aimed.</summary>
        public bool IsAiming { get; private set; }
        /// <summary>True while aiming and the ball is close enough to kick.</summary>
        public bool AimIsValid { get; private set; }
        /// <summary>0..1 power of the current aim.</summary>
        public float AimPower { get; private set; }

        void Start()
        {
            if (worldCamera == null) worldCamera = Camera.main;
            var input = GameInput.Instance;
            if (input != null)
            {
                if (input.worldCamera == null) input.worldCamera = worldCamera;
                if (input.ball == null) input.ball = ball.transform;
                input.ballWorldRadius = ball.Radius;
            }
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input == null) return;

            if (input.KickReleased)
            {
                Vector2 velocity;
                float power;
                if (TryComputeKick(input.KickStartScreen, input.KickCurrentScreen, out velocity, out power)
                    && ball.InKickReach && ball.kid.InputEnabled)
                {
                    ball.Kick(velocity);
                }
            }

            if (input.KickAiming)
            {
                if (!IsAiming) BeginAim();

                Vector2 velocity;
                float power;
                bool hasPower = TryComputeKick(input.KickStartScreen, input.KickCurrentScreen, out velocity, out power);
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

        bool TryComputeKick(Vector2 startScreen, Vector2 currentScreen, out Vector2 velocity, out float power)
        {
            var tuning = ball.tuning;
            float worldPerPixel = 2f * worldCamera.orthographicSize / Screen.height;
            Vector2 drag = (startScreen - currentScreen) * worldPerPixel; // pull back to launch forward
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
