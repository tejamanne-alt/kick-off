using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// What the raised platforms and the ramps look like (their colliders are the layout's, unchanged): they were a plain box in the
    /// chapter's colour, a tilted slab floating over the ground, and read as placeholders ("what are those brown blocks?",
    /// docs/LEARNINGS.md E16). Now a platform is a retaining wall with its coping: in a park a raised lawn bed with shrubs along its
    /// back (stone in Kamakura, coral keystone in Miami), in a street a stone or block terrace with a paved top, on a building site
    /// concrete with a safety-yellow edge. A ramp is a solid wedge of the same wall under its paved or grassy slope.
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            enum Setting { Park, Site, Street }

            Setting PlaceSetting { get { return Chapter == 5 ? Setting.Park : Chapter == 4 ? Setting.Site : Setting.Street; } }

            /// <summary>The wall's colour: Kamakura's grey granite, Miami's coral keystone, a site's concrete, the town's sandstone.</summary>
            Color WallColor(Setting s)
            {
                if (MiamiLook) return new Color(0.93f, 0.87f, 0.74f);
                if (s == Setting.Site) return new Color(0.78f, 0.78f, 0.76f);
                if (StreetBuilder.KM) return new Color(0.72f, 0.72f, 0.7f);
                return new Color(0.84f, 0.8f, 0.72f);
            }

            Material WallMaterial(Setting s)
            {
                return Art.surfaces[s == Setting.Site ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.BlockWall];
            }

            /// <summary>The look of a raised platform from <paramref name="fromX"/> to <paramref name="toX"/>, its top at <paramref name="top"/>.</summary>
            void DressPlatform(float fromX, float toX, float top, float groundTop)
            {
                float w = toX - fromX, h = top - groundTop, cx = (fromX + toX) * 0.5f;
                if (w <= 0.05f || h <= 0.05f) return;
                const float depth = 1.6f;
                var s = PlaceSetting;
                var t = new GameObject("PlatformLook").transform;
                t.SetParent(root, false);
                float cap = Mathf.Clamp(h * 0.18f, 0.08f, 0.16f);
                Color wall = WallColor(s);
                // The wall, its coping a hair proud of it (the edge the kid stands on), and the top's surface.
                StreetBuilder.Solid(t, "RetainingWall", new Vector3(cx, groundTop + (h - cap) * 0.5f, 0f), new Vector3(w, h - cap, depth), wall, WallMaterial(s));
                StreetBuilder.Solid(t, "Coping", new Vector3(cx, top - cap * 0.5f, 0f), new Vector3(w + 0.08f, cap, depth + 0.08f),
                    Color.Lerp(wall, Color.white, 0.25f), Art.surfaces[ProceduralArt.Surface.Kerb]);
                var topSurface = s == Setting.Park ? ProceduralArt.Surface.Grass : s == Setting.Site ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.Paving;
                var lid = StreetBuilder.Solid(t, "Top", new Vector3(cx, top + 0.006f, 0.04f), new Vector3(Mathf.Max(0.05f, w - 0.18f), 0.012f, depth - 0.2f),
                    Color.white, Art.surfaces[topSurface]);
                lid.faces = MeshBuilder.Faces.Top;
                lid.Rebuild();
                if (s == Setting.Site)
                {
                    // A painted safety edge along the front of the top.
                    StreetBuilder.Solid(t, "SafetyEdge", new Vector3(cx, top + 0.008f, -depth * 0.5f + 0.06f), new Vector3(w, 0.014f, 0.1f), new Color(0.98f, 0.8f, 0.15f));
                }
                if (s == Setting.Park && w >= 1.2f)
                {
                    // Shrubs along the back of the bed (behind the kid's lane), small enough to stand clear of the coins above.
                    string shrub = StreetBuilder.KM && HasKitModel("Plants", "Azalea") ? "Azalea"
                        : MiamiLook && HasKitModel("Plants", "SawPalmetto") ? "SawPalmetto" : "ShrubFlowering";
                    int n = Mathf.Max(1, Mathf.FloorToInt(w / 1.4f));
                    for (int i = 0; i < n; i++)
                    {
                        float x = fromX + (i + 0.5f) * w / n;
                        KitModel(t, "Plants", shrub, new Vector3(x, top, 0.52f), (x * 47f) % 360f, 0.34f);
                    }
                }
            }

            /// <summary>The look of a ramp from <paramref name="a"/> to <paramref name="b"/> (a.x &lt; b.x): a wedge down to the ground.</summary>
            void DressRamp(Vector2 a, Vector2 b)
            {
                float bottom, g;
                bottom = Mathf.Min(a.y, b.y);
                if (GroundTopAt((a.x + b.x) * 0.5f, out g) && g < bottom) bottom = g;
                if (Mathf.Abs(b.y - a.y) < 0.02f && Mathf.Abs(a.y - bottom) < 0.02f) return;
                const float half = 0.8f;
                var s = PlaceSetting;
                var t = new GameObject("RampLook");
                t.transform.SetParent(root, false);
                var body = t.AddComponent<PatchShape>();
                Color wall = WallColor(s);
                // The front face (what the camera sees), and the ends.
                body.AddQuad(new Vector3(a.x, bottom, -half), new Vector3(b.x, bottom, -half), new Vector3(b.x, b.y, -half), new Vector3(a.x, a.y, -half), wall);
                if (a.y - bottom > 0.02f)
                    body.AddQuad(new Vector3(a.x, bottom, -half), new Vector3(a.x, a.y, -half), new Vector3(a.x, a.y, half), new Vector3(a.x, bottom, half), wall);
                if (b.y - bottom > 0.02f)
                    body.AddQuad(new Vector3(b.x, bottom, -half), new Vector3(b.x, b.y, -half), new Vector3(b.x, b.y, half), new Vector3(b.x, bottom, half), wall);
                t.GetComponent<MeshRenderer>().sharedMaterial = WallMaterial(s);
                body.Rebuild();

                var slopeGo = new GameObject("RampTop");
                slopeGo.transform.SetParent(t.transform, false);
                var slope = slopeGo.AddComponent<PatchShape>();
                var top = s == Setting.Park ? ProceduralArt.Surface.Grass : s == Setting.Site ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.Paving;
                slope.AddQuad(new Vector3(a.x, a.y + 0.005f, -half), new Vector3(b.x, b.y + 0.005f, -half), new Vector3(b.x, b.y + 0.005f, half), new Vector3(a.x, a.y + 0.005f, half), Color.white);
                slopeGo.GetComponent<MeshRenderer>().sharedMaterial = Art.surfaces[top];
                slope.Rebuild();
            }
        }
    }
}
