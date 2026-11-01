using System.Collections;
using System.Collections.Generic;
using DribbleToSchool.Audio;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// The Holiday Run's two menus, opened by HolidayRunHud: the pause menu, and the results that follow a
    /// crash (score, distance, coins, how far the run got, the three missions with this run counted in, and
    /// the way on: revive, run again, home). Like the story levels' menus they are modals of the HUD's
    /// canvas, at a fixed size inside the 1080-tall canvas, so they fit from 4:3 to 21:9.
    /// </summary>
    public static class HolidayRunPanels
    {
        static readonly Vector2 TopLeft = new Vector2(0f, 1f);
        static readonly Color PanelTint = new Color(0.84f, 0.89f, 0.97f, 0.55f);
        static readonly Color DoneTint = new Color(0.78f, 0.95f, 0.82f);
        static readonly Color CrashRed = new Color(0.85f, 0.33f, 0.3f);
        static readonly Color CoinGold = new Color(0.8f, 0.52f, 0.06f);
        static readonly Color DoneGreen = new Color(0.16f, 0.55f, 0.3f);

        /// <summary>Most chimes the results play, so a long list of good news doesn't turn into a tune.</summary>
        const int MaxChimes = 5;

        // ================================================================ pause

        /// <summary>The pause menu: resume, restart the run, settings, and back to the title screen.</summary>
        public static GameObject OpenPause(Transform canvas, HolidayRunDirector director)
        {
            GameObject root;
            var card = UIKit.Modal(canvas, "Pause", new Vector2(720f, 700f), out root);
            UIKit.Header(card.transform, Loc.T("pause.title"), 460f);

            float y = -200f;
            PauseButton(card.transform, ref y, "pause.resume", UITheme.Green, director.TogglePause);
            PauseButton(card.transform, ref y, "holiday.pause.restart", UITheme.Accent, director.Restart);
            PauseButton(card.transform, ref y, "pause.settings", new Color(0.6f, 0.5f, 0.8f), () => SettingsPanel.Open(canvas, null));
            PauseButton(card.transform, ref y, "holiday.pause.quit", UITheme.Red, director.QuitToMenu);
            return root;
        }

        static void PauseButton(Transform parent, ref float y, string key, Color color, UnityAction action)
        {
            var b = UIKit.Button(parent, key, Loc.T(key), color, action, 40);
            UIKit.Place((RectTransform)b.transform, new Vector2(0.5f, 1f), new Vector2(0f, y), new Vector2(520f, 100f));
            y -= 120f;
        }

        // ================================================================ results

        /// <summary>
        /// The results menu for the run that just ended (director.Result). <paramref name="chimes"/> is how many
        /// good-news chimes to play with it (a new best, a finished mission): hand it to <see cref="Chimes"/>
        /// along with the returned menu.
        /// </summary>
        public static GameObject OpenResults(Transform canvas, HolidayRunDirector director, out int chimes)
        {
            var r = director.Result;
            GameObject root;
            var card = UIKit.Modal(canvas, "HolidayResults", new Vector2(1340f, 980f), out root);
            var t = card.transform;
            UIKit.Header(t, Loc.T("holiday.results.title"), 640f);

            // What ended the run.
            string reason = Loc.T(r.reason);
            if (reason.Length > 0)
            {
                var line = UIKit.Label(t, "Reason", reason, 40, CrashRed, TextAnchor.MiddleCenter, true);
                UIKit.Place(line.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -104f), new Vector2(700f, 56f), new Vector2(0.5f, 0.5f));
                UIKit.Fit(line, 26);
            }

            Wallet(t);
            int good = Stats(t, r);
            good += Missions(t, r);
            Buttons(t, director);
            chimes = Mathf.Min(good, MaxChimes);
            return root;
        }

        /// <summary>The coins in the bank, top right: what the revive is paid from. (This run's coins are banked when the results are left.)</summary>
        static void Wallet(Transform card)
        {
            var face = UIKit.Card(card, "Wallet", UITheme.Paper);
            UIKit.Place((RectTransform)face.transform.parent, new Vector2(1f, 1f), new Vector2(-48f, -76f), new Vector2(236f, 66f), new Vector2(1f, 1f));
            var coins = UIKit.CoinAmount(face.transform, "Coins", 0, 42, UITheme.Ink);
            UIKit.Stretch((RectTransform)coins.transform.parent, 8f);
            coins.text = Num(SaveSystem.Data.coins);
        }

        /// <summary>The left panel: the score, the distance, the coins and how far the run got. Returns the number of new bests in it.</summary>
        static int Stats(Transform card, RunResult r)
        {
            var panel = UIKit.Panel(card, "Stats", PanelTint, ProceduralSprites.RoundedSmall);
            UIKit.Place(panel.rectTransform, TopLeft, new Vector2(48f, -160f), new Vector2(620f, 600f), TopLeft);
            panel.raycastTarget = false;
            UIKit.PopIn(panel.gameObject, 0.1f);
            var t = panel.transform;
            int good = 0;

            var caption = UIKit.Label(t, "ScoreCaption", Loc.T("holiday.results.score"), 28, UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(caption.rectTransform, TopLeft, new Vector2(28f, -16f), new Vector2(300f, 38f), TopLeft);

            // The score is the big number; its size follows how many digits it will end up with.
            int digits = r.score.ToString().Length;
            var score = UIKit.Label(t, "Score", "0", digits <= 7 ? 128 : 100, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(score.rectTransform, TopLeft, new Vector2(28f, -52f), new Vector2(564f, 140f), TopLeft);
            CountUp(score, r.score, "{0:N0}", 0.45f, 1f);
            if (r.newBestScore)
            {
                NewBest(t, new Vector2(1f, 1f), new Vector2(-24f, -20f), new Vector2(240f, 56f), 30, 1.2f);
                good++;
            }

            Divider(t, -206f);
            Row(t, -214f, "holiday.results.distance");
            var distance = Value(t, -214f, "Distance");
            CountUp(distance, r.distance, "{0:N0} m", 0.65f, 0.9f);
            if (r.newBestDistance)
            {
                NewBest(t, TopLeft, new Vector2(190f, -230f), new Vector2(160f, 40f), 22, 1.4f);
                good++;
            }

            Divider(t, -298f);
            Row(t, -306f, "holiday.results.coins");
            var coins = UIKit.CoinAmount(t, "CoinsValue", 0, 46, UITheme.Ink);
            var coinRow = (RectTransform)coins.transform.parent;
            UIKit.Place(coinRow, new Vector2(1f, 1f), new Vector2(-28f, -306f), new Vector2(300f, 80f), new Vector2(1f, 1f));
            coinRow.GetComponent<HorizontalLayoutGroup>().childAlignment = TextAnchor.MiddleRight;
            CountUp(coins, r.coins, "+{0:N0}", 0.85f, 0.8f);

            Divider(t, -390f);
            var stage = HolidayStages.All[Mathf.Clamp(r.stage, 0, HolidayStages.Count - 1)];
            string reached = Loc.F("holiday.reached", Mathf.Clamp(r.stage, 0, HolidayStages.Count - 1) + 1, Loc.T("level." + stage.levelId), Mathf.Max(1, r.day));
            var where = UIKit.Label(t, "Reached", reached, 34, UITheme.Ink, TextAnchor.MiddleLeft, false);
            UIKit.Place(where.rectTransform, TopLeft, new Vector2(28f, -404f), new Vector2(564f, 140f), TopLeft);
            UIKit.Fit(where, 22);
            return good;
        }

        /// <summary>The right panel: the active missions with this run counted in, the finished ones lit up. Returns how many finished.</summary>
        static int Missions(Transform card, RunResult r)
        {
            var panel = UIKit.Panel(card, "Missions", PanelTint, ProceduralSprites.RoundedSmall);
            UIKit.Place(panel.rectTransform, TopLeft, new Vector2(692f, -160f), new Vector2(600f, 600f), TopLeft);
            panel.raycastTarget = false;
            UIKit.PopIn(panel.gameObject, 0.2f);
            var title = UIKit.Row(panel.transform, "Title", 14f, 46f, 16f, 16f);
            UIKit.SectionLabel(title, Loc.T("holiday.missions"));

            // A damaged save must not keep the player from the buttons below: no missions, then.
            IList<MissionView> missions;
            try
            {
                missions = HolidayMissions.Preview(r.stats);
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Holiday Run] Could not read the missions: " + e.Message);
                missions = new List<MissionView>();
            }

            int done = 0;
            for (int i = 0; i < missions.Count && i < HolidayMissions.ActiveCount; i++)
            {
                MissionRow(panel.transform, missions[i], 74f + i * 172f, 0.55f + i * 0.15f);
                if (missions[i].done) done++;
            }
            return done;
        }

        /// <summary>One mission: what it asks, a bar for how far it has got, and what it pays; lit green once this run finished it.</summary>
        static void MissionRow(Transform parent, MissionView m, float top, float delay)
        {
            var holder = UIKit.Rect(parent, "Mission_" + m.id);
            UIKit.Place(holder, TopLeft, new Vector2(16f, -top), new Vector2(568f, 156f), TopLeft);
            UIKit.PopIn(holder.gameObject, delay);
            var back = UIKit.Panel(holder, "Back", m.done ? DoneTint : UITheme.Paper, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Stretch(back.rectTransform);
            back.raycastTarget = false;

            var text = UIKit.Label(holder, "Text", m.text, 32, UITheme.Ink, TextAnchor.MiddleLeft, false);
            UIKit.Place(text.rectTransform, TopLeft, new Vector2(20f, -12f), new Vector2(358f, 82f), TopLeft);
            UIKit.Fit(text, 20);

            // The reward, top right: gold until the mission is done, then green and breathing.
            var reward = UIKit.CoinAmount(holder, "Reward", 0, 36, m.done ? DoneGreen : CoinGold);
            reward.text = "+" + m.reward;
            var rewardRow = (RectTransform)reward.transform.parent;
            UIKit.Place(rewardRow, new Vector2(1f, 1f), new Vector2(-18f, -16f), new Vector2(150f, 50f), new Vector2(1f, 1f));
            rewardRow.GetComponent<HorizontalLayoutGroup>().childAlignment = TextAnchor.MiddleRight;
            if (m.done) rewardRow.gameObject.AddComponent<UIPulse>().amount = 0.06f;

            // The bar, and beside it the count (or a cheer).
            var track = UIKit.Panel(holder, "Track", UITheme.PaperDark, ProceduralSprites.RoundedSmall);
            UIKit.Place(track.rectTransform, new Vector2(0f, 0f), new Vector2(20f, 22f), new Vector2(346f, 26f), Vector2.zero);
            track.raycastTarget = false;
            float fraction = m.target > 0 ? Mathf.Clamp01(m.progress / (float)m.target) : 0f;
            if (fraction > 0.005f)
            {
                var fill = UIKit.Panel(track.transform, "Fill", m.done ? UITheme.Green : UITheme.Blue, ProceduralSprites.RoundedSmall);
                fill.rectTransform.anchorMin = Vector2.zero;
                fill.rectTransform.anchorMax = new Vector2(fraction, 1f);
                fill.rectTransform.offsetMin = fill.rectTransform.offsetMax = Vector2.zero;
                fill.raycastTarget = false;
            }
            var count = UIKit.Label(holder, "Count", m.done ? Loc.T("holiday.missionDone") : Num(m.progress) + " / " + Num(m.target),
                m.done ? 30 : 28, m.done ? DoneGreen : UITheme.InkSoft, TextAnchor.MiddleRight, true);
            UIKit.Place(count.rectTransform, new Vector2(1f, 0f), new Vector2(-18f, 16f), new Vector2(170f, 38f), new Vector2(1f, 0f));
            UIKit.Fit(count, 18);
        }

        /// <summary>
        /// Revive (when the run allows another, greyed if the bank is short), run again, home. Each sits in a
        /// holder that pops in, because a button's own scale belongs to its press animation.
        /// </summary>
        static void Buttons(Transform card, HolidayRunDirector director)
        {
            bool revive = director.CanRevive;
            float again = revive ? 0f : -215f, home = revive ? 445f : 260f;

            if (revive)
            {
                int cost = director.ReviveCost;
                bool affordable = SaveSystem.Data.coins >= cost;
                var slot = Slot(card, "ReviveSlot", -445f, new Vector2(390f, 124f), 0.9f);
                var button = UIKit.Button(slot, "Revive", "", affordable ? UITheme.Green : UITheme.Locked, director.Revive);
                UIKit.Stretch((RectTransform)button.transform);
                button.interactable = affordable;
                var face = button.transform.Find("Face");
                Color ink = affordable ? Color.white : new Color(0.3f, 0.33f, 0.42f);
                var label = UIKit.Label(face, "Label", Loc.T("holiday.revive"), 46, ink, TextAnchor.MiddleCenter, true);
                label.rectTransform.anchorMin = new Vector2(0f, 0.44f);
                label.rectTransform.anchorMax = Vector2.one;
                label.rectTransform.offsetMin = new Vector2(12f, 0f);
                label.rectTransform.offsetMax = new Vector2(-12f, -6f);
                UIKit.Fit(label, 28);
                var price = UIKit.CoinAmount(face, "Price", cost, 36, ink);
                UIKit.Place((RectTransform)price.transform.parent, new Vector2(0.5f, 0f), new Vector2(0f, 9f), new Vector2(240f, 46f), new Vector2(0.5f, 0f));
            }

            var runSlot = Slot(card, "RunAgainSlot", again, new Vector2(revive ? 420f : 480f, 130f), 1f);
            var run = UIKit.Button(runSlot, "RunAgain", Loc.T("holiday.runAgain"), UITheme.Accent, director.Restart, 48);
            UIKit.Stretch((RectTransform)run.transform);
            run.gameObject.AddComponent<UIPulse>().amount = 0.035f;

            var homeSlot = Slot(card, "HomeSlot", home, new Vector2(390f, 112f), 1.1f);
            var back = UIKit.Button(homeSlot, "Home", Loc.T("holiday.home"), UITheme.Paper, director.QuitToMenu, 44, UITheme.Ink);
            UIKit.Stretch((RectTransform)back.transform);
        }

        static RectTransform Slot(Transform card, string name, float x, Vector2 size, float delay)
        {
            var slot = UIKit.Rect(card, name);
            UIKit.Place(slot, new Vector2(0.5f, 0f), new Vector2(x, 56f), size, new Vector2(0.5f, 0f));
            UIKit.PopIn(slot.gameObject, delay);
            return slot;
        }

        // ================================================================ pieces

        /// <summary>A stat's name, on the left of its row.</summary>
        static Text Row(Transform parent, float top, string labelKey)
        {
            var label = UIKit.Label(parent, labelKey, Loc.T(labelKey), 30, UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(label.rectTransform, TopLeft, new Vector2(28f, top), new Vector2(160f, 80f), TopLeft);
            UIKit.Fit(label, 18);
            return label;
        }

        /// <summary>A stat's number, on the right of its row.</summary>
        static Text Value(Transform parent, float top, string name)
        {
            var value = UIKit.Label(parent, name, "", 52, UITheme.Ink, TextAnchor.MiddleRight, true);
            UIKit.Place(value.rectTransform, new Vector2(1f, 1f), new Vector2(-28f, top), new Vector2(330f, 80f), new Vector2(1f, 1f));
            return value;
        }

        static void Divider(Transform parent, float top)
        {
            // A flat line: a rounded, sliced sprite would squash at three pixels high.
            var line = UIKit.Icon(parent, "Divider", null, new Color(0.11f, 0.13f, 0.2f, 0.1f), 3f);
            UIKit.Place(line.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, top), new Vector2(564f, 3f), new Vector2(0.5f, 1f));
        }

        /// <summary>
        /// A gold "NEW BEST!" sticker, tilted, that pops in late and then pulses. The pulse sits on the chip and
        /// the pop on the holder around it, as both set the scale.
        /// </summary>
        static void NewBest(Transform parent, Vector2 anchor, Vector2 position, Vector2 size, int fontSize, float delay)
        {
            var holder = UIKit.Rect(parent, "NewBest");
            UIKit.Place(holder, anchor, position, size, anchor);
            holder.localRotation = Quaternion.Euler(0f, 0f, 4f);
            UIKit.PopIn(holder.gameObject, delay).fromScale = 1.8f;
            var chip = UIKit.Panel(holder, "Chip", UITheme.Gold, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Stretch(chip.rectTransform);
            chip.raycastTarget = false;
            var label = UIKit.Label(chip.transform, "Text", Loc.T("holiday.newBest"), fontSize, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(label.rectTransform, 4f);
            UIKit.Fit(label, fontSize / 2);
            var pulse = chip.gameObject.AddComponent<UIPulse>();
            pulse.amount = 0.05f;
            pulse.speed = 5f;
        }

        static void CountUp(Text text, int target, string format, float delay, float duration)
        {
            var count = text.gameObject.AddComponent<UICountUp>();
            count.target = target;
            count.format = format;
            count.delay = delay;
            count.duration = duration;
            text.text = string.Format(format, 0);   // UICountUp starts from its default format for a frame otherwise
        }

        static string Num(int n)
        {
            return n.ToString("N0");
        }

        /// <summary>
        /// The chimes that go with the results, one after another, a little higher each time (like the story levels'
        /// stars). They stop if the results are left before they are done.
        /// </summary>
        public static IEnumerator Chimes(GameObject results, int count)
        {
            for (int i = 0; i < count; i++)
            {
                float until = Time.unscaledTime + (i == 0 ? 0.6f : 0.35f);
                while (Time.unscaledTime < until) yield return null;
                if (results == null) yield break;
                AudioDirector.Play(Sfx.Perfect, 0.8f, 1f + i * 0.2f);
                Haptics.Impact(Haptics.Strength.Light);
            }
        }
    }
}
