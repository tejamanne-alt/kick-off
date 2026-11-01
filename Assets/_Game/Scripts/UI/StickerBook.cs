using System.Collections.Generic;
using DribbleToSchool.Localization;
using UnityEngine;

namespace DribbleToSchool.UI
{
    public enum StickerRarity { Normal, Holo, Gold }

    /// <summary>
    /// The album's 23 stickers, one per story level, each themed to its level: die-cut vinyl
    /// stickers drawn from the game's own models (tools/blender/sticker_art.py renders them in
    /// the toon look, sticker_compose.py cuts them out: Resources/UI/Stickers/&lt;level&gt;.png).
    /// Most are plain white vinyl, some are holo (rainbow foil, with a moving sheen in the UI)
    /// and each chapter's finale is gold. Names, flavour lines and where-to-look hints are
    /// strings: sticker.&lt;level&gt;, sticker.&lt;level&gt;.text, sticker.&lt;level&gt;.hint.
    /// </summary>
    public static class StickerBook
    {
        /// <summary>Where the art's blank name ribbon is, as a fraction of the sticker (from the bottom left).</summary>
        public static readonly Rect RibbonRect = new Rect(0.15f, 0.117f, 0.70f, 0.117f);

        static readonly Dictionary<string, StickerRarity> rarities = new Dictionary<string, StickerRarity>
        {
            { "L04", StickerRarity.Holo }, { "L08", StickerRarity.Holo }, { "L12", StickerRarity.Holo },
            { "L16", StickerRarity.Holo }, { "L20", StickerRarity.Holo }, { "L22", StickerRarity.Holo },
            { "L05", StickerRarity.Gold }, { "L10", StickerRarity.Gold }, { "L14", StickerRarity.Gold },
            { "L18", StickerRarity.Gold }, { "L23", StickerRarity.Gold },
        };

        static readonly Dictionary<string, Sprite> art = new Dictionary<string, Sprite>();

        public static StickerRarity Rarity(string levelId)
        {
            StickerRarity r;
            return rarities.TryGetValue(levelId, out r) ? r : StickerRarity.Normal;
        }

        /// <summary>True when the drawn sticker (with its name ribbon) exists, rather than the procedural stand-in.</summary>
        public static bool HasArt(string levelId)
        {
            return Load(levelId) != null;
        }

        /// <summary>The level's sticker: the drawn one, or a procedural badge in the chapter's colour if it's missing.</summary>
        public static Sprite Art(string levelId, Color chapterColor)
        {
            var sprite = Load(levelId);
            return sprite != null ? sprite : StickerArt.For(levelId, chapterColor);
        }

        static Sprite Load(string levelId)
        {
            Sprite sprite;
            if (art.TryGetValue(levelId, out sprite)) return sprite;
            string path = "UI/Stickers/" + levelId;
            sprite = Resources.Load<Sprite>(path);
            if (sprite == null)
            {
                var tex = Resources.Load<Texture2D>(path);
                if (tex != null) sprite = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f), 100f);
            }
            art[levelId] = sprite;
            return sprite;
        }

        public static string Name(string levelId) { return Loc.T("sticker." + levelId, levelId); }
        public static string Flavour(string levelId) { return Loc.T("sticker." + levelId + ".text", ""); }
        public static string Hint(string levelId) { return Loc.T("sticker." + levelId + ".hint", Loc.T("album.hint")); }

        public static string RarityName(StickerRarity rarity)
        {
            switch (rarity)
            {
                case StickerRarity.Holo: return Loc.T("sticker.holo");
                case StickerRarity.Gold: return Loc.T("sticker.gold");
                default: return Loc.T("sticker.normal");
            }
        }

        public static Color RarityColor(StickerRarity rarity)
        {
            switch (rarity)
            {
                case StickerRarity.Holo: return new Color(0.55f, 0.45f, 0.95f);
                case StickerRarity.Gold: return new Color(0.92f, 0.66f, 0.12f);
                default: return new Color(0.36f, 0.6f, 0.86f);
            }
        }
    }
}
