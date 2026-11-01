using DribbleToSchool.Cosmetics;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// A sticker up close, opened by tapping it in the album. Found: the big sticker tilting
    /// gently in the light (holo and gold ones shimmer), its rarity, name and a line about it,
    /// where it was found, and what it counts toward (the chapter's set and the next collector
    /// reward). Not found yet: its silhouette, a hint about where it hides in the level, and
    /// Play this level when the level is open.
    /// </summary>
    public static class StickerDetail
    {
        public static GameObject Open(Transform canvas, LevelCatalog levels, CosmeticCatalog cosmetics, LevelDefinition level, System.Action<LevelDefinition> play)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Sticker", new Vector2(1260f, 860f), out root);
            string id = level.levelId;
            bool found = SaveSystem.HasSticker(id);
            var chapter = levels.Chapter(level.chapter);
            Color chapterColor = chapter != null ? chapter.color : UITheme.Accent;
            var rarity = StickerBook.Rarity(id);
            UIKit.Header(card.transform, Loc.T("album.title"), 560f);

            // Left: the sticker, held up to the light.
            var holder = UIKit.Rect(card.transform, "Holder");
            UIKit.Place(holder, new Vector2(0f, 0.5f), new Vector2(330f, 10f), new Vector2(520f, 520f), new Vector2(0.5f, 0.5f));
            if (found)
            {
                var glow = UIKit.Icon(holder, "Glow", ProceduralSprites.SoftDisc, new Color(chapterColor.r, chapterColor.g, chapterColor.b, 0.35f), 640f);
                UIKit.Place(glow.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(640f, 640f));
            }
            var sticker = StickerView.Build(holder, id, chapterColor, found, 500f);
            UIKit.Place(sticker, new Vector2(0.5f, 0.5f), Vector2.zero, sticker.sizeDelta);
            if (found) sticker.gameObject.AddComponent<UIWobble>();
            UIKit.PopIn(holder.gameObject, 0.05f).fromScale = 0.4f;

            // Right: about it.
            var info = UIKit.Rect(card.transform, "Info");
            info.anchorMin = new Vector2(0f, 0f);
            info.anchorMax = new Vector2(1f, 1f);
            info.offsetMin = new Vector2(640f, 170f);
            info.offsetMax = new Vector2(-60f, -90f);
            float y = 0f;

            // Rarity chip and number.
            var chipRow = UIKit.Row(info, "Chips", y, 52f);
            Chip(chipRow, 0f, 200f, found ? StickerBook.RarityName(rarity) : Loc.T("album.notFound"), found ? StickerBook.RarityColor(rarity) : UITheme.Locked);
            Chip(chipRow, 214f, 150f, "#" + StickerNumber(levels, level), UITheme.Navy);
            y += 70f;

            var name = UIKit.Label(UIKit.Row(info, "NameRow", y, 80f), "Name", found ? StickerBook.Name(id) : Loc.T("album.missing"), 60, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Stretch(name.rectTransform);
            UIKit.Fit(name, 38);
            y += 90f;

            var body = UIKit.Label(UIKit.Row(info, "TextRow", y, 128f), "Text", found ? StickerBook.Flavour(id) : Loc.T("album.hintTitle") + "\n" + StickerBook.Hint(id),
                32, found ? UITheme.Ink : UITheme.Navy, TextAnchor.UpperLeft);
            UIKit.Stretch(body.rectTransform);
            UIKit.Fit(body, 22);
            y += 140f;

            // Where it's from.
            string levelName = Loc.T("level." + id, level.displayName);
            string chapterName = Loc.T("chapter." + level.chapter, chapter != null ? chapter.title : "");
            var from = UIKit.Label(UIKit.Row(info, "FromRow", y, 84f), "From",
                Loc.F("album.inLevel", StickerNumber(levels, level), levelName) + "\n" + Loc.F("menu.chapter", level.chapter, chapterName),
                30, UITheme.InkSoft, TextAnchor.UpperLeft, true);
            UIKit.Stretch(from.rectTransform);
            UIKit.Fit(from, 22);
            y += 96f;

            // What it counts toward: the chapter's set and the next collector reward.
            var counts = UIKit.Row(info, "Counts", y, 96f);
            var countsCard = UIKit.Card(counts, "Card", new Color(UITheme.SkyBottom.r, UITheme.SkyBottom.g, UITheme.SkyBottom.b, 0.35f));
            UIKit.Stretch((RectTransform)countsCard.transform.parent);
            int total;
            int got = StickerRewards.FoundInChapter(levels, level.chapter, out total);
            var setItem = StickerRewards.ForChapter(cosmetics, level.chapter);
            string setLine = Loc.F("album.towardSet", chapterName, got, total) + (setItem != null ? "  >  " + setItem.displayName : "");
            string nextLine = NextMilestoneLine(levels, cosmetics);
            var countsText = UIKit.Label(countsCard.transform, "Text", setLine + (nextLine.Length > 0 ? "\n" + nextLine : ""), 27, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Stretch(countsText.rectTransform);
            countsText.rectTransform.offsetMin = new Vector2(96f, 6f);
            countsText.rectTransform.offsetMax = new Vector2(-16f, -6f);
            UIKit.Fit(countsText, 18);
            if (setItem != null)
            {
                var icon = UIKit.Icon(countsCard.transform, "Reward", CosmeticArt.Icon(setItem), Color.white, 70f);
                UIKit.Place(icon.rectTransform, new Vector2(0f, 0.5f), new Vector2(14f, 0f), new Vector2(70f, 70f), new Vector2(0f, 0.5f));
            }

            // Buttons.
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () => Object.Destroy(root), 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(1f, 0f), new Vector2(-60f, 46f), new Vector2(300f, 100f), new Vector2(1f, 0f));
            if (!found)
            {
                bool open = LevelUnlocks.IsUnlocked(levels, level);
                if (open && play != null)
                {
                    var go = UIKit.Button(card.transform, "Play", Loc.T("album.play"), UITheme.Accent, () => { Object.Destroy(root); play(level); }, 40);
                    UIKit.Place((RectTransform)go.transform, new Vector2(1f, 0f), new Vector2(-380f, 46f), new Vector2(380f, 100f), new Vector2(1f, 0f));
                    go.gameObject.AddComponent<UIPulse>().amount = 0.025f;
                }
                else if (!open)
                {
                    var locked = UIKit.Label(card.transform, "Locked", Loc.T("album.levelLocked"), 30, UITheme.InkSoft, TextAnchor.MiddleRight, true);
                    UIKit.Place(locked.rectTransform, new Vector2(1f, 0f), new Vector2(-380f, 96f), new Vector2(420f, 60f), new Vector2(1f, 0.5f));
                }
            }
            return root;
        }

        static void Chip(RectTransform row, float x, float width, string text, Color color)
        {
            var chip = UIKit.Panel(row, "Chip", color, ProceduralSprites.RoundedEdgeSmall);
            chip.rectTransform.anchorMin = new Vector2(0f, 0f);
            chip.rectTransform.anchorMax = new Vector2(0f, 1f);
            chip.rectTransform.pivot = new Vector2(0f, 0.5f);
            chip.rectTransform.sizeDelta = new Vector2(width, 0f);
            chip.rectTransform.anchoredPosition = new Vector2(x, 0f);
            chip.gameObject.AddComponent<UISkew>().skew = 0.2f;
            var label = UIKit.Label(chip.transform, "Text", text.ToUpperInvariant(), 28, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(label.rectTransform, 6f);
            UIKit.Fit(label, 18);
        }

        /// <summary>The sticker's number in the album: the story level's number (L03 is 3).</summary>
        public static int StickerNumber(LevelCatalog levels, LevelDefinition level)
        {
            int n = 0;
            foreach (var l in levels.levels)
            {
                if (l == null || l.isChallenge) continue;
                n++;
                if (l == level) return n;
            }
            return n;
        }

        /// <summary>"Next reward at 20 stickers: Holo Streak", or nothing once the album is complete.</summary>
        public static string NextMilestoneLine(LevelCatalog levels, CosmeticCatalog cosmetics)
        {
            int found = StickerRewards.Found(levels);
            foreach (int count in StickerRewards.Milestones(cosmetics))
            {
                if (count <= found) continue;
                var items = StickerRewards.ForCount(cosmetics, count);
                string names = "";
                foreach (var item in items) names += (names.Length > 0 ? " + " : "") + item.displayName;
                return Loc.F("album.nextReward", count, names);
            }
            return "";
        }
    }
}
