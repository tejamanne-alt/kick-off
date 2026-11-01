using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Pickups
{
    /// <summary>
    /// The level's hidden sticker for the album. Collected by the kid or the ball;
    /// saved when the level is completed. Already-owned stickers show faded. On the 3D badge,
    /// the level's own album sticker is stuck to the front, so you can see which one it is.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Sticker : MonoBehaviour, IResettable
    {
        public Transform visual;
        public SpriteRenderer visualRenderer;
        [Tooltip("A 3D sticker's renderers (instead of the sprite): greyed when already owned, hidden once collected.")]
        public Renderer[] meshes;

        static readonly Color OwnedTint = new Color(0.72f, 0.72f, 0.78f);
        /// <summary>The album art on the badge's face: about 0.6 m across, on the 0.8 m badge.</summary>
        const float ArtSize = 0.88f;

        public bool Collected { get; private set; }

        float collectedAt;
        SpriteRenderer art;

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void Start()
        {
            AddArt();
            ApplyOwnedLook();
        }

        /// <summary>Stick the level's album sticker on the front of the 3D badge.</summary>
        void AddArt()
        {
            var level = LevelManager.Current;
            if (visual == null || meshes == null || meshes.Length == 0 || level == null || level.level == null) return;
            string id = level.level.levelId;
            if (!UI.StickerBook.HasArt(id)) return;
            var sprite = UI.StickerBook.Art(id, Color.white);
            var go = new GameObject("StickerArt");
            go.transform.SetParent(visual, false);
            go.transform.localPosition = new Vector3(0f, 0.02f, -0.14f);    // just in front of the badge's face
            float units = Mathf.Max(sprite.bounds.size.x, sprite.bounds.size.y);
            go.transform.localScale = Vector3.one * (ArtSize / Mathf.Max(0.01f, units));
            art = go.AddComponent<SpriteRenderer>();
            art.sprite = sprite;
            art.sortingOrder = 26;
        }

        /// <summary>Stickers already in the album show faded, so players know it's a repeat.</summary>
        void ApplyOwnedLook()
        {
            var level = LevelManager.Current;
            bool owned = level != null && level.level != null && Progression.SaveSystem.HasSticker(level.level.levelId);
            if (meshes != null)
                foreach (var r in meshes) World.Tint.Set(r, owned ? OwnedTint : Color.white);
            if (art != null) art.color = owned ? new Color(0.8f, 0.8f, 0.86f, 0.75f) : Color.white;
            if (visualRenderer == null) return;
            Color c = visualRenderer.color;
            c.a = owned ? 0.4f : 1f;
            visualRenderer.color = c;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (Collected) return;
            var rb = other.attachedRigidbody;
            if (rb == null) return;
            if (rb.GetComponent<KidController>() == null && rb.GetComponent<BallController>() == null) return;
            var level = LevelManager.Current;
            if (level == null) return;

            Collected = true;
            collectedAt = Time.time;
            level.CollectSticker();
            GameEvents.Raise(GameEventType.Sticker, transform.position);
        }

        void Update()
        {
            if (visual == null) return;
            if (Collected)
            {
                float t = Mathf.Clamp01((Time.time - collectedAt) / 0.5f);
                visual.localScale = Vector3.one * 0.7f * (1f + t * 0.6f);
                if (visualRenderer != null)
                {
                    Color c = visualRenderer.color;
                    c.a = 1f - t;
                    visualRenderer.color = c;
                }
                else if (t >= 1f) visual.gameObject.SetActive(false);
                return;
            }
            visual.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(Time.time * 2f) * 10f);
        }

        public void ResetState()
        {
            Collected = false;
            if (visual != null)
            {
                visual.localScale = Vector3.one * 0.7f;
                visual.gameObject.SetActive(true);
            }
            ApplyOwnedLook();
        }
    }
}
