using UnityEngine;

namespace DribbleToSchool.Art
{
    public enum EdgeStyle { Grass, Cobbles, Sand, Concrete, ParkPath }
    public enum SceneryStyle { Houses, Market, Beach, City, Park }

    /// <summary>
    /// Colours and scenery for one chapter. The palette warms through the
    /// school morning: cool dawn on Home Street to golden light at the school.
    /// </summary>
    public struct ChapterTheme
    {
        public Color skyTop, skyBottom, sun, cloud;
        public Color far, mid, near;
        public Color groundFill, groundEdge, obstacle, platform, ink;
        public EdgeStyle edge;
        public SceneryStyle scenery;

        public static readonly Color Ink = new Color(0.2f, 0.15f, 0.14f);

        public static ChapterTheme For(int chapter)
        {
            var t = new ChapterTheme { ink = Ink, sun = new Color(1f, 0.93f, 0.65f), cloud = new Color(1f, 1f, 1f, 0.92f) };
            switch (chapter)
            {
                case 2:
                    t.skyTop = C(0.56f, 0.77f, 0.95f); t.skyBottom = C(1f, 0.91f, 0.78f);
                    t.far = C(0.8f, 0.74f, 0.72f); t.mid = C(0.9f, 0.72f, 0.6f); t.near = C(0.78f, 0.52f, 0.45f);
                    t.groundFill = C(0.58f, 0.53f, 0.5f); t.groundEdge = C(0.72f, 0.67f, 0.62f);
                    t.obstacle = C(0.8f, 0.68f, 0.6f); t.platform = C(0.72f, 0.6f, 0.52f);
                    t.edge = EdgeStyle.Cobbles; t.scenery = SceneryStyle.Market;
                    break;
                case 3:
                    t.skyTop = C(0.42f, 0.74f, 0.96f); t.skyBottom = C(0.96f, 0.95f, 0.86f);
                    t.far = C(0.34f, 0.64f, 0.86f); t.mid = C(0.98f, 0.86f, 0.62f); t.near = C(0.82f, 0.78f, 0.5f);
                    t.groundFill = C(0.9f, 0.79f, 0.58f); t.groundEdge = C(0.97f, 0.9f, 0.72f);
                    t.obstacle = C(0.86f, 0.72f, 0.52f); t.platform = C(0.72f, 0.56f, 0.4f);
                    t.edge = EdgeStyle.Sand; t.scenery = SceneryStyle.Beach;
                    break;
                case 4:
                    t.skyTop = C(0.6f, 0.71f, 0.84f); t.skyBottom = C(0.95f, 0.88f, 0.82f);
                    t.far = C(0.62f, 0.63f, 0.73f); t.mid = C(0.52f, 0.52f, 0.62f); t.near = C(0.68f, 0.6f, 0.45f);
                    t.groundFill = C(0.5f, 0.5f, 0.54f); t.groundEdge = C(0.68f, 0.68f, 0.7f);
                    t.obstacle = C(0.7f, 0.66f, 0.62f); t.platform = C(0.95f, 0.72f, 0.3f);
                    t.edge = EdgeStyle.Concrete; t.scenery = SceneryStyle.City;
                    break;
                case 5:
                    t.skyTop = C(0.55f, 0.72f, 0.93f); t.skyBottom = C(1f, 0.84f, 0.64f);
                    t.sun = C(1f, 0.85f, 0.5f);
                    t.far = C(0.55f, 0.7f, 0.52f); t.mid = C(0.42f, 0.62f, 0.4f); t.near = C(0.36f, 0.56f, 0.34f);
                    t.groundFill = C(0.66f, 0.55f, 0.42f); t.groundEdge = C(0.46f, 0.72f, 0.38f);
                    t.obstacle = C(0.78f, 0.66f, 0.55f); t.platform = C(0.72f, 0.5f, 0.38f);
                    t.edge = EdgeStyle.ParkPath; t.scenery = SceneryStyle.Park;
                    break;
                default:
                    t.skyTop = C(0.62f, 0.8f, 0.95f); t.skyBottom = C(0.99f, 0.9f, 0.82f);
                    t.far = C(0.7f, 0.82f, 0.74f); t.mid = C(0.95f, 0.82f, 0.7f); t.near = C(0.44f, 0.64f, 0.4f);
                    t.groundFill = C(0.6f, 0.48f, 0.38f); t.groundEdge = C(0.5f, 0.76f, 0.4f);
                    t.obstacle = C(0.8f, 0.7f, 0.62f); t.platform = C(0.68f, 0.56f, 0.46f);
                    t.edge = EdgeStyle.Grass; t.scenery = SceneryStyle.Houses;
                    break;
            }
            return t;
        }

        static Color C(float r, float g, float b) { return new Color(r, g, b); }
    }
}
