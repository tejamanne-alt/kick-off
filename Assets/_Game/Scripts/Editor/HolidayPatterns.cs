using System;
using System.Collections.Generic;
using DribbleToSchool.Holiday;

namespace DribbleToSchool.EditorTools
{
    /// <summary>What a pattern item is. The furniture kinds are the same in all three layouts of a stage.</summary>
    public enum PatternKind
    {
        // Furniture: part of the stage, whichever layout is on.
        Gap, Tunnel, Crossing, Fountain, TideArea, Gull, Cranes, Checkpoint,
        // Street life: in the layouts, so each of the three has its people and dogs in other places.
        Walkers, DogPatch,
        // Things in the kid's way.
        Hop, Mid, Tall, Crate, Stack, Car, Slide, Puddle, SandPatch, Spring,
        // Pickups and targets.
        Coin, CoinRow, CoinArc, Star, PowerUp, Balloon,
    }

    /// <summary>
    /// One thing in a stage's layout, in world coordinates. The builder (HolidayRunBuilder) turns each into
    /// scene objects with the chapter's kit models; this file only decides what goes where.
    /// </summary>
    public sealed class PatternItem
    {
        public PatternKind kind;
        /// <summary>Where it stands along the street (the middle of a ranged item).</summary>
        public float x;
        /// <summary>The stretch it covers (gaps, puddles, tunnels, beats, coin rows and arcs).</summary>
        public float x0, x1;
        /// <summary>Size of a solid: across the street's line and up.</summary>
        public float w, h;
        /// <summary>Height of a coin, a row, a power-up, a gull, a balloon.</summary>
        public float y;
        /// <summary>How far an arc rises above its ends.</summary>
        public float rise;
        public int count;
        /// <summary>
        /// A palette index the builder picks from: car paint, coat, fur, power-up kind; for a gap, 1 if it is the wide kind; for a
        /// coin, 1 if it hangs on a trampoline's throw; for a balloon, what it is (0 balloon, 1 paper lantern, 2 beach ball).
        /// </summary>
        public int style;
        /// <summary>A <c>TrackBuilder.SlideLook</c> name.</summary>
        public string look;
        /// <summary>Gap: water instead of a pit.</summary>
        public bool flag;
        /// <summary>Free parameters: pipes (interval, despawn x), tide (period, phase), gull (phase), walkers (speed), fountain (strength), balloon (colour).</summary>
        public float a, b;

        public PatternItem Copy() { return (PatternItem)MemberwiseClone(); }
    }

    /// <summary>A stage's plan: the furniture it always has, and three alternative layouts of obstacles, street life, targets, coins and power-ups.</summary>
    public sealed class StagePlan
    {
        public int stage;
        public float from, to;
        /// <summary>The first and last x an obstacle may occupy (the run-in and run-out are clear).</summary>
        public float firstX, lastX;
        /// <summary>1: the spacing between demands is what the density asks for; below it, tightened (never past the minimums) to fit all the stage's traits.</summary>
        public float relax;
        /// <summary>How many beats of walkers and dogs each layout has (the same in all three).</summary>
        public int life;
        public readonly List<PatternItem> furniture = new List<PatternItem>();
        public readonly List<PatternItem>[] layouts = new List<PatternItem>[HolidayPatterns.Variants];
    }

    /// <summary>
    /// The obstacle and pickup layouts of a Holiday Run stage, worked out from its traits and density
    /// (HolidayStages). Pure logic on world x, so it can be checked without the editor: the rules are in
    /// <see cref="Validate"/>.
    ///
    /// The kid is steered with the walk stick at 4.2 m/s, so what a stage may ask comes from what the kid can really
    /// do at that speed (JumpReach): a plain gap (one jump) is 1.4 to 1.9 m wide and never over 2.0, a wide gap (a double
    /// jump) 2.7 to 3.1 and never over 3.2; low things (steps, kerbs) are up to 0.5 m, mid things (planters, rocks) up to
    /// 1.0, tall things 1.7 at most and only a double jump gets over them, nothing is higher than 1.8 (a parked car is
    /// climbed in two hops); a barrier to slide under leaves 0.85 m; a gap has 6 m of clear ground before it (run-up and room to
    /// kick the ball across) and 4 m after it (landing and room to fetch the ball).
    ///
    /// The player sets the pace, so spacing is about clutter and ball logistics, not reaction time: between two demands
    /// there are 20 m at density 0.3 down to 9 m at density 1 (10 m between different ones, a little more after a slide, a
    /// pad or a pipe lane). In between: walls and gaps alternate with things to smash (crates, stacks, sandcastles, cones),
    /// street life (beats of walkers and dogs), floating targets (balloons, lanterns, beach balls that burst into coins when
    /// the ball hits them), a trail of coins in gentle waves, arcs over every wall and gap, a power-up in every second stage
    /// at least, and now and then a bonus detour (a high arc of coins and a star, for a double jump).
    ///
    /// The gaps, tunnel, crossings, fountains, tide and gulls are furniture: the same in all three layouts. The layouts
    /// share one recipe (the same obstacles, beats and targets of the same kinds, so they are as hard as each other) and
    /// differ in order, places, sizes, looks, coins and power-ups.
    /// </summary>
    public static class HolidayPatterns
    {
        public const int Variants = 3;

        /// <summary>What a thing asks of the kid; two different demands are never closer than <see cref="MinDifferent"/>.</summary>
        enum Demand { Jump, Double, Slide, Gap, Slow, Launch }

        // ----------------------------------------------------------------------------------------------- what the kid can do

        static readonly JumpReach.Motion Reach = JumpReach.Defaults;

        /// <summary>Plain gap (one jump): never wider than this, made 1.4 to 1.9 m.</summary>
        public static readonly float PlainGapMax = JumpReach.SafePlainGap(Reach);
        public static readonly float PlainGapMin = JumpReach.ComfortablePlainMin(Reach);
        public static readonly float PlainGapComfortMax = JumpReach.ComfortablePlainMax(Reach);
        /// <summary>Wide gap (a double jump): between these, made 2.7 to 3.1 m.</summary>
        public static readonly float WideGapMin = JumpReach.MinWideGap(Reach);
        public static readonly float WideGapMax = JumpReach.SafeWideGap(Reach);
        public static readonly float WideGapComfortMin = JumpReach.ComfortableWideMin(Reach);
        public static readonly float WideGapComfortMax = JumpReach.ComfortableWideMax(Reach);
        /// <summary>Low (steps, kerbs), mid (a single jump), tall (a double jump) and the highest anything may be.</summary>
        public static readonly float LowWallMax = JumpReach.SafeLowWall(Reach);
        public static readonly float MidWallMax = JumpReach.SafeMidWall(Reach);
        public static readonly float TallWallMax = JumpReach.SafeTallWall(Reach);
        public static readonly float WallMax = JumpReach.MaxWall(Reach);

        /// <summary>A pile of crates two high is 1.42 m: a double jump, or a hard kick.</summary>
        public const float StackWidth = 1.42f, StackHeight = 1.42f;
        /// <summary>The parked car (Wall of the kit's hatchback): bonnet at 0.95, roof at 1.55.</summary>
        public const float CarLength = 3.3f, CarHeight = 1.55f;

        /// <summary>The underpass's deck is this high: a double jump (head at 3.24 m) fits with room to spare.</summary>
        public const float TunnelHeight = 3.8f;
        /// <summary>The crane's load hangs this high, over the trench: out of reach even of a trampoline throw with the air jump.</summary>
        public const float CraneHang = 5f;
        /// <summary>The clear height under every barrier to slide under (TrackBuilder.SlideGap).</summary>
        public const float SlideClearance = 0.85f;
        /// <summary>
        /// The middle checkpoint of a stage keeps this much ground clear before it and after it (the kid is put down on it with the ball a metre
        /// ahead, and needs a run-up of 6 m to whatever comes next).
        /// </summary>
        public const float CheckpointBefore = 4f, CheckpointAfter = 6f;

        // ----------------------------------------------------------------------------------------------- spacing

        /// <summary>Metres between two demands: the same kind 9 at the least, different kinds 10.</summary>
        public const float MinSame = 9f, MinDifferent = 10f;
        /// <summary>A power-up floats at least this far from any demand (the kid doesn't have to leap for it).</summary>
        public const float PowerUpClear = 3f;
        /// <summary>The ground a beat of walkers or dogs keeps clear round it, and the shortest beat.</summary>
        public const float BeatMargin = 1.5f, MinBeat = 4.5f, MaxBeat = 7f;
        /// <summary>No stretch of a stage's open ground is longer than this without something on it (a demand, street life, a target, a power-up...).</summary>
        public const float MaxBare = 25f;

        // The barriers to slide under, by chapter: name, length along the street, the top of the solid, and whether
        // it fits under a tunnel's deck.
        struct SlideSpec
        {
            public string name; public float length, top; public bool lowTop;
            public SlideSpec(string name, float length, float top, bool lowTop) { this.name = name; this.length = length; this.top = top; this.lowTop = lowTop; }
        }

        static readonly SlideSpec[][] Slides =
        {
            new[] { new SlideSpec("PlankTrestles", 2.6f, 0.95f, false), new SlideSpec("BoomBarrier", 1.2f, 0.95f, false), new SlideSpec("AccessPlatform", 1.9f, 2.0f, false), new SlideSpec("AppleBough", 1.7f, 1.09f, false),
                    new SlideSpec("WashingLine", 2.7f, 2.0f, false) },
            new[] { new SlideSpec("StallAwning", 2.2f, 2.5f, false), new SlideSpec("RollShutter", 1.4f, 3.15f, false), new SlideSpec("DeliveryConveyor", 1.2f, 0.96f, false),
                    new SlideSpec("BarrowCart", 2.6f, 1.4f, false) },
            new[] { new SlideSpec("SurfRack", 2.6f, 2.37f, false), new SlideSpec("BoatTrestles", 3.4f, 1.53f, false), new SlideSpec("Boardwalk", 1.6f, 1.94f, false), new SlideSpec("RescueBoardStand", 3.0f, 1.07f, false) },
            new[] { new SlideSpec("ScaffoldGantry", 2.7f, 4.25f, false), new SlideSpec("BeamTrestles", 4.4f, 1.3f, true), new SlideSpec("PipeRack", 4.1f, 2.04f, true), new SlideSpec("SiteBarrier", 1.2f, 0.94f, true) },
            new[] { new SlideSpec("FallenTrunk", 0.8f, 1.55f, false), new SlideSpec("OakBough", 2.1f, 1.19f, false), new SlideSpec("NetTunnel", 2.1f, 0.96f, false), new SlideSpec("PlayTower", 1.4f, 2.6f, false),
                    new SlideSpec("WobbleBridge", 2.4f, 0.97f, false) },
        };

        /// <summary>The slide looks of a chapter (1 to 5), as TrackBuilder.SlideLook names.</summary>
        public static string[] SlideLooks(int chapter)
        {
            var list = Slides[Math.Max(1, Math.Min(5, chapter)) - 1];
            var names = new string[list.Length];
            for (int i = 0; i < names.Length; i++) names[i] = list[i].name;
            return names;
        }

        /// <summary>Length of a barrier along the street (what the coin row under it spans).</summary>
        public static float SlideLength(int chapter, string look)
        {
            foreach (var s in Slides[Math.Max(1, Math.Min(5, chapter)) - 1]) if (s.name == look) return s.length;
            return 2f;
        }

        /// <summary>Length of the barrier with this look, whichever chapter it belongs to (0 if there is no such look).</summary>
        public static float SlideLengthAny(string look)
        {
            foreach (var chapter in Slides)
                foreach (var s in chapter)
                    if (s.name == look) return s.length;
            return 0f;
        }

        // A tunnel keeps its ends clear: nothing for the first 10 m inside, the last 4, the 6 m before or the 2 after.
        public const float TunnelLeadIn = 10f, TunnelLeadOut = 4f, TunnelApproach = 6f, TunnelAfter = 2f;
        /// <summary>The utility poles stand every 21 m; a tunnel or a crane's plot must not take the ones that carry the wires over a stage's ends.</summary>
        public const float PoleSpacing = 21f;
        /// <summary>A crossing's side street keeps this much clear round it.</summary>
        const float CrossingMargin = 2.3f;
        /// <summary>A fountain's bay: its jets throw the ball about, so nothing else stands this near.</summary>
        const float FountainBay = 6f;

        // ----------------------------------------------------------------------------------------------- the rules

        static float Lerp(float a, float b, float t) { return a + (b - a) * t; }
        static float Clamp01(float v) { return v < 0f ? 0f : v > 1f ? 1f : v; }

        /// <summary>Metres between one demand and the next of the same kind: 20 at density 0.3 down to 9 at 1.</summary>
        public static float BaseSpacing(float density)
        {
            return Lerp(20f, MinSame, Clamp01((density - 0.3f) / 0.7f));
        }

        /// <summary>How many beats of walkers and dogs a stage has: 1 to 2 at low density, 3 to 4 at high.</summary>
        public static int LifeCount(float density)
        {
            return Math.Max(1, Math.Min(4, (int)Math.Round(Lerp(1.4f, 4.2f, Clamp01((density - 0.28f) / 0.72f)))));
        }

        /// <summary>How many floating targets (balloons, lanterns, beach balls) a stage has: 2 to 4.</summary>
        public static int BalloonCount(float density)
        {
            return density < 0.45f ? 2 : density < 0.78f ? 3 : 4;
        }

        struct Span
        {
            public float x0, x1;
            public Demand demand;
            /// <summary>More room wanted after it (a slide goes on, a lane of pipes rolls on).</summary>
            public float extra;
            /// <summary>Keep-out ground that is not a demand (the ends of a tunnel, a crossing): it carries its own margins.</summary>
            public bool zone;
            public bool tunnelStart, tunnelEnd;
        }

        /// <summary>
        /// The room wanted between two demands: the density's spacing (tightened by <paramref name="relax"/>, 1 to 0, toward the minimums), at least 10 m between
        /// different ones, and what the first needs after it. Zones need only a little.
        /// </summary>
        static float Spacing(Span prev, Span next, float density, float relax)
        {
            if (prev.zone || next.zone) return 2f;
            float b = Lerp(MinSame, BaseSpacing(density), relax);
            return (prev.demand == next.demand ? b : Math.Max(b, MinDifferent)) + prev.extra;
        }

        static Span Demanding(float x0, float x1, Demand demand, float extra)
        {
            return new Span { x0 = x0, x1 = x1, demand = demand, extra = extra };
        }

        static Span Zone(float x0, float x1)
        {
            return new Span { x0 = x0, x1 = x1, zone = true };
        }

        static int StageSeed(int stage) { return 0x5EED + stage * 7919; }

        // ----------------------------------------------------------------------------------------------- the plan

        /// <summary>The plan of a stage (0 to 22): the same every time it is asked.</summary>
        public static StagePlan Plan(int stage)
        {
            var st = HolidayStages.All[stage];
            var plan = new StagePlan { stage = stage, from = HolidayStages.StartOf(stage), to = HolidayStages.EndOf(stage) };
            float a = plan.from + HolidayStages.StageRunIn;
            if (stage == 0) a = Math.Max(a, HolidayStages.FirstStageX + HolidayStages.RunIn);
            float b = plan.to - HolidayStages.StageRunOut;
            // The last stretch to the school gate is clear: a straight to run down.
            if (st.Has(StageTraits.School)) b = Math.Min(b, HolidayStages.GateX - 14f);
            plan.firstX = a;
            plan.lastX = b;

            var rng = new Random(StageSeed(stage));
            for (int outer = 0; outer < 90; outer++)
            {
                plan.furniture.Clear();
                var anchors = new List<Span>();
                // If the furniture won't all fit: first without the middle checkpoint, then one gap fewer (then another).
                int fewerGaps = outer < 60 ? 0 : (outer - 60) / 15 + 1;
                if (!PlaceFurniture(plan, st, rng, a, b, anchors, fewerGaps, outer < 30)) continue;
                if (Recipe(plan, st, anchors, a, b, rng)) return plan;
            }
            // Never expected (every stage fits, see the checks), but a stage must still get built: a stage with its
            // furniture only and bare layouts, rather than none.
            plan.furniture.Clear();
            for (int v = 0; v < Variants; v++) plan.layouts[v] = new List<PatternItem>();
            plan.relax = 0f;
            return plan;
        }

        // ----------------------------------------------------------------------------------------------- furniture

        /// <summary>
        /// Places the stage's gaps, tunnel, crossings and fountains at random along the free stretch, apart from each
        /// other, and its tide and gulls (scenery that takes no ground). False if they don't all fit (the caller tries again).
        /// </summary>
        static bool PlaceFurniture(StagePlan plan, HolidayStages.Stage st, Random rng, float a, float b, List<Span> anchors, int fewerGaps, bool checkpoint)
        {
            float d = st.density;
            bool poles = st.chapter == 1 || st.chapter == 4;

            // A second checkpoint near the middle of the stage's open ground (the first stands 8 m in): a lost ball costs half a stage of
            // walking back, not a whole one. Its ground is kept clear like a tunnel's mouth (a stage too full to spare it goes without).
            if (checkpoint)
            {
                float cx = Lerp(a, b, Range(rng, 0.42f, 0.58f));
                anchors.Add(Zone(cx - CheckpointBefore, cx + CheckpointAfter));
                plan.furniture.Add(new PatternItem { kind = PatternKind.Checkpoint, x = cx, x0 = cx, x1 = cx });
            }

            if (st.Has(StageTraits.Gaps))
            {
                int count = Math.Max(1, (d < 0.5f ? 1 : d < 0.78f ? 2 : 3) - fewerGaps);
                // Wide gaps (a double jump) only where the density is over 0.5: one, or two in the hardest stages.
                int wide = 0;
                if (d > 0.5f) wide = count >= 3 && d > 0.85f ? 2 : count >= 2 ? 1 : (rng.NextDouble() < 0.4 ? 1 : 0);
                var wides = new List<bool>();
                for (int i = 0; i < count; i++) wides.Add(i < wide);
                Shuffle(wides, rng);
                for (int i = 0; i < count; i++)
                {
                    bool wideGap = wides[i];
                    // Plain gaps are 1.4 to 1.9 m (the easiest stages stay near the narrow end), wide ones 2.7 to 3.1.
                    float w = wideGap ? Range(rng, WideGapComfortMin, WideGapComfortMax)
                        : (d < 0.5f ? Range(rng, PlainGapMin, PlainGapMin + 0.35f) : Range(rng, PlainGapMin, PlainGapComfortMax));
                    var span = Demanding(0f, 0f, wideGap ? Demand.Double : Demand.Gap, 0f);
                    float x;
                    // A gap's neighbourhood keeps clear of the first and last pole (a crane's plot sits beside it).
                    if (!TryPlace(anchors, w, span, a, b, rng, d, plan, poles ? 7f : -1f, false, out x)) return false;
                    span.x0 = x; span.x1 = x + w;
                    anchors.Add(span);
                    plan.furniture.Add(new PatternItem
                    {
                        kind = PatternKind.Gap, x = x + w * 0.5f, x0 = x, x1 = x + w, w = w,
                        flag = rng.NextDouble() < 0.5, style = wideGap ? 1 : 0,
                    });
                }
            }

            if (st.Has(StageTraits.Tunnel))
            {
                float len = Range(rng, 26f, 32f);
                float whole = len + TunnelApproach + TunnelAfter;
                float x;
                // A tunnel is placed as one block, with its keep-out ends in.
                if (!TryPlace(anchors, whole, Zone(0f, 0f), a, b, rng, d, plan, poles ? 1.5f : -1f, false, out x)) return false;
                float t0 = x + TunnelApproach, t1 = t0 + len;
                anchors.Add(new Span { x0 = t0 - TunnelApproach, x1 = t0 + TunnelLeadIn, zone = true, tunnelStart = true });
                anchors.Add(new Span { x0 = t1 - TunnelLeadOut, x1 = t1 + TunnelAfter, zone = true, tunnelEnd = true });
                plan.furniture.Add(new PatternItem { kind = PatternKind.Tunnel, x = (t0 + t1) * 0.5f, x0 = t0, x1 = t1, w = len });
            }

            if (st.Has(StageTraits.Crossing))
            {
                int count = d > 0.65f ? 2 : 1;
                for (int i = 0; i < count; i++)
                {
                    float width = 5f, margin = CrossingMargin, x;
                    // The side street is wide: it stays clear of every pole, so none is lost (and the wires meet).
                    if (!TryPlace(anchors, width + margin * 2f, Zone(0f, 0f), a, b, rng, d, plan, -1f, true, out x)) return false;
                    float c0 = x + margin;
                    anchors.Add(Zone(x, x + width + margin * 2f));
                    plan.furniture.Add(new PatternItem { kind = PatternKind.Crossing, x = c0 + width * 0.5f, x0 = c0, x1 = c0 + width, w = width, a = i * 2f });
                }
            }

            if (st.Has(StageTraits.Fountain))
            {
                for (int i = 0; i < 2; i++)
                {
                    float x;
                    if (!TryPlace(anchors, 2f * FountainBay, Zone(0f, 0f), a, b, rng, d, plan, -1f, false, out x)) return false;
                    anchors.Add(Zone(x, x + 2f * FountainBay));
                    plan.furniture.Add(new PatternItem { kind = PatternKind.Fountain, x = x + FountainBay, x0 = x + FountainBay - 0.6f, x1 = x + FountainBay + 0.6f, h = i == 0 ? 4f : 5f, a = i == 0 ? 18f : 16f });
                }
            }

            // Scenery with no say in the pacing: the sea washing up, gulls, the cranes over the trenches.
            if (st.Has(StageTraits.Tide))
            {
                float at = a + Range(rng, 2f, 10f);
                for (int i = 0; i < 3 && at < b - 8f; i++)
                {
                    float len = Range(rng, 5f, 8f);
                    plan.furniture.Add(new PatternItem { kind = PatternKind.TideArea, x = at + len * 0.5f, x0 = at, x1 = at + len, a = Range(rng, 5f, 7f), b = Range(rng, 0f, 3f) });
                    at += len + Range(rng, 14f, 24f);
                }
            }
            // Gulls on every beach stage, more where the stage is about them: they swoop at a ball in the air (a chip, a shot at a
            // balloon) and never at one rolling along the ground.
            if (st.Has(StageTraits.Seagulls) || st.chapter == 3)
            {
                int gulls = st.Has(StageTraits.Seagulls) ? 5 : 3;
                for (int i = 0; i < gulls; i++)
                {
                    float centre = Lerp(a, b, (i + 0.5f) / gulls) + Range(rng, -6f, 6f);
                    plan.furniture.Add(new PatternItem { kind = PatternKind.Gull, x = centre, x0 = centre + 15f, x1 = centre - 15f, y = Range(rng, 3.0f, 3.6f), a = Range(rng, 0f, 3f) });
                }
            }
            if (st.Has(StageTraits.Cranes))
            {
                int cranes = 0;
                foreach (var gap in plan.furniture.ToArray())
                    if (gap.kind == PatternKind.Gap && cranes++ < 2)
                        plan.furniture.Add(new PatternItem { kind = PatternKind.Cranes, x = gap.x, x0 = gap.x - 3f, x1 = gap.x + 3f });
            }
            return true;
        }

        /// <summary>
        /// The first and last utility pole of a stage's own stretch: the ones the wires cross the seams from. The
        /// cross street at the end (and the one the previous stage left at the start) takes the poles near the
        /// seam, so these are the first one 1.1 m past the start and the last one 8.1 m short of the end.
        /// </summary>
        static void EndPoles(StagePlan plan, out float first, out float last)
        {
            first = (float)Math.Ceiling((plan.from + 1.1f) / PoleSpacing) * PoleSpacing;
            last = (float)Math.Floor((plan.to - 8.1f) / PoleSpacing) * PoleSpacing;
        }

        /// <summary>
        /// A random x for something <paramref name="length"/> long that keeps its distance from everything placed.
        /// With <paramref name="poleMargin"/> above 0 the spot also stays that far from the stage's first and last
        /// pole; with <paramref name="clearOfPoles"/> from every pole.
        /// </summary>
        static bool TryPlace(List<Span> placed, float length, Span kind, float a, float b, Random rng, float density, StagePlan plan,
            float poleMargin, bool clearOfPoles, out float x)
        {
            x = 0f;
            if (b - a < length) return false;
            float firstPole, lastPole;
            EndPoles(plan, out firstPole, out lastPole);
            for (int attempt = 0; attempt < 120; attempt++)
            {
                float px = a + (float)rng.NextDouble() * (b - a - length);
                var me = kind; me.x0 = px; me.x1 = px + length;
                bool ok = true;
                foreach (var p in placed)
                {
                    float need;
                    bool pGap = !p.zone && (p.demand == Demand.Gap || p.demand == Demand.Double);
                    if (p.zone && me.zone) need = 1f;
                    else if (p.zone || me.zone)
                    {
                        need = 2f;
                        // A gap wants 6 m of ground before it: the tunnel's exit (2 m of keep-out) is no run-up, so 4 more.
                        if (p.zone && p.tunnelEnd && p.x1 <= me.x0) need = 4f;
                        if (me.zone && pGap && p.x0 >= me.x1) need = 4f;
                    }
                    else need = Math.Max(p.x1 <= me.x0 ? Spacing(p, me, density, 1f) : Spacing(me, p, density, 1f), MinDifferent);
                    if (!(p.x1 + need <= me.x0 || me.x1 + need <= p.x0)) { ok = false; break; }
                }
                if (ok && poleMargin > 0f && (Near(firstPole, me.x0, me.x1, poleMargin) || Near(lastPole, me.x0, me.x1, poleMargin))) ok = false;
                if (ok && clearOfPoles)
                    for (float pole = (float)Math.Floor(me.x0 / PoleSpacing) * PoleSpacing; pole < me.x1 + PoleSpacing; pole += PoleSpacing)
                        if (Near(pole, me.x0, me.x1, 1.5f)) { ok = false; break; }
                if (ok) { x = px; return true; }
            }
            return false;
        }

        static bool Near(float x, float x0, float x1, float margin) { return x > x0 - margin && x < x1 + margin; }

        // ----------------------------------------------------------------------------------------------- the recipe

        /// <summary>One group the layouts all share: its kind, and how many hurdles of it (a run of two or three low things, a pair of mid ones).</summary>
        struct Template
        {
            public PatternKind kind; public int n;
            public Template(PatternKind kind, int n) { this.kind = kind; this.n = n; }
        }

        /// <summary>
        /// Chooses what the layouts hold and how tightly it is packed. The groups every trait of the stage asks
        /// for must fit, so the spacing is tightened (never below the minimums) until they do; then the density's
        /// share of further groups is added while they still fit; then the street life. All three layouts have the same ones.
        /// </summary>
        static bool Recipe(StagePlan plan, HolidayStages.Stage st, List<Span> anchors, float a, float b, Random rng)
        {
            float d = st.density;
            var sorted = new List<Span>(anchors);
            sorted.Sort((p, q) => p.x0.CompareTo(q.x0));

            var required = new List<Template>();
            if (st.Has(StageTraits.Steps)) required.Add(new Template(PatternKind.Hop, HopCount(d, rng)));
            if (st.Has(StageTraits.Crates)) { required.Add(new Template(PatternKind.Mid, MidCount(d, rng))); required.Add(new Template(PatternKind.Crate, 1)); }
            // Every stage has something to smash (crates, a sandcastle on the beach, cones on the site).
            else required.Add(new Template(PatternKind.Crate, 1));
            if (st.Has(StageTraits.Cars)) required.Add(new Template(PatternKind.Car, 1));
            if (st.Has(StageTraits.Awnings)) required.Add(new Template(PatternKind.Slide, 1));
            if (st.Has(StageTraits.Puddles)) required.Add(new Template(PatternKind.Puddle, 1));
            if (st.Has(StageTraits.SoftSand)) required.Add(new Template(PatternKind.SandPatch, 1));
            if (st.Has(StageTraits.Springboards)) required.Add(new Template(PatternKind.Spring, 1));

            // The density's share of further groups, drawn up front so the choice doesn't depend on what fits. Gaps count as demands.
            float free = b - a;
            float s = BaseSpacing(d);
            int target = Math.Max(5, (int)Math.Round((free + s) / (s + 2.8f)));
            int have = required.Count;
            foreach (var sp in sorted) if (!sp.zone) have++;
            var weights = new List<KeyValuePair<PatternKind, float>>();
            weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Hop, st.Has(StageTraits.Steps) ? 1.2f : 0.7f));
            weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Mid, 1f));
            weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Crate, st.Has(StageTraits.Crates) ? 1.1f : 0.8f));
            if (d >= 0.45f) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Stack, st.Has(StageTraits.Crates) ? 0.7f : 0.45f));
            if (st.Has(StageTraits.Cars)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Car, 0.7f));
            if (st.Has(StageTraits.Awnings)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Slide, 1.3f));
            if (st.Has(StageTraits.Puddles)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Puddle, 0.5f));
            if (st.Has(StageTraits.SoftSand)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.SandPatch, 0.6f));
            if (st.Has(StageTraits.Springboards)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Spring, 0.3f));
            // A tall thing wants a double jump: rare, and not at all in the easy stages.
            if (st.Has(StageTraits.Crates) && d >= 0.6f) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Tall, 0.35f));
            var extras = new List<Template>();
            // No more than this of a kind in a stage (the required ones count): the stage stays varied.
            int springs = Count(required, PatternKind.Spring), talls = 0, stacks = 0, crates = Count(required, PatternKind.Crate);
            int slides = Count(required, PatternKind.Slide), puddles = Count(required, PatternKind.Puddle), sands = Count(required, PatternKind.SandPatch);
            for (int guard = 0; have + extras.Count < target && guard < 60; guard++)
            {
                var k = Pick(weights, rng);
                if (k == PatternKind.Spring && springs >= 2) continue;
                if (k == PatternKind.Tall && talls >= 1) continue;
                if (k == PatternKind.Stack && stacks >= 1) continue;
                if (k == PatternKind.Crate && crates >= 3) continue;
                if (k == PatternKind.Slide && slides >= 2) continue;
                if (k == PatternKind.Puddle && puddles >= 2) continue;
                if (k == PatternKind.SandPatch && sands >= 2) continue;
                if (k == PatternKind.Spring) springs++;
                if (k == PatternKind.Tall) talls++;
                if (k == PatternKind.Stack) stacks++;
                if (k == PatternKind.Crate) crates++;
                if (k == PatternKind.Slide) slides++;
                if (k == PatternKind.Puddle) puddles++;
                if (k == PatternKind.SandPatch) sands++;
                extras.Add(new Template(k, k == PatternKind.Hop ? HopCount(d, rng) : k == PatternKind.Mid ? MidCount(d, rng) : 1));
            }

            var life = LifeKinds(st);
            var found = new List<PatternItem>[Variants];
            foreach (float relax in new[] { 1f, 0.8f, 0.6f, 0.4f, 0.2f, 0f })
            {
                // The street life goes in last, round what the layout holds; as many beats as fit in all three.
                if (!TryLayouts(plan, st, sorted, required, life, a, b, relax, found)) continue;
                var chosen = new List<Template>(required);
                var best = (List<PatternItem>[])found.Clone();
                foreach (var extra in extras)
                {
                    chosen.Add(extra);
                    if (TryLayouts(plan, st, sorted, chosen, life, a, b, relax, found)) best = (List<PatternItem>[])found.Clone();
                    else chosen.RemoveAt(chosen.Count - 1);
                }
                for (int v = 0; v < Variants; v++) plan.layouts[v] = best[v];
                plan.relax = relax;
                plan.life = life.Count;
                return true;
            }
            // The street life won't fit round the required groups: carry on with fewer beats rather than none of the stage.
            for (int keep = life.Count - 1; keep >= 0; keep--)
            {
                var fewer = life.GetRange(0, keep);
                foreach (float relax in new[] { 1f, 0.6f, 0.2f, 0f })
                {
                    if (!TryLayouts(plan, st, sorted, required, fewer, a, b, relax, found)) continue;
                    for (int v = 0; v < Variants; v++) plan.layouts[v] = (List<PatternItem>)found[v];
                    plan.relax = relax;
                    plan.life = keep;
                    return true;
                }
            }
            return false;
        }

        /// <summary>The beats of street life a stage has, in order of importance: people first and a dog second (so every stage with two beats or more has both), and the stage's own traits first.</summary>
        static List<PatternKind> LifeKinds(HolidayStages.Stage st)
        {
            PatternKind w = PatternKind.Walkers, g = PatternKind.DogPatch;
            PatternKind[] mix;
            switch (st.chapter)
            {
                case 1: mix = new[] { w, g, w, w }; break;
                case 2: mix = new[] { w, g, w, w }; break;
                case 3: mix = new[] { w, g, w, g }; break;
                case 4: mix = new[] { w, g, w, w }; break;   // a watchdog on the site
                default: mix = new[] { g, w, g, w }; break;
            }
            int n = LifeCount(st.density);
            var list = new List<PatternKind>();
            for (int i = 0; i < n; i++) list.Add(mix[i]);
            if (st.Has(StageTraits.Pedestrians) && !list.Contains(w)) list[0] = w;
            if (st.Has(StageTraits.Dogs) && !list.Contains(g)) list[list.Count - 1] = g;
            return list;
        }

        static int HopCount(float density, Random rng)
        {
            if (density < 0.45f) return 1;
            double r = rng.NextDouble();
            return r < 0.3 ? 1 : r < 0.75 ? 2 : 3;
        }

        static int MidCount(float density, Random rng)
        {
            return density >= 0.6f && rng.NextDouble() < 0.3 ? 2 : 1;
        }

        static int Count(List<Template> list, PatternKind kind)
        {
            int n = 0;
            foreach (var t in list) if (t.kind == kind) n++;
            return n;
        }

        static PatternKind Pick(List<KeyValuePair<PatternKind, float>> weights, Random rng)
        {
            float total = 0f;
            foreach (var w in weights) total += w.Value;
            float r = (float)rng.NextDouble() * total;
            foreach (var w in weights)
            {
                r -= w.Value;
                if (r <= 0f) return w.Key;
            }
            return weights[weights.Count - 1].Key;
        }

        // ----------------------------------------------------------------------------------------------- the layouts

        /// <summary>A group of obstacles worked out around its leading edge at 0.</summary>
        sealed class Group
        {
            public PatternKind kind;
            public Demand demand;
            public float length, extra;
            public bool tunnelOk;
            public readonly List<PatternItem> items = new List<PatternItem>();
            public Span Span { get { return Demanding(0f, length, demand, extra); } }
            public float Reserve(float density, float relax)
            {
                return length + Math.Max(Lerp(MinSame, BaseSpacing(density), relax), MinDifferent) + extra;
            }
        }

        /// <summary>A free stretch between two pieces of furniture (or the stage's free ends) that groups can go in.</summary>
        sealed class Segment
        {
            public Span? left, right;
            public float from, to;
            public bool tunnel;
            public readonly List<Group> groups = new List<Group>();
            public float used;
        }

        static bool TryLayouts(StagePlan plan, HolidayStages.Stage st, List<Span> sorted, List<Template> recipe, List<PatternKind> life, float a, float b, float relax, List<PatternItem>[] into)
        {
            for (int v = 0; v < Variants; v++)
            {
                into[v] = Layout(plan, st, sorted, recipe, life, a, b, v, relax);
                if (into[v] == null) return false;
            }
            return true;
        }

        static List<PatternItem> Layout(StagePlan plan, HolidayStages.Stage st, List<Span> sorted, List<Template> recipe, List<PatternKind> life, float a, float b, int variant, float relax)
        {
            float d = st.density;
            for (int attempt = 0; attempt < 250; attempt++)
            {
                var rng = new Random(StageSeed(plan.stage) * 31 + variant * 104729 + attempt * 7 + 1);
                var segments = MakeSegments(sorted, a, b);
                var groups = new List<Group>();
                foreach (var t in recipe) groups.Add(MakeGroup(t, st, rng));
                Shuffle(groups, rng);
                bool ok = true;
                foreach (var g in groups)
                {
                    var options = new List<Segment>();
                    foreach (var s in segments)
                    {
                        if (s.tunnel && !g.tunnelOk) continue;
                        // The last group in a segment needs no spacing after it.
                        if (s.used + g.Reserve(d, relax) <= (s.to - s.from) + Math.Max(Lerp(MinSame, BaseSpacing(d), relax), MinDifferent) + g.extra) options.Add(s);
                    }
                    if (options.Count == 0) { ok = false; break; }
                    var pick = options[rng.Next(options.Count)];
                    pick.groups.Add(g);
                    pick.used += g.Reserve(d, relax);
                }
                if (!ok) continue;

                // Left to right, each group the right distance from the one before it, even across a keep-out zone.
                var items = new List<PatternItem>();
                var placed = new List<Span>();
                Span? prev = null;
                for (int s = 0; s < segments.Count && ok; s++)
                {
                    var seg = segments[s];
                    if (seg.left.HasValue && !seg.left.Value.zone) prev = seg.left;
                    if (seg.groups.Count == 0) continue;
                    ok = PlaceSegment(seg, segments, s, ref prev, items, placed, d, relax, rng);
                }
                if (!ok || !SpacedRight(plan, placed, items, d)) continue;
                // The power-up first (every second stage must have one), then the people and dogs, then the targets.
                AddPowerUp(plan, items, a, b, rng, variant);
                if (!AddLife(plan, items, life, a, b, rng)) continue;
                if (!AddBalloons(plan, items, st, a, b, rng)) continue;
                AddDetour(plan, items, a, b, rng, variant);
                AddCoins(plan, items, a, b, rng);
                items.Sort((p, q) => p.x.CompareTo(q.x));
                return items;
            }
            return null;
        }

        /// <summary>The free stretches between the furniture (and the stage's free ends).</summary>
        static List<Segment> MakeSegments(List<Span> sorted, float a, float b)
        {
            var list = new List<Segment>();
            Span? prev = null;
            for (int i = 0; i <= sorted.Count; i++)
            {
                var s = new Segment { left = prev };
                s.from = prev.HasValue ? prev.Value.x1 : a;
                if (i < sorted.Count)
                {
                    s.right = sorted[i];
                    s.to = sorted[i].x0;
                    s.tunnel = prev.HasValue && prev.Value.tunnelStart && sorted[i].tunnelEnd;
                }
                else s.to = b;
                s.from = Math.Max(s.from, a);
                s.to = Math.Min(s.to, b);
                if (s.to - s.from > 1f) list.Add(s);
                if (i < sorted.Count) prev = sorted[i];
            }
            return list;
        }

        /// <summary>Lays a segment's groups in a random order along it, the spare room spread at random. False if they don't fit.</summary>
        static bool PlaceSegment(Segment s, List<Segment> all, int index, ref Span? prev, List<PatternItem> items, List<Span> placed, float d, float relax, Random rng)
        {
            Shuffle(s.groups, rng);
            var g = s.groups;
            float start = s.from;
            if (prev.HasValue) start = Math.Max(start, prev.Value.x1 + Spacing(prev.Value, g[0].Span, d, relax));
            float total = 0f;
            for (int i = 0; i < g.Count; i++)
            {
                total += g[i].length;
                if (i + 1 < g.Count) total += Spacing(g[i].Span, g[i + 1].Span, d, relax);
            }
            // The next piece of furniture, and the next demand beyond any zones.
            float limit = s.to;
            Span last = g[g.Count - 1].Span;
            if (s.right.HasValue)
            {
                limit = Math.Min(limit, s.right.Value.x0 - Spacing(last, s.right.Value, d, relax));
                var nextDemand = NextDemand(all, index);
                if (nextDemand.HasValue) limit = Math.Min(limit, nextDemand.Value.x0 - Spacing(last, nextDemand.Value, d, relax));
            }
            float room = limit - (start + total);
            if (room < -0.001f) return false;
            var shares = new float[g.Count];
            float sum = 0.4f;
            for (int i = 0; i < shares.Length; i++) { shares[i] = (float)rng.NextDouble(); sum += shares[i]; }
            float x = start;
            for (int i = 0; i < g.Count; i++)
            {
                x += room * shares[i] / sum;
                AddGroup(g[i], x, items);
                var span = Demanding(x, x + g[i].length, g[i].demand, g[i].extra);
                placed.Add(span);
                prev = span;
                x += g[i].length;
                if (i + 1 < g.Count) x += Spacing(g[i].Span, g[i + 1].Span, d, relax);
            }
            return true;
        }

        /// <summary>The first furniture demand (a gap) to the right of segment <paramref name="index"/>, past any zones, whose own spacing counts.</summary>
        static Span? NextDemand(List<Segment> all, int index)
        {
            for (int i = index; i < all.Count; i++)
                if (all[i].right.HasValue && !all[i].right.Value.zone) return all[i].right;
            return null;
        }

        static void AddGroup(Group g, float lead, List<PatternItem> items)
        {
            foreach (var item in g.items)
            {
                var c = item.Copy();
                c.x += lead;
                c.x0 += lead;
                c.x1 += lead;
                items.Add(c);
            }
        }

        /// <summary>The finished layout against the rules that hold everywhere (the minimum spacings), with the gaps in.</summary>
        static bool SpacedRight(StagePlan plan, List<Span> placed, List<PatternItem> items, float d)
        {
            var spans = new List<Span>(placed);
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Gap) spans.Add(Demanding(f.x0, f.x1, f.style == 1 ? Demand.Double : Demand.Gap, 0f));
            spans.Sort((p, q) => p.x0.CompareTo(q.x0));
            for (int i = 1; i < spans.Count; i++)
                if (spans[i].x0 - spans[i - 1].x1 + 1e-3f < Spacing(spans[i - 1], spans[i], d, 0f)) return false;
            return true;
        }

        // ----------------------------------------------------------------------------------------------- the groups

        static float ExtraFor(PatternKind kind)
        {
            switch (kind)
            {
                case PatternKind.Tall: case PatternKind.Car: case PatternKind.Stack: return 1f;
                case PatternKind.Slide: return 2f;
                case PatternKind.Puddle: case PatternKind.SandPatch: return 1f;
                default: return 0f;
            }
        }

        static Group MakeGroup(Template t, HolidayStages.Stage st, Random rng)
        {
            switch (t.kind)
            {
                case PatternKind.Hop: return MakeRun(PatternKind.Hop, t.n, rng, new[] { 0.6f, 0.8f, 1f, 1.2f, 1.4f }, new[] { 0.3f, 0.35f, 0.4f, 0.45f, LowWallMax }, true);
                case PatternKind.Mid: return MakeRun(PatternKind.Mid, t.n, rng, new[] { 0.8f, 1f, 1.2f, 1.4f, 1.6f }, new[] { 0.6f, 0.7f, 0.8f, 0.9f, MidWallMax }, true);
                case PatternKind.Tall: return MakeTall(rng);
                case PatternKind.Crate: return MakeCrate();
                case PatternKind.Stack: return MakeStack();
                case PatternKind.Car: return MakeCar(rng);
                case PatternKind.Slide: return MakeSlide(st, rng);
                case PatternKind.Puddle: return MakeSlow(PatternKind.Puddle, rng, 3.5f, 5f);
                case PatternKind.SandPatch: return MakeSlow(PatternKind.SandPatch, rng, 6f, 9f);
                case PatternKind.Spring: return MakeSpring();
                default: throw new ArgumentOutOfRangeException("t", "no group is made for " + t.kind);
            }
        }

        static float Pick(Random rng, params float[] values) { return values[rng.Next(values.Length)]; }

        static void Solid(Group g, PatternKind kind, float x, float w, float h)
        {
            g.items.Add(new PatternItem { kind = kind, x = x, x0 = x - w * 0.5f, x1 = x + w * 0.5f, w = w, h = h });
        }

        /// <summary>
        /// A run of <paramref name="n"/> low (kerbs and borders) or mid (planters, rocks, hedges) things about
        /// 8 to 9.5 m apart (a hurdle run; the player sets the pace, but the ball has to be chipped over each).
        /// </summary>
        static Group MakeRun(PatternKind kind, int n, Random rng, float[] widths, float[] heights, bool tunnelOk)
        {
            var g = new Group { kind = kind, demand = Demand.Jump, tunnelOk = tunnelOk };
            float pitch = Range(rng, 8f, 9.5f), first = 0f, last = 0f, lastW = 0f;
            for (int i = 0; i < n; i++)
            {
                float w = Pick(rng, widths), h = Pick(rng, heights);
                float c = i == 0 ? w * 0.5f : first + i * pitch;
                if (i == 0) first = c;
                Solid(g, kind, c, w, h);
                last = c; lastW = w;
            }
            g.length = last + lastW * 0.5f;
            return g;
        }

        /// <summary>Head high: a double jump, over a high arc of coins.</summary>
        static Group MakeTall(Random rng)
        {
            var g = new Group { kind = PatternKind.Tall, demand = Demand.Double, extra = ExtraFor(PatternKind.Tall) };
            float w = Pick(rng, 0.7f, 0.85f, 1f), h = Pick(rng, 1.5f, 1.55f, 1.6f, 1.65f, TallWallMax);
            Solid(g, PatternKind.Tall, w * 0.5f, w, h);
            g.length = w;
            return g;
        }

        /// <summary>A crate (a sandcastle on the beach, a stack of cones on the site) a kicked ball smashes.</summary>
        static Group MakeCrate()
        {
            var g = new Group { kind = PatternKind.Crate, demand = Demand.Jump, tunnelOk = true };
            const float w = 1f;
            Solid(g, PatternKind.Crate, w * 0.5f, w, 0.7f);
            g.length = w;
            return g;
        }

        /// <summary>A pile of crates two high (a big sandcastle on the beach): a double jump over it, or a hard kick through it.</summary>
        static Group MakeStack()
        {
            var g = new Group { kind = PatternKind.Stack, demand = Demand.Double, extra = ExtraFor(PatternKind.Stack), tunnelOk = false };
            Solid(g, PatternKind.Stack, StackWidth * 0.5f, StackWidth, StackHeight);
            g.length = StackWidth;
            return g;
        }

        /// <summary>A parked car, 3.3 m long and 1.55 high: a double jump, or a hop onto the bonnet and another.</summary>
        static Group MakeCar(Random rng)
        {
            var g = new Group { kind = PatternKind.Car, demand = Demand.Double, extra = ExtraFor(PatternKind.Car) };
            g.items.Add(new PatternItem { kind = PatternKind.Car, x = CarLength * 0.5f, x0 = 0f, x1 = CarLength, w = CarLength, h = CarHeight, style = rng.Next(1000) });
            g.length = CarLength;
            return g;
        }

        /// <summary>A barrier to slide under, from the chapter's kit.</summary>
        static Group MakeSlide(HolidayStages.Stage st, Random rng)
        {
            var g = new Group { kind = PatternKind.Slide, demand = Demand.Slide, extra = ExtraFor(PatternKind.Slide) };
            var options = Slides[st.chapter - 1];
            SlideSpec spec = options[rng.Next(options.Length)];
            // The tunnel's deck is low: only the low barriers fit under it.
            if (st.Has(StageTraits.Tunnel))
            {
                var low = new List<SlideSpec>();
                foreach (var s in options) if (s.lowTop) low.Add(s);
                if (low.Count > 0) spec = low[rng.Next(low.Count)];
            }
            float len = spec.length;
            g.tunnelOk = spec.lowTop;
            g.items.Add(new PatternItem { kind = PatternKind.Slide, x = len * 0.5f, x0 = 0f, x1 = len, w = len, h = spec.top, look = spec.name });
            g.length = len;
            return g;
        }

        /// <summary>Puddles and soft sand: slow going.</summary>
        static Group MakeSlow(PatternKind kind, Random rng, float min, float max)
        {
            var g = new Group { kind = kind, demand = Demand.Slow, extra = ExtraFor(kind), tunnelOk = kind == PatternKind.Puddle };
            float len = Range(rng, min, max);
            g.items.Add(new PatternItem { kind = kind, x = len * 0.5f, x0 = 0f, x1 = len, w = len });
            g.length = len;
            return g;
        }

        /// <summary>A trampoline flush with the path; its coins go up the arc it throws the kid along (see AddCoins).</summary>
        static Group MakeSpring()
        {
            var g = new Group { kind = PatternKind.Spring, demand = Demand.Launch, extra = ExtraFor(PatternKind.Spring) };
            g.items.Add(new PatternItem { kind = PatternKind.Spring, x = 0.6f, x0 = 0f, x1 = 1.2f, w = 1.2f, h = 0.4f });
            g.length = 1.2f;
            return g;
        }

        // ----------------------------------------------------------------------------------------------- what the ground holds

        static bool IsSolidKind(PatternKind k)
        {
            return k == PatternKind.Hop || k == PatternKind.Mid || k == PatternKind.Tall || k == PatternKind.Crate || k == PatternKind.Stack || k == PatternKind.Car ||
                k == PatternKind.Slide || k == PatternKind.Puddle || k == PatternKind.SandPatch || k == PatternKind.Spring;
        }

        /// <summary>Things that stand in the kid's way as walls to get over (a coin must not hang inside these).</summary>
        static bool IsWallKind(PatternKind k)
        {
            return k == PatternKind.Hop || k == PatternKind.Mid || k == PatternKind.Tall || k == PatternKind.Crate || k == PatternKind.Stack || k == PatternKind.Car || k == PatternKind.Spring;
        }

        static bool IsLife(PatternKind k) { return k == PatternKind.Walkers || k == PatternKind.DogPatch; }

        /// <summary>
        /// The ground a stage and a layout already use, as [from, to] pairs: gaps, the tunnel with its approach and exit, the
        /// side streets, the fountains' bays, the solids, and the street life, balloons and power-up already placed.
        /// </summary>
        static List<float[]> Taken(StagePlan plan, List<PatternItem> items, bool forLife = false)
        {
            var list = new List<float[]>();
            foreach (var f in plan.furniture)
            {
                switch (f.kind)
                {
                    // Street life keeps off a gap's run-up and landing as well as the gap (BeatMargin is added again by the caller).
                    case PatternKind.Gap: list.Add(forLife ? new[] { f.x0 - (JumpReach.RunUp - BeatMargin), f.x1 + (JumpReach.Landing - BeatMargin) } : new[] { f.x0, f.x1 }); break;
                    case PatternKind.Tunnel: list.Add(new[] { f.x0 - TunnelApproach, f.x1 + TunnelAfter }); break;
                    case PatternKind.Crossing: list.Add(new[] { f.x0 - CrossingMargin, f.x1 + CrossingMargin }); break;
                    case PatternKind.Fountain: list.Add(new[] { f.x - FountainBay, f.x + FountainBay }); break;
                    case PatternKind.Checkpoint: list.Add(new[] { f.x - CheckpointBefore, f.x + CheckpointAfter }); break;
                }
            }
            foreach (var i in items)
            {
                // A trampoline's throw (and landing) is no place for a beat.
                if (forLife && i.kind == PatternKind.Spring) list.Add(new[] { i.x0, i.x + JumpReach.SpringLanding(Reach) - BeatMargin });
                else if (IsSolidKind(i.kind) || IsLife(i.kind)) list.Add(new[] { i.x0, i.x1 });
                else if (i.kind == PatternKind.PowerUp) list.Add(new[] { i.x - 1f, i.x + 1f });
                else if (i.kind == PatternKind.Balloon) list.Add(new[] { i.x - 0.8f, i.x + 0.8f });
            }
            return list;
        }

        /// <summary>The stretches of [a, b] at least <paramref name="clear"/> from everything in <paramref name="taken"/>.</summary>
        static List<float[]> Corridors(List<float[]> taken, float a, float b, float clear)
        {
            var spans = new List<float[]>(taken);
            spans.Sort((p, q) => p[0].CompareTo(q[0]));
            var free = new List<float[]>();
            float cursor = a;
            foreach (var s in spans)
            {
                if (s[0] - clear > cursor) free.Add(new[] { cursor, s[0] - clear });
                cursor = Math.Max(cursor, s[1] + clear);
            }
            if (b > cursor) free.Add(new[] { cursor, b });
            return free;
        }

        static bool InsideTunnel(StagePlan plan, float x)
        {
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Tunnel && x > f.x0 - TunnelApproach && x < f.x1 + TunnelAfter) return true;
            return false;
        }

        // ----------------------------------------------------------------------------------------------- street life

        /// <summary>Puts a beat of walkers or dogs in a stretch of open ground for each of <paramref name="life"/>; false if one doesn't fit.</summary>
        static bool AddLife(StagePlan plan, List<PatternItem> items, List<PatternKind> life, float a, float b, Random rng)
        {
            foreach (var kind in life)
            {
                var free = Corridors(Taken(plan, items, true), a, b, BeatMargin);
                var fit = new List<float[]>();
                float total = 0f;
                foreach (var f in free)
                    if (f[1] - f[0] >= MinBeat) { fit.Add(f); total += f[1] - f[0]; }
                if (fit.Count == 0) return false;
                // Any stretch that is long enough, the longer the likelier.
                float r = (float)rng.NextDouble() * total;
                float[] stretch = fit[fit.Count - 1];
                foreach (var f in fit)
                {
                    r -= f[1] - f[0];
                    if (r <= 0f) { stretch = f; break; }
                }
                float room = stretch[1] - stretch[0];
                float len = Range(rng, MinBeat, Math.Min(MaxBeat, room));
                float x0 = stretch[0] + (float)rng.NextDouble() * (room - len);
                items.Add(new PatternItem
                {
                    kind = kind, x = x0 + len * 0.5f, x0 = x0, x1 = x0 + len,
                    style = rng.Next(1000), a = kind == PatternKind.Walkers ? Range(rng, 0.9f, 1.4f) : 0f,
                });
            }
            return true;
        }

        // ----------------------------------------------------------------------------------------------- targets

        /// <summary>What hangs in the air for a chapter: balloons at home and on the site, paper lanterns in the market and the park, beach balls on the beach.</summary>
        static int BalloonStyle(int chapter) { return chapter == 2 || chapter == 5 ? 1 : chapter == 3 ? 2 : 0; }

        /// <summary>The floating targets: each in the middle of the barest open stretch, 2.3 to 3.4 m up, where a chip kick reaches.</summary>
        static bool AddBalloons(StagePlan plan, List<PatternItem> items, HolidayStages.Stage st, float a, float b, Random rng)
        {
            int count = BalloonCount(st.density);
            for (int n = 0; n < count; n++)
            {
                // Candidate spots every metre: clear of tunnels, side streets, bays, other balloons, and 4 m from a gap.
                var taken = Taken(plan, items);
                var bare = new List<float>();
                for (float x = a + 2f; x <= b - 2f; x += 1f)
                {
                    if (BalloonSpotOk(plan, items, taken, x)) bare.Add(x);
                }
                if (bare.Count == 0) return false;
                // The spot farthest from anything that is already a feature (a demand, street life, a target).
                var features = Features(plan, items);
                float bestX = bare[0], best = -1f;
                foreach (float x in bare)
                {
                    float near = 1e9f;
                    foreach (var f in features) near = Math.Min(near, x < f[0] ? f[0] - x : x > f[1] ? x - f[1] : 0f);
                    near += (float)rng.NextDouble() * 3f;
                    if (near > best) { best = near; bestX = x; }
                }
                float y = n == 0 ? Range(rng, 2.3f, 2.8f) : Range(rng, 2.5f, 3.4f);
                items.Add(new PatternItem { kind = PatternKind.Balloon, x = bestX, x0 = bestX, x1 = bestX, y = y, style = BalloonStyle(st.chapter), a = rng.Next(6) });
            }
            return true;
        }

        static bool BalloonSpotOk(StagePlan plan, List<PatternItem> items, List<float[]> taken, float x)
        {
            foreach (var f in plan.furniture)
            {
                if (f.kind == PatternKind.Gap && x > f.x0 - 4f && x < f.x1 + 4f) return false;
                if (f.kind == PatternKind.Tunnel && x > f.x0 - TunnelApproach - 1f && x < f.x1 + TunnelAfter + 1f) return false;
                if (f.kind == PatternKind.Crossing && x > f.x0 - CrossingMargin - 1f && x < f.x1 + CrossingMargin + 1f) return false;
                if (f.kind == PatternKind.Fountain && x > f.x - FountainBay - 1f && x < f.x + FountainBay + 1f) return false;
            }
            foreach (var i in items)
            {
                if (IsSolidKind(i.kind) && x > i.x0 - 1.5f && x < i.x1 + 1.5f) return false;
                if (i.kind == PatternKind.Balloon && Math.Abs(x - i.x) < 8f) return false;
            }
            return true;
        }

        /// <summary>The ground each thing that counts as something happening (a demand, street life, a target, a power-up, the tunnel) covers.</summary>
        static List<float[]> Features(StagePlan plan, List<PatternItem> items)
        {
            var list = new List<float[]>();
            foreach (var f in plan.furniture)
            {
                if (f.kind == PatternKind.Gap || f.kind == PatternKind.Tunnel || f.kind == PatternKind.Crossing) list.Add(new[] { f.x0, f.x1 });
                else if (f.kind == PatternKind.Fountain) list.Add(new[] { f.x - 1f, f.x + 1f });
            }
            foreach (var i in items)
                if (IsSolidKind(i.kind) || IsLife(i.kind)) list.Add(new[] { i.x0, i.x1 });
                else if (i.kind == PatternKind.Balloon || i.kind == PatternKind.PowerUp || (i.kind == PatternKind.Star && i.style == 0)) list.Add(new[] { i.x, i.x });
            return list;
        }

        // ----------------------------------------------------------------------------------------------- pickups

        /// <summary>
        /// A power-up floating in the widest open stretch: in every layout of every second stage (so at least one in any two
        /// stages, whichever layouts load), and in about one in two of the others. A shield when a gap is coming, else a magnet or a turbo.
        /// </summary>
        static void AddPowerUp(StagePlan plan, List<PatternItem> items, float a, float b, Random rng, int variant)
        {
            // Drawn either way, so the layouts' other choices don't depend on it.
            double roll = rng.NextDouble();
            float height = Range(rng, 1.0f, 1.6f);
            int pick = rng.Next(2);
            if (plan.stage % 2 != 0 && roll >= 0.5) return;
            var free = Corridors(Taken(plan, items), a, b, PowerUpClear);
            float bestLen = 0f, at = 0f;
            foreach (var f in free)
            {
                float len = f[1] - f[0];
                float mid = (f[0] + f[1]) * 0.5f;
                if (len <= bestLen || InsideTunnel(plan, mid)) continue;
                bestLen = len; at = mid;
            }
            if (bestLen < 0.5f) return;
            bool gapAhead = false;
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Gap && f.x0 > at && f.x0 < at + 30f) gapAhead = true;
            int kind = gapAhead ? (int)PowerUpShield : (plan.stage + variant + pick) % 2 == 0 ? (int)PowerUpMagnet : (int)PowerUpTurbo;
            items.Add(new PatternItem { kind = PatternKind.PowerUp, x = at, x0 = at, x1 = at, y = height, style = kind });
        }

        // PowerUpKind values (Magnet, Shield, Turbo), repeated here so this file stays free of the runtime types.
        const int PowerUpMagnet = 0, PowerUpShield = 1, PowerUpTurbo = 2;

        /// <summary>
        /// An occasional bonus detour: an arc of coins up where only a double jump gets, with a star at the top. The arc follows a
        /// real double jump (JumpReach), over open ground clear of everything else. One in each layout where there is room.
        /// </summary>
        static void AddDetour(StagePlan plan, List<PatternItem> items, float a, float b, Random rng, int variant)
        {
            double roll = rng.NextDouble();
            if (HolidayStages.All[plan.stage].density < 0.4f || roll >= 0.7) return;
            JumpReach.Flight dj = JumpReach.DoubleJump(Reach);
            float need = dj.distance + 3f;
            var free = Corridors(Taken(plan, items), a, b, 2f);
            var fit = new List<float[]>();
            foreach (var f in free) if (f[1] - f[0] >= need && !InsideTunnel(plan, (f[0] + f[1]) * 0.5f)) fit.Add(f);
            if (fit.Count == 0) return;
            var stretch = fit[rng.Next(fit.Count)];
            float takeoff = stretch[0] + 1f + (float)rng.NextDouble() * (stretch[1] - stretch[0] - need);
            float[] xs, ys;
            JumpReach.Path(Reach, Reach.runSpeed, JumpReach.JumpKind.Double, 7, out xs, out ys);
            float apexX = dj.apexTime * Reach.runSpeed;
            for (int k = 0; k < xs.Length; k++)
                items.Add(new PatternItem { kind = PatternKind.Coin, x = takeoff + xs[k], x0 = takeoff + xs[k], x1 = takeoff + xs[k], y = ys[k] + 0.9f });
            // The star at the very top of it: only a double jump reaches this high.
            float starX = takeoff + apexX, starY = dj.apex + 1.25f;
            items.Add(new PatternItem { kind = PatternKind.Star, x = starX, x0 = starX, x1 = starX, y = starY, count = 5 });
        }

        // ----------------------------------------------------------------------------------------------- coins

        static PatternItem MakeCoin(float x, float y, int style)
        {
            return new PatternItem { kind = PatternKind.Coin, x = x, x0 = x, x1 = x, y = y, style = style };
        }

        /// <summary>
        /// Coins on the way: an arc along a real jump over every wall and gap (a double jump over the tall things and the wide gaps), a
        /// row under every barrier, on the slow ground and on top of the broad walls, the trampolines' throw with a star at the top of it
        /// if the air jump is used there, and between them all a trail every 1.6 to 2.4 m in gentle waves. Nothing hangs inside a
        /// solid or low over a gap.
        /// </summary>
        static void AddCoins(StagePlan plan, List<PatternItem> items, float a, float b, Random rng)
        {
            var coins = new List<PatternItem>();
            JumpReach.Flight single = JumpReach.SingleJump(Reach), dbl = JumpReach.DoubleJump(Reach);
            float singleApexX = single.apexTime * Reach.runSpeed, dblApexX = dbl.apexTime * Reach.runSpeed;
            // Where the arcs and rows go (kept clear of the trail).
            var arcZones = new List<float[]>();

            foreach (var f in plan.furniture)
            {
                if (f.kind == PatternKind.Gap)
                {
                    bool wide = f.style == 1;
                    float takeoff = f.x0 - 0.4f;
                    float[] xs, ys;
                    int n = wide ? 7 : 5;
                    JumpReach.Path(Reach, Reach.runSpeed, wide ? JumpReach.JumpKind.Double : JumpReach.JumpKind.Single, n, out xs, out ys);
                    for (int k = 0; k < n; k++)
                    {
                        float x = takeoff + xs[k], y = ys[k] + 0.6f;
                        // Low over the gap is no place for a coin: a kid walking off the edge for it would fall.
                        if (x > f.x0 + 0.35f && x < f.x1 - 0.35f && y < 0.95f) continue;
                        coins.Add(MakeCoin(x, y, 0));
                    }
                    float len = wide ? dbl.distance : single.distance;
                    arcZones.Add(new[] { f.x0 - 1.4f, takeoff + len + 1.0f });
                }
                else if (f.kind == PatternKind.Fountain)
                {
                    for (int k = 0; k < 5; k++)
                    {
                        float t = k / 4f;
                        coins.Add(MakeCoin(f.x - 2.5f + 5f * t, 1.2f + 4f * t * (1f - t) * 1.4f, 0));
                    }
                    coins.Add(MakeCoin(f.x, 3.2f, 0));
                    arcZones.Add(new[] { f.x - 3.5f, f.x + 3.5f });
                }
            }

            foreach (var i in items)
            {
                switch (i.kind)
                {
                    case PatternKind.Hop:
                    case PatternKind.Mid:
                    case PatternKind.Crate:
                    {
                        float c = (i.x0 + i.x1) * 0.5f;
                        // (A kid who climbs a broad one and stands on it still reaches the arc: its coins hang within the body.)
                        PathCoins(coins, c - singleApexX, JumpReach.JumpKind.Single, 5, 0.6f, 0, i.kind == PatternKind.Hop ? 0.8f : 1f);
                        arcZones.Add(new[] { i.x0 - 1.5f, i.x1 + 1.5f });
                        break;
                    }
                    case PatternKind.Tall:
                    case PatternKind.Stack:
                    {
                        float c = (i.x0 + i.x1) * 0.5f;
                        PathCoins(coins, c - dblApexX, JumpReach.JumpKind.Double, 6, 0.6f, 0, 1f);
                        arcZones.Add(new[] { i.x0 - 2.5f, i.x1 + 2.0f });
                        break;
                    }
                    case PatternKind.Car:
                        // The bonnet, the roof and the bonnet again: the two hops a car takes.
                        coins.Add(MakeCoin(i.x0 + 0.5f, 0.95f + 0.7f, 0));
                        coins.Add(MakeCoin(i.x0 + 1.3f, CarHeight + 0.7f, 0));
                        coins.Add(MakeCoin(i.x0 + 1.9f, CarHeight + 0.7f, 0));
                        coins.Add(MakeCoin(i.x0 + 2.5f, CarHeight + 0.7f, 0));
                        coins.Add(MakeCoin(i.x1 + 0.5f, 0.95f + 0.7f, 0));
                        arcZones.Add(new[] { i.x0 - 1.5f, i.x1 + 1.5f });
                        break;
                    case PatternKind.Slide:
                    {
                        // Low under the barrier: a sliding kid (or a rolling ball) collects them.
                        float len = i.x1 - i.x0;
                        int n = Math.Max(3, Math.Min(6, (int)Math.Round(len / 0.8f)));
                        for (int k = 0; k < n; k++) coins.Add(MakeCoin(Lerp(i.x0 + 0.4f, i.x1 - 0.4f, n == 1 ? 0.5f : k / (float)(n - 1)), 0.4f, 0));
                        arcZones.Add(new[] { i.x0 - 1.0f, i.x1 + 1.0f });
                        break;
                    }
                    case PatternKind.Puddle:
                    case PatternKind.SandPatch:
                    {
                        int n = i.kind == PatternKind.Puddle ? 3 : 4;
                        for (int k = 0; k < n; k++) coins.Add(MakeCoin(Lerp(i.x0 + 0.7f, i.x1 - 0.7f, n == 1 ? 0.5f : k / (float)(n - 1)), 0.6f, 0));
                        arcZones.Add(new[] { i.x0 - 0.5f, i.x1 + 0.5f });
                        break;
                    }
                    case PatternKind.Spring:
                    {
                        // Up the throw: along the path of a kid walking on over the pad, a star at the top of it (with the air jump).
                        float launch = i.x + JumpReach.SpringLaunchOffset;
                        float[] xs, ys;
                        JumpReach.Path(Reach, Reach.runSpeed, JumpReach.JumpKind.Spring, 8, out xs, out ys);
                        for (int k = 0; k < xs.Length; k++) coins.Add(MakeCoin(launch + xs[k], ys[k] + 0.6f, 1));
                        JumpReach.Flight sd = JumpReach.Of(Reach, Reach.runSpeed, JumpReach.JumpKind.SpringDouble);
                        float topX = launch + sd.apexTime * Reach.runSpeed;
                        coins.Add(new PatternItem { kind = PatternKind.Star, x = topX, x0 = topX, x1 = topX, y = sd.apex + 1.25f, count = 5, style = 1 });
                        arcZones.Add(new[] { i.x0 - 1.5f, i.x + JumpReach.SpringLanding(Reach) });
                        break;
                    }
                }
            }

            // The trail: between everything else, from the stage's start to its end, every 1.6 to 2.4 m, in gentle waves.
            var taken = new List<float[]>();
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Gap) taken.Add(new[] { f.x0, f.x1 });
            foreach (var i in items)
                if (IsSolidKind(i.kind) || i.kind == PatternKind.Star) taken.Add(new[] { i.x0, i.x1 });
            taken.AddRange(arcZones);
            foreach (var c in coins) taken.Add(new[] { c.x - 1.1f, c.x + 1.1f });
            foreach (var i in items) if (i.kind == PatternKind.Coin || i.kind == PatternKind.Star) taken.Add(new[] { i.x - 1.1f, i.x + 1.1f });
            var free = Corridors(taken, plan.from + 5f, plan.to - 3f, 0.6f);
            float phase = (float)rng.NextDouble() * 6.28f;
            foreach (var f in free)
            {
                if (f[1] - f[0] < 1.5f) continue;
                float x = f[0] + (float)rng.NextDouble() * 0.8f;
                while (x <= f[1])
                {
                    coins.Add(MakeCoin(x, 0.8f + 0.3f * (float)Math.Sin(x * 0.7f + phase), 0));
                    x += Range(rng, 1.6f, 2.4f);
                }
            }

            // Nothing hangs inside a solid.
            coins.RemoveAll(c => CoinInside(items, c));
            foreach (var c in coins) items.Add(c);
        }

        /// <summary>The height of the solid <paramref name="o"/> at x (a parked car has its bonnet at 0.95 m and its cabin at 1.55).</summary>
        static float TopAt(PatternItem o, float x)
        {
            if (o.kind != PatternKind.Car) return o.h;
            float cabin = (o.x0 + o.x1) * 0.5f - 0.17f;
            return Math.Abs(x - cabin) <= 1.05f ? CarHeight : 0.95f;
        }

        /// <summary>True if a coin hangs inside a solid (or inside a barrier's overhead bulk) of the layout.</summary>
        static bool CoinInside(List<PatternItem> items, PatternItem c)
        {
            foreach (var o in items)
            {
                if (!IsSolidKind(o.kind) || c.x <= o.x0 - 0.1f || c.x >= o.x1 + 0.1f) continue;
                if (o.kind == PatternKind.Slide) { if (c.y + 0.28f > SlideClearance) return true; }
                else if (o.kind == PatternKind.Puddle || o.kind == PatternKind.SandPatch) continue;
                else if (c.y < TopAt(o, c.x) + 0.25f) return true;
            }
            return false;
        }

        /// <summary>
        /// Coins along a flight of the given kind that takes off at <paramref name="takeoff"/>, <paramref name="count"/> of them at the
        /// body's middle (<paramref name="lift"/> above the feet), the height scaled by <paramref name="scale"/>.
        /// </summary>
        static void PathCoins(List<PatternItem> coins, float takeoff, JumpReach.JumpKind kind, int count, float lift, int style, float scale)
        {
            float[] xs, ys;
            JumpReach.Path(Reach, Reach.runSpeed, kind, count, out xs, out ys);
            for (int k = 0; k < count; k++) coins.Add(MakeCoin(takeoff + xs[k], ys[k] * scale + lift, style));
        }

        // ----------------------------------------------------------------------------------------------- the checks

        /// <summary>
        /// Checks a layout against the rules: the clear run-ins, the spacing between demands, the hurdle pitch, the size classes
        /// (nothing over what a jump gets over; no gap wider than the jump that crosses it), the run-up and landing a gap has, the
        /// tunnel's and the bays' keep-out ground, the street life, targets and power-ups on open ground, no coin inside a solid
        /// or low over a gap, a coin arc over every tall thing, and that no long stretch is bare. Returns the problems found (none: fair).
        /// </summary>
        public static List<string> Validate(StagePlan plan, int variant)
        {
            var problems = new List<string>();
            var st = HolidayStages.All[plan.stage];
            var items = plan.layouts[variant];
            float d = st.density;
            string tag = "stage " + (plan.stage + 1) + " layout " + (char)('A' + variant) + ": ";
            const float eps = 1e-3f;

            // ------ gaps: how wide, where, and what ground they have before and after
            var spans = new List<Span>();
            var kinds = new List<PatternKind>();
            foreach (var f in plan.furniture)
            {
                if (f.kind != PatternKind.Gap) continue;
                bool wide = f.style == 1;
                float w = f.x1 - f.x0;
                if (wide && !(d > 0.5f)) problems.Add(tag + "a wide gap at density " + d);
                if (!wide && w > PlainGapMax + eps) problems.Add(tag + "gap width " + w + " is over what one jump crosses (" + PlainGapMax + ")");
                if (!wide && w < PlainGapMin - eps) problems.Add(tag + "gap width " + w + " is under " + PlainGapMin);
                if (wide && w > WideGapMax + eps) problems.Add(tag + "wide gap width " + w + " is over what a double jump crosses (" + WideGapMax + ")");
                if (wide && w < WideGapMin - eps) problems.Add(tag + "wide gap width " + w + " is under " + WideGapMin);
                if (f.x0 < plan.firstX - eps || f.x1 > plan.lastX + eps) problems.Add(tag + "a gap outside the open stretch");
                spans.Add(Demanding(f.x0, f.x1, wide ? Demand.Double : Demand.Gap, 0f));
                kinds.Add(PatternKind.Gap);
            }
            foreach (var i in items)
            {
                if (!IsSolidKind(i.kind)) continue;
                spans.Add(Demanding(i.x0, i.x1, DemandOf(i), ExtraFor(i.kind)));
                kinds.Add(i.kind);
                if (i.x0 < plan.firstX - eps) problems.Add(tag + i.kind + " starts at " + i.x0 + ", before " + plan.firstX);
                if (i.x1 > plan.lastX + eps) problems.Add(tag + i.kind + " ends at " + i.x1 + ", after " + plan.lastX);
            }
            var order = new List<int>();
            for (int k = 0; k < spans.Count; k++) order.Add(k);
            order.Sort((p, q) => spans[p].x0.CompareTo(spans[q].x0));
            for (int n = 1; n < order.Count; n++)
            {
                var p = spans[order[n - 1]];
                var q = spans[order[n]];
                var kp = kinds[order[n - 1]];
                var kq = kinds[order[n]];
                float gap = q.x0 - p.x1;
                // A hurdle run: two or three low (or mid) things about 8 to 9.5 m apart, centre to centre.
                if ((kp == PatternKind.Hop && kq == PatternKind.Hop || kp == PatternKind.Mid && kq == PatternKind.Mid) && gap < MinSame)
                {
                    float pitch = (q.x0 + q.x1) * 0.5f - (p.x0 + p.x1) * 0.5f;
                    if (pitch < 7.5f || pitch > 10f) problems.Add(tag + "hurdle pitch " + pitch);
                    continue;
                }
                float need = Spacing(p, q, d, 0f);
                if (gap + eps < need) problems.Add(tag + kp + " to " + kq + " are " + gap + " m apart, wanted " + need);
                if (gap + eps < (p.demand == q.demand ? MinSame : MinDifferent)) problems.Add(tag + "only " + gap + " m between " + kp + " and " + kq);
            }
            // A gap needs 6 m of clear ground before it and 4 after it, with no wall in either.
            foreach (var f in plan.furniture)
            {
                if (f.kind != PatternKind.Gap) continue;
                foreach (var i in items)
                {
                    if (!IsSolidKind(i.kind) && !IsLife(i.kind)) continue;
                    if (i.x1 > f.x0 - JumpReach.RunUp && i.x0 < f.x0) problems.Add(tag + i.kind + " within " + JumpReach.RunUp + " m before a gap (no run-up)");
                    if (i.x0 < f.x1 + JumpReach.Landing && i.x1 > f.x1) problems.Add(tag + i.kind + " within " + JumpReach.Landing + " m after a gap (no landing)");
                    if (i.x0 < f.x1 && i.x1 > f.x0) problems.Add(tag + i.kind + " over a gap");
                }
                if (f.x0 - JumpReach.RunUp < plan.from) problems.Add(tag + "a gap without a run-up in its stage");
                if (f.x1 + JumpReach.Landing > plan.to) problems.Add(tag + "a gap without a landing in its stage");
                // The tunnel's mouth is no run-up (dark, and 2 m of keep-out), and its approach is no landing.
                foreach (var t in plan.furniture)
                {
                    if (t.kind != PatternKind.Tunnel) continue;
                    if (f.x0 >= t.x1 && f.x0 - t.x1 < JumpReach.RunUp) problems.Add(tag + "a gap " + (f.x0 - t.x1).ToString("0.0") + " m after the tunnel (no run-up)");
                    if (f.x1 <= t.x0 && t.x0 - f.x1 < JumpReach.Landing) problems.Add(tag + "the tunnel " + (t.x0 - f.x1).ToString("0.0") + " m after a gap (no landing)");
                    if (f.x1 > t.x0 && f.x0 < t.x1) problems.Add(tag + "a gap in the tunnel");
                }
            }

            // The checkpoint: the kid is put down there with the ball a metre ahead, so nothing stands near it.
            foreach (var c in plan.furniture)
            {
                if (c.kind != PatternKind.Checkpoint) continue;
                if (c.x < plan.firstX || c.x > plan.lastX) problems.Add(tag + "the middle checkpoint is outside the open stretch");
                if (InsideTunnel(plan, c.x)) problems.Add(tag + "the middle checkpoint in the tunnel");
                foreach (var i in items)
                    if ((IsSolidKind(i.kind) || IsLife(i.kind)) && i.x1 > c.x - CheckpointBefore + eps && i.x0 < c.x + CheckpointAfter - eps) problems.Add(tag + i.kind + " by the middle checkpoint");
                foreach (var f in plan.furniture)
                    if ((f.kind == PatternKind.Gap || f.kind == PatternKind.Tunnel || f.kind == PatternKind.Crossing || f.kind == PatternKind.Fountain)
                        && f.x1 > c.x - CheckpointBefore + eps && f.x0 < c.x + CheckpointAfter - eps) problems.Add(tag + f.kind + " by the middle checkpoint");
            }

            // ------ the size of things
            foreach (var i in items)
            {
                if (i.kind == PatternKind.Hop && (i.h < 0.3f - eps || i.h > LowWallMax + eps)) problems.Add(tag + "hop height " + i.h);
                if (i.kind == PatternKind.Mid && (i.h < 0.6f - eps || i.h > MidWallMax + eps)) problems.Add(tag + "mid height " + i.h);
                if (i.kind == PatternKind.Tall && (i.h < 1.5f - eps || i.h > TallWallMax + eps)) problems.Add(tag + "tall height " + i.h);
                if (i.kind == PatternKind.Stack && (i.h > TallWallMax + eps || i.w > 2f)) problems.Add(tag + "stack of " + i.w + " x " + i.h);
                if (i.kind == PatternKind.Car && i.h > WallMax + eps) problems.Add(tag + "car height " + i.h);
                if ((i.kind == PatternKind.Hop || i.kind == PatternKind.Mid || i.kind == PatternKind.Tall || i.kind == PatternKind.Crate || i.kind == PatternKind.Stack || i.kind == PatternKind.Car) && i.h > WallMax + eps)
                    problems.Add(tag + i.kind + " is " + i.h + " m high, over " + WallMax);
                if (i.kind == PatternKind.Slide)
                {
                    float length = i.x1 - i.x0;
                    if (length > JumpReach.MaxSlideBarrier(Reach) + eps) problems.Add(tag + "a barrier " + length + " m long is longer than a slide carries the kid");
                    if (SlideClearance < JumpReach.MinSlideClearance(Reach) - eps) problems.Add(tag + "a barrier with only " + SlideClearance + " m under it");
                }
                // The ball goes over every wall by a kick: it has to have room to be lined up (a walk-up of 4 m at the least).
                if ((i.kind == PatternKind.Tall || i.kind == PatternKind.Stack || i.kind == PatternKind.Car) && i.h > JumpReach.MaxWallWithoutKick(Reach))
                    foreach (var o in items)
                        if (IsSolidKind(o.kind) && o != i && o.x1 > i.x0 - 4f && o.x1 <= i.x0) problems.Add(tag + o.kind + " within 4 m before a " + i.kind + " (no room for the chip)");
            }

            // ------ keep-out ground: nothing stands in a crossing, the fountain's bay or the tunnel's ends
            foreach (var f in plan.furniture)
            {
                float z0 = float.NaN, z1 = float.NaN;
                switch (f.kind)
                {
                    case PatternKind.Crossing: z0 = f.x0 - CrossingMargin; z1 = f.x1 + CrossingMargin; break;
                    case PatternKind.Fountain: z0 = f.x - FountainBay; z1 = f.x + FountainBay; break;
                    case PatternKind.Tunnel: z0 = f.x0 - TunnelApproach; z1 = f.x0 + TunnelLeadIn; break;
                }
                if (!float.IsNaN(z0))
                    foreach (var i in items)
                        if ((IsSolidKind(i.kind) || IsLife(i.kind)) && i.x1 > z0 && i.x0 < z1) problems.Add(tag + i.kind + " inside the " + f.kind + " bay");
                if (f.kind != PatternKind.Tunnel) continue;
                foreach (var i in items)
                {
                    if (IsLife(i.kind) && i.x1 > f.x0 - TunnelApproach && i.x0 < f.x1 + TunnelAfter) problems.Add(tag + i.kind + " in the tunnel");
                    if (i.kind == PatternKind.Balloon && i.x > f.x0 - TunnelApproach && i.x < f.x1 + TunnelAfter) problems.Add(tag + "a balloon in the tunnel");
                    if (i.kind == PatternKind.PowerUp && i.x > f.x0 - TunnelApproach && i.x < f.x1 + TunnelAfter) problems.Add(tag + "a power-up in the tunnel");
                    if (!IsSolidKind(i.kind)) continue;
                    if (i.x1 > f.x1 - TunnelLeadOut && i.x0 < f.x1 + TunnelAfter) problems.Add(tag + i.kind + " at the tunnel's exit");
                    if (i.x0 < f.x0 + TunnelLeadIn || i.x1 > f.x1 - TunnelLeadOut) continue;
                    if (i.kind == PatternKind.Tall || i.kind == PatternKind.Car || i.kind == PatternKind.Stack || i.kind == PatternKind.Spring) problems.Add(tag + i.kind + " inside the tunnel");
                    if (i.kind == PatternKind.Slide && i.h > 2.1f) problems.Add(tag + "a tall barrier inside the tunnel");
                    // A double jump has to clear the deck, with the head and room to spare.
                    if (JumpReach.DoubleJumpHeadroom(Reach) + 0.3f > TunnelHeight) problems.Add(tag + "the tunnel's deck is too low for a double jump");
                }
            }
            // A trampoline throws the kid up and ahead: nothing stands in the way of that, or over it.
            foreach (var s in items)
            {
                if (s.kind != PatternKind.Spring) continue;
                foreach (var i in items)
                {
                    if (i == s || !(IsSolidKind(i.kind) || IsLife(i.kind))) continue;
                    if (i.x1 > s.x1 && i.x0 < s.x + JumpReach.SpringLanding(Reach)) problems.Add(tag + i.kind + " within the throw of a trampoline");
                }
                foreach (var f in plan.furniture)
                    if ((f.kind == PatternKind.Gap || f.kind == PatternKind.Tunnel) && f.x1 > s.x1 && f.x0 < s.x + JumpReach.SpringLanding(Reach)) problems.Add(tag + "a " + f.kind + " within the throw of a trampoline");
            }

            // ------ street life, targets, power-ups: on open ground
            int beats = 0, balloons = 0;
            foreach (var i in items)
            {
                if (IsLife(i.kind))
                {
                    beats++;
                    if (i.x0 < plan.firstX - eps || i.x1 > plan.lastX + eps) problems.Add(tag + i.kind + " outside the open stretch");
                    float len = i.x1 - i.x0;
                    if (len < MinBeat - eps || len > MaxBeat + eps) problems.Add(tag + i.kind + " beat of " + len + " m");
                    foreach (var f in plan.furniture)
                        if (f.kind == PatternKind.Gap && i.x1 + BeatMargin > f.x0 && i.x0 - BeatMargin < f.x1) problems.Add(tag + i.kind + " over or beside a gap");
                    foreach (var o in items)
                        if (o != i && IsSolidKind(o.kind) && i.x1 + BeatMargin - eps > o.x0 && i.x0 - BeatMargin + eps < o.x1) problems.Add(tag + i.kind + " inside or beside a " + o.kind);
                    foreach (var o in items)
                        if (o != i && IsLife(o.kind) && i.x1 + BeatMargin - eps > o.x0 && i.x0 - BeatMargin + eps < o.x1) problems.Add(tag + i.kind + " on another beat");
                }
                else if (i.kind == PatternKind.Balloon)
                {
                    balloons++;
                    if (i.y < 2.2f - eps || i.y > 3.6f + eps) problems.Add(tag + "balloon at height " + i.y);
                    foreach (var f in plan.furniture)
                    {
                        if (f.kind == PatternKind.Gap && i.x > f.x0 - 4f + eps && i.x < f.x1 + 4f - eps) problems.Add(tag + "a balloon within 4 m of a gap");
                        if (f.kind == PatternKind.Crossing && i.x > f.x0 && i.x < f.x1) problems.Add(tag + "a balloon over a crossing");
                    }
                    foreach (var o in items)
                        if (IsSolidKind(o.kind) && i.x > o.x0 - 1.5f + eps && i.x < o.x1 + 1.5f - eps) problems.Add(tag + "a balloon within 1.5 m of a " + o.kind);
                }
                else if (i.kind == PatternKind.PowerUp)
                {
                    if (i.y < 1f - eps || i.y > 1.6f + eps) problems.Add(tag + "power-up at height " + i.y);
                    foreach (var s in spans)
                        if (i.x > s.x0 - PowerUpClear + eps && i.x < s.x1 + PowerUpClear - eps) problems.Add(tag + "power-up within " + PowerUpClear + " m of an obstacle");
                    foreach (var o in items)
                        if (IsLife(o.kind) && i.x > o.x0 - 1f && i.x < o.x1 + 1f) problems.Add(tag + "a power-up on a beat");
                }
            }
            if (beats != plan.life) problems.Add(tag + beats + " beats of street life, the plan says " + plan.life);

            // ------ coins and stars: not inside a solid, not low over a gap, not out of reach
            foreach (var c in items)
            {
                if (c.kind != PatternKind.Coin && c.kind != PatternKind.Star) continue;
                bool onThrow = c.style == 1;
                float limit = onThrow ? JumpReach.HighestCoin(Reach) + 1.5f : JumpReach.HighestCoin(Reach);
                if (c.y > limit + eps) problems.Add(tag + "a coin at " + c.y + " m, higher than anyone reaches (" + limit + ")");
                if (c.y < 0.3f - eps) problems.Add(tag + "a coin at " + c.y + " m, in the ground");
                if (CoinInside(items, c)) problems.Add(tag + "a coin inside a solid at x " + c.x + ", y " + c.y);
                foreach (var f in plan.furniture)
                    if (f.kind == PatternKind.Gap && c.x > f.x0 + 0.35f && c.x < f.x1 - 0.35f && c.y < 0.95f - eps) problems.Add(tag + "a coin low over a gap at x " + c.x);
            }
            foreach (var i in items)
            {
                if (i.kind != PatternKind.Tall && i.kind != PatternKind.Stack) continue;
                bool arc = false;
                foreach (var c in items)
                    if (c.kind == PatternKind.Coin && c.x > i.x0 - 1.5f && c.x < i.x1 + 1.5f && c.y > i.h + 0.5f) arc = true;
                if (!arc) problems.Add(tag + "a " + i.kind + " without an arc of coins over it");
            }

            // ------ something happens on every stretch
            var features = Features(plan, items);
            features.Sort((p, q) => p[0].CompareTo(q[0]));
            float cursor = plan.firstX;
            foreach (var f in features)
            {
                if (f[1] < plan.firstX || f[0] > plan.lastX) continue;
                if (f[0] - cursor > MaxBare) problems.Add(tag + "bare ground from " + (cursor - plan.from).ToString("0") + " to " + (f[0] - plan.from).ToString("0") + " m of the stage");
                cursor = Math.Max(cursor, f[1]);
            }
            if (plan.lastX - cursor > MaxBare) problems.Add(tag + "bare ground from " + (cursor - plan.from).ToString("0") + " m of the stage to its end");

            // ------ the stage shows each of its traits
            Need(problems, tag, st, StageTraits.Steps, items, PatternKind.Hop);
            Need(problems, tag, st, StageTraits.Crates, items, PatternKind.Mid);
            Need(problems, tag, st, StageTraits.Crates, items, PatternKind.Crate);
            Need(problems, tag, st, StageTraits.Cars, items, PatternKind.Car);
            Need(problems, tag, st, StageTraits.Awnings, items, PatternKind.Slide);
            Need(problems, tag, st, StageTraits.Puddles, items, PatternKind.Puddle);
            Need(problems, tag, st, StageTraits.SoftSand, items, PatternKind.SandPatch);
            Need(problems, tag, st, StageTraits.Springboards, items, PatternKind.Spring);
            if (plan.life > 0)
            {
                Need(problems, tag, st, StageTraits.Pedestrians, items, PatternKind.Walkers);
                Need(problems, tag, st, StageTraits.Dogs, items, PatternKind.DogPatch);
            }
            NeedFurniture(problems, tag, st, StageTraits.Gaps, plan, PatternKind.Gap);
            NeedFurniture(problems, tag, st, StageTraits.Tunnel, plan, PatternKind.Tunnel);
            NeedFurniture(problems, tag, st, StageTraits.Fountain, plan, PatternKind.Fountain);
            NeedFurniture(problems, tag, st, StageTraits.Crossing, plan, PatternKind.Crossing);
            NeedFurniture(problems, tag, st, StageTraits.Tide, plan, PatternKind.TideArea);
            NeedFurniture(problems, tag, st, StageTraits.Seagulls, plan, PatternKind.Gull);
            if (balloons < 2 || balloons > 4) problems.Add(tag + balloons + " balloons");
            return problems;
        }

        static void Need(List<string> problems, string tag, HolidayStages.Stage st, StageTraits trait, List<PatternItem> items, PatternKind kind)
        {
            if (!st.Has(trait)) return;
            foreach (var i in items) if (i.kind == kind) return;
            problems.Add(tag + "no " + kind + " for " + trait);
        }

        static void NeedFurniture(List<string> problems, string tag, HolidayStages.Stage st, StageTraits trait, StagePlan plan, PatternKind kind)
        {
            if (!st.Has(trait)) return;
            foreach (var i in plan.furniture) if (i.kind == kind) return;
            problems.Add(tag + "no " + kind + " for " + trait);
        }

        static Demand DemandOf(PatternItem i)
        {
            switch (i.kind)
            {
                case PatternKind.Tall: case PatternKind.Car: case PatternKind.Stack: return Demand.Double;
                case PatternKind.Slide: return Demand.Slide;
                case PatternKind.Puddle: case PatternKind.SandPatch: return Demand.Slow;
                case PatternKind.Spring: return Demand.Launch;
                default: return Demand.Jump;
            }
        }

        // ----------------------------------------------------------------------------------------------- helpers

        static float Range(Random rng, float min, float max) { return min + (float)rng.NextDouble() * (max - min); }

        static void Shuffle<T>(List<T> list, Random rng)
        {
            for (int i = list.Count - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                T t = list[i]; list[i] = list[j]; list[j] = t;
            }
        }
    }
}
