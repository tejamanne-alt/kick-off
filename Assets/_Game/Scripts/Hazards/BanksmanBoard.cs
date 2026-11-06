using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// The banksman's lollipop board at a building site's vehicle gate: GO (green) while walkers may cross, GO flashing just
    /// before the site's vehicles come out, STOP (red) while they cross the footpath. It shows the gate's Crossing.
    /// </summary>
    public class BanksmanBoard : MonoBehaviour
    {
        public Crossing crossing;
        public GameObject stopFace, goFace;
        [Tooltip("The banksman's arm and board: turned a little toward the gate while it says STOP.")]
        public Transform board;

        void Update()
        {
            if (crossing == null) return;
            var light = crossing.Current;
            bool flashOff = light == Crossing.Light.Amber && Mathf.Repeat(Time.time * 3f, 1f) >= 0.55f;
            if (stopFace != null) stopFace.SetActive(light == Crossing.Light.Red);
            if (goFace != null) goFace.SetActive(light != Crossing.Light.Red && !flashOff);
            if (board != null)
            {
                float want = light == Crossing.Light.Red ? -14f : 0f;
                var e = board.localEulerAngles;
                float z = Mathf.MoveTowardsAngle(e.z, want, Time.deltaTime * 60f);
                board.localEulerAngles = new Vector3(e.x, e.y, z);
            }
        }
    }
}
