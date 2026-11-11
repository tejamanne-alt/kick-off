using System;
using System.Collections.Generic;
using DribbleToSchool.Holiday;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Where a level's how-tos go (Tutorial/ActionSpot, shown by UI/ActionCoach as the kid comes up to each): the hazards the
    /// track builder marks as it lays them (zebra crossings, the site's vehicle gates, the call-button gates, dogs, passers-by,
    /// gulls, the tide, fountains, moving platforms and hoists, rope swings), and what its feasibility audit recorded
    /// (LevelFeasibility): every barrier to slide under; every wall by its height (a kerb to hop, a wall to chip over and jump,
    /// a tall one to lob and double jump, unless a trampoline just before it is the way up); every step up in the ground
    /// with no ramp or trampoline to it (a kerb, or a step to chip the ball up and jump); the crate stacks; the parked
    /// cars; the step and its high wall; every pit or trench by its width (one jump, or a double jump; one wider still is
    /// crossed on its bridge, whose how-to that is); and the trampolines (just after a fountain, which has lifted the ball,
    /// only the kid's bounce). Neighbours of the same kind (two cars in a row, a run of barriers) make one spot. Pure
    /// arithmetic, so the offline audit harness lists every level's spots.
    /// </summary>
    public sealed class CoachPlan
    {
        public struct Spot
        {
            public string action;
            public float from, to;

            public override string ToString() { return action + " " + from.ToString("0.0") + " to " + to.ToString("0.0"); }
        }

        /// <summary>Every action id a plan can give (each has its how-to in UI/CoachCatalog; the tests check).</summary>
        public static readonly string[] Actions =
        {
            "slide", "kerb", "stepup", "chip", "chiphigh", "gap", "gapdouble", "crates", "car", "highwall", "springboard", "bounce",
            "platform", "lift", "swing", "gate", "crossing", "siteexit", "tide", "dog", "people", "seagull", "fountain",
            "drawbridge", "sprinkler", "golfcart",
        };

        /// <summary>Spots of the same action closer than this (m) are one.</summary>
        public const float JoinGap = 2f;
        /// <summary>A wall up to this high is a kerb: hop it, and the ball bounces up after.</summary>
        public const float KerbHeight = 0.35f;
        /// <summary>A trampoline this close (m) before a tall wall is the way over it.</summary>
        public const float PadBeforeWall = 5f;
        /// <summary>A fountain this close (m) before a trampoline has lifted the ball already.</summary>
        public const float FountainBeforePad = 4f;

        const float Eps = 1e-3f;

        /// <summary>False for a build that has no coach (the Holiday Run's stages).</summary>
        public bool Enabled = true;

        readonly List<Spot> marked = new List<Spot>();

        /// <summary>A hazard's how-to over <paramref name="from"/> to <paramref name="to"/> (world x, either order).</summary>
        public void Mark(string action, float from, float to)
        {
            marked.Add(new Spot { action = action, from = Math.Min(from, to), to = Math.Max(from, to) });
        }

        /// <summary>
        /// The level's spots, sorted along it: the marked hazards and what <paramref name="audit"/> recorded, neighbours joined.
        /// With <paramref name="slopedGround"/> (the beach, whose sand slopes up each step of the ground) the ground's steps need no how-to.
        /// </summary>
        public List<Spot> Build(LevelFeasibility audit, JumpReach.Motion reach, bool slopedGround = false)
        {
            var spots = new List<Spot>(marked);
            float plain = JumpReach.SafePlainGap(reach), wide = JumpReach.SafeWideGap(reach), mid = JumpReach.SafeMidWall(reach);

            foreach (var b in audit.barriers) Add(spots, "slide", b.x - b.length * 0.5f, b.x + b.length * 0.5f);
            foreach (var w in audit.walls)
            {
                string action = WallAction(w, audit, mid);
                if (action != null) Add(spots, action, w.x - w.width * 0.5f, w.x + w.width * 0.5f);
            }
            foreach (var h in audit.holes)
            {
                float width = h.to - h.from;
                if (width <= plain + Eps) Add(spots, "gap", h.from, h.to);
                else if (width <= wide + Eps) Add(spots, "gapdouble", h.from, h.to);
            }
            foreach (var p in audit.pads) Add(spots, FountainBefore(p.x) ? "bounce" : "springboard", p.x - 0.6f, p.x + 0.6f);
            // Where the ground itself steps up (a hill climbed step by step) and no ramp or trampoline leads up it.
            if (!slopedGround)
            {
                foreach (var a in audit.spans)
                    foreach (var b in audit.spans)
                    {
                        float rise = b.top - a.top;
                        if (Math.Abs(a.to - b.from) > 0.06f || rise <= 0.05f || RampOrPadAt(audit, b.from)) continue;
                        Add(spots, rise <= KerbHeight + Eps ? "kerb" : "stepup", b.from - 0.3f, b.from + 0.3f);
                    }
            }
            return Join(spots);
        }

        static void Add(List<Spot> spots, string action, float from, float to)
        {
            spots.Add(new Spot { action = action, from = Math.Min(from, to), to = Math.Max(from, to) });
        }

        static string WallAction(LevelFeasibility.Wall w, LevelFeasibility audit, float mid)
        {
            if (w.kind == "crate stack") return "crates";
            if (w.kind == "parked car") return "car";
            if (w.kind == "step" || w.kind.StartsWith("high wall", StringComparison.Ordinal)) return "highwall";
            if (w.kind != "wall") return null;
            if (w.height <= KerbHeight + Eps) return "kerb";
            if (w.height <= mid + Eps) return "chip";
            foreach (var p in audit.pads)
                if (p.x <= w.x && p.x >= w.x - PadBeforeWall) return null;   // the trampoline's how-to is the way over
            return "chiphigh";
        }

        static bool RampOrPadAt(LevelFeasibility audit, float x)
        {
            foreach (var r in audit.ramps) if (x >= r.x0 - 0.1f && x <= r.x1 + 0.1f) return true;
            foreach (var p in audit.pads) if (p.x <= x && p.x >= x - PadBeforeWall) return true;
            return false;
        }

        bool FountainBefore(float padX)
        {
            foreach (var s in marked)
            {
                if (s.action != "fountain") continue;
                float x = (s.from + s.to) * 0.5f;
                if (x <= padX && x >= padX - FountainBeforePad) return true;
            }
            return false;
        }

        /// <summary>Sorts the spots along the level and joins each to the last of its kind when they are within <see cref="JoinGap"/>.</summary>
        static List<Spot> Join(List<Spot> spots)
        {
            spots.Sort((a, b) => a.from.CompareTo(b.from));
            var joined = new List<Spot>();
            var last = new Dictionary<string, int>();
            foreach (var s in spots)
            {
                int i;
                if (last.TryGetValue(s.action, out i) && s.from <= joined[i].to + JoinGap)
                {
                    var j = joined[i];
                    j.to = Math.Max(j.to, s.to);
                    joined[i] = j;
                    continue;
                }
                last[s.action] = joined.Count;
                joined.Add(s);
            }
            return joined;
        }
    }
}
