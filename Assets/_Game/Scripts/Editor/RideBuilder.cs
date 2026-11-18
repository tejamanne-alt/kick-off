using DribbleToSchool.Art;
using DribbleToSchool.Core;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Builds a ride's scene (Levels/Rides, Core/RideCutscene): Miami's people mover, a little driverless car gliding along its
    /// elevated guideway round the bay's edge, the camera beside it, the bay below, palms and the downtown towers in the humid
    /// haze, all from the Miami kit (the Metromover's car, the guideway on its mural piers, the bayfront's balustrade, royal palms
    /// and banyans, a cruise ship, Brickell's towers), with boxes only if the kit is missing. It runs by itself and loads the next
    /// leg (FL3-2) at its end.
    /// </summary>
    public static class RideBuilder
    {
        public static void Build(string scenePath, string ride)
        {
            LevelBuildKit.EnsureFolder(System.IO.Path.GetDirectoryName(scenePath).Replace('\\', '/'));
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            LevelBuildKit.Chapter = 3;
            LevelBuildKit.Theme = LevelBuildKit.ThemeFor(3);
            var mood = LevelBuildKit.Theme.mood;
            var art = LevelBuildKit.Art;

            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.fieldOfView = 38f;
            cam.nearClipPlane = 0.3f;
            cam.farClipPlane = 2500f;
            cam.allowHDR = false;
            cam.allowMSAA = false;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = mood.horizon;
            camGo.AddComponent<AudioListener>();
            camGo.transform.rotation = Quaternion.Euler(4f, 0f, 0f);
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
            post.shader = Shader.Find("Hidden/DribbleToSchool/PostFX");
            post.shadowTint = mood.shadowTint;
            post.balance = mood.balance;
            post.bloomTint = Color.Lerp(mood.glow, Color.white, 0.7f);

            var world = new GameObject("Ride").transform;
            Color concrete = new Color(0.86f, 0.85f, 0.82f), car = new Color(0.95f, 0.95f, 0.93f), band = new Color(0.13f, 0.6f, 0.6f);
            // The car runs on the guideway's deck, between its parapets (the Miami kit's GuidewayMIA: its girder's top at 10.3 m).
            bool kit = LevelBuildKit.HasKitModel("Miami", "GuidewayMIA") && LevelBuildKit.HasKitModel("Miami", "MetromoverMIA");
            float deck = kit ? 10.3f : 6f;
            const float startX = -10f, endX = 170f;
            var sea = art.surfaces[ProceduralArt.Surface.Sea];
            var water = StreetBuilder.Solid(world, "Bay", new Vector3(80f, -0.05f, 60f), new Vector3(400f, 0.1f, 200f), Color.white, sea);
            water.faces = MeshBuilder.Faces.Top;
            water.Rebuild();
            var rng = new System.Random(305);
            if (kit)
            {
                // The guideway's spans, 30 m each on their mural piers; the bayfront promenade under them with its balustrade,
                // royal palms and banyans; on the bay a cruise ship, a freighter and a tug; across it Brickell's and the beach's
                // towers in the haze.
                for (float x = -30f; x < 210f; x += 30f)
                    LevelBuildKit.KitModel(world, "Miami", "GuidewayMIA", new Vector3(x, 0f, 0f));
                // (the promenade runs behind the line, between it and the water: nothing stands between the camera and the car)
                StreetBuilder.Solid(world, "Promenade", new Vector3(80f, -0.02f, 0f), new Vector3(260f, 0.04f, 22f), new Color(0.9f, 0.86f, 0.78f),
                    art.surfaces[ProceduralArt.Surface.Paving]);
                for (float x = -30f; x < 210f; x += 4f)
                    LevelBuildKit.KitModel(world, "Miami", "BayRailMIA", new Vector3(x, 0f, 10.6f));
                for (float x = -26f; x < 206f; x += 11f + (float)rng.NextDouble() * 6f)
                    LevelBuildKit.KitModel(world, "Plants", rng.NextDouble() < 0.8 ? "PalmRoyal" : "Banyan",
                        new Vector3(x, 0f, 4f + (float)rng.NextDouble() * 5f), (float)rng.NextDouble() * 360f, 0.9f + (float)rng.NextDouble() * 0.2f);
                LevelBuildKit.KitModel(world, "Miami", "CruiseShipMIA", new Vector3(110f, -0.9f, 160f), 0f, 1f);
                LevelBuildKit.KitModel(world, "Miami", "FreighterMIA", new Vector3(20f, -0.7f, 70f), 10f, 1f);
                LevelBuildKit.KitModel(world, "Miami", "TugMIA", new Vector3(60f, -0.6f, 40f), 190f, 1f);
                string[] towers = { "CondoTowerMIA", "OfficeTowerMIA", "CondoTower2MIA" };
                for (float x = -40f; x < 220f; x += 22f + (float)rng.NextDouble() * 18f)
                    LevelBuildKit.KitModel(world, "Miami", towers[rng.Next(towers.Length)], new Vector3(x, 0f, 250f + (float)rng.NextDouble() * 80f),
                        (float)rng.NextDouble() * 20f - 10f, 0.9f + (float)rng.NextDouble() * 0.4f);
            }
            else
            {
                // (without the kit: a concrete beam on piers, palms, towers as boxes)
                StreetBuilder.Solid(world, "Guideway", new Vector3(80f, deck - 0.4f, 0f), new Vector3(220f, 0.8f, 2.2f), concrete);
                for (float x = -20f; x < 190f; x += 18f)
                    StreetBuilder.Solid(world, "Pier", new Vector3(x, (deck - 0.8f) * 0.5f, 0f), new Vector3(1f, deck - 0.8f, 1f), concrete);
                StreetBuilder.Solid(world, "Promenade", new Vector3(80f, 0.3f, -6f), new Vector3(220f, 0.6f, 8f), new Color(0.9f, 0.86f, 0.78f));
                for (float x = -20f; x < 190f; x += 9f + (float)rng.NextDouble() * 6f)
                    if (LevelBuildKit.KitModel(world, "Plants", "PalmSabalTall", new Vector3(x, 0.6f, -4f - (float)rng.NextDouble() * 3f), (float)rng.NextDouble() * 360f) == null)
                        StreetBuilder.Solid(world, "Palm", new Vector3(x, 3f, -5f), new Vector3(0.3f, 6f, 0.3f), new Color(0.5f, 0.42f, 0.32f));
                for (float x = -10f; x < 200f; x += 14f + (float)rng.NextDouble() * 12f)
                {
                    float h = 30f + (float)rng.NextDouble() * 70f, w = 12f + (float)rng.NextDouble() * 10f;
                    Color glass = Color.Lerp(new Color(0.55f, 0.7f, 0.78f), new Color(0.92f, 0.9f, 0.85f), (float)rng.NextDouble());
                    StreetBuilder.Solid(world, "Tower", new Vector3(x, h * 0.5f, 90f + (float)rng.NextDouble() * 50f), new Vector3(w, h, w), glass);
                }
            }

            // The car, with the kid's window; the cutscene moves it along and keeps the camera beside it.
            var carRoot = new GameObject("PeopleMover").transform;
            carRoot.SetParent(world, false);
            carRoot.position = new Vector3(startX, deck, 0f);
            if (!kit || LevelBuildKit.KitModel(carRoot, "Miami", "MetromoverMIA", carRoot.position) == null)
            {
                StreetBuilder.Solid(carRoot, "Body", new Vector3(0f, 1.4f, 0f), new Vector3(10f, 2.6f, 2.6f), car);
                StreetBuilder.Solid(carRoot, "Band", new Vector3(0f, 0.6f, -1.31f), new Vector3(10f, 0.3f, 0.02f), band);
                for (float x = -3.6f; x <= 3.6f; x += 1.8f)
                    StreetBuilder.Solid(carRoot, "Window", new Vector3(x, 1.75f, -1.32f), new Vector3(1.4f, 1f, 0.02f), new Color(0.3f, 0.42f, 0.5f));
                foreach (float x in new[] { -3.4f, 3.4f })
                    StreetBuilder.Solid(carRoot, "Bogie", new Vector3(x, 0.1f, 0f), new Vector3(0.9f, 0.4f, 1.6f), new Color(0.3f, 0.3f, 0.32f));
            }

            var cutscene = new GameObject("RideCutscene").AddComponent<RideCutscene>();
            cutscene.car = carRoot;
            cutscene.startX = startX;
            cutscene.endX = endX;
            cutscene.cameraRig = camGo.transform;
            cutscene.cameraOffset = new Vector3(2f, 0.6f, -16f);
            cutscene.spinners = new Transform[0];
            cutscene.ride = ride;
            cutscene.duration = Rides.Seconds;
            camGo.transform.position = carRoot.position + cutscene.cameraOffset;

            EditorSceneManager.SaveScene(scene, scenePath);
        }
    }
}
