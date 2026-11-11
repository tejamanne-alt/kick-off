using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Filters (a button on the title screen, after Stickers, and in the pause menus): the looks over the whole picture, as cards to
    /// choose from: the original, the comic halftone, the pencil sketch and the classic cartoon. A choice applies at once, in
    /// every scene and every city (World/PostFX reads it each frame; the menus' pictures and buttons follow Filters.Changed), so it
    /// can be tried from the pause menu over the level itself. Progression/Filters has the list. (This was Add-ons and Filters
    /// before the cities: a city is now chosen after PLAY, UI/CityPicker.)
    /// </summary>
    public static class FiltersPanel
    {
        const float CardHeight = 150f, Gap = 18f;

        /// <summary>Filters' button colour, on the title screen and in the pause menus: orange.</summary>
        public static readonly Color ButtonColor = new Color(0.95f, 0.55f, 0.25f);

        /// <summary>
        /// The pause menus' Settings and Filters, side by side in the row Settings had, so the card keeps its height: 520 units
        /// wide in all, its top at <paramref name="y"/> below the card's top. Filters chosen here show at once behind the menu.
        /// </summary>
        public static void PauseRow(Transform card, Transform canvas, float y, float height, Color settingsColor)
        {
            const float width = 520f, gap = 16f;
            float half = (width - gap) * 0.5f;
            var settings = UIKit.Button(card, "pause.settings", Loc.T("pause.settings"), settingsColor, () => SettingsPanel.Open(canvas, null), 40);
            UIKit.Place((RectTransform)settings.transform, new Vector2(0.5f, 1f), new Vector2(-(half + gap) * 0.5f, y), new Vector2(half, height));
            var filters = UIKit.Button(card, "pause.filters", Loc.T("pause.filters"), ButtonColor, () => Open(canvas, null), 40);
            UIKit.Place((RectTransform)filters.transform, new Vector2(0.5f, 1f), new Vector2((half + gap) * 0.5f, y), new Vector2(half, height));
        }

        public static GameObject Open(Transform canvas, System.Action onClose)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Filters", new Vector2(1240f, 720f), out root);
            UIKit.Header(card.transform, Loc.T("filters.title"), 560f);

            // Two cards a row.
            var body = UIKit.Rect(card.transform, "Body");
            body.anchorMin = Vector2.zero;
            body.anchorMax = Vector2.one;
            body.offsetMin = new Vector2(50f, 170f);
            body.offsetMax = new Vector2(-50f, -130f);
            for (int i = 0; i < Filters.All.Length; i++)
            {
                string filter = Filters.All[i];
                bool on = filter == Filters.Chosen;
                var cell = Cell(body, "Filter_" + filter, (i / 2) * (CardHeight + Gap), i % 2);
                Choice(cell, Loc.T("filter." + filter), Loc.T("filter." + filter + ".about"), on ? Loc.T("filters.selected") : Loc.T("filters.choose"), on, () =>
                {
                    Filters.Chosen = filter;
                    Object.Destroy(root);
                    Open(canvas, onClose);   // rebuilt to show the choice
                });
            }

            // Along the bottom: when a choice applies, and Done.
            var note = UIKit.Label(card.transform, "Note", Loc.T("filters.note"), 28, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Place(note.rectTransform, Vector2.zero, new Vector2(50f, 50f), new Vector2(760f, 90f), Vector2.zero);
            UIKit.Fit(note, 20);
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 46);
            UIKit.Place((RectTransform)done.transform, new Vector2(1f, 0f), new Vector2(-50f, 40f), new Vector2(340f, 106f), new Vector2(1f, 0f));
            return root;
        }

        /// <summary>A card-sized cell in the left (0) or right (1) half of the body, <paramref name="top"/> down.</summary>
        internal static RectTransform Cell(RectTransform body, string name, float top, int column, float height = CardHeight, float gap = Gap)
        {
            var rt = UIKit.Rect(body, name);
            rt.anchorMin = new Vector2(column * 0.5f, 1f);
            rt.anchorMax = new Vector2(column * 0.5f + 0.5f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.offsetMin = new Vector2(column == 0 ? 0f : gap * 0.5f, -top - height);
            rt.offsetMax = new Vector2(column == 0 ? -gap * 0.5f : 0f, -top);
            return rt;
        }

        /// <summary>A filter's card: its name, what it does and its status; blue when chosen.</summary>
        static void Choice(RectTransform cell, string title, string line, string status, bool chosen, UnityEngine.Events.UnityAction choose)
        {
            Color face = chosen ? UITheme.Blue : UITheme.Paper;
            Color ink = chosen ? Color.white : UITheme.Ink;
            var b = UIKit.Button(cell, "Card", "", face, chosen ? null : choose);
            var rt = (RectTransform)b.transform;
            UIKit.Stretch(rt);
            rt.offsetMin = new Vector2(0f, UIButtonFx.Depth);
            var t = b.transform.Find("Face");

            var name = UIKit.Label(t, "Name", title, 40, ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(name.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -18f), new Vector2(500f, 52f), new Vector2(0f, 1f));
            UIKit.Fit(name, 26);
            var about = UIKit.Label(t, "Line", line, 28, new Color(ink.r, ink.g, ink.b, ink.a * 0.8f), TextAnchor.MiddleLeft);
            UIKit.Place(about.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -68f), new Vector2(500f, 38f), new Vector2(0f, 1f));
            UIKit.Fit(about, 20);
            var state = UIKit.Label(t, "Status", status, 26, chosen ? Color.white : UITheme.Navy, TextAnchor.MiddleLeft, true);
            UIKit.Place(state.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -102f), new Vector2(500f, 34f), new Vector2(0f, 1f));
            UIKit.Fit(state, 18);
        }
    }
}
