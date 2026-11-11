using DribbleToSchool.Art;
using DribbleToSchool.Levels;
using UnityEngine;

namespace DribbleToSchool.Progression
{
    /// <summary>
    /// A city's weather and light, relative to Kamakura's (the game's measured look, docs/ART_DIRECTION.md): the colour
    /// temperature of its direct sun and of its shade, and how humid its air is (docs/CITIES.md, "Each city's light and
    /// climate"). It shifts a chapter's mood when that city's scenes are built (Editor/LevelBuildKit.ThemeFor), so it costs
    /// nothing at runtime, and every filter reads it: WorldLook's globals and the grade come before the filters' passes.
    /// </summary>
    public struct CityClimate
    {
        /// <summary>Kamakura's direct sun and shade (a clear May morning): the colour temperatures the chapter moods were measured in.</summary>
        public const float ReferenceSunKelvin = 5400f, ReferenceShadeKelvin = 9000f;

        /// <summary>The direct sun's and the shade's colour temperatures (K).</summary>
        public readonly float sunKelvin, shadeKelvin;
        /// <summary>
        /// -1 very dry (a high plateau: almost no haze, a deeper sky down to the horizon) to 1 tropical (a milky horizon,
        /// haze that starts nearer and reads stronger); 0 is Kamakura's clean sea air.
        /// </summary>
        public readonly float humidity;
        /// <summary>Added to the grade's shadows: the cool (teal or blue) of the shade in a hot, bright place.</summary>
        public readonly Color shadowTint;

        public CityClimate(float sunKelvin, float shadeKelvin, float humidity, Color shadowTint)
        {
            this.sunKelvin = sunKelvin;
            this.shadeKelvin = shadeKelvin;
            this.humidity = Mathf.Clamp(humidity, -1f, 1f);
            this.shadowTint = shadowTint;
        }

        /// <summary>Kamakura's own: changes nothing.</summary>
        public static CityClimate Reference { get { return new CityClimate(ReferenceSunKelvin, ReferenceShadeKelvin, 0f, Color.clear); } }

        public bool IsReference
        {
            get { return sunKelvin == ReferenceSunKelvin && shadeKelvin == ReferenceShadeKelvin && humidity == 0f && shadowTint == Color.clear; }
        }

        /// <summary>
        /// A chapter's mood in this climate: the sun and its glow take the sun's colour temperature, the shade the shade's
        /// (each relative to the reference, keeping its brightness), and humidity pales the horizon and moves the haze.
        /// </summary>
        public ChapterTheme.Mood Apply(ChapterTheme.Mood m)
        {
            if (IsReference) return m;
            Vector3 sun = Shift(ReferenceSunKelvin, sunKelvin), shade = Shift(ReferenceShadeKelvin, shadeKelvin);
            m.sun = Tint(m.sun, sun);
            m.glow = Tint(m.glow, sun);
            m.ambientSky = Tint(m.ambientSky, shade);
            if (humidity > 0f)
            {
                // Wet air: the horizon goes milky, the haze starts nearer, reads stronger and takes a little of the sun's warmth.
                m.horizon = Color.Lerp(m.horizon, new Color(0.86f, 0.89f, 0.9f), 0.32f * humidity);
                m.haze = Color.Lerp(m.haze, Color.Lerp(m.horizon, m.glow, 0.25f), 0.45f * humidity);
                m.hazeStrength = Mathf.Min(0.8f, m.hazeStrength * (1f + 0.35f * humidity));
                m.hazeStart *= 1f - 0.3f * humidity;
                m.hazeEnd *= 1f - 0.2f * humidity;
            }
            else if (humidity < 0f)
            {
                // Dry air: the sky stays deep to the horizon and the far distance stays crisp.
                float d = -humidity;
                m.horizon = Color.Lerp(m.horizon, m.zenith, 0.3f * d);
                m.hazeStrength *= 1f - 0.4f * d;
                m.hazeStart *= 1f + 0.5f * d;
                m.hazeEnd *= 1f + 0.4f * d;
            }
            m.shadowTint = new Color(m.shadowTint.r + shadowTint.r, m.shadowTint.g + shadowTint.g, m.shadowTint.b + shadowTint.b, 0f);
            return m;
        }

        /// <summary>
        /// The linear-light multiplier that turns light of colour temperature <paramref name="from"/> into <paramref name="to"/>
        /// (the Planckian locus: Krystek's approximation, to linear sRGB).
        /// </summary>
        public static Vector3 Shift(float from, float to)
        {
            Vector3 a = Blackbody(from), b = Blackbody(to);
            return new Vector3(b.x / a.x, b.y / a.y, b.z / a.z);
        }

        /// <summary>A blackbody's colour at <paramref name="kelvin"/> (1,000 to 15,000 K) in linear sRGB, with luminance 1.</summary>
        public static Vector3 Blackbody(float kelvin)
        {
            double t = Mathf.Clamp(kelvin, 1000f, 15000f);
            double u = (0.860117757 + 1.54118254e-4 * t + 1.28641212e-7 * t * t) / (1.0 + 8.42420235e-4 * t + 7.08145163e-7 * t * t);
            double v = (0.317398726 + 4.22806245e-5 * t + 4.20481691e-8 * t * t) / (1.0 - 2.89741816e-5 * t + 1.61456053e-7 * t * t);
            double d = 2.0 * u - 8.0 * v + 4.0;
            double x = 3.0 * u / d, y = 2.0 * v / d;
            double X = x / y, Y = 1.0, Z = (1.0 - x - y) / y;
            double r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z;
            double g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z;
            double bl = 0.0557 * X - 0.2040 * Y + 1.0570 * Z;
            return new Vector3((float)System.Math.Max(r, 1e-4), (float)System.Math.Max(g, 1e-4), (float)System.Math.Max(bl, 1e-4));
        }

        /// <summary><paramref name="c"/> (sRGB) times a linear multiplier, brought back to its own brightest channel.</summary>
        static Color Tint(Color c, Vector3 k)
        {
            float r = Mathf.GammaToLinearSpace(c.r) * k.x, g = Mathf.GammaToLinearSpace(c.g) * k.y, b = Mathf.GammaToLinearSpace(c.b) * k.z;
            float before = Mathf.Max(Mathf.GammaToLinearSpace(c.r), Mathf.Max(Mathf.GammaToLinearSpace(c.g), Mathf.GammaToLinearSpace(c.b)));
            float after = Mathf.Max(r, Mathf.Max(g, b));
            float s = after > 0f ? before / after : 1f;
            return new Color(Mathf.LinearToGammaSpace(r * s), Mathf.LinearToGammaSpace(g * s), Mathf.LinearToGammaSpace(b * s), c.a);
        }
    }

    /// <summary>One of the five cities: a chapter of its own, with its own streets, light and music (docs/CITIES.md).</summary>
    public sealed class City
    {
        /// <summary>Saved (SaveData.addOn) and sent in co-op: never change one. Kamakura's is "original", from before the cities.</summary>
        public readonly string id;
        /// <summary>Its name, its country, and a line about its trip to school (Localization keys).</summary>
        public readonly string nameKey, countryKey, aboutKey;
        /// <summary>What a level's scene in its streets adds to the scene's name ("" for Kamakura, the original town).</summary>
        public readonly string sceneSuffix;
        /// <summary>Its story levels can be played (false: listed as coming soon).</summary>
        public readonly bool story;
        /// <summary>The Holiday Run runs in its streets (false: listed as coming soon there).</summary>
        public readonly bool holidayRun;
        /// <summary>Whose music plays with it (Audio/MusicGenerator).</summary>
        public readonly Audio.MusicCountry music;
        /// <summary>Unlocked by finishing every one of Kamakura's story levels (Kamakura needs nothing).</summary>
        public readonly bool needsEveryLevel;
        /// <summary>
        /// The chapters its streets have so far (null: every one). While it is the active city, the other chapters' levels stay
        /// locked (LevelUnlocks.NotInTown): Florida has Home Street and the beach.
        /// </summary>
        public readonly int[] chapters;
        /// <summary>Its light and weather (applied when its scenes are built).</summary>
        public readonly CityClimate climate;
        /// <summary>The colour of its card's band in the city picker.</summary>
        public readonly Color colour;

        public City(string id, string sceneSuffix, bool story, bool holidayRun, Audio.MusicCountry music, bool needsEveryLevel,
            int[] chapters, CityClimate climate, Color colour)
        {
            this.id = id;
            nameKey = "city." + id;
            countryKey = "city." + id + ".country";
            aboutKey = "city." + id + ".about";
            this.sceneSuffix = sceneSuffix;
            this.story = story;
            this.holidayRun = holidayRun;
            this.music = music;
            this.needsEveryLevel = needsEveryLevel;
            this.chapters = chapters;
            this.climate = climate;
            this.colour = colour;
        }

        public bool Unlocked { get { return story && (!needsEveryLevel || Cities.EveryLevelFinished); } }

        /// <summary>Its streets have this chapter's levels (every chapter when it lists none).</summary>
        public bool HasChapter(int chapter) { return chapters == null || System.Array.IndexOf(chapters, chapter) >= 0; }

        /// <summary>It has only some of the chapters (the map says the others are still to come).</summary>
        public bool Partial { get { return chapters != null; } }
    }

    /// <summary>
    /// The five cities (docs/CITIES.md). PLAY and HOLIDAY RUN each ask which city to play in (UI/CityPicker).
    /// - Kamakura, Japan, the original town: every level, and the Holiday Run.
    /// - Florida (Miami), unlocked by finishing every one of Kamakura's story levels. So far it has chapters 1 and 3 in its
    ///   own streets (&lt;scene&gt;_FL, Editor/StreetBuilder.Florida and FloridaHome): while it is chosen, the other chapters'
    ///   levels are locked.
    /// - Madrid, New York and Mumbai: designed, listed as coming soon.
    /// California (Santa Monica, &lt;scene&gt;_CA) was an add-on before the cities and is not one of them: a save that chose
    /// it plays Kamakura. The filters are Progression/Filters.
    /// </summary>
    public static class Cities
    {
        public const string KamakuraId = "original";
        public const string FloridaId = "florida";
        /// <summary>What a level's Florida scene adds to its scene's name.</summary>
        public const string FloridaSuffix = "_FL";
        /// <summary>The chapters Florida's streets have so far: Home Street (a canal suburb) and the beach (Seaside Road).</summary>
        public static readonly int[] FloridaChapters = { 1, 3 };

        public static readonly City Kamakura = new City(KamakuraId, "", true, true, Audio.MusicCountry.Japan, false, null,
            CityClimate.Reference, new Color(0.84f, 0.27f, 0.22f));
        // A hot, humid late-summer morning: a warm 5,000 K sun, teal shade, a milky horizon.
        public static readonly City Florida = new City(FloridaId, FloridaSuffix, true, false, Audio.MusicCountry.Florida, true, FloridaChapters,
            new CityClimate(5000f, 8500f, 0.6f, new Color(-0.004f, 0.002f, 0.006f)), new Color(0.13f, 0.7f, 0.68f));
        // Just after Madrid's late sunrise in early October: a golden 4,200 K sun, clear blue shade, very dry air.
        public static readonly City Madrid = new City("madrid", "_MD", false, false, Audio.MusicCountry.Japan, true, null,
            new CityClimate(4200f, 9500f, -0.8f, new Color(0f, 0f, 0.008f)), new Color(0.86f, 0.5f, 0.16f));
        // A cold, clear late-October morning: a low 4,000 K sun down the cross streets, deep blue canyons.
        public static readonly City NewYork = new City("newyork", "_NY", false, false, Audio.MusicCountry.Japan, true, null,
            new CityClimate(4000f, 10000f, -0.3f, new Color(0f, 0.002f, 0.01f)), new Color(0.95f, 0.75f, 0.12f));
        // The monsoon: an overcast 6,800 K sky, everything wet, sea mist.
        public static readonly City Mumbai = new City("mumbai", "_MB", false, false, Audio.MusicCountry.Japan, true, null,
            new CityClimate(6800f, 7500f, 1f, Color.clear), new Color(0.55f, 0.3f, 0.75f));

        /// <summary>In the order the picker lists them.</summary>
        public static readonly City[] All = { Kamakura, Florida, Madrid, NewYork, Mumbai };

        /// <summary>Every one of Kamakura's story levels finished at least once (every leg of every route to school).</summary>
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

        public static City ById(string id)
        {
            foreach (var c in All)
                if (c.id == id) return c;
            return null;
        }

        /// <summary>The city last chosen (Kamakura when none is saved, or one that isn't a city any more, like California).</summary>
        public static City Selected
        {
            get { return ById(SaveSystem.Data.addOn) ?? Kamakura; }
        }

        /// <summary>The city the levels load in: the chosen one once it can be played, else Kamakura.</summary>
        public static City Active
        {
            get
            {
                var c = Selected;
                return c.Unlocked ? c : Kamakura;
            }
        }

        /// <summary>The active city's streets have this chapter's levels.</summary>
        public static bool InTown(int chapter) { return Active.HasChapter(chapter); }

        /// <summary>Choose a city (only one that can be played is kept); saves.</summary>
        public static void Select(City city)
        {
            if (city == null || !city.Unlocked) return;
            var data = SaveSystem.Data;
            if (data.addOn == city.id && !data.californiaSkin) return;
            data.addOn = city.id;
            data.californiaSkin = false;
            SaveSystem.Save();
        }

        /// <summary>The scene to load for a level's scene: its scene in the active city's streets, when the build has one.</summary>
        public static string SceneFor(string scene)
        {
            return SceneFor(scene, Active);
        }

        /// <summary>
        /// The scene to load for a level's scene in <paramref name="c"/>'s streets (a co-op race runs in the location one player
        /// chose for everyone, whatever each phone has chosen or unlocked for itself), when the build has one.
        /// </summary>
        public static string SceneFor(string scene, City c)
        {
            if (c == null) c = Kamakura;
            if (string.IsNullOrEmpty(scene) || string.IsNullOrEmpty(c.sceneSuffix)) return scene;
            string inCity = scene + c.sceneSuffix;
            return Application.CanStreamedLevelBeLoaded(inCity) ? inCity : scene;
        }

        /// <summary>The city a loaded scene is in (by its name's suffix), so the music matches the streets on screen.</summary>
        public static City OfScene(string sceneName)
        {
            if (!string.IsNullOrEmpty(sceneName))
                foreach (var c in All)
                    if (c.sceneSuffix.Length > 0 && sceneName.EndsWith(c.sceneSuffix)) return c;
            return Kamakura;
        }
    }
}
