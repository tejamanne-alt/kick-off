using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.Art;
using DribbleToSchool.Holiday;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The street scenery of a Holiday Run: one stage's 120 m at a time (<see cref="StageScenery"/>), laid
    /// end to end along the lap, and the distant land that all the stages share (<see cref="FarLand"/>, in the
    /// core scene).
    ///
    /// The story levels build one long street per scene. A stage must build exactly its own stretch, so the
    /// builders' loops (lots, shopfronts, hedges, rows of far buildings, poles) fit what is left of their run
    /// instead of overhanging the end, and the seams are made to look like places rather than cuts:
    /// every urban stage ends on a cross street (and the first one after the beach starts on one), the lots
    /// of the neighbouring stages stop at its kerbs, the street's own far end belongs to the stage that
    /// builds it, and the poles stand on one lattice for the whole lap so their wires meet. Where the
    /// chapter changes, the last lot before the street and the first after it dress themselves as the other
    /// chapter, and patches of the other chapter's surface are laid over the road for a few metres each side.
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>What a Holiday Run stage asks of the scenery.</summary>
        public sealed class StageSpec
        {
            public int stage;
            /// <summary>The stretch the scenery builds: a stage's own, padded at the ends of the world.</summary>
            public float from, to;
            public int seed;
            /// <summary>The chapters of the stages before and after this one (0: none), for the seams.</summary>
            public int prevChapter, nextChapter;
            /// <summary>Where the stage's first lot starts, and where the cross street at its end begins.</summary>
            public float firstLotX, endStreetFrom;
            /// <summary>Utility poles in the neighbouring stage too (their wires carry over the seam).</summary>
            public bool polesBefore, polesAfter;
            /// <summary>Birds crossing the sky (a few stages only: they are not tied to the stage).</summary>
            public bool flocks;
            /// <summary>The park clearing to put in: 0 a playground, 1 a duck pond, -1 as it comes.</summary>
            public int clearing = -1;
            /// <summary>Side streets' far ends are cut to this range (next to the beach, which has none).</summary>
            public float clipLo = float.NegativeInfinity, clipHi = float.PositiveInfinity;
            /// <summary>
            /// A story level's pass rather than a Holiday Run stage's: a level has no core scene, so this pass builds the distant land too
            /// (fields and hills, the sea and its headlands, the site's cranes), across the whole level as a level does.
            /// </summary>
            public bool level;
        }

        /// <summary>Non-null while a stage's scenery is being built.</summary>
        static StageSpec chunk;

        static float ClipLo { get { return chunk != null ? chunk.clipLo : float.NegativeInfinity; } }
        static float ClipHi { get { return chunk != null ? chunk.clipHi : float.PositiveInfinity; } }

        /// <summary>Loop bounds: a level's scenery runs on past its ends by <paramref name="pad"/>; a stage's stops at its own.</summary>
        static float Lo(float x0, float pad) { return chunk != null ? x0 : x0 - pad; }
        static float Hi(float x1, float pad) { return chunk != null ? x1 : x1 + pad; }
        /// <summary>A margin kept at a stage's ends (so what stands there doesn't overlap the neighbour's); none in a level.</summary>
        static float Margin(float m) { return chunk != null ? m : 0f; }

        /// <summary>The animals' holder of the scenery just built (the caller moves it into its scene root).</summary>
        public static Transform Critters { get { return critters; } }

        /// <summary>Utility poles stand every 21 m from the world's origin, in every stage, so their wires meet.</summary>
        public const float PoleSpacing = 21f;

        /// <summary>
        /// Everything beside the street for one Holiday Run stage: the chapter's lots, walls, shops or
        /// hedges along exactly [from, to], the pole line, the near trees' shade, the rows behind, the cross streets' far ends,
        /// the school and the wildlife, and the dressing of the seams. Call after the track's ground and
        /// side streets (OpenAreas, QuietAreas) are in.
        /// </summary>
        public static void StageScenery(LevelBuildKit.TrackBuilder track, Transform root, StageSpec spec)
        {
            if (!spec.level && spec.stage >= 0) levelSalt = 0;     // (a Holiday Run stage: its seeds are its own)
            int ch = LevelBuildKit.Chapter;
            chunk = spec;
            try
            {
                var rng = new System.Random(spec.seed);
                float x0 = spec.from, x1 = spec.to;
                critters = new GameObject("Critters").transform;
                wallTops.Clear();
                switch (ch)
                {
                    case 2: Market(track, root, rng, x0, x1); break;
                    case 3: Beach(track, root, rng, x0, x1); break;
                    case 4: City(track, root, rng, x0, x1); break;
                    case 5: Park(track, root, rng, x0, x1); break;
                    default: Suburb(track, root, rng, x0, x1); break;
                }
                if (ch != 3) Poles(track, root, x0, x1);
                if (ch != 3) CanopyShadows(track, root, new System.Random(spec.seed + 173), x0, x1);
                Depth(track, root, new System.Random(spec.seed + 211), x0, x1);
                if (ch != 3)
                    foreach (var area in track.OpenAreas.ToArray())
                    {
                        // A street belongs to the stage it is in (the previous stage's end street is only kept clear).
                        float centre = (area.x + area.y) * 0.5f;
                        if (centre >= x0 && centre <= x1) SideStreetEnd(track, root, new System.Random(ch * 53 + Mathf.RoundToInt(area.x * 3f)), area);
                    }
                SchoolSurroundings(track, root, new System.Random(ch * 97 + Mathf.RoundToInt(track.GoalX)));
                Wildlife(track, root, new System.Random(spec.seed + 389), x0, x1);
                SeamDressing(track, root, new System.Random(spec.seed + 577), spec);
            }
            finally
            {
                chunk = null;
            }
        }

        // ---------------------------------------------------------------- lots that fit

        /// <summary>
        /// Where the run of street that starts at x ends: at the next side street or quiet area (less the
        /// margin lots keep from it), else at <paramref name="limit"/>.
        /// </summary>
        static float RunEnd(LevelBuildKit.TrackBuilder track, float x, float limit)
        {
            float end = limit;
            foreach (var area in track.OpenAreas.Concat(track.QuietAreas))
            {
                float start = area.x - 0.6f;
                if (start > x - 0.001f && start < end) end = start;
            }
            return end;
        }

        /// <summary>
        /// The width of the next lot: a random one between min and max in a level. In a stage the lots of a run
        /// (up to the next side street or the stage's end) add up to the run exactly: the last one takes what
        /// is left, and the one before it is not left a scrap too small for a building.
        /// </summary>
        static float NextLot(LevelBuildKit.TrackBuilder track, System.Random rng, float x, float limit, float min, float max)
        {
            float lot = Rand(rng, min, max);
            if (chunk == null) return lot;
            float rest = RunEnd(track, x, limit) - x;
            if (rest <= max * 1.4f) return Mathf.Max(rest, 1f);
            return rest - lot < min ? rest * 0.5f : lot;
        }

        // ---------------------------------------------------------------- poles

        /// <summary>
        /// The stage's share of the pole line: the poles of the lap's lattice that stand in [x0, x1) and are
        /// not in a side street, with the street lamps between them. The wires run on to the pole just
        /// outside either end (the neighbour's first or last), which is not drawn here.
        /// </summary>
        static void PolesForStage(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            var go = new GameObject("PoleLine");
            go.transform.SetParent(root, false);
            var line = go.AddComponent<PoleLine3D>();
            line.wireMaterial = Art.wire;
            bool models = LevelBuildKit.HasKitModel("Street", "UtilityPole");

            if (models && chunk.polesBefore)
            {
                // The previous stage's last pole: the last on the lattice before its end street.
                float p = Mathf.Floor((x0 - 8.1f) / PoleSpacing) * PoleSpacing;
                line.poles.Add(new Vector3(p, GroundAt(track, p), PoleZ));
            }
            for (float x = Mathf.Ceil(x0 / PoleSpacing) * PoleSpacing; x < x1; x += PoleSpacing)
            {
                float skip;
                if (Blocked(track, x - 0.5f, x + 0.5f, out skip)) continue;
                var pole = new Vector3(x, GroundAt(track, x), PoleZ);
                line.poles.Add(pole);
                if (!models) continue;
                // The kit's concrete pole, turned side-on so its crossarm runs across the street like a
                // real line's; the wires hang from its insulators.
                var model = Model(go.transform, "Street", PoleModel, pole.x, pole.y, pole.z, PoleYaw);
                if (model == null || line.anchorOffsets.Count > 0) continue;
                foreach (var t in model.GetComponentsInChildren<Transform>())
                    if (t.name.StartsWith("Attach.Wire") || t.name.StartsWith("Attach_Wire"))
                        line.anchorOffsets.Add(t.position - pole);
            }
            if (models && chunk.polesAfter)
            {
                // The next stage's first pole: the first on the lattice past its start street.
                float p = Mathf.Ceil((x1 + 1.1f) / PoleSpacing) * PoleSpacing;
                line.poles.Add(new Vector3(p, GroundAt(track, p), PoleZ));
            }
            line.drawPoles = !models;
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            line.Rebuild();

            // Street lamps halfway between the poles (the swan neck reads from the side), a bin by some.
            if (!LevelBuildKit.HasKitModel("Street", "StreetLamp")) return;
            var rng = new System.Random(LevelBuildKit.Chapter * 53 + Mathf.RoundToInt(x0));
            for (float x = Mathf.Ceil((x0 - 10.5f) / PoleSpacing) * PoleSpacing + 10.5f; x < x1; x += PoleSpacing)
            {
                float skip;
                if (Blocked(track, x - 1.5f, x + 1.5f, out skip)) continue;
                float gy = GroundAt(track, x);
                Model(root, "Street", "StreetLamp", x, gy, PoleZ);
                if (rng.NextDouble() < 0.45) Model(root, "Street", "Bin", x + 0.7f, gy, PoleZ + 0.05f, Rand(rng, -10f, 10f));
            }
        }

        // ---------------------------------------------------------------- seams between chapters

        /// <summary>
        /// Which chapter's look the lot [x, x + w] should take on, or 0 for its own: the last lot before the
        /// end street dresses itself as the next chapter, the first one of a stage as the one before.
        /// </summary>
        static int TransitionStyle(float x, float w)
        {
            if (chunk == null) return 0;
            int own = LevelBuildKit.Chapter;
            if (chunk.nextChapter != 0 && chunk.nextChapter != own && x < chunk.endStreetFrom && x + w >= chunk.endStreetFrom - 0.7f) return chunk.nextChapter;
            if (chunk.prevChapter != 0 && chunk.prevChapter != own && x <= chunk.firstLotX + 0.5f) return chunk.prevChapter;
            return 0;
        }

        /// <summary>
        /// A lot dressed in another chapter's style, so one chapter bleeds into the next: stalls and banners
        /// where the town begins, palms and parasols where the beach does, site fencing, a hedge row with a
        /// lamp, a garden wall.
        /// </summary>
        static void ThemeLot(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, int style, float a, float b)
        {
            float gy = GroundAt(track, (a + b) * 0.5f), w = b - a, mid = (a + b) * 0.5f;
            switch (style)
            {
                case 2:
                    for (float sx = a + 1.6f; sx < b - 1.2f; sx += 3.1f)
                    {
                        if (Model(root, "Street", "MarketStall", sx, gy, PropertyZ + 0.6f, Rand(rng, -4f, 4f)) == null) break;
                        if (rng.NextDouble() < 0.5) Model(root, "Street", "ProduceCrate", sx + 1.5f, gy, PropertyZ + 0.1f, Rand(rng, -15f, 15f));
                    }
                    Banner(root, rng, a + 0.8f, gy);
                    Banner(root, rng, b - 0.8f, gy);
                    break;
                case 3:
                    for (float px = a + 1.5f; px < b - 1.5f; px += Rand(rng, 3.2f, 5f))
                        Plant(root, rng.NextDouble() < 0.5 ? "Palm" : "PalmShort", null, px, gy, PropertyZ + Rand(rng, 1.8f, 3.2f), Rand(rng, 0.85f, 1.1f), 1f, -60, rng);
                    for (float gx = a; gx < b; gx += Rand(rng, 1f, 2.2f))
                        Plant(root, "DuneGrass", null, gx, gy, PropertyZ + Rand(rng, 0.3f, 0.9f), Rand(rng, 0.8f, 1.2f), 1f, -50, rng);
                    Model(root, "Leisure", "Parasol", mid, gy, PropertyZ + 3.6f, Rand(rng, 0f, 360f), 1f, new Color(0.9f, 0.3f, 0.28f));
                    Model(root, "Leisure", "BeachTowel", mid + 0.2f, gy, PropertyZ + 2.6f, 90f, 1f, new Color(0.45f, 0.75f, 0.9f));
                    break;
                default:
                    // The chapter's own way of closing a gap (a garden wall, a hoarding, a hedge), with what stands about it.
                    int saved = LevelBuildKit.Chapter;
                    LevelBuildKit.Chapter = style;
                    try { FillGap(track, root, rng, a, b); }
                    finally { LevelBuildKit.Chapter = saved; }
                    if (style == 4)
                    {
                        Model(root, "Street", "RoadBarrier", a + w * 0.3f, gy, PropertyZ - 0.3f, Rand(rng, -6f, 6f));
                        Model(root, "Street", "TrafficCone", a + w * 0.3f + 1.3f, gy, PropertyZ - 0.2f, Rand(rng, 0f, 360f));
                        Model(root, "Street", "Pallet", b - 2.2f, gy, PropertyZ + 0.9f, Rand(rng, -20f, 20f));
                    }
                    else if (style == 5)
                    {
                        Model(root, "Leisure", "ParkLamp", a + 0.6f, gy + 0.04f, PropertyZ - 0.1f);
                        Model(root, "Street", "Bench", mid, gy + 0.04f, PropertyZ - 0.55f);
                    }
                    else if (style == 1)
                    {
                        Model(root, "Street", "BinPair", mid + 1.5f, gy, PropertyZ + 0.55f, Rand(rng, -10f, 10f));
                        Model(root, "Street", "PostBox", a + 1f, gy, PoleZ - 0.1f);
                    }
                    break;
            }
        }

        /// <summary>The surface a chapter's road or lane in front of the footpath is made of.</summary>
        static ProceduralArt.Surface FrontSurface(int chapter)
        {
            switch (chapter)
            {
                case 2: return ProceduralArt.Surface.Cobbles;
                case 3: return ProceduralArt.Surface.Sand;
                case 4: return ProceduralArt.Surface.Concrete;
                case 5: return ProceduralArt.Surface.Grass;
                default: return ProceduralArt.Surface.Asphalt;
            }
        }

        /// <summary>Height of the surface in front of the footpath in a chapter (the road is sunk, the park's lawn raised a little).</summary>
        static float FrontHeight(int chapter)
        {
            switch (chapter)
            {
                case 2: return -0.06f;
                case 5: return 0.04f;
                case 3: return 0f;
                default: return -0.14f;
            }
        }

        /// <summary>
        /// Ragged patches of another chapter's surface over the road in front, thickening toward the seam: the
        /// stage before it lays the next chapter's, the stage after it the last chapter's, so the two meet in a
        /// mosaic rather than a cut. <paramref name="side"/> is -1 when the seam is at the stage's end.
        /// </summary>
        static void Feather(Transform root, System.Random rng, int own, int other, float seamX, int side, float limitLo, float limitHi)
        {
            if (own == 3 || other == own) return;
            var material = Art.surfaces[FrontSurface(other)];
            float y = FrontHeight(own);
            bool road = own == 1 || own == 4;
            float zLo = road ? RoadFar + 0.15f : -9f, zHi = road ? RoadNear - 0.15f : -PathHalf - 0.1f;
            const int count = 11;
            for (int i = 0; i < count; i++)
            {
                float t = (i + (float)rng.NextDouble()) / count;
                float dist = 15f * (1f - t * t);
                float len = Rand(rng, 1.3f, 3.4f) * (0.55f + 0.9f * t);
                float a = side < 0 ? seamX - dist - len : seamX + dist;
                float b = a + len;
                if (a < limitLo || b > limitHi) continue;
                float z0 = Rand(rng, zLo, zHi - 1.2f), z1 = Mathf.Min(zHi, z0 + Rand(rng, 1.4f, 4.4f));
                Patch(root, "Feather", a, b, y, z0, z1, Color.white, material, 0.02f);
            }
        }

        static void SeamDressing(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, StageSpec spec)
        {
            int own = LevelBuildKit.Chapter;
            if (spec.nextChapter != 0 && spec.nextChapter != own && own != 3)
                Feather(root, rng, own, spec.nextChapter, spec.to, -1, spec.from, spec.to);
            if (spec.prevChapter != 0 && spec.prevChapter != own && own != 3)
                Feather(root, rng, own, spec.prevChapter, spec.from, 1, spec.from, spec.to);
            if (own != 3) return;

            // The beach has no lots to dress: a few props of the neighbouring chapter stand on the sand's back edge.
            if (spec.prevChapter != 0 && spec.prevChapter != 3) BeachEdgeProps(track, root, rng, spec.prevChapter, spec.from + 3f, spec.from + 18f);
            if (spec.nextChapter != 0 && spec.nextChapter != 3) BeachEdgeProps(track, root, rng, spec.nextChapter, spec.to - 18f, spec.to - 3f);
        }

        static void BeachEdgeProps(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, int chapter, float a, float b)
        {
            for (float x = a + Rand(rng, 0f, 2f); x < b; x += Rand(rng, 4f, 6f))
            {
                float z = Rand(rng, 4.2f, 5.6f), gy = GroundAt(track, x, z);
                switch (chapter)
                {
                    case 2:
                        Model(root, "Street", "MarketStall", x, gy, z, Rand(rng, -6f, 6f));
                        break;
                    case 4:
                        if (rng.NextDouble() < 0.6) Model(root, "Street", "RoadBarrier", x, gy, z, Rand(rng, -8f, 8f));
                        else Model(root, "Street", "TrafficCone", x, gy, z, Rand(rng, 0f, 360f));
                        break;
                    default:
                        Model(root, "Street", "Bin", x, gy, z, Rand(rng, -20f, 20f));
                        break;
                }
            }
        }

        // ---------------------------------------------------------------- the far land (core scene)

        /// <summary>The chapter at world x along the lap (the first before it, the last after it).</summary>
        static int ChapterAt(float x)
        {
            return HolidayStages.All[HolidayStages.StageAt(x)].chapter;
        }

        /// <summary>
        /// The distant land all along the lap, for the core scene: fields to the foot of the hills, a wooded
        /// rise, rolling hills and two mountain ranges behind the town, the park and the site, the sea to the
        /// horizon with its headlands along the beach, and the site's tower cranes. They are too big and far to
        /// belong to a stage (they would come and go with it), and each belongs to the chapter its place is in.
        /// </summary>
        public static void FarLand(Transform root)
        {
            float lapFrom = HolidayStages.FirstStageX, lapTo = HolidayStages.FirstStageX + HolidayStages.LapLength;
            float a = lapFrom - 800f, b = lapTo + 800f;
            var rng = new System.Random(4242);
            bool kitHills = LevelBuildKit.HasKitModel("Terrain", "HillsRolling");

            // Fields from the back strips (z 90) to the hills, in strips of 40 m whose colour follows the chapter
            // and eases from one to the next; where the beach begins or ends the edge is a ragged coast.
            for (float x = a; x < b; x += 40f)
            {
                float mid = x + 20f;
                int ch = ChapterAt(mid);
                if (ch == 3) continue;
                // Eased from chapter to chapter over the 80 m round a boundary.
                Color c = Color.Lerp(FieldColor(ChapterAt(mid - 40f)), FieldColor(ChapterAt(mid + 40f)), 0.5f);
                bool coastLeft = ChapterAt(x - 20f) == 3, coastRight = ChapterAt(x + 60f) == 3;
                if (!coastLeft && !coastRight)
                {
                    Plain(root, x, x + 40f, c);
                    continue;
                }
                // Five bands of depth, each ending a different distance short of the sea.
                float zFrom = BackZ;
                for (int band = 0; band < 5; band++)
                {
                    float zTo = Mathf.Lerp(BackZ, 760f, (band + 1) / 5f);
                    float cut = 10f * rng.Next(0, 4);
                    Plain(root, coastLeft ? x + cut : x, coastRight ? x + 40f - cut : x + 40f, c, zFrom, zTo);
                    zFrom = zTo;
                }
            }

            // The tiled landforms: each tile belongs to the chapter its place is in; none over the beach.
            if (kitHills)
            {
                LayerAlongLap(root, "ForestStrip", a, b, -0.3f, 70f, 1f, 0f);
                LayerAlongLap(root, "HillsRolling", a, b, -0.4f, 230f, 1f, 0f);
                LayerAlongLap(root, "MountainRange1", a, b, -0.8f, 440f, 0.75f, 0f);
                LayerAlongLap(root, "MountainRange2", a, b, -0.8f, 640f, 1f, 0.5f);
            }
            else
            {
                for (int ch = 1; ch <= 5; ch++)
                {
                    if (ch == 3) continue;
                    float c0 = ch == 1 ? a : StartOfChapter(ch), c1 = ch == 5 ? b : StartOfChapter(ch + 1);
                    var far = CutOut(root, "DistantHills", Art.far[ch], (c0 + c1) * 0.5f, -6f, 260f, 6f, -85);
                    far.drawMode = SpriteDrawMode.Tiled;
                    far.size = new Vector2((c1 - c0 + 400f) / 6f, Art.far[ch].bounds.size.y);
                }
            }

            // The sea all along the beach, and wooded headlands out on the horizon.
            float s0 = StartOfChapter(3), s1 = StartOfChapter(4);
            float sea = -0.3f;
            var water = Solid(root, "Sea", new Vector3((s0 + s1) * 0.5f, sea - 0.05f, 480f), new Vector3(s1 - s0 + 200f, 0.1f, 950f), Color.white, Art.surfaces[ProceduralArt.Surface.Sea]);
            water.faces = MeshBuilder.Faces.Top;
            water.Rebuild();
            for (int i = 0; i < 3; i++)
            {
                float x = s0 + (s1 - s0) * (0.15f + i * 0.4f) + Rand(rng, -40f, 40f), z = 650f + i * 60f;
                if (Model(root, "Terrain", "Headland", x, sea - 0.5f, z, Rand(rng, -15f, 15f), Rand(rng, 2.2f, 3f), null, null, null, false) == null)
                    CutOut(root, "Headland", Art.headland, x, sea - 0.5f, z, 10f, -85, i % 2 == 1);
            }

            // Tower cranes over the building site.
            if (LevelBuildKit.HasKitModel("Works", "TowerCrane"))
            {
                float c0 = StartOfChapter(4), c1 = StartOfChapter(5);
                for (float x = c0 + Rand(rng, 10f, 40f); x < c1; x += Rand(rng, 70f, 110f))
                    Model(root, "Works", "TowerCrane", x, 0f, Rand(rng, 170f, 230f), Rand(rng, -40f, 40f) + (rng.NextDouble() < 0.5 ? 180f : 0f), Rand(rng, 0.85f, 1.05f), null, null, null, false);
            }
        }

        static float StartOfChapter(int chapter)
        {
            for (int i = 0; i < HolidayStages.Count; i++)
                if (HolidayStages.All[i].chapter >= chapter) return HolidayStages.StartOf(i);
            return HolidayStages.EndOf(HolidayStages.Count - 1);
        }

        static Color FieldColor(int chapter)
        {
            return chapter == 4 ? new Color(0.54f, 0.58f, 0.46f) : new Color(0.44f, 0.54f, 0.32f);
        }

        static void Plain(Transform root, float x0, float x1, Color color, float zFrom = BackZ, float zTo = 760f)
        {
            if (x1 - x0 < 0.5f) return;
            var plain = Solid(root, "Fields", new Vector3((x0 + x1) * 0.5f, -0.06f, (zFrom + zTo) * 0.5f - 1f), new Vector3(x1 - x0, 0.1f, zTo - zFrom), color);
            plain.faces = MeshBuilder.Faces.Top;
            plain.Rebuild();
        }

        /// <summary>
        /// Copies of a landform that tiles along x, side by side across [a, b], exactly a tile apart so the
        /// joins don't show; skipping those over the beach. They cast no shadows: far beyond the shadow distance.
        /// </summary>
        static void LayerAlongLap(Transform root, string model, float a, float b, float y, float z, float scale, float phase)
        {
            if (!LevelBuildKit.HasKitModel("Terrain", model)) return;
            float tile = TileWidth("Terrain", model) * scale;
            if (tile < 1f) return;
            for (float x = Mathf.Floor(a / tile) * tile + phase * tile; x < b + tile; x += tile)
            {
                if (ChapterAt(x) == 3 && x >= HolidayStages.FirstStageX && x <= HolidayStages.FirstStageX + HolidayStages.LapLength) continue;
                Model(root, "Terrain", model, x, y, z, 0f, scale, null, null, null, false);
            }
        }
    }
}
