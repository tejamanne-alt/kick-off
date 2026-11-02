using System;
using System.Collections.Generic;
using DribbleToSchool.Holiday;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Checks a level's (or a Holiday Run stage's) ground and obstacles against what the kid can really do (JumpReach), so a
    /// trench nobody can cross or a wall nobody can climb is a warning in the console when the level is built instead of a
    /// surprise on a phone. The track builder records what it lays (ground, pits and water, bridges over them, ramps and
    /// trampolines, walls and platforms, barriers, tunnels) and <see cref="Check"/> reads it back. Pure arithmetic, so the
    /// offline audit harness runs the same code over the story levels' layouts.
    ///
    /// A hole up to 2.0 m is one jump, up to 3.2 m a double jump; anything wider needs a bridge (a moving platform, a raft,
    /// a swing...) that reaches within a plain jump of both banks, one after another. A step up of more than 1.0 m is a double jump (up
    /// to 1.7 m), and above that wants a ramp or a trampoline whose throw really lands on it.
    /// </summary>
    public sealed class LevelFeasibility
    {
        public struct Span { public float from, to, top; }
        public struct Hole { public float from, to, top; public string kind; }
        /// <summary>Something to stand on over a hole: the x range it covers over its travel, and the lowest and highest its top gets.</summary>
        public struct Bridge { public float left, right, lowTop, highTop; public string kind; }
        /// <summary>A solid in the way: <c>height</c> above the ground the kid stands on in front of it.</summary>
        public struct Wall { public float x, width, height; public string kind; }
        /// <summary>A raised slab standing on the ground.</summary>
        public struct Ledge { public float from, to, top, groundTop; }
        public struct Ramp { public float x0, y0, x1, y1; }
        public struct Pad { public float x, groundTop; }
        public struct Barrier { public float x, length, clearance; public string look; }
        public struct Roof { public float from, to, height; }

        public readonly List<Span> spans = new List<Span>();
        public readonly List<Hole> holes = new List<Hole>();
        public readonly List<Bridge> bridges = new List<Bridge>();
        public readonly List<Wall> walls = new List<Wall>();
        public readonly List<Ledge> ledges = new List<Ledge>();
        public readonly List<Ramp> ramps = new List<Ramp>();
        public readonly List<Pad> pads = new List<Pad>();
        public readonly List<Barrier> barriers = new List<Barrier>();
        public readonly List<Roof> roofs = new List<Roof>();

        readonly JumpReach.Motion reach;

        public LevelFeasibility() : this(JumpReach.Defaults) { }

        public LevelFeasibility(JumpReach.Motion reach)
        {
            this.reach = reach;
        }

        // ----------------------------------------------------------------------------------------------- recording

        public void AddSpan(float from, float to, float top) { spans.Add(new Span { from = Math.Min(from, to), to = Math.Max(from, to), top = top }); }
        public void AddHole(float from, float to, float top, string kind) { holes.Add(new Hole { from = from, to = to, top = top, kind = kind }); }
        public void AddRamp(float x0, float y0, float x1, float y1) { ramps.Add(new Ramp { x0 = Math.Min(x0, x1), y0 = x0 <= x1 ? y0 : y1, x1 = Math.Max(x0, x1), y1 = x0 <= x1 ? y1 : y0 }); }
        public void AddPad(float x, float groundTop) { pads.Add(new Pad { x = x, groundTop = groundTop }); }
        public void AddWall(float x, float width, float height, string kind) { walls.Add(new Wall { x = x, width = width, height = height, kind = kind }); }
        public void AddLedge(float from, float to, float top, float groundTop) { ledges.Add(new Ledge { from = from, to = to, top = top, groundTop = groundTop }); }
        public void AddBarrier(float x, float length, float clearance, string look) { barriers.Add(new Barrier { x = x, length = length, clearance = clearance, look = look }); }
        public void AddRoof(float from, float to, float height) { roofs.Add(new Roof { from = from, to = to, height = height }); }

        /// <summary>A platform that slides to and fro (a pallet on a crane, a raft): over its travel it covers [x - w/2, x + travel + w/2].</summary>
        public void AddSliding(float centerX, float centerY, float width, float travelX, float travelY)
        {
            const float half = 0.175f;   // the platform is 0.35 thick
            bridges.Add(new Bridge
            {
                left = centerX + Math.Min(0f, travelX) - width * 0.5f, right = centerX + Math.Max(0f, travelX) + width * 0.5f,
                lowTop = centerY + Math.Min(0f, travelY) + half, highTop = centerY + Math.Max(0f, travelY) + half,
                kind = Math.Abs(travelX) < 0.01f ? "lift" : "platform",
            });
        }

        /// <summary>A swing seat hanging from <paramref name="pivotX"/>, <paramref name="pivotY"/> on a rope, swinging through +-<paramref name="amplitude"/> degrees.</summary>
        public void AddSwing(float pivotX, float pivotY, float rope, float amplitude)
        {
            float a = amplitude * (float)Math.PI / 180f, reachX = rope * (float)Math.Sin(a);
            bridges.Add(new Bridge
            {
                left = pivotX - reachX - 0.7f, right = pivotX + reachX + 0.7f,
                lowTop = pivotY - rope + 0.1f, highTop = pivotY - rope * (float)Math.Cos(a) + 0.1f, kind = "swing",
            });
        }

        // ----------------------------------------------------------------------------------------------- the check

        const float Eps = 1e-3f;

        float TopLeftOf(float x, float fallback)
        {
            foreach (var s in spans) if (Math.Abs(s.to - x) < 0.06f) return s.top;
            return fallback;
        }

        float TopRightOf(float x, float fallback)
        {
            foreach (var s in spans) if (Math.Abs(s.from - x) < 0.06f) return s.top;
            return fallback;
        }

        /// <summary>The problems found, in words (none: every hole, step, wall and barrier can be done). <paramref name="doubleJumps"/> collects the notes about things that need a double jump.</summary>
        public List<string> Check(List<string> doubleJumps = null)
        {
            var problems = new List<string>();
            float plain = JumpReach.SafePlainGap(reach), wide = JumpReach.SafeWideGap(reach);
            float mid = JumpReach.SafeMidWall(reach), tall = JumpReach.SafeTallWall(reach);

            foreach (var h in holes)
            {
                float w = h.to - h.from;
                string where = h.kind + " " + h.from.ToString("0.0") + " to " + h.to.ToString("0.0") + " (" + w.ToString("0.0") + " m)";
                float left = TopLeftOf(h.from, h.top), right = TopRightOf(h.to, h.top);
                if (w <= plain + Eps && Math.Abs(left - right) <= mid + Eps) continue;
                if (w <= wide + Eps && Math.Abs(left - right) <= tall + Eps)
                {
                    if (w > plain + Eps && doubleJumps != null) doubleJumps.Add(where + " wants a double jump");
                    continue;
                }
                // Wider than a double jump crosses: a bridge must get the kid within a plain jump of each bank, one after another.
                // (A swing is boarded and left with a double jump: its seat is only near a bank at the ends of its swing.)
                float cursor = h.from;
                float cursorTop = left;
                float hop = plain;
                var used = new bool[bridges.Count];
                bool progress = true;
                string via = "";
                while (progress && h.to - cursor > hop + Eps)
                {
                    progress = false;
                    int best = -1;
                    float bestRight = cursor;
                    for (int i = 0; i < bridges.Count; i++)
                    {
                        var b = bridges[i];
                        float reachOn = b.kind == "swing" ? wide : plain;
                        if (used[i] || b.right <= bestRight + Eps || b.left > cursor + reachOn + Eps || b.left > h.to || b.right < h.from) continue;
                        // Getting on from the bank: a step up of no more than a jump (or a double jump for a swing).
                        if (b.lowTop - cursorTop > (b.kind == "swing" ? tall : mid) + Eps && cursor <= h.from + Eps) continue;
                        best = i; bestRight = b.right;
                    }
                    if (best < 0) break;
                    used[best] = true;
                    via += (via.Length > 0 ? ", " : "") + bridges[best].kind + " at " + (0.5f * (bridges[best].left + bridges[best].right)).ToString("0.0");
                    cursor = bestRight;
                    cursorTop = bridges[best].highTop;
                    hop = bridges[best].kind == "swing" ? wide : plain;
                    progress = true;
                }
                float rest = h.to - cursor;
                if (rest > hop + Eps)
                    problems.Add(where + " is wider than a double jump crosses (" + wide.ToString("0.0") + " m)" + (via.Length > 0 ? ", and what bridges it (" + via + ") stops " + rest.ToString("0.0") + " m short of the far bank" : " and has no bridge"));
                else if (cursorTop < right - tall - Eps && via.Length > 0)
                    problems.Add(where + ": the bridge (" + via + ") tops out " + (right - cursorTop).ToString("0.0") + " m under the far bank, more than a jump climbs");
                else if (doubleJumps != null)
                    doubleJumps.Add(where + " is crossed by " + via);
            }

            // Steps in the ground.
            foreach (var a in spans)
                foreach (var b in spans)
                {
                    if (Math.Abs(a.to - b.from) > 0.06f) continue;
                    float rise = b.top - a.top;
                    if (rise <= mid + Eps) continue;
                    string where = "ground steps up " + rise.ToString("0.0") + " m at " + b.from.ToString("0.0");
                    if (rise <= tall + Eps) { if (doubleJumps != null) doubleJumps.Add(where + " (a double jump)"); continue; }
                    bool ramp = false;
                    foreach (var r in ramps) if (r.x0 <= b.from + 0.5f && r.x1 >= b.from - 0.5f && Math.Abs(r.y1 - b.top) < 0.3f) ramp = true;
                    if (!ramp) problems.Add(where + ", more than a double jump climbs, and no ramp leads up");
                }

            // Walls and the crates and cars in the way.
            foreach (var w in walls)
            {
                string where = w.kind + " at " + w.x.ToString("0.0") + " (" + w.height.ToString("0.00") + " m high)";
                if (w.height > JumpReach.MaxWall(reach) + Eps) problems.Add(where + " is higher than a double jump clears (" + JumpReach.MaxWall(reach).ToString("0.0") + " m)");
                else if (w.height > mid + Eps && doubleJumps != null) doubleJumps.Add(where + " wants a double jump");
            }

            // Raised slabs: a step up, a ramp, or a trampoline whose throw lands on it.
            foreach (var l in ledges)
            {
                float height = l.top - l.groundTop;
                string where = "platform " + l.from.ToString("0.0") + " to " + l.to.ToString("0.0") + " (" + height.ToString("0.0") + " m up)";
                if (height <= mid + Eps) continue;
                bool ok = false;
                // A ramp whose top end meets the slab's left edge.
                foreach (var r in ramps) if (Math.Abs(r.x1 - l.from) < 0.6f && Math.Abs(r.y1 - l.top) < 0.3f) ok = true;
                // A trampoline whose throw comes down on it: the throw alone, or with the air jump it gives back.
                foreach (var p in pads) if (!ok && p.x < l.from && l.from - p.x < 9f && ThrowLandsOn(p.x, l.from, l.to, height, false)) ok = true;
                if (!ok)
                    foreach (var p in pads)
                        if (p.x < l.from && l.from - p.x < 9f && ThrowLandsOn(p.x, l.from, l.to, height, true))
                        {
                            ok = true;
                            if (doubleJumps != null) doubleJumps.Add(where + " is reached by the trampoline at " + p.x.ToString("0.0") + " and the air jump it gives back");
                        }
                if (!ok && height <= tall + Eps) { ok = true; if (doubleJumps != null) doubleJumps.Add(where + " wants a double jump"); }
                if (!ok) problems.Add(where + " has no ramp up and no trampoline whose throw lands on it");
            }

            foreach (var b in barriers)
            {
                if (b.length > JumpReach.MaxSlideBarrier(reach) + Eps) problems.Add("barrier " + b.look + " at " + b.x.ToString("0.0") + " is " + b.length.ToString("0.0") + " m long, more than a slide carries the kid (" + JumpReach.MaxSlideBarrier(reach).ToString("0.0") + " m)");
                if (b.clearance < JumpReach.MinSlideClearance(reach) - Eps) problems.Add("barrier " + b.look + " at " + b.x.ToString("0.0") + " leaves only " + b.clearance.ToString("0.00") + " m to slide under");
            }

            foreach (var r in roofs)
            {
                float need = JumpReach.DoubleJumpHeadroom(reach);
                if (r.height < need - Eps) problems.Add("roof at " + r.from.ToString("0.0") + " to " + r.to.ToString("0.0") + " is " + r.height.ToString("0.0") + " m up, under a double jump's head (" + need.ToString("0.0") + " m)");
            }
            return problems;
        }

        /// <summary>
        /// Does the throw of a trampoline at <paramref name="padX"/> (the kid walking on over it, and pressing the air jump at the top of
        /// the throw if <paramref name="airJump"/>) come down on top of a slab <paramref name="height"/> up from <paramref name="from"/> to <paramref name="to"/>?
        /// </summary>
        public bool ThrowLandsOn(float padX, float from, float to, float height, bool airJump)
        {
            float[] xs, ys;
            const int n = 200;
            JumpReach.Path(reach, reach.runSpeed, airJump ? JumpReach.JumpKind.SpringDouble : JumpReach.JumpKind.Spring, n, out xs, out ys);
            float launch = padX + JumpReach.SpringLaunchOffset;
            for (int i = 1; i < n; i++)
            {
                // Coming down through the slab's top, with the capsule's whole width on it.
                if (ys[i - 1] > height + 0.05f && ys[i] <= height + 0.05f)
                {
                    float x = launch + xs[i];
                    if (x >= from + 0.25f && x <= to - 0.25f) return true;
                }
            }
            return false;
        }
    }
}
