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
        [Tooltip("Dressed in the outfit's shirt and shorts colours (a CharacterBody3D, ModelOutfit or CharacterChoice).")]
        public MonoBehaviour kidBody;
        [Tooltip("The pennant on each playable character's bag.")]
        public SpriteRenderer[] backpackFlags;
        [Tooltip("A Holiday Run: the kid is not in school uniform unless they chose to be. While the school uniform is the equipped outfit, " +
            "the Holiday outfit is worn instead (casual, no tie); any other outfit the player equipped is kept.")]
        public bool holiday;

        public const string SchoolOutfitId = "outfit_school";
        public const string HolidayOutfitId = "outfit_holiday";

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
            ApplyBall(catalog.Find(save.equippedBall));
            ApplyOutfit(OutfitFor(save.equippedOutfit));
            ApplyFlag(catalog.Find(save.equippedFlag));
            ApplyTrail(catalog.Find(save.equippedTrail));
        }

        /// <summary>The id of the outfit to wear: the Holiday one in a Holiday Run instead of the default school uniform; anything else the player equipped is kept.</summary>
        public static string OutfitIdFor(bool holiday, string equippedId)
        {
            if (holiday && (string.IsNullOrEmpty(equippedId) || equippedId == SchoolOutfitId)) return HolidayOutfitId;
            return equippedId;
        }

        CosmeticItem OutfitFor(string equippedId)
        {
            var item = catalog.Find(OutfitIdFor(holiday, equippedId));
            return item != null ? item : catalog.Find(equippedId);
        }

        /// <summary>
        /// Show one item without equipping it (the Locker Room's try-on on the menu's teen).
        /// <see cref="Apply"/> puts the equipped things back.
        /// </summary>
        public void Preview(CosmeticItem item)
        {
            if (item == null) return;
            switch (item.category)
            {
                case CosmeticCategory.Ball: ApplyBall(item); break;
                case CosmeticCategory.Outfit: ApplyOutfit(item); break;
                case CosmeticCategory.Flag: ApplyFlag(item); break;
                case CosmeticCategory.Trail: ApplyTrail(item); break;
            }
        }

        void ApplyBall(CosmeticItem ball)
        {
            if (ball == null || ballRenderer == null) return;
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

        void ApplyOutfit(CosmeticItem outfit)
        {
            var dressable = kidBody as Presentation.IOutfit;
            if (outfit != null && dressable != null && dressedIn != outfit.id)
            {
                // Re-dressing is cheap but not free: only when the outfit changes. The school uniform
                // is dressed like any other outfit (a white shirt, navy shorts): the teens were modelled
                // in casual colours that sat too close to the street's greens and sand.
                dressedIn = outfit.id;
                dressable.SetOutfit(outfit.primary, outfit.secondary);
                // The third colour of an outfit is the tie's (fully see-through: no tie).
                var accented = kidBody as Presentation.IAccentOutfit;
                if (accented != null) accented.SetAccent(outfit.accent);
            }
        }

        void ApplyFlag(CosmeticItem flag)
        {
            if (backpackFlags == null) return;
            bool show = flag != null && flag.pattern != CosmeticPattern.None;
            foreach (var backpackFlag in backpackFlags)
            {
                if (backpackFlag == null) continue;
                backpackFlag.enabled = show;
                if (show) backpackFlag.sprite = CosmeticArt.FlagSprite(flag);
            }
        }

        void ApplyTrail(CosmeticItem trail)
        {
            if (ballTrail == null) return;
            bool show = trail != null && trail.pattern != CosmeticPattern.None;
            ballTrail.enabled = show;
            if (!show) return;
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
