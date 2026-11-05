using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The Controls page, from the pause menu (story levels and the Holiday Run) and Settings > Controls: one row per
    /// move, each with a small picture of the control on a dark tile (in the HUD's glass look) and what it does, a line
    /// about left-handed play, and a button for the guided tour (<see cref="ControlsTour"/>): played there and then in
    /// a level, or turned back on for the next level from the menus.
    /// </summary>
    public static class ControlsGuide
    {
        /// <summary>A row of the page: its picture, its heading (the tour's step title) and its text.</summary>
        public enum Picture { Walk, Slide, Jump, Kick, Touch }

        public struct Row
        {
            public readonly Picture picture;
            public readonly string titleKey, textKey;

            public Row(Picture picture, string titleKey, string textKey)
            {
                this.picture = picture;
                this.titleKey = titleKey;
                this.textKey = textKey;
            }
        }

        /// <summary>The page's rows, in order (the tests check every key is in every language).</summary>
        public static readonly Row[] Rows =
        {
            new Row(Picture.Walk, "tour.walk.title", "controls.walk"),
            new Row(Picture.Slide, "tour.slide.title", "controls.slide"),
            new Row(Picture.Jump, "tour.jump.title", "controls.jump"),
            new Row(Picture.Kick, "tour.kick.title", "controls.kick"),
            new Row(Picture.Touch, "tour.touch.title", "controls.touch"),
        };

        /// <summary>Every other key the page uses.</summary>
        public static readonly string[] OtherKeys = { "controls.title", "controls.leftHanded", "controls.tour", "controls.tourSet", "settings.done" };

        const float RowHeight = 118f;
        const float RowGap = 8f;
        static readonly Color Tile = new Color(0.16f, 0.24f, 0.42f);

        public static GameObject Open(Transform canvas, System.Action onClose)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "ControlsGuide", new Vector2(1340f, 980f), out root);
            UIKit.Header(card.transform, Loc.T("controls.title"), 520f);

            var list = UIKit.Rect(card.transform, "Rows");
            list.anchorMin = Vector2.zero;
            list.anchorMax = Vector2.one;
            list.offsetMin = new Vector2(56f, 190f);
            list.offsetMax = new Vector2(-56f, -84f);

            float y = 0f;
            foreach (var row in Rows)
            {
                var rt = UIKit.Row(list, row.titleKey, y, RowHeight);
                Draw(rt, row.picture);
                var heading = UIKit.Label(rt, "Title", Loc.T(row.titleKey), 34, UITheme.Navy, TextAnchor.UpperLeft, true);
                heading.rectTransform.anchorMin = new Vector2(0f, 1f);
                heading.rectTransform.anchorMax = new Vector2(1f, 1f);
                heading.rectTransform.pivot = new Vector2(0f, 1f);
                heading.rectTransform.offsetMin = new Vector2(200f, -44f);
                heading.rectTransform.offsetMax = new Vector2(0f, -4f);
                UIKit.Fit(heading, 24);
                var text = UIKit.Label(rt, "Text", Loc.T(row.textKey), 27, UITheme.Ink, TextAnchor.UpperLeft);
                text.rectTransform.anchorMin = Vector2.zero;
                text.rectTransform.anchorMax = Vector2.one;
                text.rectTransform.offsetMin = new Vector2(200f, 0f);
                text.rectTransform.offsetMax = new Vector2(0f, -46f);
                text.resizeTextForBestFit = true;
                text.resizeTextMinSize = 19;
                text.resizeTextMaxSize = 27;
                text.verticalOverflow = VerticalWrapMode.Truncate;
                y += RowHeight + RowGap;
            }

            var hand = UIKit.Label(card.transform, "LeftHanded", Loc.T("controls.leftHanded"), 26, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Place(hand.rectTransform, new Vector2(0f, 0f), new Vector2(56f, 160f), new Vector2(1228f, 44f), new Vector2(0f, 0.5f));
            UIKit.Fit(hand, 18);

            // The tour: there and then in a level; from the menus, on again for the next level.
            Button tour = null;
            tour = UIKit.Button(card.transform, "Tour", Loc.T("controls.tour"), UITheme.Blue, () =>
            {
                var replay = ControlsTour.Replay;
                if (replay != null)
                {
                    Object.Destroy(root);
                    replay();
                    return;
                }
                ControlsTour.Done = false;
                tour.interactable = false;
                var label = tour.GetComponentInChildren<Text>();
                if (label != null) label.text = Loc.T("controls.tourSet");
            }, 34);
            UIKit.Place((RectTransform)tour.transform, Vector2.zero, new Vector2(56f, 40f), new Vector2(520f, 100f), Vector2.zero);

            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(1f, 0f), new Vector2(-56f, 40f), new Vector2(320f, 100f), new Vector2(1f, 0f));
            return root;
        }

        // ---------- The pictures ----------

        /// <summary>A dark tile at the row's left with the control drawn on it in the HUD's white glass (the challenge guide's rows too).</summary>
        public static void Draw(RectTransform row, Picture picture)
        {
            var tile = UIKit.Panel(row, "Tile", Tile, ProceduralSprites.RoundedSmall);
            UIKit.Place(tile.rectTransform, new Vector2(0f, 0.5f), new Vector2(0f, 0f), new Vector2(176f, RowHeight - 6f), new Vector2(0f, 0.5f));
            tile.raycastTarget = false;
            var t = tile.rectTransform;
            switch (picture)
            {
                case Picture.Walk:
                    Stick(t, new Vector2(26f, 0f));
                    break;
                case Picture.Slide:
                    Stick(t, new Vector2(14f, -27f));
                    break;
                case Picture.Jump:
                    Disc(t, UITheme.Blue);
                    Glyph(t, ProceduralSprites.JumpIcon, Vector2.zero, 60f, 0f, 1f);
                    break;
                case Picture.Kick:
                    Disc(t, UITheme.Accent);
                    Glyph(t, ProceduralSprites.BallIcon, Vector2.zero, 50f, 0f, 1f);
                    break;
                case Picture.Touch:
                    Glyph(t, ProceduralSprites.Ring, Vector2.zero, 84f, 0f, 0.45f);
                    Glyph(t, ProceduralSprites.SoftEdgeDisc, Vector2.zero, 48f, 0f, 0.85f);
                    break;
            }
        }

        /// <summary>The stick as the HUD draws it: its ring, a faint knob where it rests and the knob pushed by <paramref name="knob"/>.</summary>
        static void Stick(RectTransform tile, Vector2 knob)
        {
            const float size = 96f;
            Glyph(tile, ProceduralSprites.SoftEdgeDisc, Vector2.zero, size, 0f, 0.14f);
            Glyph(tile, ProceduralSprites.ThinRing, Vector2.zero, size, 0f, 0.8f);
            Glyph(tile, ProceduralSprites.SoftEdgeDisc, Vector2.zero, size * 0.44f, 0f, 0.15f);
            Glyph(tile, ProceduralSprites.SoftEdgeDisc, knob, size * 0.44f, 0f, 0.6f);
            Glyph(tile, ProceduralSprites.ThinRing, knob, size * 0.44f, 0f, 0.9f);
        }

        static void Disc(RectTransform tile, Color tint)
        {
            Glyph(tile, ProceduralSprites.SoftEdgeDisc, Vector2.zero, 92f, 0f, 0.35f, tint);
            Glyph(tile, ProceduralSprites.ThinRing, Vector2.zero, 92f, 0f, 0.85f);
        }

        static void Glyph(RectTransform tile, Sprite sprite, Vector2 at, float size, float angle, float alpha, Color? tint = null)
        {
            Color c = tint ?? Color.white;
            c.a = alpha;
            var image = UIKit.Icon(tile, sprite != null ? sprite.name : "Glyph", sprite, c, size);
            var rt = image.rectTransform;
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = at;
            rt.localRotation = Quaternion.Euler(0f, 0f, angle);
        }
    }
}
