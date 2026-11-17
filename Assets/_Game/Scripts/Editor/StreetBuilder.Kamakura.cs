using System.Linq;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's street (LevelBuildKit.Kamakura): what its levels' layouts don't place themselves. The layouts (KamakuraLevels)
    /// place the Kamakura kit's models along the lane by the proposed layouts in review/kamakura/levels; this adds the ground
    /// behind the footpath they stand on, the green hills behind Hase, the cat on the block wall, the kid's home at the door
    /// (KM-B01) and Hase Station at the stop (its ticket gate, platform and name board). Nothing of the original town's street
    /// (its houses, gardens, poles and birds) is built in a Kamakura level.
    /// </summary>
    public static partial class StreetBuilder
    {
        static bool KM { get { return LevelBuildKit.Kamakura; } }

        /// <summary>The stops of the cities' routes (Levels/CityRoutes) that <see cref="StopFront"/> has a set piece for, beside <see cref="SetPieces"/> (the original town's).</summary>
        public static readonly string[] CitySetPieces =
        {
            "hase", "kamakuraStation", "shrineSideGate", "boardwalk", "grandmasShop", "lifeguardTower", "greatTorii", "trailSign",
            "genjiyama",
        };

        /// <summary>The street of a Kamakura level, in place of the chapter's (see <see cref="Scenery"/>).</summary>
        static void KamakuraStreet(LevelBuildKit.TrackBuilder track, Transform root)
        {
            // A Holiday Run stage (chunk) covers exactly its own stretch, so the next stage's ground and hills meet it and never
            // overlap it (two faces in one place flicker); a level's reach well past both ends.
            bool stage = chunk != null;
            float x0 = stage ? chunk.from : track.MinX - 50f, x1 = stage ? chunk.to : track.MaxX + 50f, mid = (x0 + x1) * 0.5f;
            critters = new GameObject("Critters").transform;
            wallTops.Clear();
            // the ground behind the footpath, paving and gravel, that the houses, walls and plants stand on
            Solid(root, "Frontage", new Vector3(mid, -0.02f, PropertyZ + 20f), new Vector3(x1 - x0, 0.04f, 40f), new Color(0.6f, 0.58f, 0.55f));
            // the wooded hills behind Hase, far back, and the sky's haze over them
            Solid(root, "Hills", new Vector3(mid, 7f, 75f), new Vector3(x1 - x0 + (stage ? 0f : 120f), 14f, 6f), new Color(0.3f, 0.42f, 0.3f));
            Solid(root, "HillsFar", new Vector3(mid + (stage ? 0f : 20f), 11f, 110f), new Vector3(x1 - x0 + (stage ? 0f : 200f), 22f, 6f),
                new Color(0.46f, 0.56f, 0.52f));

            // the ginger cat on the block wall (KM1-1's hazard in the reference: WallCat), Kamakura's own (KM-N01) where its kit
            // has it, else the Animals kit's cat in its colours; facing the way the kid comes
            var walls = track.KamakuraWalls.ToArray();
            if (walls.Length > 0)
            {
                var rng = new System.Random(1101);
                var w = walls[0];
                var holder = Holder("Cat", Mathf.Lerp(w.x, w.y, 0.25f), w.z, w.w, 180f + Rand(rng, -10f, 10f));
                var game = LevelBuildKit.KmGame("KmCatWalking");
                Transform model = game != null ? KmAnimal(holder, "KmCatWalking") : null;
                Vector3 tailAxis = game != null ? LevelBuildKit.KmAxis(LevelBuildKit.KmText(game, "tailAxis")) : Vector3.up;
                if (model == null) model = Animal(holder, "Cat", 1f, new Color(0.86f, 0.52f, 0.22f), new Color(0.97f, 0.93f, 0.86f));
                if (model == null) Object.DestroyImmediate(holder.gameObject);
                else
                {
                    var cat = holder.gameObject.AddComponent<WallCat>();
                    cat.seed = rng.Next();
                    cat.model = model;
                    cat.tail = PartOf(model, "Tail", tailAxis);
                    cat.walls = walls;
                    cat.wall = 0;
                }
            }
            KamakuraCritters(track);
        }

        // ---------------------------------------------------------------- Kamakura's own animals (KamakuraAnimals)

        /// <summary>The strip a Kamakura leg's animals keep to: the footpath's back edge to just before the lane's pictures.</summary>
        const float KmStripNear = PathHalf + 0.1f, KmStripFar = PathHalf + 0.55f, KmStripTop = 0.01f;   // (KM1-1's block wall's face at 2.15)

        /// <summary>A Kamakura animal under the holder, at its origin and turned with it (null if the kit hasn't got it).</summary>
        static Transform KmAnimal(Transform holder, string model)
        {
            var t = LevelBuildKit.KitModel(holder, LevelBuildKit.KmAnimalsKit, model, holder.position);
            if (t == null) return null;
            t.localPosition = Vector3.zero;
            t.localRotation = Quaternion.identity;
            return t;
        }

        /// <summary>
        /// The animals a Kamakura leg asks for (TrackBuilder.KmAnimals): each spread over its stretch on the strip before the lane's
        /// pictures, turned to show the flank its photograph has, and moved by the behaviour its manifest names, with the
        /// settings its review played (tools/blender/kit_animals_km.py): GroundBird, CritterIdle or FlitButterfly; still if none.
        /// </summary>
        static void KamakuraCritters(LevelBuildKit.TrackBuilder track)
        {
            var rng = new System.Random(1301);
            foreach (var c in track.KamakuraCritters)
                for (int i = 0; i < c.count; i++)
                {
                    float x = c.count == 1 ? (c.fromX + c.toX) * 0.5f : Mathf.Lerp(c.fromX, c.toX, (i + Rand(rng, 0.25f, 0.75f)) / c.count);
                    KmCritter(c.model, x, Rand(rng, KmStripNear, KmStripFar), rng);
                }
        }

        /// <summary>A bird's flight where Kamakura's kit has no flying model of it: the Animals kit's gull in its colours, at its span.</summary>
        struct KmFlight
        {
            public Color wing, beak;
            public float span;
            public KmFlight(Color wing, Color beak, float span) { this.wing = wing; this.beak = beak; this.span = span; }
        }

        static readonly System.Collections.Generic.Dictionary<string, KmFlight> KmFlights = new System.Collections.Generic.Dictionary<string, KmFlight>
        {
            { "Pigeon", new KmFlight(new Color(0.55f, 0.58f, 0.66f), new Color(0.32f, 0.3f, 0.32f), 0.7f) },
            { "Crow", new KmFlight(new Color(0.12f, 0.12f, 0.14f), new Color(0.1f, 0.1f, 0.1f), 0.9f) },
            { "Gull", new KmFlight(new Color(0.85f, 0.86f, 0.88f), new Color(0.9f, 0.75f, 0.2f), 1.1f) },
            { "Egret", new KmFlight(new Color(0.96f, 0.96f, 0.94f), new Color(0.15f, 0.15f, 0.15f), 0.95f) },
            { "Heron", new KmFlight(new Color(0.6f, 0.62f, 0.66f), new Color(0.85f, 0.7f, 0.3f), 1.5f) },
            { "Wagtail", new KmFlight(new Color(0.2f, 0.2f, 0.22f), new Color(0.1f, 0.1f, 0.1f), 0.3f) },
        };

        /// <summary>The kit's own flying model of a standing bird (the sparrow's, the dove's...), or null.</summary>
        static string KmFlyer(string standing)
        {
            foreach (string kind in new[] { "Sparrow", "Dove", "WhiteEye", "Bulbul", "Swallow" })
                if (standing.StartsWith("Km" + kind) && LevelBuildKit.HasKitModel(LevelBuildKit.KmAnimalsKit, "Km" + kind + "Flying"))
                    return "Km" + kind + "Flying";
            return null;
        }

        static void KmCritter(string model, float x, float z, System.Random rng)
        {
            var game = LevelBuildKit.KmGame(model);
            string component = LevelBuildKit.KmText(game, "component");
            var holder = Holder(model, x, KmStripTop, z, Rand(rng, -12f, 12f));
            var standing = KmAnimal(holder, model);
            if (standing == null)
            {
                Object.DestroyImmediate(holder.gameObject);
                return;
            }
            if (component == "GroundBird") KmGroundBird(holder, standing, model, game, x, z, rng);
            else if (component == "CritterIdle") KmIdle(holder, standing, game);
            else if (component == "FlitButterfly") KmFlit(holder, standing, game, x, z, rng);
            // else: still (a sleeping cat, a cormorant drying its wings): nothing of it moves
        }

        static void KmGroundBird(Transform holder, Transform standing, string model, System.Collections.Generic.Dictionary<string, object> game,
            float x, float z, System.Random rng)
        {
            var bird = holder.gameObject.AddComponent<GroundBird>();
            bird.seed = rng.Next();
            bird.standing = standing;
            string flyer = KmFlyer(model);
            if (flyer != null)
            {
                var fg = LevelBuildKit.KmGame(flyer);
                var flying = KmAnimal(holder, flyer);
                Vector3 wingAxis = LevelBuildKit.KmAxis(LevelBuildKit.KmText(fg, "wingAxis"));
                bird.flying = flying;
                bird.wingA = PartOf(flying, "WingR", wingAxis);
                bird.wingB = PartOf(flying, "WingL", wingAxis);
                bird.wingUp = LevelBuildKit.KmNumber(fg, "wingUp", bird.wingUp);
                bird.wingDown = LevelBuildKit.KmNumber(fg, "wingDown", bird.wingDown);
                bird.wingFold = LevelBuildKit.KmNumber(fg, "wingFold", bird.wingFold);
                bird.wingSweep = LevelBuildKit.KmNumber(fg, "wingSweep", bird.wingSweep);
                bird.wingSweepAxis = LevelBuildKit.KmAxis(LevelBuildKit.KmText(fg, "wingSweepAxis"));
                string tail = LevelBuildKit.KmText(fg, "flyingTail");
                if (tail != null) bird.flyingTail = PartOf(flying, tail, LevelBuildKit.KmAxis(LevelBuildKit.KmText(fg, "flyingTailAxis")));
            }
            else
            {
                // the Animals kit's gull in the bird's colours (as the original town's pigeons fly)
                var look = new KmFlight(new Color(0.85f, 0.86f, 0.88f), new Color(0.9f, 0.75f, 0.2f), 0.8f);
                foreach (var kv in KmFlights)
                    if (model.StartsWith("Km" + kv.Key)) look = kv.Value;
                float span = look.span;
                var flying = LevelBuildKit.KitModel(holder, "Animals", "Seagull", holder.position, 0f, span, look.wing, look.beak);
                if (flying != null)
                {
                    flying.localPosition = new Vector3(0f, 0.16f * span, 0f);
                    flying.localRotation = Quaternion.identity;
                }
                bird.flying = flying;
                bird.wingA = PartOf(flying, "WingR", Vector3.right);
                bird.wingB = PartOf(flying, "WingL", Vector3.right);
            }
            if (bird.flying == null)
            {
                Object.DestroyImmediate(bird);
                return;
            }
            bird.flying.gameObject.SetActive(false);
            Vector3 headAxis = LevelBuildKit.KmAxis(LevelBuildKit.KmText(game, "headAxis"));
            bird.head = PartOf(standing, LevelBuildKit.KmText(game, "head") ?? "Head", headAxis);
            bird.hopper = LevelBuildKit.KmFlag(game, "hopper");
            bird.headSlide = LevelBuildKit.KmNumber(game, "headSlide", bird.headSlide);
            bird.headNod = LevelBuildKit.KmNumber(game, "headNod", bird.headNod);
            bird.peckTurn = LevelBuildKit.KmNumber(game, "peckTurn", bird.peckTurn);
            bird.peckTip = LevelBuildKit.KmNumber(game, "peckTip", bird.peckTip);
            string tailName = LevelBuildKit.KmText(game, "tail"), plume = LevelBuildKit.KmText(game, "plume");
            if (tailName != null)
            {
                bird.tail = PartOf(standing, tailName, LevelBuildKit.KmAxis(LevelBuildKit.KmText(game, "tailAxis")));
                bird.tailPump = LevelBuildKit.KmNumber(game, "tailPump", bird.tailPump);
                bird.tailPumpRate = LevelBuildKit.KmNumber(game, "tailPumpRate", bird.tailPumpRate);
            }
            if (plume != null) bird.plume = PartOf(standing, plume, LevelBuildKit.KmAxis(LevelBuildKit.KmText(game, "plumeAxis")));
            bird.baseY = KmStripTop;
            bird.homeX = x;
            bird.homeZ = z;
            bird.zMin = KmStripNear;
            bird.zMax = KmStripFar;
            bird.roam = 1.2f;
            // it flies off along the street, in front of the lane's pictures (behind them it would vanish into the photograph)
            bird.flightZMin = KmStripNear;
            bird.flightZMax = KmStripFar;
            bird.ground = new[] { KmStripTop };
        }

        static void KmIdle(Transform holder, Transform standing, System.Collections.Generic.Dictionary<string, object> game)
        {
            object list;
            var motions = new System.Collections.Generic.List<CritterIdle.Motion>();
            if (game != null && game.TryGetValue("motions", out list) && list is System.Collections.Generic.List<object>)
                foreach (var o in (System.Collections.Generic.List<object>)list)
                {
                    var m = o as System.Collections.Generic.Dictionary<string, object>;
                    var part = LevelBuildKit.FindDeep(standing, LevelBuildKit.KmText(m, "part") ?? "");
                    if (part == null) continue;
                    motions.Add(new CritterIdle.Motion
                    {
                        part = part,
                        axis = LevelBuildKit.KmAxis(LevelBuildKit.KmText(m, "axis")),
                        amplitude = LevelBuildKit.KmNumber(m, "amplitude", 10f),
                        speed = LevelBuildKit.KmNumber(m, "speed", 1f),
                        snap = LevelBuildKit.KmFlag(m, "snap"),
                    });
                }
            if (motions.Count == 0) return;
            var idle = holder.gameObject.AddComponent<CritterIdle>();
            idle.motions = motions.ToArray();
        }

        static void KmFlit(Transform holder, Transform model, System.Collections.Generic.Dictionary<string, object> game, float x, float z,
            System.Random rng)
        {
            Vector3 axis = LevelBuildKit.KmAxis(LevelBuildKit.KmText(game, "wingAxis"));
            var b = holder.gameObject.AddComponent<FlitButterfly>();
            b.seed = rng.Next();
            b.wingL = PartOf(model, LevelBuildKit.KmText(game, "wingL") ?? "WingL", axis);
            b.wingR = PartOf(model, LevelBuildKit.KmText(game, "wingR") ?? "WingR", axis);
            string hindL = LevelBuildKit.KmText(game, "hindL"), hindR = LevelBuildKit.KmText(game, "hindR");
            if (hindL != null) b.hindL = PartOf(model, hindL, axis);
            if (hindR != null) b.hindR = PartOf(model, hindR, axis);
            b.hindLead = LevelBuildKit.KmNumber(game, "hindLead", b.hindLead);
            b.beatMid = LevelBuildKit.KmNumber(game, "beatMid", b.beatMid);
            b.beatSwing = LevelBuildKit.KmNumber(game, "beatSwing", b.beatSwing);
            float y = Rand(rng, 0.6f, 1.2f);
            holder.position = new Vector3(x, y, z);
            b.homeX = x;
            b.homeY = y;
            b.homeZ = z;
            b.zMin = KmStripNear;
            b.zMax = KmStripFar;
            b.rise = 0.6f;
            b.roam = Rand(rng, 2f, 3.2f);
            b.speed = Rand(rng, 0.5f, 0.85f);
        }

        /// <summary>The kid's home in Kamakura (KM-B01, the photographic KM1-1's house and its fence), its entrance at the gate.</summary>
        static void HomeFrontKM(Transform parent, float gx, float gy)
        {
            LevelBuildKit.KitModel(parent, "Kamakura", "KmHome", new Vector3(gx, gy, LevelBuildKit.KamakuraZ("KmHome", 1.6f)));
        }

        /// <summary>
        /// Hase Station (KM1-1's stop, review/kamakura/levels/KM1-1/layout.json): its ticket gate at the stop's door, where the kid
        /// finishes, the platform beyond it along the tracks' side and the station's name board at its far end.
        /// </summary>
        static void HaseStation(Transform parent, float gx, float gy)
        {
            Kamakura(parent, "KmTicketGate", gx, gy, 1.3f);
            Kamakura(parent, "KmStationPlatform", gx + 5.4f, gy, 2.3f);
            Kamakura(parent, "KmStationSign", gx + 11.4f, gy, 1.4f);
        }

        /// <summary>A Kamakura kit model at x, its street face at a layout's <paramref name="front"/>.</summary>
        static Transform Kamakura(Transform parent, string model, float x, float gy, float front)
        {
            if (!LevelBuildKit.HasKitModel("Kamakura", model)) return null;
            return LevelBuildKit.KitModel(parent, "Kamakura", model, new Vector3(x, gy, LevelBuildKit.KamakuraZ(model, front)));
        }
    }
}
