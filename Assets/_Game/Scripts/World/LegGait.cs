using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Jointed legs for the animals (docs/LEARNINGS.md D19). A walking leg is a thigh (Leg.., its origin at the hip or
    /// shoulder) with a shin under it (Shin.., its origin at the knee) and an empty at the foot's contact point (Foot..).
    /// Each foot follows a path: planted on the ground while the body passes over it (the stance), then lifted and
    /// carried forward (the swing). The thigh and the shin are turned every frame to reach it, the knee bending the way
    /// it bends in the model. So the feet stay on the ground and the knees bend, where a rigid leg swung from the hip
    /// scissors and lifts its foot at both ends of its swing.
    ///
    /// The asset review renders the same gait (tools/blender/asset_review.py: GAITS, foot_path, two_bone, gait, hop,
    /// peck): change the two together. Positions are in the model's side plane: forward (the root's +x, where the
    /// animals face) and up (+y).
    /// </summary>
    public static class LegGait
    {
        public enum Kind { Walk, Trot, Step }

        /// <summary>The share of a cycle a foot is down: a walk keeps three feet down most of the time, a trot has a
        /// moment with none.</summary>
        public static float Duty(Kind kind) { return kind == Kind.Walk ? 0.65f : kind == Kind.Trot ? 0.42f : 0.6f; }

        /// <summary>How far a foot sweeps back under the body while it is down, as a share of the leg's length.</summary>
        public static float Stride(Kind kind) { return kind == Kind.Walk ? 0.6f : kind == Kind.Trot ? 0.9f : 0.55f; }

        /// <summary>How high a foot lifts in its swing, as a share of the leg's length.</summary>
        public static float Lift(Kind kind) { return kind == Kind.Walk ? 0.14f : kind == Kind.Trot ? 0.22f : 0.22f; }

        /// <summary>The body's rise (+) or dip (-) twice a cycle, as a share of the leg's length.</summary>
        public static float Bob(Kind kind) { return kind == Kind.Walk ? -0.012f : kind == Kind.Trot ? 0.03f : -0.008f; }

        /// <summary>When in the cycle a leg starts its stance: a four-beat walk (back-left, front-left, back-right,
        /// front-right), a trot's diagonal pairs, a bird's one foot then the other.</summary>
        public static float Phase(Kind kind, string leg)
        {
            switch (kind)
            {
                case Kind.Walk:
                    return leg == "BL" ? 0f : leg == "FL" ? 0.25f : leg == "BR" ? 0.5f : 0.75f;
                case Kind.Trot:
                    return leg == "FR" || leg == "BL" ? 0f : 0.5f;
                default:
                    return leg == "L" ? 0.5f : 0f;
            }
        }

        /// <summary>Where a foot is at phase p (0..1) from the middle of its path: (forward, up). Down, it slides back
        /// along the ground at an even pace; in the air it lifts and comes forward, eased.</summary>
        public static Vector2 FootPath(float p, float duty, float stride, float lift)
        {
            p -= Mathf.Floor(p);
            if (p < duty) return new Vector2(stride * (0.5f - p / duty), 0f);
            float t = (p - duty) / (1f - duty);
            return new Vector2(stride * (t * t * (3f - 2f * t) - 0.5f), lift * Mathf.Sin(Mathf.PI * t));
        }

        /// <summary>A thigh from the hip to the knee and a shin from the knee to the foot (rest positions from the hip,
        /// in the side plane) turned so the foot reaches target, as near as the leg reaches. bend: +1 the knee forward of
        /// the hip-to-foot line, -1 behind it. Returns the thigh's turn and the shin's turn on top of it (radians,
        /// forward toward up).</summary>
        public static Vector2 TwoBone(Vector2 knee, Vector2 foot, Vector2 target, float bend)
        {
            float l1 = knee.magnitude, l2 = (foot - knee).magnitude;
            float d = Mathf.Clamp(target.magnitude, Mathf.Abs(l1 - l2) + 1e-5f, l1 + l2 - 1e-5f);
            float phi = Mathf.Atan2(target.y, target.x);
            float a = Mathf.Acos(Mathf.Clamp((l1 * l1 + d * d - l2 * l2) / (2f * l1 * d), -1f, 1f));
            float th1 = phi + bend * a;
            float kx = l1 * Mathf.Cos(th1), ky = l1 * Mathf.Sin(th1);
            float th2 = Mathf.Atan2(d * Mathf.Sin(phi) - ky, d * Mathf.Cos(phi) - kx);
            float d1 = th1 - Mathf.Atan2(knee.y, knee.x);
            return new Vector2(d1, th2 - Mathf.Atan2(foot.y - knee.y, foot.x - knee.x) - d1);
        }

        /// <summary>How far a foot is rolled at phase p of its cycle (radians, toes down: its heel lifted, D21). Late in
        /// the stance the heel lifts and the foot rolls over its toes; in the swing a bird's toes curl down and a
        /// mammal's paw folds back (a front paw the most, its pad turned up behind it); it comes level again before it
        /// lands, flat. A foot kept level all the way round looked stuck to a board.</summary>
        public static float Roll(Kind kind, bool front, float p)
        {
            p -= Mathf.Floor(p);
            float off, swing;
            if (kind == Kind.Step) { off = 25f; swing = 55f; }
            else if (kind == Kind.Walk) { off = front ? 30f : 25f; swing = front ? 75f : 40f; }
            else { off = front ? 35f : 30f; swing = front ? 90f : 50f; }
            float duty = Duty(kind), r;
            if (p < duty) r = off * Smooth(0.75f, 1f, p / duty);
            else
            {
                float u = (p - duty) / (1f - duty);
                r = u < 0.35f ? Mathf.Lerp(off, swing, Smooth(0f, 0.35f, u)) : u < 0.85f ? swing * (1f - Smooth(0.35f, 0.85f, u)) : 0f;
            }
            return r * Mathf.Deg2Rad;
        }

        static float Smooth(float a, float b, float x)
        {
            float t = Mathf.Clamp01((x - a) / (b - a));
            return t * t * (3f - 2f * t);
        }

        /// <summary>Which way a knee bends: as it does in the model; a straight leg's, a front leg's forward and a hind
        /// leg's or a bird's back.</summary>
        public static float Bend(Vector2 knee, Vector2 foot, bool front)
        {
            float cross = knee.x * (foot.y - knee.y) - knee.y * (foot.x - knee.x);
            if (Mathf.Abs(cross) > 0.08f * knee.magnitude * (foot - knee).magnitude) return -Mathf.Sign(cross);
            return front ? 1f : -1f;
        }

        /// <summary>A model's jointed legs, captured in their rest pose against the root they move with (a Dog's visual,
        /// a GroundBird's own transform). Legs without a shin and a foot are left alone.</summary>
        public class Rig
        {
            struct Leg
            {
                public string name;
                public Transform thigh, shin, toe;   // toe: optional, the foot kept level (Toe..)
                public Quaternion thighRest, shinRest, toeRest;
                public Vector3 thighAxis, shinAxis, toeAxis;
                // hip in the root's side plane; knee, end, foot and tip from the hip. end: where the two bones end, the
                // ankle (the toe's joint) or, with no toe, the foot; tip: the front of the toes on the ground (a Tip..
                // under the toe; else the foot): the point the gait plants and rolls the foot over; fromTip: the end
                // from the tip, at rest
                public Vector2 hip, knee, end, foot, tip, fromTip;
                public float length, bend;
                public bool bird;
            }

            readonly Leg[] legs;
            readonly Transform root;

            /// <summary>The axis (in the root's own space) a positive turn about which brings its forward toward up: a
            /// body pitched by Pose turns about it, at the root's origin.</summary>
            public Vector3 Side { get; private set; }

            public int Count { get { return legs.Length; } }

            /// <summary>The legs' mean length (hip to knee to foot), metres in the root's space.</summary>
            public float Length { get; private set; }

            Rig(Transform root, Leg[] legs)
            {
                this.root = root;
                this.legs = legs;
                float sum = 0f;
                for (int i = 0; i < legs.Length; i++) sum += legs[i].length;
                Length = legs.Length > 0 ? sum / legs.Length : 0f;
            }

            /// <summary>The jointed legs under model (LegFR.. or a bird's LegR, LegL), against root; none found: Count 0.</summary>
            public static Rig Find(Transform model, Transform root)
            {
                string[] names = { "FR", "FL", "BR", "BL", "R", "L" };
                var found = new System.Collections.Generic.List<Leg>();
                // The side axis: turning the root's +x about it by a positive angle brings it toward +y.
                Vector3 side = Vector3.forward;
                if (Vector3.Dot(Quaternion.AngleAxis(10f, side) * Vector3.right, Vector3.up) < 0f) side = -side;
                Vector3 sideWorld = root.TransformDirection(side);
                foreach (string n in names)
                {
                    var thigh = Deep(model, "Leg" + n);
                    var shin = thigh != null ? Deep(thigh, "Shin" + n) : null;
                    var foot = shin != null ? Deep(shin, "Foot" + n) : null;
                    if (foot == null) continue;
                    var leg = new Leg();
                    leg.name = n;
                    leg.bird = n.Length == 1;
                    leg.thigh = thigh;
                    leg.shin = shin;
                    leg.thighRest = thigh.localRotation;
                    leg.shinRest = shin.localRotation;
                    leg.thighAxis = Quaternion.Inverse(thigh.rotation) * sideWorld;
                    leg.shinAxis = Quaternion.Inverse(shin.rotation) * sideWorld;
                    // a foot of its own (a bird's toes, a paw), hung from the shin at the ankle, the Foot point under
                    // it: kept level with the ground, as a foot stays flat (D20: a bird's long toes, rigid in its
                    // shin, tipped into the floor; a tall paw kept level about its contact point sheared off the shin)
                    leg.toe = Deep(shin, "Toe" + n);
                    if (leg.toe != null)
                    {
                        leg.toeRest = leg.toe.localRotation;
                        leg.toeAxis = Quaternion.Inverse(leg.toe.rotation) * sideWorld;
                    }
                    leg.hip = Plane(root, thigh.position);
                    leg.knee = Plane(root, shin.position) - leg.hip;
                    leg.foot = Plane(root, foot.position) - leg.hip;
                    leg.end = leg.toe != null ? Plane(root, leg.toe.position) - leg.hip : leg.foot;
                    var tipMark = leg.toe != null ? Deep(leg.toe, "Tip" + n) : null;
                    leg.tip = tipMark != null ? Plane(root, tipMark.position) - leg.hip : leg.foot;
                    leg.fromTip = leg.end - leg.tip;
                    leg.length = leg.knee.magnitude + (leg.end - leg.knee).magnitude;
                    leg.bend = Bend(leg.knee, leg.end, n[0] == 'F');
                    if (leg.length > 1e-4f) found.Add(leg);
                }
                var rig = new Rig(root, found.ToArray());
                rig.Side = side;
                return rig;
            }

            static Vector2 Plane(Transform root, Vector3 world)
            {
                Vector3 p = root.InverseTransformPoint(world);
                return new Vector2(p.x, p.y);
            }

            static Transform Deep(Transform t, string name)
            {
                if (t.name == name) return t;
                for (int i = 0; i < t.childCount; i++)
                {
                    var hit = Deep(t.GetChild(i), name);
                    if (hit != null) return hit;
                }
                return null;
            }

            /// <summary>Turn a leg so the front of its toes reaches target (in the root's plane), the foot rolled by roll
            /// (radians, toes down) and turned back by tip, the body's own turn (radians, forward toward up), so with no
            /// roll it lies level on the ground: the bones end at the ankle, set back from the toes as the foot lies.</summary>
            void Place(ref Leg leg, Vector2 target, float tip = 0f, float roll = 0f)
            {
                float a = tip + roll, c = Mathf.Cos(a), s = Mathf.Sin(a);
                Vector2 back = new Vector2(leg.fromTip.x * c + leg.fromTip.y * s, -leg.fromTip.x * s + leg.fromTip.y * c);
                Vector2 turn = TwoBone(leg.knee, leg.end, target + back - leg.hip, leg.bend);
                leg.thigh.localRotation = leg.thighRest * Quaternion.AngleAxis(turn.x * Mathf.Rad2Deg, leg.thighAxis);
                leg.shin.localRotation = leg.shinRest * Quaternion.AngleAxis(turn.y * Mathf.Rad2Deg, leg.shinAxis);
                if (leg.toe != null)
                    leg.toe.localRotation = leg.toeRest * Quaternion.AngleAxis(-(turn.x + turn.y + tip + roll) * Mathf.Rad2Deg, leg.toeAxis);
            }

            /// <summary>The body's rise (+) or dip (-) at phase p of a gait (its root moves by it; the feet stay down).</summary>
            public float BodyLift(float p, Kind kind)
            {
                return Bob(kind) * Length * 0.5f * (1f - Mathf.Cos(4f * Mathf.PI * p));
            }

            /// <summary>Walk the legs: phase p (0..1) of a gait blended from walk to trot by trot (0..1), weight 0 the
            /// rest pose to 1 the full gait, the body lifted by lift (metres, in the root's space) while the feet stay
            /// on the ground. A bird's legs always step. The body comes down as far as a foot needs to reach the ground
            /// (a leg reaches 98 % of its length: a straight one can't step without), so it returns the lift used: move
            /// the body by that. The body stays level: for a pitched one, the other overload.</summary>
            public float Pose(float p, float trot, float weight, float lift)
            {
                float pitch;
                return Walk(p, trot, weight, lift, false, out pitch);
            }

            /// <summary>As Pose, and the body pitched (radians, forward toward up, about Side at the root's origin) as the
            /// front and the hind legs each set how low their end of it must come (D21: a real back tilts with the
            /// stride; one carried level on straight legs read as a table on wheels): turn the root by pitch, then move
            /// it by the lift returned. A bird's two legs share one end: no pitch.</summary>
            public float Pose(float p, float trot, float weight, float lift, out float pitch)
            {
                return Walk(p, trot, weight, lift, true, out pitch);
            }

            float Walk(float p, float trot, float weight, float lift, bool pitched, out float pitch)
            {
                var want = new Vector2[legs.Length];
                var roll = new float[legs.Length];
                for (int i = 0; i < legs.Length; i++)
                {
                    var leg = legs[i];
                    Vector2 tip = leg.hip + leg.tip;
                    Vector2 w;
                    float r;
                    if (leg.bird)
                    {
                        w = Target(leg, tip.x, Kind.Step, p, 0f);
                        r = Roll(Kind.Step, false, p + Phase(Kind.Step, leg.name));
                    }
                    else
                    {
                        float middle = (leg.hip.x + tip.x) * 0.5f;
                        bool front = leg.name[0] == 'F';
                        w = Vector2.Lerp(Target(leg, middle, Kind.Walk, p, 0f), Target(leg, middle, Kind.Trot, p, 0f), trot);
                        r = Mathf.Lerp(Roll(Kind.Walk, front, p + Phase(Kind.Walk, leg.name)),
                                       Roll(Kind.Trot, front, p + Phase(Kind.Trot, leg.name)), trot);
                    }
                    want[i] = Vector2.Lerp(tip, w, weight);
                    roll[i] = r * weight;
                }
                // each end of the body as low as its legs need to reach their ankles (above the planted toes)
                float hF = lift, hB = lift, xF = 0f, xB = 0f;
                int nF = 0, nB = 0;
                pitch = 0f;
                for (int pass = 0; pass < 2; pass++)
                {
                    float dipF = 0f, dipB = 0f, lift0 = pitched ? LiftAt(0f, hF, hB, xF, xB, nF, nB) : lift;
                    float c = Mathf.Cos(pitch), s = Mathf.Sin(pitch);
                    nF = nB = 0;
                    xF = xB = 0f;
                    for (int i = 0; i < legs.Length; i++)
                    {
                        var leg = legs[i];
                        Vector2 ankle = Ankle(leg, want[i], roll[i]);
                        Vector2 g = ankle - new Vector2(0f, lift0);
                        Vector2 t = new Vector2(g.x * c + g.y * s, -g.x * s + g.y * c) - leg.hip;
                        float r = 0.98f * leg.length;
                        float dip = t.y < 0f && Mathf.Abs(t.x) < r ? Mathf.Max(0f, -t.y - Mathf.Sqrt(r * r - t.x * t.x)) : 0f;
                        if (pitched && leg.name[0] == 'F') { dipF = Mathf.Max(dipF, dip); xF += leg.hip.x; nF++; }
                        else { dipB = Mathf.Max(dipB, dip); xB += leg.hip.x; nB++; }
                    }
                    if (nF > 0) xF /= nF;
                    if (nB > 0) xB /= nB;
                    if (pass == 0) { hF = lift - (nF > 0 ? dipF : dipB); hB = lift - dipB; }
                    else { hF -= nF > 0 ? dipF : dipB; hB -= dipB; }
                    if (!pitched) { hF = hB = Mathf.Min(hF, hB); }
                    pitch = pitched && nF > 0 && nB > 0 && Mathf.Abs(xF - xB) > 1e-4f ? Mathf.Atan2(hF - hB, xF - xB) : 0f;
                }
                float liftUsed = pitched ? LiftAt(0f, hF, hB, xF, xB, nF, nB) : Mathf.Min(hF, hB);
                float pc = Mathf.Cos(pitch), ps = Mathf.Sin(pitch);
                for (int i = 0; i < legs.Length; i++)
                {
                    // the toes' target in the root's frame: lowered by the lift, turned back by the body's pitch
                    Vector2 g = want[i] - new Vector2(0f, liftUsed);
                    Place(ref legs[i], new Vector2(g.x * pc + g.y * ps, -g.x * ps + g.y * pc), pitch, roll[i]);
                }
                return liftUsed;
            }

            /// <summary>The body's height at x along it when its front end is at hF over xF and its back at hB over xB.</summary>
            static float LiftAt(float x, float hF, float hB, float xF, float xB, int nF, int nB)
            {
                if (nF == 0 || nB == 0 || Mathf.Abs(xF - xB) < 1e-4f) return Mathf.Min(hF, hB);
                return hB + (x - xB) * (hF - hB) / (xF - xB);
            }

            /// <summary>Where a leg's ankle is when the front of its toes is at tip and the foot is rolled by roll.</summary>
            static Vector2 Ankle(Leg leg, Vector2 tip, float roll)
            {
                float c = Mathf.Cos(roll), s = Mathf.Sin(roll);
                return tip + new Vector2(leg.fromTip.x * c + leg.fromTip.y * s, -leg.fromTip.x * s + leg.fromTip.y * c);
            }

            Vector2 Target(Leg leg, float middle, Kind kind, float p, float lift)
            {
                Vector2 d = FootPath(p + Phase(kind, leg.name), Duty(kind), Stride(kind) * leg.length, Lift(kind) * leg.length);
                return new Vector2(middle + d.x, d.y - lift);   // planted on the ground (the root's y 0), not at the model's height
            }

            /// <summary>As much of tip (radians) as the body can tip about the root's origin with every foot still
            /// planted (each leg reaching 98 % of its length): a bird with its feet apart tips less, or a foot would lift.
            /// Turn the body by this, then Plant it.</summary>
            public float Reach(float tip)
            {
                if (Reachable(tip)) return tip;
                float lo = 0f, hi = tip;
                for (int k = 0; k < 16; k++)
                {
                    float mid = (lo + hi) * 0.5f;
                    if (Reachable(mid)) lo = mid; else hi = mid;
                }
                return lo;
            }

            bool Reachable(float tip)
            {
                float c = Mathf.Cos(tip), s = Mathf.Sin(tip);
                for (int i = 0; i < legs.Length; i++)
                {
                    Vector2 f = legs[i].hip + legs[i].end;     // the ankle stays over the planted, level foot
                    Vector2 t = new Vector2(f.x * c + f.y * s, -f.x * s + f.y * c) - legs[i].hip;
                    float l1 = legs[i].knee.magnitude, l2 = (legs[i].end - legs[i].knee).magnitude;
                    if (t.magnitude > 0.98f * (l1 + l2) || t.magnitude < Mathf.Abs(l1 - l2)) return false;
                }
                return true;
            }

            /// <summary>Hold every foot where it stands while the body tips by tip (radians, forward toward up: a peck
            /// is negative) about the root's origin, between the feet (tip no further than Reach allows).</summary>
            public void Plant(float tip)
            {
                float c = Mathf.Cos(tip), s = Mathf.Sin(tip);
                for (int i = 0; i < legs.Length; i++)
                {
                    Vector2 f = legs[i].hip + legs[i].tip;
                    Place(ref legs[i], new Vector2(f.x * c + f.y * s, -f.x * s + f.y * c), tip);
                }
            }

            /// <summary>A hop at s = sin of its phase: in the air (s above 0) the feet tucked under and a little back;
            /// on the ground planted, the knees taking the crouch (the body lowered by -lift).</summary>
            public void Hop(float s, float lift)
            {
                for (int i = 0; i < legs.Length; i++)
                {
                    Vector2 f = legs[i].hip + legs[i].tip;
                    float L = legs[i].length;
                    // tucked in the air, the toes curled under; planted with the knees taking the crouch
                    Place(ref legs[i], s > 0f ? f + new Vector2(-0.15f * L * s, 0.25f * L * s) : new Vector2(f.x, -lift),
                          0f, s > 0f ? 0.6f * s : 0f);
                }
            }

            /// <summary>Every leg back in its rest pose.</summary>
            public void Rest()
            {
                for (int i = 0; i < legs.Length; i++)
                {
                    legs[i].thigh.localRotation = legs[i].thighRest;
                    legs[i].shin.localRotation = legs[i].shinRest;
                    if (legs[i].toe != null) legs[i].toe.localRotation = legs[i].toeRest;
                }
            }
        }
    }
}
