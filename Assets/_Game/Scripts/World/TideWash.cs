using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// The sea washing up the beach and back: one sheet of sea from out under the open water, up the sand to a wavy front edge
    /// with a white band of foam, rebuilt each frame it can be seen from <see cref="Level"/> (0 = the tide is out, 1 = in, over the kid's path).
    /// The sheet follows the beach's own shape (<see cref="SandField.Shore"/>) a hair above the sand, and where the sand runs
    /// down under the sea it stays just under the sea's surface, so the wash and the sea are one body of water: the same
    /// material, the same light, no seam, no strip of sand between them. Submesh 0 is the water (sea material), 1 the foam.
    /// </summary>
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class TideWash : MonoBehaviour
    {
        public float fromX, toX = 6f, groundY;
        [Tooltip("Front edge z at low and high water.")]
        public float lowZ = 7.2f, highZ = -2.8f;
        [Tooltip("The water's edge, where the sand drops to the sea.")]
        public float seaZ = 9.3f;
        [Tooltip("The height of the sea's surface (world y): the sheet runs on just under it once the sand has gone under.")]
        public float seaY = -0.3f;

        [Range(0f, 1f)] public float Level;

        /// <summary>The depths (z) of the sheet's rows behind its front: close together where the beach curves down into the sea, out under the water at the back.</summary>
        static readonly float[] Shelf = { 4.6f, 5.4f, 5.8f, 6.25f, 6.8f, 7.4f, 8.0f, 8.5f, 8.9f, 9.3f, 9.7f, 10.1f, 10.6f, 11.4f, 12.8f };

        Mesh mesh;
        Vector3[] vertices;
        int columns;
        static int Rows { get { return 2 + Shelf.Length; } }
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

        // The sheet's mesh is made here and belongs to no scene: it goes with the wash (a Holiday Run stage unloads).
        void OnDestroy()
        {
            if (mesh != null) Destroy(mesh);
        }

        /// <summary>The sheet's farthest depth (the back of the shelf), where the view is widest.</summary>
        const float BackZ = 12.8f;
        float builtLevel = -1f, builtTime = -1f;

        void LateUpdate()
        {
            time += Time.deltaTime;
            // The sheet is a pure function of Level and time, so a frame that would draw it the same, or where it can't be seen,
            // needn't rebuild it: it is exact again the frame it comes back into view. (A beach level has up to five of them, of
            // 700 to 900 vertices each, and only one or two are ever in view: docs/PERFORMANCE.md.) The 2 m margin covers the
            // camera moving after this runs in a frame.
            if (time == builtTime && Level == builtLevel) return;
            float nearestX = Mathf.Clamp(AmbientView.CameraX, fromX - 3f, toX + 3f);
            if (AmbientView.Valid && AmbientView.OutsideBy(nearestX, BackZ) > 2f) return;
            Rebuild();
        }

        /// <summary>The sheet's height at depth z: a hair above the beach, and never above the sea once the beach is under it.</summary>
        public float HeightAt(float z)
        {
            return Mathf.Max(groundY + 0.025f + SandField.Shore(z), seaY - 0.012f);
        }

        void Rebuild()
        {
            if (mesh == null) return;
            float x0 = fromX - 3f, step = (toX - fromX + 6f) / (columns - 1);
            // Ease the front so it lingers at the top of the swash, as a real wave does.
            float front = Mathf.Lerp(lowZ, highZ, Mathf.Pow(Mathf.Clamp01(Level), 0.8f));
            int rows = Rows;
            Vector3 origin = transform.position;   // (read once: it is a native call, and the loop below runs ~800 times)
            for (int c = 0; c < columns; c++)
            {
                float x = x0 + c * step;
                float z0 = Shoreline.Front(x, fromX, toX, front, seaZ, time);
                for (int r = 0; r < rows; r++)
                {
                    // The front and the back of the foam band, then the shelf rows behind it (those it has passed gather just behind it).
                    float z = r == 0 ? z0 : r == 1 ? z0 + 0.22f : Mathf.Max(Shelf[r - 2], z0 + 0.3f + 0.01f * (r - 2));
                    vertices[c * rows + r] = new Vector3(x, HeightAt(z), z) - origin;
                }
            }
            mesh.vertices = vertices;
            mesh.RecalculateBounds();
            builtLevel = Level; builtTime = time;
        }
    }
}
