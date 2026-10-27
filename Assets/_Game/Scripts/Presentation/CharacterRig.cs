using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>Pivots of a paper-doll character (kid or pedestrian), animated by code.</summary>
    public class CharacterRig : MonoBehaviour
    {
        [Tooltip("Root of all visuals; squashed and bobbed as a whole.")]
        public Transform body;
        public Transform legFront;
        public Transform legBack;
        public Transform armFront;
        public Transform armBack;
        public Transform head;

        Vector3 bodyBasePosition;
        Vector3 headBasePosition;

        void Awake()
        {
            if (body != null) bodyBasePosition = body.localPosition;
            if (head != null) headBasePosition = head.localPosition;
        }

        /// <summary>Apply a pose. Angles in degrees; positive swings forward (to the right).</summary>
        public void Pose(float legF, float legB, float armF, float armB, float bob, Vector2 squash, float headTilt = 0f)
        {
            if (legFront != null) legFront.localRotation = Quaternion.Euler(0f, 0f, legF);
            if (legBack != null) legBack.localRotation = Quaternion.Euler(0f, 0f, legB);
            if (armFront != null) armFront.localRotation = Quaternion.Euler(0f, 0f, armF);
            if (armBack != null) armBack.localRotation = Quaternion.Euler(0f, 0f, armB);
            if (body != null)
            {
                body.localPosition = bodyBasePosition + Vector3.up * bob;
                body.localScale = new Vector3(squash.x, squash.y, 1f);
            }
            if (head != null)
            {
                head.localRotation = Quaternion.Euler(0f, 0f, headTilt);
                head.localPosition = headBasePosition;
            }
        }
    }
}
