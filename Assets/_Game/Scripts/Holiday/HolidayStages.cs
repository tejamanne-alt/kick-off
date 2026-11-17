using System;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// What a stage's stretch of street has in it. The editor's Holiday Run builder turns these into
    /// obstacles, hazards and scenery details (HolidayPatterns), with the kit models of the chapter.
    /// </summary>
    [Flags]
    public enum StageTraits
    {
        None = 0,
        /// <summary>Kerbs, stone steps, garden borders: low things to jump.</summary>
        Steps = 1 << 0,
        /// <summary>Crates, planters, hedges, rocks, sandcastles: knee to head high things to jump (the tall ones want a double jump).</summary>
        Crates = 1 << 1,
        /// <summary>Parked cars to hop over.</summary>
        Cars = 1 << 2,
        /// <summary>Things to slide under: the Barriers kit (boards, boom barriers, awnings, scaffolds, boughs...).</summary>
        Awnings = 1 << 3,
        /// <summary>Drain works, trenches, water: jump them (the wide ones want a double jump).</summary>
        Gaps = 1 << 4,
        /// <summary>Puddles that slow you down.</summary>
        Puddles = 1 << 5,
        /// <summary>Soft sand that slows you down.</summary>
        SoftSand = 1 << 6,
        /// <summary>Trampolines with coins up high.</summary>
        Springboards = 1 << 7,
        /// <summary>People strolling along (scenery the kid slips past).</summary>
        Pedestrians = 1 << 8,
        /// <summary>Dogs wandering about (scenery).</summary>
        Dogs = 1 << 9,
        /// <summary>A zebra crossing over a side street with traffic: scenery, never a hazard.</summary>
        Crossing = 1 << 10,
        /// <summary>Gulls swooping about (scenery).</summary>
        Seagulls = 1 << 11,
        /// <summary>The sea washing up the sand (scenery that never reaches the path).</summary>
        Tide = 1 << 12,
        /// <summary>A dim tunnel with lamps.</summary>
        Tunnel = 1 << 13,
        /// <summary>Pallets carried by cranes over trenches.</summary>
        Cranes = 1 << 15,
        /// <summary>Fountain jets that lift you: coins in them.</summary>
        Fountain = 1 << 16,
        /// <summary>Swings over a stream.</summary>
        Swings = 1 << 17,
        /// <summary>A pond with ducks beside the path.</summary>
        Pond = 1 << 18,
        /// <summary>The school gate: the end of the lap.</summary>
        School = 1 << 19,
    }

    /// <summary>
    /// The world of a Holiday Run: one stage for each story level, in story order (Home Street, the
    /// Market, the Beach, the Underpass and building site, the Park and the school), laid end to end
    /// along x as one lap, "a day": at the school gate the next day starts again at home, faster.
    /// Each stage is its own scene, built at its final place in the world, so the hazards and animals
    /// keep their absolute coordinates; the world streamer loads the ones near the kid and unloads
    /// the rest. The editor's builder and the runtime both read this table.
    /// </summary>
    public static class HolidayStages
    {
        public struct Stage
        {
            /// <summary>The story level it stands for ("L01"): its name is the localization key level.L01.</summary>
            public string levelId;
            public int chapter;
            public StageTraits traits;
            /// <summary>How crowded the stage is with obstacles, 0 (relaxed) to 1 (packed): the lap's difficulty curve.</summary>
            public float density;

            public Stage(string levelId, int chapter, StageTraits traits, float density)
            {
                this.levelId = levelId;
                this.chapter = chapter;
                this.traits = traits;
                this.density = density;
            }

            public bool Has(StageTraits t) { return (traits & t) == t; }
        }

        public const int Count = 23;

        /// <summary>Metres of footpath in each stage.</summary>
        public const float StageLength = 120f;

        /// <summary>World x where stage 0 begins. Stages before it (a run-in) are never entered.</summary>
        public const float FirstStageX = 0f;

        /// <summary>Where the kid stands at the start of a day, inside stage 0.</summary>
        public const float SpawnX = 4f;

        /// <summary>No obstacles in the first part of a day or of a stage: time to get going, and to look around.</summary>
        public const float RunIn = 22f, StageRunIn = 14f, StageRunOut = 8f;

        public const string CoreSceneName = "HolidayRun";
        public const string StageScenePrefix = "HolidayRun_S";

        public static readonly Stage[] All =
        {
            // Chapter 1: Home Street
            new Stage("L01", 1, StageTraits.Steps | StageTraits.Crates, 0.28f),
            new Stage("L02", 1, StageTraits.Cars | StageTraits.Awnings | StageTraits.Steps, 0.36f),
            new Stage("L03", 1, StageTraits.Steps | StageTraits.Gaps | StageTraits.Crates, 0.42f),
            new Stage("L04", 1, StageTraits.Crates | StageTraits.Awnings | StageTraits.Pedestrians, 0.48f),
            new Stage("L05", 1, StageTraits.Puddles | StageTraits.Gaps | StageTraits.Crates, 0.54f),
            // Chapter 2: Market
            new Stage("L06", 2, StageTraits.Crates | StageTraits.Awnings | StageTraits.Pedestrians, 0.5f),
            new Stage("L07", 2, StageTraits.Crossing | StageTraits.Pedestrians | StageTraits.Cars | StageTraits.Steps, 0.54f),
            new Stage("L08", 2, StageTraits.Awnings | StageTraits.Crates | StageTraits.Springboards, 0.6f),
            new Stage("L09", 2, StageTraits.Awnings | StageTraits.Crates | StageTraits.Pedestrians, 0.64f),
            new Stage("L10", 2, StageTraits.Crossing | StageTraits.Pedestrians | StageTraits.Crates | StageTraits.Springboards, 0.7f),
            // Chapter 3: The Beach
            new Stage("L11", 3, StageTraits.Gaps | StageTraits.Awnings | StageTraits.Steps, 0.6f),
            new Stage("L12", 3, StageTraits.Tide | StageTraits.SoftSand | StageTraits.Gaps, 0.64f),
            new Stage("L13", 3, StageTraits.Seagulls | StageTraits.SoftSand | StageTraits.Awnings, 0.7f),
            new Stage("L14", 3, StageTraits.SoftSand | StageTraits.Crates | StageTraits.Springboards, 0.76f),
            // Chapter 4: Underpass and building site
            new Stage("L15", 4, StageTraits.Tunnel | StageTraits.Crates | StageTraits.Awnings, 0.7f),
            new Stage("L16", 4, StageTraits.Gaps | StageTraits.Crates | StageTraits.Awnings, 0.76f),
            new Stage("L17", 4, StageTraits.Cranes | StageTraits.Gaps | StageTraits.Awnings, 0.8f),
            new Stage("L18", 4, StageTraits.Tunnel | StageTraits.Pedestrians | StageTraits.Gaps, 0.86f),
            // Chapter 5: Park and school
            new Stage("L19", 5, StageTraits.Crates | StageTraits.Dogs | StageTraits.Awnings, 0.76f),
            new Stage("L20", 5, StageTraits.Fountain | StageTraits.Pedestrians | StageTraits.Springboards | StageTraits.Crates | StageTraits.Awnings, 0.8f),
            new Stage("L21", 5, StageTraits.Swings | StageTraits.Crates | StageTraits.Awnings, 0.86f),
            new Stage("L22", 5, StageTraits.Pond | StageTraits.Gaps | StageTraits.Dogs, 0.92f),
            new Stage("L23", 5, StageTraits.School | StageTraits.Crates | StageTraits.Awnings, 1f),
        };

        /// <summary>The length of one day, from the start of stage 0 to the end of the last stage.</summary>
        public static float LapLength { get { return Count * StageLength; } }

        /// <summary>Where the school gate stands (the end of the day): a little before the last stage ends.</summary>
        public static float GateX { get { return FirstStageX + LapLength - 16f; } }

        public static float StartOf(int stage) { return FirstStageX + stage * StageLength; }
        public static float EndOf(int stage) { return StartOf(stage) + StageLength; }

        /// <summary>The stage that covers world x (clamped to the first and last).</summary>
        public static int StageAt(float x)
        {
            return Mathf.Clamp(Mathf.FloorToInt((x - FirstStageX) / StageLength), 0, Count - 1);
        }

        /// <summary>0..1 through the whole day at world x.</summary>
        public static float LapProgress(float x)
        {
            return Mathf.Clamp01((x - FirstStageX) / LapLength);
        }

        /// <summary>Scene name of a stage: HolidayRun_S01 ... HolidayRun_S23.</summary>
        public static string SceneName(int stage)
        {
            return StageScenePrefix + (stage + 1).ToString("00");
        }
    }
}
