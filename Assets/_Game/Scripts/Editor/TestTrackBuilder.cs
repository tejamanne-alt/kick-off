using System.IO;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using DribbleToSchool.Tuning;
using DribbleToSchool.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Generates the Phase 1 grey-box test track: placeholder sprites, tuning
    /// assets, physics materials and a fully wired scene. Runs automatically the
    /// first time the project opens; re-run any time from the menu.
    /// </summary>
    [InitializeOnLoad]
    public static class TestTrackBuilder
    {
        const string Root = "Assets/_Game";
        const string ScenePath = Root + "/Scenes/Phase1_TestTrack.unity";
        const string ArtDir = Root + "/Art/Placeholder";
        const string SettingsDir = Root + "/Settings";
        const string PhysicsDir = Root + "/Physics";
        const string AutoBuildKey = "DribbleToSchool.AutoBuildChecked";

        static readonly Color SkyColor = new Color(0.80f, 0.91f, 0.98f);
        static readonly Color GroundColor = new Color(0.45f, 0.42f, 0.38f);
        static readonly Color ObstacleColor = new Color(0.62f, 0.56f, 0.50f);
        static readonly Color CrateColor = new Color(0.78f, 0.58f, 0.33f);
        static readonly Color BouncyColor = new Color(0.90f, 0.40f, 0.40f);
        static readonly Color KidColor = new Color(0.20f, 0.45f, 0.85f);
        static readonly Color SkinColor = new Color(0.98f, 0.80f, 0.65f);
        static readonly Color SchoolColor = new Color(0.95f, 0.75f, 0.30f);

        static Sprite square;
        static Sprite circle;
        static PhysicsMaterial2D groundMat;
        static PhysicsMaterial2D bouncyMat;
        static PhysicsMaterial2D kidMat;
        static PhysicsMaterial2D crateMat;
        static Font signFont;

        static TestTrackBuilder()
        {
            EditorApplication.delayCall += AutoBuildIfMissing;
        }

        static void AutoBuildIfMissing()
        {
            if (SessionState.GetBool(AutoBuildKey, false)) return;
            SessionState.SetBool(AutoBuildKey, true);
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath) != null) return;

            Debug.Log("[Dribble To School] First open: building the Phase 1 test track.");
            Build();
        }

        [MenuItem("Dribble To School/Rebuild Phase 1 Test Track")]
        static void RebuildFromMenu()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            Build();
        }

        public static void Build()
        {
            EnsureFolder(Root + "/Scenes");
            EnsureFolder(ArtDir);
            EnsureFolder(SettingsDir);
            EnsureFolder(PhysicsDir);

            square = LoadOrCreateSprite(ArtDir + "/Square.png", 64, false);
            circle = LoadOrCreateSprite(ArtDir + "/Circle.png", 128, true);
            var ballTuning = LoadOrCreateAsset<BallTuning>(SettingsDir + "/BallTuning.asset");
            var playerTuning = LoadOrCreateAsset<PlayerTuning>(SettingsDir + "/PlayerTuning.asset");
            groundMat = LoadOrCreateMaterial(PhysicsDir + "/Ground.physicsMaterial2D", 0.6f, 0f);
            bouncyMat = LoadOrCreateMaterial(PhysicsDir + "/Bouncy.physicsMaterial2D", 0.2f, 0.9f);
            kidMat = LoadOrCreateMaterial(PhysicsDir + "/Kid.physicsMaterial2D", 0f, 0f);
            crateMat = LoadOrCreateMaterial(PhysicsDir + "/Crate.physicsMaterial2D", 0.5f, 0.1f);
            signFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // Camera
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

            // Systems
            var input = new GameObject("GameInput").AddComponent<GameInput>();
            input.worldCamera = cam;

            var goal = BuildTrack();

            // Kid
            var kidGo = new GameObject("Kid");
            kidGo.transform.position = new Vector3(0f, 0.65f, 0f);
            var kidBody = kidGo.AddComponent<Rigidbody2D>();
            kidBody.mass = 1f;
            var capsule = kidGo.AddComponent<CapsuleCollider2D>();
            capsule.size = new Vector2(0.5f, 1.2f);
            capsule.sharedMaterial = kidMat;
            Visual(kidGo.transform, "Body", square, new Vector2(0f, -0.15f), new Vector2(0.5f, 0.9f), KidColor, 10);
            Visual(kidGo.transform, "Head", circle, new Vector2(0f, 0.38f), new Vector2(0.42f, 0.42f), SkinColor, 11);
            Visual(kidGo.transform, "Eye", circle, new Vector2(0.11f, 0.42f), new Vector2(0.07f, 0.07f), Color.black, 12);
            var feet = new GameObject("Feet").transform;
            feet.SetParent(kidGo.transform, false);
            feet.localPosition = new Vector3(0f, -0.6f, 0f);
            var kid = kidGo.AddComponent<KidController>();
            kid.tuning = playerTuning;
            kid.feet = feet;

            // Ball
            var ballGo = new GameObject("Ball");
            ballGo.transform.position = new Vector3(1f, 0.25f, 0f);
            ballGo.AddComponent<Rigidbody2D>();
            var circleCol = ballGo.AddComponent<CircleCollider2D>();
            circleCol.radius = 0.2f;
            Visual(ballGo.transform, "Shell", circle, Vector2.zero, new Vector2(0.4f, 0.4f), Color.white, 20);
            Visual(ballGo.transform, "Patch", circle, new Vector2(0.08f, 0.06f), new Vector2(0.12f, 0.12f), new Color(0.15f, 0.15f, 0.15f), 21);
            Visual(ballGo.transform, "Patch2", circle, new Vector2(-0.09f, -0.07f), new Vector2(0.09f, 0.09f), new Color(0.15f, 0.15f, 0.15f), 21);
            var ball = ballGo.AddComponent<BallController>();
            ball.tuning = ballTuning;
            ball.kid = kid;
            input.ball = ballGo.transform;
            input.ballWorldRadius = circleCol.radius;

            // Kick aiming
            var aimGo = new GameObject("KickAimer");
            var preview = aimGo.AddComponent<TrajectoryPreview>();
            preview.tuning = ballTuning;
            preview.dotSprite = circle;
            var aimer = aimGo.AddComponent<KickAimer>();
            aimer.ball = ball;
            aimer.preview = preview;
            aimer.worldCamera = cam;

            follow.kid = kid;
            follow.ball = ball;

            // Session + goal + HUD
            var session = new GameObject("TestTrackSession").AddComponent<TestTrackSession>();
            session.kid = kid;
            session.ball = ball;
            session.cameraFollow = follow;

            goal.session = session;

            var hud = new GameObject("DevHud").AddComponent<DevHud>();
            hud.session = session;
            hud.kid = kid;
            hud.ball = ball;
            hud.aimer = aimer;

            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            ConfigurePlayerSettings();
            AssetDatabase.SaveAssets();

            Debug.Log("[Dribble To School] Phase 1 test track ready: " + ScenePath + ". Press Play.");
        }

        /// <summary>
        /// A ~110 m grey-box route that exercises every Phase 1 mechanic in turn.
        /// Ground top is y = 0 unless noted.
        /// </summary>
        static GoalZone BuildTrack()
        {
            var level = new GameObject("Level").transform;

            // Start area and back wall
            Block(level, "BackWall", new Vector2(-10.5f, 3f), new Vector2(1f, 10f), GroundColor, groundMat);
            Ground(level, "Ground_Start", -10f, 34f);
            Sign(level, "Dribble!\nTap the right side as the ball\nreaches the sweet spot", new Vector2(3f, 3.4f));

            // 1. Kerb: jump it, the ball bounces over
            Block(level, "Kerb", new Vector2(18f, 0.15f), new Vector2(0.6f, 0.3f), ObstacleColor, groundMat);
            Sign(level, "Kerb - jump!", new Vector2(18f, 2.2f));

            // 2. Low wall: chip the ball over, then jump
            Block(level, "LowWall", new Vector2(27f, 0.45f), new Vector2(0.4f, 0.9f), ObstacleColor, groundMat);
            Sign(level, "Chip it over:\ndrag back from the ball", new Vector2(25.5f, 3f));

            // 3. Gap: chip the ball across and jump after it
            Sign(level, "Mind the gap", new Vector2(35f, 2.6f));
            Ground(level, "Ground_AfterGap", 36f, 80f);

            // 4. Crate stack: kick it down or chip over it
            Crate(level, new Vector2(44f, 0.35f));
            Crate(level, new Vector2(44.72f, 0.35f));
            Crate(level, new Vector2(44.36f, 1.07f));
            Sign(level, "Kick the crates\n(or chip over)", new Vector2(42f, 3.2f));

            // 5. Ramp up to a raised platform, then step back down
            Ramp(level, new Vector2(52f, 0f), new Vector2(58f, 1.5f));
            Block(level, "Platform", new Vector2(64f, 0.75f), new Vector2(12f, 1.5f), GroundColor, groundMat);
            Sign(level, "Ramp", new Vector2(54f, 2.8f));

            // 6. Bouncy awning: kick the ball off it
            Block(level, "Awning", new Vector2(75f, 2.6f), new Vector2(2.2f, 0.2f), BouncyColor, bouncyMat);
            Decor(level, "AwningPost", new Vector2(76f, 1.25f), new Vector2(0.12f, 2.5f), ObstacleColor);
            Sign(level, "Bounce it off the awning", new Vector2(75f, 4.2f));

            // 7. Step + high wall: hop onto the step, chip the ball over the wall
            Block(level, "Step", new Vector2(80.6f, 0.4f), new Vector2(2f, 0.8f), ObstacleColor, groundMat);
            Block(level, "HighWall", new Vector2(81.85f, 0.9f), new Vector2(0.5f, 1.8f), ObstacleColor, groundMat);
            Ground(level, "Ground_Finish", 80f, 115f);
            Sign(level, "Step up, brake, chip over", new Vector2(80.5f, 3.6f));

            // 8. Juggling stretch before the school
            Sign(level, "Kick it up and juggle:\ntap while it's in the air", new Vector2(92f, 3.2f));

            // School gate
            var school = new GameObject("School").transform;
            school.SetParent(level, false);
            Decor(school, "GatePostL", new Vector2(104f, 1.5f), new Vector2(0.3f, 3f), SchoolColor);
            Decor(school, "GatePostR", new Vector2(107f, 1.5f), new Vector2(0.3f, 3f), SchoolColor);
            Decor(school, "GateTop", new Vector2(105.5f, 3.1f), new Vector2(3.3f, 0.3f), SchoolColor);
            var goalGo = new GameObject("GoalZone");
            goalGo.transform.SetParent(school, false);
            goalGo.transform.position = new Vector3(105.5f, 1.5f, 0f);
            var trigger = goalGo.AddComponent<BoxCollider2D>();
            trigger.isTrigger = true;
            trigger.size = new Vector2(2.6f, 3f);
            var goal = goalGo.AddComponent<GoalZone>();
            Sign(school, "SCHOOL", new Vector2(105.5f, 4f));

            Block(level, "EndWall", new Vector2(115.5f, 3f), new Vector2(1f, 10f), GroundColor, groundMat);
            return goal;
        }

        static void Ground(Transform parent, string name, float fromX, float toX)
        {
            const float depth = 4f;
            Block(parent, name, new Vector2((fromX + toX) * 0.5f, -depth * 0.5f), new Vector2(toX - fromX, depth), GroundColor, groundMat);
        }

        static void Crate(Transform parent, Vector2 center)
        {
            var go = Block(parent, "Crate", center, new Vector2(0.7f, 0.7f), CrateColor, crateMat);
            var body = go.AddComponent<Rigidbody2D>();
            body.mass = 0.8f;
            body.gravityScale = 1.5f;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
        }

        static void Ramp(Transform parent, Vector2 bottom, Vector2 top)
        {
            const float thickness = 0.4f;
            Vector2 along = top - bottom;
            float angle = Mathf.Atan2(along.y, along.x) * Mathf.Rad2Deg;
            Vector2 normal = new Vector2(-along.normalized.y, along.normalized.x);
            Vector2 center = (bottom + top) * 0.5f - normal * (thickness * 0.5f);
            var go = Block(parent, "Ramp", center, new Vector2(along.magnitude + 0.2f, thickness), GroundColor, groundMat);
            go.transform.rotation = Quaternion.Euler(0f, 0f, angle);
        }

        /// <summary>A coloured box with a matching collider. Scale drives both sprite and collider.</summary>
        static GameObject Block(Transform parent, string name, Vector2 center, Vector2 size, Color color, PhysicsMaterial2D material)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = center;
            go.transform.localScale = new Vector3(size.x, size.y, 1f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = square;
            sr.color = color;
            var col = go.AddComponent<BoxCollider2D>();
            col.sharedMaterial = material;
            return go;
        }

        /// <summary>A coloured box with no collider (background dressing).</summary>
        static void Decor(Transform parent, string name, Vector2 center, Vector2 size, Color color)
        {
            var go = Block(parent, name, center, size, color, null);
            Object.DestroyImmediate(go.GetComponent<BoxCollider2D>());
            go.GetComponent<SpriteRenderer>().sortingOrder = -1;
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

        static void Sign(Transform parent, string text, Vector2 position)
        {
            var go = new GameObject("Sign_" + text.Split('\n')[0]);
            go.transform.SetParent(parent, false);
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

        static void ConfigurePlayerSettings()
        {
            PlayerSettings.productName = "Dribble To School";
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
        }

        static void EnsureFolder(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            string parent = Path.GetDirectoryName(path).Replace('\\', '/');
            EnsureFolder(parent);
            AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
        }

        static T LoadOrCreateAsset<T>(string path) where T : ScriptableObject
        {
            var asset = AssetDatabase.LoadAssetAtPath<T>(path);
            if (asset != null) return asset;
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
