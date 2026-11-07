using System.Collections.Generic;
using DribbleToSchool.Levels;
using UnityEngine;

namespace DribbleToSchool.Progression
{
    /// <summary>One way the streets can look: the original town or an add-on set in another country.</summary>
    public sealed class AddOn
    {
        public readonly string id;
        /// <summary>Its name and its city and country (Localization keys).</summary>
        public readonly string nameKey, placeKey;
        /// <summary>What a level's scene for it adds to the scene's name ("" for the original).</summary>
        public readonly string sceneSuffix;
        /// <summary>False for an add-on still to come: it is listed, but cannot be chosen yet.</summary>
        public readonly bool available;
        /// <summary>Whose music plays with it (Audio/MusicGenerator).</summary>
        public readonly Audio.MusicCountry music;
        /// <summary>Unlocked by finishing every story level (the original needs nothing).</summary>
        public readonly bool needsEveryLevel;

        public AddOn(string id, string nameKey, string placeKey, string sceneSuffix, bool available, Audio.MusicCountry music, bool needsEveryLevel)
        {
            this.id = id;
            this.nameKey = nameKey;
            this.placeKey = placeKey;
            this.sceneSuffix = sceneSuffix;
            this.available = available;
            this.music = music;
            this.needsEveryLevel = needsEveryLevel;
        }

        public bool Unlocked { get { return available && (!needsEveryLevel || AddOns.EveryLevelFinished); } }
    }

    /// <summary>
    /// The add-ons: the same levels in another country's streets, with that country's music, chosen in
    /// Settings, Add-ons and Filters (UI/AddOnsPanel). The original is Kamakura, Japan (a seaside town south
    /// of Tokyo: its shop signs, concrete poles, block walls and the railway). California (Santa Monica)
    /// is unlocked by finishing every story level; each level has a California scene built beside the
    /// original (&lt;scene&gt;_CA, Editor/StreetBuilder.Coast). India and a Tokyo city add-on are still to come.
    /// The filters (a look over the whole picture, drawn by World/PostFX) are listed beside them: the
    /// original look and the comic halftone (a printed comic: cel bands, halftone dots, an ink line,
    /// colour plates out of register, paper). A filter applies at once, in every scene.
    /// </summary>
    public static class AddOns
    {
        public const string OriginalId = "original";
        public const string CaliforniaId = "california";
        /// <summary>What a level's California scene adds to its scene's name.</summary>
        public const string CaliforniaSuffix = "_CA";

        public static readonly AddOn Original = new AddOn(OriginalId, "addon.original", "addon.original.place", "", true, Audio.MusicCountry.Japan, false);
        public static readonly AddOn California = new AddOn(CaliforniaId, "addon.california", "addon.california.place", CaliforniaSuffix, true, Audio.MusicCountry.California, true);

        public static readonly AddOn[] All =
        {
            Original,
            California,
            new AddOn("india", "addon.india", "addon.india.place", "_IN", false, Audio.MusicCountry.Japan, true),
            new AddOn("japan", "addon.japan", "addon.japan.place", "_JP", false, Audio.MusicCountry.Japan, true),
        };

        public const string OriginalFilter = "original";
        public const string ComicFilter = "comic";

        /// <summary>The filters: the original look and the comic halftone.</summary>
        public static readonly string[] Filters = { OriginalFilter, ComicFilter };

        /// <summary>Every story level finished at least once (every leg of every route to school).</summary>
        public static bool EveryLevelFinished
        {
            get
            {
                foreach (var route in RouteTable.All)
                    foreach (string id in route.levels)
                        if (!SaveSystem.IsCompleted(id)) return false;
                return true;
            }
        }

        public static AddOn ById(string id)
        {
            foreach (var a in All)
                if (a.id == id) return a;
            return null;
        }

        /// <summary>The add-on chosen in Settings (a save from before the add-ons had only the California switch).</summary>
        public static AddOn Selected
        {
            get
            {
                var data = SaveSystem.Data;
                string id = string.IsNullOrEmpty(data.addOn) ? (data.californiaSkin ? CaliforniaId : OriginalId) : data.addOn;
                return ById(id) ?? Original;
            }
        }

        /// <summary>The add-on the levels load in: the chosen one once it is unlocked, else the original.</summary>
        public static AddOn Active
        {
            get
            {
                var a = Selected;
                return a.Unlocked ? a : Original;
            }
        }

        /// <summary>Choose an add-on (only an unlocked one is kept); saves.</summary>
        public static void Select(AddOn addOn)
        {
            if (addOn == null || !addOn.Unlocked) return;
            var data = SaveSystem.Data;
            data.addOn = addOn.id;
            data.californiaSkin = addOn.id == CaliforniaId;
            SaveSystem.Save();
        }

        /// <summary>The chosen filter (the original when none, or an unknown one, is saved).</summary>
        public static string Filter
        {
            get
            {
                string f = SaveSystem.Data.filter;
                return System.Array.IndexOf(Filters, f) >= 0 ? f : Filters[0];
            }
            set
            {
                if (System.Array.IndexOf(Filters, value) < 0) return;
                SaveSystem.Data.filter = value;
                SaveSystem.Save();
            }
        }

        /// <summary>The scene to load for a level's scene: its scene for the active add-on, when the build has one.</summary>
        public static string SceneFor(string scene)
        {
            var a = Active;
            if (string.IsNullOrEmpty(scene) || string.IsNullOrEmpty(a.sceneSuffix)) return scene;
            string skin = scene + a.sceneSuffix;
            return Application.CanStreamedLevelBeLoaded(skin) ? skin : scene;
        }

        /// <summary>The add-on a loaded scene is in (by its name's suffix), so the music matches the streets on screen.</summary>
        public static AddOn OfScene(string sceneName)
        {
            if (!string.IsNullOrEmpty(sceneName))
                foreach (var a in All)
                    if (a.sceneSuffix.Length > 0 && sceneName.EndsWith(a.sceneSuffix)) return a;
            return Original;
        }
    }
}
