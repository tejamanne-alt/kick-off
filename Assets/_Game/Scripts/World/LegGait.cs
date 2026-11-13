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
                // hip in the root's side plane; knee, end and foot from the hip. end: where the two bones end, the
                // ankle (the toe's joint) or, with no toe, the foot; off: the foot from the end, at rest (the foot
                // below a level toe stays that far from its ankle however the leg turns)
                public Vector2 hip, knee, end, foot, off;
                public float length, bend;
                public bool bird;
            }

            readonly Leg[] legs;
            readonly Transform root;

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
                    leg.off = leg.foot - leg.end;
                    leg.length = leg.knee.magnitude + (leg.end - leg.knee).magnitude;
                    leg.bend = Bend(leg.knee, leg.end, n[0] == 'F');
                    if (leg.length > 1e-4f) found.Add(leg);
                }
                return new Rig(root, found.ToArray());
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

            /// <summary>Turn a leg so its foot reaches target (in the root's plane), its toe (if any) turned back by the
            /// leg's turns and by tip, the body's own turn (radians, forward toward up), so the foot stays level with
            /// the ground: the bones end at the ankle, the foot's offset below it turned into the root's frame.</summary>
            void Place(ref Leg leg, Vector2 target, float tip = 0f)
            {
                float c = Mathf.Cos(tip), s = Mathf.Sin(tip);
                Vector2 off = new Vector2(leg.off.x * c + leg.off.y * s, -leg.off.x * s + leg.off.y * c);
                Vector2 turn = TwoBone(leg.knee, leg.end, target - off - leg.hip, leg.bend);
                leg.thigh.localRotation = leg.thighRest * Quaternion.AngleAxis(turn.x * Mathf.Rad2Deg, leg.thighAxis);
                leg.shin.localRotation = leg.shinRest * Quaternion.AngleAxis(turn.y * Mathf.Rad2Deg, leg.shinAxis);
                if (leg.toe != null)
                    leg.toe.localRotation = leg.toeRest * Quaternion.AngleAxis(-(turn.x + turn.y + tip) * Mathf.Rad2Deg, leg.toeAxis);
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
            /// the body by that.</summary>
            public float Pose(float p, float trot, float weight, float lift)
            {
                var want = new Vector2[legs.Length];
                float dip = 0f;
                for (int i = 0; i < legs.Length; i++)
                {
                    var leg = legs[i];
                    Vector2 foot = leg.hip + leg.foot;
                    Vector2 w;
                    if (leg.bird)
                        w = Target(leg, foot.x, Kind.Step, p, 0f);
                    else
                    {
                        float middle = (leg.hip.x + foot.x) * 0.5f;
                        w = Vector2.Lerp(Target(leg, middle, Kind.Walk, p, 0f), Target(leg, middle, Kind.Trot, p, 0f), trot);
                    }
                    want[i] = Vector2.Lerp(foot, w, weight);
                    Vector2 t = want[i] - leg.off - leg.hip;     // where the bones must reach: the ankle above the foot
                    float r = 0.98f * leg.length;
                    if (t.y < 0f && Mathf.Abs(t.x) < r) dip = Mathf.Max(dip, -t.y - Mathf.Sqrt(r * r - t.x * t.x));
                }
                lift -= dip;
                for (int i = 0; i < legs.Length; i++) Place(ref legs[i], want[i] - new Vector2(0f, lift));
                return lift;
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
                    Vector2 f = legs[i].hip + legs[i].foot;
                    Place(ref legs[i], new Vector2(f.x * c + f.y * s, -f.x * s + f.y * c), tip);
                }
            }

            /// <summary>A hop at s = sin of its phase: in the air (s above 0) the feet tucked under and a little back;
            /// on the ground planted, the knees taking the crouch (the body lowered by -lift).</summary>
            public void Hop(float s, float lift)
            {
                for (int i = 0; i < legs.Length; i++)
                {
                    Vector2 f = legs[i].hip + legs[i].foot;
                    float L = legs[i].length;
                    Place(ref legs[i], s > 0f ? f + new Vector2(-0.15f * L * s, 0.25f * L * s) : new Vector2(f.x, -lift));
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
