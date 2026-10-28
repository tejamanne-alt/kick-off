using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>A solid box centred on the object (crates, walls, platforms, steps, house parts).</summary>
    public class Box3D : ProceduralShape
    {
        public Vector3 size = Vector3.one;
        public Vector3 offset;
        public Color color = Color.white;
        public MeshBuilder.Faces faces = MeshBuilder.Faces.NoBottom;
        [Tooltip("Put the front face (toward the camera) in submesh 1, e.g. for a facade texture.")]
        public bool separateFront;

        protected override int SubmeshCount { get { return separateFront ? 2 : 1; } }

        protected override void Build(MeshBuilder b)
        {
            Vector3 half = size * 0.5f;
            b.Box(0, offset - half, offset + half, color, faces, separateFront ? 1 : 0);
        }
    }
}
