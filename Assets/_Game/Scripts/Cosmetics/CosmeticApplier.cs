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
        [Tooltip("The 3D ball; the skin's drawing is projected onto it.")]
        public Renderer ballRenderer;
        public TrailRenderer ballTrail;

        [Header("Kid")]
        [Tooltip("Dressed in the outfit's shirt and shorts colours.")]
        public Presentation.CharacterBody3D kidBody;
        public SpriteRenderer backpackFlag;

        static readonly int MainTexId = Shader.PropertyToID("_MainTex");
        static readonly int MainTexStId = Shader.PropertyToID("_MainTex_ST");
        MaterialPropertyBlock block;
        string dressedIn;

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
                // The ball's UVs map its front and back onto the skin's drawing of a ball.
                var sprite = CosmeticArt.BallSprite(ball);
                if (block == null) block = new MaterialPropertyBlock();
                ballRenderer.GetPropertyBlock(block);
                block.SetTexture(MainTexId, sprite.texture);
                Rect r = sprite.textureRect;
                float w = sprite.texture.width, h = sprite.texture.height;
                block.SetVector(MainTexStId, new Vector4(r.width / w, r.height / h, r.x / w, r.y / h));
                ballRenderer.SetPropertyBlock(block);
            }

            var outfit = catalog.Find(save.equippedOutfit);
            if (outfit != null && kidBody != null && dressedIn != outfit.id)
            {
                // Rebuilding the body is cheap but not free: only when the outfit changes.
                dressedIn = outfit.id;
                kidBody.SetOutfit(outfit.primary, outfit.secondary);
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
