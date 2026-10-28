using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Base for meshes built from a few parameters when the scene loads (and live in the
    /// editor when a parameter changes), so scenes stay small and shapes stay editable.
    /// Materials are assigned on the MeshRenderer, one per submesh.
    /// </summary>
    [ExecuteAlways]
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public abstract class ProceduralShape : MonoBehaviour
    {
        Mesh mesh;
        bool dirty;

        protected virtual int SubmeshCount { get { return 1; } }
        protected abstract void Build(MeshBuilder builder);

        void OnEnable()
        {
            Rebuild();
        }

        void OnValidate()
        {
            dirty = true;
        }

        void Update()
        {
            if (!dirty) return;
            dirty = false;
            Rebuild();
        }

        public void Rebuild()
        {
            var builder = new MeshBuilder(SubmeshCount);
            Build(builder);
            if (mesh == null)
            {
                mesh = new Mesh();
                mesh.name = name + " (procedural)";
                mesh.hideFlags = HideFlags.DontSave;
            }
            builder.Fill(mesh);
            GetComponent<MeshFilter>().sharedMesh = mesh;
        }

        void OnDestroy()
        {
            if (mesh == null) return;
            if (Application.isPlaying) Destroy(mesh);
            else DestroyImmediate(mesh);
        }
    }
}
