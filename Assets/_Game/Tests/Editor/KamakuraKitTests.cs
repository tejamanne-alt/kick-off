using System.IO;
using System.Text.RegularExpressions;
using DribbleToSchool.EditorTools;
using DribbleToSchool.Hazards;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// Kamakura's first level (StreetBuilder.Kamakura, LevelBuildKit.Kamakura) needs its kit: every Kamakura model the lane and
    /// its set pieces place is in the Kamakura kit, and the trees it plants in the Plants kit. Its level crossing
    /// (Hazards/LevelCrossing) is safe as a real one: the tram is never in the street unless the arms are all the way down,
    /// and the arms only go up once the tram is through.
    /// </summary>
    public class KamakuraKitTests
    {
        const string Models = "Assets/_Game/Art/Models/";

        [Test]
        public void EveryKamakuraModelTheLanePlacesIsInTheKit()
        {
            string manifest = File.ReadAllText(Models + "Kamakura/Kamakura.json");
            foreach (string model in StreetBuilder.KamakuraModelsUsed)
            {
                Assert.IsTrue(File.Exists(Models + "Kamakura/" + model + ".fbx"), model + ".fbx is missing");
                Assert.IsTrue(Regex.IsMatch(manifest, "\"" + model + "\"\\s*:"), model + " is not in Kamakura.json");
            }
            Assert.IsTrue(File.Exists(Models + "Kamakura/KamakuraAtlas.png"), "the kit's atlas is missing");
        }

        [Test]
        public void KamakurasTreesAreInThePlantsKit()
        {
            string manifest = File.ReadAllText(Models + "Plants/Plants.json");
            foreach (string model in StreetBuilder.KamakuraPlantsUsed)
            {
                Assert.IsTrue(File.Exists(Models + "Plants/" + model + ".fbx"), model + ".fbx is missing");
                Assert.IsTrue(Regex.IsMatch(manifest, "\"" + model + "\"\\s*:"), model + " is not in Plants.json");
            }
        }

        [Test]
        public void KamakuraIsAKit()
        {
            CollectionAssert.Contains(LevelBuildKit.Kits, "Kamakura");
        }

        static LevelCrossing NewCrossing(out GameObject go)
        {
            go = new GameObject("crossing");
            var c = go.AddComponent<LevelCrossing>();
            c.stopX = 70f;
            c.farX = 75f;
            return c;
        }

        [Test]
        public void TheCrossingIsOpenWithNoTramBeforeTheBellsAndAfterTheCycle()
        {
            GameObject go;
            var c = NewCrossing(out go);
            foreach (float t in new[] { -1f, c.OpenTime, c.OpenTime + 5f })
            {
                var s = c.At(t);
                Assert.IsFalse(s.closed, "open at " + t);
                Assert.IsFalse(s.warning, "quiet at " + t);
                Assert.IsFalse(s.tramShown, "no tram at " + t);
                Assert.AreEqual(0f, s.arm, 1e-4f, "arms up at " + t);
            }
            Object.DestroyImmediate(go);
        }

        [Test]
        public void TheTramIsOnlyInTheStreetWithTheArmsAllTheWayDown()
        {
            GameObject go;
            var c = NewCrossing(out go);
            bool sawTramInStreet = false;
            for (float t = 0f; t < c.OpenTime; t += 0.02f)
            {
                var s = c.At(t);
                Assert.IsTrue(s.closed && s.warning, "closed and ringing all through the cycle (" + t + ")");
                bool inStreet = s.tramShown && s.tramFrontZ < c.crossingFarZ && s.tramFrontZ + c.tramLength > c.crossingNearZ;
                if (!inStreet) continue;
                sawTramInStreet = true;
                Assert.AreEqual(1f, s.arm, 1e-4f, "the arms are all the way down while the tram is in the street (" + t + ")");
            }
            Assert.IsTrue(sawTramInStreet, "the tram goes through the crossing");
            Object.DestroyImmediate(go);
        }

        [Test]
        public void TheTramDoesNotStopAndGoesOnPastTheCamera()
        {
            GameObject go;
            var c = NewCrossing(out go);
            float last = float.MaxValue;
            for (float t = 0f; t < c.OpenTime; t += 0.1f)
            {
                var s = c.At(t);
                Assert.Less(s.tramFrontZ, last, "always moving toward the camera (" + t + ")");
                last = s.tramFrontZ;
            }
            Assert.Greater(c.At(0f).tramFrontZ, 100f, "it comes from far up the track, in the haze");
            float dt = 0.01f, through = (c.TramFrontZ(c.tramAtCrossing - dt) - c.TramFrontZ(c.tramAtCrossing + dt)) / (2f * dt);
            Assert.AreEqual(c.tramSpeed, through, 0.05f, "at the Enoden's speed through the crossing");
            Assert.Less(c.At(c.OpenTime - 0.01f).tramFrontZ + c.tramLength, c.crossingNearZ, "it is through before the arms are all the way up");
            Object.DestroyImmediate(go);
        }
    }
}
