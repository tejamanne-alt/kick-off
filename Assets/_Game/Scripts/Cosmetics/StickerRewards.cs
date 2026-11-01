using System.Collections.Generic;
using DribbleToSchool.Levels;
using DribbleToSchool.Progression;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>
    /// What stickers are worth: Locker Room items coins can't buy. Finding every sticker in a
    /// chapter unlocks that chapter's set reward; finding 5, 10, 15, 20 and all 23 unlocks the
    /// collector rewards (CosmeticItem.unlock / unlockValue, set in Editor/CosmeticsTable).
    /// Rewards are worked out from the stickers in the save, so an old save gets everything its
    /// stickers have earned the first time the menu checks (and nothing extra is stored).
    /// </summary>
    public static class StickerRewards
    {
        /// <summary>Stickers come from story levels (one each); challenges have none.</summary>
        public static int Total(LevelCatalog levels)
        {
            int n = 0;
            if (levels == null) return 0;
            foreach (var l in levels.levels) if (l != null && !l.isChallenge) n++;
            return n;
        }

        public static int Found(LevelCatalog levels)
        {
            int n = 0;
            if (levels == null) return 0;
            foreach (var l in levels.levels)
                if (l != null && !l.isChallenge && SaveSystem.HasSticker(l.levelId)) n++;
            return n;
        }

        /// <summary>Stickers found in one chapter, and how many it has.</summary>
        public static int FoundInChapter(LevelCatalog levels, int chapter, out int total)
        {
            int n = 0;
            total = 0;
            if (levels == null) return 0;
            foreach (var l in levels.LevelsInChapter(chapter))
            {
                if (l.isChallenge) continue;
                total++;
                if (SaveSystem.HasSticker(l.levelId)) n++;
            }
            return n;
        }

        /// <summary>Have the stickers earned this item?</summary>
        public static bool IsEarned(CosmeticItem item, LevelCatalog levels)
        {
            if (item == null || !item.IsStickerReward) return false;
            if (item.unlock == CosmeticUnlock.StickerCount) return Found(levels) >= item.unlockValue;
            int total;
            int found = FoundInChapter(levels, item.unlockValue, out total);
            return total > 0 && found >= total;
        }

        /// <summary>How many more stickers this item needs (0 once earned).</summary>
        public static int StillNeeded(CosmeticItem item, LevelCatalog levels)
        {
            if (item == null || !item.IsStickerReward) return 0;
            if (item.unlock == CosmeticUnlock.StickerCount) return System.Math.Max(0, item.unlockValue - Found(levels));
            int total;
            int found = FoundInChapter(levels, item.unlockValue, out total);
            return System.Math.Max(0, total - found);
        }

        /// <summary>Every sticker reward, by count rewards in count order then set rewards by chapter.</summary>
        public static List<CosmeticItem> All(CosmeticCatalog cosmetics)
        {
            var list = new List<CosmeticItem>();
            if (cosmetics == null) return list;
            foreach (var item in cosmetics.items) if (item != null && item.IsStickerReward) list.Add(item);
            list.Sort((a, b) => a.unlock != b.unlock ? b.unlock.CompareTo(a.unlock) : a.unlockValue.CompareTo(b.unlockValue));
            return list;
        }

        /// <summary>The set reward for a chapter, or null.</summary>
        public static CosmeticItem ForChapter(CosmeticCatalog cosmetics, int chapter)
        {
            if (cosmetics == null) return null;
            foreach (var item in cosmetics.items)
                if (item != null && item.unlock == CosmeticUnlock.StickerSet && item.unlockValue == chapter) return item;
            return null;
        }

        /// <summary>The collector rewards for one sticker count (the full album gives two).</summary>
        public static List<CosmeticItem> ForCount(CosmeticCatalog cosmetics, int count)
        {
            var list = new List<CosmeticItem>();
            if (cosmetics == null) return list;
            foreach (var item in cosmetics.items)
                if (item != null && item.unlock == CosmeticUnlock.StickerCount && item.unlockValue == count) list.Add(item);
            return list;
        }

        /// <summary>The sticker counts that unlock something, in order (5, 10, 15, 20, 23).</summary>
        public static List<int> Milestones(CosmeticCatalog cosmetics)
        {
            var counts = new List<int>();
            if (cosmetics == null) return counts;
            foreach (var item in cosmetics.items)
                if (item != null && item.unlock == CosmeticUnlock.StickerCount && !counts.Contains(item.unlockValue)) counts.Add(item.unlockValue);
            counts.Sort();
            return counts;
        }

        /// <summary>Earned but not yet in the save: what the next <see cref="GrantEarned"/> will hand out.</summary>
        public static List<CosmeticItem> Pending(LevelCatalog levels, CosmeticCatalog cosmetics)
        {
            var list = new List<CosmeticItem>();
            foreach (var item in All(cosmetics))
                if (!SaveSystem.Owns(item.id) && IsEarned(item, levels)) list.Add(item);
            return list;
        }

        /// <summary>
        /// Give the player every reward their stickers have earned and they don't own yet, save,
        /// and return them (for the celebration). Safe to call any time; returns an empty list
        /// when there's nothing new.
        /// </summary>
        public static List<CosmeticItem> GrantEarned(LevelCatalog levels, CosmeticCatalog cosmetics)
        {
            var granted = Pending(levels, cosmetics);
            if (granted.Count == 0) return granted;
            foreach (var item in granted) SaveSystem.Grant(item.id);
            SaveSystem.Save();
            return granted;
        }
    }
}
