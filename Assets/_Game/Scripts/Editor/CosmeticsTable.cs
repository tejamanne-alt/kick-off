using DribbleToSchool.Cosmetics;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The shop's contents. Edit here and rebuild; assets are regenerated from
    /// this table. Ids must stay stable once players own them. Sticker rewards are
    /// never sold: completing a chapter's sticker set or reaching a sticker count
    /// unlocks them (see Cosmetics/StickerRewards); nor are the rewards for walking
    /// routes all the way to school (see Cosmetics/RouteRewards).
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
            public CosmeticUnlock unlock;
            public int unlockValue;
        }

        static Row R(string id, string name, CosmeticCategory cat, Rarity rarity, int price, CosmeticPattern pattern,
            Color primary, Color secondary, Color accent)
        {
            return new Row { id = id, name = name, category = cat, rarity = rarity, price = price, pattern = pattern,
                primary = primary, secondary = secondary, accent = accent };
        }

        /// <summary>A sticker reward: unlocked by a chapter's full set or by a sticker count, not by coins.</summary>
        static Row Sticker(string id, string name, CosmeticCategory cat, Rarity rarity, CosmeticUnlock unlock, int value,
            CosmeticPattern pattern, Color primary, Color secondary, Color accent)
        {
            var row = R(id, name, cat, rarity, 0, pattern, primary, secondary, accent);
            row.unlock = unlock;
            row.unlockValue = value;
            return row;
        }

        /// <summary>A reward for walking routes all the way to school (Cosmetics/RouteRewards): unlocked by how many, not by coins.</summary>
        static Row School(string id, string name, CosmeticCategory cat, Rarity rarity, int routes, CosmeticPattern pattern, Color primary, Color secondary, Color accent)
        {
            var row = R(id, name, cat, rarity, 0, pattern, primary, secondary, accent);
            row.unlock = CosmeticUnlock.SchoolRoutes;
            row.unlockValue = routes;
            return row;
        }

        static Color C(float r, float g, float b) { return new Color(r, g, b); }

        const CosmeticUnlock Set = CosmeticUnlock.StickerSet;
        const CosmeticUnlock Count = CosmeticUnlock.StickerCount;

        const CosmeticCategory Ball = CosmeticCategory.Ball;
        const CosmeticCategory Flag = CosmeticCategory.Flag;
        const CosmeticCategory Outfit = CosmeticCategory.Outfit;
        const CosmeticCategory Trail = CosmeticCategory.Trail;
        const CosmeticCategory Bag = CosmeticCategory.Bag;
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
                Sticker("ball_set_home", "Home Street Hero", Ball, Rare, Set, 1, CosmeticPattern.Classic, C(0.99f, 0.95f, 0.86f), C(0.95f, 0.5f, 0.15f), C(0.16f, 0.2f, 0.4f)),
                Sticker("ball_set_beach", "Surf's Up", Ball, Rare, Set, 3, CosmeticPattern.Diagonal, C(0.2f, 0.75f, 0.8f), C(0.98f, 0.88f, 0.6f), white),
                Sticker("ball_ms_15", "Holo Foil", Ball, Epic, Count, 15, CosmeticPattern.Holo, C(0.85f, 0.95f, 1f), C(1f, 0.85f, 0.95f), white),
                Sticker("ball_ms_23", "Golden Album", Ball, Epic, Count, 23, CosmeticPattern.Foil, C(1f, 0.8f, 0.28f), C(0.75f, 0.48f, 0.08f), white),
                // Every way to school walked: the trophy's ball, gold with the school's navy stars.
                School("ball_top_class", "Top of the Class", Ball, Epic, 6, CosmeticPattern.Star, C(1f, 0.8f, 0.26f), C(0.16f, 0.2f, 0.42f), white),

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
                Sticker("flag_ms_10", "Gold Seal", Flag, Rare, Count, 10, CosmeticPattern.CenterDot, C(0.1f, 0.55f, 0.6f), C(1f, 0.8f, 0.25f), white),
                Sticker("flag_set_site", "Site Safety", Flag, Rare, Set, 4, CosmeticPattern.Stripes, C(1f, 0.8f, 0.1f), ink, white),
                // Three ways to school walked: a gold star on the park's green.
                School("flag_way_finder", "Way Finder", Flag, Rare, 3, CosmeticPattern.Star, C(0.2f, 0.56f, 0.36f), C(1f, 0.82f, 0.25f), white),

                // ---------- Outfits (shirt, shorts, collar/accent) ----------
                R("outfit_school", "School Uniform", Outfit, Common, 0, CosmeticPattern.Solid, C(0.97f, 0.97f, 0.99f), C(0.22f, 0.23f, 0.42f), C(0.78f, 0.2f, 0.24f)),
                // The Holiday Run's own look (see CosmeticApplier.holiday): casual, a bright top and khaki, and no tie (the accent's alpha is 0).
                R("outfit_holiday", "Holiday", Outfit, Common, 0, CosmeticPattern.Solid, C(0.16f, 0.72f, 0.82f), C(0.82f, 0.72f, 0.5f), new Color(1f, 1f, 1f, 0f)),
                R("outfit_red", "Red Kit", Outfit, Common, 120, CosmeticPattern.Solid, C(0.88f, 0.25f, 0.25f), white, white),
                R("outfit_blue", "Blue Kit", Outfit, Common, 120, CosmeticPattern.Solid, C(0.2f, 0.4f, 0.85f), white, white),
                R("outfit_hoops", "Green Hoops", Outfit, Common, 180, CosmeticPattern.Stripes, C(0.25f, 0.65f, 0.35f), ink, white),
                R("outfit_raincoat", "Yellow Raincoat", Outfit, Common, 160, CosmeticPattern.Solid, C(1f, 0.85f, 0.25f), C(0.2f, 0.3f, 0.55f), C(1f, 0.95f, 0.6f)),
                R("outfit_hoodie", "Cosy Hoodie", Outfit, Common, 140, CosmeticPattern.Solid, C(0.6f, 0.62f, 0.66f), C(0.25f, 0.27f, 0.32f), white),
                R("outfit_orange", "Orange Pop", Outfit, Rare, 240, CosmeticPattern.Stripes, C(1f, 0.55f, 0.2f), white, white),
                R("outfit_royal", "Royal Purple", Outfit, Rare, 320, CosmeticPattern.Solid, C(0.5f, 0.3f, 0.75f), C(1f, 0.8f, 0.3f), C(1f, 0.8f, 0.3f)),
                R("outfit_gold", "Champion Gold", Outfit, Epic, 700, CosmeticPattern.Solid, C(1f, 0.8f, 0.3f), white, white),
                Sticker("outfit_set_market", "Market Day", Outfit, Rare, Set, 2, CosmeticPattern.Stripes, C(0.86f, 0.24f, 0.26f), C(0.18f, 0.2f, 0.38f), white),
                Sticker("outfit_set_park", "Cherry Blossom", Outfit, Rare, Set, 5, CosmeticPattern.Solid, C(1f, 0.74f, 0.82f), C(0.3f, 0.55f, 0.32f), white),
                Sticker("outfit_ms_23", "Album Legend", Outfit, Epic, Count, 23, CosmeticPattern.Stripes, C(1f, 0.8f, 0.3f), C(0.16f, 0.2f, 0.4f), white),

                // ---------- Ball trails ----------
                R("trail_none", "No Trail", Trail, Common, 0, CosmeticPattern.None, white, white, white),
                R("trail_sunshine", "Sunshine", Trail, Common, 120, CosmeticPattern.Gradient, C(1f, 0.95f, 0.4f), C(1f, 0.6f, 0.2f), white),
                R("trail_ocean", "Ocean", Trail, Common, 120, CosmeticPattern.Gradient, C(0.4f, 0.95f, 1f), C(0.2f, 0.4f, 0.95f), white),
                R("trail_mint", "Mint", Trail, Common, 120, CosmeticPattern.Gradient, C(0.6f, 1f, 0.8f), white, white),
                R("trail_fire", "Fireball", Trail, Rare, 260, CosmeticPattern.Gradient, C(1f, 0.9f, 0.3f), C(0.95f, 0.2f, 0.1f), white),
                R("trail_bubblegum", "Bubblegum", Trail, Rare, 260, CosmeticPattern.Gradient, C(1f, 0.6f, 0.85f), C(0.6f, 0.4f, 0.95f), white),
                R("trail_rainbow", "Rainbow", Trail, Epic, 650, CosmeticPattern.Rainbow, white, white, white),
                Sticker("trail_ms_5", "Confetti", Trail, Common, Count, 5, CosmeticPattern.Gradient, C(1f, 0.55f, 0.75f), C(1f, 0.85f, 0.3f), white),
                Sticker("trail_ms_20", "Holo Streak", Trail, Epic, Count, 20, CosmeticPattern.Holo, white, white, white),
                // Every way to school walked: gold fading into the school's navy.
                School("trail_victory_lap", "Victory Lap", Trail, Epic, 6, CosmeticPattern.Gradient, C(1f, 0.82f, 0.26f), C(0.2f, 0.3f, 0.72f), white),

                // ---------- Bags (Cosmetics/Bags) ----------
                // Worn by each kid modelled without a bag of their own, as they choose; owned from the start. Each id is
                // "bag_" + the name of the bag's mesh in the kids' models (Bag_KickOff: tools/blender/meshy_bag.py); the
                // colour is chosen in Settings. The icon is the bag's own picture, Resources/UI/Bag<Id>.png.
                R(DribbleToSchool.Cosmetics.Bags.NoneId, "No Bag", Bag, Common, 0, CosmeticPattern.None, white, white, white),
                R(DribbleToSchool.Cosmetics.Bags.DefaultId, "Kick Off Backpack", Bag, Common, 0, CosmeticPattern.Solid, C(0.53f, 0.08f, 0.73f), ink, white),
            };
        }
    }
}
