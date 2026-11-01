using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>The sticker album: one slot per story level, grouped by chapter colour, on a white page over the sky.</summary>
    public class AlbumScreen : FrontEndScreen
    {
        RectTransform grid;
        Text count;

        public override string Title { get { return Loc.T("album.title"); } }

        protected override void Build(RectTransform root)
        {
            var page = UIKit.Card(root, "Page", new Color(1f, 1f, 1f, 0.9f));
            var pageRoot = (RectTransform)page.transform.parent;
            pageRoot.anchorMin = Vector2.zero;
            pageRoot.anchorMax = Vector2.one;
            pageRoot.offsetMin = new Vector2(40f, 40f);
            pageRoot.offsetMax = new Vector2(-40f, -175f);

            var top = UIKit.Row(page.transform, "Heading", 22f, 56f, 40f, 40f);
            count = UIKit.SectionLabel(top, "");
            var hint = UIKit.Label(top, "Hint", Loc.T("album.hint"), 28, UITheme.InkSoft, TextAnchor.MiddleRight);
            UIKit.Stretch(hint.rectTransform);
            hint.rectTransform.offsetMin = new Vector2(520f, 0f);
            UIKit.Fit(hint, 20);

            ScrollRect scroll;
            grid = UIKit.ScrollArea(page.transform, "Grid", true, out scroll);
            var gridRoot = (RectTransform)scroll.transform;
            gridRoot.anchorMin = Vector2.zero;
            gridRoot.anchorMax = Vector2.one;
            gridRoot.offsetMin = new Vector2(20f, 12f);
            gridRoot.offsetMax = new Vector2(-20f, -96f);
            var layout = grid.gameObject.AddComponent<GridLayoutGroup>();
            layout.cellSize = new Vector2(224f, 264f);
            layout.spacing = new Vector2(22f, 22f);
            layout.padding = new RectOffset(10, 10, 10, 30);
            layout.childAlignment = TextAnchor.UpperCenter;
            grid.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;
        }

        public override void OnShow()
        {
            for (int i = grid.childCount - 1; i >= 0; i--) Object.Destroy(grid.GetChild(i).gameObject);
            var catalog = Controller.levels;
            int total = 0, found = 0, index = 0;
            foreach (var level in catalog.levels)
            {
                if (level.isChallenge) continue;
                total++;
                bool has = SaveSystem.HasSticker(level.levelId);
                if (has) found++;
                var info = catalog.Chapter(level.chapter);
                Color chapterColor = info != null ? info.color : UITheme.Accent;

                var cell = UIKit.Card(grid, "Sticker_" + level.levelId, has ? UITheme.Paper : UITheme.PaperDark);
                UIKit.PopIn(cell.transform.parent.gameObject, index++ * 0.02f);
                var band = UIKit.Panel(cell.transform, "Chapter", chapterColor, ProceduralSprites.RoundedEdgeSmall);
                UIKit.Place(band.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -12f), new Vector2(170f, 12f), new Vector2(0.5f, 1f));
                var icon = UIKit.Icon(cell.transform, "Icon", has ? StickerArt.For(level.levelId, chapterColor) : ProceduralSprites.Circle,
                    has ? Color.white : new Color(0.1f, 0.15f, 0.3f, 0.12f), 160f);
                UIKit.Place(icon.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -30f), new Vector2(160f, 160f), new Vector2(0.5f, 1f));
                if (has) icon.gameObject.AddComponent<UIPulse>().amount = 0.02f;
                var name = UIKit.Label(cell.transform, "Name", has ? Loc.T("level." + level.levelId, level.displayName) : Loc.T("album.missing"),
                    26, has ? UITheme.Ink : UITheme.InkSoft, TextAnchor.MiddleCenter, true);
                UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 40f), new Vector2(206f, 60f));
                UIKit.Fit(name, 18);
            }
            count.text = Loc.F("album.count", found, total).ToUpperInvariant();
        }
    }
}
