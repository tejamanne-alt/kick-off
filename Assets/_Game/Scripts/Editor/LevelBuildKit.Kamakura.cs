using System.Collections.Generic;
using DribbleToSchool.Hazards;
using DribbleToSchool.Levels;
using DribbleToSchool.Presentation;
using DribbleToSchool.World;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's own levels (docs/KAMAKURA_BUILD.md, Step 7; GeneratedContent.CityLevels): built while <see cref="Kamakura"/> is
    /// set, their stops and routes are Kamakura's (Levels/CityRoutes), not the original town's (Levels/RouteTable), their street
    /// is StreetBuilder.Kamakura's, and their layouts (KamakuraLevels) place the Kamakura kit's models by the levels' proposed
    /// layouts (review/kamakura/levels/&lt;id&gt;/layout.json), plus the hazards Kamakura's first leg needs: the first-graders
    /// walking to school, and the level crossing the tram comes through.
    /// </summary>
    public static partial class LevelBuildKit
    {
        /// <summary>Set while a Kamakura level's scene is built (GeneratedContent.BuildAll): its stops, route and street are Kamakura's.</summary>
        public static bool Kamakura;

        /// <summary>
        /// How much further from the play lane the game sets what stands beside it than a Kamakura layout does: a layout's
        /// walking strip is 0.75 m either side of the lane, the game's footpath 1.5 m (StreetBuilder.PathHalf), so a model's
        /// street face goes this much further back than its layout's "front" and the kerb and frontage keep their distance
        /// from the lane (nothing tall stands in front of it: docs/LEARNINGS.md E10).
        /// </summary>
        public const float KamakuraDepth = 0.75f;

        /// <summary>Where a level starts: Kamakura's own stops while a Kamakura level is built, else the original town's.</summary>
        static Stop FromStop(string levelId)
        {
            return Kamakura ? CityRoutes.Kamakura.From(levelId) : RouteTable.From(levelId);
        }

        /// <summary>Where a level ends (as <see cref="FromStop"/>).</summary>
        static Stop ToStop(string levelId)
        {
            return Kamakura ? CityRoutes.Kamakura.To(levelId) : RouteTable.To(levelId);
        }

        /// <summary>The route a level is on (as <see cref="FromStop"/>).</summary>
        static Route RouteOfLevel(string levelId)
        {
            return Kamakura ? CityRoutes.Kamakura.Of(levelId) : RouteTable.Of(levelId);
        }

        /// <summary>The z of a Kamakura model's origin whose street face a layout puts at <paramref name="front"/> (yaw 0), moved back by <see cref="KamakuraDepth"/>.</summary>
        public static float KamakuraZ(string model, float front)
        {
            return front + KamakuraDepth - KitMin("Kamakura", model).z;
        }

        public partial class TrackBuilder
        {
            Transform kamakuraScenery;

            /// <summary>What a Kamakura layout places beside the lane (one holder, batched with the street).</summary>
            Transform KamakuraScenery()
            {
                if (kamakuraScenery == null)
                {
                    kamakuraScenery = new GameObject("KamakuraScenery").transform;
                    kamakuraScenery.SetParent(root, false);
                    kamakuraScenery.gameObject.AddComponent<StaticBatcher>();
                }
                return kamakuraScenery;
            }

            /// <summary>
            /// A Kamakura kit model at the layout's <paramref name="x"/>, its street face at the layout's <paramref name="front"/>
            /// (moved back by <see cref="KamakuraDepth"/>), facing the camera, or turned by <paramref name="yaw"/> 90 (its length in
            /// depth, its near end at the front: the tram). Null when the kit hasn't got it (the level is built without it).
            /// </summary>
            public Transform KmModel(string model, float x, float front, float yaw = 0f, float groundTop = 0f)
            {
                if (!HasKitModel("Kamakura", model)) return null;
                float z = Mathf.Abs(yaw - 90f) < 1f
                    ? front + KamakuraDepth + KitSize("Kamakura", model).x * 0.5f
                    : KamakuraZ(model, front);
                return KitModel(KamakuraScenery(), "Kamakura", model, new Vector3(x, groundTop, z), yaw);
            }

            /// <summary>
            /// A stand-in for what is still to come (a layout's marker): a plain box in its colour, its street face at the layout's
            /// <paramref name="front"/>. A wall or fence the cat may sit on is a <paramref name="catWall"/> (StreetBuilder's wall tops).
            /// </summary>
            public void KmStandIn(string what, float x, float front, float width, float depth, float height, Color colour,
                bool catWall = false, float groundTop = 0f)
            {
                float z = front + KamakuraDepth + depth * 0.5f;
                StreetBuilder.Solid(KamakuraScenery(), what, new Vector3(x, groundTop + height * 0.5f, z), new Vector3(width, height, depth), colour);
                if (catWall) KamakuraWalls.Add(new Vector4(x - width * 0.5f, x + width * 0.5f, groundTop + height, z));
            }

            /// <summary>Walls a cat may sit on (from x, to x, their top, their z), for StreetBuilder.Kamakura's wildlife.</summary>
            public readonly List<Vector4> KamakuraWalls = new List<Vector4>();

            /// <summary>
            /// KM1-1's first-graders walking to school (docs/KAMAKURA_BUILD.md, KM-C01 and KM-C02): <paramref name="count"/> of them
            /// in a loose line from <paramref name="fromX"/> to <paramref name="toX"/>, boys and girls in turn, each dressed from the
            /// first-graders' wardrobe (their yellow caps kept), walking to school ahead of the kid at one slow pace
            /// (Hazards.Pedestrian.toSchool: always toward school, never stooped or at a phone, all setting off together as the
            /// view comes near, so the kid catches up with the line): solid to the ball, the kid slips past them. Six-year-olds:
            /// a 1.25 m capsule (FirstGraderNeck, docs/LEARNINGS.md C13).
            /// </summary>
            public void FirstGraderLine(float fromX, float toX, int count, float groundTop = 0f, float speed = 0.7f)
            {
                Coaching.Mark("people", fromX, toX);
                float step = (toX - fromX) / Mathf.Max(1, count);
                for (int i = 0; i < count; i++)
                    FirstGrader(fromX + i * step, fromX + i * step + step * 0.8f, fromX, FirstGraders[i % FirstGraders.Length], i, groundTop, speed);
            }

            void FirstGrader(float minX, float maxX, float lineFrom, Passerby who, int k, float groundTop, float speed)
            {
                string bodyModel;
                Material look;
                float neck;
                var whom = who;
                GrownUpLook(ref whom, out bodyModel, out look, out neck);
                if (whom == null) return;                      // the first-graders' models aren't in: no stand-in grown-up
                var go = new GameObject("FirstGrader");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(minX, groundTop + 0.625f);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<CapsuleCollider2D>();
                col.size = new Vector2(0.4f, 1.25f);
                int seed = Mathf.Abs(Mathf.RoundToInt(minX * 37f)) + k * 17 + 1;
                var parts = BuildModelCharacter(go.transform, bodyModel, look, neck, new Vector3(0f, -0.625f + 0.6f * neck / 1.3f, 0.75f), false);
                if (parts.rig == null)
                {
                    Object.DestroyImmediate(go);
                    return;
                }
                var dress = (ModelOutfit)parts.outfit;
                dress.dressOnStart = true;
                dress.shirt = who.tops[(seed / 3) % who.tops.Length];
                dress.legwear = who.legwears[(seed / 7) % who.legwears.Length];
                dress.hair = who.thirds[(seed / 11) % who.thirds.Length];     // the randoseru
                var p = go.AddComponent<Hazards.Pedestrian>();
                p.minX = minX;
                p.maxX = maxX;
                p.walkSpeed = speed;
                p.toSchool = true;
                p.lineFrom = lineFrom;
                p.visual = parts.visual;
                p.seed = seed;
                p.outfit = parts.outfit;
                p.rig = parts.rig;
                p.coats = new Color[0];                         // the same clothes on every pass: a line of schoolchildren
                p.legwears = new Color[0];
                parts.rig.gameObject.AddComponent<WalkerAnimator>().pedestrian = p;
            }

            /// <summary>
            /// A level crossing across the footpath from <paramref name="fromX"/> to <paramref name="toX"/> (KM1-1's, by Hase):
            /// the tracks run away from the camera, their rails across the lane; the bells and lamps either side (KmCrossingSignal),
            /// the barriers (KmCrossingBarrier, their arms coming down along the lane behind it, each away from the tracks, so
            /// the tram passes clear of them, and never toward the camera: docs/LEARNINGS.md E10, E13), and the tram (KmTram) as the crossing's traffic, coming down the tracks toward the camera and
            /// on over the road. On the rails while the lamps flash, the kid or the ball loses the ball (Hazards.Crossing). The
            /// tracks are their own list (<see cref="Rails"/>, docs/LEARNINGS.md E11), not a side street's open area.
            /// </summary>
            public void LevelCrossing(float fromX, float toX, float phaseOffset = 0f, float groundTop = 0f)
            {
                float width = toX - fromX, center = (fromX + toX) * 0.5f;
                Coaching.Mark("crossing", fromX, toX);
                Rails.Add(new Vector2(fromX, toX));
                QuietAreas.Add(new Vector2(fromX - 1.5f, toX + 1.5f));

                // the track bed and the two rails, from the far side of the street to the road
                var bed = new GameObject("Tracks").transform;
                bed.SetParent(KamakuraScenery(), false);
                StreetBuilder.Solid(bed, "TrackBed", new Vector3(center, groundTop + 0.006f, 12f), new Vector3(2.4f, 0.012f, 44f), new Color(0.3f, 0.28f, 0.26f));
                foreach (float rx in new[] { center - 0.53f, center + 0.53f })
                    StreetBuilder.Solid(bed, "Rail", new Vector3(rx, groundTop + 0.03f, 12f), new Vector3(0.07f, 0.06f, 44f), new Color(0.55f, 0.52f, 0.5f));

                var go = new GameObject("LevelCrossing");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(center, groundTop + 1.25f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(width, 2.5f);
                var gate = go.AddComponent<Crossing>();
                gate.phaseOffset = phaseOffset;
                gate.loseKey = "lose.tram";
                // Time to cross, the bells, then the tram's long pass.
                gate.greenTime = 4.5f;
                gate.amberTime = 1.6f;
                gate.redTime = 5f;
                gate.queueGap = 30f;

                // the tram, 12 m long, its length along the tracks: it stops short of the crossing behind the barriers' line
                var tram = new GameObject("Tram").transform;
                tram.SetParent(go.transform, false);
                tram.position = new Vector3(center, groundTop, 60f);
                var model = KitModel(tram, "Kamakura", "KmTram", tram.position, 90f);
                gate.cars = new Transform[1];
                if (model != null) gate.cars[0] = tram;
                else
                {
                    Object.DestroyImmediate(tram.gameObject);
                    gate.cars[0] = Car(go.transform, "TramStandIn", new Vector3(center, groundTop, 60f), 90f, new Color(0.3f, 0.55f, 0.38f), "Van");
                }
                gate.groundY = groundTop;
                gate.stopLineZ = StreetBuilder.PathHalf + 8f;
                gate.farZ = 70f;
                gate.exitZ = -30f;

                // the bells and lamps either side, and the barriers whose arms come down while they flash
                KmModel("KmCrossingSignal", fromX - 1.1f, 0.95f, 0f, groundTop);
                KmModel("KmCrossingSignal", toX + 1.1f, 0.95f, 0f, groundTop);
                var arms = new List<Transform>();
                var downs = new List<float>();
                var near = KmModel("KmCrossingBarrier", fromX - 0.1f, 0.95f, 0f, groundTop);
                var far = KmModel("KmCrossingBarrier", toX + 0.1f, 0.95f, 0f, groundTop);
                foreach (var b in new[] { near, far })
                {
                    if (b == null) continue;
                    var arm = FindDeep(b, "Arm");
                    if (arm == null) continue;
                    arm.SetParent(go.transform, true);         // out of the street's static batch: it moves
                    arms.Add(arm);
                    // each comes down along the lane, away from the tracks: an arm about 2.9 m long lowered toward them would
                    // reach into the tram's path (docs/LEARNINGS.md E13)
                    downs.Add(b == near ? 90f : -90f);
                }
                if (arms.Count > 0)
                {
                    var lowering = go.AddComponent<CrossingArms>();
                    lowering.crossing = gate;
                    lowering.arms = arms.ToArray();
                    lowering.downAngles = downs.ToArray();
                }
            }

            /// <summary>Where tracks cross the street (<see cref="LevelCrossing"/>): the street keeps its houses and walls out of them.</summary>
            public readonly List<Vector2> Rails = new List<Vector2>();
        }
    }
}
