using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The beach (chapter 3) as one smooth surface of sand, worked out from the gameplay ground.
    /// Along the kid's lane it is exactly the ground's height, each step eased into an S-shaped
    /// slope on its lower side (at most about 22 degrees) and any gap dipping into a channel;
    /// raised ground swells into a dune that rolls away on both sides of the lane; away from the
    /// lane the sand lies in gentle hummocks; toward the sea it settles into wet sand and runs on
    /// under the water. Every slope eases in and out, so there are no edges or flat cuts anywhere.
    /// The sand's mesh (<see cref="SandDunes"/>), the slopes' colliders and the height props stand
    /// at all come from here, so they always agree.
    /// </summary>
    [System.Serializable]
    public class SandField
    {
        /// <summary>The lowest ground height: the open beach.</summary>
        public float baseTop;
        /// <summary>The gameplay ground spans as (from x, to x, top).</summary>
        public List<Vector3> spans = new List<Vector3>();
        /// <summary>Stretches (from x, to x) where the sand lies smooth, without hummocks: where the tide washes over it.</summary>
        public List<Vector2> calm = new List<Vector2>();

        /// <summary>How far a step's slope runs for each unit it climbs (an S-curve: about 22 degrees at its steepest).</summary>
        public const float SlopeRun = 3.6f;
        /// <summary>Where the sand starts to turn wet, and where the wet sand starts down under the sea.</summary>
        public const float WetFrom = 5.6f, ShoreFrom = 8.6f;
        /// <summary>How far a channel's bed lies below the beach.</summary>
        public const float ChannelDepth = 0.6f;

        public static readonly Color Dry = Color.white;
        public static readonly Color Trodden = new Color(0.96f, 0.93f, 0.88f);
        public static readonly Color Wet = new Color(0.82f, 0.74f, 0.62f);

        /// <summary>A step between two touching spans: its slope runs from (edge, top) down to bottom over run (negative: to the left).</summary>
        public struct Step { public float edge, top, bottom, run; }
        /// <summary>A gap between spans: a channel from l (ground top hl) to r (hr).</summary>
        public struct Gap { public float l, r, hl, hr; }

        [System.NonSerialized] List<Step> steps;
        [System.NonSerialized] List<Gap> gaps;
        [System.NonSerialized] float firstFrom, firstTop, lastTo, lastTop;

        public SandField() { }

        public SandField(float baseTop, IEnumerable<Vector3> groundSpans, IEnumerable<Vector2> calmAreas)
        {
            this.baseTop = baseTop;
            spans = new List<Vector3>(groundSpans);
            calm = new List<Vector2>(calmAreas);
        }

        public List<Step> Steps { get { Prepare(); return steps; } }
        public List<Gap> Gaps { get { Prepare(); return gaps; } }

        void Prepare()
        {
            if (steps != null) return;
            steps = new List<Step>();
            gaps = new List<Gap>();
            if (spans.Count == 0) return;
            var sorted = new List<Vector3>(spans);
            sorted.Sort((p, q) => p.x.CompareTo(q.x));
            firstFrom = sorted[0].x;
            firstTop = sorted[0].z;
            lastTo = float.MinValue;
            foreach (var s in sorted)
                if (s.y > lastTo) { lastTo = s.y; lastTop = s.z; }

            // Steps: the slope goes on the lower span, no longer than most of that span.
            foreach (var a in sorted)
                foreach (var b in sorted)
                {
                    if (Mathf.Abs(a.y - b.x) > 0.01f || Mathf.Abs(a.z - b.z) < 0.02f) continue;
                    float drop = Mathf.Abs(a.z - b.z);
                    var step = a.z > b.z
                        ? new Step { edge = a.y, top = a.z, bottom = b.z, run = Mathf.Min(SlopeRun * drop, (b.y - b.x) * 0.9f) }
                        : new Step { edge = b.x, top = b.z, bottom = a.z, run = -Mathf.Min(SlopeRun * drop, (a.y - a.x) * 0.9f) };
                    if (Mathf.Abs(step.run) > 0.05f) steps.Add(step);
                }

            // Gaps: wherever the ground stops before the next span starts.
            float reach = sorted[0].y, reachTop = sorted[0].z;
            for (int i = 1; i < sorted.Count; i++)
            {
                if (sorted[i].x > reach + 0.01f) gaps.Add(new Gap { l = reach, r = sorted[i].x, hl = reachTop, hr = sorted[i].z });
                if (sorted[i].y > reach) { reach = sorted[i].y; reachTop = sorted[i].z; }
            }
        }

        /// <summary>The sand's height along the kid's lane (z = 0): the ground, its steps eased into slopes, its gaps into channels.</summary>
        public float Lane(float x)
        {
            Prepare();
            if (spans.Count == 0) return baseTop;
            float h = float.MinValue;
            foreach (var s in spans)
                if (x >= s.x && x <= s.y && s.z > h) h = s.z;
            if (h == float.MinValue)
            {
                if (x < firstFrom) h = firstTop;
                else if (x > lastTo) h = lastTop;
                else
                {
                    h = baseTop - ChannelDepth;
                    foreach (var g in gaps)
                        if (x > g.l && x < g.r) h = Channel(g, x);
                }
            }
            foreach (var s in steps)
            {
                float d = (x - s.edge) / s.run;   // 0 at the top of the slope, 1 at its foot
                if (d >= 0f && d < 1f) h = Mathf.Max(h, s.bottom + (s.top - s.bottom) * Ease(1f - d));
            }
            return h;
        }

        /// <summary>Across a channel: banks easing down from the ground either side to the bed.</summary>
        float Channel(Gap g, float x)
        {
            float bed = baseTop - ChannelDepth, bank = Mathf.Min(0.6f, (g.r - g.l) * 0.4f);
            float left = Mathf.Lerp(g.hl, bed, Ease((x - g.l) / bank));
            float right = Mathf.Lerp(g.hr, bed, Ease((g.r - x) / bank));
            return Mathf.Max(left, right);
        }

        /// <summary>The sand's height at (x, z).</summary>
        public float Height(float x, float z)
        {
            float lift = Lane(x) - baseTop;
            float h = baseTop + lift * (lift > 0f ? Dune(x, z, lift) : ChannelReach(z));
            return h + Hummocks(x, z) + Shore(z);
        }

        /// <summary>The sand's colour at (x, z): trodden along the lane, darker where it is wet.</summary>
        public Color Tint(float x, float z)
        {
            float lane = 1f - Ease((Mathf.Abs(z) - 1.3f) / 0.5f);
            Color c = Color.Lerp(Dry, Trodden, lane);
            float wet = Ease((z - (WetFrom - 0.2f)) / 1.2f);
            float lift = Lane(x) - baseTop;
            if (lift < 0f) wet = Mathf.Max(wet, Mathf.Clamp01(-lift / ChannelDepth) * ChannelReach(z));
            return Color.Lerp(c, Wet, wet);
        }

        /// <summary>
        /// How much of a dune's height (lift) stands at depth z: all of it along the lane and a
        /// little either side (the top's edges wander), easing away toward the camera and toward
        /// the sea, more gently for a higher dune.
        /// </summary>
        static float Dune(float x, float z, float lift)
        {
            float front = -1.65f - 0.6f * Noise(x * 0.09f, 3.7f), back = 1.8f + 1.8f * Noise(x * 0.06f, 9.2f);
            if (z < front) return Ease(1f - (front - z) / (1.4f + 2.2f * lift));
            if (z > back) return Ease(1f - (z - back) / (1.8f + 2.8f * lift));
            return 1f;
        }

        /// <summary>A channel runs from just in front of the lane out to the sea.</summary>
        static float ChannelReach(float z) { return Ease((z + 3.6f) / 2f); }

        /// <summary>Low, wind-blown hummocks: none in the lane, on the wet sand or where the tide comes in.</summary>
        float Hummocks(float x, float z)
        {
            float m = Ease((Mathf.Abs(z) - 1.7f) / 1.8f) * (1f - Ease((z - 4.4f) / 1.2f));
            if (m <= 0f) return 0f;
            foreach (var c in calm)
            {
                float d = x < c.x ? c.x - x : x > c.y ? x - c.y : 0f;
                m *= Ease(d / 3f);
            }
            if (m <= 0f) return 0f;
            return m * (0.18f * (Noise(x * 0.19f, z * 0.26f) - 0.5f) + 0.07f * (Noise(x * 0.55f + 11f, z * 0.6f + 5f) - 0.5f));
        }

        /// <summary>The wet sand a little lower, then the beach running down under the sea.</summary>
        static float Shore(float z)
        {
            return -0.12f * Ease((z - WetFrom) / 1.4f) - 0.44f * Ease((z - ShoreFrom) / 2.4f);
        }

        /// <summary>Smoothstep on 0..1, clamped.</summary>
        public static float Ease(float t)
        {
            t = Mathf.Clamp01(t);
            return t * t * (3f - 2f * t);
        }

        /// <summary>Smooth value noise, 0..1 (the same numbers on every platform).</summary>
        public static float Noise(float x, float y)
        {
            int i = Mathf.FloorToInt(x), j = Mathf.FloorToInt(y);
            float u = Ease(x - i), v = Ease(y - j);
            return Mathf.Lerp(Mathf.Lerp(Hash(i, j), Hash(i + 1, j), u), Mathf.Lerp(Hash(i, j + 1), Hash(i + 1, j + 1), u), v);
        }

        static float Hash(int i, int j)
        {
            unchecked
            {
                int h = i * 374761393 + j * 668265263;
                h = (h ^ (h >> 13)) * 1274126177;
                return ((h ^ (h >> 16)) & 0xffff) / 65535f;
            }
        }
    }
}
