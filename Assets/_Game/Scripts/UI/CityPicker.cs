using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The city picker, after PLAY and HOLIDAY RUN on the title screen (docs/CITIES.md): the five cities as cards, each with its
    /// colour, its country, a line about its way to school and whether it can be played yet. After PLAY, a city that can be
    /// played is chosen (Progression/Cities.Select: the levels load in its streets) and the map opens; the city played last is
    /// blue. After HOLIDAY RUN, only a city with its own Holiday Run can be tapped (Kamakura, so far), and the story's choice is
    /// left as it was. Cities still to build are listed as coming soon.
    /// </summary>
    public static class CityPicker
    {
        public enum Mode { Story, Holiday }

        const float CardHeight = 168f, Gap = 18f;

        public static GameObject Open(Transform canvas, Mode mode, System.Action onChosen)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Cities", new Vector2(1400f, 960f), out root);
            UIKit.Header(card.transform, Loc.T(mode == Mode.Story ? "city.pick.story" : "city.pick.holiday"), 820f);

            // Two cards a row, in the order of Cities.All.
            var body = UIKit.Rect(card.transform, "Body");
            body.anchorMin = Vector2.zero;
            body.anchorMax = Vector2.one;
            body.offsetMin = new Vector2(50f, 170f);
            body.offsetMax = new Vector2(-50f, -130f);
            var last = Cities.Active;
            for (int i = 0; i < Cities.All.Length; i++)
            {
                var city = Cities.All[i];
                bool open = CanPlay(city, mode);
                bool chosen = open && mode == Mode.Story && city == last;
                var cell = FiltersPanel.Cell(body, "City_" + city.id, (i / 2) * (CardHeight + Gap), i % 2, CardHeight, Gap);
                Card(cell, city, Status(city, mode, chosen), chosen, open, () =>
                {
                    if (mode == Mode.Story) Cities.Select(city);
                    Object.Destroy(root);
                    if (onChosen != null) onChosen();
                });
            }

            // Along the bottom: what makes each city its own, and Back.
            var note = UIKit.Label(card.transform, "Note", Loc.T("city.pick.note"), 28, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Place(note.rectTransform, Vector2.zero, new Vector2(50f, 50f), new Vector2(900f, 90f), Vector2.zero);
            UIKit.Fit(note, 20);
            var back = UIKit.Button(card.transform, "Back", Loc.T("city.pick.back"), UITheme.Paper, () => Object.Destroy(root), 44, UITheme.Ink);
            UIKit.Place((RectTransform)back.transform, new Vector2(1f, 0f), new Vector2(-50f, 40f), new Vector2(300f, 106f), new Vector2(1f, 0f));
            return root;
        }

        /// <summary>The city can be played in this mode now: built, unlocked and, for the Holiday Run, with its own run.</summary>
        public static bool CanPlay(City city, Mode mode)
        {
            return city.Unlocked && (mode == Mode.Story || city.holidayRun);
        }

        static string Status(City city, Mode mode, bool chosen)
        {
            if (!city.story) return Loc.T("city.pick.soon");
            if (mode == Mode.Holiday && !city.holidayRun) return Loc.T("city.pick.holidaySoon");
            if (!city.Unlocked) return Loc.T("city.pick.locked");
            return Loc.T(chosen ? "city.pick.last" : "city.pick.play");
        }

        /// <summary>A city's card: its colour down the left, its name and country, its line, its status; blue for the last played, grey when it can't be.</summary>
        static void Card(RectTransform cell, City city, string status, bool chosen, bool open, UnityEngine.Events.UnityAction choose)
        {
            Color face = chosen ? UITheme.Blue : open ? UITheme.Paper : UITheme.PaperDark;
            Color ink = chosen ? Color.white : open ? UITheme.Ink : UITheme.InkSoft;
            var b = UIKit.Button(cell, "Card", "", face, open ? choose : null);
            var rt = (RectTransform)b.transform;
            UIKit.Stretch(rt);
            rt.offsetMin = new Vector2(0f, UIButtonFx.Depth);
            if (!open) b.interactable = false;
            var t = b.transform.Find("Face");

            var band = UIKit.Panel(t, "Band", open ? city.colour : Color.Lerp(city.colour, UITheme.PaperDark, 0.55f), ProceduralSprites.RoundedSmall);
            band.rectTransform.anchorMin = Vector2.zero;
            band.rectTransform.anchorMax = new Vector2(0f, 1f);
            band.rectTransform.offsetMin = new Vector2(14f, 16f);
            band.rectTransform.offsetMax = new Vector2(36f, -16f);
            band.raycastTarget = false;

            var name = UIKit.Label(t, "Name", Loc.T(city.nameKey), 44, ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(name.rectTransform, new Vector2(0f, 1f), new Vector2(58f, -16f), new Vector2(320f, 56f), new Vector2(0f, 1f));
            UIKit.Fit(name, 28);
            var country = UIKit.Label(t, "Country", Loc.T(city.countryKey), 27, new Color(ink.r, ink.g, ink.b, ink.a * 0.75f), TextAnchor.MiddleRight);
            UIKit.Place(country.rectTransform, new Vector2(1f, 1f), new Vector2(-26f, -24f), new Vector2(230f, 40f), new Vector2(1f, 1f));
            UIKit.Fit(country, 18);
            var about = UIKit.Label(t, "About", Loc.T(city.aboutKey), 28, new Color(ink.r, ink.g, ink.b, ink.a * 0.85f), TextAnchor.MiddleLeft);
            UIKit.Place(about.rectTransform, new Vector2(0f, 1f), new Vector2(58f, -74f), new Vector2(560f, 38f), new Vector2(0f, 1f));
            UIKit.Fit(about, 19);
            var state = UIKit.Label(t, "Status", status, 26, chosen ? Color.white : open ? UITheme.Navy : UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(state.rectTransform, new Vector2(0f, 1f), new Vector2(58f, -114f), new Vector2(560f, 34f), new Vector2(0f, 1f));
            UIKit.Fit(state, 18);
        }
    }
}
