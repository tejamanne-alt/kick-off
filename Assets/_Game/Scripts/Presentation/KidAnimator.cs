using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Procedural animation for the kid with knees and elbows: a run cycle whose
    /// knees fold in the swing and straighten on the plant, bent-elbow arm drive,
    /// idle breathing, a jump that drives one knee up off the other foot, a double jump that is a
    /// second, harder push in the air (the knee driven up again, the other leg kicking down, both arms
    /// swung up hard, then the legs gathered under to land: a real body's move, no spin); a feet-first slide that lunges in with an overshoot, scuffs along and springs up;
    /// a cocked-knee kick that snaps through, a crouching landing, a celebration at the gate and
    /// a stumble when the ball is lost.
    /// </summary>
    [RequireComponent(typeof(CharacterRig))]
    public class KidAnimator : MonoBehaviour
    {
        public KidController kid;
        public float strideFrequency = 1.9f;   // long teen legs: fewer, longer strides
        public float maxLegSwing = 42f;
        public float maxArmSwing = 34f;

        [Header("Double jump")]
        [Tooltip("How long the double jump's push, gather and reach for the ground take.")]
        public float airJumpDuration = 0.46f;

        [Header("Slide")]
        [Tooltip("How far the body leans back in the slide (degrees from upright).")]
        public float slideLean = 58f;
        [Tooltip("Height of the hips above the ground in the slide, as a fraction of the leg length.")]
        public float slideHipHeight = 0.2f;

        CharacterRig rig;
        float phase;
        float kickTime = -10f;
        float kickStrength;
        float landTime = -10f;
        float landStrength;
        float jumpTime = -10f;
        float doubleJumpTime = -10f;
        float stumbleTime = -10f;
        bool celebrating;
        float facing = 1f;
        float bagAngle, bagVelocity;
        float slideBlend;
        float footOnBallBlend;
        bool wasLow;
        float getUpTime = -10f;
        // Rest-pose measurements (world units) the slide is built from: how high the body's pivot
        // and the hips sit above the feet. Every character (boy, girl, procedural kid) differs.
        float pivotHeight = 0.6f, hipHeight = 0.72f;

        void Awake()
        {
            rig = GetComponent<CharacterRig>();
            MeasureRestPose();
        }

        /// <summary>Runs while the rig still stands in its rest pose (nothing has posed it yet).</summary>
        void MeasureRestPose()
        {
            if (kid == null || kid.feet == null || rig.body == null || rig.legFront == null) return;
            float feetY = kid.feet.position.y;
            pivotHeight = rig.body.position.y - feetY;
            hipHeight = Mathf.Max(0.3f, rig.legFront.position.y - feetY);
        }

        void OnEnable()
        {
            GameEvents.Raised += OnGameEvent;
            if (kid != null)
            {
                kid.Landed += OnLanded;
                kid.Jumped += OnJumped;
                kid.DoubleJumped += OnDoubleJumped;
            }
        }

        void OnDisable()
        {
            GameEvents.Raised -= OnGameEvent;
            if (kid != null)
            {
                kid.Landed -= OnLanded;
                kid.Jumped -= OnJumped;
                kid.DoubleJumped -= OnDoubleJumped;
            }
        }

        void OnLanded(float fallSpeed)
        {
            landTime = Time.time;
            landStrength = Mathf.Clamp01(fallSpeed / 14f);
        }

        void OnJumped() { jumpTime = Time.time; }

        void OnDoubleJumped() { doubleJumpTime = jumpTime = Time.time; }


        /// <summary>
        /// The head on the run (degrees, positive tips it back). A runner keeps the eyes level: the head turns back
        /// against most of the body's forward lean (it's on the neck, which bends), with the chin a little down to look
        /// ahead. With each foot strike (the legs passing, twice a stride) the head dips a touch under the landing and
        /// comes back up through the flight, a beat after the body (the neck's give).
        /// </summary>
        public static float RunHeadTilt(float phase, float lean, float runK)
        {
            float steady = 0.75f * lean - 2f * runK;
            float nod = -2.5f * Mathf.Cos(2f * (phase - 0.35f)) * runK;
            return steady + nod;
        }

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
            float runK = Mathf.Clamp01(speed / Mathf.Max(kid.RunSpeed, 0.1f));
            float vy = kid.Body.linearVelocity.y;

            var p = RigPose.Neutral;

            // The double jump: a second push in the air. Landing before it's done hurries it to its end.
            float ft = (Time.time - doubleJumpTime) / Mathf.Max(0.05f, airJumpDuration);
            if (ft >= 0f && ft < 1f && kid.IsGrounded)
            {
                doubleJumpTime -= Time.deltaTime * 3f;   // four times as fast
                ft = (Time.time - doubleJumpTime) / Mathf.Max(0.05f, airJumpDuration);
            }
            bool airJumping = ft >= 0f && ft <= 1f;
            // The push (knee up, the other leg driving down, arms thrown up), then the legs gathered up under
            // the body, then reaching down for the ground.
            float push = airJumping ? Mathf.SmoothStep(0f, 1f, ft / 0.12f) * (1f - Mathf.SmoothStep(0f, 1f, (ft - 0.3f) / 0.2f)) : 0f;
            float gather = airJumping ? Mathf.SmoothStep(0f, 1f, (ft - 0.3f) / 0.22f) * (1f - Mathf.SmoothStep(0f, 1f, (ft - 0.72f) / 0.28f)) : 0f;

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
                // (the lead knee up, the take-off leg left long behind)
                p.legF = Mathf.Lerp(18f, 52f, rising);
                p.kneeF = Mathf.Lerp(-25f, -82f, rising);
                p.legB = Mathf.Lerp(-12f, -30f, rising);
                p.kneeB = Mathf.Lerp(-35f, -42f, rising);
                p.armF = Mathf.Lerp(Mathf.Lerp(60f, 80f, falling), -35f, rising);
                p.elbowF = Mathf.Lerp(30f, 85f, rising);
                p.armB = Mathf.Lerp(Mathf.Lerp(-40f, 70f, falling), 55f, rising);
                p.elbowB = Mathf.Lerp(25f, 60f, rising);
                p.lean = Mathf.Lerp(2f, 8f, rising);
                float stretch = Mathf.Clamp01(1f - (Time.time - jumpTime) / 0.2f) * 0.035f;
                p.squash = new Vector2(1f - stretch, 1f + stretch);

                // Double jump: one more push, as if off an invisible step. The lead knee drives up to the
                // chest while the other leg stamps down straight behind, both arms swing up hard past the
                // face, the chest lifts; then both knees come up together, arms dropping out for balance,
                // and the legs open down toward the ground. No spin: the body stays upright.
                if (airJumping)
                {
                    p.legF = Mathf.Lerp(p.legF, 82f, push); p.kneeF = Mathf.Lerp(p.kneeF, -108f, push);
                    p.legB = Mathf.Lerp(p.legB, -24f, push); p.kneeB = Mathf.Lerp(p.kneeB, -8f, push);
                    p.armF = Mathf.Lerp(p.armF, 150f, push); p.elbowF = Mathf.Lerp(p.elbowF, 28f, push);
                    p.armB = Mathf.Lerp(p.armB, 120f, push); p.elbowB = Mathf.Lerp(p.elbowB, 40f, push);
                    p.lean = Mathf.Lerp(p.lean, -4f, push);
                    p.headTilt = Mathf.Lerp(p.headTilt, 8f, push);

                    p.legF = Mathf.Lerp(p.legF, 70f, gather); p.kneeF = Mathf.Lerp(p.kneeF, -100f, gather);
                    p.legB = Mathf.Lerp(p.legB, 58f, gather); p.kneeB = Mathf.Lerp(p.kneeB, -96f, gather);
                    p.armF = Mathf.Lerp(p.armF, 70f, gather); p.elbowF = Mathf.Lerp(p.elbowF, 35f, gather);
                    p.armB = Mathf.Lerp(p.armB, -30f, gather); p.elbowB = Mathf.Lerp(p.elbowB, 30f, gather);
                    p.lean = Mathf.Lerp(p.lean, 12f, gather);
                    p.headTilt = Mathf.Lerp(p.headTilt, -6f, gather);

                    p.squash = new Vector2(1f - 0.02f * push, 1f + 0.03f * push);
                }
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
                p.headTilt = RunHeadTilt(phase, p.lean, runK);

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

                // A foot on the ball (KidController.FootOnBall): the near foot lifted onto it, the weight back a little,
                // the far arm out for balance.
                footOnBallBlend = Mathf.MoveTowards(footOnBallBlend, kid.FootOnBall && runK < 0.1f ? 1f : 0f, Time.deltaTime / 0.15f);
                if (footOnBallBlend > 0f)
                {
                    float f = Mathf.SmoothStep(0f, 1f, footOnBallBlend);
                    p.legF = Mathf.Lerp(p.legF, 30f, f);
                    p.kneeF = Mathf.Lerp(p.kneeF, -48f, f);
                    p.lean = Mathf.Lerp(p.lean, -3f, f);
                    p.armB = Mathf.Lerp(p.armB, -14f, f);
                    p.elbowB = Mathf.Lerp(p.elbowB, 24f, f);
                }

                // Landing: a quick crouch through the knees.
                float land = Mathf.Clamp01(1f - (Time.time - landTime) / 0.22f) * landStrength;
                p.legF += 30f * land; p.legB += 30f * land;
                p.kneeF -= 60f * land; p.kneeB -= 60f * land;
                p.elbowF += 20f * land; p.elbowB += 20f * land;
                p.lean += 10f * land;
                p.bob -= 0.07f * land;   // bent knees already lift the feet; keep them on the ground
                p.squash = new Vector2(p.squash.x + land * 0.04f, p.squash.y - land * 0.04f);   // a body, not a rubber ball
            }

            // Slide: drops in fast and gets up a little slower, and holds while the kid shuffles
            // low under something.
            bool low = kid.IsLow && !celebrating;
            if (wasLow && !low) getUpTime = Time.time;
            wasLow = low;
            slideBlend = Mathf.MoveTowards(slideBlend, low ? 1f : 0f, Time.deltaTime / (low ? 0.07f : 0.18f));
            if (slideBlend > 0f) p = Blend(p, SlidePose(speed), Mathf.SmoothStep(0f, 1f, slideBlend));

            // Springing back up: a little hop, stretched tall, arms swinging into the stride.
            float gu = (Time.time - getUpTime) / 0.26f;
            if (!low && gu >= 0f && gu <= 1f && kid.IsGrounded)
            {
                float hop = Mathf.Sin(gu * Mathf.PI);
                p.bob += 0.06f * hop;
                p.squash = new Vector2(p.squash.x * (1f - 0.05f * hop), p.squash.y * (1f + 0.09f * hop));
                p.armF += 34f * hop; p.armB -= 24f * hop;
                p.kneeF -= 14f * hop; p.kneeB -= 10f * hop;
            }

            // Kick: knee cocks back during the wind-up, then the thigh whips through while
            // the knee snaps straight just before the "contact", and follows through.
            // (Not in the slide: the boot just nudges the ball on.)
            float kt = (Time.time - kickTime) / 0.3f;
            if (kt >= 0f && kt <= 1f && slideBlend < 1f)
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
                float k = kickStrength * (1f - slideBlend);
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
            // lags behind jumps, on a soft spring so it feels like it has weight. In the slide
            // it drags out behind, clear of the ground under the hips.
            float bagTarget = -10f * runK - Mathf.Sin(phase * 2f) * 6f * runK;
            if (!kid.IsGrounded) bagTarget += Mathf.Clamp(-vy * 3f, -25f, 25f);
            bagTarget = Mathf.Lerp(bagTarget, -95f, slideBlend);
            if (airJumping) bagTarget += 22f * push - 12f * gather;   // jerked by the push, then swinging back
            bagAngle = Mathf.SmoothDamp(bagAngle, bagTarget, ref bagVelocity, 0.09f);
            p.bag = bagAngle;

            rig.Pose(p);

            // Turn around in 3D: a quick spin through facing the camera.
            facing = Mathf.MoveTowards(facing, kid.Facing, Time.deltaTime * 7f);
            Transform visual = transform.parent;
            if (visual != null) visual.localRotation = Quaternion.Euler(0f, CharacterRig.FacingYaw(facing), 0f);
        }

        /// <summary>
        /// A feet-first slide, like a slide tackle: leaning far back, the front leg stretched out
        /// just off the ground, the back leg folded under with its knee up, the far hand planted on
        /// the ground beside the hip and the near arm thrown forward for balance, chin down to
        /// look ahead. Joint angles are in the body's frame, so the lean adds to every limb: each
        /// limb below is written as (its direction in the world, from straight down, + forward)
        /// minus the lean. The body drops so the hips sit <see cref="slideHipHeight"/> of a leg
        /// above the ground.
        /// </summary>
        RigPose SlidePose(float speed)
        {
            var s = RigPose.Neutral;
            // The lean dives in with a quick overshoot, then eases upright as the slide runs out of speed.
            float t = kid.IsSliding ? kid.SlideTime : 1f;
            float top = Mathf.Max(0.1f, kid.RunSpeed * kid.tuning.slideSpeedBoost);
            float spent = kid.IsSliding ? 1f - Mathf.Clamp01(kid.SlideSpeed / top) : 0.6f;
            float lean = slideLean * (1f + 0.15f * Mathf.Exp(-t * 15f) * Mathf.Sin(t * 28f + 0.4f)) * (1f - 0.15f * spent);
            s.lean = -lean;
            s.legF = 82f - lean;    // nearly level, the heel skimming the ground
            s.kneeF = -6f;
            // The trailing foot scuffs along the ground, quicker the faster the slide.
            float scuff = Mathf.Sin(Time.time * (18f + 12f * (1f - spent))) * 5f * (1f - spent * 0.6f);
            s.legB = 96f - lean + scuff;    // thigh forward and a touch up...
            s.kneeB = -148f + scuff * 1.5f; // ...the shin folded back under it
            s.armB = 24f - lean;    // down along the side to the hand on the ground by the hip
            s.elbowB = 10f;
            s.armF = 95f - lean;    // reaching forward toward the feet for balance (the hand stays under the bar)
            s.elbowF = 30f;
            s.headTilt = -44f;      // chin down against the lean, so the eyes look on ahead
            // The body turns about its own origin, so the hips (above it at rest) swing back and
            // down with the lean; drop the body by what's left to put them at the wanted height.
            float hipAbovePivot = hipHeight - pivotHeight;
            s.bob = slideHipHeight * hipHeight - pivotHeight - hipAbovePivot * Mathf.Cos(lean * Mathf.Deg2Rad);
            // A faint judder while skidding fast over the ground.
            s.bob += Mathf.Sin(Time.time * 47f) * 0.006f * Mathf.Clamp01(speed / 4f);
            return s;
        }

        static RigPose Blend(RigPose a, RigPose b, float t)
        {
            return new RigPose
            {
                legF = Mathf.Lerp(a.legF, b.legF, t), legB = Mathf.Lerp(a.legB, b.legB, t),
                kneeF = Mathf.Lerp(a.kneeF, b.kneeF, t), kneeB = Mathf.Lerp(a.kneeB, b.kneeB, t),
                armF = Mathf.Lerp(a.armF, b.armF, t), armB = Mathf.Lerp(a.armB, b.armB, t),
                elbowF = Mathf.Lerp(a.elbowF, b.elbowF, t), elbowB = Mathf.Lerp(a.elbowB, b.elbowB, t),
                bob = Mathf.Lerp(a.bob, b.bob, t), headTilt = Mathf.Lerp(a.headTilt, b.headTilt, t),
                lean = Mathf.Lerp(a.lean, b.lean, t), bag = Mathf.Lerp(a.bag, b.bag, t),
                squash = Vector2.Lerp(a.squash == Vector2.zero ? Vector2.one : a.squash, b.squash == Vector2.zero ? Vector2.one : b.squash, t),
                shift = Vector2.Lerp(a.shift, b.shift, t),
            };
        }
    }
}
