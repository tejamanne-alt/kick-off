#if UNITY_INCLUDE_TESTS
using DribbleToSchool.Ball;
using DribbleToSchool.InputHandling;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Holding the ball like a real dribbler. The stick's push sets the pace (a little push jogs, a full push runs), and a
    /// touch follows the pace (small at a walk, so the ball stays close; the long knock-on flat out). The kick button: a
    /// tap kicks as it always did, a drag aims, and a hold keeps the ball at the feet, after which letting go kicks nothing.
    /// Pure rules (no scene), with the game's default thresholds.
    /// </summary>
    public class DribbleControlTests
    {
        const float Dead = 0.22f, FullAt = 0.7f, MinPace = 0.3f, HoldTime = 0.22f;

        // ---------------------------------------------------------------- the stick's pace

        [Test]
        public void InsideTheDeadZoneTheKidStands()
        {
            Assert.AreEqual(0f, GameInput.StickPace(0f, Dead, FullAt, MinPace));
            Assert.AreEqual(0f, GameInput.StickPace(0.2f, Dead, FullAt, MinPace));
            Assert.AreEqual(0f, GameInput.StickPace(Dead, Dead, FullAt, MinPace), "on the dead zone's edge: still standing");
        }

        [Test]
        public void TheGentlestPushJogsAndAFullPushRuns()
        {
            Assert.AreEqual(MinPace, GameInput.StickPace(Dead + 0.0001f, Dead, FullAt, MinPace), 0.001f, "just past the dead zone: a jog");
            Assert.AreEqual(1f, GameInput.StickPace(FullAt, Dead, FullAt, MinPace), 0.0001f, "full speed where it says");
            Assert.AreEqual(1f, GameInput.StickPace(1f, Dead, FullAt, MinPace), 0.0001f, "at the ring's edge");
            Assert.AreEqual(1f, GameInput.StickPace(1.4f, Dead, FullAt, MinPace), 0.0001f, "a thumb past the ring runs, never faster");
            float half = GameInput.StickPace((Dead + FullAt) / 2f, Dead, FullAt, MinPace);
            Assert.AreEqual((MinPace + 1f) / 2f, half, 0.001f, "half way across, half way between a jog and a run");
        }

        [Test]
        public void PushingFurtherNeverSlowsTheKid()
        {
            float last = 0f;
            for (float x = 0f; x <= 1.2f; x += 0.01f)
            {
                float pace = GameInput.StickPace(x, Dead, FullAt, MinPace);
                Assert.GreaterOrEqual(pace, last, "at " + x);
                last = pace;
            }
        }

        // ---------------------------------------------------------------- the kick button

        [Test]
        public void AQuickTapStillKicks()
        {
            var g = GameInput.ReadKick(GameInput.KickGesture.Pending, 0.08f, false, HoldTime);
            Assert.AreEqual(GameInput.KickGesture.Pending, g, "a tap is not a hold yet");
            Assert.AreEqual(GameInput.KickLetGo.Tap, GameInput.ReleaseKick(g, false), "let go: the quick pass, as before");
        }

        [Test]
        public void HoldingKeepsTheBallAndLettingGoKicksNothing()
        {
            var g = GameInput.ReadKick(GameInput.KickGesture.Pending, HoldTime, false, HoldTime);
            Assert.AreEqual(GameInput.KickGesture.Hold, g, "held still to the hold time: keep the ball close");
            Assert.AreEqual(GameInput.KickLetGo.Nothing, GameInput.ReleaseKick(g, false), "let go after a hold: no kick");
            // A thumb that wanders while holding never starts an aim (no slow motion mid-dribble), and still kicks nothing.
            g = GameInput.ReadKick(g, 1.5f, true, HoldTime);
            Assert.AreEqual(GameInput.KickGesture.Hold, g);
            Assert.AreEqual(GameInput.KickLetGo.Nothing, GameInput.ReleaseKick(g, true));
        }

        [Test]
        public void ADragBeforeTheHoldTimeAimsAsBefore()
        {
            var g = GameInput.ReadKick(GameInput.KickGesture.Pending, 0.1f, true, HoldTime);
            Assert.AreEqual(GameInput.KickGesture.Aim, g);
            g = GameInput.ReadKick(g, 1f, true, HoldTime);
            Assert.AreEqual(GameInput.KickGesture.Aim, g, "an aim held a long time is still an aim");
            Assert.AreEqual(GameInput.KickLetGo.AimedKick, GameInput.ReleaseKick(g, true), "let go: the aimed kick");
            Assert.AreEqual(GameInput.KickLetGo.Tap, GameInput.ReleaseKick(g, false), "dragged back to the start: a quick pass, as before");
        }

        // ---------------------------------------------------------------- the touch follows the pace

        [Test]
        public void ATouchAtAWalkIsSmallAndFlatOutIsTheFullKnockOn()
        {
            const float Lead = 1.6f, Walk = 0.1f;
            Assert.AreEqual(Lead * Walk, BallController.TouchLead(Lead, Walk, 0f), 0.0001f, "standing start: the smallest touch");
            Assert.AreEqual(Lead, BallController.TouchLead(Lead, Walk, 1f), 0.0001f, "flat out: as it always was");
            Assert.AreEqual(Lead, BallController.TouchLead(Lead, Walk, 1.5f), 0.0001f, "never more than the full lead");
            Assert.Less(BallController.TouchLead(Lead, Walk, 0.3f), BallController.TouchLead(Lead, Walk, 0.6f), "the faster, the further");
        }
    }
}
#endif
