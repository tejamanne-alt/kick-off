using System.Collections.Generic;
using System.Text;
using DribbleToSchool.Coop;
using DribbleToSchool.Coop.Net;
using DribbleToSchool.Core;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// Co-op, from the title screen: up to four phones nearby (iPhones and Android phones together, over Bluetooth LE) race
    /// from home to school on the same stage. The screen has four faces:
    /// - Start: the name the others will see (with this phone's tag, "#K7QX", so two players of the same name are told apart;
    ///   empty means "Player 2" for the slot), the kid (the picker), Bluetooth's state with a way to fix it, and HOST or JOIN.
    /// - Join: the lobbies the scan hears, with their host, how many are in, and whether a race is already on.
    /// - Lobby: the four seats (who, their tag, host, ready, a lost connection), the stage and location and who chose them
    ///   (any player may change them, as in a fighting game's stage select: the last choice wins and everyone readies again),
    ///   READY, and the countdown once everyone is ready.
    /// - Race: back from the school gate while the others run, or after the race: the standings, and for the host NEW RACE.
    /// The filters (comic, sketch) stay each phone's own choice, from Add-ons and Filters on the title screen.
    /// </summary>
    public class CoopScreen : FrontEndScreen
    {
        enum View { Start, Join, Connecting, Lobby, Race }

        CoopService service;
        RectTransform root, body, nameRow;
        InputField nameField;
        Text tagLabel, toast, countdown;
        Image kidPortrait;
        View view = (View)(-1);
        string signature = "";
        float toastUntil, nextRefresh, nextSignature;
        string shownTag;
        bool picking;

        public override string Title { get { return Loc.T("coop.title"); } }

        /// <summary>The body's width in canvas units (1360 at 4:3, 1840 at 16:9), so the two columns never overlap.</summary>
        static float BodyWidth
        {
            get
            {
                float aspect = Screen.height > 0 ? (float)Screen.width / Screen.height : 16f / 9f;
                return UIKit.ReferenceResolution.y * aspect - 80f;
            }
        }

        /// <summary>The left column (the name, the seats, Bluetooth's state) and the right one (the stage, HOST and JOIN).</summary>
        static float LeftWidth { get { return Mathf.Min(760f, BodyWidth - 620f); } }
        static float RightWidth { get { return Mathf.Clamp(BodyWidth - LeftWidth - 60f, 520f, 860f); } }

        CoopSession Session { get { return service.Session; } }

        protected override void Build(RectTransform root)
        {
            this.root = root;
            service = CoopService.Ensure();
            if (service.Catalog == null) service.Catalog = Controller.levels;

            body = UIKit.Rect(root, "Body");
            UIKit.Stretch(body);
            body.offsetMin = new Vector2(40f, 30f);
            body.offsetMax = new Vector2(-40f, -170f);

            BuildNameRow();

            toast = UIKit.Title(root, "Toast", "", 44, Color.white);
            UIKit.Place(toast.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -150f), new Vector2(1500f, 70f));
            UIKit.Fit(toast, 26);
            toast.gameObject.SetActive(false);
            countdown = UIKit.Title(root, "Countdown", "", 200, Color.white);
            UIKit.Place(countdown.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(600f, 260f));
            countdown.gameObject.SetActive(false);

            service.Noticed += OnNotice;
            GameSettings.Changed += RefreshKid;
        }

        public override void OnDestroyed()
        {
            if (service != null) service.Noticed -= OnNotice;
            GameSettings.Changed -= RefreshKid;
        }

        public override void OnShow()
        {
            if (service.Catalog == null) service.Catalog = Controller.levels;
            // Android asks for Bluetooth's permissions now (only those still missing); iOS asked when Bluetooth started.
            if (!Session.InSession) service.RequestPermission();
            nameField.text = CoopProfile.Name;
            RefreshKid();
            view = (View)(-1);
            signature = "";
            Tick();
        }

        public override void OnHide()
        {
            if (!Session.InSession) service.StopBrowsing();
        }

        /// <summary>The back button: out of the Join list back to Start; out of a lobby only after asking.</summary>
        public override bool HandleBack()
        {
            if (view == View.Join || view == View.Connecting)
            {
                if (view == View.Connecting) service.Leave();
                service.StopBrowsing();
                view = (View)(-1);
                forceStart = true;
                return true;
            }
            if (Session.InSession)
            {
                ConfirmLeave(() => { service.Leave(); Controller.Show(FrontEndScreenId.Title); });
                return true;
            }
            return false;
        }

        bool forceStart, browsing;

        // ---------- The name row (kept through rebuilds, so typing is never interrupted) ----------

        void BuildNameRow()
        {
            nameRow = UIKit.Rect(root, "NameRow");
            UIKit.Place(nameRow, new Vector2(0f, 1f), new Vector2(40f, -170f), new Vector2(LeftWidth, 120f), new Vector2(0f, 1f));

            var caption = UIKit.Label(nameRow, "Caption", Loc.T("coop.nameCaption"), 26, Color.white, TextAnchor.LowerLeft, true);
            UIKit.Place(caption.rectTransform, new Vector2(0f, 1f), new Vector2(0f, 0f), new Vector2(560f, 34f), new Vector2(0f, 1f));
            UIKit.GlassText(caption);
            UIKit.Fit(caption, 18);

            var face = UIKit.Card(nameRow, "Field", UITheme.Paper);
            UIKit.Place((RectTransform)face.transform.parent, new Vector2(0f, 1f), new Vector2(0f, -38f), new Vector2(420f, 80f), new Vector2(0f, 1f));
            var text = UIKit.Label(face.transform, "Text", "", 36, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Stretch(text.rectTransform);
            text.rectTransform.offsetMin = new Vector2(22f, 4f);
            text.rectTransform.offsetMax = new Vector2(-18f, -4f);
            text.supportRichText = false;
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            var placeholder = UIKit.Label(face.transform, "Placeholder", Loc.T("coop.namePlaceholder"), 32, UITheme.InkSoft, TextAnchor.MiddleLeft);
            UIKit.Stretch(placeholder.rectTransform);
            placeholder.rectTransform.offsetMin = new Vector2(22f, 4f);
            placeholder.rectTransform.offsetMax = new Vector2(-18f, -4f);
            nameField = face.gameObject.AddComponent<InputField>();
            nameField.textComponent = text;
            nameField.placeholder = placeholder;
            nameField.characterLimit = CoopRules.MaxNameLength;
            nameField.lineType = InputField.LineType.SingleLine;
            nameField.targetGraphic = face;
            nameField.text = CoopProfile.Name;
            nameField.onEndEdit.AddListener(v =>
            {
                if (CoopRules.IsRefused(v)) Toast(Loc.T("coop.toast.nameRefused"));
                CoopProfile.Name = v;
                nameField.text = CoopProfile.Name;
                Session.SetName(CoopProfile.Name);
            });

            // The tag that follows the name on the others' screens.
            var tagCard = UIKit.Card(nameRow, "Tag", UITheme.PaperDark);
            UIKit.Place((RectTransform)tagCard.transform.parent, new Vector2(0f, 1f), new Vector2(434f, -38f), new Vector2(150f, 80f), new Vector2(0f, 1f));
            tagLabel = UIKit.Label(tagCard.transform, "Text", "", 34, UITheme.Navy, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(tagLabel.rectTransform, 6f);
            UIKit.Fit(tagLabel, 20);

            // The kid (tap to change: the others see this kid).
            var kid = UIKit.Button(nameRow, "Kid", "", UITheme.Paper, () => PlayerPicker.Open(Controller.CanvasRoot));
            UIKit.Place((RectTransform)kid.transform, new Vector2(0f, 1f), new Vector2(598f, -30f), new Vector2(96f, 96f), new Vector2(0f, 1f));
            UIKit.MakeRound(kid);
            var mask = UIKit.Rect(kid.transform.Find("Face"), "Mask");
            UIKit.Stretch(mask, 6f);
            mask.gameObject.AddComponent<RectMask2D>();
            kidPortrait = CartoonPicture.On(UIKit.Icon(mask, "Portrait", null, Color.white, 90f));
            kidPortrait.rectTransform.anchorMin = Vector2.zero;
            kidPortrait.rectTransform.anchorMax = Vector2.one;
            kidPortrait.rectTransform.offsetMin = new Vector2(-6f, -10f);
            kidPortrait.rectTransform.offsetMax = new Vector2(6f, 6f);
        }

        void RefreshKid()
        {
            if (kidPortrait == null) return;
            var portrait = PlayerPicker.Portrait(GameSettings.Character);
            kidPortrait.sprite = portrait != null ? portrait : ProceduralSprites.BallIcon;
            kidPortrait.preserveAspect = true;
        }

        // ---------- Every frame ----------

        public override void Tick()
        {
            if (service == null) return;
            var next = CurrentView();
            // (what the view shows is looked at a few times a second, not every frame: building it allocates)
            if (next != view || Time.unscaledTime >= nextSignature)
            {
                nextSignature = Time.unscaledTime + 0.2f;
                string sig = Signature(next);
                if (next != view || sig != signature)
                {
                    view = next;
                    signature = sig;
                    Rebuild();
                }
            }
            // The Join list needs a scan running (one that ended with a failed join, or a lobby that closed, starts again).
            if (view == View.Join && !Session.InSession && !Session.Browsing && Session.Radio == RadioState.On) service.Browse();
            string tag = MyTag();
            if (tag != shownTag) { shownTag = tag; tagLabel.text = "#" + tag; }
            nameRow.gameObject.SetActive(view == View.Start || view == View.Lobby);

            float left = toastUntil - Time.unscaledTime;
            toast.gameObject.SetActive(left > 0f);
            if (left > 0f) { var c = toast.color; c.a = Mathf.Clamp01(left / 0.4f); toast.color = c; }

            bool counting = Session.Phase == SessionPhase.Starting && view == View.Lobby;
            countdown.gameObject.SetActive(counting && !picking);
            if (counting) countdown.text = Mathf.Max(1, Mathf.CeilToInt((float)Session.CountdownMs / 1000f)).ToString();
        }

        View CurrentView()
        {
            var s = Session;
            if (s.InSession)
            {
                forceStart = false;
                if (s.Connection == ConnectionState.Connecting) return View.Connecting;
                if (s.Phase == SessionPhase.Lobby || s.Phase == SessionPhase.Starting) return View.Lobby;
                return View.Race;
            }
            if (forceStart) { browsing = false; return View.Start; }
            return browsing ? View.Join : View.Start;
        }

        /// <summary>What the view shows, as a string: the view is rebuilt when it changes (a few times a second at most).</summary>
        string Signature(View v)
        {
            var s = Session;
            var sb = new StringBuilder();
            sb.Append((int)s.Radio).Append('|').Append(service.LocationOff ? 1 : 0).Append('|');
            if (v == View.Join)
            {
                if (Time.unscaledTime < nextRefresh) return signature;   // the list changes often: twice a second is plenty
                nextRefresh = Time.unscaledTime + 0.5f;
                // What the list draws: the rooms nearest first, each with its signal word. The raw strength jitters by
                // 5 to 10 dB, and keying on it rebuilt the whole list about twice a second for nothing.
                sortedRooms.Clear();
                sortedRooms.AddRange(s.Rooms);
                sortedRooms.Sort(Nearest);
                foreach (var r in sortedRooms) sb.Append(r.address).Append(r.beacon.players).Append((int)r.beacon.phase).Append(r.beacon.hostName).Append(SignalLevel(r.rssi)).Append(';');
                sortedRooms.Clear();
            }
            if (v == View.Lobby || v == View.Race)
            {
                sb.Append((int)s.Phase).Append(s.Selection.route).Append(s.Selection.addOn).Append(s.Selection.chosenBy).Append(s.IsHost ? 'H' : 'C').Append((int)s.Connection);
                foreach (var p in s.Players)
                    sb.Append(p.slot).Append(p.name).Append(p.tag).Append(p.character).Append(p.ready ? 'r' : '-').Append(p.connected ? 'c' : 'x')
                      .Append(p.isHost ? 'h' : '-').Append((int)p.status).Append(p.place).Append(v == View.Race ? Mathf.FloorToInt(p.progress * 10f) : 0).Append(';');
                sb.Append(s.MyReady);
            }
            return sb.ToString();
        }

        string MyTag()
        {
            var me = Session.Me;
            return me != null && !string.IsNullOrEmpty(me.tag) ? me.tag : CoopRules.TagFor(CoopProfile.TagSeed, 0);
        }

        void Rebuild()
        {
            for (int i = body.childCount - 1; i >= 0; i--) Object.Destroy(body.GetChild(i).gameObject);
            switch (view)
            {
                case View.Start: BuildStart(); break;
                case View.Join: BuildJoin(); break;
                case View.Connecting: BuildConnecting(); break;
                case View.Lobby: BuildLobby(); break;
                case View.Race: BuildRace(); break;
            }
        }

        // ---------- Start ----------

        void BuildStart()
        {
            // Bluetooth's state, and what to do about it.
            var status = Panel(body, "Radio", new Vector2(0f, 1f), new Vector2(0f, -150f), new Vector2(LeftWidth, 150f));
            string line, action = null;
            System.Action fix = null;
            switch (Session.Radio)
            {
                case RadioState.On:
                    line = service.LocationOff ? Loc.T("coop.radio.location") : service.Simulated ? Loc.T("coop.radio.editor") : Loc.T("coop.radio.on");
                    break;
                case RadioState.Off:
#if UNITY_IOS
                    // (no app can open Bluetooth's switch on iOS: it is in Control Center, or Settings > Bluetooth)
                    line = Loc.T("coop.radio.offIos");
#else
                    line = Loc.T("coop.radio.off");
                    action = Loc.T("coop.radio.openBluetooth");
                    fix = () => service.OpenSettings(true);
#endif
                    break;
                case RadioState.Unauthorized:
                    line = Loc.T("coop.radio.unauthorized");
                    action = Loc.T("coop.radio.allow");
                    fix = () => { service.RequestPermission(); service.OpenSettingsIfDenied(); };
                    break;
                case RadioState.Unsupported:
                    line = Loc.T("coop.radio.unsupported");
                    break;
                default:
                    line = Loc.T("coop.radio.starting");
                    action = Loc.T("coop.radio.allow");
                    fix = service.RequestPermission;
                    break;
            }
            var text = UIKit.Label(status.transform, "Line", line, 30, UITheme.Ink, TextAnchor.MiddleLeft);
            UIKit.Stretch(text.rectTransform);
            text.rectTransform.offsetMin = new Vector2(28f, 10f);
            text.rectTransform.offsetMax = new Vector2(action != null ? -280f : -28f, -10f);
            UIKit.Fit(text, 20);
            if (action != null)
            {
                var b = UIKit.Button(status.transform, "Fix", action, UITheme.Blue, () => fix(), 30);
                UIKit.Place((RectTransform)b.transform, new Vector2(1f, 0.5f), new Vector2(-24f, 0f), new Vector2(240f, 90f), new Vector2(1f, 0.5f));
            }

            // How it works.
            var how = Panel(body, "How", new Vector2(0f, 1f), new Vector2(0f, -320f), new Vector2(LeftWidth, 440f));
            UIKit.SectionLabel(UIKit.Row(how.transform, "Label", 22f, 46f, 26f, 26f), Loc.T("coop.how.title"));
            var about = UIKit.Label(how.transform, "Text", Loc.T("coop.how.text"), 27, UITheme.Ink, TextAnchor.UpperLeft);
            UIKit.Stretch(about.rectTransform);
            about.rectTransform.offsetMin = new Vector2(30f, 20f);
            about.rectTransform.offsetMax = new Vector2(-30f, -84f);
            UIKit.Fit(about, 18);

            // HOST and JOIN.
            bool ready = Session.Radio == RadioState.On;
            float buttons = Mathf.Min(560f, BodyWidth - LeftWidth - 80f);
            var host = UIKit.Button(body, "Host", Loc.T("coop.host.button"), UITheme.Accent, () => { service.Host(); }, 58);
            UIKit.Place((RectTransform)host.transform, new Vector2(1f, 1f), new Vector2(-40f, -30f), new Vector2(buttons, 200f), new Vector2(1f, 1f));
            AddSubtitle(host, Loc.T("coop.host.about"));
            host.interactable = ready;
            var join = UIKit.Button(body, "Join", Loc.T("coop.join.button"), UITheme.Blue, () => { browsing = true; forceStart = false; service.Browse(); }, 58);
            UIKit.Place((RectTransform)join.transform, new Vector2(1f, 1f), new Vector2(-40f, -270f), new Vector2(buttons, 200f), new Vector2(1f, 1f));
            AddSubtitle(join, Loc.T("coop.join.about"));
            join.interactable = ready;

            var stats = SaveSystemStats();
            if (stats != null)
            {
                var s = UIKit.Label(body, "Stats", stats, 28, Color.white, TextAnchor.MiddleRight, true);
                UIKit.GlassText(s);
                UIKit.Place(s.rectTransform, new Vector2(1f, 1f), new Vector2(-40f, -500f), new Vector2(buttons, 50f), new Vector2(1f, 1f));
                UIKit.Fit(s, 20);
            }
        }

        static string SaveSystemStats()
        {
            var d = Progression.SaveSystem.Data;
            if (d.coopRaces <= 0) return null;
            return Loc.F("coop.stats", d.coopRaces, d.coopWins);
        }

        static void AddSubtitle(Button b, string line)
        {
            var face = b.transform.Find("Face");
            var label = face.Find("Label");
            if (label != null)
            {
                var rt = (RectTransform)label;
                rt.anchorMin = new Vector2(0f, 0.38f);
                rt.offsetMin = new Vector2(14f, 0f);
            }
            var sub = UIKit.Label(face, "Sub", line, 26, new Color(1f, 1f, 1f, 0.92f), TextAnchor.MiddleCenter, true);
            sub.rectTransform.anchorMin = new Vector2(0f, 0f);
            sub.rectTransform.anchorMax = new Vector2(1f, 0.42f);
            sub.rectTransform.offsetMin = new Vector2(20f, 14f);
            sub.rectTransform.offsetMax = new Vector2(-20f, 0f);
            UIKit.Fit(sub, 18);
        }

        // ---------- Join ----------

        void BuildJoin()
        {
            var list = new List<CoopRoom>(Session.Rooms);
            list.Sort(Nearest);   // the nearest first
            var heading = UIKit.Label(body, "Heading", Loc.T(list.Count > 0 ? "coop.join.pick" : "coop.join.looking"), 36, Color.white, TextAnchor.MiddleLeft, true);
            UIKit.GlassText(heading);
            float listWidth = Mathf.Min(1100f, BodyWidth - 40f);
            UIKit.Place(heading.rectTransform, new Vector2(0f, 1f), Vector2.zero, new Vector2(listWidth, 60f), new Vector2(0f, 1f));
            UIKit.Fit(heading, 24);
            if (list.Count == 0)
            {
                var tip = Panel(body, "Tip", new Vector2(0f, 1f), new Vector2(0f, -80f), new Vector2(listWidth, 160f));
                var t = UIKit.Label(tip.transform, "Text", Loc.T(service.LocationOff ? "coop.radio.location" : "coop.join.tip"), 30, UITheme.Ink, TextAnchor.MiddleLeft);
                UIKit.Stretch(t.rectTransform, 28f);
                UIKit.Fit(t, 20);
                return;
            }
            float y = -80f;
            foreach (var room in list)
            {
                if (y < -80f - 5 * 130f) break;
                var card = Panel(body, "Room", new Vector2(0f, 1f), new Vector2(0f, y), new Vector2(listWidth, 116f));
                y -= 130f;
                var b = room.beacon;
                string host = string.IsNullOrEmpty(b.hostName) ? Loc.T("coop.join.someone") : b.hostName;
                var name = UIKit.Label(card.transform, "Host", Loc.F("coop.join.hostsRace", host), 36, UITheme.Ink, TextAnchor.MiddleLeft, true);
                UIKit.Place(name.rectTransform, new Vector2(0f, 1f), new Vector2(28f, -12f), new Vector2(640f, 50f), new Vector2(0f, 1f));
                UIKit.Fit(name, 22);
                bool sameVersion = b.protocol == CoopMessages.Protocol;
                bool open = sameVersion && b.phase == RoomPhase.Lobby && b.players < CoopRules.MaxPlayers;
                string state = !sameVersion ? Loc.T("coop.join.version") : b.phase != RoomPhase.Lobby ? Loc.T("coop.join.racing")
                    : b.players >= CoopRules.MaxPlayers ? Loc.T("coop.join.full") : Loc.F("coop.join.players", b.players, CoopRules.MaxPlayers);
                var line = UIKit.Label(card.transform, "State", state + "  ·  " + Signal(room.rssi), 26, UITheme.InkSoft, TextAnchor.MiddleLeft);
                UIKit.Place(line.rectTransform, new Vector2(0f, 1f), new Vector2(28f, -64f), new Vector2(640f, 38f), new Vector2(0f, 1f));
                UIKit.Fit(line, 18);
                var target = room;
                var join = UIKit.Button(card.transform, "Join", Loc.T("coop.join.this"), open ? UITheme.Green : UITheme.Locked, () => service.Join(target), 36);
                UIKit.Place((RectTransform)join.transform, new Vector2(1f, 0.5f), new Vector2(-20f, 0f), new Vector2(260f, 86f), new Vector2(1f, 0.5f));
                join.interactable = open;
            }
        }

        static readonly System.Comparison<CoopRoom> Nearest = (a, b) => b.rssi.CompareTo(a.rssi);
        readonly List<CoopRoom> sortedRooms = new List<CoopRoom>();

        /// <summary>2 strong, 1 good, 0 weak: what <see cref="Signal"/> says.</summary>
        static int SignalLevel(int rssi) { return rssi > -60 ? 2 : rssi > -78 ? 1 : 0; }

        static string Signal(int rssi)
        {
            int level = SignalLevel(rssi);
            return Loc.T(level == 2 ? "coop.signal.strong" : level == 1 ? "coop.signal.good" : "coop.signal.weak");
        }

        void BuildConnecting()
        {
            var card = Panel(body, "Joining", new Vector2(0.5f, 0.5f), new Vector2(0f, 40f), new Vector2(900f, 260f));
            var t = UIKit.Label(card.transform, "Text", Loc.T("coop.joining"), 40, UITheme.Ink, TextAnchor.MiddleCenter, true);
            UIKit.Place(t.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -70f), new Vector2(820f, 70f));
            var cancel = UIKit.Button(card.transform, "Cancel", Loc.T("coop.cancel"), UITheme.Red, () => { service.Leave(); browsing = true; }, 34);
            UIKit.Place((RectTransform)cancel.transform, new Vector2(0.5f, 0f), new Vector2(0f, 34f), new Vector2(300f, 90f), new Vector2(0.5f, 0f));
        }

        // ---------- Lobby ----------

        void BuildLobby()
        {
            var s = Session;
            // The four seats, under the name row.
            for (int slot = 0; slot < CoopRules.MaxPlayers; slot++)
            {
                var p = s.InSlot(slot);
                var seat = Panel(body, "Seat" + slot, new Vector2(0f, 1f), new Vector2(0f, -140f - slot * 132f), new Vector2(LeftWidth, 120f));
                var ring = UIKit.Icon(seat.transform, "Colour", ProceduralSprites.CircleEdge, p != null ? CoopPalette.Of(slot) : UITheme.Locked, 84f);
                UIKit.Place(ring.rectTransform, new Vector2(0f, 0.5f), new Vector2(18f, 0f), new Vector2(84f, 84f), new Vector2(0f, 0.5f));
                if (p == null)
                {
                    var num = UIKit.Label(ring.transform, "N", (slot + 1).ToString(), 34, Color.white, TextAnchor.MiddleCenter, true);
                    UIKit.Stretch(num.rectTransform);
                    var empty = UIKit.Label(seat.transform, "Waiting", Loc.T("coop.seat.empty"), 30, UITheme.InkSoft, TextAnchor.MiddleLeft);
                    UIKit.Place(empty.rectTransform, new Vector2(0f, 0.5f), new Vector2(124f, 0f), new Vector2(LeftWidth - 150f, 60f), new Vector2(0f, 0.5f));
                    continue;
                }
                var portrait = PlayerPicker.Portrait(CoopProfile.CharacterId(p.character));
                var mask = UIKit.Rect(ring.transform, "Mask");
                UIKit.Stretch(mask, 6f);
                mask.gameObject.AddComponent<RectMask2D>();
                var img = CartoonPicture.On(UIKit.Icon(mask, "Kid", portrait, Color.white, 84f));
                img.rectTransform.anchorMin = Vector2.zero;
                img.rectTransform.anchorMax = Vector2.one;
                img.rectTransform.offsetMin = new Vector2(-6f, -10f);
                img.rectTransform.offsetMax = new Vector2(6f, 6f);

                bool me = p.uid == s.Uid;
                // The host can send a player away (someone who joined uninvited, a name that shouldn't be shown).
                bool removable = s.IsHost && !me && s.Phase != SessionPhase.Starting;
                string name = CoopProfile.DisplayName(p) + " <color=#1c213380><size=26>#" + p.tag + "</size></color>";
                if (p.isHost) name += "  <color=#2a4fa0><size=24>" + Loc.T("coop.host") + "</size></color>";
                if (me) name += "  <color=#e0731c><size=24>" + Loc.T("coop.you") + "</size></color>";
                var label = UIKit.Label(seat.transform, "Name", name, 36, UITheme.Ink, TextAnchor.MiddleLeft, true);
                label.supportRichText = true;
                UIKit.Place(label.rectTransform, new Vector2(0f, 1f), new Vector2(124f, -12f), new Vector2(LeftWidth - (removable ? 300f : 200f), 54f), new Vector2(0f, 1f));
                UIKit.Fit(label, 22);
                if (removable)
                {
                    uint uid = p.uid;
                    string who = CoopProfile.FullName(p);
                    var remove = UIKit.Button(seat.transform, "Remove", Loc.T("coop.remove"), UITheme.Locked, () =>
                        CoopStagePicker.Confirm(Controller.CanvasRoot, Loc.F("coop.confirmRemove", who), () => Session.RemovePlayer(uid), "coop.yesRemove"), 24);
                    UIKit.Place((RectTransform)remove.transform, new Vector2(1f, 1f), new Vector2(-16f, -10f), new Vector2(150f, 50f), new Vector2(1f, 1f));
                }
                string state = !p.connected ? Loc.T("coop.standing.lost") : p.ready ? Loc.T("coop.ready") : Loc.T("coop.notReady");
                var st = UIKit.Label(seat.transform, "State", state, 28, !p.connected ? UITheme.Red : p.ready ? UITheme.Green : UITheme.InkSoft, TextAnchor.MiddleLeft, true);
                UIKit.Place(st.rectTransform, new Vector2(0f, 0f), new Vector2(124f, 12f), new Vector2(600f, 40f), new Vector2(0f, 0f));
                if (p.ready && p.connected)
                {
                    var check = UIKit.Icon(seat.transform, "Check", ProceduralSprites.Check, UITheme.Green, 56f);
                    if (removable) UIKit.Place(check.rectTransform, new Vector2(1f, 0f), new Vector2(-40f, 8f), new Vector2(46f, 46f), new Vector2(1f, 0f));
                    else UIKit.Place(check.rectTransform, new Vector2(1f, 0.5f), new Vector2(-24f, 0f), new Vector2(56f, 56f), new Vector2(1f, 0.5f));
                }
            }

            // The stage, the location and who chose them; any player may change them.
            float right = RightWidth;
            var stage = Panel(body, "Stage", new Vector2(1f, 1f), new Vector2(-40f, 0f), new Vector2(right, 470f));
            UIKit.SectionLabel(UIKit.Row(stage.transform, "Label", 20f, 46f, 26f, 26f), Loc.T("coop.stage"));
            var sel = s.Selection;
            bool randomRoute = sel.route == CoopSelection.Random || sel.route >= RouteTable.All.Length;
            var route = randomRoute ? null : RouteTable.All[sel.route];
            var title = UIKit.Label(stage.transform, "Route", randomRoute ? Loc.T("coop.random.route") : Loc.T(route.NameKey), 50, UITheme.Navy, TextAnchor.MiddleLeft, true);
            UIKit.Place(title.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -76f), new Vector2(right - 60f, 66f), new Vector2(0f, 1f));
            UIKit.Fit(title, 30);
            var stops = UIKit.Label(stage.transform, "Stops", randomRoute ? Loc.T("coop.random.routeAbout") : StopsLine(route), 26, UITheme.InkSoft, TextAnchor.UpperLeft);
            UIKit.Place(stops.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -148f), new Vector2(right - 60f, 96f), new Vector2(0f, 1f));
            UIKit.Fit(stops, 18);
            bool randomPlace = sel.addOn == CoopSelection.Random || sel.addOn >= CoopLocations.Count;
            var place = randomPlace ? null : CoopLocations.At(sel.addOn);
            var loc = UIKit.Label(stage.transform, "Location", Loc.F("coop.location", randomPlace ? Loc.T("coop.random.place") : Loc.T(place.nameKey) + " · " + Loc.T(place.countryKey)), 30, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(loc.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -252f), new Vector2(right - 60f, 48f), new Vector2(0f, 1f));
            UIKit.Fit(loc, 20);
            var chooser = s.InSlot(sel.chosenBy);
            string by = sel.chosenBy == CoopSelection.Nobody || chooser == null ? Loc.T("coop.chosenByDefault") : Loc.F("coop.chosenBy", CoopProfile.FullName(chooser));
            var byLabel = UIKit.Label(stage.transform, "By", by, 26, chooser != null ? CoopPalette.Of(chooser.slot) * 0.8f + Color.black * 0.2f : UITheme.InkSoft, TextAnchor.MiddleLeft, true);
            UIKit.Place(byLabel.rectTransform, new Vector2(0f, 1f), new Vector2(30f, -304f), new Vector2(right - 380f, 40f), new Vector2(0f, 1f));
            UIKit.Fit(byLabel, 18);
            var change = UIKit.Button(stage.transform, "Change", Loc.T("coop.changeStage"), UITheme.Blue, OpenPicker, 34);
            UIKit.Place((RectTransform)change.transform, new Vector2(1f, 0f), new Vector2(-26f, 30f), new Vector2(320f, 96f), new Vector2(1f, 0f));

            // READY, and what the race is waiting for.
            int connected = 0, ready = 0;
            foreach (var p in s.Players) { if (p.connected) connected++; if (p.connected && p.ready) ready++; }
            string wait = connected < CoopRules.MinPlayers ? Loc.T("coop.wait.players")
                : ready < connected ? Loc.F("coop.wait.ready", ready, connected)
                : Loc.T("coop.wait.starting");
            var waitLabel = UIKit.Label(body, "Wait", wait, 30, Color.white, TextAnchor.MiddleRight, true);
            UIKit.GlassText(waitLabel);
            UIKit.Place(waitLabel.rectTransform, new Vector2(1f, 1f), new Vector2(-40f, -490f), new Vector2(right, 50f), new Vector2(1f, 1f));
            UIKit.Fit(waitLabel, 20);
            bool mine = s.MyReady;
            var readyButton = UIKit.Button(body, "Ready", Loc.T(mine ? "coop.unready.button" : "coop.ready.button"), mine ? UITheme.Locked : UITheme.Green,
                () => Session.SetReady(!Session.MyReady), 56);
            UIKit.Place((RectTransform)readyButton.transform, new Vector2(1f, 0f), new Vector2(-40f, 20f), new Vector2(500f, 150f), new Vector2(1f, 0f));
            var leave = UIKit.Button(body, "Leave", Loc.T("coop.leave"), UITheme.Red, () => ConfirmLeave(() => service.Leave()), 34);
            UIKit.Place((RectTransform)leave.transform, new Vector2(1f, 0f), new Vector2(-570f, 20f), new Vector2(260f, 110f), new Vector2(1f, 0f));
        }

        /// <summary>"Home » Bus stop » Granny's house » Church » Sam's house » School · 5 legs".</summary>
        static string StopsLine(Route route)
        {
            var sb = new StringBuilder(Loc.T(RouteTable.Home.NameKey));
            foreach (string id in route.stops)
            {
                var stop = RouteTable.StopById(id);
                if (stop != null) sb.Append(" » ").Append(Loc.T(stop.NameKey));
            }
            sb.Append(" » ").Append(Loc.T(RouteTable.School.NameKey));
            sb.Append("  ·  ").Append(Loc.F("coop.legs", route.levels.Length));
            return sb.ToString();
        }

        void OpenPicker()
        {
            picking = true;
            CoopStagePicker.Open(Controller.CanvasRoot, Session, Controller.levels, () => picking = false);
        }

        // ---------- Race (back from the gate, or after the race) ----------

        void BuildRace()
        {
            var s = Session;
            bool over = s.Phase == SessionPhase.Over;
            string heading = over ? Loc.T("coop.race.over") : s.Phase == SessionPhase.Loading ? Loc.T("coop.race.loading") : Loc.T("coop.race.on");
            var h = UIKit.Label(body, "Heading", heading, 40, Color.white, TextAnchor.MiddleLeft, true);
            UIKit.GlassText(h);
            UIKit.Place(h.rectTransform, new Vector2(0f, 1f), Vector2.zero, new Vector2(1200f, 64f), new Vector2(0f, 1f));
            var list = UIKit.Rect(body, "Standings");
            UIKit.Place(list, new Vector2(0f, 1f), new Vector2(0f, -80f), new Vector2(Mathf.Min(1100f, BodyWidth - 40f), 440f), new Vector2(0f, 1f));
            CoopStandingsView.Build(list, s, 104f);

            if (over && s.IsHost)
            {
                var again = UIKit.Button(body, "Again", Loc.T("coop.newRace"), UITheme.Green, () => Session.NewRace(), 50);
                UIKit.Place((RectTransform)again.transform, new Vector2(1f, 0f), new Vector2(-40f, 20f), new Vector2(460f, 140f), new Vector2(1f, 0f));
            }
            else
            {
                var note = UIKit.Label(body, "Note", Loc.T(over ? "coop.race.waitHost" : "coop.race.watch"), 30, Color.white, TextAnchor.MiddleRight, true);
                UIKit.GlassText(note);
                UIKit.Place(note.rectTransform, new Vector2(1f, 0f), new Vector2(-40f, 60f), new Vector2(800f, 60f), new Vector2(1f, 0f));
                UIKit.Fit(note, 20);
            }
            var leave = UIKit.Button(body, "Leave", Loc.T("coop.leave"), UITheme.Red, () => ConfirmLeave(() => service.Leave()), 34);
            UIKit.Place((RectTransform)leave.transform, new Vector2(0f, 0f), new Vector2(0f, 20f), new Vector2(260f, 110f), new Vector2(0f, 0f));
        }

        // ---------- Helpers ----------

        static Image Panel(RectTransform parent, string name, Vector2 anchor, Vector2 position, Vector2 size)
        {
            var face = UIKit.Card(parent, name, UITheme.Paper);
            UIKit.Place((RectTransform)face.transform.parent, anchor, position, size, new Vector2(anchor.x, 1f));
            return face;
        }

        void ConfirmLeave(System.Action leave)
        {
            string key = Session.FinishUnconfirmed ? "coop.confirmLeave.unseen"
                : Session.InSession && Session.MyStatus == PlayerStatus.Racing ? "coop.confirmLeave.race" : "coop.confirmLeave";
            CoopStagePicker.Confirm(Controller.CanvasRoot, Loc.T(key), leave);
        }

        void OnNotice(CoopNotice n)
        {
            string name = n.player != null ? CoopProfile.FullName(n.player) : "";
            string text = null;
            switch (n.type)
            {
                case NoticeType.PlayerJoined: text = Loc.F("coop.toast.joined", name); break;
                case NoticeType.PlayerLeft: text = Loc.F("coop.feed.left", name); break;
                case NoticeType.PlayerLost: text = Loc.F("coop.feed.lost", name); break;
                case NoticeType.PlayerBack: text = Loc.F("coop.feed.back", name); break;
                case NoticeType.SelectionChanged: if (n.player != null) text = Loc.F("coop.toast.stage", name); break;
                case NoticeType.LobbyClosed: text = Loc.T("coop.toast.closed"); break;
                case NoticeType.ConnectFailed: text = Loc.T("coop.toast.connectFailed"); break;
                case NoticeType.HostFailed: text = Loc.T("coop.toast.hostFailed"); break;
                case NoticeType.RadioOff: text = Loc.T("coop.radio.off"); break;
                case NoticeType.Rejected:
                    text = Loc.T(n.code == (int)RejectReason.Full ? "coop.toast.full" : n.code == (int)RejectReason.Version ? "coop.join.version"
                        : n.code == (int)RejectReason.Removed ? "coop.toast.removed" : "coop.toast.inProgress");
                    break;
            }
            Toast(text);
        }

        void Toast(string text)
        {
            if (text == null || toast == null) return;
            toast.text = text;
            toastUntil = Time.unscaledTime + 3f;
        }

        public override void FrameStage(MenuStage stage)
        {
            stage.Frame(MenuShot.Sky, new Rect());
        }
    }
}
