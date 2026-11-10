using DribbleToSchool.Audio;
using DribbleToSchool.Core;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Press feedback for buttons and cards: the face pushes down onto its darker base
    /// (UIKit.Button) with a crisp haptic click, squishes a little, and springs back with
    /// an overshoot on release. Raises a UI click event for audio.
    /// </summary>
    public class UIButtonFx : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler, IPointerClickHandler
    {
        /// <summary>How far a button face stands above its base, in canvas pixels.</summary>
        public const float Depth = 9f;

        public float pressedScale = 0.95f;
        /// <summary>Extra scale multiplier set by UIPulse on the same object.</summary>
        [System.NonSerialized] public float pulse = 1f;

        Vector3 baseScale = Vector3.one;
        float target = 1f;
        float current = 1f;
        bool down;
        float push;
        RectTransform face;
        Image faceImage, keyBase;
        Vector2 faceMin, faceMax;

        public static Color BaseColor(Color face)
        {
            return new Color(face.r * 0.66f, face.g * 0.62f, face.b * 0.66f, Mathf.Max(face.a, 0.9f));
        }

        void Awake()
        {
            baseScale = transform.localScale;
            var f = transform.Find("Face");
            if (f != null)
            {
                face = (RectTransform)f;
                faceImage = f.GetComponent<Image>();
                faceMin = face.offsetMin;
                faceMax = face.offsetMax;
            }
            var b = transform.Find("Base");
            if (b != null) keyBase = b.GetComponent<Image>();
        }

        bool Interactable
        {
            get
            {
                var selectable = GetComponent<Selectable>();
                return selectable == null || selectable.IsInteractable();
            }
        }

        public void OnPointerDown(PointerEventData eventData)
        {
            if (!Interactable) return;
            target = pressedScale;
            down = true;
            Haptics.Press(false);
        }

        public void OnPointerUp(PointerEventData eventData) { target = 1f; down = false; }
        public void OnPointerExit(PointerEventData eventData) { target = 1f; down = false; }

        public void OnPointerClick(PointerEventData eventData)
        {
            if (!Interactable) return;
            current = 1.06f;   // little overshoot on release
            GameEvents.Raise(GameEventType.UIClick, Vector2.zero, 0.5f);
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            current = Mathf.Lerp(current, target, 1f - Mathf.Exp(-18f * dt));
            // The eases only ever approach their targets, so without landing on them a released button would keep
            // moving by invisible fractions of a pixel for seconds (the push decays all the way down to float
            // underflow), and every one of those frames rebuilds its face, shine and best-fit label. Within these
            // limits (a ten-thousandth of the scale, a hundredth of a canvas pixel of push) nothing visible is left.
            if (Mathf.Abs(current - target) < 1e-4f) current = target;
            // Write only when the value really changes: a write dirties the transform, and can have the canvas
            // re-batch, even when nothing moved. (Compared with what the transform holds now, not with our last
            // write, so anything else that scales this object, such as the UIPopIn on the Stuck? button, is
            // overridden exactly as before.)
            var tr = transform;
            Vector3 scale = baseScale * current * pulse;
            if (tr.localScale != scale) tr.localScale = scale;

            push = down ? Mathf.MoveTowards(push, 1f, dt * 30f) : Mathf.Lerp(push, 0f, 1f - Mathf.Exp(-20f * dt));
            if (!down && push < 1e-3f) push = 0f;
            if (face != null)
            {
                Vector2 offset = new Vector2(0f, -Depth * 0.8f * push);
                Vector2 min = faceMin + offset, max = faceMax + offset;
                if (face.offsetMin != min) face.offsetMin = min;
                if (face.offsetMax != max) face.offsetMax = max;
            }
            // Keep the base matched to the face (toggles recolour the face).
            if (keyBase != null && faceImage != null) keyBase.color = BaseColor(faceImage.color);
        }
    }
}
