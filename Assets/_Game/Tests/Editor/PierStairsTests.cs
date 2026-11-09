#if UNITY_INCLUDE_TESTS
using DribbleToSchool.World;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The way up to the pier: how a flight of its stairs is laid out for the drop from the deck to the sand. Comfortable
    /// steps (all the same height), a mid-landing halfway on a long flight, and the reach the level builder keeps clear.
    /// Pure rules (no scene).
    /// </summary>
    public class PierStairsTests
    {
        [Test]
        public void EveryStepIsComfortableAndTheyAddUpToTheDrop()
        {
            for (float drop = 1.5f; drop <= 4.8f; drop += 0.05f)
            {
                var p = PierStairs.PlanFor(drop);
                Assert.GreaterOrEqual(p.riser, 0.175f, "risers within a centimetre and a half of 0.19 for a drop of " + drop);
                Assert.LessOrEqual(p.riser, 0.205f, "risers within a centimetre and a half of 0.19 for a drop of " + drop);
                Assert.AreEqual(drop, p.riser * p.risers, 0.0001f, "the steps add up to the drop of " + drop);
                Assert.AreEqual(p.risers, p.toMid + p.afterMid);
            }
        }

        [Test]
        public void ALongFlightHasAMidLandingHalfway()
        {
            var deck = PierStairs.PlanFor(4.5f);     // the deck over the open beach
            Assert.Greater(deck.afterMid, 0, "a mid-landing on the way down from the deck");
            Assert.LessOrEqual(deck.toMid - deck.afterMid, 1, "halfway (the upper half one step longer at most)");
            Assert.GreaterOrEqual(deck.toMid - deck.afterMid, 0);
            Assert.AreEqual((deck.toMid - 1) * PierStairs.Going + PierStairs.MidLength + (deck.afterMid - 1) * PierStairs.Going, deck.run, 0.0001f);

            var dune = PierStairs.PlanFor(2f);       // sand piled high under the pier
            Assert.AreEqual(0, dune.afterMid, "a short flight runs straight down");
            Assert.AreEqual((dune.risers - 1) * PierStairs.Going, dune.run, 0.0001f);
        }

        [Test]
        public void AFurtherDropNeverMakesAShorterFlight()
        {
            float last = 0f;
            for (float drop = 0.5f; drop <= 4.8f; drop += 0.01f)
            {
                float run = PierStairs.PlanFor(drop).run;
                Assert.GreaterOrEqual(run, last - 0.0001f, "at a drop of " + drop);
                last = run;
            }
        }

        [Test]
        public void TheReachCoversTheLongestFlightAndItsPad()
        {
            // The level builder keeps the towers, palms and parasols out of the reach at the longest drop (the sand at sea level).
            float reach = PierStairs.Reach(6f, 4.8f);
            for (float drop = 0.5f; drop <= 4.8f; drop += 0.05f)
                Assert.LessOrEqual(3f + PierStairs.PlanFor(drop).run + PierStairs.FootPad, reach + 0.0001f, "at a drop of " + drop);
            Assert.Less(reach, 13f, "the stairs stay a sensible size");
        }
    }
}
#endif
