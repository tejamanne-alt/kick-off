using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Settings modal used by the menu and the pause screen. Two columns of grouped rows, laid
    /// out top-down from fixed row heights inside columns that stretch with the card, so
    /// nothing overlaps at any aspect ratio (the card fits a 4:3 canvas, 1440 x 1080):
    /// left, Audio (music, ambience: the sounds of each place, sound effects) and Gameplay (school bell,
    /// colour-blind aim, vibration, screen shake, the coach's how-to tips: UI/ActionCoach); right, Player (the chosen kid, which opens the
    /// player picker), Language and Controls (left-handed, and the Controls page: UI/ControlsGuide); along the bottom, Reset progress, Restore purchases and Done. Labels shrink
    /// to fit rather than run into their controls, for longer translations.
    /// </summary>
    public static class SettingsPanel
    {
        const float RowHeight = 66f;
        const float RowGap = 7f;
        const float SectionHeight = 46f;
        const float ToggleWidth = 150f;

        public static GameObject Open(Transform canvas, System.Action onClose)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Settings", new Vector2(1340f, 960f), out root);
            UIKit.Header(card.transform, Loc.T("settings.title"), 520f);

            var left = Column(card.transform, "Left", 0f, 0.55f, 50f, 20f);
            var right = Column(card.transform, "Right", 0.55f, 1f, 20f, 50f);

            // Audio
            float y = 0f;
            Section(left, ref y, "settings.audio");
            SliderRow(left, ref y, "settings.music", GameSettings.MusicVolume, v => GameSettings.MusicVolume = v);
            SliderRow(left, ref y, "settings.ambience", GameSettings.AmbienceVolume, v => GameSettings.AmbienceVolume = v);
            SliderRow(left, ref y, "settings.sfx", GameSettings.SfxVolume, v => GameSettings.SfxVolume = v);
            y += 6f;

            // Gameplay
            Section(left, ref y, "settings.gameplay");
            ToggleRow(left, ref y, "settings.bell", GameSettings.BellTimerEnabled, v => GameSettings.BellTimerEnabled = v, "settings.bellHint");
            ToggleRow(left, ref y, "settings.colorblind", GameSettings.ColorblindAim, v => GameSettings.ColorblindAim = v);
            ToggleRow(left, ref y, "settings.haptics", GameSettings.HapticsEnabled, v => GameSettings.HapticsEnabled = v);
            ToggleRow(left, ref y, "settings.shake", GameSettings.ScreenShakeEnabled, v => GameSettings.ScreenShakeEnabled = v);
            ToggleRow(left, ref y, "settings.coachTips", GameSettings.CoachTips, v => GameSettings.CoachTips = v);

            // Player: who walks to school.
            y = 0f;
            Section(right, ref y, "settings.player");
            var player = UIKit.Row(right, "PlayerSummary", y, 200f, 4f, 4f);
            PlayerPicker.Summary(player, canvas);
            y += 200f + 22f;

            // Language: one button per table; the current one is filled.
            Section(right, ref y, "settings.language");
            var languages = UIKit.Row(right, "Languages", y, 84f, 4f, 4f);
            int count = Loc.Languages.Length;
            for (int i = 0; i < count; i++)
            {
                string code = Loc.Languages[i];
                bool current = code == Loc.Current;
                var lang = UIKit.Button(languages, "Language_" + code, Loc.LanguageNames[i], current ? UITheme.Blue : UITheme.Paper, () =>
                {
                    if (code == Loc.Current) return;
                    Loc.SetLanguage(code);
                    Object.Destroy(root);
                    Open(canvas, onClose);   // rebuild in the new language
                }, 36, current ? Color.white : UITheme.Ink);
                var rt = (RectTransform)lang.transform;
                rt.anchorMin = new Vector2(i / (float)count, 0f);
                rt.anchorMax = new Vector2((i + 1) / (float)count, 1f);
                rt.offsetMin = new Vector2(i == 0 ? 0f : 10f, UIButtonFx.Depth);
                rt.offsetMax = new Vector2(i == count - 1 ? 0f : -10f, 0f);
            }
            y += 84f + 22f;

            // Controls: which hand has the stick and which the buttons, and the page that says what each one does.
            Section(right, ref y, "settings.controls");
            ToggleRow(right, ref y, "settings.leftHanded", GameSettings.LeftHanded, v => GameSettings.LeftHanded = v);
            var guideRow = UIKit.Row(right, "ControlsGuide", y, RowHeight, 4f, 4f);
            var guide = UIKit.Button(guideRow, "Open", Loc.T("settings.controlsGuide"), new Color(0.25f, 0.62f, 0.7f), () => ControlsGuide.Open(canvas, null), 32);
            UIKit.Stretch((RectTransform)guide.transform);
            ((RectTransform)guide.transform).offsetMin = new Vector2(0f, UIButtonFx.Depth);
            y += RowHeight + RowGap;

            // Bottom row: reset (with confirmation), restore purchases, done.
            var reset = UIKit.Button(card.transform, "Reset", Loc.T("settings.reset"), UITheme.Red, () => ConfirmReset(canvas), 34);
            UIKit.Place((RectTransform)reset.transform, Vector2.zero, new Vector2(50f, 44f), new Vector2(330f, 96f), Vector2.zero);
            if (Store.Monetization.RequireUnlock)
            {
                var restore = UIKit.Button(card.transform, "Restore", Loc.T("unlock.restore"), UITheme.Paper, () => Store.StoreService.Restore(null), 30, UITheme.Ink);
                UIKit.Place((RectTransform)restore.transform, new Vector2(0.5f, 0f), new Vector2(-10f, 44f), new Vector2(300f, 96f), new Vector2(0.5f, 0f));
            }
            var done = UIKit.Button(card.transform, "Done", Loc.T("settings.done"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (onClose != null) onClose();
            }, 46);
            UIKit.Place((RectTransform)done.transform, new Vector2(1f, 0f), new Vector2(-50f, 40f), new Vector2(340f, 106f), new Vector2(1f, 0f));
            return root;
        }

        /// <summary>A column of the card between two horizontal anchors, below the header and above the bottom row.</summary>
        static RectTransform Column(Transform card, string name, float from, float to, float padLeft, float padRight)
        {
            var col = UIKit.Rect(card, name);
            col.anchorMin = new Vector2(from, 0f);
            col.anchorMax = new Vector2(to, 1f);
            col.offsetMin = new Vector2(padLeft, 160f);
            col.offsetMax = new Vector2(-padRight, -76f);
            return col;
        }

        static void Section(RectTransform column, ref float y, string key)
        {
            var row = UIKit.Row(column, key, y, SectionHeight);
            UIKit.SectionLabel(row, Loc.T(key));
            y += SectionHeight + RowGap;
        }

        static void SliderRow(RectTransform column, ref float y, string key, float value, UnityEngine.Events.UnityAction<float> onChanged)
        {
            var row = UIKit.Row(column, key, y, RowHeight, 12f, 0f);
            var label = UIKit.Label(row, "Label", Loc.T(key), 34, UITheme.Ink, TextAnchor.MiddleLeft, true);
            label.rectTransform.anchorMin = new Vector2(0f, 0f);
            label.rectTransform.anchorMax = new Vector2(0f, 1f);
            label.rectTransform.pivot = new Vector2(0f, 0.5f);
            label.rectTransform.sizeDelta = new Vector2(240f, 0f);
            label.rectTransform.anchoredPosition = Vector2.zero;
            UIKit.Fit(label, 24);
            var slider = UIKit.Slider(row, "Slider", value, onChanged);
            var rt = (RectTransform)slider.transform;
            rt.anchorMin = new Vector2(0f, 0.5f);
            rt.anchorMax = new Vector2(1f, 0.5f);
            rt.offsetMin = new Vector2(256f, -32f);
            rt.offsetMax = new Vector2(-6f, 32f);
            y += RowHeight + RowGap;
        }

        /// <summary>A label (and an optional hint under it) on the left, the On/Off pill on the right.</summary>
        static void ToggleRow(RectTransform column, ref float y, string key, bool value, UnityEngine.Events.UnityAction<bool> onChanged, string hintKey = null)
        {
            float height = hintKey != null ? RowHeight + 22f : RowHeight;
            var row = UIKit.Row(column, key, y, height, 12f, 0f);
            var label = UIKit.Label(row, "Label", Loc.T(key), 34, UITheme.Ink, TextAnchor.MiddleLeft, true);
            label.rectTransform.anchorMin = new Vector2(0f, hintKey != null ? 0.42f : 0f);
            label.rectTransform.anchorMax = Vector2.one;
            label.rectTransform.offsetMin = Vector2.zero;
            label.rectTransform.offsetMax = new Vector2(-(ToggleWidth + 24f), 0f);
            UIKit.Fit(label, 24);
            if (hintKey != null)
            {
                var hint = UIKit.Label(row, "Hint", Loc.T(hintKey), 25, UITheme.InkSoft, TextAnchor.UpperLeft);
                hint.rectTransform.anchorMin = Vector2.zero;
                hint.rectTransform.anchorMax = new Vector2(1f, 0.42f);
                hint.rectTransform.offsetMin = Vector2.zero;
                hint.rectTransform.offsetMax = new Vector2(-(ToggleWidth + 24f), 0f);
                UIKit.Fit(hint, 18);
            }
            var toggle = UIKit.Toggle(row, "Toggle", value, v => Loc.T(v ? "settings.on" : "settings.off"), onChanged);
            UIKit.Place((RectTransform)toggle.transform, new Vector2(1f, 0.5f), new Vector2(-6f, UIButtonFx.Depth * 0.5f), new Vector2(ToggleWidth, 60f), new Vector2(1f, 0.5f));
            y += height + RowGap;
        }

        static void ConfirmReset(Transform canvas)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "ConfirmReset", new Vector2(900f, 500f), out root);
            UIKit.Header(card.transform, Loc.T("settings.reset"), 520f);
            var text = UIKit.Label(card.transform, "Text", Loc.T("settings.resetConfirm"), 40, UITheme.Ink, TextAnchor.MiddleCenter, true);
            text.rectTransform.anchorMin = Vector2.zero;
            text.rectTransform.anchorMax = Vector2.one;
            text.rectTransform.offsetMin = new Vector2(60f, 170f);
            text.rectTransform.offsetMax = new Vector2(-60f, -70f);
            UIKit.Fit(text, 28);
            var no = UIKit.Button(card.transform, "No", Loc.T("settings.no"), UITheme.Green, () => Object.Destroy(root), 40);
            UIKit.Place((RectTransform)no.transform, new Vector2(0.3f, 0f), new Vector2(0f, 95f), new Vector2(300f, 100f));
            var yes = UIKit.Button(card.transform, "Yes", Loc.T("settings.yes"), UITheme.Red, () =>
            {
                SaveSystem.ResetProgress();
                Tutorial.TutorialHint.ResetAll(Tutorial.TutorialHint.AllIds);
                ActionCoach.ResetLearned();
                Object.Destroy(root);
            }, 40);
            UIKit.Place((RectTransform)yes.transform, new Vector2(0.7f, 0f), new Vector2(0f, 95f), new Vector2(300f, 100f));
        }
    }
}
