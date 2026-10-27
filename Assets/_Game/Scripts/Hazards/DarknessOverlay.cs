using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Full-screen darkness with a soft hole of light that follows the kid.
    /// Lives on a child of the camera; fades with DarkZone.Wanted.
    /// </summary>
    [RequireComponent(typeof(SpriteRenderer))]
    public class DarknessOverlay : MonoBehaviour
    {
        public Transform follow;
        public float fadeSpeed = 3f;
        [Tooltip("Radius of the light pool in world units.")]
        public float lightRadius = 3.2f;

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

            // The sprite is a 2x2-unit square with the hole in the middle; scale it so the
            // hole matches lightRadius and the dark part covers the whole view.
            transform.position = new Vector3(follow.position.x, follow.position.y + 0.3f, 0f);
            float holeScale = lightRadius / 0.25f;   // hole radius is 0.25 units in the sprite
            transform.localScale = new Vector3(holeScale, holeScale, 1f);
        }

        static Sprite BuildSprite()
        {
            const int size = 256;
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    float d = Mathf.Sqrt(u * u + v * v) * 1f;     // 0 centre .. 1 edge (sprite is 2 units)
                    float a = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.12f, 0.3f, d));
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            // 2 world units across at scale 1; hole edge ~0.25 units from centre.
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), size / 2f);
        }
    }
}
