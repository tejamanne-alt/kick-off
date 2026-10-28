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
            transform.localScale = baseScale * current * pulse;

            push = down ? Mathf.MoveTowards(push, 1f, dt * 30f) : Mathf.Lerp(push, 0f, 1f - Mathf.Exp(-20f * dt));
            if (face != null)
            {
                Vector2 offset = new Vector2(0f, -Depth * 0.8f * push);
                face.offsetMin = faceMin + offset;
                face.offsetMax = faceMax + offset;
            }
            // Keep the base matched to the face (toggles recolour the face).
            if (keyBase != null && faceImage != null) keyBase.color = BaseColor(faceImage.color);
        }
    }
}
