using DribbleToSchool.Ball;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.CameraRig
{
    /// <summary>
    /// Side-scroller camera: keeps the kid on the left third with look-ahead
    /// that grows with run speed, leans toward the ball, ignores small hops
    /// (vertical dead zone) and never shows past the level edges.
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

        [Header("Feel")]
        [Tooltip("Zoom out by this factor while aiming a kick, to see where it lands.")]
        public float aimZoom = 1.12f;
        public float zoomSpeed = 4f;

        Camera cam;
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
            baseSize = cam.orthographicSize;
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

            float targetLook = Mathf.Clamp(kid.SpeedX * lookAheadTime, 0f, maxLookAhead);
            lookAhead = Mathf.SmoothDamp(lookAhead, targetLook, ref lookAheadVelocity, lookAheadSmoothing);

            Vector2 focus = Focus();
            float desiredY = focus.y + offset.y;
            if (Mathf.Abs(desiredY - trackedY) > verticalDeadZone * 0.5f)
                trackedY = desiredY - Mathf.Sign(desiredY - trackedY) * verticalDeadZone * 0.5f;

            bool aiming = GameInput.Instance != null && GameInput.Instance.KickAiming;
            float wantedSize = baseSize * (aiming ? aimZoom : 1f);
            cam.orthographicSize = Mathf.Lerp(cam.orthographicSize, wantedSize, 1f - Mathf.Exp(-zoomSpeed * Time.unscaledDeltaTime));

            Vector2 target = ClampToBounds(new Vector2(focus.x + offset.x + lookAhead, trackedY));
            Vector3 pos = transform.position - shakeOffset;
            pos.x = Mathf.SmoothDamp(pos.x, target.x, ref velocityX, smoothTimeX);
            pos.y = Mathf.SmoothDamp(pos.y, target.y, ref velocityY, smoothTimeY);

            shakeOffset = Vector3.zero;
            if (Time.unscaledTime < shakeUntil)
            {
                float t = Time.unscaledTime * 40f;
                shakeOffset = new Vector3(Mathf.PerlinNoise(t, 0.3f) - 0.5f, Mathf.PerlinNoise(0.7f, t) - 0.5f, 0f) * 2f * shakeAmount;
            }

            transform.position = pos + shakeOffset;
        }

        /// <summary>Jump straight to the framing target (level start, respawn).</summary>
        public void SnapToTarget()
        {
            if (kid == null) return;
            lookAhead = 0f;
            lookAheadVelocity = velocityX = velocityY = 0f;
            Vector2 focus = Focus();
            trackedY = focus.y + offset.y;
            Vector2 target = ClampToBounds(new Vector2(focus.x + offset.x, trackedY));
            transform.position = new Vector3(target.x, target.y, transform.position.z);
            shakeOffset = Vector3.zero;
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
            float halfWidth = cam.orthographicSize * cam.aspect;
            float left = minX + halfWidth;
            float right = maxX - halfWidth;
            p.x = left < right ? Mathf.Clamp(p.x, left, right) : (minX + maxX) * 0.5f;
            p.y = Mathf.Max(minY, p.y);
            return p;
        }
    }
}
