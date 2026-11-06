using UnityEngine;

namespace DribbleToSchool.Art
{
    public enum EdgeStyle { Grass, Cobbles, Sand, Concrete, ParkPath, Road }
    public enum SceneryStyle { Houses, Market, Beach, City, Park }

    /// <summary>
    /// Colours and scenery for one chapter: clear anime daylight throughout (docs/ART_DIRECTION.md):
    /// a deep cobalt sky only a little lighter at the horizon, a near-white sun, cool crisp shade,
    /// deep cool sun shadows on the ground and a little blue distance haze, so colours read true
    /// and the characters stand out.
    /// </summary>
    public struct ChapterTheme
    {
        public Color skyTop, skyBottom, sun, cloud;
        public Color far, mid, near;
        public Color groundFill, groundEdge, obstacle, platform, ink;
        public EdgeStyle edge;
        public SceneryStyle scenery;
        /// <summary>The chapter's light and atmosphere (see docs/ART_DIRECTION.md and WorldLook).</summary>
        public Mood mood;

        /// <summary>Light and atmosphere for one chapter: a clear sun against cool sky-tinted shade,
        /// deeper sun shadows on the ground, a cobalt sky with a little blue haze, and the camera's
        /// grade (shadowTint and balance, see PostFX).</summary>
        public struct Mood
        {
            public Color sun, ambientSky, ambientGround, castShadow, zenith, horizon, glow, haze, shadowTint, balance;
            public Vector3 sunDirection, skySunDirection;
            public float hazeStart, hazeEnd, hazeStrength;
        }

        // Shared by every chapter (measured against the reference shots, see docs/ART_DIRECTION.md).
        static readonly Color CastShadow = new Color(0.6f, 0.6f, 0.64f);
        static readonly Color GradeShadows = new Color(0f, 0f, 0.006f);
        static readonly Color GradeBalance = new Color(1f, 1f, 1.01f);

        static Mood MakeMood(Color sun, Color zenith, Color horizon, Color glow, Color shade, Color bounce, Color haze,
            Vector3 sunDir, Vector3 skySunDir, float hazeStart = 50f, float hazeEnd = 700f, float hazeStrength = 0.45f)
        {
            return new Mood
            {
                sun = sun, zenith = zenith, horizon = horizon, glow = glow, ambientSky = shade, ambientGround = bounce,
                castShadow = CastShadow, haze = haze, shadowTint = GradeShadows, balance = GradeBalance,
                sunDirection = sunDir, skySunDirection = skySunDir,
                hazeStart = hazeStart, hazeEnd = hazeEnd, hazeStrength = hazeStrength,
            };
        }

        public static readonly Color Ink = new Color(0.2f, 0.15f, 0.14f);

        public static ChapterTheme For(int chapter)
        {
            var t = new ChapterTheme { ink = Ink, sun = new Color(1f, 0.97f, 0.86f), cloud = Color.white };
            switch (chapter)
            {
                case 2:
                    t.skyTop = C(0.16f, 0.37f, 0.78f); t.skyBottom = C(0.56f, 0.76f, 0.95f);
                    t.far = C(0.8f, 0.74f, 0.72f); t.mid = C(0.9f, 0.72f, 0.6f); t.near = C(0.78f, 0.52f, 0.45f);
                    t.groundFill = C(0.58f, 0.53f, 0.5f); t.groundEdge = C(0.72f, 0.67f, 0.62f);
                    t.obstacle = C(0.8f, 0.68f, 0.6f); t.platform = C(0.72f, 0.6f, 0.52f);
                    t.edge = EdgeStyle.Cobbles; t.scenery = SceneryStyle.Market;
                    // Market: a bright late morning, the sun high.
                    t.mood = MakeMood(C(1f, 0.979f, 0.962f), C(0.234f, 0.421f, 0.67f), C(0.306f, 0.537f, 0.733f), C(1f, 0.97f, 0.92f),
                        C(0.56f, 0.565f, 0.64f), C(0.52f, 0.49f, 0.5f), C(0.34f, 0.54f, 0.75f),
                        new Vector3(0.4f, 0.85f, -0.35f), new Vector3(0.35f, 0.9f, 1f), 50f, 700f, 0.45f);
                    break;
                case 3:
                    t.skyTop = C(0.13f, 0.35f, 0.78f); t.skyBottom = C(0.48f, 0.74f, 0.96f);
                    t.far = C(0.34f, 0.64f, 0.86f); t.mid = C(0.98f, 0.86f, 0.62f); t.near = C(0.82f, 0.78f, 0.5f);
                    t.groundFill = C(0.9f, 0.79f, 0.58f); t.groundEdge = C(0.97f, 0.9f, 0.72f);
                    t.obstacle = C(0.86f, 0.72f, 0.52f); t.platform = C(0.72f, 0.56f, 0.4f);
                    t.edge = EdgeStyle.Sand; t.scenery = SceneryStyle.Beach;
                    // Beach: a brilliant midday, the deepest sky over a soft turquoise sea, warm bounce off the sand.
                    t.mood = MakeMood(C(1f, 0.979f, 0.967f), C(0.22f, 0.412f, 0.676f), C(0.295f, 0.537f, 0.745f), C(1f, 0.97f, 0.92f),
                        C(0.57f, 0.57f, 0.64f), C(0.6f, 0.55f, 0.52f), C(0.34f, 0.55f, 0.76f),
                        new Vector3(0.5f, 0.75f, -0.45f), new Vector3(-0.3f, 0.95f, 1f), 55f, 760f, 0.42f);
                    break;
                case 4:
                    t.skyTop = C(0.22f, 0.4f, 0.74f); t.skyBottom = C(0.66f, 0.78f, 0.92f);
                    t.far = C(0.62f, 0.63f, 0.73f); t.mid = C(0.52f, 0.52f, 0.62f); t.near = C(0.68f, 0.6f, 0.45f);
                    t.groundFill = C(0.5f, 0.5f, 0.54f); t.groundEdge = C(0.68f, 0.68f, 0.7f);
                    t.obstacle = C(0.7f, 0.66f, 0.62f); t.platform = C(0.95f, 0.72f, 0.3f);
                    t.edge = EdgeStyle.Concrete; t.scenery = SceneryStyle.City;
                    // Underpass and building site: a clear day, the sky a little paler over the city.
                    t.mood = MakeMood(C(1f, 0.979f, 0.962f), C(0.25f, 0.432f, 0.666f), C(0.33f, 0.552f, 0.73f), C(1f, 0.97f, 0.92f),
                        C(0.56f, 0.565f, 0.64f), C(0.5f, 0.49f, 0.5f), C(0.36f, 0.54f, 0.72f),
                        new Vector3(0.5f, 0.75f, -0.4f), new Vector3(0.4f, 0.9f, 1f), 45f, 640f, 0.5f);
                    break;
                case 5:
                    t.skyTop = C(0.15f, 0.38f, 0.8f); t.skyBottom = C(0.6f, 0.8f, 0.95f);
                    t.far = C(0.55f, 0.7f, 0.52f); t.mid = C(0.42f, 0.62f, 0.4f); t.near = C(0.36f, 0.56f, 0.34f);
                    t.groundFill = C(0.66f, 0.55f, 0.42f); t.groundEdge = C(0.46f, 0.72f, 0.38f);
                    t.obstacle = C(0.78f, 0.66f, 0.55f); t.platform = C(0.72f, 0.5f, 0.38f);
                    t.edge = EdgeStyle.ParkPath; t.scenery = SceneryStyle.Park;
                    // Park and school: a clear summer afternoon, the sun a touch warmer, green bounce off the lawns.
                    t.mood = MakeMood(C(1f, 0.969f, 0.942f), C(0.234f, 0.421f, 0.67f), C(0.306f, 0.537f, 0.733f), C(1f, 0.96f, 0.9f),
                        C(0.55f, 0.57f, 0.62f), C(0.46f, 0.5f, 0.44f), C(0.34f, 0.54f, 0.74f),
                        new Vector3(0.55f, 0.7f, -0.45f), new Vector3(-0.4f, 0.9f, 1f), 50f, 700f, 0.45f);
                    break;
                default:
                    t.skyTop = C(0.15f, 0.36f, 0.78f); t.skyBottom = C(0.52f, 0.74f, 0.95f);
                    t.far = C(0.7f, 0.82f, 0.74f); t.mid = C(0.95f, 0.82f, 0.7f); t.near = C(0.44f, 0.64f, 0.4f);
                    t.groundFill = C(0.52f, 0.52f, 0.56f); t.groundEdge = C(0.88f, 0.88f, 0.86f);
                    t.obstacle = C(0.8f, 0.7f, 0.62f); t.platform = C(0.68f, 0.56f, 0.46f);
                    t.edge = EdgeStyle.Road; t.scenery = SceneryStyle.Houses;
                    // Home street: a fresh, clear morning.
                    t.mood = MakeMood(C(1f, 0.979f, 0.962f), C(0.234f, 0.421f, 0.67f), C(0.306f, 0.537f, 0.733f), C(1f, 0.97f, 0.92f),
                        C(0.56f, 0.565f, 0.64f), C(0.5f, 0.48f, 0.5f), C(0.34f, 0.54f, 0.75f),
                        new Vector3(0.45f, 0.78f, -0.45f), new Vector3(-0.4f, 0.9f, 1f), 50f, 700f, 0.45f);
                    break;
            }
            return t;
        }

        static Color C(float r, float g, float b) { return new Color(r, g, b); }
    }
}
