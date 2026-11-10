using System.IO;
using UnityEditor;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Player Settings, Active Input Handling: the Input System package only, set from code since ProjectSettings is not in
    /// the repository (docs/LEARNINGS.md, rule 3 and A11). A fresh project defaults to the old Input Manager, which Unity
    /// 6.5 reports on every load as "marked for deprecation". The game reads touches, the mouse and keys through the Input
    /// System (Input/GameInput.cs, with the old Input Manager only as a fallback) and the menus through its
    /// InputSystemUIInputModule (UI/Kit/UIKit.cs); nothing else reads input. So the old handler is switched off here.
    ///
    /// The editor reads the setting when it starts, so after changing it this offers to restart the editor, as Player
    /// Settings does (a build made before the restart already uses the Input System). In batch mode it just applies it.
    /// </summary>
    [InitializeOnLoad]
    public static class InputHandling
    {
        /// <summary>Player Settings' activeInputHandler: 0 the Input Manager (old), 1 the Input System package, 2 both.</summary>
        const int InputSystemOnly = 1;
        const string AskedKey = "DribbleToSchool.InputHandlingRestartAsked";

        static InputHandling()
        {
            EditorApplication.delayCall += Apply;
        }

        [MenuItem("Kick Off/Build/Use the Input System Package")]
        public static void Apply()
        {
            var settings = Unsupported.GetSerializedAssetInterfaceSingleton("PlayerSettings");
            if (settings == null) { Debug.LogWarning("[Kick Off] Player Settings not found: set Active Input Handling to the Input System Package by hand."); return; }
            var so = new SerializedObject(settings);
            var handler = so.FindProperty("activeInputHandler");
            if (handler == null) { Debug.LogWarning("[Kick Off] Player Settings has no activeInputHandler: set Active Input Handling to the Input System Package by hand."); return; }
            if (handler.intValue == InputSystemOnly) { SessionState.EraseBool(AskedKey); return; }
            handler.intValue = InputSystemOnly;
            so.ApplyModifiedPropertiesWithoutUndo();
            AssetDatabase.SaveAssets();
            Debug.Log("[Kick Off] Active Input Handling set to the Input System Package (it takes effect when the editor restarts).");
            if (Application.isBatchMode || SessionState.GetBool(AskedKey, false)) return;
            SessionState.SetBool(AskedKey, true);
            if (EditorUtility.DisplayDialog("Restart Unity",
                    "Kick Off now uses the Input System package only (the old Input Manager is deprecated in Unity 6). " +
                    "The editor needs a restart to switch. Restart now?", "Restart", "Later"))
                EditorApplication.OpenProject(Directory.GetCurrentDirectory());
        }
    }
}
