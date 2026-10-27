using DribbleToSchool.Progression;
using UnityEngine;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>
    /// Dresses the kid and the ball in the equipped cosmetics when a level starts
    /// (and whenever the save changes, e.g. after equipping in a menu).
    /// </summary>
    public class CosmeticApplier : MonoBehaviour
    {
        public CosmeticCatalog catalog;

        [Header("Ball")]
        public SpriteRenderer ballRenderer;
        [Tooltip("Placeholder details hidden once a drawn skin is applied.")]
        public GameObject[] ballPlaceholderDetails;
        public TrailRenderer ballTrail;

        [Header("Kid")]
        [Tooltip("Renderers tinted with the outfit's shirt colour.")]
        public SpriteRenderer[] shirtRenderers;
        [Tooltip("Renderers tinted with the outfit's shorts colour.")]
        public SpriteRenderer[] shortsRenderers;
        public SpriteRenderer backpackFlag;

        void OnEnable()
        {
            SaveSystem.Changed += Apply;
            Apply();
        }

        void OnDisable()
        {
            SaveSystem.Changed -= Apply;
        }

        public void Apply()
        {
            if (catalog == null) return;
            var save = SaveSystem.Data;

            var ball = catalog.Find(save.equippedBall);
            if (ball != null && ballRenderer != null)
            {
                ballRenderer.sprite = CosmeticArt.BallSprite(ball);
                ballRenderer.color = Color.white;
                // The drawn skin already includes the patches, so hide the placeholder ones.
                if (ballPlaceholderDetails != null)
                {
                    foreach (var go in ballPlaceholderDetails)
                    {
                        if (go != null) go.SetActive(false);
                    }
                }
            }

            var outfit = catalog.Find(save.equippedOutfit);
            if (outfit != null)
            {
                if (shirtRenderers != null) foreach (var r in shirtRenderers) if (r != null) r.color = outfit.primary;
                if (shortsRenderers != null) foreach (var r in shortsRenderers) if (r != null) r.color = outfit.secondary;
            }

            var flag = catalog.Find(save.equippedFlag);
            if (backpackFlag != null)
            {
                bool show = flag != null && flag.pattern != CosmeticPattern.None;
                backpackFlag.enabled = show;
                if (show) backpackFlag.sprite = CosmeticArt.FlagSprite(flag);
            }

            var trail = catalog.Find(save.equippedTrail);
            if (ballTrail != null)
            {
                bool show = trail != null && trail.pattern != CosmeticPattern.None;
                ballTrail.enabled = show;
                if (show)
                {
                    var gradient = new Gradient();
                    gradient.SetKeys(
                        new[]
                        {
                            new GradientColorKey(CosmeticArt.TrailColor(trail, 0f), 0f),
                            new GradientColorKey(CosmeticArt.TrailColor(trail, 0.5f), 0.5f),
                            new GradientColorKey(CosmeticArt.TrailColor(trail, 1f), 1f),
                        },
                        new[] { new GradientAlphaKey(0.85f, 0f), new GradientAlphaKey(0f, 1f) });
                    ballTrail.colorGradient = gradient;
                }
            }
        }
    }
}
