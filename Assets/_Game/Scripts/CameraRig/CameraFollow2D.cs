using DribbleToSchool.Ball;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.CameraRig
{
    /// <summary>
    /// Side-scroller camera for the 3D street: a perspective camera looking along +z,
    /// tilted down a little so the road and pavements read as ground. It frames a point on
    /// the gameplay plane (z = 0) with look-ahead that grows with run speed, leans toward
    /// the ball, ignores small hops (vertical dead zone) and never shows past the level edges.
    /// An orthographic camera still works (the old flat look).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class CameraFollow2D : MonoBehaviour
    {
        public KidController kid;
        public BallController ball;

        [Header("Framing")]
        [Tooltip("How much the camera leans toward the ball (0 = kid only).")]
        [Range(0f, 1f)] public float ballWeight = 0.3f;
        [Tooltip("Offset from the focus point when standing still.")]
        public Vector2 offset = new Vector2(1.5f, 1.8f);
        [Tooltip("Extra look-ahead per unit of run speed (seconds).")]
        public float lookAheadTime = 0.4f;
        public float maxLookAhead = 2.5f;
        public float lookAheadSmoothing = 0.5f;

        [Header("Smoothing")]
        public float smoothTimeX = 0.15f;
        public float smoothTimeY = 0.35f;
        [Tooltip("The camera ignores vertical movement inside this band (jumps, bounces).")]
        public float verticalDeadZone = 1.2f;

        [Header("Bounds")]
        [Tooltip("Left/right world edges the camera never shows past.")]
        public float minX = -10f;
        public float maxX = 120f;
        [Tooltip("Camera centre never goes below this height.")]
        public float minY = 2f;

        [Header("Perspective")]
        [Tooltip("Half the visible height at the gameplay plane (world units).")]
        public float viewHalfHeight = 4.8f;
        [Tooltip("Downward tilt in degrees, so the street surface shows.")]
        public float pitch = 5f;

        /// <summary>Unzoomed half-height of the view at the gameplay plane, for screen-to-world drag scaling.</summary>
        public static float BaseViewHalfHeight = 4.8f;

        [Header("Feel")]
        [Tooltip("Zoom out by this factor while aiming a kick, to see where it lands.")]
        public float aimZoom = 1.12f;
        public float zoomSpeed = 4f;

        Camera cam;
        Vector2 center;
        float zoom = 1f;
        float velocityX;
        float velocityY;
        float lookAhead;
        float lookAheadVelocity;
        float trackedY;
        float baseSize;
        float shakeAmount;
        float shakeUntil;
        Vector3 shakeOffset;

        void Awake()
        {
            cam = GetComponent<Camera>();
            baseSize = cam.orthographic ? cam.orthographicSize : viewHalfHeight;
            BaseViewHalfHeight = baseSize;
        }

        /// <summary>Distance from the camera to the gameplay plane for a given half-height.</summary>
        float DistanceFor(float halfHeight)
        {
            return halfHeight / Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        }

        float HalfHeight { get { return cam.orthographic ? cam.orthographicSize : viewHalfHeight * zoom; } }

        void Place(Vector2 c, Vector3 shake)
        {
            if (cam.orthographic)
            {
                transform.position = new Vector3(c.x, c.y, transform.position.z) + shake;
                return;
            }
            Quaternion rot = Quaternion.Euler(pitch, 0f, 0f);
            transform.rotation = rot;
            transform.position = new Vector3(c.x, c.y, 0f) - rot * Vector3.forward * DistanceFor(HalfHeight) + shake;
        }

        /// <summary>Brief screen shake (world units). Uses unscaled time so it works in slow motion.</summary>
        public void Shake(float amount, float duration)
        {
            if (Time.unscaledTime >= shakeUntil) shakeAmount = 0f;
            shakeAmount = Mathf.Max(shakeAmount, amount);
            shakeUntil = Mathf.Max(shakeUntil, Time.unscaledTime + duration);
        }

        void Start()
        {
            SnapToTarget();
        }

        void LateUpdate()
        {
            if (kid == null) return;

            // Lean the view the way the kid faces, and further while walking.
            float targetLook = offset.x * kid.Facing + Mathf.Clamp(kid.SpeedX * lookAheadTime, -maxLookAhead, maxLookAhead);
            lookAhead = Mathf.SmoothDamp(lookAhead, targetLook, ref lookAheadVelocity, lookAheadSmoothing);

            Vector2 focus = Focus();
            float desiredY = focus.y + offset.y;
            if (Mathf.Abs(desiredY - trackedY) > verticalDeadZone * 0.5f)
                trackedY = desiredY - Mathf.Sign(desiredY - trackedY) * verticalDeadZone * 0.5f;

            bool aiming = GameInput.Instance != null && GameInput.Instance.KickAiming;
            float k = 1f - Mathf.Exp(-zoomSpeed * Time.unscaledDeltaTime);
            zoom = Mathf.Lerp(zoom, aiming ? aimZoom : 1f, k);
            if (cam.orthographic) cam.orthographicSize = baseSize * zoom;

            Vector2 target = ClampToBounds(new Vector2(focus.x + lookAhead, trackedY));
            center.x = Mathf.SmoothDamp(center.x, target.x, ref velocityX, smoothTimeX);
            center.y = Mathf.SmoothDamp(center.y, target.y, ref velocityY, smoothTimeY);

            shakeOffset = Vector3.zero;
            if (Time.unscaledTime < shakeUntil)
            {
                float t = Time.unscaledTime * 40f;
                shakeOffset = new Vector3(Mathf.PerlinNoise(t, 0.3f) - 0.5f, Mathf.PerlinNoise(0.7f, t) - 0.5f, 0f) * 2f * shakeAmount;
            }

            Place(center, shakeOffset);
        }

        /// <summary>Jump straight to the framing target (level start, respawn).</summary>
        public void SnapToTarget()
        {
            if (kid == null) return;
            lookAhead = offset.x * kid.Facing;
            lookAheadVelocity = velocityX = velocityY = 0f;
            Vector2 focus = Focus();
            trackedY = focus.y + offset.y;
            if (cam == null) cam = GetComponent<Camera>();
            zoom = 1f;
            center = ClampToBounds(new Vector2(focus.x + lookAhead, trackedY));
            shakeOffset = Vector3.zero;
            Place(center, Vector3.zero);
        }

        Vector2 Focus()
        {
            Vector2 focus = kid.transform.position;
            if (ball != null) focus = Vector2.Lerp(focus, ball.transform.position, ballWeight);
            return focus;
        }

        Vector2 ClampToBounds(Vector2 p)
        {
            if (cam == null) cam = GetComponent<Camera>();
            float halfWidth = HalfHeight * cam.aspect;
            float left = minX + halfWidth;
            float right = maxX - halfWidth;
            p.x = left < right ? Mathf.Clamp(p.x, left, right) : (minX + maxX) * 0.5f;
            p.y = Mathf.Max(minY, p.y);
            return p;
        }
    }
}
