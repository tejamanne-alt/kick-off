using System;
using System.Collections.Generic;
using DribbleToSchool.Art;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Holiday;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using TrackBuilder = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Builds the Holiday Run's scenes, for each city's lap (HolidayStages.Laps: Kamakura's 23 stages, Florida's 9): its stages (one
    /// scene each, at its final place along the lap) and the core scene they are loaded into (LevelBuildKit.BuildHolidayCore).
    /// A Florida stage is built as its leg is, in Florida's streets and climate (LevelBuildKit.Florida, LevelId): its own Miami
    /// district, from the leg's plan moved along to the stage (StreetBuilder.MiamiWindow), the Miami kit's barriers, crates and
    /// checkpoints; the district's distant ground, water and skyline go in the core scene (StreetBuilder.MiamiFarLand).
    ///
    /// A stage scene has exactly one root object, <c>Stage</c>, with a <see cref="RunChunk"/>, inactive in the
    /// file (the world streamer prepares it and switches it on). Under it: the ground and its gaps, the 3D
    /// street, the scenery with its animals, the furniture of the stage (tunnel, crossings, fountains, gulls,
    /// tide, cranes), and three inactive layouts, <c>Layout_A</c> to <c>Layout_C</c>, of obstacles, things to
    /// smash, beats of walkers and dogs, floating targets, coins and power-ups (HolidayPatterns decides what goes where).
    /// </summary>
    public static class HolidayRunBuilder
    {
        public const string Dir = LevelBuildKit.Root + "/Scenes/Holiday";

        /// <summary>The active lap's core scene, and one of its stages.</summary>
        public static string CorePath { get { return Dir + "/" + HolidayStages.CoreSceneName + ".unity"; } }
        public static string StagePath(int stage) { return Dir + "/" + HolidayStages.SceneName(stage) + ".unity"; }

        /// <summary>For each lap, its core scene, then its stages in order: the order they go into the build settings.</summary>
        public static List<string> ScenePaths()
        {
            var paths = new List<string>();
            ForEachLap(lap =>
            {
                paths.Add(CorePath);
                for (int i = 0; i < HolidayStages.Count; i++) paths.Add(StagePath(i));
            });
            return paths;
        }

        /// <summary>Runs <paramref name="step"/> with each lap active in turn (Kamakura's lap is active again afterwards).</summary>
        static void ForEachLap(Action<HolidayStages.Lap> step)
        {
            try
            {
                foreach (var lap in HolidayStages.Laps)
                {
                    HolidayStages.Active = lap;
                    step(lap);
                }
            }
            finally
            {
                HolidayStages.Active = HolidayStages.Kamakura;
            }
        }

        public static bool AllScenesExist()
        {
            foreach (string path in ScenePaths())
                if (AssetDatabase.LoadAssetAtPath<SceneAsset>(path) == null) return false;
            return true;
        }

        /// <summary>
        /// Builds every lap's stages and core scene and returns their paths in build order. The shared assets must
        /// be loaded (LevelBuildKit.LoadShared). A stage that fails to build is logged and skipped, so one bad
        /// stage doesn't cost the rest.
        /// </summary>
        public static List<string> BuildAll(Func<LevelCatalog> catalog, Func<CosmeticCatalog> cosmetics)
        {
            LevelBuildKit.EnsureFolder(Dir);
            try
            {
                ForEachLap(lap =>
                {
                    string city = lap.florida ? "Florida" : "Kamakura";
                    for (int i = 0; i < HolidayStages.Count; i++)
                    {
                        EditorUtility.DisplayProgressBar("Kick Off: Holiday Run (" + city + ")", "Stage " + (i + 1) + " of " + HolidayStages.Count + " (" + HolidayStages.All[i].levelId + ")", i / (float)(HolidayStages.Count + 1));
                        try
                        {
                            BuildStage(i);
                        }
                        catch (Exception e)
                        {
                            Debug.LogError("[Kick Off] Couldn't build " + city + "'s Holiday Run stage " + (i + 1) + ": " + e);
                        }
                    }
                    EditorUtility.DisplayProgressBar("Kick Off: Holiday Run (" + city + ")", "The core scene", HolidayStages.Count / (float)(HolidayStages.Count + 1));
                    // Building the stages may have unloaded assets nothing references: load them again.
                    LevelBuildKit.Cosmetics = cosmetics();
                    LevelBuildKit.Florida = lap.florida;
                    try { LevelBuildKit.BuildHolidayCore(CorePath, catalog()); }
                    finally { LevelBuildKit.Florida = false; LevelBuildKit.LevelId = null; }
                });
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }
            // Open what was saved again and make sure every component's script is found: a scene saved with one that is
            // not cannot be loaded by a player (it stops with 'The file ... is corrupted!'). Reported here, in the editor.
            try
            {
                int missing = SceneScriptCheck.Check(ScenePaths());
                if (missing > 0) Debug.LogError("[Kick Off] The Holiday Run's scenes have " + missing + " components with a missing script: a build would not load them (see the errors above).");
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Kick Off] Couldn't check the Holiday Run's scenes for missing scripts: " + e.Message);
            }
            return ScenePaths();
        }

        // ---------------------------------------------------------------- palettes

        static readonly Color[] CarPaint =
        {
            new Color(0.85f, 0.3f, 0.3f), new Color(0.3f, 0.5f, 0.85f), new Color(0.35f, 0.7f, 0.45f),
            new Color(0.95f, 0.8f, 0.3f), new Color(0.6f, 0.45f, 0.8f), new Color(0.3f, 0.65f, 0.7f),
        };

        static readonly Color[] Coats =
        {
            new Color(0.55f, 0.35f, 0.6f), new Color(0.3f, 0.55f, 0.55f), new Color(0.75f, 0.5f, 0.3f), new Color(0.4f, 0.4f, 0.7f),
            new Color(0.82f, 0.42f, 0.4f), new Color(0.45f, 0.68f, 0.5f),
        };

        static readonly Color[] Furs =
        {
            new Color(0.6f, 0.42f, 0.28f), new Color(0.92f, 0.9f, 0.85f), new Color(0.25f, 0.22f, 0.22f),
        };

        // ---------------------------------------------------------------- one stage

        /// <summary>Builds and saves the scene of one stage of the active lap (Kamakura's 0 to 22, Florida's 0 to 8).</summary>
        public static void BuildStage(int i)
        {
            // A Florida stage is built in its leg's streets and light, as the leg is (GeneratedContent's build of the levels).
            LevelBuildKit.Florida = HolidayStages.IsFlorida;
            LevelBuildKit.LevelId = HolidayStages.IsFlorida ? HolidayStages.All[i].levelId : null;
            try { BuildStageScene(i); }
            finally { LevelBuildKit.Florida = false; LevelBuildKit.LevelId = null; }
        }

        static void BuildStageScene(int i)
        {
            var st = HolidayStages.All[i];
            bool florida = HolidayStages.IsFlorida;
            var plan = HolidayPatterns.Plan(i);
            for (int v = 0; v < HolidayPatterns.Variants; v++)
                foreach (string problem in HolidayPatterns.Validate(plan, v))
                    Debug.LogWarning("[Kick Off] Holiday Run layout: " + problem);

            float from = plan.from, to = plan.to;
            bool first = i == 0, last = i == HolidayStages.Count - 1;
            int prevChapter = first ? 0 : HolidayStages.All[i - 1].chapter;
            int nextChapter = last ? 0 : HolidayStages.All[i + 1].chapter;
            bool urban = st.chapter != 3;
            string where = (florida ? "Florida's " : "") + "Holiday Run stage " + (i + 1) + " (" + st.levelId + ")";

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            LevelBuildKit.Chapter = st.chapter;
            LevelBuildKit.Theme = LevelBuildKit.ThemeFor(st.chapter);   // (with Florida's climate in a Florida stage)

            var stage = new GameObject("Stage");
            var chunk = stage.AddComponent<RunChunk>();
            chunk.stage = i;
            chunk.startX = from;
            chunk.endX = to;

            var t = new TrackBuilder(stage.transform);
            t.AuditName = where;
            t.Coaching.Enabled = false;   // the run has its own first-run tips, not the levels' coach
            // The slabs and sand cover exactly the stage's stretch, padded only at the ends of the world.
            t.SetChunk(first ? from - 70f : from, last ? to + 70f : to,
                !first && prevChapter != st.chapter, !last && nextChapter != st.chapter);

            // Every urban stage ends on a cross street, like a real block; the first after the beach starts on one.
            // The previous stage's street is only kept clear (its far end is built by that stage). Not in Florida: a Miami
            // district's side streets are where its plan has them, and its buildings stand in the stage's seams.
            float firstLotX = from;
            float endStreetFrom = to;
            if (!florida) Attempt(i, "the streets", () =>
            {
                if (urban && !last)
                {
                    t.RunStreet(to - 7f, to);
                    endStreetFrom = to - 7f;
                }
                if (urban && !first && prevChapter == 3)
                {
                    t.RunStreet(from, from + 7f);
                    firstLotX = from + 7.8f;
                }
                else if (urban && !first)
                {
                    t.OpenAreas.Add(new Vector2(from - 7f, from));
                    firstLotX = from + 0.8f;   // lots keep 0.8 m clear of a side street's kerb
                }
            });

            // Ground, with the gaps the plan has.
            var gaps = new List<Vector2>();
            var water = new List<bool>();
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Gap) { gaps.Add(new Vector2(f.x0, f.x1)); water.Add(f.flag); }
            SortGaps(gaps, water);
            Attempt(i, "the ground", () => t.RunGround(from, to, gaps, water));

            // The stage's furniture: the same in every layout.
            foreach (var f in plan.furniture)
            {
                try
                {
                    BuildFurniture(t, f);
                }
                catch (Exception e)
                {
                    Debug.LogWarning("[Kick Off] Holiday Run stage " + (i + 1) + ": couldn't build " + f.kind + " at " + f.x + ": " + e.Message);
                }
            }
            if (st.Has(StageTraits.School)) Attempt(i, "the school gate", () => t.RunSchoolGate(HolidayStages.GateX));

            // The lap starts at the kid's own front door: the house every story level starts in front of (its plot is in the
            // first 14 m, where nothing else stands, and the street's own lots keep out of it).
            if (first) Attempt(i, "the home front", () => t.HomeFront(HolidayStages.SpawnX));

            // A checkpoint in the clear ground at the start of the stage (nothing stands in the first 14 m): a lost ball
            // brings the kid back here, as in a level. It joins the level manager when the stage is switched on.
            Attempt(i, "the checkpoint", () => t.Checkpoint(from + 8f));

            Attempt(i, "the street slabs", () => t.Finish());

            // The street's scenery and animals.
            var street = new GameObject("Street");
            street.transform.SetParent(stage.transform, false);
            var spec = new StreetBuilder.StageSpec
            {
                stage = i,
                from = first ? from - 50f : from,
                to = to,
                seed = 0x7A1 * (i + 1) + st.chapter * 131,
                prevChapter = prevChapter,
                nextChapter = nextChapter,
                firstLotX = firstLotX,
                endStreetFrom = endStreetFrom,
                polesBefore = !first && prevChapter == st.chapter && (st.chapter == 1 || st.chapter == 4),
                polesAfter = !last && nextChapter == st.chapter && (st.chapter == 1 || st.chapter == 4),
                flocks = true,   // birds cross the sky of every stage
                clearing = st.Has(StageTraits.Swings) ? 0 : st.Has(StageTraits.Pond) ? 1 : -1,
                clipLo = prevChapter == 3 ? from : float.NegativeInfinity,
                clipHi = nextChapter == 3 ? to : float.PositiveInfinity,
            };
            if (florida)
            {
                // The district keeps to its stage's own stretch (the world's ends padded), and its near part only: the far
                // ground, water and skyline are the core scene's.
                spec.clipLo = first ? from - 70f : from;
                spec.clipHi = last ? to + 70f : to;
                spec.miami = StreetBuilder.MiamiWindow.Stage(from - FloridaPlanStart(i), spec.clipLo, spec.clipHi);
            }
            try
            {
                StreetBuilder.StageScenery(t, street.transform, spec);
            }
            catch (Exception e)
            {
                Debug.LogError("[Kick Off] " + where + ": the scenery failed: " + e);
            }
            street.AddComponent<StaticBatcher>();
            // The animals live outside the street's static batch; they belong to the stage too.
            if (StreetBuilder.Critters != null) StreetBuilder.Critters.SetParent(stage.transform, false);

            // The three layouts of obstacles, coins and power-ups.
            var layouts = new GameObject[HolidayPatterns.Variants];
            for (int v = 0; v < layouts.Length; v++)
            {
                var layout = new GameObject("Layout_" + (char)('A' + v));
                layout.transform.SetParent(stage.transform, false);
                var layoutBuilder = new TrackBuilder(layout.transform);
                layoutBuilder.Coaching.Enabled = false;
                layoutBuilder.AuditName = where + " layout " + (char)('A' + v);
                BuildLayout(layoutBuilder, plan.layouts[v], i);
                // The layout's walls, barriers and trampolines against what the kid can do (the stage's own builder checked its ground and gaps).
                layoutBuilder.ReportFeasibility();
                layouts[v] = layout;
                layout.SetActive(false);
            }
            chunk.variants = layouts;

            // The streamer wants one root and nothing else.
            foreach (var go in scene.GetRootGameObjects())
            {
                if (go == stage) continue;
                Debug.LogWarning("[Kick Off] Holiday Run stage " + (i + 1) + ": '" + go.name + "' was left outside the Stage object; moved under it.");
                go.transform.SetParent(stage.transform, true);
            }
            stage.SetActive(false);
            EditorSceneManager.SaveScene(scene, StagePath(i));
        }

        /// <summary>
        /// Where in its leg's plan (the leg's own x, StreetBuilder.Miami) a Florida stage's 120 m begin: 8 m before the leg's street
        /// (where its walls start: FloridaLevels), so the stage shows the leg's own street; on the first stage 4 m before it, so the
        /// home stands where the leg has it (the kid starts at HolidayStages.SpawnX, the leg's x 0); on the last, so the school gate
        /// (HolidayStages.GateX) stands where the leg's goal is (Museum Park's, at 106), with the port beside it.
        /// </summary>
        public static float FloridaPlanStart(int stage)
        {
            if (stage == 0) return -HolidayStages.SpawnX;
            if (stage == HolidayStages.Count - 1) return MuseumParkGoal - (HolidayStages.GateX - HolidayStages.StartOf(stage));
            return -8f;
        }

        /// <summary>Where FloridaLevels.MuseumPark (FL3-3, Florida's last leg) has its goal.</summary>
        const float MuseumParkGoal = 106f;

        /// <summary>Runs one step of a stage's build; if it fails the stage still gets saved, without it, and the problem is logged.</summary>
        static void Attempt(int stage, string what, Action step)
        {
            try
            {
                step();
            }
            catch (Exception e)
            {
                Debug.LogError("[Kick Off] Holiday Run stage " + (stage + 1) + ": couldn't build " + what + ": " + e);
            }
        }

        static void SortGaps(List<Vector2> gaps, List<bool> water)
        {
            for (int a = 1; a < gaps.Count; a++)
                for (int b = a; b > 0 && gaps[b].x < gaps[b - 1].x; b--)
                {
                    Vector2 g = gaps[b]; gaps[b] = gaps[b - 1]; gaps[b - 1] = g;
                    bool w = water[b]; water[b] = water[b - 1]; water[b - 1] = w;
                }
        }

        static void BuildFurniture(TrackBuilder t, PatternItem f)
        {
            switch (f.kind)
            {
                case PatternKind.Tunnel: t.RunTunnel(f.x0, f.x1); break;
                case PatternKind.Crossing: t.RunCrossing(f.x0, f.x1, f.a); break;
                case PatternKind.Fountain: t.Fountain(f.x, 0f, f.h, f.a); break;
                case PatternKind.Checkpoint: t.Checkpoint(f.x); break;
                case PatternKind.TideArea: t.RunTide(f.x0, f.x1, f.a, f.b); break;
                case PatternKind.Gull: t.Seagull(f.x0, f.x1, f.y, f.a); break;
                case PatternKind.Cranes: t.RunCrane(f.x); break;
            }
        }

        /// <summary>Builds one layout's obstacles, coins and power-ups into <paramref name="t"/> (whose root is the layout object).</summary>
        static void BuildLayout(TrackBuilder t, List<PatternItem> items, int stage)
        {
            foreach (var it in items)
            {
                try
                {
                    switch (it.kind)
                    {
                        case PatternKind.Hop:
                        case PatternKind.Mid:
                        case PatternKind.Tall: t.RunWall(it.x, it.h, it.w); break;
                        case PatternKind.Crate: t.RunBreakable(it.x); break;
                        case PatternKind.Stack: t.RunStack(it.x); break;
                        case PatternKind.Walkers: t.Pedestrian(it.x0, it.x1, Coats[it.style % Coats.Length], 0f, it.a); break;
                        case PatternKind.DogPatch: t.Dog(it.x0, it.x1, Furs[it.style % Furs.Length], 0f); break;
                        case PatternKind.Balloon: t.RunBalloon(it.x, it.y, it.style, (int)it.a); break;
                        case PatternKind.Star: t.RunStar(it.x, it.y, it.count); break;
                        case PatternKind.Car: t.RunCar(it.x, CarPaint[it.style % CarPaint.Length]); break;
                        case PatternKind.Slide:
                            t.RunSlide(it.x, (TrackBuilder.SlideLook)Enum.Parse(typeof(TrackBuilder.SlideLook), it.look));
                            break;
                        case PatternKind.Puddle: t.Puddle(it.x0, it.x1); break;
                        case PatternKind.SandPatch: t.Sand(it.x0, it.x1); break;
                        case PatternKind.Spring: t.Springboard(it.x); break;
                        case PatternKind.Coin: t.Coin(new Vector2(it.x, it.y)); break;
                        case PatternKind.CoinRow: t.CoinRow(it.x0, it.x1, it.y, it.count); break;
                        case PatternKind.CoinArc: t.CoinArc(it.x0, it.x1, it.y, it.rise, it.count); break;
                        case PatternKind.PowerUp: t.RunPowerUp(it.x, it.y, it.style == (int)PowerUpKind.Turbo ? PowerUpKind.Turbo : PowerUpKind.Magnet); break;
                    }
                }
                catch (Exception e)
                {
                    Debug.LogWarning("[Kick Off] Holiday Run stage " + (stage + 1) + ": couldn't build " + it.kind + " at " + it.x + ": " + e.Message);
                }
            }
        }
    }
}
