using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>A smooth sphere (the ball). Its UVs show a drawing of a ball on the side facing the camera.</summary>
    public class SphereShape : ProceduralShape
    {
        public float radius = 0.2f;
        public Color color = Color.white;

        protected override void Build(MeshBuilder b)
        {
            b.Sphere(0, Vector3.zero, radius, color);
        }
    }
}
