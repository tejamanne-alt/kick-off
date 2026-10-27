using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.UI
{
    public static class CreditsPanel
    {
        public static void Open(Transform canvas)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Credits", new Vector2(1100f, 820f), out root);
            var title = UIKit.Title(card.transform, "Title", Loc.T("credits.title"), 64, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -70f), new Vector2(900f, 90f));
            var body = UIKit.Label(card.transform, "Body", Loc.T("credits.body") + "\n\nv" + Application.version, 38, UITheme.Ink);
            UIKit.Place(body.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, 10f), new Vector2(950f, 520f));
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () => Object.Destroy(root), 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(0.5f, 0f), new Vector2(0f, 90f), new Vector2(360f, 110f));
        }
    }
}
