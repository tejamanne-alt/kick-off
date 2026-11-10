using DribbleToSchool.Art;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.FrontEnd;
using DribbleToSchool.Presentation;
using DribbleToSchool.World;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    public static partial class LevelBuildKit
    {
        /// <summary>Where the menu's street runs (x): far down to the left, where the camera looks, a little to the right.</summary>
        const float MenuStreetFrom = -120f, MenuStreetTo = 12f;

        /// <summary>
        /// The menu's live backdrop (see MenuStage), built into the open scene with the levels'
        /// own builders: chapter 1's camera look (WorldLook, PostFX), the sky dome and big cumulus
        /// round the way the menu camera looks, a stretch of the home street (StreetBuilder's
        /// houses, walls, trees, poles and wires) running away to the left, and the kid (every
        /// playable kid under a CharacterChoice, each with a MenuKid) on the footpath with a ball,
        /// dressed by a CosmeticApplier. Call after <see cref="LoadShared"/>.
        /// </summary>
        public static MenuStage BuildMenuStage(CosmeticCatalog cosmetics)
        {
            Chapter = 1;
            Theme = ChapterTheme.For(1);
            var mood = Theme.mood;

            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = false;
            cam.fieldOfView = 34f;
            cam.nearClipPlane = 0.2f;
            cam.farClipPlane = 2500f;
            cam.allowHDR = false;    // an 8-bit picture, no MSAA (Core/GraphicsQuality.ConfigureCamera does the same at runtime)
            cam.allowMSAA = false;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = mood.horizon;
            camGo.AddComponent<AudioListener>();
            camGo.transform.position = new Vector3(3.3f, 1f, -3.4f);
            camGo.transform.rotation = Quaternion.Euler(-3f, -58f, 0f);
            var look = camGo.AddComponent<WorldLook>();
            look.sunDirection = mood.sunDirection;
            look.sunColor = mood.sun;
            look.skySunDirection = mood.skySunDirection;
            look.sunGlow = mood.glow;
            look.ambientSky = mood.ambientSky;
            look.ambientGround = mood.ambientGround;
            look.castShadow = mood.castShadow;
            look.skyZenith = mood.zenith;
            look.skyHorizon = mood.horizon;
            look.hazeColor = mood.haze;
            look.hazeStart = mood.hazeStart;
            look.hazeEnd = mood.hazeEnd;
            look.hazeStrength = mood.hazeStrength;
            look.Apply();
            var post = camGo.AddComponent<PostFX>();
            post.shader = Shader.Find("Hidden/DribbleToSchool/PostFX");   // referenced, so builds include it
            post.shadowTint = mood.shadowTint;
            post.balance = mood.balance;
            post.bloomTint = Color.Lerp(mood.glow, Color.white, 0.7f);

            MenuSky(cam);

            // The home street, running away down the left of the view.
            var track = new TrackBuilder(new GameObject("Street").transform);
            track.Coaching.Enabled = false;
            track.Walls(MenuStreetFrom, MenuStreetTo);
            track.Ground(MenuStreetFrom, MenuStreetTo, 0f);
            track.Finish();
            var scenery = new GameObject("Scenery");
            StreetBuilder.Scenery(track, scenery.transform);
            // The levels' camera never looks across the road; this one does, down the street: a
            // field on the far side so the ground runs on to the horizon.
            var field = StreetBuilder.Solid(scenery.transform, "Field", new Vector3(-250f, -0.25f, -216f), new Vector3(800f, 0.3f, 400f),
                new Color(0.62f, 0.72f, 0.52f), Art.surfaces[ProceduralArt.Surface.Grass]);
            field.faces = MeshBuilder.Faces.Top;
            StreetBuilder.NoShadowCast(field);   // the lowest ground in the shot: its shadow falls on nothing
            field.Rebuild();
            scenery.AddComponent<StaticBatcher>();

            var stage = new GameObject("MenuStage").AddComponent<MenuStage>();
            stage.cam = cam;
            BuildMenuTeen(stage, cam, cosmetics);
            return stage;
        }

        /// <summary>The sky dome on the camera, and cumulus far off all round where the menu camera looks and tilts up.</summary>
        static void MenuSky(Camera cam)
        {
            var dome = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            dome.name = "SkyDome";
            Object.DestroyImmediate(dome.GetComponent<Collider>());
            dome.transform.SetParent(cam.transform, false);
            dome.transform.localScale = Vector3.one * 4000f;      // radius 2000, inside the far clip plane
            var domeRenderer = dome.GetComponent<MeshRenderer>();
            domeRenderer.sharedMaterial = Art.skyDome;
            domeRenderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            domeRenderer.receiveShadows = false;

            // Compass directions from down the street on the left (-125) round to straight across (+10),
            // low banks near the horizon and taller ones higher up for the shot that tilts to the sky.
            var clouds = new GameObject("Clouds").transform;
            var rng = new System.Random(2024);
            for (float bearing = -125f; bearing < 12f; bearing += 9f + (float)rng.NextDouble() * 9f)
            {
                for (int tier = 0; tier < 2; tier++)
                {
                    if (tier == 1 && rng.NextDouble() < 0.35) continue;
                    float distance = 420f + (float)rng.NextDouble() * 260f;
                    float elevation = tier == 0 ? 3.5f + (float)rng.NextDouble() * 6f : 15f + (float)rng.NextDouble() * 20f;
                    float b = (bearing + (float)rng.NextDouble() * 5f) * Mathf.Deg2Rad;
                    var go = new GameObject("Cloud");
                    go.transform.SetParent(clouds, false);
                    go.transform.position = new Vector3(Mathf.Sin(b) * distance, Mathf.Tan(elevation * Mathf.Deg2Rad) * distance, Mathf.Cos(b) * distance);
                    // Face the street (the camera) so the broad side shows.
                    go.transform.rotation = Quaternion.Euler(0f, bearing, 0f);
                    var cloud = go.AddComponent<CloudShape>();
                    cloud.seed = rng.Next();
                    cloud.width = (tier == 0 ? 70f : 55f) + (float)rng.NextDouble() * 80f;
                    cloud.height = cloud.width * (0.3f + (float)rng.NextDouble() * 0.18f);
                    go.GetComponent<MeshRenderer>().sharedMaterial = Art.cloud;
                    cloud.Rebuild();
                }
            }
            clouds.gameObject.AddComponent<StaticBatcher>();
        }

        /// <summary>
        /// The kid on the footpath at x = 0, feet on the ground: every playable kid (Settings picks;
        /// CharacterChoice shows one), each juggling with MenuKid, the shared ball and their
        /// shadows, dressed in the equipped cosmetics.
        /// </summary>
        /// <summary>
        /// The menu ball's radius for a teen (metres). The title screen shows the kid close up, so the ball is a real
        /// football's size there (a size 5 is 0.11 m), not the levels' bigger, easier-to-read <see cref="BallRadius"/>.
        /// </summary>
        public const float MenuBallRadiusTeen = 0.115f;
        /// <summary>The menu ball's radius for a primary-school kid: a size 4 ball, for smaller feet.</summary>
        public const float MenuBallRadiusPrimary = 0.1f;

        /// <summary>The ball a kid juggles on the title screen, by the kid's model name (<see cref="PlayerInfo.model"/>).</summary>
        public static float MenuBallRadiusFor(string model)
        {
            foreach (var info in PlayerRoster.All)
                if (info.model == model)
                    return info.level == SchoolLevel.Primary ? MenuBallRadiusPrimary : MenuBallRadiusTeen;
            return MenuBallRadiusTeen;
        }

        static void BuildMenuTeen(MenuStage stage, Camera cam, CosmeticCatalog cosmetics)
        {
            var teenGo = new GameObject("Teen");
            teenGo.transform.position = new Vector3(0f, 0.6f, 0f);   // feet at local y -0.6, on the footpath
            var cast = BuildCast(teenGo.transform);
            var feet = new GameObject("Feet").transform;
            feet.SetParent(teenGo.transform, false);
            feet.localPosition = new Vector3(0f, -0.6f, 0f);

            var kidShadow = ShadowSprite("TeenShadow");
            kidShadow.transform.SetParent(teenGo.transform, false);
            kidShadow.transform.position = new Vector3(0f, 0.012f, 0f);
            kidShadow.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
            Vector2 shadowSprite = kidShadow.sprite != null ? (Vector2)kidShadow.sprite.bounds.size : Vector2.one;
            kidShadow.transform.localScale = new Vector3(0.8f / Mathf.Max(shadowSprite.x, 0.01f), 0.5f / Mathf.Max(shadowSprite.y, 0.01f), 1f);

            var ball = new GameObject("Ball");
            ball.transform.position = new Vector3(0.3f, MenuBallRadiusTeen, -0.2f);
            var sphere = ball.AddComponent<SphereShape>();
            sphere.radius = MenuBallRadiusTeen;
            ball.GetComponent<MeshRenderer>().sharedMaterial = Art.ball;
            sphere.Rebuild();
            var ballShadow = ShadowSprite("BallShadow");

            foreach (var parts in cast.all)
            {
                var kid = parts.rig.gameObject.AddComponent<MenuKid>();
                kid.cam = cam;
                kid.ball = ball.transform;
                kid.ballShadow = ballShadow;
                kid.ballRadius = MenuBallRadiusFor(parts.visual != null ? parts.visual.name : null);
                kid.ballMeshRadius = MenuBallRadiusTeen;
                kid.groundY = 0f;
            }

            var applier = new GameObject("CosmeticApplier").AddComponent<CosmeticApplier>();
            applier.catalog = cosmetics;
            applier.ballRenderer = ball.GetComponent<MeshRenderer>();
            applier.kidBody = cast.outfit;
            applier.backpackFlags = cast.flags.ToArray();
            applier.bags = cast.bags.ToArray();

            stage.teen = teenGo.transform;
            stage.feet = feet;
            stage.applier = applier;
        }
    }
}
