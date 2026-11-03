#if UNITY_INCLUDE_TESTS
using DribbleToSchool.CameraRig;
using DribbleToSchool.InputHandling;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The on-screen touch controls: the left thumb has one walk stick (push sideways to walk, pull down to slide, the
    /// ring comes to the thumb anywhere in its area), the right thumb jumps and kicks (two buttons of one size on one
    /// baseline). None crowds another, they stay on the screen, leave the aim drag room and swap sides for left-handed
    /// play, on every landscape shape from 4:3 tablets to 21:9 phones; the kid is stood clear of the stick's area so no
    /// thumb covers them; and the stick reads the way the tour says it does.
    /// </summary>
    public class ControlLayoutTests
    {
        // (width, height) of the screens a phone or tablet may have in landscape.
        static readonly int[][] Screens =
        {
            new[] { 1024, 768 },     // 4:3 tablet
            new[] { 1280, 800 },     // 16:10
            new[] { 1920, 1080 },    // 16:9
            new[] { 2340, 1080 },    // 19.5:9
            new[] { 2532, 1170 },    // iPhone
            new[] { 2520, 1080 },    // 21:9
        };

        GameObject go;
        GameInput input;

        [SetUp]
        public void MakeInput()
        {
            go = new GameObject("InputUnderTest");
            input = go.AddComponent<GameInput>();
        }

        [TearDown]
        public void DestroyInput()
        {
            Object.DestroyImmediate(go);
        }

        static Rect Full(int w, int h) { return new Rect(0f, 0f, w, h); }

        static float Gap(GameInput.Round a, GameInput.Round b)
        {
            return Vector2.Distance(a.center, b.center) - a.radius - b.radius;
        }

        /// <summary>How far a button's edge is from the rect (negative if it reaches inside).</summary>
        static float Clear(GameInput.Round b, Rect r)
        {
            float dx = Mathf.Max(r.xMin - b.center.x, 0f, b.center.x - r.xMax);
            float dy = Mathf.Max(r.yMin - b.center.y, 0f, b.center.y - r.yMax);
            return Mathf.Sqrt(dx * dx + dy * dy) - b.radius;
        }

        delegate void Check(GameInput.ControlLayout layout, int w, int h, bool leftHanded, string where);

        /// <summary>Every screen shape, both hands.</summary>
        void ForEveryLayout(Check check)
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var layout = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                    check(layout, s[0], s[1], left, (left ? "left-handed " : "") + s[0] + "x" + s[1]);
                }
        }

        static bool OnScreen(GameInput.Round b, int w, int h)
        {
            return b.center.x - b.radius >= -0.5f && b.center.x + b.radius <= w + 0.5f && b.center.y - b.radius >= -0.5f && b.center.y + b.radius <= h + 0.5f;
        }

        [Test]
        public void JumpAndKickDoNotCrowdOrTouch()
        {
            ForEveryLayout((l, w, h, left, where) => Assert.GreaterOrEqual(Gap(l.jump, l.kick), 0.02f * h, where));
        }

        [Test]
        public void TheStickAreaKeepsClearOfJumpAndKick()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                Assert.GreaterOrEqual(Clear(l.jump, l.stickArea), 0.05f * h, where + ": jump");
                Assert.GreaterOrEqual(Clear(l.kick, l.stickArea), 0.05f * h, where + ": kick");
            });
        }

        [Test]
        public void EveryControlIsFullyOnScreen()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                Assert.IsTrue(OnScreen(l.jump, w, h), where + ": jump");
                Assert.IsTrue(OnScreen(l.kick, w, h), where + ": kick");
                Assert.IsTrue(OnScreen(l.stick, w, h), where + ": the stick at rest");
                Assert.IsTrue(l.stickArea.xMin >= -0.5f && l.stickArea.xMax <= w + 0.5f && l.stickArea.yMin >= -0.5f && l.stickArea.yMax <= h + 0.5f, where + ": the stick's area");
            });
        }

        [Test]
        public void JumpAndKickAreOneSizeAndTheControlsAreBigEnoughForAThumb()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                Assert.AreEqual(l.jump.radius, l.kick.radius, 0.5f, where + ": jump and kick");
                // 0.1 of the screen's height across at least: about 9 mm on a phone.
                Assert.GreaterOrEqual(l.jump.radius * 2f, 0.1f * h, where + ": jump");
                Assert.GreaterOrEqual(l.stick.radius * 2f, 0.2f * h, where + ": the stick's ring");
            });
        }

        [Test]
        public void JumpIsInTheCornerAndKickBesideItOnTheSameBaseline()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                float jumpIn = left ? l.jump.center.x : w - l.jump.center.x;
                float kickIn = left ? l.kick.center.x : w - l.kick.center.x;
                Assert.Less(jumpIn, kickIn, where + ": jump is nearer the edge");
                Assert.AreEqual(l.jump.center.y, l.kick.center.y, 1f, where + ": one baseline");
            });
        }

        [Test]
        public void KickHasRoomToAimAboveAndToBothSides()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                // A full-power drag is about a quarter of the screen's height.
                float room = 0.22f * h;
                Assert.GreaterOrEqual(l.kick.center.x, room, where + ": room to the left");
                Assert.GreaterOrEqual(w - l.kick.center.x, room, where + ": room to the right");
                Assert.GreaterOrEqual(h - l.kick.center.y, room, where + ": room above");
            });
        }

        [Test]
        public void TheStickIsOnTheLeftAndTheButtonsOnTheRightUnlessLeftHanded()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                bool stickLeft = l.stick.center.x < w * 0.5f;
                Assert.AreEqual(!left, stickLeft, where + ": the stick's side");
                Assert.AreEqual(left, l.jump.center.x < w * 0.5f, where + ": jump's side");
                Assert.AreEqual(left, l.kick.center.x < w * 0.5f, where + ": kick's side");
                // The area runs from the stick's own screen edge.
                Assert.AreEqual(left ? w : 0f, left ? l.stickArea.xMax : l.stickArea.xMin, 0.5f, where + ": the area starts at the edge");
            });
        }

        [Test]
        public void LeftHandedIsAMirrorImage()
        {
            foreach (var s in Screens)
            {
                var right = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), false);
                var left = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), true);
                string where = s[0] + "x" + s[1];
                Assert.AreEqual(s[0] - right.jump.center.x, left.jump.center.x, 0.5f, where + ": jump");
                Assert.AreEqual(s[0] - right.stick.center.x, left.stick.center.x, 0.5f, where + ": the stick");
                Assert.AreEqual(right.stickArea.width, left.stickArea.width, 0.5f, where + ": the stick's area");
            }
        }

        [Test]
        public void TheSticksAreaStaysOutOfTheTopOfTheScreen()
        {
            // The level's card and the pause button live up there.
            ForEveryLayout((l, w, h, left, where) => Assert.LessOrEqual(l.stickArea.yMax, 0.75f * h, where));
        }

        [Test]
        public void TheStickComesToTheThumbAndStaysInsideItsArea()
        {
            var l = input.LayoutOn(2532, 1170, Full(2532, 1170), false);
            float r = l.stick.radius;
            // A thumb in the middle of the area: the ring is right under it.
            Vector2 mid = new Vector2(l.stick.center.x + 20f, l.stick.center.y + 30f);
            Assert.AreEqual(mid, GameInput.StickCenterFor(mid, l.stick, l.stickArea), "under the thumb");
            // A thumb near the screen's edge or the bottom: the ring stays whole on the screen.
            Vector2 corner = GameInput.StickCenterFor(new Vector2(5f, 5f), l.stick, l.stickArea);
            Assert.GreaterOrEqual(corner.x - r, l.stickArea.xMin - 0.01f, "off the left edge");
            Assert.Greater(corner.y - r, 0f, "off the bottom edge");
            // A thumb past the area's inner edge or top: the ring stays inside the area.
            Vector2 far = GameInput.StickCenterFor(new Vector2(l.stickArea.xMax + 400f, l.stickArea.yMax + 400f), l.stick, l.stickArea);
            Assert.LessOrEqual(far.x + r, l.stickArea.xMax + 0.01f, "the inner edge");
            Assert.LessOrEqual(far.y + r, l.stickArea.yMax + 0.01f, "the top");
        }

        [Test]
        public void TheKidIsStoodClearOfTheStickAndEveryButtonOnTheLeft()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                float safe = GameInput.KidSafeScreenXOn(l, w, h, 0.14f);
                if (!left) Assert.GreaterOrEqual(safe * w, l.stickArea.xMax + 0.139f * h, where + ": clear of anywhere the stick can be");
                foreach (var b in new[] { l.jump, l.kick })
                {
                    if (b.center.x >= w * 0.5f) continue;
                    Assert.GreaterOrEqual(safe * w, b.center.x + b.radius + 0.139f * h, where + ": clear of a button on the left");
                }
                // Not so far over that the view ahead is lost: a quarter of the screen to just past the middle.
                Assert.GreaterOrEqual(safe, 0.25f, where + ": not hard against the left edge");
                Assert.LessOrEqual(safe, 0.56f, where + ": not past the middle");
            });
        }

        [Test]
        public void OnPhonesTheKidStandsAboutAThirdOfTheWayIn()
        {
            // 16:9 and wider: the controls take up little of the width, so the kid keeps a good view ahead.
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    if (s[0] / (float)s[1] < 1.7f) continue;
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                    float safe = GameInput.KidSafeScreenXOn(l, s[0], s[1], 0.14f);
                    Assert.LessOrEqual(safe, 0.42f, (left ? "left-handed " : "") + s[0] + "x" + s[1]);
                }
        }

        [Test]
        public void TheCameraLeadsAKidWhoStandsLeftOfCentreByTheRightDistance()
        {
            Assert.AreEqual(0f, CameraFollow2D.LeadFor(0.5f, 8f), 0.0001f, "the middle needs no lead");
            Assert.AreEqual(4f, CameraFollow2D.LeadFor(0.25f, 8f), 0.0001f, "a quarter in: a quarter of the view's width ahead");
            // 0.38 of the way in on a view 15.6 m wide: the view's centre is 1.87 m ahead.
            Assert.AreEqual(1.872f, CameraFollow2D.LeadFor(0.38f, 7.8f), 0.001f);
            // The nearer the middle, the smaller the lead.
            Assert.Less(CameraFollow2D.LeadFor(0.42f, 7.8f), CameraFollow2D.LeadFor(0.38f, 7.8f));
        }

        // ---------------------------------------------------------------- reading the stick

        /// <summary>One reading on a ring of radius 100 with the game's thresholds.</summary>
        void Read(float x, float y, ref bool down, out float move, out bool slide)
        {
            GameInput.ReadStick(new Vector2(x, y), 100f, input.stickDeadZone, input.stickSlideDown, input.stickSlideRelease, ref down, out move, out slide);
        }

        [Test]
        public void ASmallPushDoesNothingAndAPushPastTheDeadZoneWalks()
        {
            bool down = false; float move; bool slide;
            Read(10f, 5f, ref down, out move, out slide);
            Assert.AreEqual(0f, move, "a resting thumb");
            Read(60f, 0f, ref down, out move, out slide);
            Assert.AreEqual(1f, move, "pushed right: forward");
            Read(-60f, 10f, ref down, out move, out slide);
            Assert.AreEqual(-1f, move, "pushed left: back");
            Assert.IsFalse(slide);
        }

        [Test]
        public void PullingDownSlidesOnceAndAgainOnlyAfterComingBackUp()
        {
            bool down = false; float move; bool slide;
            Read(0f, -70f, ref down, out move, out slide);
            Assert.IsTrue(slide, "pulled down: slide");
            Read(0f, -90f, ref down, out move, out slide);
            Assert.IsFalse(slide, "held down: no second slide");
            Assert.IsTrue(down, "still held down");
            Read(0f, -40f, ref down, out move, out slide);
            Assert.IsFalse(slide, "eased up a little, still below the release line");
            Read(0f, -10f, ref down, out move, out slide);
            Assert.IsFalse(down, "back up");
            Read(0f, -70f, ref down, out move, out slide);
            Assert.IsTrue(slide, "pulled down again: another slide");
        }

        [Test]
        public void ThePullsSideSaysWhichWayTheKidSlides()
        {
            bool down = false; float move; bool slide;
            Read(40f, -70f, ref down, out move, out slide);
            Assert.IsTrue(slide);
            Assert.AreEqual(1f, move, "down and right: slide forward");
            down = false;
            Read(-40f, -70f, ref down, out move, out slide);
            Assert.IsTrue(slide);
            Assert.AreEqual(-1f, move, "down and left: slide back");
            down = false;
            Read(5f, -80f, ref down, out move, out slide);
            Assert.IsTrue(slide);
            Assert.AreEqual(0f, move, "straight down: the way the kid is already going");
        }

        [Test]
        public void ASidewaysPushThatDipsALittleIsNotASlide()
        {
            bool down = false; float move; bool slide;
            Read(95f, -55f, ref down, out move, out slide);
            Assert.IsFalse(slide, "mostly sideways: keep walking");
            Assert.AreEqual(1f, move);
        }

        [Test]
        public void ANotchPushesTheControlsInward()
        {
            var flat = input.LayoutOn(2532, 1170, Full(2532, 1170), false);
            var notched = input.LayoutOn(2532, 1170, new Rect(141f, 0f, 2250f, 1170f), false);
            Assert.Less(notched.jump.center.x, flat.jump.center.x, "jump moves in from the right edge");
            Assert.Greater(notched.stick.center.x, flat.stick.center.x, "the stick moves in from the left edge");
        }
    }
}
#endif
