using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    public enum FrontEndScreenId { Title, Map, Shop, Album, Coop }

    /// <summary>Base for a front-end screen built from code on first show.</summary>
    public abstract class FrontEndScreen
    {
        protected FrontEndController Controller { get; private set; }
        public RectTransform Root { get; private set; }

        public void Create(FrontEndController controller, RectTransform parent, string name)
        {
            Controller = controller;
            Root = UIKit.Stretch(UIKit.Rect(parent, name));
            Build(Root);
        }

        protected abstract void Build(RectTransform root);
        public virtual void OnShow() { }
        public virtual void OnHide() { }
        /// <summary>The screen is being thrown away (rebuilt in another language): unhook events.</summary>
        public virtual void OnDestroyed() { }
        public virtual string Title { get { return ""; } }
        /// <summary>Called every frame while the screen shows (after the stage is framed).</summary>
        public virtual void Tick() { }
        /// <summary>The header's back button: true when the screen dealt with it (asked first, say), else back to the title.</summary>
        public virtual bool HandleBack() { return false; }

        /// <summary>
        /// Where the menu's 3D camera should look while this screen shows (called every frame).
        /// Busy screens look up at the sky, a calm backdrop.
        /// </summary>
        public virtual void FrameStage(MenuStage stage)
        {
            stage.Frame(MenuShot.Sky, new Rect());
        }

        static readonly Vector3[] corners = new Vector3[4];

        /// <summary>A RectTransform of an overlay canvas as a viewport rect (0..1 from the bottom left).</summary>
        protected static Rect ViewportRect(RectTransform rt)
        {
            rt.GetWorldCorners(corners);   // screen pixels on an overlay canvas
            float w = Mathf.Max(1f, Screen.width), h = Mathf.Max(1f, Screen.height);
            return Rect.MinMaxRect(corners[0].x / w, corners[0].y / h, corners[2].x / w, corners[2].y / h);
        }
    }

    /// <summary>
    /// Runs the menu scene: the live 3D street behind everything (MenuStage, built into the
    /// scene by the editor; a flat sky if it's missing), a shared header with back button and
    /// wallet, and the Title / Map / Shop / Album screens. Buttons sit inside the screen's safe
    /// area; each screen tells the stage where to point the camera.
    /// </summary>
    public class FrontEndController : MonoBehaviour
    {
        public const string SceneName = "FrontEnd";

        public LevelCatalog levels;
        public CosmeticCatalog cosmetics;

        /// <summary>Screen to open when the front end loads (set before loading the scene).</summary>
        public static FrontEndScreenId RequestedScreen = FrontEndScreenId.Title;

        /// <summary>Chapter the map should show first (e.g. the one just played).</summary>
        public static int RequestedChapter;

        readonly Dictionary<FrontEndScreenId, FrontEndScreen> screens = new Dictionary<FrontEndScreenId, FrontEndScreen>();
        static bool splashShown;
        RectTransform canvasRoot;
        FrontEndScreenId current;
        RectTransform screenLayer;
        RectTransform header;
        Text headerTitle;
        Text wallet;
        GameObject backButton;

        public static void Open(FrontEndScreenId screen, int chapter = 0)
        {
            RequestedScreen = screen;
            RequestedChapter = chapter;
            TimeControl.ResetTime();
            SceneManager.LoadScene(SceneName);
        }

        /// <summary>
        /// Start the Holiday Run, the endless mode. It is a scene of its own; its pause and results menus
        /// lead back here through <see cref="Open"/> (HolidayRunDirector.QuitToMenu).
        /// </summary>
        public static void OpenHolidayRun()
        {
            if (!Application.CanStreamedLevelBeLoaded(Holiday.HolidayStages.CoreSceneName))
            {
                Debug.LogError("[Holiday Run] The scene '" + Holiday.HolidayStages.CoreSceneName + "' is not in the build settings: rebuild the generated content from the Kick Off menu.");
                return;
            }
            TimeControl.ResetTime();
            SceneManager.LoadScene(Holiday.HolidayStages.CoreSceneName);
        }

        /// <summary>The live 3D backdrop, or null in a scene built without it.</summary>
        public MenuStage Stage { get { return MenuStage.Current; } }

        void Start()
        {
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.SystemSetting;   // menus may dim; levels keep the screen on
            TimeControl.ResetTime();

            var canvas = UIKit.CreateCanvas("FrontEndCanvas", 0);
            var root = (RectTransform)canvas.transform;
            canvasRoot = root;
            MenuBackdrop.Build(root, Stage != null);

            var safe = UIKit.Stretch(UIKit.Rect(root, "SafeArea"));
            safe.gameObject.AddComponent<UISafeArea>();
            screenLayer = UIKit.Stretch(UIKit.Rect(safe, "Screens"));
            BuildHeader(safe);

            CreateScreens();
            SaveSystem.Changed += RefreshWallet;
            Loc.Changed += OnLanguageChanged;
            Show(RequestedScreen);
            RequestedScreen = FrontEndScreenId.Title;

            // Stickers earn Locker Room items: hand out (and celebrate, once) whatever they've
            // earned that the save doesn't own yet, which also brings an older save up to date.
            var earned = StickerRewards.GrantEarned(levels, cosmetics);
            System.Action stickers = () => { if (earned.Count > 0) StickerRewardPanel.Open(root, earned, () => Show(FrontEndScreenId.Shop)); };

            // Walking to school earns a medal for each route walked all the way, the trophy for every way, and Locker Room
            // prizes (Cosmetics/RouteRewards): celebrated once, first, then the stickers' rewards.
            var medals = RouteRewards.NewMedals();
            bool trophy = RouteRewards.TrophyIsNew();
            var prizes = RouteRewards.GrantEarned(cosmetics);
            if (medals.Count > 0 || trophy || prizes.Count > 0)
            {
                RouteRewards.MarkCelebrated(medals, trophy);
                if (medals.Count == 0 && !trophy)
                    foreach (var route in RouteTable.All) if (RouteRewards.IsWalked(route)) medals.Add(route);   // (a new prize alone: the medals so far)
                SchoolRewardPanel.Open(root, levels, cosmetics, medals, trophy, prizes, () => { Show(FrontEndScreenId.Shop); stickers(); }, stickers);
            }
            else stickers();

            if (!splashShown)
            {
                splashShown = true;
                Splash.Show(root);
            }
        }

        void CreateScreens()
        {
            screens[FrontEndScreenId.Title] = new TitleScreen();
            screens[FrontEndScreenId.Map] = new ChapterMapScreen();
            screens[FrontEndScreenId.Shop] = new ShopScreen();
            screens[FrontEndScreenId.Album] = new AlbumScreen();
            screens[FrontEndScreenId.Coop] = new CoopScreen();
        }

        void OnDestroy()
        {
            SaveSystem.Changed -= RefreshWallet;
            Loc.Changed -= OnLanguageChanged;
            foreach (var kv in screens) kv.Value.OnDestroyed();
        }

        /// <summary>Rebuild every screen so text appears in the new language.</summary>
        void OnLanguageChanged()
        {
            foreach (var kv in screens)
            {
                kv.Value.OnDestroyed();
                if (kv.Value.Root != null) Destroy(kv.Value.Root.gameObject);
            }
            CreateScreens();
            Show(current);
        }

        void LateUpdate()
        {
            var stage = Stage;
            if (stage != null && screens.ContainsKey(current) && screens[current].Root != null)
                screens[current].FrameStage(stage);
            if (screens.ContainsKey(current) && screens[current].Root != null && screens[current].Root.gameObject.activeSelf)
                screens[current].Tick();
        }

        public RectTransform CanvasRoot { get { return canvasRoot; } }

        public void OpenSettings()
        {
            SettingsPanel.Open(canvasRoot, null);
        }

        public void OpenCredits()
        {
            CreditsPanel.Open(canvasRoot);
        }

        public void Show(FrontEndScreenId id)
        {
            foreach (var kv in screens)
            {
                if (kv.Value.Root != null && kv.Value.Root.gameObject.activeSelf)
                {
                    kv.Value.Root.gameObject.SetActive(false);
                    kv.Value.OnHide();
                }
            }

            var screen = screens[id];
            if (screen.Root == null) screen.Create(this, screenLayer, id.ToString());
            screen.Root.gameObject.SetActive(true);
            screen.OnShow();
            current = id;

            backButton.SetActive(id != FrontEndScreenId.Title);
            headerTitle.text = screen.Title;
            RefreshWallet();
        }

        public void Back()
        {
            if (screens.ContainsKey(current) && screens[current].HandleBack()) return;
            Show(FrontEndScreenId.Title);
        }

        public void PlayLevel(LevelDefinition def)
        {
            if (def == null) return;
            LevelManager.LoadLevel(def);
        }

        void BuildHeader(RectTransform root)
        {
            header = UIKit.Rect(root, "Header");
            header.anchorMin = new Vector2(0f, 1f);
            header.anchorMax = new Vector2(1f, 1f);
            header.pivot = new Vector2(0.5f, 1f);
            header.sizeDelta = new Vector2(0f, 150f);
            header.anchoredPosition = Vector2.zero;

            var back = UIKit.Button(header, "Back", "<", UITheme.Paper, Back, 64, UITheme.Navy);
            UIKit.Place((RectTransform)back.transform, new Vector2(0f, 0.5f), new Vector2(40f, 4f), new Vector2(116f, 104f), new Vector2(0f, 0.5f));
            backButton = back.gameObject;

            headerTitle = UIKit.Title(header, "Title", "", 66, Color.white);
            // Between the back button and the wallet on any screen from 4:3 up (a long title, the map's, shrinks to fit).
            float aspect = Screen.height > 0 ? (float)Screen.width / Screen.height : 16f / 9f;
            float titleWidth = Mathf.Clamp(UIKit.ReferenceResolution.y * aspect - 2f * 360f, 680f, 1000f);
            UIKit.Place(headerTitle.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, 4f), new Vector2(titleWidth, 120f));
            UIKit.Fit(headerTitle, 40);
            headerTitle.horizontalOverflow = HorizontalWrapMode.Wrap;

            var walletCard = UIKit.Card(header, "Wallet", UITheme.Paper);
            UIKit.Place((RectTransform)walletCard.transform.parent, new Vector2(1f, 0.5f), new Vector2(-40f, 4f), new Vector2(290f, 96f), new Vector2(1f, 0.5f));
            wallet = UIKit.CoinAmount(walletCard.transform, "Coins", 0, 52, UITheme.Ink);
            UIKit.Stretch((RectTransform)wallet.transform.parent, 10f);
        }

        void RefreshWallet()
        {
            if (wallet != null) wallet.text = SaveSystem.Data.coins.ToString();
        }
    }
}
