using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A stretch of street seen in 3D: a solid slab from <see cref="fromX"/> to <see cref="toX"/>
    /// whose top is made of strips running along the street (front pavement, kerb, road, back
    /// pavement...), each with its own height, material and tint. The gameplay surface is
    /// <see cref="top"/> at z = 0; strips can sit a little higher (kerbs, pavements). Ends can be
    /// closed with side walls, which shows the slab's depth at steps and gaps.
    /// </summary>
    public class StreetSlab : ProceduralShape
    {
        [System.Serializable]
        public struct Strip
        {
            public float zFrom;
            public float zTo;
            [Tooltip("Height above the slab top (kerbs, raised pavements).")]
            public float lift;
            public int submesh;
            public Color color;

            public Strip(float zFrom, float zTo, float lift, int submesh, Color color)
            {
                this.zFrom = zFrom; this.zTo = zTo; this.lift = lift; this.submesh = submesh; this.color = color;
            }
        }

        public float fromX;
        public float toX = 10f;
        public float top;
        public float bottom = -12f;
        public bool closeLeft = true;
        public bool closeRight = true;
        public int materials = 1;
        public List<Strip> strips = new List<Strip>();
        [Tooltip("Colour of the slab's sides (end caps and risers), usually the soil or kerb colour.")]
        public Color sideColor = new Color(0.55f, 0.52f, 0.5f);
        public int sideSubmesh;

        protected override int SubmeshCount { get { return Mathf.Max(1, materials); } }

        protected override void Build(MeshBuilder b)
        {
            float prevY = bottom;
            for (int i = 0; i < strips.Count; i++)
            {
                Strip s = strips[i];
                float y = top + s.lift;
                b.Quad(s.submesh, new Vector3(fromX, y, s.zFrom), new Vector3(fromX, y, s.zTo), new Vector3(toX, y, s.zTo), new Vector3(toX, y, s.zFrom),
                    Vector3.up, s.color);
                if (y > prevY + 0.0001f)
                {
                    // A step up toward the back faces the camera (the slab front, kerb faces).
                    int sub = i == 0 ? sideSubmesh : s.submesh;
                    Color c = i == 0 ? sideColor : Color.Lerp(s.color, Color.black, 0.08f);
                    b.Quad(sub, new Vector3(fromX, prevY, s.zFrom), new Vector3(fromX, y, s.zFrom), new Vector3(toX, y, s.zFrom), new Vector3(toX, prevY, s.zFrom),
                        Vector3.back, c);
                }
                if (closeLeft)
                    b.Quad(sideSubmesh, new Vector3(fromX, bottom, s.zTo), new Vector3(fromX, y, s.zTo), new Vector3(fromX, y, s.zFrom), new Vector3(fromX, bottom, s.zFrom),
                        Vector3.left, sideColor);
                if (closeRight)
                    b.Quad(sideSubmesh, new Vector3(toX, bottom, s.zFrom), new Vector3(toX, y, s.zFrom), new Vector3(toX, y, s.zTo), new Vector3(toX, bottom, s.zTo),
                        Vector3.right, sideColor);
                prevY = y;
            }
        }
    }
}
