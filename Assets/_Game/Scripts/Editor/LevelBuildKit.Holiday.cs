using System;
using System.Collections.Generic;
using System.IO;
using DribbleToSchool.Art;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Hazards;
using DribbleToSchool.Holiday;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Levels;
using DribbleToSchool.Player;
using DribbleToSchool.Presentation;
using DribbleToSchool.World;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The Holiday Run's side of the builder kit: the core scene (the camera, the running kid, the director
    /// and everything the stages are loaded into) and what a stage's track builder adds for a runner
    /// (obstacles marked as solid, ambient hazards that never end the run, chunk-wise slabs).
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            // ---------- A stage draws exactly its own stretch ----------

            float chunkFrom = float.NaN, chunkTo = float.NaN;
            bool chunkCloseLeft, chunkCloseRight;

            /// <summary>True for a Holiday Run stage: its slabs and sand cover [ChunkFrom, ChunkTo] exactly, so neighbouring stages never overlap.</summary>
            public bool IsChunk { get { return !float.IsNaN(chunkFrom); } }
            public float ChunkFrom { get { return chunkFrom; } }
            public float ChunkTo { get { return chunkTo; } }

            /// <summary>
            /// Make this builder one stage's: the 3D street is drawn over [from, to] with no padding. Its ends are open
            /// (the neighbour's slab carries straight on) unless the neighbour is of another chapter, whose surfaces
            /// stand at other heights: then the end is closed with a cap, so no gap shows between the two.
            /// </summary>
            public void SetChunk(float from, float to, bool closeLeft = false, bool closeRight = false)
            {
                chunkFrom = from;
                chunkTo = to;
                chunkCloseLeft = closeLeft;
                chunkCloseRight = closeRight;
                MinX = from;
                MaxX = to;
            }

            /// <summary>The extent of a builder that holds no ground of its own (the sky's: it only needs to know how far to spread clouds).</summary>
            public void SetBounds(float minX, float maxX, float lowestGroundTop)
            {
                MinX = minX;
                MaxX = maxX;
                LowestGroundTop = lowestGroundTop;
            }

            /// <summary>
            /// The 3D street of a stage: the road in front and the strip behind run the whole stretch; the footpath
            /// lane runs it too, with a hole (and the walls of one) wherever the ground has a gap; side streets
            /// cut through lane and back. Nothing past the stretch: the next stage draws its own.
            /// </summary>
            void BuildChunkSlabs(Transform slabs)
            {
                float from = chunkFrom, to = chunkTo;
                if (Chapter == 3)
                {
                    BeachGround(slabs, from, to);
                    return;
                }
                float top = LowestGroundTop;
                StreetBuilder.Slab(slabs, "Road", from, to, top, chunkCloseLeft, chunkCloseRight, StreetBuilder.Part.Front, 0f);

                // Holes in the lane: where one span ends before the next starts (not the run-in or run-out).
                var spans = new List<GroundSpan>(groundSpans);
                spans.Sort((p, q) => p.from.CompareTo(q.from));
                var pieces = new List<Vector2>();
                float piece = from, reach = spans[0].to;
                for (int i = 1; i < spans.Count; i++)
                {
                    if (spans[i].from > reach + 0.01f && reach > from && spans[i].from < to)
                    {
                        pieces.Add(new Vector2(piece, reach));
                        piece = spans[i].from;
                    }
                    reach = Mathf.Max(reach, spans[i].to);
                }
                pieces.Add(new Vector2(piece, to));
                foreach (var p in pieces)
                    SlabAvoidingSideStreets(slabs, "Footpath", p.x, p.y, top,
                        p.x > from + 0.01f || chunkCloseLeft, p.y < to - 0.01f || chunkCloseRight, StreetBuilder.Part.Lane);
                SlabAvoidingSideStreets(slabs, "Verge", from, to, top, chunkCloseLeft, chunkCloseRight, StreetBuilder.Part.Back);
            }

            // ---------- Holders ----------

            /// <summary>
            /// Builds with <paramref name="build"/> into a new holder under the current root (everything it
            /// makes ends up in it) and returns the holder: a parked car, a stack of crates or a barrier is one object.
            /// </summary>
            GameObject Into(string name, Action build)
            {
                var holder = new GameObject(name);
                holder.transform.SetParent(root, false);
                var saved = root;
                root = holder.transform;
                try { build(); }
                finally { root = saved; }
                return holder;
            }

            /// <summary>
            /// Makes an obstacle something to run into: a RunSolid on its top object (a RunBreakable if a kicked ball
            /// smashes it). Crates are pushable in the story levels; here every obstacle is immovable, so their
            /// bodies go and the colliders stay as static ones.
            /// </summary>
            static void Solidify(GameObject holder, bool breakable, int coins = 3)
            {
                foreach (var reset in holder.GetComponentsInChildren<ResettableBody>(true)) Object.DestroyImmediate(reset);
                foreach (var oneWay in holder.GetComponentsInChildren<OneWayBody>(true)) Object.DestroyImmediate(oneWay);   // it needs the body
                foreach (var body in holder.GetComponentsInChildren<Rigidbody2D>(true)) Object.DestroyImmediate(body);
                if (breakable) holder.AddComponent<RunBreakable>().coins = coins;
                else holder.AddComponent<RunSolid>();
            }

            // ---------- A stage's ground and gaps ----------

            /// <summary>
            /// The stage's solid ground: its stretch and a metre into each neighbour (all with the top at y = 0),
            /// split at the gaps, which are drain works or flooded trenches (the pit and the water kill, as they do in a level).
            /// </summary>
            public void RunGround(float from, float to, List<Vector2> gaps, List<bool> water)
            {
                float cursor = from - 1f;
                for (int i = 0; i < gaps.Count; i++)
                {
                    Ground(cursor, gaps[i].x);
                    cursor = gaps[i].y;
                }
                Ground(cursor, to + 1f);
                for (int i = 0; i < gaps.Count; i++)
                {
                    if (water[i]) Water(gaps[i].x, gaps[i].y);
                    else Pit(gaps[i].x, gaps[i].y);
                }
            }

            /// <summary>A cross street over [fromX, toX], a stage's block end: no zebra, the kerbs and a stop line, and the lane and back strip cut round it.</summary>
            public void RunStreet(float fromX, float toX)
            {
                OpenAreas.Add(new Vector2(fromX, toX));
                StreetBuilder.CrossingStreet(root, fromX, toX, 0f, false);
            }

            /// <summary>
            /// A zebra crossing over a side street with its pedestrian signal and the traffic, as scenery: the man
            /// stays green and the cars wait at the stop line, and its trigger is off, so it is never a hazard.
            /// </summary>
            public void RunCrossing(float fromX, float toX, float phase)
            {
                int before = root.childCount;
                Crossing(fromX, toX, phase);
                for (int i = before; i < root.childCount; i++)
                {
                    var crossing = root.GetChild(i).GetComponent<Hazards.Crossing>();
                    if (crossing == null) continue;
                    // A cycle of 28 hours stopped at its green's end: the cars have pulled up to the line.
                    crossing.greenTime = 100000f;
                    crossing.phaseOffset = 95000f;
                    var trigger = crossing.GetComponent<BoxCollider2D>();
                    if (trigger != null) trigger.enabled = false;
                }
            }

            /// <summary>A tunnel with a deck high enough for a double jump under it (HolidayPatterns.TunnelHeight: the head of a kid at the top of one is at 3.24 m); the lots behind it stand aside.</summary>
            public void RunTunnel(float fromX, float toX)
            {
                Tunnel(fromX, toX, 0f, HolidayPatterns.TunnelHeight);
                QuietAreas.Add(new Vector2(fromX, toX));
            }

            /// <summary>
            /// The school gate: the arch over the footpath at <paramref name="gateX"/>, the school across the yard.
            /// Its goal zone is removed: reaching the gate is the director's to detect (by x), and the level's
            /// goal would end the run.
            /// </summary>
            public void RunSchoolGate(float gateX)
            {
                Goal(gateX - 0.4f);
                var school = root.Find("School");
                var zone = school != null ? school.Find("GoalZone") : null;
                if (zone != null) Object.DestroyImmediate(zone.gameObject);
            }

            /// <summary>
            /// The sea washing up the sand behind the path, as scenery: the same wash and wet sand as a level's tide,
            /// but the wave never gets nearer the footpath than 3 m, and there is no lose zone.
            /// </summary>
            public void RunTide(float fromX, float toX, float period, float phaseOffset)
            {
                calmSand.Add(new Vector2(fromX - 3f, toX + 3f));   // smooth sand under the wash
                tideStretches.Add(new Vector2(fromX - 3f, toX + 3f));
                sand = null;

                var wet = new GameObject("WetSand");
                wet.transform.SetParent(root, false);
                var wetStrip = wet.AddComponent<WavyStrip>();
                wetStrip.fromX = fromX;
                wetStrip.toX = toX;
                wetStrip.frontZ = 2.2f;
                wetStrip.backZ = 5.6f;
                wetStrip.seaZ = 9.3f;
                wetStrip.phase = 1.3f;
                wetStrip.y = 0.006f;
                wetStrip.color = new Color(0.86f, 0.79f, 0.72f);
                wet.GetComponent<MeshRenderer>().sharedMaterial = Art.surfaces[ProceduralArt.Surface.Sand];
                wetStrip.Rebuild();

                var washGo = new GameObject("Wash");
                washGo.transform.SetParent(root, false);
                washGo.AddComponent<MeshFilter>();
                washGo.AddComponent<MeshRenderer>().sharedMaterials = new[] { Art.surfaces[ProceduralArt.Surface.Sea], Art.solid };
                var wash = washGo.AddComponent<TideWash>();
                wash.fromX = fromX;
                wash.toX = toX;
                wash.groundY = 0f;
                wash.seaY = -0.3f;   // the core scene's sea, all along the beach
                wash.highZ = 3.6f;   // its front wanders +-0.65: never nearer than 2.9, past the footpath's edge at 1.5

                var go = new GameObject("Tide");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((fromX + toX) * 0.5f, 0f);
                var tide = go.AddComponent<Hazards.Tide>();
                tide.lowOffset = 0f;
                tide.highOffset = 0f;
                tide.period = period;
                tide.phaseOffset = phaseOffset;
                tide.wash = wash;
            }

            /// <summary>
            /// A tower crane carrying a pallet back and forth high over the trench, out of the kid's reach:
            /// the story levels' crane and load, with the load moving by itself and no collider to ride.
            /// </summary>
            public void RunCrane(float x)
            {
                const float hang = HolidayPatterns.CraneHang;
                var go = new GameObject("CraneLoad");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(x - 3f, hang, 0f);
                go.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var mover = go.AddComponent<Hazards.MovingPlatform>();
                mover.travel = new Vector2(6f, 0f);
                mover.speed = 1.2f;
                mover.waitTime = 1.2f;
                CraneLoad(go.transform, new Vector2(x - 3f, hang), 2.6f, mover.travel);
            }

            // ---------- Obstacles ----------

            /// <summary>A block in the kid's way: a kerb or step, a planter, a rock, a hedge, a stack of crates, by its size and the chapter.</summary>
            public GameObject RunWall(float x, float height, float width)
            {
                var holder = Into("Obstacle", () => Wall(x, height, 0f, width));
                Solidify(holder, false);
                return holder;
            }

            /// <summary>A parked car, 3.3 m long and 1.55 high.</summary>
            public GameObject RunCar(float x, Color paint)
            {
                var holder = Into("ParkedCar", () => ParkedCar(x, paint));
                Solidify(holder, false);
                return holder;
            }

            /// <summary>A barrier to slide under, from the Barriers kit.</summary>
            public GameObject RunSlide(float x, SlideLook look)
            {
                var holder = Into("Barrier", () => SlideUnder(x, look));
                Solidify(holder, false);
                return holder;
            }

            /// <summary>
            /// Something a kicked ball smashes for coins: a wooden crate, a sandcastle on the beach, a stack of
            /// cones on the site (every other one).
            /// </summary>
            public GameObject RunBreakable(float x)
            {
                GameObject holder;
                if (Chapter == 3) holder = Into("Sandcastle", () => SandCastleBlock(x));
                else if (Chapter == 4 && Mathf.Abs(Mathf.RoundToInt(x)) % 2 == 0) holder = Into("Cones", () => ConeBlock(x));
                else holder = Into("Crate", () => Crate(x, 0.35f));
                Solidify(holder, true);
                return holder;
            }

            /// <summary>A sandcastle about a metre across (or the size asked): the Leisure kit's, stretched to fill its collider.</summary>
            void SandCastleBlock(float x, float w = 1f, float h = 0.75f)
            {
                var go = Block("Sandcastle", new Vector2(x, h * 0.5f), new Vector2(w, h), ObstacleColor, GroundMat, false);
                Vector3 native = KitSize("Leisure", "SandCastle");
                if (native.x > 0.05f && native.y > 0.05f && HasKitModel("Leisure", "SandCastle"))
                {
                    var t = KitModel(go.transform, "Leisure", "SandCastle", new Vector3(x, 0f, 0f));
                    if (t != null)
                    {
                        t.localScale = new Vector3(w / native.x, h / native.y, 0.9f / Mathf.Max(0.05f, native.z));
                        return;
                    }
                }
                Part(go.transform, "Mound", Vector3.zero, new Vector3(w, h, 0.9f), new Color(0.92f, 0.82f, 0.58f));
            }

            /// <summary>
            /// A pile of crates two high, 1.42 m, that a hard kick smashes for coins (a big sandcastle on the beach). Too high for a
            /// single jump: a double jump gets over it (HolidayPatterns.StackHeight).
            /// </summary>
            public GameObject RunStack(float x)
            {
                GameObject holder;
                if (Chapter == 3) holder = Into("BigSandcastle", () => SandCastleBlock(x, HolidayPatterns.StackWidth + 0.1f, HolidayPatterns.StackHeight));
                else holder = Into("CrateStack", () => CrateStack(x - 0.36f));
                Solidify(holder, true, 6);
                return holder;
            }

            // The colours balloons come in.
            static readonly Color[] BalloonPaint =
            {
                new Color(0.92f, 0.28f, 0.3f), new Color(1f, 0.8f, 0.25f), new Color(0.3f, 0.6f, 0.95f),
                new Color(0.35f, 0.78f, 0.5f), new Color(0.98f, 0.55f, 0.75f), new Color(1f, 0.58f, 0.2f),
            };

            /// <summary>
            /// A floating target the ball bursts into coins: a balloon on a string (at home, on the site), a paper lantern on a cord
            /// (the market, the park) or a beach ball hung from a line (the beach), <paramref name="y"/> up. It is a trigger with a
            /// RunBreakable: the kid passes through it, nothing counts it as an obstacle, and a ball flying through it bursts it.
            /// </summary>
            public GameObject RunBalloon(float x, float y, int style, int color)
            {
                var go = new GameObject(style == 1 ? "Lantern" : style == 2 ? "BeachBall" : "Balloon");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(x, y, 0f);
                var circle = go.AddComponent<CircleCollider2D>();
                circle.isTrigger = true;
                circle.radius = 0.45f;
                var target = go.AddComponent<RunBreakable>();
                target.floating = true;
                target.coins = 5;
                target.minSpeed = 2.5f;
                Color paint = BalloonPaint[Mathf.Abs(color) % BalloonPaint.Length];
                Color dark = Color.Lerp(paint, Color.black, 0.35f), light = Color.Lerp(paint, Color.white, 0.55f);
                Color cord = new Color(0.85f, 0.84f, 0.8f);
                if (style == 1)
                {
                    // A paper lantern: a warm ball with gold caps, hung from a cord, a tassel below.
                    Color lantern = Color.Lerp(paint, new Color(1f, 0.55f, 0.2f), 0.5f), gold = new Color(0.95f, 0.78f, 0.3f);
                    Blobs(go.transform, "Paper", Vector3.zero,
                        new BlobShape.Blob(Vector3.zero, new Vector3(0.3f, 0.34f, 0.3f), lantern),
                        new BlobShape.Blob(new Vector3(0f, 0.34f, 0f), new Vector3(0.14f, 0.04f, 0.14f), gold),
                        new BlobShape.Blob(new Vector3(0f, -0.34f, 0f), new Vector3(0.14f, 0.04f, 0.14f), gold),
                        new BlobShape.Blob(new Vector3(0f, -0.52f, 0f), new Vector3(0.04f, 0.14f, 0.04f), gold),
                        new BlobShape.Blob(new Vector3(-0.1f, 0.1f, -0.24f), new Vector3(0.06f, 0.14f, 0.04f), Color.Lerp(lantern, Color.white, 0.5f)));
                    Part(go.transform, "Cord", new Vector3(0f, 1.1f, 0f), new Vector3(0.015f, 1.5f, 0.015f), cord);
                }
                else if (style == 2)
                {
                    // A beach ball: white with a coloured band either side of the middle, hung from a line.
                    Blobs(go.transform, "Ball", Vector3.zero,
                        new BlobShape.Blob(Vector3.zero, new Vector3(0.34f, 0.34f, 0.34f), Color.white),
                        new BlobShape.Blob(Vector3.zero, new Vector3(0.345f, 0.09f, 0.345f), paint),
                        new BlobShape.Blob(new Vector3(0f, 0.2f, 0f), new Vector3(0.275f, 0.075f, 0.275f), BalloonPaint[(color + 2) % BalloonPaint.Length]),
                        new BlobShape.Blob(new Vector3(0f, -0.2f, 0f), new Vector3(0.275f, 0.075f, 0.275f), BalloonPaint[(color + 2) % BalloonPaint.Length]),
                        new BlobShape.Blob(new Vector3(0f, 0.34f, 0f), new Vector3(0.05f, 0.03f, 0.05f), dark));
                    Part(go.transform, "Line", new Vector3(0f, 1.2f, 0f), new Vector3(0.015f, 1.7f, 0.015f), cord);
                }
                else
                {
                    // A party balloon: a rounded ellipsoid with a knot, a shine, and a string trailing down.
                    Blobs(go.transform, "Balloon", Vector3.zero,
                        new BlobShape.Blob(new Vector3(0f, 0.05f, 0f), new Vector3(0.3f, 0.37f, 0.3f), paint),
                        new BlobShape.Blob(new Vector3(0f, -0.34f, 0f), new Vector3(0.07f, 0.05f, 0.07f), dark),
                        new BlobShape.Blob(new Vector3(-0.1f, 0.16f, -0.22f), new Vector3(0.07f, 0.11f, 0.04f), light));
                    Part(go.transform, "String", new Vector3(0f, -0.95f, 0f), new Vector3(0.015f, 1.1f, 0.015f), cord);
                }
                return go;
            }

            /// <summary>
            /// A big star coin worth <paramref name="value"/> coins: the Animals kit's star, half again as big as a coin, spinning like
            /// one (a Coin with a bigger worth), where only a double jump or a trampoline's throw gets to.
            /// </summary>
            public GameObject RunStar(float x, float y, int value)
            {
                var go = new GameObject("StarCoin");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(x, y, 0f);
                var col = go.AddComponent<CircleCollider2D>();
                col.isTrigger = true;
                col.radius = 0.5f;
                var visual = new GameObject("Visual");
                visual.transform.SetParent(go.transform, false);
                if (KitModel(visual.transform, "Animals", "Star", visual.transform.position, 0f, 1.7f) == null)
                {
                    // Without the kit: a fat golden disc.
                    var disc = visual.AddComponent<CylinderShape>();
                    disc.radius = 0.42f;
                    disc.length = 0.1f;
                    disc.sideColor = new Color(0.9f, 0.62f, 0.12f);
                    disc.endColor = new Color(1f, 0.85f, 0.3f);
                    disc.innerRadius = 0.26f;
                    disc.innerColor = new Color(1f, 0.92f, 0.5f);
                    visual.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    disc.Rebuild();
                }
                var coin = go.AddComponent<Pickups.Coin>();
                coin.visual = visual.transform;
                coin.value = Mathf.Max(1, value);
                return go;
            }

            /// <summary>Three traffic cones in a row on the path's line, with one box collider round them.</summary>
            void ConeBlock(float x)
            {
                var go = Block("Cones", new Vector2(x, 0.335f), new Vector2(1.1f, 0.67f), ObstacleColor, GroundMat, false);
                for (int i = -1; i <= 1; i++)
                {
                    float cx = x + i * 0.36f;
                    if (StreetBuilder.Model(go.transform, "Street", "TrafficCone", cx, 0f, 0f, i * 37f) != null) continue;
                    var cone = new GameObject("Cone");
                    cone.transform.SetParent(go.transform, false);
                    cone.transform.position = new Vector3(cx, 0f, 0f);
                    cone.AddComponent<ConeShape>();
                    cone.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    cone.GetComponent<ConeShape>().Rebuild();
                }
            }

            /// <summary>A magnet, shield or turbo floating in the path (a glass orb that builds its own look when the stage loads).</summary>
            public GameObject RunPowerUp(float x, float y, PowerUpKind kind)
            {
                var go = new GameObject("PowerUp_" + kind);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(x, y, 0f);
                var circle = go.AddComponent<CircleCollider2D>();
                circle.isTrigger = true;
                circle.radius = 0.6f;
                go.AddComponent<PowerUp>().kind = kind;
                return go;
            }
        }

        // ================================================================== the core scene

        /// <summary>
        /// The Holiday Run's core scene, always loaded: the camera with the look of the first chapter, the
        /// input, the kid and the ball (the campaign's, walking and dribbling and kicking), the level manager
        /// in endless mode (the campaign with no goal: it hosts the hazards and checkpoints of the stages), the effects, the sky and
        /// the distant land all along the lap, and the director, the stage streamer, the atmosphere and the
        /// HUD, wired. The stages are separate scenes, loaded into this one while the kid runs.
        /// Call after <see cref="LoadShared"/>.
        /// </summary>
        public static void BuildHolidayCore(string scenePath, LevelCatalog catalog)
        {
            EnsureFolder(Path.GetDirectoryName(scenePath).Replace('\\', '/'));
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Chapter = 1;
            Theme = ChapterTheme.For(1);

            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            // As in the levels: a perspective camera looking down the street at a slight tilt (CameraFollow2D).
            var cam = camGo.AddComponent<Camera>();
            cam.orthographic = false;
            cam.fieldOfView = 34f;
            cam.nearClipPlane = 0.3f;
            cam.farClipPlane = 2500f;
            var mood = Theme.mood;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = mood.horizon;
            camGo.AddComponent<AudioListener>();
            camGo.transform.position = new Vector3(HolidayStages.SpawnX, 2f, -20f);
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
            var follow = camGo.AddComponent<CameraFollow2D>();
            // The camera of a level, but it never stops at an edge (the stages come and go).
            follow.minX = -60f;
            follow.maxX = 1e7f;
            follow.minY = 1.8f;

            var input = new GameObject("GameInput").AddComponent<GameInput>();
            input.worldCamera = cam;

            // The level start: where the kid is put down (and where a day begins).
            var startGo = new GameObject("Start");
            startGo.transform.position = new Vector2(HolidayStages.SpawnX, 0f);
            var start = startGo.AddComponent<Checkpoint>();
            start.isStart = true;
            start.kidSpawn = new GameObject("KidSpawn").transform;
            start.kidSpawn.SetParent(startGo.transform, false);
            start.kidSpawn.localPosition = new Vector3(0f, 0.6f, 0f);
            start.ballSpawn = new GameObject("BallSpawn").transform;
            start.ballSpawn.SetParent(startGo.transform, false);
            start.ballSpawn.localPosition = new Vector3(1f, BallRadius + 0.05f, 0f);

            // Kid: every playable kid, as in the levels (the chosen one shows).
            var kidGo = new GameObject("Kid");
            kidGo.transform.position = start.KidSpawnPosition;
            var kidBody = kidGo.AddComponent<Rigidbody2D>();
            kidBody.mass = 1f;
            var capsule = kidGo.AddComponent<CapsuleCollider2D>();
            capsule.size = new Vector2(0.5f, 1.2f);
            capsule.sharedMaterial = kidMat;
            var cast = BuildCast(kidGo.transform);
            var feet = new GameObject("Feet").transform;
            feet.SetParent(kidGo.transform, false);
            feet.localPosition = new Vector3(0f, -0.6f, 0f);
            var kid = kidGo.AddComponent<KidController>();
            kid.tuning = playerTuning;
            kid.feet = feet;
            foreach (var parts in cast.all) parts.rig.gameObject.AddComponent<KidAnimator>().kid = kid;
            MonoBehaviour kidOutfit = cast.outfit;
            var kidFlags = cast.flags;

            // Ball: built as in the levels (dribbled by the kid's touches, kicked by the aim drag); a kick
            // that hits a crate smashes it (BallSmasher).
            var ballGo = new GameObject("Ball");
            ballGo.transform.position = start.BallSpawnPosition;
            ballGo.AddComponent<Rigidbody2D>();
            var circleCol = ballGo.AddComponent<CircleCollider2D>();
            circleCol.radius = BallRadius;
            var squashRoot = new GameObject("SquashRoot").transform;
            squashRoot.SetParent(ballGo.transform, false);
            var shell = new GameObject("Ball3D");
            shell.transform.SetParent(squashRoot, false);
            var sphere = shell.AddComponent<SphereShape>();
            sphere.radius = BallRadius;
            shell.GetComponent<MeshRenderer>().sharedMaterial = Art.ball;
            sphere.Rebuild();
            var ballShadow = ShadowSprite("BallShadow");
            var kidShadow = ShadowSprite("KidShadow");
            var trail = ballGo.AddComponent<TrailRenderer>();
            trail.sharedMaterial = trailMaterial;
            trail.time = 0.25f;
            trail.minVertexDistance = 0.05f;
            trail.widthMultiplier = BallRadius * 1.6f;
            trail.widthCurve = AnimationCurve.Linear(0f, 1f, 1f, 0f);
            trail.sortingOrder = 19;
            trail.enabled = false;
            var ball = ballGo.AddComponent<BallController>();
            ball.tuning = ballTuning;
            ball.kid = kid;
            ballGo.AddComponent<BallSmasher>();
            var ballVisual = ballGo.AddComponent<BallVisual>();
            ballVisual.ball = ball;
            ballVisual.squashRoot = squashRoot;
            var ballShade = ballGo.AddComponent<GroundShadow>();
            ballShade.target = ballGo.GetComponent<Rigidbody2D>();
            ballShade.ignore = new[] { kidBody };
            ballShade.shadow = ballShadow;
            ballShade.size = new Vector2(BallRadius * 2.1f, BallRadius * 1.2f);
            var kidShade = kidGo.AddComponent<GroundShadow>();
            kidShade.target = kidBody;
            kidShade.ignore = new[] { ballShade.target };
            kidShade.shadow = kidShadow;
            kidShade.size = new Vector2(0.7f, 0.36f);
            kidShade.maxDistance = 6f;

            // Kick aiming, as in the levels.
            var aimGo = new GameObject("KickAimer");
            var preview = aimGo.AddComponent<TrajectoryPreview>();
            preview.tuning = ballTuning;
            preview.dotSprite = Circle;
            var aimer = aimGo.AddComponent<KickAimer>();
            aimer.ball = ball;
            aimer.preview = preview;
            aimer.worldCamera = cam;

            // Tunnels darken the view round the kid.
            var darkGo = new GameObject("Darkness");
            darkGo.AddComponent<SpriteRenderer>();
            darkGo.AddComponent<DarknessOverlay>().follow = kidGo.transform;

            follow.kid = kid;
            follow.ball = ball;

            // Sky and distant land, all along the lap.
            var skyBounds = new TrackBuilder(new GameObject("SkyBounds").transform);
            skyBounds.SetBounds(HolidayStages.FirstStageX, HolidayStages.FirstStageX + HolidayStages.LapLength, 0f);
            BuildSky(skyBounds, cam);
            var far = new GameObject("FarLand");
            StreetBuilder.FarLand(far.transform);
            far.AddComponent<StaticBatcher>();

            var fxGo = new GameObject("FX");
            var pool = fxGo.AddComponent<FxPool>();
            var fx = fxGo.AddComponent<FxDirector>();
            fx.pool = pool;
            fx.cameraFollow = follow;
            fx.puff = Art.puff;
            fx.spark = Art.spark;
            fx.drop = Art.drop;
            fx.dustColor = Color.Lerp(Theme.groundEdge, Color.white, 0.5f);

            // The level manager only hosts the stages' hazards and the countdown; losing the ball ends the run.
            var manager = new GameObject("LevelManager").AddComponent<LevelManager>();
            manager.endless = true;
            manager.level = null;
            manager.catalog = catalog;
            manager.kid = kid;
            manager.ball = ball;
            manager.cameraFollow = follow;
            manager.checkpoints = new List<Checkpoint> { start };
            manager.killY = -8f;
            // As in a level, a ball left far behind is lost (so a kid can't wander off without it, or be stranded without it).
            manager.maxBallBehindDistance = 16f;

            var applier = new GameObject("CosmeticApplier").AddComponent<CosmeticApplier>();
            applier.catalog = Cosmetics;
            applier.holiday = true;   // casual clothes, not the school uniform, unless the player chose another outfit
            applier.ballRenderer = shell.GetComponent<MeshRenderer>();
            applier.ballTrail = trail;
            applier.kidBody = kidOutfit;
            applier.backpackFlags = kidFlags.ToArray();
            applier.bags = cast.bags.ToArray();

            // The Holiday Run itself.
            var streamer = new GameObject("RunWorldStreamer").AddComponent<RunWorldStreamer>();
            streamer.follow = kidGo.transform;
            var atmosphere = new GameObject("HolidayAtmosphere").AddComponent<HolidayAtmosphere>();
            atmosphere.look = look;
            atmosphere.follow = kidGo.transform;
            var director = new GameObject("HolidayRunDirector").AddComponent<HolidayRunDirector>();
            director.level = manager;
            director.kid = kid;
            director.ball = ball;
            director.aimer = aimer;
            director.cameraFollow = follow;
            director.streamer = streamer;
            director.atmosphere = atmosphere;
            var hud = new GameObject("HolidayRunHud").AddComponent<HolidayRunHud>();
            hud.director = director;

            EditorSceneManager.SaveScene(scene, scenePath);
        }
    }
}
