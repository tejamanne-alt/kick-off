using System.IO;
using DribbleToSchool.Localization;
using DribbleToSchool.Progression;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>
    /// The pencil sketch and the classic cartoon filters are gone (v141, at the user's request, docs/LEARNINGS.md D13): only the
    /// original look and the comic halftone are offered, the camera's pass has no passes of theirs left, and nothing in the menus
    /// or the comic words still draws them.
    /// </summary>
    public class FilterRemovalTests
    {
        static string Read(string relative) { return File.ReadAllText(Path.Combine(Application.dataPath, relative)); }

        [Test]
        public void OnlyTheOriginalAndTheComicAreOffered()
        {
            CollectionAssert.AreEqual(new[] { Filters.Original, Filters.Comic }, Filters.All);
            var en = StringTables.For("en");
            Assert.IsFalse(en.ContainsKey("filter.sketch"), "no card for the sketch");
            Assert.IsFalse(en.ContainsKey("filter.classic"), "no card for the cartoon");
        }

        [Test]
        public void TheCamerasPassHasOnlyTheGradeAndTheComic()
        {
            string shader = Read("_Game/Shaders/PostFX.shader");
            StringAssert.Contains("// 5: comic", shader);
            StringAssert.DoesNotContain("// 6:", shader, "no sketch pass");
            StringAssert.DoesNotContain("DtsCartoon", shader, "no cartoon colour");
            Assert.IsFalse(File.Exists(Path.Combine(Application.dataPath, "_Game/Shaders/DtsCartoon.cginc")));
            Assert.IsFalse(File.Exists(Path.Combine(Application.dataPath, "_Game/Resources/Shaders/CartoonPicture.shader")));
            string fx = Read("_Game/Scripts/World/PostFX.cs");
            StringAssert.DoesNotContain("Sketch", fx);
            StringAssert.DoesNotContain("Classic", fx);
        }

        [Test]
        public void TheComicWordsHaveNoPencilVersion()
        {
            string pops = Read("_Game/Scripts/UI/ComicPops.cs");
            StringAssert.DoesNotContain("pencil", pops);
            StringAssert.Contains("Filters.Chosen == Filters.Comic", pops, "the words show with the comic filter only");
            StringAssert.DoesNotContain("_Hatch", Read("_Game/Resources/Shaders/ComicLettering.shader"));
        }
    }
}
