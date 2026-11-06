using System.Collections.Generic;
using DribbleToSchool.Core;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace DribbleToSchool.InputHandling
{
    /// <summary>Where a round touch button sits, in screen heights (so it is the same physical size on any phone).</summary>
    [System.Serializable]
    public struct ControlSpec
    {
        [Tooltip("Centre: distance in from the screen edge on the button's side.")]
        public float x;
        [Tooltip("Centre: distance up from the bottom edge.")]
        public float y;
        public float radius;

        public ControlSpec(float x, float y, float radius)
        {
            this.x = x;
            this.y = y;
            this.radius = radius;
        }
    }

    /// <summary>
    /// Turns raw touches, mouse and keyboard into game intents, once per frame.
    ///
    /// Touch layout (landscape, mirrored for left-handed play). Each thumb has a job:
    ///  - The LEFT thumb has one control, the walk stick: a ring with a knob. Touch anywhere in the
    ///    bottom-left area and the stick comes to the thumb. Push the knob right to dribble forward,
    ///    left to walk back, let go to stop. Pull it DOWN to slide: down and right slides forward,
    ///    down and left slides back, straight down slides the way the kid is going.
    ///  - The RIGHT thumb jumps and kicks, two round buttons of one size on one baseline, JUMP at the
    ///    corner where the thumb rests and KICK a thumb's width to its left, so kicking is a flick
    ///    sideways and jumping a press, never a neighbour to mistake:
    ///    - Jump button: jump (hold for higher); press again in the air for a double jump. Swipe up
    ///      anywhere else does the same.
    ///    - Kick button: drag from it in the direction you want the ball to go (the whole screen above
    ///      it is room to aim), then release. Longer drag = more power. A quick tap is a short pass the
    ///      way the kid is facing.
    ///  - Quick tap anywhere else: touch the ball (perfect touch / juggle). A swipe down there slides.
    /// The kid is never under a thumb: the camera stands them clear of the stick's area
    /// (<see cref="KidSafeScreenX"/>, used by CameraFollow2D).
    /// A touch on the right belongs to the button whose edge it is nearest (within a small slop),
    /// so there are no gaps between buttons and no overlaps to guess at.
    ///
    /// Keyboard + mouse (editor testing):
    ///  - A / Left: walk back. D / Right: walk forward. Space / W / Up: jump (again in the air: double jump).
    ///  - S / Down: slide. F / J: touch. K: quick kick. Mouse drag from the kick button: aimed kick.
    ///  - R: restart. Esc / P: pause. Tab: tuning panel.
    /// </summary>
    [DefaultExecutionOrder(-100)]
    public class GameInput : MonoBehaviour
    {
        enum Role { Stick, Kick, Slide, Jump, TapOrSwipe }

        class Pointer
        {
            public int id;
            public Role role;
            public Vector2 start;
            public Vector2 current;
            public float startTime;
            // The walk stick: where its ring sits now and the point the knob is measured from (both move when the thumb runs off the ring).
            public Vector2 stickCenter;
            public Vector2 stickOrigin;
        }

        struct Sample
        {
            public int id;
            public Vector2 position;
            public Sample(int id, Vector2 position) { this.id = id; this.position = position; }
        }

        const int MousePointerId = -1;

        public static GameInput Instance { get; private set; }

        /// <summary>Screen-space rects (origin bottom-left) owned by on-screen UI; touches starting there are ignored.</summary>
        public static readonly List<Rect> UIBlockers = new List<Rect>();

        [Header("Layout (in screen heights, so the buttons are the same physical size on any phone)")]
        [Tooltip("Where the right thumb rests, in the corner: the button pressed most.")]
        public ControlSpec jumpButton = new ControlSpec(0.18f, 0.185f, 0.145f);
        [Tooltip("Beside Jump on its baseline, a thumb's width to its left, close enough to flick across to. The aim drag has the whole screen above it.")]
        public ControlSpec kickButton = new ControlSpec(0.515f, 0.185f, 0.145f);
        [Tooltip("The walk stick's ring where it rests: centre in from the screen edge on its side and up from the bottom, and its radius. The knob travels to the ring.")]
        public ControlSpec walkStick = new ControlSpec(0.28f, 0.3f, 0.17f);
        [Tooltip("How far (screen heights) the stick may follow the thumb in from its resting place toward the middle of the screen, and up.")]
        public float stickRoamIn = 0.12f;
        public float stickRoamUp = 0.24f;
        [Tooltip("The knob's size as a part of the ring's.")]
        public float stickKnob = 0.44f;
        [Tooltip("Push the knob sideways past this part of the ring to walk.")]
        public float stickDeadZone = 0.22f;
        [Tooltip("Pull the knob down past this part of the ring (more down than sideways) to slide; it slides again once it has come back above the release.")]
        public float stickSlideDown = 0.5f;
        public float stickSlideRelease = 0.3f;
        [Tooltip("Extra touch area around each button, in inches, so near misses still count.")]
        public float buttonSlopInches = 0.12f;
        [Tooltip("Keep the two clusters at least this far apart (screen heights) on narrow screens, by shrinking the layout.")]
        public float clusterGap = 0.1f;
        [Tooltip("The kid stands at least this far (screen heights) to the right of the controls on the left of the screen, so a thumb on them never covers the kid.")]
        public float kidClearance = 0.14f;

        [Header("Gestures")]
        public float tapMaxDuration = 0.25f;
        public float tapMaxMoveInches = 0.15f;
        public float swipeUpMinInches = 0.35f;
        public float swipeDownMinInches = 0.35f;
        public float swipeMaxDuration = 0.35f;

        [Header("References")]
        public Camera worldCamera;

        /// <summary>-1 = walk back, +1 = walk forward, 0 = stand still.</summary>
        public float MoveAxis { get; private set; }
        public bool JumpPressed { get; private set; }
        public bool JumpHeld { get; private set; }
        /// <summary>The stick was pulled down, a swipe down or S / Down this frame: slide.</summary>
        public bool SlidePressed { get; private set; }
        /// <summary>True while the stick is held down (or the key): used by the HUD.</summary>
        public bool SlideHeld { get; private set; }
        public bool TouchPressed { get; private set; }
        /// <summary>True while a finger drags from the kick button.</summary>
        public bool KickAiming { get; private set; }
        /// <summary>True while a finger is down on the kick button (tap or drag).</summary>
        public bool KickHeld { get; private set; }
        /// <summary>The aimed kick was let go this frame (see KickDrag).</summary>
        public bool KickReleased { get; private set; }
        /// <summary>The kick button was tapped without dragging: a quick pass.</summary>
        public bool KickTapped { get; private set; }
        /// <summary>Drag from the kick button, in screen pixels (the direction the ball should go).</summary>
        public Vector2 KickDrag { get; private set; }
        public bool ResetPressed { get; private set; }
        public bool PausePressed { get; private set; }
        public bool DebugTogglePressed { get; private set; }

        /// <summary>
        /// When true, gameplay intents are suppressed (pause, countdown, respawn, results).
        /// Fingers already down stay ignored until lifted. Menu keys still work.
        /// </summary>
        public bool Blocked { get; set; }

        // The controls as the HUD draws them: normalized screen rects (origin bottom-left), square on
        // screen. Left-handed play swaps the stick and the two buttons.
        public Rect JumpButtonNormalized { get { return Normalized(Current.jump); } }
        public Rect KickButtonNormalized { get { return Normalized(Current.kick); } }
        /// <summary>The walk stick's ring: where the thumb has brought it, or where it rests.</summary>
        public Rect StickRingNormalized { get { return Normalized(StickActive ? new Round { center = StickCenter, radius = StickRadius } : Current.stick); } }
        /// <summary>The stick's ring where it rests (the tour points at it).</summary>
        public Rect StickHomeNormalized { get { return Normalized(Current.stick); } }
        /// <summary>True while a thumb holds the stick.</summary>
        public bool StickActive { get; private set; }
        /// <summary>Where the knob is, as a part of the ring's radius (each axis -1..1, up and right positive).</summary>
        public Vector2 StickKnob { get; private set; }
        /// <summary>The knob's size as a part of the ring's.</summary>
        public float StickKnobScale { get { return stickKnob; } }
        Vector2 StickCenter;
        float StickRadius;

        /// <summary>
        /// A move held by a script instead of a finger (the store screenshot tour): -1..1, 0 = none.
        /// Applies only while gameplay input isn't blocked.
        /// </summary>
        public static float ScriptedMove;

        /// <summary>True while the stick (or key) points that way.</summary>
        public bool LeftHeld { get; private set; }
        public bool RightHeld { get; private set; }

        /// <summary>A round button on screen, in pixels.</summary>
        public struct Round
        {
            public Vector2 center;
            public float radius;

            /// <summary>Distance from the button's edge: negative inside it.</summary>
            public float EdgeDistance(Vector2 p) { return (p - center).magnitude - radius; }
        }

        /// <summary>Where every touch control sits on one screen (in pixels, origin bottom-left).</summary>
        public struct ControlLayout
        {
            public Round jump, kick;
            /// <summary>The walk stick's ring where it rests.</summary>
            public Round stick;
            /// <summary>The area a touch takes the stick in, and that its ring stays inside.</summary>
            public Rect stickArea;
        }

        /// <summary>
        /// The whole layout for a screen of the given size, safe area and handedness. Pure (it reads no
        /// screen state), so it can be checked on any aspect ratio: see Tests/Editor/ControlLayoutTests.
        /// </summary>
        public ControlLayout LayoutOn(float width, float height, Rect safeArea, bool leftHanded)
        {
            float scale = LayoutScale(width / Mathf.Max(1f, height));
            var layout = new ControlLayout();
            layout.jump = Place(jumpButton, true, leftHanded, width, height, safeArea, scale);
            layout.kick = Place(kickButton, true, leftHanded, width, height, safeArea, scale);
            layout.stick = Place(walkStick, false, leftHanded, width, height, safeArea, scale);
            // The stick's area: from the screen's edge on its side in to its resting ring plus the roam, from the bottom up to
            // the ring's top plus the roam.
            float reach = Mathf.Abs(layout.stick.center.x - (leftHanded ? width : 0f)) + layout.stick.radius + stickRoamIn * scale * height;
            float top = layout.stick.center.y + layout.stick.radius + stickRoamUp * scale * height;
            layout.stickArea = leftHanded ? Rect.MinMaxRect(width - reach, 0f, width, top) : Rect.MinMaxRect(0f, 0f, reach, top);
            return layout;
        }

        /// <summary>
        /// How far across the screen (0..1) the kid must stand to be clear of every control on the left half of it: the
        /// inner edge of the stick's area (where the ring can go) or of the farthest button there, plus
        /// <paramref name="clearance"/> screen heights.
        /// </summary>
        public static float KidSafeScreenXOn(ControlLayout layout, float width, float height, float clearance)
        {
            float edge = 0f, half = width * 0.5f;
            if (layout.jump.center.x < half) edge = Mathf.Max(edge, layout.jump.center.x + layout.jump.radius);
            if (layout.kick.center.x < half) edge = Mathf.Max(edge, layout.kick.center.x + layout.kick.radius);
            if (layout.stick.center.x < half) edge = Mathf.Max(edge, layout.stickArea.xMax);
            return Mathf.Clamp01((edge + clearance * height) / Mathf.Max(1f, width));
        }

        /// <summary>Where the kid has to stand across the screen so no thumb on the left covers them (see <see cref="KidSafeScreenXOn"/>).</summary>
        public float KidSafeScreenX
        {
            get
            {
                float w = Mathf.Max(1f, Screen.width), h = Mathf.Max(1f, Screen.height);
                return KidSafeScreenXOn(Current, w, h, kidClearance);
            }
        }

        static Round Place(ControlSpec spec, bool rightCluster, bool leftHanded, float w, float h, Rect safe, float scale)
        {
            bool onRight = rightCluster != leftHanded;
            // Keep clear of a notch or rounded corner: part of the unsafe margin, since the thumb sits further in anyway.
            float inset = onRight ? Mathf.Max(0f, w - safe.xMax) : Mathf.Max(0f, safe.xMin);
            float x = spec.x * scale * h + inset * 0.5f;
            return new Round
            {
                center = new Vector2(onRight ? w - x : x, spec.y * scale * h + Mathf.Max(0f, safe.yMin) * 0.5f),
                radius = spec.radius * scale * h,
            };
        }

        ControlLayout Current { get { return LayoutOn(Screen.width, Screen.height, Screen.safeArea, GameSettings.LeftHanded); } }

        /// <summary>
        /// How much the layout shrinks so the stick's area and the buttons fit side by side: 1 on phones and tablets
        /// (4:3 and wider), less on anything narrower.
        /// </summary>
        float LayoutScale(float aspect)
        {
            float left = walkStick.x + walkStick.radius + stickRoamIn;
            float right = Mathf.Max(jumpButton.x + jumpButton.radius, kickButton.x + kickButton.radius);
            return Mathf.Clamp((aspect - clusterGap) / (left + right), 0.6f, 1f);
        }

        /// <summary>
        /// Where the stick's ring goes when a thumb lands at <paramref name="touch"/>: under the thumb, kept whole inside the
        /// stick's area (and off the very bottom edge).
        /// </summary>
        public static Vector2 StickCenterFor(Vector2 touch, Round home, Rect area)
        {
            float r = home.radius;
            float minY = Mathf.Min(home.center.y, r * 1.15f);
            return new Vector2(Mathf.Clamp(touch.x, area.xMin + r, area.xMax - r), Mathf.Clamp(touch.y, minY, Mathf.Max(minY, area.yMax - r)));
        }

        /// <summary>
        /// What the stick says, from where the knob is (<paramref name="offset"/>, from the point the thumb went down, in
        /// pixels) on a ring of <paramref name="radius"/>: <paramref name="move"/> -1, 0 or 1, and whether it is pulled down
        /// to slide. <paramref name="down"/> carries between frames: <paramref name="slideNow"/> is true on the frame it goes
        /// down, and it must come back above the release line before it slides again. Pulled down, a smaller push sideways
        /// still says which way, so down-left slides back and down-right forward. Pure, for the tests.
        /// </summary>
        public static void ReadStick(Vector2 offset, float radius, float deadZone, float slideDown, float slideRelease, ref bool down, out float move, out bool slideNow)
        {
            float r = Mathf.Max(1f, radius);
            float x = offset.x / r, y = offset.y / r;
            bool was = down;
            down = was ? y < -slideRelease : y < -slideDown && -y > Mathf.Abs(x) * 0.7f;
            slideNow = down && !was;
            float dead = down ? deadZone * 0.6f : deadZone;
            move = Mathf.Abs(x) > dead ? Mathf.Sign(x) : 0f;
        }

        static Rect Normalized(Round r)
        {
            float w = Screen.width, h = Screen.height;
            return new Rect((r.center.x - r.radius) / w, (r.center.y - r.radius) / h, 2f * r.radius / w, 2f * r.radius / h);
        }

        readonly Dictionary<int, Pointer> pointers = new Dictionary<int, Pointer>();
        readonly List<Sample> samples = new List<Sample>();
        readonly List<int> ended = new List<int>();
        readonly HashSet<int> ignored = new HashSet<int>();

        float Dpi { get { return Screen.dpi > 0f ? Screen.dpi : 160f; } }

        void Awake()
        {
            // One per scene; during a scene load the newest instance takes over.
            Instance = this;
            if (worldCamera == null) worldCamera = Camera.main;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Update()
        {
            MoveAxis = 0f;
            LeftHeld = RightHeld = JumpPressed = JumpHeld = SlidePressed = SlideHeld = KickHeld = TouchPressed = false;
            KickAiming = KickReleased = KickTapped = ResetPressed = PausePressed = DebugTogglePressed = false;
            StickActive = false;
            StickKnob = Vector2.zero;

            samples.Clear();
            GatherPointers(samples);
            ReadMenuKeys();

            if (Blocked)
            {
                pointers.Clear();
                stickDown = false;
                foreach (var s in samples) ignored.Add(s.id);
                return;
            }

            var layout = Current;
            ended.Clear();
            foreach (var kv in pointers)
            {
                if (!ContainsSample(kv.Key)) ended.Add(kv.Key);
            }
            foreach (int id in ended)
            {
                OnPointerUp(pointers[id]);
                pointers.Remove(id);
            }
            ignored.RemoveWhere(id => !ContainsSample(id));

            foreach (var s in samples)
            {
                Pointer p;
                if (pointers.TryGetValue(s.id, out p))
                {
                    p.current = s.position;
                    OnPointerMove(p, layout);
                }
                else if (ignored.Contains(s.id))
                {
                    continue;
                }
                else if (IsOverUI(s.position))
                {
                    // Finger started on a UI button: ignore it until it lifts.
                    ignored.Add(s.id);
                }
                else
                {
                    p = new Pointer { id = s.id, start = s.position, current = s.position, startTime = Time.unscaledTime };
                    p.role = ClassifyDown(s.position, layout);
                    if (p.role == Role.Stick)
                    {
                        // The stick comes to the thumb; the knob is measured from where the thumb went down.
                        p.stickCenter = StickCenterFor(s.position, layout.stick, layout.stickArea);
                        p.stickOrigin = s.position;
                        stickDown = false;
                    }
                    pointers[s.id] = p;
                    if (p.role == Role.Jump) JumpPressed = true;
                    if (p.role == Role.Slide) SlidePressed = true;
                }
            }

            float stickMove = 0f;
            foreach (var p in pointers.Values)
            {
                switch (p.role)
                {
                    case Role.Stick:
                    {
                        StickActive = true;
                        StickCenter = p.stickCenter;
                        StickRadius = layout.stick.radius;
                        Vector2 offset = p.current - p.stickOrigin;
                        bool slideNow;
                        ReadStick(offset, StickRadius, stickDeadZone, stickSlideDown, stickSlideRelease, ref stickDown, out stickMove, out slideNow);
                        if (slideNow) SlidePressed = true;
                        if (stickDown) SlideHeld = true;
                        StickKnob = Vector2.ClampMagnitude(offset / Mathf.Max(1f, StickRadius), 1f);
                        break;
                    }
                    case Role.Jump: JumpHeld = true; break;
                    case Role.Slide: SlideHeld = true; break;
                    case Role.Kick:
                        KickHeld = true;
                        // Only a real drag aims (and slows time); a tap is a quick pass on release.
                        if (IsDrag(p))
                        {
                            KickAiming = true;
                            KickDrag = p.current - p.start;
                        }
                        break;
                }
            }
            if (!StickActive) stickDown = false;
            if (stickMove > 0f) RightHeld = true;
            else if (stickMove < 0f) LeftHeld = true;

            ReadGameplayKeys();
            if (ScriptedMove != 0f)
            {
                RightHeld = ScriptedMove > 0f;
                LeftHeld = ScriptedMove < 0f;
            }
            MoveAxis = (RightHeld ? 1f : 0f) - (LeftHeld ? 1f : 0f);
        }

        bool stickDown;

        bool IsDrag(Pointer p)
        {
            return (p.current - p.start).magnitude > tapMaxMoveInches * Dpi;
        }

        /// <summary>
        /// What a new touch is for: the jump or kick button whose edge it is nearest (counting a touch inside a button
        /// as nearer than one in another button's slop), else the walk stick if it lands in the stick's area and no other
        /// thumb holds it, else a tap or swipe.
        /// </summary>
        Role ClassifyDown(Vector2 pos, ControlLayout layout)
        {
            float slop = buttonSlopInches * Dpi;
            Role best = Role.TapOrSwipe;
            float bestEdge = slop;
            Consider(Role.Jump, layout.jump, pos, ref best, ref bestEdge);
            if (!AnyPointerWithRole(Role.Kick)) Consider(Role.Kick, layout.kick, pos, ref best, ref bestEdge);
            if (best != Role.TapOrSwipe) return best;
            if (layout.stickArea.Contains(pos) && !AnyPointerWithRole(Role.Stick)) return Role.Stick;
            return best;
        }

        static void Consider(Role role, Round button, Vector2 pos, ref Role best, ref float bestEdge)
        {
            float edge = button.EdgeDistance(pos);
            if (edge >= bestEdge) return;
            best = role;
            bestEdge = edge;
        }

        void OnPointerMove(Pointer p, ControlLayout layout)
        {
            if (p.role == Role.Stick)
            {
                // A thumb that runs off the ring drags the stick after it (inside its area), so the push keeps reading
                // the way the thumb is going.
                Vector2 offset = p.current - p.stickOrigin;
                float reach = layout.stick.radius * 1.15f;
                if (offset.magnitude > reach)
                {
                    Vector2 shift = offset - offset.normalized * reach;
                    Vector2 moved = StickCenterFor(p.stickCenter + shift, layout.stick, layout.stickArea);
                    p.stickOrigin += moved - p.stickCenter;
                    p.stickCenter = moved;
                }
                return;
            }
            if (p.role != Role.TapOrSwipe) return;
            bool quick = Time.unscaledTime - p.startTime <= swipeMaxDuration;
            if (quick && p.current.y - p.start.y >= swipeUpMinInches * Dpi)
            {
                // Swipe up turns into a held jump so the kid jumps higher while the finger stays down.
                p.role = Role.Jump;
                JumpPressed = true;
            }
            else if (quick && p.start.y - p.current.y >= swipeDownMinInches * Dpi)
            {
                // Swipe down: drop into a slide.
                p.role = Role.Slide;
                SlidePressed = true;
            }
        }

        void OnPointerUp(Pointer p)
        {
            if (p.role == Role.Kick)
            {
                if (IsDrag(p))
                {
                    KickReleased = true;
                    KickDrag = p.current - p.start;
                }
                else
                {
                    KickTapped = true;
                }
            }
            else if (p.role == Role.TapOrSwipe)
            {
                bool shortTap = Time.unscaledTime - p.startTime <= tapMaxDuration;
                bool still = (p.current - p.start).magnitude <= tapMaxMoveInches * Dpi;
                if (shortTap && still) TouchPressed = true;
            }
        }

        bool AnyPointerWithRole(Role role)
        {
            foreach (var p in pointers.Values)
            {
                if (p.role == role) return true;
            }
            return false;
        }

        bool ContainsSample(int id)
        {
            for (int i = 0; i < samples.Count; i++)
            {
                if (samples[i].id == id) return true;
            }
            return false;
        }

        static bool IsOverUI(Vector2 screenPos)
        {
            for (int i = 0; i < UIBlockers.Count; i++)
            {
                if (UIBlockers[i].Contains(screenPos)) return true;
            }
            return false;
        }

#if ENABLE_INPUT_SYSTEM
        static void GatherPointers(List<Sample> into)
        {
            var screen = Touchscreen.current;
            if (screen != null)
            {
                foreach (var touch in screen.touches)
                {
                    if (touch.press.isPressed)
                        into.Add(new Sample(touch.touchId.ReadValue(), touch.position.ReadValue()));
                }
            }
            var mouse = Mouse.current;
            if (into.Count == 0 && mouse != null && mouse.leftButton.isPressed)
                into.Add(new Sample(MousePointerId, mouse.position.ReadValue()));
        }

        void ReadGameplayKeys()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed) LeftHeld = true;
            if (kb.dKey.isPressed || kb.rightArrowKey.isPressed) RightHeld = true;
            if (kb.kKey.wasPressedThisFrame) KickTapped = true;
            if (kb.spaceKey.wasPressedThisFrame || kb.wKey.wasPressedThisFrame || kb.upArrowKey.wasPressedThisFrame) JumpPressed = true;
            if (kb.spaceKey.isPressed || kb.wKey.isPressed || kb.upArrowKey.isPressed) JumpHeld = true;
            if (kb.sKey.wasPressedThisFrame || kb.downArrowKey.wasPressedThisFrame) SlidePressed = true;
            if (kb.sKey.isPressed || kb.downArrowKey.isPressed) SlideHeld = true;
            if (kb.fKey.wasPressedThisFrame || kb.jKey.wasPressedThisFrame) TouchPressed = true;
        }

        void ReadMenuKeys()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.rKey.wasPressedThisFrame) ResetPressed = true;
            if (kb.escapeKey.wasPressedThisFrame || kb.pKey.wasPressedThisFrame) PausePressed = true;
            if (kb.tabKey.wasPressedThisFrame) DebugTogglePressed = true;
        }
#elif ENABLE_LEGACY_INPUT_MANAGER
        static void GatherPointers(List<Sample> into)
        {
            for (int i = 0; i < Input.touchCount; i++)
            {
                Touch t = Input.GetTouch(i);
                if (t.phase != TouchPhase.Ended && t.phase != TouchPhase.Canceled)
                    into.Add(new Sample(t.fingerId, t.position));
            }
            if (into.Count == 0 && Input.touchCount == 0 && Input.GetMouseButton(0))
                into.Add(new Sample(MousePointerId, Input.mousePosition));
        }

        void ReadGameplayKeys()
        {
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) LeftHeld = true;
            if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) RightHeld = true;
            if (Input.GetKeyDown(KeyCode.K)) KickTapped = true;
            if (Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow)) JumpPressed = true;
            if (Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) JumpHeld = true;
            if (Input.GetKeyDown(KeyCode.S) || Input.GetKeyDown(KeyCode.DownArrow)) SlidePressed = true;
            if (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow)) SlideHeld = true;
            if (Input.GetKeyDown(KeyCode.F) || Input.GetKeyDown(KeyCode.J)) TouchPressed = true;
        }

        void ReadMenuKeys()
        {
            if (Input.GetKeyDown(KeyCode.R)) ResetPressed = true;
            if (Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P)) PausePressed = true;
            if (Input.GetKeyDown(KeyCode.Tab)) DebugTogglePressed = true;
        }
#else
        static void GatherPointers(List<Sample> into) { }
        void ReadGameplayKeys() { }
        void ReadMenuKeys() { }
#endif
    }
}
