using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Merges the never-moving street and scenery meshes under this object into a few static
    /// batches once the level has built them, so a long 3D street costs a handful of draw calls.
    /// </summary>
    public class StaticBatcher : MonoBehaviour
    {
        void Start()
        {
            if (Application.isPlaying) StaticBatchingUtility.Combine(gameObject);
        }
    }
}
