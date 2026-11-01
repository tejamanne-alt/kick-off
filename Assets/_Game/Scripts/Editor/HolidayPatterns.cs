using System;
using System.Collections.Generic;
using DribbleToSchool.Holiday;

namespace DribbleToSchool.EditorTools
{
    /// <summary>What a pattern item is. The furniture kinds are the same in all three layouts of a stage.</summary>
    public enum PatternKind
    {
        // Furniture: part of the stage, whichever layout is on.
        Gap, Tunnel, Crossing, Fountain, Walkers, DogPatch, TideArea, Gull, Cranes,
        // Things in the kid's way.
        Hop, Mid, Tall, Crate, Car, Slide, Puddle, SandPatch, Spring, Pipes,
        // Pickups.
        Coin, CoinRow, CoinArc, PowerUp,
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
        /// <summary>Height of a coin, a row, a power-up, a gull.</summary>
        public float y;
        /// <summary>How far an arc rises above its ends.</summary>
        public float rise;
        public int count;
        /// <summary>A palette index the builder picks from: car paint, coat, fur, power-up kind; for a gap, 1 if it is the wide kind.</summary>
        public int style;
        /// <summary>A <c>TrackBuilder.SlideLook</c> name.</summary>
        public string look;
        /// <summary>Gap: water instead of a pit.</summary>
        public bool flag;
        /// <summary>Free parameters: pipes (interval, despawn x), tide (period, phase), gull (phase), walkers (speed), fountain (strength).</summary>
        public float a, b;

        public PatternItem Copy() { return (PatternItem)MemberwiseClone(); }
    }

    /// <summary>A stage's plan: the furniture it always has, and three alternative layouts of obstacles, coins and power-ups.</summary>
    public sealed class StagePlan
    {
        public int stage;
        public float from, to;
        /// <summary>The first and last x an obstacle may occupy (the run-in and run-out are clear).</summary>
        public float firstX, lastX;
        /// <summary>1: the spacing between demands is what the density asks for; below it, tightened (never past the minimums) to fit all the stage's traits.</summary>
        public float relax;
        public readonly List<PatternItem> furniture = new List<PatternItem>();
        public readonly List<PatternItem>[] layouts = new List<PatternItem>[HolidayPatterns.Variants];
    }

    /// <summary>
    /// The obstacle and pickup layouts of a Holiday Run stage, worked out from its traits and density
    /// (HolidayStages). Pure logic on world x, so it can be checked without the editor: the rules are in
    /// <see cref="Validate"/>.
    ///
    /// What the kid can do: a single jump clears 1.3 m and spans about 5 m of ground at 9 m/s, a double jump
    /// clears 2.1 m, a slide lasts 0.7 s and passes under 0.85 m. So there are low things (0.3 to 0.5 m: steps
    /// and borders, in a hurdle run of two or three now and then), mid things (0.6 to 1.0 m), tall things (1.5 to
    /// 1.9 m, a double jump: rare and always with a coin arc over them), cars, barriers to slide under, gaps (a
    /// plain one 2 to 3.4 m, a wide one 4 to 5.2 m where the density is over 0.5), slow patches, trampolines and
    /// rolling pipes. Between two demands there are 28 m at density 0.3 down to 11 m at density 1 (12 m between
    /// different ones, and more after a slide, a wide gap or a trampoline); nothing within 6 m of a power-up.
    ///
    /// The gaps, tunnel, crossings, fountains and the beats of walkers and dogs are furniture: the same in all
    /// three layouts. The layouts share one recipe (the same obstacles of the same kinds, so they are as hard
    /// as each other) and differ in order, places, sizes, looks, coins and power-ups.
    /// </summary>
    public static class HolidayPatterns
    {
        public const int Variants = 3;

        /// <summary>What a thing asks of the kid; two different demands are never closer than <see cref="MinDifferent"/>.</summary>
        enum Demand { Jump, Double, Slide, Gap, Slow, Launch, Dodge }

        public const float MinSame = 11f, MinDifferent = 12f, PowerUpClear = 6f;

        // The barriers to slide under, by chapter: name, length along the street, the top of the solid, and whether
        // it fits under a tunnel's deck.
        struct SlideSpec
        {
            public string name; public float length, top; public bool lowTop;
            public SlideSpec(string name, float length, float top, bool lowTop) { this.name = name; this.length = length; this.top = top; this.lowTop = lowTop; }
        }

        static readonly SlideSpec[][] Slides =
        {
            new[] { new SlideSpec("PlankTrestles", 2.6f, 0.95f, false), new SlideSpec("BoomBarrier", 1.2f, 0.95f, false), new SlideSpec("AccessPlatform", 1.9f, 2.0f, false), new SlideSpec("AppleBough", 1.7f, 1.09f, false) },
            new[] { new SlideSpec("StallAwning", 2.2f, 2.5f, false), new SlideSpec("RollShutter", 1.4f, 3.15f, false), new SlideSpec("DeliveryConveyor", 1.2f, 0.96f, false) },
            new[] { new SlideSpec("SurfRack", 2.6f, 2.37f, false), new SlideSpec("BoatTrestles", 3.4f, 1.53f, false), new SlideSpec("Boardwalk", 1.6f, 1.94f, false), new SlideSpec("RescueBoardStand", 3.0f, 1.07f, false) },
            new[] { new SlideSpec("ScaffoldGantry", 2.7f, 4.25f, false), new SlideSpec("BeamTrestles", 4.4f, 1.3f, true), new SlideSpec("PipeRack", 4.1f, 2.04f, true), new SlideSpec("SiteBarrier", 1.2f, 0.94f, true) },
            new[] { new SlideSpec("FallenTrunk", 0.8f, 1.55f, false), new SlideSpec("OakBough", 2.1f, 1.19f, false), new SlideSpec("NetTunnel", 2.1f, 0.96f, false), new SlideSpec("PlayTower", 1.4f, 2.6f, false) },
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

        // A tunnel keeps its ends clear: nothing for the first 10 m inside, the last 4, the 6 m before or the 2 after.
        public const float TunnelLeadIn = 10f, TunnelLeadOut = 4f, TunnelApproach = 6f, TunnelAfter = 2f;
        /// <summary>The utility poles stand every 21 m; a tunnel or a crane's plot must not take the ones that carry the wires over a stage's ends.</summary>
        public const float PoleSpacing = 21f;

        // ----------------------------------------------------------------------------------------------- the rules

        static float Lerp(float a, float b, float t) { return a + (b - a) * t; }
        static float Clamp01(float v) { return v < 0f ? 0f : v > 1f ? 1f : v; }

        /// <summary>Metres between one demand and the next of the same kind: 28 at density 0.3 down to 11 at 1.</summary>
        public static float BaseSpacing(float density)
        {
            return Lerp(28f, MinSame, Clamp01((density - 0.3f) / 0.7f));
        }

        struct Span
        {
            public float x0, x1;
            public Demand demand;
            /// <summary>More room wanted after it (a slide goes on, a wide jump lands long, a trampoline throws far).</summary>
            public float extra;
            /// <summary>Keep-out ground that is not a demand (the ends of a tunnel, a beat of walkers): it carries its own margins.</summary>
            public bool zone;
            public bool tunnelStart, tunnelEnd;
        }

        /// <summary>
        /// The room wanted between two demands: the density's spacing (tightened by <paramref name="relax"/>, 1 to 0, toward the minimums), at least 12 m between
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
                // If the furniture won't all fit, one gap fewer (then another).
                if (!PlaceFurniture(plan, st, rng, a, b, anchors, outer / 30)) continue;
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
        /// Places the stage's gaps, tunnel, crossings, fountains and beats of walkers and dogs at random along
        /// the free stretch, apart from each other. False if they don't all fit (the caller tries again).
        /// </summary>
        static bool PlaceFurniture(StagePlan plan, HolidayStages.Stage st, Random rng, float a, float b, List<Span> anchors, int fewerGaps)
        {
            float d = st.density;
            bool poles = st.chapter == 1 || st.chapter == 4;

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
                    float w = wideGap ? Range(rng, 4.0f, 5.2f) : (d < 0.5f ? Range(rng, 2.0f, 3.0f) : Range(rng, 2.4f, 3.4f));
                    var span = Demanding(0f, 0f, wideGap ? Demand.Double : Demand.Gap, wideGap ? 4f : 0f);
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
                // With rolling pipes in it the tunnel is longer: the pipes run along its inside.
                float len = st.Has(StageTraits.Pipes) ? Range(rng, 38f, 42f) : Range(rng, 26f, 32f);
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
                    float width = 5f, margin = 2.3f, x;
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
                    if (!TryPlace(anchors, 12f, Zone(0f, 0f), a, b, rng, d, plan, -1f, false, out x)) return false;
                    anchors.Add(Zone(x, x + 12f));
                    plan.furniture.Add(new PatternItem { kind = PatternKind.Fountain, x = x + 6f, x0 = x + 5.4f, x1 = x + 6.6f, h = i == 0 ? 4f : 5f, a = i == 0 ? 18f : 16f });
                }
            }

            if (st.Has(StageTraits.Pedestrians))
            {
                int beats = d > 0.55f ? 2 : 1;
                for (int i = 0; i < beats; i++)
                {
                    float len = Range(rng, 6f, 9f), margin = 2f, x;
                    if (!TryPlace(anchors, len + margin * 2f, Zone(0f, 0f), a, b, rng, d, plan, -1f, false, out x)) return false;
                    anchors.Add(Zone(x, x + len + margin * 2f));
                    plan.furniture.Add(new PatternItem
                    {
                        kind = PatternKind.Walkers, x = x + margin + len * 0.5f, x0 = x + margin, x1 = x + margin + len,
                        style = rng.Next(1000), a = Range(rng, 0.9f, 1.4f),
                    });
                }
            }

            if (st.Has(StageTraits.Dogs))
            {
                int patches = d > 0.8f ? 2 : 1;
                for (int i = 0; i < patches; i++)
                {
                    float len = Range(rng, 7f, 9f), margin = 2f, x;
                    if (!TryPlace(anchors, len + margin * 2f, Zone(0f, 0f), a, b, rng, d, plan, -1f, false, out x)) return false;
                    anchors.Add(Zone(x, x + len + margin * 2f));
                    plan.furniture.Add(new PatternItem { kind = PatternKind.DogPatch, x = x + margin + len * 0.5f, x0 = x + margin, x1 = x + margin + len, style = rng.Next(1000) });
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
            if (st.Has(StageTraits.Seagulls))
            {
                for (int i = 0; i < 3; i++)
                {
                    float centre = Lerp(a, b, (i + 0.5f) / 3f) + Range(rng, -6f, 6f);
                    plan.furniture.Add(new PatternItem { kind = PatternKind.Gull, x = centre, x0 = centre + 15f, x1 = centre - 15f, y = Range(rng, 4.2f, 4.8f), a = Range(rng, 0f, 3f) });
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
                    if (p.zone && me.zone) need = 1f;
                    else if (p.zone || me.zone) need = 2f;
                    else need = Math.Max(p.x1 <= me.x0 ? Spacing(p, me, density, 1f) : Spacing(me, p, density, 1f), 10f);
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
        /// share of further groups is added while they still fit. All three layouts have the same ones.
        /// </summary>
        static bool Recipe(StagePlan plan, HolidayStages.Stage st, List<Span> anchors, float a, float b, Random rng)
        {
            float d = st.density;
            var sorted = new List<Span>(anchors);
            sorted.Sort((p, q) => p.x0.CompareTo(q.x0));

            var required = new List<Template>();
            if (st.Has(StageTraits.Steps)) required.Add(new Template(PatternKind.Hop, HopCount(d, rng)));
            if (st.Has(StageTraits.Crates)) { required.Add(new Template(PatternKind.Mid, MidCount(d, rng))); required.Add(new Template(PatternKind.Crate, 1)); }
            if (st.Has(StageTraits.Cars)) required.Add(new Template(PatternKind.Car, 1));
            if (st.Has(StageTraits.Awnings)) required.Add(new Template(PatternKind.Slide, 1));
            if (st.Has(StageTraits.Puddles)) required.Add(new Template(PatternKind.Puddle, 1));
            if (st.Has(StageTraits.SoftSand)) required.Add(new Template(PatternKind.SandPatch, 1));
            if (st.Has(StageTraits.Springboards)) required.Add(new Template(PatternKind.Spring, 1));
            if (st.Has(StageTraits.Pipes)) required.Add(new Template(PatternKind.Pipes, 1));

            // The density's share of further groups, drawn up front so the choice doesn't depend on what fits.
            float free = b - a;
            int target = Math.Max(3, (int)Math.Round(free / (BaseSpacing(d) + 4.5f)));
            int have = required.Count;
            foreach (var s in sorted) if (!s.zone) have++;
            var weights = new List<KeyValuePair<PatternKind, float>>();
            weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Hop, st.Has(StageTraits.Steps) ? 1.2f : 0.7f));
            weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Mid, 1f));
            if (st.Has(StageTraits.Crates)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Crate, 0.9f));
            if (st.Has(StageTraits.Cars)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Car, 0.7f));
            if (st.Has(StageTraits.Awnings)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Slide, 1.3f));
            if (st.Has(StageTraits.Puddles)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Puddle, 0.5f));
            if (st.Has(StageTraits.SoftSand)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.SandPatch, 0.6f));
            if (st.Has(StageTraits.Springboards)) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Spring, 0.3f));
            // A tall thing wants a double jump: rare, and not at all in the easy stages.
            if (st.Has(StageTraits.Crates) && d >= 0.6f) weights.Add(new KeyValuePair<PatternKind, float>(PatternKind.Tall, 0.35f));
            var extras = new List<Template>();
            int springs = Count(required, PatternKind.Spring), talls = 0;
            for (int guard = 0; have + extras.Count < target && guard < 30; guard++)
            {
                var k = Pick(weights, rng);
                if (k == PatternKind.Spring && springs >= 2) continue;
                if (k == PatternKind.Tall && talls >= 1) continue;
                if (k == PatternKind.Spring) springs++;
                if (k == PatternKind.Tall) talls++;
                extras.Add(new Template(k, k == PatternKind.Hop ? HopCount(d, rng) : k == PatternKind.Mid ? MidCount(d, rng) : 1));
            }

            var found = new List<PatternItem>[Variants];
            foreach (float relax in new[] { 1f, 0.8f, 0.6f, 0.4f, 0.2f, 0f })
            {
                if (!TryLayouts(plan, st, sorted, required, a, b, relax, found)) continue;
                var chosen = new List<Template>(required);
                var best = (List<PatternItem>[])found.Clone();
                foreach (var extra in extras)
                {
                    chosen.Add(extra);
                    if (TryLayouts(plan, st, sorted, chosen, a, b, relax, found)) best = (List<PatternItem>[])found.Clone();
                    else chosen.RemoveAt(chosen.Count - 1);
                }
                for (int v = 0; v < Variants; v++) plan.layouts[v] = best[v];
                plan.relax = relax;
                return true;
            }
            return false;
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

        /// <summary>A group of obstacles with its pickups, worked out around its leading edge at 0.</summary>
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

        static bool TryLayouts(StagePlan plan, HolidayStages.Stage st, List<Span> sorted, List<Template> recipe, float a, float b, float relax, List<PatternItem>[] into)
        {
            for (int v = 0; v < Variants; v++)
            {
                into[v] = Layout(plan, st, sorted, recipe, a, b, v, relax);
                if (into[v] == null) return false;
            }
            return true;
        }

        static List<PatternItem> Layout(StagePlan plan, HolidayStages.Stage st, List<Span> sorted, List<Template> recipe, float a, float b, int variant, float relax)
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
                AddFurnitureCoins(plan, items);
                AddPowerUp(plan, items, a, b, rng, variant);
                AddFreeCoins(plan, items, a, b);
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
                if (c.kind == PatternKind.Pipes) c.b += lead;
                items.Add(c);
            }
        }

        /// <summary>The finished layout against the rules that hold everywhere (the minimum spacings), with the gaps in.</summary>
        static bool SpacedRight(StagePlan plan, List<Span> placed, List<PatternItem> items, float d)
        {
            var spans = new List<Span>(placed);
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Gap) spans.Add(Demanding(f.x0, f.x1, f.style == 1 ? Demand.Double : Demand.Gap, f.style == 1 ? 4f : 0f));
            spans.Sort((p, q) => p.x0.CompareTo(q.x0));
            for (int i = 1; i < spans.Count; i++)
                if (spans[i].x0 - spans[i - 1].x1 + 1e-3f < Spacing(spans[i - 1], spans[i], d, 0f)) return false;
            return true;
        }

        // ----------------------------------------------------------------------------------------------- the groups

        static Group MakeGroup(Template t, HolidayStages.Stage st, Random rng)
        {
            switch (t.kind)
            {
                case PatternKind.Hop: return MakeRun(PatternKind.Hop, t.n, rng, new[] { 0.6f, 0.8f, 1f, 1.2f, 1.4f }, new[] { 0.3f, 0.35f, 0.4f, 0.45f, 0.5f }, 6f, 7f, 2.2f, 0.6f, 1.1f, 4, true);
                case PatternKind.Mid: return MakeRun(PatternKind.Mid, t.n, rng, new[] { 0.8f, 1f, 1.2f, 1.4f, 1.6f }, new[] { 0.6f, 0.7f, 0.8f, 0.9f, 1f }, 6.2f, 7f, 2.5f, 0.8f, 1.3f, 5, true);
                case PatternKind.Tall: return MakeTall(rng);
                case PatternKind.Crate: return MakeCrate();
                case PatternKind.Car: return MakeCar(rng);
                case PatternKind.Slide: return MakeSlide(st, rng);
                case PatternKind.Puddle: return MakeSlow(PatternKind.Puddle, rng, 3.5f, 5f, 3);
                case PatternKind.SandPatch: return MakeSlow(PatternKind.SandPatch, rng, 6f, 9f, 4);
                case PatternKind.Spring: return MakeSpring();
                default: return MakePipes(st);
            }
        }

        static float Pick(Random rng, params float[] values) { return values[rng.Next(values.Length)]; }

        static void Solid(Group g, PatternKind kind, float x, float w, float h)
        {
            g.items.Add(new PatternItem { kind = kind, x = x, x0 = x - w * 0.5f, x1 = x + w * 0.5f, w = w, h = h });
        }

        static void Arc(Group g, float c, float halfLength, float baseY, float rise, int count)
        {
            g.items.Add(new PatternItem { kind = PatternKind.CoinArc, x = c, x0 = c - halfLength, x1 = c + halfLength, y = baseY, rise = rise, count = count });
        }

        static void Row(Group g, float x0, float x1, float y, int count)
        {
            g.items.Add(new PatternItem { kind = PatternKind.CoinRow, x = (x0 + x1) * 0.5f, x0 = x0, x1 = x1, y = y, count = count });
        }

        /// <summary>
        /// A run of <paramref name="n"/> low (kerbs and borders) or mid (planters, rocks, hedges) things about
        /// 6 to 7 m apart, each with its own arc of coins.
        /// </summary>
        static Group MakeRun(PatternKind kind, int n, Random rng, float[] widths, float[] heights, float pitchMin, float pitchMax, float arc, float arcBase, float arcRise, int coins, bool tunnelOk)
        {
            var g = new Group { kind = kind, demand = Demand.Jump, tunnelOk = tunnelOk };
            float pitch = Range(rng, pitchMin, pitchMax), first = 0f, last = 0f, lastW = 0f;
            for (int i = 0; i < n; i++)
            {
                float w = Pick(rng, widths), h = Pick(rng, heights);
                float c = i == 0 ? w * 0.5f : first + i * pitch;
                if (i == 0) first = c;
                Solid(g, kind, c, w, h);
                Arc(g, c, arc, arcBase, arcRise, coins);
                last = c; lastW = w;
            }
            g.length = last + lastW * 0.5f;
            return g;
        }

        /// <summary>Head high: a double jump, over a high arc of coins.</summary>
        static Group MakeTall(Random rng)
        {
            var g = new Group { kind = PatternKind.Tall, demand = Demand.Double, extra = 3f };
            float w = Pick(rng, 0.7f, 0.85f, 1f), h = Pick(rng, 1.5f, 1.6f, 1.7f, 1.8f, 1.9f);
            Solid(g, PatternKind.Tall, w * 0.5f, w, h);
            Arc(g, w * 0.5f, 3f, 1.6f, 1.6f, 6);
            g.length = w;
            return g;
        }

        /// <summary>A crate (a sandcastle on the beach, a stack of cones on the site) a kicked ball smashes.</summary>
        static Group MakeCrate()
        {
            var g = new Group { kind = PatternKind.Crate, demand = Demand.Jump, tunnelOk = true };
            const float w = 1f;
            Solid(g, PatternKind.Crate, w * 0.5f, w, 0.7f);
            Arc(g, w * 0.5f, 2.5f, 0.8f, 1.2f, 5);
            g.length = w;
            return g;
        }

        /// <summary>A parked car, 3.3 m long and 1.55 high: a double jump, or a hop onto the bonnet and another.</summary>
        static Group MakeCar(Random rng)
        {
            var g = new Group { kind = PatternKind.Car, demand = Demand.Double, extra = 2f };
            g.items.Add(new PatternItem { kind = PatternKind.Car, x = 1.65f, x0 = 0f, x1 = 3.3f, w = 3.3f, h = 1.55f, style = rng.Next(1000) });
            Arc(g, 1.65f, 3.3f, 1.2f, 1.3f, 6);
            g.length = 3.3f;
            return g;
        }

        /// <summary>A barrier to slide under, from the chapter's kit, with a row of coins low under it.</summary>
        static Group MakeSlide(HolidayStages.Stage st, Random rng)
        {
            var g = new Group { kind = PatternKind.Slide, demand = Demand.Slide, extra = 4f };
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
            Row(g, len * 0.5f - Math.Max(0.6f, len * 0.35f), len * 0.5f + Math.Max(0.6f, len * 0.35f), 0.4f, len > 3f ? 4 : 3);
            g.length = len;
            return g;
        }

        /// <summary>Puddles and soft sand: slow going, with coins to collect on the way through.</summary>
        static Group MakeSlow(PatternKind kind, Random rng, float min, float max, int coins)
        {
            var g = new Group { kind = kind, demand = Demand.Slow, extra = 3f, tunnelOk = kind == PatternKind.Puddle };
            float len = Range(rng, min, max);
            g.items.Add(new PatternItem { kind = kind, x = len * 0.5f, x0 = 0f, x1 = len, w = len });
            Row(g, 0.7f, len - 0.7f, 0.6f, coins);
            g.length = len;
            return g;
        }

        // The trampoline's launch at 9 m/s: where the kid is (metres on from the pad, height of the body's middle).
        static readonly float[] SpringX = { 1.1f, 2.2f, 3.2f, 4.3f, 5.4f, 6.5f };
        static readonly float[] SpringY = { 1.95f, 2.87f, 3.38f, 3.46f, 2.95f, 1.88f };

        /// <summary>A trampoline flush with the path, and coins up the arc it throws the kid along (out of reach of a plain jump).</summary>
        static Group MakeSpring()
        {
            var g = new Group { kind = PatternKind.Spring, demand = Demand.Launch, extra = 10f };
            g.items.Add(new PatternItem { kind = PatternKind.Spring, x = 0.6f, x0 = 0f, x1 = 1.2f, w = 1.2f, h = 0.4f });
            for (int i = 0; i < SpringX.Length; i++)
                g.items.Add(new PatternItem { kind = PatternKind.Coin, x = 0.6f + SpringX[i], x0 = 0.6f + SpringX[i], x1 = 0.6f + SpringX[i], y = SpringY[i] });
            g.length = 1.2f;
            return g;
        }

        /// <summary>
        /// A stretch where pipes roll down at the kid from its far end every few seconds, kept clear of
        /// everything else (they would pile up against it); inside the tunnel in a stage that has one.
        /// </summary>
        static Group MakePipes(HolidayStages.Stage st)
        {
            var g = new Group { kind = PatternKind.Pipes, demand = Demand.Dodge, extra = 4f, tunnelOk = st.Has(StageTraits.Tunnel) };
            float lane = st.Has(StageTraits.Tunnel) ? 22f : 30f;
            float interval = Lerp(6f, 4.6f, Clamp01((st.density - 0.5f) / 0.5f));
            // x is the spawner's place; b is where the pipes are removed (the lane's start, once the group is placed).
            g.items.Add(new PatternItem { kind = PatternKind.Pipes, x = lane, x0 = 0f, x1 = lane + 2f, w = 1f, a = interval, b = 0f });
            g.length = lane + 2f;
            return g;
        }

        // ----------------------------------------------------------------------------------------------- pickups

        /// <summary>Coins that telegraph the stage's gaps and fountains (in every layout, since coins live in the layouts).</summary>
        static void AddFurnitureCoins(StagePlan plan, List<PatternItem> items)
        {
            foreach (var f in plan.furniture)
            {
                if (f.kind == PatternKind.Gap)
                {
                    float w = f.x1 - f.x0;
                    if (f.style == 1) items.Add(new PatternItem { kind = PatternKind.CoinArc, x = f.x, x0 = f.x0 - 1.5f, x1 = f.x1 + 1.5f, y = 0.9f, rise = 2.3f, count = 6 });
                    else items.Add(new PatternItem { kind = PatternKind.CoinArc, x = f.x, x0 = f.x0 - 1f, x1 = f.x1 + 1f, y = 0.7f, rise = 1.3f, count = w > 3f ? 6 : 5 });
                }
                else if (f.kind == PatternKind.Fountain)
                {
                    items.Add(new PatternItem { kind = PatternKind.CoinArc, x = f.x, x0 = f.x - 2.5f, x1 = f.x + 2.5f, y = 1.2f, rise = 1.4f, count = 5 });
                    items.Add(new PatternItem { kind = PatternKind.Coin, x = f.x, x0 = f.x, x1 = f.x, y = 3.2f });
                }
            }
        }

        /// <summary>The stretches of a layout at least <paramref name="clear"/> from every demand (gaps, the tunnel's ends and the solids).</summary>
        static List<float[]> FreeStretches(StagePlan plan, List<PatternItem> items, float a, float b, float clear)
        {
            var spans = new List<float[]>();
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Gap) spans.Add(new[] { f.x0, f.x1 });
                else if (f.kind == PatternKind.Tunnel) spans.Add(new[] { f.x0 - TunnelApproach, f.x1 + TunnelAfter });
            foreach (var i in items) if (IsSolidKind(i.kind)) spans.Add(new[] { i.x0, i.x1 });
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

        static bool IsSolidKind(PatternKind k)
        {
            return k == PatternKind.Hop || k == PatternKind.Mid || k == PatternKind.Tall || k == PatternKind.Crate || k == PatternKind.Car ||
                k == PatternKind.Slide || k == PatternKind.Puddle || k == PatternKind.SandPatch || k == PatternKind.Spring || k == PatternKind.Pipes;
        }

        /// <summary>Roughly one layout in two gets a power-up floating in the widest clear stretch.</summary>
        static void AddPowerUp(StagePlan plan, List<PatternItem> items, float a, float b, Random rng, int variant)
        {
            // Drawn either way, so the layouts' other choices don't depend on it.
            double roll = rng.NextDouble();
            float height = Range(rng, 1.0f, 1.6f);
            int kind = (plan.stage + variant + rng.Next(3)) % 3;
            if (roll >= 0.5) return;
            var free = FreeStretches(plan, items, a, b, PowerUpClear + 2f);
            float bestLen = 0f, at = 0f;
            foreach (var f in free)
            {
                float len = f[1] - f[0];
                float mid = (f[0] + f[1]) * 0.5f;
                if (len <= bestLen || InsideTunnel(plan, mid)) continue;
                bestLen = len; at = mid;
            }
            if (bestLen < 1f) return;
            items.Add(new PatternItem { kind = PatternKind.PowerUp, x = at, x0 = at, x1 = at, y = height, style = kind });
        }

        static bool InsideTunnel(StagePlan plan, float x)
        {
            foreach (var f in plan.furniture)
                if (f.kind == PatternKind.Tunnel && x > f.x0 - TunnelApproach && x < f.x1 + TunnelAfter) return true;
            return false;
        }

        /// <summary>A row of coins along the open footpath in the widest clear stretches (not the one holding a power-up).</summary>
        static void AddFreeCoins(StagePlan plan, List<PatternItem> items, float a, float b)
        {
            float powerUp = float.NaN;
            foreach (var i in items) if (i.kind == PatternKind.PowerUp) powerUp = i.x;
            var free = FreeStretches(plan, items, a, b, 5f);
            free.Sort((p, q) => (q[1] - q[0]).CompareTo(p[1] - p[0]));
            int rows = 0;
            foreach (var f in free)
            {
                if (rows >= 2 || f[1] - f[0] < 8f) break;
                float mid = (f[0] + f[1]) * 0.5f;
                if (InsideTunnel(plan, mid)) continue;
                if (!float.IsNaN(powerUp) && powerUp > f[0] - 3f && powerUp < f[1] + 3f) continue;
                items.Add(new PatternItem { kind = PatternKind.CoinRow, x = mid, x0 = mid - 2.4f, x1 = mid + 2.4f, y = 0.5f, count = 5 });
                rows++;
            }
        }

        // ----------------------------------------------------------------------------------------------- the checks

        /// <summary>
        /// Checks a layout against the rules: the clear run-ins, the minimum spacing between demands (more after a
        /// slide, a wide gap or a trampoline), the hurdle pitch, the size classes, the gaps, the tunnel's and
        /// the beats' keep-out ground, a coin arc over every tall thing, and the power-up's clearance. Returns the
        /// problems found (none: fair).
        /// </summary>
        public static List<string> Validate(StagePlan plan, int variant)
        {
            var problems = new List<string>();
            var st = HolidayStages.All[plan.stage];
            var items = plan.layouts[variant];
            float d = st.density;
            string tag = "stage " + (plan.stage + 1) + " layout " + (char)('A' + variant) + ": ";

            var spans = new List<Span>();
            var kinds = new List<PatternKind>();
            foreach (var f in plan.furniture)
            {
                if (f.kind != PatternKind.Gap) continue;
                bool wide = f.style == 1;
                float w = f.x1 - f.x0;
                if (wide && !(d > 0.5f)) problems.Add(tag + "a wide gap at density " + d);
                if (!wide && (w < 2f - 1e-3f || w > 3.4f + 1e-3f)) problems.Add(tag + "gap width " + w);
                if (wide && (w < 4f - 1e-3f || w > 5.2f + 1e-3f)) problems.Add(tag + "wide gap width " + w);
                if (f.x0 < plan.firstX - 1e-3f || f.x1 > plan.lastX + 1e-3f) problems.Add(tag + "a gap outside the open stretch");
                spans.Add(Demanding(f.x0, f.x1, wide ? Demand.Double : Demand.Gap, wide ? 4f : 0f));
                kinds.Add(PatternKind.Gap);
            }
            foreach (var i in items)
            {
                if (!IsSolidKind(i.kind)) continue;
                spans.Add(Demanding(i.x0, i.x1, DemandOf(i), ExtraOf(i)));
                kinds.Add(i.kind);
                if (i.x0 < plan.firstX - 1e-3f) problems.Add(tag + i.kind + " starts at " + i.x0 + ", before " + plan.firstX);
                if (i.x1 > plan.lastX + 1e-3f) problems.Add(tag + i.kind + " ends at " + i.x1 + ", after " + plan.lastX);
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
                // A hurdle run: two or three low (or mid) things 6 to 7 m apart, centre to centre.
                if ((kp == PatternKind.Hop && kq == PatternKind.Hop || kp == PatternKind.Mid && kq == PatternKind.Mid) && gap < 9f)
                {
                    float pitch = (q.x0 + q.x1) * 0.5f - (p.x0 + p.x1) * 0.5f;
                    if (pitch < 5.8f || pitch > 7.7f) problems.Add(tag + "hurdle pitch " + pitch);
                    continue;
                }
                float need = Spacing(p, q, d, 0f);
                if (gap + 1e-3f < need) problems.Add(tag + kp + " to " + kq + " are " + gap + " m apart, wanted " + need);
                if (gap + 1e-3f < (p.demand == q.demand ? MinSame : MinDifferent)) problems.Add(tag + "only " + gap + " m between " + kp + " and " + kq);
            }

            // Keep-out ground: nothing stands in a beat of walkers, a crossing, the fountain's bay or the tunnel's ends.
            foreach (var f in plan.furniture)
            {
                float z0 = float.NaN, z1 = float.NaN;
                switch (f.kind)
                {
                    case PatternKind.Walkers: case PatternKind.DogPatch: z0 = f.x0 - 2f; z1 = f.x1 + 2f; break;
                    case PatternKind.Crossing: z0 = f.x0 - 2.3f; z1 = f.x1 + 2.3f; break;
                    case PatternKind.Fountain: z0 = f.x - 6f; z1 = f.x + 6f; break;
                    case PatternKind.Tunnel: z0 = f.x0 - TunnelApproach; z1 = f.x0 + TunnelLeadIn; break;
                }
                if (!float.IsNaN(z0))
                    foreach (var i in items)
                        if (IsSolidKind(i.kind) && i.x1 > z0 && i.x0 < z1) problems.Add(tag + i.kind + " inside the " + f.kind + " bay");
                if (f.kind != PatternKind.Tunnel) continue;
                foreach (var i in items)
                {
                    if (!IsSolidKind(i.kind)) continue;
                    if (i.x1 > f.x1 - TunnelLeadOut && i.x0 < f.x1 + TunnelAfter) problems.Add(tag + i.kind + " at the tunnel's exit");
                    if (i.x0 < f.x0 + TunnelLeadIn || i.x1 > f.x1 - TunnelLeadOut) continue;
                    if (i.kind == PatternKind.Tall || i.kind == PatternKind.Car || i.kind == PatternKind.Spring) problems.Add(tag + i.kind + " inside the tunnel");
                    if (i.kind == PatternKind.Slide && i.h > 2.1f) problems.Add(tag + "a tall barrier inside the tunnel");
                }
            }

            foreach (var i in items)
            {
                if (i.kind == PatternKind.PowerUp)
                {
                    if (i.y < 1f - 1e-3f || i.y > 1.6f + 1e-3f) problems.Add(tag + "power-up at height " + i.y);
                    foreach (var s in spans)
                        if (i.x > s.x0 - PowerUpClear && i.x < s.x1 + PowerUpClear) problems.Add(tag + "power-up within " + PowerUpClear + " m of an obstacle");
                }
                if (i.kind == PatternKind.Hop && (i.h < 0.3f - 1e-3f || i.h > 0.5f + 1e-3f)) problems.Add(tag + "hop height " + i.h);
                if (i.kind == PatternKind.Mid && (i.h < 0.6f - 1e-3f || i.h > 1f + 1e-3f)) problems.Add(tag + "mid height " + i.h);
                if (i.kind == PatternKind.Tall && (i.h < 1.5f - 1e-3f || i.h > 1.9f + 1e-3f)) problems.Add(tag + "tall height " + i.h);
                if (i.kind != PatternKind.Tall) continue;
                bool arc = false;
                foreach (var c in items)
                    if (c.kind == PatternKind.CoinArc && c.x0 < i.x && c.x1 > i.x && c.y + c.rise > i.h + 0.5f) arc = true;
                if (!arc) problems.Add(tag + "a tall thing without an arc of coins over it");
            }

            // The stage shows each of its traits.
            Need(problems, tag, st, StageTraits.Steps, items, PatternKind.Hop);
            Need(problems, tag, st, StageTraits.Crates, items, PatternKind.Mid);
            Need(problems, tag, st, StageTraits.Crates, items, PatternKind.Crate);
            Need(problems, tag, st, StageTraits.Cars, items, PatternKind.Car);
            Need(problems, tag, st, StageTraits.Awnings, items, PatternKind.Slide);
            Need(problems, tag, st, StageTraits.Puddles, items, PatternKind.Puddle);
            Need(problems, tag, st, StageTraits.SoftSand, items, PatternKind.SandPatch);
            Need(problems, tag, st, StageTraits.Springboards, items, PatternKind.Spring);
            Need(problems, tag, st, StageTraits.Pipes, items, PatternKind.Pipes);
            NeedFurniture(problems, tag, st, StageTraits.Gaps, plan, PatternKind.Gap);
            NeedFurniture(problems, tag, st, StageTraits.Tunnel, plan, PatternKind.Tunnel);
            NeedFurniture(problems, tag, st, StageTraits.Fountain, plan, PatternKind.Fountain);
            NeedFurniture(problems, tag, st, StageTraits.Pedestrians, plan, PatternKind.Walkers);
            NeedFurniture(problems, tag, st, StageTraits.Dogs, plan, PatternKind.DogPatch);
            NeedFurniture(problems, tag, st, StageTraits.Crossing, plan, PatternKind.Crossing);
            NeedFurniture(problems, tag, st, StageTraits.Tide, plan, PatternKind.TideArea);
            NeedFurniture(problems, tag, st, StageTraits.Seagulls, plan, PatternKind.Gull);
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
                case PatternKind.Tall: case PatternKind.Car: return Demand.Double;
                case PatternKind.Slide: return Demand.Slide;
                case PatternKind.Puddle: case PatternKind.SandPatch: return Demand.Slow;
                case PatternKind.Spring: return Demand.Launch;
                case PatternKind.Pipes: return Demand.Dodge;
                default: return Demand.Jump;
            }
        }

        static float ExtraOf(PatternItem i)
        {
            switch (i.kind)
            {
                case PatternKind.Tall: return 3f;
                case PatternKind.Car: return 2f;
                case PatternKind.Slide: return 4f;
                case PatternKind.Puddle: case PatternKind.SandPatch: return 3f;
                case PatternKind.Spring: return 10f;
                case PatternKind.Pipes: return 4f;
                default: return 0f;
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
