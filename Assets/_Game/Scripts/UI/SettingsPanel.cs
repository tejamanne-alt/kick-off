using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>Settings modal used by the menu and the pause screen.</summary>
    public static class SettingsPanel
    {
        public static GameObject Open(Transform canvas, System.Action onClose)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Settings", new Vector2(1250f, 900f), out root);

            var title = UIKit.Title(card.transform, "Title", Loc.T("settings.title"), 64, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -70f), new Vector2(900f, 90f));

            // Two columns: left = sound & feel, right = play & accessibility.
            float y = -170f;
            SliderRow(card.transform, new Vector2(0.27f, 1f), ref y, "settings.music", GameSettings.MusicVolume, v => GameSettings.MusicVolume = v);
            SliderRow(card.transform, new Vector2(0.27f, 1f), ref y, "settings.sfx", GameSettings.SfxVolume, v => GameSettings.SfxVolume = v);
            ToggleRow(card.transform, new Vector2(0.27f, 1f), ref y, "settings.haptics", GameSettings.HapticsEnabled, v => GameSettings.HapticsEnabled = v);
            ToggleRow(card.transform, new Vector2(0.27f, 1f), ref y, "settings.shake", GameSettings.ScreenShakeEnabled, v => GameSettings.ScreenShakeEnabled = v);

            y = -170f;
            ToggleRow(card.transform, new Vector2(0.73f, 1f), ref y, "settings.bell", GameSettings.BellTimerEnabled, v => GameSettings.BellTimerEnabled = v);
            var hint = UIKit.Label(card.transform, "BellHint", Loc.T("settings.bellHint"), 28, UITheme.InkSoft);
            UIKit.Place(hint.rectTransform, new Vector2(0.73f, 1f), new Vector2(0f, y + 30f), new Vector2(560f, 40f));
            y -= 30f;
            ToggleRow(card.transform, new Vector2(0.73f, 1f), ref y, "settings.leftHanded", GameSettings.LeftHanded, v => GameSettings.LeftHanded = v);
            ToggleRow(card.transform, new Vector2(0.73f, 1f), ref y, "settings.colorblind", GameSettings.ColorblindAim, v => GameSettings.ColorblindAim = v);

            // Language cycles through the available tables.
            var langLabel = UIKit.Label(card.transform, "LanguageLabel", Loc.T("settings.language"), 36, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(langLabel.rectTransform, new Vector2(0.73f, 1f), new Vector2(-150f, y), new Vector2(300f, 70f));
            int langIndex = Mathf.Max(0, System.Array.IndexOf(Loc.Languages, Loc.Current));
            Button lang = null;
            lang = UIKit.Button(card.transform, "Language", Loc.LanguageNames[langIndex], UITheme.Blue, () =>
            {
                int i = (System.Array.IndexOf(Loc.Languages, Loc.Current) + 1) % Loc.Languages.Length;
                Loc.SetLanguage(Loc.Languages[i]);
                Object.Destroy(root);
                Open(canvas, onClose);   // rebuild in the new language
            }, 36);
            UIKit.Place((RectTransform)lang.transform, new Vector2(0.73f, 1f), new Vector2(170f, y), new Vector2(240f, 80f));

            // Bottom row: reset (with confirmation) and done.
            var reset = UIKit.Button(card.transform, "Reset", Loc.T("settings.reset"), UITheme.Red, () => ConfirmReset(canvas), 34);
            UIKit.Place((RectTransform)reset.transform, new Vector2(0.27f, 0f), new Vector2(0f, 90f), new Vector2(380f, 100f));
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 44);
            UIKit.Place((RectTransform)done.transform, new Vector2(0.73f, 0f), new Vector2(0f, 90f), new Vector2(380f, 110f));
            return root;
        }

        static void SliderRow(Transform parent, Vector2 anchor, ref float y, string key, float value, UnityEngine.Events.UnityAction<float> onChanged)
        {
            var label = UIKit.Label(parent, key, Loc.T(key), 36, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(label.rectTransform, anchor, new Vector2(-30f, y), new Vector2(500f, 60f));
            var slider = UIKit.Slider(parent, key + ".slider", value, onChanged);
            UIKit.Place((RectTransform)slider.transform, anchor, new Vector2(-10f, y - 60f), new Vector2(520f, 70f));
            y -= 150f;
        }

        static void ToggleRow(Transform parent, Vector2 anchor, ref float y, string key, bool value, UnityEngine.Events.UnityAction<bool> onChanged)
        {
            var label = UIKit.Label(parent, key, Loc.T(key), 34, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(label.rectTransform, anchor, new Vector2(-100f, y), new Vector2(400f, 70f));
            var toggle = UIKit.Toggle(parent, key + ".toggle", value, v => Loc.T(v ? "settings.on" : "settings.off"), onChanged);
            UIKit.Place((RectTransform)toggle.transform, anchor, new Vector2(190f, y), new Vector2(160f, 76f));
            y -= 105f;
        }

        static void ConfirmReset(Transform canvas)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "ConfirmReset", new Vector2(900f, 480f), out root);
            var text = UIKit.Label(card.transform, "Text", Loc.T("settings.resetConfirm"), 40, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(text.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -150f), new Vector2(800f, 200f));
            var no = UIKit.Button(card.transform, "No", Loc.T("settings.no"), UITheme.Green, () => Object.Destroy(root), 40);
            UIKit.Place((RectTransform)no.transform, new Vector2(0.3f, 0f), new Vector2(0f, 90f), new Vector2(300f, 100f));
            var yes = UIKit.Button(card.transform, "Yes", Loc.T("settings.yes"), UITheme.Red, () =>
            {
                SaveSystem.ResetProgress();
                Tutorial.TutorialHint.ResetAll(Tutorial.TutorialHint.AllIds);
                Object.Destroy(root);
            }, 40);
            UIKit.Place((RectTransform)yes.transform, new Vector2(0.7f, 0f), new Vector2(0f, 90f), new Vector2(300f, 100f));
        }
    }
}
