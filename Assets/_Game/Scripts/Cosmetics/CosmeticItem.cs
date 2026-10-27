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
    }

    public enum Rarity { Common, Rare, Epic }

    /// <summary>One cosmetic: ball skin, backpack flag, outfit or trail. Visuals are drawn from these values.</summary>
    [CreateAssetMenu(menuName = "Dribble To School/Cosmetic Item", fileName = "Cosmetic")]
    public class CosmeticItem : ScriptableObject
    {
        public string id = "ball_classic";
        public string displayName = "Classic";
        public CosmeticCategory category;
        public Rarity rarity;
        [Tooltip("Coin price. 0 = free / owned from the start.")]
        public int price;
        public CosmeticPattern pattern;
        public Color primary = Color.white;
        public Color secondary = Color.black;
        public Color accent = Color.gray;
    }
}
