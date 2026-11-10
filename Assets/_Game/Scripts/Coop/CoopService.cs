using System;
using System.Collections.Generic;
using DribbleToSchool.Coop.Net;
using DribbleToSchool.Coop.Transport;
using DribbleToSchool.Core;
using DribbleToSchool.Levels;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// The co-op mode's one object that outlives scenes (DontDestroyOnLoad): it owns the radio (Bluetooth LE on a phone, a
    /// pretend radio with practice bots in the editor), the session (Coop/Session/CoopSession) and the race across the
    /// route's legs (<see cref="CoopRaceMode"/>), ticks them every frame, and hooks each leg's scene up to the race as it
    /// loads (Coop/CoopLevelLink). The menus (FrontEnd/CoopScreen) and the race's HUD (Coop/CoopHud) read it.
    /// </summary>
    [DefaultExecutionOrder(-60)]
    public class CoopService : MonoBehaviour
    {
        public static CoopService Instance { get; private set; }

        /// <summary>The service, made the first time it is needed (the co-op screen).</summary>
        public static CoopService Ensure()
        {
            if (Instance != null) return Instance;
            var go = new GameObject("CoopService");
            DontDestroyOnLoad(go);
            return go.AddComponent<CoopService>();
        }

        /// <summary>A race is under way on this phone (a leg is loaded or loading).</summary>
        public static bool Racing { get { return Instance != null && LevelManager.Race != null && LevelManager.Race == Instance.race; } }

        ICoopLink link;
        readonly StopwatchClock clock = new StopwatchClock();
        CoopRaceMode race;
        InMemoryRadio editorRadio;
        InMemoryLink editorLink;
        CoopBots bots;
        readonly List<CoopNotice> log = new List<CoopNotice>();

        public CoopSession Session { get; private set; }
        public CoopRaceMode Race { get { return race; } }
        /// <summary>The level table (handed over by the menu or by the first level loaded).</summary>
        public LevelCatalog Catalog { get; set; }
        /// <summary>The editor's practice bots (null on a phone).</summary>
        public CoopBots Bots { get { return bots; } }
        /// <summary>This phone runs the pretend radio (the editor), not Bluetooth.</summary>
        public bool Simulated { get { return editorRadio != null; } }

        /// <summary>Every notice the session raises (the screens show them as toasts).</summary>
        public event Action<CoopNotice> Noticed;

        public RadioState Radio { get { return Session != null ? Session.Radio : RadioState.Unknown; } }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            link = CreateLink();
            Session = new CoopSession(link, clock, CoopProfile.Uid, CoopProfile.Name, CoopProfile.Character, 0, CoopProfile.TagSeed);
            Session.RouteCount = RouteTable.All.Length;
            Session.AddOnCount = CoopLocations.Count;
            Session.ContentHash = ContentHash();
            Session.KeepHostingWhilePaused = Application.platform == RuntimePlatform.IPhonePlayer;
            Session.Noticed += OnNotice;
            Session.PhaseChanged += OnPhase;
            race = new CoopRaceMode(this);
            SceneManager.sceneLoaded += OnSceneLoaded;
            GameSettings.Changed += OnSettingsChanged;
        }

        ICoopLink CreateLink()
        {
            if (Application.isEditor)
            {
                editorRadio = new InMemoryRadio(clock) { PacketSize = 182 };
                editorLink = editorRadio.CreateDevice("you");
                bots = new CoopBots(editorRadio, clock);
                return editorLink;
            }
#if UNITY_IOS
            return new IosBleLink();
#elif UNITY_ANDROID
            return new AndroidBleLink();
#else
            return new UnsupportedLink();
#endif
        }

        void OnDestroy()
        {
            if (Instance != this) return;
            SceneManager.sceneLoaded -= OnSceneLoaded;
            GameSettings.Changed -= OnSettingsChanged;
            if (Session != null) Session.Shutdown();
            if (link != null) link.Shutdown();
            if (LevelManager.Race == race) LevelManager.Race = null;
            Instance = null;
        }

        void OnApplicationQuit()
        {
            if (Session != null && Session.InSession) Session.Leave();
            if (link != null) link.Shutdown();
        }

        void OnApplicationPause(bool paused)
        {
            // A host sent to the background stops hosting at once (CoopSession.SetAppPaused); a player needs nothing.
            if (Session != null) Session.SetAppPaused(paused);
        }

        bool keptAwake;
        float nextIdleTick;

        void Update()
        {
            // A phone that dims and locks drops off the radio: keep the screen on while in a session. (Every frame: a level
            // or a menu may set the system's setting back meanwhile.)
            bool awake = Session.InSession;
            if (awake)
            {
                if (Screen.sleepTimeout != SleepTimeout.NeverSleep) Screen.sleepTimeout = SleepTimeout.NeverSleep;
            }
            else if (keptAwake && LevelManager.Current == null) Screen.sleepTimeout = SleepTimeout.SystemSetting;
            keptAwake = awake;

            // Out of any session and not looking for one, there is only the radio's state to follow: a few times a second.
            bool idle = !Session.InSession && !Session.Browsing && bots == null;
            if (idle && Time.unscaledTime < nextIdleTick) return;
            nextIdleTick = Time.unscaledTime + 0.25f;
            Session.Tick();
            if (bots != null) bots.Tick(race);
            race.Tick();
        }

        /// <summary>
        /// A fingerprint of what the session refers to by index: the kids, the routes and their legs, the locations. Two
        /// phones with different versions of the game would otherwise read the same numbers as different things (another
        /// kid, another route); the host turns away a phone whose fingerprint differs (FNV-1a, 32 bits).
        /// </summary>
        static uint ContentHash()
        {
            uint h = 2166136261u;
            foreach (var kid in PlayerRoster.All) h = Fnv(h, kid.id);
            foreach (var route in RouteTable.All)
            {
                h = Fnv(h, route.id);
                foreach (string level in route.levels) h = Fnv(h, level);
            }
            for (int i = 0; i < CoopLocations.Count; i++) h = Fnv(h, CoopLocations.At(i).id);
            return h != 0 ? h : 1u;
        }

        static uint Fnv(uint h, string s)
        {
            if (s != null)
                foreach (char c in s)
                {
                    h = (h ^ (byte)c) * 16777619u;
                    h = (h ^ (byte)(c >> 8)) * 16777619u;
                }
            return (h ^ 0xFF) * 16777619u;   // (a separator: "ab"+"c" is not "a"+"bc")
        }

        void OnSettingsChanged()
        {
            // The kid picked in the lobby (the player picker) is what the others' ghosts show.
            Session.SetCharacter(CoopProfile.Character);
        }

        void OnNotice(CoopNotice n)
        {
            log.Add(n);
            if (log.Count > 32) log.RemoveAt(0);
            if (Noticed != null) Noticed(n);
            if (n.type == NoticeType.LobbyClosed || n.type == NoticeType.Rejected || n.type == NoticeType.ConnectFailed)
                race.SessionEnded();
        }

        void OnPhase(SessionPhase phase)
        {
            if (Session.Leaving) return;   // (on the way out: the next race is not this phone's)
            if (phase == SessionPhase.Loading) race.Begin(Session.RaceId, Session.RaceSelection);
            else if (phase == SessionPhase.Lobby) race.BackInLobby();
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            // A leg that finished loading after its race was over (back to the lobby, or left, meanwhile): not a level to
            // play on its own.
            if (!race.SceneLoaded(scene))
            {
                FrontEnd.FrontEndController.Open(FrontEnd.FrontEndScreenId.Coop);
                return;
            }
            if (!Racing) return;
            var level = LevelManager.Current;
            if (level == null || level.gameObject.scene != scene) return;
            if (Catalog == null) Catalog = level.catalog;
            var go = new GameObject("CoopLevelLink");
            SceneManager.MoveGameObjectToScene(go, scene);
            go.AddComponent<CoopLevelLink>().Attach(this, race, level);
        }

        // ---------- What the menus call ----------

        /// <summary>The radio is ready, or the reason it isn't (shown on the co-op screen).</summary>
        public bool Ready { get { return Radio == RadioState.On; } }

        /// <summary>Ask for Bluetooth (Android's permissions; iOS asks by itself when Bluetooth starts).</summary>
        public void RequestPermission()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            AndroidBleLink.RequestPermissions(granted => { });
#endif
        }

#if !(UNITY_IOS && !UNITY_EDITOR)
        bool askedForPermission;   // (iOS asks only once, by itself: OpenSettingsIfDenied)
#endif

        /// <summary>
        /// "Allow Bluetooth": the first time the system's own question (Android); after a no (or on iOS, which asks only once,
        /// by itself), the game's page in the phone's settings.
        /// </summary>
        public void OpenSettingsIfDenied()
        {
#if UNITY_IOS && !UNITY_EDITOR
            OpenSettings(false);
#else
            if (askedForPermission) OpenSettings(false);
            askedForPermission = true;
#endif
        }

        /// <summary>The game's page in the phone's settings (after saying no to Bluetooth), or Bluetooth's (to switch it on).</summary>
        public void OpenSettings(bool bluetooth)
        {
#if UNITY_IOS && !UNITY_EDITOR
            IosBleLink.OpenSettings();
#elif UNITY_ANDROID && !UNITY_EDITOR
            var android = link as AndroidBleLink;
            if (android != null) { if (bluetooth) android.OpenBluetoothSettings(); else android.OpenSettings(); }
#endif
        }

        /// <summary>Android before 12: scanning needs Location switched on.</summary>
        public bool LocationOff
        {
            get
            {
                var android = link as AndroidBleLink;
                return android != null && android.LocationNeededAndOff;
            }
        }

        public void Host()
        {
            Session.SetName(CoopProfile.Name);
            Session.SetCharacter(CoopProfile.Character);
            Session.Host();
            race.Reset();
            if (bots != null) bots.JoinLobby(Mathf.Clamp(PlayerPrefs.GetInt("coop.editorBots", 2), 1, CoopRules.MaxPlayers - 1));
        }

        public void Browse()
        {
            if (bots != null && bots.Count == 0) bots.HostLobby(Mathf.Clamp(PlayerPrefs.GetInt("coop.editorBots", 2), 1, CoopRules.MaxPlayers - 1));
            Session.Browse();
        }

        public void StopBrowsing()
        {
            Session.StopBrowsing();
            if (bots != null && !Session.InSession) bots.Clear();
        }

        public void Join(CoopRoom room)
        {
            if (room == null) return;
            Session.SetName(CoopProfile.Name);
            Session.SetCharacter(CoopProfile.Character);
            race.Reset();
            Session.Join(room.address);
        }

        /// <summary>Leave the lobby or the race (a finished time is kept by the others), and stop the bots.</summary>
        public void Leave()
        {
            Session.Leave();
            race.Reset();
            if (bots != null) bots.Clear();
        }

        /// <summary>Editor: switch this phone's pretend Bluetooth off or on (to try the race's resilience).</summary>
        public void SimulateRadio(bool on)
        {
            if (editorRadio != null) editorRadio.SetPower(editorLink, on);
        }

        public bool SimulatedRadioOn { get { return editorLink == null || editorLink.State == RadioState.On; } }
    }

    /// <summary>A link that never works: a platform with no Bluetooth plugin (the menus say Co-op is unsupported).</summary>
    public sealed class UnsupportedLink : ICoopLink
    {
        bool told;
        public RadioState State { get { return RadioState.Unsupported; } }
        public int MaxPacket { get { return CoopFraming.MinPacket; } }
        public void StartHost(RoomBeacon beacon) { }
        public void UpdateBeacon(RoomBeacon beacon) { }
        public void StopHost() { }
        public void Kick(int peer) { }
        public void StartScan() { }
        public void StopScan() { }
        public void Connect(string address) { }
        public void Disconnect() { }
        public void Send(int peer, byte[] packet) { }
        public bool Poll(out LinkEvent e)
        {
            e = new LinkEvent { type = LinkEventType.Radio, state = RadioState.Unsupported };
            if (told) return false;
            told = true;
            return true;
        }
        public void Shutdown() { }
    }

    /// <summary>The locations a race can run in: the add-ons that exist (Progression/AddOns), by index on the wire.</summary>
    public static class CoopLocations
    {
        static List<Progression.AddOn> list;

        static List<Progression.AddOn> List
        {
            get
            {
                if (list == null)
                {
                    list = new List<Progression.AddOn>();
                    foreach (var a in Progression.AddOns.All) if (a.available) list.Add(a);
                }
                return list;
            }
        }

        public static int Count { get { return List.Count; } }

        public static Progression.AddOn At(int index)
        {
            return index >= 0 && index < List.Count ? List[index] : Progression.AddOns.Original;
        }

        public static int IndexOf(Progression.AddOn a)
        {
            int i = List.IndexOf(a);
            return i < 0 ? 0 : i;
        }
    }
}
