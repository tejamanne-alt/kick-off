using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>The sticker album: one slot per story level, grouped by chapter colour.</summary>
    public class AlbumScreen : FrontEndScreen
    {
        RectTransform grid;
        Text count;

        public override string Title { get { return Loc.T("album.title"); } }

        protected override void Build(RectTransform root)
        {
            count = UIKit.Label(root, "Count", "", 40, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(count.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -195f), new Vector2(1000f, 60f));
            var hint = UIKit.Label(root, "Hint", Loc.T("album.hint"), 30, UITheme.InkSoft);
            UIKit.Place(hint.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -245f), new Vector2(1400f, 50f));

            ScrollRect scroll;
            grid = UIKit.ScrollArea(root, "Grid", true, out scroll);
            var gridRoot = (RectTransform)scroll.transform;
            gridRoot.anchorMin = Vector2.zero;
            gridRoot.anchorMax = Vector2.one;
            gridRoot.offsetMin = new Vector2(80f, 40f);
            gridRoot.offsetMax = new Vector2(-80f, -290f);
            var layout = grid.gameObject.AddComponent<GridLayoutGroup>();
            layout.cellSize = new Vector2(230f, 270f);
            layout.spacing = new Vector2(24f, 24f);
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
                var icon = UIKit.Icon(cell.transform, "Icon", has ? StickerArt.For(level.levelId, chapterColor) : ProceduralSprites.Circle,
                    has ? Color.white : new Color(0f, 0f, 0f, 0.12f), 170f);
                UIKit.Place(icon.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -20f), new Vector2(170f, 170f), new Vector2(0.5f, 1f));
                if (has) icon.gameObject.AddComponent<UIPulse>().amount = 0.02f;
                var name = UIKit.Label(cell.transform, "Name", has ? Loc.T("level." + level.levelId, level.displayName) : Loc.T("album.missing"),
                    26, has ? UITheme.Ink : UITheme.InkSoft, TextAnchor.MiddleCenter, true);
                UIKit.Place(name.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 40f), new Vector2(220f, 60f));
            }
            count.text = Loc.F("album.count", found, total);
        }
    }
}
