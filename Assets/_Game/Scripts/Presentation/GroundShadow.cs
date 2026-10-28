using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// A soft round shadow lying on the ground under a body (the kid, the ball), found by a
    /// ray straight down. It shrinks and fades as the body rises, which helps read heights.
    /// </summary>
    public class GroundShadow : MonoBehaviour
    {
        public Rigidbody2D target;
        [Tooltip("Bodies the ray ignores (e.g. the kid for the ball's shadow).")]
        public Rigidbody2D[] ignore;
        public SpriteRenderer shadow;
        public float maxDistance = 5f;
        public Vector2 size = new Vector2(0.55f, 0.25f);
        [Range(0f, 1f)] public float maxAlpha = 0.4f;

        readonly RaycastHit2D[] hits = new RaycastHit2D[6];
        ContactFilter2D filter;

        void Awake()
        {
            filter = new ContactFilter2D();
            filter.useTriggers = false;
        }

        void LateUpdate()
        {
            if (target == null || shadow == null) return;
            int count = Physics2D.Raycast(target.position, Vector2.down, filter, hits, maxDistance);
            float best = float.MaxValue;
            Vector2 point = Vector2.zero;
            for (int i = 0; i < count; i++)
            {
                var rb = hits[i].rigidbody;
                if (rb == target || Ignored(rb)) continue;
                if (hits[i].distance < best) { best = hits[i].distance; point = hits[i].point; }
            }
            if (best == float.MaxValue)
            {
                shadow.enabled = false;
                return;
            }
            shadow.enabled = true;
            float k = 1f - Mathf.Clamp01(best / maxDistance);
            // Lies flat on the ground (the sprite's face turned up).
            shadow.transform.position = new Vector3(point.x, point.y + 0.015f, 0f);
            shadow.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            float s = Mathf.Lerp(0.45f, 1f, k);
            Vector2 sprite = shadow.sprite != null ? (Vector2)shadow.sprite.bounds.size : Vector2.one;
            shadow.transform.localScale = new Vector3(size.x * s / Mathf.Max(sprite.x, 0.01f), size.y * s / Mathf.Max(sprite.y, 0.01f), 1f);
            Color c = shadow.color;
            c.a = Mathf.Lerp(0.08f, maxAlpha, k);
            shadow.color = c;
        }

        bool Ignored(Rigidbody2D rb)
        {
            if (rb == null || ignore == null) return false;
            foreach (var other in ignore) if (other == rb) return true;
            return false;
        }
    }
}
