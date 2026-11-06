using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// The teen boy's school satchel (the supplied boy model has none): a soft leather bag with a deep
    /// flap, a darker welt round its edges and a brass buckle, centred on the object, its broad face
    /// toward -z (the camera side of the body), its width along x (the way he faces). It rides on the
    /// rig's Bag bone; LevelBuildKit hangs a strap from it over his chest.
    /// </summary>
    public class SatchelShape : ProceduralShape
    {
        public Vector3 size = new Vector3(0.34f, 0.26f, 0.1f);
        public Color leather = new Color(0.58f, 0.24f, 0.18f);
        public Color flap = new Color(0.5f, 0.2f, 0.15f);
        public Color welt = new Color(0.36f, 0.15f, 0.11f);
        public Color buckle = new Color(0.86f, 0.7f, 0.36f);

        protected override void Build(MeshBuilder b)
        {
            Vector3 h = size * 0.5f;
            // The body: a box with its edges eased by a slightly smaller box over each face pair.
            b.Box(0, new Vector3(-h.x, -h.y, -h.z * 0.86f), new Vector3(h.x, h.y, h.z * 0.86f), leather, MeshBuilder.Faces.All);
            b.Box(0, new Vector3(-h.x * 0.94f, -h.y * 1.04f, -h.z), new Vector3(h.x * 0.94f, h.y * 0.96f, h.z), leather, MeshBuilder.Faces.All);
            // A welt along the bottom and up the ends.
            b.Box(0, new Vector3(-h.x * 1.02f, -h.y * 1.06f, -h.z * 0.6f), new Vector3(h.x * 1.02f, -h.y * 0.92f, h.z * 0.6f), welt, MeshBuilder.Faces.All);
            // The flap over the front, two thirds of the way down, a little proud of it.
            float fz = -h.z - 0.012f;
            b.Box(0, new Vector3(-h.x * 0.97f, -h.y * 0.25f, fz), new Vector3(h.x * 0.97f, h.y * 1.02f, -h.z + 0.01f), flap, MeshBuilder.Faces.All);
            b.Box(0, new Vector3(-h.x * 0.97f, -h.y * 0.29f, fz - 0.004f), new Vector3(h.x * 0.97f, -h.y * 0.22f, fz + 0.006f), welt, MeshBuilder.Faces.All);
            // A strap and buckle down the middle of the flap.
            b.Box(0, new Vector3(-0.025f, -h.y * 0.55f, fz - 0.008f), new Vector3(0.025f, h.y * 0.4f, fz), welt, MeshBuilder.Faces.All);
            b.Box(0, new Vector3(-0.03f, -h.y * 0.42f, fz - 0.014f), new Vector3(0.03f, -h.y * 0.18f, fz - 0.006f), buckle, MeshBuilder.Faces.All);
        }
    }
}
