using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// The race's screen over the level's own HUD (Coop/CoopLevelLink makes it each leg): the standings under the pause button
    /// (each player's colour, place or position, "Name #TAG", how far along the route on a thin bar, and their time or what
    /// they are doing), a banner while this phone is out of touch (Bluetooth off, out of range: how long before the others
    /// list it last, and once they do, that its run counts again as soon as it is back), a short feed of what happens to the others (got to school, lost the connection, back,
    /// out, a new host), name tags over the ghosts (at the screen's edge with their distance when they are out of view), the
    /// stop's message between two legs, and the standings card at the school gate. In the editor a row of buttons tries the
    /// resilience: a bot walks out of range, comes back, the bot host leaves, this phone's Bluetooth goes off.
    /// </summary>
    public class CoopHud : MonoBehaviour
    {
        const float RowHeight = 54f, CardWidth = 430f, NarrowCardWidth = 360f;

        CoopService service;
        CoopRaceMode race;
        CoopLevelLink link;
        RectTransform root, card, feed, tagLayer;
        Text banner, bigStop, smallStop;
        Image bannerGlass, fade;
        readonly List<Row> rows = new List<Row>();
        readonly List<Tag> tags = new List<Tag>();
        readonly List<FeedLine> lines = new List<FeedLine>();
        GameObject results;
        Text resultsHeading, resultsSub;
        RectTransform resultsBody;
        float nextRefresh, nextResultsRefresh;
        bool resultsShownForFinish;
        int resultsSignature;
        Camera cam;

        sealed class Row
        {
            public RectTransform rt;
            public Image dot, barFill;
            public Text number, name, tag, state;
            // What the name label was last made from (a new string only when it changes).
            public uint uid;
            public string shownName;
            public bool shownBold;
        }

        sealed class Tag
        {
            public RectTransform rt;
            public Text text;
            public uint uid;
            public string fullName;
        }

        sealed class FeedLine
        {
            public Text text;
            public float until;
        }

        public void Attach(CoopService service, CoopRaceMode race, CoopLevelLink link)
        {
            this.service = service;
            this.race = race;
            this.link = link;
            Build();
            service.Noticed += OnNotice;
        }

        void OnDestroy()
        {
            if (service != null) service.Noticed -= OnNotice;
        }

        CoopSession Session { get { return service.Session; } }

        // ---------- Build ----------

        void Build()
        {
            var canvas = UIKit.CreateCanvas("CoopHUD", 11);
            canvas.transform.SetParent(transform, false);
            root = (RectTransform)canvas.transform;
            float aspect = Screen.height > 0 ? (float)Screen.width / Screen.height : 16f / 9f;
            float width = UIKit.ReferenceResolution.y * aspect >= 1700f ? CardWidth : NarrowCardWidth;

            // The standings, under the pause button.
            var glass = UIKit.Glass(root, "Standings");
            card = (RectTransform)glass.transform.parent;
            UIKit.Place(card, new Vector2(1f, 1f), new Vector2(-30f, -186f), new Vector2(width, 20f), new Vector2(1f, 1f));
            foreach (var g in card.GetComponentsInChildren<Graphic>()) g.raycastTarget = false;
            for (int i = 0; i < CoopRules.MaxPlayers; i++) rows.Add(MakeRow(glass.transform, i, width));

            feed = UIKit.Rect(root, "Feed");
            UIKit.Place(feed, new Vector2(1f, 1f), new Vector2(-30f, -186f), new Vector2(760f, 200f), new Vector2(1f, 1f));

            // The banner while out of touch.
            bannerGlass = UIKit.Glass(root, "Banner");
            UIKit.Place((RectTransform)bannerGlass.transform.parent, new Vector2(0.5f, 0.66f), Vector2.zero, new Vector2(1100f, 92f));
            banner = UIKit.GlassText(UIKit.Label(bannerGlass.transform, "Text", "", 34, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
            UIKit.Stretch(banner.rectTransform, 12f);
            UIKit.Fit(banner, 22);
            foreach (var g in bannerGlass.transform.parent.GetComponentsInChildren<Graphic>()) g.raycastTarget = false;
            bannerGlass.transform.parent.gameObject.SetActive(false);

            // Between two legs: "Made it to the bus stop!", then the next scene.
            fade = UIKit.Icon(root, "Fade", null, new Color(0.05f, 0.04f, 0.08f, 0f), 10f);
            UIKit.Stretch(fade.rectTransform);
            fade.preserveAspect = false;
            bigStop = UIKit.Title(root, "Stop", "", 92, Color.white);
            UIKit.Place(bigStop.rectTransform, new Vector2(0.5f, 0.56f), Vector2.zero, new Vector2(1700f, 140f));
            UIKit.Fit(bigStop, 50);
            smallStop = UIKit.GlassText(UIKit.Label(root, "Next", "", 40, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
            UIKit.Place(smallStop.rectTransform, new Vector2(0.5f, 0.45f), Vector2.zero, new Vector2(1500f, 70f));
            bigStop.gameObject.SetActive(false);
            smallStop.gameObject.SetActive(false);

            // The name tags move every frame: a canvas of their own, so moving them doesn't rebuild the rest of the HUD.
            tagLayer = UIKit.Rect(root, "Tags");
            UIKit.Stretch(tagLayer);
            tagLayer.gameObject.AddComponent<Canvas>();
            tagLayer.SetSiblingIndex(0);
            for (int i = 0; i < CoopRules.MaxPlayers - 1; i++)
            {
                var label = UIKit.Label(tagLayer, "Tag" + i, "", 28, Color.white, TextAnchor.MiddleCenter, true);
                label.rectTransform.sizeDelta = new Vector2(420f, 44f);
                var outline = label.gameObject.AddComponent<Outline>();
                outline.effectColor = new Color(0f, 0.02f, 0.12f, 0.75f);
                outline.effectDistance = new Vector2(2f, -2f);
                label.gameObject.SetActive(false);
                tags.Add(new Tag { rt = label.rectTransform, text = label });
            }

            if (service.Simulated) BuildEditorButtons();
        }

        Row MakeRow(Transform parent, int i, float width)
        {
            var row = new Row { rt = UIKit.Rect(parent, "Row" + i) };
            UIKit.Place(row.rt, new Vector2(0f, 1f), new Vector2(14f, -12f - i * RowHeight), new Vector2(width - 28f, RowHeight), new Vector2(0f, 1f));
            row.dot = UIKit.Icon(row.rt, "Dot", ProceduralSprites.Circle, Color.white, 40f);
            UIKit.Place(row.dot.rectTransform, new Vector2(0f, 0.5f), new Vector2(0f, 2f), new Vector2(40f, 40f), new Vector2(0f, 0.5f));
            row.number = UIKit.Label(row.dot.transform, "N", "", 24, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(row.number.rectTransform);
            // The name, and its tag in a label of its own (so a long name shrinks to fit without the tag going with it).
            row.name = UIKit.GlassText(UIKit.Label(row.rt, "Name", "", 26, UITheme.GlassInk, TextAnchor.MiddleLeft, true));
            UIKit.Place(row.name.rectTransform, new Vector2(0f, 1f), new Vector2(52f, -4f), new Vector2(width - 310f, 32f), new Vector2(0f, 1f));
            UIKit.Fit(row.name, 16);
            row.name.supportRichText = true;
            row.tag = UIKit.GlassText(UIKit.Label(row.rt, "Tag", "", 20, new Color(1f, 1f, 1f, 0.67f), TextAnchor.MiddleLeft, true));
            UIKit.Place(row.tag.rectTransform, new Vector2(0f, 1f), new Vector2(width - 252f, -6f), new Vector2(84f, 30f), new Vector2(0f, 1f));
            row.state = UIKit.GlassText(UIKit.Label(row.rt, "State", "", 24, UITheme.GlassInk, TextAnchor.MiddleRight, true));
            UIKit.Place(row.state.rectTransform, new Vector2(1f, 1f), new Vector2(0f, -4f), new Vector2(160f, 32f), new Vector2(1f, 1f));
            UIKit.Fit(row.state, 16);
            var bar = UIKit.Panel(row.rt, "Bar", new Color(1f, 1f, 1f, 0.18f), ProceduralSprites.RoundedSmall);
            UIKit.Place(bar.rectTransform, new Vector2(0f, 0f), new Vector2(52f, 8f), new Vector2(width - 82f, 8f), new Vector2(0f, 0f));
            row.barFill = UIKit.Panel(bar.transform, "Fill", Color.white, ProceduralSprites.RoundedSmall);
            row.barFill.rectTransform.anchorMin = Vector2.zero;
            row.barFill.rectTransform.anchorMax = new Vector2(0f, 1f);
            row.barFill.rectTransform.pivot = new Vector2(0f, 0.5f);
            row.barFill.rectTransform.offsetMin = row.barFill.rectTransform.offsetMax = Vector2.zero;
            foreach (var g in row.rt.GetComponentsInChildren<Graphic>()) g.raycastTarget = false;
            row.rt.gameObject.SetActive(false);
            return row;
        }

        void BuildEditorButtons()
        {
            var bar = UIKit.Rect(root, "EditorTests");
            UIKit.Place(bar, new Vector2(0.5f, 0f), new Vector2(0f, 24f), new Vector2(900f, 64f), new Vector2(0.5f, 0f));
            string[] labels = { "Bot out of range", "Bots back", "Bot host leaves", "My Bluetooth" };
            for (int i = 0; i < labels.Length; i++)
            {
                int which = i;
                var b = UIKit.Button(bar, labels[i], labels[i], UITheme.Locked, () =>
                {
                    var bots = service.Bots;
                    if (which == 0 && bots != null) bots.DropOne();
                    else if (which == 1 && bots != null) bots.BringBack();
                    else if (which == 2 && bots != null) bots.HostLeaves();
                    else if (which == 3) service.SimulateRadio(!service.SimulatedRadioOn);
                }, 22);
                UIKit.Place((RectTransform)b.transform, new Vector2(0f, 0.5f), new Vector2(i * 226f, 0f), new Vector2(214f, 60f), new Vector2(0f, 0.5f));
            }
        }

        // ---------- Per frame ----------

        bool Paused { get { return link != null && link.Level != null && link.Level.State == LevelState.Paused; } }

        void Update()
        {
            // Under the pause menu the live HUD steps aside (the race goes on: it is back as the menu closes).
            bool live = !Paused;
            if (card.gameObject.activeSelf != live)
            {
                card.gameObject.SetActive(live);
                feed.gameObject.SetActive(live);
                tagLayer.gameObject.SetActive(live);
            }
            if (live && Time.unscaledTime >= nextRefresh)
            {
                nextRefresh = Time.unscaledTime + 0.25f;
                RefreshStandings();
            }
            RefreshBanner(live);
            RefreshFeed();
            RefreshStop();
            RefreshResults();
        }

        void LateUpdate()
        {
            if (!Paused) RefreshTags();
        }

        /// <summary>Everyone in the order they stand, with the bar of how far along the route they are.</summary>
        void RefreshStandings()
        {
            var standings = CoopRules.Standings(Session.Players);
            int shown = 0, position = 0;
            foreach (var p in standings)
            {
                if (shown >= rows.Count) break;
                if (p.status == PlayerStatus.Lobby) continue;
                var row = rows[shown++];
                row.rt.gameObject.SetActive(true);
                bool me = p.uid == Session.Uid;
                Color c = CoopPalette.Of(p.slot);
                row.dot.color = p.IsOut ? new Color(c.r, c.g, c.b, 0.35f) : c;
                if (!p.IsOut) position++;
                row.number.text = p.IsOut ? "-" : (p.status == PlayerStatus.Finished ? p.place : position).ToString();
                string name = CoopProfile.DisplayName(p);
                if (row.uid != p.uid || row.shownName != name || row.shownBold != me)
                {
                    row.uid = p.uid;
                    row.shownName = name;
                    row.shownBold = me;
                    row.name.text = me ? "<b>" + name + "</b>" : name;
                    row.tag.text = "#" + p.tag;
                }
                float progress = p.status == PlayerStatus.Finished ? 1f
                    : me ? (race.LoadingLeg ? race.Progress(0f) : race.Progress(LocalFraction())) : p.progress;
                row.barFill.rectTransform.anchorMax = new Vector2(Mathf.Clamp01(progress), 1f);
                row.barFill.color = p.IsOut ? new Color(1f, 1f, 1f, 0.3f) : c;
                row.state.text = StateOf(p, me);
                row.state.color = p.IsOut ? new Color(1f, 0.6f, 0.55f) : p.status == PlayerStatus.Finished ? UITheme.Gold : UITheme.GlassInk;
            }
            for (int i = shown; i < rows.Count; i++) rows[i].rt.gameObject.SetActive(false);
            card.sizeDelta = new Vector2(card.sizeDelta.x, 24f + shown * RowHeight);
            feed.anchoredPosition = new Vector2(-30f, -186f - card.sizeDelta.y - 12f);
        }

        float LocalFraction()
        {
            if (link == null || link.Level == null) return 0f;
            return (link.Level.kid.transform.position.x - link.StartX) / link.LegLength;
        }

        string StateOf(CoopPlayer p, bool me)
        {
            switch (p.status)
            {
                case PlayerStatus.Finished: return CoopRules.FormatTime(p.finishMs, true);
                case PlayerStatus.Disconnected: return Loc.T("coop.state.out");
                case PlayerStatus.Left: return Loc.T("coop.state.left");
            }
            if (!me && !p.connected) return Loc.T("coop.state.lost");
            int leg = me ? race.Leg : p.leg;
            return Loc.F("coop.state.leg", leg + 1, race.LegCount);
        }

        /// <summary>
        /// While this phone is out of touch: why, and how long before the others list it last. Once they do: that it is
        /// listed last for now, and its run counts again the moment it is back in touch (so keep going).
        /// </summary>
        void RefreshBanner(bool live)
        {
            string text = null;
            var s = Session;
            bool racing = s.MyStatus == PlayerStatus.Racing;
            if (s.ListedOut) text = Loc.T(s.Radio == Net.RadioState.On ? "coop.banner.listedOut" : "coop.banner.listedOutRadio");
            else if (s.Connection == ConnectionState.Reconnecting)
            {
                int left = Mathf.Max(0, Mathf.CeilToInt((float)((CoopTiming.RaceGrace - s.LostForMs) / 1000.0)));
                string key = s.Radio == Net.RadioState.On ? "coop.banner.reconnecting" : "coop.banner.radioOff";
                text = racing ? Loc.F(key + ".time", left) : Loc.T(key);
            }
            else if (s.Alone && OthersStillRacing()) text = Loc.T("coop.banner.alone");
            var holder = bannerGlass.transform.parent.gameObject;
            holder.SetActive(live && text != null && !race.BetweenLegs);
            if (text != null) banner.text = text;
        }

        bool OthersStillRacing()
        {
            var players = Session.Players;
            for (int i = 0; i < players.Count; i++)
                if (players[i].uid != Session.Uid && players[i].status == PlayerStatus.Racing) return true;
            return false;
        }

        // ---------- The feed ----------

        void OnNotice(CoopNotice n)
        {
            string name = n.player != null ? CoopProfile.FullName(n.player) : "";
            string text = null;
            switch (n.type)
            {
                case NoticeType.PlayerFinished: text = Loc.F("coop.feed.finished", name, CoopPalette.Place(n.code)); break;
                case NoticeType.PlayerLost: text = Loc.F("coop.feed.lost", name); break;
                case NoticeType.PlayerBack: text = Loc.F("coop.feed.back", name); break;
                case NoticeType.PlayerOut: text = Loc.F("coop.feed.out", name); break;
                case NoticeType.PlayerLeft: text = Loc.F("coop.feed.left", name); break;
                case NoticeType.NewHost: text = Loc.F("coop.feed.newHost", name); break;
                case NoticeType.YouAreHost: text = Loc.T("coop.feed.youHost"); break;
                case NoticeType.Reconnected: text = Loc.T("coop.feed.reconnected"); break;
                case NoticeType.RaceOver: text = Loc.T("coop.feed.over"); break;
                case NoticeType.YouAreOut: text = Loc.T("coop.feed.youOut"); break;
            }
            if (text == null || feed == null) return;
            var label = UIKit.GlassText(UIKit.Label(feed, "Line", text, 27, UITheme.GlassInk, TextAnchor.MiddleRight, true));
            label.rectTransform.anchorMin = label.rectTransform.anchorMax = label.rectTransform.pivot = new Vector2(1f, 1f);
            label.rectTransform.sizeDelta = new Vector2(760f, 40f);
            UIKit.Fit(label, 18);
            if (n.player != null) label.color = Color.Lerp(UITheme.GlassInk, CoopPalette.Of(n.player.slot), 0.35f);
            lines.Insert(0, new FeedLine { text = label, until = Time.unscaledTime + 5f });
            while (lines.Count > 4) { Destroy(lines[lines.Count - 1].text.gameObject); lines.RemoveAt(lines.Count - 1); }
        }

        void RefreshFeed()
        {
            for (int i = lines.Count - 1; i >= 0; i--)
            {
                var line = lines[i];
                float left = line.until - Time.unscaledTime;
                if (left <= 0f) { Destroy(line.text.gameObject); lines.RemoveAt(i); continue; }
                var c = line.text.color;
                c.a = Mathf.Clamp01(left / 0.6f);
                line.text.color = c;
                line.text.rectTransform.anchoredPosition = new Vector2(0f, -i * 42f);
            }
        }

        // ---------- Name tags ----------

        void RefreshTags()
        {
            if (cam == null) cam = Camera.main;
            int used = 0;
            if (cam != null && link != null)
            {
                float kidX = link.Level.kid.transform.position.x;
                foreach (var ghost in link.Ghosts)
                {
                    if (!ghost.Shown || used >= tags.Count) continue;
                    var p = Session.Find(ghost.uid);
                    if (p == null) continue;
                    var tag = tags[used++];
                    Vector3 screen = cam.WorldToScreenPoint(ghost.TagPoint);
                    bool behind = screen.z < 0f;
                    float margin = 120f;
                    bool off = behind || screen.x < margin || screen.x > Screen.width - margin;
                    if (tag.uid != p.uid || tag.fullName == null || Time.frameCount % 30 == 0)
                    {
                        tag.uid = p.uid;
                        tag.fullName = CoopProfile.FullName(p);
                    }
                    string name = tag.fullName;
                    if (off)
                    {
                        // Out of view: at the side it is on, with how far away it is.
                        bool right = ghost.transform.position.x > kidX;
                        int metres = Mathf.RoundToInt(Mathf.Abs(ghost.transform.position.x - kidX));
                        tag.text.text = right ? name + "  " + metres + " m »" : "« " + metres + " m  " + name;
                        screen.x = right ? Screen.width - margin * 1.9f : margin * 1.9f;
                        screen.y = Mathf.Clamp(screen.y, Screen.height * 0.3f, Screen.height * 0.7f);
                    }
                    else if (!ReferenceEquals(tag.text.text, name)) tag.text.text = name;
                    tag.text.color = Color.Lerp(Color.white, CoopPalette.Of(p.slot), 0.45f);
                    tag.rt.position = new Vector3(screen.x, screen.y, 0f);
                    tag.rt.gameObject.SetActive(true);
                }
            }
            for (int i = used; i < tags.Count; i++) tags[i].rt.gameObject.SetActive(false);
        }

        // ---------- Between legs ----------

        void RefreshStop()
        {
            bool between = race.BetweenLegs;
            bigStop.gameObject.SetActive(between);
            smallStop.gameObject.SetActive(between);
            var c = fade.color;
            c.a = Mathf.MoveTowards(c.a, between ? 0.55f : 0f, Time.unscaledDeltaTime * 2f);
            fade.color = c;
            if (!between) return;
            var stop = race.ReachedStop;
            bigStop.text = stop != null && stop.ToKey != null ? Loc.F("coop.stop.made", Loc.T(stop.ToKey)) : Loc.T("coop.stop.onward");
            var nextTo = race.Route != null && race.Leg + 1 < race.LegCount ? Levels.RouteTable.To(race.Route.levels[race.Leg + 1]) : null;
            smallStop.text = nextTo != null ? Loc.F("coop.stop.next", Loc.T(nextTo.NameKey), race.Leg + 2, race.LegCount) : "";
        }

        // ---------- At the gate ----------

        void RefreshResults()
        {
            if (race.Finished && !resultsShownForFinish) { resultsShownForFinish = true; OpenResults(); }
            if (results == null || Time.unscaledTime < nextResultsRefresh) return;
            nextResultsRefresh = Time.unscaledTime + 0.5f;
            FillResults();
        }

        /// <summary>What the standings card shows, in one number: it is rebuilt only when this changes.</summary>
        int ResultsSignature()
        {
            var s = Session;
            int h = (int)s.Phase * 31 + race.CoinsEarned;
            var players = s.Players;
            for (int i = 0; i < players.Count; i++)
            {
                var p = players[i];
                h = h * 31 + (int)p.uid;
                h = h * 31 + (int)p.status;
                h = h * 31 + p.place;
                h = h * 31 + (int)p.finishMs;
                h = h * 31 + (p.connected ? 1 : 0);
                h = h * 31 + (p.name != null ? p.name.GetHashCode() : 0);
                h = h * 31 + (int)(p.progress * 20f);
            }
            return h;
        }

        void OpenResults()
        {
            if (results != null) return;
            var face = UIKit.Modal(root, "CoopResults", new Vector2(1100f, 860f), out results);
            UIKit.Header(face.transform, Loc.T("coop.results.title"), 620f);
            resultsHeading = UIKit.Title(face.transform, "Heading", "", 64, Color.white);
            UIKit.Place(resultsHeading.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -120f), new Vector2(980f, 90f));
            UIKit.Fit(resultsHeading, 40);
            resultsSub = UIKit.Label(face.transform, "Sub", "", 30, UITheme.InkSoft, TextAnchor.MiddleCenter);
            UIKit.Place(resultsSub.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -186f), new Vector2(980f, 44f));
            UIKit.Fit(resultsSub, 20);
            resultsBody = UIKit.Rect(face.transform, "Standings");
            UIKit.Place(resultsBody, new Vector2(0.5f, 1f), new Vector2(0f, -230f), new Vector2(960f, 420f), new Vector2(0.5f, 1f));

            var lobby = UIKit.Button(face.transform, "Lobby", Loc.T("coop.results.lobby"), UITheme.Green, () => race.ToLobby(), 40);
            UIKit.Place((RectTransform)lobby.transform, new Vector2(0.5f, 0f), new Vector2(-190f, 50f), new Vector2(320f, 100f), new Vector2(0.5f, 0f));
            var leave = UIKit.Button(face.transform, "Leave", Loc.T("coop.results.leave"), UITheme.Red, () =>
            {
                // A finish no other phone has heard of yet would go with this phone: say so before leaving.
                if (Session.FinishUnconfirmed) CoopStagePicker.Confirm(root, Loc.T("coop.confirmLeave.unseen"), () => race.Leave());
                else race.Leave();
            }, 40);
            UIKit.Place((RectTransform)leave.transform, new Vector2(0.5f, 0f), new Vector2(190f, 50f), new Vector2(320f, 100f), new Vector2(0.5f, 0f));
            resultsSignature = 0;
            FillResults();
        }

        void FillResults()
        {
            if (results == null) return;
            var s = Session;
            var me = s.Me;
            bool over = s.Phase == SessionPhase.Over || !OthersStillRacing();
            if (race.Finished && me != null && me.status == PlayerStatus.Finished)
                resultsHeading.text = me.place == 1 ? Loc.T("coop.results.won") : Loc.F("coop.results.place", CoopPalette.Place(me.place));
            else if (s.ListedOut) resultsHeading.text = Loc.T("coop.results.unseen");
            else resultsHeading.text = Loc.T("coop.results.atSchool");
            string coins = race.CoinsEarned > 0 ? Loc.F("coop.results.coins", race.CoinsEarned) : "";
            resultsSub.text = over ? Loc.T("coop.results.final") + (coins.Length > 0 ? "  ·  " + coins : "")
                : Loc.T("coop.results.live") + (coins.Length > 0 ? "  ·  " + coins : "");

            int signature = ResultsSignature();
            if (signature == resultsSignature && resultsBody.childCount > 0) return;
            resultsSignature = signature;
            for (int i = resultsBody.childCount - 1; i >= 0; i--) Destroy(resultsBody.GetChild(i).gameObject);
            CoopStandingsView.Build(resultsBody, s, 96f);
        }
    }
}
