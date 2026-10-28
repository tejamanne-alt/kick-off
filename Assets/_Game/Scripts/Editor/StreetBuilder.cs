using System.Collections.Generic;
using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Builds the 3D street around the 2D gameplay plane (z = 0): ground slabs with
    /// pavements, kerbs and the road, side streets at crossings, and the scenery along
    /// both sides of the street for each chapter. Scale: about 0.9 m per unit.
    ///
    /// Depth layout (z grows away from the camera):
    ///   z &lt; -2.6       front pavement / verge, running to the bottom of the screen
    ///   -2.6 .. 2.6    the street the kid plays on (gameplay at z = 0)
    ///   2.6 .. 4.6     back pavement with utility poles
    ///   z &gt; 4.6        property walls, houses, shops, trees; the sea on the beach
    /// </summary>
    public static class StreetBuilder
    {
        public const float FrontZ = -16f;
        public const float RoadHalf = 2.6f;
        public const float PropertyZ = 4.6f;
        public const float PoleZ = 4.1f;
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

        static List<StripSpec> StripsFor(int chapter)
        {
            var white = Color.white;
            var s = new List<StripSpec>();
            switch (chapter)
            {
                case 2:   // market: cobbled street between paved shop fronts
                    s.Add(new StripSpec(FrontZ, -RoadHalf, 0.06f, ProceduralArt.Surface.Paving, new Color(1f, 0.97f, 0.92f)));
                    s.Add(new StripSpec(-RoadHalf, RoadHalf, 0f, ProceduralArt.Surface.Cobbles, white));
                    s.Add(new StripSpec(RoadHalf, PropertyZ + 0.6f, 0.06f, ProceduralArt.Surface.Paving, new Color(1f, 0.97f, 0.92f)));
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0.06f, ProceduralArt.Surface.Paving, new Color(0.92f, 0.9f, 0.86f)));
                    break;
                case 3:   // beach: sand down to wet sand at the water's edge
                    s.Add(new StripSpec(FrontZ, 5.6f, 0f, ProceduralArt.Surface.Sand, white));
                    s.Add(new StripSpec(5.6f, 9f, -0.12f, ProceduralArt.Surface.Sand, new Color(0.82f, 0.74f, 0.62f)));
                    break;
                case 5:   // park: gravel path between lawns
                    s.Add(new StripSpec(FrontZ, -RoadHalf, 0.04f, ProceduralArt.Surface.Grass, white));
                    s.Add(new StripSpec(-RoadHalf, RoadHalf, 0f, ProceduralArt.Surface.Gravel, white));
                    s.Add(new StripSpec(RoadHalf, PropertyZ + 0.6f, 0.04f, ProceduralArt.Surface.Grass, white));
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0.04f, ProceduralArt.Surface.Grass, new Color(0.92f, 0.95f, 0.9f)));
                    break;
                default:  // home street (1) and underpass (4): road with kerbs and pavements
                {
                    var pave = chapter == 4 ? ProceduralArt.Surface.Concrete : ProceduralArt.Surface.Paving;
                    s.Add(new StripSpec(FrontZ, -RoadHalf - 0.2f, 0.14f, pave, white));
                    s.Add(new StripSpec(-RoadHalf - 0.2f, -RoadHalf, 0.16f, ProceduralArt.Surface.Kerb, white));
                    s.Add(new StripSpec(-RoadHalf, RoadHalf, 0f, ProceduralArt.Surface.Asphalt, white));
                    s.Add(new StripSpec(RoadHalf, RoadHalf + 0.2f, 0.16f, ProceduralArt.Surface.Kerb, white));
                    s.Add(new StripSpec(RoadHalf + 0.2f, PropertyZ + 0.6f, 0.14f, pave, white));
                    // Driveways, yards and gardens behind the property line, under the houses.
                    s.Add(new StripSpec(PropertyZ + 0.6f, BackZ, 0.14f, ProceduralArt.Surface.Concrete, new Color(0.9f, 0.9f, 0.88f)));
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

        /// <summary>One slab of street from fromX to toX with its gameplay surface at <paramref name="top"/>.</summary>
        public static GameObject Slab(Transform parent, string name, float fromX, float toX, float top, bool closeLeft, bool closeRight)
        {
            int ch = LevelBuildKit.Chapter;
            var specs = StripsFor(ch);
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

            if (HasRoadLines(ch))
            {
                // White edge lines along the road.
                foreach (float z in new[] { -RoadHalf + 0.35f, RoadHalf - 0.35f })
                    Patch(go.transform, "EdgeLine", fromX + 0.1f, toX - 0.1f, top, z - 0.06f, z + 0.06f, new Color(0.95f, 0.95f, 0.93f));
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
        /// Where the pavement meets a side street: the main road surface runs straight through,
        /// zebra stripes cross the street, and the side street runs away from the camera with
        /// kerbs and a stop line.
        /// </summary>
        public static void CrossingStreet(Transform parent, float fromX, float toX, float top)
        {
            int ch = LevelBuildKit.Chapter;
            var asphalt = Art.surfaces[ch == 2 ? ProceduralArt.Surface.Cobbles : ProceduralArt.Surface.Asphalt];
            var kerb = Art.surfaces[ProceduralArt.Surface.Kerb];
            var root = new GameObject("SideStreet").transform;
            root.SetParent(parent, false);

            // Road surface from the bottom of the screen to far up the side street.
            var surface = new GameObject("Road");
            surface.transform.SetParent(root, false);
            var slab = surface.AddComponent<StreetSlab>();
            slab.fromX = fromX; slab.toX = toX; slab.top = top; slab.bottom = top - 14f;
            slab.closeLeft = slab.closeRight = true;
            slab.materials = 3;
            slab.sideColor = SideColor(ch);
            slab.sideSubmesh = 2;
            slab.strips.Add(new StreetSlab.Strip(FrontZ, 70f, 0f, 0, Color.white));
            surface.GetComponent<MeshRenderer>().sharedMaterials = new[] { asphalt, kerb, Art.solid };
            slab.Rebuild();

            // Kerbs along the side street, behind the main street.
            foreach (float x in new[] { fromX + 0.1f, toX - 0.1f })
                Solid(root, "SideKerb", new Vector3(x, top + 0.08f, (PropertyZ + 70f) * 0.5f), new Vector3(0.22f, 0.16f, 70f - PropertyZ), Color.white, kerb);

            // Zebra stripes across the main street, a stop line and centre dashes up the side street.
            for (float x = fromX + 0.45f; x < toX - 0.3f; x += 0.95f)
                Patch(root, "Zebra", x, x + 0.5f, top, -RoadHalf + 0.25f, RoadHalf - 0.25f, new Color(0.95f, 0.95f, 0.93f));
            Patch(root, "StopLine", fromX + 0.3f, (fromX + toX) * 0.5f, top, PropertyZ + 1.2f, PropertyZ + 1.45f, new Color(0.95f, 0.95f, 0.93f));
            for (float z = PropertyZ + 3f; z < 70f; z += 4f)
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

        /// <summary>Does [a, b] overlap a side street (where the back row must stay open)?</summary>
        static bool Blocked(LevelBuildKit.TrackBuilder track, float a, float b, out float skipTo)
        {
            foreach (var area in track.OpenAreas)
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
            return house;
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
            FrontVerge(track, root, rng, x0, x1, ch);
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
                line.poles.Add(new Vector3(x, GroundAt(track, x) + 0.14f, PoleZ));
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
                float cx = x + lot * 0.5f, gy = GroundAt(track, cx) + 0.14f;

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
            // A second row of houses further back gives the street depth.
            for (float x = x0 - 20f; x < x1 + 20f; x += Rand(rng, 10f, 14f))
            {
                float gy = GroundAt(track, x) + 0.14f;
                Building(root, x, gy, Rand(rng, 20f, 24f), rng.NextDouble() < 0.5 ? ProceduralArt.FacadeKind.HouseGable : ProceduralArt.FacadeKind.HouseLong,
                    rng.NextDouble() < 0.5 ? House3D.RoofStyle.GableToStreet : House3D.RoofStyle.GableSideways, 7f, 2.4f, new Color(0.93f, 0.93f, 0.9f), roofDark);
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
                float cx = x + w * 0.5f, gy = GroundAt(track, cx) + 0.06f;
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
            for (float x = x0 - 20f; x < x1 + 20f; x += Rand(rng, 13f, 16f))
                Building(root, x, GroundAt(track, x), Rand(rng, 22f, 28f), ProceduralArt.FacadeKind.Apartment, House3D.RoofStyle.Flat, 10f, 0f, new Color(0.92f, 0.88f, 0.82f), new Color(0.6f, 0.6f, 0.62f));
        }

        static void Beach(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            float sea = track.LowestGroundTop - 0.3f;
            var water = Solid(root, "Sea", new Vector3((x0 + x1) * 0.5f, sea - 0.05f, 480f), new Vector3(x1 - x0 + 1600f, 0.1f, 950f), Color.white, Art.surfaces[ProceduralArt.Surface.Sea]);
            water.faces = MeshBuilder.Faces.Top;
            water.Rebuild();
            for (float x = x0; x < x1; x += Rand(rng, 30f, 45f))
                CutOut(root, "Lifeguard", Art.mid[3, 0], x, GroundAt(track, x), 7.2f, 1f, -60);
            for (float x = x0 + 8f; x < x1; x += Rand(rng, 12f, 20f))
                CutOut(root, "Parasol", Art.mid[3, 1], x, GroundAt(track, x), Rand(rng, 3.6f, 5.4f), 1f, -58, rng.NextDouble() < 0.5);
            for (float x = x0 + 15f; x < x1; x += Rand(rng, 25f, 40f))
                CutOut(root, "Rocks", Art.mid[3, 2], x, GroundAt(track, x), 8f, 1f, -59);
            // Wooded headlands out on the horizon.
            for (int i = 0; i < 3; i++)
                CutOut(root, "Headland", Art.headland, x0 + (x1 - x0) * (0.15f + i * 0.4f) + Rand(rng, -40f, 40f), sea - 0.5f, 650f + i * 60f, 10f, -85, i % 2 == 1);
        }

        static void City(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1)
        {
            var hoarding = Art.surfaces[ProceduralArt.Surface.Hoarding];
            for (float x = x0; x < x1;)
            {
                float w = Rand(rng, 11f, 14f), skip;
                if (Blocked(track, x, x + w, out skip)) { x = skip; continue; }
                float cx = x + w * 0.5f, gy = GroundAt(track, cx) + 0.14f;
                if (rng.NextDouble() < 0.5)
                    Solid(root, "Hoarding", new Vector3(cx, gy + 1.3f, PropertyZ + 0.2f), new Vector3(w - 0.3f, 2.6f, 0.2f), Color.white, hoarding);
                if (rng.NextDouble() < 0.5)
                    Building(root, cx, gy, PropertyZ + 3f, ProceduralArt.FacadeKind.Warehouse, House3D.RoofStyle.Shed, 8f, 1.2f, new Color(0.78f, 0.74f, 0.7f), new Color(0.5f, 0.52f, 0.56f));
                else
                    Building(root, cx, gy, PropertyZ + 5f, ProceduralArt.FacadeKind.Apartment, House3D.RoofStyle.Flat, 10f, 0f, new Color(0.92f, 0.88f, 0.82f), new Color(0.6f, 0.6f, 0.62f));
                x += w;
            }
            for (float x = x0; x < x1; x += Rand(rng, 40f, 60f))
                CutOut(root, "Crane", Art.mid[4, 2], x, GroundAt(track, x), 45f, 2f, -75);
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
            // The school at the end of the run.
            float schoolX = track.GoalX > track.MinX ? track.GoalX : track.MaxX - 10f;
            var school = Building(root, schoolX, GroundAt(track, schoolX), 26f, ProceduralArt.FacadeKind.School, House3D.RoofStyle.Flat, 12f, 0f, new Color(0.95f, 0.94f, 0.9f), new Color(0.7f, 0.7f, 0.72f));
            Solid(root, "ClockTower", school.transform.position + new Vector3(0f, 11.6f, 2f), new Vector3(4f, 3.6f, 4f), new Color(0.95f, 0.94f, 0.9f));
            DistantHills(track, root, x0, x1);
        }

        static void DistantHills(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1)
        {
            int ch = LevelBuildKit.Chapter;
            var far = CutOut(root, "DistantHills", Art.far[ch], (x0 + x1) * 0.5f, track.LowestGroundTop - 6f, 260f, 6f, -85);
            far.drawMode = SpriteDrawMode.Tiled;
            far.size = new Vector2((x1 - x0 + 900f) / 6f, Art.far[ch].bounds.size.y);
        }

        /// <summary>Low things on the near side of the street: planters with shrubs, bike racks, verge plants.</summary>
        static void FrontVerge(LevelBuildKit.TrackBuilder track, Transform root, System.Random rng, float x0, float x1, int ch)
        {
            if (ch == 3) return;
            for (float x = x0; x < x1; x += Rand(rng, 12f, 22f))
            {
                float skip;
                if (Blocked(track, x - 1f, x + 1f, out skip)) continue;
                float gy = GroundAt(track, x) + 0.14f, z = Rand(rng, -6.5f, -4.5f);
                if (rng.NextDouble() < 0.6)
                {
                    Solid(root, "Planter", new Vector3(x, gy + 0.22f, z), new Vector3(2f, 0.44f, 0.8f), new Color(0.72f, 0.36f, 0.28f));
                    CutOut(root, "PlanterBush", Art.bush, x, gy + 0.4f, z, 0.8f, 30);
                }
                else
                {
                    // Bike rack: two inverted-U hoops.
                    foreach (float dx in new[] { -0.5f, 0.5f })
                    {
                        Solid(root, "RackPost", new Vector3(x + dx - 0.35f, gy + 0.4f, z), new Vector3(0.06f, 0.8f, 0.06f), new Color(0.45f, 0.47f, 0.45f));
                        Solid(root, "RackPost", new Vector3(x + dx + 0.35f, gy + 0.4f, z), new Vector3(0.06f, 0.8f, 0.06f), new Color(0.45f, 0.47f, 0.45f));
                        Solid(root, "RackTop", new Vector3(x + dx, gy + 0.8f, z), new Vector3(0.76f, 0.06f, 0.06f), new Color(0.45f, 0.47f, 0.45f));
                    }
                }
            }
        }
    }
}
