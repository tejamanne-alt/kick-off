using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Kinematic platform that travels between its start and an offset, pausing
    /// at each end. Carries the kid (via IMovingSurface) and the ball (friction).
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class MovingPlatform : HazardBase, IMovingSurface
    {
        [Tooltip("Travel from the start position, in world units.")]
        public Vector2 travel = new Vector2(4f, 0f);
        public float speed = 1.5f;
        public float waitTime = 0.6f;

        public Vector2 SurfaceVelocity { get; private set; }

        Rigidbody2D body;
        Vector2 start;
        float progress;     // 0..1 along the path
        int direction = 1;
        float waitUntil;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            start = body.position;
        }

        public override void ResetState()
        {
            progress = 0f;
            direction = 1;
            waitUntil = 0f;
            body.position = start;
            transform.position = start;
            SurfaceVelocity = Vector2.zero;
        }

        void FixedUpdate()
        {
            float length = travel.magnitude;
            if (length < 0.01f || Time.time < waitUntil)
            {
                SurfaceVelocity = Vector2.zero;
                return;
            }

            progress += direction * speed * Time.fixedDeltaTime / length;
            if (progress >= 1f || progress <= 0f)
            {
                progress = Mathf.Clamp01(progress);
                direction = -direction;
                waitUntil = Time.time + waitTime;
            }

            Vector2 target = start + travel * EaseInOut(progress);
            SurfaceVelocity = (target - body.position) / Time.fixedDeltaTime;
            body.MovePosition(target);
        }

        static float EaseInOut(float t)
        {
            return t * t * (3f - 2f * t);
        }
    }
}
