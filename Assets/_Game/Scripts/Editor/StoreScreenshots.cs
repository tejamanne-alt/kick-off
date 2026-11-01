using DribbleToSchool.FrontEnd;
using UnityEditor;
using UnityEditor.SceneManagement;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kick Off > Store Screenshots: the store screenshot tour (FrontEnd/ScreenshotTour) in Play
    /// mode, at the Game view's resolution, saving to Screenshots/WIDTHxHEIGHT next to Assets.
    /// No build, Xcode or Simulator needed.
    /// </summary>
    public static class StoreScreenshots
    {
        const string FrontEndScene = LevelBuildKit.Root + "/Scenes/" + FrontEndController.SceneName + ".unity";

        [MenuItem("Kick Off/Store Screenshots (Play mode)")]
        static void Take()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                EditorUtility.DisplayDialog("Store screenshots", "Stop Play mode first, then choose this again.", "OK");
                return;
            }
            bool start = EditorUtility.DisplayDialog("Store screenshots",
                "First set the Game view to a store size: the resolution menu at the top of the Game view (\"Free Aspect\"), " +
                "then + > Type: Fixed Resolution.\n\n" +
                "    iPhone: 2622 x 1206\n    iPad: 2752 x 2064\n\n" +
                "The game then plays itself for about two minutes and saves 9 pictures to the Screenshots folder next to " +
                "Assets (Finder opens it at the end). Your own progress and settings are put back afterwards.",
                "Start", "Cancel");
            if (!start || !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(FrontEndScene);
            SessionState.SetBool(ScreenshotTour.EditorFlag, true);
            EditorApplication.isPlaying = true;
        }
    }
}
