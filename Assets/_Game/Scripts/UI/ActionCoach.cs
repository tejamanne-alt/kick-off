using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.Challenges;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.Tutorial;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// The coach: a card at the top of the HUD, between the info card and the pause button, that says how to do what comes
    /// next, with the Controls page's picture of the control. In a story level it shows the how-to of the special action the
    /// kid is coming up to (an <see cref="ActionSpot"/> the level builder placed: slide under, chip it over the wall, wait for
    /// the green man...) from <see cref="Lead"/> before it until it is passed; once a move has been done
    /// <see cref="LearnedAfter"/> times with the ball, only its title (which names the control). In a challenge it shows the
    /// step to do now, all the way through (keepy-uppy: pop it up from KICK, then tap as it drops; the targets: aim from
    /// KICK, or fetch the ball; the slalom: keep it low under the bar, chip it through the hoop). A first-time tip
    /// (TutorialHint) shows here too, for a few seconds, when nothing else is to be said. The card takes no touches: a tap on
    /// it still touches the ball. Settings > How-to tips turns the how-tos and the steps off (the first-time tips stay).
    /// </summary>
    public class ActionCoach : MonoBehaviour
    {
        /// <summary>How far before a special action (world units) its how-to comes up.</summary>
        public const float Lead = 6f;
        /// <summary>How far past its end it stays.</summary>
        public const float Tail = 0.3f;
        /// <summary>A spot longer than this (world units) is a stretch to get along, not a move: inside it, what comes up next shows first.</summary>
        public const float LongStretch = 8f;
        /// <summary>After this many passes with the ball, a move's how-to is its title only.</summary>
        public const int LearnedAfter = 3;

        const float HintLife = 8f;
        const float HintFirst = 3f;        // a new first-time tip holds this long against a how-to that is not yet close
        const float HintGivesWay = 2.5f;   // (unless the kid is this close to the move)
        const float MinShow = 1f;          // a how-to stays at least this long before another takes its place
        const float StepSettle = 0.3f;     // a challenge's step must hold this long before the card changes to it
        const float FullHeight = 140f, CompactHeight = 84f, MaxWidth = 1000f, MinSlot = 620f, Margin = 24f;
        const float PictureWidth = 150f, PictureHeight = 112f;

        /// <summary>Set by the store screenshot tour: no coach at all.</summary>
        public static bool Suppressed;

        LevelManager level;
        KidController kid;
        BallController ball;
        StuckHelper stuck;
        RectTransform canvas, info, right;
        bool beside = true;

        RectTransform card, picture, tile;
        Text title, body;
        UIPopIn pop;
        string shown;

        ActionSpot current;
        float currentSince;
        bool lostSince;

        string hintId;
        float hintUntil = -1f, hintSince;

        string step, pendingStep;
        float pendingSince;

        static readonly Dictionary<string, int> done = new Dictionary<string, int>();
        readonly Vector3[] corners = new Vector3[4];

        /// <summary>
        /// The coach on the HUD's <paramref name="canvasRoot"/>, fitted between <paramref name="infoCard"/> (top left) and
        /// <paramref name="rightButton"/> (the pause button, top right), or under the info card where that is too narrow (and
        /// then out of the way of <paramref name="stuckHelper"/>'s button while it is up).
        /// </summary>
        public static ActionCoach Create(RectTransform canvasRoot, LevelManager level, KidController kid, BallController ball, RectTransform infoCard, RectTransform rightButton, StuckHelper stuckHelper)
        {
            var holder = UIKit.Stretch(UIKit.Rect(canvasRoot, "Coach"));
            var coach = holder.gameObject.AddComponent<ActionCoach>();
            coach.level = level;
            coach.kid = kid;
            coach.ball = ball;
            coach.canvas = canvasRoot;
            coach.info = infoCard;
            coach.right = rightButton;
            coach.stuck = stuckHelper;
            coach.Build(holder);
            if (level != null) level.BallLost += coach.OnBallLost;
            return coach;
        }

        void OnDestroy()
        {
            if (level != null) level.BallLost -= OnBallLost;
        }

        void OnBallLost(string reason) { lostSince = true; }

        /// <summary>A first-time tip (tut.&lt;id&gt;): shown for a few seconds when there is no how-to or step to show.</summary>
        public void Hint(string id)
        {
            hintId = id;
            hintSince = Time.unscaledTime;
            hintUntil = hintSince + HintLife;
        }

        void Build(RectTransform holder)
        {
            var face = UIKit.Card(holder, "Card", UITheme.Paper);
            card = (RectTransform)face.transform.parent;
            card.anchorMin = card.anchorMax = new Vector2(0f, 1f);
            card.pivot = new Vector2(0f, 1f);
            picture = UIKit.Rect(face.transform, "Picture");
            title = UIKit.Label(face.transform, "Title", "", 30, UITheme.Navy, TextAnchor.MiddleLeft, true);
            body = UIKit.Label(face.transform, "Text", "", 24, UITheme.Ink, TextAnchor.UpperLeft);
            body.resizeTextForBestFit = true;
            body.resizeTextMinSize = 17;
            body.resizeTextMaxSize = 24;
            body.verticalOverflow = VerticalWrapMode.Truncate;
            foreach (var g in card.GetComponentsInChildren<Graphic>(true)) g.raycastTarget = false;
            pop = UIKit.PopIn(card.gameObject);
            pop.duration = 0.25f;
            card.gameObject.SetActive(false);
        }

        // ---------- Per frame ----------

        void Update()
        {
            if (level == null || kid == null || ball == null) return;
            bool playing = !Suppressed && level.State == LevelState.Playing && !level.Held && !ControlsTour.Running
                && !(!beside && stuck != null && stuck.Showing);
            float x = kid.transform.position.x;
            bool tips = GameSettings.CoachTips;

            // Which move the kid is at (and whether the one before was done), even while the card is hidden.
            var spot = level.Objective == null && tips ? PickSpot(x) : null;
            if (spot != current)
            {
                if (current != null && !lostSince && x > current.toX && ball.transform.position.x > current.toX - 0.5f) Learn(current.action);
                current = spot;
                currentSince = Time.unscaledTime;
                lostSince = false;
            }

            if (!playing)
            {
                Hide();
                return;
            }

            float now = Time.unscaledTime;
            bool hint = hintId != null && now < hintUntil;
            bool freshHint = hint && now - hintSince < HintFirst && (current == null || current.fromX - x > HintGivesWay);
            CoachCatalog.Entry entry;
            if (level.Objective != null && tips && CoachCatalog.TryFind(Settle(ChallengeStep(level.Objective)), out entry))
                Show(entry, false);
            else if (current != null && !freshHint && CoachCatalog.TryFind(current.action, out entry))
                Show(entry, Learned(current.action));
            else if (hint)
                ShowHint(hintId);
            else
                Hide();
        }

        /// <summary>
        /// The special action to show: the nearest ahead within <see cref="Lead"/>, or the one the kid is in (the shorter of two);
        /// a long stretch the kid is in only when nothing else comes up.
        /// </summary>
        ActionSpot PickSpot(float x)
        {
            ActionSpot best = null;
            float bestDistance = float.MaxValue, bestLength = float.MaxValue;
            var all = ActionSpot.All;
            for (int i = 0; i < all.Count; i++)
            {
                var s = all[i];
                if (s == null || !Near(s, x)) continue;
                float distance = Mathf.Max(0f, s.fromX - x), length = s.toX - s.fromX;
                // A long stretch the kid is in (gulls all along the beach, a busy market) gives way to anything coming up.
                if (length > LongStretch && x >= s.fromX) distance = Lead;
                if (distance < bestDistance - 0.01f || (Mathf.Abs(distance - bestDistance) <= 0.01f && length < bestLength))
                {
                    best = s;
                    bestDistance = distance;
                    bestLength = length;
                }
            }
            // The one shown stays a moment, as long as the kid is still at it, so the card does not flick between two.
            if (current != null && best != current && Near(current, x) && Time.unscaledTime - currentSince < MinShow) return current;
            return best;
        }

        static bool Near(ActionSpot s, float x) { return x >= s.fromX - Lead && x <= s.toX + Tail; }

        string ChallengeStep(ChallengeObjective objective)
        {
            if (objective is JuggleChallenge) return CoachCatalog.JuggleStep(ball.IsGrounded, ball.OffsetFromFeet, ball.InKickReach);
            var slalom = objective as SlalomChallenge;
            if (slalom != null)
            {
                SlalomGate next = null;
                if (slalom.gates != null)
                    foreach (var g in slalom.gates)
                        if (g != null && !g.Done && (next == null || g.transform.position.x < next.transform.position.x)) next = g;
                return CoachCatalog.SlalomStep(next != null, next != null && next.kind == SlalomGate.Kind.Hoop);
            }
            return CoachCatalog.TargetStep(ball.InKickReach);
        }

        /// <summary>The step to show: a new one once it has held for <see cref="StepSettle"/> (the ball's bounces don't flick the card).</summary>
        string Settle(string want)
        {
            if (step == null || want == step)
            {
                step = want;
                pendingStep = null;
                return step;
            }
            if (want != pendingStep)
            {
                pendingStep = want;
                pendingSince = Time.unscaledTime;
            }
            if (Time.unscaledTime - pendingSince >= StepSettle)
            {
                step = want;
                pendingStep = null;
            }
            return step;
        }

        // ---------- Learned moves ----------

        static string Key(string action) { return "coach.done." + action; }

        static bool Learned(string action)
        {
            int count;
            if (!done.TryGetValue(action, out count))
            {
                count = PlayerPrefs.GetInt(Key(action), 0);
                done[action] = count;
            }
            return count >= LearnedAfter;
        }

        static void Learn(string action)
        {
            int count = PlayerPrefs.GetInt(Key(action), 0);
            if (count >= LearnedAfter) return;
            done[action] = count + 1;
            PlayerPrefs.SetInt(Key(action), count + 1);
            PlayerPrefs.Save();
        }

        /// <summary>Forget which moves have been learned (Settings > Reset progress): every how-to is shown in full again.</summary>
        public static void ResetLearned()
        {
            foreach (var e in CoachCatalog.Actions) PlayerPrefs.DeleteKey(Key(e.id));
            done.Clear();
        }

        // ---------- The card ----------

        void Show(CoachCatalog.Entry entry, bool compact)
        {
            string signature = entry.id + (compact ? "#" : "") + "@" + Loc.Current;
            if (signature != shown)
            {
                shown = signature;
                SetPicture(true, entry.picture);
                title.text = Loc.T(entry.TitleKey);
                body.text = compact ? "" : Loc.T(entry.TextKey);
                Arrange(compact, true);
                Appear();
            }
            Place(compact, true);
        }

        void ShowHint(string id)
        {
            string signature = "tut." + id + "@" + Loc.Current;
            ControlsGuide.Picture pic;
            bool hasPicture = CoachCatalog.HintPicture(id, out pic);
            if (signature != shown)
            {
                shown = signature;
                SetPicture(hasPicture, pic);
                title.text = "";
                body.text = Loc.T("tut." + id);
                Arrange(false, hasPicture);
                Appear();
            }
            Place(false, hasPicture);
        }

        void Appear()
        {
            card.gameObject.SetActive(true);
            pop.Play();
        }

        void Hide()
        {
            if (shown == null) return;
            shown = null;
            card.gameObject.SetActive(false);
        }

        ControlsGuide.Picture? drawn;

        void SetPicture(bool show, ControlsGuide.Picture which)
        {
            picture.gameObject.SetActive(show);
            if (!show || (drawn.HasValue && drawn.Value == which && tile != null)) return;
            if (tile != null) Destroy(tile.gameObject);
            tile = ControlsGuide.Draw(picture, which, new Vector2(PictureWidth, PictureHeight));
            foreach (var g in tile.GetComponentsInChildren<Graphic>(true)) g.raycastTarget = false;
            drawn = which;
        }

        /// <summary>Lays out the card's picture and text: in full (a title and the how-to under it) or compact (the title only).</summary>
        void Arrange(bool compact, bool hasPicture)
        {
            float height = compact ? CompactHeight : FullHeight;
            float scale = compact ? 0.62f : 1f;
            UIKit.Place(picture, new Vector2(0f, 0.5f), new Vector2(14f, 0f), new Vector2(PictureWidth, PictureHeight), new Vector2(0f, 0.5f));
            picture.localScale = Vector3.one * scale;
            float left = hasPicture ? 14f + PictureWidth * scale + 18f : 28f;
            var t = title.rectTransform;
            var b = body.rectTransform;
            t.anchorMin = new Vector2(0f, 1f);
            t.anchorMax = new Vector2(1f, 1f);
            t.pivot = new Vector2(0f, 1f);
            b.anchorMin = Vector2.zero;
            b.anchorMax = Vector2.one;
            title.gameObject.SetActive(title.text.Length > 0);
            body.gameObject.SetActive(body.text.Length > 0);
            if (compact)
            {
                t.offsetMin = new Vector2(left, -height + 10f);
                t.offsetMax = new Vector2(-22f, -10f);
            }
            else if (title.text.Length > 0)
            {
                t.offsetMin = new Vector2(left, -54f);
                t.offsetMax = new Vector2(-22f, -12f);
                b.offsetMin = new Vector2(left, 10f);
                b.offsetMax = new Vector2(-22f, -56f);
                body.alignment = TextAnchor.UpperLeft;
            }
            else
            {
                // A first-time tip: its text alone, in the middle of the card.
                b.offsetMin = new Vector2(left, 12f);
                b.offsetMax = new Vector2(-22f, -12f);
                body.alignment = TextAnchor.MiddleLeft;
            }
            UIKit.Fit(title, 22);
        }

        /// <summary>Fits the card between the info card and the pause button (or under the info card on a narrow screen).</summary>
        void Place(bool compact, bool hasPicture)
        {
            var area = canvas.rect;
            float infoRight = 0f, infoBottom = 0f, rightLeft = area.width;
            if (info != null)
            {
                info.GetWorldCorners(corners);
                infoRight = canvas.InverseTransformPoint(corners[2]).x - area.xMin;
                infoBottom = area.yMax - canvas.InverseTransformPoint(corners[0]).y;
            }
            if (right != null)
            {
                right.GetWorldCorners(corners);
                rightLeft = canvas.InverseTransformPoint(corners[0]).x - area.xMin;
            }
            float slot = rightLeft - infoRight - 2f * Margin;
            beside = slot >= MinSlot;
            float width = beside ? Mathf.Min(slot, MaxWidth) : Mathf.Min(area.width - 60f, MaxWidth);
            if (compact)
            {
                float scale = 0.62f;
                float need = (hasPicture ? 14f + PictureWidth * scale + 18f : 28f) + title.preferredWidth + 30f;
                width = Mathf.Min(width, need);
            }
            float height = compact ? CompactHeight : FullHeight;
            float x = beside ? infoRight + Margin + (slot - width) * 0.5f : 30f;
            float top = beside ? 30f : infoBottom + 14f;
            card.anchoredPosition = new Vector2(x, -top);
            card.sizeDelta = new Vector2(width, height);
        }
    }
}
