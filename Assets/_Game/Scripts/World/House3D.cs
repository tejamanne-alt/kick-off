using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A building: a box of walls with its street face textured (windows, door, shopfront)
    /// and a roof. The origin is on the ground at the middle of the street face; the
    /// building extends back (+z) by <see cref="depth"/>.
    /// Submeshes: 0 walls (sides and back, tinted), 1 street facade (textured), 2 roof.
    /// </summary>
    public class House3D : ProceduralShape
    {
        public enum RoofStyle { GableToStreet, GableSideways, Flat, Shed }

        public float width = 7f;
        public float depth = 7f;
        public float wallHeight = 6f;
        public float roofHeight = 2.4f;
        public float eave = 0.45f;
        public RoofStyle roof = RoofStyle.GableToStreet;
        public Color wallColor = new Color(0.95f, 0.94f, 0.9f);
        public Color roofColor = new Color(0.32f, 0.35f, 0.42f);
        public Color trimColor = new Color(0.93f, 0.93f, 0.9f);

        protected override int SubmeshCount { get { return 3; } }

        protected override void Build(MeshBuilder b)
        {
            float hw = width * 0.5f;
            // Walls: sides and back tinted; the street face carries the facade texture (submesh 1).
            b.Box(0, new Vector3(-hw, 0f, 0f), new Vector3(hw, wallHeight, depth), wallColor, MeshBuilder.Faces.NoBottom & ~MeshBuilder.Faces.Top, 1);

            float t = 0.16f;   // roof thickness, shown as a fascia board
            switch (roof)
            {
                case RoofStyle.GableToStreet:
                {
                    float ridgeY = wallHeight + roofHeight, ex = hw + eave;
                    float eaveY = wallHeight - eave * roofHeight / hw;
                    float z0 = -eave, z1 = depth + eave;
                    // Gable ends
                    b.Triangle(0, new Vector3(-hw, wallHeight, 0f), new Vector3(0f, ridgeY, 0f), new Vector3(hw, wallHeight, 0f), Vector3.back, wallColor, Vector2.zero, Vector2.up, Vector2.one);
                    b.Triangle(0, new Vector3(-hw, wallHeight, depth), new Vector3(0f, ridgeY, depth), new Vector3(hw, wallHeight, depth), Vector3.forward, wallColor, Vector2.zero, Vector2.up, Vector2.one);
                    foreach (float side in new[] { -1f, 1f })
                    {
                        Vector3 eaveFront = new Vector3(side * ex, eaveY, z0), ridgeFront = new Vector3(0f, ridgeY, z0);
                        Vector3 eaveBack = new Vector3(side * ex, eaveY, z1), ridgeBack = new Vector3(0f, ridgeY, z1);
                        Vector3 outward = new Vector3(side * roofHeight, hw, 0f);
                        b.Quad(2, eaveFront, ridgeFront, ridgeBack, eaveBack, outward, roofColor);
                        // Fascia boards along the gable, white like the reference streets.
                        b.Quad(0, eaveFront + Vector3.down * t, eaveFront, ridgeFront, ridgeFront + Vector3.down * t, Vector3.back, trimColor);
                        b.Quad(0, eaveFront + Vector3.down * t, eaveBack + Vector3.down * t, eaveBack, eaveFront, new Vector3(side, 0f, 0f), trimColor);
                    }
                    break;
                }
                case RoofStyle.GableSideways:
                {
                    float ridgeY = wallHeight + roofHeight, hd = depth * 0.5f;
                    float eaveY = wallHeight - eave * roofHeight / hd;
                    float x0 = -hw - eave, x1 = hw + eave;
                    // Gable ends on the sides
                    b.Triangle(0, new Vector3(-hw, wallHeight, 0f), new Vector3(-hw, ridgeY, hd), new Vector3(-hw, wallHeight, depth), Vector3.left, wallColor, Vector2.zero, Vector2.up, Vector2.one);
                    b.Triangle(0, new Vector3(hw, wallHeight, 0f), new Vector3(hw, ridgeY, hd), new Vector3(hw, wallHeight, depth), Vector3.right, wallColor, Vector2.zero, Vector2.up, Vector2.one);
                    Vector3 fl = new Vector3(x0, eaveY, -eave), fr = new Vector3(x1, eaveY, -eave);
                    Vector3 rl = new Vector3(x0, ridgeY, hd), rr = new Vector3(x1, ridgeY, hd);
                    Vector3 bl = new Vector3(x0, eaveY, depth + eave), br = new Vector3(x1, eaveY, depth + eave);
                    b.Quad(2, fl, rl, rr, fr, new Vector3(0f, hd, -roofHeight), roofColor);
                    b.Quad(2, br, rr, rl, bl, new Vector3(0f, hd, roofHeight), roofColor);
                    b.Quad(0, fl + Vector3.down * t, fl, fr, fr + Vector3.down * t, Vector3.back, Color.Lerp(roofColor, Color.black, 0.2f));
                    break;
                }
                case RoofStyle.Shed:
                {
                    // Low at the street, rising to the back.
                    float backY = wallHeight + roofHeight;
                    b.Triangle(0, new Vector3(-hw, wallHeight, 0f), new Vector3(-hw, backY, depth), new Vector3(-hw, wallHeight, depth), Vector3.left, wallColor, Vector2.zero, Vector2.up, Vector2.one);
                    b.Triangle(0, new Vector3(hw, wallHeight, 0f), new Vector3(hw, backY, depth), new Vector3(hw, wallHeight, depth), Vector3.right, wallColor, Vector2.zero, Vector2.up, Vector2.one);
                    b.Box(0, new Vector3(-hw, wallHeight, depth - 0.01f), new Vector3(hw, backY, depth), wallColor, MeshBuilder.Faces.Back);
                    Vector3 f0 = new Vector3(-hw - eave, wallHeight - 0.1f, -eave), f1 = new Vector3(hw + eave, wallHeight - 0.1f, -eave);
                    Vector3 b0 = new Vector3(-hw - eave, backY, depth + 0.1f), b1 = new Vector3(hw + eave, backY, depth + 0.1f);
                    b.Quad(2, f0, b0, b1, f1, new Vector3(0f, depth, -roofHeight), roofColor);
                    b.Quad(0, f0 + Vector3.down * t, f0, f1, f1 + Vector3.down * t, Vector3.back, Color.Lerp(roofColor, Color.black, 0.2f));
                    break;
                }
                default:
                {
                    // Flat roof with a parapet.
                    b.Box(2, new Vector3(-hw - 0.08f, wallHeight, -0.08f), new Vector3(hw + 0.08f, wallHeight + 0.35f, depth + 0.08f), roofColor);
                    break;
                }
            }
        }
    }
}
