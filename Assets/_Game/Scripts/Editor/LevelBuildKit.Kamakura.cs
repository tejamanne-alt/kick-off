using System.Collections.Generic;
using DribbleToSchool.Core;
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

        // ------------------------------------------------------------------ Kamakura's animals (Art/Models/KamakuraAnimals)

        /// <summary>Kamakura's animals (tools/blender/kit_animals_km.py, KM-N01 to N28): each one skinned mesh on its bones.</summary>
        public const string KmAnimalsKit = "KamakuraAnimals";

        /// <summary>
        /// An axis as a Kamakura animal's manifest names it ("side", "long", "up"), in the model's own axes as the kit's FBX
        /// brings every part and bone (along the body x, across it y, up z): the axes the Animals kit's behaviours already use
        /// (a dog's legs swing about y, a gull's wings beat about x, a head looks about z).
        /// </summary>
        public static Vector3 KmAxis(string name)
        {
            switch (name)
            {
                case "long": return Vector3.right;
                case "up": return Vector3.forward;
                default: return Vector3.up;
            }
        }

        /// <summary>How the game moves a Kamakura animal: its manifest's "game" entry (its behaviour and settings, as its review played them), or null.</summary>
        public static Dictionary<string, object> KmGame(string model)
        {
            var info = KitInfo(KmAnimalsKit, model);
            object g;
            return info != null && info.TryGetValue("game", out g) ? g as Dictionary<string, object> : null;
        }

        /// <summary>A text setting of a Kamakura animal's "game" entry, or null.</summary>
        public static string KmText(Dictionary<string, object> game, string key)
        {
            object v;
            return game != null && game.TryGetValue(key, out v) ? v as string : null;
        }

        /// <summary>A number setting of a Kamakura animal's "game" entry, or <paramref name="fallback"/>.</summary>
        public static float KmNumber(Dictionary<string, object> game, string key, float fallback)
        {
            object v;
            if (game == null || !game.TryGetValue(key, out v) || v == null || v is string || v is bool) return fallback;
            return System.Convert.ToSingle(v);
        }

        /// <summary>A yes-or-no setting of a Kamakura animal's "game" entry.</summary>
        public static bool KmFlag(Dictionary<string, object> game, string key)
        {
            object v;
            return game != null && game.TryGetValue(key, out v) && v is bool && (bool)v;
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

            /// <summary>Some of Kamakura's animals a leg asks for (<see cref="KmAnimals"/>).</summary>
            public struct KmCritter
            {
                public string model;
                public float fromX, toX;
                public int count;
            }

            /// <summary>The animals the leg asks for, placed by StreetBuilder.Kamakura.</summary>
            public readonly List<KmCritter> KamakuraCritters = new List<KmCritter>();

            /// <summary>
            /// <paramref name="count"/> of a Kamakura animal (<paramref name="model"/>, KamakuraAnimals) spread from
            /// <paramref name="fromX"/> to <paramref name="toX"/> on the ground between the footpath and the lane's pictures, each
            /// moved by the behaviour its manifest names (GroundBird, CritterIdle, FlitButterfly; still if none), as its review
            /// played it. Left out when the kit hasn't got it.
            /// </summary>
            public void KmAnimals(string model, float fromX, float toX, int count = 1)
            {
                if (!HasKitModel(KmAnimalsKit, model)) return;
                KamakuraCritters.Add(new KmCritter { model = model, fromX = fromX, toX = toX, count = count });
            }

            /// <summary>
            /// A Kamakura animal as the dog hazard (the Shiba KM-N04, the tanuki KM-N02): its jointed legs walked by World/LegGait,
            /// its tail and head moved about the axes its manifest gives. False if the kit hasn't got it.
            /// </summary>
            bool KamakuraDog(GameObject go, Transform visual, float minX, float maxX, string model)
            {
                var game = KmGame(model);
                if (game == null || KmText(game, "component") != "Dog") return false;
                var kit = KitModel(visual, KmAnimalsKit, model, visual.position + Vector3.down * 0.3f);
                if (kit == null) return false;
                string[] legNames = { "LegFR", "LegFL", "LegBR", "LegBL" };
                var legs = new Transform[legNames.Length];
                for (int i = 0; i < legNames.Length; i++)
                    if ((legs[i] = FindDeep(kit, legNames[i])) == null)
                    {
                        Object.DestroyImmediate(kit.gameObject);
                        return false;
                    }
                var hound = go.AddComponent<Hazards.Dog>();
                hound.minX = minX;
                hound.maxX = maxX;
                hound.visual = visual;
                hound.legs = legs;
                hound.legAxis = KmAxis("side");
                string tail = KmText(game, "tail"), head = KmText(game, "head");
                hound.tail = tail != null ? FindDeep(kit, tail) : null;
                hound.tailAxis = KmAxis(KmText(game, "tailAxis"));     // the Shiba's curled tail about its length (D20)
                hound.head = head != null ? FindDeep(kit, head) : null;
                hound.headNodAxis = KmAxis("side");
                hound.headTurnAxis = KmAxis("up");
                return true;
            }

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

            // ------------------------------------------------------------------ the lanes from the user's lane pictures

            /// <summary>
            /// A leg's lane from its lane pictures (tools/blender/km_lanes.py: KmLane&lt;leg&gt;A, B, C...): each picture's front
            /// upright behind the footpath, its ground laid from the footpath's back edge to it, side by side from
            /// <paramref name="x0"/> (the first picture's left edge), as the pictures continue one another. Returns the x where
            /// the last ends. A leg whose pictures aren't in the kit is built without them.
            /// </summary>
            public float KmLane(string leg, float x0)
            {
                string stem = "KmLane" + leg.Replace("-", "");
                float x = x0;
                for (char c = 'A'; c <= 'H'; c++)
                {
                    string model = stem + c;
                    if (!HasKitModel("Kamakura", model)) break;
                    float w = KitSize("Kamakura", model).x;
                    // its ground's near edge on the footpath's back edge (front 0.75, moved back by KamakuraDepth), a centimetre up
                    KmModel(model, x + w * 0.5f, StreetBuilder.PathHalf - KamakuraDepth, 0f, 0.01f);
                    x += w;
                }
                return x;
            }

            /// <summary>
            /// The June rain over the leg (World/RainFall: KM3's three legs, whose pictures are wet), in front of its pictures;
            /// in a Holiday Run stage only while the camera is over it (<paramref name="fromX"/> to <paramref name="toX"/>).
            /// </summary>
            public void Rain(float fromX = float.NegativeInfinity, float toX = float.PositiveInfinity)
            {
                var go = new GameObject("Rain");
                go.transform.SetParent(root, false);
                go.AddComponent<MeshFilter>();
                var r = go.AddComponent<MeshRenderer>();
                r.sharedMaterial = Art != null ? Art.wire : null;     // Sprites/Default: unlit, vertex colour, blended
                var rain = go.AddComponent<RainFall>();
                rain.fromX = fromX;
                rain.toX = toX;
            }

            /// <summary>
            /// A leg's lane pictures fitted into the stretch from <paramref name="from"/> to <paramref name="to"/> (a Holiday Run
            /// stage, HolidayRunBuilder): side by side, each scaled alike in height and length (a photograph keeps its
            /// proportions), the ground's near edge on the footpath's back edge as in the leg. False if the kit hasn't got them.
            /// </summary>
            public bool KmLaneFitted(string leg, float from, float to)
            {
                string stem = "KmLane" + leg.Replace("-", "");
                var models = new List<string>();
                float total = 0f;
                for (char c = 'A'; c <= 'H'; c++)
                {
                    string model = stem + c;
                    if (!HasKitModel("Kamakura", model)) break;
                    models.Add(model);
                    total += KitSize("Kamakura", model).x;
                }
                if (models.Count == 0 || total <= 0f) return false;
                float s = (to - from) / total, x = from;
                foreach (string model in models)
                {
                    float w = KitSize("Kamakura", model).x * s;
                    float z = StreetBuilder.PathHalf - KitMin("Kamakura", model).z * s;
                    KitModel(KamakuraScenery(), "Kamakura", model, new Vector3(x + w * 0.5f, 0.01f, z), 0f, s);
                    x += w;
                }
                return true;
            }

            // ------------------------------------------------------------------ the mini-games and the errand (MiniGames)

            /// <summary>A trigger across the lane at <paramref name="x"/>, <paramref name="width"/> wide, with a mini-game's component on it.</summary>
            T LaneTrigger<T>(string name, float x, float width, float groundTop) where T : Component
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(x, groundTop + 1.25f);
                var box = go.AddComponent<BoxCollider2D>();
                box.isTrigger = true;
                box.size = new Vector2(width, 2.5f);
                return go.AddComponent<T>();
            }

            /// <summary>
            /// KM1-2's ride (docs/CITIES.md M1): at Hase's ticket gate (<paramref name="x"/>) the ride opens over the level
            /// (MiniGames/TramRide, from the user's set pictures KM1-2a to c in Resources/UI/Kamakura); at Kamakura the leg is done.
            /// </summary>
            public void RideGate(float x, float groundTop = 0f)
            {
                Coaching.Mark("people", x - 1f, x + 1f);
                LaneTrigger<MiniGames.TramRide>("TramRide", x, 1.2f, groundTop);
            }

            /// <summary>
            /// KM2-3's errand (docs/CITIES.md M2): at Grandma's counter (<paramref name="x"/>) the errand opens over the level
            /// (MiniGames/BentoErrand); once the bento is wrapped it rides on the backpack (Progression/Errands).
            /// </summary>
            public void ErrandCounter(float x, float groundTop = 0f)
            {
                LaneTrigger<MiniGames.BentoErrand>("BentoErrand", x, 1.2f, groundTop);
            }

            /// <summary>
            /// The bento on the kid's backpack while the trip carries it (MiniGames/BentoOnBack): a lacquered box wrapped in its
            /// navy furoshiki, the knot on top and the rice ball beside it, built hidden, put on the kid's bag when carried.
            /// </summary>
            public void BentoOnBack()
            {
                var holder = new GameObject("BentoOnBack").transform;
                holder.SetParent(root, false);
                var bento = new GameObject("Bento").transform;
                bento.SetParent(holder, false);
                Color cloth = new Color(0.17f, 0.2f, 0.36f), band = new Color(0.72f, 0.36f, 0.24f), rice = new Color(0.96f, 0.95f, 0.9f);
                Blobs(bento, "Wrapped", Vector3.zero,
                    new BlobShape.Blob(Vector3.zero, new Vector3(0.13f, 0.07f, 0.1f), cloth),
                    new BlobShape.Blob(new Vector3(0f, 0.065f, 0f), new Vector3(0.05f, 0.03f, 0.04f), band),
                    new BlobShape.Blob(new Vector3(-0.045f, 0.075f, 0f), new Vector3(0.035f, 0.022f, 0.02f), band),
                    new BlobShape.Blob(new Vector3(0.045f, 0.075f, 0f), new Vector3(0.035f, 0.022f, 0.02f), band));
                var riceBall = Blobs(bento, "RiceBall", new Vector3(0.1f, 0.06f, 0f),
                    new BlobShape.Blob(Vector3.zero, new Vector3(0.045f, 0.04f, 0.035f), rice),
                    new BlobShape.Blob(new Vector3(0f, -0.018f, 0f), new Vector3(0.047f, 0.016f, 0.037f), new Color(0.1f, 0.14f, 0.1f)));
                bento.gameObject.SetActive(false);
                var on = holder.gameObject.AddComponent<MiniGames.BentoOnBack>();
                on.bento = bento.gameObject;
                on.riceBall = riceBall.gameObject;
            }

            /// <summary>
            /// KM2-4's twist (docs/CITIES.md M4): past <paramref name="triggerX"/> a black kite takes the rice ball off the bento and
            /// drops it on the rocks at <paramref name="dropX"/> behind; the wave comes in over it unless the kid gets back in time
            /// (MiniGames/KiteThief). The kite is the gull's shape in a black kite's browns; the wave a sheet of sea water.
            /// </summary>
            public void KiteThief(float triggerX, float dropX, float groundTop = 0f)
            {
                Coaching.Mark("seagull", dropX, triggerX);
                var go = new GameObject("KiteThief");
                go.transform.SetParent(root, false);
                var kite = new GameObject("Kite").transform;
                kite.SetParent(go.transform, false);
                Color brown = new Color(0.36f, 0.27f, 0.2f), pale = new Color(0.62f, 0.52f, 0.42f), dark = new Color(0.16f, 0.12f, 0.1f);
                Blobs(kite, "Body", Vector3.zero,
                    new BlobShape.Blob(Vector3.zero, new Vector3(0.3f, 0.1f, 0.1f), brown),
                    new BlobShape.Blob(new Vector3(0.26f, 0.06f, 0f), new Vector3(0.09f, 0.08f, 0.075f), pale),
                    new BlobShape.Blob(new Vector3(0.36f, 0.04f, 0f), new Vector3(0.05f, 0.025f, 0.02f), dark),
                    new BlobShape.Blob(new Vector3(-0.34f, 0.01f, 0f), new Vector3(0.14f, 0.025f, 0.09f), brown));
                var wings = new List<Transform>();
                foreach (float side in new[] { -1f, 1f })
                    wings.Add(Blobs(kite, "Wing", new Vector3(0f, 0.04f, side * 0.07f),
                        new BlobShape.Blob(new Vector3(-0.02f, 0f, side * 0.3f), new Vector3(0.16f, 0.02f, 0.3f), brown),
                        new BlobShape.Blob(new Vector3(-0.08f, 0f, side * 0.56f), new Vector3(0.1f, 0.016f, 0.1f), dark)).transform);
                var rice = Blobs(go.transform, "RiceBall", Vector3.zero,
                    new BlobShape.Blob(Vector3.zero, new Vector3(0.09f, 0.08f, 0.07f), new Color(0.96f, 0.95f, 0.9f)),
                    new BlobShape.Blob(new Vector3(0f, -0.035f, 0f), new Vector3(0.094f, 0.03f, 0.074f), new Color(0.1f, 0.14f, 0.1f))).transform;
                var wave = StreetBuilder.Solid(go.transform, "Wave", new Vector3(dropX, groundTop + 0.025f, 9f), new Vector3(5f, 0.05f, 4f),
                    new Color(0.42f, 0.68f, 0.78f)).transform;
                var thief = go.AddComponent<MiniGames.KiteThief>();
                thief.triggerX = triggerX;
                thief.dropX = dropX;
                thief.groundY = groundTop;
                thief.kite = kite;
                thief.wings = wings.ToArray();
                thief.rice = rice;
                thief.wave = wave;
            }

            /// <summary>
            /// A Kamakura leg that ends at school: the user's lane picture shows the school's gate there, so the goal is only the
            /// zone past the gate's line (the kid and the ball both through it), the street kept quiet beyond.
            /// </summary>
            void KamakuraSchoolGoal(float x, float groundTop)
            {
                GoalX = x;
                QuietAreas.Add(new Vector2(x - 1f, x + 200f));
                const float grounds = 40f;
                var goalGo = new GameObject("GoalZone");
                goalGo.transform.SetParent(root, false);
                goalGo.transform.position = new Vector3(x + 0.4f + grounds * 0.5f, groundTop + 8f, 0f);
                var trigger = goalGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(grounds, 20f);
                goalGo.AddComponent<GoalZone>();
            }
        }
    }
}
