#if UNITY_INCLUDE_TESTS
using DribbleToSchool.World;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// A real bird's wingbeat (World/WingStroke, docs/LEARNINGS.md D21): one smooth loop; spread and swept a little
    /// forward on the way down; folded at the wrist and swept back on the way up; the body rising on the downstroke.
    /// And a wing in links set by it: its outer link folds against the flap.
    /// </summary>
    public class WingStrokeTests
    {
        [Test]
        public void TheBeatIsOneSmoothLoopSpreadDownFoldedUp()
        {
            float up = 50f, down = 40f, fold = 65f, sweep = 20f;
            Vector4 top = WingStroke.At(0f, up, down, fold, sweep), end = WingStroke.At(2f * Mathf.PI - 1e-4f, up, down, fold, sweep);
            Assert.Less((top - end).magnitude, 0.2f, "the beat's end meets its start");
            Assert.AreEqual(up, top.x, 1e-3f, "it starts at the top");
            Vector4 last = top;
            float lowest = up, foldedMost = 0f;
            for (int i = 1; i <= 400; i++)
            {
                float u = i / 400f;
                Vector4 w = WingStroke.At(u * 2f * Mathf.PI, up, down, fold, sweep);
                Assert.Less(Mathf.Abs(w.x - last.x), 4f, "no jump in the flap at " + u);
                Assert.Less(Mathf.Abs(w.y - last.y), 4f, "no jump in the fold at " + u);
                if (u < WingStroke.DownShare)
                {
                    Assert.AreEqual(0f, w.y, 1e-3f, "spread on the way down");
                    Assert.LessOrEqual(w.z, 1e-3f, "swept forward, if at all, on the way down");
                    Assert.GreaterOrEqual(w.w, -1e-3f, "the body rises on the downstroke");
                }
                else
                {
                    Assert.GreaterOrEqual(w.y, -1e-3f, "folded on the way up");
                    Assert.GreaterOrEqual(w.z, -1e-3f, "swept back on the way up");
                }
                lowest = Mathf.Min(lowest, w.x);
                foldedMost = Mathf.Max(foldedMost, w.y);
                last = w;
            }
            Assert.AreEqual(-down, lowest, 0.5f, "it beats down to the bottom");
            Assert.AreEqual(fold, foldedMost, 0.5f, "and folds fully mid-upstroke");
        }

        [Test]
        public void AWingInLinksFoldsItsOuterLinkAgainstTheFlap()
        {
            var root = new GameObject("Bird").transform;
            try
            {
                var wing = new GameObject("WingL").transform;
                wing.SetParent(root, false);
                var outer = new GameObject("WingL2").transform;
                outer.SetParent(wing, false);
                outer.localPosition = new Vector3(0f, 0f, 0.1f);
                var part = new AmbientAgent.Part(wing, Vector3.right);
                Assert.IsNotNull(part.chain, "a wing in two links");
                part.SetWing(30f, 50f, 15f, Vector3.up);
                Assert.Less(Quaternion.Angle(wing.localRotation, Quaternion.AngleAxis(15f, Vector3.up) * Quaternion.AngleAxis(30f, Vector3.right)), 0.1f,
                    "the inner wing swept back and flapped up");
                Assert.Less(Quaternion.Angle(outer.localRotation, Quaternion.AngleAxis(-50f, Vector3.right)), 0.1f,
                    "the outer wing folded down against the flap at the wrist");
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
        }
    }
}
#endif
