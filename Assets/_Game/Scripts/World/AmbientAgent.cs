using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Shared plumbing for the animals that live around the street (Animals kit): a small seeded
    /// random stream (the level builder hands each one its seed), turning smoothly to face where it
    /// goes (models face +x at yaw 0), swinging a part from its rest pose, a baked strip of ground
    /// heights to keep feet on the ground, and resting while far off-screen so dozens of them cost
    /// next to nothing on a phone. Subclasses do their behaviour in <see cref="Tick"/>.
    /// </summary>
    public abstract class AmbientAgent : MonoBehaviour
    {
        [Tooltip("Seed for this animal's own random choices (set by the level builder).")]
        public int seed = 1;
        [Tooltip("Ground heights along x from groundFrom, every groundStep (baked by the level builder); empty: flat at the start height.")]
        public float[] ground = new float[0];
        public float groundFrom;
        public float groundStep = 0.5f;
        [Tooltip("Rests while further than this outside the view's sides (metres).")]
        public float sleepMargin = 12f;

        uint state;
        float nextWake;

        protected virtual void Awake()
        {
            state = (uint)(seed * 2654435761u) ^ 0x9E3779B9u;
            if (state == 0) state = 1;
        }

        protected void Update()
        {
            float dt = Time.deltaTime;
            if (dt <= 0f) return;
            // Far out of sight, check back now and then instead of every frame.
            if (Time.time < nextWake) return;
            Vector3 at = transform.position;
            if (!AmbientView.Valid || AmbientView.OutsideBy(at.x, at.z) > sleepMargin + Reach)
            {
                nextWake = Time.time + 0.5f;
                Sleep();
                return;
            }
            Tick(Mathf.Min(dt, 0.05f));
        }

        /// <summary>How far from where it stands the animal may roam (widens the sleep test).</summary>
        protected virtual float Reach { get { return 0f; } }

        /// <summary>Called instead of Tick while far out of sight.</summary>
        protected virtual void Sleep() { }

        protected abstract void Tick(float dt);

        // ---------------------------------------------------------------- random

        /// <summary>0..1 from this animal's own stream (xorshift: no allocations, repeatable per seed).</summary>
        protected float Rand01()
        {
            state ^= state << 13;
            state ^= state >> 17;
            state ^= state << 5;
            return (state & 0xFFFFFF) / 16777216f;
        }

        protected float Range(float min, float max) { return min + (max - min) * Rand01(); }

        protected bool Chance(float p) { return Rand01() < p; }

        // ---------------------------------------------------------------- ground

        /// <summary>The ground's height at x (from the baked strip), or fallback without one.</summary>
        protected float GroundY(float x, float fallback)
        {
            if (ground == null || ground.Length == 0) return fallback;
            if (ground.Length == 1) return ground[0];
            float f = (x - groundFrom) / Mathf.Max(0.01f, groundStep);
            if (f <= 0f) return ground[0];
            int i = (int)f;
            if (i >= ground.Length - 1) return ground[ground.Length - 1];
            return Mathf.Lerp(ground[i], ground[i + 1], f - i);
        }

        /// <summary>The x range the baked ground strip covers (or the given range without one).</summary>
        protected void GroundRange(ref float min, ref float max)
        {
            if (ground == null || ground.Length < 2) return;
            min = Mathf.Max(min, groundFrom);
            max = Mathf.Min(max, groundFrom + groundStep * (ground.Length - 1));
        }

        // ---------------------------------------------------------------- facing

        /// <summary>Yaw that turns a model's head (+x) toward the direction (dx, dz).</summary>
        public static float YawToward(float dx, float dz)
        {
            return Mathf.Atan2(-dz, dx) * Mathf.Rad2Deg;
        }

        /// <summary>
        /// Yaw for heading along (dx, dz), turned a little toward the camera when going along the
        /// street so the face reads (as the people do, see CharacterRig.FacingYaw).
        /// </summary>
        public static float SideYaw(float dx, float dz, float towardCamera)
        {
            float yaw = YawToward(dx, dz);
            float len = Mathf.Sqrt(dx * dx + dz * dz);
            if (len < 1e-4f) return yaw;
            // +x heading: + towardCamera; -x heading: - towardCamera (both toward yaw 90).
            return yaw + towardCamera * (dx / len);
        }

        // ---------------------------------------------------------------- parts

        /// <summary>A model part swung from its rest pose (kit parts' axes are the model's). A part in links (Tail with
        /// Tail2 and Tail3 under it, WingL with WingL2: the Kamakura kit's) bends link by link (PartChain); one without
        /// moves whole, as before.</summary>
        [System.Serializable]
        public struct Part
        {
            public Transform transform;
            public Vector3 axis;
            [System.NonSerialized] public Quaternion rest;
            [System.NonSerialized] public Vector3 restPosition;
            [System.NonSerialized] public bool ready;
            [System.NonSerialized] public PartChain chain;

            public Part(Transform transform, Vector3 axis)
            {
                this.transform = transform;
                this.axis = axis;
                rest = transform != null ? transform.localRotation : Quaternion.identity;
                restPosition = transform != null ? transform.localPosition : Vector3.zero;
                ready = transform != null;
                chain = Linked(transform, axis);
            }

            public void Capture()
            {
                ready = transform != null;
                if (!ready) return;
                rest = transform.localRotation;
                restPosition = transform.localPosition;
                chain = Linked(transform, axis);
            }

            static PartChain Linked(Transform t, Vector3 axis)
            {
                if (t == null) return null;
                var c = PartChain.Find(t, axis);
                return c.Links > 1 ? c : null;
            }

            public void Set(float degrees)
            {
                if (!ready) return;
                if (chain != null) chain.Set(degrees, Time.deltaTime);
                else transform.localRotation = rest * Quaternion.AngleAxis(degrees, axis);
            }

            /// <summary>Rotate about a second axis as well (in the part's own space).</summary>
            public void Set(float degrees, Vector3 otherAxis, float otherDegrees)
            {
                if (ready) transform.localRotation = rest * Quaternion.AngleAxis(degrees, axis) * Quaternion.AngleAxis(otherDegrees, otherAxis);
            }

            public void Slide(Vector3 localOffset)
            {
                if (ready) transform.localPosition = restPosition + localOffset;
            }
        }

        protected static void Capture(Part[] parts)
        {
            if (parts == null) return;
            for (int i = 0; i < parts.Length; i++) parts[i].Capture();
        }

        /// <summary>Smoothly eased 0..1 (smoothstep).</summary>
        protected static float Ease(float t)
        {
            t = Mathf.Clamp01(t);
            return t * t * (3f - 2f * t);
        }
    }
}
