using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A rounded shape made of overlapping ellipsoids (an animal's body, a leg, a wing).
    /// With the outlined toon material the blobs read as one soft, cartoon form.
    /// </summary>
    public class BlobShape : ProceduralShape
    {
        [System.Serializable]
        public struct Blob
        {
            public Vector3 center;
            public Vector3 radii;
            public Color color;
            public Blob(Vector3 center, Vector3 radii, Color color) { this.center = center; this.radii = radii; this.color = color; }
        }

        public List<Blob> blobs = new List<Blob>();

        protected override void Build(MeshBuilder b)
        {
            foreach (var blob in blobs)
            {
                // Small blobs need fewer facets.
                float size = Mathf.Max(blob.radii.x, Mathf.Max(blob.radii.y, blob.radii.z));
                int lon = size > 0.1f ? 16 : 10, lat = size > 0.1f ? 10 : 7;
                b.Ellipsoid(0, blob.center, blob.radii, blob.color, lon, lat);
            }
        }
    }
}
