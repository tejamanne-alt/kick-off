using System.IO;
using System.Text.RegularExpressions;
using DribbleToSchool.World;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The filters' colour, as the user asked for it (v134, docs/LEARNINGS.md D12): the classic cartoon in natural colour (no
    /// push toward orange, no browned shadows, a natural blue sky), the pencil sketch in black and white only.
    /// </summary>
    public class FilterLookTests
    {
        static bool Neutral(Vector4 c, float tolerance)
        {
            return Mathf.Abs(c.x - c.y) <= tolerance && Mathf.Abs(c.y - c.z) <= tolerance && Mathf.Abs(c.x - c.z) <= tolerance;
        }

        [Test]
        public void TheCartoonKeepsNaturalColour()
        {
            foreach (var look in new[] { ClassicLook.Classic, ClassicLook.CalmerLook })
            {
                Assert.AreEqual(new Vector4(1f, 1f, 1f, 1f), look.warm, "warm colours are not pushed toward orange");
                Assert.AreEqual(new Vector4(1f, 1f, 1f, 1f), look.shadowWarm, "shadows are not browned");
                Assert.LessOrEqual(look.vibrance, 0.5f, "beige and sand are not lifted to ochre and gold");
                Assert.LessOrEqual(look.saturation, 1.15f);
                Assert.IsTrue(Neutral(look.celInk, 0.02f), "the outline is a neutral black");
                Assert.Greater(look.skyTop.z, look.skyTop.y + 0.1f, "the sky is blue, not turquoise");
            }
        }

        [Test]
        public void TheSketchIsBlackAndWhite()
        {
            var go = new GameObject("PostFXTest");
            try
            {
                var fx = go.AddComponent<PostFX>();
                Assert.IsTrue(Neutral(fx.sketchPaper, 0.005f), "white paper");
                Assert.IsTrue(Neutral(fx.graphite, 0.005f), "grey graphite");
            }
            finally { Object.DestroyImmediate(go); }
            // Whatever a scene saved for the paper and the graphite, the pass returns grey.
            string shader = File.ReadAllText(Path.Combine(Application.dataPath, "_Game/Shaders/PostFX.shader"));
            int sketch = shader.IndexOf("// 6: pencil sketch");
            int next = shader.IndexOf("// 7: classic cartoon", sketch);
            Assert.Greater(sketch, 0);
            string pass = shader.Substring(sketch, next - sketch);
            StringAssert.Contains("return half4(grey, grey, grey, 1);", pass);
            Assert.IsFalse(Regex.IsMatch(pass, @"\(c - tone\)"), "no colour in the wash");
        }
    }
}
