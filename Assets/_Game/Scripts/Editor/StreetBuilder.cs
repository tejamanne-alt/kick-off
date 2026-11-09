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
    /// street for each chapter. Scale: 1 unit to the metre, as the asset kits are modelled (the kid
    /// is about 1.55 tall, a house about 9 to its ridge); only the ball is drawn larger than life.
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
    public static partial class StreetBuilder
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
                    s.Add(new StripSpec(-PathHalf, PathHalf, 0f, ProceduralArt.Surface.Paving, new Color(1f, 0.985f, 0.975f)));
                    s.Add(new StripSpec(PathHalf, PropertyZ + 0.6f, 0f, ProceduralArt.Surface.Paving, new Color(1f, 0.985f, 0.975f)));
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0f, ProceduralArt.Surface.Paving, new Color(0.92f, 0.91f, 0.9f)));
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
                    // Behind the property line, under the houses: lawns and gardens on the home street,
                    // yards and lots in the city.
                    if (chapter == 4) s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0f, ProceduralArt.Surface.Concrete, new Color(0.9f, 0.9f, 0.88f)));
                    else s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0f, ProceduralArt.Surface.Grass, new Color(0.96f, 0.97f, 0.92f)));
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
        public static GameObject Slab(Transform parent, string name, float fromX, float toX, float top, bool closeLeft, bool closeRight, Part part, float lineInset = 0.1f)
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
            // The faces where the ground steps up or down are retaining walls: concrete blocks on the
            // home street and in the park, plain cast concrete at the market and in the city.
            materials.Add(Art.surfaces[ch == 1 || ch == 5 ? ProceduralArt.Surface.BlockWall : ProceduralArt.Surface.Concrete]);
            slab.sideColor = new Color(0.9f, 0.9f, 0.88f);
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
                    Patch(go.transform, "EdgeLine", fromX + lineInset, toX - lineInset, road, z - 0.06f, z + 0.06f, paint);
                float mid = (RoadNear + RoadFar) * 0.5f;
                for (float x = Mathf.Ceil(fromX / 6f) * 6f; x + 3f < toX; x += 6f)
                    Patch(go.transform, "CentreDash", x, x + 3f, road, mid - 0.06f, mid + 0.06f, paint);
                for (float x = Mathf.Ceil(fromX / 13f) * 13f + 5f; x < toX - 1f; x += 13f)
                    Model(go.transform, "Street", "DrainGrate", x, road, RoadNear - 0.35f);   // gullies along the kerb
                for (float x = Mathf.Ceil(fromX / 37f) * 37f + 11f; x < toX - 1f; x += 37f)
                {
                    if (Model(go.transform, "Street", "ManholeCover", x, road, mid - 1.6f, (x * 31f) % 90f) != null) continue;
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
        public static void CrossingStreet(Transform parent, float fromX, float toX, float top, bool zebra = true)
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
            for (float x = fromX + 0.45f; zebra && x < toX - 0.3f; x += 0.95f)
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

        /// <summary>The ground's height at (x, z): on the beach the sand's, which rolls (see <see cref="SandField"/>); elsewhere the gameplay ground's at x.</summary>
        static float GroundAt(LevelBuildKit.TrackBuilder track, float x, float z)
        {
            return LevelBuildKit.Chapter == 3 ? track.SandHeight(x, z) : GroundAt(track, x);
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

        /// <summary>Would a back-row building of this facade, centred on x, stand on a side street
        /// (they run far back from the footpath) or on the school building past the gate?</summary>
        static bool OnSideStreet(LevelBuildKit.TrackBuilder track, float x, ProceduralArt.FacadeKind facade)
        {
            float half = ProceduralArt.FacadeSize(facade).x * 0.5f + 0.3f;
            return OverlapsBackRow(track, x - half, x + half);
        }

        /// <summary>
        /// [a, b] overlaps a side street, the seam between the home street and the route's own (no building of the back rows
        /// stands across it: each street's pass builds its own side), or the school building (it stands 10 to 22 units past the gate).
        /// </summary>
        static bool OverlapsBackRow(LevelBuildKit.TrackBuilder track, float a, float b)
        {
            if (AcrossSeam(track, a, b)) return true;
            foreach (var area in track.OpenAreas)
                if (b > area.x - 0.6f && a < area.y + 0.6f) return true;
            float goal = track.GoalX;
            return goal > track.MinX && b > goal + 8f && a < goal + 24f;
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
            Patch(parent, "ContactShadow", a, b, groundY, zFrom, zTo, new Color(0.48f, 0.49f, 0.58f), SurfaceUnder((zFrom + zTo) * 0.5f), 0.004f);
        }

        /// <summary>The ground material at depth z behind the footpath, for shadows that keep its texture.</summary>
        static Material SurfaceUnder(float z)
        {
            int ch = LevelBuildKit.Chapter;
            foreach (var spec in StripsFor(ch))
                if (spec.zFrom >= PathHalf - 0.001f && z >= spec.zFrom && z <= spec.zTo) return Art.surfaces[spec.surface];
            return Art.surfaces[ch == 3 ? ProceduralArt.Surface.Sand : ch == 5 ? ProceduralArt.Surface.Grass : ProceduralArt.Surface.Concrete];
        }

        // ---------------------------------------------------------------- kit models

        /// <summary>A kit model standing at (x, groundY, z) facing the camera, or null if the kit hasn't got it.</summary>
        public static Transform Model(Transform parent, string kit, string model, float x, float groundY, float z, float yaw = 0f, float scale = 1f,
            Color? tint1 = null, Color? tint2 = null, Color? tint3 = null, bool castShadows = true)
        {
            return LevelBuildKit.KitModel(parent, kit, model, new Vector3(x, groundY, z), yaw, scale, tint1, tint2, tint3, castShadows);
        }

        /// <summary>
        /// Lines up kit segments (walls, hedges, fences, hoardings) end to end from a to b, each
        /// stretched a little so a whole number of them fills the run. False if the kit hasn't got
        /// the model, so the caller can fall back.
        /// </summary>
        public static bool Row(Transform parent, string kit, string model, float a, float b, float groundY, float z, Color? tint1 = null)
        {
            float length = LevelBuildKit.KitSize(kit, model).x;
            if (length < 0.1f || !LevelBuildKit.HasKitModel(kit, model)) return false;
            int n = Mathf.Max(1, Mathf.RoundToInt((b - a) / length));
            float step = (b - a) / n;
            for (int i = 0; i < n; i++)
            {
                var piece = Model(parent, kit, model, a + step * (i + 0.5f), groundY, z, 0f, 1f, tint1);
                if (piece != null) piece.localScale = new Vector3(step / length, 1f, 1f);
            }
            return true;
        }

        /// <summary>The first of these models the kit has, or null.</summary>
        static string FirstModel(string kit, params string[] models)
        {
            foreach (var m in models)
                if (LevelBuildKit.HasKitModel(kit, m)) return m;
            return null;
        }

        /// <summary>The Buildings kit's model for each facade (tools/blender/kit_buildings.py).</summary>
        static string BuildingModel(ProceduralArt.FacadeKind facade)
        {
            switch (facade)
            {
                case ProceduralArt.FacadeKind.Shop0: return "ShopFruit";
                case ProceduralArt.FacadeKind.Shop1: return "ShopShutter";
                default: return facade.ToString();
            }
        }

        /// <summary>A paint scheme for a kit building: walls (part 1), trim (part 2) and roof (part 3), sRGB.</summary>
        struct Paint
        {
            public Color wall, trim, roof;
            public Paint(Color wall, Color trim, Color roof) { this.wall = wall; this.trim = trim; this.roof = roof; }
        }

        // A few curated, slightly faded schemes rather than random mixes: each look stays
        // harmonious, and each building model only ever needs a handful of recoloured copies.
        // Paint schemes (wall, trim, roof): mostly white, pale grey and light stucco walls under dark
        // slate, charcoal, blue-grey or tiled roofs, as real streets are; colour comes in small doses
        // (a shop's awning, a door, a tin roof).
        static readonly Paint[] HousePaints =
        {
            new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.3f, 0.3f, 0.32f), new Color(0.32f, 0.34f, 0.38f)),    // white, charcoal, slate
            new Paint(new Color(0.9f, 0.88f, 0.84f), new Color(0.97f, 0.97f, 0.95f), new Color(0.66f, 0.38f, 0.3f)),     // warm grey, white, terracotta tile
            new Paint(new Color(0.82f, 0.84f, 0.86f), new Color(0.96f, 0.96f, 0.95f), new Color(0.3f, 0.38f, 0.48f)),    // pale grey, white, blue slate
            new Paint(new Color(0.92f, 0.88f, 0.8f), new Color(0.42f, 0.32f, 0.26f), new Color(0.36f, 0.33f, 0.32f)),    // light stucco, brown, dark tile
            new Paint(new Color(0.88f, 0.91f, 0.92f), new Color(0.96f, 0.96f, 0.95f), new Color(0.24f, 0.42f, 0.46f)),   // blue-white, white, green tin
            new Paint(new Color(0.96f, 0.94f, 0.9f), new Color(0.55f, 0.3f, 0.25f), new Color(0.42f, 0.42f, 0.44f)),     // cream, brick, grey
        };
        static readonly Paint[] ShopPaints =
        {
            new Paint(new Color(0.94f, 0.94f, 0.92f), new Color(0.2f, 0.42f, 0.74f), new Color(0.56f, 0.57f, 0.6f)),     // blue awning
            new Paint(new Color(0.88f, 0.86f, 0.82f), new Color(0.82f, 0.22f, 0.2f), new Color(0.56f, 0.57f, 0.6f)),     // red awning
            new Paint(new Color(0.84f, 0.86f, 0.86f), new Color(0.18f, 0.52f, 0.36f), new Color(0.56f, 0.57f, 0.6f)),    // green awning
            new Paint(new Color(0.93f, 0.91f, 0.86f), new Color(0.96f, 0.72f, 0.12f), new Color(0.56f, 0.57f, 0.6f)),    // yellow awning
        };
        static readonly Paint[] WorkPaints =
        {
            new Paint(new Color(0.82f, 0.82f, 0.81f), new Color(0.9f, 0.56f, 0.14f), new Color(0.5f, 0.53f, 0.57f)),
            new Paint(new Color(0.8f, 0.81f, 0.82f), new Color(0.8f, 0.26f, 0.22f), new Color(0.46f, 0.5f, 0.55f)),
            new Paint(new Color(0.86f, 0.84f, 0.8f), new Color(0.24f, 0.44f, 0.64f), new Color(0.52f, 0.52f, 0.54f)),
        };

        /// <summary>
        /// The Buildings kit's model of a facade, front wall on z, fitted to the facade's width and
        /// painted from the schemes for its kind. False if the kit hasn't got it.
        /// </summary>
        static bool KitBuilding(Transform parent, float x, float groundY, float z, ProceduralArt.FacadeKind facade, int seed)
        {
            string model = BuildingModel(facade);
            float width = LevelBuildKit.KitSize("Buildings", model).x;
            if (width < 0.1f || !LevelBuildKit.HasKitModel("Buildings", model)) return false;
            Paint[] schemes;
            switch (facade)
            {
                case ProceduralArt.FacadeKind.Shop0:
                case ProceduralArt.FacadeKind.Shop1: schemes = ShopPaints; break;
                case ProceduralArt.FacadeKind.Warehouse: schemes = WorkPaints; break;
                case ProceduralArt.FacadeKind.School: schemes = null; break;
                default: schemes = HousePaints; break;
            }
            float scale = Mathf.Clamp(ProceduralArt.FacadeSize(facade).x / width, 0.8f, 1.25f);
            Transform t;
            if (schemes == null) t = Model(parent, "Buildings", model, x, groundY, z, 0f, scale);
            else
            {
                var p = schemes[Scramble(seed) % schemes.Length];
                t = Model(parent, "Buildings", model, x, groundY, z, 0f, scale, p.wall, p.trim, p.roof);
            }
            return t != null;
        }

        /// <summary>Mixes a position-derived seed, so evenly spaced buildings don't fall into the same scheme.</summary>
        static int Scramble(int seed)
        {
            unchecked
            {
                uint h = (uint)seed * 2654435761u;
                h ^= h >> 15;
                h *= 2246822519u;
                return (int)((h ^ (h >> 13)) & 0x7fffffff);
            }
        }

        // Summer greens for broadleaf trees and bushes (Plants kit part 1), so neighbours differ a
        // little: true leaf greens as in the reference shots, the sunlit clumps a fresh yellow-green
        // and the shade inside the crown going deep (not olive, and not lime either).
        static readonly Color[] SummerLeaves =
        {
            new Color(0.243f, 0.327f, 0.207f), new Color(0.218f, 0.302f, 0.207f), new Color(0.268f, 0.352f, 0.207f),
            new Color(0.201f, 0.293f, 0.217f), new Color(0.26f, 0.335f, 0.186f),
        };
        // Meadow grass in leaf (the kit's tall grass and tufts are made seeding, golden).
        static readonly Color[] MeadowGreens = { new Color(0.46f, 0.57f, 0.26f), new Color(0.5f, 0.6f, 0.28f), new Color(0.4f, 0.53f, 0.25f) };
        /// <summary>Palm fronds and clipped hedges: the same leaf greens, hedges a deep clipped green.</summary>
        public static readonly Color PalmGreen = new Color(0.3f, 0.42f, 0.2f), HedgeGreen = new Color(0.21f, 0.33f, 0.17f);

        /// <summary>
        /// A tree (or bush) from the Plants kit standing at (x, groundY, z), turned at random, its
        /// leaves in one of the summer greens; the old cut-out if the kit hasn't got the model.
        /// </summary>
        static void Plant(Transform parent, string model, Sprite fallback, float x, float groundY, float z, float scale, float spriteScale, int order, System.Random rng)
        {
            Color? leaves = null;
            bool leafy = model.StartsWith("Broadleaf") || model == "Birch" || model.StartsWith("Bush");
            if (leafy) leaves = SummerLeaves[rng.Next(SummerLeaves.Length)];
            else if (model.StartsWith("Palm")) leaves = PalmGreen;
            else if ((model == "TallGrass" || model == "GrassTuft") && rng.NextDouble() < 0.8) leaves = MeadowGreens[rng.Next(MeadowGreens.Length)];
            if (Model(parent, "Plants", model, x, groundY, z, Rand(rng, 0f, 360f), scale, leaves) != null) return;
            if (fallback != null) CutOut(parent, model, fallback, x, groundY, z, spriteScale, order, rng.NextDouble() < 0.5);
        }

        /// <summary>
        /// A building with its front wall on z: the Buildings kit's model of the facade, else the
        /// procedural house with the painted facade and its dressing. True if it is the kit model.
        /// </summary>
        static bool Building(Transform parent, float x, float groundY, float z, ProceduralArt.FacadeKind facade, House3D.RoofStyle roof,
            float depth, float roofHeight, Color wall, Color roofColor)
        {
            Vector2 size = ProceduralArt.FacadeSize(facade);
            int seed = Mathf.Abs(Mathf.RoundToInt(x * 7f + z * 13f));
            if (KitBuilding(parent, x, groundY, z, facade, seed))
            {
                ContactShadow(parent, x - size.x * 0.5f, x + size.x * 0.5f, groundY, z - 0.45f, z);
                return true;
            }
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
            Dress(parent, x - size.x * 0.5f, groundY, z, facade, seed);
            return false;
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
            // A level that starts at home and goes on in another chapter's street: two streets, side by side (StreetBuilder.Home.cs).
            if (track.HasSeam)
            {
                SceneryWithSeam(track, root);
                return;
            }
            int ch = LevelBuildKit.Chapter;
            var rng = new System.Random(ch * 131 + Mathf.RoundToInt(track.MaxX));
            float x0 = track.MinX - 50f, x1 = track.MaxX + 50f;
            // The animals live outside the street root: its static batching would freeze their moving parts.
            critters = new GameObject("Critters").transform;
            wallTops.Clear();

            switch (ch)
            {
                case 2: Market(track, root, rng, x0, x1); break;
                case 3: Beach(track, root, rng, x0, x1); break;
                case 4: City(track, root, rng, x0, x1); break;
                case 5: Park(track, root, rng, x0, x1); break;
                default: Suburb(track, root, rng, x0, x1); break;
            }
            if (ch != 3) Poles(track, root, x0, x1);
            if (ch != 3) CanopyShadows(track, root, new System.Random(ch * 173 + Mathf.RoundToInt(x0)), x0, x1);
            Depth(track, root, new System.Random(ch * 211 + Mathf.RoundToInt(x0)), x0, x1);
            if (ch != 3)
                foreach (var area in track.OpenAreas)
                    SideStreetEnd(track, root, new System.Random(ch * 53 + Mathf.RoundToInt(area.x * 3f)), area);
            SchoolSurroundings(track, root, new System.Random(ch * 97 + Mathf.RoundToInt(track.GoalX)));
            Wildlife(track, root, new System.Random(ch * 389 + Mathf.RoundToInt(x0)), x0, x1);
        }

        // ---------------------------------------------------------------- shade across the near road

        /// <summary>Where the dappled shade of the near trees falls: the middle of the foreground band of ground (depth z).</summary>
        const float CanopyShadeZ = -5f;

        /// <summary>The sun the scene is lit by, when it isn't the chapter being built's (a level's home street).</summary>
        static Vector3? lightSun;

        /// <summary>
        /// Street trees on our side of the road, between the camera and the street, seen only by
        /// their shade: they cast shadows but are not drawn. Their dappled shade lies in patches
        /// across the near road (or cobbles, or lawn), the dark foreground band that frames the
        /// reference shots (docs/ART_DIRECTION.md), and sways a little with the breeze. Each is placed
        /// from the chapter's sun so the shade lands on the foreground and stops short of the
        /// footpath the kid plays on: crowns squashed front to back, centred so their shade sits at
        /// <see cref="CanopyShadeZ"/>.
        /// </summary>
        static void CanopyShadows(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            string[] models = { "BroadleafWide", "BroadleafLarge", "Broadleaf" };
            if (!LevelBuildKit.HasKitModel("Plants", models[0]) && !LevelBuildKit.HasKitModel("Plants", models[2])) return;
            Vector3 sun = (lightSun ?? LevelBuildKit.Theme.mood.sunDirection).normalized;
            if (sun.y < 0.2f || sun.z > -0.05f) return;   // the shade would not fall toward the camera
            // How far a point's shadow moves along the ground per metre of its height.
            float perX = -sun.x / sun.y, perZ = -sun.z / sun.y;
            var group = new GameObject("CanopyShade").transform;
            group.SetParent(root, false);
            for (float x = x0 + Rand(rng, 0f, 12f); x < x1; x += Rand(rng, 11f, 26f))
            {
                if (x < ClipLo || x > ClipHi) continue;
                int trees = rng.NextDouble() < 0.35 ? 2 : 1;
                for (int k = 0; k < trees; k++)
                {
                    string model = models[rng.Next(models.Length)];
                    if (!LevelBuildKit.HasKitModel("Plants", model)) model = models[2];
                    if (!LevelBuildKit.HasKitModel("Plants", model)) return;
                    float scale = Rand(rng, 0.95f, 1.2f);
                    // The crown's middle is about two thirds of the way up the tree.
                    float crown = LevelBuildKit.KitSize("Plants", model).y * scale * 0.66f;
                    float shadeX = x + k * Rand(rng, 4f, 7f);
                    float gy = GroundAt(track, shadeX);
                    // Turned only a little from square on, so squashing its local depth squashes it front to back.
                    float yaw = (rng.NextDouble() < 0.5 ? 0f : 180f) + Rand(rng, -15f, 15f);
                    var tree = Model(group, "Plants", model, shadeX - perX * crown, gy, CanopyShadeZ - perZ * crown, yaw, scale);
                    if (tree == null) continue;
                    tree.localScale = new Vector3(scale, scale, scale * 0.5f);
                    foreach (var r in tree.GetComponentsInChildren<MeshRenderer>())
                        r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.ShadowsOnly;
                }
            }
        }

        // ---------------------------------------------------------------- side streets

        /// <summary>Where a side street's road ends and the back road it meets begins (depth z).</summary>
        const float BackRoadNear = 70f, BackRoadFar = 77.5f;

        /// <summary>
        /// The rest of a side street, so the view up it is a street scene rather than a road cut off
        /// against the fields: pavements along both sides with a few street trees, and at its far
        /// end a T-junction with a back road running across, its far pavement and a row of buildings
        /// facing it (trees in the park) that close the view.
        /// </summary>
        static void SideStreetEnd(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, Vector2 area)
        {
            int ch = LevelBuildKit.Chapter;
            float cx = (area.x + area.y) * 0.5f, top = GroundAt(track, cx);
            var paving = Art.surfaces[ch == 4 ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.Paving];
            var road = Art.surfaces[ch == 2 ? ProceduralArt.Surface.Cobbles : ProceduralArt.Surface.Asphalt];
            var kerb = Art.surfaces[ProceduralArt.Surface.Kerb];
            var street = new GameObject("SideStreetEnd").transform;
            street.SetParent(root, false);
            const float lift = 0.012f;   // just over the ground behind the street, so the two never flicker

            // Pavements along the side street, kerbed, from the main footpath to the back road. (A Holiday
            // Run stage keeps to its own stretch: ClipLo and ClipHi are the ends of the world in a level.)
            foreach (var side in new[] { new Vector2(area.x - 1.9f, area.x), new Vector2(area.y, area.y + 1.9f) })
            {
                if (side.x < ClipLo || side.y > ClipHi) continue;
                Ground(street, "SidePavement", side.x, side.y, top + lift, PathHalf, BackRoadNear, paving, kerb);
            }
            // The back road across the end, kerbs either side of the mouth and along its far side, and
            // the far pavement in front of the buildings.
            float a = Mathf.Max(cx - 38f, ClipLo), b = Mathf.Min(cx + 38f, ClipHi);
            Ground(street, "BackRoad", a, b, top + lift, BackRoadNear, BackRoadFar, road, kerb);
            Ground(street, "BackPavement", a, b, top + lift, BackRoadFar + 0.25f, BackRoadFar + 3f, paving, kerb);
            foreach (var run in new[] { new Vector2(a, area.x - 1.9f), new Vector2(area.y + 1.9f, b) })
            {
                if (run.y - run.x < 0.05f) continue;
                Solid(street, "BackKerb", new Vector3((run.x + run.y) * 0.5f, top + 0.08f, BackRoadNear - 0.11f), new Vector3(run.y - run.x, 0.16f, 0.22f), Color.white, kerb);
            }
            Solid(street, "BackKerb", new Vector3(cx, top + 0.08f, BackRoadFar + 0.11f), new Vector3(b - a, 0.16f, 0.22f), Color.white, kerb);
            for (float x = a + 1f; x < b - 1f; x += 4f)
                Patch(street, "CentreDash", x, x + 2f, top + lift, (BackRoadNear + BackRoadFar) * 0.5f - 0.06f, (BackRoadNear + BackRoadFar) * 0.5f + 0.06f, new Color(0.95f, 0.95f, 0.93f));

            // Street trees along the side street's pavements.
            if (LevelBuildKit.HasKitModel("Plants", "Broadleaf"))
                foreach (float tx in new[] { area.x - 1.1f, area.y + 1.1f })
                    for (float z = Rand(rng, 14f, 18f); z < 34f; z += Rand(rng, 9f, 12f))   // clear of the far row behind
                    {
                        // (The draws stay in their old order, so the levels' streets come out as before.)
                        string tree = rng.NextDouble() < 0.7 ? "Broadleaf" : "Birch";
                        float height = Rand(rng, 0.75f, 0.95f);
                        if (tx >= a && tx <= b) Plant(street, tree, null, tx, top, z, height, 1f, -65, rng);
                    }

            // Across the end: buildings facing the back road, the first one squarely in the view.
            ProceduralArt.FacadeKind[] kinds;
            switch (ch)
            {
                case 2: kinds = new[] { ProceduralArt.FacadeKind.Shop0, ProceduralArt.FacadeKind.Apartment, ProceduralArt.FacadeKind.Shop1, ProceduralArt.FacadeKind.HouseLong }; break;
                case 4: kinds = new[] { ProceduralArt.FacadeKind.Warehouse, ProceduralArt.FacadeKind.Apartment }; break;
                case 5: kinds = null; break;
                default: kinds = new[] { ProceduralArt.FacadeKind.HouseGable, ProceduralArt.FacadeKind.HouseLong, ProceduralArt.FacadeKind.Bungalow }; break;
            }
            float front = BackRoadFar + 3.4f;
            if (kinds == null || !LevelBuildKit.HasKitModel("Buildings", "HouseGable"))
            {
                for (float x = a + 2f; x < b - 2f; x += Rand(rng, 3.5f, 6f))
                    Plant(street, rng.NextDouble() < 0.6 ? "BroadleafLarge" : "Broadleaf", null, x, top, front + Rand(rng, 1f, 6f), Rand(rng, 0.9f, 1.2f), 1f, -70, rng);
                return;
            }
            var first = kinds[rng.Next(kinds.Length)];
            float x0 = cx - ProceduralArt.FacadeSize(first).x * Rand(rng, 0.3f, 0.7f);
            // Rightward from the one closing the view, then leftward from it.
            for (int dir = 1; dir >= -1; dir -= 2)
            {
                float x = dir > 0 ? x0 : x0 - Rand(rng, 1f, 3f);
                for (int k = 0; k < 4; k++)
                {
                    var kind = dir > 0 && k == 0 ? first : kinds[rng.Next(kinds.Length)];
                    float width = ProceduralArt.FacadeSize(kind).x;
                    float bx = dir > 0 ? x + width * 0.5f : x - width * 0.5f;
                    if (bx - width * 0.5f < a || bx + width * 0.5f > b) break;
                    KitBuilding(street, bx, top, front, kind, Mathf.Abs(Mathf.RoundToInt(bx * 7f + front * 13f)));
                    x += dir * (width + Rand(rng, 1f, 3f));
                }
            }
        }

        /// <summary>A strip of street surface from x a to b and depth z0 to z1, its top at y: road or pavement, kerb-sided.</summary>
        static void Ground(Transform parent, string name, float a, float b, float y, float z0, float z1, Material surface, Material kerb)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var slab = go.AddComponent<StreetSlab>();
            slab.fromX = a; slab.toX = b; slab.top = y; slab.bottom = y - 0.5f;
            slab.closeLeft = slab.closeRight = true;
            slab.materials = 3;
            slab.sideColor = SideColor(LevelBuildKit.Chapter);
            slab.sideSubmesh = 2;
            slab.strips.Add(new StreetSlab.Strip(z0, z1, 0f, 0, Color.white));
            go.GetComponent<MeshRenderer>().sharedMaterials = new[] { surface, kerb, Art.solid };
            slab.Rebuild();
        }

        // ---------------------------------------------------------------- ground steps

        /// <summary>The height of the ground behind the footpath at x: the span there, or across a gap the lower side (the back strip bridges gaps at that height).</summary>
        static float BackTop(LevelBuildKit.TrackBuilder track, float x)
        {
            float inside = float.MinValue, left = float.NaN, right = float.NaN, leftGap = float.MaxValue, rightGap = float.MaxValue;
            foreach (var s in track.GroundSpans)
            {
                if (x >= s.x && x <= s.y) inside = Mathf.Max(inside, s.z);
                else if (s.y < x && x - s.y < leftGap) { leftGap = x - s.y; left = s.z; }
                else if (s.x > x && s.x - x < rightGap) { rightGap = s.x - x; right = s.z; }
            }
            if (inside > float.MinValue) return inside;
            if (float.IsNaN(left)) return float.IsNaN(right) ? 0f : right;
            return float.IsNaN(right) ? left : Mathf.Min(left, right);
        }

        /// <summary>
        /// The first place inside (a, b) where the ground steps up or down, or NaN. Lots and buildings
        /// end there rather than straddle it, so walls and houses stand on their own ground.
        /// </summary>
        static float StepWithin(LevelBuildKit.TrackBuilder track, float a, float b)
        {
            float best = float.NaN;
            foreach (var s in track.GroundSpans)
                foreach (float e in new[] { s.x, s.y })
                    if (e > a + 0.3f && e < b - 0.3f && (float.IsNaN(best) || e < best) &&
                        Mathf.Abs(BackTop(track, e - 0.05f) - BackTop(track, e + 0.05f)) > 0.05f)
                        best = e;
            return best;
        }

        // ---------------------------------------------------------------- depth

        /// <summary>
        /// The land deep behind the street, so nothing past the back gardens lies empty: a far row of
        /// buildings and bands of trees for each chapter, fading into the haze toward the hills.
        /// Side streets stay open all the way back.
        /// </summary>
        static void Depth(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            if (!LevelBuildKit.HasKitModel("Buildings", "HouseGable")) return;
            var gable = ProceduralArt.FacadeKind.HouseGable;
            var longHouse = ProceduralArt.FacadeKind.HouseLong;
            var flats = ProceduralArt.FacadeKind.Apartment;
            string[] green = { "Broadleaf", "BroadleafLarge", "BroadleafWide", "ConiferMid", "ConiferTall", "Birch", "BroadleafSmall" };
            switch (LevelBuildKit.Chapter)
            {
                case 2:
                    // (The distant wood begins about 62 units back.)
                    FarRow(track, root, rng, x0, x1, 40f, 46f, flats, ProceduralArt.FacadeKind.Shop0, ProceduralArt.FacadeKind.Shop1, longHouse, gable);
                    TreeBand(track, root, rng, x0, x1, 57f, 61f, green, 5f, 10f);
                    if (CA) PalmSkyline(track, root, rng, x0, x1, 64f, 100f, 12f, 28f);
                    break;
                case 3:
                    break;   // the sea
                case 4:
                    FarRow(track, root, rng, x0, x1, 32f, 40f, ProceduralArt.FacadeKind.Warehouse, flats, ProceduralArt.FacadeKind.Warehouse);
                    TreeBand(track, root, rng, x0, x1, 54f, 64f, green, 4f, 9f);
                    if (CA) PalmSkyline(track, root, rng, x0, x1, 66f, 110f, 15f, 35f);
                    break;
                case 5:
                    TreeBand(track, root, rng, x0, x1, 44f, 62f, green, 3f, 6f);
                    if (CA) PalmSkyline(track, root, rng, x0, x1, 66f, 100f, 14f, 30f);
                    break;
                default:
                    TreeBand(track, root, rng, x0, x1, 34f, 37f, green, 5f, 10f);
                    // The next street over: stucco villas under tile roofs (the kit's gabled houses without the Coast kit).
                    if (CA) CoastFarRow(track, root, rng, x0, x1, 40f, 46f, "VillaStucco", "VillaRanch", "CraftsmanPorch", "VillaStucco");
                    else FarRow(track, root, rng, x0, x1, 40f, 46f, gable, longHouse, ProceduralArt.FacadeKind.Bungalow, gable);
                    TreeBand(track, root, rng, x0, x1, 56f, 66f, green, 4f, 8f);
                    if (CA) PalmSkyline(track, root, rng, x0, x1, 64f, 105f, 10f, 26f);
                    break;
            }
        }

        /// <summary>Where the first side street or quiet area blocking [a, b] begins (less its margin), or b if none does.</summary>
        static float BlockStart(LevelBuildKit.TrackBuilder track, float a, float b)
        {
            float start = b;
            foreach (var area in track.OpenAreas.Concat(track.QuietAreas))
                if (b > area.x - 0.6f && a < area.y + 0.6f) start = Mathf.Min(start, area.x - 0.6f);
            return Mathf.Max(a, start);
        }

        /// <summary>
        /// The leftover strip of a lot that doesn't fit before a side street, the crane's plot or the
        /// school: closed off as the chapter would (a garden wall, a market stall, the site hoarding, a
        /// hedge) rather than left as a gap.
        /// </summary>
        static void FillGap(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float a, float b)
        {
            float w = b - a;
            if (w < 0.6f) return;
            float gy = BackTop(track, (a + b) * 0.5f);
            switch (LevelBuildKit.Chapter)
            {
                case 2:
                    if (w > 2.8f) Model(root, "Street", "MarketStall", (a + b) * 0.5f, gy, PropertyZ + 0.6f, Rand(rng, -5f, 5f));
                    else Model(root, "Street", "PotC", (a + b) * 0.5f, gy, PropertyZ + 0.25f, Rand(rng, 0f, 360f));
                    break;
                case 3:
                    break;
                case 4:
                    if (!Row(root, "Street", "Hoarding3", a + 0.15f, b - 0.15f, gy, PropertyZ + 0.2f))
                        Solid(root, "Hoarding", new Vector3((a + b) * 0.5f, gy + 1.3f, PropertyZ + 0.2f), new Vector3(w - 0.3f, 2.6f, 0.2f), Color.white, Art.surfaces[ProceduralArt.Surface.Hoarding]);
                    // Behind it the lot has gone wild: a tree or two over the hoarding, not bare concrete.
                    for (float tx = a + Rand(rng, 1.4f, 2.4f); tx < b - 1.4f; tx += Rand(rng, 3.5f, 5.5f))
                        Plant(root, rng.NextDouble() < 0.7 ? "Broadleaf" : "Birch", null, tx, gy, PropertyZ + Rand(rng, 3.5f, 7f), Rand(rng, 0.8f, 1.05f), 1f, -60, rng);
                    break;
                case 5:
                    if (w > 1.2f) Row(root, "Plants", "HedgeBlock2", a + 0.3f, b - 0.3f, gy + 0.04f, PropertyZ + 0.4f, HedgeGreen);
                    break;
                default:
                    if (!(w > 1.2f && CA && Row(root, "Plants", "HedgeBlock2", a + 0.3f, b - 0.3f, gy, PropertyZ + 0.4f, HedgeGreen)))
                        BlockWall(root, a + 0.1f, b - 0.1f, gy, Art.surfaces[ProceduralArt.Surface.BlockWall], true, true);
                    if (w > 3f) Plant(root, rng.NextDouble() < 0.5 ? "Broadleaf" : "ConiferMid", null, (a + b) * 0.5f, gy, PropertyZ + 2.5f, Rand(rng, 0.8f, 1.05f), 1f, -60, rng);
                    break;
            }
        }

        /// <summary>
        /// Where the ground steps up or down inside the lot [x, x + lot]: a piece before the step too
        /// short for the lot's building (minLot) is closed off on its own level (FillGap) and x moves
        /// on to the step (true: start the next lot there); otherwise the lot is shortened to end at
        /// the step (false: build it).
        /// </summary>
        static bool LotEndsAtStep(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, ref float x, ref float lot, float minLot)
        {
            float step = StepWithin(track, x, x + lot);
            if (float.IsNaN(step)) return false;
            if (step - x < minLot)
            {
                FillGap(track, root, rng, x, step);
                x = step;
                return true;
            }
            lot = step - x;
            return false;
        }

        /// <summary>Does [a, b] run into a side street (they run 70 units back from the footpath)?</summary>
        static bool OnSideStreetRange(LevelBuildKit.TrackBuilder track, float a, float b)
        {
            if (AcrossSeam(track, a, b)) return true;
            foreach (var area in track.OpenAreas)
                if (b > area.x - 0.6f && a < area.y + 0.6f) return true;
            return false;
        }

        /// <summary>A row of buildings of the given kinds between depths zMin and zMax, with gaps between them, along the whole level.</summary>
        static void FarRow(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float zMin, float zMax, params ProceduralArt.FacadeKind[] kinds)
        {
            for (float x = Lo(x0, 40f); x < Hi(x1, 40f);)
            {
                var kind = kinds[rng.Next(kinds.Length)];
                float width = ProceduralArt.FacadeSize(kind).x;
                float step = StepWithin(track, x, x + width);
                if (!float.IsNaN(step)) { x = step + 0.5f; continue; }   // a building stands on one level
                if (!OnSideStreetRange(track, x, x + width) && (chunk == null || x + width <= x1))
                {
                    float cx = x + width * 0.5f;
                    KitBuilding(root, cx, GroundAt(track, cx), Rand(rng, zMin, zMax), kind, Mathf.Abs(Mathf.RoundToInt(cx * 7f + zMin * 13f)));
                }
                x += width + Rand(rng, 1.5f, 6f);
            }
        }

        /// <summary>A band of trees between depths zMin and zMax, every so often along the whole level.</summary>
        static void TreeBand(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, float zMin, float zMax, string[] models, float spacingMin, float spacingMax)
        {
            for (float x = Lo(x0, 40f); x < Hi(x1, 40f); x += Rand(rng, spacingMin, spacingMax))
            {
                if (OnSideStreetRange(track, x - 2f, x + 2f)) continue;
                Plant(root, models[rng.Next(models.Length)], null, x, GroundAt(track, x), Rand(rng, zMin, zMax), Rand(rng, 0.9f, 1.35f), 1f, -70, rng);
            }
        }

        /// <summary>Trees around the school: behind it, and in its grounds past the building (palms by the sea).</summary>
        static void SchoolSurroundings(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng)
        {
            float goal = track.GoalX;
            if (goal <= track.MinX || !LevelBuildKit.HasKitModel("Plants", "Broadleaf")) return;
            int ch = LevelBuildKit.Chapter;
            string[] trees = ch == 3 ? (CA ? new[] { "Palm", "PalmDate", "PalmShort", "Palm" } : new[] { "Palm", "PalmShort", "Palm" }) : new[] { "Broadleaf", "BroadleafLarge", "BroadleafWide", "ConiferMid", "Birch", "Broadleaf", "BroadleafSmall" };
            float gy = GroundAt(track, goal);
            // Behind the school (it stands 10 to 22 units past the gate, 12 deep, its 32-unit front along
            // z from -12 to 20), where the back rows leave room for it.
            for (float x = goal + 9f; x < goal + 24f && (chunk == null || x < chunk.to); x += Rand(rng, 3.5f, 5.5f))
                Plant(root, trees[rng.Next(trees.Length)], null, x, gy, Rand(rng, 22f, 27f), Rand(rng, 0.95f, 1.3f), 1f, -70, rng);
            // The school grounds beyond the building, behind the footpath.
            for (float x = goal + 26f; x < goal + 75f && (chunk == null || x < chunk.to); x += Rand(rng, 4f, 7f))
                Plant(root, trees[rng.Next(trees.Length)], null, x, gy, Rand(rng, 3.5f, 15f), Rand(rng, 0.9f, 1.2f), 1f, -65, rng);
        }

        // ---------------------------------------------------------------- animals

        static Transform critters;
        /// <summary>The kit block walls' tops (from x, to x, height), where a cat may sit.</summary>
        static readonly List<Vector3> wallTops = new List<Vector3>();

        /// <summary>
        /// An empty holder for an animal at (x, y, z) turned by yaw (models head toward +x at yaw 0),
        /// on the critters root, outside the street's static batches; its behaviour goes on the holder
        /// and the kit model(s) under it.
        /// </summary>
        static Transform Holder(string name, float x, float y, float z, float yaw)
        {
            var t = new GameObject(name).transform;
            t.SetParent(critters, false);
            t.position = new Vector3(x, y, z);
            t.rotation = Quaternion.Euler(0f, yaw, 0f);
            return t;
        }

        /// <summary>A kit animal under the holder, at its origin and turned with it (null if the kit hasn't got it).</summary>
        static Transform Animal(Transform holder, string model, float scale = 1f, Color? tint1 = null, Color? tint2 = null, Vector3 lift = default(Vector3))
        {
            var t = LevelBuildKit.KitModel(holder, "Animals", model, holder.position, 0f, scale, tint1, tint2);
            if (t == null) return null;
            t.localPosition = lift;
            t.localRotation = Quaternion.identity;
            return t;
        }

        static AmbientAgent.Part PartOf(Transform model, string name, Vector3 axis)
        {
            return new AmbientAgent.Part(model != null ? LevelBuildKit.FindDeep(model, name) : null, axis);
        }

        /// <summary>The ground span holding x, highest first (false over a gap in the footpath).</summary>
        static bool SpanAt(LevelBuildKit.TrackBuilder track, float x, out Vector3 span)
        {
            span = Vector3.zero;
            bool found = false;
            foreach (var s in track.GroundSpans)
                if (x >= s.x && x <= s.y && (!found || s.z > span.z)) { span = s; found = true; }
            return found;
        }

        /// <summary>Bakes the ground's height every step from a to b (at depth z) into the animal's strip.</summary>
        static void BakeGround(AmbientAgent agent, LevelBuildKit.TrackBuilder track, float a, float b, float z, float step, float lift = 0f)
        {
            int n = Mathf.Max(2, Mathf.CeilToInt((b - a) / step) + 1);
            var heights = new float[n];
            for (int i = 0; i < n; i++)
            {
                float x = a + i * step;
                heights[i] = (z > PathHalf && LevelBuildKit.Chapter != 3 ? BackTop(track, x) : GroundAt(track, x, z)) + lift;
            }
            agent.ground = heights;
            agent.groundFrom = a;
            agent.groundStep = step;
        }

        /// <summary>
        /// A bird on the ground (a pigeon, a standing gull) with its flying self hidden beside it
        /// (the flying gull model, in a pigeon's grey for a pigeon), ready to take off.
        /// </summary>
        static GroundBird Bird(string standingModel, float scale, float flightScale, Color? wing, Color? beak, float x, float y, float z, float yaw, System.Random rng)
        {
            var holder = Holder(standingModel, x, y, z, yaw);
            var standing = Animal(holder, standingModel, scale);
            var flying = Animal(holder, "Seagull", flightScale, wing, beak, new Vector3(0f, 0.16f * flightScale, 0f));
            if (standing == null || flying == null)
            {
                Object.DestroyImmediate(holder.gameObject);
                return null;
            }
            flying.gameObject.SetActive(false);
            var bird = holder.gameObject.AddComponent<GroundBird>();
            bird.seed = rng.Next();
            bird.standing = standing;
            bird.flying = flying;
            bird.head = PartOf(standing, "Head", Vector3.up);
            // The gull's wings flap about the body's axis, the right one with a negative angle.
            bird.wingA = PartOf(flying, "WingR", Vector3.right);
            bird.wingB = PartOf(flying, "WingL", Vector3.right);
            bird.baseY = y;
            bird.homeX = x;
            bird.homeZ = z;
            return bird;
        }

        /// <summary>
        /// The street's animals, by chapter, each going about its life (see the behaviours in
        /// World): pigeons pecking about the market and city pavements in little groups, flying up
        /// when the kid runs at them; cats on the garden walls and butterflies over the front
        /// gardens; gulls on the sand that hop about and take off, crabs scuttling at the water's
        /// edge; butterflies and squirrels on the park lawn (the squirrels make for the trees), and
        /// ducks on the pond (see ParkFeatures). Birds cross the sky in loose flocks over every
        /// chapter. Kept off the side streets and out of the kid's lane.
        /// </summary>
        static void Wildlife(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            if (!LevelBuildKit.HasKitModel("Animals", "Pigeon")) return;
            int ch = LevelBuildKit.Chapter;
            float skip;
            Color pigeonWing = new Color(0.55f, 0.58f, 0.66f), pigeonBeak = new Color(0.32f, 0.3f, 0.32f);
            switch (ch)
            {
                case 2:
                case 4:
                    for (float x = x0; x < x1; x += Rand(rng, ch == 2 ? 14f : 24f, ch == 2 ? 26f : 40f))
                    {
                        if (Blocked(track, x - 2f, x + 2f, out skip)) continue;
                        int n = rng.Next(2, 5);
                        for (int k = 0; k < n; k++)
                        {
                            float px = x + Rand(rng, -1.2f, 1.2f), pz = Rand(rng, 0.9f, 1.35f);
                            float yaw = rng.NextDouble() < 0.5 ? Rand(rng, -20f, 20f) : 180f + Rand(rng, -20f, 20f);
                            // On the footpath: only where there is footpath (not over a hole in it).
                            Vector3 span;
                            if (!SpanAt(track, px, out span)) continue;
                            var pigeon = Bird("Pigeon", 1f, 0.7f, pigeonWing, pigeonBeak, px, span.z, pz, yaw, rng);
                            if (pigeon == null) continue;
                            pigeon.roam = 0.7f;
                            pigeon.zMin = 0.85f;
                            pigeon.zMax = 1.4f;
                            pigeon.walkSpeed = Rand(rng, 0.24f, 0.4f);
                            pigeon.startle = Rand(rng, 2.2f, 3.2f);
                            pigeon.flightSpeed = Rand(rng, 3f, 4.5f);
                            // Up and out over the street, clear of the shop awnings and fronts behind.
                            pigeon.flightZMin = -0.9f;
                            pigeon.flightZMax = -0.3f;
                            // A flat strip over its stretch of footpath, so it never walks off the edge of a hole or step.
                            float a = Mathf.Max(px - 0.7f, span.x + 0.25f), b = Mathf.Min(px + 0.7f, span.y - 0.25f);
                            pigeon.ground = new[] { span.z, span.z };
                            pigeon.groundFrom = Mathf.Min(a, px);
                            pigeon.groundStep = Mathf.Max(0.01f, Mathf.Max(b, px) - pigeon.groundFrom);
                        }
                    }
                    break;
                case 3:
                    for (float x = x0; x < x1; x += Rand(rng, 9f, 18f))
                    {
                        float gx = x + Rand(rng, -1f, 1f), gz = Rand(rng, 2.6f, 5.4f);
                        float yaw = rng.NextDouble() < 0.5 ? Rand(rng, -30f, 30f) : 180f + Rand(rng, -30f, 30f);
                        var gull = Bird("SeagullStanding", 1f, 1f, null, null, gx, GroundAt(track, gx, gz), gz, yaw, rng);
                        if (gull == null) continue;
                        gull.hopper = true;
                        gull.roam = 1f;
                        gull.zMin = gz - 0.35f;
                        gull.zMax = gz + 0.35f;
                        gull.walkSpeed = Rand(rng, 0.35f, 0.5f);
                        gull.startle = Rand(rng, 3.2f, 4.2f);
                        gull.flightSpeed = Rand(rng, 4f, 5.5f);
                        BakeGround(gull, track, gx - 1.5f, gx + 1.5f, gz, 0.25f);
                    }
                    for (float x = x0 + 6f; x < x1; x += Rand(rng, 18f, 30f))
                    {
                        // A shore crab, a hand's width across.
                        float cz = Rand(rng, 6.2f, 8.2f);
                        var holder = Holder("Crab", x, GroundAt(track, x, cz), cz, Rand(rng, -20f, 20f));
                        var model = Animal(holder, "Crab", 0.5f);
                        if (model == null) { Object.DestroyImmediate(holder.gameObject); continue; }
                        var crab = holder.gameObject.AddComponent<ShoreCrab>();
                        crab.seed = rng.Next();
                        crab.model = model;
                        crab.clawL = PartOf(model, "ClawL", Vector3.up);
                        crab.clawR = PartOf(model, "ClawR", Vector3.up);
                        crab.homeX = x;
                        crab.baseY = holder.position.y;
                        crab.roam = 2.2f;
                        BakeGround(crab, track, x - 2.5f, x + 2.5f, cz, 0.25f);
                    }
                    break;
                case 5:
                    for (float x = x0; x < x1; x += Rand(rng, 8f, 16f))
                        Butterfly(rng, x, GroundAt(track, x) + Rand(rng, 0.6f, 1.6f), Rand(rng, 2.9f, 6f), 2.8f, 6.5f, 0.45f);
                    var trees = ParkTrees(root);
                    for (float x = x0 + 10f; x < x1; x += Rand(rng, 25f, 45f))
                    {
                        float sz = Rand(rng, 3.5f, 7f);
                        var holder = Holder("Squirrel", x, BackTop(track, x) + 0.04f, sz, rng.NextDouble() < 0.5 ? 10f : 170f);
                        var model = Animal(holder, "Squirrel");
                        if (model == null) { Object.DestroyImmediate(holder.gameObject); continue; }
                        var squirrel = holder.gameObject.AddComponent<TreeSquirrel>();
                        squirrel.seed = rng.Next();
                        squirrel.model = model;
                        squirrel.tail = PartOf(model, "Tail", Vector3.up);
                        squirrel.baseY = holder.position.y;
                        squirrel.homeX = x;
                        squirrel.homeZ = sz;
                        squirrel.roam = 2.5f;
                        float sx = x;
                        squirrel.trees = trees.Where(t => Mathf.Abs(t.x - sx) < 14f).ToArray();
                        BakeGround(squirrel, track, x - 16f, x + 16f, sz, 0.5f, 0.04f);
                    }
                    break;
                default:
                {
                    // Cats sitting on garden walls, swishing their tails; butterflies over the front gardens.
                    var walls = wallTops.Where(w => w.y - w.x >= 1f).Select(w => new Vector4(w.x, w.y, w.z, PropertyZ + 0.15f)).ToArray();
                    for (int i = 0; i < walls.Length; i++)
                    {
                        if (rng.NextDouble() > 0.12) continue;
                        var w = walls[i];
                        bool right = rng.NextDouble() < 0.6;
                        var holder = Holder("Cat", Rand(rng, w.x, w.y), w.z, w.w, (right ? 0f : 180f) + Rand(rng, -10f, 10f));
                        var model = Animal(holder, "Cat");
                        if (model == null) { Object.DestroyImmediate(holder.gameObject); continue; }
                        var cat = holder.gameObject.AddComponent<WallCat>();
                        cat.seed = rng.Next();
                        cat.model = model;
                        cat.tail = PartOf(model, "Tail", Vector3.up);
                        cat.walls = walls;
                        cat.wall = i;
                    }
                    for (float x = x0; x < x1; x += Rand(rng, 14f, 26f))
                    {
                        if (Blocked(track, x - 1f, x + 1f, out skip)) continue;
                        // Over the garden walls (1.6 high at PropertyZ + 0.15), never down into the footpath.
                        Butterfly(rng, x, GroundAt(track, x) + Rand(rng, 1.9f, 2.5f), PropertyZ + Rand(rng, 0.6f, 1.2f), PropertyZ + 0.45f, PropertyZ + 1.6f, 0.3f);
                    }
                    break;
                }
            }
            if (chunk == null || chunk.flocks) SkyFlocks(rng);
        }

        /// <summary>A butterfly flitting about a patch, kept between depths zMin and zMax.</summary>
        static void Butterfly(System.Random rng, float x, float y, float z, float zMin, float zMax, float rise)
        {
            var holder = Holder("Butterfly", x, y, z, Rand(rng, 0f, 360f));
            var model = Animal(holder, "Butterfly", Rand(rng, 0.45f, 0.6f));   // wings 6 to 8 cm across
            if (model == null) { Object.DestroyImmediate(holder.gameObject); return; }
            var b = holder.gameObject.AddComponent<FlitButterfly>();
            b.seed = rng.Next();
            b.wingL = PartOf(model, "WingL", Vector3.right);
            b.wingR = PartOf(model, "WingR", Vector3.right);
            b.homeX = x;
            b.homeY = y;
            b.homeZ = Mathf.Clamp(z, zMin, zMax);
            b.zMin = zMin;
            b.zMax = zMax;
            b.rise = rise;
            b.roam = Rand(rng, 2f, 3.2f);
            b.speed = Rand(rng, 0.5f, 0.85f);
        }

        /// <summary>
        /// A duck on the pond centred at (cx, cz), paddling a loop of its own (the index-th duck
        /// keeps to a line nearer the middle), or null if the kit hasn't got one.
        /// </summary>
        static PondDuck Duck(float cx, float cz, float waterY, float pondYaw, float pondScale, int index, float dx, float dz, float yaw)
        {
            if (!LevelBuildKit.HasKitModel("Animals", "Duck")) return null;
            var holder = Holder("Duck", cx + dx, waterY, cz + dz, yaw);
            var model = Animal(holder, "Duck");
            if (model == null) { Object.DestroyImmediate(holder.gameObject); return null; }
            var duck = holder.gameObject.AddComponent<PondDuck>();
            duck.seed = Mathf.Abs(Mathf.RoundToInt(cx * 31f)) + index * 7 + 1;
            duck.head = PartOf(model, "Head", Vector3.up);
            duck.centerX = cx;
            duck.centerZ = cz;
            duck.waterY = waterY;
            duck.pondYaw = pondYaw;
            // The pond's water is about 1.85 by 1.15 (times its scale) from the middle to the edge.
            float band = Mathf.Max(0.3f, 0.62f - index * 0.13f);
            duck.radiusX = 1.85f * pondScale * band;
            duck.radiusZ = 1.15f * pondScale * band * 0.92f;
            return duck;
        }

        static readonly string[] SquirrelTrees ={ "Broadleaf", "BroadleafLarge", "BroadleafWide", "BroadleafSmall", "Birch", "CherryBlossom" };

        /// <summary>The park's trees a squirrel can run up: (x, ground, z, trunk radius), from the trees already planted.</summary>
        static List<Vector4> ParkTrees(Transform root)
        {
            var list = new List<Vector4>();
            for (int i = 0; i < root.childCount; i++)
            {
                var t = root.GetChild(i);
                if (System.Array.IndexOf(SquirrelTrees, t.name) < 0) continue;
                Vector3 p = t.position;
                if (p.z < 5.5f || p.z > 17f) continue;
                float radius = 0.2f;
                var info = LevelBuildKit.KitInfo("Plants", t.name);
                object r;
                if (info != null && info.TryGetValue("trunkRadius", out r)) radius = System.Convert.ToSingle(r);
                list.Add(new Vector4(p.x, p.y, p.z, radius * t.localScale.x));
            }
            return list;
        }

        /// <summary>
        /// Birds crossing the sky now and then, in loose flocks, coming in from one side of the view
        /// and leaving by the other: gulls over the beach, pigeons (and a few crows) over the town and
        /// the park.
        /// </summary>
        static void SkyFlocks(System.Random rng)
        {
            int ch = LevelBuildKit.Chapter;
            if (ch == 3)
            {
                Flock("GullFlock", rng, Rand(rng, 3f, 6f), 1f, null, null, 6f, 20f, 0.25f, 0.7f, 3f, 5f, 4f, 14f, 1.6f);
                Flock("GullFlock", rng, Rand(rng, 2f, 4f), 1f, null, null, 12f, 28f, 0.45f, 0.85f, 2.5f, 4f, 8f, 20f, 1.8f);
                return;
            }
            // Over the footpath and the road, in front of the shopfronts and houses (they start at
            // PropertyZ), the poles' wires and the park's trees, high in the view.
            Color pigeon = new Color(0.55f, 0.58f, 0.66f), crow = new Color(0.2f, 0.2f, 0.24f), beak = new Color(0.3f, 0.28f, 0.3f);
            bool park = ch == 5;
            Flock("PigeonFlock", rng, Rand(rng, 4f, 7f), 0.7f, pigeon, beak, park ? 1f : -1.2f, park ? 3f : 1.2f, 0.6f, 0.88f, 4f, 6.5f, 6f, 18f, 0.9f);
            Flock("CrowFlock", rng, Rand(rng, 2f, 4f), 0.85f, crow, crow, park ? 1.5f : -0.8f, park ? 3.5f : 1.4f, 0.68f, 0.92f, 3f, 4.5f, 12f, 28f, 1.3f);
        }

        static void Flock(string name, System.Random rng, float birds, float scale, Color? wing, Color? beak, float zMin, float zMax,
            float heightMin, float heightMax, float speedMin, float speedMax, float gapMin, float gapMax, float spacing)
        {
            if (!LevelBuildKit.HasKitModel("Animals", "Seagull")) return;
            var root = new GameObject(name).transform;
            root.SetParent(critters, false);
            int n = Mathf.Max(1, Mathf.RoundToInt(birds));
            var models = new List<Transform>();
            var wings = new List<AmbientAgent.Part>();
            for (int i = 0; i < n; i++)
            {
                var bird = LevelBuildKit.KitModel(root, "Animals", "Seagull", new Vector3(0f, -100f, 0f), 0f, scale * Rand(rng, 0.9f, 1.1f), wing, beak, null, false);
                if (bird == null) continue;
                bird.gameObject.SetActive(false);
                models.Add(bird);
                wings.Add(PartOf(bird, "WingR", Vector3.right));
                wings.Add(PartOf(bird, "WingL", Vector3.right));
            }
            if (models.Count == 0) { Object.DestroyImmediate(root.gameObject); return; }
            var flock = root.gameObject.AddComponent<SkyFlock>();
            flock.seed = rng.Next();
            flock.birds = models.ToArray();
            flock.wings = wings.ToArray();
            flock.zMin = zMin;
            flock.zMax = zMax;
            flock.heightMin = heightMin;
            flock.heightMax = heightMax;
            flock.speedMin = speedMin;
            flock.speedMax = speedMax;
            flock.gapMin = gapMin;
            flock.gapMax = gapMax;
            flock.spacing = spacing;
        }

        static void Poles(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            // No overhead lines in the park, or over the market's shopfronts (it has its own lamps).
            if (LevelBuildKit.Chapter == 5 || (LevelBuildKit.Chapter == 2 && LevelBuildKit.HasKitModel("Buildings", "ShopFruit"))) return;
            if (chunk != null) { PolesForStage(track, root, x0, x1); return; }
            var go = new GameObject("PoleLine");
            go.transform.SetParent(root, false);
            var line = go.AddComponent<PoleLine3D>();
            line.wireMaterial = Art.wire;
            bool models = LevelBuildKit.HasKitModel("Street", "UtilityPole");
            for (float x = x0; x < x1; x += 21f)
            {
                float skip;
                if (Blocked(track, x - 0.5f, x + 0.5f, out skip)) continue;
                var pole = new Vector3(x, GroundAt(track, x), PoleZ);
                line.poles.Add(pole);
                if (!models) continue;
                // The kit's concrete pole, turned side-on so its crossarm runs across the street like a
                // real line's; the wires hang from its insulators.
                var model = Model(go.transform, "Street", PoleModel, pole.x, pole.y, pole.z, PoleYaw);
                if (model == null || line.anchorOffsets.Count > 0) continue;
                foreach (var t in model.GetComponentsInChildren<Transform>())
                    if (t.name.StartsWith("Attach.Wire") || t.name.StartsWith("Attach_Wire"))
                        line.anchorOffsets.Add(t.position - pole);
            }
            line.drawPoles = !models;
            go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            line.Rebuild();

            // Street lamps halfway between the poles (the swan neck reads from the side), a bin by some.
            if (!LevelBuildKit.HasKitModel("Street", "StreetLamp")) return;
            var rng = new System.Random(LevelBuildKit.Chapter * 53 + Mathf.RoundToInt(x0));
            for (float x = x0 + 10.5f; x < x1; x += 21f)
            {
                float skip;
                if (Blocked(track, x - 1.5f, x + 1.5f, out skip)) continue;
                float gy = GroundAt(track, x);
                Model(root, "Street", "StreetLamp", x, gy, PoleZ);
                if (rng.NextDouble() < 0.45) Model(root, "Street", "Bin", x + 0.7f, gy, PoleZ + 0.05f, Rand(rng, -10f, 10f));
            }
        }

        /// <summary>The utility pole model's turn: its crossarm (along the model's width) runs across the street, in depth.</summary>
        const float PoleYaw = 90f;

        static void Suburb(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            var wallMat = Art.surfaces[ProceduralArt.Surface.BlockWall];
            Color roofDark = new Color(0.34f, 0.37f, 0.44f), roofRed = new Color(0.7f, 0.36f, 0.3f);
            var houses = new Deck(HomeHouses, rng);
            for (float x = x0; x < x1;)
            {
                float lot = CA ? NextLot(track, rng, x, x1, 12.9f, 15f) : NextLot(track, rng, x, x1, 9f, 13f), skip;   // (every Coast house fits: the villas are 12 wide)
                if (Blocked(track, x, x + lot, out skip)) { FillGap(track, root, rng, x, BlockStart(track, x, x + lot)); x = skip; continue; }
                // The last scrap of a run (too small for a house) is closed off like any gap.
                if (chunk != null && lot < 7.5f) { FillGap(track, root, rng, x, x + lot); x += lot; continue; }
                int mix = TransitionStyle(x, lot);
                if (mix != 0) { ThemeLot(track, root, rng, mix, x, x + lot); x += lot; continue; }
                if (LotEndsAtStep(track, root, rng, ref x, ref lot, 7.5f)) continue;
                float cx = x + lot * 0.5f, gy = GroundAt(track, cx);

                // Block wall along the front of the lot with a gap for the gate; a white picket fence
                // round some front gardens instead. (California: a picket fence with a gate, a low
                // clipped hedge, or an open lawn running down to the pavement.)
                float gate = Rand(rng, x + 2f, x + lot - 4f);
                double front = rng.NextDouble();
                bool picket = front < (CA ? 0.35 : 0.3) && LevelBuildKit.HasKitModel("Street", "PicketFence2");
                bool hedge = CA && !picket && front < 0.65 && LevelBuildKit.HasKitModel("Plants", "HedgeBlock2");
                if (picket)
                {
                    ContactShadow(root, x + 0.1f, x + lot - 0.1f, gy, PropertyZ - 0.25f, PropertyZ + 0.02f);
                    Row(root, "Street", "PicketFence2", x + 0.1f, gate, gy, PropertyZ + 0.15f);
                    Row(root, "Street", "PicketFence2", gate + 1.4f, x + lot - 0.1f, gy, PropertyZ + 0.15f);
                }
                else if (hedge)
                {
                    if (gate - x > 1.6f) Row(root, "Plants", "HedgeBlock2", x + 0.3f, gate - 0.2f, gy, PropertyZ + 0.4f, HedgeGreen);
                    if (x + lot - gate > 3.6f) Row(root, "Plants", "HedgeBlock2", gate + 1.6f, x + lot - 0.3f, gy, PropertyZ + 0.4f, HedgeGreen);
                }
                else if (!CA)
                {
                    BlockWall(root, x + 0.1f, gate, gy, wallMat, true, true);
                    BlockWall(root, gate + 2.2f, x + lot - 0.1f, gy, wallMat, true, false);
                }
                // Now and then a post box at the kerb of the lot, or a bicycle leaning on the wall.
                double life = rng.NextDouble();
                if (life < 0.12) Model(root, "Street", "PostBox", x + Rand(rng, 1f, lot - 1f), gy, PoleZ - 0.1f);
                else if (life < 0.3 && !picket && !hedge && gate - x > 3.4f) Model(root, "Street", "Bicycle", Rand(rng, x + 1.2f, gate - 1f), gy, PropertyZ - 0.32f, 180f + Rand(rng, -6f, 6f), 1f, BikeColors[rng.Next(BikeColors.Length)]);

                // The house: the next of the home street's houses that fits the lot (with no kit, one of
                // the three painted kinds).
                string house = houses.Next(m => LevelBuildKit.KitSize(KitOf(m), m).x <= lot - 0.8f);
                int kind = rng.Next(3);
                float z = PropertyZ + 1.6f + Rand(rng, 0f, 1.4f) + (house == "HouseLeanTo" ? 0.3f : 0f) + CoastSetback(house);
                Color roof = rng.NextDouble() < 0.75 ? roofDark : roofRed;
                var facade = kind == 0 ? ProceduralArt.FacadeKind.HouseGable : kind == 1 && lot >= 11f ? ProceduralArt.FacadeKind.HouseLong : ProceduralArt.FacadeKind.Bungalow;
                if (house == "HouseGable") facade = ProceduralArt.FacadeKind.HouseGable;
                else if (house == "HouseLong") facade = ProceduralArt.FacadeKind.HouseLong;
                else if (house == "Bungalow") facade = ProceduralArt.FacadeKind.Bungalow;
                bool town = house != null && TownHouse(root, house, cx, gy, z);
                if (!town)
                {
                    if (facade == ProceduralArt.FacadeKind.HouseGable) Building(root, cx, gy, z, facade, House3D.RoofStyle.GableToStreet, 7f, 2.6f, new Color(0.95f, 0.94f, 0.9f), roof);
                    else if (facade == ProceduralArt.FacadeKind.HouseLong) Building(root, cx, gy, z, facade, House3D.RoofStyle.GableSideways, 7f, 2.4f, new Color(0.93f, 0.91f, 0.86f), roof);
                    else Building(root, cx, gy, z, facade, House3D.RoofStyle.Shed, 5.5f, 1f, new Color(0.88f, 0.89f, 0.9f), roofDark);
                }
                float houseHalf = (town ? LevelBuildKit.KitSize(KitOf(house), house).x : ProceduralArt.FacadeSize(facade).x) * 0.5f;

                // Life at the gate: the bins out for collection or a doorstep of pots; garden shrubs over
                // the block wall; a bicycle under the carport.
                if (LevelBuildKit.HasKitModel("Street", "BinPair"))
                {
                    double d = rng.NextDouble();
                    if (d < 0.3 && !picket)
                        Model(root, "Street", "BinPair", gate + 1.1f, gy, PropertyZ + 0.55f, Rand(rng, -10f, 10f), 1f, BinColors[rng.Next(BinColors.Length)], BinColors[rng.Next(BinColors.Length)]);
                    else if (d < 0.55)
                        Model(root, "Street", "PotGroup", gate + 0.55f, gy, PropertyZ + 0.6f, Rand(rng, -20f, 20f), 1f, Petals[rng.Next(Petals.Length)]);
                }
                float yard = x + lot - (cx + houseHalf);
                if (!picket && yard > 1.2f && rng.NextDouble() < 0.6 && LevelBuildKit.HasKitModel("Plants", "BushRound"))
                    Plant(root, rng.NextDouble() < 0.5 ? "BushRound" : "ShrubFlowering", null, x + lot - yard * 0.5f, gy, PropertyZ + 1.35f, Rand(rng, 1.3f, 1.6f), 1f, -60, rng);
                if (house == "HouseCarport" && town && rng.NextDouble() < 0.8)
                    Model(root, "Street", "Bicycle", cx + 3.4f, gy, z + 1.3f, 180f + Rand(rng, -5f, 5f), 1f, BikeColors[rng.Next(BikeColors.Length)]);

                if (LevelBuildKit.HasKitModel("Plants", "Broadleaf"))
                {
                    // Trees in the back garden rise over the roof; a slim one stands in the side yard
                    // when the gap beside the house is wide enough for it.
                    if (rng.NextDouble() < 0.7)
                    {
                        string[] back = CA ? new[] { "Broadleaf", "PalmDate", "BroadleafLarge", "PalmFan", "BroadleafWide", "Broadleaf", "PalmDate", "BroadleafSmall" }
                            : new[] { "Broadleaf", "BroadleafLarge", "BroadleafWide", "ConiferTall", "Broadleaf", "Birch", "BroadleafSmall" };
                        string tree = back[rng.Next(back.Length)];
                        // (A fan palm this close is a young one: a grown one's crown would stand out of the view.)
                        // (The draws in the original order, so the original street comes out as it was.)
                        float tx = cx + Rand(rng, -houseHalf, houseHalf), tz = z + 8f + Rand(rng, 0f, 3f);
                        float ts = tree == "PalmFan" ? Rand(rng, 0.45f, 0.55f) : Rand(rng, 0.9f, 1.25f);
                        Plant(root, tree, null, tx, gy, tz, ts, 1f, -70, rng);
                    }
                    float gap = (cx - houseHalf) - x;
                    if (gap > 4f && house != "HouseCarport" && !CoastModels.Contains(house ?? "") && rng.NextDouble() < 0.4 && LevelBuildKit.HasKitModel("Buildings", "Garage"))
                    {
                        // A garage beside the house, set back a little, painted to match it.
                        var p = HousePaints[Scramble(Mathf.Abs(Mathf.RoundToInt(cx * 7f + z * 13f)) + 1) % HousePaints.Length];
                        Model(root, "Buildings", "Garage", x + gap * 0.5f, gy, z + 0.8f, 0f, 1f, p.wall, p.trim, p.roof);
                    }
                    else if (gap > 1.8f && rng.NextDouble() < 0.6)
                    {
                        string[] side = CA ? new[] { "PalmDate", "ShrubFlowering", "BroadleafYoung", "PalmDate", "ConiferSmall", "BushWide" }
                            : new[] { "Birch", "ConiferSmall", "GardenPine", "ConiferMid", "ShrubFlowering", "BroadleafYoung" };
                        string model = side[rng.Next(side.Length)];
                        float sz = PropertyZ + 1.4f + Rand(rng, 0f, 1.2f);
                        float ss = model == "ShrubFlowering" || model == "BushWide" ? Rand(rng, 1.3f, 1.6f) : model == "PalmDate" ? Rand(rng, 0.55f, 0.72f) : Rand(rng, 0.7f, 0.95f);
                        Plant(root, model, null, x + gap * 0.5f, gy, sz, ss, 1f, -60, rng);
                    }
                }
                else
                {
                    // Garden trees behind the wall, and the odd big tree further back.
                    if (rng.NextDouble() < 0.6)
                    {
                        bool pine = rng.NextDouble() < 0.4;
                        CutOut(root, pine ? "Pine" : "Tree", pine ? Art.pine : Art.mid[5, 2], x + Rand(rng, 0.5f, 2f), gy, PropertyZ + 0.9f, pine ? 0.75f : Rand(rng, 0.7f, 0.9f), -60, rng.NextDouble() < 0.5);
                    }
                    if (rng.NextDouble() < 0.35)
                        CutOut(root, "BigTree", Art.mid[5, rng.NextDouble() < 0.15 ? 1 : 2], cx + Rand(rng, -2f, 2f), gy, z + 9f, Rand(rng, 1.1f, 1.4f), -70);
                }
                x += lot;
            }
            // Palms in the front gardens, every couple of lots.
            if (CA) StreetPalms(track, root, rng, x0, x1, PropertyZ + 0.95f, 12f, 26f);
            // A second row of houses further back gives the street depth (never on a side street).
            var backRow = new Deck(CA ? new[] { "VillaStucco", "VillaRanch", "CraftsmanPorch", "VillaStucco", "VillaRanch" }
                : new[] { "HouseGable", "HouseLong", "HouseLeanTo", "HouseFlat" }, rng);
            for (float x = Lo(x0, 20f); x < Hi(x1, 20f); x += Rand(rng, 10f, 14f))
            {
                string house = backRow.Next(m => true);
                var facade = rng.NextDouble() < 0.5 ? ProceduralArt.FacadeKind.HouseGable : ProceduralArt.FacadeKind.HouseLong;
                var roofStyle = rng.NextDouble() < 0.5 ? House3D.RoofStyle.GableToStreet : House3D.RoofStyle.GableSideways;
                float bz = Rand(rng, 20f, 24f);
                if (house == "HouseLeanTo" || house == "HouseFlat" || CoastModels.Contains(house))
                {
                    float half = LevelBuildKit.KitSize(KitOf(house), house).x * 0.5f + 0.3f;
                    if (!OverlapsBackRow(track, x - half, x + half)) TownHouse(root, house, x, GroundAt(track, x), bz);
                    continue;
                }
                if (house == "HouseGable") facade = ProceduralArt.FacadeKind.HouseGable;
                else if (house == "HouseLong") facade = ProceduralArt.FacadeKind.HouseLong;
                if (OnSideStreet(track, x, facade)) continue;
                Building(root, x, GroundAt(track, x), bz, facade, roofStyle, 7f, 2.4f, new Color(0.93f, 0.93f, 0.9f), roofDark);
            }
            DistantHills(track, root, x0, x1);
        }

        static readonly Color[] BikeColors = { new Color(0.52f, 0.72f, 0.68f), new Color(0.86f, 0.42f, 0.36f), new Color(0.95f, 0.8f, 0.35f), new Color(0.4f, 0.5f, 0.72f) };

        /// <summary>A block wall along the front of a lot from a to b, with a square pillar at either end if asked (kit models only).</summary>
        static void BlockWall(Transform root, float a, float b, float gy, Material mat, bool pillarA, bool pillarB)
        {
            if (b - a < 0.4f) return;
            ContactShadow(root, a, b, gy, PropertyZ - 0.35f, PropertyZ + 0.02f);
            if (Row(root, "Street", "BlockWall2", a, b, gy, PropertyZ + 0.15f))
            {
                wallTops.Add(new Vector3(a + 0.4f, b - 0.4f, gy + 1.6f));
                // Square pillars at the gate and where the lot begins.
                if (pillarA) Model(root, "Street", "WallPillar", a, gy, PropertyZ + 0.15f);
                if (pillarB) Model(root, "Street", "WallPillar", b, gy, PropertyZ + 0.15f);
                return;
            }
            Solid(root, "BlockWall", new Vector3((a + b) * 0.5f, gy + 0.8f, PropertyZ + 0.15f), new Vector3(b - a, 1.6f, 0.25f), Color.white, mat);
            Solid(root, "WallCap", new Vector3((a + b) * 0.5f, gy + 1.63f, PropertyZ + 0.15f), new Vector3(b - a + 0.04f, 0.06f, 0.3f), new Color(0.82f, 0.82f, 0.8f));
        }

        // ---------------------------------------------------------------- the town's shops and houses

        /// <summary>The shopping street's fronts (Buildings kit), dealt from a shuffled deck.</summary>
        static string[] MarketFronts { get { return CA ? MarketFrontsCA : MarketFrontsTown; } }
        static readonly string[] MarketFrontsTown = { "ShopFruit", "ShopShutter", "ShopMart", "ShopCafe", "ShopBooks", "ShopFlorist", "ShopNoodle", "ShopTall", "ShopBoutique", "ShopKonbini" };
        /// <summary>The California skin's: beach-town and Mission shops among the kit's.</summary>
        static readonly string[] MarketFrontsCA = { "ShopFruit", "ShopBeach", "ShopShutter", "ShopMission", "ShopMart", "ShopCafe", "ShopBeach", "ShopBooks", "ShopFlorist", "ShopMission", "ShopTall", "ShopBoutique" };
        /// <summary>The home street's houses (HouseLong and HouseCarport want the wider lots).</summary>
        static string[] HomeHouses { get { return CA ? HomeHousesCA : HomeHousesTown; } }
        static readonly string[] HomeHousesTown = { "HouseGable", "HouseLong", "Bungalow", "HouseLeanTo", "HouseFlat", "HouseCarport" };
        /// <summary>The California skin's: stucco villas, ranch houses and Craftsman porches (the villas want the wider lots).</summary>
        static readonly string[] HomeHousesCA = { "VillaStucco", "CraftsmanPorch", "VillaRanch", "VillaStucco", "CraftsmanPorch", "VillaRanch" };

        /// <summary>
        /// Deals kit models from a shuffled deck: each turns up once before any comes round again, the
        /// same one never twice in a row, and only those that fit (and that the kit has).
        /// </summary>
        class Deck
        {
            readonly string[] models;
            readonly System.Random rng;
            readonly List<string> left = new List<string>();
            string last;

            public Deck(string[] models, System.Random rng) { this.models = models; this.rng = rng; }

            public string Next(System.Func<string, bool> fits)
            {
                for (int pass = 0; pass < 2; pass++)
                {
                    if (pass == 1 || left.Count == 0) Refill();
                    for (int i = 0; i < left.Count; i++)
                    {
                        string m = left[i];
                        if (m == last || !fits(m)) continue;
                        left.RemoveAt(i);
                        last = m;
                        return m;
                    }
                }
                return null;
            }

            void Refill()
            {
                left.Clear();
                foreach (var m in models)
                    if (LevelBuildKit.HasKitModel(KitOf(m), m)) left.Add(m);
                for (int i = left.Count - 1; i > 0; i--)
                {
                    int j = rng.Next(i + 1);
                    var t = left[i]; left[i] = left[j]; left[j] = t;
                }
            }
        }

        // Paint schemes for the town's fronts (wall, trim / awning / shutter, roof), chosen to sit with
        // each shop's own sign: mostly white, grey and stucco walls, tiled cladding in quiet tones (and
        // the odd dark one), colour in the awning, door or shutter.
        static readonly Color ShopRoof = new Color(0.56f, 0.57f, 0.6f);
        static readonly Dictionary<string, Paint[]> FrontPaints = new Dictionary<string, Paint[]>
        {
            { "ShopMart", new[] {
                new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.84f, 0.26f, 0.2f), ShopRoof),
                new Paint(new Color(0.93f, 0.91f, 0.86f), new Color(0.93f, 0.55f, 0.18f), ShopRoof),
                new Paint(new Color(0.86f, 0.87f, 0.87f), new Color(0.2f, 0.42f, 0.72f), ShopRoof),
                new Paint(new Color(0.94f, 0.92f, 0.87f), new Color(0.96f, 0.76f, 0.2f), ShopRoof) } },
            { "ShopCafe", new[] {
                new Paint(new Color(0.94f, 0.93f, 0.9f), new Color(0.22f, 0.4f, 0.42f), ShopRoof),
                new Paint(new Color(0.9f, 0.88f, 0.84f), new Color(0.2f, 0.26f, 0.4f), ShopRoof),
                new Paint(new Color(0.92f, 0.9f, 0.86f), new Color(0.5f, 0.2f, 0.22f), ShopRoof),
                new Paint(new Color(0.86f, 0.87f, 0.86f), new Color(0.42f, 0.46f, 0.28f), ShopRoof) } },
            { "ShopBooks", new[] {
                new Paint(new Color(0.8f, 0.62f, 0.52f), new Color(0.18f, 0.36f, 0.3f), ShopRoof),
                new Paint(new Color(0.84f, 0.8f, 0.72f), new Color(0.2f, 0.27f, 0.42f), ShopRoof),
                new Paint(new Color(0.68f, 0.52f, 0.44f), new Color(0.2f, 0.34f, 0.3f), ShopRoof),
                new Paint(new Color(0.8f, 0.8f, 0.78f), new Color(0.46f, 0.18f, 0.18f), ShopRoof) } },
            { "ShopFlorist", new[] {
                new Paint(new Color(0.95f, 0.94f, 0.9f), new Color(0.34f, 0.55f, 0.37f), ShopRoof),
                new Paint(new Color(0.9f, 0.9f, 0.88f), new Color(0.52f, 0.62f, 0.5f), ShopRoof),
                new Paint(new Color(0.94f, 0.92f, 0.87f), new Color(0.4f, 0.58f, 0.74f), ShopRoof),
                new Paint(new Color(0.88f, 0.89f, 0.9f), new Color(0.74f, 0.42f, 0.32f), ShopRoof) } },
            { "ShopNoodle", new[] {
                new Paint(new Color(0.93f, 0.9f, 0.84f), new Color(0.3f, 0.22f, 0.18f), ShopRoof),
                new Paint(new Color(0.95f, 0.95f, 0.93f), new Color(0.3f, 0.22f, 0.18f), ShopRoof),
                new Paint(new Color(0.84f, 0.85f, 0.86f), new Color(0.3f, 0.22f, 0.18f), ShopRoof) } },
            { "ShopTall", new[] {
                new Paint(new Color(0.84f, 0.82f, 0.78f), new Color(0.62f, 0.64f, 0.66f), ShopRoof),
                new Paint(new Color(0.9f, 0.9f, 0.89f), new Color(0.72f, 0.73f, 0.72f), ShopRoof),
                new Paint(new Color(0.32f, 0.34f, 0.4f), new Color(0.66f, 0.68f, 0.7f), ShopRoof),
                new Paint(new Color(0.66f, 0.56f, 0.48f), new Color(0.6f, 0.62f, 0.6f), ShopRoof),
                new Paint(new Color(0.78f, 0.81f, 0.84f), new Color(0.5f, 0.58f, 0.54f), ShopRoof) } },
            { "ShopBoutique", new[] {
                new Paint(new Color(0.26f, 0.28f, 0.33f), new Color(0.3f, 0.31f, 0.33f), ShopRoof),
                new Paint(new Color(0.36f, 0.31f, 0.28f), new Color(0.3f, 0.31f, 0.33f), ShopRoof),
                new Paint(new Color(0.3f, 0.35f, 0.34f), new Color(0.62f, 0.64f, 0.66f), ShopRoof),
                new Paint(new Color(0.56f, 0.54f, 0.51f), new Color(0.3f, 0.31f, 0.33f), ShopRoof) } },
            { "ShopKonbini", new[] {
                new Paint(new Color(0.95f, 0.95f, 0.94f), new Color(0.62f, 0.66f, 0.7f), ShopRoof),
                new Paint(new Color(0.88f, 0.89f, 0.9f), new Color(0.62f, 0.66f, 0.7f), ShopRoof) } },
        };

        /// <summary>A paint scheme for a kit model, by its own schemes if it has any, else from the fallback set.</summary>
        static Paint PaintFor(string model, Paint[] fallback, float x, float z)
        {
            Paint[] schemes;
            if (!FrontPaints.TryGetValue(model, out schemes)) schemes = fallback;
            return schemes[Scramble(Mathf.Abs(Mathf.RoundToInt(x * 7f + z * 13f))) % schemes.Length];
        }

        static readonly Color[] BannerColors =
        {
            new Color(0.84f, 0.28f, 0.22f), new Color(0.24f, 0.42f, 0.72f), new Color(0.26f, 0.54f, 0.36f), new Color(0.94f, 0.55f, 0.2f),
        };
        static readonly Color[] BannerBands = { new Color(0.98f, 0.82f, 0.3f), new Color(0.96f, 0.95f, 0.92f) };
        static readonly Color[] CrateColors =
        {
            new Color(0.93f, 0.74f, 0.26f), new Color(0.3f, 0.5f, 0.74f), new Color(0.36f, 0.6f, 0.42f), new Color(0.84f, 0.3f, 0.26f),
        };
        static readonly Color[] BinColors =
        {
            new Color(0.32f, 0.5f, 0.4f), new Color(0.36f, 0.46f, 0.6f), new Color(0.46f, 0.48f, 0.5f), new Color(0.26f, 0.38f, 0.3f),
        };

        /// <summary>A standing shop banner on the footpath's back edge, clear of the kid's lane.</summary>
        static void Banner(Transform root, System.Random rng, float x, float gy)
        {
            Model(root, "Street", "BannerFlag", x, gy, PoleZ + 0.3f, Rand(rng, -6f, 6f), 1f, BannerColors[rng.Next(BannerColors.Length)], BannerBands[rng.Next(BannerBands.Length)]);
        }

        /// <summary>
        /// One of the town's shop fronts, centred on cx, with what stands outside it: crates and banners
        /// at the supermarket, pavement boards at the cafe, bookshop and noodle house, an electrical
        /// cabinet and a bicycle at the narrow tiled building, drinks machines and bicycles on the
        /// convenience store's apron. False if the kit hasn't got the model.
        /// </summary>
        static bool ShopFront(Transform root, System.Random rng, string model, float cx, float gy, float w)
        {
            if (CoastModels.Contains(model)) return CoastHouse(root, model, cx, gy, PropertyZ + 0.6f);
            float z = PropertyZ + (model == "ShopKonbini" ? 2.6f : 0.6f);
            var p = PaintFor(model, ShopPaints, cx, z);
            if (Model(root, "Buildings", model, cx, gy, z, 0f, 1f, p.wall, p.trim, p.roof) == null) return false;
            ContactShadow(root, cx - w * 0.5f, cx + w * 0.5f, gy, z - 0.45f, z);
            float board = PropertyZ + 0.02f;
            switch (model)
            {
                case "ShopMart":
                    Model(root, "Street", "DrinksCrates", cx + 3.55f, gy, PropertyZ + 0.32f, Rand(rng, -8f, 8f), 1f, CrateColors[rng.Next(CrateColors.Length)]);
                    if (rng.NextDouble() < 0.5) Model(root, "Street", "CrateStack", cx - 3.1f, gy, PropertyZ + 0.35f, Rand(rng, -10f, 10f));
                    Banner(root, rng, cx - 2.4f, gy);
                    Banner(root, rng, cx + 2.2f, gy);
                    break;
                case "ShopCafe":
                    Model(root, "Street", "SignBoardA", cx + 0.75f, gy, board, Rand(rng, -15f, 15f), 1f, new Color(0.3f, 0.26f, 0.22f));
                    break;
                case "ShopBooks":
                    Model(root, "Street", "SignBoardA", cx - 1.7f, gy, board, Rand(rng, -15f, 15f), 1f, new Color(0.2f, 0.3f, 0.26f));
                    break;
                case "ShopNoodle":
                    Model(root, "Street", "SignBoardA", cx + 0.1f, gy, board, 180f + Rand(rng, -15f, 15f), 1f, new Color(0.3f, 0.22f, 0.18f));
                    Banner(root, rng, cx + 2.75f, gy);
                    break;
                case "ShopTall":
                    Model(root, "Street", "UtilityBox", cx - 0.5f, gy, z - 0.32f, 0f);
                    if (rng.NextDouble() < 0.5)
                        Model(root, "Street", "Bicycle", cx + 1.35f, gy, z - 0.45f, 180f + Rand(rng, -6f, 6f), 1f, BikeColors[rng.Next(BikeColors.Length)]);
                    break;
                case "ShopBoutique":
                    Banner(root, rng, cx - 2.15f, gy);
                    if (rng.NextDouble() < 0.5) Model(root, "Street", "PotGroup", cx + 1.4f, gy, z - 0.55f, Rand(rng, -20f, 20f), 1f, Petals[rng.Next(Petals.Length)]);
                    break;
                case "ShopKonbini":
                    Model(root, "Street", "VendingRed", cx - 4.1f, gy, z - 0.45f);
                    Model(root, "Street", "VendingBlue", cx - 3.05f, gy, z - 0.45f);
                    if (Model(root, "Street", "BikeRack", cx - 0.9f, gy, z - 1.2f) != null)
                        for (int k = 0; k < 3; k++)
                            if (rng.NextDouble() < 0.6)
                                Model(root, "Street", "Bicycle", cx - 1.8f + 0.9f * k + 0.25f, gy, z - 1.15f - 0.08f * k, 180f + Rand(rng, -5f, 5f), 1f, BikeColors[rng.Next(BikeColors.Length)]);
                    break;
            }
            return true;
        }

        /// <summary>
        /// One of the town's kit houses (HouseLeanTo, HouseFlat, HouseCarport) with its front wall on z,
        /// in a house scheme, with its contact shadow. False for the painted kinds (Building places
        /// those) or if the kit hasn't got it.
        /// </summary>
        static bool TownHouse(Transform root, string model, float x, float gy, float z)
        {
            if (CoastModels.Contains(model)) return CoastHouse(root, model, x, gy, z);
            if (model == "HouseGable" || model == "HouseLong" || model == "Bungalow") return false;
            float w = LevelBuildKit.KitSize("Buildings", model).x;
            var p = PaintFor(model, HousePaints, x, z);
            if (w < 1f || Model(root, "Buildings", model, x, gy, z, 0f, 1f, p.wall, p.trim, p.roof) == null) return false;
            ContactShadow(root, x - w * 0.5f, x + w * 0.5f, gy, z - 0.45f, z);
            return true;
        }

        static void Market(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            Color[] awnings = { new Color(0.25f, 0.45f, 0.75f), new Color(0.78f, 0.25f, 0.25f), new Color(0.3f, 0.6f, 0.4f) };
            var deck = new Deck(MarketFronts, rng);
            bool vended = false;
            int i = 0;
            for (float x = x0; x < x1; i++)
            {
                // The next front from the deck at its own width; the old pair of painted shops without the kit.
                // (In a Holiday Run stage it has to fit what is left before the side street or the stage's end.)
                float runEnd = chunk != null ? RunEnd(track, x, x1) : x1;
                string front = deck.Next(m => chunk == null || LevelBuildKit.KitSize(KitOf(m), m).x <= runEnd - x + 0.01f);
                float w = front != null ? LevelBuildKit.KitSize(KitOf(front), front).x : 0f, skip;
                if (chunk != null && front == null && LevelBuildKit.HasKitModel("Buildings", "ShopFruit"))
                {
                    // Nothing fits the rest of the run: close it off and go on past the side street.
                    FillGap(track, root, rng, x, runEnd);
                    x = Mathf.Max(runEnd, x + 0.05f);
                    continue;
                }
                if (w < 1f) { front = null; w = 8f; }
                if (Blocked(track, x, x + w, out skip)) { FillGap(track, root, rng, x, BlockStart(track, x, x + w)); x = skip; continue; }
                int mix = front != null ? TransitionStyle(x, w) : 0;
                if (mix != 0) { ThemeLot(track, root, rng, mix, x, x + w); x += w; continue; }
                // A shopfront stands on one level: where the ground steps inside it, the piece before
                // the step gets a stall or pots on its own level and the next front starts at the step.
                float step = StepWithin(track, x, x + w);
                if (!float.IsNaN(step)) { FillGap(track, root, rng, x, step); x = step; continue; }
                float cx = x + w * 0.5f, gy = GroundAt(track, cx);
                bool model = front != null && ShopFront(root, rng, front, cx, gy, w);
                if (!model)
                {
                    var kind = i % 2 == 0 ? ProceduralArt.FacadeKind.Shop0 : ProceduralArt.FacadeKind.Shop1;
                    model = Building(root, cx, gy, PropertyZ + 0.6f, kind, House3D.RoofStyle.Flat, 8f, 0f, i % 3 == 0 ? new Color(0.95f, 0.9f, 0.82f) : new Color(0.88f, 0.9f, 0.94f), new Color(0.6f, 0.6f, 0.62f));
                }
                ContactShadow(root, cx - w * 0.5f + 0.1f, cx + w * 0.5f - 0.1f, gy, PropertyZ - 0.7f, PropertyZ + 0.6f);
                if (!model)
                {
                    // Awning sticking out over the pavement (the kit's shops have their own shopfronts).
                    Color awn = awnings[i % awnings.Length];
                    Solid(root, "Awning", new Vector3(cx, gy + 3.55f, PropertyZ - 0.1f), new Vector3(7.4f, 0.14f, 1.4f), awn);
                    Solid(root, "AwningValance", new Vector3(cx, gy + 3.3f, PropertyZ - 0.78f), new Vector3(7.4f, 0.5f, 0.06f), Color.Lerp(awn, Color.white, 0.15f));
                }
                x += w;
                bool between = model && rng.NextDouble() < 0.5;
                if (model && !between && i % 2 == 1)
                    Model(root, "Street", "StreetLamp", x, gy, PoleZ - 0.1f);   // where two shopfronts meet, clear of their stands
                if (between)
                {
                    // Between shopfronts: a potted lemon tree or shrub, a doorstep of pots, a pair of bins,
                    // or crates and a sack waiting to go in.
                    float gx = x + Rand(rng, -0.25f, 0.25f), gz = PropertyZ + 0.25f;
                    double r = rng.NextDouble();
                    if (r < 0.25) Model(root, "Street", "PotC", gx, gy, gz, Rand(rng, 0f, 360f));
                    else if (r < 0.42) Model(root, "Street", "PotB", gx, gy, gz, Rand(rng, 0f, 360f));
                    else if (r < 0.58) Model(root, "Street", "PotGroup", gx, gy, gz, Rand(rng, -20f, 20f), 1f, Petals[rng.Next(Petals.Length)]);
                    else if (r < 0.72) Model(root, "Street", "BinPair", gx, gy, PropertyZ + 0.35f, Rand(rng, -8f, 8f), 1f, BinColors[rng.Next(BinColors.Length)], BinColors[rng.Next(BinColors.Length)]);
                    else
                    {
                        Model(root, "Street", rng.NextDouble() < 0.5 ? "CrateStack" : "ProduceCrate", gx, gy, gz, Rand(rng, -15f, 15f));
                        Model(root, "Street", "Sack", gx + 0.75f, gy, gz - 0.1f, Rand(rng, 0f, 360f));
                    }
                }
                bool vend = !vended && front != "ShopKonbini" && rng.NextDouble() < 0.28 && x + (chunk != null ? 2.7f : 2.4f) < runEnd;
                vended = vend;
                if (vend && CA && LevelBuildKit.HasKitModel("Plants", "PalmDate"))
                {
                    // A date palm in the gap between shops (never two gaps running), its crown over the awnings.
                    Plant(root, "PalmDate", null, x + 1.3f, gy, PropertyZ + 0.5f, Rand(rng, 0.6f, 0.75f), 1f, -60, rng);
                    x += 2.6f;
                }
                else if (vend)
                {
                    // Drinks machines in the gap between shops (never two gaps running).
                    if (Model(root, "Street", "VendingRed", x + 0.7f, gy, PropertyZ + 0.2f) == null)
                        Solid(root, "Vending", new Vector3(x + 0.7f, gy + 0.93f, PropertyZ + 0.2f), new Vector3(1f, 1.85f, 0.8f), new Color(0.85f, 0.22f, 0.24f));
                    if (Model(root, "Street", "VendingBlue", x + 1.75f, gy, PropertyZ + 0.2f) == null)
                        Solid(root, "Vending", new Vector3(x + 1.75f, gy + 0.93f, PropertyZ + 0.2f), new Vector3(1f, 1.85f, 0.8f), new Color(0.25f, 0.45f, 0.78f));
                    x += 2.6f;
                }
            }
            // Flats behind the shops (never on a side street).
            for (float x = Lo(x0, 20f); x < Hi(x1, 20f); x += Rand(rng, 13f, 16f))
            {
                float z = Rand(rng, 22f, 28f);
                if (OnSideStreet(track, x, ProceduralArt.FacadeKind.Apartment)) continue;
                // Every other block a white beach condo, the rest the kit's flats.
                if (CA && rng.NextDouble() < 0.5 && CoastHouse(root, "BeachCondo", x, GroundAt(track, x), z)) continue;
                Building(root, x, GroundAt(track, x), z, ProceduralArt.FacadeKind.Apartment, House3D.RoofStyle.Flat, 10f, 0f, new Color(0.92f, 0.88f, 0.82f), new Color(0.6f, 0.6f, 0.62f));
            }
            DistantHills(track, root, x0, x1);
        }

        /// <summary>
        /// The end of a beach level at the school (docs/WORLD_MAP.md: the school stands by the sea, at the top of the beach): the
        /// school is on land, not in the water. <paramref name="coastX"/> is where the coast turns away from the beach: from the
        /// water's edge there a low sea wall with rocks at its foot runs back diagonally to well behind the school
        /// (<see cref="SchoolLandZ"/>) at the gate, and the sea lies beyond it. The land in the corner is grass behind the beach's dry
        /// sand, and past the gate the school's yard is paved from the camera's side to behind the footpath, so the school, its wall
        /// and its trees all stand on solid ground. The beach's sand runs on under the land and the yard (only the footpath is played).
        /// </summary>
        static void SchoolHeadland(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1, float sea, float coastX)
        {
            var rng = new System.Random(Mathf.RoundToInt(track.GoalX * 7f) + 131);
            float goal = track.GoalX, gy = GroundAt(track, goal);
            float coastEnd = goal - 4f, near = x0 - 800f, far = x1 + 800f;
            float land = gy + 0.02f, front = SandField.WetFrom - 0.2f;           // the grass begins where the beach starts down to the sea

            // The sea: up to the coast's turn, then back behind the land (the water shader is in world space: one sea).
            var waterGo = new GameObject("Sea");
            waterGo.transform.SetParent(root, false);
            var water = waterGo.AddComponent<PatchShape>();
            waterGo.GetComponent<MeshRenderer>().sharedMaterial = Art.surfaces[ProceduralArt.Surface.Sea];
            water.AddQuad(new Vector3(near, sea, 5f), new Vector3(near, sea, 955f), new Vector3(coastX, sea, 955f), new Vector3(coastX, sea, 5f), Color.white);
            water.AddQuad(new Vector3(coastX, sea, 5f), new Vector3(coastX, sea, 955f), new Vector3(coastEnd, sea, 955f), new Vector3(coastEnd, sea, SchoolLandZ - 2f), Color.white);
            water.AddQuad(new Vector3(coastEnd, sea, SchoolLandZ - 2f), new Vector3(coastEnd, sea, 955f), new Vector3(far, sea, 955f), new Vector3(far, sea, SchoolLandZ - 2f), Color.white);
            water.Rebuild();

            // The land: grass from the coast's turn on, behind the dry sand, and back to the sea behind the school.
            Color lawn = new Color(0.66f, 0.8f, 0.5f);
            var landGo = new GameObject("SchoolLand");
            landGo.transform.SetParent(root, false);
            var ground = landGo.AddComponent<PatchShape>();
            landGo.GetComponent<MeshRenderer>().sharedMaterial = Art.surfaces[ProceduralArt.Surface.Grass];
            Vector3 shoreA = new Vector3(coastX - 3f, land, front), shoreB = new Vector3(coastX + 0.6f, land, 10.2f), headEnd = new Vector3(coastEnd, land, SchoolLandZ);
            ground.AddQuad(shoreA, shoreB, headEnd, new Vector3(coastEnd, land, front), lawn);
            ground.AddQuad(new Vector3(coastEnd, land, front), headEnd, new Vector3(far, land, SchoolLandZ), new Vector3(far, land, front), lawn);
            ground.Rebuild();

            // A low sea wall along the land's edge (the beach end and the coast), standing in the water, with rocks at its foot.
            Color wall = new Color(0.8f, 0.78f, 0.72f);
            var concrete = Art.surfaces[ProceduralArt.Surface.Concrete];
            Vector3 backEnd = new Vector3(x1 + 60f, land, SchoolLandZ);
            foreach (var edge in new[] { new[] { shoreA, shoreB }, new[] { shoreB, headEnd }, new[] { headEnd, backEnd } })
            {
                Vector3 a = edge[0], b = edge[1];
                Vector3 mid = (a + b) * 0.5f, along = b - a;
                float length = new Vector2(along.x, along.z).magnitude, top = land + 0.45f, bottom = sea - 0.6f;
                var seawall = Solid(root, "SeaWall", new Vector3(mid.x, (top + bottom) * 0.5f, mid.z), new Vector3(0.6f, top - bottom, length + 0.6f), wall, concrete);
                seawall.transform.rotation = Quaternion.Euler(0f, Mathf.Atan2(along.x, along.z) * Mathf.Rad2Deg, 0f);
                // Rocks on the sea side, every few metres.
                Vector3 outward = new Vector3(along.z, 0f, -along.x).normalized;
                if (outward.x > 0.01f || (Mathf.Abs(outward.x) <= 0.01f && outward.z < 0f)) outward = -outward;   // toward the sea: the beach's side of the turn, and behind the school
                for (float t = 0.08f; t < 1f; t += 3.2f / Mathf.Max(length, 1f))
                {
                    Vector3 p = a + along * t + outward * Rand(rng, 0.7f, 1.4f);
                    Model(root, "Terrain", rng.NextDouble() < 0.5 ? "RockCluster" : "Boulder2", p.x, sea - 0.25f, p.z, Rand(rng, 0f, 360f), Rand(rng, 0.7f, 1.2f));
                }
            }

            // The school's yard: paved from the gate past the building, from the camera's side to the lawn; the lawn beyond.
            Patch(root, "SchoolYard", goal + 0.4f, goal + 30f, gy, FrontZ, front, new Color(0.9f, 0.88f, 0.84f), Art.surfaces[ProceduralArt.Surface.Paving], 0.02f);
            Patch(root, "SchoolField", goal + 30f, x1 + 60f, gy, FrontZ, front, lawn, Art.surfaces[ProceduralArt.Surface.Grass], 0.02f);

            // Pines and a few palms on the land between the beach and the school.
            for (float x = coastX + 2f; x < goal - 2f; x += Rand(rng, 4f, 7f))
            {
                float z = Rand(rng, 12f, 30f);
                // Behind the coast's line only.
                float coastZ = Mathf.Lerp(10.2f, SchoolLandZ, Mathf.InverseLerp(coastX, coastEnd, x));
                if (z < coastZ + 2f) z = coastZ + Rand(rng, 2f, 6f);
                if (z > SchoolLandZ - 2f) continue;
                Plant(root, rng.NextDouble() < 0.6 ? "ConiferMid" : "Palm", null, x, land, z, Rand(rng, 0.9f, 1.2f), 1f, -70, rng);
            }
        }

        /// <summary>The stretches of [a, b] outside every tide's stretch (in order; the shoreline's foam runs along them).</summary>
        public static List<Vector2> ShoreRuns(float a, float b, IList<Vector2> tides)
        {
            var cuts = new List<Vector2>(tides);
            cuts.Sort((p, q) => p.x.CompareTo(q.x));
            var runs = new List<Vector2>();
            float from = a;
            foreach (var cut in cuts)
            {
                if (cut.y <= from || cut.x >= b) continue;
                if (cut.x - from > 0.5f) runs.Add(new Vector2(from, cut.x));
                from = Mathf.Max(from, cut.y);
            }
            if (b - from > 0.5f) runs.Add(new Vector2(from, b));
            return runs;
        }

        /// <summary>How far before the school's gate the coast starts to turn away from the beach (see <see cref="SchoolHeadland"/>).</summary>
        public const float SchoolCoastBefore = 26f;
        /// <summary>How far back (z) the sea lies behind the school: well behind the building, its wall and its trees.</summary>
        public const float SchoolLandZ = 46f;

        static void Beach(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            float sea = track.LowestGroundTop - 0.3f;
            // A level that ends at the school: the school stands on its own land by the sea, not in it. The coast turns away
            // before the gate (SchoolHeadland), and the beach's own things stop short of the school.
            bool schoolEnd = track.GoalX > track.MinX && (chunk == null || chunk.level);
            float coastX = schoolEnd ? track.GoalX - SchoolCoastBefore : float.PositiveInfinity;
            float propsEnd = schoolEnd ? Mathf.Min(x1, track.GoalX - 2f) : x1;
            if (chunk == null || chunk.level)   // (a Holiday Run's sea is in the core scene, all along the beach)
            {
                if (schoolEnd) SchoolHeadland(track, root, x0, x1, sea, coastX);
                else
                {
                    var water = Solid(root, "Sea", new Vector3((x0 + x1) * 0.5f, sea - 0.05f, 480f), new Vector3(x1 - x0 + 1600f, 0.1f, 950f), Color.white, Art.surfaces[ProceduralArt.Surface.Sea]);
                    water.faces = MeshBuilder.Faces.Top;
                    water.Rebuild();
                }
            }

            // Foam lapping up the sand where the waves break, and lines of breaking crests rolling in
            // out at sea. They move, so they live outside the street's static batches.
            var waves = new GameObject("Waves").transform;
            // The foam lies just above the sea, so where it meets the sand is where the water does; each
            // surge carries it a little up the beach. It stops where a tide washes up the beach: there the
            // wash is the sea running on up the sand, with its own foam at its front, and a line of foam
            // across it would cut the water in two.
            foreach (var run in ShoreRuns(Lo(x0, 60f), Mathf.Min(Hi(x1, 60f), coastX), track.TideStretches))
            {
                var shoreline = Foam(waves, run.x, run.y, 9.2f, 10f, sea + 0.02f, 0.3f);
                var lap = shoreline.AddComponent<Lapping>();
                lap.reach = new Vector3(0f, 0.04f, -0.35f);
                lap.period = 5.5f;
            }
            float[] crests = { 13f, 19f, 28f, 42f };
            for (int i = 0; i < crests.Length; i++)
                for (float x = Lo(x0, 60f) + (float)rng.NextDouble() * 10f; x < Hi(x1, 60f); x += Rand(rng, 14f, 30f))
                {
                    float len = Rand(rng, 5f, 14f), w = Mathf.Lerp(0.35f, 0.9f, i / (float)(crests.Length - 1));
                    if ((chunk != null && x + len > x1) || x + len > coastX - 2f) continue;
                    var crest = Foam(waves, x, x + len, crests[i] + Rand(rng, -1f, 1f), crests[i] + w, sea - 0.04f, i * 1.7f + x);
                    var roll = crest.AddComponent<Lapping>();
                    roll.reach = new Vector3(Rand(rng, -0.5f, 0.5f), 0f, -Rand(rng, 1.8f, 3.2f));
                    roll.period = Rand(rng, 6.5f, 9f);
                    roll.phase = (float)rng.NextDouble();
                }

            // The pier: once along a level's beach, running straight out to sea, its stairs and their paths clear of
            // the stops' plots. The lifeguard towers, palms and parasols keep clear of it (pierReach either side).
            float skip;
            float pierX = float.NaN, pierReach = 0f;
            if (track.PierClimbs.Count > 0)
            {
                // The course climbs the pier (TrackBuilder.PierClimb): it stands across the lane there.
                var climb = track.PierClimbs[0];
                pierX = climb.Centre;
                pierReach = Mathf.Max(PierWidth * 0.5f, (climb.end - climb.foot) * 0.5f + 0.8f);
                PierOnCourse(track, root, climb, 13);
            }
            else if (CA && (chunk == null || chunk.level) && LevelBuildKit.HasKitModel("Coast", "PierSpan") && propsEnd - x0 > 60f)
            {
                pierReach = PierReach;
                for (float tryX = x0 + (propsEnd - x0) * 0.55f; tryX < propsEnd - pierReach - 8f; tryX += 7f)
                {
                    if (Blocked(track, tryX - pierReach, tryX + pierReach, out skip)) continue;
                    pierX = tryX;
                    break;
                }
                if (!float.IsNaN(pierX)) Pier(track, root, pierX, sea, 6.2f, 13);
            }
            var towers = new List<float>();
            for (float x = x0 + Margin(4f); x < Mathf.Min(x1 - Margin(4f), propsEnd - 4f); x += Rand(rng, 30f, 45f))
            {
                if (Blocked(track, x - 2f, x + 2f, out skip)) continue;     // a stop's plot (StreetBuilder.Stops)
                if (Mathf.Abs(x - pierX) < pierReach + 2f) continue;        // (the pier's stairs)
                LifeguardTower(root, x, GroundAt(track, x, 7.4f), 7.4f);
                towers.Add(x);
            }
            // Date palms and the odd young fan palm along the back of the beach.
            if (CA) StreetPalms(track, root, rng, x0 + Margin(3f), propsEnd - 3f, 2.8f, 14f, 30f, pierX - pierReach, pierX + pierReach);
            Color[] canopy = { new Color(0.9f, 0.3f, 0.28f), new Color(0.25f, 0.5f, 0.85f), new Color(1f, 0.75f, 0.2f), new Color(0.3f, 0.66f, 0.62f) };
            Color[] towels = { new Color(0.95f, 0.55f, 0.6f), new Color(0.45f, 0.75f, 0.9f), new Color(1f, 0.85f, 0.35f), new Color(0.55f, 0.8f, 0.55f) };
            bool beachKit = LevelBuildKit.HasKitModel("Leisure", "Parasol");
            for (float x = x0 + 8f; x < Mathf.Min(x1 - Margin(3f), propsEnd - 3f); x += beachKit ? Rand(rng, 5f, 11f) : Rand(rng, 10f, 18f))
            {
                float z = Rand(rng, 3.4f, 5.2f), gy = GroundAt(track, x, z);
                if (Blocked(track, x - 1.5f, x + 2.6f, out skip)) continue;
                if (x > pierX - pierReach - 2.6f && x < pierX + pierReach + 1.5f) continue;     // (the pier's stairs and paths)
                if (beachKit)
                {
                    if (towers.Any(t => Mathf.Abs(t - x) < 3f)) continue;
                    // A parasol leaning a little over a towel; now and then a cool box, or a sandcastle
                    // with a bucket and spade. Each sits on the sand where it is.
                    var parasolModel = Model(root, "Leisure", "Parasol", x, gy - 0.05f, z, Rand(rng, 0f, 360f), 1f, canopy[rng.Next(canopy.Length)]);
                    if (parasolModel != null) parasolModel.rotation = Quaternion.Euler(Rand(rng, -7f, 7f), 0f, Rand(rng, -7f, 7f)) * parasolModel.rotation;
                    float tx = x + Rand(rng, -0.3f, 0.3f);
                    Model(root, "Leisure", "BeachTowel", tx, GroundAt(track, tx, z - 0.4f), z - 0.4f, 90f + Rand(rng, -15f, 15f), 1f, towels[rng.Next(towels.Length)]);
                    if (rng.NextDouble() < 0.4)
                        Model(root, "Leisure", "CoolBox", x + 0.9f, GroundAt(track, x + 0.9f, z + 0.3f), z + 0.3f, Rand(rng, -25f, 25f), 1f, canopy[rng.Next(canopy.Length)]);
                    if (rng.NextDouble() < 0.3)
                    {
                        float cx = x + Rand(rng, 1.3f, 1.8f), cz = z - Rand(rng, 1f, 1.6f), bx = x + Rand(rng, 2.1f, 2.5f), bz = z - Rand(rng, 0.8f, 1.3f);
                        Model(root, "Leisure", "SandCastle", cx, GroundAt(track, cx, cz) - 0.03f, cz, Rand(rng, -20f, 20f));
                        Model(root, "Leisure", "BucketSpade", bx, GroundAt(track, bx, bz), bz, Rand(rng, 0f, 360f));
                    }
                    continue;
                }
                var go = new GameObject("Parasol");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector3(x, gy, z);
                var parasol = go.AddComponent<ParasolShape>();
                parasol.colorA = canopy[rng.Next(canopy.Length)];
                parasol.lean = Rand(rng, -9f, 9f);
                go.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                parasol.Rebuild();
                // A towel in its shade, and sometimes a cool box.
                Solid(root, "Towel", new Vector3(x + Rand(rng, -0.3f, 0.3f), gy + 0.008f, z - 0.4f), new Vector3(0.8f, 0.016f, 1.7f), towels[rng.Next(towels.Length)]);
                if (rng.NextDouble() < 0.4)
                    Solid(root, "CoolBox", new Vector3(x + 0.9f, gy + 0.18f, z + 0.3f), new Vector3(0.55f, 0.36f, 0.38f), new Color(0.3f, 0.55f, 0.85f));
            }
            bool rockModels = LevelBuildKit.HasKitModel("Terrain", "RockCluster");
            for (float x = x0 + 15f; x < Mathf.Min(x1 - Margin(4f), coastX - 3f); x += rockModels ? Rand(rng, 12f, 24f) : Rand(rng, 22f, 38f))
            {
                // Rocks at the water's edge, bedded in the sand, darker where the sea wets them.
                float gy = track.LowestGroundTop - 0.12f, s = Rand(rng, 0.8f, 1.6f);
                if (rockModels)
                {
                    float rz = Rand(rng, 8.6f, 11f), bx = x + Rand(rng, 2f, 3.5f), bz = rz - Rand(rng, 0.5f, 1.2f);
                    Model(root, "Terrain", "RockCluster", x, GroundAt(track, x, rz) - 0.15f, rz, Rand(rng, -30f, 30f), s * 0.8f);
                    if (rng.NextDouble() < 0.5)
                        Model(root, "Terrain", rng.NextDouble() < 0.5 ? "Boulder2" : "Boulder1", bx, GroundAt(track, bx, bz) - 0.1f, bz, Rand(rng, 0f, 360f), Rand(rng, 0.7f, 1.1f));
                    continue;
                }
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
            // Palms in ones, twos and threes behind the parasols, clear of the lifeguard towers.
            if (LevelBuildKit.HasKitModel("Plants", "Palm"))
                for (float x = x0 + Rand(rng, 5f, 15f); x < Mathf.Min(x1 - Margin(8f), propsEnd - 4f); x += Rand(rng, 16f, 32f))
                {
                    int n = rng.Next(1, 4);
                    for (int k = 0; k < n; k++)
                    {
                        float px = x + k * Rand(rng, 2.2f, 3.4f), pz = Rand(rng, 5.6f, 7f);
                        if (towers.Any(t => Mathf.Abs(t - px) < 4.5f) || px > propsEnd || Blocked(track, px - 1.5f, px + 1.5f, out skip)) continue;
                        if (Mathf.Abs(px - pierX) < pierReach + 1.5f) continue;     // (the pier and its stairs)
                        Plant(root, rng.NextDouble() < 0.5 ? "Palm" : "PalmShort", null, px, GroundAt(track, px, pz) - 0.1f, pz, Rand(rng, 0.85f, 1.15f), 1f, -60, rng);
                    }
                }

            // Tufts of beach grass in the soft sand nearer the camera.
            if (LevelBuildKit.HasKitModel("Plants", "DuneGrass"))
            {
                for (float x = x0; x < propsEnd; x += Rand(rng, 1.2f, 4f))
                {
                    // Dune grass in little drifts, a clump or two at a time, far enough in front of the path
                    // not to hide the ball from the low camera.
                    float z = Rand(rng, -6.5f, -3.8f);
                    int clumps = rng.Next(1, 4);
                    for (int k = 0; k < clumps; k++)
                    {
                        float gx = x + k * Rand(rng, 0.5f, 0.9f), gz = z + Rand(rng, -0.4f, 0.4f);
                        Plant(root, "DuneGrass", null, gx, GroundAt(track, gx, gz) - 0.03f, gz, Rand(rng, 0.7f, 1.3f), 1f, -50, rng);
                    }
                }
                Headlands(root, rng, x0, x1, sea);
                return;
            }
            var grass = new GameObject("BeachGrass");
            grass.transform.SetParent(root, false);
            var tufts = grass.AddComponent<BlobShape>();
            for (float x = x0; x < propsEnd; x += Rand(rng, 1.5f, 5f))
            {
                float z = Rand(rng, -9f, -2.4f), gy = GroundAt(track, x, z);
                // A low, spreading clump of dune grass.
                for (int k = 0; k < 4; k++)
                    tufts.blobs.Add(new BlobShape.Blob(new Vector3(x + Rand(rng, -0.3f, 0.3f), gy + 0.03f, z + Rand(rng, -0.25f, 0.25f)),
                        new Vector3(Rand(rng, 0.14f, 0.24f), Rand(rng, 0.06f, 0.11f), Rand(rng, 0.12f, 0.2f)), Color.Lerp(new Color(0.58f, 0.66f, 0.34f), new Color(0.82f, 0.8f, 0.5f), (float)rng.NextDouble())));
            }
            grass.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
            tufts.Rebuild();
            Headlands(root, rng, x0, x1, sea);
        }

        /// <summary>Wooded headlands out on the horizon across the bay.</summary>
        static void Headlands(Transform root, System.Random rng, float x0, float x1, float sea)
        {
            if (chunk != null && !chunk.level) return;   // (a Holiday Run's are in the core scene)
            for (int i = 0; i < 3; i++)
            {
                float x = x0 + (x1 - x0) * (0.15f + i * 0.4f) + Rand(rng, -40f, 40f), z = 650f + i * 60f;
                if (Model(root, "Terrain", "Headland", x, sea - 0.5f, z, Rand(rng, -15f, 15f), Rand(rng, 2.2f, 3f), null, null, null, false) == null)
                    CutOut(root, "Headland", Art.headland, x, sea - 0.5f, z, 10f, -85, i % 2 == 1);
            }
        }

        /// <summary>A white band of foam with a wavy edge toward the camera.</summary>
        static GameObject Foam(Transform root, float a, float b, float zFront, float zBack, float y, float phase)
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
            return go;
        }

        /// <summary>A white wooden lifeguard tower: legs and braces, a platform, a hut with a red roof, a ladder and a flag.</summary>
        static void LifeguardTower(Transform root, float x, float gy, float z)
        {
            if (Model(root, "Leisure", "LifeguardTower", x, gy, z) != null) return;
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
            bool site = LevelBuildKit.HasKitModel("Works", "Skip");
            for (float x = x0; x < x1;)
            {
                float w = NextLot(track, rng, x, x1, 11f, 14f), skip;
                if (Blocked(track, x, x + w, out skip)) { FillGap(track, root, rng, x, BlockStart(track, x, x + w)); x = skip; continue; }
                // The last scrap of a run (too small for a block) is closed off like any gap.
                if (chunk != null && w < 11.5f) { FillGap(track, root, rng, x, x + w); x += w; continue; }
                int mix = TransitionStyle(x, w);
                if (mix != 0) { ThemeLot(track, root, rng, mix, x, x + w); x += w; continue; }
                if (LotEndsAtStep(track, root, rng, ref x, ref w, 12.5f)) continue;
                float cx = x + w * 0.5f, gy = GroundAt(track, cx);
                bool flats = rng.NextDouble() >= 0.5, cabin = false;
                double front = rng.NextDouble();
                if (front < 0.35)
                {
                    if (rng.NextDouble() < 0.5) Model(root, "Street", "SignNoEntry", cx - w * 0.5f + 0.5f, gy, PoleZ - 0.15f);
                    if (!Row(root, "Street", "Hoarding3", cx - w * 0.5f + 0.15f, cx + w * 0.5f - 0.15f, gy, PropertyZ + 0.2f))
                        Solid(root, "Hoarding", new Vector3(cx, gy + 1.3f, PropertyZ + 0.2f), new Vector3(w - 0.3f, 2.6f, 0.2f), Color.white, hoarding);
                }
                else if (front < 0.55 && site)
                {
                    // Mesh site fencing on block feet, with the yard showing through.
                    Row(root, "Works", "SiteFence", cx - w * 0.5f + 0.2f, cx + w * 0.5f - 0.2f, gy, PropertyZ + 0.2f);
                    cabin = SiteYard(root, rng, x, w, gy, flats);
                }
                else if (site) cabin = SiteYard(root, rng, x, w, gy, flats);
                else if (LevelBuildKit.HasKitModel("Terrain", "SandPile"))
                {
                    // An open yard: a heap of sand or gravel, a pallet of blocks, a few cones.
                    float px = x + Rand(rng, 1.5f, 3f);
                    Model(root, "Terrain", rng.NextDouble() < 0.5 ? "SandPile" : "GravelPile", px, gy, PropertyZ + 1.6f, Rand(rng, 0f, 360f), Rand(rng, 0.8f, 1.2f));
                    Model(root, "Street", "Pallet", px + Rand(rng, 2.2f, 3f), gy, PropertyZ + 1.1f, Rand(rng, -20f, 20f));
                    for (int k = 0; k < 2; k++)
                        Model(root, "Street", "TrafficCone", x + w - 1.2f - k * 0.8f, gy, PropertyZ + 0.5f, Rand(rng, 0f, 360f));
                }
                // An electrical cabinet in some yards; now and then a pair of narrow tiled buildings
                // (one of each) instead of the flats.
                if (front >= 0.35 && rng.NextDouble() < 0.35) Model(root, "Street", "UtilityBox", x + w - 1f, gy, PropertyZ + 0.65f, Rand(rng, -4f, 4f));
                bool pair = flats && rng.NextDouble() < 0.35 && LevelBuildKit.HasKitModel("Buildings", "ShopTall") && LevelBuildKit.HasKitModel("Buildings", "ShopBoutique");
                if (pair)
                {
                    string[] two = rng.NextDouble() < 0.5 ? new[] { "ShopTall", "ShopBoutique" } : new[] { "ShopBoutique", "ShopTall" };
                    for (int k = 0; k < 2; k++)
                    {
                        float hw = LevelBuildKit.KitSize("Buildings", two[k]).x * 0.5f, bx = k == 0 ? cx - hw - 0.1f : cx + hw + 0.1f;
                        var p = PaintFor(two[k], WorkPaints, bx, PropertyZ + 4f);
                        Model(root, "Buildings", two[k], bx, gy, PropertyZ + 4f, 0f, 1f, p.wall, p.trim, p.roof);
                        ContactShadow(root, bx - hw, bx + hw, gy, PropertyZ + 3.55f, PropertyZ + 4f);
                    }
                }
                else if (!flats)
                    Building(root, cx, gy, PropertyZ + 3f, ProceduralArt.FacadeKind.Warehouse, House3D.RoofStyle.Shed, 8f, 1.2f, new Color(0.78f, 0.74f, 0.7f), new Color(0.5f, 0.52f, 0.56f));
                else
                {
                    bool kit = Building(root, cx, gy, PropertyZ + 5f, ProceduralArt.FacadeKind.Apartment, House3D.RoofStyle.Flat, 10f, 0f, new Color(0.92f, 0.88f, 0.82f), new Color(0.6f, 0.6f, 0.62f));
                    // Some blocks are still going up: scaffolding over the lower floors.
                    if (kit && site && !cabin && rng.NextDouble() < 0.4)
                        Row(root, "Works", "Scaffold", cx - 6.2f, cx + 6.2f, gy, PropertyZ + 5f - 0.9f);
                }
                x += w;
            }
            // Tower cranes over the site, far enough off to stand whole above the street in the haze.
            // (A Holiday Run's are part of the far land in the core scene, so they never come and go with a stage.)
            bool cranes = LevelBuildKit.HasKitModel("Works", "TowerCrane");
            for (float x = x0; (chunk == null || chunk.level) && x < x1; x += Rand(rng, 40f, 60f))
            {
                if (cranes)
                {
                    Model(root, "Works", "TowerCrane", x + Rand(rng, -20f, 20f), GroundAt(track, x), Rand(rng, 170f, 230f), Rand(rng, -40f, 40f) + (rng.NextDouble() < 0.5 ? 180f : 0f), Rand(rng, 0.85f, 1.05f), null, null, null, false);
                    x += Rand(rng, 30f, 60f);
                    continue;
                }
                if (OverlapsBackRow(track, x - 4f, x + 4f)) continue;
                CutOut(root, "Crane", Art.mid[4, 2], x, GroundAt(track, x), 45f, 2f, -75);
            }
            DistantHills(track, root, x0, x1);
        }

        /// <summary>
        /// A building site's yard behind the fence line (Works kit): one of a digger by a sand pile,
        /// a skip with a wheelbarrow and a cement mixer, pipes and steel beams waiting, or (in front
        /// of the deeper flats) the site cabin and a portable loo. True if it put the cabin there.
        /// </summary>
        static bool SiteYard(Transform root, System.Random rng, float x, float w, float gy, bool deep)
        {
            float z = PropertyZ + 1.4f;
            switch (rng.Next(deep ? 4 : 3))
            {
                case 0:
                    Model(root, "Works", "Digger", x + Rand(rng, 3f, 4.5f), gy, z + 0.4f, Rand(rng, -25f, 25f));
                    Model(root, "Terrain", "SandPile", x + w - Rand(rng, 2f, 3f), gy, z, Rand(rng, 0f, 360f), Rand(rng, 0.9f, 1.2f));
                    break;
                case 1:
                    Model(root, "Works", "Skip", x + Rand(rng, 2.5f, 3.5f), gy, z + 0.3f, Rand(rng, -10f, 10f), 1f, SkipColors[rng.Next(SkipColors.Length)]);
                    Model(root, "Works", "Wheelbarrow", x + Rand(rng, 6f, 7f), gy, z - 0.2f, Rand(rng, -40f, 40f));
                    Model(root, "Works", "CementMixer", x + w - Rand(rng, 1.8f, 2.6f), gy, z, Rand(rng, -30f, 30f));
                    break;
                case 2:
                    Model(root, "Works", "PipeStack", x + Rand(rng, 2f, 3f), gy, z + 0.2f, Rand(rng, -10f, 10f));
                    Model(root, "Works", "SteelBeams", x + Rand(rng, 6.5f, 7.5f), gy, z, Rand(rng, -15f, 15f));
                    Model(root, "Street", "TrafficCone", x + w - 1.2f, gy, PropertyZ + 0.5f, Rand(rng, 0f, 360f));
                    break;
                default:
                    Model(root, "Works", "SiteCabin", x + Rand(rng, 3.6f, 4.4f), gy, z + 1.3f, Rand(rng, -5f, 5f));
                    Model(root, "Works", "PortaLoo", x + w - Rand(rng, 1.4f, 2f), gy, z + 0.4f, Rand(rng, -20f, 20f));
                    return true;
            }
            return false;
        }

        static readonly Color[] SkipColors = { new Color(0.36f, 0.5f, 0.62f), new Color(0.9f, 0.6f, 0.22f), new Color(0.42f, 0.6f, 0.44f) };

        static void Park(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            Color hedge = new Color(0.28f, 0.5f, 0.3f);
            bool plants = LevelBuildKit.HasKitModel("Plants", "Broadleaf");
            int segment = 0;
            for (float x = x0; x < x1;)
            {
                float w = NextLot(track, rng, x, x1, 6f, 10f), skip;
                if (Blocked(track, x, x + w, out skip)) { FillGap(track, root, rng, x, BlockStart(track, x, x + w)); x = skip; continue; }
                if (chunk != null && w < 3f) { FillGap(track, root, rng, x, x + w); x += w; continue; }
                int mix = TransitionStyle(x, w);
                if (mix != 0) { ThemeLot(track, root, rng, mix, x, x + w); x += w; continue; }
                float cx = x + w * 0.5f, gy = GroundAt(track, cx) + 0.04f;
                // A lamp in every other gap between the hedges.
                if (segment++ % 2 == 0) Model(root, "Leisure", "ParkLamp", x, GroundAt(track, x) + 0.04f, PropertyZ - 0.1f);
                if (!Row(root, "Plants", "HedgeBlock2", cx - w * 0.5f + 0.6f, cx + w * 0.5f - 0.6f, gy, PropertyZ + 0.4f, HedgeGreen))
                    Solid(root, "Hedge", new Vector3(cx, gy + 0.5f, PropertyZ + 0.4f), new Vector3(w - 1.2f, 1f, 0.8f), hedge);
                ContactShadow(root, cx - w * 0.5f + 0.6f, cx + w * 0.5f - 0.6f, gy, PropertyZ - 0.25f, PropertyZ);
                if (plants)
                {
                    // A flowering shrub peeking over the hedge from the lawn behind it.
                    Plant(root, rng.NextDouble() < 0.5 ? "ShrubFlowering" : "BushRound", null, cx - w * 0.25f, gy, PropertyZ + 1.5f, Rand(rng, 1.2f, 1.6f), 1f, -55, rng);
                }
                else CutOut(root, "Bush", Art.bush, cx - w * 0.25f, gy + 0.6f, PropertyZ + 0.3f, 1f, -55);
                if (rng.NextDouble() < 0.4 && Model(root, "Street", "Bench", cx + 1.5f, gy, PropertyZ - 0.55f) == null)
                    Solid(root, "Bench", new Vector3(cx + 1.5f, gy + 0.25f, PropertyZ - 0.6f), new Vector3(1.8f, 0.5f, 0.5f), new Color(0.6f, 0.42f, 0.3f));
                x += w;
            }
            var clearings = ParkFeatures(track, root, rng, x0, x1);
            for (float x = x0; x < x1; x += Rand(rng, 4f, 8f))
            {
                float skip;
                if (Blocked(track, x - 3f, x + 3f, out skip) || clearings.Any(c => x > c.x - 3f && x < c.y + 3f)) continue;
                double r = rng.NextDouble();
                if (plants)
                {
                    string model = r < 0.3 ? "CherryBlossom" : r < 0.65 ? "Broadleaf" : r < 0.85 ? "BroadleafLarge" : "Birch";
                    Plant(root, model, null, x, GroundAt(track, x), Rand(rng, 6.5f, 16f), Rand(rng, 0.85f, 1.15f), 1f, -62, rng);
                    continue;
                }
                bool cherry = r < 0.4;
                CutOut(root, cherry ? "Cherry" : "Tree", Art.mid[5, cherry ? 1 : 2], x, GroundAt(track, x), Rand(rng, 6.5f, 16f), Rand(rng, 0.9f, 1.2f), -62, rng.NextDouble() < 0.5);
            }
            if (plants)
            {
                // Bushes between the trunks, and a wood further back that closes the view.
                for (float x = x0; x < x1; x += Rand(rng, 4f, 9f))
                {
                    float skip;
                    if (Blocked(track, x - 1.5f, x + 1.5f, out skip) || clearings.Any(c => x > c.x - 1.5f && x < c.y + 1.5f)) continue;
                    Plant(root, rng.NextDouble() < 0.6 ? "BushWide" : "BushRound", null, x, GroundAt(track, x) + 0.04f, Rand(rng, 3.5f, 6f), Rand(rng, 1f, 1.5f), 1f, -58, rng);
                }
                string[] wood = { "BroadleafLarge", "Broadleaf", "BroadleafWide", "ConiferTall", "BroadleafLarge", "ConiferMid", "Birch" };
                for (float x = Lo(x0, 20f); x < Hi(x1, 20f); x += Rand(rng, 3f, 6f))
                {
                    if (OverlapsBackRow(track, x - 2f, x + 2f)) continue;
                    Plant(root, wood[rng.Next(wood.Length)], null, x, GroundAt(track, x) + 0.04f, Rand(rng, 22f, 40f), Rand(rng, 0.95f, 1.35f), 1f, -70, rng);
                }
                // Long grass, tufts and wild flowers on the lawn in front of the path, sized as they
                // grow: grass knee to thigh high, tufts and flowers lower.
                string[] low = { "TallGrass", "GrassTuft", "FlowerPatch", "GrassTuft", "TallGrass" };
                for (float x = x0; x < x1; x += Rand(rng, 0.8f, 2.6f))
                {
                    string model = low[rng.Next(low.Length)];
                    float scale = model == "TallGrass" ? Rand(rng, 0.6f, 0.8f) : model == "GrassTuft" ? Rand(rng, 0.6f, 0.9f) : Rand(rng, 0.8f, 1.1f);
                    // Clear of the path's edge, so the low camera's view of the ball isn't blocked.
                    Plant(root, model, null, x, GroundAt(track, x) + 0.04f, Rand(rng, -6.5f, -3.4f), scale, 1f, -50, rng);
                }
            }
            DistantHills(track, root, x0, x1);
        }

        /// <summary>
        /// The land beyond the street: fields running out to a wooded rise, rolling hills and a
        /// mountain range, each layer further into the warm haze (Terrain kit); the painted hills
        /// strip if the kit hasn't got them.
        /// </summary>
        /// <summary>
        /// Clearings on the park lawn every so often (Leisure kit): a playground, a duck pond fringed
        /// with reeds, a bandstand, or picnic tables. Returns their x ranges, where trees stay out.
        /// </summary>
        static List<Vector2> ParkFeatures(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            var clearings = new List<Vector2>();
            if (!LevelBuildKit.HasKitModel("Leisure", "Slide")) return clearings;
            int kind = rng.Next(4);
            if (chunk != null && chunk.clearing >= 0) kind = chunk.clearing;   // the stage's own: the playground, the pond
            for (float x = x0 + Rand(rng, 10f, 30f); x < x1; x += Rand(rng, 45f, 75f))
            {
                float skip;
                if (Blocked(track, x - 6f, x + 6f, out skip)) continue;
                if (chunk != null && (x - 6f < x0 || x + 6f > x1)) continue;
                float gy = GroundAt(track, x) + 0.04f;
                switch (kind++ % 4)
                {
                    case 0:
                        Model(root, "Leisure", "Sandpit", x - 0.5f, gy, 6.8f, Rand(rng, -10f, 10f));
                        Model(root, "Leisure", "Slide", x - 3.8f, gy, 8.8f, Rand(rng, -20f, 20f));
                        Model(root, "Leisure", "SwingSet", x + 1.2f, gy, 10f, Rand(rng, -10f, 10f));
                        Model(root, "Leisure", "SeeSaw", x + 4.6f, gy, 7.4f, Rand(rng, -25f, 25f));
                        break;
                    case 1:
                        float pond = Rand(rng, 1.3f, 1.6f), pondYaw = Rand(rng, -10f, 10f);
                        Model(root, "Leisure", "DuckPond", x, gy - 0.02f, 9f, pondYaw, pond);
                        int ducks = rng.Next(2, 4);
                        for (int k = 0; k < ducks; k++)
                        {
                            // Ducks on the water (its surface 4.5 cm up the pond model), each paddling its own
                            // loop round it. (The same draws from rng as ever, so the park around stays put.)
                            float dx = Rand(rng, -1.2f, 1.2f), dz = Rand(rng, -0.5f, 0.5f), yaw = Rand(rng, 0f, 360f);
                            var duck = Duck(x, 9f, gy - 0.02f + 0.045f * pond, pondYaw, pond, k, dx, dz, yaw);
                            if (duck == null) break;
                            float pace = Rand(rng, 0.8f, 1.4f);
                            duck.paddle = (k % 2 == 0 ? 1f : -1f) * 0.12f * pace;
                        }
                        for (int k = 0; k < 4; k++)
                            Plant(root, "Reeds", null, x + Rand(rng, -3.2f, 3.2f), gy, 9f + (k % 2 == 0 ? -1f : 1f) * Rand(rng, 1.6f, 2.2f), Rand(rng, 0.9f, 1.3f), 1f, -58, rng);
                        break;
                    case 2:
                        Model(root, "Leisure", "Gazebo", x, gy, 11f, Rand(rng, -20f, 20f));
                        break;
                    default:
                        Model(root, "Leisure", "PicnicTable", x - 1.8f, gy, 6.8f, Rand(rng, -15f, 15f));
                        Model(root, "Leisure", "PicnicTable", x + 2f, gy, 8.2f, Rand(rng, -15f, 15f));
                        break;
                }
                clearings.Add(new Vector2(x - 6f, x + 6f));
            }
            return clearings;
        }

        static void DistantHills(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            if (chunk != null && !chunk.level) return;   // (a Holiday Run's are in the core scene, all along the lap)
            int ch = LevelBuildKit.Chapter;
            if (LevelBuildKit.HasKitModel("Terrain", "HillsRolling"))
            {
                float y = track.LowestGroundTop;
                Color fields = ch == 4 ? new Color(0.54f, 0.58f, 0.46f) : new Color(0.44f, 0.54f, 0.32f);
                Color? grass = null;
                // Flat fields from the end of the street ground out to the hills, so nothing floats.
                var plain = Solid(root, "Fields", new Vector3((x0 + x1) * 0.5f, y - 0.06f, (BackZ + 760f) * 0.5f - 1f), new Vector3(x1 - x0 + 2200f, 0.1f, 760f - BackZ), fields);
                plain.faces = MeshBuilder.Faces.Top;
                plain.Rebuild();
                // Layers that tile seamlessly at the kit's tile widths, each deeper in the haze: a wooded
                // rise, rolling hills, then two mountain ranges, the far one offset half a tile so its
                // peaks show between the near one's. The camera sits about 4 m up and sees about 10
                // degrees above the horizon: the near range peaks at about 8 degrees, over the back
                // row's roofs, leaving sky for the clouds.
                Layer(root, "ForestStrip", x0 - 250f, x1 + 250f, y - 0.3f, 70f, 1f, 0f, null);
                Layer(root, "HillsRolling", x0 - 450f, x1 + 450f, y - 0.4f, 230f, 1f, 0f, grass);
                Layer(root, "MountainRange1", x0 - 700f, x1 + 700f, y - 0.8f, 440f, 0.75f, 0f, grass);
                Layer(root, "MountainRange2", x0 - 900f, x1 + 900f, y - 0.8f, 640f, 1f, 0.5f, grass);
                return;
            }
            var far = CutOut(root, "DistantHills", Art.far[ch], (x0 + x1) * 0.5f, track.LowestGroundTop - 6f, 260f, 6f, -85);
            far.drawMode = SpriteDrawMode.Tiled;
            far.size = new Vector2((x1 - x0 + 900f) / 6f, Art.far[ch].bounds.size.y);
        }

        /// <summary>
        /// One layer of the distant land: copies of a landform that tiles along x, side by side from
        /// a to b at depth z, exactly a tile apart so the joins don't show (<paramref name="phase"/>
        /// shifts the row by a fraction of a tile). They cast no shadows: they are far beyond the
        /// shadow distance.
        /// </summary>
        static void Layer(Transform root, string model, float a, float b, float y, float z, float scale, float phase, Color? grass)
        {
            if (!LevelBuildKit.HasKitModel("Terrain", model)) return;
            float tile = TileWidth("Terrain", model) * scale;
            if (tile < 1f) return;
            for (float x = Mathf.Floor(a / tile) * tile + phase * tile; x < b + tile; x += tile)
                Model(root, "Terrain", model, x, y, z, 0f, scale, grass, null, null, false);
        }

        /// <summary>The distance a kit model repeats at along x (its manifest's tileWidth), else its width.</summary>
        static float TileWidth(string kit, string model)
        {
            var info = LevelBuildKit.KitInfo(kit, model);
            object tile;
            if (info != null && info.TryGetValue("tileWidth", out tile)) return System.Convert.ToSingle(tile);
            return LevelBuildKit.KitSize(kit, model).x;
        }
    }
}
