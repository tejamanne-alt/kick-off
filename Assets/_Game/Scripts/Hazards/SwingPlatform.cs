using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>A playground swing seat on ropes: a pendulum platform that carries the kid.</summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class SwingPlatform : HazardBase, IMovingSurface
    {
        public Vector2 pivot;
        public float ropeLength = 2.5f;
        [Tooltip("Swing amplitude in degrees.")]
        public float amplitude = 40f;
        public float period = 3f;
        public float phaseOffset;
        public LineRenderer rope;

        public Vector2 SurfaceVelocity { get; private set; }

        Rigidbody2D body;
        float time;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Vector2 p = PositionAt(time);
            body.position = p;
            transform.position = p;
            SurfaceVelocity = Vector2.zero;
        }

        Vector2 PositionAt(float t)
        {
            float angle = amplitude * Mathf.Deg2Rad * Mathf.Sin(t / period * Mathf.PI * 2f);
            return pivot + new Vector2(Mathf.Sin(angle), -Mathf.Cos(angle)) * ropeLength;
        }

        void FixedUpdate()
        {
            time += Time.fixedDeltaTime;
            Vector2 target = PositionAt(time);
            SurfaceVelocity = (target - body.position) / Time.fixedDeltaTime;
            body.MovePosition(target);
        }

        void LateUpdate()
        {
            if (rope == null) return;
            rope.SetPosition(0, pivot);
            rope.SetPosition(1, transform.position);
        }
    }
}
