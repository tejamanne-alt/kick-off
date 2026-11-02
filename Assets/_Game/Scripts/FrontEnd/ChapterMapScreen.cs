using System.Collections.Generic;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The way to school: a rendered picture of the town (Resources/UI/TownMap.jpg, laid out by Resources/TownMapLayout.json,
    /// see <see cref="TownMap"/>) with the six routes from the kid's house to the one school drawn over it as coloured lines,
    /// each level a numbered node on its route (stars, a lock, the next one pulsing) and each challenge a gold "!" node beside
    /// its route. The route with the next level to play is in focus: bright and wide, its levels named; the others are thin
    /// and dimmed, their nodes still tappable. Along the bottom: the focused route's levels as a strip like a level
    /// select (a house, the level chips with their stars or lock, the school) and a chip for each route to change the focus.
    /// The picture's core (everything that matters) is scaled to fit the room between the title and the strip, whatever the
    /// screen's shape, and the picture's ring shows round it as far as it reaches. Without the picture a plain background
    /// takes its place (the routes and nodes still work); without the layout the strip and the chips still play the game.
    /// </summary>
    public class ChapterMapScreen : FrontEndScreen
    {
        // ---- the layout, in canvas units (the canvas is 1080 tall inside the safe area)
        const float HeaderHeight = 150f;      // FrontEndController's shared header
        const float TitleHeight = 62f;
        const float Gap = 6f;
        const float ChipHeight = 92f;         // the route chips, along the very bottom (a name may take two lines on a narrow screen)
        const float ChipBottom = 12f;
        const float StripHeight = 104f;       // the level strip, above them
        const float ChipY = 68f, StarsY = 18f; // inside the strip (from its bottom): the level chips' centres, and the stars or names under them
        const float SideMargin = 12f;

        // ---- sizes in the picture's own pixels (the map block is scaled to the screen, about 0.5)
        const float RouteWidthOn = 54f, RouteWidthOff = 30f;
        const int LabelFont = 50;             // 25 canvas units at the usual scale: never under 22
        const float PinHead = 40f;

        static readonly Color Mat = new Color(0.1f, 0.15f, 0.31f);
        static readonly Color Plain = new Color(0.86f, 0.9f, 0.76f);
        static readonly Color Dark = new Color(0.07f, 0.1f, 0.22f, 0.93f);
        static readonly Color HomeRed = new Color(0.9f, 0.32f, 0.3f);
        static readonly Color SchoolBlue = new Color(0.22f, 0.36f, 0.72f);

        RectTransform body;                   // the room for the picture's core, between the title and the strip
        RectTransform map;                    // the picture's block (3200 x 1800 pixels), scaled by UIFitRect
        UIFitRect fit;
        RawImage picture;
        Image plain;
        Texture2D texture;
        RectTransform routeLayer, textLayer, nodeLayer, stripRoot;
        Text focusName, focusStars;
        Image focusSwatch;
        readonly Dictionary<string, MapPainter> routePainters = new Dictionary<string, MapPainter>();
        readonly Dictionary<string, UIMapMesh> routeMeshes = new Dictionary<string, UIMapMesh>();
        readonly Dictionary<string, Button> chips = new Dictionary<string, Button>();
        readonly Dictionary<string, Text> chipStars = new Dictionary<string, Text>();
        readonly List<Rect> taken = new List<Rect>();     // boxes of the texts already placed on the picture
        string focus;
        bool firstShow, popIn;                // the nodes pop in when the map is opened, not each time the focus moves

        public override string Title { get { return Loc.T("menu.map"); } }

        // ------------------------------------------------------------------ building

        protected override void Build(RectTransform root)
        {
            // The mat: the colour round the picture, over the whole screen (and beyond the safe area).
            var mat = UIKit.Rect(root, "Mat");
            mat.anchorMin = Vector2.zero;
            mat.anchorMax = Vector2.one;
            mat.offsetMin = new Vector2(-900f, -450f);
            mat.offsetMax = new Vector2(900f, 450f);
            var matImage = mat.gameObject.AddComponent<Image>();
            matImage.color = Mat;
            matImage.raycastTarget = false;

            BuildMap(root);

            // A dark wash at the top so the header and title read over the picture.
            var wash = UIKit.Icon(root, "TopWash", ProceduralSprites.VerticalGradient, new Color(Mat.r, Mat.g, Mat.b, 0.92f), 10f);
            wash.preserveAspect = false;
            wash.rectTransform.anchorMin = new Vector2(0f, 1f);
            wash.rectTransform.anchorMax = new Vector2(1f, 1f);
            wash.rectTransform.pivot = new Vector2(0.5f, 1f);
            wash.rectTransform.offsetMin = new Vector2(-900f, -(HeaderHeight + TitleHeight + 40f));
            wash.rectTransform.offsetMax = new Vector2(900f, 0f);

            BuildTitle(root);
            stripRoot = UIKit.Rect(root, "Strip");
            BuildChips(root);
        }

        void BuildMap(RectTransform root)
        {
            Vector2 frame = TownMap.FrameSize;
            Rect core = TownMap.Core;
            if (core.width <= 0f) core = TownMap.ExpectedCore;

            // The room for the core: between the title row and the strip, whatever the screen's shape.
            body = UIKit.Rect(root, "Body");
            body.anchorMin = Vector2.zero;
            body.anchorMax = Vector2.one;
            body.offsetMin = new Vector2(SideMargin, ChipBottom + ChipHeight + Gap + StripHeight + Gap);
            body.offsetMax = new Vector2(-SideMargin, -(HeaderHeight + TitleHeight + Gap));

            map = UIKit.Rect(body, "Map");
            UIKit.Place(map, new Vector2(0.5f, 0.5f), Vector2.zero, frame, new Vector2(0.5f, 0.5f));
            fit = map.gameObject.AddComponent<UIFitRect>();
            fit.designSize = frame;
            fit.fitSize = new Vector2(core.width, core.height);
            fit.fitCentre = core.center;
            fit.minScale = 0.2f;
            fit.maxScale = 1.2f;

            // The picture; a plain background stands in until (or unless) it loads.
            var plainRect = UIKit.Stretch(UIKit.Rect(map, "Plain"));
            plain = plainRect.gameObject.AddComponent<Image>();
            plain.color = Plain;
            plain.raycastTarget = false;
            var pictureRect = UIKit.Stretch(UIKit.Rect(map, "Picture"));
            picture = pictureRect.gameObject.AddComponent<RawImage>();
            picture.raycastTarget = false;
            picture.enabled = false;
            BuildFades(frame);

            routeLayer = UIKit.Stretch(UIKit.Rect(map, "Routes"));
            foreach (var route in TownMap.Routes)
            {
                var painter = new MapPainter();
                routePainters[route.id] = painter;
                routeMeshes[route.id] = UIMapMesh.Create(routeLayer, "Route_" + route.id, painter, frame);
            }
            BuildMarkers(frame);
            textLayer = UIKit.Stretch(UIKit.Rect(map, "Texts"));
            BuildTexts();
            nodeLayer = UIKit.Stretch(UIKit.Rect(map, "Nodes"));
        }

        /// <summary>
        /// The picture's four edges fade into the mat (a gradient the width of the ring, in the mat's colour), so the picture
        /// has no hard border whether the screen is wider than it (the mat shows at its sides) or narrower (the sides are cut off).
        /// </summary>
        void BuildFades(Vector2 frame)
        {
            Rect core = TownMap.Core.width > 0f ? TownMap.Core : TownMap.ExpectedCore;
            // Four fifths of the ring on each side; the rest of the ring stays as it is.
            float fadeX = Mathf.Max(0f, core.xMin) * 0.8f, fadeY = Mathf.Max(0f, core.yMin) * 0.8f;
            Color mat = new Color(Mat.r, Mat.g, Mat.b, 1f);
            // The gradient is opaque at the top of its rect and clear at the bottom; each edge turns it to face outwards.
            if (fadeY > 1f)
            {
                Fade("FadeTop", new Vector2(0f, frame.y * 0.5f - fadeY * 0.5f), new Vector2(frame.x, fadeY), 0f, mat);
                Fade("FadeBottom", new Vector2(0f, -frame.y * 0.5f + fadeY * 0.5f), new Vector2(frame.x, fadeY), 180f, mat);
            }
            if (fadeX > 1f)
            {
                // Turned a quarter, a rect's width and height swap: its width is the fade's length along the picture's side.
                Fade("FadeLeft", new Vector2(-frame.x * 0.5f + fadeX * 0.5f, 0f), new Vector2(frame.y, fadeX), 90f, mat);
                Fade("FadeRight", new Vector2(frame.x * 0.5f - fadeX * 0.5f, 0f), new Vector2(frame.y, fadeX), -90f, mat);
            }
        }

        void Fade(string name, Vector2 at, Vector2 size, float turn, Color colour)
        {
            var image = UIKit.Icon(map, name, ProceduralSprites.VerticalGradient, colour, 10f);
            image.preserveAspect = false;
            image.raycastTarget = false;
            UIKit.Place(image.rectTransform, new Vector2(0.5f, 0.5f), at, size, new Vector2(0.5f, 0.5f));
            image.rectTransform.localRotation = Quaternion.Euler(0f, 0f, turn);
        }

        /// <summary>The picture's anchored position inside <c>map</c> (centre pivot, y up) for a point of the picture (pixels, y down).</summary>
        Vector2 At(Vector2 p)
        {
            Vector2 frame = TownMap.FrameSize;
            return new Vector2(p.x - frame.x * 0.5f, frame.y * 0.5f - p.y);
        }

        /// <summary>The house and the school: a pin over each, drawn once.</summary>
        void BuildMarkers(Vector2 frame)
        {
            if (!TownMap.Available) return;
            var painter = new MapPainter();
            Vector2 headHome = MapGlyphs.Pin(painter, TownMap.Home, PinHead, HomeRed);
            MapGlyphs.House(painter, headHome + new Vector2(0f, 2f), PinHead * 1.15f, Color.white, HomeRed);
            Vector2 headSchool = MapGlyphs.Pin(painter, TownMap.School, PinHead, SchoolBlue);
            MapGlyphs.School(painter, headSchool + new Vector2(0f, 4f), PinHead * 1.25f, Color.white, SchoolBlue);
            UIMapMesh.Create(map, "Markers", painter, frame);
        }

        /// <summary>The names on the picture: home and school, the districts and the streets, kept clear of the nodes and of each other.</summary>
        void BuildTexts()
        {
            taken.Clear();
            if (!TownMap.Available) return;
            // Boxes already spoken for: the nodes' discs (with room for their stars) and the two pins.
            foreach (var node in TownMap.Nodes)
            {
                taken.Add(new Rect(node.pos.x - TownMap.NodeRadius - 6f, node.pos.y - TownMap.NodeRadius - 6f, TownMap.NodeDiameter + 12f, TownMap.NodeDiameter + 40f));
                // ...and where its name goes when its route is in focus.
                Rect label = TownMap.LabelRect(node);
                taken.Add(new Rect(label.x - 10f, label.y - 10f, label.width + 20f, label.height + 20f));
            }
            foreach (string id in new[] { "home", "school" })
            {
                Vector2 p = TownMap.Place(id);
                taken.Add(new Rect(p.x - PinHead - 10f, p.y - PinHead * 3.2f, (PinHead + 10f) * 2f, PinHead * 3.2f + 12f));
            }

            // Home (with "you are here") and School: the name beside the pin, on whichever side has room.
            PlaceName("home", Loc.T("place.home"), HomeRed);
            PlaceName("school", Loc.T("place.school"), SchoolBlue);

            // "You are here" over the house, where there is room for it (above, else below, else beside).
            var pillSize = new Vector2(330f, 64f);
            float up = PinHead * 3.2f + 36f;
            Vector2? here = FreeSpotAmong(new[]
            {
                TownMap.Home + new Vector2(0f, -up),
                TownMap.Home + new Vector2(0f, 60f + pillSize.y * 0.5f),
                TownMap.Home + new Vector2(-(PinHead + 20f + pillSize.x * 0.5f), -PinHead * 1.75f),
                TownMap.Home + new Vector2(PinHead + 20f + pillSize.x * 0.5f, -PinHead * 1.75f)
            }, pillSize);
            if (here != null)
            {
                var pill = UIKit.Panel(textLayer, "HerePill", HomeRed, ProceduralSprites.RoundedEdgeSmall);
                UIKit.Place(pill.rectTransform, new Vector2(0.5f, 0.5f), At(here.Value), pillSize, new Vector2(0.5f, 0.5f));
                pill.raycastTarget = false;
                var hereText = UIKit.Label(pill.transform, "Text", Loc.T("map.here"), LabelFont, Color.white, TextAnchor.MiddleCenter, true);
                UIKit.Stretch(hereText.rectTransform, 4f);
                UIKit.Fit(hereText, LabelFont - 2);
                Shadowed(hereText);
            }

            // Districts: small capitals, white with a dark outline (the school's is left out: its pin already says so).
            foreach (var district in TownMap.Districts)
            {
                if (district.id == "school") continue;
                string text = Loc.T(district.NameKey).ToUpperInvariant();
                Vector2 size = new Vector2(text.Length * LabelFont * 0.62f + 30f, LabelFont * 1.3f);
                Vector2? at = FreeSpot(district.pos, size);
                if (at == null) continue;
                var t = UIKit.Label(textLayer, "District_" + district.id, text, LabelFont, Color.white, TextAnchor.MiddleCenter, true);
                UIKit.Place(t.rectTransform, new Vector2(0.5f, 0.5f), At(at.Value), size, new Vector2(0.5f, 0.5f));
                Outlined(t);
            }

            // Streets: named along the road at the angle given (as the art gives the names, not translated), where they touch
            // no node, name or route line.
            int count = 0;
            foreach (var street in TownMap.Streets)
            {
                float width = street.name.Length * LabelFont * 0.56f + 24f;
                float rad = street.angle * Mathf.Deg2Rad;
                Vector2 size = new Vector2(Mathf.Abs(Mathf.Cos(rad)) * width + Mathf.Abs(Mathf.Sin(rad)) * LabelFont * 1.2f, Mathf.Abs(Mathf.Sin(rad)) * width + Mathf.Abs(Mathf.Cos(rad)) * LabelFont * 1.2f);
                if (OnARoute(street.pos, street.angle, width)) continue;
                Vector2? at = FreeSpot(street.pos, size, false);
                if (at == null) continue;
                var t = UIKit.Label(textLayer, "Street_" + (count++), street.name, LabelFont, Color.white, TextAnchor.MiddleCenter, false);
                t.horizontalOverflow = HorizontalWrapMode.Overflow;       // one line, however long the name
                UIKit.Place(t.rectTransform, new Vector2(0.5f, 0.5f), At(at.Value), new Vector2(width, LabelFont * 1.2f), new Vector2(0.5f, 0.5f));
                t.rectTransform.localRotation = Quaternion.Euler(0f, 0f, -street.angle);   // the layout's angle turns clockwise (y down)
                Outlined(t, 2.5f);
            }
        }

        /// <summary>True if a line of text <paramref name="length"/> long, centred on <paramref name="centre"/> at <paramref name="angle"/> degrees (y down), comes close to a route line.</summary>
        static bool OnARoute(Vector2 centre, float angle, float length)
        {
            Vector2 along = new Vector2(Mathf.Cos(angle * Mathf.Deg2Rad), Mathf.Sin(angle * Mathf.Deg2Rad));
            for (float t = -length * 0.5f; t <= length * 0.5f + 1f; t += 20f)
            {
                Vector2 p = centre + along * t;
                foreach (var route in TownMap.Routes)
                    if (TownMap.DistanceTo(route.points, p) < RouteWidthOn * 0.5f + 40f + LabelFont * 0.6f) return true;
            }
            return false;
        }

        /// <summary>A name beside a place's pin: on the right or the left, whichever has more room (clear of the routes and the nodes).</summary>
        void PlaceName(string id, string text, Color colour)
        {
            Vector2 p = TownMap.Place(id);
            Vector2 size = new Vector2(text.Length * LabelFont * 0.6f + 30f, LabelFont * 1.3f);
            Vector2 head = p + new Vector2(0f, -PinHead * 1.75f);
            float best = -1f;
            Vector2 centre = head + new Vector2(PinHead + 14f + size.x * 0.5f, 0f);
            for (int side = -1; side <= 1; side += 2)
            {
                Vector2 c = head + new Vector2(side * (PinHead + 14f + size.x * 0.5f), 0f);
                var box = new Rect(c.x - size.x * 0.5f, c.y - size.y * 0.5f, size.x, size.y);
                float room = 1000f;
                foreach (var route in TownMap.Routes) room = Mathf.Min(room, TownMap.DistanceToLine(box, route.points));
                foreach (var node in TownMap.Nodes) room = Mathf.Min(room, TownMap.DistanceToRect(box, node.pos) - TownMap.NodeRadius);
                if (room > best) { best = room; centre = c; }
            }
            var t = UIKit.Label(textLayer, "Place_" + id, text, LabelFont, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(t.rectTransform, new Vector2(0.5f, 0.5f), At(centre), size, new Vector2(0.5f, 0.5f));
            Outlined(t);
            taken.Add(new Rect(centre.x - size.x * 0.5f, centre.y - size.y * 0.5f, size.x, size.y));
        }

        /// <summary>
        /// The spot nearest to <paramref name="wanted"/> where a text of <paramref name="size"/> touches no node, pin or earlier text
        /// (it is tried where the art put it, then a little way round it), or null if there is none. The box is reserved.
        /// </summary>
        Vector2? FreeSpot(Vector2 wanted, Vector2 size, bool tryAround = true)
        {
            Vector2[] tries = tryAround
                ? new[] { Vector2.zero, new Vector2(0f, -70f), new Vector2(0f, 70f), new Vector2(-110f, 0f), new Vector2(110f, 0f), new Vector2(-110f, -70f), new Vector2(110f, -70f), new Vector2(-110f, 70f), new Vector2(110f, 70f) }
                : new[] { Vector2.zero };
            var spots = new Vector2[tries.Length];
            for (int i = 0; i < tries.Length; i++) spots[i] = wanted + tries[i];
            return FreeSpotAmong(spots, size);
        }

        /// <summary>The first of the <paramref name="spots"/> (centres) where a text of <paramref name="size"/> is inside the core and touches nothing taken; its box is reserved.</summary>
        Vector2? FreeSpotAmong(Vector2[] spots, Vector2 size)
        {
            Rect core = TownMap.Core;
            foreach (Vector2 c in spots)
            {
                var box = new Rect(c.x - size.x * 0.5f, c.y - size.y * 0.5f, size.x, size.y);
                if (box.xMin < core.xMin || box.xMax > core.xMax || box.yMin < core.yMin || box.yMax > core.yMax) continue;
                bool free = true;
                foreach (var other in taken)
                    if (box.Overlaps(other)) { free = false; break; }
                if (!free) continue;
                taken.Add(box);
                return c;
            }
            return null;
        }

        /// <summary>White lettering with a dark line round it, so it reads on the picture.</summary>
        static void Outlined(Text text, float thickness = 3.5f)
        {
            var line = text.gameObject.AddComponent<Outline>();
            line.effectColor = new Color(0.07f, 0.1f, 0.22f, 0.95f);
            line.effectDistance = new Vector2(thickness, -thickness);
            Shadowed(text);
        }

        static void Shadowed(Text text)
        {
            var drop = text.gameObject.AddComponent<Shadow>();
            drop.effectColor = new Color(0.03f, 0.05f, 0.15f, 0.45f);
            drop.effectDistance = new Vector2(0f, -5f);
        }

        // ------------------------------------------------------------------ the title and the route chips

        void BuildTitle(RectTransform root)
        {
            float margin = 24f + ExtraSide();
            var row = UIKit.Row(root, "TitleRow", HeaderHeight, TitleHeight, margin, margin);
            var choose = UIKit.Label(row, "Choose", Loc.T("map.choose"), 40, Color.white, TextAnchor.MiddleLeft, true);
            UIKit.Place(choose.rectTransform, new Vector2(0f, 0.5f), new Vector2(8f, 0f), new Vector2(760f, 56f), new Vector2(0f, 0.5f));
            var line = choose.gameObject.AddComponent<Outline>();
            line.effectColor = UITheme.Ink;
            line.effectDistance = new Vector2(2.5f, -2.5f);

            // The focused route: its colour, name and stars on a little card at the right.
            var card = UIKit.Card(row, "Focus", UITheme.Paper);
            UIKit.Place((RectTransform)card.transform.parent, new Vector2(1f, 0.5f), Vector2.zero, new Vector2(580f, 54f), new Vector2(1f, 0.5f));
            focusSwatch = UIKit.Icon(card.transform, "Swatch", ProceduralSprites.CircleEdge, Color.white, 34f);
            UIKit.Place(focusSwatch.rectTransform, new Vector2(0f, 0.5f), new Vector2(18f, 0f), new Vector2(34f, 34f), new Vector2(0f, 0.5f));
            focusName = UIKit.Label(card.transform, "Name", "", 32, UITheme.Ink, TextAnchor.MiddleLeft, true);
            UIKit.Place(focusName.rectTransform, new Vector2(0f, 0.5f), new Vector2(62f, 0f), new Vector2(330f, 46f), new Vector2(0f, 0.5f));
            UIKit.Fit(focusName, 22);
            var star = UIKit.Icon(card.transform, "Star", ProceduralSprites.Star, UITheme.Gold, 34f);
            UIKit.Place(star.rectTransform, new Vector2(1f, 0.5f), new Vector2(-160f, 0f), new Vector2(34f, 34f), new Vector2(1f, 0.5f));
            var o = star.gameObject.AddComponent<Outline>();
            o.effectColor = new Color(0.45f, 0.28f, 0.02f, 0.9f);
            o.effectDistance = new Vector2(2f, -2f);
            focusStars = UIKit.Label(card.transform, "Stars", "", 30, UITheme.Ink, TextAnchor.MiddleRight, true);
            UIKit.Place(focusStars.rectTransform, new Vector2(1f, 0.5f), new Vector2(-14f, 0f), new Vector2(140f, 46f), new Vector2(1f, 0.5f));
            UIKit.Fit(focusStars, 22);
        }

        void BuildChips(RectTransform root)
        {
            var row = UIKit.Rect(root, "Chips");
            row.anchorMin = new Vector2(0f, 0f);
            row.anchorMax = new Vector2(1f, 0f);
            row.pivot = new Vector2(0.5f, 0f);
            float side = SideMargin + ExtraSide();
            row.offsetMin = new Vector2(side, ChipBottom);
            row.offsetMax = new Vector2(-side, ChipBottom + ChipHeight);
            int count = RouteTable.All.Length;
            for (int i = 0; i < count; i++)
            {
                var route = RouteTable.All[i];
                var cell = UIKit.Rect(row, "Cell_" + route.id);
                cell.anchorMin = new Vector2(i / (float)count, 0f);
                cell.anchorMax = new Vector2((i + 1) / (float)count, 1f);
                cell.offsetMin = new Vector2(4f, 0f);
                cell.offsetMax = new Vector2(-4f, 0f);
                string id = route.id;
                var chip = UIKit.Button(cell, "Chip_" + id, "", Color.white, () => ShowRoute(id), 26);
                var chipRect = (RectTransform)chip.transform;
                UIKit.Stretch(chipRect);
                chipRect.offsetMin = new Vector2(0f, UIButtonFx.Depth);     // the key's base shows under the face
                chips[id] = chip;

                var face = chip.transform.Find("Face");
                var swatch = UIKit.Icon(face, "Swatch", ProceduralSprites.CircleEdge, Color.white, 30f);
                UIKit.Place(swatch.rectTransform, new Vector2(0f, 0.64f), new Vector2(12f, 0f), new Vector2(30f, 30f), new Vector2(0f, 0.5f));
                // The name takes two lines on a narrow screen (it shrinks to 22 before it would be cut).
                var name = UIKit.Label(face, "Name", Loc.T(route.NameKey), 26, UITheme.Ink, TextAnchor.MiddleLeft, true);
                name.rectTransform.anchorMin = new Vector2(0f, 0.34f);
                name.rectTransform.anchorMax = new Vector2(1f, 1f);
                name.rectTransform.offsetMin = new Vector2(48f, 0f);
                name.rectTransform.offsetMax = new Vector2(-6f, -4f);
                UIKit.Fit(name, 22);
                var star = UIKit.Icon(face, "Star", ProceduralSprites.Star, UITheme.Gold, 24f);
                UIKit.Place(star.rectTransform, new Vector2(0f, 0f), new Vector2(50f, 17f), new Vector2(24f, 24f), new Vector2(0f, 0.5f));
                var amount = UIKit.Label(face, "Stars", "", 24, UITheme.Ink, TextAnchor.MiddleLeft, true);
                UIKit.Place(amount.rectTransform, new Vector2(0f, 0f), new Vector2(78f, 17f), new Vector2(120f, 30f), new Vector2(0f, 0.5f));
                chipStars[id] = amount;

                // The touch target: the chip, the gap beside it and down to the screen's edge, a little up.
                var hit = UIKit.Rect(chip.transform, "Hit");
                hit.anchorMin = Vector2.zero;
                hit.anchorMax = Vector2.one;
                hit.offsetMin = new Vector2(-4f, -(UIButtonFx.Depth + ChipBottom));
                hit.offsetMax = new Vector2(4f, Gap);
                ClearHit(hit);
            }
        }

        /// <summary>An invisible image that takes taps (they reach the button above it), so a target can be bigger than what is drawn.</summary>
        static void ClearHit(RectTransform rect)
        {
            var image = rect.gameObject.AddComponent<Image>();
            image.color = Color.clear;
            image.raycastTarget = true;
        }

        /// <summary>On the widest screens the chips stop growing: they are kept to about 1900 canvas units across.</summary>
        static float ExtraSide()
        {
            float aspect = Screen.height > 0 ? (float)Screen.width / Screen.height : 16f / 9f;
            float width = UIKit.ReferenceResolution.y * aspect;
            return Mathf.Max(0f, (width - 1900f) * 0.5f);
        }

        // ------------------------------------------------------------------ showing

        public override void OnShow()
        {
            EnsurePicture();
            firstShow = true;
            int requested = FrontEndController.RequestedChapter;
            FrontEndController.RequestedChapter = 0;
            var catalog = Controller.levels;
            LevelDefinition next = catalog != null ? LevelUnlocks.NextToPlay(catalog) : null;
            string id = null;
            if (requested > 0)
            {
                // The route of the chapter just played that holds the next level (chapter 4 has two), else its first.
                if (next != null && next.chapter == requested && RouteTable.Of(next.levelId) != null) id = RouteTable.Of(next.levelId).id;
                else
                {
                    var routes = RouteTable.InChapter(requested);
                    if (routes.Count > 0) id = routes[0].id;
                }
            }
            if (id == null)
            {
                var r = next != null ? RouteTable.Of(next.levelId) : null;
                id = r != null ? r.id : RouteTable.All[0].id;
            }
            ShowRoute(id);
        }

        public override void OnHide()
        {
            ReleasePicture();
        }

        public override void OnDestroyed()
        {
            ReleasePicture();
        }

        /// <summary>Load the picture (a texture, or a sprite if it was imported as one) while the map is on screen.</summary>
        void EnsurePicture()
        {
            if (texture != null || picture == null) return;
            string path = TownMap.Image;
            texture = Resources.Load<Texture2D>(path);
            if (texture != null)
            {
                picture.texture = texture;
                picture.enabled = true;
            }
            else
            {
                // Imported as a sprite: show its texture all the same.
                var sprite = Resources.Load<Sprite>(path);
                if (sprite != null)
                {
                    texture = sprite.texture;
                    picture.texture = texture;
                    picture.uvRect = new Rect(0f, 0f, 1f, 1f);
                    picture.enabled = true;
                }
            }
            plain.enabled = !picture.enabled;
        }

        void ReleasePicture()
        {
            if (picture != null) { picture.texture = null; picture.enabled = false; }
            if (plain != null) plain.enabled = true;
            if (texture != null) Resources.UnloadAsset(texture);
            texture = null;
        }

        void ShowRoute(string id)
        {
            var catalog = Controller.levels;
            focus = id;
            popIn = firstShow;
            firstShow = false;
            var focusRoute = RouteTable.All[RouteTable.IndexOf(id)];
            for (int i = nodeLayer.childCount - 1; i >= 0; i--) Object.Destroy(nodeLayer.GetChild(i).gameObject);
            for (int i = stripRoot.childCount - 1; i >= 0; i--) Object.Destroy(stripRoot.GetChild(i).gameObject);

            DrawRoutes(catalog);

            Color focusColour = ColourOf(catalog, focusRoute);
            focusSwatch.color = focusColour;
            focusName.text = Loc.T(focusRoute.NameKey);
            focusStars.text = StarsOf(focusRoute) + " / " + TotalOf(focusRoute);
            foreach (var route in RouteTable.All)
            {
                bool on = route.id == id;
                Color c = ColourOf(catalog, route);
                chips[route.id].targetGraphic.color = on ? Color.Lerp(c, Color.white, 0.5f) : Color.Lerp(c, Color.white, 0.84f);
                chips[route.id].transform.Find("Face").Find("Swatch").GetComponent<Image>().color = c;
                chipStars[route.id].text = StarsOf(route) + " / " + TotalOf(route);
            }

            if (catalog == null || catalog.levels.Count == 0)
            {
                var soon = UIKit.Title(nodeLayer, "ComingSoon", Loc.T("menu.soon"), 160, Color.white);
                UIKit.Stretch(soon.rectTransform);
                return;
            }

            var next = LevelUnlocks.NextToPlay(catalog);
            BuildStrip(catalog, focusRoute, next);

            // The nodes: the other routes' first, the focused route's last (on top), its levels named.
            int index = 0;
            foreach (var route in RouteTable.All)
            {
                if (route.id == id) continue;
                BuildNodes(catalog, route, next, false, ref index);
            }
            BuildNodes(catalog, focusRoute, next, true, ref index);

            if (!Store.Monetization.IsChapterUnlocked(focusRoute.chapter)) ShowRouteLock(focusRoute);
        }

        // ------------------------------------------------------------------ the routes and their nodes

        /// <summary>The six route lines: the dimmed ones first, the focused one on top of them.</summary>
        void DrawRoutes(LevelCatalog catalog)
        {
            int order = 0;
            foreach (var route in RouteTable.All)
            {
                var line = TownMap.Route(route.id);
                if (line == null) continue;
                bool on = route.id == focus;
                var painter = routePainters[route.id];
                painter.Clear();
                Color core = ColourOf(catalog, route);
                if (!on) core = Color.Lerp(core, new Color(0.9f, 0.92f, 0.95f), 0.4f);
                float width = on ? RouteWidthOn : RouteWidthOff;
                float casing = on ? 13f : 8f;
                painter.Stroke(line.points, width + casing * 2f, Color.white, false, true);
                painter.Stroke(line.points, width, core, false, true);
                if (on) painter.Dashed(line.points, 7f, 24f, 34f, new Color(1f, 1f, 1f, 0.85f));
                // The dotted branch from the route to its challenge's node.
                if (route.challenge != null)
                {
                    var node = TownMap.Node(route.challenge);
                    if (node != null)
                    {
                        Vector2 near;
                        TownMap.DistanceTo(line.points, node.pos, out near);
                        painter.Dashed(new[] { near, node.pos }, on ? 20f : 14f, 26f, 20f, Color.white);
                        painter.Dashed(new[] { near, node.pos }, on ? 12f : 8f, 26f, 20f, core);
                    }
                }
                routeMeshes[route.id].Show(painter);
                if (!on) routeMeshes[route.id].transform.SetSiblingIndex(order++);
            }
            if (routeMeshes.ContainsKey(focus)) routeMeshes[focus].transform.SetAsLastSibling();
        }

        void BuildNodes(LevelCatalog catalog, Route route, LevelDefinition next, bool focused, ref int index)
        {
            Color colour = ColourOf(catalog, route);
            if (!focused) colour = Color.Lerp(colour, new Color(0.9f, 0.92f, 0.95f), 0.18f);
            var ids = new List<string>(route.levels);
            if (route.challenge != null) ids.Add(route.challenge);
            foreach (string levelId in ids)
            {
                var def = catalog.FindById(levelId);
                var spot = TownMap.Node(levelId);
                if (def == null || spot == null) continue;
                BuildNode(catalog, def, spot, colour, def == next, focused, index++);
            }
        }

        void BuildNode(LevelCatalog catalog, LevelDefinition def, TownNode spot, Color colour, bool isNext, bool named, int index)
        {
            bool unlocked = LevelUnlocks.IsUnlocked(catalog, def);
            int stars = SaveSystem.StarsFor(def.levelId);

            var holder = UIKit.Rect(nodeLayer, "Node_" + def.levelId);
            UIKit.Place(holder, new Vector2(0.5f, 0.5f), At(spot.pos), new Vector2(TownMap.NodeDiameter, TownMap.NodeDiameter), new Vector2(0.5f, 0.5f));
            // The nodes pop in one after another when the map is opened (not every time the focus moves).
            if (popIn) UIKit.PopIn(holder.gameObject, Mathf.Min(index, 14) * 0.03f);

            Color face = def.isChallenge ? UITheme.Gold : colour;
            var button = UIKit.Button(holder, "Button", "", unlocked ? face : UITheme.Locked, () => Controller.PlayLevel(def));
            UIKit.Place((RectTransform)button.transform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(TownMap.NodeDiameter, TownMap.NodeDiameter), new Vector2(0.5f, 0.5f));
            button.interactable = unlocked;
            UIKit.MakeRound(button);
            // The next level's disc breathes (its stars and name stay still; UIPulse hands the scale to the button's press animation).
            if (isNext && unlocked) button.gameObject.AddComponent<UIPulse>();

            // The touch target: the disc, or about 118 canvas units across if that is more (a clear square: taps reach the button).
            float hitSize = Mathf.Max(TownMap.NodeDiameter, 118f / Mathf.Max(0.3f, ScaleNow()));
            var hit = UIKit.Rect(button.transform, "Hit");
            UIKit.Place(hit, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(hitSize, hitSize), new Vector2(0.5f, 0.5f));
            ClearHit(hit);

            if (unlocked)
            {
                string number = def.isChallenge ? "!" : def.levelId.TrimStart('L').TrimStart('0');
                var label = UIKit.Title(button.transform.Find("Face"), "Number", number, 78, Color.white);
                UIKit.Stretch(label.rectTransform);
            }
            else
            {
                var lockIcon = UIKit.Icon(button.transform.Find("Face"), "Lock", ProceduralSprites.Lock, new Color(1f, 1f, 1f, 0.9f), 78f);
                UIKit.Place(lockIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(78f, 78f));
            }

            // Stars on the disc's lower rim, on a light pill so they read on the picture whether earned (gold) or not (grey); a locked level has none to show.
            if (unlocked)
            {
                float starSize = 40f, drop = TownMap.NodeRadius - 4f;
                var starRow = UIKit.Stars(holder, "Stars", stars, starSize, 4f);
                var pill = UIKit.Panel(holder, "StarsPill", new Color(1f, 1f, 1f, 0.94f), ProceduralSprites.RoundedEdgeSmall);
                pill.raycastTarget = false;
                UIKit.Place(pill.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, -drop), new Vector2(starRow.sizeDelta.x + 26f, starSize + 14f), new Vector2(0.5f, 0.5f));
                starRow.SetAsLastSibling();
                UIKit.Place(starRow, new Vector2(0.5f, 0.5f), new Vector2(0f, -drop), starRow.sizeDelta, new Vector2(0.5f, 0.5f));
            }

            if (named) BuildName(holder, def, spot.side);
        }

        /// <summary>The level's name beside its node (on the side the layout gives): white with a dark outline, wrapping to two lines if it is long.</summary>
        void BuildName(RectTransform holder, LevelDefinition def, LabelSide side)
        {
            const float width = 360f, height = 128f;       // two lines of the label font, with a little air
            float gap = TownMap.NodeRadius + TownMap.LabelGap;
            Vector2 centre;       // from the node's centre, y up
            TextAnchor anchor;
            switch (side)
            {
                case LabelSide.Above: centre = new Vector2(0f, gap + height * 0.5f); anchor = TextAnchor.LowerCenter; break;
                case LabelSide.Left: centre = new Vector2(-(gap + width * 0.5f), 0f); anchor = TextAnchor.MiddleRight; break;
                case LabelSide.Right: centre = new Vector2(gap + width * 0.5f, 0f); anchor = TextAnchor.MiddleLeft; break;
                default: centre = new Vector2(0f, -(gap + 8f + height * 0.5f)); anchor = TextAnchor.UpperCenter; break;
            }
            var name = UIKit.Label(holder, "Name", Loc.T("level." + def.levelId, def.displayName), LabelFont, Color.white, anchor, true);
            UIKit.Place(name.rectTransform, new Vector2(0.5f, 0.5f), centre, new Vector2(width, height), new Vector2(0.5f, 0.5f));
            name.rectTransform.SetAsFirstSibling();
            Outlined(name);
        }

        /// <summary>
        /// The scale the map block is (or is about to be) at, about 0.5: worked out from the room, since the canvas has no size yet
        /// when the screens are built. A usual 16:9 screen is assumed until the body has one.
        /// </summary>
        float ScaleNow()
        {
            Vector2 room = body != null ? body.rect.size : Vector2.zero;
            if (room.x <= 1f || room.y <= 1f)
            {
                float height = UIKit.ReferenceResolution.y;
                room = new Vector2(UIKit.ReferenceResolution.x - 2f * SideMargin,
                    height - (HeaderHeight + TitleHeight + Gap) - (ChipBottom + ChipHeight + Gap + StripHeight + Gap));
            }
            Rect core = TownMap.Core.width > 0f ? TownMap.Core : TownMap.ExpectedCore;
            float min = fit != null ? fit.minScale : 0.2f, max = fit != null ? fit.maxScale : 1.2f;
            return UIFitRect.ScaleFor(room, core.size, min, max);
        }

        void ShowRouteLock(Route route)
        {
            var line = TownMap.Route(route.id);
            if (line == null) return;
            Vector2 middle = TownMap.At(line.points, line.length * 0.5f);
            // In the nodes' layer, which is cleared with them each time the focus moves.
            var unlock = UIKit.Button(nodeLayer, "Unlock", Loc.T("unlock.cta"), UITheme.Accent, () =>
                UI.UnlockPanel.Open(Controller.CanvasRoot, () => ShowRoute(route.id)), 90);
            UIKit.Place((RectTransform)unlock.transform, new Vector2(0.5f, 0.5f), At(middle), new Vector2(1200f, 260f));
            unlock.transform.SetAsLastSibling();
            unlock.gameObject.AddComponent<UIPulse>().amount = 0.03f;
        }

        // ------------------------------------------------------------------ the level strip

        /// <summary>The focused route's levels in a bar along the bottom: [LEVELS] [house] [1] [2] ... [!] [school], each level with its stars or lock.</summary>
        void BuildStrip(LevelCatalog catalog, Route route, LevelDefinition next)
        {
            var ids = new List<string>(route.levels);
            if (route.challenge != null) ids.Add(route.challenge);
            const float tagWidth = 150f, chip = 92f, gap = 8f, pad = 16f;
            int slots = ids.Count + 2;
            float width = pad + tagWidth + gap + slots * chip + (slots - 1) * gap + pad;

            stripRoot.anchorMin = stripRoot.anchorMax = new Vector2(0.5f, 0f);
            stripRoot.pivot = new Vector2(0.5f, 0f);
            stripRoot.anchoredPosition = new Vector2(0f, ChipBottom + ChipHeight + Gap);
            stripRoot.sizeDelta = new Vector2(width, StripHeight);
            Color colour = ColourOf(catalog, route);

            var bar = UIKit.Panel(stripRoot, "Bar", Dark, ProceduralSprites.RoundedEdge);
            UIKit.Stretch(bar.rectTransform);
            bar.raycastTarget = false;

            // The tag at the left, in the route's colour.
            var tag = UIKit.Panel(stripRoot, "Tag", colour, ProceduralSprites.RoundedEdgeSmall);
            UIKit.Place(tag.rectTransform, new Vector2(0f, 0.5f), new Vector2(pad, 0f), new Vector2(tagWidth, 52f), new Vector2(0f, 0.5f));
            tag.raycastTarget = false;
            var tagText = UIKit.Label(tag.transform, "Text", Loc.T("map.levels"), 28, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Stretch(tagText.rectTransform, 4f);
            UIKit.Fit(tagText, 22);
            var sh = tagText.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0.1f, 0.45f);
            sh.effectDistance = new Vector2(0f, -3f);

            float x = pad + tagWidth + gap;
            // The house.
            EndChip(stripRoot, "Home", x + chip * 0.5f, true, colour);
            x += chip + gap;

            foreach (string levelId in ids)
            {
                var def = catalog.FindById(levelId);
                if (def == null) { x += chip + gap; continue; }
                bool unlocked = LevelUnlocks.IsUnlocked(catalog, def);
                int stars = SaveSystem.StarsFor(levelId);
                Color face = def.isChallenge ? UITheme.Gold : colour;
                string number = def.isChallenge ? "!" : def.levelId.TrimStart('L').TrimStart('0');
                var button = UIKit.Button(stripRoot, "Level_" + levelId, unlocked ? number : "", unlocked ? face : UITheme.Locked, () => Controller.PlayLevel(def), 36);
                var rt = (RectTransform)button.transform;
                UIKit.Place(rt, new Vector2(0f, 0f), new Vector2(x + chip * 0.5f, ChipY), new Vector2(chip, 54f), new Vector2(0.5f, 0.5f));
                button.interactable = unlocked;
                // The touch target: the whole slot, the chip and its stars, the full height of the bar.
                var hit = UIKit.Rect(button.transform, "Hit");
                UIKit.Place(hit, new Vector2(0.5f, 0.5f), new Vector2(0f, StripHeight * 0.5f - ChipY), new Vector2(chip + gap, StripHeight), new Vector2(0.5f, 0.5f));
                ClearHit(hit);
                if (!unlocked)
                {
                    var lockIcon = UIKit.Icon(button.transform.Find("Face"), "Lock", ProceduralSprites.Lock, new Color(1f, 1f, 1f, 0.9f), 34f);
                    UIKit.Place(lockIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(34f, 34f));
                }
                if (def == next && unlocked)
                {
                    button.gameObject.AddComponent<UIPulse>().amount = 0.05f;
                    var marker = UIKit.Icon(stripRoot, "Next", ProceduralSprites.ArrowUp, UITheme.Gold, 34f);
                    UIKit.Place(marker.rectTransform, new Vector2(0f, 0f), new Vector2(x + chip * 0.5f, StripHeight + 12f), new Vector2(34f, 34f), new Vector2(0.5f, 0.5f));
                    marker.rectTransform.localRotation = Quaternion.Euler(0f, 0f, 180f);
                    var o = marker.gameObject.AddComponent<Outline>();
                    o.effectColor = UITheme.Ink;
                    o.effectDistance = new Vector2(2f, -2f);
                }
                // The stars under the chip, on a light box (unearned ones are grey, which would vanish on the dark bar).
                if (unlocked)
                {
                    var starRow = UIKit.Stars(stripRoot, "Stars_" + levelId, stars, 24f, 3f);
                    var box = UIKit.Panel(stripRoot, "StarsBox_" + levelId, new Color(1f, 1f, 1f, 0.94f), ProceduralSprites.RoundedEdgeSmall);
                    box.raycastTarget = false;
                    UIKit.Place(box.rectTransform, new Vector2(0f, 0f), new Vector2(x + chip * 0.5f, StarsY), new Vector2(starRow.sizeDelta.x + 16f, 30f), new Vector2(0.5f, 0.5f));
                    starRow.SetAsLastSibling();
                    UIKit.Place(starRow, new Vector2(0f, 0f), new Vector2(x + chip * 0.5f, StarsY), starRow.sizeDelta, new Vector2(0.5f, 0.5f));
                }
                x += chip + gap;
            }

            // The school at the end.
            EndChip(stripRoot, "Goal", x + chip * 0.5f, false, colour);
        }

        /// <summary>The house (start) or the school (goal) at an end of the strip: a small coloured plate with its picture.</summary>
        void EndChip(RectTransform strip, string name, float x, bool home, Color colour)
        {
            var plate = UIKit.Panel(strip, name, home ? HomeRed : SchoolBlue, ProceduralSprites.RoundedEdge);
            UIKit.Place(plate.rectTransform, new Vector2(0f, 0f), new Vector2(x, ChipY), new Vector2(92f, 54f), new Vector2(0.5f, 0.5f));
            plate.raycastTarget = false;
            var painter = new MapPainter();
            if (home) MapGlyphs.House(painter, new Vector2(50f, 52f), 56f, Color.white, HomeRed);
            else MapGlyphs.School(painter, new Vector2(50f, 56f), 62f, Color.white, SchoolBlue);
            var glyph = UIMapMesh.Create(plate.transform, "Glyph", painter, new Vector2(100f, 100f));
            UIKit.Place(glyph.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(52f, 52f), new Vector2(0.5f, 0.5f));
            var label = UIKit.Label(strip, name + "Label", Loc.T(home ? "place.home" : "place.school"), 22, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(label.rectTransform, new Vector2(0f, 0f), new Vector2(x, StarsY), new Vector2(96f, 28f), new Vector2(0.5f, 0.5f));
            UIKit.Fit(label, 22);
        }

        // ------------------------------------------------------------------ colours and stars

        /// <summary>The route's colour: its chapter's colour from the catalog (chapter 4's two routes get two shades of it).</summary>
        static Color ColourOf(LevelCatalog catalog, Route route)
        {
            var info = catalog != null ? catalog.Chapter(route.chapter) : null;
            return TownMap.RouteColor(route.id, info != null ? info.color : UITheme.Accent);
        }

        static int StarsOf(Route route)
        {
            int total = 0;
            foreach (string id in route.levels) total += SaveSystem.StarsFor(id);
            if (route.challenge != null) total += SaveSystem.StarsFor(route.challenge);
            return total;
        }

        static int TotalOf(Route route)
        {
            return (route.levels.Length + (route.challenge != null ? 1 : 0)) * 3;
        }
    }
}
