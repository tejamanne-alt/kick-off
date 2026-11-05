using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>UI sprites drawn in code: rounded panels, circles, stars, coins, a padlock.</summary>
    public static class ProceduralSprites
    {
        static Sprite rounded, roundedSmall, circle, star, coin, lockIcon, gradient, arrow, pause, ring, softDisc, softEdgeDisc, ballIcon;
        static Sprite trophy, medal, medalRibbon;
        static Sprite roundedEdge, roundedEdgeSmall, circleEdge, check, pitchBadge, holoSheen, goldSheen, stickerIcon, streak, swoosh, bolt, shield, magnet;
        static Sprite jumpIcon, spotHole, thinRing, clock, play, retry;

        /// <summary>A lightning bolt (the turbo power-up).</summary>
        public static Sprite Bolt
        {
            get
            {
                if (bolt != null) return bolt;
                var pts = new[]
                {
                    new Vector2(0.18f, 0.95f), new Vector2(-0.5f, -0.08f), new Vector2(-0.04f, -0.08f),
                    new Vector2(-0.2f, -0.95f), new Vector2(0.52f, 0.14f), new Vector2(0.06f, 0.14f),
                };
                return bolt = MakeShape(96, (u, v) => InPolygon(u, v, pts) ? 1f : 0f);
            }
        }

        /// <summary>A heater shield with a bold chevron cut out of it (the shield power-up).</summary>
        public static Sprite Shield
        {
            get
            {
                return shield != null ? shield : (shield = MakeShape(96, (u, v) =>
                {
                    if (v > 0.88f || v < -0.95f) return 0f;
                    // Flat top, straight sides to the middle, then curving in to a point at the bottom.
                    float half = v >= 0f ? 0.72f : 0.72f * Mathf.Cos(Mathf.Clamp01(-v / 0.95f) * Mathf.PI * 0.5f);
                    if (Mathf.Abs(u) > half) return 0f;
                    // A chevron cut out of it: two slanted bars meeting on the middle line.
                    bool cut = Mathf.Abs(v - (0.1f - Mathf.Abs(u) * 0.85f)) < 0.09f && Mathf.Abs(u) < 0.48f;
                    return cut ? 0f : 1f;
                }));
            }
        }

        /// <summary>A horseshoe magnet, opening downward (the magnet power-up).</summary>
        public static Sprite Magnet
        {
            get
            {
                return magnet != null ? magnet : (magnet = MakeShape(96, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    bool arch = v >= 0f && r < 0.76f && r > 0.4f;
                    bool leg = v < 0f && v > -0.78f && Mathf.Abs(u) < 0.76f && Mathf.Abs(u) > 0.4f;
                    // The two pole tips are left as a gap from the legs, so they read as separate pieces.
                    if (leg && v < -0.5f && v > -0.56f) return 0f;
                    return arch || leg ? 1f : 0f;
                }));
            }
        }

        static bool InPolygon(float u, float v, Vector2[] pts)
        {
            bool inside = false;
            for (int i = 0, j = pts.Length - 1; i < pts.Length; j = i++)
            {
                if ((pts[i].y > v) != (pts[j].y > v) &&
                    u < (pts[j].x - pts[i].x) * (v - pts[i].y) / (pts[j].y - pts[i].y) + pts[i].x)
                    inside = !inside;
            }
            return inside;
        }

        /// <summary>
        /// A speed line pointing right: fat and bright at its head, tapering to nothing at its tail (so a
        /// line that stays behind a runner reads as being left in their wake). 2.56 x 0.32 units at scale 1.
        /// </summary>
        public static Sprite Streak
        {
            get
            {
                return streak != null ? streak : (streak = MakeWide(256, 32, (u, v) =>
                {
                    float ramp = Mathf.Clamp01((u + 1f) / 1.55f);
                    float lengthwise = ramp * ramp * (3f - 2f * ramp);
                    float thick = Mathf.Lerp(0.12f, 1f, lengthwise);
                    float edge = Mathf.Clamp01((thick - Mathf.Abs(v)) / 0.3f);
                    float cap = Mathf.Clamp01((1f - u) / 0.1f);
                    return lengthwise * edge * cap;
                }));
            }
        }

        /// <summary>
        /// A crescent swept round a centre like a thrown arc of light: its bright, rounded head at the
        /// right (angle 0) and a tail curling away counter-clockwise for about 220 degrees, thinning and
        /// fading as it goes. Turn it clockwise to follow a forward somersault. 1.28 units across at scale 1.
        /// </summary>
        public static Sprite Swoosh
        {
            get
            {
                return swoosh != null ? swoosh : (swoosh = MakeShape(128, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float a = Mathf.Atan2(v, u);
                    if (a < -0.3f) a += Mathf.PI * 2f;                      // the tail runs on past 180 degrees
                    const float span = 3.84f;                               // 220 degrees
                    if (a < -0.3f || a > span) return 0f;
                    float t = Mathf.Clamp01(a / span);
                    float centre = Mathf.Lerp(0.8f, 0.7f, t);
                    float half = Mathf.Lerp(0.115f, 0.015f, t);
                    float radial = Mathf.Clamp01((half - Mathf.Abs(r - centre)) / 0.05f);
                    float along = Mathf.Pow(Mathf.Clamp01(1f - t), 1.3f);
                    float head = Mathf.Clamp01((a + 0.3f) / 0.22f);         // a rounded leading end
                    return radial * along * head;
                }));
            }
        }

        /// <summary>A soft band of rainbow light (left to right), for the sheen sweeping over holo stickers.</summary>
        public static Sprite HoloSheen
        {
            get { return holoSheen != null ? holoSheen : (holoSheen = MakeSheen(true)); }
        }

        /// <summary>A soft band of warm white light, for the glint sweeping over gold stickers.</summary>
        public static Sprite GoldSheen
        {
            get { return goldSheen != null ? goldSheen : (goldSheen = MakeSheen(false)); }
        }

        static Sprite MakeSheen(bool rainbow)
        {
            const int w = 128, h = 8;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
            for (int x = 0; x < w; x++)
            {
                float t = (x + 0.5f) / w;
                float band = Mathf.Pow(Mathf.Sin(t * Mathf.PI), 2.2f);
                Color c = rainbow ? Color.HSVToRGB(Mathf.Repeat(t * 1.2f + 0.45f, 1f), 0.45f, 1f) : new Color(1f, 0.97f, 0.82f);
                c.a = band * (rainbow ? 0.5f : 0.6f);
                for (int y = 0; y < h; y++) tex.SetPixel(x, y, c);
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f);
        }

        /// <summary>A little die-cut sticker: a gold star on a white-bordered disc with its corner peeling (prices of sticker rewards).</summary>
        public static Sprite StickerIcon
        {
            get
            {
                if (stickerIcon != null) return stickerIcon;
                const int size = 96;
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                Color gold = UITheme.Gold, ink = EdgeInk, peel = new Color(0.86f, 0.89f, 0.94f);
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                        float r = Mathf.Sqrt(u * u + v * v);
                        // The corner at the bottom right is peeled back: cut off by a diagonal.
                        float cut = u - v - 1.05f;
                        Color c = Color.clear;
                        if (r < 0.96f && cut < 0f)
                        {
                            c = Color.white;
                            if (r > 0.9f) c = ink;
                            else if (r < 0.74f) c = new Color(0.36f, 0.6f, 0.9f);
                            if (r < 0.74f && StarAlpha(u / 0.7f, v / 0.7f) > 0.5f) c = gold;
                            c.a = Mathf.Clamp01((0.96f - r) * size * 0.5f) * Mathf.Clamp01(-cut * size * 0.5f);
                        }
                        // The peeled flap: a pale triangle folded over the cut.
                        if (cut >= 0f && u - 0.1f < 0.96f && -v - 0.1f < 0.96f && (u + 0.02f) + (-v + 0.02f) < 1.78f && cut < 0.42f)
                            c = cut > 0.38f ? ink : peel;
                        tex.SetPixel(x, y, c);
                    }
                }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                stickerIcon = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return stickerIcon;
            }
        }

        /// <summary>
        /// The logo's badge: a disc of mown turf (light and dark stripes) with a dark line round
        /// it, the centre circle, halfway line and centre spot in chalk: where a game kicks off.
        /// </summary>
        public static Sprite PitchBadge
        {
            get
            {
                if (pitchBadge != null) return pitchBadge;
                const int size = 512;
                var px = new Color32[size * size];
                float r = size * 0.5f, line = size * 0.017f, ring = size * 0.283f;
                Color turf = new Color(0.25f, 0.6f, 0.3f), mown = new Color(0.31f, 0.65f, 0.35f), chalk = new Color(0.97f, 0.98f, 0.96f);
                Color edge = new Color(turf.r * EdgeInk.r, turf.g * EdgeInk.g, turf.b * EdgeInk.b);
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float dx = x + 0.5f - r, dy = y + 0.5f - r;
                        float d = Mathf.Sqrt(dx * dx + dy * dy);
                        float a = Mathf.Clamp01(r - d + 0.5f);
                        if (a <= 0f) { px[y * size + x] = new Color32(0, 0, 0, 0); continue; }
                        Color c = Mathf.FloorToInt((x + size * 0.04f) / (size * 0.083f)) % 2 == 0 ? turf : mown;
                        // Chalk: the centre circle, the halfway line across and the centre spot.
                        float chalkA = Mathf.Max(Mathf.Clamp01(line * 0.5f + 0.5f - Mathf.Abs(d - ring)),
                            Mathf.Max(Mathf.Clamp01(line * 0.5f + 0.5f - Mathf.Abs(dy)), Mathf.Clamp01(size * 0.024f + 0.5f - d)));
                        c = Color.Lerp(c, chalk, chalkA * 0.92f);
                        c = Color.Lerp(c, edge, Mathf.Clamp01(size * 0.0095f + 0.5f - (r - d)));
                        c.a = a;
                        px[y * size + x] = c;
                    }
                }
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                tex.SetPixels32(px);
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                pitchBadge = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return pitchBadge;
            }
        }

        /// <summary>
        /// The colour of the line drawn round <see cref="RoundedEdge"/> and <see cref="CircleEdge"/>.
        /// The Image colour multiplies it, so every face gets a thin dark line in a deep shade of
        /// its own colour, like the characters' ink line (near-black on white and grey faces).
        /// </summary>
        public static readonly Color EdgeInk = new Color(0.17f, 0.19f, 0.27f);

        /// <summary>9-sliced rounded rectangle with a thin dark line round it (buttons, panels, cards).</summary>
        public static Sprite RoundedEdge
        {
            get { return roundedEdge != null ? roundedEdge : (roundedEdge = MakeRounded(96, 26, 4f)); }
        }

        /// <summary>A smaller-cornered <see cref="RoundedEdge"/> for small chips, tabs and pills.</summary>
        public static Sprite RoundedEdgeSmall
        {
            get { return roundedEdgeSmall != null ? roundedEdgeSmall : (roundedEdgeSmall = MakeRounded(48, 14, 3f)); }
        }

        /// <summary>A disc with a thin dark line round it (round buttons, badges).</summary>
        public static Sprite CircleEdge
        {
            get
            {
                if (circleEdge != null) return circleEdge;
                const int size = 160;
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float dx = x + 0.5f - size * 0.5f, dy = y + 0.5f - size * 0.5f;
                        float d = Mathf.Sqrt(dx * dx + dy * dy);
                        float a = Mathf.Clamp01(size * 0.5f - d + 0.5f);
                        float line = Mathf.Clamp01(d - (size * 0.5f - 6.5f));
                        tex.SetPixel(x, y, new Color(Mathf.Lerp(1f, EdgeInk.r, line), Mathf.Lerp(1f, EdgeInk.g, line), Mathf.Lerp(1f, EdgeInk.b, line), a));
                    }
                }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                circleEdge = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return circleEdge;
            }
        }

        /// <summary>A bold tick (selected cards).</summary>
        public static Sprite Check
        {
            get
            {
                return check != null ? check : (check = MakeShape(96, (u, v) =>
                {
                    // Two thick strokes: short down-right, long up-right.
                    float a = Segment(u, v, -0.55f, 0.02f, -0.15f, -0.42f);
                    float b = Segment(u, v, -0.15f, -0.42f, 0.6f, 0.45f);
                    return Mathf.Min(a, b) < 0.15f ? 1f : 0f;
                }));
            }
        }

        static float Segment(float u, float v, float ax, float ay, float bx, float by)
        {
            Vector2 p = new Vector2(u, v), a = new Vector2(ax, ay), ab = new Vector2(bx - ax, by - ay);
            float t = Mathf.Clamp01(Vector2.Dot(p - a, ab) / ab.sqrMagnitude);
            return Vector2.Distance(p, a + ab * t);
        }

        /// <summary>Upward chevron (jump button).</summary>
        public static Sprite ArrowUp
        {
            get
            {
                return arrow != null ? arrow : (arrow = MakeShape(96, (u, v) =>
                {
                    // Thick chevron: inside a wide triangle but outside a smaller one shifted down.
                    bool outer = v > -0.6f && v < 0.75f - Mathf.Abs(u) * 1.35f;
                    bool inner = v > -0.6f && v < 0.15f - Mathf.Abs(u) * 1.35f;
                    return outer && !inner && Mathf.Abs(u) < 0.95f ? 1f : 0f;
                }));
            }
        }

        /// <summary>
        /// The jump button: a figure springing up and forward, in the bold rounded strokes of a pictogram: a round head,
        /// the front arm thrown up, the back arm down, the front knee driven up and the back leg pushing off, with a thin
        /// gap where that leg meets the body (after a reference picture the user sent).
        /// </summary>
        public static Sprite JumpIcon
        {
            get
            {
                return jumpIcon != null ? jumpIcon : (jumpIcon = MakeShape(160, (u, v) =>
                {
                    if ((u - 0.08f) * (u - 0.08f) + (v - 0.77f) * (v - 0.77f) < 0.18f * 0.18f) return 1f;   // head
                    // The body and the front leg (knee up), as a distance from their edge: below zero is inside.
                    float body = Mathf.Min(Segment(u, v, -0.03f, 0.36f, -0.13f, -0.12f) - 0.15f,
                                  Mathf.Min(Segment(u, v, -0.07f, -0.12f, 0.3f, 0.03f) - 0.11f, Segment(u, v, 0.3f, 0.03f, 0.18f, -0.46f) - 0.11f));
                    if (body < 0f) return 1f;
                    const float arm = 0.095f;
                    if (Mathf.Min(Segment(u, v, -0.07f, 0.42f, -0.33f, 0.31f), Segment(u, v, -0.33f, 0.31f, -0.45f, -0.1f)) < arm) return 1f;   // back arm, down
                    if (Mathf.Min(Segment(u, v, 0.05f, 0.42f, 0.31f, 0.25f), Segment(u, v, 0.31f, 0.25f, 0.6f, 0.45f)) < arm) return 1f;       // front arm, up
                    // The back leg pushing off, kept a thin gap clear of the body and the front leg.
                    bool back = Mathf.Min(Segment(u, v, -0.15f, -0.22f, -0.17f, -0.54f), Segment(u, v, -0.17f, -0.54f, -0.58f, -0.82f)) < 0.11f;
                    return back && body > 0.035f ? 1f : 0f;
                }));
            }
        }

        /// <summary>
        /// An alarm clock: a round face with two hands (at twelve and three), two bells on
        /// top and two short legs: "late for school" on the map's locked level and its banner.
        /// </summary>
        public static Sprite Clock
        {
            get
            {
                return clock != null ? clock : (clock = MakeShape(128, (u, v) =>
                {
                    float cx = u, cy = v + 0.06f;
                    float r = Mathf.Sqrt(cx * cx + cy * cy);
                    if (Mathf.Abs(r - 0.56f) < 0.1f) return 1f;                                            // the rim
                    if (r < 0.08f) return 1f;                                                               // the middle
                    if (Segment(u, v, 0f, -0.06f, 0f, 0.3f) < 0.06f || Segment(u, v, 0f, -0.06f, 0.24f, -0.06f) < 0.06f) return 1f;   // the hands
                    // Two bells, each a half disc tilted out over the rim.
                    for (int side = -1; side <= 1; side += 2)
                    {
                        float bx = u - side * 0.5f, by = v - 0.62f;
                        float bd = Mathf.Sqrt(bx * bx + by * by);
                        if (bd < 0.22f && (bx * side * 0.5f + by * 0.86f) > -0.02f) return 1f;
                    }
                    if (Segment(u, v, -0.34f, -0.52f, -0.5f, -0.82f) < 0.065f || Segment(u, v, 0.34f, -0.52f, 0.5f, -0.82f) < 0.065f) return 1f;   // legs
                    return 0f;
                }));
            }
        }

        /// <summary>A "play" triangle pointing right, its corners rounded: the next level to play on the map.</summary>
        public static Sprite PlayIcon
        {
            get
            {
                return play != null ? play : (play = MakeShape(96, (u, v) =>
                {
                    // Inside the triangle shrunk by the rounding, or within the rounding of its edges.
                    Vector2 a = new Vector2(-0.4f, 0.52f), b = new Vector2(-0.4f, -0.52f), c = new Vector2(0.56f, 0f);
                    const float round = 0.14f;
                    bool inside = Cross(b - a, new Vector2(u, v) - a) <= 0f && Cross(c - b, new Vector2(u, v) - b) <= 0f && Cross(a - c, new Vector2(u, v) - c) <= 0f;
                    float edge = Mathf.Min(Segment(u, v, a.x, a.y, b.x, b.y), Mathf.Min(Segment(u, v, b.x, b.y, c.x, c.y), Segment(u, v, c.x, c.y, a.x, a.y)));
                    return inside || edge < round ? 1f : 0f;
                }));
            }
        }

        static float Cross(Vector2 p, Vector2 q) { return p.x * q.y - p.y * q.x; }

        /// <summary>A round "again" arrow (most of a ring, an arrowhead at its end): a level to play again on the map.</summary>
        public static Sprite RetryIcon
        {
            get
            {
                return retry != null ? retry : (retry = MakeShape(96, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float ang = Mathf.Repeat(Mathf.Atan2(v, u) * Mathf.Rad2Deg, 360f);
                    // The ring from 60 degrees round (anticlockwise) to 330, open at the top right.
                    if (Mathf.Abs(r - 0.55f) < 0.12f && ang > 60f && ang < 330f) return 1f;
                    // The arrowhead at the 60 degree end, pointing on round the ring (anticlockwise: down and left at this end).
                    Vector2 tip = new Vector2(Mathf.Cos(30f * Mathf.Deg2Rad), Mathf.Sin(30f * Mathf.Deg2Rad)) * 0.55f;
                    Vector2 baseMid = new Vector2(Mathf.Cos(72f * Mathf.Deg2Rad), Mathf.Sin(72f * Mathf.Deg2Rad)) * 0.55f;
                    Vector2 across = baseMid.normalized * 0.3f;
                    Vector2 p = new Vector2(u, v), b1 = baseMid + across, b2 = baseMid - across;
                    float s1 = Cross(b1 - tip, p - tip), s2 = Cross(b2 - b1, p - b1), s3 = Cross(tip - b2, p - b2);
                    bool head = (s1 >= 0f && s2 >= 0f && s3 >= 0f) || (s1 <= 0f && s2 <= 0f && s3 <= 0f);
                    return head ? 1f : 0f;
                }));
            }
        }

        /// <summary>
        /// The controls tour's spotlight: solid outside a circle, clear inside it, with a soft edge. Stretched over a
        /// control's square (the circle fills 80% of it), with plain panels round it for the rest of the screen.
        /// </summary>
        public static Sprite SpotHole
        {
            get
            {
                return spotHole != null ? spotHole : (spotHole = MakeShape(128, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float t = Mathf.Clamp01((r - 0.8f) / 0.16f);
                    return t * t * (3f - 2f * t);
                }));
            }
        }

        /// <summary>Two rounded bars.</summary>
        public static Sprite Pause
        {
            get
            {
                return pause != null ? pause : (pause = MakeShape(96, (u, v) =>
                    Mathf.Abs(v) < 0.6f && (Mathf.Abs(u - 0.3f) < 0.16f || Mathf.Abs(u + 0.3f) < 0.16f) ? 1f : 0f));
            }
        }

        /// <summary>9-sliced rounded rectangle with a faint hand-drawn inner edge.</summary>
        public static Sprite Rounded
        {
            get { return rounded != null ? rounded : (rounded = MakeRounded(96, 34)); }
        }

        public static Sprite RoundedSmall
        {
            get { return roundedSmall != null ? roundedSmall : (roundedSmall = MakeRounded(48, 16)); }
        }

        public static Sprite Circle
        {
            get { return circle != null ? circle : (circle = MakeShape(128, (u, v) => Disc(u, v, 1f))); }
        }

        public static Sprite Star
        {
            get { return star != null ? star : (star = MakeShape(128, StarAlpha)); }
        }

        /// <summary>
        /// A trophy cup (the reward for walking every way to school): the bowl with a star cut in it, a handle each side, the
        /// stem with its knot, and the base on its plinth. Tinted gold where it is used.
        /// </summary>
        public static Sprite Trophy
        {
            get
            {
                return trophy != null ? trophy : (trophy = MakeShape(192, (u, v) =>
                {
                    if (StarAlpha(u / 0.21f, (v - 0.47f) / 0.21f) > 0.5f) return 0f;   // the star on the bowl
                    if (v >= 0.02f && v <= 0.84f && Mathf.Abs(u) <= 0.14f + 0.44f * Mathf.Sqrt((v - 0.02f) / 0.82f)) return 1f;   // the bowl
                    if (v > 0.8f && v <= 0.9f && Mathf.Abs(u) <= 0.63f) return 1f;   // its rim
                    float hx = Mathf.Abs(u), hd = Mathf.Sqrt((hx - 0.56f) * (hx - 0.56f) + (v - 0.5f) * (v - 0.5f));
                    if (hx > 0.5f && Mathf.Abs(hd - 0.2f) < 0.06f) return 1f;   // the handles
                    if (Mathf.Abs(u) < 0.08f && v < 0.05f && v > -0.5f) return 1f;   // the stem
                    if (Mathf.Abs(u) < 0.18f && Mathf.Abs(v + 0.15f) < 0.06f) return 1f;   // its knot
                    if (v <= -0.48f && v > -0.68f && Mathf.Abs(u) < 0.34f) return 1f;   // the base
                    if (v <= -0.71f && v > -0.9f && Mathf.Abs(u) < 0.5f) return 1f;   // the plinth
                    return 0f;
                }));
            }
        }

        /// <summary>A medal's disc (one for each way walked to school): a fine ring inside the rim and a star struck in the middle, cut out.</summary>
        public static Sprite Medal
        {
            get
            {
                return medal != null ? medal : (medal = MakeShape(160, (u, v) =>
                {
                    float d = Mathf.Sqrt(u * u + v * v);
                    if (d > 0.92f || Mathf.Abs(d - 0.74f) < 0.035f) return 0f;
                    return StarAlpha(u / 0.5f, v / 0.5f) > 0.5f ? 0f : 1f;
                }));
            }
        }

        /// <summary>A medal's ribbon: two straps from a flat top down into a V, for behind the disc (tinted in the route's colour).</summary>
        public static Sprite MedalRibbon
        {
            get
            {
                return medalRibbon != null ? medalRibbon : (medalRibbon = MakeShape(160, (u, v) =>
                {
                    if (v > 0.92f) return 0f;
                    return Segment(u, v, -0.5f, 0.95f, -0.04f, -0.25f) < 0.17f || Segment(u, v, 0.5f, 0.95f, 0.04f, -0.25f) < 0.17f ? 1f : 0f;
                }));
            }
        }

        public static Sprite Lock
        {
            get { return lockIcon != null ? lockIcon : (lockIcon = MakeShape(96, LockAlpha)); }
        }

        /// <summary>Vertical white-to-clear gradient, tinted by the Image colour.</summary>
        public static Sprite VerticalGradient
        {
            get
            {
                if (gradient != null) return gradient;
                var tex = new Texture2D(4, 64, TextureFormat.RGBA32, false);
                for (int y = 0; y < 64; y++)
                    for (int x = 0; x < 4; x++)
                        tex.SetPixel(x, y, new Color(1f, 1f, 1f, y / 63f));
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                gradient = Sprite.Create(tex, new Rect(0, 0, 4, 64), new Vector2(0.5f, 0.5f), 100f);
                return gradient;
            }
        }

        /// <summary>Full-colour gold coin icon.</summary>
        public static Sprite Coin
        {
            get
            {
                if (coin != null) return coin;
                const int size = 96;
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                Color gold = UITheme.Gold, dark = new Color(0.8f, 0.55f, 0.1f), ink = UITheme.Ink;
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                        float r = Mathf.Sqrt(u * u + v * v);
                        float a = Mathf.Clamp01((1f - r) * size * 0.5f);
                        Color c = gold;
                        if (r > 0.62f && r < 0.7f) c = dark;
                        if (Mathf.Abs(u) < 0.1f && Mathf.Abs(v) < 0.38f) c = dark;   // engraved bar
                        float hl = Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(-0.35f, 0.4f)) / 0.3f);
                        c = Color.Lerp(c, Color.white, hl * 0.5f);
                        c = Color.Lerp(c, ink, Mathf.Clamp01((r - 0.88f) / 0.07f));
                        c.a = a;
                        tex.SetPixel(x, y, c);
                    }
                }
                tex.Apply();
                coin = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return coin;
            }
        }

        /// <summary>Thin circle outline (ripples, rims).</summary>
        public static Sprite Ring
        {
            get
            {
                return ring != null ? ring : (ring = MakeShape(160, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    return Mathf.Clamp01((0.06f - Mathf.Abs(r - 0.92f)) * 80f);
                }));
            }
        }

        /// <summary>
        /// A thin, crisp ring at the very edge of its square (about 2.6% of the radius): the light border of the touch
        /// controls (JUMP, KICK, the stick's ring and knob).
        /// </summary>
        public static Sprite ThinRing
        {
            get
            {
                return thinRing != null ? thinRing : (thinRing = MakeShape(256, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    return Mathf.Clamp01((0.013f - Mathf.Abs(r - 0.97f)) * 200f);
                }));
            }
        }

        /// <summary>
        /// A disc of frosted glass: even in the middle, slightly brighter just inside the edge,
        /// and fading out softly at the rim instead of having a border.
        /// </summary>
        public static Sprite SoftEdgeDisc
        {
            get
            {
                return softEdgeDisc != null ? softEdgeDisc : (softEdgeDisc = MakeShape(160, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float fade = Mathf.Clamp01((1f - r) / 0.12f);
                    float lip = Mathf.Clamp01(1f - Mathf.Abs(r - 0.86f) / 0.1f) * 0.35f;
                    return fade * fade * (3f - 2f * fade) * (0.75f + lip);
                }));
            }
        }

        /// <summary>Blurry disc for drop shadows and glows.</summary>
        public static Sprite SoftDisc
        {
            get
            {
                return softDisc != null ? softDisc : (softDisc = MakeShape(96, (u, v) =>
                {
                    float r = Mathf.Sqrt(u * u + v * v);
                    float k = Mathf.Clamp01((1f - r) / 0.45f);
                    return k * k * (3f - 2f * k);
                }));
            }
        }

        /// <summary>Full-colour football icon: white with dark patches and an ink rim (kick button).</summary>
        public static Sprite BallIcon
        {
            get
            {
                if (ballIcon != null) return ballIcon;
                const int size = 128;
                var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
                Color ink = new Color(0.12f, 0.12f, 0.16f);
                var centres = new Vector2[6];
                centres[0] = new Vector2(0.08f, 0.06f);
                for (int i = 0; i < 5; i++)
                {
                    float a = i * Mathf.PI * 0.4f + 0.5f;
                    centres[i + 1] = centres[0] + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 0.78f;
                }
                for (int y = 0; y < size; y++)
                {
                    for (int x = 0; x < size; x++)
                    {
                        float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                        float r = Mathf.Sqrt(u * u + v * v);
                        Color c = Color.white;
                        for (int i = 0; i < centres.Length; i++)
                        {
                            Vector2 d = new Vector2(u, v) - centres[i];
                            // Pentagonal patches, squashed toward the rim like on a sphere.
                            float ang = Mathf.Atan2(d.y, d.x);
                            float seg = Mathf.PI * 0.4f;
                            float edge = Mathf.Cos(seg * 0.5f) / Mathf.Cos(Mathf.Repeat(ang + 0.3f, seg) - seg * 0.5f);
                            float patch = (i == 0 ? 0.3f : 0.24f) * edge;
                            if (d.magnitude < patch) c = ink;
                        }
                        // Cel shading: a shadow crescent at the lower right, a highlight top left.
                        float shade = Vector2.Dot(new Vector2(u, v), new Vector2(0.6f, -0.8f));
                        if (shade > 0.45f && c != ink) c = new Color(0.82f, 0.86f, 0.95f);
                        if (Vector2.Distance(new Vector2(u, v), new Vector2(-0.38f, 0.42f)) < 0.14f && c != ink) c = Color.white;
                        c = Color.Lerp(c, ink, Mathf.Clamp01((r - 0.86f) / 0.05f));
                        c.a = Mathf.Clamp01((1f - r) * size * 0.5f);
                        tex.SetPixel(x, y, c);
                    }
                }
                tex.wrapMode = TextureWrapMode.Clamp;
                tex.Apply();
                ballIcon = Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
                return ballIcon;
            }
        }

        delegate float AlphaFn(float u, float v);

        /// <summary>Like <see cref="MakeShape"/> for a sprite that isn't square (u runs across the width, v up the height).</summary>
        static Sprite MakeWide(int width, int height, AlphaFn fn)
        {
            var tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    float u = (x + 0.5f) / width * 2f - 1f, v = (y + 0.5f) / height * 2f - 1f;
                    float du = 0.5f / width, dv = 0.5f / height;
                    float a = (fn(u - du, v - dv) + fn(u + du, v - dv) + fn(u - du, v + dv) + fn(u + du, v + dv)) * 0.25f;
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, width, height), new Vector2(0.5f, 0.5f), 100f);
        }

        static Sprite MakeShape(int size, AlphaFn fn)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float u = (x + 0.5f) / size * 2f - 1f, v = (y + 0.5f) / size * 2f - 1f;
                    // 2x2 supersampling for smooth edges
                    float d = 0.5f / size;
                    float a = (fn(u - d, v - d) + fn(u + d, v - d) + fn(u - d, v + d) + fn(u + d, v + d)) * 0.25f;
                    tex.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f);
        }

        /// <summary>A rounded rectangle; with <paramref name="edge"/> &gt; 0, a line of <see cref="EdgeInk"/> that many pixels wide runs round it.</summary>
        static Sprite MakeRounded(int size, int radius, float edge = 0f)
        {
            var tex = new Texture2D(size, size, TextureFormat.RGBA32, false);
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    float cx = Mathf.Clamp(x + 0.5f, radius, size - radius);
                    float cy = Mathf.Clamp(y + 0.5f, radius, size - radius);
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(cx, cy));
                    float a = Mathf.Clamp01(radius - d + 0.5f);
                    // Distance in from the outline: corners measure from the arc, sides from the edge.
                    float inside = Mathf.Min(radius - d, Mathf.Min(Mathf.Min(x + 0.5f, size - x - 0.5f), Mathf.Min(y + 0.5f, size - y - 0.5f)));
                    float line = edge > 0f ? Mathf.Clamp01(edge + 0.5f - inside) : 0f;
                    tex.SetPixel(x, y, new Color(Mathf.Lerp(1f, EdgeInk.r, line), Mathf.Lerp(1f, EdgeInk.g, line), Mathf.Lerp(1f, EdgeInk.b, line), a));
                }
            }
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.Apply();
            float b = radius + 2;
            return Sprite.Create(tex, new Rect(0, 0, size, size), new Vector2(0.5f, 0.5f), 100f, 0, SpriteMeshType.FullRect, new Vector4(b, b, b, b));
        }

        static float Disc(float u, float v, float r)
        {
            return Mathf.Clamp01((r - Mathf.Sqrt(u * u + v * v)) * 64f);
        }

        static float StarAlpha(float u, float v)
        {
            float ang = Mathf.Atan2(v, u) - Mathf.PI * 0.5f;
            float seg = Mathf.PI * 2f / 5f;
            float t = Mathf.Abs(Mathf.Repeat(ang, seg) - seg * 0.5f) / (seg * 0.5f);
            float limit = Mathf.Lerp(0.95f, 0.42f, 1f - t);
            // Slightly rounded points
            return Mathf.Clamp01((limit - Mathf.Sqrt(u * u + v * v)) * 40f);
        }

        static float LockAlpha(float u, float v)
        {
            // Body
            if (Mathf.Abs(u) < 0.62f && v > -0.85f && v < 0.1f)
            {
                // keyhole
                if (u * u + (v + 0.3f) * (v + 0.3f) < 0.02f) return 0f;
                if (Mathf.Abs(u) < 0.06f && v > -0.62f && v < -0.3f) return 0f;
                return 1f;
            }
            // Shackle (ring)
            float r = Mathf.Sqrt(u * u + (v - 0.15f) * (v - 0.15f));
            if (v > 0.1f && r > 0.32f && r < 0.5f) return 1f;
            return 0f;
        }
    }
}
