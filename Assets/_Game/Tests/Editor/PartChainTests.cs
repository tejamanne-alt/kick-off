#if UNITY_INCLUDE_TESTS
using DribbleToSchool.World;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// A moving part in links (World/PartChain, docs/LEARNINGS.md D19): a tail of three links is found by its names; held
    /// at an angle it bends by exactly that angle in all, the first link the most; swung suddenly, its further links
    /// follow late (a whip, not a stick); and a part with no links turns whole, as the original kit's always did.
    /// </summary>
    public class PartChainTests
    {
        static Transform Link(string name, Transform parent, Vector3 local)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = local;
            return t;
        }

        [Test]
        public void TheSharesAddUpToTheWholeAngleTheFirstLinkTakingMost()
        {
            for (int n = 1; n <= 5; n++)
            {
                float sum = 0f;
                for (int i = 0; i < n; i++)
                {
                    sum += PartChain.Share(i, n);
                    if (i > 0) Assert.Less(PartChain.Share(i, n), PartChain.Share(i - 1, n));
                }
                Assert.AreEqual(1f, sum, 1e-5f, n + " links");
            }
        }

        [Test]
        public void ATailInLinksBendsByTheAngleAskedAndItsTipFollowsLate()
        {
            var root = new GameObject("Cat").transform;
            try
            {
                var tail = Link("Tail", root, Vector3.zero);
                var tail2 = Link("Tail2", tail, new Vector3(-0.1f, 0f, 0f));
                var tail3 = Link("Tail3", tail2, new Vector3(-0.08f, 0f, 0f));
                var chain = PartChain.Find(tail, Vector3.forward);
                Assert.AreEqual(3, chain.Links);
                // Held at 30 degrees long enough to settle: the tip points 30 degrees round from where it rested.
                for (int i = 0; i < 200; i++) chain.Set(30f, 0.02f);
                Assert.AreEqual(30f, Quaternion.Angle(Quaternion.identity, tail3.rotation), 0.05f, "the whole tail bends by the angle");
                Assert.AreEqual(15f, Quaternion.Angle(Quaternion.identity, tail.localRotation), 0.05f, "the first link takes half");
                // Swung suddenly back the other way: one frame later the base has turned, the tip barely.
                chain.Set(-30f, 0.02f);
                float baseTurn = Quaternion.Angle(Quaternion.identity, tail.localRotation);
                float tipTurn = Quaternion.Angle(Quaternion.identity, tail3.localRotation);
                Assert.AreEqual(15f, baseTurn, 0.05f, "the base swings at once");
                Assert.Greater(tipTurn, 3f, "the tip still points the old way: it follows late");
                chain.Rest();
                Assert.AreEqual(0f, Quaternion.Angle(Quaternion.identity, tail3.rotation), 0.01f);
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
        }

        [Test]
        public void APartWithNoLinksTurnsWholeAsBefore()
        {
            var root = new GameObject("Dog").transform;
            try
            {
                var tail = Link("Tail", root, Vector3.zero);
                Link("TailTip", tail, new Vector3(-0.1f, 0f, 0f));       // not named Tail2: not a link
                Assert.AreEqual(1, PartChain.Find(tail, Vector3.forward).Links);
                var part = new AmbientAgent.Part(tail, Vector3.forward);
                Assert.IsNull(part.chain, "a part without links has no chain");
                part.Set(20f);
                Assert.AreEqual(20f, Quaternion.Angle(Quaternion.identity, tail.localRotation), 0.01f, "it turns whole");
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
        }
    }
}
#endif
