using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using UnityEngine;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>Where the menu's camera looks (see <see cref="MenuStage"/>).</summary>
    public enum MenuShot
    {
        /// <summary>Down the home street, the teen juggling in the screen rect the title screen gives.</summary>
        Title,
        /// <summary>Tilted up from the title shot to the sky and the clouds over the rooftops: a calm backdrop for busy screens.</summary>
        Sky,
        /// <summary>The teen standing in the Locker Room's showcase, trying things on.</summary>
        Locker,
    }

    /// <summary>
    /// The menu's live 3D backdrop: a short stretch of the home street in the game's clear
    /// daylight (built by LevelBuildKit.BuildMenuStage with the levels' own builders), the
    /// chosen kid juggling a ball on the footpath (MenuKid; CharacterChoice swaps the playable
    /// kids live), real clouds, and a camera that frames the teen wherever a screen
    /// wants it, eases between shots and drifts gently. The CosmeticApplier dresses the teen
    /// and the ball in what is equipped; the Locker Room tries things on with <see cref="TryOn"/>.
    /// </summary>
    public class MenuStage : MonoBehaviour
    {
        public static MenuStage Current { get; private set; }

        public Camera cam;
        [Tooltip("The kid's root (CharacterChoice); its feet are at feet.")]
        public Transform teen;
        public Transform feet;
        [Tooltip("Dresses the kid and the ball in the equipped cosmetics.")]
        public CosmeticApplier applier;

        [Header("Camera")]
        [Tooltip("Vertical field of view (the game's camera uses 34).")]
        public float fieldOfView = 34f;
        [Tooltip("Compass direction the camera looks in, degrees from straight into the street (+z); negative looks down the street to the left.")]
        public float yaw = -58f;
        [Tooltip("Degrees the camera tilts up in the title shot: low, the teen against the sky.")]
        public float pitch = 3f;
        [Tooltip("Tilt in the locker shot: at eye level, looking a little down at the teen standing in the showcase.")]
        public float lockerPitch = -6f;
        [Tooltip("Extra tilt up for the sky shot.")]
        public float skyTilt = 24f;
        [Tooltip("Seconds to ease from one shot to the next.")]
        public float transition = 0.9f;
        [Tooltip("How far the camera drifts (metres) and turns (degrees), very slowly.")]
        public float drift = 0.12f;
        public float driftTurn = 1.2f;

        /// <summary>How tall the chosen kid stands (PlayerRoster), for framing: a primary-school kid fills the shot like a teen.</summary>
        float KidHeight { get { return PlayerRoster.Get(GameSettings.Character).height; } }

        MenuShot shot = MenuShot.Title;
        Rect target = new Rect(0.4f, 0.16f, 0.6f, 0.62f);
        // The title screen's framing, which the sky shot tilts up from.
        Rect titleRect = new Rect(0.4f, 0.16f, 0.6f, 0.62f);
        Vector3 position, velocity;
        Quaternion rotation;
        bool framed, placed;

        /// <summary>The shot the camera is in or easing toward.</summary>
        public MenuShot Shot { get { return shot; } }

        /// <summary>
        /// True while a screen hides the whole view under something opaque (the map's mat): the camera then draws
        /// nothing, no shadows, no filter, only a clear, and is put back as it was when that screen goes. The street
        /// and the teen go on moving, so they are exactly where they would have been.
        /// </summary>
        public bool Covered
        {
            get { return covered; }
            set
            {
                if (value == covered || cam == null) return;
                covered = value;
                if (covered)
                {
                    coveredMask = cam.cullingMask;
                    coveredClear = cam.clearFlags;
                    cam.cullingMask = 0;
                    cam.clearFlags = CameraClearFlags.SolidColor;
                    var post = cam.GetComponent<World.PostFX>();
                    if (post != null && post.enabled) { post.enabled = false; pausedPost = post; }
                }
                else
                {
                    cam.cullingMask = coveredMask;
                    cam.clearFlags = coveredClear;
                    if (pausedPost != null) pausedPost.enabled = true;
                    pausedPost = null;
                }
            }
        }

        bool covered;
        int coveredMask;
        CameraClearFlags coveredClear;
        World.PostFX pausedPost;

        void Awake()
        {
            Current = this;
            if (cam == null) cam = GetComponentInChildren<Camera>();
        }

        void OnDestroy()
        {
            if (Current == this) Current = null;
        }

        /// <summary>
        /// Ease to <paramref name="next"/>, with the teen's feet and head filling the bottom and top
        /// of <paramref name="viewportRect"/> (viewport coordinates, 0..1 from the bottom left).
        /// </summary>
        public void Frame(MenuShot next, Rect viewportRect)
        {
            shot = next;
            target = viewportRect;
            if (next == MenuShot.Title) titleRect = viewportRect;
            framed = true;
        }

        /// <summary>Show a Locker Room item on the teen or the ball without equipping it.</summary>
        /// <summary>The kid turns to show their back (the Locker Room's Bags tab), still juggling.</summary>
        public bool ShowBack { get; set; }

        public void TryOn(CosmeticItem item)
        {
            if (applier != null) applier.Preview(item);
        }

        /// <summary>Back to what is equipped.</summary>
        public void ResetLook()
        {
            if (applier != null) applier.Apply();
        }

        /// <summary>The teen on screen (pixels, from the bottom left), for a tap zone over them.</summary>
        public Rect TeenScreenRect()
        {
            if (cam == null || feet == null) return new Rect();
            Vector3 a = cam.WorldToScreenPoint(feet.position);
            Vector3 b = cam.WorldToScreenPoint(feet.position + Vector3.up * KidHeight);
            float h = Mathf.Abs(b.y - a.y);
            return new Rect(a.x - h * 0.24f, Mathf.Min(a.y, b.y), h * 0.48f, h);
        }

        void LateUpdate()
        {
            // Wait for a screen to say where to look, then cut straight there.
            if (cam == null || feet == null || !framed) return;
            cam.fieldOfView = fieldOfView;
            Vector3 goalPos;
            Quaternion goalRot;
            Solve(out goalPos, out goalRot);

            if (!placed)
            {
                placed = true;
                position = goalPos;
                rotation = goalRot;
            }
            float dt = Time.unscaledDeltaTime;
            position = Vector3.SmoothDamp(position, goalPos, ref velocity, transition * 0.35f, Mathf.Infinity, dt);
            rotation = Quaternion.Slerp(rotation, goalRot, 1f - Mathf.Exp(-dt * 4.5f / Mathf.Max(0.1f, transition)));

            // A slow sway, like a camera on someone's shoulder across the road.
            float t = Time.unscaledTime;
            Vector3 sway = rotation * new Vector3(Mathf.Sin(t * 0.21f) * drift, Mathf.Sin(t * 0.13f + 1f) * drift * 0.5f, Mathf.Sin(t * 0.17f + 2f) * drift);
            Quaternion turn = Quaternion.Euler(Mathf.Sin(t * 0.11f + 0.5f) * driftTurn * 0.4f, Mathf.Sin(t * 0.09f) * driftTurn, 0f);
            cam.transform.SetPositionAndRotation(position + sway, rotation * turn);
        }

        /// <summary>
        /// Where the camera goes for the current shot: looking along <see cref="yaw"/> and
        /// <see cref="pitch"/>, and back far enough, and to the side, that the teen fills the
        /// target rect on this screen's aspect ratio.
        /// </summary>
        void Solve(out Vector3 pos, out Quaternion rot)
        {
            float aspect = cam.aspect > 0.01f ? cam.aspect : 16f / 9f;
            float tanHalf = Mathf.Tan(fieldOfView * 0.5f * Mathf.Deg2Rad);
            Rect r = target;
            if (shot == MenuShot.Sky) r = titleRect;   // the title framing, then tilt up
            float height = Mathf.Max(0.1f, r.height);
            float kidHeight = KidHeight;
            float distance = kidHeight / (height * 2f * tanHalf);
            rot = Quaternion.Euler(-(shot == MenuShot.Locker ? lockerPitch : pitch), yaw, 0f);
            Vector3 mid = feet.position + Vector3.up * kidHeight * 0.5f;
            Vector3 local = new Vector3((r.center.x - 0.5f) * 2f * distance * tanHalf * aspect,
                (r.center.y - 0.5f) * 2f * distance * tanHalf, distance);
            pos = mid - rot * local;
            if (shot == MenuShot.Sky) rot = Quaternion.Euler(-pitch - skyTilt, yaw - 6f, 0f);
        }
    }
}
