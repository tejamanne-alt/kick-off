using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Scales a block of UI that was laid out at a fixed design size (the town map's picture is 3200 x 1800 pixels) so that a
    /// chosen part of it, <see cref="fitSize"/> centred on <see cref="fitCentre"/> (the picture's core), fits whole inside the
    /// parent's rect, whatever the screen's shape: the largest scale at which that part fits both ways, kept between
    /// <see cref="minScale"/> and <see cref="maxScale"/>. The block is moved so that the part sits in the middle of the
    /// parent, and the rest of the block (the picture's ring) simply spills out round it. Set the block's anchors and pivot
    /// (both the centre) and size (the design size) when making it. Like UIFitHeight it waits for the parent to have a
    /// size, and follows it when the screen turns or is resized.
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class UIFitRect : MonoBehaviour
    {
        public Vector2 designSize = new Vector2(1600f, 900f);
        [Tooltip("The part that has to fit (design pixels, y down); zero size means the whole block.")]
        public Vector2 fitSize;
        [Tooltip("The centre of that part in the design (pixels from the top left, y down).")]
        public Vector2 fitCentre;
        [Tooltip("Never smaller than this.")]
        public float minScale = 0.3f;
        [Tooltip("Never bigger than this (a block meant to shrink to fit can also be kept from growing).")]
        public float maxScale = 1f;

        /// <summary>The scale the block is at now (1 until the parent has a size).</summary>
        public float Scale { get { return transform.localScale.x; } }

        void OnEnable()
        {
            Apply();
        }

        // Every frame, not only when the parent's size changes: the fields are set right after AddComponent has run OnEnable,
        // and it costs a handful of multiplications.
        void LateUpdate()
        {
            Apply();
        }

        /// <summary>The scale at which a part of <paramref name="fit"/> size fits whole in <paramref name="room"/>.</summary>
        public static float ScaleFor(Vector2 room, Vector2 fit, float min, float max)
        {
            if (room.x <= 1f || room.y <= 1f || fit.x <= 0f || fit.y <= 0f) return Mathf.Clamp(1f, min, max);
            return Mathf.Clamp(Mathf.Min(room.x / fit.x, room.y / fit.y), min, max);
        }

        void Apply()
        {
            var parent = transform.parent as RectTransform;
            if (parent == null) return;
            Vector2 room = parent.rect.size;
            if (room.x <= 1f || room.y <= 1f) return;
            Vector2 part = fitSize.x > 0f && fitSize.y > 0f ? fitSize : designSize;
            Vector2 centre = fitSize.x > 0f && fitSize.y > 0f ? fitCentre : designSize * 0.5f;
            float s = ScaleFor(room, part, minScale, maxScale);
            // The block's centre is where the part's centre should be, moved by how far the part's centre is off the block's.
            Vector2 off = centre - designSize * 0.5f;                       // y down
            Vector2 position = new Vector2(-off.x * s, off.y * s);
            var rect = (RectTransform)transform;
            if (!Mathf.Approximately(transform.localScale.x, s)) transform.localScale = new Vector3(s, s, 1f);
            if (rect.anchoredPosition != position) rect.anchoredPosition = position;
        }
    }
}
