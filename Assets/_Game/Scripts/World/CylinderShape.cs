using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A cylinder with smooth sides, lying along the depth axis by default: rolling pipes
    /// (with a dark hollow), coins (a thin disc with a raised face) and posts.
    /// </summary>
    public class CylinderShape : ProceduralShape
    {
        public float radius = 0.45f;
        public float length = 1.4f;
        public Vector3 axis = Vector3.forward;
        public Color sideColor = new Color(0.6f, 0.6f, 0.64f);
        public Color endColor = new Color(0.68f, 0.68f, 0.72f);
        [Tooltip("Inner disc on each end: a pipe's hollow, a coin's face.")]
        public float innerRadius;
        public Color innerColor = new Color(0.2f, 0.2f, 0.22f);
        public int segments = 20;

        protected override void Build(MeshBuilder b)
        {
            b.Cylinder(0, Vector3.zero, axis, radius, length, sideColor, endColor, innerRadius, innerColor, segments);
        }
    }
}
