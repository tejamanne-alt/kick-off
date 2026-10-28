using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>Storybook palette and type sizes shared by every screen.</summary>
    public static class UITheme
    {
        public static readonly Color Paper = new Color(0.99f, 0.96f, 0.89f);
        public static readonly Color PaperDark = new Color(0.93f, 0.87f, 0.76f);
        public static readonly Color Ink = new Color(0.22f, 0.17f, 0.15f);
        public static readonly Color InkSoft = new Color(0.22f, 0.17f, 0.15f, 0.6f);
        public static readonly Color Accent = new Color(0.97f, 0.55f, 0.27f);
        public static readonly Color Green = new Color(0.42f, 0.75f, 0.45f);
        public static readonly Color Blue = new Color(0.36f, 0.6f, 0.9f);
        public static readonly Color Red = new Color(0.9f, 0.4f, 0.38f);
        public static readonly Color Gold = new Color(1f, 0.8f, 0.26f);
        public static readonly Color Locked = new Color(0.7f, 0.68f, 0.66f);
        public static readonly Color Shadow = new Color(0.25f, 0.15f, 0.1f, 0.25f);
        public static readonly Color Dim = new Color(0.1f, 0.08f, 0.12f, 0.55f);
        public static readonly Color SkyTop = new Color(0.15f, 0.36f, 0.78f);
        public static readonly Color SkyBottom = new Color(0.55f, 0.76f, 0.95f);

        public static readonly Color Common = new Color(0.6f, 0.75f, 0.6f);
        public static readonly Color Rare = new Color(0.4f, 0.6f, 0.95f);
        public static readonly Color Epic = new Color(0.8f, 0.45f, 0.9f);

        public const int SizeSmall = 30;
        public const int SizeBody = 38;
        public const int SizeButton = 44;
        public const int SizeTitle = 72;
        public const int SizeHero = 120;

        static Font font;

        public static Font Font
        {
            get
            {
                if (font == null) font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                return font;
            }
        }

        public static Color RarityColor(Cosmetics.Rarity rarity)
        {
            switch (rarity)
            {
                case Cosmetics.Rarity.Rare: return Rare;
                case Cosmetics.Rarity.Epic: return Epic;
                default: return Common;
            }
        }
    }
}
