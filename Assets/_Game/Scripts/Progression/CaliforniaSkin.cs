using DribbleToSchool.Levels;
using UnityEngine;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// The California skin: an add-on look for the story levels, unlocked by finishing every one of them
    /// (every leg of every route to school). Each level also has a California scene, built beside the
    /// original (&lt;scene&gt;_CA: stucco villas under tile roofs, Craftsman porches, palms, a pier on the
    /// beach, English shop signs; Editor/StreetBuilder.Coast). With the skin switched on in Settings the
    /// levels load those; off (the default), and always until it is unlocked, the original streets.
    /// </summary>
    public static class CaliforniaSkin
    {
        /// <summary>What a level's California scene adds to its scene's name.</summary>
        public const string SceneSuffix = "_CA";

        /// <summary>Every story level finished at least once.</summary>
        public static bool Unlocked
        {
            get
            {
                foreach (var route in RouteTable.All)
                    foreach (string id in route.levels)
                        if (!SaveSystem.IsCompleted(id)) return false;
                return true;
            }
        }

        /// <summary>Unlocked and switched on in Settings.</summary>
        public static bool Enabled
        {
            get { return SaveSystem.Data.californiaSkin && Unlocked; }
            set
            {
                if (SaveSystem.Data.californiaSkin == value) return;
                SaveSystem.Data.californiaSkin = value;
                SaveSystem.Save();
            }
        }

        /// <summary>The scene to load for a level's scene: its California one while the skin is on and the build has it.</summary>
        public static string SceneFor(string scene)
        {
            if (string.IsNullOrEmpty(scene) || !Enabled) return scene;
            string skin = scene + SceneSuffix;
            return Application.CanStreamedLevelBeLoaded(skin) ? skin : scene;
        }
    }
}
