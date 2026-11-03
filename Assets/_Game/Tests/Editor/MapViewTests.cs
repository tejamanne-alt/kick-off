#if UNITY_INCLUDE_TESTS
using DribbleToSchool.UI.Kit;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The town map's pan and zoom (UI/Kit/MapViewMath, used by UIMapView): the fit, the mapping between the picture and the
    /// view, zooming about a point that stays put, the picture never sliding off the view, and the things drawn on the picture
    /// growing on screen more slowly than the picture as it zooms in.
    /// </summary>
    public class MapViewTests
    {
        static readonly Vector2 Design = new Vector2(3200f, 1800f);

        [Test]
        public void TheFitIsTheLargestScaleAtWhichThePartFitsBothWays()
        {
            var part = new Rect(447f, 277f, 2355f, 1231f);
            float s = MapViewMath.FitScale(new Vector2(1784f, 710f), part);
            Assert.AreEqual(Mathf.Min(1784f / 2355f, 710f / 1231f), s, 1e-5f);
            Assert.LessOrEqual(part.width * s, 1784f + 1e-3f);
            Assert.LessOrEqual(part.height * s, 710f + 1e-3f);
            Assert.AreEqual(1f, MapViewMath.FitScale(Vector2.zero, part), "no room yet: 1");

            // A little more, if that makes the picture fill the screen (16:9: 0.6 fills 1920 x 1080 with 3200 x 1800)...
            var picture = new Rect(0f, 0f, 3200f, 1800f);
            float filled = MapViewMath.FitScale(new Vector2(1784f, 710f), part, new Vector2(1920f, 1080f), picture, 0.05f);
            Assert.AreEqual(0.6f, filled, 1e-4f);
            // ...but never more than the slack allows (a very wide screen keeps the fit and shows the mat at its sides).
            float wide = MapViewMath.FitScale(new Vector2(2384f, 710f), part, new Vector2(2520f, 1080f), picture, 0.05f);
            Assert.AreEqual(MapViewMath.FitScale(new Vector2(2384f, 710f), part) * 1.05f, wide, 1e-4f);
        }

        [Test]
        public void ViewAndPicturePointsMapBothWays()
        {
            float scale = 0.6f;
            var position = new Vector2(35f, -20f);
            foreach (var p in new[] { new Vector2(0f, 0f), new Vector2(1600f, 900f), new Vector2(820f, 1045f), new Vector2(3200f, 1800f) })
            {
                Vector2 v = MapViewMath.ToView(Design, p, scale, position);
                Vector2 back = MapViewMath.ToDesign(Design, v, scale, position);
                Assert.AreEqual(p.x, back.x, 1e-3f);
                Assert.AreEqual(p.y, back.y, 1e-3f);
            }
            // The picture's middle is the block's position; its top (y = 0 in the picture) is up in the view.
            Assert.AreEqual(position, MapViewMath.ToView(Design, Design * 0.5f, scale, position));
            Assert.Greater(MapViewMath.ToView(Design, new Vector2(1600f, 0f), scale, position).y, position.y);
            // PositionFor puts a picture point where it is asked.
            Vector2 at = MapViewMath.PositionFor(Design, new Vector2(820f, 1045f), new Vector2(-100f, 50f), 0.8f);
            Vector2 seen = MapViewMath.ToView(Design, new Vector2(820f, 1045f), 0.8f, at);
            Assert.AreEqual(-100f, seen.x, 1e-3f);
            Assert.AreEqual(50f, seen.y, 1e-3f);
        }

        [Test]
        public void ZoomingAboutAPointKeepsThatPointStill()
        {
            var position = new Vector2(40f, -30f);
            var pinch = new Vector2(300f, 120f);
            Vector2 under = MapViewMath.ToDesign(Design, pinch, 0.6f, position);
            Vector2 after = MapViewMath.ZoomAbout(position, 0.6f, 1.5f, pinch);
            Vector2 still = MapViewMath.ToView(Design, under, 1.5f, after);
            Assert.AreEqual(pinch.x, still.x, 1e-3f);
            Assert.AreEqual(pinch.y, still.y, 1e-3f);
        }

        [Test]
        public void ThePictureNeverSlidesOffAViewItCovers()
        {
            var cover = new Rect(0f, 0f, 3200f, 1800f);
            var view = new Vector2(1920f, 1080f);
            float scale = 1f;   // the picture is far bigger than the view
            foreach (var wanted in new[] { new Vector2(5000f, 0f), new Vector2(-5000f, 3000f), new Vector2(0f, -4000f) })
            {
                Vector2 p = MapViewMath.ClampPosition(Design, cover, view, scale, wanted, Vector2.zero);
                Vector2 lo = MapViewMath.ToView(Design, new Vector2(0f, 1800f), scale, p);
                Vector2 hi = MapViewMath.ToView(Design, new Vector2(3200f, 0f), scale, p);
                Assert.LessOrEqual(lo.x, -view.x * 0.5f + 1e-3f, "left edge inside the view");
                Assert.GreaterOrEqual(hi.x, view.x * 0.5f - 1e-3f, "right edge inside the view");
                Assert.LessOrEqual(lo.y, -view.y * 0.5f + 1e-3f, "bottom edge inside the view");
                Assert.GreaterOrEqual(hi.y, view.y * 0.5f - 1e-3f, "top edge inside the view");
            }
            // Smaller than the view along x (a very wide screen at the fit): it stays where it is put.
            Vector2 small = MapViewMath.ClampPosition(Design, cover, new Vector2(2520f, 1080f), 0.58f, new Vector2(400f, 0f), new Vector2(-12f, 3f));
            Assert.AreEqual(-12f, small.x, 1e-4f);
        }

        [Test]
        public void ThingsOnThePictureGrowMoreSlowlyThanItAsItZoomsIn()
        {
            Assert.AreEqual(1f, MapViewMath.ItemScale(1f), 1e-5f, "fitted: as drawn");
            Assert.AreEqual(1f, MapViewMath.ItemScale(0.8f), 1e-5f, "zoomed out: they shrink with the picture");
            float last = 1f, lastOnScreen = 1f;
            for (float zoom = 1.25f; zoom <= 3.01f; zoom += 0.25f)
            {
                float s = MapViewMath.ItemScale(zoom);
                float onScreen = s * zoom;
                Assert.Less(s, last, "smaller against the picture the more it zooms (more room between them)");
                Assert.Greater(onScreen, lastOnScreen, "but still bigger on screen (easier to read and tap)");
                Assert.Less(onScreen, zoom, "and never as fast as the picture");
                last = s;
                lastOnScreen = onScreen;
            }
        }
    }
}
#endif
