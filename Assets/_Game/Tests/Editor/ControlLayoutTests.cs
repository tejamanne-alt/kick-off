#if UNITY_INCLUDE_TESTS
using DribbleToSchool.CameraRig;
using DribbleToSchool.InputHandling;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The on-screen touch buttons: the left thumb walks (two arrows) and slides (a button up and to the left of
    /// the forward arrow, or, by a setting, above jump), the right thumb jumps and kicks (two buttons on one
    /// baseline); the three action buttons are one size. None crowds another, they stay on the screen, leave the
    /// aim drag room and keep their order when mirrored for left-handed play, on every landscape shape from 4:3
    /// tablets to 21:9 phones; and the kid is stood clear of the left-hand buttons so no thumb covers them.
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

        delegate void Check(GameInput.ControlLayout layout, int w, int h, bool leftHanded, bool slideWithArrows, string where);

        /// <summary>Every screen shape, both hands, the slide button with the arrows and beside jump and kick.</summary>
        void ForEveryLayout(Check check)
        {
            foreach (bool left in new[] { false, true })
                foreach (bool arrows in new[] { true, false })
                    foreach (var s in Screens)
                    {
                        var layout = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left, arrows);
                        check(layout, s[0], s[1], left, arrows, (left ? "left-handed " : "") + (arrows ? "slide by arrows " : "slide by jump ") + s[0] + "x" + s[1]);
                    }
        }

        /// <summary>How far in from the screen edge the cluster sits on: a right-handed player's action buttons are on the right.</summary>
        static float FromEdge(GameInput.Round b, int w, bool onRight)
        {
            return onRight ? w - b.center.x : b.center.x;
        }

        static GameInput.Round[] All(GameInput.ControlLayout l)
        {
            return new[] { l.jump, l.kick, l.slide, l.walkBack, l.walkForward };
        }

        [Test]
        public void NoTwoButtonsCrowdOrTouch()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                var b = All(l);
                for (int i = 0; i < b.Length; i++)
                    for (int j = i + 1; j < b.Length; j++)
                        Assert.GreaterOrEqual(Gap(b[i], b[j]), 0.035f * h, where + ": buttons " + i + " and " + j);
            });
        }

        [Test]
        public void KickAndSlideAreNeverNeighbours()
        {
            // Turning the kick into a slide (or back) in the heat of it was the old complaint: they stay at least
            // a button's width apart.
            ForEveryLayout((l, w, h, left, arrows, where) =>
                Assert.GreaterOrEqual(Gap(l.kick, l.slide), 0.1f * h, where + ": kick/slide"));
        }

        [Test]
        public void EveryButtonIsFullyOnScreen()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                foreach (var b in All(l))
                {
                    Assert.GreaterOrEqual(b.center.x - b.radius, 0f, where + ": left edge");
                    Assert.LessOrEqual(b.center.x + b.radius, w, where + ": right edge");
                    Assert.GreaterOrEqual(b.center.y - b.radius, 0f, where + ": bottom edge");
                    Assert.LessOrEqual(b.center.y + b.radius, h, where + ": top edge");
                }
            });
        }

        [Test]
        public void AllThreeActionButtonsAreTheSameSize()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                Assert.AreEqual(l.jump.radius, l.slide.radius, 0.01f, where + ": jump vs slide");
                Assert.AreEqual(l.jump.radius, l.kick.radius, 0.01f, where + ": jump vs kick");
            });
        }

        [Test]
        public void ButtonsAreBigEnoughForAThumb()
        {
            // At least 9 mm across on a phone held at about 2.9 inches of screen height: 0.17 of the height.
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                foreach (var b in All(l))
                    Assert.GreaterOrEqual(b.radius * 2f, 0.17f * h, where + ": button diameter");
            });
        }

        [Test]
        public void JumpIsInTheCornerAndKickBesideItOnTheSameBaseline()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                Assert.AreEqual(l.jump.center.y, l.kick.center.y, 0.03f * h, where + ": kick is on jump's baseline");
                Assert.Less(FromEdge(l.jump, w, !left), 0.3f * h, where + ": jump is at the edge");
                Assert.Greater(FromEdge(l.kick, w, !left), FromEdge(l.jump, w, !left) + l.jump.radius + l.kick.radius, where + ": kick is beside jump, not under it");
                Assert.Less(Vector2.Distance(l.kick.center, l.jump.center), 0.36f * h, where + ": kick is within a thumb's reach of jump");
            });
        }

        [Test]
        public void TheSlideButtonIsWithTheWalkingThumbUpAndToTheLeftOfTheForwardArrow()
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left, true);
                    string where = (left ? "left-handed " : "") + s[0] + "x" + s[1];
                    // On the walking side of the screen, like the arrows.
                    bool arrowsOnRight = left;
                    Assert.AreEqual(arrowsOnRight, l.slide.center.x > s[0] * 0.5f, where + ": slide is on the arrows' half");
                    Assert.AreEqual(arrowsOnRight, l.walkForward.center.x > s[0] * 0.5f, where + ": arrows half");
                    Assert.Less(l.slide.center.x, l.walkForward.center.x, where + ": to the left of the forward arrow");
                    Assert.Greater(l.slide.center.y, l.walkForward.center.y + l.walkForward.radius, where + ": above the arrows");
                    Assert.Less(Vector2.Distance(l.slide.center, l.walkForward.center), 0.34f * s[1], where + ": within a thumb's reach of the forward arrow");
                    Assert.Less(Vector2.Distance(l.slide.center, l.walkBack.center), 0.36f * s[1], where + ": and of the back arrow");
                }
        }

        [Test]
        public void TheSlideButtonStacksAboveJumpWhenSettingsKeepItThere()
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left, false);
                    string where = (left ? "left-handed " : "") + s[0] + "x" + s[1];
                    Assert.AreEqual(l.jump.center.x, l.slide.center.x, 0.01f, where + ": one column");
                    Assert.Greater(l.slide.center.y, l.jump.center.y + l.jump.radius + l.slide.radius, where + ": slide is above jump, clear of it");
                    Assert.Less(l.slide.center.y - l.jump.center.y, 0.36f * s[1], where + ": slide is within a thumb's reach of jump");
                }
        }

        [Test]
        public void KickHasRoomToAimAboveAndToBothSides()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                // A full-power drag is about a quarter of the screen's height.
                float room = 0.22f * h;
                Assert.GreaterOrEqual(l.kick.center.x, room, where + ": room to the left");
                Assert.GreaterOrEqual(w - l.kick.center.x, room, where + ": room to the right");
                Assert.GreaterOrEqual(h - l.kick.center.y, room, where + ": room above");
            });
        }

        [Test]
        public void LeftHandedMirrorsTheActionCluster()
        {
            foreach (bool arrows in new[] { true, false })
                foreach (var s in Screens)
                {
                    var right = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), false, arrows);
                    var left = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), true, arrows);
                    Assert.AreEqual(s[0] - right.jump.center.x, left.jump.center.x, 0.01f, "jump mirrors");
                    Assert.AreEqual(s[0] - right.kick.center.x, left.kick.center.x, 0.01f, "kick mirrors");
                    Assert.AreEqual(right.jump.center.y, left.jump.center.y, 0.01f, "same height");
                    Assert.AreEqual(right.slide.center.y, left.slide.center.y, 0.01f, "same height");
                    if (!arrows) Assert.AreEqual(s[0] - right.slide.center.x, left.slide.center.x, 0.01f, "slide mirrors");
                }
        }

        [Test]
        public void WalkArrowsKeepTheirOrderWhenMirrored()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                Assert.Less(l.walkBack.center.x, l.walkForward.center.x, where + ": back stays left of forward");
                // And side by side, near enough to rock the thumb across without lifting it.
                Assert.Less(Gap(l.walkBack, l.walkForward), 0.08f * h, where + ": arrows are neighbours");
                Assert.GreaterOrEqual(Gap(l.walkBack, l.walkForward), 0f, where + ": arrows do not overlap");
            });
        }

        [Test]
        public void TheClustersDoNotCollide()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                // The two jump/kick buttons against the arrows (the slide button belongs to one cluster or the other).
                foreach (var a in new[] { l.walkBack, l.walkForward })
                    foreach (var b in new[] { l.jump, l.kick })
                        Assert.GreaterOrEqual(Gap(a, b), 0.05f * h, where + ": a walk arrow and jump/kick");
                if (!arrows)
                    foreach (var a in new[] { l.walkBack, l.walkForward })
                        Assert.GreaterOrEqual(Gap(a, l.slide), 0.05f * h, where + ": a walk arrow and the slide button");
            });
        }

        [Test]
        public void TheKidIsStoodClearOfEveryButtonOnTheLeftOfTheScreen()
        {
            ForEveryLayout((l, w, h, left, arrows, where) =>
            {
                float safe = GameInput.KidSafeScreenXOn(l, w, h, 0.14f);
                foreach (var b in All(l))
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
            // 16:9 and wider: the buttons take up little of the width, so the kid keeps a good view ahead.
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    if (s[0] / (float)s[1] < 1.7f) continue;
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left, true);
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

        [Test]
        public void AFlickDownNeedsToBeFastAndFarEnoughAndComeBackUpToRepeat()
        {
            float y = 400f, time = 0f;    // a resting finger
            float drop = 48f;             // 0.3 inch at 160 dpi
            Assert.IsFalse(GameInput.FlickDown(ref y, ref time, 400f, 0.1f, drop, 0.3f), "resting");
            Assert.IsFalse(GameInput.FlickDown(ref y, ref time, 380f, 0.2f, drop, 0.3f), "a small drop");
            Assert.IsTrue(GameInput.FlickDown(ref y, ref time, 340f, 0.3f, drop, 0.3f), "a quick, long drop (60 px in 0.2 s)");
            Assert.IsFalse(GameInput.FlickDown(ref y, ref time, 300f, 0.35f, drop, 0.3f), "no second flick without coming back up");
            Assert.IsFalse(GameInput.FlickDown(ref y, ref time, 360f, 0.4f, drop, 0.3f), "coming back up");
            Assert.IsTrue(GameInput.FlickDown(ref y, ref time, 300f, 0.55f, drop, 0.3f), "and a flick again");
        }

        [Test]
        public void ASlowDriftDownIsNotAFlick()
        {
            float y = 400f, time = 0f;
            bool flicked = false;
            // 100 px down over two seconds, sampled every 1/30 s: always under a window's worth of the drop.
            for (int i = 1; i <= 60; i++)
                flicked |= GameInput.FlickDown(ref y, ref time, 400f - i * (100f / 60f), i / 30f, 48f, 0.3f);
            Assert.IsFalse(flicked, "a thumb easing down is not a slide");
        }

        [Test]
        public void ANotchPushesButtonsInward()
        {
            var flat = input.LayoutOn(2532, 1170, Full(2532, 1170), false, false);
            var notched = input.LayoutOn(2532, 1170, new Rect(141f, 0f, 2250f, 1170f), false, false);
            Assert.Less(notched.jump.center.x, flat.jump.center.x, "jump moves in from the right edge");
            Assert.Less(notched.slide.center.x, flat.slide.center.x, "slide moves in from the right edge");
            Assert.Greater(notched.walkBack.center.x, flat.walkBack.center.x, "the arrows move in from the left edge");
            var flatArrows = input.LayoutOn(2532, 1170, Full(2532, 1170), false, true);
            var notchedArrows = input.LayoutOn(2532, 1170, new Rect(141f, 0f, 2250f, 1170f), false, true);
            Assert.Greater(notchedArrows.slide.center.x, flatArrows.slide.center.x, "the slide button moves in from the left edge with the arrows");
        }
    }
}
#endif
