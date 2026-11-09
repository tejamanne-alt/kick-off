#if UNITY_INCLUDE_TESTS
using DribbleToSchool.Presentation;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The kid's gait (KidAnimator.StrideRate, StrideSwing): the steps quicken with the pace, a walk keeping most of a run's
    /// cadence; at a walk or a jog the planted foot sweeps back under the body at the body's own speed (it stays put on the
    /// ground, no skating); flat out, the run's long stride as before. Pure rules (no scene).
    /// </summary>
    public class GaitTests
    {
        const float RunSpeed = 4.2f, StrideFrequency = 1.9f, RunSwing = 42f, Leg = 0.62f;
        static float RunRate { get { return StrideFrequency * RunSpeed * 0.25f; } }

        /// <summary>How fast the planted foot sweeps back under the hip at mid-stance: leg x swing (radians) x the stride's rate.</summary>
        static float FootSweep(float pace)
        {
            float rate = KidAnimator.StrideRate(pace, RunRate);
            float swing = KidAnimator.StrideSwing(pace * RunSpeed, rate, Leg, pace, RunSwing);
            return Leg * swing * Mathf.Deg2Rad * 2f * Mathf.PI * rate;
        }

        [Test]
        public void TheStepsQuickenWithThePace()
        {
            Assert.AreEqual(0f, KidAnimator.StrideRate(0f, RunRate), 0.0001f, "standing: no steps");
            Assert.AreEqual(RunRate, KidAnimator.StrideRate(1f, RunRate), 0.0001f, "flat out: the run's rate, as before");
            float last = 0f;
            for (float pace = 0.05f; pace <= 1f; pace += 0.05f)
            {
                float rate = KidAnimator.StrideRate(pace, RunRate);
                Assert.Greater(rate, last, "quicker at " + pace);
                last = rate;
            }
            Assert.GreaterOrEqual(KidAnimator.StrideRate(0.25f, RunRate), 0.5f * RunRate, "a walk keeps half a run's cadence or more");
        }

        [Test]
        public void ThePlantedFootStaysPut()
        {
            foreach (float pace in new[] { 0.1f, 0.21f, 0.3f, 0.4f })
            {
                float speed = pace * RunSpeed, sweep = FootSweep(pace);
                Assert.AreEqual(speed, sweep, 0.15f * speed, "at " + pace + " of a run the foot sweeps back at the body's speed");
            }
            Assert.AreEqual(RunSwing, KidAnimator.StrideSwing(RunSpeed, RunRate, Leg, 1f, RunSwing), 0.0001f, "flat out: the long stride");
            Assert.AreEqual(0f, KidAnimator.StrideSwing(0f, 0f, Leg, 0f, RunSwing), 0.0001f, "standing: legs together");
            float prev = 0f;
            for (float pace = 0.05f; pace <= 1f; pace += 0.05f)
            {
                float swing = KidAnimator.StrideSwing(pace * RunSpeed, KidAnimator.StrideRate(pace, RunRate), Leg, pace, RunSwing);
                Assert.GreaterOrEqual(swing, prev - 0.0001f, "the stride opens out with the pace");
                Assert.LessOrEqual(swing, RunSwing + 0.0001f);
                prev = swing;
            }
        }
    }
}
#endif
