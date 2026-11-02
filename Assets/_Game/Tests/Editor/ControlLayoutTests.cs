#if UNITY_INCLUDE_TESTS
using DribbleToSchool.InputHandling;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The on-screen touch buttons: JUMP and SLIDE stacked at the edge, KICK to their left, all one size;
    /// none of them crowds another, they stay on the screen, leave the aim drag room, and keep their order
    /// when mirrored for left-handed play, on every landscape shape from 4:3 tablets to 21:9 phones.
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

        delegate void Check(GameInput.ControlLayout layout, int w, int h, bool leftHanded, string where);

        void ForEveryLayout(Check check)
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var layout = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                    check(layout, s[0], s[1], left, (left ? "left-handed " : "") + s[0] + "x" + s[1]);
                }
        }

        /// <summary>How far in from the edge the action buttons' side of the screen a button's centre is.</summary>
        static float FromEdge(GameInput.Round b, int w, bool leftHanded)
        {
            return leftHanded ? b.center.x : w - b.center.x;
        }

        [Test]
        public void ActionButtonsAreNeverCrowded()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                float min = 0.1f * h;
                Assert.GreaterOrEqual(Gap(l.jump, l.kick), min, where + ": jump/kick");
                Assert.GreaterOrEqual(Gap(l.jump, l.slide), min, where + ": jump/slide");
                Assert.GreaterOrEqual(Gap(l.kick, l.slide), min, where + ": kick/slide");
            });
        }

        [Test]
        public void EveryButtonIsFullyOnScreen()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                foreach (var b in new[] { l.jump, l.kick, l.slide })
                {
                    Assert.GreaterOrEqual(b.center.x - b.radius, 0f, where + ": left edge");
                    Assert.LessOrEqual(b.center.x + b.radius, w, where + ": right edge");
                    Assert.GreaterOrEqual(b.center.y - b.radius, 0f, where + ": bottom edge");
                    Assert.LessOrEqual(b.center.y + b.radius, h, where + ": top edge");
                }
            });
        }

        [Test]
        public void AllThreeButtonsAreTheSameSize()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                Assert.AreEqual(l.jump.radius, l.slide.radius, 0.01f, where + ": jump vs slide");
                Assert.AreEqual(l.jump.radius, l.kick.radius, 0.01f, where + ": jump vs kick");
            });
        }

        [Test]
        public void ButtonsAreBigEnoughForAThumb()
        {
            // At least 9 mm across on a phone held at about 2.9 inches of screen height: 0.17 of the height.
            ForEveryLayout((l, w, h, left, where) =>
            {
                foreach (var b in new[] { l.jump, l.kick, l.slide })
                    Assert.GreaterOrEqual(b.radius * 2f, 0.17f * h, where + ": button diameter");
            });
        }

        [Test]
        public void JumpAndSlideAreStackedAtTheEdgeJumpAtTheBottom()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                Assert.AreEqual(l.jump.center.x, l.slide.center.x, 0.01f, where + ": one column");
                Assert.Greater(l.slide.center.y, l.jump.center.y + l.jump.radius + l.slide.radius, where + ": slide is above jump, clear of it");
                Assert.Less(FromEdge(l.jump, w, left), 0.3f * h, where + ": the stack is at the edge");
            });
        }

        [Test]
        public void KickSitsOnJumpsBaselineBesideTheStack()
        {
            ForEveryLayout((l, w, h, left, where) =>
            {
                Assert.AreEqual(l.jump.center.y, l.kick.center.y, 0.03f * h, where + ": kick is on jump's baseline");
                Assert.Greater(FromEdge(l.kick, w, left), FromEdge(l.jump, w, left) + l.jump.radius + l.kick.radius, where + ": kick is beside the stack, not under it");
            });
        }

        [Test]
        public void StoryClustersDoNotCollide()
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                    string where = (left ? "left-handed " : "") + s[0] + "x" + s[1];
                    foreach (var a in new[] { l.walkBack, l.walkForward })
                        foreach (var b in new[] { l.jump, l.kick, l.slide })
                            Assert.GreaterOrEqual(Gap(a, b), 0.05f * s[1], where + ": a walk arrow and an action button");
                }
        }

        [Test]
        public void KickHasRoomToAimAboveAndToBothSides()
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                    string where = (left ? "left-handed " : "") + s[0] + "x" + s[1];
                    // A full-power drag is about a quarter of the screen's height.
                    float room = 0.22f * s[1];
                    Assert.GreaterOrEqual(l.kick.center.x, room, where + ": room to the left");
                    Assert.GreaterOrEqual(s[0] - l.kick.center.x, room, where + ": room to the right");
                    Assert.GreaterOrEqual(s[1] - l.kick.center.y, room, where + ": room above");
                }
        }

        [Test]
        public void LeftHandedMirrorsTheCluster()
        {
            foreach (var s in Screens)
            {
                var right = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), false);
                var left = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), true);
                Assert.AreEqual(s[0] - right.jump.center.x, left.jump.center.x, 0.01f, "jump mirrors");
                Assert.AreEqual(s[0] - right.kick.center.x, left.kick.center.x, 0.01f, "kick mirrors");
                Assert.AreEqual(s[0] - right.slide.center.x, left.slide.center.x, 0.01f, "slide mirrors");
                Assert.AreEqual(right.jump.center.y, left.jump.center.y, 0.01f, "same height");
                Assert.AreEqual(right.slide.center.y, left.slide.center.y, 0.01f, "same height");
            }
        }

        [Test]
        public void WalkArrowsKeepTheirOrderWhenMirrored()
        {
            foreach (bool left in new[] { false, true })
                foreach (var s in Screens)
                {
                    var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                    Assert.Less(l.walkBack.center.x, l.walkForward.center.x, "back stays left of forward (" + (left ? "left-handed " : "") + s[0] + "x" + s[1] + ")");
                    // And side by side, near enough to rock the thumb across without lifting it.
                    Assert.Less(Gap(l.walkBack, l.walkForward), 0.08f * s[1], "arrows are neighbours");
                    Assert.GreaterOrEqual(Gap(l.walkBack, l.walkForward), 0f, "arrows do not overlap");
                }
        }

        [Test]
        public void ANotchPushesButtonsInward()
        {
            var flat = input.LayoutOn(2532, 1170, Full(2532, 1170), false);
            var notched = input.LayoutOn(2532, 1170, new Rect(141f, 0f, 2250f, 1170f), false);
            Assert.Less(notched.jump.center.x, flat.jump.center.x, "jump moves in from the right edge");
            Assert.Less(notched.slide.center.x, flat.slide.center.x, "slide moves in from the right edge");
            Assert.Greater(notched.walkBack.center.x, flat.walkBack.center.x, "the arrows move in from the left edge");
        }
    }
}
#endif
