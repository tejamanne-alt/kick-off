using DribbleToSchool.Audio;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A bascule drawbridge over a canal (the Florida add-on's Home Street): two leaves hinged at the banks that tip up to let
    /// the boats through, on a cycle the kid learns to time. Down; then a warning (the bells, the flashing lights, the gate arms
    /// swinging down across the way); the leaves rise, stay up a moment, and come down again, the arms lifting after them. The
    /// canal under it is too wide to jump, so the way over is to wait for the bridge. A kid or a ball on a leaf as it rises
    /// slides back down it to its own bank (the leaf tips up from the middle), never into the water; what does fall goes in the
    /// canal's lose zone and back to the checkpoint. Each leaf is a kinematic body turned about its hinge, so the kid and the ball
    /// ride and slide on it as on any ground.
    /// </summary>
    public class Drawbridge : HazardBase
    {
        [Tooltip("The leaves' bodies, each with its pivot at its hinge: the left one opens counter-clockwise, the right one clockwise.")]
        public Rigidbody2D leftLeaf, rightLeaf;
        [Tooltip("How far up the leaves open (degrees).")]
        public float openAngle = 78f;
        [Header("The cycle (seconds)")]
        public float downTime = 6f;
        public float warnTime = 1.6f;
        public float raiseTime = 2.2f;
        public float upTime = 2.4f;
        public float lowerTime = 2.2f;
        public float phaseOffset;

        [Header("Signals")]
        [Tooltip("The footpath's gate arms: each turns down from upright (about its own x) by armDrop degrees while the bridge is not down.")]
        public Transform[] arms;
        public float armDrop = 90f;
        [Tooltip("The warning lights, flashed in turn while the bridge is not down.")]
        public Renderer[] lights;
        [Tooltip("How near (m, along the street) the camera's kid must be to hear the bells.")]
        public float hearing = 26f;

        /// <summary>The leaves are down and the way over is open.</summary>
        public bool IsOpenToWalk { get; private set; }

        float time;
        float lastBell = -10f;
        Quaternion[] armRest;
        int shownFlash = -1;

        float Period { get { return downTime + warnTime + raiseTime + upTime + lowerTime; } }

        void Awake()
        {
            if (arms != null)
            {
                armRest = new Quaternion[arms.Length];
                for (int i = 0; i < arms.Length; i++) if (arms[i] != null) armRest[i] = arms[i].localRotation;
            }
            foreach (var body in new[] { leftLeaf, rightLeaf })
                if (body != null)
                {
                    body.bodyType = RigidbodyType2D.Kinematic;
                    body.interpolation = RigidbodyInterpolation2D.Interpolate;
                }
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Pose(true);
        }

        void FixedUpdate()
        {
            time += Time.fixedDeltaTime;
            Pose(false);
        }

        /// <summary>How open the leaves are now (0 down, 1 fully up), and how far down the arms (0 up, 1 lowered).</summary>
        void Phase(out float lift, out float arm, out bool warning)
        {
            float t = Mathf.Repeat(time, Period);
            warning = false;
            if (t < downTime) { lift = 0f; arm = 0f; return; }
            t -= downTime;
            if (t < warnTime) { lift = 0f; arm = Ease(t / warnTime); warning = true; return; }
            t -= warnTime;
            if (t < raiseTime) { lift = Ease(t / raiseTime); arm = 1f; warning = true; return; }
            t -= raiseTime;
            if (t < upTime) { lift = 1f; arm = 1f; warning = true; return; }
            t -= upTime;
            lift = 1f - Ease(t / lowerTime);
            arm = lift > 0.02f ? 1f : 0f;
            warning = lift > 0.02f;
        }

        void Pose(bool snap)
        {
            float lift, arm;
            bool warning;
            Phase(out lift, out arm, out warning);
            IsOpenToWalk = lift < 0.01f && !warning;
            float angle = lift * openAngle;
            Turn(leftLeaf, angle, snap);
            Turn(rightLeaf, -angle, snap);

            if (arms != null && armRest != null)
                for (int i = 0; i < arms.Length; i++)
                    if (arms[i] != null) arms[i].localRotation = armRest[i] * Quaternion.Euler(-armDrop * arm, 0f, 0f);

            // The lights flash in turn while the bridge isn't down; the bells ring with them (when the kid is near enough to hear).
            int flash = warning ? (Mathf.FloorToInt(time * 2.5f) % 2) : -1;
            if (flash != shownFlash && lights != null)
            {
                for (int i = 0; i < lights.Length; i++)
                    if (lights[i] != null) lights[i].enabled = warning && (i % 2) == flash;
                shownFlash = flash;
            }
            if (warning && !snap && Time.time - lastBell > 0.8f && Near())
            {
                lastBell = Time.time;
                AudioDirector.Play(Sfx.Beep, 0.35f, 1.25f);
            }
        }

        static void Turn(Rigidbody2D leaf, float angle, bool snap)
        {
            if (leaf == null) return;
            if (snap)
            {
                leaf.rotation = angle;
                leaf.transform.rotation = Quaternion.Euler(0f, 0f, angle);
            }
            else leaf.MoveRotation(angle);
        }

        bool Near()
        {
            var kid = Kid;
            return kid != null && Mathf.Abs(kid.transform.position.x - transform.position.x) < hearing;
        }

        static float Ease(float t)
        {
            t = Mathf.Clamp01(t);
            return t * t * (3f - 2f * t);
        }
    }
}
