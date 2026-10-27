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
    public enum FrontEndScreenId { Title, Map, Shop, Album }

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
        public virtual string Title { get { return ""; } }
    }

    /// <summary>
    /// Runs the menu scene: animated storybook backdrop, a shared header with
    /// back button and wallet, and the Title / Map / Shop screens.
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

        void Start()
        {
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.SystemSetting;   // menus may dim; levels keep the screen on
            TimeControl.ResetTime();

            var canvas = UIKit.CreateCanvas("FrontEndCanvas", 0);
            var root = (RectTransform)canvas.transform;
            canvasRoot = root;
            MenuBackdrop.Build(root);

            screenLayer = UIKit.Stretch(UIKit.Rect(root, "Screens"));
            BuildHeader(root);

            screens[FrontEndScreenId.Title] = new TitleScreen();
            screens[FrontEndScreenId.Map] = new ChapterMapScreen();
            screens[FrontEndScreenId.Shop] = new ShopScreen();
            screens[FrontEndScreenId.Album] = new AlbumScreen();

            SaveSystem.Changed += RefreshWallet;
            Loc.Changed += OnLanguageChanged;
            Show(RequestedScreen);
            RequestedScreen = FrontEndScreenId.Title;

            if (!splashShown)
            {
                splashShown = true;
                Splash.Show(root);
            }
        }

        void OnDestroy()
        {
            SaveSystem.Changed -= RefreshWallet;
            Loc.Changed -= OnLanguageChanged;
        }

        /// <summary>Rebuild every screen so text appears in the new language.</summary>
        void OnLanguageChanged()
        {
            foreach (var kv in screens)
            {
                if (kv.Value.Root != null) Destroy(kv.Value.Root.gameObject);
            }
            screens[FrontEndScreenId.Title] = new TitleScreen();
            screens[FrontEndScreenId.Map] = new ChapterMapScreen();
            screens[FrontEndScreenId.Shop] = new ShopScreen();
            screens[FrontEndScreenId.Album] = new AlbumScreen();
            Show(current);
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
                if (kv.Value.Root != null) kv.Value.Root.gameObject.SetActive(false);
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

            var back = UIKit.Button(header, "Back", "<", UITheme.Paper, Back, 64, UITheme.Ink);
            UIKit.Place((RectTransform)back.transform, new Vector2(0f, 0.5f), new Vector2(50f, 0f), new Vector2(120f, 110f), new Vector2(0f, 0.5f));
            backButton = back.gameObject;

            headerTitle = UIKit.Title(header, "Title", "", 64, Color.white);
            UIKit.Place(headerTitle.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(1000f, 120f));

            var walletCard = UIKit.Card(header, "Wallet", UITheme.Paper);
            UIKit.Place((RectTransform)walletCard.transform.parent, new Vector2(1f, 0.5f), new Vector2(-50f, 0f), new Vector2(300f, 100f), new Vector2(1f, 0.5f));
            wallet = UIKit.CoinAmount(walletCard.transform, "Coins", 0, 52, UITheme.Ink);
            UIKit.Stretch((RectTransform)wallet.transform.parent, 10f);
        }

        void RefreshWallet()
        {
            if (wallet != null) wallet.text = SaveSystem.Data.coins.ToString();
        }
    }
}
