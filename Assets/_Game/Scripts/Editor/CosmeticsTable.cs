using DribbleToSchool.Cosmetics;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The shop's contents. Edit here and rebuild; assets are regenerated from
    /// this table. Ids must stay stable once players own them.
    /// </summary>
    public static class CosmeticsTable
    {
        public struct Row
        {
            public string id, name;
            public CosmeticCategory category;
            public Rarity rarity;
            public int price;
            public CosmeticPattern pattern;
            public Color primary, secondary, accent;
        }

        static Row R(string id, string name, CosmeticCategory cat, Rarity rarity, int price, CosmeticPattern pattern,
            Color primary, Color secondary, Color accent)
        {
            return new Row { id = id, name = name, category = cat, rarity = rarity, price = price, pattern = pattern,
                primary = primary, secondary = secondary, accent = accent };
        }

        static Color C(float r, float g, float b) { return new Color(r, g, b); }

        const CosmeticCategory Ball = CosmeticCategory.Ball;
        const CosmeticCategory Flag = CosmeticCategory.Flag;
        const CosmeticCategory Outfit = CosmeticCategory.Outfit;
        const CosmeticCategory Trail = CosmeticCategory.Trail;
        const Rarity Common = Rarity.Common;
        const Rarity Rare = Rarity.Rare;
        const Rarity Epic = Rarity.Epic;

        public static Row[] Rows()
        {
            Color white = C(0.97f, 0.97f, 0.95f), ink = C(0.15f, 0.13f, 0.13f);
            return new[]
            {
                // ---------- Balls ----------
                R("ball_classic", "Classic", Ball, Common, 0, CosmeticPattern.Classic, white, ink, ink),
                R("ball_retro", "Retro Leather", Ball, Common, 80, CosmeticPattern.Retro, C(0.68f, 0.44f, 0.26f), C(0.4f, 0.24f, 0.13f), ink),
                R("ball_beach", "Beach Ball", Ball, Common, 100, CosmeticPattern.Stripes, C(1f, 0.85f, 0.3f), C(0.3f, 0.6f, 0.95f), white),
                R("ball_polka", "Polka", Ball, Common, 120, CosmeticPattern.Dots, C(0.9f, 0.3f, 0.3f), white, ink),
                R("ball_bullseye", "Bullseye", Ball, Common, 150, CosmeticPattern.Rings, C(0.95f, 0.35f, 0.3f), white, ink),
                R("ball_candy", "Candy Stripe", Ball, Rare, 220, CosmeticPattern.Diagonal, C(1f, 0.6f, 0.75f), white, ink),
                R("ball_orange", "Orange", Ball, Rare, 220, CosmeticPattern.Fruit, C(1f, 0.6f, 0.15f), C(0.85f, 0.4f, 0.05f), C(0.35f, 0.7f, 0.3f)),
                R("ball_melon", "Melon", Ball, Rare, 240, CosmeticPattern.Stripes, C(0.45f, 0.78f, 0.38f), C(0.2f, 0.5f, 0.22f), white),
                R("ball_star", "Lucky Star", Ball, Rare, 280, CosmeticPattern.Star, C(0.2f, 0.25f, 0.5f), C(1f, 0.82f, 0.25f), white),
                R("ball_saturn", "Saturn", Ball, Epic, 420, CosmeticPattern.Planet, C(0.9f, 0.75f, 0.5f), C(0.7f, 0.5f, 0.3f), C(1f, 0.95f, 0.8f)),
                R("ball_earth", "Blue Planet", Ball, Epic, 480, CosmeticPattern.Planet, C(0.3f, 0.55f, 0.9f), C(0.35f, 0.7f, 0.4f), white),
                R("ball_neon", "Neon Night", Ball, Epic, 520, CosmeticPattern.Neon, C(0.12f, 0.12f, 0.25f), C(0.2f, 1f, 0.95f), C(1f, 0.3f, 0.85f)),
                R("ball_gold", "Golden Boot", Ball, Epic, 900, CosmeticPattern.Classic, C(1f, 0.82f, 0.3f), C(0.6f, 0.4f, 0.1f), ink),

                // ---------- Backpack flags ----------
                R("flag_none", "No Flag", Flag, Common, 0, CosmeticPattern.None, white, white, white),
                R("flag_france", "France", Flag, Common, 60, CosmeticPattern.VerticalTri, C(0.15f, 0.3f, 0.65f), white, C(0.85f, 0.2f, 0.2f)),
                R("flag_italy", "Italy", Flag, Common, 60, CosmeticPattern.VerticalTri, C(0.1f, 0.55f, 0.3f), white, C(0.8f, 0.2f, 0.2f)),
                R("flag_ireland", "Ireland", Flag, Common, 60, CosmeticPattern.VerticalTri, C(0.1f, 0.6f, 0.35f), white, C(1f, 0.55f, 0.2f)),
                R("flag_nigeria", "Nigeria", Flag, Common, 60, CosmeticPattern.VerticalTri, C(0f, 0.53f, 0.32f), white, C(0f, 0.53f, 0.32f)),
                R("flag_germany", "Germany", Flag, Common, 60, CosmeticPattern.HorizontalTri, ink, C(0.85f, 0.1f, 0.1f), C(1f, 0.8f, 0f)),
                R("flag_netherlands", "Netherlands", Flag, Common, 60, CosmeticPattern.HorizontalTri, C(0.7f, 0.1f, 0.15f), white, C(0.1f, 0.25f, 0.55f)),
                R("flag_ukraine", "Ukraine", Flag, Common, 60, CosmeticPattern.HorizontalBi, C(0f, 0.35f, 0.75f), C(1f, 0.84f, 0f), white),
                R("flag_japan", "Japan", Flag, Common, 80, CosmeticPattern.CenterDot, white, C(0.75f, 0.0f, 0.16f), white),
                R("flag_sweden", "Sweden", Flag, Common, 80, CosmeticPattern.NordicCross, C(0f, 0.42f, 0.66f), C(1f, 0.8f, 0f), white),
                R("flag_india", "India", Flag, Common, 80, CosmeticPattern.BandsWithDot, C(1f, 0.6f, 0.2f), white, C(0.07f, 0.53f, 0.03f)),
                R("flag_sunset", "Sunset Banner", Flag, Rare, 150, CosmeticPattern.Stripes, C(1f, 0.55f, 0.3f), C(1f, 0.75f, 0.8f), white),
                R("flag_stars", "Star Banner", Flag, Rare, 150, CosmeticPattern.Star, C(0.15f, 0.2f, 0.45f), C(1f, 0.82f, 0.25f), white),

                // ---------- Outfits (shirt, shorts, collar/accent) ----------
                R("outfit_school", "School Uniform", Outfit, Common, 0, CosmeticPattern.Solid, C(0.97f, 0.97f, 0.99f), C(0.22f, 0.23f, 0.42f), C(0.78f, 0.2f, 0.24f)),
                R("outfit_red", "Red Kit", Outfit, Common, 120, CosmeticPattern.Solid, C(0.88f, 0.25f, 0.25f), white, white),
                R("outfit_blue", "Blue Kit", Outfit, Common, 120, CosmeticPattern.Solid, C(0.2f, 0.4f, 0.85f), white, white),
                R("outfit_hoops", "Green Hoops", Outfit, Common, 180, CosmeticPattern.Stripes, C(0.25f, 0.65f, 0.35f), ink, white),
                R("outfit_raincoat", "Yellow Raincoat", Outfit, Common, 160, CosmeticPattern.Solid, C(1f, 0.85f, 0.25f), C(0.2f, 0.3f, 0.55f), C(1f, 0.95f, 0.6f)),
                R("outfit_hoodie", "Cosy Hoodie", Outfit, Common, 140, CosmeticPattern.Solid, C(0.6f, 0.62f, 0.66f), C(0.25f, 0.27f, 0.32f), white),
                R("outfit_orange", "Orange Pop", Outfit, Rare, 240, CosmeticPattern.Stripes, C(1f, 0.55f, 0.2f), white, white),
                R("outfit_royal", "Royal Purple", Outfit, Rare, 320, CosmeticPattern.Solid, C(0.5f, 0.3f, 0.75f), C(1f, 0.8f, 0.3f), C(1f, 0.8f, 0.3f)),
                R("outfit_gold", "Champion Gold", Outfit, Epic, 700, CosmeticPattern.Solid, C(1f, 0.8f, 0.3f), white, white),

                // ---------- Ball trails ----------
                R("trail_none", "No Trail", Trail, Common, 0, CosmeticPattern.None, white, white, white),
                R("trail_sunshine", "Sunshine", Trail, Common, 120, CosmeticPattern.Gradient, C(1f, 0.95f, 0.4f), C(1f, 0.6f, 0.2f), white),
                R("trail_ocean", "Ocean", Trail, Common, 120, CosmeticPattern.Gradient, C(0.4f, 0.95f, 1f), C(0.2f, 0.4f, 0.95f), white),
                R("trail_mint", "Mint", Trail, Common, 120, CosmeticPattern.Gradient, C(0.6f, 1f, 0.8f), white, white),
                R("trail_fire", "Fireball", Trail, Rare, 260, CosmeticPattern.Gradient, C(1f, 0.9f, 0.3f), C(0.95f, 0.2f, 0.1f), white),
                R("trail_bubblegum", "Bubblegum", Trail, Rare, 260, CosmeticPattern.Gradient, C(1f, 0.6f, 0.85f), C(0.6f, 0.4f, 0.95f), white),
                R("trail_rainbow", "Rainbow", Trail, Epic, 650, CosmeticPattern.Rainbow, white, white, white),
            };
        }
    }
}
