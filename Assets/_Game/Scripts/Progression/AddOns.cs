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
        /// <summary>
        /// The chapters built in its streets (null: every one). While it is the active add-on, the levels of the
        /// other chapters stay locked (LevelUnlocks.NotInTown): Florida has only the beach so far.
        /// </summary>
        public readonly int[] chapters;

        public AddOn(string id, string nameKey, string placeKey, string sceneSuffix, bool available, Audio.MusicCountry music, bool needsEveryLevel,
            int[] chapters = null)
        {
            this.chapters = chapters;
            this.id = id;
            this.nameKey = nameKey;
            this.placeKey = placeKey;
            this.sceneSuffix = sceneSuffix;
            this.available = available;
            this.music = music;
            this.needsEveryLevel = needsEveryLevel;
        }

        public bool Unlocked { get { return available && (!needsEveryLevel || AddOns.EveryLevelFinished); } }

        /// <summary>Its streets have this chapter's levels (every chapter when it lists none).</summary>
        public bool HasChapter(int chapter) { return chapters == null || System.Array.IndexOf(chapters, chapter) >= 0; }

        /// <summary>It has only some of the chapters (the map says the others are still to come).</summary>
        public bool Partial { get { return chapters != null; } }
    }

    /// <summary>
    /// The add-ons: the same levels in another country's streets, with that country's music, chosen in
    /// Add-ons and Filters (UI/AddOnsPanel, from the title screen). The original is Kamakura, Japan (a seaside town south
    /// of Tokyo: its shop signs, concrete poles, block walls and the railway). California (Santa Monica)
    /// is unlocked by finishing every story level; each level has a California scene built beside the
    /// original (&lt;scene&gt;_CA, Editor/StreetBuilder.Coast). Florida (a Space Coast beach town on the A1A) is
    /// unlocked the same way and so far has only chapter 3, the beach (&lt;scene&gt;_FL, Editor/StreetBuilder.Florida):
    /// while it is chosen, the other chapters' levels are locked. India and a Tokyo city add-on are still to come.
    /// The filters (a look over the whole picture, drawn by World/PostFX) are listed beside them: the
    /// original look, the comic halftone (a printed comic: cel bands, halftone dots, an ink line,
    /// colour plates out of register, paper), the pencil sketch (pencil lines and hatching on paper,
    /// the kids kept in colour) and the classic cartoon (inked cels over a painted background: World/ClassicLook).
    /// A filter applies at once, in every scene, and to the menus' pictures and buttons (FilterChanged).
    /// </summary>
    public static class AddOns
    {
        public const string OriginalId = "original";
        public const string CaliforniaId = "california";
        /// <summary>What a level's California scene adds to its scene's name.</summary>
        public const string CaliforniaSuffix = "_CA";
        public const string FloridaId = "florida";
        /// <summary>What a level's Florida scene adds to its scene's name.</summary>
        public const string FloridaSuffix = "_FL";
        /// <summary>The chapters Florida's streets have so far: the beach (Seaside Road).</summary>
        public static readonly int[] FloridaChapters = { 3 };

        public static readonly AddOn Original = new AddOn(OriginalId, "addon.original", "addon.original.place", "", true, Audio.MusicCountry.Japan, false);
        public static readonly AddOn California = new AddOn(CaliforniaId, "addon.california", "addon.california.place", CaliforniaSuffix, true, Audio.MusicCountry.California, true);
        public static readonly AddOn Florida = new AddOn(FloridaId, "addon.florida", "addon.florida.place", FloridaSuffix, true, Audio.MusicCountry.Florida, true,
            FloridaChapters);

        public static readonly AddOn[] All =
        {
            Original,
            California,
            Florida,
            new AddOn("india", "addon.india", "addon.india.place", "_IN", false, Audio.MusicCountry.Japan, true),
            new AddOn("japan", "addon.japan", "addon.japan.place", "_JP", false, Audio.MusicCountry.Japan, true),
        };

        public const string OriginalFilter = "original";
        public const string ComicFilter = "comic";
        public const string SketchFilter = "sketch";
        public const string ClassicFilter = "classic";

        /// <summary>The filters: the original look, the comic halftone, the pencil sketch and the classic cartoon.</summary>
        public static readonly string[] Filters = { OriginalFilter, ComicFilter, SketchFilter, ClassicFilter };

        /// <summary>Raised when the filter is changed (the menus' pictures and buttons follow it at once).</summary>
        public static event System.Action FilterChanged;

        /// <summary>The classic cartoon filter is chosen.</summary>
        public static bool ClassicOn { get { return Filter == ClassicFilter; } }

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

        /// <summary>The active add-on's streets have this chapter's levels (the original and California have every chapter).</summary>
        public static bool InTown(int chapter) { return Active.HasChapter(chapter); }

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
                bool changed = SaveSystem.Data.filter != value;
                SaveSystem.Data.filter = value;
                SaveSystem.Save();
                if (changed && FilterChanged != null) FilterChanged();
            }
        }

        /// <summary>The scene to load for a level's scene: its scene for the active add-on, when the build has one.</summary>
        public static string SceneFor(string scene)
        {
            return SceneFor(scene, Active);
        }

        /// <summary>
        /// The scene to load for a level's scene in <paramref name="a"/>'s streets (a co-op race runs in the location one player
        /// chose for everyone, whatever each phone has chosen or unlocked for itself), when the build has one.
        /// </summary>
        public static string SceneFor(string scene, AddOn a)
        {
            if (a == null) a = Original;
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
