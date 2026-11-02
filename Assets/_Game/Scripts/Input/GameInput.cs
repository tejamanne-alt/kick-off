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
    ///  - The LEFT thumb walks and slides. Left / right arrow buttons (bottom-left): walk backward /
    ///    forward; let go to stop, rock the thumb across to turn round. The slide button sits up and to
    ///    the left of the forward arrow, and a quick flick DOWN on either arrow slides without letting
    ///    go: the kid keeps walking into the slide. (Settings can move the slide button back beside
    ///    jump and kick; the flick works either way.)
    ///  - The RIGHT thumb jumps and kicks, two round buttons of one size on one baseline, JUMP at the
    ///    corner where the thumb rests and KICK a thumb's width to its left, so kicking is a flick
    ///    sideways and jumping a press, never a neighbour to mistake:
    ///    - Jump button: jump (hold for higher); press again in the air for a double jump. Swipe up
    ///      anywhere else does the same.
    ///    - Slide (button or flick): a feet-first slide along the ground, low enough to pass under
    ///      barriers. Swipe down anywhere else does the same.
    ///    - Kick button: drag from it in the direction you want the ball to go (the whole screen above
    ///      it is room to aim), then release. Longer drag = more power. A quick tap is a short pass the
    ///      way the kid is facing.
    ///  - Quick tap anywhere else: touch the ball (perfect touch / juggle).
    /// The kid is never under a thumb: the camera stands them clear of the buttons on the left of the
    /// screen (<see cref="KidSafeScreenX"/>, used by CameraFollow2D).
    /// A touch belongs to the button whose edge it is nearest (within a small slop), so there
    /// are no gaps between buttons and no overlaps to guess at.
    ///
    /// Keyboard + mouse (editor testing):
    ///  - A / Left: walk back. D / Right: walk forward. Space / W / Up: jump (again in the air: double jump).
    ///  - S / Down: slide. F / J: touch. K: quick kick. Mouse drag from the kick button: aimed kick.
    ///  - R: restart. Esc / P: pause. Tab: tuning panel.
    /// </summary>
    [DefaultExecutionOrder(-100)]
    public class GameInput : MonoBehaviour
    {
        enum Role { MoveLeft, MoveRight, Kick, Slide, Jump, TapOrSwipe }

        class Pointer
        {
            public int id;
            public Role role;
            public Vector2 start;
            public Vector2 current;
            public float startTime;
            // For the flick down on an arrow: the highest recent point and when it was.
            public float flickY;
            public float flickTime;
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
        public ControlSpec jumpButton = new ControlSpec(0.16f, 0.17f, 0.125f);
        [Tooltip("Beside Jump on its baseline, a thumb's width to its left, close enough to flick across to. The aim drag has the whole screen above it.")]
        public ControlSpec kickButton = new ControlSpec(0.45f, 0.17f, 0.125f);
        [Tooltip("The slide button when Settings keeps it beside jump and kick: straight above Jump, a thumb's width away. Tap only.")]
        public ControlSpec slideButton = new ControlSpec(0.16f, 0.46f, 0.125f);
        [Tooltip("The slide button when it sits with the walking thumb (the default): x is how far to the left of the forward arrow's centre, y up from the bottom. A flick down on an arrow slides too.")]
        public ControlSpec slideByArrows = new ControlSpec(0.15f, 0.46f, 0.125f);
        [Tooltip("The left thumb's two arrows: back, then (bigger, it is held all the time) forward. Tucked into the corner so the thumb stays clear of the kid.")]
        public ControlSpec walkBackButton = new ControlSpec(0.135f, 0.17f, 0.105f);
        public ControlSpec walkForwardButton = new ControlSpec(0.42f, 0.19f, 0.14f);
        [Tooltip("Extra touch area around each button, in inches, so near misses still count.")]
        public float buttonSlopInches = 0.12f;
        [Tooltip("Keep the two clusters at least this far apart (screen heights) on narrow screens, by shrinking the layout.")]
        public float clusterGap = 0.1f;
        [Tooltip("The kid stands at least this far (screen heights) to the right of the buttons on the left of the screen, so a thumb on them never covers the kid.")]
        public float kidClearance = 0.14f;

        /// <summary>The gap (screen heights) between the two walk arrows.</summary>
        const float ArrowGap = 0.04f;

        [Header("Gestures")]
        public float tapMaxDuration = 0.25f;
        public float tapMaxMoveInches = 0.15f;
        public float swipeUpMinInches = 0.35f;
        public float swipeDownMinInches = 0.35f;
        public float swipeMaxDuration = 0.35f;
        [Tooltip("A flick down on a walk arrow: this far (inches) within the window (seconds) slides, without letting go.")]
        public float flickDownInches = 0.3f;
        public float flickWindow = 0.3f;

        [Header("References")]
        public Camera worldCamera;

        /// <summary>-1 = walk back, +1 = walk forward, 0 = stand still.</summary>
        public float MoveAxis { get; private set; }
        public bool JumpPressed { get; private set; }
        public bool JumpHeld { get; private set; }
        /// <summary>Slide button tapped, swiped down or S / Down pressed this frame.</summary>
        public bool SlidePressed { get; private set; }
        /// <summary>True while the finger (or key) for the slide is down; used by the HUD.</summary>
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

        // The buttons as the HUD draws them: normalized screen rects (origin bottom-left), square on
        // screen. Left-handed play swaps the two clusters but keeps "back" on the left of "forward"
        // so the arrows still point the right way.
        public Rect JumpButtonNormalized { get { return Normalized(JumpDisc()); } }
        public Rect KickButtonNormalized { get { return Normalized(KickDisc()); } }
        public Rect SlideButtonNormalized { get { return Normalized(SlideDisc()); } }
        public Rect LeftButtonNormalized { get { return Normalized(WalkDisc(false)); } }
        public Rect RightButtonNormalized { get { return Normalized(WalkDisc(true)); } }

        /// <summary>
        /// A move held by a script instead of a finger (the store screenshot tour): -1..1, 0 = none.
        /// Applies only while gameplay input isn't blocked.
        /// </summary>
        public static float ScriptedMove;

        /// <summary>True while the finger (or key) for that direction is down; used by the HUD.</summary>
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

        /// <summary>Where every touch button sits on one screen (in pixels, origin bottom-left).</summary>
        public struct ControlLayout
        {
            public Round jump, kick, slide, walkBack, walkForward;
        }

        /// <summary>
        /// The whole layout for a screen of the given size, safe area and handedness. Pure (it reads no
        /// screen state), so it can be checked on any aspect ratio: see Tests/Editor/ControlLayoutTests.
        /// <paramref name="slideWithArrows"/> puts the slide button up and to the left of the forward arrow
        /// (the walking thumb's), else straight above jump.
        /// </summary>
        public ControlLayout LayoutOn(float width, float height, Rect safeArea, bool leftHanded, bool slideWithArrows = true)
        {
            float scale = LayoutScale(width / Mathf.Max(1f, height), slideWithArrows);
            var layout = new ControlLayout();
            layout.jump = Place(jumpButton, true, leftHanded, width, height, safeArea, scale);
            layout.kick = Place(kickButton, true, leftHanded, width, height, safeArea, scale);
            // Left-handed, the arrows move to the right-hand side and swap places, so "back" is still the one on the left:
            // the big forward arrow takes the corner (its rim just inside the edge), back sits inside it, a gap apart.
            ControlSpec back = walkBackButton, forward = walkForwardButton;
            if (leftHanded)
            {
                forward.x = forward.radius + 0.02f;
                back.x = forward.x + forward.radius + ArrowGap + back.radius;
            }
            layout.walkBack = Place(back, false, leftHanded, width, height, safeArea, scale);
            layout.walkForward = Place(forward, false, leftHanded, width, height, safeArea, scale);
            if (slideWithArrows)
            {
                // Above the gap, on the screen's left of the forward arrow (x counts from the cluster's own edge).
                ControlSpec slide = slideByArrows;
                slide.x = forward.x + (leftHanded ? slideByArrows.x : -slideByArrows.x);
                layout.slide = Place(slide, false, leftHanded, width, height, safeArea, scale);
            }
            else
            {
                layout.slide = Place(slideButton, true, leftHanded, width, height, safeArea, scale);
            }
            return layout;
        }

        /// <summary>
        /// How far across the screen (0..1) the kid must stand to be clear of every button on the left half
        /// of it: the right edge of the farthest one, plus <paramref name="clearance"/> screen heights.
        /// </summary>
        public static float KidSafeScreenXOn(ControlLayout layout, float width, float height, float clearance)
        {
            float edge = 0f, half = width * 0.5f;
            if (layout.jump.center.x < half) edge = Mathf.Max(edge, layout.jump.center.x + layout.jump.radius);
            if (layout.kick.center.x < half) edge = Mathf.Max(edge, layout.kick.center.x + layout.kick.radius);
            if (layout.slide.center.x < half) edge = Mathf.Max(edge, layout.slide.center.x + layout.slide.radius);
            if (layout.walkBack.center.x < half) edge = Mathf.Max(edge, layout.walkBack.center.x + layout.walkBack.radius);
            if (layout.walkForward.center.x < half) edge = Mathf.Max(edge, layout.walkForward.center.x + layout.walkForward.radius);
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

        ControlLayout Current { get { return LayoutOn(Screen.width, Screen.height, Screen.safeArea, GameSettings.LeftHanded, GameSettings.SlideWithWalkThumb); } }

        /// <summary>
        /// How much the layout shrinks so both clusters fit side by side: 1 on phones and tablets (4:3 and
        /// wider), less on anything narrower.
        /// </summary>
        float LayoutScale(float aspect, bool slideWithArrows)
        {
            float left = Mathf.Max(walkBackButton.x + walkBackButton.radius, walkForwardButton.x + walkForwardButton.radius);
            float right = Mathf.Max(jumpButton.x + jumpButton.radius, kickButton.x + kickButton.radius);
            if (!slideWithArrows) right = Mathf.Max(right, slideButton.x + slideButton.radius);
            return Mathf.Clamp((aspect - clusterGap) / (left + right), 0.6f, 1f);
        }

        Round JumpDisc() { return Current.jump; }
        Round KickDisc() { return Current.kick; }
        Round SlideDisc() { return Current.slide; }
        Round WalkDisc(bool forward) { return forward ? Current.walkForward : Current.walkBack; }

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

            samples.Clear();
            GatherPointers(samples);
            ReadMenuKeys();

            if (Blocked)
            {
                pointers.Clear();
                foreach (var s in samples) ignored.Add(s.id);
                return;
            }

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
                    OnPointerMove(p);
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
                    p = new Pointer { id = s.id, start = s.position, current = s.position, startTime = Time.unscaledTime, flickY = s.position.y, flickTime = Time.unscaledTime };
                    p.role = ClassifyDown(s.position);
                    pointers[s.id] = p;
                    if (p.role == Role.Jump) JumpPressed = true;
                    if (p.role == Role.Slide) SlidePressed = true;
                }
            }

            foreach (var p in pointers.Values)
            {
                switch (p.role)
                {
                    case Role.MoveLeft: LeftHeld = true; break;
                    case Role.MoveRight: RightHeld = true; break;
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

            ReadGameplayKeys();
            if (ScriptedMove != 0f)
            {
                RightHeld = ScriptedMove > 0f;
                LeftHeld = ScriptedMove < 0f;
            }
            MoveAxis = (RightHeld ? 1f : 0f) - (LeftHeld ? 1f : 0f);
        }

        bool IsDrag(Pointer p)
        {
            return (p.current - p.start).magnitude > tapMaxMoveInches * Dpi;
        }

        /// <summary>
        /// The button a new touch belongs to: the one whose edge it is nearest, counting a touch
        /// inside a button as nearer than one in another button's slop. Anywhere else is a tap or swipe.
        /// </summary>
        Role ClassifyDown(Vector2 pos)
        {
            float slop = buttonSlopInches * Dpi;
            Role best = Role.TapOrSwipe;
            float bestEdge = slop;
            Consider(Role.Jump, JumpDisc(), pos, ref best, ref bestEdge);
            if (!AnyPointerWithRole(Role.Kick)) Consider(Role.Kick, KickDisc(), pos, ref best, ref bestEdge);
            Consider(Role.Slide, SlideDisc(), pos, ref best, ref bestEdge);
            Consider(Role.MoveLeft, WalkDisc(false), pos, ref best, ref bestEdge);
            Consider(Role.MoveRight, WalkDisc(true), pos, ref best, ref bestEdge);
            return best;
        }

        static void Consider(Role role, Round button, Vector2 pos, ref Role best, ref float bestEdge)
        {
            float edge = button.EdgeDistance(pos);
            if (edge >= bestEdge) return;
            best = role;
            bestEdge = edge;
        }

        void OnPointerMove(Pointer p)
        {
            if (p.role == Role.MoveLeft || p.role == Role.MoveRight)
            {
                // Rocking the thumb across to the other arrow switches direction without lifting.
                if (p.role == Role.MoveLeft && WalkDisc(true).EdgeDistance(p.current) <= 0f) p.role = Role.MoveRight;
                else if (p.role == Role.MoveRight && WalkDisc(false).EdgeDistance(p.current) <= 0f) p.role = Role.MoveLeft;
                // A flick down on an arrow slides without letting go of it: the kid keeps walking into the slide.
                if (FlickedDown(p)) SlidePressed = true;
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

        /// <summary>
        /// Did the finger just flick down? It must drop <see cref="flickDownInches"/> within <see cref="flickWindow"/>
        /// seconds of its highest recent point (a thumb resting on an arrow, or drifting slowly, never counts), and
        /// it needs to come up again before it can flick again.
        /// </summary>
        bool FlickedDown(Pointer p)
        {
            return FlickDown(ref p.flickY, ref p.flickTime, p.current.y, Time.unscaledTime, flickDownInches * Dpi, flickWindow);
        }

        /// <summary>
        /// The flick test itself, on its own so it can be checked: <paramref name="refY"/> and <paramref name="refTime"/>
        /// are the finger's highest recent height and when it was there (the caller keeps them between calls), the
        /// finger is now at <paramref name="y"/> at time <paramref name="now"/>. True when it has dropped at least
        /// <paramref name="minDrop"/> within <paramref name="window"/> seconds of that point.
        /// </summary>
        public static bool FlickDown(ref float refY, ref float refTime, float y, float now, float minDrop, float window)
        {
            if (y >= refY || now - refTime > window)
            {
                refY = y;
                refTime = now;
                return false;
            }
            if (refY - y < minDrop) return false;
            refY = y;
            refTime = now;
            return true;
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
