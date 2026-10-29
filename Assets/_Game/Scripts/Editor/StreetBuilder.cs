using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Builds the 3D street around the 2D gameplay plane (z = 0): ground slabs with the
    /// footpath, kerbs and the road, side streets at crossings, and the scenery along the
    /// street for each chapter. Scale: about 0.9 m per unit.
    ///
    /// Depth layout (z grows away from the camera):
    ///   z &lt; -8.1        near pavement, below the bottom of the screen
    ///   -8.1 .. -1.7    the road (two lanes), in the foreground
    ///   -1.7 .. -1.5    kerb
    ///   -1.5 .. 1.5     the footpath the kid runs along (gameplay at z = 0)
    ///   1.5 .. 1.85     the rest of the footpath, with utility poles
    ///   z &gt; 1.85       property walls, houses, shops, trees; the sea on the beach
    ///
    /// The road and everything behind the footpath run unbroken; gaps in the gameplay
    /// ground only open holes in the footpath lane (drain works, flooded trenches).
    /// </summary>
    public static class StreetBuilder
    {
        public const float FrontZ = -16f;
        /// <summary>Half the width of the footpath lane the kid runs in.</summary>
        public const float PathHalf = 1.5f;
        /// <summary>Road edges: nearer the kid, and nearer the camera.</summary>
        public const float RoadNear = -1.7f, RoadFar = -8.1f;
        public const float PropertyZ = 1.85f;
        public const float PoleZ = 1.55f;
        /// <summary>Kid-lane half depth: decor nearer z = 0 than this would be walked through.</summary>
        public const float LaneClear = 0.5f;
        /// <summary>How far back the ground runs behind the street (under the houses and beyond).</summary>
        public const float BackZ = 90f;

        struct StripSpec
        {
            public float zFrom, zTo, lift;
            public ProceduralArt.Surface surface;
            public Color tint;
            public StripSpec(float zFrom, float zTo, float lift, ProceduralArt.Surface surface, Color tint)
            {
                this.zFrom = zFrom; this.zTo = zTo; this.lift = lift; this.surface = surface; this.tint = tint;
            }
        }

        static ArtBaker.ArtSet Art { get { return LevelBuildKit.Art; } }

        /// <summary>Which part of the street a strip belongs to (see <see cref="Slab"/>).</summary>
        public enum Part { Front, Lane, Back }

        static Part PartOf(StripSpec s)
        {
            if (s.zTo <= -PathHalf + 0.001f) return Part.Front;
            if (s.zFrom >= PathHalf - 0.001f) return Part.Back;
            return Part.Lane;
        }

        static List<StripSpec> StripsFor(int chapter)
        {
            var white = Color.white;
            var s = new List<StripSpec>();
            switch (chapter)
            {
                case 2:   // market: a cobbled lane in front of the paved shop fronts
                    s.Add(new StripSpec(FrontZ, -PathHalf, -0.06f, ProceduralArt.Surface.Cobbles, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Paving, new Color(1f, 0.97f, 0.92f)));
                    s.Add(new StripSpec(PathHalf, PropertyZ + 0.6f, 0f, ProceduralArt.Surface.Paving, new Color(1f, 0.97f, 0.92f)));
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0f, ProceduralArt.Surface.Paving, new Color(0.92f, 0.9f, 0.86f)));
                    break;
                case 3:   // beach: sand, a firmer trodden track, then wet sand at the water's edge
                    s.Add(new StripSpec(FrontZ, -PathHalf, 0f, ProceduralArt.Surface.Sand, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Sand, new Color(0.96f, 0.93f, 0.88f)));
                    s.Add(new StripSpec(PathHalf, 5.6f, 0f, ProceduralArt.Surface.Sand, white));
                    s.Add(new StripSpec(5.6f, 9f, -0.12f, ProceduralArt.Surface.Sand, new Color(0.82f, 0.74f, 0.62f)));
                    break;
                case 5:   // park: a gravel path between lawns
                    s.Add(new StripSpec(FrontZ, -PathHalf, 0.04f, ProceduralArt.Surface.Grass, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Gravel, white));
                    s.Add(new StripSpec(PathHalf, PropertyZ + 0.6f, 0.04f, ProceduralArt.Surface.Grass, white));
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0.04f, ProceduralArt.Surface.Grass, new Color(0.92f, 0.95f, 0.9f)));
                    break;
                default:  // home street (1) and city (4): footpath, kerb and a road in front
                {
                    var pave = chapter == 4 ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.Paving;
                    s.Add(new StripSpec(FrontZ, RoadFar - 0.2f, 0f, pave, white));
                    s.Add(new StripSpec(RoadFar - 0.2f, RoadFar, 0f, ProceduralArt.Surface.Kerb, white));
                    s.Add(new StripSpec(RoadFar, RoadNear, -0.14f, ProceduralArt.Surface.Asphalt, white));
                    s.Add(new StripSpec(RoadNear, -PathHalf, 0f, ProceduralArt.Surface.Kerb, white));
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, pave, white));
                    s.Add(new StripSpec(PathHalf, PropertyZ + 0.6f, 0f, pave, white));
                    // Driveways, yards and gardens behind the property line, under the houses.
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0f, ProceduralArt.Surface.Concrete, new Color(0.9f, 0.9f, 0.88f)));
                    break;
                }
            }
            return s;
        }

        static bool HasRoadLines(int chapter) { return chapter == 1 || chapter == 4; }

        static Color SideColor(int chapter)
        {
            switch (chapter)
            {
                case 3: return new Color(0.84f, 0.74f, 0.55f);
                case 5: return new Color(0.5f, 0.42f, 0.34f);
                default: return new Color(0.66f, 0.65f, 0.63f);
            }
        }

        // ---------------------------------------------------------------- ground

        /// <summary>
        /// One slab of one part of the street (in front of the footpath, the footpath lane, or
        /// behind it) from fromX to toX with its gameplay surface at <paramref name="top"/>.
        /// </summary>
        public static GameObject Slab(Transform parent, string name, float fromX, float toX, float top, bool closeLeft, bool closeRight, Part part)
        {
            int ch = LevelBuildKit.Chapter;
            var specs = StripsFor(ch).FindAll(spec => PartOf(spec) == part);
            var materials = new List<Material>();
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var slab = go.AddComponent<StreetSlab>();
            slab.fromX = fromX;
            slab.toX = toX;
            slab.top = top;
            slab.bottom = top - 14f;
            slab.closeLeft = closeLeft;
            slab.closeRight = closeRight;
            slab.sideColor = SideColor(ch);
            foreach (var spec in specs)
            {
                var m = Art.surfaces[spec.surface];
                int index = materials.IndexOf(m);
                if (index < 0) { index = materials.Count; materials.Add(m); }
                slab.strips.Add(new StreetSlab.Strip(spec.zFrom, spec.zTo, spec.lift, index, spec.tint));
            }
            materials.Add(Art.solid);
            slab.sideSubmesh = materials.Count - 1;
            slab.materials = materials.Count;
            go.GetComponent<MeshRenderer>().sharedMaterials = materials.ToArray();
            slab.Rebuild();

            if (HasRoadLines(ch) && part == Part.Front)
            {
                // White edge lines along the road, a dashed centre line, and the odd manhole.
                float road = top - 0.14f;
                Color paint = new Color(0.95f, 0.95f, 0.93f);
                foreach (float z in new[] { RoadNear - 0.3f, RoadFar + 0.3f })
                    Patch(go.transform, "EdgeLine", fromX + 0.1f, toX - 0.1f, road, z - 0.06f, z + 0.06f, paint);
                float mid = (RoadNear + RoadFar) * 0.5f;
                for (float x = Mathf.Ceil(fromX / 6f) * 6f; x + 3f < toX; x += 6f)
                    Patch(go.transform, "CentreDash", x, x + 3f, road, mid - 0.06f, mid + 0.06f, paint);
                for (float x = Mathf.Ceil(fromX / 37f) * 37f + 11f; x < toX - 1f; x += 37f)
                {
                    var cover = new GameObject("Manhole");
                    cover.transform.SetParent(go.transform, false);
                    cover.transform.position = new Vector3(x, road + 0.005f, mid - 1.6f);
                    var disc = cover.AddComponent<CylinderShape>();
                    disc.axis = Vector3.up;
                    disc.radius = 0.38f;
                    disc.length = 0.01f;
                    disc.sideColor = disc.endColor = new Color(0.36f, 0.36f, 0.38f);
                    disc.innerRadius = 0.3f;
                    disc.innerColor = new Color(0.42f, 0.42f, 0.44f);
                    cover.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    disc.Rebuild();
                }
            }
            return go;
        }

        /// <summary>A flat decal on the ground (paint, puddles, wet sand, grates).</summary>
        public static GameObject Patch(Transform parent, string name, float fromX, float toX, float top, float zFrom, float zTo, Color color, Material material = null, float lift = 0.012f)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3((fromX + toX) * 0.5f, top + lift * 0.5f, (zFrom + zTo) * 0.5f);
            var box = go.AddComponent<Box3D>();
            box.size = new Vector3(toX - fromX, lift, zTo - zFrom);
            box.color = color;
            box.faces = MeshBuilder.Faces.Top;
            go.GetComponent<MeshRenderer>().sharedMaterial = material != null ? material : Art.solid;
            box.Rebuild();
            return go;
        }

        /// <summary>A solid box in the street (obstacles, walls, posts), centred at <paramref name="center"/>.</summary>
        public static Box3D Solid(Transform parent, string name, Vector3 center, Vector3 size, Color color, Material material = null)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = center;
            var box = go.AddComponent<Box3D>();
            box.size = size;
            box.color = color;
            go.GetComponent<MeshRenderer>().sharedMaterial = material != null ? material : Art.solid;
            box.Rebuild();
            return box;
        }

        /// <summary>
        /// Where the footpath crosses a side street: a raised zebra crossing, and the side street
        /// running away from the camera with kerbs and a stop line. The main road in front runs on.
        /// </summary>
        public static void CrossingStreet(Transform parent, float fromX, float toX, float top)
        {
            int ch = LevelBuildKit.Chapter;
            var asphalt = Art.surfaces[ch == 2 ? ProceduralArt.Surface.Cobbles : ProceduralArt.Surface.Asphalt];
            var kerb = Art.surfaces[ProceduralArt.Surface.Kerb];
            var root = new GameObject("SideStreet").transform;
            root.SetParent(parent, false);

            // Road surface from the footpath to far up the side street (the main road in front runs on).
            var surface = new GameObject("Road");
            surface.transform.SetParent(root, false);
            var slab = surface.AddComponent<StreetSlab>();
            slab.fromX = fromX; slab.toX = toX; slab.top = top; slab.bottom = top - 14f;
            slab.closeLeft = slab.closeRight = true;
            slab.materials = 3;
            slab.sideColor = SideColor(ch);
            slab.sideSubmesh = 2;
            // A raised crossing: the side street meets the footpath at footpath height.
            slab.strips.Add(new StreetSlab.Strip(-PathHalf, 70f, 0f, 0, Color.white));
            surface.GetComponent<MeshRenderer>().sharedMaterials = new[] { asphalt, kerb, Art.solid };
            slab.Rebuild();

            // Kerbs along the side street, behind the main street.
            foreach (float x in new[] { fromX + 0.1f, toX - 0.1f })
                Solid(root, "SideKerb", new Vector3(x, top + 0.08f, (PathHalf + 70f) * 0.5f), new Vector3(0.22f, 0.16f, 70f - PathHalf), Color.white, kerb);

            // Zebra stripes where the footpath crosses, a stop line and centre dashes up the side street.
            for (float x = fromX + 0.45f; x < toX - 0.3f; x += 0.95f)
                Patch(root, "Zebra", x, x + 0.5f, top, -PathHalf + 0.1f, PathHalf - 0.1f, new Color(0.95f, 0.95f, 0.93f));
            Patch(root, "StopLine", fromX + 0.3f, (fromX + toX) * 0.5f, top, PathHalf + 1f, PathHalf + 1.25f, new Color(0.95f, 0.95f, 0.93f));
            for (float z = PathHalf + 3f; z < 70f; z += 4f)
                Patch(root, "CentreDash", (fromX + toX) * 0.5f - 0.06f, (fromX + toX) * 0.5f + 0.06f, top, z, z + 2f, new Color(0.95f, 0.85f, 0.4f));
        }

        // ---------------------------------------------------------------- scenery

        /// <summary>Surface height at x (the highest ground span covering it, else the nearest one).</summary>
        static float GroundAt(LevelBuildKit.TrackBuilder track, float x)
        {
            float best = float.MinValue, nearestTop = 0f, nearest = float.MaxValue;
            foreach (var span in track.GroundSpans)
            {
                if (x >= span.x && x <= span.y) best = Mathf.Max(best, span.z);
                float d = x < span.x ? span.x - x : x > span.y ? x - span.y : 0f;
                if (d < nearest) { nearest = d; nearestTop = span.z; }
            }
            return best > float.MinValue ? best : nearestTop;
        }

        /// <summary>Does [a, b] overlap a side street or the school grounds (where the street's scenery must stay out)?</summary>
        static bool Blocked(LevelBuildKit.TrackBuilder track, float a, float b, out float skipTo)
        {
            foreach (var area in track.OpenAreas.Concat(track.QuietAreas))
            {
                if (b > area.x - 0.6f && a < area.y + 0.6f)
                {
                    skipTo = area.y + 0.8f;
                    return true;
                }
            }
            skipTo = a;
            return false;
        }

        /// <summary>Would a building of this facade, centred on x, stand on a side street (they run
        /// far back from the footpath) or in the school grounds?</summary>
        static bool OnSideStreet(LevelBuildKit.TrackBuilder track, float x, ProceduralArt.FacadeKind facade)
        {
            float half = ProceduralArt.FacadeSize(facade).x * 0.5f + 0.3f, skip;
            return Blocked(track, x - half, x + half, out skip);
        }

        static float Rand(System.Random rng, float min, float max) { return min + (float)rng.NextDouble() * (max - min); }

        /// <summary>A cut-out (tree, bush, prop) standing on the ground at (x, ground, z), with distance haze.</summary>
        static SpriteRenderer CutOut(Transform parent, string name, Sprite sprite, float x, float groundY, float z, float scale, int order, bool flip = false)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sharedMaterial = Art.hazeSprite;
            sr.sortingOrder = order;
            sr.flipX = flip;
            go.transform.localScale = Vector3.one * scale;
            go.transform.position = new Vector3(x, groundY + sprite.bounds.size.y * 0.5f * scale - 0.15f * scale, z);
            if (z < 300f && sprite != Art.headland)
            {
                // A soft shadow on the ground under the cut-out, so it stands in the street rather than floating.
                var shadow = new GameObject(name + "Shadow");
                shadow.transform.SetParent(parent, false);
                var ssr = shadow.AddComponent<SpriteRenderer>();
                ssr.sprite = Art.shadow;
                ssr.sharedMaterial = Art.hazeSprite;
                ssr.color = new Color(0.1f, 0.12f, 0.2f, 0.35f);
                ssr.sortingOrder = order - 1;
                float w = sprite.bounds.size.x * scale * 0.55f;
                shadow.transform.position = new Vector3(x + w * 0.15f, groundY + 0.02f, z + 0.1f);
                shadow.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
                shadow.transform.localScale = new Vector3(w / Art.shadow.bounds.size.x, Mathf.Min(w, 3f) / Art.shadow.bounds.size.y, 1f);
            }
            return sr;
        }

        /// <summary>A darker band on the ground at the foot of something solid (fake ambient occlusion).</summary>
        static void ContactShadow(Transform parent, float a, float b, float groundY, float zFrom, float zTo)
        {
            if (b - a < 0.1f) return;
            Patch(parent, "ContactShadow", a, b, groundY, zFrom, zTo, new Color(0.62f, 0.64f, 0.72f), SurfaceUnder(), 0.004f);
        }

        /// <summary>The ground material on the back pavement / lots, for shadows that keep its texture.</summary>
        static Material SurfaceUnder()
        {
            switch (LevelBuildKit.Chapter)
            {
                case 2: return Art.surfaces[ProceduralArt.Surface.Paving];
                case 3: return Art.surfaces[ProceduralArt.Surface.Sand];
                case 5: return Art.surfaces[ProceduralArt.Surface.Grass];
                default: return Art.surfaces[ProceduralArt.Surface.Concrete];
            }
        }

        static House3D Building(Transform parent, float x, float groundY, float z, ProceduralArt.FacadeKind facade, House3D.RoofStyle roof,
            float depth, float roofHeight, Color wall, Color roofColor)
        {
            Vector2 size = ProceduralArt.FacadeSize(facade);
            var go = new GameObject("Building_" + facade);
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3(x, groundY, z);
            var house = go.AddComponent<House3D>();
            house.width = size.x;
            house.wallHeight = size.y;
            house.depth = depth;
            house.roof = roof;
            house.roofHeight = roofHeight;
            house.wallColor = wall;
            house.roofColor = roofColor;
            go.GetComponent<MeshRenderer>().sharedMaterials = new[] { Art.solid, Art.facades[facade], Art.surfaces[ProceduralArt.Surface.RoofTiles] };
            house.Rebuild();
            ContactShadow(parent, x - size.x * 0.5f, x + size.x * 0.5f, groundY, z - 0.45f, z);
            Dress(parent, x - size.x * 0.5f, groundY, z, facade, Mathf.Abs(Mathf.RoundToInt(x * 7f + z * 13f)));
            return house;
        }

        // ---------------------------------------------------------------- facade dressing

        static readonly Color SillColor = new Color(0.9f, 0.89f, 0.85f);
        static readonly Color[] Petals =
        {
            new Color(0.98f, 0.5f, 0.6f), new Color(0.95f, 0.3f, 0.32f), new Color(1f, 0.82f, 0.3f),
            new Color(0.97f, 0.96f, 0.94f), new Color(0.72f, 0.5f, 0.9f),
        };

        /// <summary>
        /// Real depth on a painted building front, lined up with the windows and doors painted on
        /// its facade (see ProceduralArt.Facade; facade units are world units from the bottom-left
        /// corner): sills and lintels, window boxes of flowers, a door canopy with a lamp and pots,
        /// a downpipe, and balconies with railings (and the odd plant or towel) on the flats.
        /// </summary>
        static void Dress(Transform parent, float left, float gy, float z, ProceduralArt.FacadeKind facade, int seed)
        {
            var rng = new System.Random(seed);
            System.Action<float, float, float, float, bool> window = (x0, y0, x1, y1, flowers) =>
            {
                float cx = left + (x0 + x1) * 0.5f, w = x1 - x0;
                Solid(parent, "Sill", new Vector3(cx, gy + y0 - 0.05f, z - 0.09f), new Vector3(w + 0.24f, 0.08f, 0.2f), SillColor);
                Solid(parent, "Lintel", new Vector3(cx, gy + y1 + 0.05f, z - 0.04f), new Vector3(w + 0.2f, 0.1f, 0.09f), SillColor);
                if (flowers) FlowerBox(parent, cx, gy + y0 - 0.01f, z - 0.2f, w - 0.1f, rng);
            };
            System.Action<float, float, float> door = (x0, width, height) =>
            {
                float cx = left + x0 + width * 0.5f;
                Solid(parent, "DoorCanopy", new Vector3(cx, gy + height + 0.22f, z - 0.32f), new Vector3(width + 0.5f, 0.08f, 0.62f), new Color(0.42f, 0.44f, 0.5f));
                Solid(parent, "DoorStep", new Vector3(cx, gy + 0.06f, z - 0.22f), new Vector3(width + 0.3f, 0.12f, 0.42f), new Color(0.78f, 0.77f, 0.74f));
                Solid(parent, "Lamp", new Vector3(cx + width * 0.5f + 0.32f, gy + height - 0.1f, z - 0.08f), new Vector3(0.16f, 0.24f, 0.14f), new Color(1f, 0.88f, 0.6f));
                Pot(parent, cx - width * 0.5f - 0.35f, gy, z - 0.32f, rng);
            };
            System.Action<float, float> downpipe = (x, top) =>
            {
                var go = new GameObject("Downpipe");
                go.transform.SetParent(parent, false);
                go.transform.position = new Vector3(left + x, gy + top * 0.5f, z - 0.07f);
                var pipe = go.AddComponent<CylinderShape>();
                pipe.axis = Vector3.up;
                pipe.radius = 0.055f;
                pipe.length = top;
                pipe.segments = 10;
                pipe.sideColor = new Color(0.62f, 0.64f, 0.66f);
                pipe.endColor = pipe.sideColor;
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                pipe.Rebuild();
            };

            switch (facade)
            {
                case ProceduralArt.FacadeKind.HouseGable:
                    window(0.8f, 3.7f, 2.9f, 5f, true);
                    window(3.8f, 3.7f, 6.3f, 5f, true);
                    window(3.9f, 1f, 6.3f, 2.3f, rng.NextDouble() < 0.5);
                    door(0.5f, 1.2f, 2.2f);
                    downpipe(6.9f, 5.9f);
                    break;
                case ProceduralArt.FacadeKind.HouseLong:
                    for (int i = 0; i < 3; i++) window(0.8f + i * 3.1f, 3.5f, 2.9f + i * 3.1f, 4.8f, i != 1);
                    window(5.6f, 0.9f, 9.2f, 2.3f, true);
                    door(1f, 1.4f, 2.2f);
                    downpipe(9.9f, 5.5f);
                    break;
                case ProceduralArt.FacadeKind.Bungalow:
                    window(1f, 1.2f, 1.9f, 2.8f, true);
                    door(3.6f, 1.1f, 2.2f);
                    Pot(parent, left + 5.7f, gy, z - 0.35f, rng);
                    break;
                case ProceduralArt.FacadeKind.Shop0:
                case ProceduralArt.FacadeKind.Shop1:
                    for (int i = 0; i < 3; i++) window(0.8f + i * 2.5f, 5f, 2.4f + i * 2.5f, 6.3f, true);
                    downpipe(7.92f, 7.3f);
                    break;
                case ProceduralArt.FacadeKind.Apartment:
                    for (int floor = 0; floor < 5; floor++)
                    {
                        float y = 0.6f + floor * 2.7f;
                        if (floor == 0)
                        {
                            for (int i = 0; i < 3; i++) window(1f + i * 3.8f, y, 3.4f + i * 3.8f, y + 1.5f, false);
                            continue;
                        }
                        Balcony(parent, left, gy + y - 0.18f, z, 12f, rng);
                    }
                    downpipe(11.92f, 13.9f);
                    break;
                case ProceduralArt.FacadeKind.Warehouse:
                    window(8.8f, 2.6f, 10.2f, 3.6f, false);
                    Solid(parent, "Lamp", new Vector3(left + 8f, gy + 2.6f, z - 0.1f), new Vector3(0.3f, 0.12f, 0.24f), new Color(1f, 0.88f, 0.6f));
                    break;
            }
        }

        /// <summary>A painted window box with a row of soft flower clumps along its top.</summary>
        static void FlowerBox(Transform parent, float cx, float y, float z, float width, System.Random rng)
        {
            Color[] boxes = { new Color(0.72f, 0.42f, 0.3f), new Color(0.35f, 0.5f, 0.42f), new Color(0.92f, 0.9f, 0.84f) };
            Solid(parent, "FlowerBox", new Vector3(cx, y + 0.11f, z), new Vector3(width, 0.22f, 0.26f), boxes[rng.Next(boxes.Length)]);
            Color petal = Petals[rng.Next(Petals.Length)], petal2 = Petals[rng.Next(Petals.Length)];
            var blobs = new List<BlobShape.Blob>();
            for (float dx = -width * 0.5f + 0.14f; dx <= width * 0.5f - 0.12f; dx += 0.24f)
            {
                blobs.Add(new BlobShape.Blob(new Vector3(dx, 0.27f, 0f), new Vector3(0.15f, 0.09f, 0.12f), new Color(0.36f, 0.58f, 0.32f)));
                blobs.Add(new BlobShape.Blob(new Vector3(dx + 0.04f, 0.34f, -0.04f), new Vector3(0.07f, 0.05f, 0.06f), rng.NextDouble() < 0.6 ? petal : petal2));
            }
            Blobs(parent, "Flowers", new Vector3(cx, y, z), blobs);
        }

        /// <summary>A terracotta pot with a round, leafy plant.</summary>
        static void Pot(Transform parent, float x, float gy, float z, System.Random rng)
        {
            var go = new GameObject("Pot");
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3(x, gy + 0.2f, z);
            var pot = go.AddComponent<CylinderShape>();
            pot.axis = Vector3.up;
            pot.radius = 0.2f;
            pot.length = 0.4f;
            pot.segments = 14;
            pot.sideColor = new Color(0.76f, 0.44f, 0.32f);
            pot.endColor = new Color(0.4f, 0.3f, 0.22f);
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            pot.Rebuild();
            Color leaf = rng.NextDouble() < 0.5 ? new Color(0.36f, 0.58f, 0.32f) : new Color(0.3f, 0.5f, 0.3f);
            var blobs = new List<BlobShape.Blob>
            {
                new BlobShape.Blob(new Vector3(0f, 0.55f, 0f), new Vector3(0.3f, 0.32f, 0.28f), leaf),
                new BlobShape.Blob(new Vector3(0.12f, 0.75f, -0.05f), new Vector3(0.18f, 0.18f, 0.16f), Color.Lerp(leaf, Color.white, 0.15f)),
            };
            if (rng.NextDouble() < 0.5)
                blobs.Add(new BlobShape.Blob(new Vector3(-0.1f, 0.8f, -0.12f), new Vector3(0.07f, 0.06f, 0.06f), Petals[rng.Next(Petals.Length)]));
            Blobs(parent, "Plant", new Vector3(x, gy, z), blobs);
        }

        /// <summary>A balcony across a block of flats: a slab, a rail with balusters, and now and then a plant or a towel over the rail.</summary>
        static void Balcony(Transform parent, float left, float y, float z, float width, System.Random rng)
        {
            Color rail = new Color(0.7f, 0.71f, 0.74f);
            float cx = left + width * 0.5f;
            Solid(parent, "BalconySlab", new Vector3(cx, y, z - 0.42f), new Vector3(width + 0.1f, 0.14f, 0.84f), new Color(0.86f, 0.85f, 0.83f));
            Solid(parent, "BalconyRail", new Vector3(cx, y + 0.95f, z - 0.82f), new Vector3(width + 0.1f, 0.06f, 0.06f), rail);
            for (float bx = left + 0.1f; bx <= left + width - 0.05f; bx += 0.36f)
                Solid(parent, "Baluster", new Vector3(bx, y + 0.5f, z - 0.82f), new Vector3(0.035f, 0.88f, 0.035f), rail);
            for (int i = 0; i < 3; i++)
            {
                float bx = left + 2.2f + i * 3.8f;
                double r = rng.NextDouble();
                if (r < 0.3) Pot(parent, bx, y + 0.07f, z - 0.45f, rng);
                else if (r < 0.5)
                {
                    Color[] towels = { new Color(0.95f, 0.6f, 0.55f), new Color(0.55f, 0.75f, 0.9f), new Color(0.98f, 0.9f, 0.55f) };
                    Solid(parent, "Towel", new Vector3(bx, y + 0.72f, z - 0.86f), new Vector3(0.8f, 0.5f, 0.03f), towels[rng.Next(towels.Length)]);
                }
            }
        }

        static void Blobs(Transform parent, string name, Vector3 position, List<BlobShape.Blob> blobs)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            var shape = go.AddComponent<BlobShape>();
            shape.blobs = blobs;
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            shape.Rebuild();
        }

        /// <summary>Everything beside the street for the current chapter, from well before the start to well past the end.</summary>
        public static void Scenery(LevelBuildKit.TrackBuilder track, Transform root)
        {
            int ch = LevelBuildKit.Chapter;
            var rng = new System.Random(ch * 131 + Mathf.RoundToInt(track.MaxX));
            float x0 = track.MinX - 50f, x1 = track.MaxX + 50f;

            switch (ch)
            {
                case 2: Market(track, root, rng, x0, x1); break;
                case 3: Beach(track, root, rng, x0, x1); break;
                case 4: City(track, root, rng, x0, x1); break;
                case 5: Park(track, root, rng, x0, x1); break;
                default: Suburb(track, root, rng, x0, x1); break;
            }
            if (ch != 3) Poles(track, root, x0, x1);
        }

        static void Poles(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            if (LevelBuildKit.Chapter == 5) return;   // no overhead lines in the park
            var go = new GameObject("PoleLine");
            go.transform.SetParent(root, false);
            var line = go.AddComponent<PoleLine3D>();
            line.wireMaterial = Art.wire;
            for (float x = x0; x < x1; x += 21f)
            {
                float skip;
                if (Blocked(track, x - 0.5f, x + 0.5f, out skip)) continue;
                line.poles.Add(new Vector3(x, GroundAt(track, x), PoleZ));
            }
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            line.Rebuild();
        }

        static void Suburb(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            var wallMat = Art.surfaces[ProceduralArt.Surface.BlockWall];
            Color roofDark = new Color(0.34f, 0.37f, 0.44f), roofRed = new Color(0.7f, 0.36f, 0.3f);
            for (float x = x0; x < x1;)
            {
                float lot = Rand(rng, 9f, 13f), skip;
                if (Blocked(track, x, x + lot, out skip)) { x = skip; continue; }
                float cx = x + lot * 0.5f, gy = GroundAt(track, cx);

                // Block wall along the front of the lot with a gap for the gate.
                float gate = Rand(rng, x + 2f, x + lot - 4f);
                BlockWall(root, x + 0.1f, gate, gy, wallMat);
                BlockWall(root, gate + 2.2f, x + lot - 0.1f, gy, wallMat);

                int kind = rng.Next(3);
                float z = PropertyZ + 1.6f + Rand(rng, 0f, 1.4f);
                Color roof = rng.NextDouble() < 0.75 ? roofDark : roofRed;
                if (kind == 0) Building(root, cx, gy, z, ProceduralArt.FacadeKind.HouseGable, House3D.RoofStyle.GableToStreet, 7f, 2.6f, new Color(0.95f, 0.94f, 0.9f), roof);
                else if (kind == 1 && lot >= 11f) Building(root, cx, gy, z, ProceduralArt.FacadeKind.HouseLong, House3D.RoofStyle.GableSideways, 7f, 2.4f, new Color(0.93f, 0.91f, 0.86f), roof);
                else Building(root, cx, gy, z, ProceduralArt.FacadeKind.Bungalow, House3D.RoofStyle.Shed, 5.5f, 1f, new Color(0.88f, 0.89f, 0.9f), roofDark);

                // Garden trees behind the wall, and the odd big tree further back.
                if (rng.NextDouble() < 0.6)
                {
                    bool pine = rng.NextDouble() < 0.4;
                    CutOut(root, pine ? "Pine" : "Tree", pine ? Art.pine : Art.mid[5, 2], x + Rand(rng, 0.5f, 2f), gy, PropertyZ + 0.9f, pine ? 0.75f : Rand(rng, 0.7f, 0.9f), -60, rng.NextDouble() < 0.5);
                }
                if (rng.NextDouble() < 0.35)
                    CutOut(root, "BigTree", Art.mid[5, rng.NextDouble() < 0.15 ? 1 : 2], cx + Rand(rng, -2f, 2f), gy, z + 9f, Rand(rng, 1.1f, 1.4f), -70);
                x += lot;
            }
            // A second row of houses further back gives the street depth (never on a side street).
            for (float x = x0 - 20f; x < x1 + 20f; x += Rand(rng, 10f, 14f))
            {
                var facade = rng.NextDouble() < 0.5 ? ProceduralArt.FacadeKind.HouseGable : ProceduralArt.FacadeKind.HouseLong;
                var roofStyle = rng.NextDouble() < 0.5 ? House3D.RoofStyle.GableToStreet : House3D.RoofStyle.GableSideways;
                if (OnSideStreet(track, x, facade)) continue;
                Building(root, x, GroundAt(track, x), Rand(rng, 20f, 24f), facade, roofStyle, 7f, 2.4f, new Color(0.93f, 0.93f, 0.9f), roofDark);
            }
            DistantHills(track, root, x0, x1);
        }

        static void BlockWall(Transform root, float a, float b, float gy, Material mat)
        {
            if (b - a < 0.4f) return;
            Solid(root, "BlockWall", new Vector3((a + b) * 0.5f, gy + 0.8f, PropertyZ + 0.15f), new Vector3(b - a, 1.6f, 0.25f), Color.white, mat);
            ContactShadow(root, a, b, gy, PropertyZ - 0.35f, PropertyZ + 0.02f);
            Solid(root, "WallCap", new Vector3((a + b) * 0.5f, gy + 1.63f, PropertyZ + 0.15f), new Vector3(b - a + 0.04f, 0.06f, 0.3f), new Color(0.82f, 0.82f, 0.8f));
        }

        static void Market(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            Color[] awnings = { new Color(0.25f, 0.45f, 0.75f), new Color(0.78f, 0.25f, 0.25f), new Color(0.3f, 0.6f, 0.4f) };
            int i = 0;
            for (float x = x0; x < x1; i++)
            {
                float w = 8f, skip;
                if (Blocked(track, x, x + w, out skip)) { x = skip; continue; }
                float cx = x + w * 0.5f, gy = GroundAt(track, cx);
                var kind = i % 2 == 0 ? ProceduralArt.FacadeKind.Shop0 : ProceduralArt.FacadeKind.Shop1;
                Building(root, cx, gy, PropertyZ + 0.6f, kind, House3D.RoofStyle.Flat, 8f, 0f, i % 3 == 0 ? new Color(0.95f, 0.9f, 0.82f) : new Color(0.88f, 0.9f, 0.94f), new Color(0.6f, 0.6f, 0.62f));
                // Awning sticking out over the pavement.
                Color awn = awnings[i % awnings.Length];
                Solid(root, "Awning", new Vector3(cx, gy + 3.55f, PropertyZ - 0.1f), new Vector3(7.4f, 0.14f, 1.4f), awn);
                Solid(root, "AwningValance", new Vector3(cx, gy + 3.3f, PropertyZ - 0.78f), new Vector3(7.4f, 0.5f, 0.06f), Color.Lerp(awn, Color.white, 0.15f));
                ContactShadow(root, cx - 3.9f, cx + 3.9f, gy, PropertyZ - 0.7f, PropertyZ + 0.6f);
                x += w;
                if (rng.NextDouble() < 0.35 && x + 2.4f < x1)
                {
                    // Drinks machines in the gap between shops.
                    Solid(root, "Vending", new Vector3(x + 0.7f, gy + 0.93f, PropertyZ + 0.2f), new Vector3(1f, 1.85f, 0.8f), new Color(0.85f, 0.22f, 0.24f));
                    Solid(root, "Vending", new Vector3(x + 1.75f, gy + 0.93f, PropertyZ + 0.2f), new Vector3(1f, 1.85f, 0.8f), new Color(0.25f, 0.45f, 0.78f));
                    x += 2.6f;
                }
            }
            // Flats behind the shops (never on a side street).
            for (float x = x0 - 20f; x < x1 + 20f; x += Rand(rng, 13f, 16f))
            {
                float z = Rand(rng, 22f, 28f);
                if (OnSideStreet(track, x, ProceduralArt.FacadeKind.Apartment)) continue;
                Building(root, x, GroundAt(track, x), z, ProceduralArt.FacadeKind.Apartment, House3D.RoofStyle.Flat, 10f, 0f, new Color(0.92f, 0.88f, 0.82f), new Color(0.6f, 0.6f, 0.62f));
            }
        }

        static void Beach(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            float sea = track.LowestGroundTop - 0.3f;
            var water = Solid(root, "Sea", new Vector3((x0 + x1) * 0.5f, sea - 0.05f, 480f), new Vector3(x1 - x0 + 1600f, 0.1f, 950f), Color.white, Art.surfaces[ProceduralArt.Surface.Sea]);
            water.faces = MeshBuilder.Faces.Top;
            water.Rebuild();

            // Foam where the waves break on the sand, and lines of breaking crests out at sea.
            Foam(root, x0 - 60f, x1 + 60f, 9.0f, 9.45f, sea + 0.19f, 0.3f);
            float[] crests = { 13f, 19f, 28f, 42f };
            for (int i = 0; i < crests.Length; i++)
                for (float x = x0 - 60f + (float)rng.NextDouble() * 10f; x < x1 + 60f; x += Rand(rng, 14f, 30f))
                {
                    float len = Rand(rng, 5f, 14f), w = Mathf.Lerp(0.35f, 0.9f, i / (float)(crests.Length - 1));
                    Foam(root, x, x + len, crests[i] + Rand(rng, -1f, 1f), crests[i] + w, sea - 0.04f, i * 1.7f + x);
                }

            for (float x = x0; x < x1; x += Rand(rng, 30f, 45f))
                LifeguardTower(root, x, GroundAt(track, x), 7.4f);
            for (float x = x0 + 8f; x < x1; x += Rand(rng, 10f, 18f))
            {
                float gy = GroundAt(track, x), z = Rand(rng, 3.4f, 5.2f);
                var go = new GameObject("Parasol");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(x, gy, z);
                var parasol = go.AddComponent<ParasolShape>();
                Color[] canopy = { new Color(0.9f, 0.3f, 0.28f), new Color(0.25f, 0.5f, 0.85f), new Color(1f, 0.75f, 0.2f) };
                parasol.colorA = canopy[rng.Next(canopy.Length)];
                parasol.lean = Rand(rng, -9f, 9f);
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                parasol.Rebuild();
                // A towel in its shade, and sometimes a cool box.
                Color[] towels = { new Color(0.95f, 0.55f, 0.6f), new Color(0.45f, 0.75f, 0.9f), new Color(1f, 0.85f, 0.35f) };
                Solid(root, "Towel", new Vector3(x + Rand(rng, -0.3f, 0.3f), gy + 0.008f, z - 0.4f), new Vector3(0.8f, 0.016f, 1.7f), towels[rng.Next(towels.Length)]);
                if (rng.NextDouble() < 0.4)
                    Solid(root, "CoolBox", new Vector3(x + 0.9f, gy + 0.18f, z + 0.3f), new Vector3(0.55f, 0.36f, 0.38f), new Color(0.3f, 0.55f, 0.85f));
            }
            for (float x = x0 + 15f; x < x1; x += Rand(rng, 22f, 38f))
            {
                // Rocks at the water's edge, darker where the sea wets them.
                float gy = GroundAt(track, x) - 0.12f, s = Rand(rng, 0.8f, 1.6f);
                var rock = new GameObject("Rocks");
                rock.transform.SetParent(root, false);
                rock.transform.position = new Vector3(x, gy, Rand(rng, 8.6f, 11f));
                var blobs = rock.AddComponent<BlobShape>();
                Color grey = new Color(0.55f, 0.53f, 0.5f), wet = new Color(0.38f, 0.37f, 0.36f);
                blobs.blobs.Add(new BlobShape.Blob(new Vector3(0f, 0.2f * s, 0f), new Vector3(1.4f, 0.75f, 1.1f) * s, grey));
                blobs.blobs.Add(new BlobShape.Blob(new Vector3(1.1f * s, 0.05f, 0.3f), new Vector3(0.8f, 0.45f, 0.7f) * s, wet));
                blobs.blobs.Add(new BlobShape.Blob(new Vector3(-1f * s, 0.1f, -0.2f), new Vector3(0.6f, 0.4f, 0.5f) * s, grey));
                rock.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                blobs.Rebuild();
            }
            // Tufts of beach grass in the soft sand nearer the camera.
            var grass = new GameObject("BeachGrass");
            grass.transform.SetParent(root, false);
            var tufts = grass.AddComponent<BlobShape>();
            for (float x = x0; x < x1; x += Rand(rng, 1.5f, 5f))
            {
                float gy = GroundAt(track, x), z = Rand(rng, -9f, -2.4f);
                // A low, spreading clump of dune grass.
                for (int k = 0; k < 4; k++)
                    tufts.blobs.Add(new BlobShape.Blob(new Vector3(x + Rand(rng, -0.3f, 0.3f), gy + 0.03f, z + Rand(rng, -0.25f, 0.25f)),
                        new Vector3(Rand(rng, 0.14f, 0.24f), Rand(rng, 0.06f, 0.11f), Rand(rng, 0.12f, 0.2f)), Color.Lerp(new Color(0.58f, 0.66f, 0.34f), new Color(0.82f, 0.8f, 0.5f), (float)rng.NextDouble())));
            }
            grass.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            tufts.Rebuild();
            // Wooded headlands out on the horizon.
            for (int i = 0; i < 3; i++)
                CutOut(root, "Headland", Art.headland, x0 + (x1 - x0) * (0.15f + i * 0.4f) + Rand(rng, -40f, 40f), sea - 0.5f, 650f + i * 60f, 10f, -85, i % 2 == 1);
        }

        /// <summary>A white band of foam with a wavy edge toward the camera.</summary>
        static void Foam(Transform root, float a, float b, float zFront, float zBack, float y, float phase)
        {
            var go = new GameObject("Foam");
            go.transform.SetParent(root, false);
            var strip = go.AddComponent<WavyStrip>();
            strip.fromX = a;
            strip.toX = b;
            strip.frontZ = zFront;
            strip.backZ = zBack;
            strip.y = y;
            strip.phase = phase;
            strip.color = new Color(0.97f, 0.98f, 1f);
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            strip.Rebuild();
        }

        /// <summary>A white wooden lifeguard tower: legs and braces, a platform, a hut with a red roof, a ladder and a flag.</summary>
        static void LifeguardTower(Transform root, float x, float gy, float z)
        {
            Color white = new Color(0.96f, 0.96f, 0.94f), red = new Color(0.85f, 0.25f, 0.22f), dark = new Color(0.3f, 0.35f, 0.42f);
            const float deck = 2.6f;
            foreach (float dx in new[] { -0.75f, 0.75f })
                foreach (float dz in new[] { -0.75f, 0.75f })
                    Solid(root, "TowerLeg", new Vector3(x + dx, gy + deck * 0.5f, z + dz), new Vector3(0.12f, deck, 0.12f), white);
            foreach (float dz in new[] { -0.75f, 0.75f })
                Solid(root, "TowerBrace", new Vector3(x, gy + 1.1f, z + dz), new Vector3(1.5f, 0.08f, 0.08f), white);
            foreach (float dx in new[] { -0.75f, 0.75f })
                Solid(root, "TowerBrace", new Vector3(x + dx, gy + 1.1f, z), new Vector3(0.08f, 0.08f, 1.5f), white);
            Solid(root, "TowerDeck", new Vector3(x, gy + deck, z), new Vector3(1.9f, 0.12f, 1.9f), white);
            Solid(root, "TowerRail", new Vector3(x, gy + deck + 0.45f, z - 0.92f), new Vector3(1.9f, 0.06f, 0.06f), white);
            Solid(root, "TowerHut", new Vector3(x, gy + deck + 0.65f, z + 0.15f), new Vector3(1.3f, 1.2f, 1.2f), white);
            Solid(root, "TowerWindow", new Vector3(x, gy + deck + 0.8f, z - 0.46f), new Vector3(0.8f, 0.45f, 0.02f), dark);
            Solid(root, "TowerRoof", new Vector3(x, gy + deck + 1.35f, z + 0.15f), new Vector3(1.6f, 0.16f, 1.5f), red);
            Solid(root, "TowerRoofTop", new Vector3(x, gy + deck + 1.5f, z + 0.15f), new Vector3(1.1f, 0.16f, 1f), red);
            // Ladder up the front.
            foreach (float dx in new[] { -0.25f, 0.25f })
                Solid(root, "LadderRail", new Vector3(x + dx, gy + deck * 0.5f, z - 1.25f), new Vector3(0.06f, deck + 0.1f, 0.06f), white);
            for (float y = 0.3f; y < deck; y += 0.32f)
                Solid(root, "LadderRung", new Vector3(x, gy + y, z - 1.25f), new Vector3(0.5f, 0.04f, 0.05f), white);
            Solid(root, "FlagPole", new Vector3(x + 0.55f, gy + deck + 2.1f, z + 0.15f), new Vector3(0.04f, 1.6f, 0.04f), white);
            Solid(root, "Flag", new Vector3(x + 0.8f, gy + deck + 2.7f, z + 0.15f), new Vector3(0.5f, 0.32f, 0.02f), new Color(1f, 0.85f, 0.15f));
        }

        static void City(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            var hoarding = Art.surfaces[ProceduralArt.Surface.Hoarding];
            for (float x = x0; x < x1;)
            {
                float w = Rand(rng, 11f, 14f), skip;
                if (Blocked(track, x, x + w, out skip)) { x = skip; continue; }
                float cx = x + w * 0.5f, gy = GroundAt(track, cx);
                if (rng.NextDouble() < 0.5)
                    Solid(root, "Hoarding", new Vector3(cx, gy + 1.3f, PropertyZ + 0.2f), new Vector3(w - 0.3f, 2.6f, 0.2f), Color.white, hoarding);
                if (rng.NextDouble() < 0.5)
                    Building(root, cx, gy, PropertyZ + 3f, ProceduralArt.FacadeKind.Warehouse, House3D.RoofStyle.Shed, 8f, 1.2f, new Color(0.78f, 0.74f, 0.7f), new Color(0.5f, 0.52f, 0.56f));
                else
                    Building(root, cx, gy, PropertyZ + 5f, ProceduralArt.FacadeKind.Apartment, House3D.RoofStyle.Flat, 10f, 0f, new Color(0.92f, 0.88f, 0.82f), new Color(0.6f, 0.6f, 0.62f));
                x += w;
            }
            for (float x = x0; x < x1; x += Rand(rng, 40f, 60f))
            {
                float skip;
                if (Blocked(track, x - 4f, x + 4f, out skip)) continue;
                CutOut(root, "Crane", Art.mid[4, 2], x, GroundAt(track, x), 45f, 2f, -75);
            }
            DistantHills(track, root, x0, x1);
        }

        static void Park(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            Color hedge = new Color(0.28f, 0.5f, 0.3f);
            for (float x = x0; x < x1;)
            {
                float w = Rand(rng, 6f, 10f), skip;
                if (Blocked(track, x, x + w, out skip)) { x = skip; continue; }
                float cx = x + w * 0.5f, gy = GroundAt(track, cx) + 0.04f;
                Solid(root, "Hedge", new Vector3(cx, gy + 0.5f, PropertyZ + 0.4f), new Vector3(w - 1.2f, 1f, 0.8f), hedge);
                ContactShadow(root, cx - w * 0.5f + 0.6f, cx + w * 0.5f - 0.6f, gy, PropertyZ - 0.25f, PropertyZ);
                CutOut(root, "Bush", Art.bush, cx - w * 0.25f, gy + 0.6f, PropertyZ + 0.3f, 1f, -55);
                if (rng.NextDouble() < 0.4)
                    Solid(root, "Bench", new Vector3(cx + 1.5f, gy + 0.25f, PropertyZ - 0.6f), new Vector3(1.8f, 0.5f, 0.5f), new Color(0.6f, 0.42f, 0.3f));
                x += w;
            }
            for (float x = x0; x < x1; x += Rand(rng, 4f, 8f))
            {
                float skip;
                if (Blocked(track, x - 3f, x + 3f, out skip)) continue;
                bool cherry = rng.NextDouble() < 0.4;
                CutOut(root, cherry ? "Cherry" : "Tree", Art.mid[5, cherry ? 1 : 2], x, GroundAt(track, x), Rand(rng, 6.5f, 16f), Rand(rng, 0.9f, 1.2f), -62, rng.NextDouble() < 0.5);
            }
            DistantHills(track, root, x0, x1);
        }

        static void DistantHills(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            int ch = LevelBuildKit.Chapter;
            var far = CutOut(root, "DistantHills", Art.far[ch], (x0 + x1) * 0.5f, track.LowestGroundTop - 6f, 260f, 6f, -85);
            far.drawMode = SpriteDrawMode.Tiled;
            far.size = new Vector2((x1 - x0 + 900f) / 6f, Art.far[ch].bounds.size.y);
        }
    }
}
