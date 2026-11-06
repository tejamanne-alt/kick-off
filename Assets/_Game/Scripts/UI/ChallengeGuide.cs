using DribbleToSchool.Challenges;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// How to play a challenge (the gold "!" levels): what to do (challenge.&lt;id&gt;.goal), what each star needs (from the
    /// challenge's own thresholds), the time it has, and two or three tips on the controls for its kind (keepy-uppy, targets,
    /// the slalom), each with the Controls page's picture of the control. GameHud opens it when a challenge is first started,
    /// holding the run before its clock starts, and again from the pause menu (How to play).
    /// </summary>
    public static class ChallengeGuide
    {
        /// <summary>A tip: the control's picture and its text.</summary>
        public struct Tip
        {
            public readonly ControlsGuide.Picture picture;
            public readonly string key;

            public Tip(ControlsGuide.Picture picture, string key)
            {
                this.picture = picture;
                this.key = key;
            }
        }

        public enum Kind { Juggle, Targets, Slalom }

        /// <summary>The tips for each kind of challenge, in order.</summary>
        public static Tip[] TipsFor(Kind kind)
        {
            switch (kind)
            {
                case Kind.Juggle:
                    return new[]
                    {
                        new Tip(ControlsGuide.Picture.Kick, "guide.juggle.kick"),
                        new Tip(ControlsGuide.Picture.Touch, "guide.juggle.touch"),
                        new Tip(ControlsGuide.Picture.Walk, "guide.juggle.walk"),
                    };
                case Kind.Targets:
                    return new[]
                    {
                        new Tip(ControlsGuide.Picture.Kick, "guide.targets.kick"),
                        new Tip(ControlsGuide.Picture.Walk, "guide.targets.walk"),
                        new Tip(ControlsGuide.Picture.Jump, "guide.targets.jump"),
                    };
                default:
                    return new[]
                    {
                        new Tip(ControlsGuide.Picture.Walk, "guide.slalom.walk"),
                        new Tip(ControlsGuide.Picture.Slide, "guide.slalom.slide"),
                        new Tip(ControlsGuide.Picture.Kick, "guide.slalom.kick"),
                    };
            }
        }

        public static Kind KindOf(ChallengeObjective objective)
        {
            if (objective is JuggleChallenge) return Kind.Juggle;
            if (objective is SlalomChallenge) return Kind.Slalom;
            return Kind.Targets;
        }

        /// <summary>Every key the guide uses besides the challenges' goals (challenge.C0n.goal) and tips.</summary>
        public static readonly string[] OtherKeys = { "challenge.howTo", "challenge.timeLimit", "challenge.noLimit", "challenge.missed", "tour.go", "results.reach", "results.under" };

        const float RowHeight = 108f, RowGap = 8f;

        /// <summary>
        /// Opens the guide for <paramref name="objective"/> (in the level <paramref name="levelId"/>) over <paramref name="canvas"/>.
        /// With <paramref name="hold"/>, the run waits (LevelManager.Hold) until the guide is closed.
        /// </summary>
        public static GameObject Open(Transform canvas, ChallengeObjective objective, string levelId, LevelManager hold, System.Action onClose)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "ChallengeGuide", new Vector2(1240f, 980f), out root);
            root.AddComponent<UIInputBlocker>();
            string title = Loc.T("level." + levelId, objective != null ? objective.challengeName : levelId);
            UIKit.Header(card.transform, title, 700f);
            var t = card.transform;

            // What to do.
            var sub = UIKit.Label(t, "HowTo", Loc.T("challenge.howTo").ToUpperInvariant(), 28, UITheme.Accent, TextAnchor.MiddleCenter, true);
            UIKit.Place(sub.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -86f), new Vector2(1100f, 40f));
            var goal = UIKit.Label(t, "Goal", Loc.T("challenge." + levelId + ".goal", objective != null ? objective.instructions : ""), 34, UITheme.Ink, TextAnchor.UpperCenter, true);
            UIKit.Place(goal.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -160f), new Vector2(1120f, 100f));
            goal.resizeTextForBestFit = true;
            goal.resizeTextMinSize = 24;
            goal.resizeTextMaxSize = 34;
            goal.verticalOverflow = VerticalWrapMode.Truncate;

            // The stars and the clock.
            if (objective != null)
            {
                var starsRow = UIKit.Rect(t, "Stars");
                UIKit.Place(starsRow, new Vector2(0.5f, 1f), new Vector2(0f, -250f), new Vector2(1120f, 60f));
                for (int i = 0; i < 3 && i < objective.starThresholds.Length; i++)
                {
                    var cell = UIKit.Rect(starsRow, "Star" + (i + 1));
                    cell.anchorMin = new Vector2(i / 3f, 0f);
                    cell.anchorMax = new Vector2((i + 1) / 3f, 1f);
                    cell.offsetMin = cell.offsetMax = Vector2.zero;
                    var row = UIKit.Stars(cell, "Icons", i + 1, 30f, 2f);
                    UIKit.Place(row, new Vector2(0.5f, 0.5f), new Vector2(-row.sizeDelta.x * 0.5f - 6f, 0f), row.sizeDelta, new Vector2(0.5f, 0.5f));
                    string need = Loc.F(objective.lowerIsBetter ? "results.under" : "results.reach", objective.FormatScore(objective.starThresholds[i]));
                    var text = UIKit.Label(cell, "Need", need, 28, UITheme.Ink, TextAnchor.MiddleLeft, true);
                    UIKit.Place(text.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(110f, 0f), new Vector2(220f, 50f), new Vector2(0.5f, 0.5f));
                    UIKit.Fit(text, 20);
                }
                var slalom = objective as SlalomChallenge;
                string clock = objective.timeLimit > 0f ? Loc.F("challenge.timeLimit", Mathf.RoundToInt(objective.timeLimit)) : Loc.T("challenge.noLimit");
                if (slalom != null) clock += "  " + Loc.F("challenge.missed", Mathf.RoundToInt(slalom.missPenalty));
                var time = UIKit.Label(t, "Clock", clock, 27, UITheme.InkSoft, TextAnchor.MiddleCenter);
                UIKit.Place(time.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -305f), new Vector2(1120f, 40f));
                UIKit.Fit(time, 20);
            }

            // The tips: the control's picture, and what to do with it here.
            var list = UIKit.Rect(t, "Tips");
            list.anchorMin = Vector2.zero;
            list.anchorMax = Vector2.one;
            list.offsetMin = new Vector2(60f, 170f);
            list.offsetMax = new Vector2(-60f, -362f);
            float y = 0f;
            foreach (var tip in TipsFor(KindOf(objective)))
            {
                var row = UIKit.Row(list, tip.key, y, RowHeight);
                ControlsGuide.Draw(row, tip.picture);
                var text = UIKit.Label(row, "Text", Loc.T(tip.key), 29, UITheme.Ink, TextAnchor.MiddleLeft);
                text.rectTransform.anchorMin = Vector2.zero;
                text.rectTransform.anchorMax = Vector2.one;
                text.rectTransform.offsetMin = new Vector2(200f, 0f);
                text.rectTransform.offsetMax = Vector2.zero;
                text.resizeTextForBestFit = true;
                text.resizeTextMinSize = 20;
                text.resizeTextMaxSize = 29;
                text.verticalOverflow = VerticalWrapMode.Truncate;
                y += RowHeight + RowGap;
            }

            if (hold != null) hold.Hold(true);
            bool closed = false;
            System.Action close = () =>
            {
                if (closed) return;
                closed = true;
                if (hold != null) hold.Hold(false);
                Object.Destroy(root);
                if (onClose != null) onClose();
            };
            var go = UIKit.Button(t, "Go", Loc.T("tour.go"), UITheme.Green, () => close(), 44);
            UIKit.Place((RectTransform)go.transform, new Vector2(0.5f, 0f), new Vector2(0f, 90f), new Vector2(420f, 108f));
            return root;
        }
    }
}
