using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Add-ons and Filters (a button on the title screen, after Stickers): the add-ons (the same levels in another country's streets with that
    /// country's music: the original Kamakura, Japan; California, unlocked by finishing every level; India and
    /// a Tokyo city still to come) as cards to choose from, and the filters (a look over the whole picture:
    /// the original, the comic halftone and the pencil sketch). A choice is saved at once; an add-on applies from the next
    /// level loaded, a filter at once.
    /// Progression/AddOns has the list and the rules.
    /// </summary>
    public static class AddOnsPanel
    {
        const float CardHeight = 132f, Gap = 16f, SectionHeight = 46f;   // two rows of add-ons and two of filters fit the modal

        public static GameObject Open(Transform canvas, System.Action onClose)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "AddOns", new Vector2(1340f, 960f), out root);
            UIKit.Header(card.transform, Loc.T("addons.title"), 640f);

            // The add-ons and filters in a scroll area: today they fill it exactly, so it stays still; the lists are made to
            // grow (an add-on or a filter still to come), and then the rest scrolls into view instead of running off the card.
            ScrollRect scroll;
            var body = UIKit.ScrollArea(card.transform, "Body", true, out scroll);
            var area = (RectTransform)scroll.transform;
            area.anchorMin = Vector2.zero;
            area.anchorMax = Vector2.one;
            area.offsetMin = new Vector2(50f, 160f);
            area.offsetMax = new Vector2(-50f, -76f);

            // Add-ons: two cards a row.
            float y = 0f;
            UIKit.SectionLabel(UIKit.Row(body, "AddOnsLabel", y, SectionHeight), Loc.T("addons.addons"));
            y += SectionHeight + 10f;
            var selected = AddOns.Active;
            for (int i = 0; i < AddOns.All.Length; i++)
            {
                var addOn = AddOns.All[i];
                var cell = Cell(body, "AddOn_" + addOn.id, y + (i / 2) * (CardHeight + Gap), i % 2);
                string status = !addOn.available ? Loc.T("addons.soon")
                    : !addOn.Unlocked ? Loc.T("addons.locked")
                    : addOn == selected ? Loc.T("addons.selected") : Loc.T("addons.choose");
                Choice(cell, Loc.T(addOn.nameKey), Loc.T(addOn.placeKey), status, addOn == selected, addOn.Unlocked, () =>
                {
                    AddOns.Select(addOn);
                    Object.Destroy(root);
                    Open(canvas, onClose);   // rebuilt to show the choice
                });
            }
            y += ((AddOns.All.Length + 1) / 2) * (CardHeight + Gap) + 6f;

            // Filters: two cards a row; what is still to come on the right of the section's label.
            UIKit.SectionLabel(UIKit.Row(body, "FiltersLabel", y, SectionHeight), Loc.T("addons.filters"));
            var more = UIKit.Label(UIKit.Row(body, "MoreFilters", y, SectionHeight, 420f, 0f), "Text", Loc.T("addons.moreFilters"), 26, UITheme.InkSoft, TextAnchor.MiddleRight);
            UIKit.Stretch(more.rectTransform);
            UIKit.Fit(more, 18);
            y += SectionHeight + 10f;
            for (int i = 0; i < AddOns.Filters.Length; i++)
            {
                string filter = AddOns.Filters[i];
                bool on = filter == AddOns.Filter;
                var cell = Cell(body, "Filter_" + filter, y + (i / 2) * (CardHeight + Gap), i % 2);
                Choice(cell, Loc.T("filter." + filter), Loc.T("filter." + filter + ".about"), on ? Loc.T("addons.selected") : Loc.T("addons.choose"), on, true, () =>
                {
                    AddOns.Filter = filter;
                    Object.Destroy(root);
                    Open(canvas, onClose);
                });
            }

            y += ((AddOns.Filters.Length + 1) / 2) * (CardHeight + Gap);
            body.sizeDelta = new Vector2(0f, y);
            // Scrolls only when there is more than fits (the area is the card's height less the header and the bottom row),
            // and stops at the ends rather than springing past them.
            float viewHeight = Mathf.Min(960f, UIKit.ReferenceResolution.y - 80f) - 160f - 76f;
            scroll.vertical = y > viewHeight + 1f;
            scroll.movementType = ScrollRect.MovementType.Clamped;

            // Along the bottom: when a choice applies, and Done.
            var note = UIKit.Label(card.transform, "Note", Loc.T("addons.note"), 28, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Place(note.rectTransform, Vector2.zero, new Vector2(50f, 50f), new Vector2(820f, 90f), Vector2.zero);
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
        static RectTransform Cell(RectTransform body, string name, float top, int column)
        {
            var rt = UIKit.Rect(body, name);
            rt.anchorMin = new Vector2(column * 0.5f, 1f);
            rt.anchorMax = new Vector2(column * 0.5f + 0.5f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.offsetMin = new Vector2(column == 0 ? 0f : Gap * 0.5f, -top - CardHeight);
            rt.offsetMax = new Vector2(column == 0 ? -Gap * 0.5f : 0f, -top);
            return rt;
        }

        /// <summary>A choice card: its name, a line under it (the place, or what it does) and its status; blue when chosen, grey when it cannot be.</summary>
        static void Choice(RectTransform cell, string title, string line, string status, bool chosen, bool open, UnityEngine.Events.UnityAction choose)
        {
            Color face = chosen ? UITheme.Blue : open ? UITheme.Paper : UITheme.PaperDark;
            Color ink = chosen ? Color.white : open ? UITheme.Ink : UITheme.InkSoft;
            var b = UIKit.Button(cell, "Card", "", face, chosen || !open ? null : choose);
            var rt = (RectTransform)b.transform;
            UIKit.Stretch(rt);
            rt.offsetMin = new Vector2(0f, UIButtonFx.Depth);
            if (!open) b.interactable = false;
            var t = b.transform.Find("Face");

            var name = UIKit.Label(t, "Name", title, 38, ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(name.rectTransform, new Vector2(0f, 1f), new Vector2(28f, -14f), new Vector2(560f, 50f), new Vector2(0f, 1f));
            UIKit.Fit(name, 26);
            var place = UIKit.Label(t, "Line", line, 27, new Color(ink.r, ink.g, ink.b, ink.a * 0.8f), TextAnchor.MiddleLeft);
            UIKit.Place(place.rectTransform, new Vector2(0f, 1f), new Vector2(28f, -60f), new Vector2(560f, 36f), new Vector2(0f, 1f));
            UIKit.Fit(place, 20);
            var state = UIKit.Label(t, "Status", status, 25, chosen ? Color.white : open ? UITheme.Navy : UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(state.rectTransform, new Vector2(0f, 1f), new Vector2(28f, -94f), new Vector2(560f, 32f), new Vector2(0f, 1f));
            UIKit.Fit(state, 18);
        }
    }
}
