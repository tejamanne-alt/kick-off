using UnityEngine;

namespace DribbleToSchool.Cosmetics
{
    public enum CosmeticCategory { Ball, Flag, Outfit, Trail }

    public enum CosmeticPattern
    {
        // Balls
        Classic, Solid, Stripes, Dots, Rings, Planet, Fruit, Star, Neon, Diagonal, Retro,
        // Flags
        None, VerticalTri, HorizontalTri, HorizontalBi, NordicCross, CenterDot, BandsWithDot,
        // Trails
        Gradient, Rainbow,
        // Sticker rewards (added last: saved items store the pattern as a number)
        /// <summary>Iridescent pastel rainbow, like a holo sticker (balls, flags, trails).</summary>
        Holo,
        /// <summary>Polished metal foil in the primary colour with bright glints (balls).</summary>
        Foil,
    }

    public enum Rarity { Common, Rare, Epic }

    /// <summary>How an item is unlocked: bought with coins, or earned with stickers (never sold).</summary>
    public enum CosmeticUnlock
    {
        Coins,
        /// <summary>Finding every sticker in one chapter (unlockValue = the chapter).</summary>
        StickerSet,
        /// <summary>Finding a number of stickers in all (unlockValue = how many).</summary>
        StickerCount,
    }

    /// <summary>One cosmetic: ball skin, backpack flag, outfit or trail. Visuals are drawn from these values.</summary>
    [CreateAssetMenu(menuName = "Kick Off/Cosmetic Item", fileName = "Cosmetic")]
    public class CosmeticItem : ScriptableObject
    {
        public string id = "ball_classic";
        public string displayName = "Classic";
        public CosmeticCategory category;
        public Rarity rarity;
        [Tooltip("Coin price. 0 = free / owned from the start.")]
        public int price;
        [Tooltip("Coins, or a sticker reward the Locker Room never sells (see StickerRewards).")]
        public CosmeticUnlock unlock = CosmeticUnlock.Coins;
        [Tooltip("StickerSet: the chapter whose stickers must all be found. StickerCount: how many stickers.")]
        public int unlockValue;
        public CosmeticPattern pattern;
        public Color primary = Color.white;
        public Color secondary = Color.black;
        public Color accent = Color.gray;

        /// <summary>Earned with stickers rather than bought.</summary>
        public bool IsStickerReward { get { return unlock != CosmeticUnlock.Coins; } }
    }
}
