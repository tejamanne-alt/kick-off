using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Art;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Challenges;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Hazards;
using DribbleToSchool.World;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Levels;
using DribbleToSchool.Pickups;
using DribbleToSchool.Player;
using DribbleToSchool.Presentation;
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
        /// <summary>Theme of the chapter currently being built (colours, ground edge, scenery).</summary>
        public static ChapterTheme Theme = ChapterTheme.For(1);
        public static int Chapter = 1;
        public static ArtBaker.ArtSet Art { get; private set; }
        public static Color GroundColor { get { return Theme.groundFill; } }
        public static Color ObstacleColor { get { return Theme.obstacle; } }
        public static Color PlatformColor { get { return Theme.platform; } }
        public static readonly Color CrateColor = new Color(0.78f, 0.58f, 0.33f);
        public static readonly Color BouncyColor = new Color(0.90f, 0.40f, 0.40f);
        public static readonly Color PitColor = new Color(0.22f, 0.20f, 0.22f);
        public static readonly Color WaterColor = new Color(0.30f, 0.55f, 0.85f);
        static readonly Color KidColor = new Color(0.97f, 0.97f, 0.99f);   // white school shirt
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
        static Material trailMaterial;
        public static CosmeticCatalog Cosmetics { get; set; }

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
            signFont = UI.Kit.UITheme.Display;
            Art = ArtBaker.BakeAll();

            const string trailPath = ArtDir + "/BallTrail.mat";
            trailMaterial = AssetDatabase.LoadAssetAtPath<Material>(trailPath);
            if (trailMaterial == null)
            {
                trailMaterial = new Material(Shader.Find("Sprites/Default"));
                AssetDatabase.CreateAsset(trailMaterial, trailPath);
            }
        }

        /// <summary>
        /// Build and save one level scene: camera, input, the track from
        /// <paramref name="layout"/>, kid, ball, kick aimer, level manager and HUD.
        /// </summary>
        /// <remarks>
        /// <paramref name="chapter"/> is passed in rather than read from <paramref name="def"/>: creating a new
        /// scene can unload level assets nothing references, after which <c>def</c> compares equal to null.
        /// </remarks>
        public static void BuildScene(string scenePath, LevelDefinition def, LevelCatalog catalog, Action<TrackBuilder> layout, int chapter = 1)
        {
            EnsureFolder(Path.GetDirectoryName(scenePath).Replace('\\', '/'));
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Chapter = Mathf.Clamp(chapter, 1, 5);
            Theme = ChapterTheme.For(Chapter);

            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            // A perspective camera looking down the street at a slight tilt (see CameraFollow2D):
            // gameplay stays on the z = 0 plane, the street and scenery are real 3D around it.
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = false;
            cam.fieldOfView = 30f;
            cam.nearClipPlane = 0.3f;
            cam.farClipPlane = 2500f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = Theme.skyBottom;
            camGo.AddComponent<AudioListener>();
            camGo.transform.position = new Vector3(3f, 2f, -20f);
            var look = camGo.AddComponent<WorldLook>();
            look.hazeColor = Color.Lerp(Theme.skyBottom, Color.white, 0.12f);
            look.Apply();
            var follow = camGo.AddComponent<CameraFollow2D>();

            var input = new GameObject("GameInput").AddComponent<GameInput>();
            input.worldCamera = cam;

            var track = new TrackBuilder(new GameObject("Level").transform);
            layout(track);
            track.Finish();
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
            var kidRig = BuildCharacter(kidGo.transform, "Visual", Vector2.zero, 1f, KidColor, new Color(0.22f, 0.23f, 0.42f),
                new Color(0.16f, 0.15f, 0.2f), true);   // glossy near-black hair
            var feet = new GameObject("Feet").transform;
            feet.SetParent(kidGo.transform, false);
            feet.localPosition = new Vector3(0f, -0.6f, 0f);
            var kid = kidGo.AddComponent<KidController>();
            kid.tuning = playerTuning;
            kid.feet = feet;
            kidRig.rig.gameObject.AddComponent<KidAnimator>().kid = kid;

            // Ball
            var ballGo = new GameObject("Ball");
            ballGo.transform.position = ballSpawn;
            ballGo.AddComponent<Rigidbody2D>();
            var circleCol = ballGo.AddComponent<CircleCollider2D>();
            circleCol.radius = 0.2f;
            var squashRoot = new GameObject("SquashRoot").transform;
            squashRoot.SetParent(ballGo.transform, false);
            // A 3D ball; the equipped skin's drawing is projected onto it (CosmeticApplier).
            var shell = new GameObject("Ball3D");
            shell.transform.SetParent(squashRoot, false);
            var sphere = shell.AddComponent<SphereShape>();
            sphere.radius = 0.2f;
            shell.GetComponent<MeshRenderer>().sharedMaterial = Art.ball;
            sphere.Rebuild();
            var ballShadow = ShadowSprite("BallShadow");
            var kidShadow = ShadowSprite("KidShadow");
            var trail = ballGo.AddComponent<TrailRenderer>();
            trail.sharedMaterial = trailMaterial;
            trail.time = 0.25f;
            trail.minVertexDistance = 0.05f;
            trail.widthMultiplier = 0.32f;
            trail.widthCurve = AnimationCurve.Linear(0f, 1f, 1f, 0f);
            trail.sortingOrder = 19;
            trail.enabled = false;
            var ball = ballGo.AddComponent<BallController>();
            ball.tuning = ballTuning;
            ball.kid = kid;
            var ballVisual = ballGo.AddComponent<BallVisual>();
            ballVisual.ball = ball;
            ballVisual.squashRoot = squashRoot;
            var ballShade = ballGo.AddComponent<GroundShadow>();
            ballShade.target = ballGo.GetComponent<Rigidbody2D>();
            ballShade.ignore = new[] { kidBody };
            ballShade.shadow = ballShadow;
            ballShade.size = new Vector2(0.42f, 0.24f);
            var kidShade = kidGo.AddComponent<GroundShadow>();
            kidShade.target = kidBody;
            kidShade.ignore = new[] { ballShade.target };
            kidShade.shadow = kidShadow;
            kidShade.size = new Vector2(0.7f, 0.36f);
            kidShade.maxDistance = 6f;

            // Kick aiming
            var aimGo = new GameObject("KickAimer");
            var preview = aimGo.AddComponent<TrajectoryPreview>();
            preview.tuning = ballTuning;
            preview.dotSprite = Circle;
            var aimer = aimGo.AddComponent<KickAimer>();
            aimer.ball = ball;
            aimer.preview = preview;
            aimer.worldCamera = cam;

            var darkGo = new GameObject("Darkness");
            darkGo.AddComponent<SpriteRenderer>();
            darkGo.AddComponent<DarknessOverlay>().follow = kidGo.transform;

            follow.kid = kid;
            follow.ball = ball;
            follow.minX = track.MinX;
            follow.maxX = track.MaxX;
            follow.minY = track.LowestGroundTop + 2f;

            BuildSky(track, cam);
            var street = new GameObject("Street");
            StreetBuilder.Scenery(track, street.transform);
            street.AddComponent<StaticBatcher>();

            var fxGo = new GameObject("FX");
            var pool = fxGo.AddComponent<FxPool>();
            var fx = fxGo.AddComponent<FxDirector>();
            fx.pool = pool;
            fx.cameraFollow = follow;
            fx.puff = Art.puff;
            fx.spark = Art.spark;
            fx.drop = Art.drop;
            fx.dustColor = Color.Lerp(Theme.groundEdge, Color.white, 0.5f);

            // Level flow
            var manager = new GameObject("LevelManager").AddComponent<LevelManager>();
            manager.level = def;
            manager.catalog = catalog;
            manager.kid = kid;
            manager.ball = ball;
            manager.cameraFollow = follow;
            manager.checkpoints = new List<Checkpoint>(track.Checkpoints);
            manager.killY = track.LowestGroundTop - 6f;
            manager.startBoundaryX = track.MinX;
            manager.startWall = track.StartWall;

            var applier = new GameObject("CosmeticApplier").AddComponent<CosmeticApplier>();
            applier.catalog = Cosmetics;
            applier.ballRenderer = shell.GetComponent<MeshRenderer>();
            applier.ballTrail = trail;
            applier.kidBody = kidRig.body;
            applier.backpackFlag = kidRig.flag;

            var tuningPanel = new GameObject("DevTuning").AddComponent<DevTuningPanel>();
            tuningPanel.kid = kid;
            tuningPanel.ball = ball;

            var hud = new GameObject("GameHud").AddComponent<GameHud>();
            hud.level = manager;
            hud.kid = kid;
            hud.ball = ball;
            hud.aimer = aimer;
            hud.tuning = tuningPanel;

            EditorSceneManager.SaveScene(scene, scenePath);
        }

        /// <summary>The parts of a built character that other systems dress or animate.</summary>
        public struct CharacterParts
        {
            public CharacterRig rig;
            public CharacterBody3D body;
            public SpriteRenderer flag;
            public Transform visual;
        }

        /// <summary>
        /// A 3D character: joints for CharacterRig (hips, knees, shoulders, elbows, neck and the
        /// bag) and one smooth skinned body (CharacterBody3D) on them. Feet at local y -0.6 * scale,
        /// facing +x; limbs on the near side (toward the camera, -z) are the "front" ones.
        /// </summary>
        static CharacterParts BuildCharacter(Transform parent, string name, Vector2 localPos, float scale, Color shirt, Color legwear,
            Color hair, bool kid)
        {
            var parts = new CharacterParts();
            var visual = new GameObject(name).transform;
            visual.SetParent(parent, false);
            visual.localPosition = localPos;
            parts.visual = visual;
            var body = new GameObject("Body").transform;
            body.SetParent(visual, false);
            body.localScale = Vector3.one * scale;
            var rig = body.gameObject.AddComponent<CharacterRig>();
            rig.body = body;
            parts.rig = rig;

            rig.legFront = Pivot(body, "LegFront", new Vector3(0f, 0.12f, -0.072f));
            rig.kneeFront = Pivot(rig.legFront, "Knee", new Vector3(0f, -0.36f, 0f));
            rig.legBack = Pivot(body, "LegBack", new Vector3(0f, 0.12f, 0.072f));
            rig.kneeBack = Pivot(rig.legBack, "Knee", new Vector3(0f, -0.36f, 0f));
            rig.armFront = Pivot(body, "ArmFront", new Vector3(0.005f, 0.555f, -0.168f));
            rig.elbowFront = Pivot(rig.armFront, "Elbow", new Vector3(0f, -0.24f, 0f));
            rig.armBack = Pivot(body, "ArmBack", new Vector3(0.005f, 0.555f, 0.168f));
            rig.elbowBack = Pivot(rig.armBack, "Elbow", new Vector3(0f, -0.24f, 0f));
            rig.head = Pivot(body, "Head", new Vector3(0.03f, 0.6f, 0f));
            if (kid)
            {
                // The school bag hangs on the back of the hips from its strap; a pennant (the
                // shop's "backpack flags") is clipped to it on the near side.
                rig.bag = Pivot(body, "Bag", new Vector3(-0.12f, 0.32f, 0f));
                var pole = Visual(rig.bag, "FlagPole", Square, new Vector2(-0.05f, 0.08f), new Vector2(0.015f, 0.2f), new Color(0.3f, 0.25f, 0.2f), 7);
                pole.transform.localPosition = new Vector3(-0.05f, 0.08f, -0.12f);
                var flag = Visual(rig.bag, "BackpackFlag", Square, new Vector2(-0.11f, 0.15f), new Vector2(0.12f, 0.09f), Color.white, 7);
                flag.transform.localPosition = new Vector3(-0.11f, 0.15f, -0.12f);
                parts.flag = flag.GetComponent<SpriteRenderer>();
            }

            var meshGo = new GameObject("Body3D");
            meshGo.transform.SetParent(visual, false);
            var smr = meshGo.AddComponent<SkinnedMeshRenderer>();
            smr.sharedMaterial = Art.character;
            var body3D = meshGo.AddComponent<CharacterBody3D>();
            body3D.rig = rig;
            body3D.kidOutfit = kid;
            body3D.shirt = shirt;
            body3D.legwear = legwear;
            body3D.hair = hair;
            if (!kid) body3D.build = 1.05f;
            body3D.Rebuild();
            parts.body = body3D;
            return parts;
        }

        static Transform Pivot(Transform parent, string name, Vector3 localPos)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = localPos;
            return t;
        }

        /// <summary>A 3D car with its wheels on <paramref name="position"/>, turned <paramref name="yaw"/> degrees (0 faces +x, 90 faces the camera).</summary>
        static Car3D Car(Transform parent, string name, Vector3 position, float yaw, Color paint)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            var car = go.AddComponent<Car3D>();
            car.paint = paint;
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            car.Rebuild();
            return car;
        }

        /// <summary>A rounded 3D form of ellipsoids at a local position, in the outlined character style.</summary>
        static BlobShape Blobs(Transform parent, string name, Vector3 localPos, params BlobShape.Blob[] blobs)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var shape = go.AddComponent<BlobShape>();
            shape.blobs = new List<BlobShape.Blob>(blobs);
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.character;
            shape.Rebuild();
            return shape;
        }

        /// <summary>A soft shadow sprite for a GroundShadow to lay on the ground.</summary>
        static SpriteRenderer ShadowSprite(string name)
        {
            var sr = new GameObject(name).AddComponent<SpriteRenderer>();
            sr.sprite = Art.shadow;
            sr.sortingOrder = 3;
            sr.color = new Color(0.1f, 0.1f, 0.2f, 0.35f);
            return sr;
        }

        static SpriteRenderer SpriteObject(Transform parent, string name, Sprite sprite, Vector3 localPos, int order, Color? color = null)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = order;
            sr.color = color ?? Color.white;
            return sr;
        }

        /// <summary>
        /// The sky: a gradient glued far behind the camera, big cumulus clouds high and far away,
        /// and the low golden sun in the last chapter. Distances are large so the 3D street,
        /// scenery and haze all sit in front.
        /// </summary>
        static void BuildSky(TrackBuilder track, Camera cam)
        {
            int ch = Chapter;
            var sky = SpriteObject(cam.transform, "Sky", Art.sky[ch], new Vector3(0f, 0f, 1500f), -100);
            sky.transform.localScale = new Vector3(9600f, 140f, 1f);
            if (ch == 5)
            {
                var sun = SpriteObject(cam.transform, "Sun", Art.sun, new Vector3(260f, 110f, 1400f), -95, Theme.sun);
                sun.transform.localScale = Vector3.one * 55f;
            }

            var clouds = new GameObject("Clouds").transform;
            var rng = new System.Random(ch * 101 + Mathf.RoundToInt(track.MaxX));
            for (float x = track.MinX - 450f; x < track.MaxX + 450f; x += 70f + (float)rng.NextDouble() * 90f)
            {
                float z = 520f + (float)rng.NextDouble() * 180f;
                var c = SpriteObject(clouds, "Cloud", Art.clouds[rng.Next(3)], new Vector3(x, track.LowestGroundTop + 30f + (float)rng.NextDouble() * 70f, z), -90, Theme.cloud);
                c.transform.localScale = Vector3.one * (8f + (float)rng.NextDouble() * 6f);
                c.flipX = rng.NextDouble() < 0.5;
                c.sharedMaterial = Art.hazeSprite;
            }
        }

        static GameObject Visual(Transform parent, string name, Sprite sprite, Vector2 localPos, Vector2 size, Color color, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localScale = new Vector3(size.x, size.y, 1f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.color = color;
            sr.sortingOrder = order;
            return go;
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
            /// <summary>Stretches of the track where the backdrop must stay open (side streets at crossings).</summary>
            public readonly List<Vector2> OpenAreas = new List<Vector2>();
            /// <summary>x of the school gate, once the layout has placed it.</summary>
            public float GoalX = float.MinValue;
            /// <summary>Every ground span as (fromX, toX, top).</summary>
            public IEnumerable<Vector3> GroundSpans
            {
                get { foreach (var g in groundSpans) yield return new Vector3(g.from, g.to, g.top); }
            }
            /// <summary>The wall at the level start: stops the kid, lets the ball through (see LevelManager).</summary>
            public Collider2D StartWall { get; private set; }

            struct GroundSpan { public float from, to, top; }
            struct PendingSign { public Transform sign; public Vector2 boardSize; }
            readonly List<GroundSpan> groundSpans = new List<GroundSpan>();
            readonly List<PendingSign> pendingSigns = new List<PendingSign>();

            // Ground and pit fills reach well below the lowest camera view, so no sky shows under the level.
            static float FillDepth(float top) { return Mathf.Max(4f, top + 12f); }

            public TrackBuilder(Transform root)
            {
                this.root = root;
                MinX = -10f;
                MaxX = 100f;
                LowestGroundTop = float.MaxValue;
            }

            /// <summary>Walls at both ends; also the camera's horizontal limits. The ball can pass the back wall (and is then lost).</summary>
            public void Walls(float minX, float maxX)
            {
                MinX = minX;
                MaxX = maxX;
                // Invisible: the 3D street carries on past both ends.
                StartWall = Block("BackWall", new Vector2(minX - 0.5f, 3f), new Vector2(1f, 14f), GroundColor, GroundMat, false).GetComponent<Collider2D>();
                Block("EndWall", new Vector2(maxX + 0.5f, 3f), new Vector2(1f, 14f), GroundColor, GroundMat, false);
            }

            /// <summary>Solid ground from fromX to toX with its top at <paramref name="top"/>. The 3D street over it is built in Finish.</summary>
            public void Ground(float fromX, float toX, float top = 0f)
            {
                float depth = FillDepth(top);
                LowestGroundTop = Mathf.Min(LowestGroundTop, top);
                groundSpans.Add(new GroundSpan { from = Mathf.Min(fromX, toX), to = Mathf.Max(fromX, toX), top = top });
                Block("Ground", new Vector2((fromX + toX) * 0.5f, top - depth * 0.5f), new Vector2(toX - fromX, depth), GroundColor, GroundMat, false);
            }

            /// <summary>A gap you fall into. Losing the ball or the kid here respawns at the checkpoint.</summary>
            public void Pit(float fromX, float toX, float top = 0f)
            {
                Hole("Pit", fromX, toX, top, PitColor, "lose.gap", 0f);
            }

            /// <summary>A puddle/stream. Same rules as a pit, but blue and splashy.</summary>
            public void Water(float fromX, float toX, float top = 0f)
            {
                Hole("Water", fromX, toX, top, WaterColor, "lose.splash", 0.35f);
            }

            void Hole(string name, float fromX, float toX, float top, Color color, string message, float surfaceDrop)
            {
                // A trench across the whole street: the slabs either side show their sides; a dark
                // floor (or water) fills the bottom, all the way back to the property line.
                float cx = (fromX + toX) * 0.5f, zc = (StreetBuilder.FrontZ + StreetBuilder.PropertyZ + 0.6f) * 0.5f;
                Vector3 size = new Vector3(toX - fromX, 0.2f, StreetBuilder.PropertyZ + 0.6f - StreetBuilder.FrontZ);
                if (surfaceDrop > 0f)
                {
                    var water = StreetBuilder.Solid(root, name + "Surface", new Vector3(cx, top - surfaceDrop - 0.1f, zc), size, Color.white, Art.surfaces[ProceduralArt.Surface.Sea]);
                    water.faces = MeshBuilder.Faces.Top;
                    water.Rebuild();
                }
                else
                {
                    StreetBuilder.Solid(root, name + "Floor", new Vector3(cx, top - 3f, zc), size, color);
                }

                var go = new GameObject(name + "LoseZone");
                go.transform.SetParent(root, false);
                // Deep enough that it can never reach the surface of lower ground on either side.
                go.transform.position = new Vector2((fromX + toX) * 0.5f, Mathf.Min(top - 2.2f, -1f));
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(toX - fromX, 1f);
                go.AddComponent<LoseZone>().message = message;
            }

            public void Crate(float x, float y)
            {
                var go = Block("Crate", new Vector2(x, y), new Vector2(0.7f, 0.7f), Color.white, CrateMat, true, 0.7f, Art.crateMaterial);
                var body = go.AddComponent<Rigidbody2D>();
                body.mass = 0.8f;
                body.gravityScale = 1.5f;
                body.interpolation = RigidbodyInterpolation2D.Interpolate;
                go.AddComponent<ResettableBody>();
            }

            // ---------- Pickups ----------

            public void Coin(Vector2 position)
            {
                var go = new GameObject("Coin");
                go.transform.SetParent(root, false);
                go.transform.position = position;
                var col = go.AddComponent<CircleCollider2D>();
                col.isTrigger = true;
                col.radius = 0.28f;
                // A gold coin: a thin disc with a raised face, spinning about its vertical axis.
                var visual = new GameObject("Visual");
                visual.transform.SetParent(go.transform, false);
                var disc = visual.AddComponent<CylinderShape>();
                disc.radius = 0.22f;
                disc.length = 0.07f;
                disc.sideColor = new Color(0.86f, 0.58f, 0.12f);
                disc.endColor = new Color(1f, 0.8f, 0.25f);
                disc.innerRadius = 0.14f;
                disc.innerColor = new Color(1f, 0.88f, 0.45f);
                visual.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                disc.Rebuild();
                go.AddComponent<Pickups.Coin>().visual = visual.transform;
            }

            /// <summary>Coins in a straight line, start and end inclusive.</summary>
            public void CoinRow(float fromX, float toX, float y, int count)
            {
                for (int i = 0; i < count; i++)
                {
                    float t = count == 1 ? 0.5f : i / (float)(count - 1);
                    Coin(new Vector2(Mathf.Lerp(fromX, toX, t), y));
                }
            }

            /// <summary>Coins along a jump-shaped arc, hinting at the path to take.</summary>
            public void CoinArc(float fromX, float toX, float baseY, float height, int count)
            {
                for (int i = 0; i < count; i++)
                {
                    float t = count == 1 ? 0.5f : i / (float)(count - 1);
                    Coin(new Vector2(Mathf.Lerp(fromX, toX, t), baseY + 4f * t * (1f - t) * height));
                }
            }

            /// <summary>The level's hidden sticker. Put it somewhere that takes a good kick or a brave jump.</summary>
            public void Sticker(Vector2 position)
            {
                var go = new GameObject("Sticker");
                go.transform.SetParent(root, false);
                go.transform.position = position;
                var col = go.AddComponent<CircleCollider2D>();
                col.isTrigger = true;
                col.radius = 0.35f;
                var visual = Visual(go.transform, "Visual", Circle, Vector2.zero, new Vector2(0.7f, 0.7f), new Color(1f, 0.55f, 0.75f), 25);
                Visual(visual.transform, "Border", Circle, Vector2.zero, new Vector2(1.15f, 1.15f), Color.white, 24);
                Visual(visual.transform, "Heart", Circle, new Vector2(0f, 0.05f), new Vector2(0.45f, 0.45f), new Color(1f, 0.95f, 0.5f), 26);
                var sticker = go.AddComponent<Pickups.Sticker>();
                sticker.visual = visual.transform;
                sticker.visualRenderer = visual.GetComponent<SpriteRenderer>();
            }

            // ---------- Hazards & interactables ----------

            /// <summary>A parked car: hop onto the bonnet, then the roof. The ball can't roll under it.</summary>
            public void ParkedCar(float x, Color color, float groundTop = 0f)
            {
                // Colliders only; the 3D car covers them.
                // A small city car about 3.4 units (3 m) long: bonnet at 0.95, roof at 1.55, both jumpable.
                Block("CarBody", new Vector2(x, groundTop + 0.575f), new Vector2(3.3f, 0.75f), color, GroundMat, false);
                Block("CarCabin", new Vector2(x - 0.17f, groundTop + 1.25f), new Vector2(1.9f, 0.6f), color, GroundMat, false);
                Car(root, "Car", new Vector3(x, groundTop, 0.15f), 0f, color);
            }

            /// <summary>Someone walking between minX and maxX. Solid to the ball and the kid.</summary>
            public void Pedestrian(float minX, float maxX, Color coat, float groundTop = 0f, float speed = 1.1f)
            {
                var go = new GameObject("Pedestrian");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(minX, groundTop + 0.925f);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<CapsuleCollider2D>();
                col.size = new Vector2(0.5f, 1.85f);

                Color[] hairs = { new Color(0.46f, 0.34f, 0.28f), new Color(1f, 0.95f, 0.6f), new Color(0.92f, 0.92f, 0.95f), new Color(0.85f, 0.46f, 0.3f) };
                // Adults: the kid rig at 1.22x (about 1.9 units, 1.7 m), feet on the capsule bottom (-0.925).
                var parts = BuildCharacter(go.transform, "Visual", new Vector2(0f, -0.193f), 1.22f, coat, Color.Lerp(coat, Color.black, 0.45f),
                    hairs[Mathf.Abs(Mathf.RoundToInt(minX)) % hairs.Length], false);

                var p = go.AddComponent<Hazards.Pedestrian>();
                p.minX = minX;
                p.maxX = maxX;
                p.walkSpeed = speed;
                p.visual = parts.visual;
                var walker = parts.rig.gameObject.AddComponent<WalkerAnimator>();
                walker.pedestrian = p;
            }

            /// <summary>A zebra crossing from fromX to toX with a pedestrian light and passing traffic.</summary>
            public void Crossing(float fromX, float toX, float phaseOffset = 0f, float groundTop = 0f)
            {
                float width = toX - fromX;
                float center = (fromX + toX) * 0.5f;

                // The side street, zebra and stop line are 3D (see StreetBuilder.CrossingStreet);
                // the main street's slabs leave this stretch open for it.
                OpenAreas.Add(new Vector2(fromX - 0.8f, toX + 0.8f));
                StreetBuilder.CrossingStreet(root, fromX - 0.8f, toX + 0.8f, groundTop);

                var go = new GameObject("Crossing");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(center, groundTop + 1.25f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(width, 2.5f);
                var crossing = go.AddComponent<Hazards.Crossing>();
                crossing.phaseOffset = phaseOffset;

                // Pedestrian signal on the far pavement at the kerb, facing the kid:
                // red standing man above, green walking man below.
                float poleX = fromX - 1.2f, poleZ = StreetBuilder.RoadHalf + 0.6f, pave = groundTop + 0.14f;
                StreetBuilder.Solid(root, "SignalPole", new Vector3(poleX, pave + 1.4f, poleZ), new Vector3(0.12f, 2.8f, 0.12f), new Color(0.55f, 0.56f, 0.58f));
                StreetBuilder.Solid(root, "SignalBox", new Vector3(poleX, pave + 2.45f, poleZ - 0.1f), new Vector3(0.55f, 1f, 0.3f), new Color(0.15f, 0.15f, 0.17f));
                crossing.redFigure = SpriteObject(go.transform, "RedMan", Art.standFigure, Vector3.zero, 1);
                crossing.redFigure.transform.position = new Vector3(poleX, pave + 2.68f, poleZ - 0.27f);
                crossing.greenFigure = SpriteObject(go.transform, "GreenMan", Art.walkFigure, Vector3.zero, 1);
                crossing.greenFigure.transform.position = new Vector3(poleX, pave + 2.22f, poleZ - 0.27f);

                // Side-street traffic driving toward the camera; the Crossing script moves it in depth.
                Color[] paint = { new Color(0.9f, 0.35f, 0.3f), new Color(0.35f, 0.55f, 0.85f) };
                crossing.cars = new Transform[paint.Length];
                for (int i = 0; i < paint.Length; i++)
                    crossing.cars[i] = Car(go.transform, "Car" + i, new Vector3(center, groundTop, 30f), 90f, paint[i]).transform;   // placed by Crossing
                crossing.groundY = groundTop;
            }

            /// <summary>A playful dog that patrols minX..maxX and noses low balls back.</summary>
            public void Dog(float minX, float maxX, Color fur, float groundTop = 0f)
            {
                var go = new GameObject("Dog");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((minX + maxX) * 0.5f, groundTop + 0.3f);
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                // A small 3D dog of soft blobs (feet at -0.3), facing +x, with swinging legs.
                Color light = Color.Lerp(fur, Color.white, 0.45f), darkFur = Color.Lerp(fur, Color.black, 0.35f), ink = new Color(0.1f, 0.08f, 0.1f);
                Blobs(visual, "Body", Vector3.zero,
                    new BlobShape.Blob(new Vector3(0f, 0.02f, 0f), new Vector3(0.3f, 0.14f, 0.13f), fur),
                    new BlobShape.Blob(new Vector3(0.16f, 0.04f, 0f), new Vector3(0.15f, 0.15f, 0.13f), fur),
                    new BlobShape.Blob(new Vector3(0.12f, -0.02f, 0f), new Vector3(0.14f, 0.1f, 0.11f), light),
                    new BlobShape.Blob(new Vector3(0.25f, 0.1f, 0f), new Vector3(0.05f, 0.1f, 0.11f), new Color(0.85f, 0.25f, 0.25f)),
                    new BlobShape.Blob(new Vector3(0.34f, 0.2f, 0f), new Vector3(0.12f, 0.11f, 0.1f), fur),
                    new BlobShape.Blob(new Vector3(0.45f, 0.16f, 0f), new Vector3(0.08f, 0.055f, 0.055f), light),
                    new BlobShape.Blob(new Vector3(0.525f, 0.18f, 0f), new Vector3(0.022f, 0.02f, 0.022f), ink),
                    new BlobShape.Blob(new Vector3(0.42f, 0.245f, -0.06f), new Vector3(0.016f, 0.022f, 0.012f), ink),
                    new BlobShape.Blob(new Vector3(0.42f, 0.245f, 0.06f), new Vector3(0.016f, 0.022f, 0.012f), ink),
                    new BlobShape.Blob(new Vector3(0.29f, 0.29f, -0.075f), new Vector3(0.04f, 0.085f, 0.025f), darkFur),
                    new BlobShape.Blob(new Vector3(0.29f, 0.29f, 0.075f), new Vector3(0.04f, 0.085f, 0.025f), darkFur),
                    new BlobShape.Blob(new Vector3(-0.31f, 0.13f, 0f), new Vector3(0.08f, 0.035f, 0.035f), fur),
                    new BlobShape.Blob(new Vector3(-0.37f, 0.19f, 0f), new Vector3(0.05f, 0.03f, 0.03f), light));
                var legs = new List<Transform>();
                foreach (var hip in new[] { new Vector3(0.18f, -0.02f, -0.08f), new Vector3(0.18f, -0.02f, 0.08f), new Vector3(-0.18f, -0.02f, -0.08f), new Vector3(-0.18f, -0.02f, 0.08f) })
                    legs.Add(Blobs(visual, "Leg", hip,
                        new BlobShape.Blob(new Vector3(0f, -0.12f, 0f), new Vector3(0.042f, 0.14f, 0.042f), fur),
                        new BlobShape.Blob(new Vector3(0.02f, -0.255f, 0f), new Vector3(0.052f, 0.03f, 0.046f), light)).transform);
                var dog = go.AddComponent<Hazards.Dog>();
                dog.minX = minX;
                dog.maxX = maxX;
                dog.visual = visual;
                dog.legs = legs.ToArray();
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
                StreetBuilder.Patch(root, name + "Surface", fromX, toX, groundTop, -StreetBuilder.RoadHalf, StreetBuilder.RoadHalf, color);

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
                    var streak = FlatDecor("Streak", new Vector2(sx, sy), size, new Color(1f, 1f, 1f, 0.55f));
                    streak.GetComponent<SpriteRenderer>().sortingOrder = 30;
                    streaks.Add(streak.transform);
                }
                wind.streaks = streaks.ToArray();
            }

            /// <summary>A platform that slides by <paramref name="travel"/> and back.</summary>
            public void MovingPlatform(Vector2 center, float width, Vector2 travel, float speed = 1.5f)
            {
                var go = Block("MovingPlatform", center, new Vector2(width, 0.35f), PlatformColor, GroundMat);
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
                gateGo.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var gate = gateGo.AddComponent<Gate>();
                gate.openHeight = gateHeight + 0.2f;

                // A frame for the gate to slide up into, so the open gate never floats.
                float frameTop = groundTop + gateHeight * 2f + 0.45f;
                Color frame = new Color(0.55f, 0.4f, 0.3f);
                foreach (float side in new[] { -0.3f, 0.3f })
                    Decor("GateFrame", new Vector2(gateX + side, (groundTop + frameTop) * 0.5f - 0.1f), new Vector2(0.14f, frameTop - groundTop + 0.2f), frame, 1.8f);
                Decor("GateLintel", new Vector2(gateX, frameTop), new Vector2(0.9f, 0.2f), frame, 1.8f);

                var sw = Block("Switch", switchPosition, new Vector2(0.55f, 0.55f), new Color(0.3f, 0.3f, 0.32f), GroundMat, true, 0.55f);
                // The lamp is a round button on the switch's face, lit by BallSwitch.
                var lamp = new GameObject("Indicator");
                lamp.transform.SetParent(sw.transform, false);
                lamp.transform.localPosition = new Vector3(0f, 0f, -0.29f);
                var button = lamp.AddComponent<CylinderShape>();
                button.radius = 0.16f;
                button.length = 0.06f;
                button.sideColor = button.endColor = button.innerColor = Color.white;
                lamp.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                button.Rebuild();
                var ballSwitch = sw.AddComponent<BallSwitch>();
                ballSwitch.gates = new[] { gate };
                ballSwitch.indicator = lamp.GetComponent<MeshRenderer>();
                Decor("SwitchPost", new Vector2(switchPosition.x, (groundTop + switchPosition.y) * 0.5f),
                    new Vector2(0.1f, switchPosition.y - groundTop), ObstacleColor);
            }

            /// <summary>A seagull that swoops from fromX to toX (right to left = toward the kid).</summary>
            public void Seagull(float fromX, float toX, float baseY, float phaseOffset = 0f)
            {
                var go = new GameObject("Seagull");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(fromX, baseY);
                go.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<CircleCollider2D>();
                col.isTrigger = true;
                col.radius = 0.4f;
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                // A 3D gull: white body, grey back and wings with dark tips, a yellow beak.
                Color white = new Color(0.97f, 0.97f, 0.98f), grey = new Color(0.66f, 0.7f, 0.76f), tip = new Color(0.18f, 0.18f, 0.22f);
                Blobs(visual, "Body", Vector3.zero,
                    new BlobShape.Blob(new Vector3(0f, 0f, 0f), new Vector3(0.24f, 0.09f, 0.09f), white),
                    new BlobShape.Blob(new Vector3(-0.03f, 0.035f, 0f), new Vector3(0.18f, 0.06f, 0.075f), grey),
                    new BlobShape.Blob(new Vector3(0.21f, 0.06f, 0f), new Vector3(0.085f, 0.075f, 0.07f), white),
                    new BlobShape.Blob(new Vector3(0.31f, 0.05f, 0f), new Vector3(0.055f, 0.018f, 0.018f), new Color(1f, 0.8f, 0.25f)),
                    new BlobShape.Blob(new Vector3(0.25f, 0.09f, -0.055f), new Vector3(0.012f, 0.014f, 0.01f), tip),
                    new BlobShape.Blob(new Vector3(0.25f, 0.09f, 0.055f), new Vector3(0.012f, 0.014f, 0.01f), tip),
                    new BlobShape.Blob(new Vector3(-0.26f, 0.01f, 0f), new Vector3(0.09f, 0.025f, 0.065f), grey));
                var wings = new List<Transform>();
                foreach (float side in new[] { -1f, 1f })
                    wings.Add(Blobs(visual, "Wing", new Vector3(0f, 0.04f, side * 0.06f),
                        new BlobShape.Blob(new Vector3(-0.02f, 0f, side * 0.22f), new Vector3(0.12f, 0.018f, 0.22f), grey),
                        new BlobShape.Blob(new Vector3(-0.06f, 0f, side * 0.42f), new Vector3(0.08f, 0.014f, 0.08f), tip)).transform);
                var gull = go.AddComponent<Hazards.Seagull>();
                gull.fromX = fromX;
                gull.toX = toX;
                gull.baseY = baseY;
                gull.phaseOffset = phaseOffset;
                gull.visual = visual;
                gull.wings = wings.ToArray();
            }

            /// <summary>Sea water washing over the sand between fromX and toX. Cross at low tide.</summary>
            public void Tide(float fromX, float toX, float period = 6f, float phaseOffset = 0f, float groundTop = 0f)
            {
                float width = toX - fromX;
                var go = new GameObject("Tide");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((fromX + toX) * 0.5f, groundTop);
                go.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;

                // Darker wet sand marks where the sea reaches. The water is a tapering lens of sea with a
                // foam crest, behind the ground so only the part above the sand shows as it washes in.
                StreetBuilder.Patch(root, "WetSand", fromX - 0.5f, toX + 0.5f, groundTop, StreetBuilder.FrontZ, 9f, new Color(0.78f, 0.68f, 0.52f), Art.surfaces[ProceduralArt.Surface.Sand]);
                // A sheet of sea washing up the beach over this stretch: hidden under the sand at low
                // water, covering it (with the waves scrolling) at high water.
                float zc = (StreetBuilder.FrontZ + 9f) * 0.5f;
                var water = StreetBuilder.Solid(root, "Water", new Vector3((fromX + toX) * 0.5f, groundTop - 0.1f, zc),
                    new Vector3(width + 1.6f, 0.2f, 9f - StreetBuilder.FrontZ), Color.white, Art.surfaces[ProceduralArt.Surface.Sea]);
                water.faces = MeshBuilder.Faces.Top | MeshBuilder.Faces.Front | MeshBuilder.Faces.Left | MeshBuilder.Faces.Right;
                water.Rebuild();
                water.transform.SetParent(go.transform, true);

                var zoneGo = new GameObject("TideLoseZone");
                zoneGo.transform.SetParent(go.transform, false);
                zoneGo.transform.localPosition = new Vector3(0f, -0.35f, 0f);
                var trigger = zoneGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(width, 0.5f);
                zoneGo.AddComponent<LoseZone>().message = "lose.tide";

                var tide = go.AddComponent<Hazards.Tide>();
                tide.lowOffset = -0.9f;
                tide.highOffset = 0.45f;
                tide.period = period;
                tide.phaseOffset = phaseOffset;
                tide.surface = water.transform;
            }

            /// <summary>A dark tunnel with a ceiling: darkens the screen around the kid while inside.</summary>
            public void Tunnel(float fromX, float toX, float groundTop = 0f, float height = 3.3f)
            {
                float center = (fromX + toX) * 0.5f;
                float width = toX - fromX;
                // An underpass: a back wall and a deep concrete deck over the street.
                StreetBuilder.Solid(root, "TunnelBack", new Vector3(center, groundTop + height * 0.5f, StreetBuilder.RoadHalf + 0.6f), new Vector3(width, height, 0.4f), new Color(0.36f, 0.34f, 0.38f));
                Block("TunnelCeiling", new Vector2(center, groundTop + height + 0.6f), new Vector2(width + 1f, 1.2f), new Color(0.62f, 0.62f, 0.64f), GroundMat, true, 7.4f);
                for (float lx = fromX + 3f; lx < toX - 1f; lx += 6f)
                {
                    var lamp = Visual(root, "TunnelLamp", Circle, new Vector2(lx, groundTop + height - 0.35f), new Vector2(0.45f, 0.22f), new Color(1f, 0.9f, 0.6f), -4);
                    lamp.transform.position = new Vector3(lamp.transform.position.x, lamp.transform.position.y, StreetBuilder.RoadHalf + 0.35f);
                }

                var go = new GameObject("DarkZone");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(center, groundTop + height * 0.5f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(width, height);
                go.AddComponent<DarkZone>();
            }

            /// <summary>Spawns pipes at <paramref name="position"/> that roll left until <paramref name="despawnX"/>.</summary>
            public void Pipes(Vector2 position, float interval, float despawnX, float firstDelay = 1.5f)
            {
                var go = new GameObject("PipeSpawner");
                go.transform.SetParent(root, false);
                go.transform.position = position;
                var spawner = go.AddComponent<PipeSpawner>();
                spawner.interval = interval;
                spawner.despawnX = despawnX;
                spawner.firstDelay = firstDelay;
                spawner.material = Art.solid;
                // A stack of pipes beside the spawn point, lying across the street.
                Vector2 stack = position + new Vector2(0.9f, -0.2f);
                float r = spawner.radius;
                Vector2[] at = { new Vector2(-r, -0.55f + r), new Vector2(r, -0.55f + r), new Vector2(0f, -0.55f + r * 2.7f) };
                foreach (var o in at)
                {
                    var pipe = new GameObject("StackedPipe");
                    pipe.transform.SetParent(root, false);
                    pipe.transform.position = new Vector3(stack.x + o.x, stack.y + o.y, 0.6f);
                    PipeSpawner.BuildPipe(pipe, r, spawner.color, Art.solid);
                }
            }

            /// <summary>A swing seat hanging from <paramref name="pivot"/>.</summary>
            public void Swing(Vector2 pivot, float ropeLength, float amplitude = 35f, float period = 3f, float phaseOffset = 0f)
            {
                // A swing frame standing across the street: the beam runs in depth over the seat,
                // on splayed A-frame legs at either end, clear of the kid's path.
                Color wood = new Color(0.55f, 0.4f, 0.3f);
                float frameZ = 1.1f, ground = GroundTopUnder(pivot.x, pivot.y);
                Decor("SwingBeam", pivot + new Vector2(0f, 0.1f), new Vector2(0.2f, 0.2f), wood, frameZ * 2f + 0.3f);
                foreach (float z in new[] { -frameZ, frameZ })
                    foreach (float splay in new[] { -1f, 1f })
                    {
                        float height = pivot.y + 0.1f - ground;
                        var leg = Decor("SwingLeg", new Vector2(pivot.x + splay * height * 0.18f, ground + height * 0.5f), new Vector2(0.15f, height / Mathf.Cos(Mathf.Atan(0.36f))), wood, 0.15f, z);
                        leg.transform.rotation = Quaternion.Euler(0f, 0f, splay * Mathf.Atan(0.36f) * Mathf.Rad2Deg);
                    }

                var seat = Block("SwingSeat", pivot + Vector2.down * ropeLength, new Vector2(1.4f, 0.2f), new Color(0.85f, 0.35f, 0.3f), GroundMat, true, 0.7f);
                seat.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var rope = seat.AddComponent<LineRenderer>();
                rope.sharedMaterial = trailMaterial;
                rope.positionCount = 2;
                rope.widthMultiplier = 0.05f;
                rope.startColor = rope.endColor = new Color(0.35f, 0.3f, 0.25f);
                rope.sortingOrder = -1;
                rope.useWorldSpace = true;
                var swing = seat.AddComponent<SwingPlatform>();
                swing.pivot = pivot;
                swing.ropeLength = ropeLength;
                swing.amplitude = amplitude;
                swing.period = period;
                swing.phaseOffset = phaseOffset;
                swing.rope = rope;
            }

            /// <summary>A fountain whose spray lifts the ball (dribble into it to pop the ball up).</summary>
            /// <summary>A plaza floor fountain: pulsing jets from a grate flush with the paving, which lift the ball.</summary>
            public void Fountain(float x, float groundTop, float height, float strength)
            {
                StreetBuilder.Patch(root, "WetPaving", x - 1.8f, x + 1.8f, groundTop, -2.2f, 2.2f, new Color(0.55f, 0.6f, 0.62f));
                StreetBuilder.Patch(root, "Grate", x - 0.75f, x + 0.75f, groundTop, -0.75f, 0.75f, new Color(0.3f, 0.32f, 0.36f), null, 0.02f);
                for (float gx = x - 0.6f; gx <= x + 0.61f; gx += 0.2f)
                    StreetBuilder.Patch(root, "GrateSlot", gx - 0.04f, gx + 0.04f, groundTop, -0.65f, 0.65f, new Color(0.12f, 0.13f, 0.15f), null, 0.03f);

                var go = new GameObject("Fountain");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(x, groundTop);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(1.1f, height);
                trigger.offset = new Vector2(0f, height * 0.5f);
                var fountain = go.AddComponent<Hazards.Fountain>();
                fountain.maxHeight = height;
                fountain.strength = strength;
                fountain.phaseOffset = x * 0.37f;
                fountain.jetSpriteHeight = Art.waterJet.bounds.size.y;

                // One tall jet with a smaller one either side, leaning out a little.
                float[] offsets = { 0f, -0.45f, 0.45f };
                float[] widths = { 1f, 0.7f, 0.7f };
                fountain.jets = new Transform[offsets.Length];
                for (int i = 0; i < offsets.Length; i++)
                {
                    var jet = SpriteObject(go.transform, "Jet" + i, Art.waterJet, new Vector3(offsets[i], 1f, 0f), 6);
                    jet.transform.localScale = new Vector3(widths[i], 1f, 1f);
                    jet.transform.localRotation = Quaternion.Euler(0f, 0f, -offsets[i] * 18f);
                    fountain.jets[i] = jet.transform;
                }
                fountain.droplets = new Transform[6];
                for (int i = 0; i < fountain.droplets.Length; i++)
                {
                    var drop = SpriteObject(go.transform, "Droplet", Art.drop, new Vector3(0f, 0.5f, 0f), 7, new Color(0.75f, 0.9f, 1f, 0.9f));
                    drop.transform.localScale = Vector3.one * 0.3f;
                    fountain.droplets[i] = drop.transform;
                }
            }

            /// <summary>First-time tutorial hint when the kid reaches x (text key tut.&lt;id&gt;).</summary>
            public void Hint(float x, string id, float groundTop = 0f)
            {
                var go = new GameObject("Hint_" + id);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(x, groundTop + 2f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(0.6f, 4f);
                go.AddComponent<Tutorial.TutorialHint>().hintId = id;
            }

            // ---------- Challenges ----------

            /// <summary>A target the ball must hit (accuracy challenge).</summary>
            public ChallengeTarget Target(Vector2 position, bool onPost = true, float groundTop = 0f)
            {
                if (onPost)
                    Decor("TargetPost", new Vector2(position.x, (groundTop + position.y) * 0.5f), new Vector2(0.1f, position.y - groundTop), ObstacleColor);
                var go = new GameObject("Target");
                go.transform.SetParent(root, false);
                go.transform.position = position;
                var col = go.AddComponent<CircleCollider2D>();
                col.isTrigger = true;
                col.radius = 0.45f;
                // A round target board facing the street: white rim, tinted face, red bull's-eye.
                var board = new GameObject("Board");
                board.transform.SetParent(go.transform, false);
                var disc = board.AddComponent<CylinderShape>();
                disc.radius = 0.475f;
                disc.length = 0.1f;
                disc.sideColor = disc.endColor = Color.white;
                disc.innerRadius = 0.375f;
                disc.innerColor = Color.white;
                board.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                disc.Rebuild();
                var faceGo = new GameObject("Face");
                faceGo.transform.SetParent(go.transform, false);
                faceGo.transform.localPosition = new Vector3(0f, 0f, -0.04f);
                var faceDisc = faceGo.AddComponent<CylinderShape>();
                faceDisc.radius = 0.375f;
                faceDisc.length = 0.04f;
                faceDisc.sideColor = faceDisc.endColor = Color.white;
                faceDisc.innerRadius = 0.15f;
                faceDisc.innerColor = new Color(0.9f, 0.35f, 0.3f);
                faceGo.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                faceDisc.Rebuild();
                var target = go.AddComponent<ChallengeTarget>();
                target.face = faceGo.GetComponent<MeshRenderer>();
                return target;
            }

            /// <summary>A slalom gate: Low = keep the ball under the bar; Hoop = loft it through.</summary>
            public SlalomGate SlalomGate(float x, SlalomGate.Kind kind, float groundTop = 0f)
            {
                var go = new GameObject(kind == Challenges.SlalomGate.Kind.Low ? "LowGate" : "Hoop");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(x, groundTop);
                var gate = go.AddComponent<SlalomGate>();
                gate.kind = kind;
                var flags = new List<Renderer>();
                Color c = new Color(1f, 0.85f, 0.3f);
                if (kind == Challenges.SlalomGate.Kind.Low)
                {
                    gate.height = 0.7f;
                    // A low bar across the street on two posts.
                    foreach (float z in new[] { -0.9f, 0.9f })
                        flags.Add(Bar(go.transform, "Post", new Vector3(0f, 0.45f, z), new Vector3(0.08f, 0.9f, 0.08f)));
                    flags.Add(Bar(go.transform, "Bar", new Vector3(0f, 0.85f, 0f), new Vector3(0.08f, 0.08f, 1.9f)));
                }
                else
                {
                    gate.height = 1.4f;
                    gate.hoopSize = 1.3f;
                    // A square hoop on a pole beside the street, open toward the kid.
                    Bar(go.transform, "Pole", new Vector3(0f, 0.7f, 0.75f), new Vector3(0.08f, 1.4f, 0.08f)).GetComponent<Box3D>().color = ObstacleColor;
                    flags.Add(Bar(go.transform, "HoopBottom", new Vector3(0f, 1.4f, 0f), new Vector3(0.08f, 0.08f, 1.58f)));
                    flags.Add(Bar(go.transform, "HoopTop", new Vector3(0f, 2.7f, 0f), new Vector3(0.08f, 0.08f, 1.58f)));
                    flags.Add(Bar(go.transform, "HoopNear", new Vector3(0f, 2.05f, -0.75f), new Vector3(0.08f, 1.38f, 0.08f)));
                    flags.Add(Bar(go.transform, "HoopFar", new Vector3(0f, 2.05f, 0.75f), new Vector3(0.08f, 1.38f, 0.08f)));
                }
                gate.flags = flags.ToArray();
                foreach (var f in flags) World.Tint.Set(f, c);
                return gate;
            }

            /// <summary>A white 3D bar (tinted at runtime with Tint) at a local position.</summary>
            static Renderer Bar(Transform parent, string name, Vector3 localCenter, Vector3 size)
            {
                var go = new GameObject(name);
                go.transform.SetParent(parent, false);
                go.transform.localPosition = localCenter;
                var box = go.AddComponent<Box3D>();
                box.size = size;
                box.color = Color.white;
                var r = go.GetComponent<MeshRenderer>();
                r.sharedMaterial = Art.solid;
                box.Rebuild();
                return r;
            }

            /// <summary>Adds the challenge logic object; returns it for configuration.</summary>
            public T Challenge<T>(string name, string instructions, float timeLimit, params int[] thresholds) where T : ChallengeObjective
            {
                var go = new GameObject("Challenge");
                go.transform.SetParent(root, false);
                var c = go.AddComponent<T>();
                c.challengeName = name;
                c.instructions = instructions;
                c.timeLimit = timeLimit;
                c.starThresholds = thresholds;
                return c;
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
                // A springy trampoline pad: a red mat on a dark frame, set into the street.
                var mat = new GameObject("Board");
                mat.transform.SetParent(visual, false);
                var top = mat.AddComponent<Box3D>();
                top.size = new Vector3(1.3f, 0.14f, 1.3f);
                top.color = BouncyColor;
                mat.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                top.Rebuild();
                var frameGo = new GameObject("Frame");
                frameGo.transform.SetParent(visual, false);
                frameGo.transform.localPosition = new Vector3(0f, -0.06f, 0f);
                var frameBox = frameGo.AddComponent<Box3D>();
                frameBox.size = new Vector3(1.45f, 0.1f, 1.45f);
                frameBox.color = new Color(0.25f, 0.25f, 0.28f);
                frameGo.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                frameBox.Rebuild();
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
                    new Vector2(toX - fromX, top - groundTop), PlatformColor, GroundMat);
            }

            /// <summary>Hop onto a step, stop, chip the ball over the high wall behind it.</summary>
            public void StepAndHighWall(float x, float groundTop = 0f)
            {
                Block("Step", new Vector2(x, groundTop + 0.4f), new Vector2(2f, 0.8f), ObstacleColor, GroundMat);
                Block("HighWall", new Vector2(x + 1.25f, groundTop + 0.9f), new Vector2(0.5f, 1.8f), ObstacleColor, GroundMat);
            }

            /// <summary>A bouncy awning the ball can be kicked off.</summary>
            public void Awning(float x, float height, float groundTop = 0f)
            {
                Block("Awning", new Vector2(x, groundTop + height), new Vector2(2.2f, 0.2f), BouncyColor, BouncyMat);
                Decor("AwningPost", new Vector2(x + 1f, groundTop + height * 0.5f), new Vector2(0.12f, height), ObstacleColor, -1f, 0.7f);
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
                    // Flags stand at the far kerb, beside the line the kid crosses.
                    float flagZ = StreetBuilder.RoadHalf + 0.4f;
                    Decor("FlagPole", new Vector2(x, groundTop + 1.14f), new Vector2(0.08f, 2f), ObstacleColor, -1f, flagZ);
                    var flag = Decor("Flag", new Vector2(x + 0.31f, groundTop + 1.94f), new Vector2(0.55f, 0.35f), Color.white, 0.03f, flagZ);
                    cp.flag = flag.GetComponent<MeshRenderer>();
                    flag.transform.SetParent(go.transform, true);
                }

                checkpoints.Add(cp);
                return cp;
            }

            public void Goal(float x, float groundTop = 0f)
            {
                var school = new GameObject("School").transform;
                school.SetParent(root, false);
                // The school gate stands across the street: posts either side, a beam overhead.
                GoalX = x;
                float postZ = StreetBuilder.RoadHalf + 0.3f;
                StreetBuilder.Solid(school, "GatePostNear", new Vector3(x, groundTop + 1.6f, -postZ), new Vector3(0.45f, 3.2f, 0.45f), SchoolColor);
                StreetBuilder.Solid(school, "GatePostFar", new Vector3(x, groundTop + 1.6f, postZ), new Vector3(0.45f, 3.2f, 0.45f), SchoolColor);
                StreetBuilder.Solid(school, "GateTop", new Vector3(x, groundTop + 3.35f, 0f), new Vector3(0.5f, 0.4f, postZ * 2f + 0.6f), SchoolColor);

                var goalGo = new GameObject("GoalZone");
                goalGo.transform.SetParent(school, false);
                goalGo.transform.position = new Vector3(x, groundTop + 1.5f, 0f);
                var trigger = goalGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(2.6f, 3f);
                goalGo.AddComponent<GoalZone>();
                Banner("SCHOOL", new Vector2(x, groundTop + 3.95f), groundTop + 3.55f);
            }

            /// <summary>A signboard on posts. The posts are planted in the ground below once the layout is done (see Finish).</summary>
            public void Sign(string text, Vector2 position)
            {
                Vector2 boardSize;
                var go = SignBoard(text, position, out boardSize);
                pendingSigns.Add(new PendingSign { sign = go.transform, boardSize = boardSize });
            }

            /// <summary>A signboard hanging on short chains from something solid at <paramref name="hangFromY"/> (a gate, an awning).</summary>
            public void Banner(string text, Vector2 position, float hangFromY)
            {
                Vector2 boardSize;
                var go = SignBoard(text, position, out boardSize);
                float bottom = position.y - boardSize.y * 0.5f;
                float offset = boardSize.x * 0.5f - 0.3f;
                foreach (float side in new[] { -offset, offset })
                {
                    var chain = Decor("BannerChain", new Vector2(position.x + side, (bottom + hangFromY) * 0.5f), new Vector2(0.06f, Mathf.Abs(hangFromY - bottom) + 0.1f), new Color(0.35f, 0.32f, 0.3f));
                    chain.transform.SetParent(go.transform, true);
                }
            }

            /// <summary>Plant every sign's posts in the ground under it. Called once the whole layout exists.</summary>
            public void Finish()
            {
                foreach (var pending in pendingSigns) PlantSign(pending.sign, pending.boardSize);
                pendingSigns.Clear();
                BuildStreetSlabs();
            }

            /// <summary>
            /// The 3D street over every ground span, leaving gaps where side streets cross, and
            /// carrying on well past both ends of the level so the street never just stops.
            /// </summary>
            void BuildStreetSlabs()
            {
                var slabs = new GameObject("StreetSlabs").transform;
                slabs.SetParent(root, false);
                slabs.gameObject.AddComponent<StaticBatcher>();
                foreach (var span in groundSpans)
                {
                    float a = span.from;
                    bool closeLeft = true;
                    var cuts = new List<Vector2>(OpenAreas);
                    cuts.Sort((p, q) => p.x.CompareTo(q.x));
                    foreach (var cut in cuts)
                    {
                        if (cut.y <= a || cut.x >= span.to) continue;
                        if (cut.x > a) StreetBuilder.Slab(slabs, "Street", a, cut.x, span.top, closeLeft, false);
                        a = Mathf.Max(a, cut.y);
                        closeLeft = false;
                    }
                    if (span.to > a) StreetBuilder.Slab(slabs, "Street", a, span.to, span.top, closeLeft, true);
                }
                if (groundSpans.Count == 0) return;
                float startTop = 0f, endTop = 0f, first = float.MaxValue, last = float.MinValue;
                foreach (var span in groundSpans)
                {
                    if (span.from < first) { first = span.from; startTop = span.top; }
                    if (span.to > last) { last = span.to; endTop = span.top; }
                }
                StreetBuilder.Slab(slabs, "StreetBefore", first - 70f, first, startTop, false, false);
                StreetBuilder.Slab(slabs, "StreetAfter", last, last + 70f, endTop, false, false);
            }

            void PlantSign(Transform sign, Vector2 boardSize)
            {
                Vector2 pos = sign.position;
                float boardBottom = pos.y - boardSize.y * 0.5f;
                float half = boardSize.x * 0.5f;
                bool twoLegs = boardSize.x > 2.2f;
                float legOffset = twoLegs ? half - 0.35f : 0f;

                // Ground under every leg; a sign over a gap moves to the nearest edge instead of
                // floating, preferring the near side so it is read before the gap.
                float groundTop;
                if (!GroundUnder(pos.x - legOffset, pos.x + legOffset, boardBottom, out groundTop))
                {
                    float bestX = pos.x, bestDistance = float.MaxValue, bestTop = 0f;
                    for (int pass = 0; pass < 2 && bestDistance == float.MaxValue; pass++)
                    {
                        foreach (var span in groundSpans)
                        {
                            float lo = span.from + legOffset + 0.4f, hi = span.to - legOffset - 0.4f;
                            if (lo > hi) continue;
                            float x = Mathf.Clamp(pos.x, lo, hi);
                            if (pass == 0 && x > pos.x) continue;
                            if (Mathf.Abs(x - pos.x) < bestDistance)
                            {
                                bestDistance = Mathf.Abs(x - pos.x);
                                bestX = x;
                                bestTop = span.top;
                            }
                        }
                    }
                    if (bestDistance == float.MaxValue) return; // no ground at all: leave it be
                    pos.x = bestX;
                    groundTop = bestTop;
                }

                // Keep at least a short post so the board never sits in the grass.
                float minBottom = groundTop + 0.6f;
                if (boardBottom < minBottom)
                {
                    pos.y += minBottom - boardBottom;
                    boardBottom = minBottom;
                }
                // Signs stand on the far pavement, facing the street.
                sign.position = new Vector3(pos.x, pos.y + 0.14f, StreetBuilder.RoadHalf + 0.9f);

                // Posts sink a little into the ground; the grass strip (drawn on top) hides the joint.
                float postBottom = groundTop - 0.25f;
                float height = boardBottom - postBottom + 0.1f;
                Color wood = new Color(0.55f, 0.4f, 0.3f);
                var legs = twoLegs ? new[] { -legOffset, legOffset } : new[] { 0f };
                foreach (float lx in legs)
                {
                    var post = Decor("SignPost", new Vector2(pos.x + lx, postBottom + height * 0.5f), new Vector2(0.14f, height), wood, -1f, sign.position.z + 0.06f);
                    post.transform.SetParent(sign, true);
                }
            }

            /// <summary>Top of the highest ground span under <paramref name="x"/> that is below <paramref name="belowY"/> (0 if none yet).</summary>
            float GroundTopUnder(float x, float belowY)
            {
                float top = float.MinValue;
                foreach (var span in groundSpans)
                    if (x >= span.from && x <= span.to && span.top <= belowY) top = Mathf.Max(top, span.top);
                return top == float.MinValue ? 0f : top;
            }

            /// <summary>Highest ground top under both x positions that is below <paramref name="belowY"/>.</summary>
            bool GroundUnder(float xA, float xB, float belowY, out float top)
            {
                top = float.MinValue;
                float topA = float.MinValue, topB = float.MinValue;
                foreach (var span in groundSpans)
                {
                    if (span.top > belowY) continue;
                    if (xA >= span.from && xA <= span.to) topA = Mathf.Max(topA, span.top);
                    if (xB >= span.from && xB <= span.to) topB = Mathf.Max(topB, span.top);
                }
                if (topA == float.MinValue || topB == float.MinValue) return false;
                top = Mathf.Max(topA, topB);
                return true;
            }

            GameObject SignBoard(string text, Vector2 position, out Vector2 boardSize)
            {
                var go = new GameObject("Sign_" + text.Split('\n')[0]);
                go.transform.SetParent(root, false);
                go.transform.position = position;
                var textGo = new GameObject("Text");
                textGo.transform.SetParent(go.transform, false);
                textGo.transform.localPosition = new Vector3(0f, 0f, -0.05f);
                var mesh = textGo.AddComponent<TextMesh>();
                mesh.text = text;
                mesh.font = signFont;
                mesh.fontSize = 48;
                mesh.characterSize = 0.06f;
                mesh.anchor = TextAnchor.MiddleCenter;
                mesh.alignment = TextAlignment.Center;
                mesh.color = new Color(0.25f, 0.3f, 0.4f);
                var renderer = textGo.GetComponent<MeshRenderer>();
                if (signFont != null) renderer.sharedMaterial = signFont.material;
                renderer.sortingOrder = 6;

                // Wooden signboard behind the text.
                string[] lines = text.Split('\n');
                int longest = 0;
                foreach (var l in lines) longest = Mathf.Max(longest, l.Length);
                boardSize = new Vector2(longest * 0.135f + 0.6f, lines.Length * 0.3f + 0.35f);
                var board = new GameObject("SignBoard");
                board.transform.SetParent(go.transform, false);
                board.transform.localPosition = new Vector3(0f, 0f, 0.03f);
                var face = board.AddComponent<Box3D>();
                face.size = new Vector3(boardSize.x, boardSize.y, 0.08f);
                face.color = new Color(0.98f, 0.9f, 0.74f);
                board.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                face.Rebuild();
                // A darker frame round the edge.
                var rim = new GameObject("SignFrame");
                rim.transform.SetParent(go.transform, false);
                rim.transform.localPosition = new Vector3(0f, 0f, 0.05f);
                var frameBox = rim.AddComponent<Box3D>();
                frameBox.size = new Vector3(boardSize.x + 0.1f, boardSize.y + 0.1f, 0.06f);
                frameBox.color = new Color(0.5f, 0.36f, 0.26f);
                rim.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                frameBox.Rebuild();
                return go;
            }

            /// <summary>A coloured box with a matching collider. Scale drives both sprite and collider.</summary>
            /// <summary>
            /// A solid box with a matching 2D collider on the gameplay plane, drawn as a 3D block
            /// <paramref name="depth"/> deep (centred on z = 0). Invisible blocks are colliders only.
            /// </summary>
            public GameObject Block(string name, Vector2 center, Vector2 size, Color color, PhysicsMaterial2D material,
                bool visible = true, float depth = 1.6f, Material look = null)
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = center;
                if (visible)
                {
                    var box = go.AddComponent<World.Box3D>();
                    box.size = new Vector3(size.x, size.y, depth);
                    box.color = color;
                    go.GetComponent<MeshRenderer>().sharedMaterial = look != null ? look : Art.surfaces[ProceduralArt.Surface.Concrete];
                    box.Rebuild();
                }
                var col = go.AddComponent<BoxCollider2D>();
                col.size = size;
                col.offset = Vector2.zero;
                col.sharedMaterial = material;
                return go;
            }

            /// <summary>
            /// A 3D box with no collider (posts, beams, frames, flags) centred at
            /// (<paramref name="center"/>, <paramref name="z"/>). A negative depth makes it as deep as
            /// it is thin (a square post).
            /// </summary>
            public GameObject Decor(string name, Vector2 center, Vector2 size, Color color, float depth = -1f, float z = 0f)
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(center.x, center.y, z);
                var box = go.AddComponent<Box3D>();
                box.size = new Vector3(size.x, size.y, depth > 0f ? depth : Mathf.Clamp(Mathf.Min(size.x, size.y), 0.03f, 0.5f));
                box.color = color;
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                box.Rebuild();
                return go;
            }

            /// <summary>A flat, see-through sprite (effects such as wind streaks).</summary>
            public GameObject FlatDecor(string name, Vector2 center, Vector2 size, Color color)
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
