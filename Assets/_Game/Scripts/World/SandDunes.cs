using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// One stretch of the beach's sand (see <see cref="SandField"/>) as a smooth mesh: a grid on a
    /// fixed half-unit lattice along x, finer in depth where the camera looks, with smooth normals.
    /// Neighbouring stretches sample the same lattice (and one sample past their ends, for the
    /// normals), so they meet without a seam. Textures come from the material's world-space
    /// projection, so no UVs are needed.
    /// </summary>
    public class SandDunes : ProceduralShape
    {
        public SandField field = new SandField();
        [Tooltip("This stretch, along x. Both ends should sit on the half-unit lattice.")]
        public float fromX, toX = 40f;

        public const float Step = 0.5f;

        /// <summary>The depths sampled (one extra at each end, for the normals): coarse in front, below the screen; finer from there to the sea.</summary>
        static readonly float[] Rows = MakeRows();

        static float[] MakeRows()
        {
            var rows = new List<float>();
            for (int k = -1; k < 8; k++) rows.Add(-16f + k * 1.25f);
            for (int k = 0; k <= 41; k++) rows.Add(-6f + k * 0.4f);
            rows.Add(11.2f);
            rows.Add(12f);
            return rows.ToArray();
        }

        protected override void Build(MeshBuilder b)
        {
            int cols = Mathf.Max(1, Mathf.RoundToInt((toX - fromX) / Step));
            int nx = cols + 3, nz = Rows.Length;
            var h = new float[nx, nz];
            for (int i = 0; i < nx; i++)
                for (int j = 0; j < nz; j++)
                    h[i, j] = field.Height(fromX + (i - 1) * Step, Rows[j]);

            var index = new int[nx, nz];
            for (int i = 1; i < nx - 1; i++)
                for (int j = 1; j < nz - 1; j++)
                {
                    float x = fromX + (i - 1) * Step, z = Rows[j];
                    float dx = (h[i + 1, j] - h[i - 1, j]) / (2f * Step);
                    float dz = (h[i, j + 1] - h[i, j - 1]) / (Rows[j + 1] - Rows[j - 1]);
                    index[i, j] = b.Vertex(new Vector3(x, h[i, j], z), new Vector3(-dx, 1f, -dz), field.Tint(x, z), Vector2.zero);
                }
            for (int i = 1; i < nx - 2; i++)
                for (int j = 1; j < nz - 2; j++)
                {
                    b.Tri(0, index[i, j], index[i, j + 1], index[i + 1, j + 1]);
                    b.Tri(0, index[i, j], index[i + 1, j + 1], index[i + 1, j]);
                }
        }
    }
}
