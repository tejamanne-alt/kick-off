using DribbleToSchool.Localization;
using DribbleToSchool.Store;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>"Unlock the full game" offer: what you get, the price, buy and restore.</summary>
    public static class UnlockPanel
    {
        public static void Open(Transform canvas, System.Action onUnlocked)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Unlock", new Vector2(1100f, 860f), out root);
            var title = UIKit.Title(card.transform, "Title", Loc.T("unlock.title"), 64, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -80f), new Vector2(1000f, 100f));
            var body = UIKit.Label(card.transform, "Body", Loc.T("unlock.body"), 38, UITheme.Ink);
            UIKit.Place(body.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, 60f), new Vector2(950f, 380f));
            var status = UIKit.Label(card.transform, "Status", "", 32, UITheme.Red, TextAnchor.MiddleCenter, true);
            UIKit.Place(status.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, 250f), new Vector2(950f, 50f));

            var buy = UIKit.Button(card.transform, "Buy", Loc.F("unlock.buy", StoreService.FullGamePrice), UITheme.Accent, () =>
            {
                StoreService.BuyFullGame(result =>
                {
                    if (result == PurchaseResult.Success)
                    {
                        Object.Destroy(root);
                        if (onUnlocked != null) onUnlocked();
                    }
                    else status.text = Loc.T(result == PurchaseResult.Cancelled ? "unlock.cancelled" : "unlock.failed");
                });
            }, 46);
            UIKit.Place((RectTransform)buy.transform, new Vector2(0.5f, 0f), new Vector2(0f, 150f), new Vector2(520f, 120f));
            buy.gameObject.AddComponent<UIPulse>().amount = 0.03f;

            var restore = UIKit.Button(card.transform, "Restore", Loc.T("unlock.restore"), UITheme.Paper, () =>
            {
                StoreService.Restore(ok =>
                {
                    if (Progression.SaveSystem.Data.fullGameUnlocked)
                    {
                        Object.Destroy(root);
                        if (onUnlocked != null) onUnlocked();
                    }
                    else status.text = Loc.T("unlock.nothing");
                });
            }, 30, UITheme.Ink);
            UIKit.Place((RectTransform)restore.transform, new Vector2(0f, 0f), new Vector2(40f, 40f), new Vector2(300f, 80f), Vector2.zero);
            var close = UIKit.Button(card.transform, "Close", Loc.T("settings.done"), UITheme.Paper, () => Object.Destroy(root), 30, UITheme.Ink);
            UIKit.Place((RectTransform)close.transform, new Vector2(1f, 0f), new Vector2(-40f, 40f), new Vector2(240f, 80f), new Vector2(1f, 0f));
        }
    }
}
