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
            float bob = walking ? Mathf.Abs(Mathf.Cos(phase)) * 0.03f : 0f;
            rig.Pose(s * swing, -s * swing, -s * swing * 0.7f, s * swing * 0.7f, bob, Vector2.one);
        }
    }
}
