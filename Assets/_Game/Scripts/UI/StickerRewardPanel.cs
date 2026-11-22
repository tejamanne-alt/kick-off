using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The celebration when stickers earn something: each new Locker Room item pops in on a card
    /// with what earned it ("Beach set complete", "10 stickers found"), over a burst of light.
    /// Shown once, the first time the menu finds the reward (StickerRewards.GrantEarned).
    /// </summary>
    public static class StickerRewardPanel
    {
        public static GameObject Open(Transform canvas, List<CosmeticItem> items, System.Action openLocker)
        {
            GameObject root;
            // An old save can earn many at once: up to six to a row, scaled down to fit the screen.
            int n = Mathf.Max(1, items.Count);
            int perRow = Mathf.Min(n, n > 8 ? 6 : 4);
            int rows = (n + perRow - 1) / perRow;
            float cardW = 250f, cardH = 300f, gap = 26f;
            float gridW = perRow * cardW + (perRow - 1) * gap, gridH = rows * cardH + (rows - 1) * gap;
            var size = new Vector2(Mathf.Clamp(gridW + 120f, 820f, 1380f), Mathf.Min(360f + gridH, 1000f));
            float fit = Mathf.Min(1f, Mathf.Min((size.x - 80f) / gridW, (size.y - 360f) / gridH));
            var card = UIKit.Modal(canvas, "StickerReward", size, out root);
            UIKit.Header(card.transform, Loc.T("reward.title"), 620f);

            var line = UIKit.Label(card.transform, "Line", Loc.T("reward.body"), 32, UITheme.InkSoft, TextAnchor.MiddleCenter);
            UIKit.Place(line.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -112f), new Vector2(760f, 50f));
            UIKit.Fit(line, 22);

            var grid = UIKit.Rect(card.transform, "Items");
            UIKit.Place(grid, new Vector2(0.5f, 1f), new Vector2(0f, -160f), new Vector2(gridW, gridH), new Vector2(0.5f, 1f));
            grid.localScale = Vector3.one * fit;
            for (int i = 0; i < items.Count; i++)
            {
                var item = items[i];
                int r = i / perRow, c = i % perRow;
                int inRow = Mathf.Min(perRow, items.Count - r * perRow);
                float rowW = inRow * cardW + (inRow - 1) * gap;
                float x = (gridW - rowW) * 0.5f + c * (cardW + gap);
                var face = UIKit.Card(grid, "Item_" + item.id, UITheme.Paper);
                var holder = (RectTransform)face.transform.parent;
                UIKit.Place(holder, new Vector2(0f, 1f), new Vector2(x, -r * (cardH + gap)), new Vector2(cardW, cardH), new Vector2(0f, 1f));
                UIKit.PopIn(holder.gameObject, 0.2f + i * 0.12f).fromScale = 0.3f;

                var burst = UIKit.Icon(face.transform, "Glow", ProceduralSprites.SoftDisc, new Color(1f, 0.85f, 0.35f, 0.6f), 230f);
                UIKit.Place(burst.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -100f), new Vector2(230f, 230f), new Vector2(0.5f, 0.5f));
                burst.gameObject.AddComponent<UIPulse>().amount = 0.08f;
                var icon = UIKit.Icon(face.transform, "Icon", CosmeticArt.Icon(item), Color.white, 140f);
                UIKit.Place(icon.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -100f), new Vector2(140f, 140f), new Vector2(0.5f, 0.5f));   // (centred 100 down)
                var name = UIKit.Label(face.transform, "Name", item.displayName, 32, UITheme.Ink, TextAnchor.MiddleCenter, true);
                UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 96f), new Vector2(cardW - 24f, 44f), new Vector2(0.5f, 0.5f));
                UIKit.Fit(name, 22);
                var why = UIKit.Label(face.transform, "Why", Reason(item), 24, UITheme.InkSoft, TextAnchor.MiddleCenter, true);
                UIKit.Place(why.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 42f), new Vector2(cardW - 24f, 52f), new Vector2(0.5f, 0.5f));
                UIKit.Fit(why, 16);
            }

            var great = UIKit.Button(card.transform, "Great", Loc.T("reward.great"), UITheme.Green, () => Object.Destroy(root), 42);
            UIKit.Place((RectTransform)great.transform, new Vector2(0.5f, 0f), new Vector2(openLocker != null ? 190f : 0f, 48f), new Vector2(330f, 100f), new Vector2(0.5f, 0f));
            if (openLocker != null)
            {
                var locker = UIKit.Button(card.transform, "Locker", Loc.T("menu.locker"), UITheme.Blue, () => { Object.Destroy(root); openLocker(); }, 38);
                UIKit.Place((RectTransform)locker.transform, new Vector2(0.5f, 0f), new Vector2(-190f, 48f), new Vector2(330f, 100f), new Vector2(0.5f, 0f));
            }
            GameEvents.Raise(GameEventType.Purchase, Vector2.zero);   // the shop's happy chime
            return root;
        }

        /// <summary>What earned an item: "Beach set complete" or "15 stickers found".</summary>
        public static string Reason(CosmeticItem item)
        {
            if (item.unlock == CosmeticUnlock.StickerSet)
                return Loc.F("reward.set", Loc.T("chapter." + item.unlockValue));
            return Loc.F("reward.count", item.unlockValue);
        }
    }
}
