using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A tunnel or underpass: while the kid is inside, the screen darkens to a
    /// pool of light around them (see DarknessOverlay).
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class DarkZone : HazardBase
    {
        [Range(0f, 1f)] public float darkness = 0.85f;

        /// <summary>Darkness wanted right now (max of all zones the kid is in).</summary>
        public static float Wanted { get; private set; }

        static int insideCount;

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            Player.KidController kid;
            if (!TryGetKid(other, out kid)) return;
            insideCount++;
            Wanted = Mathf.Max(Wanted, darkness);
        }

        void OnTriggerExit2D(Collider2D other)
        {
            Player.KidController kid;
            if (!TryGetKid(other, out kid)) return;
            insideCount = Mathf.Max(0, insideCount - 1);
            if (insideCount == 0) Wanted = 0f;
        }

        public override void ResetState()
        {
            insideCount = 0;
            Wanted = 0f;
        }

        void OnDestroy()
        {
            insideCount = 0;
            Wanted = 0f;
        }
    }
}
