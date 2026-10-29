using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// The dimness of an underpass: an even darkening of the view, a little deeper at the
    /// edges, that fades in and out with DarkZone.Wanted. The underpass lamps (LampGlow)
    /// draw their light over it.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class DarknessOverlay : MonoBehaviour
    {
        public Transform follow;
        public float fadeSpeed = 3f;
        [Tooltip("Size of the overlay in world units at the kid's depth; it must cover the whole view.")]
        public float coverage = 60f;

        SpriteRenderer sr;
        float amount;

        void Awake()
        {
            sr = GetComponent<SpriteRenderer>();
            sr.sprite = BuildSprite();
            sr.sortingOrder = 200;
            sr.color = new Color(0f, 0f, 0.03f, 0f);
        }

        void LateUpdate()
        {
            amount = Mathf.MoveTowards(amount, DarkZone.Wanted, fadeSpeed * Time.deltaTime);
            Color c = sr.color;
            c.a = amount;
            sr.color = c;
            sr.enabled = amount > 0.001f;
            if (!sr.enabled || follow == null) return;

            // The sprite is a 2x2-unit square; scale it to cover the whole view.
            Vector3 target = new Vector3(follow.position.x, follow.position.y + 0.3f, 0f);
            float holeScale = coverage * 0.5f;
            var cam = Camera.main;
            if (cam != null && !cam.orthographic)
            {
                // With a perspective camera, sit most of the way toward the camera on the line to the
                // kid, so nearer scenery (the front pavement) is covered too, and shrink to match.
                Vector3 eye = cam.transform.position;
                const float t = 0.6f;
                transform.position = Vector3.Lerp(target, eye, t);
                holeScale *= 1f - t;
            }
            else
            {
                transform.position = target;
            }
            transform.localScale = new Vector3(holeScale, holeScale, 1f);
        }

        static Sprite BuildSprite()
        {
            const int size = 128;
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    // Even dimness, a little deeper toward the edges of the view.
                    float d = Mathf.Sqrt(u * u + v * v);
                    float a = Mathf.Lerp(0.82f, 1f, Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.15f, 0.45f, d)));
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            // 2 world units across at scale 1.
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), size / 2f);
        }
    }
}
