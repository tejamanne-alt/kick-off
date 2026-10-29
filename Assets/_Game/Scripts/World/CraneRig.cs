using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A tower crane carrying a load: each frame the jib slews toward the load's hook, the
    /// trolley runs out along the jib to sit right above it, and the cable hangs straight down
    /// from the trolley to the hook. The load itself is moved by its own MovingPlatform; the
    /// crane only follows it, so it always looks like the crane is doing the carrying.
    /// </summary>
    public class CraneRig : MonoBehaviour
    {
        [Tooltip("Pivot at the top of the mast; the jib runs along its local +x.")]
        public Transform jib;
        public Transform trolley;
        [Tooltip("The carried load (the moving platform).")]
        public Transform load;
        [Tooltip("Where the cable meets the hook, in the load's local space.")]
        public Vector3 hookLocal = new Vector3(0f, 3.9f, 0.72f);
        public LineRenderer cable;
        [Tooltip("The trolley's drop below the jib pivot.")]
        public float trolleyDrop = 0.25f;

        void LateUpdate()
        {
            if (jib == null || load == null) return;
            Vector3 hook = load.TransformPoint(hookLocal);
            Vector3 pivot = jib.position;
            float dx = hook.x - pivot.x, dz = hook.z - pivot.z;
            float reach = Mathf.Sqrt(dx * dx + dz * dz);
            // Rotating about +y takes +x toward -z, so the yaw that points +x at (dx, dz) is atan2(-dz, dx).
            jib.rotation = Quaternion.Euler(0f, Mathf.Atan2(-dz, dx) * Mathf.Rad2Deg, 0f);
            if (trolley != null) trolley.localPosition = new Vector3(reach, -trolleyDrop, 0f);
            if (cable != null)
            {
                cable.SetPosition(0, new Vector3(hook.x, pivot.y - trolleyDrop - 0.1f, hook.z));
                cable.SetPosition(1, hook);
            }
        }
    }
}
