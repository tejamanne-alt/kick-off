using System.Collections.Generic;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// The way to school: a rendered picture of the town (Resources/UI/TownMap.jpg, laid out by Resources/TownMapLayout.json,
    /// see <see cref="TownMap"/>) with the six routes from the kid's house to the one school drawn over it as coloured lines,
    /// each level a numbered node on its route (stars, a lock, the next one pulsing), the stops between the levels (the bus stop,
    /// granny's house, the station... where one level ends and the next starts, Levels/RouteTable) as small markers on the line,
    /// and each challenge a gold "!" node beside its route. The route with the next level to play is in focus: bright and wide,
    /// its levels named; the others are thin and dimmed, their nodes still tappable. Along the bottom: the focused route's levels
    /// as a strip like a level select (a house, the level chips with their stars or lock, the school) and a chip for each route
    /// to change the focus.
    /// The picture fills the screen behind the bars, fitted so that everything on it shows between the header and the strip, and
    /// it pans and zooms (<see cref="UIMapView"/>: a drag, a pinch, the mouse wheel, or the + / - / fit buttons at the right).
    /// The nodes, pins, names and route lines grow on screen more slowly than the town as it zooms in
    /// (<see cref="MapViewMath.ItemScale"/>), so they stay the right size to read and tap and come further apart; the stops'
    /// names show once there is room for them. Without the picture a plain background takes its place (the routes and nodes
    /// still work); without the layout the strip and the chips still play the game.
    /// </summary>
    public class ChapterMapScreen : FrontEndScreen
    {
        // ---- the layout, in canvas units (the canvas is 1080 tall inside the safe area)
        const float HeaderHeight = 150f;      // FrontEndController's shared header (its title is this screen's "Choose your way to school")
        const float Gap = 6f;
        const float ChipHeight = 92f;         // the route chips, along the very bottom (a name may take two lines on a narrow screen)
        const float ChipBottom = 12f;
        const float StripHeight = 104f;       // the level strip, above them
        const float ChipY = 68f, StarsY = 18f; // inside the strip (from its bottom): the level chips' centres, and the stars or names under them
        const float SideMargin = 12f;
        const float BottomBars = ChipBottom + ChipHeight + Gap + StripHeight + Gap;
        const float ZoomButton = 88f;         // the + / - / fit buttons at the right

        // ---- sizes in the picture's own pixels (the map block is scaled to the screen, about 0.58 when fitted)
        const float RouteWidthOn = 54f, RouteWidthOff = 30f;
        const int LabelFont = TownMapNames.FontSize;   // 50 px of the picture: about 29 canvas units when fitted
        const int StopFont = 40;              // a stop's name, smaller than a level's
        const float StopRadius = TownMap.StopRadius;   // a stop's marker on its route
        const float PinHead = TownMapNames.PinHead;

        static readonly Color Mat = new Color(0.1f, 0.15f, 0.31f);
        static readonly Color Plain = new Color(0.86f, 0.9f, 0.76f);
        static readonly Color Dark = new Color(0.07f, 0.1f, 0.22f, 0.93f);
        static readonly Color HomeRed = HomeInfo.DoorColor;   // the red of the house's front door, as in every level and the Holiday Run
        static readonly Color SchoolBlue = new Color(0.22f, 0.36f, 0.72f);

        RectTransform viewRect;               // the whole screen: the picture is panned and zoomed in it
        UIMapView view;
        RectTransform map;                    // the picture's block (3200 x 1800 pixels), placed and scaled by the view
        RawImage picture;
        Image plain;
        Texture2D texture;
        RectTransform routeLayer, textLayer, nodeLayer, stripRoot;
        MapPainter markerPainter;
        UIMapMesh markerMesh;
        readonly Dictionary<string, MapPainter> routePainters = new Dictionary<string, MapPainter>();
        readonly Dictionary<string, UIMapMesh> routeMeshes = new Dictionary<string, UIMapMesh>();
        readonly Dictionary<string, Button> chips = new Dictionary<string, Button>();
        readonly Dictionary<string, Text> chipStars = new Dictionary<string, Text>();
        readonly Dictionary<string, RectTransform> chipMedals = new Dictionary<string, RectTransform>();   // a route walked all the way to school
        readonly List<Rect> taken = new List<Rect>();     // boxes of the texts already placed on the picture
        readonly List<Rect> drawn = new List<Rect>();     // what is drawn on the picture besides the nodes (pins, names, the pill): the level names keep off it
        readonly Dictionary<string, MapName> names = new Dictionary<string, MapName>();   // the focused route's level names, where they go
        readonly List<MapItem> items = new List<MapItem>();   // what keeps its size as the view zooms
        readonly List<StopLabel> stopLabels = new List<StopLabel>();
        readonly List<GameObject> zoomDetail = new List<GameObject>();   // district and street names: shown only zoomed in
        const float DetailZoom = 1.4f;
        /// <summary>A light, even wash over the picture so the focused route, its levels and its names stand out crisply on it.</summary>
        static readonly Color PictureWash = new Color(0.96f, 0.97f, 1f, 0.24f);
        readonly Dictionary<string, Image> chipBadges = new Dictionary<string, Image>();
        readonly Dictionary<string, Image> chipBadgeIcons = new Dictionary<string, Image>();
        string focus;
        bool firstShow, popIn;                // the nodes pop in when the map is opened, not each time the focus moves

        // What the map points out, worked out each time it is shown or the focus moves (Survey): the level to play next (a new
        // one, or the first leg of a stage to walk again after a late trip) and the level a late trip holds back.
        enum Beacon { None, Play, Replay, Late }
        LevelDefinition nextLevel, heldBack;
        Route lateRoute;
        bool replay;
        RectTransform banner;
        readonly Dictionary<string, float> tagShift = new Dictionary<string, float>();   // how far a tag slides sideways off the nodes beside it
        Text bannerText;
        Button bannerButton;
        const float BannerHeight = 96f;
        const int TagFont = 58;               // the tags over the next and the late level (picture pixels: about 27 canvas units when fitted)
        const float TagHeight = 96f;
        static readonly Color PlayGold = new Color(1f, 0.74f, 0.16f);
        static readonly Color ReplayOrange = new Color(1f, 0.52f, 0.14f);
        static readonly Color LateRed = new Color(0.88f, 0.24f, 0.2f);
        float itemScale = 1f;                 // the things drawn on the picture against the picture (1 when fitted, smaller zoomed in)

        /// <summary>Something drawn on the picture that keeps its size as the view zooms: it is scaled by the item scale about its anchor.</summary>
        struct MapItem
        {
            public RectTransform rect;        // null for a box that only keeps the stops' names off something drawn in a mesh (a pin)
            public Vector2 anchor;            // the point of the picture it belongs to (pixels, y down)
            public Vector2 offset;            // its middle from the anchor at item scale 1 (pixels, y down)
            public Rect box;                  // what it covers at item scale 1 (pixels, y down)
            public bool blocks;               // the stops' names keep off it
        }

        /// <summary>A stop's name beside its marker: shown only when the view is zoomed in far enough for it to touch nothing.</summary>
        struct StopLabel
        {
            public RectTransform rect;
            public Vector2 marker;            // the stop on its route (pixels)
            public Vector2 offset;            // the name's middle from the marker at item scale 1
            public Vector2 size;              // the name's box at item scale 1
        }

        public override string Title { get { return Loc.T("map.choose"); } }

        /// <summary>The mat is opaque and reaches well past the safe area: nothing of the 3D street shows.</summary>
        public override bool CoversStage { get { return true; } }

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

            // A dark wash at the top so the header reads over the picture, and a lighter one under the bars at the bottom.
            var wash = UIKit.Icon(root, "TopWash", ProceduralSprites.VerticalGradient, new Color(Mat.r, Mat.g, Mat.b, 0.92f), 10f);
            wash.preserveAspect = false;
            wash.raycastTarget = false;
            wash.rectTransform.anchorMin = new Vector2(0f, 1f);
            wash.rectTransform.anchorMax = new Vector2(1f, 1f);
            wash.rectTransform.pivot = new Vector2(0.5f, 1f);
            wash.rectTransform.offsetMin = new Vector2(-900f, -(HeaderHeight + 40f));
            wash.rectTransform.offsetMax = new Vector2(900f, 0f);
            var under = UIKit.Icon(root, "BottomWash", ProceduralSprites.VerticalGradient, new Color(Mat.r, Mat.g, Mat.b, 0.7f), 10f);
            under.preserveAspect = false;
            under.raycastTarget = false;
            under.rectTransform.anchorMin = new Vector2(0f, 0f);
            under.rectTransform.anchorMax = new Vector2(1f, 0f);
            under.rectTransform.pivot = new Vector2(0.5f, 0.5f);                  // turned about its middle, so it stays where it is
            under.rectTransform.offsetMin = new Vector2(-900f, -450f);
            under.rectTransform.offsetMax = new Vector2(900f, BottomBars * 0.75f);
            under.rectTransform.localRotation = Quaternion.Euler(0f, 0f, 180f);   // opaque at the bottom, clear above

            BuildZoomButtons(root);
            stripRoot = UIKit.Rect(root, "Strip");
            BuildChips(root);
            BuildBanner(root);
        }

        /// <summary>
        /// The banner under the header while a late trip to school holds a level back: an alarm clock, what happened and what to do
        /// ("Late for school on Seaside Road! Walk it again from home and beat the bell to open level 15."), and From home.
        /// </summary>
        void BuildBanner(RectTransform root)
        {
            var face = UIKit.Card(root, "LateBanner", new Color(1f, 0.96f, 0.93f));
            banner = (RectTransform)face.transform.parent;
            UIKit.Place(banner, new Vector2(0.5f, 1f), new Vector2(0f, -(HeaderHeight + 2f)), new Vector2(1180f, BannerHeight), new Vector2(0.5f, 1f));
            var block = UIKit.Panel(face.transform, "Clock", LateRed, ProceduralSprites.RoundedEdge);
            block.rectTransform.anchorMin = new Vector2(0f, 0f);
            block.rectTransform.anchorMax = new Vector2(0f, 1f);
            block.rectTransform.pivot = new Vector2(0f, 0.5f);
            block.rectTransform.sizeDelta = new Vector2(BannerHeight, 0f);
            block.rectTransform.anchoredPosition = Vector2.zero;
            block.raycastTarget = false;
            var clockIcon = UIKit.Icon(block.transform, "Icon", ProceduralSprites.Clock, Color.white, 60f);
            UIKit.Place(clockIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(60f, 60f));
            clockIcon.gameObject.AddComponent<UIPulse>().amount = 0.08f;
            bannerText = UIKit.Label(face.transform, "Text", "", 30, UITheme.Ink, TextAnchor.MiddleLeft, true);
            bannerText.rectTransform.anchorMin = Vector2.zero;
            bannerText.rectTransform.anchorMax = Vector2.one;
            bannerText.rectTransform.offsetMin = new Vector2(BannerHeight + 20f, 8f);
            bannerText.rectTransform.offsetMax = new Vector2(-300f, -8f);
            bannerText.resizeTextForBestFit = true;
            bannerText.resizeTextMinSize = 20;
            bannerText.resizeTextMaxSize = 30;
            bannerText.verticalOverflow = VerticalWrapMode.Truncate;
            bannerButton = UIKit.Button(face.transform, "FromHome", Loc.T("results.fromHome"), UITheme.Green, PlayLateFromHome, 32);
            UIKit.Place((RectTransform)bannerButton.transform, new Vector2(1f, 0.5f), new Vector2(-18f, UIButtonFx.Depth * 0.5f), new Vector2(260f, 68f), new Vector2(1f, 0.5f));
            banner.gameObject.SetActive(false);
        }

        void PlayLateFromHome()
        {
            var catalog = Controller.levels;
            var first = lateRoute != null && catalog != null ? catalog.FindById(lateRoute.levels[0]) : null;
            if (first != null) Controller.PlayLevel(first);
        }

        /// <summary>Works out the level to play next and any level a late trip holds back, and shows or hides the banner (the map's room above it follows).</summary>
        void Survey(LevelCatalog catalog)
        {
            bool any = catalog != null && catalog.levels.Count > 0;
            nextLevel = any ? LevelUnlocks.NextToPlay(catalog) : null;
            heldBack = any ? LevelUnlocks.FirstHeldBack(catalog, out lateRoute) : null;
            if (heldBack == null) lateRoute = null;
            replay = lateRoute != null && nextLevel != null && lateRoute.levels.Length > 0 && lateRoute.levels[0] == nextLevel.levelId;
            if (banner == null) return;
            bool show = heldBack != null;
            banner.gameObject.SetActive(show);
            if (show)
            {
                string number = heldBack.levelId.TrimStart('L').TrimStart('0');
                bannerText.text = Loc.F("map.lateBanner", Loc.T(lateRoute.NameKey), number);
                bannerButton.GetComponentInChildren<Text>().text = Loc.T("results.fromHome");
            }
            if (view != null)
            {
                var inset = view.insets;
                inset.w = HeaderHeight + (show ? BannerHeight + 8f : 0f);
                view.insets = inset;
            }
        }

        /// <summary>What the map says about a level: the next to play (or to play again), held back by a late trip, or nothing.</summary>
        Beacon BeaconFor(LevelDefinition def, bool unlocked)
        {
            if (def == null) return Beacon.None;
            if (def == heldBack) return Beacon.Late;
            if (def == nextLevel && unlocked && (replay || !SaveSystem.IsCompleted(def.levelId))) return replay ? Beacon.Replay : Beacon.Play;
            return Beacon.None;
        }

        static Color ColourOf(Beacon beacon)
        {
            return beacon == Beacon.Late ? LateRed : beacon == Beacon.Replay ? ReplayOrange : PlayGold;
        }

        static string TagText(Beacon beacon)
        {
            return Loc.T(beacon == Beacon.Late ? "map.late" : beacon == Beacon.Replay ? "map.tryAgain" : "map.play");
        }

        static Sprite TagIcon(Beacon beacon)
        {
            return beacon == Beacon.Late ? ProceduralSprites.Clock : beacon == Beacon.Replay ? ProceduralSprites.RetryIcon : ProceduralSprites.PlayIcon;
        }

        /// <summary>The tag's size and its middle above its node (picture pixels, y down) for a node drawn at <paramref name="scale"/>.</summary>
        static Vector2 TagSize(Beacon beacon, float scale)
        {
            float w = TownMapNames.Width(TagText(beacon), TagFont) + TagHeight * 1.05f + 30f;
            return new Vector2(w, TagHeight) * TagScale(scale);
        }

        /// <summary>The tags are as big on the other routes as on the focused one: they are what the map has to say.</summary>
        static float TagScale(float nodeScale) { return 1f; }

        static float TagLift(float scale)
        {
            return TownMap.NodeRadius * scale + 26f * TagScale(scale) + TagHeight * 0.5f * TagScale(scale);
        }

        /// <summary>
        /// How far (picture pixels, + right) a tag over <paramref name="node"/> slides so that it covers as little as it can of the
        /// other nodes' discs (and stays over its own): straight above if that is clear, else the nearest clear step either side.
        /// </summary>
        static float TagShift(TownNode node, Vector2 size, float lift, Route focusRoute, System.Func<string, bool> drawn)
        {
            float best = 0f, bestCover = float.MaxValue;
            float limit = Mathf.Max(0f, size.x * 0.5f - 40f);
            for (int step = 0; step <= 8; step++)
            {
                for (int side = -1; side <= 1; side += 2)
                {
                    float dx = side * step * limit / 8f;
                    var box = new Rect(node.pos.x + dx - size.x * 0.5f, node.pos.y - lift - size.y * 0.5f, size.x, size.y);
                    float cover = 0f;
                    foreach (var other in TownMap.Nodes)
                    {
                        if (other == node || !drawn(other.levelId)) continue;
                        float r = TownMap.NodeRadius * (RouteTable.Of(other.levelId) == focusRoute ? 1f : TownMapNames.OtherNodeScale) + 8f;
                        float ox = Mathf.Max(0f, Mathf.Min(box.xMax, other.pos.x + r) - Mathf.Max(box.xMin, other.pos.x - r));
                        float oy = Mathf.Max(0f, Mathf.Min(box.yMax, other.pos.y + r) - Mathf.Max(box.yMin, other.pos.y - r));
                        cover += ox * oy;
                    }
                    // A little bias toward the middle, so a tag only moves when that clears something.
                    cover += Mathf.Abs(dx) * 0.5f;
                    if (cover < bestCover) { bestCover = cover; best = dx; }
                    if (step == 0) break;
                }
            }
            return best;
        }

        void BuildMap(RectTransform root)
        {
            Vector2 frame = TownMap.FrameSize;

            // The view: the whole screen. The picture fills it behind the header and the bars, and at zoom 1 everything drawn
            // on it fits between them (the insets); it is panned and zoomed in it.
            viewRect = UIKit.Stretch(UIKit.Rect(root, "MapView"));
            var catcher = viewRect.gameObject.AddComponent<Image>();      // takes the drags and pinches on the picture
            catcher.color = Color.clear;
            catcher.raycastTarget = true;
            view = viewRect.gameObject.AddComponent<UIMapView>();

            map = UIKit.Rect(viewRect, "Map");
            UIKit.Place(map, new Vector2(0.5f, 0.5f), Vector2.zero, frame, new Vector2(0.5f, 0.5f));
            view.content = map;
            view.designSize = frame;
            view.fitRect = ContentBounds(frame);
            view.coverRect = new Rect(0f, 0f, frame.x, frame.y);
            float side = SideMargin + ZoomButton + 16f;
            view.insets = new Vector4(SideMargin, BottomBars, side, HeaderHeight);
            view.maxZoom = 3f;
            view.Changed += OnViewChanged;

            // The picture; a plain background stands in until (or unless) it loads.
            var plainRect = UIKit.Stretch(UIKit.Rect(map, "Plain"));
            plain = plainRect.gameObject.AddComponent<Image>();
            plain.color = Plain;
            plain.raycastTarget = false;
            var pictureRect = UIKit.Stretch(UIKit.Rect(map, "Picture"));
            picture = pictureRect.gameObject.AddComponent<RawImage>();
            picture.raycastTarget = false;
            CartoonPicture.On(picture, CartoonPicture.Kind.Painted);   // the town, painted like the streets with the classic cartoon filter
            picture.enabled = false;
            BuildFades(frame);
            var washRect = UIKit.Stretch(UIKit.Rect(map, "Wash"));
            var wash = washRect.gameObject.AddComponent<Image>();
            wash.color = PictureWash;
            wash.raycastTarget = false;

            routeLayer = UIKit.Stretch(UIKit.Rect(map, "Routes"));
            foreach (var route in TownMap.Routes)
            {
                var painter = new MapPainter();
                routePainters[route.id] = painter;
                routeMeshes[route.id] = UIMapMesh.Create(routeLayer, "Route_" + route.id, painter, frame);
            }
            markerPainter = new MapPainter();
            markerMesh = UIMapMesh.Create(map, "Markers", markerPainter, frame);
            DrawMarkers();
            textLayer = UIKit.Stretch(UIKit.Rect(map, "Texts"));     // filled for each focus (BuildTexts)
            nodeLayer = UIKit.Stretch(UIKit.Rect(map, "Nodes"));
        }

        /// <summary>
        /// The part of the picture the view fits at zoom 1: every node with its stars, the two pins and every route, with a margin
        /// round them (the layout's core if it has none of these).
        /// </summary>
        static Rect ContentBounds(Vector2 frame)
        {
            Rect core = TownMap.Core.width > 0f ? TownMap.Core : TownMap.ExpectedCore;
            if (!TownMap.Available || TownMap.Nodes.Length == 0) return core;
            float x0 = float.MaxValue, y0 = float.MaxValue, x1 = float.MinValue, y1 = float.MinValue;
            System.Action<Rect> add = r =>
            {
                x0 = Mathf.Min(x0, r.xMin); y0 = Mathf.Min(y0, r.yMin);
                x1 = Mathf.Max(x1, r.xMax); y1 = Mathf.Max(y1, r.yMax);
            };
            float r0 = TownMap.NodeRadius + 10f;
            foreach (var node in TownMap.Nodes) add(new Rect(node.pos.x - r0, node.pos.y - r0, 2f * r0, 2f * r0 + 40f));
            foreach (string id in new[] { "home", "school" }) add(TownMapNames.PinBox(TownMap.Place(id)));
            foreach (var route in TownMap.Routes)
                foreach (var p in route.points) add(new Rect(p.x, p.y, 0f, 0f));
            const float margin = 40f;
            var bounds = Rect.MinMaxRect(x0 - margin, y0 - margin, x1 + margin, y1 + margin);
            // Never more than the picture.
            return Rect.MinMaxRect(Mathf.Max(0f, bounds.xMin), Mathf.Max(0f, bounds.yMin), Mathf.Min(frame.x, bounds.xMax), Mathf.Min(frame.y, bounds.yMax));
        }

        /// <summary>The + / - / fit buttons, one above the other at the right, in the middle of the room the bars leave.</summary>
        void BuildZoomButtons(RectTransform root)
        {
            float x = -(SideMargin + 8f);
            float middle = (BottomBars - HeaderHeight) * 0.5f;
            ZoomButtonAt(root, "ZoomIn", "+", new Vector2(x, middle + ZoomButton + 18f), () => view.ZoomBy(1.6f));
            ZoomButtonAt(root, "ZoomOut", "-", new Vector2(x, middle), () => view.ZoomBy(1f / 1.6f));
            var fitButton = ZoomButtonAt(root, "ZoomFit", "", new Vector2(x, middle - ZoomButton - 18f), () => view.Fit());
            // The fit button's picture: the four corners of a frame.
            var painter = new MapPainter();
            Color ink = UITheme.Navy;
            foreach (var c in new[] { new Vector2(-1f, -1f), new Vector2(1f, -1f), new Vector2(1f, 1f), new Vector2(-1f, 1f) })
            {
                Vector2 corner = new Vector2(50f, 50f) + c * 22f;
                painter.Stroke(new[] { corner - new Vector2(c.x * 13f, 0f), corner, corner - new Vector2(0f, c.y * 13f) }, 7f, ink, false, true);
            }
            var glyph = UIMapMesh.Create(fitButton.transform.Find("Face"), "Glyph", painter, new Vector2(100f, 100f));
            UIKit.Place(glyph.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(ZoomButton * 0.8f, ZoomButton * 0.8f), new Vector2(0.5f, 0.5f));
        }

        Button ZoomButtonAt(RectTransform root, string name, string label, Vector2 at, UnityEngine.Events.UnityAction onClick)
        {
            var button = UIKit.Button(root, name, label, UITheme.Paper, onClick, 60, UITheme.Navy);
            UIKit.Place((RectTransform)button.transform, new Vector2(1f, 0.5f), at, new Vector2(ZoomButton, ZoomButton), new Vector2(1f, 0.5f));
            UIKit.MakeRound(button);
            // A touch target a little bigger than the disc.
            var hit = UIKit.Rect(button.transform, "Hit");
            UIKit.Place(hit, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(ZoomButton + 20f, ZoomButton + 20f), new Vector2(0.5f, 0.5f));
            ClearHit(hit);
            return button;
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

        /// <summary>Keeps something drawn on the picture at the item scale: scaled about <paramref name="anchor"/>, its middle <paramref name="offset"/> from it at scale 1.</summary>
        void Track(RectTransform rect, Vector2 anchor, Vector2 offset, Rect box, bool blocks = true)
        {
            var item = new MapItem { rect = rect, anchor = anchor, offset = offset, box = box, blocks = blocks };
            items.Add(item);
            Apply(item);
        }

        /// <summary>A box the stops' names keep off that is drawn in a mesh (scaled with the item scale about <paramref name="anchor"/>).</summary>
        void Block(Vector2 anchor, Rect box)
        {
            items.Add(new MapItem { anchor = anchor, box = box, blocks = true });
        }

        void Apply(MapItem item)
        {
            if (item.rect == null) return;
            item.rect.localScale = new Vector3(itemScale, itemScale, 1f);
            item.rect.anchoredPosition = At(item.anchor + item.offset * itemScale);
        }

        /// <summary>
        /// The view moved or zoomed. The things drawn on the picture take the item scale for the zoom (they grow on screen more
        /// slowly than the town); when it has changed by more than a little they are scaled again, the route lines and pins drawn
        /// again at the new widths, and the stops' names shown where they now fit.
        /// </summary>
        void OnViewChanged(float zoom, float scale)
        {
            float s = MapViewMath.ItemScale(zoom);
            if (Mathf.Abs(s - itemScale) <= itemScale * 0.02f && !(s == 1f && itemScale != 1f)) return;
            itemScale = s;
            foreach (var item in items) Apply(item);
            if (focus != null) DrawRoutes(Controller.levels);
            DrawMarkers();
            UpdateStopLabels();
            UpdateZoomDetail();
        }

        /// <summary>The house and the school: a pin over each, at the item scale (drawn again when it changes).</summary>
        void DrawMarkers()
        {
            markerPainter.Clear();
            if (TownMap.Available)
            {
                float head = PinHead * itemScale;
                Vector2 headHome = MapGlyphs.Pin(markerPainter, TownMap.Home, head, HomeRed);
                MapGlyphs.House(markerPainter, headHome + new Vector2(0f, 2f * itemScale), head * 1.15f, Color.white, HomeRed);
                Vector2 headSchool = MapGlyphs.Pin(markerPainter, TownMap.School, head, SchoolBlue);
                MapGlyphs.School(markerPainter, headSchool + new Vector2(0f, 4f * itemScale), head * 1.25f, Color.white, SchoolBlue);
            }
            markerMesh.Show(markerPainter);
        }

        /// <summary>
        /// The names on the picture for the focused route: home and school, the focused route's level names (placed before the
        /// district and street names, so they get the room they need), the districts and the streets, clear of the nodes and of
        /// each other. Built again each time the focus moves.
        /// </summary>
        void BuildTexts(Route focusRoute, LevelCatalog catalog)
        {
            for (int i = textLayer.childCount - 1; i >= 0; i--) Object.Destroy(textLayer.GetChild(i).gameObject);
            taken.Clear();
            drawn.Clear();
            names.Clear();
            stopLabels.Clear();
            if (!TownMap.Available) return;
            zoomDetail.Clear();
            // Boxes already spoken for: the discs of the nodes that are drawn (the focused route's with room for their stars, and the
            // other routes' next or late level, smaller) and the two pins.
            foreach (var node in TownMap.Nodes)
            {
                if (!Drawn(node.levelId, focusRoute)) continue;
                bool focused = RouteTable.Of(node.levelId) == focusRoute;
                float r = TownMap.NodeRadius * (focused ? 1f : TownMapNames.OtherNodeScale);
                taken.Add(new Rect(node.pos.x - r - 6f, node.pos.y - r - 6f, 2f * r + 12f, 2f * r + (focused ? 40f : 12f)));
            }
            foreach (string id in new[] { "home", "school" })
            {
                Rect pin = TownMapNames.PinBox(TownMap.Place(id));
                taken.Add(pin);
                drawn.Add(pin);
            }
            // The tags over the next level and the late one: slid sideways off the nodes beside them, and the names keep off them.
            tagShift.Clear();
            foreach (var def in new[] { nextLevel, heldBack })
            {
                if (def == null || catalog == null) continue;
                var node = TownMap.Node(def.levelId);
                Beacon beacon = BeaconFor(def, LevelUnlocks.IsUnlocked(catalog, def));
                if (node == null || beacon == Beacon.None) continue;
                float scale = RouteTable.Of(def.levelId) == focusRoute ? 1f : TownMapNames.OtherNodeScale;
                Vector2 size = TagSize(beacon, scale);
                float shift = TagShift(node, size, TagLift(scale), focusRoute, id => Drawn(id, focusRoute));
                tagShift[def.levelId] = shift;
                Vector2 centre = node.pos + new Vector2(shift, -TagLift(scale));
                var box = new Rect(centre.x - size.x * 0.5f, centre.y - size.y * 0.5f - 6f, size.x, size.y + 20f);
                taken.Add(box);
                drawn.Add(box);
            }

            // Home and School: the name beside the pin, where there is room for it (TownMapNames.PlaceBox).
            PlaceName("home", Loc.T("place.home"), HomeRed);
            PlaceName("school", Loc.T("place.school"), SchoolBlue);

            // The focused route's level names, where they fit round their nodes (drawn with the nodes, see BuildName).
            if (focusRoute != null)
            {
                var ids = new List<string>(focusRoute.levels);
                if (focusRoute.challenge != null) ids.Add(focusRoute.challenge);
                foreach (var pair in TownMapNames.Place(ids, levelId => NameOf(catalog, levelId), drawn))
                {
                    names[pair.Key] = pair.Value;
                    taken.Add(pair.Value.box);
                }
            }

            // (No "You are here" pill: the next level's PLAY tag says where to go, and the house has its name.)

            // Districts: small capitals, white with a dark outline (the school's is left out: its pin already says so). They are
            // detail: shown once the view is zoomed in, so the fitted map shows only the route, its levels and its names.
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
                Track(t.rectTransform, at.Value, Vector2.zero, new Rect(at.Value - size * 0.5f, size), false);
                zoomDetail.Add(t.gameObject);
            }

            // Streets: named along the road at the angle given (as the art gives the names, not translated), where they touch
            // no node, name or route line. The focused route's own street (Home Street, Market Street, Seaside Road) is always
            // named; the others are detail, shown zoomed in.
            string ownStreet = null;
            if (focusRoute != null)
            {
                var english = StringTables.For("en");
                if (english != null && english.ContainsKey(focusRoute.NameKey)) ownStreet = english[focusRoute.NameKey];
            }
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
                bool own = street.name == ownStreet;
                Track(t.rectTransform, at.Value, Vector2.zero, new Rect(at.Value - size * 0.5f, size), own);
                if (!own) zoomDetail.Add(t.gameObject);
            }
            UpdateZoomDetail();
        }

        /// <summary>
        /// The focused route's stops: each marker keeps the other stops' names off it, and a name beside each marker shows when the
        /// view is zoomed in far enough for it to fit. Built after the nodes and their names, so it knows where they are.
        /// </summary>
        void BuildStopLabels(Route focusRoute)
        {
            if (!TownMap.Available || focusRoute == null || focusRoute.stops == null) return;
            for (int i = 0; i < focusRoute.stops.Length; i++)
            {
                Vector2? marker = TownMap.StopPosition(focusRoute.id, i);
                if (marker == null) continue;
                float r = StopRadius + 6f;
                Block(marker.Value, new Rect(marker.Value.x - r, marker.Value.y - r, 2f * r, 2f * r));
            }
            for (int i = 0; i < focusRoute.stops.Length; i++)
            {
                var stop = RouteTable.StopById(focusRoute.stops[i]);
                Vector2? marker = TownMap.StopPosition(focusRoute.id, i);
                if (stop != null && marker != null) BuildStopLabel(focusRoute, stop, marker.Value);
            }
        }

        /// <summary>
        /// A stop's name beside its marker, on the side of the route line where it would touch least at a zoom of about two; hidden
        /// until it fits (<see cref="UpdateStopLabels"/>).
        /// </summary>
        void BuildStopLabel(Route route, Stop stop, Vector2 marker)
        {
            var line = TownMap.Route(route.id);
            if (line == null) return;
            string text = Loc.T(stop.NameKey);
            var size = new Vector2(TownMapNames.Width(text, StopFont) + 24f, TownMapNames.Height(1, StopFont) + 6f);
            Vector2 dir = TownMap.DirectionAt(line.points, TownMap.DistanceAlong(line.points, marker));
            Vector2 normal = new Vector2(-dir.y, dir.x);
            float reach = Mathf.Abs(normal.x) * size.x * 0.5f + Mathf.Abs(normal.y) * size.y * 0.5f;
            Vector2 offset = normal * (StopRadius + 14f + reach);
            // The side with less in the way at a zoom of about two.
            float s = MapViewMath.ItemScale(2f);
            if (Crowding(marker - offset, size, s) < Crowding(marker + offset, size, s)) offset = -offset;

            var t = UIKit.Label(textLayer, "Stop_" + stop.id, text, StopFont, Color.white, TextAnchor.MiddleCenter, true);
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            UIKit.Place(t.rectTransform, new Vector2(0.5f, 0.5f), At(marker + offset), size, new Vector2(0.5f, 0.5f));
            Outlined(t, 3f);
            stopLabels.Add(new StopLabel { rect = t.rectTransform, marker = marker, offset = offset, size = size });
            Track(t.rectTransform, marker, offset, new Rect(marker + offset - size * 0.5f, size), false);
        }

        /// <summary>How much of what is drawn on the picture a box of <paramref name="size"/> at <paramref name="centre"/> would touch at item scale <paramref name="s"/> (its centre and size scaled about the marker).</summary>
        float Crowding(Vector2 centre, Vector2 size, float s)
        {
            var box = new Rect(centre - size * 0.5f * s, size * s);
            float hit = 0f;
            foreach (var item in items)
            {
                if (!item.blocks) continue;
                Rect other = Scaled(item.box, item.anchor, s);
                if (box.Overlaps(other))
                    hit += Mathf.Max(0f, Mathf.Min(box.xMax, other.xMax) - Mathf.Max(box.xMin, other.xMin)) * Mathf.Max(0f, Mathf.Min(box.yMax, other.yMax) - Mathf.Max(box.yMin, other.yMin));
            }
            return hit;
        }

        /// <summary>A box drawn at item scale 1 as it is at item scale <paramref name="s"/>: shrunk toward the point it belongs to.</summary>
        static Rect Scaled(Rect box, Vector2 anchor, float s)
        {
            Vector2 min = anchor + (box.min - anchor) * s;
            return new Rect(min, box.size * s);
        }

        /// <summary>Shows each stop's name where it touches nothing at the current item scale (nor an earlier stop's name), and only zoomed in.</summary>
        void UpdateStopLabels()
        {
            var shown = new List<Rect>();
            bool zoomed = view != null && view.Zoom >= 1.3f;
            foreach (var label in stopLabels)
            {
                if (label.rect == null) continue;
                Rect box = Scaled(new Rect(label.marker + label.offset - label.size * 0.5f, label.size), label.marker, itemScale);
                bool fits = zoomed;
                if (fits)
                    foreach (var item in items)
                        if (item.blocks && Scaled(item.box, item.anchor, itemScale).Overlaps(box)) { fits = false; break; }
                if (fits)
                    foreach (var other in shown)
                        if (other.Overlaps(box)) { fits = false; break; }
                label.rect.gameObject.SetActive(fits);
                if (fits) shown.Add(box);
            }
        }

        /// <summary>The district and street names that are detail: shown only once the view is zoomed in.</summary>
        void UpdateZoomDetail()
        {
            bool zoomed = view != null && view.Zoom >= DetailZoom;
            foreach (var go in zoomDetail)
                if (go != null && go.activeSelf != zoomed) go.SetActive(zoomed);
        }

        /// <summary>
        /// Whether a level's node is drawn with <paramref name="focusRoute"/> in focus: the focused route's levels and challenge,
        /// and of the other routes only the next level to play and the one a late trip holds back (what the map has to point out).
        /// The other routes are otherwise just faint lines, so the map stays clean.
        /// </summary>
        bool Drawn(string levelId, Route focusRoute)
        {
            if (RouteTable.Of(levelId) == focusRoute) return true;
            if (focusRoute != null && levelId == focusRoute.challenge) return true;
            return (nextLevel != null && nextLevel.levelId == levelId) || (heldBack != null && heldBack.levelId == levelId);
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

        /// <summary>A name beside a place's pin, where <see cref="TownMapNames.PlaceBox"/> finds room for it.</summary>
        void PlaceName(string id, string text, Color colour)
        {
            Rect box = TownMapNames.PlaceBox(TownMap.Place(id), text, LabelFont);
            var t = UIKit.Label(textLayer, "Place_" + id, text, LabelFont, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(t.rectTransform, new Vector2(0.5f, 0.5f), At(box.center), box.size, new Vector2(0.5f, 0.5f));
            Outlined(t);
            taken.Add(box);
            drawn.Add(box);
            Vector2 place = TownMap.Place(id);
            Track(t.rectTransform, place, box.center - place, box);
            Block(place, TownMapNames.PinBox(place));
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
                drawn.Add(box);
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
                // The badge at the chip's top right corner (shown by ShowRoute): a clock for a late trip, play for the next level.
                // In the chip's bottom right corner, beside the stars (the name is above them).
                var badge = UIKit.Icon(face, "Badge", ProceduralSprites.CircleEdge, PlayGold, 42f);
                UIKit.Place(badge.rectTransform, new Vector2(1f, 0f), new Vector2(-28f, 22f), new Vector2(42f, 42f), new Vector2(0.5f, 0.5f));
                var badgeIcon = UIKit.Icon(badge.transform, "Icon", ProceduralSprites.PlayIcon, Color.white, 26f);
                UIKit.Place(badgeIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(26f, 26f));
                badge.gameObject.AddComponent<UIPulse>().amount = 0.08f;
                badge.gameObject.SetActive(false);
                chipBadges[id] = badge;
                chipBadgeIcons[id] = badgeIcon;
                // The route's medal, hanging over the chip's top right corner once it has been walked all the way to school
                // (Cosmetics/RouteRewards; shown by ShowRoute).
                var medal = UI.SchoolRewardPanel.MedalIcon(face, "Medal", Color.white, 46f, true);
                UIKit.Place(medal, new Vector2(1f, 1f), new Vector2(-30f, 4f), new Vector2(46f, 46f), new Vector2(0.5f, 0.5f));
                medal.gameObject.SetActive(false);
                chipMedals[id] = medal;

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
            Survey(Controller.levels);            // the banner (if a late trip holds a level back) takes room above the map
            if (view != null) view.Fit(true);
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

        static ResourceRequest preload;

        /// <summary>
        /// Start reading the map's picture in the background (the title screen, one tap before the map): a 3200 x 1800
        /// texture read and uploaded in the frame the map opened. The map's own load then finds it in memory; until
        /// then nothing changes. Let go with the picture when the map hides.
        /// </summary>
        public static void Preload()
        {
            // (one under way, or done and still in memory: a scene change unloads it)
            if (preload != null && (!preload.isDone || preload.asset != null)) return;
            preload = Resources.LoadAsync<Texture2D>(TownMap.Image);
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
            preload = null;
        }

        void ShowRoute(string id)
        {
            var catalog = Controller.levels;
            focus = id;
            popIn = firstShow;
            firstShow = false;
            var focusRoute = RouteTable.All[RouteTable.IndexOf(id)];
            Survey(catalog);
            for (int i = nodeLayer.childCount - 1; i >= 0; i--) Object.Destroy(nodeLayer.GetChild(i).gameObject);
            for (int i = stripRoot.childCount - 1; i >= 0; i--) Object.Destroy(stripRoot.GetChild(i).gameObject);
            items.Clear();

            DrawRoutes(catalog);
            BuildTexts(focusRoute, catalog);       // the names for this focus (the level names among them)

            foreach (var route in RouteTable.All)
            {
                bool on = route.id == id;
                Color c = ColourOf(catalog, route);
                chips[route.id].targetGraphic.color = on ? Color.Lerp(c, Color.white, 0.5f) : Color.Lerp(c, Color.white, 0.84f);
                chips[route.id].transform.Find("Face").Find("Swatch").GetComponent<Image>().color = c;
                chipStars[route.id].text = StarsOf(route) + " / " + TotalOf(route);
                bool walked = Cosmetics.RouteRewards.IsWalked(route);
                chipMedals[route.id].gameObject.SetActive(walked);
                if (walked) UI.SchoolRewardPanel.TintMedal(chipMedals[route.id], c, true);
                // A badge on the chip of the route that was late (a clock) or that holds the next level (play).
                var nextRoute = nextLevel != null ? RouteTable.Of(nextLevel.levelId) : null;
                Beacon badge = route == lateRoute ? Beacon.Late
                    : route == nextRoute && BeaconFor(nextLevel, catalog != null && LevelUnlocks.IsUnlocked(catalog, nextLevel)) == Beacon.Play ? Beacon.Play : Beacon.None;
                chipBadges[route.id].gameObject.SetActive(badge != Beacon.None);
                if (badge != Beacon.None)
                {
                    chipBadges[route.id].color = ColourOf(badge);
                    chipBadgeIcons[route.id].sprite = TagIcon(badge);
                }
            }

            if (catalog == null || catalog.levels.Count == 0)
            {
                var soon = UIKit.Title(nodeLayer, "ComingSoon", Loc.T("menu.soon"), 160, Color.white);
                UIKit.Stretch(soon.rectTransform);
                return;
            }

            var next = nextLevel;
            BuildStrip(catalog, focusRoute, next);

            // The nodes: the other routes' first (smaller), the focused route's last (on top), its levels named.
            int index = 0;
            foreach (var route in RouteTable.All)
            {
                if (route.id == id) continue;
                BuildNodes(catalog, route, next, false, ref index);
            }
            BuildNodes(catalog, focusRoute, next, true, ref index);

            if (!Store.Monetization.IsChapterUnlocked(focusRoute.chapter)) ShowRouteLock(focusRoute);
            BuildStopLabels(focusRoute);
            UpdateStopLabels();
            // Zoomed in, the view glides to the newly focused route's levels.
            if (view != null && view.Zoom > 1.05f) view.Show(MiddleOf(focusRoute), view.Zoom);
        }

        /// <summary>The middle of a route's level nodes (pixels).</summary>
        static Vector2 MiddleOf(Route route)
        {
            Vector2 sum = Vector2.zero;
            int n = 0;
            foreach (string levelId in route.levels)
            {
                var node = TownMap.Node(levelId);
                if (node == null) continue;
                sum += node.pos;
                n++;
            }
            return n > 0 ? sum / n : TownMap.Core.center;
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
                float k = itemScale;
                if (!on)
                {
                    // Another route: a thin, faint line in its colour, nothing on it (its chip at the bottom brings it into focus).
                    Color faint = Color.Lerp(core, Color.white, 0.25f);
                    faint.a = 0.5f;
                    painter.Stroke(line.points, RouteWidthOff * 0.55f * k, faint, false, true);
                    routeMeshes[route.id].Show(painter);
                    routeMeshes[route.id].transform.SetSiblingIndex(order++);
                    continue;
                }
                float width = RouteWidthOn * k;
                float casing = 13f * k;
                painter.Stroke(line.points, width + casing * 2f, Color.white, false, true);
                painter.Stroke(line.points, width, core, false, true);
                painter.Dashed(line.points, 7f * k, 24f * k, 34f * k, new Color(1f, 1f, 1f, 0.85f));
                // The dotted branch from the route to its challenge's node.
                if (route.challenge != null)
                {
                    var node = TownMap.Node(route.challenge);
                    if (node != null)
                    {
                        Vector2 near;
                        TownMap.DistanceTo(line.points, node.pos, out near);
                        painter.Dashed(new[] { near, node.pos }, (on ? 20f : 14f) * k, 26f * k, 20f * k, Color.white);
                        painter.Dashed(new[] { near, node.pos }, (on ? 12f : 8f) * k, 26f * k, 20f * k, core);
                    }
                }
                // The stops between the levels: a small white marker on the line with a dot of the route's colour (Levels/RouteTable).
                if (route.stops != null)
                    for (int i = 0; i < route.stops.Length; i++)
                    {
                        Vector2? at = TownMap.StopPosition(route.id, i);
                        if (at == null) continue;
                        float r = StopRadius * k * (on ? 1f : 0.8f);
                        painter.Disc(at.Value, r + 3.5f * k, MapGlyphs.Ink);
                        painter.Disc(at.Value, r, Color.white);
                        painter.Disc(at.Value, r * 0.5f, core);
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
                // The other routes show only what the map has to point out (the next level, a late one): see Drawn.
                if (!focused && !Drawn(levelId, null)) continue;
                BuildNode(catalog, def, spot, colour, BeaconFor(def, LevelUnlocks.IsUnlocked(catalog, def)), focused, index++);
            }
        }

        void BuildNode(LevelCatalog catalog, LevelDefinition def, TownNode spot, Color colour, Beacon beacon, bool named, int index)
        {
            bool unlocked = LevelUnlocks.IsUnlocked(catalog, def);
            int stars = SaveSystem.StarsFor(def.levelId);

            // The other routes' nodes are smaller and show no stars while a route is in focus (their names are not shown either).
            float scale = named ? 1f : TownMapNames.OtherNodeScale;
            float diameter = TownMap.NodeDiameter * scale;
            var holder = UIKit.Rect(nodeLayer, "Node_" + def.levelId);
            UIKit.Place(holder, new Vector2(0.5f, 0.5f), At(spot.pos), new Vector2(diameter, diameter), new Vector2(0.5f, 0.5f));
            float r = diameter * 0.5f + 6f;
            Track(holder, spot.pos, Vector2.zero, new Rect(spot.pos.x - r, spot.pos.y - r, 2f * r, 2f * r + (named ? 40f : 0f)));
            // The holder takes the zoom's item scale; what is drawn goes on a child of the same size, which pops in.
            var holderRect = holder;
            holder = UIKit.Stretch(UIKit.Rect(holderRect, "Body"));
            // The nodes pop in one after another when the map is opened (not every time the focus moves).
            if (popIn) UIKit.PopIn(holder.gameObject, Mathf.Min(index, 14) * 0.03f);

            Color face = def.isChallenge ? UITheme.Gold : colour;
            // Locked by a late trip to school: red with an alarm clock; a tap says why, and offers the way back to it.
            var late = unlocked ? null : LevelUnlocks.HeldBackBy(catalog, def);
            // Locked: a pale shade of the route's colour with its lock (quieter than grey, so the levels to play stand out).
            Color disc = unlocked ? face : late != null ? LateRed : Color.Lerp(Color.Lerp(face, UITheme.Locked, 0.35f), Color.white, 0.45f);
            var button = UIKit.Button(holder, "Button", "", disc, () => Tap(catalog, def, late));
            UIKit.Place((RectTransform)button.transform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(diameter, diameter), new Vector2(0.5f, 0.5f));
            button.interactable = unlocked || late != null;
            UIKit.MakeRound(button);
            // The next level's disc breathes (its stars and name stay still; UIPulse hands the scale to the button's press animation).
            if (beacon == Beacon.Play || beacon == Beacon.Replay) button.gameObject.AddComponent<UIPulse>();

            // The touch target: the disc, or about 118 canvas units across if that is more (a clear square: taps reach the button).
            float hitSize = Mathf.Max(TownMap.NodeDiameter, 118f / Mathf.Max(0.2f, ScaleNow()));
            var hit = UIKit.Rect(button.transform, "Hit");
            UIKit.Place(hit, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(hitSize, hitSize), new Vector2(0.5f, 0.5f));
            ClearHit(hit);

            if (unlocked)
            {
                string number = def.isChallenge ? "!" : def.levelId.TrimStart('L').TrimStart('0');
                var label = UIKit.Title(button.transform.Find("Face"), "Number", number, Mathf.RoundToInt(78 * scale), Color.white);
                UIKit.Stretch(label.rectTransform);
            }
            else
            {
                var lockIcon = UIKit.Icon(button.transform.Find("Face"), "Lock", late != null ? ProceduralSprites.Clock : ProceduralSprites.Lock,
                    new Color(1f, 1f, 1f, 0.95f), 78f * scale);
                UIKit.Place(lockIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(78f * scale, 78f * scale));
            }

            // Stars on the disc's lower rim, on a light pill so they read on the picture whether earned (gold) or not (grey); a locked level has none to show.
            if (unlocked && named)
            {
                float starSize = 40f, drop = TownMap.NodeRadius - 4f;
                var starRow = UIKit.Stars(holder, "Stars", stars, starSize, 4f);
                var pill = UIKit.Panel(holder, "StarsPill", new Color(1f, 1f, 1f, 0.94f), ProceduralSprites.RoundedEdgeSmall);
                pill.raycastTarget = false;
                UIKit.Place(pill.rectTransform, new Vector2(0.5f, 0.5f), new Vector2(0f, -drop), new Vector2(starRow.sizeDelta.x + 26f, starSize + 14f), new Vector2(0.5f, 0.5f));
                starRow.SetAsLastSibling();
                UIKit.Place(starRow, new Vector2(0.5f, 0.5f), new Vector2(0f, -drop), starRow.sizeDelta, new Vector2(0.5f, 0.5f));
            }

            MapName name;
            if (named && names.TryGetValue(def.levelId, out name))
            {
                BuildName(holder, name, spot.pos);
                Block(spot.pos, name.box);
            }
            // The next level (or the late one) glows: a soft halo and a ring round the disc, breathing (under its name, which
            // stays crisp, and under everything else on the node).
            if (beacon != Beacon.None) Halo(holder, diameter, ColourOf(beacon));
            float shift;
            if (beacon != Beacon.None) Tag(holder, beacon, scale, tagShift.TryGetValue(def.levelId, out shift) ? shift : 0f);
        }

        /// <summary>A soft halo and a ring in <paramref name="colour"/> behind a node's disc, glowing on and off.</summary>
        static void Halo(RectTransform holder, float diameter, Color colour)
        {
            var halo = UIKit.Icon(holder, "Halo", ProceduralSprites.SoftDisc, colour, diameter * 1.9f);
            UIKit.Place(halo.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(diameter * 1.9f, diameter * 1.9f));
            var glow = halo.gameObject.AddComponent<UIGlow>();
            glow.minAlpha = 0.25f; glow.maxAlpha = 0.6f;
            var ring = UIKit.Icon(holder, "Ring", ProceduralSprites.Ring, colour, diameter * 1.32f);
            UIKit.Place(ring.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(diameter * 1.32f, diameter * 1.32f));
            var pulse = ring.gameObject.AddComponent<UIGlow>();
            pulse.minAlpha = 0.6f; pulse.maxAlpha = 1f; pulse.minScale = 0.98f; pulse.maxScale = 1.08f;
            halo.rectTransform.SetAsFirstSibling();
            ring.rectTransform.SetSiblingIndex(1);
        }

        /// <summary>
        /// The tag over a node: "PLAY" (gold, the next level), "TRY AGAIN" (orange, the first leg of a stage to walk again) or
        /// "LATE!" (red, the level a late trip holds back), with its icon, on a pill pointing down at the disc, bobbing.
        /// </summary>
        static void Tag(RectTransform holder, Beacon beacon, float scale, float shift)
        {
            Color colour = ColourOf(beacon);
            float k = TagScale(scale);
            Vector2 size = TagSize(beacon, scale);
            var tag = UIKit.Rect(holder, "Tag");
            UIKit.Place(tag, new Vector2(0.5f, 0.5f), new Vector2(shift, TagLift(scale)), size, new Vector2(0.5f, 0.5f));
            // The pointer: a small square turned on its corner under the pill, over the node however far the pill slid.
            var pointer = UIKit.Panel(tag, "Pointer", colour, null);
            pointer.type = Image.Type.Simple;
            UIKit.Place(pointer.rectTransform, new Vector2(0.5f, 0f), new Vector2(-shift, 2f * k), new Vector2(40f * k, 40f * k), new Vector2(0.5f, 0.5f));
            pointer.rectTransform.localRotation = Quaternion.Euler(0f, 0f, 45f);
            pointer.raycastTarget = false;
            var pill = UIKit.Panel(tag, "Pill", colour, ProceduralSprites.RoundedEdge);
            UIKit.Stretch(pill.rectTransform);
            pill.raycastTarget = false;
            float iconSize = TagHeight * 0.62f * k;
            var icon = UIKit.Icon(pill.transform, "Icon", TagIcon(beacon), Color.white, iconSize);
            UIKit.Place(icon.rectTransform, new Vector2(0f, 0.5f), new Vector2(TagHeight * 0.55f * k, 0f), new Vector2(iconSize, iconSize), new Vector2(0.5f, 0.5f));
            var text = UIKit.Label(pill.transform, "Text", TagText(beacon), Mathf.RoundToInt(TagFont * k), Color.white, TextAnchor.MiddleCenter, true);
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            text.rectTransform.anchorMin = Vector2.zero;
            text.rectTransform.anchorMax = Vector2.one;
            text.rectTransform.offsetMin = new Vector2(TagHeight * k, 0f);
            text.rectTransform.offsetMax = new Vector2(-14f * k, 0f);
            Outlined(text, 3f);
            tag.gameObject.AddComponent<UIBob>().amount = 14f * k;
        }

        /// <summary>
        /// The level's name where <see cref="TownMapNames.Place"/> put it beside its node (at <paramref name="node"/>): white with
        /// a dark outline, broken onto two lines there if it is long, its lines against the node's side of the box.
        /// </summary>
        void BuildName(RectTransform holder, MapName spot, Vector2 node)
        {
            Vector2 centre = spot.box.center - node;
            centre.y = -centre.y;                 // the layout's y runs down, the UI's up
            TextAnchor anchor = spot.align < 0 ? TextAnchor.MiddleLeft : (spot.align > 0 ? TextAnchor.MiddleRight : TextAnchor.MiddleCenter);
            var name = UIKit.Label(holder, "Name", spot.text, spot.fontSize, Color.white, anchor, true);
            name.horizontalOverflow = HorizontalWrapMode.Overflow;     // broken already, where the placing measured it
            name.verticalOverflow = VerticalWrapMode.Overflow;
            UIKit.Place(name.rectTransform, new Vector2(0.5f, 0.5f), centre, spot.box.size, new Vector2(0.5f, 0.5f));
            name.rectTransform.SetAsFirstSibling();
            Outlined(name);
        }

        /// <summary>A level's name in the current language (its catalog name if the string table has none).</summary>
        static string NameOf(LevelCatalog catalog, string levelId)
        {
            var def = catalog != null ? catalog.FindById(levelId) : null;
            return Loc.T("level." + levelId, def != null ? def.displayName : levelId);
        }

        /// <summary>
        /// The scale the map block is at when fitted, about 0.58: the view's, or (before the canvas has a size, when the screens are
        /// built) worked out for a usual 16:9 screen.
        /// </summary>
        float ScaleNow()
        {
            if (view != null && view.FitScale > 0f && viewRect != null && viewRect.rect.width > 1f) return view.FitScale;
            Vector2 room = new Vector2(UIKit.ReferenceResolution.x - SideMargin * 2f - ZoomButton - 16f, UIKit.ReferenceResolution.y - HeaderHeight - BottomBars);
            Rect fit = view != null ? view.fitRect : (TownMap.Core.width > 0f ? TownMap.Core : TownMap.ExpectedCore);
            return MapViewMath.FitScale(room, fit);
        }

        /// <summary>A level's button: play it, or, if a late trip to school holds it back, say so (<see cref="ShowLate"/>).</summary>
        void Tap(LevelCatalog catalog, LevelDefinition def, Route late)
        {
            if (late == null) Controller.PlayLevel(def);
            else ShowLate(catalog, late);
        }

        /// <summary>
        /// Why a level is still locked after its stage was finished: the trip got to school after the bell. The whole route is
        /// walked again from home, before the bell, to open it; the main button starts that trip.
        /// </summary>
        void ShowLate(LevelCatalog catalog, Route route)
        {
            GameObject root;
            var card = UIKit.Modal(Controller.CanvasRoot, "LateForSchool", new Vector2(980f, 560f), out root);
            UIKit.Header(card.transform, Loc.T("results.lateSchool"), 620f);
            var text = UIKit.Label(card.transform, "Text", Loc.F("map.lateNote", Loc.T(route.NameKey)), 38, UITheme.Ink, TextAnchor.MiddleCenter, true);
            text.rectTransform.anchorMin = Vector2.zero;
            text.rectTransform.anchorMax = Vector2.one;
            text.rectTransform.offsetMin = new Vector2(60f, 170f);
            text.rectTransform.offsetMax = new Vector2(-60f, -76f);
            UIKit.Fit(text, 26);
            var first = catalog.FindById(route.levels[0]);
            var notNow = UIKit.Button(card.transform, "NotNow", Loc.T("map.notNow"), UITheme.Paper, () => Object.Destroy(root), 36, UITheme.Ink);
            UIKit.Place((RectTransform)notNow.transform, new Vector2(0.27f, 0f), new Vector2(0f, 95f), new Vector2(340f, 100f));
            var go = UIKit.Button(card.transform, "FromHome", Loc.T("results.fromHome"), UITheme.Green, () =>
            {
                Object.Destroy(root);
                if (first != null) Controller.PlayLevel(first);
            }, 40);
            UIKit.Place((RectTransform)go.transform, new Vector2(0.73f, 0f), new Vector2(0f, 95f), new Vector2(380f, 100f));
            go.interactable = first != null;
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
            Track((RectTransform)unlock.transform, middle, Vector2.zero, new Rect(middle.x - 600f, middle.y - 130f, 1200f, 260f));
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
                var late = unlocked ? null : LevelUnlocks.HeldBackBy(catalog, def);
                Beacon beacon = BeaconFor(def, unlocked);
                var button = UIKit.Button(stripRoot, "Level_" + levelId, unlocked ? number : "", unlocked ? face : late != null ? LateRed : UITheme.Locked, () => Tap(catalog, def, late), 36);
                var rt = (RectTransform)button.transform;
                UIKit.Place(rt, new Vector2(0f, 0f), new Vector2(x + chip * 0.5f, ChipY), new Vector2(chip, 54f), new Vector2(0.5f, 0.5f));
                button.interactable = unlocked || late != null;
                // The touch target: the whole slot, the chip and its stars, the full height of the bar.
                var hit = UIKit.Rect(button.transform, "Hit");
                UIKit.Place(hit, new Vector2(0.5f, 0.5f), new Vector2(0f, StripHeight * 0.5f - ChipY), new Vector2(chip + gap, StripHeight), new Vector2(0.5f, 0.5f));
                ClearHit(hit);
                if (!unlocked)
                {
                    var lockIcon = UIKit.Icon(button.transform.Find("Face"), "Lock", late != null ? ProceduralSprites.Clock : ProceduralSprites.Lock, new Color(1f, 1f, 1f, 0.95f), 34f);
                    UIKit.Place(lockIcon.rectTransform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(34f, 34f));
                }
                if (beacon != Beacon.None)
                {
                    if (beacon != Beacon.Late) button.gameObject.AddComponent<UIPulse>().amount = 0.05f;
                    var marker = UIKit.Icon(stripRoot, "Next", ProceduralSprites.ArrowUp, ColourOf(beacon), 34f);
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
