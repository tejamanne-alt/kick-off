using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>The three pickups of a Holiday Run.</summary>
    public enum PowerUpKind { Magnet, Shield, Turbo }

    /// <summary>
    /// A magnet, shield or turbo floating in the path: a glass orb with its icon, bobbing. The kid
    /// (or the ball) running into it takes it.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class PowerUp : MonoBehaviour
    {
        public PowerUpKind kind = PowerUpKind.Magnet;

        public static Color ColorOf(PowerUpKind kind)
        {
            switch (kind)
            {
                case PowerUpKind.Shield: return new Color(0.3f, 0.75f, 1f);
                case PowerUpKind.Turbo: return new Color(1f, 0.62f, 0.15f);
                default: return new Color(0.95f, 0.3f, 0.45f);
            }
        }

        public static Sprite IconOf(PowerUpKind kind)
        {
            switch (kind)
            {
                case PowerUpKind.Shield: return ProceduralSprites.Shield;
                case PowerUpKind.Turbo: return ProceduralSprites.Bolt;
                default: return ProceduralSprites.Magnet;
            }
        }

        Transform visual;
        Transform halo;
        SpriteRenderer[] parts;
        float[] baseAlpha;
        bool taken;
        float takenAt;
        float phase;

        void Awake()
        {
            var col = GetComponent<Collider2D>();
            col.isTrigger = true;
            phase = transform.position.x * 0.37f;
            Build();
        }

        void Build()
        {
            Color c = ColorOf(kind);
            visual = new GameObject("Orb").transform;
            visual.SetParent(transform, false);
            visual.localPosition = new Vector3(0f, 0f, -0.25f);

            halo = Sprite(visual, "Halo", ProceduralSprites.SoftDisc, new Color(c.r, c.g, c.b, 0.55f), 1.5f, 30);
            Sprite(visual, "Glass", ProceduralSprites.SoftEdgeDisc, new Color(c.r, c.g, c.b, 0.95f), 0.92f, 31);
            Sprite(visual, "Rim", ProceduralSprites.Ring, new Color(1f, 1f, 1f, 0.9f), 0.92f, 32);
            Sprite(visual, "Icon", IconOf(kind), new Color(1f, 1f, 1f, 0.97f), 0.52f, 33);

            parts = visual.GetComponentsInChildren<SpriteRenderer>();
            baseAlpha = new float[parts.Length];
            for (int i = 0; i < parts.Length; i++) baseAlpha[i] = parts[i].color.a;
        }

        static Transform Sprite(Transform parent, string name, Sprite sprite, Color color, float scale, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localScale = Vector3.one * scale;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.color = color;
            sr.sortingOrder = order;
            return go.transform;
        }

        void Update()
        {
            if (visual == null) return;
            if (taken)
            {
                // Swells and fades away.
                float t = Mathf.Clamp01((Time.time - takenAt) / 0.3f);
                visual.localScale = Vector3.one * (1f + t * 0.6f);
                for (int i = 0; i < parts.Length; i++)
                {
                    Color col = parts[i].color;
                    parts[i].color = new Color(col.r, col.g, col.b, baseAlpha[i] * (1f - t));
                }
                if (t >= 1f) visual.gameObject.SetActive(false);
                return;
            }
            float bob = Mathf.Sin(Time.time * 2.4f + phase) * 0.12f;
            visual.localPosition = new Vector3(0f, bob, -0.25f);
            float pulse = 1f + Mathf.Sin(Time.time * 5f + phase) * 0.08f;
            if (halo != null) halo.localScale = Vector3.one * 1.5f * pulse;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (taken) return;
            var rb = other.attachedRigidbody;
            if (rb == null || rb.GetComponent<KidController>() == null) return;
            var director = HolidayRunDirector.Current;
            if (director == null || director.Phase != RunPhase.Running) return;

            taken = true;
            takenAt = Time.time;
            GetComponent<Collider2D>().enabled = false;
            director.CollectPowerUp(kind, transform.position);
        }
    }
}
