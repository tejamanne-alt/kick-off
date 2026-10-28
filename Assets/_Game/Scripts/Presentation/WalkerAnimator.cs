using DribbleToSchool.Hazards;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>Simple stroll animation for pedestrians.</summary>
    [RequireComponent(typeof(CharacterRig))]
    public class WalkerAnimator : MonoBehaviour
    {
        public Pedestrian pedestrian;
        public float swing = 25f;

        CharacterRig rig;
        float phase;

        void Awake()
        {
            rig = GetComponent<CharacterRig>();
        }

        void LateUpdate()
        {
            bool walking = pedestrian == null || pedestrian.IsWalking;
            if (walking) phase += Time.deltaTime * (pedestrian != null ? pedestrian.walkSpeed : 1f) * 5f;
            float s = walking ? Mathf.Sin(phase) : 0f;
            var p = RigPose.Neutral;
            p.bob = walking ? Mathf.Abs(Mathf.Cos(phase)) * 0.03f : 0f;
            p.legF = s * swing;
            p.legB = -s * swing;
            p.armF = -s * swing * 0.7f;
            p.armB = s * swing * 0.7f;
            if (walking)
            {
                // A gentle stroll: knees lift a little in the swing, elbows stay soft.
                p.kneeF = -Knee(phase);
                p.kneeB = -Knee(phase + Mathf.PI);
                p.elbowF = 16f + 12f * Mathf.Max(0f, -s);
                p.elbowB = 16f + 12f * Mathf.Max(0f, s);
                p.lean = 2f;
            }
            rig.Pose(p);
        }

        static float Knee(float legPhase)
        {
            float swing = Mathf.Max(0f, Mathf.Cos(legPhase + 0.9f));
            return 5f + 35f * swing * swing;
        }
    }
}
