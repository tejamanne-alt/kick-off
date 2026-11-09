using System.Collections.Generic;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The sticker book, a collector's album on a white page over the sky. At the top, the
    /// collector track: stickers found out of 23, with the rewards at 5, 10, 15, 20 and the full
    /// album. Then a section per chapter: its colour band and progress (3 / 5), the exclusive
    /// item its full set unlocks, and its stickers (found ones in full colour, holo and gold
    /// ones shimmering; missing ones as silhouettes). Tap a sticker to look at it up close.
    /// </summary>
    public class AlbumScreen : FrontEndScreen
    {
        const float ColumnWidth = 1180f;
        const float Slot = 212f;
        const float SlotGap = 30f;

        RectTransform content;
        ScrollRect scroll;

        public override string Title { get { return Loc.T("album.title"); } }

        protected override void Build(RectTransform root)
        {
            var page = UIKit.Card(root, "Page", new Color(1f, 1f, 1f, 0.92f));
            var pageRoot = (RectTransform)page.transform.parent;
            pageRoot.anchorMin = Vector2.zero;
            pageRoot.anchorMax = Vector2.one;
            pageRoot.offsetMin = new Vector2(40f, 40f);
            pageRoot.offsetMax = new Vector2(-40f, -175f);

            content = UIKit.ScrollArea(page.transform, "Book", true, out scroll);
            UIKit.Stretch((RectTransform)scroll.transform, 10f);
        }

        public override void OnShow()
        {
            for (int i = content.childCount - 1; i >= 0; i--) Object.Destroy(content.GetChild(i).gameObject);
            var levels = Controller.levels;
            var cosmetics = Controller.cosmetics;
            if (levels == null) return;

            float y = 24f;
            y = CollectorTrack(levels, cosmetics, y);
            int sheen = 0;
            foreach (var chapter in levels.chapters)
            {
                var stories = levels.LevelsInChapter(chapter.number).FindAll(l => !l.isChallenge);
                if (stories.Count == 0) continue;
                y = ChapterSection(levels, cosmetics, chapter, stories, y, ref sheen);
            }
            content.sizeDelta = new Vector2(0f, y + 30f);
            scroll.verticalNormalizedPosition = 1f;
        }

        /// <summary>A row centred in the book's column, <paramref name="height"/> tall, <paramref name="top"/> down the page.</summary>
        RectTransform Line(string name, float top, float height)
        {
            var rt = UIKit.Rect(content, name);
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.anchoredPosition = new Vector2(0f, -top);
            rt.sizeDelta = new Vector2(ColumnWidth, height);
            return rt;
        }

        // ---------- The collector track ----------

        float CollectorTrack(LevelCatalog levels, CosmeticCatalog cosmetics, float y)
        {
            int found = StickerRewards.Found(levels), total = StickerRewards.Total(levels);
            var head = Line("TrackHead", y, 56f);
            UIKit.SectionLabel(head, Loc.T("album.collector"));
            var count = UIKit.Label(head, "Count", Loc.F("album.count", found, total).ToUpperInvariant(), 40, UITheme.Navy, TextAnchor.MiddleRight, true);
            UIKit.Stretch(count.rectTransform);
            count.rectTransform.offsetMin = new Vector2(500f, 0f);
            UIKit.Fit(count, 26);
            y += 70f;

            // The bar, with a node and the reward above it at each milestone.
            var track = Line("Track", y, 200f);
            // The full album's prize sits at the end of the bar, to its right; the others above it.
            const float barY = 150f, barH = 26f, pad = 40f, end = 250f;
            float barW = ColumnWidth - pad - end;
            var bar = UIKit.Panel(track, "Bar", UITheme.PaperDark, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Place(bar.rectTransform, new Vector2(0f, 1f), new Vector2(pad, -barY), new Vector2(barW, barH), new Vector2(0f, 0.5f));
            float k = total > 0 ? Mathf.Clamp01(found / (float)total) : 0f;
            if (k > 0f)
            {
                var fill = UIKit.Panel(track, "Fill", UITheme.Gold, ProceduralSprites.RoundedEdgeSmall);
                UIKit.Place(fill.rectTransform, new Vector2(0f, 1f), new Vector2(pad, -barY), new Vector2(Mathf.Max(barH, barW * k), barH), new Vector2(0f, 0.5f));
            }
            var milestones = StickerRewards.Milestones(cosmetics);
            int next = -1;
            foreach (int m in milestones) if (m > found) { next = m; break; }
            foreach (int m in milestones)
            {
                float x = pad + barW * Mathf.Clamp01(m / (float)Mathf.Max(1, total));
                bool reached = found >= m;
                var node = UIKit.Icon(track, "Node" + m, ProceduralSprites.CircleEdge, reached ? UITheme.Gold : Color.white, 56f);
                UIKit.Place(node.rectTransform, new Vector2(0f, 1f), new Vector2(x, -barY), new Vector2(56f, 56f), new Vector2(0.5f, 0.5f));
                var num = UIKit.Label(node.transform, "Count", m.ToString(), 26, reached ? Color.white : UITheme.Navy, TextAnchor.MiddleCenter, true);
                UIKit.Stretch(num.rectTransform);
                if (reached)
                {
                    var sh = num.gameObject.AddComponent<Shadow>();
                    sh.effectColor = new Color(0.4f, 0.25f, 0f, 0.6f);
                    sh.effectDistance = new Vector2(0f, -2f);
                }

                // The reward(s), on a little card above the node.
                var items = StickerRewards.ForCount(cosmetics, m);
                float w = 84f * Mathf.Max(1, items.Count) + 12f;
                bool last = m >= total;
                var reward = UIKit.Card(track, "Reward" + m, reached ? new Color(1f, 0.96f, 0.82f) : last ? new Color(1f, 0.93f, 0.7f) : UITheme.Paper);
                var rr = (RectTransform)reward.transform.parent;
                if (last) UIKit.Place(rr, new Vector2(0f, 1f), new Vector2(x + 44f, -barY), new Vector2(w, 96f), new Vector2(0f, 0.5f));
                else UIKit.Place(rr, new Vector2(0f, 1f), new Vector2(Mathf.Max(x, pad + w * 0.5f), -10f), new Vector2(w, 96f), new Vector2(0.5f, 1f));
                for (int i = 0; i < items.Count; i++)
                {
                    var icon = CartoonPicture.On(UIKit.Icon(reward.transform, "Icon", CosmeticArt.Icon(items[i]), reached ? Color.white : new Color(1f, 1f, 1f, 0.55f), 72f));
                    UIKit.Place(icon.rectTransform, new Vector2(0f, 0.5f), new Vector2(10f + i * 84f, 0f), new Vector2(72f, 72f), new Vector2(0f, 0.5f));
                }
                if (reached) Badge(reward.transform, true);
                else if (m == next) rr.gameObject.AddComponent<UIPulse>().amount = 0.04f;
            }
            return y + 210f;
        }

        // ---------- A chapter's section ----------

        float ChapterSection(LevelCatalog levels, CosmeticCatalog cosmetics, ChapterInfo chapter, List<LevelDefinition> stories, float y, ref int sheen)
        {
            int total;
            int got = StickerRewards.FoundInChapter(levels, chapter.number, out total);
            bool complete = total > 0 && got >= total;
            string chapterName = Loc.T("chapter." + chapter.number, chapter.title);

            // Colour band with the chapter's name and progress, and the set reward beside it.
            var head = Line("Chapter" + chapter.number, y, 76f);
            var band = UIKit.Panel(head, "Band", chapter.color, ProceduralSprites.RoundedEdgeSmall);
            band.rectTransform.anchorMin = new Vector2(0f, 0f);
            band.rectTransform.anchorMax = new Vector2(0.56f, 1f);
            band.rectTransform.offsetMin = band.rectTransform.offsetMax = Vector2.zero;
            band.gameObject.AddComponent<UISkew>().skew = 0.18f;
            var title = UIKit.Label(band.transform, "Title", Loc.F("menu.chapter", chapter.number, chapterName).ToUpperInvariant(), 32, Color.white, TextAnchor.MiddleLeft, true);
            UIKit.Stretch(title.rectTransform);
            title.rectTransform.offsetMin = new Vector2(28f, 0f);
            title.rectTransform.offsetMax = new Vector2(-130f, 0f);
            UIKit.Fit(title, 22);
            var tsh = title.gameObject.AddComponent<Shadow>();
            tsh.effectColor = new Color(0f, 0f, 0.1f, 0.35f);
            tsh.effectDistance = new Vector2(0f, -3f);
            var progress = UIKit.Label(band.transform, "Progress", got + " / " + total, 36, Color.white, TextAnchor.MiddleRight, true);
            UIKit.Stretch(progress.rectTransform);
            progress.rectTransform.offsetMax = new Vector2(-26f, 0f);
            var psh = progress.gameObject.AddComponent<Shadow>();
            psh.effectColor = new Color(0f, 0f, 0.1f, 0.35f);
            psh.effectDistance = new Vector2(0f, -3f);

            var setItem = StickerRewards.ForChapter(cosmetics, chapter.number);
            if (setItem != null)
            {
                var reward = UIKit.Card(head, "SetReward", complete ? new Color(1f, 0.96f, 0.82f) : UITheme.Paper);
                var rr = (RectTransform)reward.transform.parent;
                rr.anchorMin = new Vector2(0.58f, 0f);
                rr.anchorMax = new Vector2(1f, 1f);
                rr.offsetMin = rr.offsetMax = Vector2.zero;
                var icon = CartoonPicture.On(UIKit.Icon(reward.transform, "Icon", CosmeticArt.Icon(setItem), complete ? Color.white : new Color(1f, 1f, 1f, 0.6f), 60f));
                UIKit.Place(icon.rectTransform, new Vector2(0f, 0.5f), new Vector2(12f, 0f), new Vector2(60f, 60f), new Vector2(0f, 0.5f));
                var label = UIKit.Label(reward.transform, "Label", (complete ? Loc.T("album.setDone") : Loc.T("album.setReward")) + "\n" + setItem.displayName,
                    26, UITheme.Ink, TextAnchor.MiddleLeft, true);
                UIKit.Stretch(label.rectTransform);
                label.rectTransform.offsetMin = new Vector2(84f, 4f);
                label.rectTransform.offsetMax = new Vector2(-50f, -4f);
                UIKit.Fit(label, 18);
                if (complete) Badge(reward.transform, false);
                else
                {
                    var tag = UIKit.Icon(reward.transform, "Sticker", ProceduralSprites.StickerIcon, Color.white, 38f);
                    UIKit.Place(tag.rectTransform, new Vector2(1f, 0.5f), new Vector2(-10f, 0f), new Vector2(38f, 38f), new Vector2(1f, 0.5f));
                }
            }
            y += 92f;

            // The stickers.
            var row = Line("Stickers" + chapter.number, y, Slot + 10f);
            float rowW = stories.Count * Slot + (stories.Count - 1) * SlotGap;
            for (int i = 0; i < stories.Count; i++)
            {
                var level = stories[i];
                bool found = SaveSystem.HasSticker(level.levelId);
                var slot = UIKit.Rect(row, "Slot_" + level.levelId);
                UIKit.Place(slot, new Vector2(0.5f, 1f), new Vector2(-rowW * 0.5f + Slot * 0.5f + i * (Slot + SlotGap), 0f), new Vector2(Slot, Slot), new Vector2(0.5f, 1f));
                var hit = slot.gameObject.AddComponent<Image>();
                hit.color = Color.clear;
                var def = level;
                slot.gameObject.AddComponent<Button>().onClick.AddListener(() =>
                    StickerDetail.Open(Controller.CanvasRoot, Controller.levels, Controller.cosmetics, def, Controller.PlayLevel));
                slot.gameObject.AddComponent<UIButtonFx>();
                var view = StickerView.Build(slot, level.levelId, chapter.color, found, Slot, true, (sheen++ * 0.37f) % 1f);
                UIKit.Stretch(view);
                UIKit.PopIn(view.gameObject, (sheen % 12) * 0.02f);
                if (!found)
                {
                    var num = UIKit.Label(slot, "Number", "#" + StickerDetail.StickerNumber(levels, level), 26, UITheme.InkSoft, TextAnchor.LowerCenter, true);
                    UIKit.Stretch(num.rectTransform);
                    num.rectTransform.offsetMin = new Vector2(0f, 30f);
                }
            }
            return y + Slot + 44f;
        }

        /// <summary>A green tick badge on the top-right corner of a reward card.</summary>
        static void Badge(Transform card, bool small)
        {
            float s = small ? 40f : 46f;
            var badge = UIKit.Icon(card, "Got", ProceduralSprites.CircleEdge, UITheme.Green, s);
            UIKit.Place(badge.rectTransform, new Vector2(1f, 1f), new Vector2(8f, 8f), new Vector2(s, s), new Vector2(0.5f, 0.5f));
            var tick = UIKit.Icon(badge.transform, "Tick", ProceduralSprites.Check, Color.white, s * 0.65f);
            UIKit.Place(tick.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(s * 0.62f, s * 0.62f));
        }
    }
}
