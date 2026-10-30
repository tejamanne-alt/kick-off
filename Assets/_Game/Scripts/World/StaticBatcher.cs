using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Merges the never-moving street and scenery meshes under this object into a few static
    /// batches once the level has built them, so a long 3D street costs a handful of draw calls.
    /// Asset-kit models (<see cref="KitInstance"/>) stay out: their meshes are shared between
    /// copies, and combining thousands of them would multiply the street's memory for little gain.
    /// </summary>
    public class StaticBatcher : MonoBehaviour
    {
        void Start()
        {
            if (!Application.isPlaying) return;
            var parts = new List<GameObject>();
            foreach (var filter in GetComponentsInChildren<MeshFilter>())
                if (filter.GetComponentInParent<KitInstance>() == null) parts.Add(filter.gameObject);
            if (parts.Count > 0) StaticBatchingUtility.Combine(parts.ToArray(), gameObject);
        }
    }
}
