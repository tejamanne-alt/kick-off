using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.FrontEnd;
using DribbleToSchool.Holiday;
using DribbleToSchool.Levels;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Generates every grey-box scene, level definition and the level catalog.
    /// Runs automatically when the project opens and the generated content is
    /// missing or older than <see cref="Version"/>. Tuning assets are kept;
    /// generated scenes and level definitions are rebuilt from the Levels table.
    /// </summary>
    [InitializeOnLoad]
    public static class GeneratedContent
    {
        /// <summary>Bump when layouts or the scene rig change so scenes regenerate.</summary>
        public const int Version = 131;   // 131: Florida's legs built in their Miami districts at last (the level id was read after the new scene had unloaded its definition, so it was always empty), Miami's arcade canopies raised clear of a double jump's head, the feasibility check takes a step up from one platform to the next; 130: no more brown blocks: platforms are retaining walls with their coping (a lawn bed with shrubs in a park, a paved terrace in a street, a site's concrete with its safety edge) and ramps solid wedges; the market awnings are striped canopies on poles and strand no ball (BallTrap); Miami's arcade canopies stop the ball and shed it; the drawbridges' red lamps are signal heads on masts before the gates; Kamakura's green strip is paint on the asphalt; a Florida leg built without its Miami district now fails the build of the levels; 129: the drawbridges' gates fall across the path and stop the kid and the ball (one-way, away from the hinge); the downpour's rain falls (World/RainCurtain: streaks, splashes, puddle ripples, nothing under the arcades), the light darkens with each burst and the kid runs slower out in one; pigeons and crows fly as themselves (the kite's rig, painted), and Kamakura's beach flocks are kites; Florida's low kerbs are planting beds; puddles mirror the street; 128: no mini-games: Florida's Metrobus, Uncle Rey's Boat and Drugstore legs removed (and the science project's errand with them), its routes three dribbles each, the legs after them renumbered (FL1-3 Brickell Avenue is FL1-2, FL1-4 FL1-3, FL2-3 The Riverwalk FL2-2, FL2-5 Downpour FL2-3: their scenes renamed); 127: Kamakura's home street: the road's lines, drains and manholes on its flush road, not 14 cm under it (docs/LEARNINGS.md E13); 126: Kamakura's own look (the user's brief, docs/KAMAKURA_BRIEF.md: StreetBuilder.Kamakura, the Kamakura and KamakuraStreet kits, Japan's trees, the black kite and the crow): timber-and-mortar homes behind block walls and board fences, chapter 1's green walking strip, the shop lane's noren and lanterns, black pines on the beach, the tram line in chapter 4, the park as a temple ground, low wooded hills; the Florida walk signal's lights found; 125: nothing of Kamakura's in Florida's legs: the slide-unders, the work zone, the crates, the crossing, the signs, the checkpoints, the fountain and the pelican are the Miami kit's (and the Animals kit's Pelican), Riverside Street (FL2-1) is a district of the plan, the people mover's ride is built from the kit, the walkers wear Miami's clothes, Florida's stops have their people, the school is Bayside Elementary; 124: Florida's legs in Miami's own districts (StreetBuilder.Miami from Art/Models/Miami/MiamiDistricts.json, the Miami kit): Little Havana, Brickell, the bayfront, the river, downtown's arcades, the Underline, Biscayne, Museum Park; the Metrobus is the kit's bus with its near side cut away as the kid boards, the street sliding past from Calle Ocho into Brickell; the scooters, chickens, iguanas, domino table, arcades, sweeper, Uncle Rey's boat and the drugstore are kit models; Florida's stops and obstacles are Miami's; the legs' looks moved off the beach and the home seam; 123: Florida's own routes (docs/CITIES.md): FL1 Calle Ocho Bus, FL2 The River Way, FL3 Under the Line, twelve legs FL1-1 to FL3-3 (nine streets with Florida's own play: chickens, iguanas, scooters, pelicans, arcades in a downpour, the street sweeper; three mini-games: the Metrobus, Uncle Rey's boat, the drugstore) and the people mover's ride scene (Ride_peopleMover); the original town's <scene>_FL copies are no longer built, and its layouts lose their Florida branches; 122: the five cities (Progression/Cities): California's <scene>_CA scenes are no longer built (it is not one of the five), and Florida's scenes are built in Florida's climate (a warm 5,000 K sun, teal shade, humid air: CityClimate); 121: the Florida add-on's Home Street: chapter 1's levels each get a <scene>_FL scene (ranch houses and Old Florida cottages, live oaks with Spanish moss, the canal's drawbridge, the lawn sprinklers, the golf cart, the afternoon storm), and every Florida level's home street is Florida's; 120: a WaterSplash trigger at the surface of every trench, stream and tidal channel (the splash shows as things go in, not two metres under the water), the characters rebuilt (large two-colour triangles split, pale stripes and specks settled into their garment or the hair); 119: every model character's rig carries ground points measured from its mesh (CharacterRig keeps them above the ground: no foot or leg through the pavement in a slide, a kick or a crouch), the slide's back knee up with its foot planted, the low flower obstacle a raised bed with a stone kerb, and every character rebuilt with its outfit parts settled (no white or stray patches in a recoloured outfit); 118: the Fields, the Sea and the menu's field cast no shadows, and the distant hills and the clouds receive none (none of it could show: docs/LEARNINGS.md B8); 117: the Florida add-on: chapter 3's levels each get a <scene>_FL scene (the Florida kit's beach town on seawall terraces, Seagrove High at the end), the Coast and Florida kits' palms, Florida's music; 116: white tears at hems, belts and hairlines absorbed too (absorb_tears's second test); 115: the torso on the rig (Hips, Spine, Chest: CharacterRig.Torso turns, sways and breathes the middle of the body); 114: every character's head rigid on the Head bone (faces no longer fold as the head nods), the face shaded round, white tears absorbed into their garments, Mia's right eye mirrored from her left; 113: the kids keep their own scanned faces, with Max's finish (face_ink.py; the drawn faces of 111 were rejected); 112: the kids' and bags' meshes out of the scenes (Resources/Cast, LazyRenderer); 111: polished characters (welded, 32k / 14k triangles, illustrated kids' faces), cameras without HDR or MSAA, the player's thicker outline

        const string ScenesDir = LevelBuildKit.Root + "/Scenes";
        const string LevelsDir = LevelBuildKit.Root + "/Levels";
        const string VersionFile = ScenesDir + "/GeneratedContentVersion.txt";
        const string TestTrackScene = ScenesDir + "/Phase1_TestTrack.unity";
        const string FrontEndScene = ScenesDir + "/" + FrontEndController.SceneName + ".unity";
        const string CosmeticsDir = LevelBuildKit.Root + "/Cosmetics";
        /// <summary>The generated content's version this editor session last checked (and built, if it had to).</summary>
        const string AutoBuildKey = "DribbleToSchool.AutoBuildCheckedVersion";

        struct LevelSpec
        {
            public int chapter;
            public string id, name, scene;
            public float bell;
            public int streak;
            public bool challenge;
            public Action<TrackBuilder> layout;
            /// <summary>The city whose level it is (Progression.Cities' id).</summary>
            public string city;
            /// <summary>The street look (1 to 5: the chapter whose street, mood and kit the builder dresses it in).</summary>
            public int look;

            public LevelSpec(int chapter, string id, string name, string scene, float bell, int streak, Action<TrackBuilder> layout)
            {
                this.chapter = chapter; this.id = id; this.name = name; this.scene = scene;
                this.bell = bell; this.streak = streak; this.layout = layout;
                challenge = false;
                city = Progression.Cities.KamakuraId;
                look = chapter;
            }

            /// <summary>
            /// One of Florida's own legs (docs/CITIES.md: FL1-1...), built in Florida's streets (LevelBuildKit.Florida set): its own district
            /// from the Miami plan (StreetBuilder.Miami), in the light and the ground's rules of chapter <paramref name="look"/>.
            /// </summary>
            public static LevelSpec Florida(string id, string name, string scene, int look, float bell, int streak, Action<TrackBuilder> layout)
            {
                var spec = new LevelSpec(RouteTable.FloridaChapter, id, name, scene, bell, streak, layout);
                spec.city = Progression.Cities.FloridaId;
                spec.look = look;
                return spec;
            }

            public bool IsFlorida { get { return city == Progression.Cities.FloridaId; } }

            /// <summary>An optional ball-skill challenge (no bell; the objective sets the stars).</summary>
            public static LevelSpec Challenge(int chapter, string id, string name, string scene, Action<TrackBuilder> layout)
            {
                var spec = new LevelSpec(chapter, id, name, scene, 0f, 0, layout);
                spec.challenge = true;
                return spec;
            }

            public string ScenePath { get { return ScenesDir + "/Levels/" + scene + ".unity"; } }
        }

        /// <summary>
        /// A story level's bell: the seconds its street takes (as tuned in the table) and the walk from the stop it starts at that every
        /// story level starts with (<see cref="HomeLeadInRules.BellSeconds"/>), so the bell and the stars mean what they did before.
        /// </summary>
        static float Bell(float streetSeconds)
        {
            return streetSeconds + HomeLeadInRules.BellSeconds;
        }

        static readonly LevelSpec[] Levels =
        {
            // Chapter 1: Home Street
            new LevelSpec(1, "L01", "Out the Door", "L01_OutTheDoor", Bell(50f), 3, GreyboxLevels.OutTheDoor),
            new LevelSpec(1, "L02", "Parked Cars", "L02_ParkedCars", Bell(55f), 3, GreyboxLevels.ParkedCars),
            new LevelSpec(1, "L03", "Up the Hill", "L03_UpTheHill", Bell(80f), 4, GreyboxLevels.UpTheHill),
            new LevelSpec(1, "L04", "Garden Gate", "L04_GardenGate", Bell(60f), 3, GreyboxLevels.GardenGate),
            new LevelSpec(1, "L05", "Puddle Lane", "L05_PuddleLane", Bell(80f), 4, GreyboxLevels.PuddleLane),
            LevelSpec.Challenge(1, "C01", "Keepy-Uppy", "C01_KeepyUppy", GreyboxLevels.KeepyUppy),
            // Chapter 2: Market and Crossings
            new LevelSpec(2, "L06", "Market Morning", "L06_MarketMorning", Bell(60f), 4, GreyboxLevels.MarketMorning),
            new LevelSpec(2, "L07", "First Crossing", "L07_FirstCrossing", Bell(70f), 3, GreyboxLevels.FirstCrossing),
            new LevelSpec(2, "L08", "Corner Shop", "L08_CornerShop", Bell(70f), 4, GreyboxLevels.CornerShop),
            new LevelSpec(2, "L09", "Fruit Stalls", "L09_FruitStalls", Bell(75f), 5, GreyboxLevels.FruitStalls),
            new LevelSpec(2, "L10", "Rush Hour", "L10_RushHour", Bell(95f), 6, GreyboxLevels.RushHour),
            LevelSpec.Challenge(2, "C02", "Window Shopping", "C02_WindowShopping", GreyboxLevels.WindowShopping),
            // Chapter 3: The Beach
            new LevelSpec(3, "L11", "Boardwalk", "L11_Boardwalk", Bell(70f), 4, GreyboxLevels.Boardwalk),
            new LevelSpec(3, "L12", "Low Tide", "L12_LowTide", Bell(75f), 4, GreyboxLevels.LowTide),
            new LevelSpec(3, "L13", "Seagull Bay", "L13_SeagullBay", Bell(80f), 5, GreyboxLevels.SeagullBay),
            new LevelSpec(3, "L14", "Sandcastle Sprint", "L14_SandcastleSprint", Bell(95f), 6, GreyboxLevels.SandcastleSprint),
            LevelSpec.Challenge(3, "C03", "Beach Slalom", "C03_BeachSlalom", GreyboxLevels.BeachSlalom),
            // Chapter 4: Underpass & Construction
            new LevelSpec(4, "L15", "Station Dash", "L15_TheUnderpass", Bell(65f), 4, GreyboxLevels.TheUnderpass),
            new LevelSpec(4, "L16", "Building Site", "L16_BuildingSite", Bell(80f), 5, GreyboxLevels.BuildingSite),
            new LevelSpec(4, "L17", "Cranes", "L17_Cranes", Bell(85f), 4, GreyboxLevels.Cranes),
            new LevelSpec(4, "L18", "Tunnel Run", "L18_TunnelRun", Bell(105f), 6, GreyboxLevels.TunnelRun),
            LevelSpec.Challenge(4, "C04", "Site Targets", "C04_SiteTargets", GreyboxLevels.SiteTargets),
            // Chapter 5: Park & School
            new LevelSpec(5, "L19", "Park Gates", "L19_ParkGates", Bell(65f), 5, GreyboxLevels.ParkGates),
            new LevelSpec(5, "L20", "Fountain Square", "L20_FountainSquare", Bell(75f), 5, GreyboxLevels.FountainSquare),
            new LevelSpec(5, "L21", "Playground", "L21_Playground", Bell(80f), 5, GreyboxLevels.Playground),
            new LevelSpec(5, "L22", "Duck Pond", "L22_DuckPond", Bell(80f), 6, GreyboxLevels.DuckPond),
            new LevelSpec(5, "L23", "The Final Bell", "L23_TheFinalBell", Bell(120f), 7, GreyboxLevels.TheFinalBell),
            LevelSpec.Challenge(5, "C05", "Juggle Champion", "C05_JuggleChampion", GreyboxLevels.JuggleChampion),

            // Florida (Miami): the city's own three routes, from the ranch house in Little Havana to Bayside Elementary (docs/CITIES.md).
            // Each leg's street is its own district (StreetBuilder.Miami, from Art/Models/Miami/MiamiDistricts.json); the look is only
            // the light and the ground's rules: the legs that start at home look as the home street does (no seam into another
            // chapter's street), and none is the beach's (its sand and tides are not Miami's river or bay).
            // FL1 Calle Ocho Bus (the bus from Calle Ocho to Brickell Avenue is not played: FL1-2 starts at the stop where it's left)
            LevelSpec.Florida("FL1-1", "Little Havana Morning", "FL1-1_LittleHavana", 1, Bell(70f), 4, FloridaLevels.LittleHavana),
            LevelSpec.Florida("FL1-2", "Brickell Avenue", "FL1-2_BrickellAvenue", 4, Bell(80f), 5, FloridaLevels.BrickellAvenue),
            LevelSpec.Florida("FL1-3", "Bayfront to School", "FL1-3_Bayfront", 5, Bell(80f), 5, FloridaLevels.Bayfront),
            // FL2 The River Way
            LevelSpec.Florida("FL2-1", "Riverside Street", "FL2-1_RiversideStreet", 1, Bell(70f), 4, FloridaLevels.RiversideStreet),
            LevelSpec.Florida("FL2-2", "The Riverwalk", "FL2-2_Riverwalk", 5, Bell(85f), 5, FloridaLevels.Riverwalk),
            LevelSpec.Florida("FL2-3", "Downpour to School", "FL2-3_Downpour", 2, Bell(90f), 6, FloridaLevels.Downpour),
            // FL3 Under the Line (the people mover between its first two legs: Levels/Rides)
            LevelSpec.Florida("FL3-1", "The Underline", "FL3-1_Underline", 1, Bell(75f), 5, FloridaLevels.Underline),
            LevelSpec.Florida("FL3-2", "Biscayne Boulevard", "FL3-2_BiscayneBoulevard", 4, Bell(75f), 5, FloridaLevels.BiscayneBoulevard),
            LevelSpec.Florida("FL3-3", "Museum Park to School", "FL3-3_MuseumPark", 5, Bell(85f), 6, FloridaLevels.MuseumPark),
        };

        /// <summary>
        /// (id, chapter, isChallenge, scene name) for each of Kamakura's entries of the level table (the original town's 23 levels
        /// and 5 challenges). Used by tests; Florida's are <see cref="CityLevelTable"/>.
        /// </summary>
        public static List<KeyValuePair<string, int>> LevelTable(out List<bool> isChallenge, out List<string> scenes)
        {
            return CityLevelTable(Progression.Cities.KamakuraId, out isChallenge, out scenes);
        }

        /// <summary>The level table's entries of one city (its id as Progression.Cities has it), in story order. Used by tests.</summary>
        public static List<KeyValuePair<string, int>> CityLevelTable(string city, out List<bool> isChallenge, out List<string> scenes)
        {
            var list = new List<KeyValuePair<string, int>>();
            isChallenge = new List<bool>();
            scenes = new List<string>();
            foreach (var spec in Levels)
            {
                if (spec.city != city) continue;
                list.Add(new KeyValuePair<string, int>(spec.id, spec.chapter));
                isChallenge.Add(spec.challenge);
                scenes.Add(spec.scene);
            }
            return list;
        }

        /// <summary>The school bell of a level in the table, in seconds (a challenge has none: 0), or -1 for an unknown id. Used by tests.</summary>
        public static float BellTime(string id)
        {
            foreach (var spec in Levels)
                if (spec.id == id) return spec.bell;
            return -1f;
        }

        /// <summary>Does this level of the table start at a stop with a lead-in (home or a stop on its route)? Every story level does; a challenge does not. Used by tests.</summary>
        public static bool HasLeadIn(string id)
        {
            foreach (var spec in Levels)
                if (spec.id == id) return HomeLeadInRules.HasLeadIn(true, spec.challenge);
            return false;
        }

        static GeneratedContent()
        {
            EditorApplication.delayCall += AutoBuild;
        }

        static void AutoBuild()
        {
            // Once per version in an editor session, not once per session: a pull with the editor open recompiles the scripts
            // and comes back here with a newer Version, and the levels must be rebuilt then. Checked only on the first load,
            // the phone was built from levels several versions old (docs/LEARNINGS.md A17).
            if (SessionState.GetInt(AutoBuildKey, 0) >= Version) return;
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorApplication.delayCall += AutoBuild;
                return;
            }
            SessionState.SetInt(AutoBuildKey, Version);
            if (!OutOfDate) return;

            Debug.Log("[Kick Off] Generated content is missing or out of date (built v" + ReadVersion() + ", the code is v" + Version + "). Building levels...");
            BuildAll();
        }

        /// <summary>
        /// The levels on disk were built by an older version of this code (or some are missing): a player built now would ship
        /// them as they were. BuildScripts rebuilds them first, and Unity's own Build button refuses (GeneratedContentBuildCheck).
        /// </summary>
        public static bool OutOfDate { get { return ReadVersion() < Version || !AllScenesExist(); } }

        /// <summary>The version the levels on disk were built by (0 if never).</summary>
        public static int BuiltVersion { get { return ReadVersion(); } }

        [MenuItem("Kick Off/Rebuild All Levels")]
        static void RebuildFromMenu()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            BuildAll();
        }

        [MenuItem("Kick Off/Open Level 1")]
        static void OpenFirstLevel()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(Levels[0].ScenePath);
        }

        [MenuItem("Kick Off/Open Menu (FrontEnd)")]
        static void OpenFrontEnd()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(FrontEndScene);
        }

        /// <summary>Rebuild only the menu scene (its 3D stage), keeping the levels as they are.</summary>
        [MenuItem("Kick Off/Rebuild Menu (FrontEnd)")]
        static void RebuildFrontEnd()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            LevelBuildKit.LoadShared();
            var catalog = AssetDatabase.LoadAssetAtPath<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
            var cosmetics = AssetDatabase.LoadAssetAtPath<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset");
            if (catalog == null || cosmetics == null)
            {
                BuildAll();
                return;
            }
            LevelBuildKit.Cosmetics = cosmetics;
            BuildFrontEndScene(catalog, cosmetics);
        }

        /// <summary>
        /// Rebuild only the Holiday Run (its 23 stage scenes and the core scene), keeping the levels and the
        /// menu as they are, and put its scenes in the build settings after the others.
        /// </summary>
        [MenuItem("Kick Off/Rebuild Holiday Run")]
        static void RebuildHolidayRun()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            LevelBuildKit.LoadShared();
            if (LoadCatalog() == null || LoadCosmetics() == null)
            {
                BuildAll();
                return;
            }
            LevelBuildKit.Cosmetics = LoadCosmetics();
            var holiday = HolidayRunBuilder.BuildAll(LoadCatalog, LoadCosmetics);
            var scenes = new List<EditorBuildSettingsScene>();
            foreach (var scene in EditorBuildSettings.scenes)
                if (!scene.path.StartsWith(HolidayRunBuilder.Dir + "/")) scenes.Add(scene);
            foreach (string path in holiday) scenes.Add(new EditorBuildSettingsScene(path, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            AssetDatabase.SaveAssets();
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(FrontEndScene) != null) EditorSceneManager.OpenScene(FrontEndScene);
            Debug.Log("[Kick Off] Built the Holiday Run: its core scene and " + HolidayStages.Count + " stages.");
        }

        static LevelCatalog LoadCatalog() { return AssetDatabase.LoadAssetAtPath<LevelCatalog>(LevelsDir + "/LevelCatalog.asset"); }
        static CosmeticCatalog LoadCosmetics() { return AssetDatabase.LoadAssetAtPath<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset"); }

        [MenuItem("Kick Off/Reset Save Data")]
        static void ResetSave()
        {
            Progression.SaveSystem.ResetProgress();
            Debug.Log("[Kick Off] Save data reset: " + Progression.SaveSystem.FilePath);
        }

        [MenuItem("Kick Off/Give 1000 Coins (testing)")]
        static void GiveCoins()
        {
            Progression.SaveSystem.AddCoins(1000);
            Progression.SaveSystem.Save();
        }

        static readonly ChapterInfo[] Chapters =
        {
            new ChapterInfo { number = 1, title = "Home Street", subtitle = "Out the door and down the road", color = new Color(0.97f, 0.55f, 0.27f) },
            new ChapterInfo { number = 2, title = "Market", subtitle = "Crates, crowds and crossings", color = new Color(0.9f, 0.42f, 0.42f) },
            new ChapterInfo { number = 3, title = "The Beach", subtitle = "Sand, waves and seagulls", color = new Color(0.3f, 0.68f, 0.85f) },
            new ChapterInfo { number = 4, title = "Underpass", subtitle = "Tunnels, pipes and building sites", color = new Color(0.55f, 0.48f, 0.72f) },
            new ChapterInfo { number = 5, title = "Park & School", subtitle = "Dogs, fountains and the final bell", color = new Color(0.42f, 0.7f, 0.4f) },
            new ChapterInfo { number = RouteTable.FloridaChapter, title = "Miami", subtitle = "Calle Ocho, the river and the bay", color = new Color(0.13f, 0.7f, 0.68f) },
        };

        public static void BuildAll()
        {
            LevelBuildKit.LoadShared();
            StreetBuilder.MiamiDistrictsBuilt.Clear();
            LevelBuildKit.EnsureFolder(ScenesDir + "/Levels");
            LevelBuildKit.EnsureFolder(LevelsDir);
            var cosmetics = BuildCosmetics();
            LevelBuildKit.Cosmetics = cosmetics;

            var catalog = LevelBuildKit.LoadOrCreateAsset<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
            var defs = new List<LevelDefinition>();
            foreach (var spec in Levels) defs.Add(LoadOrCreateLevel(spec));
            catalog.levels = defs;
            catalog.chapters = new List<ChapterInfo>(Chapters);
            EditorUtility.SetDirty(catalog);
            AssetDatabase.SaveAssets();

            DeleteStaleScenes();
            DeleteStaleDefinitions();

            BuildFrontEndScene(catalog, cosmetics);
            var buildScenes = new List<EditorBuildSettingsScene> { new EditorBuildSettingsScene(FrontEndScene, true) };
            for (int i = 0; i < Levels.Length; i++)
            {
                // Reload shared assets: building the previous scene may have unloaded them.
                var def = AssetDatabase.LoadAssetAtPath<LevelDefinition>(LevelsDir + "/" + Levels[i].id + ".asset");
                catalog = AssetDatabase.LoadAssetAtPath<LevelCatalog>(LevelsDir + "/LevelCatalog.asset");
                LevelBuildKit.Cosmetics = AssetDatabase.LoadAssetAtPath<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset");
                // A city's own level is built in its streets and light (Florida's: LevelBuildKit.Florida set while it is built). The
                // original town's levels no longer get a Florida copy (<scene>_FL): Florida has its own routes (docs/CITIES.md), and
                // California's and Florida's old copies are removed by DeleteStaleScenes.
                LevelBuildKit.Florida = Levels[i].IsFlorida;
                try { LevelBuildKit.BuildScene(Levels[i].ScenePath, def, catalog, Levels[i].layout, Levels[i].look); }
                finally { LevelBuildKit.Florida = false; }
                buildScenes.Add(new EditorBuildSettingsScene(Levels[i].ScenePath, true));
            }
            // The rides between legs (Florida's people mover), each a short scene of its own.
            foreach (string ride in Rides.All)
            {
                string path = ScenesDir + "/Levels/" + Rides.SceneOf(ride) + ".unity";
                LevelBuildKit.Florida = true;
                try { RideBuilder.Build(path, ride); }
                finally { LevelBuildKit.Florida = false; }
                buildScenes.Add(new EditorBuildSettingsScene(path, true));
            }
            LevelBuildKit.BuildScene(TestTrackScene, null, catalog, GreyboxLevels.TestTrack);
            buildScenes.Add(new EditorBuildSettingsScene(TestTrackScene, true));

            // The Holiday Run: its core scene first, then its 23 stages (each loaded into the core as the kid runs).
            foreach (string path in HolidayRunBuilder.BuildAll(LoadCatalog, LoadCosmetics))
                buildScenes.Add(new EditorBuildSettingsScene(path, true));

            EditorBuildSettings.scenes = buildScenes.ToArray();
            BuildScripts.ApplyPlayerSettings();
            // A Florida leg can only be built in its own district (the Miami kit and its plan): without them it would be dressed
            // in a Kamakura chapter's street. Such a build is not finished, so it stays out of date (and can't ship) until the
            // kit is imported and the levels are built again (docs/LEARNINGS.md A17).
            // What was really built decides it, not a separate test of the inputs: the v129 check passed while every Florida leg
            // was built on a Kamakura street (docs/LEARNINGS.md A18).
            var bare = new List<string>();
            foreach (var spec in Levels)
                if (spec.IsFlorida && !StreetBuilder.MiamiDistrictsBuilt.Contains(spec.id)) bare.Add(spec.id);
            if (bare.Count == 0) WriteVersion();
            else
            {
                string message = string.Join(", ", bare.ToArray()) + " were built without their Miami district, on a Kamakura street. The Console's "
                    + "first error says which part is missing. The levels stay out of date, so a build refuses them: fix that and run Kick Off > Rebuild All Levels.";
                Debug.LogError("[Kick Off] " + message);
                if (!Application.isBatchMode) EditorUtility.DisplayDialog("Kick Off: Florida's streets are missing", message, "OK");
            }
            AssetDatabase.SaveAssets();

            EditorSceneManager.OpenScene(FrontEndScene);
            Debug.Log("[Kick Off] Built the menu, " + Levels.Length + " levels (Kamakura's and Florida's), " + Rides.All.Length + " ride(s), the test track and the Holiday Run (its core scene and " + HolidayStages.Count + " stages). The menu is open - press Play.");
        }

        static CosmeticCatalog BuildCosmetics()
        {
            LevelBuildKit.EnsureFolder(CosmeticsDir);
            var catalog = LevelBuildKit.LoadOrCreateAsset<CosmeticCatalog>(CosmeticsDir + "/CosmeticCatalog.asset");
            catalog.items = new List<CosmeticItem>();
            foreach (var row in CosmeticsTable.Rows())
            {
                var item = LevelBuildKit.LoadOrCreateAsset<CosmeticItem>(CosmeticsDir + "/" + row.id + ".asset");
                item.id = row.id;
                item.displayName = row.name;
                item.category = row.category;
                item.rarity = row.rarity;
                item.price = row.price;
                item.pattern = row.pattern;
                item.primary = row.primary;
                item.secondary = row.secondary;
                item.accent = row.accent;
                item.unlock = row.unlock;
                item.unlockValue = row.unlockValue;
                EditorUtility.SetDirty(item);
                catalog.items.Add(item);
            }
            EditorUtility.SetDirty(catalog);
            return catalog;
        }

        /// <summary>
        /// The menu scene: the live 3D stage (LevelBuildKit.BuildMenuStage: the home street, the
        /// teen juggling, real clouds) behind the menus the FrontEndController builds at runtime.
        /// If the stage can't be built, a plain camera, and the menus draw a flat sky instead.
        /// </summary>
        static void BuildFrontEndScene(LevelCatalog catalog, CosmeticCatalog cosmetics)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            try
            {
                LevelBuildKit.BuildMenuStage(cosmetics);
            }
            catch (Exception e)
            {
                Debug.LogError("[Kick Off] Couldn't build the menu's 3D stage; the menu will use a flat backdrop. " + e);
                scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                var camGo = new GameObject("Main Camera");
                camGo.tag = "MainCamera";
                var cam = camGo.AddComponent<Camera>();
                cam.orthographic = true;
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.backgroundColor = LevelBuildKit.SkyColor;
                camGo.AddComponent<AudioListener>();
            }

            var controller = new GameObject("FrontEnd").AddComponent<FrontEndController>();
            controller.levels = catalog;
            controller.cosmetics = cosmetics;
            EditorSceneManager.SaveScene(scene, FrontEndScene);
        }

        static LevelDefinition LoadOrCreateLevel(LevelSpec spec)
        {
            string path = LevelsDir + "/" + spec.id + ".asset";
            var def = AssetDatabase.LoadAssetAtPath<LevelDefinition>(path);
            if (def == null)
            {
                def = ScriptableObject.CreateInstance<LevelDefinition>();
                AssetDatabase.CreateAsset(def, path);
            }
            // The Levels table above is the single source of truth; tune values there.
            def.bellTime = spec.bell;
            def.perfectStreakTarget = spec.streak;
            def.levelId = spec.id;
            def.displayName = spec.name;
            def.sceneName = spec.scene;
            def.chapter = spec.chapter;
            def.isChallenge = spec.challenge;
            def.city = spec.city;
            EditorUtility.SetDirty(def);
            return def;
        }

        /// <summary>Remove generated level scenes that are no longer in the Levels table.</summary>
        static void DeleteStaleScenes()
        {
            var keep = new HashSet<string>();
            foreach (var spec in Levels) keep.Add(spec.ScenePath);
            foreach (string ride in Rides.All) keep.Add(ScenesDir + "/Levels/" + Rides.SceneOf(ride) + ".unity");
            foreach (string guid in AssetDatabase.FindAssets("t:Scene", new[] { ScenesDir + "/Levels" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!keep.Contains(path)) AssetDatabase.DeleteAsset(path);
            }
        }

        /// <summary>
        /// Remove level definitions that are no longer in the Levels table (a removed leg's, or one whose id moved: v128's
        /// Florida legs). Nothing else in the folder is touched.
        /// </summary>
        static void DeleteStaleDefinitions()
        {
            var keep = new HashSet<string>();
            foreach (var spec in Levels) keep.Add(LevelsDir + "/" + spec.id + ".asset");
            foreach (string guid in AssetDatabase.FindAssets("t:" + typeof(LevelDefinition).Name, new[] { LevelsDir }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!keep.Contains(path)) AssetDatabase.DeleteAsset(path);
            }
        }

        static bool AllScenesExist()
        {
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(TestTrackScene) == null) return false;
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(FrontEndScene) == null) return false;
            foreach (var spec in Levels)
                if (AssetDatabase.LoadAssetAtPath<SceneAsset>(spec.ScenePath) == null) return false;
            foreach (string ride in Rides.All)
                if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenesDir + "/Levels/" + Rides.SceneOf(ride) + ".unity") == null) return false;
            return HolidayRunBuilder.AllScenesExist();
        }

        static int ReadVersion()
        {
            string path = FullPath(VersionFile);
            if (!File.Exists(path)) return 0;
            int v;
            return int.TryParse(File.ReadAllText(path).Trim(), out v) ? v : 0;
        }

        static void WriteVersion()
        {
            File.WriteAllText(FullPath(VersionFile), Version.ToString());
            AssetDatabase.ImportAsset(VersionFile);
        }

        static string FullPath(string assetPath)
        {
            return Path.Combine(Directory.GetParent(Application.dataPath).FullName, assetPath);
        }
    }
}
