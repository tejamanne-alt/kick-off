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
        public void ABirdWithItsFeetApartTipsOnlyAsFarAsItsLegsKeepThemPlanted()
        {
            var root = new GameObject("Bird").transform;
            try
            {
                // Two legs bent a little at the knee, the feet well apart: a deep peck would lift the hind foot.
                var right = Node("LegR", root, new Vector3(0.02f, 0.12f, 0f));
                Node("FootR", Node("ShinR", right, new Vector3(0.03f, -0.055f, 0f)), new Vector3(0f, -0.055f, 0f));
                var left = Node("LegL", root, new Vector3(-0.02f, 0.12f, 0f));
                Node("FootL", Node("ShinL", left, new Vector3(-0.03f, -0.055f, 0f)), new Vector3(0f, -0.055f, 0f));
                var rig = LegGait.Rig.Find(root, root);
                Assert.AreEqual(2, rig.Count);
                float want = -40f * Mathf.Deg2Rad, tip = rig.Reach(want);
                Assert.Less(Mathf.Abs(tip), Mathf.Abs(want), "it tips less than asked");
                Assert.Greater(Mathf.Abs(tip), 0f, "but it does tip");
                Vector3 r0 = root.Find("LegR/ShinR/FootR").position, l0 = root.Find("LegL/ShinL/FootL").position;
                root.rotation = Quaternion.AngleAxis(tip * Mathf.Rad2Deg, Vector3.forward);
                rig.Plant(tip);
                Assert.Less((root.Find("LegR/ShinR/FootR").position - r0).magnitude, 1e-3f, "the front foot holds");
                Assert.Less((root.Find("LegL/ShinL/FootL").position - l0).magnitude, 1e-3f, "the hind foot holds");
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
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

        [Test]
        public void AFootLiesLevelPlantedRollsOverItsToesAndLandsLevelAgain()
        {
            // D20 then D21: a bird's toes, rigid in its shin, tipped into the floor; kept level all the way round they
            // looked glued to a board. A Toe hangs from the shin at the ankle, the Foot under it and a Tip at the front
            // of the toes: planted, the foot lies level on the ground; late in the stance its heel lifts and it rolls
            // over its toes (the Tip still down); in the swing its toes curl down; it lands level. Through a peck it
            // lies level and holds.
            var root = new GameObject("Bird").transform;
            try
            {
                var right = Node("LegR", root, new Vector3(0.01f, 0.12f, 0f));
                var shin = Node("ShinR", right, new Vector3(-0.02f, -0.06f, 0f));
                var toe = Node("ToeR", shin, new Vector3(0.01f, -0.05f, 0f));
                var foot = Node("FootR", toe, new Vector3(0.002f, -0.01f, 0f));
                var tip = Node("TipR", toe, new Vector3(0.03f, -0.01f, 0f));
                var left = Node("LegL", root, new Vector3(-0.01f, 0.12f, 0f));
                Node("FootL", Node("ShinL", left, new Vector3(-0.02f, -0.06f, 0f)), new Vector3(0.01f, -0.06f, 0f));
                var rig = LegGait.Rig.Find(root, root);
                Assert.AreEqual(2, rig.Count);
                Vector3 along = toe.right;
                float duty = LegGait.Duty(LegGait.Kind.Step), restAnkle = toe.position.y;
                float rolled = 0f, curled = 0f, ankleUp = 0f;
                for (int i = 0; i < 64; i++)
                {
                    float p = i / 64f;
                    root.position = new Vector3(0f, rig.Pose(p, 0f, 1f, 0f), 0f);
                    float ph = p + LegGait.Phase(LegGait.Kind.Step, "R");
                    ph -= Mathf.Floor(ph);
                    float angle = Vector3.Angle(toe.right, along);
                    Assert.GreaterOrEqual(tip.position.y, -2e-3f, "the toes never go through the ground at phase " + p);
                    if (ph < 0.7f * duty)
                    {
                        Assert.AreEqual(0f, tip.position.y, 2e-3f, "planted at phase " + p);
                        Assert.Less(angle, 0.5f, "and lying level");
                    }
                    else if (ph > 0.85f * duty && ph < duty)
                    {
                        Assert.AreEqual(0f, tip.position.y, 2e-3f, "the toes still down as the heel lifts, phase " + p);
                        rolled = Mathf.Max(rolled, angle);
                        ankleUp = Mathf.Max(ankleUp, toe.position.y - restAnkle - root.position.y);
                    }
                    else if (ph > duty + 0.2f * (1f - duty) && ph < duty + 0.5f * (1f - duty))
                        curled = Mathf.Max(curled, angle);
                    else if (ph > duty + 0.9f * (1f - duty))
                        Assert.Less(angle, 0.5f, "level again before it lands, phase " + p);
                }
                Assert.Greater(rolled, 8f, "the foot rolls over its toes late in the stance");
                Assert.Greater(ankleUp, 1e-3f, "its heel lifting");
                Assert.Greater(curled, 30f, "and its toes curl in the swing");
                rig.Rest();
                root.position = Vector3.zero;
                Vector3 stood = tip.position;
                float lean = rig.Reach(-20f * Mathf.Deg2Rad);
                root.rotation = Quaternion.AngleAxis(lean * Mathf.Rad2Deg, Vector3.forward);
                rig.Plant(lean);
                Assert.Greater(Vector3.Dot(toe.right, along), 0.9999f, "level as the body tips to peck");
                Assert.Less((tip.position - stood).magnitude, 2e-3f, "and the foot holds where it stood");
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
        }

        [Test]
        public void ABackTiltedByItsLegsKeepsEveryPlantedFootOnTheGround()
        {
            // D21: each end of the body as low as its own legs need, the back tilting between them, the feet planted.
            var root = new GameObject("Animal").transform;
            try
            {
                string[] names = { "FR", "FL", "BR", "BL" };
                foreach (string n in names)
                {
                    bool front = n[0] == 'F';
                    var thigh = Node("Leg" + n, root, new Vector3(front ? 0.12f : -0.12f, 0.3f, 0f));
                    var shin = Node("Shin" + n, thigh, new Vector3(front ? 0.02f : -0.02f, -0.15f, 0f));
                    Node("Foot" + n, shin, new Vector3(front ? -0.01f : 0.015f, -0.15f, 0f));
                }
                var rig = LegGait.Rig.Find(root, root);
                Assert.AreEqual(4, rig.Count);
                float duty = LegGait.Duty(LegGait.Kind.Walk), most = 0f;
                for (int i = 0; i < 64; i++)
                {
                    float p = i / 64f, pitch;
                    float lift = rig.Pose(p, 0f, 1f, 0f, out pitch);
                    root.SetPositionAndRotation(new Vector3(0f, lift, 0f), Quaternion.AngleAxis(pitch * Mathf.Rad2Deg, rig.Side));
                    Assert.Less(Mathf.Abs(pitch), 0.2f, "the back tilts a little, not much");
                    most = Mathf.Max(most, Mathf.Abs(pitch));
                    foreach (string n in names)
                    {
                        float ph = p + LegGait.Phase(LegGait.Kind.Walk, n);
                        ph -= Mathf.Floor(ph);
                        float y = root.Find("Leg" + n + "/Shin" + n + "/Foot" + n).position.y;
                        if (ph < duty) Assert.AreEqual(0f, y, 3e-3f, n + " is planted at phase " + p);
                        else Assert.GreaterOrEqual(y, -3e-3f, n + " never goes through the ground");
                    }
                }
                Assert.Greater(most, 1e-3f, "and it does tilt");
            }
            finally
            {
                Object.DestroyImmediate(root.gameObject);
            }
        }

        [Test]
        public void ABoundIsOneSmoothLoopStandingOnTheGroundAtContact()
        {
            // D21: a squirrel's dash bounds on its legs (TreeSquirrel): each pair of feet on one loop, k 1 meeting k 0,
            // never through the ground, both pairs down at contact; the hind feet reaching ahead of their hips to land and
            // stretching behind them after the push; the back gathered at contact and stretched in the air.
            foreach (bool hind in new[] { true, false })
            {
                Vector2 a = LegGait.BoundFoot(hind, 0f), b = LegGait.BoundFoot(hind, 1f - 1e-4f);
                Assert.Less((a - b).magnitude, 0.01f, "the loop closes");
                Assert.AreEqual(0f, a.y, 1e-3f, "down at contact");
                Vector2 last = a;
                float most = -1f, least = 1f;
                for (int i = 1; i <= 200; i++)
                {
                    Vector2 f = LegGait.BoundFoot(hind, i / 200f);
                    Assert.GreaterOrEqual(f.y, 0f, "never through the ground");
                    Assert.Less((f - last).magnitude, 0.08f, "no jump at " + i / 200f);
                    Assert.GreaterOrEqual(LegGait.BoundRoll(hind, i / 200f), 0f, "never heel down");
                    most = Mathf.Max(most, f.x);
                    least = Mathf.Min(least, f.x);
                    last = f;
                }
                Assert.Greater(most - least, 0.6f, hind ? "the hind feet swing far" : "the front feet reach far");
            }
            Assert.Greater(LegGait.BoundSpine(0f), 0f, "the back gathered at contact");
            Assert.Less(LegGait.BoundSpine(0.2f), 0f, "and stretched in the air");
        }
    }
}
#endif
