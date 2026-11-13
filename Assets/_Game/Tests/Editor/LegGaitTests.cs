#if UNITY_INCLUDE_TESTS
using DribbleToSchool.World;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The animals' jointed legs (World/LegGait, docs/LEARNINGS.md D19): a foot's path is down and sliding back evenly
    /// for the stance, then up and forward, with no jump anywhere in the cycle; the two-bone solver puts the foot where
    /// it is asked and leaves a leg at rest alone; a rig of real transforms keeps every planted foot on the ground
    /// through a whole walk (the body moved by the lift the rig used, lowered where a foot must reach), and keeps the
    /// feet where they stood while a peck tips the body.
    /// </summary>
    public class LegGaitTests
    {
        [Test]
        public void AFootSlidesBackOnTheGroundThenLiftsAndComesForwardWithNoJump()
        {
            foreach (LegGait.Kind kind in new[] { LegGait.Kind.Walk, LegGait.Kind.Trot, LegGait.Kind.Step })
            {
                float duty = LegGait.Duty(kind), stride = 0.5f, lift = 0.1f;
                Vector2 last = LegGait.FootPath(0f, duty, stride, lift);
                float highest = 0f;
                for (int i = 1; i <= 400; i++)
                {
                    float p = i / 400f;
                    Vector2 at = LegGait.FootPath(p, duty, stride, lift);
                    Assert.Less((at - last).magnitude, 0.02f, kind + ": the foot jumps at phase " + p);
                    if (p < duty)
                    {
                        Assert.AreEqual(0f, at.y, 1e-6f, kind + ": a planted foot is on the ground");
                        Assert.Less(at.x, last.x + 1e-6f, kind + ": a planted foot slides back");
                    }
                    highest = Mathf.Max(highest, at.y);
                    last = at;
                }
                Assert.AreEqual(lift, highest, 0.002f, kind + ": the swing lifts the foot by its lift");
                Assert.AreEqual(stride * 0.5f, LegGait.FootPath(0f, duty, stride, lift).x, 1e-5f);
                Assert.AreEqual(-stride * 0.5f, LegGait.FootPath(duty, duty, stride, lift).x, 1e-5f);
            }
        }

        static Vector2 Reach(Vector2 knee, Vector2 foot, Vector2 turn)
        {
            Vector2 k = Rotate(knee, turn.x);
            return k + Rotate(foot - knee, turn.x + turn.y);
        }

        static Vector2 Rotate(Vector2 v, float a)
        {
            return new Vector2(v.x * Mathf.Cos(a) - v.y * Mathf.Sin(a), v.x * Mathf.Sin(a) + v.y * Mathf.Cos(a));
        }

        [Test]
        public void TheTwoBoneSolverPutsTheFootOnItsTargetAndLeavesARestingLegAlone()
        {
            var legs = new[]
            {
                new[] { new Vector2(0.05f, -0.5f), new Vector2(0f, -1f) },
                new[] { new Vector2(-0.08f, -0.45f), new Vector2(0.02f, -0.95f) },
            };
            foreach (var leg in legs)
            {
                foreach (bool front in new[] { true, false })
                {
                    float bend = LegGait.Bend(leg[0], leg[1], front);
                    Vector2 rest = LegGait.TwoBone(leg[0], leg[1], leg[1], bend);
                    Assert.AreEqual(0f, rest.x, 1e-3f, "a leg asked for its own foot stays put");
                    Assert.AreEqual(0f, rest.y, 1e-3f);
                    foreach (var target in new[] { new Vector2(0.2f, -0.9f), new Vector2(-0.25f, -0.88f), new Vector2(0.1f, -0.7f) })
                    {
                        Vector2 at = Reach(leg[0], leg[1], LegGait.TwoBone(leg[0], leg[1], target, bend));
                        Assert.Less((at - target).magnitude, 1e-3f, "the foot reaches " + target);
                    }
                }
            }
        }

        static Transform Node(string name, Transform parent, Vector3 local)
        {
            var t = new GameObject(name).transform;
            t.SetParent(parent, false);
            t.localPosition = local;
            return t;
        }

        [Test]
        public void ARigKeepsEveryPlantedFootOnTheGroundAndHoldsItsFeetThroughAPeck()
        {
            var root = new GameObject("Animal").transform;
            try
            {
                // A front leg bent a little forward at the knee, a hind leg a little back, feet on the ground (y 0).
                var front = Node("LegFR", root, new Vector3(0.12f, 0.3f, 0f));
                var frontShin = Node("ShinFR", front, new Vector3(0.02f, -0.15f, 0f));
                Node("FootFR", frontShin, new Vector3(-0.01f, -0.15f, 0f));
                var back = Node("LegBL", root, new Vector3(-0.12f, 0.3f, 0f));
                var backShin = Node("ShinBL", back, new Vector3(-0.02f, -0.15f, 0f));
                Node("FootBL", backShin, new Vector3(0.015f, -0.15f, 0f));
                var rig = LegGait.Rig.Find(root, root);
                Assert.AreEqual(2, rig.Count);
                float duty = LegGait.Duty(LegGait.Kind.Walk);
                for (int i = 0; i < 64; i++)
                {
                    float p = i / 64f;
                    root.position = new Vector3(0f, rig.Pose(p, 0f, 1f, 0f), 0f);    // the body moved by the lift used
                    foreach (string n in new[] { "FR", "BL" })
                    {
                        float ph = p + LegGait.Phase(LegGait.Kind.Walk, n);
                        ph -= Mathf.Floor(ph);
                        float y = root.Find("Leg" + n + "/Shin" + n + "/Foot" + n).position.y;
                        if (ph < duty) Assert.AreEqual(0f, y, 2e-3f, n + " is planted at phase " + p);
                        else Assert.GreaterOrEqual(y, -2e-3f, n + " never goes through the ground");
                    }
                }
                rig.Rest();
                root.position = Vector3.zero;
                Vector3 frontFoot = root.Find("LegFR/ShinFR/FootFR").position, backFoot = root.Find("LegBL/ShinBL/FootBL").position;
                // A peck: the body tips 25 degrees nose-down about its origin; the feet stay where they stood.
                root.rotation = Quaternion.AngleAxis(-25f, Vector3.forward);
                rig.Plant(-25f * Mathf.Deg2Rad);
                Assert.Less((root.Find("LegFR/ShinFR/FootFR").position - frontFoot).magnitude, 2e-3f, "the front foot holds");
                Assert.Less((root.Find("LegBL/ShinBL/FootBL").position - backFoot).magnitude, 2e-3f, "the hind foot holds");
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
        }
    }
}
#endif
