using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Procedural animation for the kid with knees and elbows: a run cycle whose
    /// knees fold in the swing and straighten on the plant, bent-elbow arm drive,
    /// idle breathing, jump tuck and reach, a cocked-knee kick that snaps through,
    /// a crouching landing, a celebration at the gate and a stumble when the ball is lost.
    /// </summary>
    [RequireComponent(typeof(CharacterRig))]
    public class KidAnimator : MonoBehaviour
    {
        public KidController kid;
        public float strideFrequency = 1.9f;   // long teen legs: fewer, longer strides
        public float maxLegSwing = 42f;
        public float maxArmSwing = 34f;

        CharacterRig rig;
        float phase;
        float kickTime = -10f;
        float kickStrength;
        float landTime = -10f;
        float landStrength;
        float jumpTime = -10f;
        float stumbleTime = -10f;
        bool celebrating;
        float facing = 1f;
        float bagAngle, bagVelocity;

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

        /// <summary>How far a running knee folds (degrees) at a given leg phase: most early in the swing.</summary>
        static float KneeFold(float legPhase)
        {
            float swing = Mathf.Max(0f, Mathf.Cos(legPhase + 0.9f));
            return 14f + 80f * swing * swing;
        }

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

            var p = RigPose.Neutral;

            if (celebrating)
            {
                // Little hops with both arms punched up.
                float t = Time.time * 6f;
                float air = Mathf.Abs(Mathf.Sin(t));
                p.bob = air * 0.12f;
                p.legF = 12f + 10f * (1f - air); p.legB = -8f + 10f * (1f - air);
                p.kneeF = p.kneeB = -10f - 45f * (1f - air);
                p.armF = 160f + Mathf.Sin(t) * 12f; p.elbowF = 15f;
                p.armB = -160f - Mathf.Sin(t) * 12f; p.elbowB = 15f;
                p.headTilt = Mathf.Sin(t * 0.5f) * 8f;
            }
            else if (!kid.IsGrounded)
            {
                // Rising: front knee tucked high, arms driving; falling: legs reach down, arms out for balance.
                float rising = Mathf.Clamp01(vy / 6f);
                float falling = Mathf.Clamp01(-vy / 8f);
                p.legF = Mathf.Lerp(18f, 48f, rising);
                p.kneeF = Mathf.Lerp(-25f, -95f, rising);
                p.legB = Mathf.Lerp(-12f, -22f, rising);
                p.kneeB = Mathf.Lerp(-35f, -70f, rising);
                p.armF = Mathf.Lerp(Mathf.Lerp(60f, 80f, falling), -35f, rising);
                p.elbowF = Mathf.Lerp(30f, 85f, rising);
                p.armB = Mathf.Lerp(Mathf.Lerp(-40f, 70f, falling), 55f, rising);
                p.elbowB = Mathf.Lerp(25f, 60f, rising);
                p.lean = Mathf.Lerp(2f, 8f, rising);
                float stretch = Mathf.Clamp01(1f - (Time.time - jumpTime) / 0.2f) * 0.12f;
                p.squash = new Vector2(1f - stretch, 1f + stretch);
            }
            else
            {
                // Run cycle. Each knee folds most early in its swing (the foot flicks up behind),
                // and is nearly straight while the foot is planted. Arms swing against the legs
                // with bent elbows, bending more on the forward swing.
                phase += Time.deltaTime * strideFrequency * Mathf.Max(speed, 0f) * Mathf.PI * 0.5f;
                float s = Mathf.Sin(phase);
                p.legF = s * maxLegSwing * runK;
                p.legB = -s * maxLegSwing * runK;
                p.kneeF = -Mathf.Lerp(3f, KneeFold(phase), runK);
                p.kneeB = -Mathf.Lerp(3f, KneeFold(phase + Mathf.PI), runK);
                p.armF = -s * maxArmSwing * runK - 6f * runK;
                p.armB = s * maxArmSwing * runK - 6f * runK;
                p.elbowF = Mathf.Lerp(12f, 70f + 25f * Mathf.Max(0f, -s), runK);
                p.elbowB = Mathf.Lerp(12f, 70f + 25f * Mathf.Max(0f, s), runK);
                p.bob = Mathf.Abs(s) * 0.05f * runK - 0.02f * runK;
                p.lean = 7f * runK;
                p.headTilt = -4f * runK;

                if (runK < 0.1f)
                {
                    // Idle: breathing, a soft knee and loose arms.
                    float breathe = Mathf.Sin(Time.time * 2.2f);
                    p.squash = new Vector2(1f - breathe * 0.015f, 1f + breathe * 0.015f);
                    p.armF = -3f + breathe * 2f;
                    p.armB = 3f - breathe * 2f;
                    p.elbowF = p.elbowB = 14f + breathe * 3f;
                    p.kneeF = p.kneeB = -5f;
                }

                // Landing: a quick crouch through the knees.
                float land = Mathf.Clamp01(1f - (Time.time - landTime) / 0.22f) * landStrength;
                p.legF += 30f * land; p.legB += 30f * land;
                p.kneeF -= 60f * land; p.kneeB -= 60f * land;
                p.elbowF += 20f * land; p.elbowB += 20f * land;
                p.lean += 10f * land;
                p.bob -= 0.07f * land;   // bent knees already lift the feet; keep them on the ground
                p.squash = new Vector2(p.squash.x + land * 0.12f, p.squash.y - land * 0.12f);
            }

            // Kick: knee cocks back during the wind-up, then the thigh whips through while
            // the knee snaps straight just before the "contact", and follows through.
            float kt = (Time.time - kickTime) / 0.3f;
            if (kt >= 0f && kt <= 1f)
            {
                float thigh, knee;
                if (kt < 0.3f)
                {
                    float u = kt / 0.3f;
                    thigh = Mathf.Lerp(p.legF, -30f, u);
                    knee = Mathf.Lerp(p.kneeF, -100f, u);
                }
                else if (kt < 0.7f)
                {
                    float u = (kt - 0.3f) / 0.4f;
                    thigh = Mathf.Lerp(-30f, 80f, Mathf.Sin(u * Mathf.PI * 0.5f));
                    knee = Mathf.Lerp(-100f, 0f, Mathf.SmoothStep(0f, 1f, Mathf.Clamp01(u * 1.6f)));
                }
                else
                {
                    float u = (kt - 0.7f) / 0.3f;
                    thigh = Mathf.Lerp(80f, p.legF, u);
                    knee = Mathf.Lerp(0f, p.kneeF, u);
                }
                float k = kickStrength;
                p.legF = Mathf.Lerp(p.legF, thigh, k);
                p.kneeF = Mathf.Lerp(p.kneeF, knee, k);
                p.kneeB = Mathf.Lerp(p.kneeB, -14f, k);   // standing leg gives a little
                p.armB = Mathf.Lerp(p.armB, 60f, k * 0.7f);
                p.elbowB = Mathf.Lerp(p.elbowB, 35f, k * 0.7f);
                p.armF = Mathf.Lerp(p.armF, -45f, k * 0.6f);
                p.elbowF = Mathf.Lerp(p.elbowF, 40f, k * 0.6f);
                p.lean = Mathf.Lerp(p.lean, -8f, k * Mathf.Sin(kt * Mathf.PI));
            }

            // Stumble: quick wobble.
            float st = (Time.time - stumbleTime) / 0.5f;
            if (st >= 0f && st <= 1f)
            {
                float wobble = Mathf.Sin(st * Mathf.PI * 4f) * (1f - st);
                p.headTilt += wobble * 15f;
                p.lean += wobble * 8f;
                p.armF += wobble * 40f; p.armB -= wobble * 40f;
            }

            // The shoulder bag trails behind on the run, bounces with each stride and
            // lags behind jumps, on a soft spring so it feels like it has weight.
            float bagTarget = -10f * runK - Mathf.Sin(phase * 2f) * 6f * runK;
            if (!kid.IsGrounded) bagTarget += Mathf.Clamp(-vy * 3f, -25f, 25f);
            bagAngle = Mathf.SmoothDamp(bagAngle, bagTarget, ref bagVelocity, 0.09f);
            p.bag = bagAngle;

            rig.Pose(p);

            // Turn around in 3D: a quick spin through facing the camera.
            facing = Mathf.MoveTowards(facing, kid.Facing, Time.deltaTime * 7f);
            Transform visual = transform.parent;
            if (visual != null) visual.localRotation = Quaternion.Euler(0f, CharacterRig.FacingYaw(facing), 0f);
        }
    }
}
