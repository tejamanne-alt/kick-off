using UnityEngine;

namespace DribbleToSchool.Art
{
    public enum EdgeStyle { Grass, Cobbles, Sand, Concrete, ParkPath, Road }
    public enum SceneryStyle { Houses, Market, Beach, City, Park }

    /// <summary>
    /// Colours and scenery for one chapter: clear anime daylight throughout (docs/ART_DIRECTION.md):
    /// a deep blue sky paling toward the horizon, a near-white sun, cool crisp shade and only a
    /// little blue distance haze, so colours read true and the characters stand out.
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

        /// <summary>Light and atmosphere for one chapter: a clear sun against cool sky-tinted shade, a
        /// pale blue horizon with a little haze, and the camera's grade.</summary>
        public struct Mood
        {
            public Color sun, ambientSky, ambientGround, zenith, horizon, glow, haze, lift, gain;
            public Vector3 sunDirection, skySunDirection;
            public float hazeStart, hazeEnd, hazeStrength;
        }

        static Mood MakeMood(Color sun, Color zenith, Color horizon, Color glow, Color shade, Color bounce, Color haze, Color lift, Color gain,
            Vector3 sunDir, Vector3 skySunDir, float hazeStart = 40f, float hazeEnd = 700f, float hazeStrength = 0.6f)
        {
            return new Mood
            {
                sun = sun, zenith = zenith, horizon = horizon, glow = glow, ambientSky = shade, ambientGround = bounce,
                haze = haze, lift = lift, gain = gain, sunDirection = sunDir, skySunDirection = skySunDir,
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
                    t.mood = MakeMood(C(1f, 0.97f, 0.92f), C(0.2f, 0.43f, 0.72f), C(0.63f, 0.79f, 0.92f), C(1f, 0.97f, 0.9f),
                        C(0.52f, 0.56f, 0.66f), C(0.62f, 0.6f, 0.58f), C(0.68f, 0.78f, 0.88f), C(0f, 0f, 0.008f), C(1f, 0.99f, 0.97f),
                        new Vector3(0.4f, 0.85f, -0.35f), new Vector3(0.35f, 0.9f, 1f), 40f, 700f, 0.58f);
                    break;
                case 3:
                    t.skyTop = C(0.13f, 0.35f, 0.78f); t.skyBottom = C(0.48f, 0.74f, 0.96f);
                    t.far = C(0.34f, 0.64f, 0.86f); t.mid = C(0.98f, 0.86f, 0.62f); t.near = C(0.82f, 0.78f, 0.5f);
                    t.groundFill = C(0.9f, 0.79f, 0.58f); t.groundEdge = C(0.97f, 0.9f, 0.72f);
                    t.obstacle = C(0.86f, 0.72f, 0.52f); t.platform = C(0.72f, 0.56f, 0.4f);
                    t.edge = EdgeStyle.Sand; t.scenery = SceneryStyle.Beach;
                    // Beach: a brilliant midday, the deepest sky over a clear turquoise sea, warm bounce off the sand.
                    t.mood = MakeMood(C(1f, 0.98f, 0.94f), C(0.17f, 0.43f, 0.74f), C(0.58f, 0.79f, 0.93f), C(1f, 0.97f, 0.9f),
                        C(0.54f, 0.58f, 0.68f), C(0.72f, 0.66f, 0.6f), C(0.66f, 0.8f, 0.9f), C(0f, 0f, 0.008f), C(1f, 0.99f, 0.97f),
                        new Vector3(0.5f, 0.75f, -0.45f), new Vector3(-0.3f, 0.95f, 1f), 45f, 760f, 0.55f);
                    break;
                case 4:
                    t.skyTop = C(0.22f, 0.4f, 0.74f); t.skyBottom = C(0.66f, 0.78f, 0.92f);
                    t.far = C(0.62f, 0.63f, 0.73f); t.mid = C(0.52f, 0.52f, 0.62f); t.near = C(0.68f, 0.6f, 0.45f);
                    t.groundFill = C(0.5f, 0.5f, 0.54f); t.groundEdge = C(0.68f, 0.68f, 0.7f);
                    t.obstacle = C(0.7f, 0.66f, 0.62f); t.platform = C(0.95f, 0.72f, 0.3f);
                    t.edge = EdgeStyle.Concrete; t.scenery = SceneryStyle.City;
                    // Underpass and building site: a clear day, the sky a little paler over the city.
                    t.mood = MakeMood(C(1f, 0.97f, 0.93f), C(0.22f, 0.44f, 0.72f), C(0.66f, 0.8f, 0.9f), C(1f, 0.97f, 0.91f),
                        C(0.52f, 0.55f, 0.64f), C(0.6f, 0.59f, 0.58f), C(0.7f, 0.77f, 0.85f), C(0f, 0f, 0.008f), C(1f, 0.99f, 0.97f),
                        new Vector3(0.5f, 0.75f, -0.4f), new Vector3(0.4f, 0.9f, 1f), 38f, 640f, 0.62f);
                    break;
                case 5:
                    t.skyTop = C(0.15f, 0.38f, 0.8f); t.skyBottom = C(0.6f, 0.8f, 0.95f);
                    t.far = C(0.55f, 0.7f, 0.52f); t.mid = C(0.42f, 0.62f, 0.4f); t.near = C(0.36f, 0.56f, 0.34f);
                    t.groundFill = C(0.66f, 0.55f, 0.42f); t.groundEdge = C(0.46f, 0.72f, 0.38f);
                    t.obstacle = C(0.78f, 0.66f, 0.55f); t.platform = C(0.72f, 0.5f, 0.38f);
                    t.edge = EdgeStyle.ParkPath; t.scenery = SceneryStyle.Park;
                    // Park and school: a clear summer afternoon, the sun a touch warmer, green bounce off the lawns.
                    t.mood = MakeMood(C(1f, 0.96f, 0.9f), C(0.2f, 0.43f, 0.72f), C(0.64f, 0.8f, 0.92f), C(1f, 0.96f, 0.88f),
                        C(0.52f, 0.57f, 0.64f), C(0.56f, 0.6f, 0.52f), C(0.68f, 0.78f, 0.86f), C(0f, 0f, 0.008f), C(1f, 0.99f, 0.97f),
                        new Vector3(0.55f, 0.7f, -0.45f), new Vector3(-0.4f, 0.9f, 1f), 40f, 700f, 0.58f);
                    break;
                default:
                    t.skyTop = C(0.15f, 0.36f, 0.78f); t.skyBottom = C(0.52f, 0.74f, 0.95f);
                    t.far = C(0.7f, 0.82f, 0.74f); t.mid = C(0.95f, 0.82f, 0.7f); t.near = C(0.44f, 0.64f, 0.4f);
                    t.groundFill = C(0.52f, 0.52f, 0.56f); t.groundEdge = C(0.88f, 0.88f, 0.86f);
                    t.obstacle = C(0.8f, 0.7f, 0.62f); t.platform = C(0.68f, 0.56f, 0.46f);
                    t.edge = EdgeStyle.Road; t.scenery = SceneryStyle.Houses;
                    // Home street: a fresh, clear morning.
                    t.mood = MakeMood(C(1f, 0.97f, 0.92f), C(0.2f, 0.43f, 0.72f), C(0.62f, 0.79f, 0.92f), C(1f, 0.97f, 0.9f),
                        C(0.52f, 0.56f, 0.66f), C(0.62f, 0.6f, 0.58f), C(0.68f, 0.78f, 0.88f), C(0f, 0f, 0.008f), C(1f, 0.99f, 0.97f),
                        new Vector3(0.45f, 0.78f, -0.45f), new Vector3(-0.4f, 0.9f, 1f), 40f, 700f, 0.6f);
                    break;
            }
            return t;
        }

        static Color C(float r, float g, float b) { return new Color(r, g, b); }
    }
}
