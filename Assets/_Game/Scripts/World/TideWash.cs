using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The sea washing up the beach and back: a sheet of sea running from the water's edge up
    /// the sand to a wavy front edge with a white band of foam, rebuilt each frame from
    /// <see cref="Level"/> (0 = the tide is out, 1 = in, over the kid's path). Submesh 0 is the
    /// water (sea material), 1 the foam.
    /// </summary>
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class TideWash : MonoBehaviour
    {
        public float fromX, toX = 6f, groundY;
        [Tooltip("Front edge z at low and high water.")]
        public float lowZ = 7.2f, highZ = -2.8f;
        [Tooltip("The water's edge, where the sand drops to the sea.")]
        public float seaZ = 9.3f;
        [Tooltip("Where the beach starts sloping down to the water.")]
        public float slopeZ = 5.6f;

        [Range(0f, 1f)] public float Level;

        Mesh mesh;
        Vector3[] vertices;
        int columns;
        const int Rows = 5;
        float time;

        void Awake() { Build(); }

        void Build()
        {
            float x0 = fromX - 3f, x1 = toX + 3f;
            columns = Mathf.Max(2, Mathf.CeilToInt((x1 - x0) / 0.25f) + 1);
            vertices = new Vector3[columns * Rows];
            var normals = new Vector3[vertices.Length];
            var colors = new Color[vertices.Length];
            for (int i = 0; i < normals.Length; i++) { normals[i] = Vector3.up; colors[i] = Color.white; }
            var water = new System.Collections.Generic.List<int>();
            var foam = new System.Collections.Generic.List<int>();
            for (int c = 0; c < columns - 1; c++)
                for (int r = 0; r < Rows - 1; r++)
                {
                    int a = c * Rows + r, b = a + Rows;
                    var list = r == 0 ? foam : water;
                    // Rows run away from the camera (+z), columns along +x: wind so the face points up.
                    list.Add(a); list.Add(a + 1); list.Add(b + 1);
                    list.Add(a); list.Add(b + 1); list.Add(b);
                }
            mesh = new Mesh { name = "TideWash" };
            mesh.MarkDynamic();
            mesh.vertices = vertices;
            mesh.normals = normals;
            mesh.colors = colors;
            mesh.subMeshCount = 2;
            mesh.SetTriangles(water, 0);
            mesh.SetTriangles(foam, 1);
            GetComponent<MeshFilter>().sharedMesh = mesh;
            Rebuild();
        }

        void LateUpdate()
        {
            time += Time.deltaTime;
            Rebuild();
        }

        void Rebuild()
        {
            if (mesh == null) return;
            float x0 = fromX - 3f, step = (toX - fromX + 6f) / (columns - 1);
            // Ease the front so it lingers at the top of the swash, as a real wave does.
            float front = Mathf.Lerp(lowZ, highZ, Mathf.Pow(Mathf.Clamp01(Level), 0.8f));
            for (int c = 0; c < columns; c++)
            {
                float x = x0 + c * step;
                float z0 = Shoreline.Front(x, fromX, toX, front, seaZ, time);
                float[] zs = { z0, Mathf.Min(z0 + 0.22f, seaZ), Mathf.Max(z0 + 0.3f, slopeZ - 0.2f), Mathf.Max(z0 + 0.35f, slopeZ + 0.2f), seaZ + 0.6f };
                for (int r = 0; r < Rows; r++)
                {
                    float z = Mathf.Min(zs[r], seaZ + 0.6f);
                    // A hair above the sand, following it down toward the water.
                    float y = groundY + 0.025f - Mathf.InverseLerp(slopeZ, seaZ, z) * 0.17f - (z > seaZ ? 0.2f : 0f);
                    vertices[c * Rows + r] = new Vector3(x, y, z) - transform.position;
                }
            }
            mesh.vertices = vertices;
            mesh.RecalculateBounds();
        }
    }
}
