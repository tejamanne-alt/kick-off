#if UNITY_EDITOR || DTS_SCREENSHOTS
using System.Collections;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.Tutorial;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The store screenshot tour. It runs in the Editor from Kick Off > Store Screenshots (Play
    /// mode, at the Game view's resolution), or in a Simulator build made with the DTS_SCREENSHOTS
    /// define (Kick Off > Build > iOS Screenshot Project). Store builds never contain it.
    ///
    /// On launch it stages a well-played save (most levels done, 16 of 23 stickers, their rewards,
    /// some coins), then takes, in English and with no tutorial hints:
    ///   01 the title screen,
    ///   02-06 a level in each chapter: the kid running with the ball from a checkpoint partway
    ///         along (the boy and the girl in turn),
    ///   07 the sticker album, 08 the Locker Room, 09 the chapter map.
    /// Each is saved at the screen's own resolution, without transparency, to Screenshots/WIDTHxHEIGHT/
    /// next to Assets (in the Editor) or in the app's Documents (in the Simulator). Afterwards the
    /// player's own progress and settings are put back.
    /// </summary>
    public class ScreenshotTour : MonoBehaviour
    {
        /// <summary>Set by the Editor menu for the next Play mode only.</summary>
        public const string EditorFlag = "KickOff.StoreScreenshots";

        /// <summary>Landscape sizes App Store Connect takes for iPhone and iPad screenshots.</summary>
        static readonly Vector2Int[] StoreSizes =
        {
            new Vector2Int(2622, 1206), new Vector2Int(2556, 1179),                                // iPhone, medium display
            new Vector2Int(2868, 1320), new Vector2Int(2796, 1290), new Vector2Int(2736, 1260),   // iPhone, large display
            new Vector2Int(2752, 2064), new Vector2Int(2732, 2048),                                // iPad 13"
            new Vector2Int(1920, 1080), new Vector2Int(3840, 2160),                                // Google Play phone (16:9)
        };

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Begin()
        {
#if UNITY_EDITOR && !DTS_SCREENSHOTS
            if (!UnityEditor.SessionState.GetBool(EditorFlag, false)) return;
            UnityEditor.SessionState.SetBool(EditorFlag, false);
#endif
            var go = new GameObject("ScreenshotTour");
            DontDestroyOnLoad(go);
            go.AddComponent<ScreenshotTour>();
        }

        /// <summary>Stickers found per chapter in the staged save (16 of 23).</summary>
        static readonly int[] StickersPerChapter = { 5, 4, 3, 2, 2 };
        /// <summary>Who plays each chapter's shot, in turn.</summary>
        static readonly string[] Players = { "boy", "girl", "boy", "girl", "girl" };

        LevelCatalog levels;
        CosmeticCatalog cosmetics;
        string folder;
        int saved;
        bool done;
        string error;
        bool storeSize;

        // The player's own state, put back after the tour.
        string savedGame, savedCharacter, savedLanguage;
        readonly List<string> unseenHints = new List<string>();

        IEnumerator Start()
        {
            // The first scene is the menu: its controller has the catalogs.
            FrontEndController menu = null;
            float until = Time.realtimeSinceStartup + 30f;
            while (menu == null && Time.realtimeSinceStartup < until)
            {
                menu = Find<FrontEndController>();
                if (menu == null) yield return null;
            }
            if (menu == null || menu.levels == null)
            {
                Fail("The menu scene didn't load, so there's nothing to photograph.");
                yield break;
            }
            levels = menu.levels;
            cosmetics = menu.cosmetics;

#if UNITY_EDITOR
            string root = Path.Combine(Directory.GetParent(Application.dataPath).FullName, "Screenshots");
#else
            string root = Path.Combine(Application.persistentDataPath, "Screenshots");
#endif
            folder = Path.Combine(root, Screen.width + "x" + Screen.height);
            Directory.CreateDirectory(folder);
            storeSize = System.Array.IndexOf(StoreSizes, new Vector2Int(Screen.width, Screen.height)) >= 0;
            Debug.Log("[Screenshots] Saving to " + folder);
            if (!storeSize)
                Debug.LogWarning("[Screenshots] " + Screen.width + "x" + Screen.height + " isn't a store size: set the Game view to 2622x1206 (iPhone), 2752x2064 (iPad) or 1920x1080 (Google Play).");

            Remember();
            Loc.SetLanguage("en");
            TutorialHint.MarkAllSeen();
            StageSave();
            yield return Wait(3f);   // the launch splash

            // 01: the title screen.
            GameSettings.Character = "boy";
            FrontEndController.Open(FrontEndScreenId.Title);
            yield return Wait(3.5f);
            yield return Capture("01_title");

            // 02-06: a level in every chapter.
            int shot = 2;
            for (int chapter = 1; chapter <= 5; chapter++)
            {
                var level = ShowcaseLevel(chapter);
                if (level == null) continue;
                yield return Gameplay(level, Players[(chapter - 1) % Players.Length],
                    shot.ToString("00") + "_chapter" + chapter + "_" + level.levelId);
                shot++;
            }

            // The menus.
            GameSettings.Character = "boy";
            FrontEndController.Open(FrontEndScreenId.Album);
            yield return Wait(3f);
            yield return Capture(shot.ToString("00") + "_album");
            shot++;

            FrontEndController.Open(FrontEndScreenId.Shop);
            yield return Wait(3f);
            yield return Capture(shot.ToString("00") + "_locker_room");
            shot++;

            FrontEndController.Open(FrontEndScreenId.Map, 3);
            yield return Wait(3f);
            yield return Capture(shot.ToString("00") + "_map");

            Restore();
            FrontEndController.Open(FrontEndScreenId.Title);
            done = true;
            Debug.Log("[Screenshots] Done: " + saved + " screenshots in " + folder);
#if UNITY_EDITOR
            yield return Wait(1.5f);
            UnityEditor.EditorUtility.RevealInFinder(folder);
            UnityEditor.EditorApplication.isPlaying = false;
#endif
        }

        /// <summary>Note the player's progress and settings, to put back afterwards.</summary>
        void Remember()
        {
            savedGame = JsonUtility.ToJson(SaveSystem.Data, true);
            savedCharacter = GameSettings.Character;
            savedLanguage = GameSettings.Language;
            unseenHints.Clear();
            foreach (var id in TutorialHint.AllIds)
                if (!TutorialHint.Seen(id)) unseenHints.Add(id);
        }

        void Restore()
        {
            try
            {
                File.WriteAllText(SaveSystem.FilePath, savedGame);
                SaveSystem.Load();
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Screenshots] Couldn't put the save back: " + e.Message);
            }
            GameSettings.Character = savedCharacter;
            GameSettings.Language = savedLanguage;
            TutorialHint.ResetAll(unseenHints);
        }

        /// <summary>A save that looks well played: chapters 1-4 done, chapter 5 under way, 16 stickers and their rewards.</summary>
        void StageSave()
        {
            var data = SaveSystem.Data;
            data.coins = 1280;
            data.stickers.Clear();
            data.levels.Clear();
            data.levelsCompleted = 0;
            data.fullGameUnlocked = true;

            for (int chapter = 1; chapter <= 5; chapter++)
            {
                int stickers = StickersPerChapter[chapter - 1], index = 0;
                var inChapter = levels.LevelsInChapter(chapter);
                for (int i = 0; i < inChapter.Count; i++)
                {
                    var level = inChapter[i];
                    if (level == null) continue;
                    bool completed = chapter < 5 || i < 2;
                    if (completed)
                        SaveSystem.RecordLevel(level.levelId, i % 4 == 3 ? 2 : 3, Mathf.Max(10f, level.bellTime * 0.7f), 0, i % 3 != 2);
                    if (!level.isChallenge && index++ < stickers) SaveSystem.AddSticker(level.levelId);
                }
            }

            // The rewards those stickers earn, granted now so no celebration covers the menu.
            StickerRewards.GrantEarned(levels, cosmetics);
            if (cosmetics != null)
            {
                var ball = StickerRewards.ForChapter(cosmetics, 1);
                if (ball != null && ball.category == CosmeticCategory.Ball && SaveSystem.Owns(ball.id)) data.equippedBall = ball.id;
            }
            SaveSystem.Save();
        }

        /// <summary>The middle story level of a chapter (a good stretch of its streets).</summary>
        LevelDefinition ShowcaseLevel(int chapter)
        {
            var story = new List<LevelDefinition>();
            foreach (var level in levels.LevelsInChapter(chapter))
                if (level != null && !level.isChallenge) story.Add(level);
            return story.Count > 0 ? story[story.Count / 2] : null;
        }

        /// <summary>Play the level from a checkpoint partway along, run right with the ball for a moment, and take the picture.</summary>
        IEnumerator Gameplay(LevelDefinition level, string player, string file)
        {
            GameSettings.Character = player;
            LevelManager.LoadLevel(level);

            LevelManager manager = null;
            float until = Time.realtimeSinceStartup + 40f;
            while (Time.realtimeSinceStartup < until)
            {
                manager = LevelManager.Current;
                if (manager != null && manager.level == level && manager.State == LevelState.Playing) break;
                yield return null;
            }
            if (manager == null || manager.level != level)
            {
                Debug.LogWarning("[Screenshots] " + level.levelId + " didn't start; skipped.");
                yield break;
            }

            // Run a little from the middle checkpoint; if the ball gets away (a fade back to the
            // checkpoint), try again with a shorter run, then standing still.
            float[] runs = { 1.1f, 0.5f, 0f };
            for (int attempt = 0; attempt < runs.Length; attempt++)
            {
                manager.StartFromCheckpoint(manager.CheckpointCount / 2);
                yield return Wait(0.8f);   // the camera settles
                GameInput.ScriptedMove = 1f;
                yield return Wait(runs[attempt]);
                bool clear = manager.State == LevelState.Playing && manager.FadeAmount < 0.01f;
                if (clear || attempt == runs.Length - 1)
                {
                    yield return Capture(file);
                    GameInput.ScriptedMove = 0f;
                    yield break;
                }
                GameInput.ScriptedMove = 0f;
                yield return Wait(1.5f);   // let the respawn finish
            }
        }

        IEnumerator Capture(string name)
        {
            yield return new WaitForEndOfFrame();
            Texture2D frame = ScreenCapture.CaptureScreenshotAsTexture();
            int width = frame.width, height = frame.height;
            // The stores refuse screenshots with an alpha channel: copy into RGB.
            Texture2D rgb = new Texture2D(width, height, TextureFormat.RGB24, false);
            rgb.SetPixels32(frame.GetPixels32());
            rgb.Apply(false);
            string path = Path.Combine(folder, name + ".png");
            File.WriteAllBytes(path, rgb.EncodeToPNG());
            Debug.Log("[Screenshots] " + path + " (" + width + "x" + height + ")");
            Destroy(frame);
            Destroy(rgb);
            saved++;
        }

        static IEnumerator Wait(float seconds)
        {
            if (seconds > 0f) yield return new WaitForSecondsRealtime(seconds);
        }

        static T Find<T>() where T : Component
        {
            foreach (var root in SceneManager.GetActiveScene().GetRootGameObjects())
            {
                var found = root.GetComponentInChildren<T>();
                if (found != null) return found;
            }
            return null;
        }

        void Fail(string message)
        {
            error = message;
            Debug.LogError("[Screenshots] " + message);
        }

        void OnGUI()
        {
            // Only once the tour is over (or failed), so nothing of this lands in a screenshot.
            if (!done && error == null) return;
            var style = new GUIStyle(GUI.skin.box) { fontSize = Mathf.RoundToInt(Screen.height * 0.035f), wordWrap = true };
            style.normal.textColor = Color.white;
            string text = error ?? ("Store screenshots: " + saved + " saved in Screenshots/" + Screen.width + "x" + Screen.height +
                (storeSize ? "" : "\nThis isn't a store size: use 2622 x 1206 (iPhone), 2752 x 2064 (iPad) or 1920 x 1080 (Google Play)."));
            GUI.Box(new Rect(Screen.width * 0.15f, Screen.height * 0.4f, Screen.width * 0.7f, Screen.height * 0.2f), text, style);
        }
    }
}
#endif
