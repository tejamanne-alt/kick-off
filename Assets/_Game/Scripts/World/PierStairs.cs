using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The way up onto a seaside pier from the beach: a landing at deck height in front of the pier's first span, and
    /// a flight of stairs leaving each end of it, down to the sand on the left and on the right, with a mid-landing
    /// halfway when the drop is long. Timber treads on white cut stringers with white risers, white rails both sides
    /// (the pier's rails), a bent of concrete piles under the landing and two under each mid-landing, a concrete pad
    /// at each foot, and a globe lamp on each of the landing's front corners (the pier's lamps). One mesh, built from a
    /// few numbers; the level builder (StreetBuilder.Coast, Pier) measures the sand and sets them.
    /// The origin is the pier's near end at deck height, on its centre line: x along the beach, z toward the sea; the
    /// landing and the flights lie in front of the pier (z from -depth to 0). review/pier_stairs/pier_stairs.py is a
    /// step-for-step copy for the review pictures.
    /// On the course (<see cref="onCourse"/>: TrackBuilder.PierClimb) the stairs stand across the kid's lane and carry the
    /// kid and the ball up one flight, over the landing and down the other: gentler steps, a shorter landing, and nothing
    /// on the camera's side (no rail, no lamps) between the camera and the kid.
    /// </summary>
    public class PierStairs : ProceduralShape
    {
        /// <summary>A tread's depth, the riser aimed for (the real one divides the drop evenly), a mid-landing's length.</summary>
        public const float Going = 0.27f, Riser = 0.19f, MidLength = 1.3f;
        /// <summary>A flight with more risers than this has a mid-landing halfway.</summary>
        public const int SplitOver = 14;
        /// <summary>How far each foot's concrete pad reaches beyond the last step.</summary>
        public const float FootPad = 1.2f;

        const float Nosing = 0.03f, Tread = 0.06f, Band = 0.3f, Rail = 1.06f;

        public static readonly Color White = new Color(0.95f, 0.94f, 0.9f);
        public static readonly Color Timber = new Color(0.46f, 0.32f, 0.22f);
        public static readonly Color Concrete = new Color(0.8f, 0.78f, 0.74f);
        public static readonly Color Metal = new Color(0.1f, 0.1f, 0.11f);
        public static readonly Color Globe = new Color(1f, 0.93f, 0.72f);
        /// <summary>The boards of the paths on the sand to each foot (laid by the level builder).</summary>
        public static readonly Color Boards = new Color(0.5f, 0.35f, 0.24f);

        [Tooltip("The deck's width.")]
        public float width = 6f;
        [Tooltip("The landing's length along the beach: the deck's width, or shorter on the course.")]
        public float landingWidth = 6f;
        [Tooltip("How far the landing (and so each flight's width) reaches in front of the pier.")]
        public float depth = 1.9f;
        [Tooltip("From the deck down to the sand at each flight's foot, and under the landing.")]
        public float dropLeft = 4.5f, dropRight = 4.5f, landingDrop = 4.5f;
        [Tooltip("A tread's depth, the riser aimed for, and how many risers a flight takes before it needs a mid-landing.")]
        public float going = Going, riser = Riser;
        public int splitOver = SplitOver;
        [Tooltip("The stairs carry the kid's lane: nothing on the camera's side (no rail, no lamps).")]
        public bool onCourse;

        /// <summary>How one flight goes down: its risers (all the same height), how many before the mid-landing and after it, and how far it runs.</summary>
        public struct Plan
        {
            public int risers, toMid, afterMid;
            public float riser, run;
        }

        /// <summary>The flight for a drop of <paramref name="drop"/>: risers near <see cref="Riser"/>, a mid-landing halfway when it is long.</summary>
        public static Plan PlanFor(float drop)
        {
            return PlanFor(drop, Going, Riser, SplitOver);
        }

        /// <summary>The flight for a drop, with treads <paramref name="going"/> deep and risers near <paramref name="riserAim"/>.</summary>
        public static Plan PlanFor(float drop, float going, float riserAim, int splitOver)
        {
            var p = new Plan();
            p.risers = Mathf.Max(2, Mathf.RoundToInt(drop / riserAim));
            p.riser = drop / p.risers;
            p.toMid = p.risers > splitOver ? (p.risers + 1) / 2 : p.risers;
            p.afterMid = p.risers - p.toMid;
            p.run = (p.toMid - 1) * going + (p.afterMid > 0 ? MidLength + (p.afterMid - 1) * going : 0f);
            return p;
        }

        /// <summary>How far the stairs reach either side of the pier's centre line, foot pads included.</summary>
        public static float Reach(float width, float drop)
        {
            return width * 0.5f + PlanFor(drop).run + FootPad;
        }

        protected override void Build(MeshBuilder b)
        {
            float hw = landingWidth * 0.5f, deck = width * 0.5f;
            // The landing: timber on a concrete beam, like the pier's deck.
            Box(b, -hw, -0.08f, -depth, hw, 0f, 0f, Timber, false);
            Box(b, -hw, -0.45f, -depth, hw, -0.08f, 0f, Concrete, true);
            float zr = -depth + 0.08f;
            if (!onCourse)
            {
                // Its front rail, and a lamp on each front corner.
                Box(b, -hw, 0.95f, zr - 0.08f, hw, 1.08f, zr + 0.08f, White, true);
                Box(b, -hw, 0.48f, zr - 0.05f, hw, 0.56f, zr + 0.05f, White, true);
                foreach (float x in new[] { -hw + 0.09f, -1f, 1f, hw - 0.09f })
                    Box(b, x - 0.09f, 0f, zr - 0.09f, x + 0.09f, 1f, zr + 0.09f, White, false);
                foreach (float x in new[] { -hw + 0.09f, hw - 0.09f })
                {
                    Box(b, x - 0.13f, 1.08f, zr - 0.13f, x + 0.13f, 1.4f, zr + 0.13f, Metal, false);
                    b.Cylinder(0, new Vector3(x, 2.65f, zr), Vector3.up, 0.07f, 2.5f, Metal, Metal, 0f, Metal, 6);
                    b.Sphere(0, new Vector3(x, 4.12f, zr), 0.22f, Globe, 10, 6);
                }
            }
            // A landing shorter than the deck: the deck's edge either side of it is railed.
            if (deck > hw + 0.2f)
                foreach (float s in new[] { -1f, 1f })
                {
                    float a = s * hw, c = s * deck;
                    Box(b, Mathf.Min(a, c), 0.95f, 0f, Mathf.Max(a, c), 1.08f, 0.16f, White, true);
                    Box(b, Mathf.Min(a, c), 0.48f, 0.03f, Mathf.Max(a, c), 0.56f, 0.13f, White, true);
                    foreach (float x in new[] { a + s * 0.09f, c - s * 0.09f })
                        Box(b, x - 0.09f, 0f, 0f, x + 0.09f, 1f, 0.18f, White, false);
                }
            // The bent under it: a cross beam on four piles (two under a short landing).
            float zb = -depth * 0.5f;
            Box(b, -hw + 0.1f, -1.05f, zb - 0.28f, hw - 0.1f, -0.45f, zb + 0.28f, Concrete, true);
            var piles = hw >= 2f ? new[] { -hw + 0.35f, -0.9f, 0.9f, hw - 0.35f } : new[] { -hw + 0.3f, hw - 0.3f };
            foreach (float x in piles)
                Pile(b, x, zb, -landingDrop - 0.6f, -1.05f, 0.24f, 10);
            Flight(b, -1f, hw, dropLeft);
            Flight(b, 1f, hw, dropRight);
        }

        /// <summary>One flight, from the landing's end on side <paramref name="s"/> (-1 left, 1 right) down to the sand.</summary>
        void Flight(MeshBuilder b, float s, float hw, float drop)
        {
            var plan = PlanFor(drop, going, riser, splitOver);
            float r = plan.riser, run = plan.run, G = going;
            var railSides = onCourse ? new[] { -0.08f } : new[] { -depth + 0.08f, -0.08f };
            int k1 = plan.toMid, k2 = plan.afterMid;
            for (int part = 0; part < (k2 > 0 ? 2 : 1); part++)
            {
                float u0 = part == 0 ? 0f : (k1 - 1) * G + MidLength;
                float y0 = part == 0 ? 0f : -k1 * r;
                int k = part == 0 ? k1 : k2;
                float uEnd = u0 + (k - 1) * G;
                // The treads, each with a riser under its nosing.
                for (int i = 1; i < k; i++)
                {
                    float y = y0 - i * r;
                    BoxAlong(b, s, hw, u0 + (i - 1) * G, u0 + i * G + Nosing, y - Tread, y, -depth + 0.1f, -0.1f, Timber, true);
                    BoxAlong(b, s, hw, u0 + i * G - 0.025f, u0 + i * G, y - r, y - Tread, -depth + 0.1f, -0.1f, White, false);
                }
                // The cut stringers either side: a band under the steps and a tooth under each tread.
                float top0 = y0 - r - Tread, top1 = top0 - r * (uEnd - u0) / G;
                for (int side = 0; side < 2; side++)
                {
                    float za = side == 0 ? -depth : -0.1f, zb = side == 0 ? -depth + 0.1f : 0f;
                    Prism(b, new[] { At(s, hw, u0, top0), At(s, hw, uEnd, top1), At(s, hw, uEnd, top1 - Band), At(s, hw, u0, top0 - Band) }, za, zb, White);
                    for (int i = 1; i < k; i++)
                    {
                        float y = y0 - i * r - Tread;
                        Prism(b, new[] { At(s, hw, u0 + (i - 1) * G, y), At(s, hw, u0 + i * G, y), At(s, hw, u0 + i * G, y - r) }, za, zb, White);
                    }
                }
                // Rails either side: a sloping handrail and mid rail over the nosings, posts standing on the treads.
                float n0 = y0, n1 = y0 - r * (uEnd - u0) / G;
                foreach (float zc in railSides)
                {
                    Prism(b, new[] { At(s, hw, u0, n0 + Rail - 0.11f), At(s, hw, uEnd, n1 + Rail - 0.11f), At(s, hw, uEnd, n1 + Rail), At(s, hw, u0, n0 + Rail) },
                        zc - 0.07f, zc + 0.07f, White);
                    Prism(b, new[] { At(s, hw, u0, n0 + 0.48f), At(s, hw, uEnd, n1 + 0.48f), At(s, hw, uEnd, n1 + 0.55f), At(s, hw, u0, n0 + 0.55f) },
                        zc - 0.04f, zc + 0.04f, White);
                    int posts = Mathf.Max(1, Mathf.CeilToInt((uEnd - u0) / 1.4f));
                    for (int p = 0; p <= posts; p++)
                    {
                        float u = u0 + 0.06f + (uEnd - u0 - 0.12f) * p / posts;
                        int i = Mathf.Min(k - 1, Mathf.Max(1, (int)((u - u0) / G) + 1));
                        float over = y0 - r * (u - u0) / G;
                        BoxAlong(b, s, hw, u - 0.06f, u + 0.06f, y0 - i * r, over + Rail - 0.05f, zc - 0.06f, zc + 0.06f, White, false);
                    }
                }
                if (part == 0 && k2 > 0)
                {
                    // The mid-landing: timber on a concrete beam, rails both sides, two piles.
                    float ym = -k1 * r;
                    BoxAlong(b, s, hw, uEnd, uEnd + MidLength, ym - 0.08f, ym, -depth, 0f, Timber, false);
                    BoxAlong(b, s, hw, uEnd, uEnd + MidLength, ym - 0.4f, ym - 0.08f, -depth, 0f, Concrete, true);
                    foreach (float zc in railSides)
                    {
                        BoxAlong(b, s, hw, uEnd, uEnd + MidLength, ym + Rail - 0.11f, ym + Rail, zc - 0.07f, zc + 0.07f, White, true);
                        BoxAlong(b, s, hw, uEnd, uEnd + MidLength, ym + 0.48f, ym + 0.55f, zc - 0.04f, zc + 0.04f, White, true);
                        BoxAlong(b, s, hw, uEnd - 0.07f, uEnd + 0.07f, ym, n1 + Rail + 0.04f, zc - 0.07f, zc + 0.07f, White, false);
                        BoxAlong(b, s, hw, uEnd + MidLength - 0.07f, uEnd + MidLength + 0.07f, ym, ym + Rail + 0.04f, zc - 0.07f, zc + 0.07f, White, false);
                    }
                    float um = uEnd + MidLength * 0.5f;
                    float ground = -(landingDrop + (drop - landingDrop) * Mathf.Min(1f, um / Mathf.Max(run, 1e-3f)));
                    foreach (float z in new[] { -depth + 0.4f, -0.4f })
                        Pile(b, s * (hw + um), z, ground - 0.6f, ym - 0.4f, 0.18f, 8);
                }
            }
            // The foot: a concrete pad (flush with the sand on the course), and a newel post either side.
            if (onCourse) BoxAlong(b, s, hw, run - 0.2f, run + G + 0.4f, -drop - 0.12f, -drop + 0.012f, -depth - 0.1f, 0.1f, Concrete, false);
            else BoxAlong(b, s, hw, run - 0.2f, run + FootPad, -drop - 0.12f, -drop + 0.04f, -depth - 0.1f, 0.1f, Concrete, false);
            foreach (float zc in railSides)
                BoxAlong(b, s, hw, run - 0.08f, run + 0.08f, -drop + 0.04f, -drop + r + Rail + 0.06f, zc - 0.08f, zc + 0.08f, White, false);
        }

        /// <summary>A point on side s, u along the flight from the landing's end, at height y.</summary>
        static Vector2 At(float s, float hw, float u, float y)
        {
            return new Vector2(s * (hw + u), y);
        }

        static void Box(MeshBuilder b, float x0, float y0, float z0, float x1, float y1, float z1, Color c, bool bottom)
        {
            b.Box(0, new Vector3(x0, y0, z0), new Vector3(x1, y1, z1), c, bottom ? MeshBuilder.Faces.All : MeshBuilder.Faces.NoBottom);
        }

        /// <summary>A box on side s from u0 to u1 along the flight.</summary>
        static void BoxAlong(MeshBuilder b, float s, float hw, float u0, float u1, float y0, float y1, float z0, float z1, Color c, bool bottom)
        {
            float a = s * (hw + u0), d = s * (hw + u1);
            Box(b, Mathf.Min(a, d), y0, z0, Mathf.Max(a, d), y1, z1, c, bottom);
        }

        static void Pile(MeshBuilder b, float x, float z, float bottom, float top, float radius, int segments)
        {
            b.Cylinder(0, new Vector3(x, (bottom + top) * 0.5f, z), Vector3.up, radius, top - bottom, Concrete, Concrete, 0f, Concrete, segments);
        }

        /// <summary>A convex outline in the x-y plane (in order round it: three or four points), extruded from za to zb.</summary>
        static void Prism(MeshBuilder b, Vector2[] pts, float za, float zb, Color c)
        {
            Vector2 mid = Vector2.zero;
            foreach (var p in pts) mid += p;
            mid /= pts.Length;
            int n = pts.Length;
            var front = new Vector3[n];
            var back = new Vector3[n];
            for (int i = 0; i < n; i++)
            {
                front[i] = new Vector3(pts[i].x, pts[i].y, za);
                back[i] = new Vector3(pts[i].x, pts[i].y, zb);
            }
            if (n == 4)
            {
                b.Quad(0, front[0], front[1], front[2], front[3], Vector3.back, c);
                b.Quad(0, back[0], back[1], back[2], back[3], Vector3.forward, c);
            }
            else
            {
                b.Triangle(0, front[0], front[1], front[2], Vector3.back, c, Vector2.zero, Vector2.zero, Vector2.zero);
                b.Triangle(0, back[0], back[1], back[2], Vector3.forward, c, Vector2.zero, Vector2.zero, Vector2.zero);
            }
            for (int i = 0; i < n; i++)
            {
                int j = (i + 1) % n;
                Vector2 edge = (pts[i] + pts[j]) * 0.5f - mid;
                b.Quad(0, front[i], back[i], back[j], front[j], new Vector3(edge.x, edge.y, 0f), c);
            }
        }
    }
}
