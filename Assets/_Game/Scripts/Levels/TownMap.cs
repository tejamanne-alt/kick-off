using System;
using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Levels
{
    // ------------------------------------------------------------------ the file's shape (read with JsonUtility: objects and arrays only)

    [Serializable] public class LayoutPoint { public float x; public float y; }
    [Serializable] public class LayoutRect { public float x; public float y; public float w; public float h; }
    [Serializable] public class LayoutPlace { public string id; public float x; public float y; }
    [Serializable] public class LayoutRoute { public string id; public LayoutPoint[] points; }
    [Serializable] public class LayoutNode { public string id; public float x; public float y; public string label; }
    [Serializable] public class LayoutDistrict { public string id; public float x; public float y; }
    [Serializable] public class LayoutStreet { public string name; public float x; public float y; public float angle; }
    /// <summary>Where a stop between two levels is on the picture (Levels/RouteTable's stop id and route): a point on its route.</summary>
    [Serializable] public class LayoutStop { public string id; public string route; public float x; public float y; }

    /// <summary>Resources/TownMapLayout.json: where everything is in the town picture (Resources/UI/TownMap.jpg), in its pixels.</summary>
    [Serializable]
    public class TownMapLayout
    {
        public string image;
        public int width;
        public int height;
        public LayoutRect core;
        public LayoutPlace[] places;
        public LayoutRoute[] routes;
        public LayoutNode[] nodes;
        public LayoutDistrict[] districts;
        public LayoutStreet[] streets;
        /// <summary>The stops between the levels where the picture shows them (the station by the railway bridge, the surf school on the boardwalk...).</summary>
        public LayoutStop[] stops;
        /// <summary>True in a stand-in layout made from abstract geometry (not from the real picture): some checks that need real roads are skipped for it.</summary>
        public bool placeholder;
    }

    // ------------------------------------------------------------------ what the game works with

    /// <summary>Which side of its node a level's name is written on.</summary>
    public enum LabelSide { Below, Above, Left, Right }

    /// <summary>One of the six routes from the house to the school, a polyline in picture pixels.</summary>
    public sealed class TownRoute
    {
        public readonly string id;
        public readonly Vector2[] points;
        public readonly float length;
        public TownRoute(string id, Vector2[] points) { this.id = id; this.points = points; length = TownMap.Length(points); }
    }

    /// <summary>A level on the map: where its node is and on which side its name goes.</summary>
    public sealed class TownNode
    {
        public readonly string levelId;
        public readonly Vector2 pos;
        public readonly LabelSide side;
        public TownNode(string levelId, Vector2 pos, LabelSide side) { this.levelId = levelId; this.pos = pos; this.side = side; }
    }

    public sealed class TownDistrict
    {
        public readonly string id;
        public readonly Vector2 pos;
        public TownDistrict(string id, Vector2 pos) { this.id = id; this.pos = pos; }
        /// <summary>The string key of the district's name ("district.beach").</summary>
        public string NameKey { get { return "district." + id; } }
    }

    public sealed class TownStreet
    {
        public readonly string name;
        public readonly Vector2 pos;
        public readonly float angle;
        public TownStreet(string name, Vector2 pos, float angle) { this.name = name; this.pos = pos; this.angle = angle; }
    }

    /// <summary>
    /// The town map's data (docs/WORLD_MAP.md): where the house, the school, the six routes, every level's node and the
    /// names are on the rendered picture of the town. The picture is Resources/UI/TownMap.jpg (3200 x 1800); its CORE, the
    /// central 2400 x 1350, holds everything that matters, and the ring round it is more town for screens of other shapes.
    /// The layout is Resources/TownMapLayout.json, read once and cached (<see cref="Layout"/>): in play from the Resources
    /// folder, and in the editor (edit-mode tests) from the file itself if Resources has not got it yet. All positions are in
    /// picture pixels, origin top left, y down. ChapterMapScreen turns them into UI; TownMapTests checks the file.
    /// </summary>
    public static class TownMap
    {
        /// <summary>The layout's Resources path (no extension).</summary>
        public const string LayoutResource = "TownMapLayout";
        /// <summary>The same file's place under Application.dataPath, for edit-mode tests.</summary>
        public const string LayoutFile = "/_Game/Resources/TownMapLayout.json";
        /// <summary>The picture's Resources path (no extension).</summary>
        public const string ImageResource = "UI/TownMap";

        /// <summary>The picture is this big, and its core is this part of it.</summary>
        public const int ImageWidth = 3200, ImageHeight = 1800;
        public static readonly Rect ExpectedCore = new Rect(400f, 225f, 2400f, 1350f);

        /// <summary>A node's disc is this wide across (picture pixels), and its name is set in a box of <see cref="LabelSize"/> beside it.</summary>
        public const float NodeDiameter = 150f;
        public const float NodeRadius = NodeDiameter * 0.5f;
        /// <summary>The radius of a stop's marker on its route (picture pixels; the stops between the levels, Levels/RouteTable).</summary>
        public const float StopRadius = 21f;
        public static readonly Vector2 LabelSize = new Vector2(300f, 56f);
        /// <summary>The gap between a node's disc and its name's box.</summary>
        public const float LabelGap = 12f;

        static TownMapLayout layout;
        static TownRoute[] routes;
        static TownNode[] nodes;
        static TownDistrict[] districts;
        static TownStreet[] streets;
        static Dictionary<string, Vector2> places;
        static Dictionary<string, Vector2> stopPoints;
        static Rect core;

        /// <summary>Where the layout came from ("Resources/TownMapLayout", a file path, or "(none)"), and why it could not be read.</summary>
        public static string Source = "(not loaded)";
        public static string Problem = "";

        /// <summary>The string keys the map screen uses on top of the districts', routes' and levels' names (checked by TownMapTests).</summary>
        public static readonly string[] ScreenKeys = { "map.choose", "map.levels", "map.here", "unlock.cta", "menu.soon", "place.home", "place.school" };

        // ------------------------------------------------------------------ loading

        /// <summary>The layout, loaded on first use (an empty one if the file is missing or broken: <see cref="Available"/> is false then).</summary>
        public static TownMapLayout Layout
        {
            get
            {
                if (layout == null) Load();
                return layout;
            }
        }

        /// <summary>Whether a layout with at least the core, the places and the routes was found.</summary>
        public static bool Available
        {
            get
            {
                if (layout == null) Load();
                return routes != null && routes.Length > 0 && places.Count > 0 && core.width > 0f;
            }
        }

        /// <summary>Forget the cached layout (tests, and a picture swapped while the editor runs).</summary>
        public static void Reload()
        {
            layout = null;
            Load();
        }

        static void Load()
        {
            string json = null;
            Source = "(none)";
            Problem = "";
            var asset = Resources.Load<TextAsset>(LayoutResource);
            if (asset != null)
            {
                json = asset.text;
                Source = "Resources/" + LayoutResource;
            }
#if UNITY_EDITOR
            if (json == null)
            {
                try
                {
                    string path = Application.dataPath + LayoutFile;
                    if (System.IO.File.Exists(path))
                    {
                        json = System.IO.File.ReadAllText(path);
                        Source = path;
                    }
                }
                catch (Exception e) { Problem = e.Message; }
            }
#endif
            Apply(json != null ? Parse(json) : null);
            if (json == null && Problem.Length == 0) Problem = "TownMapLayout.json was not found";
        }

        /// <summary>Read a layout from its JSON text (null, with <see cref="Problem"/> set, if it cannot be read).</summary>
        public static TownMapLayout Parse(string json)
        {
            try
            {
                var parsed = JsonUtility.FromJson<TownMapLayout>(json);
                if (parsed == null) Problem = "the layout is empty";
                return parsed;
            }
            catch (Exception e)
            {
                Problem = e.Message;
                return null;
            }
        }

        /// <summary>Use <paramref name="parsed"/> as the layout (tests can feed their own).</summary>
        public static void Apply(TownMapLayout parsed)
        {
            layout = parsed ?? new TownMapLayout();
            if (layout.core == null) layout.core = new LayoutRect();
            core = new Rect(layout.core.x, layout.core.y, layout.core.w, layout.core.h);

            places = new Dictionary<string, Vector2>();
            if (layout.places != null)
                foreach (var p in layout.places) if (p != null && !string.IsNullOrEmpty(p.id)) places[p.id] = new Vector2(p.x, p.y);

            var routeList = new List<TownRoute>();
            if (layout.routes != null)
                foreach (var r in layout.routes)
                {
                    if (r == null || r.points == null || r.points.Length < 2) continue;
                    var pts = new Vector2[r.points.Length];
                    for (int i = 0; i < pts.Length; i++) pts[i] = new Vector2(r.points[i].x, r.points[i].y);
                    routeList.Add(new TownRoute(r.id, pts));
                }
            routes = routeList.ToArray();

            var nodeList = new List<TownNode>();
            if (layout.nodes != null)
                foreach (var n in layout.nodes) if (n != null && !string.IsNullOrEmpty(n.id)) nodeList.Add(new TownNode(n.id, new Vector2(n.x, n.y), SideOf(n.label)));
            nodes = nodeList.ToArray();

            var districtList = new List<TownDistrict>();
            if (layout.districts != null)
                foreach (var d in layout.districts) if (d != null && !string.IsNullOrEmpty(d.id)) districtList.Add(new TownDistrict(d.id, new Vector2(d.x, d.y)));
            districts = districtList.ToArray();

            var streetList = new List<TownStreet>();
            if (layout.streets != null)
                foreach (var s in layout.streets) if (s != null && !string.IsNullOrEmpty(s.name)) streetList.Add(new TownStreet(s.name, new Vector2(s.x, s.y), s.angle));
            streets = streetList.ToArray();

            stopPoints = new Dictionary<string, Vector2>();
            if (layout.stops != null)
                foreach (var s in layout.stops) if (s != null && !string.IsNullOrEmpty(s.id)) stopPoints[s.id] = new Vector2(s.x, s.y);
        }

        static LabelSide SideOf(string label)
        {
            switch (label)
            {
                case "above": return LabelSide.Above;
                case "left": return LabelSide.Left;
                case "right": return LabelSide.Right;
                default: return LabelSide.Below;
            }
        }

        // ------------------------------------------------------------------ the data

        /// <summary>The picture's Resources path as the layout names it.</summary>
        public static string Image { get { return string.IsNullOrEmpty(Layout.image) ? ImageResource : Layout.image; } }

        /// <summary>The picture's size in pixels (the layout's own width and height).</summary>
        public static Vector2 FrameSize { get { return new Vector2(Layout.width > 0 ? Layout.width : ImageWidth, Layout.height > 0 ? Layout.height : ImageHeight); } }

        /// <summary>The core of the picture (pixels): everything the player needs is inside it.</summary>
        public static Rect Core { get { if (layout == null) Load(); return core; } }

        /// <summary>A place's position ("home", "school"), or the core's middle if the layout has no such place.</summary>
        public static Vector2 Place(string id)
        {
            if (layout == null) Load();
            Vector2 p;
            return places.TryGetValue(id, out p) ? p : Core.center;
        }

        public static Vector2 Home { get { return Place("home"); } }
        public static Vector2 School { get { return Place("school"); } }

        /// <summary>The six routes, in the order of the file (RouteTable's order).</summary>
        public static TownRoute[] Routes { get { if (layout == null) Load(); return routes; } }

        /// <summary>A route by its id (RouteTable's), or null.</summary>
        public static TownRoute Route(string id)
        {
            foreach (var r in Routes) if (r.id == id) return r;
            return null;
        }

        public static TownNode[] Nodes { get { if (layout == null) Load(); return nodes; } }

        /// <summary>The node of a story level or challenge (by its level id), or null.</summary>
        public static TownNode Node(string levelId)
        {
            foreach (var n in Nodes) if (n.levelId == levelId) return n;
            return null;
        }

        public static TownDistrict[] Districts { get { if (layout == null) Load(); return districts; } }
        public static TownStreet[] Streets { get { if (layout == null) Load(); return streets; } }

        /// <summary>
        /// The point the layout gives for a stop (by its RouteTable id): where the picture shows the place, on its route. False if
        /// the layout does not place it.
        /// </summary>
        public static bool StopPoint(string stopId, out Vector2 point)
        {
            if (layout == null) Load();
            point = Vector2.zero;
            return stopId != null && stopPoints.TryGetValue(stopId, out point);
        }

        /// <summary>
        /// Where the <paramref name="index"/>-th stop of a route is drawn (Levels/RouteTable: the stop between its levels
        /// <paramref name="index"/> and <paramref name="index"/> + 1): at the place the layout gives for it (the station at the
        /// foot of the railway bridge, the surf school on the boardwalk...), put exactly on the route line; if the layout has no
        /// place for it, on the line halfway between the two levels' nodes as measured along it. Null if the layout lacks the
        /// route (or, for the halfway point, either node).
        /// </summary>
        public static Vector2? StopPosition(string routeId, int index)
        {
            int routeIndex = RouteTable.IndexOf(routeId);
            if (routeIndex < 0) return null;
            var route = RouteTable.All[routeIndex];
            if (index < 0 || route.stops == null || index >= route.stops.Length || index + 1 >= route.levels.Length) return null;
            var line = Route(routeId);
            if (line == null || line.points.Length < 2) return null;
            Vector2 place;
            if (StopPoint(route.stops[index], out place))
            {
                Vector2 onLine;
                DistanceTo(line.points, place, out onLine);
                return onLine;
            }
            var a = Node(route.levels[index]);
            var b = Node(route.levels[index + 1]);
            if (a == null || b == null) return null;
            float mid = (DistanceAlong(line.points, a.pos) + DistanceAlong(line.points, b.pos)) * 0.5f;
            return At(line.points, mid);
        }

        /// <summary>
        /// The box (picture pixels) a node's name is written in: <see cref="LabelSize"/>, beside the disc on the node's side with
        /// <see cref="LabelGap"/> between them.
        /// </summary>
        public static Rect LabelRect(TownNode node)
        {
            Vector2 c = node.pos;
            switch (node.side)
            {
                case LabelSide.Above: c.y -= NodeRadius + LabelGap + LabelSize.y * 0.5f; break;
                case LabelSide.Left: c.x -= NodeRadius + LabelGap + LabelSize.x * 0.5f; break;
                case LabelSide.Right: c.x += NodeRadius + LabelGap + LabelSize.x * 0.5f; break;
                default: c.y += NodeRadius + LabelGap + LabelSize.y * 0.5f; break;
            }
            return new Rect(c.x - LabelSize.x * 0.5f, c.y - LabelSize.y * 0.5f, LabelSize.x, LabelSize.y);
        }

        /// <summary>
        /// The colour of a route's line and nodes: the colour of its chapter, except that chapter 4's two routes get two shades
        /// of it (the underpass a deeper violet, the building site a lighter orchid), so all six tell apart.
        /// </summary>
        public static Color RouteColor(string routeId, Color chapterColor)
        {
            switch (routeId)
            {
                case "underpass": return Color.Lerp(chapterColor, new Color(0.18f, 0.14f, 0.42f), 0.38f);
                case "site": return Color.Lerp(chapterColor, new Color(0.95f, 0.6f, 0.9f), 0.45f);
                default: return chapterColor;
            }
        }

        /// <summary>Every string key the map uses (for the tests that check both languages have them).</summary>
        public static List<string> LocKeys()
        {
            var keys = new List<string>(ScreenKeys);
            foreach (var d in Districts) keys.Add(d.NameKey);
            foreach (var r in RouteTable.All) keys.Add(r.NameKey);
            foreach (var stop in RouteTable.Stops) keys.Add(stop.NameKey);
            foreach (var n in Nodes) keys.Add("level." + n.levelId);
            return keys;
        }

        // ------------------------------------------------------------------ geometry helpers (pure)

        public static float Length(Vector2[] line)
        {
            float total = 0f;
            for (int i = 0; i + 1 < line.Length; i++) total += Vector2.Distance(line[i], line[i + 1]);
            return total;
        }

        /// <summary>The point <paramref name="distance"/> along the line from its start.</summary>
        public static Vector2 At(Vector2[] line, float distance)
        {
            float left = Mathf.Max(0f, distance);
            for (int i = 0; i + 1 < line.Length; i++)
            {
                float seg = Vector2.Distance(line[i], line[i + 1]);
                if (left <= seg) return Vector2.Lerp(line[i], line[i + 1], seg > 0f ? left / seg : 0f);
                left -= seg;
            }
            return line[line.Length - 1];
        }

        /// <summary>The direction of the line at <paramref name="distance"/> (a unit vector).</summary>
        public static Vector2 DirectionAt(Vector2[] line, float distance)
        {
            Vector2 a = At(line, distance - 6f), b = At(line, distance + 6f);
            Vector2 d = b - a;
            return d.sqrMagnitude > 0f ? d.normalized : new Vector2(1f, 0f);
        }

        /// <summary>The distance from <paramref name="p"/> to the nearest point of the line, which is returned in <paramref name="nearest"/>.</summary>
        public static float DistanceTo(Vector2[] line, Vector2 p, out Vector2 nearest)
        {
            float best = float.MaxValue;
            nearest = line[0];
            for (int i = 0; i + 1 < line.Length; i++)
            {
                Vector2 a = line[i], ab = line[i + 1] - a;
                float len2 = ab.sqrMagnitude;
                float t = len2 > 0f ? Mathf.Clamp01(Vector2.Dot(p - a, ab) / len2) : 0f;
                Vector2 q = a + ab * t;
                float d = Vector2.Distance(p, q);
                if (d < best) { best = d; nearest = q; }
            }
            return best;
        }

        public static float DistanceTo(Vector2[] line, Vector2 p)
        {
            Vector2 q;
            return DistanceTo(line, p, out q);
        }

        /// <summary>How far along the line the point nearest to <paramref name="p"/> is.</summary>
        public static float DistanceAlong(Vector2[] line, Vector2 p)
        {
            float best = float.MaxValue, bestAt = 0f, at = 0f;
            for (int i = 0; i + 1 < line.Length; i++)
            {
                Vector2 a = line[i], ab = line[i + 1] - a;
                float len = ab.magnitude, len2 = ab.sqrMagnitude;
                float t = len2 > 0f ? Mathf.Clamp01(Vector2.Dot(p - a, ab) / len2) : 0f;
                float d = Vector2.Distance(p, a + ab * t);
                if (d < best) { best = d; bestAt = at + len * t; }
                at += len;
            }
            return bestAt;
        }

        /// <summary>The distance from a point to a rectangle (0 inside it).</summary>
        public static float DistanceToRect(Rect r, Vector2 p)
        {
            float dx = Mathf.Max(Mathf.Max(r.xMin - p.x, 0f), p.x - r.xMax), dy = Mathf.Max(Mathf.Max(r.yMin - p.y, 0f), p.y - r.yMax);
            return Mathf.Sqrt(dx * dx + dy * dy);
        }

        /// <summary>The gap between two rectangles (0 where they touch or overlap).</summary>
        public static float GapBetween(Rect a, Rect b)
        {
            float dx = Mathf.Max(Mathf.Max(a.xMin - b.xMax, b.xMin - a.xMax), 0f), dy = Mathf.Max(Mathf.Max(a.yMin - b.yMax, b.yMin - a.yMax), 0f);
            return Mathf.Sqrt(dx * dx + dy * dy);
        }

        /// <summary>The distance from a rectangle to the nearest point of a line (0 when the line passes through it).</summary>
        public static float DistanceToLine(Rect r, Vector2[] line)
        {
            float best = float.MaxValue;
            for (int i = 0; i + 1 < line.Length; i++)
            {
                Vector2 a = line[i], b = line[i + 1];
                float len = Vector2.Distance(a, b);
                int steps = Mathf.Max(1, Mathf.CeilToInt(len / 8f));
                for (int k = 0; k <= steps; k++) best = Mathf.Min(best, DistanceToRect(r, Vector2.Lerp(a, b, k / (float)steps)));
            }
            return best;
        }
    }
}
