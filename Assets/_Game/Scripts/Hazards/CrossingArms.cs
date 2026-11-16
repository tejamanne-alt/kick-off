using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A level crossing's barrier arms (the Kamakura kit's KmCrossingBarrier: its Arm, drawn raised, its origin at its pivot):
    /// they come down while their <see cref="Crossing"/> flashes (amber and red) and go back up on green. Each turns about its
    /// pivot in the street's plane, coming down along the lane behind it, never toward the camera, where it would hide the
    /// ball (docs/LEARNINGS.md E10).
    /// </summary>
    public class CrossingArms : MonoBehaviour
    {
        public Crossing crossing;
        public Transform[] arms;
        /// <summary>Each arm's turn when down, degrees about the street's depth (negative: it comes down to the right).</summary>
        public float[] downAngles;
        /// <summary>How fast an arm comes down or goes up, degrees a second.</summary>
        public float speed = 60f;

        Quaternion[] raised;
        float[] angles;

        void Awake()
        {
            int n = arms != null ? arms.Length : 0;
            raised = new Quaternion[n];
            angles = new float[n];
            for (int i = 0; i < n; i++)
                if (arms[i] != null) raised[i] = arms[i].rotation;
        }

        void Update()
        {
            if (arms == null || raised == null) return;
            bool down = crossing != null && crossing.Current != Crossing.Light.Green;
            for (int i = 0; i < arms.Length; i++)
            {
                if (arms[i] == null) continue;
                float target = down && downAngles != null && i < downAngles.Length ? downAngles[i] : 0f;
                angles[i] = Mathf.MoveTowards(angles[i], target, speed * Time.deltaTime);
                arms[i].rotation = Quaternion.AngleAxis(angles[i], Vector3.forward) * raised[i];
            }
        }
    }
}
