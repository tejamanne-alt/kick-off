using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.CameraRig
{
    /// <summary>
    /// Side-scroller camera for the 3D street: a perspective camera looking along +z from a
    /// little above the kid's eye height, tilted down a touch so the road and pavements read as
    /// ground. It frames the kid close (about a quarter of the screen tall) with the view ahead
    /// of them, a small lean toward the ball while it is close (never far: the kid is the one played, and a ball
    /// kicked away never drags the view off them; the HUD points at a ball off the screen, UI/BallMarker), a
    /// vertical dead zone for small hops, and never shows past the
    /// level edges. The kid stands where no thumb covers them: a set fraction of the way across the
    /// screen, pushed further right as far as the walk stick's area on the left needs
    /// (GameInput.KidSafeScreenX), a little nearer the middle when still. On narrower screens it pulls back
    /// just enough to keep a minimum stretch of street in view. An orthographic camera still
    /// works (the old flat look).
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class CameraFollow2D : MonoBehaviour
    {
        public KidController kid;
        public BallController ball;

        [Header("Framing")]
        [Tooltip("How much the camera leans toward the ball (0 = kid only), while the ball is close.")]
        [Range(0f, 1f)] public float ballWeight = 0.3f;
        [Tooltip("The view leans toward the ball only while it is this close to the kid (world units): from half this far the lean fades, and past it the view is on the kid alone.")]
        public float ballLeanRange = 6f;
        [Tooltip("At most this far (world units) the view leans toward the ball across the screen.")]
        public float maxBallLean = 1.2f;
        [Tooltip("At most this far (world units) the view leans toward the ball up or down.")]
        public float maxBallLeanUp = 0.5f;
        [Tooltip("The kid is never nearer a side of the screen than this (fraction of its width), however the view leans or lags.")]
        [Range(0.05f, 0.4f)] public float kidEdgeMargin = 0.15f;
        [Tooltip("How far the focus point is above the kid, so their feet sit low in the frame.")]
        public float verticalOffset = 1.0f;
        [Tooltip("Where the kid stands across the screen while walking (0 = left edge, 0.5 = middle), when the buttons leave room for it.")]
        [Range(0.25f, 0.5f)] public float kidScreenX = 0.38f;
        [Tooltip("Keep the kid clear of the control buttons on the left of the screen (GameInput.KidSafeScreenX): further right on narrow screens.")]
        public bool clearOfControls = true;
        [Tooltip("A kid standing still is this much nearer the middle of the screen (fraction of its width) than a walking one: the view leans ahead of a walking kid.")]
        public float walkLean = 0.045f;
        public float lookAheadSmoothing = 0.5f;

        [Header("Smoothing")]
        public float smoothTimeX = 0.15f;
        public float smoothTimeY = 0.35f;
        [Tooltip("The camera ignores vertical movement inside this band (jumps, bounces).")]
        public float verticalDeadZone = 1.1f;

        [Header("Bounds")]
        [Tooltip("Left/right world edges the camera never shows past.")]
        public float minX = -10f;
        public float maxX = 120f;
        [Tooltip("Camera centre never goes below this height.")]
        public float minY = 2f;

        [Header("Perspective")]
        [Tooltip("Half the visible height at the gameplay plane (world units): 2.2 shows 4.4 m, so the kid is about 40 % of the screen tall.")]
        public float viewHalfHeight = 2.2f;
        [Tooltip("At least this much of the street either side of the view's centre (world units); narrower screens pull back to keep it.")]
        public float minHalfWidth = 4.5f;
        [Tooltip("Downward tilt in degrees, so the street surface shows.")]
        public float pitch = 4f;

        /// <summary>Unzoomed half-height of the view at the gameplay plane, for screen-to-world drag scaling.</summary>
        public static float BaseViewHalfHeight = 2.2f;

        [Header("Feel")]
        [Tooltip("Zoom out by this factor while aiming a kick, to see where it lands.")]
        public float aimZoom = 1.2f;
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
        float punch, punchVelocity, punchTime = 0.2f;

        void Awake()
        {
            cam = GetComponent<Camera>();
            baseSize = cam.orthographic ? cam.orthographicSize : FramedHalfHeight;
            BaseViewHalfHeight = baseSize;
        }

        /// <summary>Distance from the camera to the gameplay plane for a given half-height.</summary>
        float DistanceFor(float halfHeight)
        {
            return halfHeight / Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        }

        /// <summary>The unzoomed half-height: the close framing, or a little further out on a narrow screen.</summary>
        float FramedHalfHeight { get { return Mathf.Max(viewHalfHeight, minHalfWidth / Mathf.Max(cam.aspect, 0.1f)); } }

        float HalfHeight { get { return cam.orthographic ? cam.orthographicSize : FramedHalfHeight * zoom * (1f + punch); } }

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

        /// <summary>
        /// A quick push of the view that eases back on its own: <paramref name="amount"/> above 0 pulls
        /// the camera out (room for a somersault), below 0 pushes it in (the lunge of a slide), about
        /// 0.03 being a clearly felt nudge. Works in slow motion; off with the screen-shake setting.
        /// </summary>
        public void Punch(float amount, float seconds)
        {
            if (!GameSettings.ScreenShakeEnabled) return;
            punch = Mathf.Clamp(amount, -0.15f, 0.15f);
            punchTime = Mathf.Max(0.05f, seconds);
        }

        void Start()
        {
            SnapToTarget();
        }

        void LateUpdate()
        {
            if (kid == null) return;

            // Lean the view the way the kid faces, so they stand at their place across the screen: further
            // over (clear of the thumb) while walking, a little nearer the middle when still.
            float walking = Mathf.Clamp01(Mathf.Abs(kid.SpeedX) / Mathf.Max(0.1f, kid.RunSpeed));
            float targetLook = LeadFor(KidScreenX + walkLean * (1f - walking), HalfWidth) * kid.Facing;
            lookAhead = Mathf.SmoothDamp(lookAhead, targetLook, ref lookAheadVelocity, lookAheadSmoothing);

            Vector2 focus = Focus();
            float desiredY = focus.y + verticalOffset;
            if (Mathf.Abs(desiredY - trackedY) > verticalDeadZone * 0.5f)
                trackedY = desiredY - Mathf.Sign(desiredY - trackedY) * verticalDeadZone * 0.5f;

            bool aiming = GameInput.Instance != null && GameInput.Instance.KickAiming;
            float k = 1f - Mathf.Exp(-zoomSpeed * Time.unscaledDeltaTime);
            zoom = Mathf.Lerp(zoom, aiming ? aimZoom : 1f, k);
            punch = Mathf.SmoothDamp(punch, 0f, ref punchVelocity, punchTime, Mathf.Infinity, Time.unscaledDeltaTime);
            if (cam.orthographic) cam.orthographicSize = baseSize * zoom * (1f + punch);

            float kidX = kid.transform.position.x;
            Vector2 target = ClampToBounds(new Vector2(KeepInView(focus.x + lookAhead, kidX, HalfWidth, kidEdgeMargin), trackedY));
            center.x = Mathf.SmoothDamp(center.x, target.x, ref velocityX, smoothTimeX);
            center.y = Mathf.SmoothDamp(center.y, target.y, ref velocityY, smoothTimeY);
            // However fast the kid goes (a trampoline's throw, a moving pallet), the smoothing never leaves them at the edge.
            center.x = ClampToBounds(new Vector2(KeepInView(center.x, kidX, HalfWidth, kidEdgeMargin * 0.5f), center.y)).x;

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
            if (cam == null) cam = GetComponent<Camera>();
            zoom = 1f;
            punch = punchVelocity = 0f;
            lookAhead = LeadFor(KidScreenX + walkLean, HalfWidth) * kid.Facing;
            lookAheadVelocity = velocityX = velocityY = 0f;
            Vector2 focus = Focus();
            trackedY = focus.y + verticalOffset;
            center = ClampToBounds(new Vector2(KeepInView(focus.x + lookAhead, kid.transform.position.x, HalfWidth, kidEdgeMargin), trackedY));
            shakeOffset = Vector3.zero;
            Place(center, Vector3.zero);
        }

        /// <summary>Half the visible width at the gameplay plane (world units).</summary>
        float HalfWidth { get { return HalfHeight * (cam != null ? Mathf.Max(0.1f, cam.aspect) : 16f / 9f); } }

        /// <summary>
        /// Where the kid stands across the screen while walking: <see cref="kidScreenX"/>, or further right as far
        /// as the buttons on the left of the screen need (so a thumb on them never hides the kid), never past the middle.
        /// </summary>
        float KidScreenX
        {
            get
            {
                float x = kidScreenX;
                var input = GameInput.Instance;
                if (clearOfControls && input != null) x = Mathf.Max(x, input.KidSafeScreenX);
                return Mathf.Clamp(x, 0.25f, 0.5f);
            }
        }

        /// <summary>
        /// How far (metres) the view's centre leads a kid facing +x for them to stand at <paramref name="screenX"/>
        /// (0 = left edge, 1 = right edge) of a view <paramref name="halfWidth"/> metres either side of its centre.
        /// </summary>
        public static float LeadFor(float screenX, float halfWidth)
        {
            return (0.5f - screenX) * 2f * halfWidth;
        }

        /// <summary>The kid, leaned a little toward the ball while it is close (<see cref="BallLean"/>).</summary>
        Vector2 Focus()
        {
            Vector2 focus = kid.transform.position;
            if (ball != null) focus += BallLean((Vector2)ball.transform.position - focus, ballWeight, ballLeanRange, maxBallLean, maxBallLeanUp);
            return focus;
        }

        /// <summary>
        /// How far the view leans from the kid toward a ball <paramref name="offset"/> away: <paramref name="weight"/> of the way while
        /// it is within half of <paramref name="range"/>, fading to nothing at <paramref name="range"/>, and never more than
        /// <paramref name="maxAcross"/> across or <paramref name="maxUp"/> up or down. A ball kicked far away leaves the view on the kid.
        /// </summary>
        public static Vector2 BallLean(Vector2 offset, float weight, float range, float maxAcross, float maxUp)
        {
            float half = Mathf.Max(0.01f, range * 0.5f);
            float fade = 1f - Mathf.Clamp01((offset.magnitude - half) / half);
            Vector2 lean = offset * (weight * fade);
            return new Vector2(Mathf.Clamp(lean.x, -maxAcross, maxAcross), Mathf.Clamp(lean.y, -maxUp, maxUp));
        }

        /// <summary>
        /// The view's centre <paramref name="centerX"/> moved just enough that the kid at <paramref name="kidX"/> stands at least
        /// <paramref name="margin"/> of the screen's width in from either side, for a view <paramref name="halfWidth"/> either side of its centre.
        /// </summary>
        public static float KeepInView(float centerX, float kidX, float halfWidth, float margin)
        {
            float reach = Mathf.Max(0f, 0.5f - margin) * 2f * halfWidth;
            return Mathf.Clamp(centerX, kidX - reach, kidX + reach);
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
