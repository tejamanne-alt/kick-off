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
        // The combined meshes made here, which belong to no scene: unloading a Holiday Run stage (an additive scene) left
        // every one of them in memory, a lap's worth more each day of the run. Only renderers under this object draw them.
        readonly List<Mesh> combined = new List<Mesh>();

        void Start()
        {
            if (!Application.isPlaying) return;
            var parts = new List<GameObject>();
            var filters = new List<MeshFilter>();
            var before = new HashSet<Mesh>();
            foreach (var filter in GetComponentsInChildren<MeshFilter>())
                if (filter.GetComponentInParent<KitInstance>() == null)
                {
                    parts.Add(filter.gameObject);
                    filters.Add(filter);
                    if (filter.sharedMesh != null) before.Add(filter.sharedMesh);
                }
            if (parts.Count == 0) return;
            StaticBatchingUtility.Combine(parts.ToArray(), gameObject);
            foreach (var filter in filters)
            {
                var mesh = filter.sharedMesh;
                if (mesh != null && !before.Contains(mesh) && !combined.Contains(mesh)) combined.Add(mesh);
            }
        }

        void OnDestroy()
        {
            foreach (var mesh in combined)
                if (mesh != null) Destroy(mesh);
            combined.Clear();
        }
    }
}
