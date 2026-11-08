using UnityEngine;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>(Added last: saved items store the category as a number.) Bag: a Locker Room bag, worn by each kid of their own choice (Cosmetics/Bags).</summary>
    public enum CosmeticCategory { Ball, Flag, Outfit, Trail, Bag }

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

    /// <summary>How an item is unlocked: bought with coins, or earned with stickers or by walking to school (never sold).</summary>
    public enum CosmeticUnlock
    {
        Coins,
        /// <summary>Finding every sticker in one chapter (unlockValue = the chapter).</summary>
        StickerSet,
        /// <summary>Finding a number of stickers in all (unlockValue = how many).</summary>
        StickerCount,
        /// <summary>Walking a number of the routes all the way to school (unlockValue = how many; 6 is every way: Cosmetics/RouteRewards).</summary>
        SchoolRoutes,
    }

    /// <summary>One cosmetic: ball skin, backpack flag, outfit, trail or bag. Visuals are drawn from these values.</summary>
    [CreateAssetMenu(menuName = "Kick Off/Cosmetic Item", fileName = "Cosmetic")]
    public class CosmeticItem : ScriptableObject
    {
        public string id = "ball_classic";
        public string displayName = "Classic";
        public CosmeticCategory category;
        public Rarity rarity;
        [Tooltip("Coin price. 0 = free / owned from the start.")]
        public int price;
        [Tooltip("Coins, or a reward the Locker Room never sells (stickers: StickerRewards; routes walked to school: RouteRewards).")]
        public CosmeticUnlock unlock = CosmeticUnlock.Coins;
        [Tooltip("StickerSet: the chapter whose stickers must all be found. StickerCount: how many stickers. SchoolRoutes: how many routes walked to school.")]
        public int unlockValue;
        public CosmeticPattern pattern;
        public Color primary = Color.white;
        public Color secondary = Color.black;
        public Color accent = Color.gray;

        /// <summary>Earned rather than bought (with stickers or by walking to school): the Locker Room never sells it.</summary>
        public bool IsReward { get { return unlock != CosmeticUnlock.Coins; } }

        /// <summary>Earned with stickers.</summary>
        public bool IsStickerReward { get { return unlock == CosmeticUnlock.StickerSet || unlock == CosmeticUnlock.StickerCount; } }

        /// <summary>Earned by walking routes all the way to school.</summary>
        public bool IsRouteReward { get { return unlock == CosmeticUnlock.SchoolRoutes; } }
    }
}
