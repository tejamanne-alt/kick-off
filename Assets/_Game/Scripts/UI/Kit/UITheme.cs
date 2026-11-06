using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Palette and type sizes shared by every screen, in the game's clear anime daylight
    /// (docs/ART_DIRECTION.md): clean, slightly see-through white panels with a thin dark line,
    /// the school uniform's navy for headings, the sky's cobalt, pitch green, and one warm orange
    /// for the main action, the way the kid pops out of the street.
    /// </summary>
    public static class UITheme
    {
        /// <summary>Panel and card faces: white, a touch see-through over the 3D street.</summary>
        public static readonly Color Paper = new Color(0.985f, 0.99f, 1f, 0.95f);
        /// <summary>Modal panels: the same white, only just see-through, so busy screens behind don't show.</summary>
        public static readonly Color Panel = new Color(0.985f, 0.99f, 1f, 0.975f);
        public static readonly Color PaperDark = new Color(0.86f, 0.89f, 0.94f);
        /// <summary>Text and line art: the characters' near-black ink, leaning navy.</summary>
        public static readonly Color Ink = new Color(0.11f, 0.13f, 0.2f);
        public static readonly Color InkSoft = new Color(0.11f, 0.13f, 0.2f, 0.62f);
        /// <summary>The school uniform's navy: headings, ribbons, selected tabs.</summary>
        public static readonly Color Navy = new Color(0.14f, 0.2f, 0.4f);
        public static readonly Color Accent = new Color(0.98f, 0.54f, 0.18f);
        public static readonly Color Green = new Color(0.27f, 0.7f, 0.42f);
        public static readonly Color Blue = new Color(0.2f, 0.47f, 0.86f);
        public static readonly Color Red = new Color(0.9f, 0.34f, 0.34f);
        public static readonly Color Gold = new Color(1f, 0.8f, 0.2f);
        public static readonly Color Locked = new Color(0.68f, 0.71f, 0.77f);
        public static readonly Color Shadow = new Color(0.05f, 0.09f, 0.24f, 0.26f);
        public static readonly Color Dim = new Color(0.04f, 0.07f, 0.18f, 0.5f);
        /// <summary>The game's sky as it shows on screen: the deep cobalt overhead, and a lighter blue
        /// for the bottom of the menus' sky (paler than the in-game horizon, so panels and text on it read).</summary>
        public static readonly Color SkyTop = new Color(0.22f, 0.43f, 0.69f);
        public static readonly Color SkyBottom = new Color(0.47f, 0.67f, 0.88f);
        /// <summary>Chalk white of the pitch lines and the logo's face.</summary>
        public static readonly Color Chalk = new Color(1f, 1f, 0.98f);

        public static readonly Color Common = new Color(0.45f, 0.7f, 0.5f);
        public static readonly Color Rare = new Color(0.3f, 0.55f, 0.95f);
        public static readonly Color Epic = new Color(0.72f, 0.4f, 0.9f);

        public const int SizeSmall = 30;
        public const int SizeBody = 38;
        public const int SizeButton = 44;
        public const int SizeTitle = 72;
        public const int SizeHero = 120;

        static Font font, display;

        /// <summary>Body text: Varela Round, a soft rounded sans (SIL OFL, Resources/Fonts).</summary>
        public static Font Font
        {
            get
            {
                if (font == null) font = Load("Fonts/VarelaRound-Regular");
                return font;
            }
        }

        /// <summary>Titles, buttons and numbers: Lilita One, a chunky rounded display face (SIL OFL).</summary>
        public static Font Display
        {
            get
            {
                if (display == null) display = Load("Fonts/LilitaOne-Regular");
                return display;
            }
        }

        static Font Load(string path)
        {
            var f = Resources.Load<Font>(path);
            return f != null ? f : Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
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
