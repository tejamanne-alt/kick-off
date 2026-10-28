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

        public static RigPose Neutral
        {
            get { return new RigPose { squash = Vector2.one, kneeF = -4f, kneeB = -4f, elbowF = 12f, elbowB = 12f }; }
        }
    }

    /// <summary>
    /// Joints of a character (kid or pedestrian), animated by code. Limbs swing in the
    /// character's side plane (about local z); the 3D body (CharacterBody3D) is skinned to these.
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

        Vector3 bodyBasePosition;
        Vector3 bodyBaseScale = Vector3.one;
        Vector3 headBasePosition;

        void Awake()
        {
            if (body != null) { bodyBasePosition = body.localPosition; bodyBaseScale = body.localScale; }
            if (head != null) headBasePosition = head.localPosition;
        }

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
            Rotate(bag, p.bag);
            if (body != null)
            {
                body.localPosition = bodyBasePosition + Vector3.up * p.bob;
                body.localRotation = Quaternion.Euler(0f, 0f, -p.lean);
                Vector2 squash = p.squash == Vector2.zero ? Vector2.one : p.squash;
                // Squash keeps the volume: wider in both x and depth when shorter.
                body.localScale = Vector3.Scale(bodyBaseScale, new Vector3(squash.x, squash.y, squash.x));
            }
            if (head != null)
            {
                head.localRotation = Quaternion.Euler(0f, 0f, p.headTilt);
                head.localPosition = headBasePosition;
            }
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

        static void Rotate(Transform t, float angle)
        {
            if (t != null) t.localRotation = Quaternion.Euler(0f, 0f, angle);
        }
    }
}
