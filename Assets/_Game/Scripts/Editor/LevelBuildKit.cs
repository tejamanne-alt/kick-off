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
            var mood = Theme.mood;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = mood.horizon;
            camGo.AddComponent<AudioListener>();
            camGo.transform.position = new Vector3(3f, 2f, -20f);
            // The chapter's light and atmosphere (docs/ART_DIRECTION.md), then the finishing pass.
            var look = camGo.AddComponent<WorldLook>();
            look.sunDirection = mood.sunDirection;
            look.sunColor = mood.sun;
            look.skySunDirection = mood.skySunDirection;
            look.sunGlow = mood.glow;
            look.ambientSky = mood.ambientSky;
            look.ambientGround = mood.ambientGround;
            look.skyZenith = mood.zenith;
            look.skyHorizon = mood.horizon;
            look.hazeColor = mood.haze;
            look.hazeStart = mood.hazeStart;
            look.hazeEnd = mood.hazeEnd;
            look.hazeStrength = mood.hazeStrength;
            look.Apply();
            var post = camGo.AddComponent<PostFX>();
            post.shader = Shader.Find("Hidden/DribbleToSchool/PostFX");   // referenced, so builds include it
            post.lift = mood.lift;
            post.gain = mood.gain;
            post.bloomTint = Color.Lerp(mood.glow, Color.white, 0.4f);
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
            // The teen boy and girl made in Blender (tools/blender/teen.py); Settings picks one.
            // Neck heights make them about 1.75 m (him) and 1.68 m (her) tall.
            // Without them, the younger Blender kid, or the procedural one.
            var boyRig = BuildModelCharacter(kidGo.transform, "Boy", Art.boy, 1.5f, TeenFeet(1.5f), true);
            var girlRig = boyRig.rig != null ? BuildModelCharacter(kidGo.transform, "Girl", Art.girl, 1.43f, TeenFeet(1.43f), true) : new CharacterParts();
            var kidRig = boyRig;
            if (kidRig.rig == null) kidRig = BuildModelCharacter(kidGo.transform, "Kid", Art.kid, 1.3f, Vector3.zero, true);
            if (kidRig.rig == null)
                kidRig = BuildCharacter(kidGo.transform, "Visual", Vector2.zero, 1f, KidColor, new Color(0.22f, 0.23f, 0.42f),
                    new Color(0.16f, 0.15f, 0.2f), true);   // glossy near-black hair
            var feet = new GameObject("Feet").transform;
            feet.SetParent(kidGo.transform, false);
            feet.localPosition = new Vector3(0f, -0.6f, 0f);
            var kid = kidGo.AddComponent<KidController>();
            kid.tuning = playerTuning;
            kid.feet = feet;
            kidRig.rig.gameObject.AddComponent<KidAnimator>().kid = kid;
            MonoBehaviour kidOutfit = kidRig.outfit;
            var kidFlags = new List<SpriteRenderer> { kidRig.flag };
            if (boyRig.rig != null && girlRig.rig == null)
                Debug.LogWarning("[Dribble To School] The girl model did not load: Settings > Player will always show the boy.");
            if (girlRig.rig != null)
            {
                girlRig.rig.gameObject.AddComponent<KidAnimator>().kid = kid;
                boyRig.visual.name = "Boy";
                girlRig.visual.name = "Girl";
                var choice = kidGo.AddComponent<CharacterChoice>();
                choice.boy = boyRig.visual.gameObject;
                choice.girl = girlRig.visual.gameObject;
                choice.boyOutfit = boyRig.outfit;
                choice.girlOutfit = girlRig.outfit;
                kidOutfit = choice;
                kidFlags.Add(girlRig.flag);
            }

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
            applier.kidBody = kidOutfit;
            applier.backpackFlags = kidFlags.ToArray();

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
            /// <summary>What the shop's outfits recolour (the body, or the imported model).</summary>
            public MonoBehaviour outfit;
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
            parts.outfit = body3D;
            return parts;
        }

        public const string ModelsDir = "Assets/_Game/Art/Models";

        /// <summary>
        /// The kid modelled, rigged and textured in Blender (Art/Models/Kid.fbx), turned to face +x
        /// with its feet at local y -0.6, under a Body transform the CharacterRig bobs and leans.
        /// Its bones become the rig's joints; the limbs nearer the camera are the "front" ones.
        /// Returns parts with no rig if the model is missing or not as expected.
        /// </summary>
        static CharacterParts BuildModelCharacter(Transform parent, string file, Material material, float neckHeight, Vector3 visualPos, bool kid)
        {
            var parts = new CharacterParts();
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelsDir + "/" + file + ".fbx");
            if (prefab == null)
            {
                Debug.LogWarning("[Dribble To School] Missing " + ModelsDir + "/" + file + ".fbx; using a fallback character.");
                return parts;
            }

            var visual = new GameObject("Visual").transform;
            visual.SetParent(parent, false);
            visual.localPosition = visualPos;
            var body = new GameObject("Body").transform;
            body.SetParent(visual, false);
            var model = (GameObject)Object.Instantiate(prefab);
            model.name = file + "Model";
            model.transform.SetParent(body, false);

            System.Func<string, Transform> bone = n => FindDeep(model.transform, n) ?? FindDeep(model.transform, n.Replace('.', '_'));
            Transform hips = bone("Hips"), head = bone("Head"), bag = bone("Bag");
            Transform legL = bone("UpperLeg.L"), legR = bone("UpperLeg.R"), kneeL = bone("LowerLeg.L"), kneeR = bone("LowerLeg.R");
            Transform armL = bone("UpperArm.L"), armR = bone("UpperArm.R"), elbowL = bone("LowerArm.L"), elbowR = bone("LowerArm.R");
            var smr = model.GetComponentInChildren<SkinnedMeshRenderer>();
            if (hips == null || head == null || (kid && bag == null) || legL == null || legR == null || kneeL == null || kneeR == null ||
                armL == null || armR == null || elbowL == null || elbowR == null || smr == null)
            {
                Debug.LogWarning("[Dribble To School] " + file + ".fbx is missing bones; using the procedural character.");
                Object.DestroyImmediate(visual.gameObject);
                return parts;
            }

            // Face +x: the Nose marker bone sits in front of the face.
            Transform nose = bone("Nose");
            Vector3 back = nose != null ? head.position - nose.position : (bag != null ? bag.position - hips.position : Vector3.left);
            back.y = 0f;
            if (back.sqrMagnitude > 1e-6f)
                model.transform.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(-back, Vector3.right, Vector3.up), Vector3.up) * model.transform.rotation;
            // Size: the neck joint at neckHeight above the feet (1.3 for the kid, who is about 1.55 tall).
            float headHeight = head.position.y - model.transform.position.y;
            if (headHeight > 0.01f) model.transform.localScale *= neckHeight / headHeight;
            model.transform.localPosition = new Vector3(0f, -0.6f * neckHeight / 1.3f, 0f);
            Vector3 offset = hips.position - body.position;
            model.transform.position -= new Vector3(offset.x, 0f, offset.z);

            bool rightNear = legR.position.z < legL.position.z;
            var rig = body.gameObject.AddComponent<CharacterRig>();
            rig.body = body;
            rig.legFront = rightNear ? legR : legL; rig.legBack = rightNear ? legL : legR;
            rig.kneeFront = rightNear ? kneeR : kneeL; rig.kneeBack = rightNear ? kneeL : kneeR;
            rig.armFront = rightNear ? armR : armL; rig.armBack = rightNear ? armL : armR;
            rig.elbowFront = rightNear ? elbowR : elbowL; rig.elbowBack = rightNear ? elbowL : elbowR;
            rig.head = head;
            rig.bag = bag;

            smr.sharedMaterial = material;
            smr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            smr.receiveShadows = false;
            smr.updateWhenOffscreen = false;
            var outfit = smr.gameObject.AddComponent<ModelOutfit>();
            ReadOutfitColors(file, outfit);
            parts.rig = rig;
            parts.visual = visual;
            parts.outfit = outfit;
            if (!kid) return parts;

            // The shop's pennant, clipped to the top of the bag on the camera side: the kid's
            // backpack, or the teens' satchel (its bone sits at the bag's top edge).
            Vector3 polePos = new Vector3(-0.18f, 0.6f, -0.16f);
            if (file != "Kid")
            {
                Vector3 top = body.InverseTransformPoint(bag.position);
                polePos = new Vector3(top.x - 0.02f, top.y + 0.08f, -0.15f);
            }
            var pole = Visual(bag, "FlagPole", Square, Vector2.zero, new Vector2(0.015f, 0.2f), new Color(0.3f, 0.25f, 0.2f), 7);
            pole.transform.position = body.TransformPoint(polePos);
            pole.transform.rotation = body.rotation;
            var flag = Visual(bag, "BackpackFlag", Square, Vector2.zero, new Vector2(0.12f, 0.09f), Color.white, 7);
            flag.transform.position = body.TransformPoint(polePos + new Vector3(-0.06f, 0.06f, 0f));
            flag.transform.rotation = body.rotation;

            parts.flag = flag.GetComponent<SpriteRenderer>();
            return parts;
        }

        [Serializable]
        class ModelColors { public float[] top; public float[] legwear; public float[] hair; }

        /// <summary>
        /// The colours a model was made with (its top, legwear and hair), from the JSON file the
        /// Blender script writes next to the FBX (tools/blender/teen.py), so the shop's outfits
        /// recolour from the right base. Models without one keep ModelOutfit's defaults.
        /// </summary>
        static void ReadOutfitColors(string file, ModelOutfit outfit)
        {
            string path = ModelsDir + "/" + file + ".json";
            if (!File.Exists(path)) return;
            var colors = JsonUtility.FromJson<ModelColors>(File.ReadAllText(path));
            System.Func<float[], Color, Color> rgb = (v, fallback) => v != null && v.Length >= 3 ? new Color(v[0], v[1], v[2]) : fallback;
            outfit.defaultShirt = rgb(colors.top, outfit.defaultShirt);
            outfit.defaultLegwear = rgb(colors.legwear, outfit.defaultLegwear);
            outfit.defaultHair = rgb(colors.hair, outfit.defaultHair);
        }

        /// <summary>Lifts a model built with <paramref name="neckHeight"/> so its feet stay on the kid's (local y -0.6).</summary>
        static Vector3 TeenFeet(float neckHeight)
        {
            return new Vector3(0f, 0.6f * neckHeight / 1.3f - 0.6f, 0f);
        }

        static Transform FindDeep(Transform root, string name)
        {
            if (root.name == name) return root;
            for (int i = 0; i < root.childCount; i++)
            {
                var found = FindDeep(root.GetChild(i), name);
                if (found != null) return found;
            }
            return null;
        }

        static Transform Pivot(Transform parent, string name, Vector3 localPos)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = localPos;
            return t;
        }

        /// <summary>A 3D car with its wheels on <paramref name="position"/>, turned <paramref name="yaw"/> degrees (0 faces +x, 90 faces the camera).</summary>
        // ---------- Asset kits (tools/blender/kit_*.py, docs/ART_DIRECTION.md) ----------

        /// <summary>The asset kits made in Blender, each in Art/Models/&lt;kit&gt;/ with its atlas and manifest.</summary>
        public static readonly string[] Kits = { "Plants", "Buildings", "Street", "Terrain", "Structures", "Animals" };

        static readonly Dictionary<string, Dictionary<string, object>> kitManifests = new Dictionary<string, Dictionary<string, object>>();

        /// <summary>A model's entry in its kit's manifest (size, min, max, tris, parts, ...), or null.</summary>
        public static Dictionary<string, object> KitInfo(string kit, string model)
        {
            Dictionary<string, object> models;
            if (!kitManifests.TryGetValue(kit, out models))
            {
                string path = ModelsDir + "/" + kit + "/" + kit + ".json";
                if (File.Exists(path))
                {
                    var root = MiniJson.Parse(File.ReadAllText(path)) as Dictionary<string, object>;
                    object m;
                    if (root != null && root.TryGetValue("models", out m)) models = m as Dictionary<string, object>;
                }
                kitManifests[kit] = models;
            }
            object entry;
            return models != null && models.TryGetValue(model, out entry) ? entry as Dictionary<string, object> : null;
        }

        /// <summary>A kit model's size from its manifest: x across, y up, z deep (Unity axes), or zero if unknown.</summary>
        public static Vector3 KitSize(string kit, string model)
        {
            var info = KitInfo(kit, model);
            object size;
            if (info == null || !info.TryGetValue("size", out size)) return Vector3.zero;
            var v = size as List<object>;
            return v != null && v.Count >= 3 ? new Vector3(Convert.ToSingle(v[0]), Convert.ToSingle(v[2]), Convert.ToSingle(v[1])) : Vector3.zero;
        }

        public static bool HasKitModel(string kit, string model)
        {
            return AssetDatabase.LoadAssetAtPath<GameObject>(ModelsDir + "/" + kit + "/" + model + ".fbx") != null;
        }

        /// <summary>
        /// Places a kit model with its origin at <paramref name="position"/>, its front turned toward the
        /// camera (-z) and then by <paramref name="yaw"/> degrees. Tints recolour its parts 1 to 3 (by
        /// brightness ratio to the manifest's base colours). Returns null if the model isn't there, so
        /// the caller can fall back to the procedural look.
        /// </summary>
        public static Transform KitModel(Transform parent, string kit, string model, Vector3 position, float yaw = 0f, float scale = 1f,
            Color? tint1 = null, Color? tint2 = null, Color? tint3 = null, bool castShadows = true)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelsDir + "/" + kit + "/" + model + ".fbx");
            Material material;
            if (prefab == null || Art == null || !Art.kits.TryGetValue(kit, out material) || material == null) return null;
            var go = new GameObject(model);
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            var inst = (GameObject)Object.Instantiate(prefab);
            inst.name = model + "Model";
            inst.transform.SetParent(go.transform, false);
            // Face the camera: the Attach.Front marker sits 1 m in front of the model's origin.
            Transform front = FindDeep(inst.transform, "Attach.Front") ?? FindDeep(inst.transform, "Attach_Front");
            if (front != null)
            {
                Vector3 dir = front.position - inst.transform.position;
                dir.y = 0f;
                Vector3 want = go.transform.rotation * Vector3.back;
                if (dir.sqrMagnitude > 1e-6f)
                    inst.transform.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(dir, want, Vector3.up), Vector3.up) * inst.transform.rotation;
            }
            go.transform.localScale = Vector3.one * scale;

            var bases = KitPartColors(KitInfo(kit, model));
            var tints = new[] { tint1 ?? Color.clear, tint2 ?? Color.clear, tint3 ?? Color.clear };
            bool tinted = tint1.HasValue || tint2.HasValue || tint3.HasValue;
            foreach (var r in inst.GetComponentsInChildren<MeshRenderer>())
            {
                r.sharedMaterial = material;
                r.shadowCastingMode = castShadows ? UnityEngine.Rendering.ShadowCastingMode.On : UnityEngine.Rendering.ShadowCastingMode.Off;
                r.receiveShadows = true;
                if (!tinted) continue;
                var tint = r.gameObject.AddComponent<ModelTint>();
                tint.baseColors = bases;
                tint.tints = tints;
            }
            return go.transform;
        }

        static Color[] KitPartColors(Dictionary<string, object> info)
        {
            var colors = new Color[3];
            object partsObj;
            var parts = info != null && info.TryGetValue("parts", out partsObj) ? partsObj as Dictionary<string, object> : null;
            for (int p = 0; p < 3; p++)
            {
                object c;
                var rgb = parts != null && parts.TryGetValue((p + 1).ToString(), out c) ? c as List<object> : null;
                colors[p] = rgb != null && rgb.Count >= 3 ? new Color(Convert.ToSingle(rgb[0]), Convert.ToSingle(rgb[1]), Convert.ToSingle(rgb[2])) : Color.white;
            }
            return colors;
        }

        /// <summary>The cars made in Blender (Art/Models/Cars/&lt;type&gt;.fbx).</summary>
        public static readonly string[] CarTypes = { "Hatch", "Wagon", "Van", "Pickup", "Fourby" };

        [Serializable]
        class CarInfo { public float[] paint; public float wheelRadius = 0.32f; }

        /// <summary>
        /// A car standing with its wheels on <paramref name="position"/>, turned <paramref name="yaw"/>
        /// degrees (0 faces +x, 90 faces the camera): the Blender-made car of that type, repainted
        /// (null keeps its own paint), with wheels that roll as it moves; the procedural hatchback
        /// if the model is missing.
        /// </summary>
        static Transform Car(Transform parent, string name, Vector3 position, float yaw, Color? paint, string type = "Hatch")
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.rotation = Quaternion.Euler(0f, yaw, 0f);

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelsDir + "/Cars/" + type + ".fbx");
            Material material;
            if (prefab != null && Art.cars.TryGetValue(type, out material))
            {
                var model = (GameObject)Object.Instantiate(prefab);
                model.name = type + "Model";
                model.transform.SetParent(go.transform, false);
                // The body is the mesh that isn't a wheel (Unity may have made it the asset root).
                Transform body = null;
                var wheels = new List<Transform>();
                Vector3 frontWheels = Vector3.zero, rearWheels = Vector3.zero;
                int fronts = 0, rears = 0;
                foreach (var r in model.GetComponentsInChildren<MeshRenderer>())
                {
                    string n = r.name.Replace('_', '.');
                    if (n.StartsWith("Wheel"))
                    {
                        wheels.Add(r.transform);
                        if (n.EndsWith(".FL") || n.EndsWith(".FR")) { frontWheels += r.transform.position; fronts++; }
                        else { rearWheels += r.transform.position; rears++; }
                    }
                    else if (body == null || n == "Body") body = r.transform;
                }
                Transform front = FindDeep(model.transform, "Front");
                // Which way the car faces: rear axle to front axle, else the Front marker.
                Vector3 dir = fronts > 0 && rears > 0 ? frontWheels / fronts - rearWheels / rears
                    : front != null && body != null ? front.position - body.position : Vector3.zero;
                dir.y = 0f;
                if (body != null && dir.sqrMagnitude > 1e-6f)
                {
                    // Face local +x.
                    model.transform.rotation = Quaternion.AngleAxis(Vector3.SignedAngle(dir, go.transform.right, Vector3.up), Vector3.up) * model.transform.rotation;
                    var info = new CarInfo();
                    string json = ModelsDir + "/Cars/" + type + ".json";
                    if (File.Exists(json)) JsonUtility.FromJsonOverwrite(File.ReadAllText(json), info);
                    foreach (var r in model.GetComponentsInChildren<MeshRenderer>())
                    {
                        r.sharedMaterial = material;
                        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                        r.receiveShadows = false;
                    }
                    if (paint.HasValue && info.paint != null && info.paint.Length >= 3)
                    {
                        var repaint = body.gameObject.AddComponent<CarPaint>();
                        repaint.basePaint = new Color(info.paint[0], info.paint[1], info.paint[2]);
                        repaint.paint = paint.Value;
                    }
                    var spin = go.AddComponent<WheelSpin>();
                    spin.wheels = wheels.ToArray();
                    spin.radius = info.wheelRadius;
                    return go.transform;
                }
                Debug.LogWarning("[Dribble To School] " + type + ".fbx has no body or wheels to face by; using the procedural car.");
                Object.DestroyImmediate(model);
            }

            if (prefab == null) Debug.LogWarning("[Dribble To School] Missing " + ModelsDir + "/Cars/" + type + ".fbx; using the procedural car.");
            var car = go.AddComponent<Car3D>();
            car.paint = paint ?? new Color(0.8f, 0.47f, 0.35f);
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            car.Rebuild();
            return go.transform;
        }

        /// <summary>A paint colour softened toward a warm grey, for the cozy, slightly faded street palette.</summary>
        static Color Faded(Color c)
        {
            return Color.Lerp(c, new Color(0.86f, 0.8f, 0.72f), 0.3f);
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
            // The sky dome: a big inverted sphere that follows the camera, drawn behind everything
            // (gradient, glowing horizon and the sun, from the WorldLook globals).
            var dome = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            dome.name = "SkyDome";
            Object.DestroyImmediate(dome.GetComponent<Collider>());
            dome.transform.SetParent(cam.transform, false);
            dome.transform.localPosition = Vector3.zero;
            dome.transform.localScale = Vector3.one * 4000f;      // radius 2000, inside the far clip plane
            var domeRenderer = dome.GetComponent<MeshRenderer>();
            domeRenderer.sharedMaterial = Art.skyDome;
            domeRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            domeRenderer.receiveShadows = false;

            // 3D cumulus far away over the street: flat bottoms, piled-up tops, cel-shaded.
            var clouds = new GameObject("Clouds").transform;
            var rng = new System.Random(ch * 101 + Mathf.RoundToInt(track.MaxX));
            for (float x = track.MinX - 450f; x < track.MaxX + 450f; x += 80f + (float)rng.NextDouble() * 110f)
            {
                float z = 480f + (float)rng.NextDouble() * 260f;
                var go = new GameObject("Cloud");
                go.transform.SetParent(clouds, false);
                go.transform.position = new Vector3(x, track.LowestGroundTop + 25f + (float)rng.NextDouble() * 70f, z);
                var cloud = go.AddComponent<CloudShape>();
                cloud.seed = rng.Next();
                cloud.width = 60f + (float)rng.NextDouble() * 90f;
                cloud.height = cloud.width * (0.35f + (float)rng.NextDouble() * 0.2f);
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.cloud;
                cloud.Rebuild();
            }
            clouds.gameObject.AddComponent<StaticBatcher>();
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
            /// <summary>Stretches (x from, x to) where the street's own scenery stays out of the way (the school grounds).</summary>
            public readonly List<Vector2> QuietAreas = new List<Vector2>();
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

            /// <summary>An open drain pit in the footpath. Losing the ball or the kid here respawns at the checkpoint.</summary>
            public void Pit(float fromX, float toX, float top = 0f)
            {
                Hole("Pit", fromX, toX, top, PitColor, "lose.gap", 0f);
            }

            /// <summary>A flooded trench (a tidal stream on the beach). Same rules as a pit, but splashy.</summary>
            public void Water(float fromX, float toX, float top = 0f)
            {
                Hole("Water", fromX, toX, top, WaterColor, "lose.splash", 0.35f);
            }

            void Hole(string name, float fromX, float toX, float top, Color color, string message, float surfaceDrop)
            {
                // A hole in the footpath only: the lane slabs either side show their ends as the
                // hole's walls and the strip behind shows its face at the back; the road in front
                // and the street behind carry on. In town it is drain works (a dug-up drain with a
                // pipe, or a rain-flooded trench) marked with cones and a barrier; on the beach it
                // is a washed-out channel or a tidal stream across the sand.
                bool beach = Chapter == 3;
                float cx = (fromX + toX) * 0.5f, w = toX - fromX, lane = StreetBuilder.PathHalf * 2f;
                if (surfaceDrop > 0f)
                {
                    // Muddy rainwater in town; a clear stream in the park.
                    Color tint = beach ? Color.white : Chapter == 5 ? new Color(0.78f, 0.95f, 0.98f) : new Color(0.66f, 0.68f, 0.56f);
                    var water = StreetBuilder.Solid(root, name + "Surface", new Vector3(cx, top - surfaceDrop - 0.1f, 0f), new Vector3(w, 0.2f, lane), tint, Art.surfaces[ProceduralArt.Surface.Sea]);
                    water.faces = MeshBuilder.Faces.Top;
                    water.Rebuild();
                }
                else
                {
                    StreetBuilder.Solid(root, name + "Floor", new Vector3(cx, top - 2.4f, 0f), new Vector3(w, 0.2f, lane), beach ? new Color(0.55f, 0.47f, 0.36f) : color);
                    if (!beach)
                    {
                        // The drain pipe the works are for, running across under the path.
                        var pipe = new GameObject("DrainPipe");
                        pipe.transform.SetParent(root, false);
                        pipe.transform.position = new Vector3(cx, top - 1.9f, 0f);
                        var shape = pipe.AddComponent<CylinderShape>();
                        shape.radius = Mathf.Min(0.35f, w * 0.3f);
                        shape.length = lane;
                        shape.sideColor = new Color(0.5f, 0.5f, 0.52f);
                        shape.endColor = new Color(0.55f, 0.55f, 0.57f);
                        pipe.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                        shape.Rebuild();
                    }
                }
                // Dark, shadowed inside walls, so it reads as a hole rather than a grey patch.
                Color inside = beach ? new Color(0.5f, 0.42f, 0.32f) : new Color(0.26f, 0.25f, 0.27f);
                float depth = surfaceDrop > 0f ? surfaceDrop + 0.05f : 2.4f;
                var back = StreetBuilder.Solid(root, name + "Wall", new Vector3(cx, top - depth * 0.5f, StreetBuilder.PathHalf - 0.01f), new Vector3(w, depth, 0.02f), inside);
                back.faces = MeshBuilder.Faces.Front;
                back.Rebuild();
                foreach (float ex in new[] { fromX + 0.01f, toX - 0.01f })
                {
                    var end = StreetBuilder.Solid(root, name + "End", new Vector3(ex, top - depth * 0.5f, 0f), new Vector3(0.02f, depth, StreetBuilder.PathHalf * 2f), Color.Lerp(inside, Color.white, 0.12f));
                    end.faces = ex < cx ? MeshBuilder.Faces.Right : MeshBuilder.Faces.Left;
                    end.Rebuild();
                }
                if (!beach)
                {
                    // A concrete lip round the dug edge.
                    StreetBuilder.Solid(root, name + "Lip", new Vector3(cx, top + 0.015f, StreetBuilder.PathHalf - 0.06f), new Vector3(w + 0.1f, 0.03f, 0.12f), new Color(0.6f, 0.6f, 0.6f));
                    RoadWorks(fromX, toX, top);
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

            /// <summary>Safety cones before and after a hole (either side of the kid's line) and a striped barrier behind it.</summary>
            void RoadWorks(float fromX, float toX, float top)
            {
                float zc = StreetBuilder.PathHalf - 0.35f;
                foreach (float x in new[] { fromX - 0.45f, toX + 0.45f })
                    foreach (float z in new[] { -zc, zc })
                    {
                        var cone = new GameObject("Cone");
                        cone.transform.SetParent(root, false);
                        cone.transform.position = new Vector3(x, top, z);
                        cone.AddComponent<ConeShape>();
                        cone.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                        cone.GetComponent<ConeShape>().Rebuild();
                    }
                // Barrier along the back edge of the hole: a yellow-and-black rail on two legs.
                float bz = StreetBuilder.PathHalf + 0.12f, a = fromX - 0.25f, b = toX + 0.25f;
                foreach (float x in new[] { a + 0.1f, b - 0.1f })
                    StreetBuilder.Solid(root, "BarrierLeg", new Vector3(x, top + 0.45f, bz), new Vector3(0.06f, 0.9f, 0.3f), new Color(0.3f, 0.3f, 0.32f));
                int n = Mathf.Max(2, Mathf.RoundToInt((b - a) / 0.3f));
                float step = (b - a) / n;
                for (int i = 0; i < n; i++)
                    StreetBuilder.Solid(root, "BarrierRail", new Vector3(a + (i + 0.5f) * step, top + 0.8f, bz), new Vector3(step, 0.14f, 0.05f),
                        i % 2 == 0 ? new Color(0.98f, 0.8f, 0.15f) : new Color(0.12f, 0.12f, 0.14f));
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
                Car(root, "Car", new Vector3(x, groundTop, 0.15f), 0f, Faded(color), "Hatch");
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
                // Adults are about 1.7 m (1.22 x the kid), feet on the capsule bottom (-0.925), a step behind the kid's line.
                Color hair = hairs[Mathf.Abs(Mathf.RoundToInt(minX)) % hairs.Length], trousers = Color.Lerp(coat, Color.black, 0.45f);
                var parts = BuildModelCharacter(go.transform, "Adult", Art.adult, 1.3f * 1.22f, new Vector3(0f, -0.193f, 0.75f), false);
                if (parts.rig != null)
                {
                    var dress = (ModelOutfit)parts.outfit;
                    dress.dressOnStart = true;
                    dress.shirt = coat;
                    dress.legwear = trousers;
                    dress.hair = hair;
                }
                else
                {
                    parts = BuildCharacter(go.transform, "Visual", new Vector2(0f, -0.193f), 1.22f, coat, trousers, hair, false);
                    parts.visual.localPosition = new Vector3(0f, -0.193f, 0.75f);
                }

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
                float poleX = fromX - 1.2f, poleZ = StreetBuilder.PathHalf + 0.15f, pave = groundTop;
                Color poleGrey = new Color(0.56f, 0.58f, 0.6f), housing = new Color(0.2f, 0.21f, 0.23f);
                Cylinder(root, "SignalBase", new Vector3(poleX, pave, poleZ), new Vector3(poleX, pave + 0.12f, poleZ), 0.13f, poleGrey);
                Cylinder(root, "SignalPole", new Vector3(poleX, pave, poleZ), new Vector3(poleX, pave + 2.95f, poleZ), 0.06f, poleGrey);
                // The push-button box at hand height, and the two-lamp head with hooded visors.
                StreetBuilder.Solid(root, "ButtonBox", new Vector3(poleX, pave + 1.1f, poleZ - 0.1f), new Vector3(0.2f, 0.3f, 0.12f), new Color(0.95f, 0.78f, 0.22f));
                StreetBuilder.Solid(root, "Button", new Vector3(poleX, pave + 1.06f, poleZ - 0.165f), new Vector3(0.08f, 0.08f, 0.02f), new Color(0.2f, 0.2f, 0.22f));
                StreetBuilder.Solid(root, "SignalBox", new Vector3(poleX, pave + 2.45f, poleZ - 0.1f), new Vector3(0.5f, 1f, 0.3f), housing);
                foreach (float vy in new[] { 2.68f, 2.22f })
                    StreetBuilder.Solid(root, "Visor", new Vector3(poleX, pave + vy + 0.2f, poleZ - 0.33f), new Vector3(0.44f, 0.04f, 0.16f), housing);
                StreetBuilder.Solid(root, "SignalCap", new Vector3(poleX, pave + 2.97f, poleZ - 0.1f), new Vector3(0.54f, 0.05f, 0.34f), Color.Lerp(housing, Color.white, 0.15f));
                crossing.redFigure = SpriteObject(go.transform, "RedMan", Art.standFigure, Vector3.zero, 1);
                crossing.redFigure.transform.position = new Vector3(poleX, pave + 2.68f, poleZ - 0.27f);
                crossing.greenFigure = SpriteObject(go.transform, "GreenMan", Art.walkFigure, Vector3.zero, 1);
                crossing.greenFigure.transform.position = new Vector3(poleX, pave + 2.22f, poleZ - 0.27f);

                // Side-street traffic driving toward the camera; the Crossing script moves it in depth.
                // A mix of everyday traffic: vans, estates, small trucks, an off-roader, in their own paint.
                string[] traffic = { "Van", "Fourby", "Pickup", "Wagon", "Hatch" };
                int first = Mathf.Abs(Mathf.RoundToInt(fromX)) % traffic.Length;
                crossing.cars = new Transform[2];
                for (int i = 0; i < crossing.cars.Length; i++)
                    crossing.cars[i] = Car(go.transform, "Car" + i, new Vector3(center, groundTop, 30f), 90f, null, traffic[(first + i * 2) % traffic.Length]);   // placed by Crossing
                crossing.groundY = groundTop;
                crossing.stopLineZ = StreetBuilder.PathHalf + 3.05f;   // front bumper at the stop line
            }

            /// <summary>A playful dog that patrols minX..maxX and noses low balls back.</summary>
            public void Dog(float minX, float maxX, Color fur, float groundTop = 0f)
            {
                var go = new GameObject("Dog");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((minX + maxX) * 0.5f, groundTop + 0.3f);
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                visual.localPosition = new Vector3(0f, 0f, 0.55f);   // trots beside the kid's line, not through it
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
                // Rain puddles (or loose sand) with natural, irregular edges across the footpath.
                var look = new GameObject(name + "Surface");
                look.transform.SetParent(root, false);
                var puddles = look.AddComponent<PuddleShape>();
                puddles.fromX = fromX;
                puddles.toX = toX;
                puddles.zFrom = -StreetBuilder.PathHalf + 0.15f;
                puddles.zTo = StreetBuilder.PathHalf - 0.15f;
                puddles.groundY = groundTop;
                puddles.seed = Mathf.RoundToInt(fromX * 13f) + 7;
                if (name == "Sand")
                {
                    puddles.reflective = false;
                    puddles.water = new Color(0.86f, 0.76f, 0.55f);
                    puddles.rim = new Color(0.9f, 0.82f, 0.62f);
                }
                look.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                puddles.Rebuild();

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
            /// <summary>
            /// Something that carries the kid and the ball across or up, always with a visible cause:
            /// a builder's hoist when it travels straight up, a rope ferry raft on park and beach
            /// water, otherwise a pallet hanging from a tower crane that slews to carry it.
            /// </summary>
            public void MovingPlatform(Vector2 center, float width, Vector2 travel, float speed = 1.5f)
            {
                var go = Block("MovingPlatform", center, new Vector2(width, 0.35f), PlatformColor, GroundMat, false);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var mp = go.AddComponent<Hazards.MovingPlatform>();
                mp.travel = travel;
                mp.speed = speed;
                if (Mathf.Abs(travel.x) < 0.01f) Hoist(go.transform, center, width, travel);
                else if (Chapter == 3 || Chapter == 5) Raft(go.transform, center, width, travel);
                else CraneLoad(go.transform, center, width, travel);
            }

            static readonly Color CraneYellow = new Color(0.96f, 0.74f, 0.22f);
            static readonly Color SteelGrey = new Color(0.56f, 0.58f, 0.62f);
            static readonly Color IronDark = new Color(0.22f, 0.22f, 0.25f);

            /// <summary>A steel plate on timber bearers, slung from a spreader beam behind the kid, on a tower crane's hook.</summary>
            void CraneLoad(Transform load, Vector2 center, float w, Vector2 travel)
            {
                Color timber = new Color(0.62f, 0.45f, 0.3f);
                Part(load, "Plate", new Vector3(0f, 0.115f, 0f), new Vector3(w, 0.12f, 1.5f), SteelGrey);
                foreach (float dz in new[] { -0.45f, 0.45f })
                    Part(load, "Bearer", new Vector3(0f, -0.04f, dz), new Vector3(w - 0.25f, 0.18f, 0.2f), timber);
                int n = Mathf.Max(2, Mathf.RoundToInt(w / 0.3f));
                for (int i = 0; i < n; i++)
                    Part(load, "Stripe", new Vector3(-w * 0.5f + (i + 0.5f) * w / n, 0.115f, -0.755f), new Vector3(w / n, 0.12f, 0.01f), i % 2 == 0 ? CraneYellow : IronDark);
                // Lifting gear at the back, behind the kid: chains up to a spreader beam, slings to the hook.
                const float zb = 0.72f, beamY = 2.95f, hookY = 3.7f;
                foreach (float sx in new[] { -1f, 1f })
                {
                    float x = sx * (w * 0.5f - 0.15f);
                    Part(load, "Chain", new Vector3(x, (0.18f + beamY) * 0.5f, zb), new Vector3(0.05f, beamY - 0.18f, 0.05f), IronDark);
                    Strut(load, "Sling", new Vector3(sx * (w * 0.5f - 0.25f), beamY + 0.07f, zb), new Vector3(0f, hookY - 0.14f, zb), 0.04f, IronDark);
                }
                Part(load, "Spreader", new Vector3(0f, beamY, zb), new Vector3(w - 0.2f, 0.14f, 0.14f), CraneYellow);
                Part(load, "Hook", new Vector3(0f, hookY, zb), new Vector3(0.24f, 0.32f, 0.24f), CraneYellow);
                Part(load, "HookBand", new Vector3(0f, hookY + 0.05f, zb - 0.125f), new Vector3(0.24f, 0.08f, 0.01f), IronDark);

                // The tower crane, on its own plot behind the street, slewing to follow the load.
                float ground = GroundTopUnder(center.x, center.y + 0.5f);
                float mx = center.x + travel.x * 0.5f, mz = 5.2f, jibY = ground + 9.6f;
                QuietAreas.Add(new Vector2(mx - 3f, mx + 3f));
                var crane = new GameObject("TowerCrane").transform;
                crane.SetParent(root, false);
                crane.position = new Vector3(mx, ground, mz);
                Part(crane, "Base", new Vector3(0f, 0.3f, 0f), new Vector3(2.2f, 0.6f, 2.2f), new Color(0.78f, 0.77f, 0.74f), Art.surfaces[ProceduralArt.Surface.Concrete]);
                float mastTop = jibY - ground - 0.45f, half = 0.55f;
                foreach (float sx in new[] { -half, half })
                    foreach (float sz in new[] { -half, half })
                        Part(crane, "MastPost", new Vector3(sx, 0.6f + (mastTop - 0.6f) * 0.5f, sz), new Vector3(0.12f, mastTop - 0.6f, 0.12f), CraneYellow);
                for (float y = 0.6f; y < mastTop - 0.1f; y += 1.4f)
                {
                    float y1 = Mathf.Min(y + 1.4f, mastTop);
                    foreach (float sz in new[] { -half, half })
                        Part(crane, "MastBrace", new Vector3(0f, y, sz), new Vector3(half * 2f, 0.07f, 0.07f), CraneYellow);
                    foreach (float sx in new[] { -half, half })
                        Part(crane, "MastBrace", new Vector3(sx, y, 0f), new Vector3(0.07f, 0.07f, half * 2f), CraneYellow);
                    Strut(crane, "MastDiagonal", new Vector3(-half, y, -half), new Vector3(half, y1, -half), 0.06f, CraneYellow);
                    Strut(crane, "MastDiagonal", new Vector3(half, y, -half), new Vector3(half, y1, half), 0.06f, CraneYellow);
                }
                Part(crane, "Slewing", new Vector3(0f, mastTop + 0.15f, 0f), new Vector3(1.4f, 0.3f, 1.4f), Color.Lerp(CraneYellow, Color.black, 0.3f));

                var jib = new GameObject("Jib").transform;
                jib.SetParent(crane, false);
                jib.localPosition = new Vector3(0f, jibY - ground, 0f);
                Part(jib, "Cab", new Vector3(0.45f, -0.6f, -0.85f), new Vector3(1f, 0.9f, 0.8f), new Color(0.95f, 0.94f, 0.9f));
                Part(jib, "CabWindow", new Vector3(0.96f, -0.55f, -0.85f), new Vector3(0.02f, 0.5f, 0.62f), new Color(0.35f, 0.48f, 0.6f));
                const float jibLength = 10.5f;
                foreach (float z in new[] { -0.3f, 0.3f })
                    Part(jib, "Chord", new Vector3(jibLength * 0.5f + 0.4f, -0.1f, z), new Vector3(jibLength, 0.08f, 0.08f), CraneYellow);
                Part(jib, "TopChord", new Vector3(jibLength * 0.5f + 0.4f, 0.55f, 0f), new Vector3(jibLength, 0.08f, 0.08f), CraneYellow);
                for (float x = 0.4f; x < jibLength; x += 1.3f)
                    foreach (float z in new[] { -0.3f, 0.3f })
                    {
                        Strut(jib, "Lacing", new Vector3(x, -0.1f, z), new Vector3(x + 0.65f, 0.55f, 0f), 0.045f, CraneYellow);
                        Strut(jib, "Lacing", new Vector3(x + 0.65f, 0.55f, 0f), new Vector3(x + 1.3f, -0.1f, z), 0.045f, CraneYellow);
                    }
                // Counter-jib with its concrete counterweights, and the A-frame with its tie bars.
                foreach (float z in new[] { -0.3f, 0.3f })
                    Part(jib, "CounterChord", new Vector3(-1.9f, -0.1f, z), new Vector3(3.6f, 0.1f, 0.1f), CraneYellow);
                Part(jib, "Counterweight", new Vector3(-3.2f, -0.55f, 0f), new Vector3(0.9f, 1.1f, 1f), new Color(0.72f, 0.71f, 0.68f), Art.surfaces[ProceduralArt.Surface.Concrete]);
                foreach (float z in new[] { -0.3f, 0.3f })
                    Strut(jib, "TowerTop", new Vector3(0f, 0f, z), new Vector3(0f, 2.3f, 0f), 0.08f, CraneYellow);
                Strut(jib, "Tie", new Vector3(0f, 2.3f, 0f), new Vector3(jibLength * 0.6f, 0.55f, 0f), 0.03f, IronDark);
                Strut(jib, "Tie", new Vector3(0f, 2.3f, 0f), new Vector3(-3.5f, 0f, 0f), 0.03f, IronDark);
                var trolley = new GameObject("Trolley").transform;
                trolley.SetParent(jib, false);
                Part(trolley, "TrolleyBody", Vector3.zero, new Vector3(0.7f, 0.22f, 0.7f), Color.Lerp(CraneYellow, Color.black, 0.3f));

                var cableGo = new GameObject("Cable");
                cableGo.transform.SetParent(crane, false);
                var cable = cableGo.AddComponent<LineRenderer>();
                cable.sharedMaterial = trailMaterial;
                cable.positionCount = 2;
                cable.widthMultiplier = 0.04f;
                cable.startColor = cable.endColor = new Color(0.18f, 0.18f, 0.2f);
                cable.useWorldSpace = true;
                cable.sortingOrder = -1;
                var rig = crane.gameObject.AddComponent<CraneRig>();
                rig.jib = jib;
                rig.trolley = trolley;
                rig.load = load;
                rig.hookLocal = new Vector3(0f, hookY + 0.16f, zb);
                rig.cable = cable;
                rig.trolleyDrop = 0.25f;
            }

            /// <summary>A builder's hoist: a caged deck that climbs a rack-and-pinion mast standing behind it.</summary>
            void Hoist(Transform deck, Vector2 center, float w, Vector2 travel)
            {
                Part(deck, "Deck", new Vector3(0f, 0.115f, 0f), new Vector3(w, 0.12f, 1.5f), SteelGrey);
                Part(deck, "ToeBoard", new Vector3(0f, 0.24f, -0.74f), new Vector3(w, 0.12f, 0.02f), CraneYellow);
                foreach (float sx in new[] { -1f, 1f })
                    Part(deck, "CagePost", new Vector3(sx * (w * 0.5f - 0.03f), 0.7f, 0.74f), new Vector3(0.06f, 1.1f, 0.06f), CraneYellow);
                Part(deck, "CageRail", new Vector3(0f, 1.22f, 0.74f), new Vector3(w, 0.06f, 0.06f), CraneYellow);
                Part(deck, "CageRail", new Vector3(0f, 0.7f, 0.74f), new Vector3(w, 0.05f, 0.05f), CraneYellow);
                Part(deck, "CageMesh", new Vector3(0f, 0.7f, 0.77f), new Vector3(w - 0.08f, 1f, 0.01f), new Color(0.4f, 0.42f, 0.45f));
                Part(deck, "DriveUnit", new Vector3(0f, 0.55f, 1.05f), new Vector3(0.7f, 0.7f, 0.45f), Color.Lerp(CraneYellow, Color.black, 0.3f));

                float ground = GroundTopUnder(center.x, center.y + 0.5f);
                float top = center.y + travel.y + 2.6f, height = top - ground, mz = 1.45f;
                var mast = new GameObject("HoistMast").transform;
                mast.SetParent(root, false);
                mast.position = new Vector3(center.x, ground, mz);
                foreach (float sx in new[] { -0.25f, 0.25f })
                    Part(mast, "MastPost", new Vector3(sx, height * 0.5f, 0f), new Vector3(0.08f, height, 0.08f), CraneYellow);
                Part(mast, "Rack", new Vector3(0f, height * 0.5f, -0.1f), new Vector3(0.1f, height, 0.04f), IronDark);
                for (float y = 0.4f; y < height; y += 0.8f)
                    Strut(mast, "MastBrace", new Vector3(-0.25f, y, 0.02f), new Vector3(0.25f, Mathf.Min(y + 0.8f, height), 0.02f), 0.05f, CraneYellow);
                Part(mast, "MastCap", new Vector3(0f, height + 0.05f, 0f), new Vector3(0.7f, 0.1f, 0.4f), Color.Lerp(CraneYellow, Color.black, 0.3f));
            }

            /// <summary>A plank raft on floats, pulled along a ferry rope strung between posts on the banks.</summary>
            void Raft(Transform raft, Vector2 center, float w, Vector2 travel)
            {
                Color plank = new Color(0.66f, 0.5f, 0.34f), plankDark = new Color(0.52f, 0.38f, 0.26f), rope = new Color(0.84f, 0.76f, 0.58f);
                int n = Mathf.Max(3, Mathf.RoundToInt(w / 0.3f));
                for (int i = 0; i < n; i++)
                    Part(raft, "Plank", new Vector3(-w * 0.5f + (i + 0.5f) * w / n, 0.105f, 0f), new Vector3(w / n - 0.03f, 0.14f, 1.5f), i % 2 == 0 ? plank : Color.Lerp(plank, plankDark, 0.5f));
                foreach (float dz in new[] { -0.5f, 0.5f })
                    Part(raft, "Float", new Vector3(0f, -0.07f, dz), new Vector3(w - 0.2f, 0.2f, 0.32f), new Color(0.32f, 0.44f, 0.52f));
                Part(raft, "RopePost", new Vector3(0f, 0.6f, 0.72f), new Vector3(0.1f, 0.95f, 0.1f), plankDark);
                Part(raft, "RopeRing", new Vector3(0f, 1.02f, 0.86f), new Vector3(0.16f, 0.16f, 0.04f), IronDark);

                float ropeY = center.y + 0.175f + 0.85f;
                float a = center.x - w * 0.5f - 0.7f, b = center.x + travel.x + w * 0.5f + 0.7f;
                Part(root, "FerryRope", new Vector3((a + b) * 0.5f, ropeY, 0.9f), new Vector3(b - a, 0.035f, 0.035f), rope);
                foreach (float px in new[] { a, b })
                {
                    float g = GroundTopUnder(px, ropeY);
                    if (g < -50f) g = center.y;
                    Part(root, "BankPost", new Vector3(px, (g + ropeY + 0.2f) * 0.5f, 0.9f), new Vector3(0.14f, ropeY + 0.2f - g, 0.14f), plankDark);
                }
            }

            /// <summary>A cylinder from local point a to local point b inside <paramref name="parent"/>
            /// (trunks, boughs, round pads). With innerRadius it shows a hollow end disc.</summary>
            static void Cylinder(Transform parent, string name, Vector3 a, Vector3 b, float radius, Color color, float innerRadius = 0f)
            {
                var go = new GameObject(name);
                go.transform.SetParent(parent, false);
                go.transform.localPosition = (a + b) * 0.5f;
                var shape = go.AddComponent<CylinderShape>();
                shape.axis = (b - a).normalized;
                shape.length = (b - a).magnitude;
                shape.radius = radius;
                shape.sideColor = color;
                shape.endColor = Color.Lerp(color, Color.white, 0.12f);
                shape.innerRadius = innerRadius;
                shape.innerColor = Color.Lerp(color, Color.black, 0.4f);
                shape.segments = 24;
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                shape.Rebuild();
            }

            /// <summary>A thin box from local point a to local point b inside <paramref name="parent"/> (lattice members, slings, ties).</summary>
            static void Strut(Transform parent, string name, Vector3 a, Vector3 b, float thickness, Color color)
            {
                var go = new GameObject(name);
                go.transform.SetParent(parent, false);
                go.transform.localPosition = (a + b) * 0.5f;
                go.transform.localRotation = Quaternion.FromToRotation(Vector3.up, b - a);
                var box = go.AddComponent<Box3D>();
                box.size = new Vector3(thickness, (b - a).magnitude, thickness);
                box.color = color;
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                box.Rebuild();
            }

            /// <summary>
            /// A sliding steel gate across the footpath between two pillars, opened by kicking the
            /// ball at its call button: an intercom panel on a gooseneck post, or (when the button
            /// is low) a push-button bollard. The gate rolls back into the property when buzzed open.
            /// </summary>
            public void SwitchAndGate(Vector2 switchPosition, float gateX, float gateHeight = 2.4f, float groundTop = 0f)
            {
                var gateGo = Block("Gate", new Vector2(gateX, groundTop + gateHeight * 0.5f), new Vector2(0.35f, gateHeight), Color.white, GroundMat, false);
                gateGo.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var gate = gateGo.AddComponent<Gate>();
                gateGo.AddComponent<BallTrap>();      // a ball resting on top of the gate is out of reach

                // A masonry pillar at the back of the footpath that the gate closes against (a sliding
                // gate needs no post at its street end, which keeps its no-entry sign in view).
                Color stone = new Color(0.86f, 0.84f, 0.8f), cap = new Color(0.62f, 0.6f, 0.58f);
                float pillarH = gateHeight + 0.35f, half = StreetBuilder.PathHalf;
                foreach (float z in new[] { half + 0.3f })
                {
                    StreetBuilder.Solid(root, "GatePillar", new Vector3(gateX, groundTop + pillarH * 0.5f, z), new Vector3(0.5f, pillarH, 0.45f), stone, Art.surfaces[ProceduralArt.Surface.Concrete]);
                    StreetBuilder.Solid(root, "GatePillarCap", new Vector3(gateX, groundTop + pillarH + 0.05f, z), new Vector3(0.6f, 0.1f, 0.55f), cap);
                }
                StreetBuilder.Patch(root, "GateTrack", gateX - 0.05f, gateX + 0.05f, groundTop, -half, half + 3.5f, new Color(0.4f, 0.4f, 0.42f));

                // The gate: a deep steel frame with two rows of bars (it is seen end-on from the street),
                // a no-entry sign on its street end, and wheels on the track. It slides back, away
                // from the camera, into the property.
                var panel = new GameObject("GatePanel").transform;
                panel.SetParent(gateGo.transform, false);
                Color steel = new Color(0.82f, 0.84f, 0.86f), dark = new Color(0.4f, 0.42f, 0.45f);
                float z0 = -half + 0.05f, z1 = half + 0.1f, zc = (z0 + z1) * 0.5f, len = z1 - z0;
                float y0 = -gateHeight * 0.5f + 0.08f, y1 = gateHeight * 0.5f;
                Part(panel, "Rail", new Vector3(0f, y1 - 0.06f, zc), new Vector3(0.3f, 0.12f, len), steel);
                Part(panel, "Rail", new Vector3(0f, y0 + 0.06f, zc), new Vector3(0.3f, 0.12f, len), steel);
                Part(panel, "Rail", new Vector3(0f, (y0 + y1) * 0.5f, zc), new Vector3(0.26f, 0.08f, len), steel);
                foreach (float bx in new[] { -0.1f, 0.1f })
                    for (float z = z0; z <= z1 + 0.001f; z += len / Mathf.Round(len / 0.2f))
                        Part(panel, "Bar", new Vector3(bx, (y0 + y1) * 0.5f, z), new Vector3(0.04f, y1 - y0, 0.04f), dark);
                foreach (float z in new[] { z0, z1 })
                {
                    Part(panel, "Stile", new Vector3(0f, (y0 + y1) * 0.5f, z), new Vector3(0.3f, y1 - y0, 0.08f), steel);
                    Part(panel, "Wheel", new Vector3(0f, y0 - 0.04f, z), new Vector3(0.1f, 0.08f, 0.14f), new Color(0.15f, 0.15f, 0.16f));
                }
                var noEntry = new GameObject("NoEntry");
                noEntry.transform.SetParent(panel, false);
                noEntry.transform.localPosition = new Vector3(0f, 0.25f, z0 - 0.07f);
                var disc = noEntry.AddComponent<CylinderShape>();
                disc.radius = 0.3f;
                disc.length = 0.04f;
                disc.sideColor = disc.endColor = new Color(0.85f, 0.15f, 0.15f);
                disc.innerRadius = 0.25f;
                disc.innerColor = new Color(0.9f, 0.18f, 0.18f);
                noEntry.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                disc.Rebuild();
                Part(noEntry.transform, "Bar", new Vector3(0f, 0f, -0.025f), new Vector3(0.36f, 0.09f, 0.01f), Color.white);
                gate.slidingPanel = panel;
                gate.slide = new Vector3(0f, 0f, len + 0.4f);

                // The call button the ball has to hit.
                bool low = switchPosition.y - groundTop < 0.9f;
                GameObject sw;
                Transform buttonParent;
                if (low)
                {
                    // A steel push-button bollard: solid from the ground to the top of the button.
                    float top = switchPosition.y + 0.275f;
                    sw = Block("Switch", new Vector2(switchPosition.x, (groundTop + top) * 0.5f), new Vector2(0.55f, top - groundTop), Color.white, GroundMat, false);
                    Part(sw.transform, "Bollard", Vector3.zero, new Vector3(0.36f, top - groundTop, 0.36f), new Color(0.68f, 0.7f, 0.72f));
                    Part(sw.transform, "BollardCap", new Vector3(0f, (top - groundTop) * 0.5f, 0f), new Vector3(0.4f, 0.05f, 0.4f), new Color(0.45f, 0.47f, 0.5f));
                    buttonParent = sw.transform;
                }
                else
                {
                    // An intercom panel hanging over the path from a gooseneck post behind it.
                    sw = Block("Switch", switchPosition, new Vector2(0.55f, 0.55f), Color.white, GroundMat, false);
                    Color post = new Color(0.55f, 0.57f, 0.6f);
                    float postZ = 1.15f, postTop = switchPosition.y + 0.45f;
                    StreetBuilder.Solid(root, "IntercomPost", new Vector3(switchPosition.x, (groundTop + postTop) * 0.5f, postZ), new Vector3(0.1f, postTop - groundTop, 0.1f), post);
                    StreetBuilder.Solid(root, "IntercomArm", new Vector3(switchPosition.x, postTop, postZ * 0.5f), new Vector3(0.08f, 0.08f, postZ + 0.1f), post);
                    StreetBuilder.Solid(root, "IntercomHanger", new Vector3(switchPosition.x, postTop - 0.1f, 0f), new Vector3(0.05f, 0.2f, 0.05f), post);
                    Part(sw.transform, "Panel", Vector3.zero, new Vector3(0.5f, 0.55f, 0.24f), new Color(0.78f, 0.8f, 0.82f));
                    for (int i = 0; i < 3; i++)   // speaker grille
                        Part(sw.transform, "Grille", new Vector3(0f, 0.17f - i * 0.05f, -0.125f), new Vector3(0.26f, 0.02f, 0.01f), new Color(0.3f, 0.3f, 0.33f));
                    Part(sw.transform, "Camera", new Vector3(0f, 0.23f, -0.125f), new Vector3(0.06f, 0.04f, 0.01f), new Color(0.1f, 0.1f, 0.12f));
                    buttonParent = sw.transform;
                }
                // The big round call button facing the street, lit by BallSwitch.
                var lamp = new GameObject("Indicator");
                lamp.transform.SetParent(buttonParent, false);
                lamp.transform.localPosition = new Vector3(0f, low ? (switchPosition.y - (groundTop + switchPosition.y + 0.275f) * 0.5f) : -0.08f, low ? -0.19f : -0.13f);
                var button = lamp.AddComponent<CylinderShape>();
                button.radius = 0.11f;
                button.length = 0.04f;
                button.sideColor = button.endColor = button.innerColor = Color.white;
                lamp.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                button.Rebuild();
                var ballSwitch = sw.AddComponent<BallSwitch>();
                ballSwitch.gates = new[] { gate };
                ballSwitch.indicator = lamp.GetComponent<MeshRenderer>();
                ballSwitch.offColor = new Color(1f, 0.6f, 0.2f);
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

                // Darker wet sand where the waves reach, with a wavy edge; the wave itself runs up
                // from the sea behind and over the path at high water (TideWash), not across it.
                var wet = new GameObject("WetSand");
                wet.transform.SetParent(root, false);
                var wetStrip = wet.AddComponent<WavyStrip>();
                wetStrip.fromX = fromX;
                wetStrip.toX = toX;
                wetStrip.frontZ = -3.3f;
                wetStrip.backZ = 5.6f;
                wetStrip.seaZ = 9.3f;
                wetStrip.phase = 1.3f;
                wetStrip.y = groundTop + 0.006f;
                wetStrip.color = new Color(0.87f, 0.78f, 0.63f);
                wet.GetComponent<MeshRenderer>().sharedMaterial = Art.surfaces[ProceduralArt.Surface.Sand];
                wetStrip.Rebuild();

                var washGo = new GameObject("Wash");
                washGo.transform.SetParent(root, false);
                washGo.AddComponent<MeshFilter>();
                washGo.AddComponent<MeshRenderer>().sharedMaterials = new[] { Art.surfaces[ProceduralArt.Surface.Sea], Art.solid };
                var wash = washGo.AddComponent<TideWash>();
                wash.fromX = fromX;
                wash.toX = toX;
                wash.groundY = groundTop;

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
                tide.wash = wash;
            }

            /// <summary>A dark tunnel with a ceiling: darkens the screen around the kid while inside.</summary>
            public void Tunnel(float fromX, float toX, float groundTop = 0f, float height = 3.3f)
            {
                float center = (fromX + toX) * 0.5f;
                float width = toX - fromX;
                // An underpass: a back wall and a deep concrete deck over the street.
                StreetBuilder.Solid(root, "TunnelBack", new Vector3(center, groundTop + height * 0.5f, StreetBuilder.PropertyZ + 0.2f), new Vector3(width, height, 0.4f), new Color(0.36f, 0.34f, 0.38f));
                Block("TunnelCeiling", new Vector2(center, groundTop + height + 0.6f), new Vector2(width + 1f, 1.2f), new Color(0.62f, 0.62f, 0.64f), GroundMat, true, 7.4f)
                    .AddComponent<BallTrap>();        // the deck over the underpass is out of reach
                // Dim lamps under the deck, lighting the footpath below them.
                for (float lx = fromX + 2.5f; lx < toX - 1f; lx += 5f)
                {
                    StreetBuilder.Solid(root, "LampFitting", new Vector3(lx, groundTop + height - 0.04f, 0.2f), new Vector3(0.9f, 0.08f, 0.3f), new Color(0.75f, 0.75f, 0.72f));
                    var lamp = new GameObject("TunnelLamp");
                    lamp.transform.SetParent(root, false);
                    lamp.transform.position = new Vector3(lx, groundTop + height - 0.1f, 0.15f);
                    var glow = lamp.AddComponent<LampGlow>();
                    glow.material = Art.glow;
                    glow.height = height - 0.1f;
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
                    pipe.transform.position = new Vector3(stack.x + o.x, stack.y + o.y, 1.3f);
                    PipeSpawner.BuildPipe(pipe, r, spawner.color, Art.solid);
                    pipe.transform.Find("Visual").localScale = new Vector3(1f, 1f, 0.75f);
                }
            }

            /// <summary>A swing seat hanging from <paramref name="pivot"/>.</summary>
            public void Swing(Vector2 pivot, float ropeLength, float amplitude = 35f, float period = 3f, float phaseOffset = 0f)
            {
                Color wood = new Color(0.55f, 0.4f, 0.3f);
                float ground = GroundTopUnder(pivot.x, pivot.y);
                if (Chapter == 5)
                {
                    // A rope swing on a big old tree on the bank: the trunk stands behind the path
                    // and a thick bough reaches out over it to where the rope is tied.
                    Color bark = new Color(0.45f, 0.34f, 0.26f);
                    float trunkTop = pivot.y + 1.4f;
                    Cylinder(root, "Trunk", new Vector3(pivot.x - 0.5f, ground - 0.1f, 2.6f), new Vector3(pivot.x - 0.4f, trunkTop, 2.5f), 0.34f, bark);
                    Cylinder(root, "Bough", new Vector3(pivot.x - 0.4f, pivot.y + 0.9f, 2.4f), new Vector3(pivot.x + 0.05f, pivot.y + 0.1f, -0.2f), 0.14f, bark);
                    Cylinder(root, "Bough", new Vector3(pivot.x - 0.4f, trunkTop - 0.2f, 2.4f), new Vector3(pivot.x + 1.4f, trunkTop + 0.9f, 1.4f), 0.11f, bark);
                    Color leaf = new Color(0.36f, 0.58f, 0.32f), leafLight = new Color(0.46f, 0.68f, 0.38f);
                    Blobs(root, "Canopy", new Vector3(pivot.x, trunkTop + 1.1f, 1.8f),
                        new BlobShape.Blob(new Vector3(0f, 0f, 0f), new Vector3(2f, 1.2f, 1.7f), leaf),
                        new BlobShape.Blob(new Vector3(-1.3f, -0.3f, 0.3f), new Vector3(1.3f, 0.9f, 1.2f), leaf),
                        new BlobShape.Blob(new Vector3(1.4f, -0.2f, -0.1f), new Vector3(1.3f, 0.95f, 1.2f), leafLight),
                        new BlobShape.Blob(new Vector3(0.3f, 0.7f, -0.2f), new Vector3(1.2f, 0.8f, 1.1f), leafLight));
                }
                else
                {
                    // A swing frame standing across the street: the beam runs in depth over the seat,
                    // on splayed A-frame legs at either end, clear of the kid's path.
                    float frameZ = 1.1f;
                    Decor("SwingBeam", pivot + new Vector2(0f, 0.1f), new Vector2(0.2f, 0.2f), wood, frameZ * 2f + 0.3f);
                    foreach (float z in new[] { -frameZ, frameZ })
                        foreach (float splay in new[] { -1f, 1f })
                        {
                            float height = pivot.y + 0.1f - ground;
                            var leg = Decor("SwingLeg", new Vector2(pivot.x + splay * height * 0.18f, ground + height * 0.5f), new Vector2(0.15f, height / Mathf.Cos(Mathf.Atan(0.36f))), wood, 0.15f, z);
                            leg.transform.rotation = Quaternion.Euler(0f, 0f, splay * Mathf.Atan(0.36f) * Mathf.Rad2Deg);
                        }
                }

                var seat = Block("SwingSeat", pivot + Vector2.down * ropeLength, new Vector2(1.4f, 0.2f), Chapter == 5 ? new Color(0.62f, 0.46f, 0.32f) : new Color(0.85f, 0.35f, 0.3f), GroundMat, true, 0.7f);
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
                StreetBuilder.Patch(root, "WetPaving", x - 1.8f, x + 1.8f, groundTop, -StreetBuilder.PathHalf, StreetBuilder.PathHalf, new Color(0.55f, 0.6f, 0.62f));
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
                {
                    // On a post behind the kid's line, with a bracket out to the board.
                    Decor("TargetPost", new Vector2(position.x, (groundTop + position.y) * 0.5f), new Vector2(0.1f, position.y - groundTop), ObstacleColor, -1f, 0.75f);
                    Decor("TargetArm", new Vector2(position.x, position.y), new Vector2(0.08f, 0.08f), ObstacleColor, 0.75f, 0.4f);
                }
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
                // A small round garden trampoline: a black jumping mat inside a padded rim, on short legs.
                Cylinder(visual, "Legs", new Vector3(0f, 0.02f, 0f), new Vector3(0f, 0.2f, 0f), 0.66f, new Color(0.35f, 0.36f, 0.4f), 0.6f);
                Cylinder(visual, "Pad", new Vector3(0f, 0.2f, 0f), new Vector3(0f, 0.3f, 0f), 0.72f, new Color(0.3f, 0.55f, 0.85f));
                Cylinder(visual, "Mat", new Vector3(0f, 0.3f, 0f), new Vector3(0f, 0.31f, 0f), 0.56f, new Color(0.14f, 0.14f, 0.16f));
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

            /// <summary>A short obstacle: jump it, chip the ball over. Drawn as something that really stands on a footpath.</summary>
            public void Wall(float x, float height, float groundTop = 0f, float width = 0.4f)
            {
                Obstacle("Wall", new Vector2(x, groundTop + height * 0.5f), new Vector2(width, height));
            }

            /// <summary>
            /// A solid obstacle in the kid's way, drawn as something that belongs there: a stone step
            /// or border when low, a concrete planter of flowers when knee to waist high, a stack of
            /// drinks crates when taller. Rocks on the beach, hedges in the park. The collider is
            /// exactly <paramref name="size"/>; the look fills it.
            /// </summary>
            GameObject Obstacle(string name, Vector2 center, Vector2 size)
            {
                var go = Block(name, center, size, ObstacleColor, GroundMat, false);
                float h = size.y, w = size.x, bottom = center.y - h * 0.5f;
                int seed = Mathf.Abs(Mathf.RoundToInt(center.x * 17f));
                if (Chapter == 3)
                {
                    // A weathered rock: a few overlapping boulders filling the box.
                    Color rock = new Color(0.6f, 0.56f, 0.5f), dark = new Color(0.48f, 0.45f, 0.42f);
                    Blobs(go.transform, "Rock", Vector3.zero,
                        new BlobShape.Blob(new Vector3(0f, -h * 0.08f, 0f), new Vector3(w * 0.55f, h * 0.48f, 0.45f), rock),
                        new BlobShape.Blob(new Vector3(-w * 0.2f, h * 0.12f, 0.12f), new Vector3(w * 0.38f, h * 0.38f, 0.32f), dark),
                        new BlobShape.Blob(new Vector3(w * 0.25f, -h * 0.25f, -0.2f), new Vector3(w * 0.35f, h * 0.28f, 0.3f), rock));
                }
                else if (h <= 0.45f)
                {
                    // A granite step / garden border across the path.
                    Part(go.transform, "Stone", Vector3.zero, new Vector3(w, h, 1.6f), new Color(0.74f, 0.73f, 0.7f), Art.surfaces[ProceduralArt.Surface.Concrete]);
                }
                else if (Chapter == 5)
                {
                    // A clipped hedge with a few leafy bumps on top.
                    Part(go.transform, "Hedge", Vector3.zero, new Vector3(w, h, 1.2f), new Color(0.3f, 0.52f, 0.3f));
                    var leaves = new List<BlobShape.Blob>();
                    for (float dx = -w * 0.35f; dx <= w * 0.36f; dx += Mathf.Max(0.2f, w * 0.35f))
                        leaves.Add(new BlobShape.Blob(new Vector3(dx, h * 0.5f, 0f), new Vector3(0.18f, 0.07f, 0.5f), new Color(0.36f, 0.6f, 0.34f)));
                    Blobs(go.transform, "Leaves", Vector3.zero, leaves.ToArray());
                }
                else if (h <= 1.05f)
                {
                    // A concrete planter with low flowers that sit just below its rim.
                    Part(go.transform, "Planter", Vector3.zero, new Vector3(w, h, 1.1f), new Color(0.8f, 0.78f, 0.74f), Art.surfaces[ProceduralArt.Surface.Concrete]);
                    Part(go.transform, "Soil", new Vector3(0f, h * 0.5f + 0.004f, 0f), new Vector3(w - 0.12f, 0.01f, 0.98f), new Color(0.36f, 0.27f, 0.2f));
                    Color[] petals = { new Color(1f, 0.55f, 0.65f), new Color(1f, 0.85f, 0.3f), new Color(0.95f, 0.95f, 0.95f) };
                    int k = seed;
                    var flowers = new List<BlobShape.Blob>();
                    for (float dx = -w * 0.5f + 0.15f; dx <= w * 0.5f - 0.14f; dx += 0.22f)
                        foreach (float dz in new[] { -0.3f, 0.05f, 0.35f })
                        {
                            flowers.Add(new BlobShape.Blob(new Vector3(dx, h * 0.5f + 0.03f, dz), new Vector3(0.07f, 0.03f, 0.07f), new Color(0.35f, 0.6f, 0.3f)));
                            flowers.Add(new BlobShape.Blob(new Vector3(dx, h * 0.5f + 0.06f, dz), new Vector3(0.035f, 0.02f, 0.035f), petals[k++ % petals.Length]));
                        }
                    Blobs(go.transform, "Flowers", Vector3.zero, flowers.ToArray());
                }
                else
                {
                    // Plastic drinks crates stacked outside a shop, two columns deep.
                    Color[] crates = { new Color(0.2f, 0.45f, 0.8f), new Color(0.95f, 0.75f, 0.15f), new Color(0.25f, 0.6f, 0.35f) };
                    const float crate = 0.32f;
                    int n = Mathf.Max(1, Mathf.FloorToInt(h / crate));
                    float filled = n * crate;
                    foreach (float dz in new[] { -0.22f, 0.22f })
                    {
                        for (int i = 0; i < n; i++)
                        {
                            Color c = crates[(seed + i + (dz > 0f ? 1 : 0)) % crates.Length];
                            float cy = -h * 0.5f + (i + 0.5f) * crate;
                            Part(go.transform, "Crate", new Vector3(0f, cy, dz), new Vector3(w, crate - 0.02f, 0.42f), c);
                            // A dark hand-hold slot on the side facing the camera.
                            Part(go.transform, "Slot", new Vector3(0f, cy + 0.05f, dz - 0.215f), new Vector3(w * 0.5f, 0.06f, 0.01f), Color.Lerp(c, Color.black, 0.55f));
                        }
                        if (h - filled > 0.06f)
                            Part(go.transform, "Box", new Vector3(0f, -h * 0.5f + filled + (h - filled) * 0.5f, dz), new Vector3(w, h - filled, 0.4f), new Color(0.78f, 0.62f, 0.42f));
                    }
                }
                go.AddComponent<StaticBatcher>();   // one draw call per material for all the parts
                return go;
            }

            /// <summary>A coloured 3D box at a local position inside <paramref name="parent"/> (no collider).</summary>
            static void Part(Transform parent, string name, Vector3 localCenter, Vector3 size, Color color, Material material = null)
            {
                var go = new GameObject(name);
                go.transform.SetParent(parent, false);
                go.transform.localPosition = localCenter;
                var box = go.AddComponent<Box3D>();
                box.size = size;
                box.color = color;
                go.GetComponent<MeshRenderer>().sharedMaterial = material != null ? material : Art.solid;
                box.Rebuild();
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
                Obstacle("Step", new Vector2(x, groundTop + 0.4f), new Vector2(2f, 0.8f));
                Obstacle("HighWall", new Vector2(x + 1.25f, groundTop + 0.9f), new Vector2(0.5f, 1.8f));
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
                    float flagZ = StreetBuilder.PathHalf - 0.15f;
                    Decor("FlagPole", new Vector2(x, groundTop + 1.14f), new Vector2(0.08f, 2f), ObstacleColor, -1f, flagZ);
                    var flag = Decor("Flag", new Vector2(x + 0.31f, groundTop + 1.94f), new Vector2(0.55f, 0.35f), Color.white, 0.03f, flagZ);
                    cp.flag = flag.GetComponent<MeshRenderer>();
                    flag.transform.SetParent(go.transform, true);
                }

                checkpoints.Add(cp);
                return cp;
            }

            /// <summary>
            /// The school at the end of the road. Its boundary wall runs across the street's end
            /// (over the footpath and the road), and its gate, a stone arch with a small tiled roof
            /// and the school's name board, faces back down the footpath toward the kid. The school
            /// stands across the yard behind. The kid and the ball both have to get through.
            /// </summary>
            public void Goal(float x, float groundTop = 0f)
            {
                var school = new GameObject("School").transform;
                school.SetParent(root, false);
                GoalX = x;
                // The street's own walls, houses and poles stop short of the school.
                QuietAreas.Add(new Vector2(x - 1f, x + 200f));

                Color stone = new Color(0.92f, 0.9f, 0.85f), trim = new Color(0.7f, 0.68f, 0.64f), roof = new Color(0.32f, 0.35f, 0.42f);
                var concrete = Art.surfaces[ProceduralArt.Surface.Concrete];
                float wx = x + 0.4f;                                    // the gate line, across the street
                float nearZ = -StreetBuilder.PathHalf - 0.3f, farZ = StreetBuilder.PathHalf + 0.35f;
                float mid = (nearZ + farZ) * 0.5f, halfSpan = (farZ - nearZ) * 0.5f, pillarH = 3.1f, rise = 1.1f;
                foreach (float z in new[] { nearZ, farZ })
                {
                    StreetBuilder.Solid(school, "GatePillar", new Vector3(wx, groundTop + pillarH * 0.5f, z), new Vector3(0.7f, pillarH, 0.7f), stone, concrete);
                    StreetBuilder.Solid(school, "GatePlinth", new Vector3(wx, groundTop + 0.2f, z), new Vector3(0.82f, 0.4f, 0.82f), trim, concrete);
                }
                // The boundary wall runs on behind the far pillar; across the road in front, a low
                // row of bollards closes the street end without hiding the gate.
                StreetBuilder.Solid(school, "SchoolWall", new Vector3(wx, groundTop + 1.1f, farZ + 0.35f + 6f), new Vector3(0.4f, 2.2f, 12f), stone, concrete);
                StreetBuilder.Solid(school, "SchoolWallCap", new Vector3(wx, groundTop + 2.25f, farZ + 0.35f + 6f), new Vector3(0.5f, 0.1f, 12f), trim);
                for (float bz = nearZ - 0.9f; bz > StreetBuilder.RoadFar - 0.4f; bz -= 1.3f)
                {
                    var bollard = new GameObject("Bollard");
                    bollard.transform.SetParent(school, false);
                    bollard.transform.position = new Vector3(wx, groundTop - 0.14f + 0.45f, bz);
                    var post = bollard.AddComponent<CylinderShape>();
                    post.axis = Vector3.up;
                    post.radius = 0.1f;
                    post.length = 0.9f;
                    post.sideColor = new Color(0.95f, 0.95f, 0.95f);
                    post.endColor = post.innerColor = new Color(0.85f, 0.25f, 0.22f);
                    bollard.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    post.Rebuild();
                    StreetBuilder.Solid(school, "BollardBand", new Vector3(wx, groundTop - 0.14f + 0.72f, bz), new Vector3(0.21f, 0.1f, 0.21f), new Color(0.85f, 0.25f, 0.22f));
                }
                // The arch over the footpath: stone voussoirs along a half-ellipse, in the plane of the wall.
                const int pieces = 11;
                for (int i = 0; i < pieces; i++)
                {
                    float t0 = i / (float)pieces * Mathf.PI, t1 = (i + 1) / (float)pieces * Mathf.PI, tm = (t0 + t1) * 0.5f;
                    float z = mid - Mathf.Cos(tm) * halfSpan, y = groundTop + pillarH + Mathf.Sin(tm) * rise;
                    float dz = halfSpan * (Mathf.Cos(t0) - Mathf.Cos(t1)), dy = rise * (Mathf.Sin(t1) - Mathf.Sin(t0));
                    var piece = StreetBuilder.Solid(school, "ArchStone", new Vector3(wx, y, z), new Vector3(0.7f, 0.42f, Mathf.Sqrt(dz * dz + dy * dy) + 0.08f), stone, concrete);
                    piece.transform.rotation = Quaternion.Euler(-Mathf.Atan2(dy, dz) * Mathf.Rad2Deg, 0f, 0f);
                }
                StreetBuilder.Solid(school, "ArchRoof", new Vector3(wx, groundTop + pillarH + rise + 0.38f, mid), new Vector3(1.3f, 0.2f, farZ - nearZ + 1.3f), roof, Art.surfaces[ProceduralArt.Surface.RoofTiles]);
                StreetBuilder.Solid(school, "ArchRidge", new Vector3(wx, groundTop + pillarH + rise + 0.55f, mid), new Vector3(0.3f, 0.14f, farZ - nearZ + 1.4f), Color.Lerp(roof, Color.black, 0.2f));
                // Flower tubs either side of the way in.
                foreach (float z in new[] { nearZ, farZ })
                {
                    float inward = z < mid ? 1f : -1f;
                    var tub = new GameObject("FlowerTub");
                    tub.transform.SetParent(school, false);
                    tub.transform.position = new Vector3(wx - 0.75f, groundTop + 0.2f, z + inward * 0.1f);
                    var shape = tub.AddComponent<CylinderShape>();
                    shape.axis = Vector3.up;
                    shape.radius = 0.25f;
                    shape.length = 0.4f;
                    shape.sideColor = new Color(0.72f, 0.4f, 0.3f);
                    shape.endColor = shape.innerColor = new Color(0.36f, 0.27f, 0.2f);
                    tub.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    shape.Rebuild();
                    Blobs(tub.transform, "Flowers", new Vector3(0f, 0.25f, 0f),
                        new BlobShape.Blob(Vector3.zero, new Vector3(0.22f, 0.12f, 0.22f), new Color(0.35f, 0.6f, 0.3f)),
                        new BlobShape.Blob(new Vector3(0.06f, 0.08f, -0.05f), new Vector3(0.07f, 0.05f, 0.07f), new Color(1f, 0.6f, 0.7f)),
                        new BlobShape.Blob(new Vector3(-0.08f, 0.07f, 0.04f), new Vector3(0.06f, 0.05f, 0.06f), new Color(1f, 0.9f, 0.4f)));
                }

                // The school across the yard, its front facing back down the street.
                var building = new GameObject("SchoolBuilding");
                building.transform.SetParent(school, false);
                building.transform.position = new Vector3(x + 10f, groundTop, 4f);
                building.transform.rotation = Quaternion.Euler(0f, 90f, 0f);
                var house = building.AddComponent<House3D>();
                Vector2 size = ProceduralArt.FacadeSize(ProceduralArt.FacadeKind.School);
                house.width = size.x;
                house.wallHeight = size.y;
                house.depth = 12f;
                house.roof = House3D.RoofStyle.Flat;
                house.wallColor = new Color(0.95f, 0.94f, 0.9f);
                house.roofColor = new Color(0.7f, 0.7f, 0.72f);
                building.GetComponent<MeshRenderer>().sharedMaterials = new[] { Art.solid, Art.facades[ProceduralArt.FacadeKind.School], Art.surfaces[ProceduralArt.Surface.RoofTiles] };
                house.Rebuild();
                StreetBuilder.Solid(school, "ClockTower", new Vector3(x + 12f, groundTop + size.y + 1.8f, 4f), new Vector3(4f, 3.6f, 4f), house.wallColor);
                foreach (float dz in new[] { -4.5f, 6.5f })
                {
                    var tree = new GameObject("YardTree").AddComponent<SpriteRenderer>();
                    tree.transform.SetParent(school, false);
                    tree.sprite = Art.mid[5, 1];
                    tree.sharedMaterial = Art.hazeSprite;
                    tree.transform.position = new Vector3(x + 5f, groundTop + tree.sprite.bounds.size.y * 0.5f - 0.15f, dz);
                }

                // Through the gate: the whole school ground past the gate line counts, at any height,
                // so the level ends as soon as the kid and the ball are both inside the gate.
                const float grounds = 40f;
                var goalGo = new GameObject("GoalZone");
                goalGo.transform.SetParent(school, false);
                goalGo.transform.position = new Vector3(wx + grounds * 0.5f, groundTop + 8f, 0f);
                var trigger = goalGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(grounds, 20f);
                goalGo.AddComponent<GoalZone>();
                // The name board on the arch, facing back down the footpath toward the kid.
                var board = Banner("SCHOOL", new Vector2(wx, groundTop + pillarH + 0.3f), groundTop + pillarH + rise - 0.2f);
                board.transform.position = new Vector3(wx - 0.38f, board.transform.position.y, mid);
                board.transform.rotation = Quaternion.Euler(0f, 90f, 0f);
                school.gameObject.AddComponent<StaticBatcher>();
            }

            /// <summary>A signboard on posts. The posts are planted in the ground below once the layout is done (see Finish).</summary>
            public void Sign(string text, Vector2 position)
            {
                Vector2 boardSize;
                var go = SignBoard(text, position, out boardSize);
                pendingSigns.Add(new PendingSign { sign = go.transform, boardSize = boardSize });
            }

            /// <summary>A signboard hanging on short chains from something solid at <paramref name="hangFromY"/> (a gate, an awning).</summary>
            public GameObject Banner(string text, Vector2 position, float hangFromY)
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
                return go;
            }

            /// <summary>Plant every sign's posts in the ground under it. Called once the whole layout exists.</summary>
            public void Finish()
            {
                foreach (var pending in pendingSigns) PlantSign(pending.sign, pending.boardSize);
                pendingSigns.Clear();
                BuildStreetSlabs();
            }

            /// <summary>
            /// The 3D street. The road in front runs unbroken at the lowest ground height; the
            /// footpath lane follows each ground span, so gaps open holes only in the lane (with
            /// stepped retaining walls where the path climbs); the strip behind the lane follows
            /// the spans and bridges the gaps, so the street never breaks. All of it carries on
            /// well past both ends of the level. Side streets cut through the lane and behind it.
            /// </summary>
            void BuildStreetSlabs()
            {
                var slabs = new GameObject("StreetSlabs").transform;
                slabs.SetParent(root, false);
                slabs.gameObject.AddComponent<StaticBatcher>();
                if (groundSpans.Count == 0) return;

                var spans = new List<GroundSpan>(groundSpans);
                spans.Sort((p, q) => p.from.CompareTo(q.from));
                float first = spans[0].from, last = float.MinValue, lastTop = 0f;
                foreach (var span in spans) if (span.to > last) { last = span.to; lastTop = span.top; }
                float baseTop = LowestGroundTop;

                StreetBuilder.Slab(slabs, "Road", first - 70f, last + 70f, baseTop, false, false, StreetBuilder.Part.Front);

                // The lane: one slab per ground span, plus the run-in and run-out.
                foreach (var span in spans)
                    SlabAvoidingSideStreets(slabs, "Footpath", span.from, span.to, span.top, true, true, StreetBuilder.Part.Lane);
                SlabAvoidingSideStreets(slabs, "FootpathBefore", first - 70f, first, spans[0].top, false, true, StreetBuilder.Part.Lane);
                SlabAvoidingSideStreets(slabs, "FootpathAfter", last, last + 70f, lastTop, true, false, StreetBuilder.Part.Lane);

                // Behind the lane: follow the spans and bridge every gap at the lower side's height.
                float covered = first, coveredTop = spans[0].top;
                SlabAvoidingSideStreets(slabs, "Verge", first - 70f, first, spans[0].top, false, true, StreetBuilder.Part.Back);
                foreach (var span in spans)
                {
                    if (span.from > covered + 0.01f)
                        SlabAvoidingSideStreets(slabs, "Verge", covered, span.from, Mathf.Min(coveredTop, span.top), true, true, StreetBuilder.Part.Back);
                    SlabAvoidingSideStreets(slabs, "Verge", span.from, span.to, span.top, true, true, StreetBuilder.Part.Back);
                    if (span.to > covered) { covered = span.to; coveredTop = span.top; }
                }
                SlabAvoidingSideStreets(slabs, "Verge", last, last + 70f, lastTop, true, false, StreetBuilder.Part.Back);
            }

            void SlabAvoidingSideStreets(Transform parent, string name, float from, float to, float top, bool closeLeft, bool closeRight, StreetBuilder.Part part)
            {
                var cuts = new List<Vector2>(OpenAreas);
                cuts.Sort((p, q) => p.x.CompareTo(q.x));
                float a = from;
                foreach (var cut in cuts)
                {
                    if (cut.y <= a || cut.x >= to) continue;
                    if (cut.x > a) StreetBuilder.Slab(parent, name, a, cut.x, top, closeLeft, true, part);
                    a = Mathf.Max(a, cut.y);
                    closeLeft = true;
                }
                if (to > a) StreetBuilder.Slab(parent, name, a, to, top, closeLeft, closeRight, part);
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
                sign.position = new Vector3(pos.x, pos.y, StreetBuilder.PropertyZ - 0.3f);

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
