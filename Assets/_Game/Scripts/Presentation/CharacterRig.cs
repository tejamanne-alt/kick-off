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
        public Vector2 squash;

        public static RigPose Neutral
        {
            get { return new RigPose { squash = Vector2.one, kneeF = -4f, kneeB = -4f, elbowF = 12f, elbowB = 12f }; }
        }
    }

    /// <summary>Pivots of a paper-doll character (kid or pedestrian), animated by code.</summary>
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

        Vector3 bodyBasePosition;
        Vector3 headBasePosition;

        void Awake()
        {
            if (body != null) bodyBasePosition = body.localPosition;
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
            if (body != null)
            {
                body.localPosition = bodyBasePosition + Vector3.up * p.bob;
                body.localRotation = Quaternion.Euler(0f, 0f, -p.lean);
                Vector2 squash = p.squash == Vector2.zero ? Vector2.one : p.squash;
                body.localScale = new Vector3(squash.x, squash.y, 1f);
            }
            if (head != null)
            {
                head.localRotation = Quaternion.Euler(0f, 0f, p.headTilt);
                head.localPosition = headBasePosition;
            }
        }

        static void Rotate(Transform t, float angle)
        {
            if (t != null) t.localRotation = Quaternion.Euler(0f, 0f, angle);
        }
    }
}
