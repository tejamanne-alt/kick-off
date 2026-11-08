using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>Credits: the logo, a line about the game, "Made with Unity", and the version.</summary>
    public static class CreditsPanel
    {
        public static void Open(Transform canvas)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Credits", new Vector2(1040f, 900f), out root);
            UIKit.Header(card.transform, Loc.T("credits.title"), 460f);

            // Laid out top down, each piece pinned by its own edge so nothing can overlap: the logo under the header,
            // the text, then the version just above Done at the bottom.
            var logo = KickOffLogo.Build(card.transform, 0.62f, false);
            UIKit.Place(logo, new Vector2(0.5f, 1f), new Vector2(0f, -84f), logo.sizeDelta, new Vector2(0.5f, 1f));

            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () => Object.Destroy(root), 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(0.5f, 0f), new Vector2(0f, 52f), new Vector2(360f, 106f), new Vector2(0.5f, 0f));

            var version = UIKit.Label(card.transform, "Version", KickOffLogo.GameName + "  v" + Application.version, 28, UITheme.InkSoft, TextAnchor.MiddleCenter, true);
            UIKit.Place(version.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 186f), new Vector2(700f, 40f), new Vector2(0.5f, 0f));

            var body = UIKit.Label(card.transform, "Body", Loc.T("credits.body"), 34, UITheme.Ink);
            body.rectTransform.anchorMin = Vector2.zero;
            body.rectTransform.anchorMax = Vector2.one;
            body.rectTransform.offsetMin = new Vector2(70f, 250f);                           // (above the version)
            body.rectTransform.offsetMax = new Vector2(-70f, -(84f + logo.sizeDelta.y + 34f));  // (below the logo)
            UIKit.Fit(body, 24);
        }
    }
}
