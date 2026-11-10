using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Joint angles for one frame of a CharacterRig, in degrees. Hips and shoulders:
    /// positive swings the limb forward (to the right). Knees bend with negative angles
    /// (the foot folds back), elbows with positive angles (the hand comes forward and up).
    /// </summary>
    public struct RigPose
    {
        public float legF, legB, kneeF, kneeB;
        public float armF, armB, elbowF, elbowB;
        public float bob, headTilt, lean;
        /// <summary>Swing of the shoulder bag (degrees, positive swings it forward).</summary>
        public float bag;
        public Vector2 squash;
        /// <summary>
        /// Moves the whole body (x forward, y up, in the character's own frame), added to <see cref="bob"/>:
        /// what turns a spin about the body's pivot into a spin about its centre of mass.
        /// </summary>
        public Vector2 shift;

        public static RigPose Neutral
        {
            get { return new RigPose { squash = Vector2.one, kneeF = -4f, kneeB = -4f, elbowF = 12f, elbowB = 12f }; }
        }
    }

    /// <summary>
    /// Joints of a character (kid or pedestrian), animated by code. Limbs swing in the
    /// character's side plane: about the body's z axis, measured from each joint's rest pose,
    /// so the joints can be bones of an imported model (whatever their own axes) or the plain
    /// pivots a CharacterBody3D is skinned to.
    /// </summary>
    public class CharacterRig : MonoBehaviour
    {
        [Tooltip("Root of all visuals; squashed and bobbed as a whole.")]
        public Transform body;
        public Transform legFront;
        public Transform legBack;
        public Transform kneeFront;
        public Transform kneeBack;
        public Transform armFront;
        public Transform armBack;
        public Transform elbowFront;
        public Transform elbowBack;
        public Transform head;
        public Transform bag;
        [Header("Torso (a model's own bones; empty for the procedural characters)")]
        [Tooltip("The pelvis (the skeleton's root bone): turns with the legs' stride.")]
        public Transform hips;
        [Tooltip("The lower back: takes half the chest's turn against the pelvis, and the sway over the standing leg.")]
        public Transform spine;
        [Tooltip("The ribcage, which the shoulders hang from: turns with the arms' swing, and breathes.")]
        public Transform chest;
        [Tooltip("Degrees the chest turns per unit of the arms' swing apart (the sine of each arm's swing: a hand's reach in " +
            "front of the shoulder). A run's swing turns it about 12 degrees, a walk's about 5.")]
        public float chestTurnPerSwing = 11f;
        [Tooltip("Degrees the pelvis turns per unit of the legs' swing apart (the other way to the chest's in a stride).")]
        public float hipTurnPerSwing = 6.5f;
        public float maxChestTurn = 15f, maxHipTurn = 10f;
        [Tooltip("Degrees the torso sways over the leg that bears the weight.")]
        public float maxSway = 3f;
        [Tooltip("Degrees the trunk dips forward as the legs reach apart in a stride (upright again as they pass).")]
        public float stepDip = 2f;
        [Tooltip("Degrees the chest lifts and settles as the character breathes.")]
        public float breath = 0.9f;
        [Tooltip("How much of the pose's bag swing the bag takes: 1 for a bag modelled with the kid; less for the Locker Room's " +
            "backpacks (Presentation/BagWear), strapped on over both shoulders.")]
        public float bagSwing = 1f;

        Vector3 bodyBasePosition;
        Vector3 bodyBaseScale = Vector3.one;
        Quaternion bodyBaseRotation = Quaternion.identity;
        Vector3 headBasePosition;

        // A joint's rest rotation and the body's three axes in the joint's own rest frame: axis, the side-to-side axis the
        // limbs swing about (the body's z); up, the axis the torso turns about (y); ahead, the axis it sways about (x).
        struct Joint { public Quaternion rest; public Vector3 axis, up, ahead; }
        readonly Dictionary<Transform, Joint> joints = new Dictionary<Transform, Joint>();
        float breathPhase;

        void Awake()
        {
            if (body != null) { bodyBasePosition = body.localPosition; bodyBaseScale = body.localScale; bodyBaseRotation = body.localRotation; }
            if (head != null) headBasePosition = head.localPosition;
            // Each joint swings about the body's z axis (the character's side-to-side axis),
            // expressed in the joint's own rest frame.
            Transform b = body != null ? body : transform;
            Vector3 swing = b.TransformDirection(Vector3.forward), up = b.TransformDirection(Vector3.up), ahead = b.TransformDirection(Vector3.right);
            foreach (var t in new[] { legFront, legBack, kneeFront, kneeBack, armFront, armBack, elbowFront, elbowBack, head, bag, hips, spine, chest })
            {
                if (t == null || joints.ContainsKey(t)) continue;
                Quaternion inv = Quaternion.Inverse(t.rotation);
                joints[t] = new Joint { rest = t.localRotation, axis = inv * swing, up = inv * up, ahead = inv * ahead };
            }
            // (each character breathes at its own moment, not the whole street in step: the golden ratio spreads the
            // rigs' moments evenly over the 2.9 s breath, however many there are. Not GetInstanceID, an error from Unity
            // 6.5: docs/LEARNINGS.md A11.)
            breathPhase = (rigsMade++ * 0.618034f) % 1f * BreathPeriod;
        }

        static int rigsMade;
        const float BreathPeriod = 2f * Mathf.PI / 2.2f;

        public void Pose(RigPose p)
        {
            Rotate(legFront, p.legF);
            Rotate(legBack, p.legB);
            // Knees only fold backward and elbows only forward, like real joints.
            Rotate(kneeFront, Mathf.Min(p.kneeF, 0f));
            Rotate(kneeBack, Mathf.Min(p.kneeB, 0f));
            Rotate(armFront, p.armF);
            Rotate(armBack, p.armB);
            Rotate(elbowFront, Mathf.Max(p.elbowF, 0f));
            Rotate(elbowBack, Mathf.Max(p.elbowB, 0f));
            Rotate(bag, p.bag * bagSwing);
            if (body != null)
            {
                body.localPosition = bodyBasePosition + new Vector3(p.shift.x, p.bob + p.shift.y, 0f);
                body.localRotation = bodyBaseRotation * Quaternion.Euler(0f, 0f, -p.lean);
                Vector2 squash = p.squash == Vector2.zero ? Vector2.one : p.squash;
                // Squash keeps the volume: wider in both x and depth when shorter.
                body.localScale = Vector3.Scale(bodyBaseScale, new Vector3(squash.x, squash.y, squash.x));
            }
            float headTurn = 0f, headSway = 0f, headDip = 0f;
            if (spine != null || chest != null) Torso(p, out headTurn, out headSway, out headDip);
            if (head != null)
            {
                Turn(head, p.headTilt + headDip, headTurn, headSway);
                head.localPosition = headBasePosition;
            }
        }

        /// <summary>
        /// The middle of the body, from the limbs' pose (so every animator gets it without saying so). A real stride turns
        /// the pelvis with the legs and the ribcage the other way with the arms, sways the torso over the leg bearing the
        /// weight, dips the trunk a little as the legs reach apart, and the chest breathes all the while; without it the chest and belly were one rigid block and the arms
        /// swung as if hung from a fixed frame (docs/LEARNINGS.md C19). Each turn is the sine of each limb's swing apart (how
        /// far the hand or foot reaches in front, so both arms raised overhead turn nothing), clamped. The pelvis takes its
        /// turn; the lower back and the chest share the chest's turn and the dip; the head turns, sways and dips back the
        /// other way, so the eyes stay level and on the way ahead. Returns the head's share.
        /// </summary>
        void Torso(RigPose p, out float headTurn, out float headSway, out float headDip)
        {
            float arms = Mathf.Sin(p.armF * Mathf.Deg2Rad) - Mathf.Sin(p.armB * Mathf.Deg2Rad);   // > 0: the near arm forward
            float legs = Mathf.Sin(p.legF * Mathf.Deg2Rad) - Mathf.Sin(p.legB * Mathf.Deg2Rad);   // > 0: the near leg forward
            float chestTurn = Mathf.Clamp(arms * chestTurnPerSwing, -maxChestTurn, maxChestTurn);
            float hipTurn = Mathf.Clamp(legs * hipTurnPerSwing, -maxHipTurn, maxHipTurn);
            // The leg bearing the weight is the straighter one, while the legs are apart (a stride, not standing).
            float apart = Mathf.Clamp01(Mathf.Abs(legs) / 0.4f);
            float sway = Mathf.Clamp((Mathf.Abs(p.kneeB) - Mathf.Abs(p.kneeF)) / 40f, -1f, 1f) * apart * maxSway;   // > 0: onto the near leg
            float breathe = Mathf.Sin((Time.time + breathPhase) * 2.2f) * breath;
            // (a forward lean is a negative pitch for a bone pointing up)
            float dip = -stepDip * Mathf.Clamp01(Mathf.Abs(legs) / 1.2f);
            // A turn about the body's up axis carries its near side (-z) backward when positive, so "the near side
            // forward" is negative; a sway about its forward axis tips the top toward the far side (+z) when positive.
            Turn(hips, 0f, -hipTurn, 0f);
            float back = -(chestTurn - hipTurn) * 0.5f;
            Turn(spine, dip * 0.5f, back, -sway);
            Turn(chest, breathe + dip * 0.5f, back, 0f);
            headTurn = chestTurn;
            headSway = sway;
            headDip = -dip;
        }

        /// <summary>A joint pitched about the body's side axis, turned about its up axis and swayed about its forward axis.</summary>
        void Turn(Transform t, float pitch, float turn, float sway)
        {
            if (t == null) return;
            Joint j;
            if (!joints.TryGetValue(t, out j)) { t.localRotation = Quaternion.Euler(0f, 0f, pitch); return; }
            t.localRotation = j.rest * Quaternion.AngleAxis(turn, j.up) * Quaternion.AngleAxis(sway, j.ahead) * Quaternion.AngleAxis(pitch, j.axis);
        }

        /// <summary>
        /// Yaw for a character facing right (+1) or left (-1), or turning in between. Characters
        /// stand a little turned toward the camera so the face reads, and turn through facing it.
        /// </summary>
        public static float FacingYaw(float facing)
        {
            const float towardCamera = 24f;
            float t = Mathf.SmoothStep(0f, 1f, (1f - Mathf.Clamp(facing, -1f, 1f)) * 0.5f);
            return Mathf.Lerp(towardCamera, 180f - towardCamera, t);
        }

        void Rotate(Transform t, float angle)
        {
            if (t == null) return;
            Joint j;
            if (joints.TryGetValue(t, out j)) t.localRotation = j.rest * Quaternion.AngleAxis(angle, j.axis);
            else t.localRotation = Quaternion.Euler(0f, 0f, angle);
        }
    }
}
