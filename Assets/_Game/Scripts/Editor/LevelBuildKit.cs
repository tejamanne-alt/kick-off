using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Core;
using DribbleToSchool.Hazards;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Levels;
using DribbleToSchool.Player;
using DribbleToSchool.Tuning;
using DribbleToSchool.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Shared pieces for generating grey-box level scenes: placeholder sprites,
    /// tuning assets, physics materials and the fully wired gameplay rig.
    /// </summary>
    public static class LevelBuildKit
    {
        public const string Root = "Assets/_Game";
        const string ArtDir = Root + "/Art/Placeholder";
        const string SettingsDir = Root + "/Settings";
        const string PhysicsDir = Root + "/Physics";

        public static readonly Color SkyColor = new Color(0.80f, 0.91f, 0.98f);
        public static readonly Color GroundColor = new Color(0.45f, 0.42f, 0.38f);
        public static readonly Color ObstacleColor = new Color(0.62f, 0.56f, 0.50f);
        public static readonly Color CrateColor = new Color(0.78f, 0.58f, 0.33f);
        public static readonly Color BouncyColor = new Color(0.90f, 0.40f, 0.40f);
        public static readonly Color PitColor = new Color(0.22f, 0.20f, 0.22f);
        public static readonly Color WaterColor = new Color(0.30f, 0.55f, 0.85f);
        static readonly Color KidColor = new Color(0.20f, 0.45f, 0.85f);
        static readonly Color SkinColor = new Color(0.98f, 0.80f, 0.65f);
        static readonly Color SchoolColor = new Color(0.95f, 0.75f, 0.30f);

        public static Sprite Square { get; private set; }
        public static Sprite Circle { get; private set; }
        public static PhysicsMaterial2D GroundMat { get; private set; }
        public static PhysicsMaterial2D BouncyMat { get; private set; }
        public static PhysicsMaterial2D CrateMat { get; private set; }
        static PhysicsMaterial2D kidMat;
        static BallTuning ballTuning;
        static PlayerTuning playerTuning;
        static Font signFont;

        /// <summary>Create or load every shared asset. Call once before building scenes.</summary>
        public static void LoadShared()
        {
            EnsureFolder(ArtDir);
            EnsureFolder(SettingsDir);
            EnsureFolder(PhysicsDir);

            Square = LoadOrCreateSprite(ArtDir + "/Square.png", 64, false);
            Circle = LoadOrCreateSprite(ArtDir + "/Circle.png", 128, true);
            ballTuning = LoadOrCreateAsset<BallTuning>(SettingsDir + "/BallTuning.asset");
            playerTuning = LoadOrCreateAsset<PlayerTuning>(SettingsDir + "/PlayerTuning.asset");
            GroundMat = LoadOrCreateMaterial(PhysicsDir + "/Ground.physicsMaterial2D", 0.6f, 0f);
            BouncyMat = LoadOrCreateMaterial(PhysicsDir + "/Bouncy.physicsMaterial2D", 0.2f, 0.9f);
            kidMat = LoadOrCreateMaterial(PhysicsDir + "/Kid.physicsMaterial2D", 0f, 0f);
            CrateMat = LoadOrCreateMaterial(PhysicsDir + "/Crate.physicsMaterial2D", 0.5f, 0.1f);
            signFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        }

        /// <summary>
        /// Build and save one level scene: camera, input, the track from
        /// <paramref name="layout"/>, kid, ball, kick aimer, level manager and HUD.
        /// </summary>
        public static void BuildScene(string scenePath, LevelDefinition def, LevelCatalog catalog, Action<TrackBuilder> layout)
        {
            EnsureFolder(Path.GetDirectoryName(scenePath).Replace('\\', '/'));
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 5.5f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = SkyColor;
            camGo.AddComponent<AudioListener>();
            camGo.transform.position = new Vector3(3f, 2f, -10f);
            var follow = camGo.AddComponent<CameraFollow2D>();

            var input = new GameObject("GameInput").AddComponent<GameInput>();
            input.worldCamera = cam;

            var track = new TrackBuilder(new GameObject("Level").transform);
            layout(track);
            if (track.StartCheckpoint == null) throw new InvalidOperationException("Layout must call Start().");

            Vector2 kidSpawn = track.StartCheckpoint.KidSpawnPosition;
            Vector2 ballSpawn = track.StartCheckpoint.BallSpawnPosition;

            // Kid
            var kidGo = new GameObject("Kid");
            kidGo.transform.position = kidSpawn;
            var kidBody = kidGo.AddComponent<Rigidbody2D>();
            kidBody.mass = 1f;
            var capsule = kidGo.AddComponent<CapsuleCollider2D>();
            capsule.size = new Vector2(0.5f, 1.2f);
            capsule.sharedMaterial = kidMat;
            Visual(kidGo.transform, "Body", Square, new Vector2(0f, -0.15f), new Vector2(0.5f, 0.9f), KidColor, 10);
            Visual(kidGo.transform, "Head", Circle, new Vector2(0f, 0.38f), new Vector2(0.42f, 0.42f), SkinColor, 11);
            Visual(kidGo.transform, "Eye", Circle, new Vector2(0.11f, 0.42f), new Vector2(0.07f, 0.07f), Color.black, 12);
            var feet = new GameObject("Feet").transform;
            feet.SetParent(kidGo.transform, false);
            feet.localPosition = new Vector3(0f, -0.6f, 0f);
            var kid = kidGo.AddComponent<KidController>();
            kid.tuning = playerTuning;
            kid.feet = feet;

            // Ball
            var ballGo = new GameObject("Ball");
            ballGo.transform.position = ballSpawn;
            ballGo.AddComponent<Rigidbody2D>();
            var circleCol = ballGo.AddComponent<CircleCollider2D>();
            circleCol.radius = 0.2f;
            Color patch = new Color(0.15f, 0.15f, 0.15f);
            Visual(ballGo.transform, "Shell", Circle, Vector2.zero, new Vector2(0.4f, 0.4f), Color.white, 20);
            Visual(ballGo.transform, "Patch", Circle, new Vector2(0.08f, 0.06f), new Vector2(0.12f, 0.12f), patch, 21);
            Visual(ballGo.transform, "Patch2", Circle, new Vector2(-0.09f, -0.07f), new Vector2(0.09f, 0.09f), patch, 21);
            var ball = ballGo.AddComponent<BallController>();
            ball.tuning = ballTuning;
            ball.kid = kid;
            input.ball = ballGo.transform;
            input.ballWorldRadius = circleCol.radius;

            // Kick aiming
            var aimGo = new GameObject("KickAimer");
            var preview = aimGo.AddComponent<TrajectoryPreview>();
            preview.tuning = ballTuning;
            preview.dotSprite = Circle;
            var aimer = aimGo.AddComponent<KickAimer>();
            aimer.ball = ball;
            aimer.preview = preview;
            aimer.worldCamera = cam;

            follow.kid = kid;
            follow.ball = ball;
            follow.minX = track.MinX;
            follow.maxX = track.MaxX;
            follow.minY = track.LowestGroundTop + 2f;

            // Level flow
            var manager = new GameObject("LevelManager").AddComponent<LevelManager>();
            manager.level = def;
            manager.catalog = catalog;
            manager.kid = kid;
            manager.ball = ball;
            manager.cameraFollow = follow;
            manager.checkpoints = new List<Checkpoint>(track.Checkpoints);
            manager.killY = track.LowestGroundTop - 6f;

            var hud = new GameObject("LevelHud").AddComponent<LevelHud>();
            hud.level = manager;
            hud.kid = kid;
            hud.ball = ball;
            hud.aimer = aimer;

            EditorSceneManager.SaveScene(scene, scenePath);
        }

        public static void ConfigurePlayerSettings()
        {
            PlayerSettings.productName = "Dribble To School";
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
        }

        static void Visual(Transform parent, string name, Sprite sprite, Vector2 localPos, Vector2 size, Color color, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localScale = new Vector3(size.x, size.y, 1f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.color = color;
            sr.sortingOrder = order;
        }

        // ---------- Track pieces ----------

        /// <summary>Fluent helper used by level layouts. Ground tops are world y values.</summary>
        public class TrackBuilder
        {
            readonly Transform root;
            readonly List<Checkpoint> checkpoints = new List<Checkpoint>();

            public IList<Checkpoint> Checkpoints { get { return checkpoints; } }
            public Checkpoint StartCheckpoint { get; private set; }
            public float MinX { get; private set; }
            public float MaxX { get; private set; }
            public float LowestGroundTop { get; private set; }

            public TrackBuilder(Transform root)
            {
                this.root = root;
                MinX = -10f;
                MaxX = 100f;
                LowestGroundTop = float.MaxValue;
            }

            /// <summary>Solid walls at both ends; also the camera's horizontal limits.</summary>
            public void Walls(float minX, float maxX)
            {
                MinX = minX;
                MaxX = maxX;
                Block("BackWall", new Vector2(minX - 0.5f, 3f), new Vector2(1f, 14f), GroundColor, GroundMat);
                Block("EndWall", new Vector2(maxX + 0.5f, 3f), new Vector2(1f, 14f), GroundColor, GroundMat);
            }

            /// <summary>Solid ground from fromX to toX with its top at <paramref name="top"/>.</summary>
            public void Ground(float fromX, float toX, float top = 0f)
            {
                const float depth = 4f;
                LowestGroundTop = Mathf.Min(LowestGroundTop, top);
                Block("Ground", new Vector2((fromX + toX) * 0.5f, top - depth * 0.5f), new Vector2(toX - fromX, depth), GroundColor, GroundMat);
            }

            /// <summary>A gap you fall into. Losing the ball or the kid here respawns at the checkpoint.</summary>
            public void Pit(float fromX, float toX, float top = 0f)
            {
                Hole("Pit", fromX, toX, top, PitColor, "Into the gap!", 0f);
            }

            /// <summary>A puddle/stream. Same rules as a pit, but blue and splashy.</summary>
            public void Water(float fromX, float toX, float top = 0f)
            {
                Hole("Water", fromX, toX, top, WaterColor, "Splash!", 0.35f);
            }

            void Hole(string name, float fromX, float toX, float top, Color color, string message, float surfaceDrop)
            {
                const float depth = 4f;
                Decor(name + "Fill", new Vector2((fromX + toX) * 0.5f, top - surfaceDrop - depth * 0.5f),
                    new Vector2(toX - fromX, depth), color);

                var go = new GameObject(name + "LoseZone");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((fromX + toX) * 0.5f, top - 2.2f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(toX - fromX + 1f, 1f);
                go.AddComponent<LoseZone>().message = message;
            }

            public void Crate(float x, float y)
            {
                var go = Block("Crate", new Vector2(x, y), new Vector2(0.7f, 0.7f), CrateColor, CrateMat);
                var body = go.AddComponent<Rigidbody2D>();
                body.mass = 0.8f;
                body.gravityScale = 1.5f;
                body.interpolation = RigidbodyInterpolation2D.Interpolate;
                go.AddComponent<ResettableBody>();
            }

            // ---------- Hazards & interactables ----------

            /// <summary>A parked car: hop onto the bonnet, then the roof. The ball can't roll under it.</summary>
            public void ParkedCar(float x, Color color, float groundTop = 0f)
            {
                Block("CarBody", new Vector2(x, groundTop + 0.575f), new Vector2(2.8f, 0.75f), color, GroundMat);
                Block("CarCabin", new Vector2(x - 0.2f, groundTop + 1.2f), new Vector2(1.5f, 0.5f), Color.Lerp(color, Color.white, 0.35f), GroundMat);
                Visual(root, "WheelL", Circle, new Vector2(x - 0.9f, groundTop + 0.22f), new Vector2(0.44f, 0.44f), new Color(0.15f, 0.15f, 0.15f), 1);
                Visual(root, "WheelR", Circle, new Vector2(x + 0.9f, groundTop + 0.22f), new Vector2(0.44f, 0.44f), new Color(0.15f, 0.15f, 0.15f), 1);
            }

            /// <summary>Someone walking between minX and maxX. Solid to the ball and the kid.</summary>
            public void Pedestrian(float minX, float maxX, Color coat, float groundTop = 0f, float speed = 1.1f)
            {
                var go = new GameObject("Pedestrian");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(minX, groundTop + 0.8f);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<CapsuleCollider2D>();
                col.size = new Vector2(0.5f, 1.6f);

                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                Visual(visual, "Coat", Square, new Vector2(0f, -0.1f), new Vector2(0.55f, 1.2f), coat, 8);
                Visual(visual, "Head", Circle, new Vector2(0f, 0.65f), new Vector2(0.4f, 0.4f), SkinColor, 9);
                Visual(visual, "Eye", Circle, new Vector2(0.1f, 0.68f), new Vector2(0.06f, 0.06f), Color.black, 10);

                var p = go.AddComponent<Hazards.Pedestrian>();
                p.minX = minX;
                p.maxX = maxX;
                p.walkSpeed = speed;
                p.visual = visual;
            }

            /// <summary>A zebra crossing from fromX to toX with a pedestrian light and passing traffic.</summary>
            public void Crossing(float fromX, float toX, float phaseOffset = 0f, float groundTop = 0f)
            {
                float width = toX - fromX;
                float center = (fromX + toX) * 0.5f;

                Decor("Road", new Vector2(center, groundTop - 0.06f), new Vector2(width, 0.12f), new Color(0.25f, 0.25f, 0.28f)).GetComponent<SpriteRenderer>().sortingOrder = 1;
                for (float sx = fromX + 0.3f; sx < toX - 0.2f; sx += 0.8f)
                    Decor("Zebra", new Vector2(sx + 0.2f, groundTop - 0.06f), new Vector2(0.4f, 0.1f), Color.white).GetComponent<SpriteRenderer>().sortingOrder = 2;

                var go = new GameObject("Crossing");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(center, groundTop + 1.25f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(width, 2.5f);
                var crossing = go.AddComponent<Hazards.Crossing>();
                crossing.phaseOffset = phaseOffset;

                // Light on a pole before the crossing.
                float poleX = fromX - 0.7f;
                Decor("LightPole", new Vector2(poleX, groundTop + 1.3f), new Vector2(0.12f, 2.6f), new Color(0.3f, 0.3f, 0.32f));
                Decor("LightBox", new Vector2(poleX, groundTop + 2.75f), new Vector2(0.45f, 1.2f), new Color(0.15f, 0.15f, 0.17f)).GetComponent<SpriteRenderer>().sortingOrder = 0;
                crossing.redLamp = Lamp(go.transform, new Vector2(poleX, groundTop + 3.15f));
                crossing.amberLamp = Lamp(go.transform, new Vector2(poleX, groundTop + 2.75f));
                crossing.greenLamp = Lamp(go.transform, new Vector2(poleX, groundTop + 2.35f));

                var car = new GameObject("Car").transform;
                car.SetParent(go.transform, false);
                car.localPosition = new Vector3(0f, -0.65f, 0f);
                Visual(car, "Body", Square, new Vector2(0f, 0f), new Vector2(2.4f, 0.7f), new Color(0.85f, 0.25f, 0.25f), 15);
                Visual(car, "Cabin", Square, new Vector2(0.1f, 0.55f), new Vector2(1.3f, 0.45f), new Color(0.95f, 0.6f, 0.55f), 15);
                Visual(car, "WheelL", Circle, new Vector2(-0.8f, -0.4f), new Vector2(0.4f, 0.4f), new Color(0.12f, 0.12f, 0.12f), 16);
                Visual(car, "WheelR", Circle, new Vector2(0.8f, -0.4f), new Vector2(0.4f, 0.4f), new Color(0.12f, 0.12f, 0.12f), 16);
                crossing.car = car;
                crossing.carTravel = width + 6f;
            }

            SpriteRenderer Lamp(Transform parent, Vector2 position)
            {
                var go = new GameObject("Lamp");
                go.transform.SetParent(parent, false);
                go.transform.position = position;
                go.transform.localScale = new Vector3(0.3f, 0.3f, 1f);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = Circle;
                sr.sortingOrder = 1;
                return sr;
            }

            /// <summary>A playful dog that patrols minX..maxX and noses low balls back.</summary>
            public void Dog(float minX, float maxX, Color fur, float groundTop = 0f)
            {
                var go = new GameObject("Dog");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((minX + maxX) * 0.5f, groundTop + 0.3f);
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                Visual(visual, "Body", Square, new Vector2(0f, 0f), new Vector2(0.8f, 0.38f), fur, 8);
                Visual(visual, "Head", Circle, new Vector2(0.45f, 0.18f), new Vector2(0.36f, 0.36f), fur, 9);
                Visual(visual, "Ear", Square, new Vector2(0.38f, 0.32f), new Vector2(0.12f, 0.2f), Color.Lerp(fur, Color.black, 0.4f), 10);
                Visual(visual, "Tail", Square, new Vector2(-0.48f, 0.15f), new Vector2(0.25f, 0.08f), fur, 8);
                Visual(visual, "LegF", Square, new Vector2(0.25f, -0.22f), new Vector2(0.1f, 0.2f), fur, 7);
                Visual(visual, "LegB", Square, new Vector2(-0.25f, -0.22f), new Vector2(0.1f, 0.2f), fur, 7);
                var dog = go.AddComponent<Hazards.Dog>();
                dog.minX = minX;
                dog.maxX = maxX;
                dog.visual = visual;
            }

            /// <summary>A puddle: the ball drags, the kid wades.</summary>
            public void Puddle(float fromX, float toX, float groundTop = 0f)
            {
                SlowArea("Puddle", fromX, toX, groundTop, new Color(0.45f, 0.65f, 0.9f, 0.85f), 2.5f, 0.6f);
            }

            /// <summary>Soft sand: gentler than a puddle but longer.</summary>
            public void Sand(float fromX, float toX, float groundTop = 0f)
            {
                SlowArea("Sand", fromX, toX, groundTop, new Color(0.93f, 0.84f, 0.6f), 1.4f, 0.75f);
            }

            void SlowArea(string name, float fromX, float toX, float groundTop, Color color, float drag, float kidMultiplier)
            {
                float center = (fromX + toX) * 0.5f;
                var surface = Decor(name + "Surface", new Vector2(center, groundTop - 0.04f), new Vector2(toX - fromX, 0.14f), color);
                surface.GetComponent<SpriteRenderer>().sortingOrder = 2;

                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(center, groundTop + 0.3f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(toX - fromX, 0.6f);
                var zone = go.AddComponent<SlowZone>();
                zone.surfaceName = name;
                zone.ballDrag = drag;
                zone.kidSpeedMultiplier = kidMultiplier;
            }

            /// <summary>A wind area. Use a negative x for a headwind, positive y for an updraft.</summary>
            public void Wind(float fromX, float toX, float bottom, float top, Vector2 acceleration, float gustPeriod = 0f)
            {
                var go = new GameObject("Wind");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((fromX + toX) * 0.5f, (bottom + top) * 0.5f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(toX - fromX, top - bottom);
                var wind = go.AddComponent<WindArea>();
                wind.ballAcceleration = acceleration;
                wind.gustPeriod = gustPeriod;

                var rng = new System.Random(Mathf.RoundToInt(fromX * 100f));
                var streaks = new List<Transform>();
                bool vertical = Mathf.Abs(acceleration.y) > Mathf.Abs(acceleration.x);
                for (int i = 0; i < 10; i++)
                {
                    float sx = Mathf.Lerp(fromX, toX, (float)rng.NextDouble());
                    float sy = Mathf.Lerp(bottom, top, (float)rng.NextDouble());
                    Vector2 size = vertical ? new Vector2(0.04f, 0.6f) : new Vector2(0.6f, 0.04f);
                    var streak = Decor("Streak", new Vector2(sx, sy), size, new Color(1f, 1f, 1f, 0.55f));
                    streak.GetComponent<SpriteRenderer>().sortingOrder = 30;
                    streaks.Add(streak.transform);
                }
                wind.streaks = streaks.ToArray();
            }

            /// <summary>A platform that slides by <paramref name="travel"/> and back.</summary>
            public void MovingPlatform(Vector2 center, float width, Vector2 travel, float speed = 1.5f)
            {
                var go = Block("MovingPlatform", center, new Vector2(width, 0.35f), new Color(0.55f, 0.5f, 0.65f), GroundMat);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var mp = go.AddComponent<Hazards.MovingPlatform>();
                mp.travel = travel;
                mp.speed = speed;
            }

            /// <summary>A gate blocking the path, opened by kicking the ball at a switch.</summary>
            public void SwitchAndGate(Vector2 switchPosition, float gateX, float gateHeight = 2.4f, float groundTop = 0f)
            {
                var gateGo = Block("Gate", new Vector2(gateX, groundTop + gateHeight * 0.5f), new Vector2(0.35f, gateHeight), new Color(0.45f, 0.35f, 0.55f), GroundMat);
                var gate = gateGo.AddComponent<Gate>();
                gate.openHeight = gateHeight + 0.2f;

                var sw = Block("Switch", switchPosition, new Vector2(0.55f, 0.55f), new Color(0.3f, 0.3f, 0.32f), GroundMat);
                var indicator = new GameObject("Indicator");
                indicator.transform.SetParent(sw.transform, false);
                indicator.transform.localScale = new Vector3(0.6f, 0.6f, 1f);
                var sr = indicator.AddComponent<SpriteRenderer>();
                sr.sprite = Circle;
                sr.sortingOrder = 3;
                var ballSwitch = sw.AddComponent<BallSwitch>();
                ballSwitch.gates = new[] { gate };
                ballSwitch.indicator = sr;
                Decor("SwitchPost", new Vector2(switchPosition.x, (groundTop + switchPosition.y) * 0.5f),
                    new Vector2(0.1f, switchPosition.y - groundTop), ObstacleColor);
            }

            /// <summary>A springy pad flush with the ground that launches the kid and the ball upward.</summary>
            public void Springboard(float x, float groundTop = 0f)
            {
                var go = new GameObject("Springboard");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(x, groundTop + 0.2f);
                var col = go.AddComponent<BoxCollider2D>();
                col.isTrigger = true;
                col.size = new Vector2(1.2f, 0.4f);
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                visual.localPosition = new Vector3(0f, -0.14f, 0f);
                Visual(visual, "Board", Square, Vector2.zero, new Vector2(1.3f, 0.14f), BouncyColor, 3);
                go.AddComponent<Hazards.Springboard>().visual = visual;
            }

            /// <summary>Three crates in a little pyramid standing on <paramref name="groundTop"/>.</summary>
            public void CrateStack(float x, float groundTop = 0f)
            {
                Crate(x, groundTop + 0.35f);
                Crate(x + 0.72f, groundTop + 0.35f);
                Crate(x + 0.36f, groundTop + 1.07f);
            }

            /// <summary>A sloped surface whose top runs from point a to point b.</summary>
            public void Ramp(Vector2 a, Vector2 b)
            {
                if (a.x > b.x) { Vector2 t = a; a = b; b = t; }
                const float thickness = 0.4f;
                Vector2 along = b - a;
                float angle = Mathf.Atan2(along.y, along.x) * Mathf.Rad2Deg;
                Vector2 normal = new Vector2(-along.normalized.y, along.normalized.x);
                Vector2 center = (a + b) * 0.5f - normal * (thickness * 0.5f);
                var go = Block("Ramp", center, new Vector2(along.magnitude + 0.2f, thickness), GroundColor, GroundMat);
                go.transform.rotation = Quaternion.Euler(0f, 0f, angle);
            }

            /// <summary>A short obstacle: jump it, chip the ball over.</summary>
            public void Wall(float x, float height, float groundTop = 0f, float width = 0.4f)
            {
                Block("Wall", new Vector2(x, groundTop + height * 0.5f), new Vector2(width, height), ObstacleColor, GroundMat);
            }

            /// <summary>A raised slab standing on the ground.</summary>
            public void Platform(float fromX, float toX, float top, float groundTop = 0f)
            {
                Block("Platform", new Vector2((fromX + toX) * 0.5f, (top + groundTop) * 0.5f),
                    new Vector2(toX - fromX, top - groundTop), GroundColor, GroundMat);
            }

            /// <summary>Hop onto a step, brake, chip the ball over the high wall behind it.</summary>
            public void StepAndHighWall(float x, float groundTop = 0f)
            {
                Block("Step", new Vector2(x, groundTop + 0.4f), new Vector2(2f, 0.8f), ObstacleColor, GroundMat);
                Block("HighWall", new Vector2(x + 1.25f, groundTop + 0.9f), new Vector2(0.5f, 1.8f), ObstacleColor, GroundMat);
            }

            /// <summary>A bouncy awning the ball can be kicked off.</summary>
            public void Awning(float x, float height, float groundTop = 0f)
            {
                Block("Awning", new Vector2(x, groundTop + height), new Vector2(2.2f, 0.2f), BouncyColor, BouncyMat);
                Decor("AwningPost", new Vector2(x + 1f, groundTop + height * 0.5f), new Vector2(0.12f, height), ObstacleColor);
            }

            public void Start(float x, float groundTop = 0f)
            {
                StartCheckpoint = MakeCheckpoint(x, groundTop, true);
            }

            public void Checkpoint(float x, float groundTop = 0f)
            {
                MakeCheckpoint(x, groundTop, false);
            }

            Checkpoint MakeCheckpoint(float x, float groundTop, bool isStart)
            {
                var go = new GameObject(isStart ? "Start" : "Checkpoint");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(x, groundTop);
                var cp = go.AddComponent<Checkpoint>();
                cp.isStart = isStart;

                cp.kidSpawn = new GameObject("KidSpawn").transform;
                cp.kidSpawn.SetParent(go.transform, false);
                cp.kidSpawn.localPosition = new Vector3(0f, 0.65f, 0f);
                cp.ballSpawn = new GameObject("BallSpawn").transform;
                cp.ballSpawn.SetParent(go.transform, false);
                cp.ballSpawn.localPosition = new Vector3(1f, 0.25f, 0f);

                if (!isStart)
                {
                    Decor("FlagPole", new Vector2(x, groundTop + 1f), new Vector2(0.08f, 2f), ObstacleColor);
                    var flag = Decor("Flag", new Vector2(x + 0.3f, groundTop + 1.8f), new Vector2(0.55f, 0.35f), Color.gray);
                    cp.flag = flag.GetComponent<SpriteRenderer>();
                    cp.flag.sortingOrder = 1;
                    flag.transform.SetParent(go.transform, true);
                }

                checkpoints.Add(cp);
                return cp;
            }

            public void Goal(float x, float groundTop = 0f)
            {
                var school = new GameObject("School").transform;
                school.SetParent(root, false);
                Decor("GatePostL", new Vector2(x - 1.5f, groundTop + 1.5f), new Vector2(0.3f, 3f), SchoolColor).transform.SetParent(school, true);
                Decor("GatePostR", new Vector2(x + 1.5f, groundTop + 1.5f), new Vector2(0.3f, 3f), SchoolColor).transform.SetParent(school, true);
                Decor("GateTop", new Vector2(x, groundTop + 3.1f), new Vector2(3.3f, 0.3f), SchoolColor).transform.SetParent(school, true);

                var goalGo = new GameObject("GoalZone");
                goalGo.transform.SetParent(school, false);
                goalGo.transform.position = new Vector3(x, groundTop + 1.5f, 0f);
                var trigger = goalGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(2.6f, 3f);
                goalGo.AddComponent<GoalZone>();
                Sign("SCHOOL", new Vector2(x, groundTop + 4f));
            }

            public void Sign(string text, Vector2 position)
            {
                var go = new GameObject("Sign_" + text.Split('\n')[0]);
                go.transform.SetParent(root, false);
                go.transform.position = position;
                var mesh = go.AddComponent<TextMesh>();
                mesh.text = text;
                mesh.font = signFont;
                mesh.fontSize = 48;
                mesh.characterSize = 0.06f;
                mesh.anchor = TextAnchor.MiddleCenter;
                mesh.alignment = TextAlignment.Center;
                mesh.color = new Color(0.25f, 0.3f, 0.4f);
                var renderer = go.GetComponent<MeshRenderer>();
                if (signFont != null) renderer.sharedMaterial = signFont.material;
                renderer.sortingOrder = 5;
            }

            /// <summary>A coloured box with a matching collider. Scale drives both sprite and collider.</summary>
            public GameObject Block(string name, Vector2 center, Vector2 size, Color color, PhysicsMaterial2D material)
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = center;
                go.transform.localScale = new Vector3(size.x, size.y, 1f);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = Square;
                sr.color = color;
                var col = go.AddComponent<BoxCollider2D>();
                col.sharedMaterial = material;
                return go;
            }

            /// <summary>A coloured box with no collider (background dressing).</summary>
            public GameObject Decor(string name, Vector2 center, Vector2 size, Color color)
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = center;
                go.transform.localScale = new Vector3(size.x, size.y, 1f);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = Square;
                sr.color = color;
                sr.sortingOrder = -1;
                return go;
            }
        }

        // ---------- Asset helpers ----------

        public static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            string parent = Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }

        public static T LoadOrCreateAsset<T>(string path) where T : ScriptableObject
        {
            var asset = AssetDatabase.LoadAssetAtPath<T>(path);
            if (asset != null) return asset;
            EnsureFolder(Path.GetDirectoryName(path).Replace('\\', '/'));
            asset = ScriptableObject.CreateInstance<T>();
            AssetDatabase.CreateAsset(asset, path);
            return asset;
        }

        static PhysicsMaterial2D LoadOrCreateMaterial(string path, float friction, float bounciness)
        {
            var mat = AssetDatabase.LoadAssetAtPath<PhysicsMaterial2D>(path);
            if (mat != null) return mat;
            mat = new PhysicsMaterial2D { friction = friction, bounciness = bounciness };
            AssetDatabase.CreateAsset(mat, path);
            return mat;
        }

        /// <summary>White square or anti-aliased circle, sized to exactly 1 world unit.</summary>
        static Sprite LoadOrCreateSprite(string path, int size, bool round)
        {
            var existing = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            if (existing != null) return existing;

            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            float r = size * 0.5f;
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float alpha = 1f;
                    if (round)
                    {
                        float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(r, r));
                        alpha = Mathf.Clamp01(r - d);
                    }
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, alpha));
                }
            }
            tex.Apply();

            string fullPath = Path.Combine(Directory.GetParent(Application.dataPath).FullName, path);
            File.WriteAllBytes(fullPath, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(path);

            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = size;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = true;
            importer.filterMode = FilterMode.Bilinear;
            importer.SaveAndReimport();

            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
    }
}
