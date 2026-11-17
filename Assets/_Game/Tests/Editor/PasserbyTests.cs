#if UNITY_INCLUDE_TESTS
using System.Collections.Generic;
using DribbleToSchool.EditorTools;
using NUnit.Framework;
using UnityEngine;
using Track = DribbleToSchool.EditorTools.LevelBuildKit.TrackBuilder;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The rigged passers-by (LevelBuildKit.Passersby): each has a wardrobe to be dressed from, level by level, and stands a
    /// grown-up's height (the jogger, the office worker, the courier and Grandad as tall as the old procedural adult; Mom and
    /// the shopkeeper a little shorter, still taller than the kid); the footpath's turn order brings each of them along once
    /// before any comes again, in an order of each level's own. Pure rules (no scene).
    /// </summary>
    public class PasserbyTests
    {
        [Test]
        public void EachPasserbyHasAWardrobe()
        {
            var names = new HashSet<string>();
            foreach (var p in LevelBuildKit.Passersby)
            {
                Assert.IsTrue(names.Add(p.model), p.model + " twice");
                Assert.Greater(p.tops.Length, 1, p.model + ": tops to change into");
                Assert.Greater(p.legwears.Length, 1, p.model + ": legwear to change into");
                Assert.Greater(p.thirds.Length, 0, p.model + ": hair, cap or hijab");
                Assert.IsTrue(p.NeckHeight > 1.3f * 1.05f && p.NeckHeight <= LevelBuildKit.AdultNeck + 0.0001f, p.model + ": taller than the kid, no taller than a grown-up");
            }
            foreach (string tall in new[] { "Jogger", "OfficeWorker", "Courier", "Grandad" })
                Assert.AreEqual(LevelBuildKit.AdultNeck, LevelBuildKit.PasserbyNamed(tall).NeckHeight, 0.0001f, tall + ": as tall as the old adult");
            foreach (string shorter in new[] { "Mom", "Shopkeeper" })
                Assert.IsTrue(LevelBuildKit.PasserbyNamed(shorter).NeckHeight < LevelBuildKit.AdultNeck - 0.1f, shorter + ": a little shorter");
            Assert.AreEqual(names.Count, LevelBuildKit.PasserbyModels.Length, "ArtBaker makes a material for each");
            foreach (string model in LevelBuildKit.PasserbyModels) Assert.IsTrue(names.Contains(model), model);
        }

        [Test]
        public void EachComesAlongOnceBeforeAnyComesAgain()
        {
            int n = LevelBuildKit.Passersby.Length;
            var firsts = new HashSet<int>();
            foreach (int salt in new[] { 0, 1, 6, 7, 52411, 81277, 23069, 100002 })
            {
                for (int from = 0; from < 3 * n; from += n - 1)
                {
                    var seen = new HashSet<int>();
                    for (int turn = from; turn < from + n; turn++)
                    {
                        int who = Track.PasserbyTurn(salt, turn, n);
                        Assert.IsTrue(who >= 0 && who < n, "a body of the n");
                        Assert.IsTrue(seen.Add(who), "salt " + salt + ": " + who + " came round again at turn " + turn);
                    }
                }
            }
            for (int salt = 0; salt < 3 * n; salt++) firsts.Add(Track.PasserbyTurn(salt, 0, n));
            Assert.AreEqual(n, firsts.Count, "levels start with different people: each of them first somewhere");
            // (with more passers-by, or fewer, it holds as well: the step is kept prime to the number of bodies)
            for (int m = 1; m <= 12; m++)
                foreach (int salt in new[] { 12345, 9, 100002 })
                {
                    var seen = new HashSet<int>();
                    for (int turn = 0; turn < m; turn++)
                    {
                        int who = Track.PasserbyTurn(salt, turn, m);
                        Assert.IsTrue(who >= 0 && who < m && seen.Add(who), m + " bodies, salt " + salt + ": turn " + turn);
                    }
                }
        }
    }
}
#endif
