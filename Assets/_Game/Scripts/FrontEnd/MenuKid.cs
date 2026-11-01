using DribbleToSchool.Presentation;
using UnityEngine;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The menu's teen doing keepy-uppy: the ball pops up off one foot, then the other, every
    /// few touches off a raised thigh, while the standing knee gives a little, the arms keep
    /// balance and the head follows the ball. Between touches the ball flies a real parabola
    /// from one contact to the next, spinning. The teen turns three-quarters to the camera,
    /// facing <see cref="facing"/> on screen. On the boy and on the girl (CharacterChoice shows
    /// one; only the shown one runs and moves the ball). Poses a CharacterRig like KidAnimator.
    /// </summary>
    [RequireComponent(typeof(CharacterRig))]
    public class MenuKid : MonoBehaviour
    {
        public Camera cam;
        public Transform ball;
        [Tooltip("The ball's soft shadow on the ground (a sprite lying flat).")]
        public SpriteRenderer ballShadow;
        public float ballRadius = 0.17f;
        [Tooltip("Height of the ground under the teen (world y).")]
        public float groundY;
        [Tooltip("Seconds between touches off the foot.")]
        public float touchInterval = 0.74f;
        [Tooltip("How high the ball rises above a foot touch (metres).")]
        public float popHeight = 0.72f;
        [Tooltip("Turn toward the camera from side-on, in degrees (90 faces it).")]
        public float turnToCamera = 48f;
        [Tooltip("Which way the teen faces on screen: -1 left, +1 right.")]
        public float facing = -1f;

        enum Touch { FootFront, FootBack, Thigh }

        CharacterRig rig;
        Transform visual, footFront, footBack;
        // Where the ball meets the teen for each touch, in the visual's space (measured from the poses).
        Vector3 contactFront, contactBack, contactThigh;
        float cycleStart, yaw, yawVelocity, appearTime;
        bool measured;

        void Awake()
        {
            rig = GetComponent<CharacterRig>();
            visual = transform.parent;
            footFront = Foot(rig.kneeFront);
            footBack = Foot(rig.kneeBack);
        }

        void OnEnable()
        {
            // Starts (or restarts, after a switch of teen) with a touch, so the ball is at a foot.
            cycleStart = Time.unscaledTime + 0.05f;
            appearTime = Time.unscaledTime;
        }

        void Start()
        {
            Measure();
            yaw = TargetYaw();
        }

        static Transform Foot(Transform knee)
        {
            if (knee == null) return null;
            for (int i = 0; i < knee.childCount; i++)
                if (knee.GetChild(i).name.StartsWith("Foot")) return knee.GetChild(i);
            return knee.childCount > 0 ? knee.GetChild(0) : null;
        }

        /// <summary>Pose each touch once and note where the ball meets the foot or the thigh.</summary>
        void Measure()
        {
            if (visual == null) return;
            rig.Pose(TouchPose(Touch.FootFront, 1f));
            contactFront = visual.InverseTransformPoint(FootPoint(footFront, rig.kneeFront));
            rig.Pose(TouchPose(Touch.FootBack, 1f));
            contactBack = visual.InverseTransformPoint(FootPoint(footBack, rig.kneeBack));
            rig.Pose(TouchPose(Touch.Thigh, 1f));
            Vector3 knee = rig.kneeFront != null ? rig.kneeFront.position : visual.position + Vector3.up;
            contactThigh = visual.InverseTransformPoint(knee + Vector3.up * (ballRadius + 0.06f));
            // Balls are met a little in front of the shin, off the laces.
            Vector3 forward = Vector3.right * 0.08f;
            contactFront += forward + Vector3.up * ballRadius;
            contactBack += forward + Vector3.up * ballRadius;
            contactThigh += Vector3.right * 0.04f;
            rig.Pose(RigPose.Neutral);
            measured = true;
        }

        Vector3 FootPoint(Transform foot, Transform knee)
        {
            if (foot != null) return foot.position;
            return knee != null ? knee.position + Vector3.down * 0.42f : visual.position;
        }

        Touch TouchAt(int k)
        {
            if (k % 5 == 4) return Touch.Thigh;
            return k % 2 == 0 ? Touch.FootFront : Touch.FootBack;
        }

        Vector3 ContactOf(Touch touch)
        {
            switch (touch)
            {
                case Touch.FootBack: return contactBack;
                case Touch.Thigh: return contactThigh;
                default: return contactFront;
            }
        }

        /// <summary>The pose at a touch, <paramref name="k"/> = 1 at the moment of contact, 0 at rest.</summary>
        static RigPose TouchPose(Touch touch, float k)
        {
            var p = Balance(0f);
            switch (touch)
            {
                case Touch.FootFront:
                    p.legF = Mathf.Lerp(p.legF, 42f, k); p.kneeF = Mathf.Lerp(p.kneeF, -58f, k);
                    p.kneeB = Mathf.Lerp(p.kneeB, -14f, k);
                    break;
                case Touch.FootBack:
                    p.legB = Mathf.Lerp(p.legB, 42f, k); p.kneeB = Mathf.Lerp(p.kneeB, -58f, k);
                    p.kneeF = Mathf.Lerp(p.kneeF, -14f, k);
                    break;
                default:
                    p.legF = Mathf.Lerp(p.legF, 86f, k); p.kneeF = Mathf.Lerp(p.kneeF, -96f, k);
                    p.kneeB = Mathf.Lerp(p.kneeB, -12f, k);
                    break;
            }
            p.lean = Mathf.Lerp(p.lean, -4f, k);
            p.bob = -0.025f * k;
            return p;
        }

        /// <summary>Standing between touches: soft knees, arms a little forward and bent for balance.</summary>
        static RigPose Balance(float breathe)
        {
            var p = RigPose.Neutral;
            p.kneeF = p.kneeB = -8f;
            p.legF = 4f; p.legB = -2f;
            p.armF = 22f + breathe * 3f; p.elbowF = 34f;
            p.armB = -16f - breathe * 3f; p.elbowB = 28f;
            p.squash = new Vector2(1f - breathe * 0.012f, 1f + breathe * 0.012f);
            return p;
        }

        float TargetYaw()
        {
            // Side-on to the camera, then turned toward it: three-quarters, facing left or right on screen.
            Vector3 view = cam != null ? cam.transform.forward : Vector3.forward;
            view.y = 0f;
            if (view.sqrMagnitude < 1e-4f) view = Vector3.forward;
            float viewYaw = Mathf.Atan2(view.x, view.z) * Mathf.Rad2Deg;
            // A model facing +x has yaw 0; facing screen-right means facing along the camera's right.
            float side = facing >= 0f ? viewYaw + 90f : viewYaw - 90f;
            float toCamera = viewYaw + 180f;
            float dir = Mathf.LerpAngle(side, toCamera, turnToCamera / 90f);
            return dir - 90f;   // Unity yaw of a +x-facing model turned to face compass direction dir
        }

        void LateUpdate()
        {
            if (!measured || visual == null) return;
            float now = Time.unscaledTime;

            // Turn to face the way the shot wants, easing round when the camera moves: toward the
            // logo on the title screen, toward the items in the Locker Room.
            var stage = MenuStage.Current;
            if (stage != null) facing = stage.Shot == MenuShot.Locker ? 1f : -1f;
            yaw =Mathf.SmoothDampAngle(yaw, TargetYaw(), ref yawVelocity, 0.35f, Mathf.Infinity, Time.unscaledDeltaTime);
            visual.localRotation = Quaternion.Euler(0f, yaw, 0f);

            // Which touch we are between: k is the last one, k + 1 the next.
            float u = Mathf.Max(0f, now - cycleStart) / touchInterval;
            int k = Mathf.FloorToInt(u);
            float s = u - k;
            Touch from = TouchAt(k), to = TouchAt(k + 1);

            // The pose: each touch eases in before its contact and out after it.
            float breathe = Mathf.Sin(now * 2.4f);
            var pose = Balance(breathe);
            float before = Mathf.Clamp01(1f - (1f - s) * touchInterval / 0.22f);   // rising into the next touch
            float after = Mathf.Clamp01(1f - s * touchInterval / 0.26f);           // falling back from the last
            pose = Mix(pose, TouchPose(to, 1f), Smooth(before));
            pose = Mix(pose, TouchPose(from, 1f), Smooth(after));

            // The ball: a parabola from this contact to the next, higher off the thigh.
            Vector3 a = visual.TransformPoint(ContactOf(from));
            Vector3 b = visual.TransformPoint(ContactOf(to));
            float height = popHeight * (from == Touch.Thigh ? 0.85f : 1f);
            Vector3 p = Vector3.Lerp(a, b, s) + Vector3.up * (4f * height * s * (1f - s));
            float heightNorm = Mathf.Clamp01((p.y - a.y) / Mathf.Max(0.1f, height));
            pose.headTilt = Mathf.Lerp(-20f, -6f, heightNorm);   // eyes on the ball

            // Pop in when this teen appears (a switch in Settings).
            float pop = Mathf.Clamp01((now - appearTime) / 0.3f);
            float squash = Mathf.Sin(pop * Mathf.PI) * 0.08f * (1f - pop);
            pose.squash = new Vector2(pose.squash.x * (1f + squash), pose.squash.y * (1f - squash));
            rig.Pose(pose);

            if (ball != null)
            {
                ball.position = p;
                // The ball's drawing faces the camera; it spins about the view axis.
                Vector3 toCam = cam != null ? cam.transform.forward : Vector3.forward;
                ball.rotation = Quaternion.LookRotation(toCam) * Quaternion.Euler(0f, 0f, -now * 260f);
            }
            if (ballShadow != null)
            {
                float lift = Mathf.Clamp01((p.y - groundY) / 1.6f);
                ballShadow.transform.position = new Vector3(p.x, groundY + 0.012f, p.z);
                ballShadow.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                float scale = Mathf.Lerp(1f, 0.55f, lift);
                Vector2 size = ballShadow.sprite != null ? (Vector2)ballShadow.sprite.bounds.size : Vector2.one;
                ballShadow.transform.localScale = new Vector3(ballRadius * 2.2f * scale / Mathf.Max(size.x, 0.01f), ballRadius * 2.2f * scale / Mathf.Max(size.y, 0.01f), 1f);
                Color c = ballShadow.color;
                c.a = Mathf.Lerp(0.38f, 0.1f, lift);
                ballShadow.color = c;
            }
        }

        static float Smooth(float t)
        {
            return t * t * (3f - 2f * t);
        }

        static RigPose Mix(RigPose a, RigPose b, float t)
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
            };
        }
    }
}
