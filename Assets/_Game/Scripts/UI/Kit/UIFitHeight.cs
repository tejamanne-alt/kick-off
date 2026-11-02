using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Keeps a block of UI that was laid out for a fixed height inside the room its parent really has:
    /// when the parent is shorter (a phone's safe area keeps clear of the home bar, or the screen is a
    /// short one), the block shrinks from its top left corner so nothing overlaps or runs off the bottom.
    /// It never grows. The block's own RectTransform should be top-left anchored and as tall as the
    /// design (<see cref="designHeight"/>).
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class UIFitHeight : MonoBehaviour
    {
        [Tooltip("The height the block was laid out for (canvas units).")]
        public float designHeight = 1080f;
        [Tooltip("Never shrink below this: the block has to stay usable on the smallest screens.")]
        public float minScale = 0.6f;

        float applied = -1f;

        void OnEnable()
        {
            Apply(true);
        }

        void LateUpdate()
        {
            Apply(false);
        }

        /// <summary>The scale that makes a block laid out for <paramref name="design"/> fit in <paramref name="room"/> (1 when it already does).</summary>
        public static float ScaleFor(float room, float design, float min)
        {
            if (room <= 1f || design <= 0f) return 1f;
            return Mathf.Clamp(room / design, min, 1f);
        }

        void Apply(bool force)
        {
            var parent = transform.parent as RectTransform;
            if (parent == null) return;
            float room = parent.rect.height;
            if (room <= 1f || (!force && Mathf.Approximately(room, applied))) return;
            applied = room;
            float s = ScaleFor(room, designHeight, minScale);
            transform.localScale = new Vector3(s, s, 1f);
        }
    }
}
