using DribbleToSchool.Coop;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The co-op lobby's stage select (from FrontEnd/CoopScreen): the six ways from home to school as cards (each with its
    /// legs) and Random, then the location (the original streets, California, Random). Any player may choose, as in a
    /// fighting game's stage select: the choice goes to the host, the last one it gets wins, everyone sees who chose, and
    /// everyone readies again. A location this phone has not unlocked can't be chosen here, but plays for everyone once
    /// someone who has it chooses it. Where chapters are sold (Store/Monetization), a stage outside them is locked to choose.
    /// Also the co-op screens' yes/no question (<see cref="Confirm"/>).
    /// </summary>
    public static class CoopStagePicker
    {
        const float CardW = 300f, CardH = 150f, Gap = 18f;

        public static GameObject Open(Transform canvas, CoopSession session, LevelCatalog catalog, System.Action onClose)
        {
            GameObject root;
            var face = UIKit.Modal(canvas, "CoopStagePicker", new Vector2(1340f, 960f), out root);
            UIKit.Header(face.transform, Loc.T("coop.pick.title"), 620f);
            var sel = session.Selection;

            float y = -90f;
            UIKit.SectionLabel(UIKit.Row(face.transform, "StagesLabel", -y, 46f, 50f, 50f), Loc.T("coop.pick.stages"));
            y -= 60f;
            int count = RouteTable.All.Length + 1;
            // The chosen location, unless it is random: a route its streets don't have yet (Florida: only the beach) is shut.
            bool anyPlace = sel.addOn >= CoopLocations.Count;
            for (int i = 0; i < count; i++)
            {
                bool random = i == RouteTable.All.Length;
                var route = random ? null : RouteTable.All[i];
                byte value = random ? CoopSelection.Random : (byte)i;
                bool fits = random || anyPlace || CoopLocations.Fits(i, sel.addOn);
                bool open = random || (Store.Monetization.IsChapterUnlocked(route.chapter) && fits);
                bool chosen = sel.route == value || (random && sel.route >= RouteTable.All.Length);
                Color colour = random ? UITheme.Gold : ChapterColour(catalog, route.chapter);
                string title = random ? Loc.T("coop.random.route") : Loc.T(route.NameKey);
                string line = random ? Loc.T("coop.random.routeShort") : !fits ? Loc.F("coop.route.notIn", Loc.T(CoopLocations.At(sel.addOn).nameKey))
                    : Loc.F("coop.legs", route.levels.Length);
                var cell = Cell(face.transform, i % 4, y - (i / 4) * (CardH + Gap), CardW, CardH);
                Card(cell, title, line, colour, chosen, open, () =>
                {
                    session.Select(value, session.Selection.addOn);
                    Object.Destroy(root);
                    Open(canvas, session, catalog, onClose);
                });
            }
            y -= 2 * (CardH + Gap) + 10f;

            UIKit.SectionLabel(UIKit.Row(face.transform, "PlacesLabel", -y, 46f, 50f, 50f), Loc.T("coop.pick.places"));
            y -= 60f;
            for (int i = 0; i <= CoopLocations.Count; i++)
            {
                bool random = i == CoopLocations.Count;
                var place = random ? null : CoopLocations.At(i);
                byte value = random ? CoopSelection.Random : (byte)i;
                // A location with only some routes (Florida: the beach) is shut while the chosen route isn't one of them.
                bool anyRoute = sel.route >= RouteTable.All.Length;
                bool fits = random || anyRoute || CoopLocations.Fits(sel.route, i);
                bool open = random || (place.Unlocked && fits);
                bool chosen = sel.addOn == value || (random && sel.addOn >= CoopLocations.Count);
                string title = random ? Loc.T("coop.random.place") : Loc.T(place.nameKey);
                string line = random ? Loc.T("coop.random.placeShort") : !place.Unlocked ? Loc.T("addons.locked")
                    : !fits ? Loc.F("coop.place.only", OnlyRoutes(place)) : Loc.T(place.placeKey);
                var cell = Cell(face.transform, i % 4, y - (i / 4) * (CardH + Gap), CardW, CardH);
                Card(cell, title, line, random ? UITheme.Gold : UITheme.Blue, chosen, open, () =>
                {
                    session.Select(session.Selection.route, value);
                    Object.Destroy(root);
                    Open(canvas, session, catalog, onClose);
                });
            }

            var note = UIKit.Label(face.transform, "Note", Loc.T("coop.pick.note"), 26, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Place(note.rectTransform, Vector2.zero, new Vector2(50f, 44f), new Vector2(860f, 90f), Vector2.zero);
            UIKit.Fit(note, 18);
            var done = UIKit.Button(face.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(1f, 0f), new Vector2(-50f, 40f), new Vector2(320f, 100f), new Vector2(1f, 0f));
            return root;
        }

        /// <summary>The names of the routes a location has (Florida: "Seaside Road").</summary>
        static string OnlyRoutes(Progression.AddOn place)
        {
            var names = new System.Collections.Generic.List<string>();
            foreach (var route in RouteTable.All)
                if (place.HasChapter(route.chapter)) names.Add(Loc.T(route.NameKey));
            return string.Join(", ", names.ToArray());
        }

        static Color ChapterColour(LevelCatalog catalog, int chapter)
        {
            var info = catalog != null ? catalog.Chapter(chapter) : null;
            return info != null ? info.color : UITheme.Accent;
        }

        static RectTransform Cell(Transform parent, int column, float top, float w, float h)
        {
            var rt = UIKit.Rect(parent, "Cell");
            rt.anchorMin = rt.anchorMax = new Vector2(0f, 1f);
            rt.pivot = new Vector2(0f, 1f);
            rt.anchoredPosition = new Vector2(50f + column * (w + Gap), top);
            rt.sizeDelta = new Vector2(w, h);
            return rt;
        }

        static void Card(RectTransform cell, string title, string line, Color colour, bool chosen, bool open, UnityEngine.Events.UnityAction choose)
        {
            Color face = chosen ? colour : open ? UITheme.Paper : UITheme.PaperDark;
            Color ink = chosen ? Color.white : open ? UITheme.Ink : UITheme.InkSoft;
            var b = UIKit.Button(cell, "Card", "", face, chosen || !open ? null : choose);
            var rt = (RectTransform)b.transform;
            UIKit.Stretch(rt);
            rt.offsetMin = new Vector2(0f, UIButtonFx.Depth);
            if (!open) b.interactable = false;
            var t = b.transform.Find("Face");
            if (!chosen)
            {
                var stripe = UIKit.Panel(t, "Stripe", colour, ProceduralSprites.RoundedSmall);
                UIKit.Place(stripe.rectTransform, new Vector2(0f, 0.5f), new Vector2(12f, 0f), new Vector2(10f, 96f), new Vector2(0f, 0.5f));
                stripe.raycastTarget = false;
            }
            var name = UIKit.Label(t, "Name", title, 34, ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(name.rectTransform, new Vector2(0f, 1f), new Vector2(34f, -16f), new Vector2(cell.sizeDelta.x - 50f, 72f), new Vector2(0f, 1f));
            UIKit.Fit(name, 22);
            var sub = UIKit.Label(t, "Line", line, 25, new Color(ink.r, ink.g, ink.b, ink.a * 0.85f), TextAnchor.MiddleLeft);
            UIKit.Place(sub.rectTransform, new Vector2(0f, 0f), new Vector2(34f, 14f), new Vector2(cell.sizeDelta.x - 50f, 44f), new Vector2(0f, 0f));
            UIKit.Fit(sub, 16);
            if (!open)
            {
                var lockIcon = UIKit.Icon(t, "Lock", ProceduralSprites.Lock, UITheme.InkSoft, 40f);
                UIKit.Place(lockIcon.rectTransform, new Vector2(1f, 1f), new Vector2(-14f, -14f), new Vector2(40f, 40f), new Vector2(1f, 1f));
            }
        }

        /// <summary>A yes/no card over everything: <paramref name="yes"/> runs on Yes.</summary>
        public static GameObject Confirm(Transform canvas, string question, System.Action yes)
        {
            return Confirm(canvas, question, yes, "coop.yesLeave");
        }

        /// <summary>A yes/no question; <paramref name="yesKey"/> labels the yes (red) button.</summary>
        public static GameObject Confirm(Transform canvas, string question, System.Action yes, string yesKey)
        {
            GameObject root;
            var face = UIKit.Modal(canvas, "CoopConfirm", new Vector2(900f, 460f), out root);
            var text = UIKit.Label(face.transform, "Question", question, 38, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(text.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -60f), new Vector2(800f, 200f), new Vector2(0.5f, 1f));
            UIKit.Fit(text, 24);
            var go = root;
            var ok = UIKit.Button(face.transform, "Yes", Loc.T(yesKey), UITheme.Red, () => { Object.Destroy(go); if (yes != null) yes(); }, 38);
            UIKit.Place((RectTransform)ok.transform, new Vector2(0.5f, 0f), new Vector2(-180f, 44f), new Vector2(320f, 100f), new Vector2(0.5f, 0f));
            var no = UIKit.Button(face.transform, "No", Loc.T("coop.stay"), UITheme.Green, () => Object.Destroy(go), 38);
            UIKit.Place((RectTransform)no.transform, new Vector2(0.5f, 0f), new Vector2(180f, 44f), new Vector2(320f, 100f), new Vector2(0.5f, 0f));
            return root;
        }
    }
}
