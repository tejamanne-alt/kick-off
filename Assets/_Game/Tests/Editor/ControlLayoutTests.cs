#if UNITY_INCLUDE_TESTS
using DribbleToSchool.InputHandling;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The on-screen touch buttons: JUMP, SLIDE and KICK must never crowd one another (kicking and
    /// sliding in turn was hard when they sat in a row), stay on the screen, leave the aim drag room,
    /// and keep their order when mirrored for left-handed play, on every landscape shape from 4:3
    /// tablets to 21:9 phones, in both the story and the Holiday Run layouts.
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

        delegate void Check(GameInput.ControlLayout layout, int w, int h, string where);

        void ForEveryLayout(Check check)
        {
            foreach (bool runner in new[] { false, true })
                foreach (bool left in new[] { false, true })
                    foreach (var s in Screens)
                    {
                        input.runnerLayout = runner;
                        var layout = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), left);
                        check(layout, s[0], s[1], (runner ? "runner " : "story ") + (left ? "left-handed " : "") + s[0] + "x" + s[1]);
                    }
        }

        [Test]
        public void ActionButtonsAreNeverCrowded()
        {
            ForEveryLayout((l, w, h, where) =>
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
            ForEveryLayout((l, w, h, where) =>
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
        public void JumpIsTheBiggestButton()
        {
            ForEveryLayout((l, w, h, where) =>
            {
                Assert.Greater(l.jump.radius, l.kick.radius, where + ": jump vs kick");
                Assert.GreaterOrEqual(l.jump.radius, l.slide.radius, where + ": jump vs slide");
            });
        }

        [Test]
        public void ButtonsAreBigEnoughForAThumb()
        {
            // At least 9 mm across on a phone held at about 2.9 inches of screen height: 0.1 of the height.
            ForEveryLayout((l, w, h, where) =>
            {
                foreach (var b in new[] { l.jump, l.kick, l.slide })
                    Assert.GreaterOrEqual(b.radius * 2f, 0.17f * h, where + ": button diameter");
            });
        }

        [Test]
        public void StoryClustersDoNotCollide()
        {
            input.runnerLayout = false;
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
            input.runnerLayout = false;
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
            foreach (bool runner in new[] { false, true })
                foreach (var s in Screens)
                {
                    input.runnerLayout = runner;
                    var right = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), false);
                    var left = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), true);
                    Assert.AreEqual(s[0] - right.jump.center.x, left.jump.center.x, 0.01f, "jump mirrors");
                    Assert.AreEqual(s[0] - right.kick.center.x, left.kick.center.x, 0.01f, "kick mirrors");
                    Assert.AreEqual(s[0] - right.slide.center.x, left.slide.center.x, 0.01f, "slide mirrors");
                    Assert.AreEqual(right.jump.center.y, left.jump.center.y, 0.01f, "same height");
                }
        }

        [Test]
        public void WalkArrowsKeepTheirOrderWhenMirrored()
        {
            input.runnerLayout = false;
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
        public void RunnerLayoutPutsJumpAndSlideUnderDifferentThumbs()
        {
            input.runnerLayout = true;
            foreach (var s in Screens)
            {
                var l = input.LayoutOn(s[0], s[1], Full(s[0], s[1]), false);
                Assert.Greater(l.jump.center.x, s[0] * 0.5f, "jump is on the right");
                Assert.Less(l.slide.center.x, s[0] * 0.5f, "slide is on the left");
            }
        }

        [Test]
        public void ANotchPushesButtonsInward()
        {
            input.runnerLayout = false;
            var flat = input.LayoutOn(2532, 1170, Full(2532, 1170), false);
            var notched = input.LayoutOn(2532, 1170, new Rect(141f, 0f, 2250f, 1170f), false);
            Assert.Less(notched.jump.center.x, flat.jump.center.x, "jump moves in from the right edge");
            Assert.Greater(notched.walkBack.center.x, flat.walkBack.center.x, "the arrows move in from the left edge");
        }
    }
}
#endif
