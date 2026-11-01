using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// Keeps the stages near the kid loaded: each stage is a scene built at its place in the world
    /// (HolidayStages), loaded additively a little ahead of the kid and unloaded once well behind.
    /// </summary>
    public class RunWorldStreamer : MonoBehaviour
    {
        public static RunWorldStreamer Current { get; private set; }

        [Tooltip("The kid whose x decides what to load.")]
        public Transform follow;
        [Tooltip("Stages whose start is within this far ahead of the kid are loaded.")]
        public float loadAhead = 190f;
        [Tooltip("Stages whose end is further behind the kid than this are unloaded.")]
        public float keepBehind = 80f;

        void Awake() { Current = this; }
        void OnDestroy() { if (Current == this) Current = null; }
    }
}
