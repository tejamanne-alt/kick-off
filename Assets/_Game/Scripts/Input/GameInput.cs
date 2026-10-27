using System.Collections.Generic;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace DribbleToSchool.InputHandling
{
    /// <summary>
    /// Turns raw touches, mouse and keyboard into game intents, once per frame.
    ///
    /// Touch layout (landscape):
    ///  - Touch on/near the ball and drag back, then release: kick (slingshot).
    ///  - Jump button (bottom-right) or swipe up on the right side: jump (hold for higher).
    ///  - Hold the left part of the screen: brake.
    ///  - Quick tap on the right side: touch the ball (perfect touch / juggle).
    ///
    /// Keyboard + mouse (editor testing):
    ///  - A / Left / Shift: brake. Space / W / Up: jump. F / J: touch. Mouse drag from ball: kick.
    ///  - R: reset. Tab: tuning panel.
    /// </summary>
    [DefaultExecutionOrder(-100)]
    public class GameInput : MonoBehaviour
    {
        enum Role { Brake, Kick, Jump, TapOrSwipe }

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

        [Header("Layout")]
        [Tooltip("Fraction of screen width, from the left, that acts as the brake zone.")]
        [Range(0.1f, 0.6f)] public float brakeZoneWidth = 0.4f;
        [Tooltip("Jump button in normalized screen coords (x, y, width, height), origin bottom-left.")]
        public Rect jumpButtonRect = new Rect(0.83f, 0.04f, 0.15f, 0.26f);

        [Header("Gestures")]
        [Tooltip("Radius around the ball, in inches, where a touch starts a kick.")]
        public float ballGrabRadiusInches = 0.45f;
        public float tapMaxDuration = 0.25f;
        public float tapMaxMoveInches = 0.15f;
        public float swipeUpMinInches = 0.35f;
        public float swipeMaxDuration = 0.35f;

        [Header("References")]
        public Camera worldCamera;
        [Tooltip("Used to start kick drags when a touch begins near the ball.")]
        public Transform ball;
        public float ballWorldRadius = 0.2f;

        public bool BrakeHeld { get; private set; }
        public bool JumpPressed { get; private set; }
        public bool JumpHeld { get; private set; }
        public bool TouchPressed { get; private set; }
        public bool KickAiming { get; private set; }
        public bool KickReleased { get; private set; }
        public Vector2 KickStartScreen { get; private set; }
        public Vector2 KickCurrentScreen { get; private set; }
        public bool ResetPressed { get; private set; }
        public bool DebugTogglePressed { get; private set; }

        public Rect JumpButtonScreenRect
        {
            get
            {
                return new Rect(jumpButtonRect.x * Screen.width, jumpButtonRect.y * Screen.height,
                    jumpButtonRect.width * Screen.width, jumpButtonRect.height * Screen.height);
            }
        }

        readonly Dictionary<int, Pointer> pointers = new Dictionary<int, Pointer>();
        readonly List<Sample> samples = new List<Sample>();
        readonly List<int> ended = new List<int>();
        readonly HashSet<int> ignored = new HashSet<int>();

        float Dpi { get { return Screen.dpi > 0f ? Screen.dpi : 160f; } }

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            if (worldCamera == null) worldCamera = Camera.main;
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        void Update()
        {
            BrakeHeld = JumpPressed = JumpHeld = TouchPressed = false;
            KickAiming = KickReleased = ResetPressed = DebugTogglePressed = false;

            samples.Clear();
            GatherPointers(samples);

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
                }
            }

            foreach (var p in pointers.Values)
            {
                switch (p.role)
                {
                    case Role.Brake: BrakeHeld = true; break;
                    case Role.Jump: JumpHeld = true; break;
                    case Role.Kick:
                        KickAiming = true;
                        KickStartScreen = p.start;
                        KickCurrentScreen = p.current;
                        break;
                }
            }

            ReadKeyboard();
        }

        Role ClassifyDown(Vector2 pos)
        {
            if (JumpButtonScreenRect.Contains(pos)) return Role.Jump;
            if (IsNearBall(pos) && !AnyPointerWithRole(Role.Kick)) return Role.Kick;
            if (pos.x < Screen.width * brakeZoneWidth) return Role.Brake;
            return Role.TapOrSwipe;
        }

        void OnPointerMove(Pointer p)
        {
            if (p.role != Role.TapOrSwipe) return;
            bool quick = Time.unscaledTime - p.startTime <= swipeMaxDuration;
            if (quick && p.current.y - p.start.y >= swipeUpMinInches * Dpi)
            {
                // Swipe up turns into a held jump so the kid jumps higher while the finger stays down.
                p.role = Role.Jump;
                JumpPressed = true;
            }
        }

        void OnPointerUp(Pointer p)
        {
            if (p.role == Role.Kick)
            {
                KickReleased = true;
                KickStartScreen = p.start;
                KickCurrentScreen = p.current;
            }
            else if (p.role == Role.TapOrSwipe)
            {
                bool shortTap = Time.unscaledTime - p.startTime <= tapMaxDuration;
                bool still = (p.current - p.start).magnitude <= tapMaxMoveInches * Dpi;
                if (shortTap && still) TouchPressed = true;
            }
        }

        bool IsNearBall(Vector2 screenPos)
        {
            if (ball == null || worldCamera == null) return false;
            Vector3 ballScreen = worldCamera.WorldToScreenPoint(ball.position);
            float pixelsPerUnit = Screen.height / (2f * worldCamera.orthographicSize);
            float radius = Mathf.Max(ballGrabRadiusInches * Dpi, ballWorldRadius * pixelsPerUnit * 1.5f);
            return ((Vector2)ballScreen - screenPos).sqrMagnitude <= radius * radius;
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

        void ReadKeyboard()
        {
            var kb = Keyboard.current;
            if (kb == null) return;
            if (kb.aKey.isPressed || kb.leftArrowKey.isPressed || kb.leftShiftKey.isPressed) BrakeHeld = true;
            if (kb.spaceKey.wasPressedThisFrame || kb.wKey.wasPressedThisFrame || kb.upArrowKey.wasPressedThisFrame) JumpPressed = true;
            if (kb.spaceKey.isPressed || kb.wKey.isPressed || kb.upArrowKey.isPressed) JumpHeld = true;
            if (kb.fKey.wasPressedThisFrame || kb.jKey.wasPressedThisFrame) TouchPressed = true;
            if (kb.rKey.wasPressedThisFrame) ResetPressed = true;
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

        void ReadKeyboard()
        {
            if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow) || Input.GetKey(KeyCode.LeftShift)) BrakeHeld = true;
            if (Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow)) JumpPressed = true;
            if (Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow)) JumpHeld = true;
            if (Input.GetKeyDown(KeyCode.F) || Input.GetKeyDown(KeyCode.J)) TouchPressed = true;
            if (Input.GetKeyDown(KeyCode.R)) ResetPressed = true;
            if (Input.GetKeyDown(KeyCode.Tab)) DebugTogglePressed = true;
        }
#else
        static void GatherPointers(List<Sample> into) { }
        void ReadKeyboard() { }
#endif
    }
}
