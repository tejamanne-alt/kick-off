using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Levels
{
    /// <summary>Where a name goes on the town map, as the screen draws it.</summary>
    public struct MapName
    {
        /// <summary>The box the lettering takes, with a little air (picture pixels, origin top left, y down).</summary>
        public Rect box;
        /// <summary>The name, with a line break in it if it takes two lines.</summary>
        public string text;
        public int fontSize;
        /// <summary>How the lines sit in the box: -1 against its left side, 0 centred, 1 against its right side (towards the node).</summary>
        public int align;
        /// <summary>False if every spot touched something it must not (the least bad one was taken).</summary>
        public bool clear;
        /// <summary>True if it lies over one of the other routes' nodes (drawn smaller, see <see cref="TownMapNames.OtherNodeScale"/>).</summary>
        public bool overOther;
    }

    /// <summary>
    /// The level names on the town map, placed where they fit (docs/WORLD_MAP.md, "The map screen"). Only the focused route's
    /// levels are named. Each name goes beside its node on the side the layout prefers, else on one of eight spots round it
    /// (below, above, right, left, the sides also slid a little along, and the four corners), on two lines if that helps (broken
    /// so that no line is wider than 380, 300 or 200 px), and one font size smaller as a last resort. It never covers its own
    /// route's nodes, stars and stop markers, the pins, the names already placed or the screen's other texts, keeps 30 px from other names
    /// where it can, and preferably keeps off the other routes' nodes (drawn smaller then). Sizes come from the
    /// label font's own advances (Lilita One, the face UIKit draws bold labels in), so the screen and the tests agree.
    /// </summary>
    public static class TownMapNames
    {
        /// <summary>The names' font size in picture pixels (about 24 canvas units at the usual scale), and the last resort (22).</summary>
        public const int FontSize = 50, SmallFontSize = 46;
        /// <summary>A name longer than this (at its size) breaks onto two lines.</summary>
        public const float OneLineMax = 380f;
        /// <summary>The other routes' nodes are drawn at this size while a route is in focus.</summary>
        public const float OtherNodeScale = 0.7f;
        /// <summary>A pin's head (the house's and the school's markers), in picture pixels.</summary>
        public const float PinHead = 40f;

        const float Gap = TownMap.LabelGap, Pad = 6f, Air = 8f;
        const float NameGap = 30f;           // wanted between two names, so that each reads as one ("Parked Cars", "Up the Hill")
        const float CornerIn = 0.72f;        // how far round the disc a corner spot starts (a fraction of the radius)
        const float StarsBelow = 98f;        // the stars' pill reaches this far below a node's centre

        // The advances of the label font at size 50, in tenths of a pixel (measured from LilitaOne-Regular.ttf).
        const string Glyphs = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~áéíóúñüÁÉÍÓÚÑÜ¡¿çÇàèìòùâêîôûäëïö";
        static readonly short[] Advances =
        {
            94, 143, 230, 417, 265, 399, 333, 150, 215, 211, 278, 301, 152, 262, 115, 287, 320, 203, 262, 264, 299, 262, 288, 250, 285, 282,
            138, 138, 242, 290, 225, 292, 433, 328, 297, 280, 308, 247, 236, 310, 322, 215, 231, 310, 218, 453, 324, 348, 285, 353, 295,
            265, 251, 314, 330, 477, 342, 308, 282, 192, 293, 192, 343, 318, 175, 258, 260, 212, 282, 243, 188, 258, 250, 137, 135, 265,
            136, 394, 275, 257, 278, 255, 198, 225, 184, 272, 260, 376, 278, 268, 227, 181, 314, 181, 230, 258, 243, 133, 257, 272, 275,
            272, 328, 244, 216, 348, 314, 328, 314, 143, 292, 212, 273, 258, 243, 133, 257, 272, 258, 243, 133, 257, 272, 258, 243, 133,
            257,
        };
        const float LineHeight50 = 58f * 0.95f;    // ascent and descent at 50, at the bold labels' line spacing (UIKit.Label)

        /// <summary>The width of one line of <paramref name="text"/> at <paramref name="size"/>, in picture pixels.</summary>
        public static float Width(string text, int size)
        {
            float tenths = 0f;
            foreach (char c in text)
            {
                int i = Glyphs.IndexOf(c);
                tenths += i >= 0 ? Advances[i] : 260f;
            }
            return tenths * 0.1f * size / 50f;
        }

        /// <summary>The height of <paramref name="lines"/> lines at <paramref name="size"/>.</summary>
        public static float Height(int lines, int size)
        {
            return lines * LineHeight50 * size / 50f;
        }

        /// <summary>
        /// <paramref name="text"/> as it is written: one line if it is no wider than <paramref name="max"/> (or has no space),
        /// else two, broken at the space that makes the longer line shortest.
        /// </summary>
        public static string[] Lines(string text, int size, float max)
        {
            if (Width(text, size) <= max || text.IndexOf(' ') < 0) return new[] { text };
            string[] words = text.Split(' ');
            string[] best = null;
            float bestWidth = float.MaxValue;
            for (int i = 1; i < words.Length; i++)
            {
                string a = string.Join(" ", words, 0, i), b = string.Join(" ", words, i, words.Length - i);
                float w = Mathf.Max(Width(a, size), Width(b, size));
                if (w < bestWidth) { bestWidth = w; best = new[] { a, b }; }
            }
            return best;
        }

        /// <summary>The box round a pin standing on <paramref name="p"/> (its head and its point).</summary>
        public static Rect PinBox(Vector2 p)
        {
            return new Rect(p.x - PinHead - 10f, p.y - PinHead * 3.2f, (PinHead + 10f) * 2f, PinHead * 3.2f + 12f);
        }

        /// <summary>
        /// The box of a place's name (<paramref name="text"/> at <paramref name="fontSize"/>) beside its pin standing on
        /// <paramref name="p"/>: the first of six spots round the pin's head (right, left, above, under the point and the two upper
        /// corners) that is inside the core and clear of every node (as drawn in focus), the one furthest from the route lines among
        /// those; if none is, the one that comes least near a node.
        /// </summary>
        public static Rect PlaceBox(Vector2 p, string text, int fontSize)
        {
            Vector2 size = new Vector2(Width(text, fontSize) + 30f, fontSize * 1.3f);
            Vector2 head = p + new Vector2(0f, -PinHead * 1.75f);
            float side = PinHead + 14f + size.x * 0.5f, up = PinHead + 14f + size.y * 0.5f, corner = PinHead * 0.6f + 14f + size.x * 0.5f;
            Vector2[] spots =
            {
                head + new Vector2(side, 0f), head - new Vector2(side, 0f), head + new Vector2(0f, -up), p + new Vector2(0f, 24f + size.y * 0.5f),
                head + new Vector2(corner, -up), head + new Vector2(-corner, -up),
            };
            Rect core = TownMap.Core;
            Rect best = new Rect(spots[0].x - size.x * 0.5f, spots[0].y - size.y * 0.5f, size.x, size.y);
            float bestNodes = float.MinValue, bestRoutes = float.MinValue;
            bool bestClear = false;
            foreach (Vector2 c in spots)
            {
                var box = new Rect(c.x - size.x * 0.5f, c.y - size.y * 0.5f, size.x, size.y);
                float nodes = 1000f, routes = 1000f;
                foreach (var node in TownMap.Nodes) nodes = Mathf.Min(nodes, DistanceTo(box, node.pos) - TownMap.NodeRadius);
                foreach (var route in TownMap.Routes) routes = Mathf.Min(routes, TownMap.DistanceToLine(box, route.points));
                bool inside = box.xMin >= core.xMin && box.xMax <= core.xMax && box.yMin >= core.yMin && box.yMax <= core.yMax;
                bool clear = inside && nodes >= Pad;
                bool better = clear ? (!bestClear || routes > bestRoutes) : (!bestClear && nodes > bestNodes);
                if (better) { best = box; bestClear = clear; bestNodes = nodes; bestRoutes = routes; }
            }
            return best;
        }

        /// <summary>The pill of stars under a node (on a focused route's unlocked node).</summary>
        public static Rect StarsBox(Vector2 node)
        {
            return new Rect(node.x - 77f, node.y + 44f, 154f, StarsBelow - 44f);
        }

        enum Spot { Below, Above, Right, Left, BelowRight, BelowLeft, AboveRight, AboveLeft }

        static Spot SpotOf(LabelSide side)
        {
            switch (side)
            {
                case LabelSide.Above: return Spot.Above;
                case LabelSide.Left: return Spot.Left;
                case LabelSide.Right: return Spot.Right;
                default: return Spot.Below;
            }
        }

        /// <summary>The box of a <paramref name="size"/> name at <paramref name="spot"/> round a node at <paramref name="p"/>, slid by <paramref name="slide"/> (-1, 0, 1) along a side.</summary>
        static Rect BoxAt(Vector2 p, Vector2 size, Spot spot, int slide, out int align)
        {
            float r = TownMap.NodeRadius, w = size.x, h = size.y;
            Vector2 c;
            align = 0;
            switch (spot)
            {
                case Spot.Above: c = new Vector2(p.x + slide * (w * 0.5f - 40f), p.y - r - Gap - h * 0.5f); break;
                case Spot.Below: c = new Vector2(p.x + slide * (w * 0.5f - 40f), p.y + StarsBelow + 4f + h * 0.5f); break;
                case Spot.Right: c = new Vector2(p.x + r + Gap + w * 0.5f, p.y + slide * 40f); align = -1; break;
                case Spot.Left: c = new Vector2(p.x - r - Gap - w * 0.5f, p.y + slide * 40f); align = 1; break;
                default:
                    float sx = spot == Spot.BelowRight || spot == Spot.AboveRight ? 1f : -1f;
                    float sy = spot == Spot.BelowRight || spot == Spot.BelowLeft ? 1f : -1f;
                    c = new Vector2(p.x + sx * (r * CornerIn + Gap + w * 0.5f), p.y + sy * (r * CornerIn + Gap + h * 0.5f + (sy > 0f ? 34f : 0f)));
                    align = sx > 0f ? -1 : 1;
                    break;
            }
            return new Rect(c.x - w * 0.5f, c.y - h * 0.5f, w, h);
        }

        static float DistanceTo(Rect r, Vector2 p)
        {
            float dx = Mathf.Max(Mathf.Max(r.xMin - p.x, p.x - r.xMax), 0f), dy = Mathf.Max(Mathf.Max(r.yMin - p.y, p.y - r.yMax), 0f);
            return Mathf.Sqrt(dx * dx + dy * dy);
        }

        static bool Overlap(Rect a, Rect b, float pad)
        {
            return a.xMin < b.xMax + pad && b.xMin < a.xMax + pad && a.yMin < b.yMax + pad && b.yMin < a.yMax + pad;
        }

        /// <summary>
        /// The names of the levels <paramref name="ids"/> (a route's levels and its challenge, in order), each from
        /// <paramref name="nameOf"/>, kept off <paramref name="blocked"/> (the pins and the screen's other texts) and off each other.
        /// A level without a node gets no entry.
        /// </summary>
        public static List<KeyValuePair<string, MapName>> Place(IList<string> ids, System.Func<string, string> nameOf, IList<Rect> blocked)
        {
            var result = new List<KeyValuePair<string, MapName>>();
            var own = new HashSet<string>(ids);
            var placed = new List<Rect>();
            Rect core = TownMap.Core;
            // The route's stop markers, on its line between its nodes: a name keeps off them as it keeps off its nodes.
            var stops = new List<Vector2>();
            var route = ids.Count > 0 ? RouteTable.Of(ids[0]) : null;
            if (route != null && route.stops != null)
                for (int i = 0; i < route.stops.Length; i++)
                {
                    Vector2? marker = TownMap.StopPosition(route.id, i);
                    if (marker != null) stops.Add(marker.Value);
                }
            // Wider first, then broken at narrower widths (two short lines fit between nodes where one long one does not), then smaller.
            var variants = new[] { new KeyValuePair<int, float>(FontSize, OneLineMax), new KeyValuePair<int, float>(FontSize, 300f), new KeyValuePair<int, float>(FontSize, 200f),
                                   new KeyValuePair<int, float>(SmallFontSize, OneLineMax), new KeyValuePair<int, float>(SmallFontSize, 300f), new KeyValuePair<int, float>(SmallFontSize, 200f) };
            foreach (string id in ids)
            {
                var node = TownMap.Node(id);
                if (node == null) continue;
                string text = nameOf(id) ?? id;
                Spot preferred = SpotOf(node.side);
                float bestScore = float.MaxValue;
                var best = new MapName();
                foreach (var variant in variants)
                {
                    string[] lines = Lines(text, variant.Key, variant.Value);
                    float w = 0f;
                    foreach (string line in lines) w = Mathf.Max(w, Width(line, variant.Key));
                    var size = new Vector2(w + Air, Height(lines.Length, variant.Key) + Air);
                    for (int s = -1; s < 8; s++)
                    {
                        Spot spot = s < 0 ? preferred : (Spot)s;
                        if (s >= 0 && spot == preferred) continue;
                        bool side = spot == Spot.Below || spot == Spot.Above || spot == Spot.Left || spot == Spot.Right;
                        for (int k = 0; k < (side ? 3 : 1); k++)
                        {
                            int slide = k == 0 ? 0 : (k == 1 ? -1 : 1);
                            int align;
                            Rect box = BoxAt(node.pos, size, spot, slide, out align);
                            int hard = 0, soft = 0, near = 0;
                            if (box.xMin < core.xMin || box.xMax > core.xMax || box.yMin < core.yMin || box.yMax > core.yMax) hard++;
                            foreach (var other in TownMap.Nodes)
                            {
                                if (other.levelId == id)
                                {
                                    if (Overlap(box, StarsBox(other.pos), 0f)) hard++;
                                    continue;
                                }
                                if (own.Contains(other.levelId))
                                {
                                    if (DistanceTo(box, other.pos) < TownMap.NodeRadius + Pad) hard++;
                                    if (Overlap(box, StarsBox(other.pos), Pad)) hard++;
                                }
                                else if (DistanceTo(box, other.pos) < TownMap.NodeRadius * OtherNodeScale + Pad) soft++;
                            }
                            foreach (var marker in stops) if (DistanceTo(box, marker) < TownMap.StopRadius + Pad) hard++;
                            if (blocked != null) foreach (var b in blocked) if (Overlap(box, b, Pad)) hard++;
                            foreach (var b in placed)
                            {
                                if (Overlap(box, b, Pad)) hard++;
                                else if (Overlap(box, b, NameGap)) near++;
                            }
                            float score = hard * 100f + near * 30f + soft * 10f + (spot == preferred ? 0f : 1f) + (slide == 0 ? 0f : 1f)
                                          + (lines.Length > 1 ? 0.5f : 0f) + (variant.Key == FontSize ? 0f : 5f);
                            if (score < bestScore)
                            {
                                bestScore = score;
                                best = new MapName { box = box, text = string.Join("\n", lines), fontSize = variant.Key, align = align, clear = hard == 0, overOther = soft > 0 };
                            }
                        }
                    }
                    if (bestScore < 10f) break;          // clear of everything, at this size
                }
                placed.Add(best.box);
                result.Add(new KeyValuePair<string, MapName>(id, best));
            }
            return result;
        }
    }
}
