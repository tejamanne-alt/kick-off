using DribbleToSchool.Core;
using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>The three pickups of a Holiday Run.</summary>
    public enum PowerUpKind { Magnet, Shield, Turbo }

    /// <summary>
    /// The root of a stage's scene (inactive in the scene file; the streamer prepares it and switches
    /// it on when the kid gets near). Everything of the stage hangs under it. Obstacle and pickup
    /// layouts can come in several <see cref="variants"/>: one is chosen at random each time the stage
    /// loads, so a day never plays the same twice, while the scenery stays put.
    /// </summary>
    public class RunChunk : MonoBehaviour
    {
        public int stage;
        public float startX, endX;
        [Tooltip("Alternative layers of obstacles and pickups (children of this object, inactive in the file). " +
            "One is switched on at random when the stage loads. Empty: everything stays as built.")]
        public GameObject[] variants = new GameObject[0];

        /// <summary>Which variant is on (-1: none to choose from).</summary>
        public int ChosenVariant { get; private set; }

        /// <summary>Choose and switch on one variant; call while the stage is still inactive.</summary>
        public void Prepare(System.Random rng)
        {
            ChosenVariant = -1;
            if (variants == null || variants.Length == 0) return;
            ChosenVariant = rng.Next(variants.Length);
            for (int i = 0; i < variants.Length; i++)
                if (variants[i] != null) variants[i].SetActive(i == ChosenVariant);
        }
    }

    /// <summary>
    /// Marks something solid in the kid's way (put on the top-level object of a crate, a wall, a car,
    /// a barrier to slide under...). The director reads a head-on touch of its colliders as a crash,
    /// counts it as cleared once the kid is past it, and scores a near miss for passing close.
    /// </summary>
    public class RunSolid : MonoBehaviour
    {
        [Tooltip("Hitting it head-on ends the run.")]
        public bool deadly = true;

        /// <summary>The director has counted this one as passed.</summary>
        public bool Cleared { get; set; }

        Collider2D[] colliders;

        /// <summary>The solid colliders (triggers excluded) of this obstacle.</summary>
        public Collider2D[] Colliders
        {
            get
            {
                if (colliders == null)
                {
                    var all = GetComponentsInChildren<Collider2D>(true);
                    var solid = new System.Collections.Generic.List<Collider2D>();
                    foreach (var c in all) if (!c.isTrigger) solid.Add(c);
                    colliders = solid.ToArray();
                }
                return colliders;
            }
        }

        /// <summary>World x of the obstacle's middle.</summary>
        public float CenterX
        {
            get
            {
                var cs = Colliders;
                return cs.Length > 0 ? cs[0].bounds.center.x : transform.position.x;
            }
        }

        /// <summary>World x of its right-hand edge: the kid is past it once beyond this.</summary>
        public float RightX
        {
            get
            {
                float right = transform.position.x;
                foreach (var c in Colliders) right = Mathf.Max(right, c.bounds.max.x);
                return right;
            }
        }

        protected virtual void OnEnable()
        {
            Cleared = false;
            var director = HolidayRunDirector.Current;
            if (director != null) director.Register(this);
        }

        protected virtual void OnDisable()
        {
            var director = HolidayRunDirector.Current;
            if (director != null) director.Unregister(this);
        }
    }

    /// <summary>
    /// A crate, cone stack or target that a kicked ball (or a turbo run) smashes: it bursts, shedding
    /// coins, and is no longer in the way.
    /// </summary>
    public class RunBreakable : RunSolid
    {
        [Tooltip("Coins it is worth when smashed.")]
        public int coins = 3;

        public bool Smashed { get; private set; }

        protected override void OnEnable()
        {
            base.OnEnable();
            Smashed = false;
        }

        /// <summary>Burst it. <paramref name="point"/> is where it was hit.</summary>
        public void Smash(Vector2 point)
        {
            if (Smashed) return;
            Smashed = true;
            foreach (var c in GetComponentsInChildren<Collider2D>(true)) c.enabled = false;
            foreach (var r in GetComponentsInChildren<Renderer>(true)) r.enabled = false;
            GameEvents.Raise(GameEventType.Kick, point, 0.8f);
            GameEvents.Raise(GameEventType.Coin, point, 0.6f);
            var director = HolidayRunDirector.Current;
            if (director != null) director.OnSmashed(this, point);
        }
    }

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
