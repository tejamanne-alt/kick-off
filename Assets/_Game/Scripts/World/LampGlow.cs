using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A dim ceiling lamp's light: a soft cone of light falling to the floor and a pool of light
    /// on the ground under it, drawn additively over everything (including the underpass
    /// darkness) so whatever stands under the lamp is lit. Sprites are made when it loads.
    /// </summary>
    public class LampGlow : MonoBehaviour
    {
        [Tooltip("Additive sprite material.")]
        public Material material;
        public float height = 3.2f;
        public Color color = new Color(1f, 0.85f, 0.55f, 0.32f);

        static Sprite beam, pool, bulb;

        void Awake()
        {
            if (beam == null) MakeSprites();
            // The cone of light from the fitting down to the floor.
            var cone = Child("Beam", beam, new Vector3(0f, -height * 0.5f, 0f), new Vector3(1.8f, height, 1f), color, 220);
            cone.transform.localRotation = Quaternion.identity;
            // The pool of light on the ground, lying flat.
            var floor = Child("Pool", pool, new Vector3(0f, -height + 0.02f, 0f), new Vector3(3.2f, 2.2f, 1f), new Color(color.r, color.g, color.b, color.a * 1.3f), 219);
            floor.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
            // The fitting itself, glowing.
            Child("Bulb", bulb, Vector3.zero, new Vector3(0.9f, 0.25f, 1f), new Color(1f, 0.95f, 0.8f, 0.9f), 221);
        }

        SpriteRenderer Child(string name, Sprite sprite, Vector3 localPos, Vector3 scale, Color c, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            go.transform.localPosition = localPos;
            go.transform.localScale = scale;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sharedMaterial = material;
            sr.color = c;
            sr.sortingOrder = order;
            return sr;
        }

        static void MakeSprites()
        {
            beam = Make(64, (u, v) =>
            {
                // u: -1..1 across, v: 0 at the floor .. 1 at the lamp. Narrow at the lamp, wide below.
                float halfWidth = Mathf.Lerp(1f, 0.18f, v);
                float across = Mathf.Clamp01(1f - Mathf.Abs(u) / halfWidth);
                return across * across * Mathf.Lerp(0.35f, 1f, v);
            });
            pool = Make(64, (u, v) =>
            {
                float r = Mathf.Sqrt(u * u + (v * 2f - 1f) * (v * 2f - 1f));
                float k = Mathf.Clamp01(1f - r);
                return k * k;
            });
            bulb = Make(32, (u, v) =>
            {
                float r = Mathf.Sqrt(u * u + (v * 2f - 1f) * (v * 2f - 1f));
                return Mathf.Clamp01((1f - r) * 3f);
            });
        }

        delegate float Fn(float u, float v);

        /// <summary>A white sprite 1 x 1 unit with alpha from fn(u in -1..1, v in 0..1 bottom to top).</summary>
        static Sprite Make(int n, Fn fn)
        {
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float u = (x + 0.5f) / n * 2f - 1f, v = (y + 0.5f) / n;
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, fn(u, v)));
                }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);
        }
    }
}
