using System.Collections.Generic;
using DribbleToSchool.Core;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace DribbleToSchool.InputHandling
{
    /// <summary>
    /// Turns raw touches, mouse and keyboard into game intents, once per frame.
    ///
    /// Touch layout (landscape, mirrored for left-handed play):
    ///  - Left / right arrow buttons (bottom-left): walk backward / forward. Let go to stop.
    ///  - Kick button (bottom-right, left of Slide): drag from it in the direction you
    ///    want the ball to go, then release. Longer drag = more power. A quick tap
    ///    is a short pass the way the kid is facing.
    ///  - Slide button (between Kick and Jump) or swipe down anywhere else: a feet-first
    ///    slide along the ground, low enough to pass under barriers.
    ///  - Jump button (bottom-right) or swipe up anywhere else: jump (hold for higher);
    ///    press again in the air for a double jump.
    ///  - Quick tap anywhere else: touch the ball (perfect touch / juggle).
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

        [Header("Layout (normalized screen coords: x, y, width, height; origin bottom-left)")]
        public Rect leftButtonRect = new Rect(0.025f, 0.04f, 0.115f, 0.24f);
        public Rect rightButtonRect = new Rect(0.155f, 0.04f, 0.115f, 0.24f);
        public Rect kickButtonRect = new Rect(0.55f, 0.04f, 0.14f, 0.26f);
        [Tooltip("A little smaller and lower than Jump, right next to it: slide, then jump, with one thumb.")]
        public Rect slideButtonRect = new Rect(0.705f, 0.04f, 0.11f, 0.2f);
        public Rect jumpButtonRect = new Rect(0.83f, 0.04f, 0.15f, 0.26f);
        [Tooltip("Extra touch area around each button, in inches, so near misses still count.")]
        public float buttonSlopInches = 0.12f;

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

        // Buttons in normalized screen coords. Left-handed play swaps the two clusters
        // but keeps "back" on the left of "forward" so the arrows still point the right way.
        public Rect JumpButtonNormalized { get { return Mirror(jumpButtonRect); } }
        public Rect KickButtonNormalized { get { return Mirror(kickButtonRect); } }
        public Rect SlideButtonNormalized { get { return Mirror(slideButtonRect); } }
        public Rect LeftButtonNormalized { get { return GameSettings.LeftHanded ? MirrorPair(rightButtonRect, leftButtonRect) : leftButtonRect; } }
        public Rect RightButtonNormalized { get { return GameSettings.LeftHanded ? MirrorPair(leftButtonRect, rightButtonRect) : rightButtonRect; } }

        /// <summary>True while the finger (or key) for that direction is down; used by the HUD.</summary>
        public bool LeftHeld { get; private set; }
        public bool RightHeld { get; private set; }

        static Rect Mirror(Rect r)
        {
            if (GameSettings.LeftHanded) r.x = 1f - r.x - r.width;
            return r;
        }

        /// <summary>Mirror the pair as a cluster: <paramref name="slot"/>'s mirrored spot, given to the other button.</summary>
        static Rect MirrorPair(Rect slot, Rect self)
        {
            Rect r = self;
            r.x = 1f - slot.x - slot.width;
            return r;
        }

        Rect ToScreen(Rect r, bool withSlop)
        {
            float slop = withSlop ? buttonSlopInches * Dpi : 0f;
            return new Rect(r.x * Screen.width - slop, r.y * Screen.height - slop,
                r.width * Screen.width + slop * 2f, r.height * Screen.height + slop * 2f);
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
                    p = new Pointer { id = s.id, start = s.position, current = s.position, startTime = Time.unscaledTime };
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
            MoveAxis = (RightHeld ? 1f : 0f) - (LeftHeld ? 1f : 0f);
        }

        bool IsDrag(Pointer p)
        {
            return (p.current - p.start).magnitude > tapMaxMoveInches * Dpi;
        }

        Role ClassifyDown(Vector2 pos)
        {
            // Exact hits first, then the slop area, so neighbouring buttons never steal a touch.
            for (int pass = 0; pass < 2; pass++)
            {
                bool slop = pass == 1;
                if (ToScreen(JumpButtonNormalized, slop).Contains(pos)) return Role.Jump;
                if (ToScreen(KickButtonNormalized, slop).Contains(pos) && !AnyPointerWithRole(Role.Kick)) return Role.Kick;
                if (ToScreen(SlideButtonNormalized, slop).Contains(pos)) return Role.Slide;
                if (ToScreen(LeftButtonNormalized, slop).Contains(pos)) return Role.MoveLeft;
                if (ToScreen(RightButtonNormalized, slop).Contains(pos)) return Role.MoveRight;
            }
            return Role.TapOrSwipe;
        }

        void OnPointerMove(Pointer p)
        {
            if (p.role == Role.MoveLeft || p.role == Role.MoveRight)
            {
                // Rocking the thumb across to the other arrow switches direction without lifting.
                if (p.role == Role.MoveLeft && ToScreen(RightButtonNormalized, false).Contains(p.current)) p.role = Role.MoveRight;
                else if (p.role == Role.MoveRight && ToScreen(LeftButtonNormalized, false).Contains(p.current)) p.role = Role.MoveLeft;
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
