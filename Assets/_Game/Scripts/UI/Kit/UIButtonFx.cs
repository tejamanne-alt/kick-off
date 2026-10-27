using DribbleToSchool.Core;
using UnityEngine;
using UnityEngine.EventSystems;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Squishy press feedback for buttons and cards; raises a UI click event for audio/haptics.</summary>
    public class UIButtonFx : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler, IPointerClickHandler
    {
        public float pressedScale = 0.92f;

        Vector3 baseScale = Vector3.one;
        float target = 1f;
        float current = 1f;

        void Awake()
        {
            baseScale = transform.localScale;
        }

        public void OnPointerDown(PointerEventData eventData) { target = pressedScale; }
        public void OnPointerUp(PointerEventData eventData) { target = 1f; }
        public void OnPointerExit(PointerEventData eventData) { target = 1f; }

        public void OnPointerClick(PointerEventData eventData)
        {
            current = 1.08f;   // little overshoot on release
            GameEvents.Raise(GameEventType.UIClick, Vector2.zero, 0.5f);
        }

        void Update()
        {
            current = Mathf.Lerp(current, target, 1f - Mathf.Exp(-18f * Time.unscaledDeltaTime));
            transform.localScale = baseScale * current;
        }
    }
}
