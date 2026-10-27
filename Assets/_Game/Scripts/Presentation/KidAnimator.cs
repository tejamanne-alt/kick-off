using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Bouncy procedural animation for the kid: run cycle scaled by speed,
    /// idle breathing, jump/fall poses, a snappy kick swing, landing squash,
    /// a celebration at the gate and a stumble when the ball is lost.
    /// </summary>
    [RequireComponent(typeof(CharacterRig))]
    public class KidAnimator : MonoBehaviour
    {
        public KidController kid;
        public float strideFrequency = 2.6f;
        public float maxLegSwing = 38f;
        public float maxArmSwing = 30f;

        CharacterRig rig;
        float phase;
        float kickTime = -10f;
        float kickStrength;
        float landTime = -10f;
        float landStrength;
        float jumpTime = -10f;
        float stumbleTime = -10f;
        bool celebrating;

        void Awake()
        {
            rig = GetComponent<CharacterRig>();
        }

        void OnEnable()
        {
            GameEvents.Raised += OnGameEvent;
            if (kid != null)
            {
                kid.Landed += OnLanded;
                kid.Jumped += OnJumped;
            }
        }

        void OnDisable()
        {
            GameEvents.Raised -= OnGameEvent;
            if (kid != null)
            {
                kid.Landed -= OnLanded;
                kid.Jumped -= OnJumped;
            }
        }

        void OnLanded(float fallSpeed)
        {
            landTime = Time.time;
            landStrength = Mathf.Clamp01(fallSpeed / 14f);
        }

        void OnJumped() { jumpTime = Time.time; }

        void OnGameEvent(GameEventType type, Vector2 position, float intensity)
        {
            switch (type)
            {
                case GameEventType.Kick:
                case GameEventType.Touch:
                case GameEventType.PerfectTouch:
                case GameEventType.Juggle:
                case GameEventType.Trap:
                    // Only swing the leg if this touch came from our kid (close to the feet).
                    if (kid != null && Vector2.Distance(position, kid.FeetPosition) < 1.6f)
                    {
                        kickTime = Time.time;
                        kickStrength = type == GameEventType.Kick ? 1f : type == GameEventType.Juggle ? 0.7f : 0.45f;
                    }
                    break;
                case GameEventType.Goal: celebrating = true; break;
                case GameEventType.BallLost: stumbleTime = Time.time; break;
                case GameEventType.LevelStart:
                case GameEventType.Respawn: celebrating = false; break;
            }
        }

        void LateUpdate()
        {
            if (kid == null) return;
            float speed = Mathf.Abs(kid.SpeedX);
            float runK = Mathf.Clamp01(speed / Mathf.Max(kid.tuning.runSpeed, 0.1f));
            float vy = kid.Body.linearVelocity.y;

            float legF, legB, armF, armB, bob = 0f, headTilt = 0f;
            Vector2 squash = Vector2.one;

            if (celebrating)
            {
                float t = Time.time * 6f;
                bob = Mathf.Abs(Mathf.Sin(t)) * 0.12f;
                legF = 10f; legB = -10f;
                armF = 160f + Mathf.Sin(t) * 15f;
                armB = -160f - Mathf.Sin(t) * 15f;
                headTilt = Mathf.Sin(t * 0.5f) * 8f;
            }
            else if (!kid.IsGrounded)
            {
                // Rising: tucked and reaching; falling: legs down, arms up for balance.
                float rising = Mathf.Clamp01(vy / 6f);
                legF = Mathf.Lerp(-10f, 35f, rising);
                legB = Mathf.Lerp(-25f, -40f, rising);
                armF = Mathf.Lerp(70f, 40f, rising);
                armB = Mathf.Lerp(-80f, -50f, rising);
                float stretch = Mathf.Clamp01(1f - (Time.time - jumpTime) / 0.2f) * 0.12f;
                squash = new Vector2(1f - stretch, 1f + stretch);
            }
            else
            {
                phase += Time.deltaTime * strideFrequency * Mathf.Max(speed, 0f) * Mathf.PI * 0.5f;
                float s = Mathf.Sin(phase);
                legF = s * maxLegSwing * runK;
                legB = -s * maxLegSwing * runK;
                armF = -s * maxArmSwing * runK - 10f * runK;
                armB = s * maxArmSwing * runK - 10f * runK;
                bob = Mathf.Abs(Mathf.Cos(phase)) * 0.05f * runK;
                headTilt = -4f * runK;

                if (runK < 0.1f)
                {
                    // Idle breathing
                    float breathe = Mathf.Sin(Time.time * 2.2f) * 0.015f;
                    squash = new Vector2(1f - breathe, 1f + breathe);
                }

                float land = Mathf.Clamp01(1f - (Time.time - landTime) / 0.18f) * landStrength;
                squash = new Vector2(squash.x + land * 0.2f, squash.y - land * 0.22f);
            }

            // Kick swing: wind up back, then whip forward.
            float kt = (Time.time - kickTime) / 0.28f;
            if (kt >= 0f && kt <= 1f)
            {
                float swing = kt < 0.3f ? Mathf.Lerp(0f, -35f, kt / 0.3f) : Mathf.Lerp(-35f, 85f, Mathf.Sin((kt - 0.3f) / 0.7f * Mathf.PI * 0.5f));
                if (kt > 0.75f) swing = Mathf.Lerp(85f, legF, (kt - 0.75f) / 0.25f);
                legF = Mathf.Lerp(legF, swing, kickStrength);
                armB = Mathf.Lerp(armB, 50f, kickStrength * 0.6f);
                armF = Mathf.Lerp(armF, -40f, kickStrength * 0.6f);
            }

            // Stumble: quick wobble.
            float st = (Time.time - stumbleTime) / 0.5f;
            if (st >= 0f && st <= 1f) headTilt += Mathf.Sin(st * Mathf.PI * 4f) * 15f * (1f - st);

            rig.Pose(legF, legB, armF, armB, bob, squash, headTilt);
        }
    }
}
