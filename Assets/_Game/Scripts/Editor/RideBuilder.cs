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
    /// haze. Grey boxes in Florida's light until the Florida kit has the car and the towers. It runs by itself and loads the next
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
            const float deck = 6f, startX = -10f, endX = 170f;
            var sea = art.surfaces[ProceduralArt.Surface.Sea];
            var water = StreetBuilder.Solid(world, "Bay", new Vector3(80f, -0.05f, 60f), new Vector3(400f, 0.1f, 200f), Color.white, sea);
            water.faces = MeshBuilder.Faces.Top;
            water.Rebuild();
            // The guideway: a concrete beam on round-ish piers every 18 m.
            StreetBuilder.Solid(world, "Guideway", new Vector3(80f, deck - 0.4f, 0f), new Vector3(220f, 0.8f, 2.2f), concrete);
            for (float x = -20f; x < 190f; x += 18f)
                StreetBuilder.Solid(world, "Pier", new Vector3(x, (deck - 0.8f) * 0.5f, 0f), new Vector3(1f, deck - 0.8f, 1f), concrete);
            // The waterfront under the line: a promenade, palms; across the water the towers in the haze.
            StreetBuilder.Solid(world, "Promenade", new Vector3(80f, 0.3f, -6f), new Vector3(220f, 0.6f, 8f), new Color(0.9f, 0.86f, 0.78f));
            var rng = new System.Random(305);
            for (float x = -20f; x < 190f; x += 9f + (float)rng.NextDouble() * 6f)
                if (LevelBuildKit.KitModel(world, "Plants", "PalmSabalTall", new Vector3(x, 0.6f, -4f - (float)rng.NextDouble() * 3f), (float)rng.NextDouble() * 360f) == null)
                    StreetBuilder.Solid(world, "Palm", new Vector3(x, 3f, -5f), new Vector3(0.3f, 6f, 0.3f), new Color(0.5f, 0.42f, 0.32f));
            for (float x = -10f; x < 200f; x += 14f + (float)rng.NextDouble() * 12f)
            {
                float h = 30f + (float)rng.NextDouble() * 70f, w = 12f + (float)rng.NextDouble() * 10f;
                Color glass = Color.Lerp(new Color(0.55f, 0.7f, 0.78f), new Color(0.92f, 0.9f, 0.85f), (float)rng.NextDouble());
                StreetBuilder.Solid(world, "Tower", new Vector3(x, h * 0.5f, 90f + (float)rng.NextDouble() * 50f), new Vector3(w, h, w), glass);
            }

            // The car, with the kid's window; the cutscene moves it along and keeps the camera beside it.
            var carRoot = new GameObject("PeopleMover").transform;
            carRoot.SetParent(world, false);
            carRoot.position = new Vector3(startX, deck, 0f);
            StreetBuilder.Solid(carRoot, "Body", new Vector3(0f, 1.4f, 0f), new Vector3(10f, 2.6f, 2.6f), car);
            StreetBuilder.Solid(carRoot, "Band", new Vector3(0f, 0.6f, -1.31f), new Vector3(10f, 0.3f, 0.02f), band);
            for (float x = -3.6f; x <= 3.6f; x += 1.8f)
                StreetBuilder.Solid(carRoot, "Window", new Vector3(x, 1.75f, -1.32f), new Vector3(1.4f, 1f, 0.02f), new Color(0.3f, 0.42f, 0.5f));
            var wheels = new System.Collections.Generic.List<Transform>();
            foreach (float x in new[] { -3.4f, 3.4f })
            {
                var w = StreetBuilder.Solid(carRoot, "Bogie", new Vector3(x, 0.1f, 0f), new Vector3(0.9f, 0.4f, 1.6f), new Color(0.3f, 0.3f, 0.32f));
                wheels.Add(w.transform);
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
