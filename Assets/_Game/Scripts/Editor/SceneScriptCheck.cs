using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Opens generated scenes again from disk and reports every component whose script can no longer be
    /// found. A scene saved with such a component cannot be loaded by a player: it stops with "The file
    /// '...' is corrupted! Remove it and launch unity again! [Position out of bounds!]", which says nothing
    /// about the cause. Found here, in the editor, it names the scene and the object. The usual cause is a
    /// MonoBehaviour that is not alone in a file named like it (Tests/Editor/ScriptConventionTests).
    /// </summary>
    public static class SceneScriptCheck
    {
        [MenuItem("Kick Off/Check Scenes For Missing Scripts")]
        static void CheckBuildScenes()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var paths = new List<string>();
            foreach (var scene in EditorBuildSettings.scenes)
                if (scene.enabled) paths.Add(scene.path);
            int missing = Check(paths);
            if (missing == 0) Debug.Log("[Kick Off] Checked " + paths.Count + " scenes: every component's script was found.");
            else Debug.LogError("[Kick Off] " + missing + " components have a missing script (see the errors above): a build with them will not load those scenes.");
        }

        /// <summary>
        /// Re-opens each scene and logs an error for every object that holds a component with a missing script.
        /// Returns how many such components there are. The last scene checked is left open.
        /// </summary>
        public static int Check(IList<string> scenePaths)
        {
            int total = 0;
            try
            {
                for (int i = 0; i < scenePaths.Count; i++)
                {
                    EditorUtility.DisplayProgressBar("Kick Off: checking scenes for missing scripts", scenePaths[i], i / (float)scenePaths.Count);
                    var scene = EditorSceneManager.OpenScene(scenePaths[i], OpenSceneMode.Single);
                    int missing = 0;
                    var examples = new List<string>();
                    foreach (var root in scene.GetRootGameObjects())
                    {
                        foreach (var t in root.GetComponentsInChildren<Transform>(true))
                        {
                            int n = GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(t.gameObject);
                            if (n == 0) continue;
                            missing += n;
                            if (examples.Count < 5) examples.Add(t.name);
                        }
                    }
                    if (missing > 0)
                    {
                        Debug.LogError("[Kick Off] " + scenePaths[i] + " has " + missing + " components with a missing script (on: " + string.Join(", ", examples.ToArray())
                            + "). A player cannot load this scene. Look for a MonoBehaviour that is not alone in a file named like it, then Kick Off > Rebuild All Levels.");
                    }
                    total += missing;
                }
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }
            return total;
        }
    }
}
