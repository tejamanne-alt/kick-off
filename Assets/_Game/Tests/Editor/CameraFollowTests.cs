using DribbleToSchool.CameraRig;
using DribbleToSchool.UI;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The camera stays on the kid (CameraFollow2D): it leans only a little toward a ball close by, not at all toward one kicked
    /// far away, and never leaves the kid near the side of the screen; a ball off the side is shown by the HUD (UI/BallMarker).
    /// </summary>
    public class CameraFollowTests
    {
        const float Weight = 0.3f, Range = 6f, MaxAcross = 1.2f, MaxUp = 0.5f;

        [Test]
        public void TheViewLeansALittleTowardABallCloseBy()
        {
            Vector2 lean = CameraFollow2D.BallLean(new Vector2(2f, 0f), Weight, Range, MaxAcross, MaxUp);
            Assert.AreEqual(0.6f, lean.x, 1e-4f, "within half the range: the full weight");
            Assert.AreEqual(0f, lean.y, 1e-4f);
            lean = CameraFollow2D.BallLean(new Vector2(4f, 0f), Weight, Range, MaxAcross, MaxUp);
            Assert.AreEqual(4f * Weight * (2f / 3f), lean.x, 1e-4f, "fading between half the range and the range");
            lean = CameraFollow2D.BallLean(new Vector2(-2f, 2f), Weight, Range, MaxAcross, MaxUp);
            Assert.AreEqual(-0.6f, lean.x, 1e-4f, "back as well as ahead");
            Assert.AreEqual(0.5f, lean.y, 1e-4f, "up only so far");
        }

        [Test]
        public void ABallKickedFarAwayLeavesTheViewOnTheKid()
        {
            foreach (var offset in new[] { new Vector2(20f, 1f), new Vector2(-15f, 0f), new Vector2(6f, 0f), new Vector2(0.5f, 9f) })
            {
                Vector2 lean = CameraFollow2D.BallLean(offset, Weight, Range, MaxAcross, MaxUp);
                Assert.AreEqual(0f, lean.magnitude, 1e-4f, "a ball " + offset + " away");
            }
            for (float d = 0f; d < 40f; d += 0.5f)
            {
                Vector2 lean = CameraFollow2D.BallLean(new Vector2(d, d * 0.3f), Weight, Range, MaxAcross, MaxUp);
                Assert.LessOrEqual(Mathf.Abs(lean.x), MaxAcross + 1e-4f);
                Assert.LessOrEqual(Mathf.Abs(lean.y), MaxUp + 1e-4f);
            }
        }

        [Test]
        public void TheKidNeverStandsNearTheSideOfTheScreen()
        {
            const float halfWidth = 7.8f, margin = 0.15f;
            foreach (float centre in new[] { -30f, -4f, 0f, 3f, 30f })
            {
                float c = CameraFollow2D.KeepInView(centre, 0f, halfWidth, margin);
                float kidScreenX = 0.5f + (0f - c) / (2f * halfWidth);
                Assert.GreaterOrEqual(kidScreenX, margin - 1e-4f, "centre " + centre);
                Assert.LessOrEqual(kidScreenX, 1f - margin + 1e-4f, "centre " + centre);
            }
            Assert.AreEqual(1.872f, CameraFollow2D.KeepInView(1.872f, 0f, halfWidth, margin), 1e-4f, "the usual framing is left alone");
        }

        [Test]
        public void TheMarkerShowsABallOffEitherSide()
        {
            Assert.AreEqual(0, BallMarker.Side(0.5f, 10f));
            Assert.AreEqual(0, BallMarker.Side(1.01f, 10f), "just at the edge: still on the screen");
            Assert.AreEqual(1, BallMarker.Side(1.3f, 10f));
            Assert.AreEqual(-1, BallMarker.Side(-0.4f, 10f));
            Assert.AreEqual(0, BallMarker.Side(1.3f, -1f), "behind the camera: no marker");
            Assert.Less(BallMarker.LowY, BallMarker.HighY);
        }
    }
}
