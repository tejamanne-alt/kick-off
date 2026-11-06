using System.Collections.Generic;
using System.Linq;
using DribbleToSchool.Localization;
using DribbleToSchool.Tutorial;
using DribbleToSchool.UI;
using NUnit.Framework;

namespace DribbleToSchool.Tests
{
    /// <summary>The guided tour of the controls and the Controls page: what they cover and that every text is there.</summary>
    public class ControlsTourTests
    {
        [Test]
        public void TheTourShowsEveryControlAndEndsAtPause()
        {
            var targets = ControlsTour.Steps.Select(s => s.target).ToList();
            foreach (ControlsTour.Target t in System.Enum.GetValues(typeof(ControlsTour.Target)))
                Assert.Contains(t, targets, "the tour shows " + t);
            Assert.AreEqual(ControlsTour.Target.Pause, targets[targets.Count - 1], "it ends at the pause button, where the Controls page is");
            // The stick's two moves, walk first.
            Assert.AreEqual("walk", ControlsTour.Steps[0].key);
            Assert.AreEqual("slide", ControlsTour.Steps[1].key);
        }

        [Test]
        public void EveryStepButTheLastCanBeTried()
        {
            for (int i = 0; i < ControlsTour.Steps.Length; i++)
            {
                var step = ControlsTour.Steps[i];
                bool last = i == ControlsTour.Steps.Length - 1;
                Assert.AreEqual(!last, step.CanTry, step.key);
                Assert.AreEqual(last, step.demo == ControlsTour.Demo.None, step.key + ": the ghost thumb acts out every move");
            }
        }

        [Test]
        public void StepKeysAreDistinct()
        {
            var keys = ControlsTour.Steps.Select(s => s.key).ToList();
            CollectionAssertDistinct(keys);
        }

        [Test]
        public void TheTourIsRememberedWithTheHints()
        {
            // So Reset progress forgets it, and the store screenshots skip it, like every hint.
            Assert.Contains(ControlsTour.SeenId, TutorialHint.AllIds);
        }

        [Test]
        public void EveryTourAndControlsPageTextExistsInEveryLanguage()
        {
            var keys = new List<string> { "tour.step", "tour.next", "tour.skip", "tour.go", "tour.nice", "tour.tryIt", "pause.controls", "settings.controlsGuide" };
            foreach (var step in ControlsTour.Steps)
            {
                keys.Add(step.TitleKey);
                keys.Add(step.BodyKey);
            }
            foreach (var row in ControlsGuide.Rows)
            {
                keys.Add(row.titleKey);
                keys.Add(row.textKey);
            }
            keys.AddRange(ControlsGuide.OtherKeys);

            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (string key in keys)
                {
                    Assert.IsTrue(table.ContainsKey(key), code + ": " + key);
                    Assert.IsFalse(string.IsNullOrEmpty(table[key]), code + ": " + key + " is empty");
                }
                Assert.IsTrue(table["tour.step"].Contains("{0}") && table["tour.step"].Contains("{1}"), code + ": the step counter shows both numbers");
            }
        }

        [Test]
        public void TheCaptionsFitTheirCard()
        {
            // The caption card's body holds three lines of about 58 characters at full size, and shrinks to fit a little
            // more: keep every step's text inside what it can show at its smallest size.
            foreach (string code in Loc.Languages)
            {
                var table = StringTables.For(code);
                foreach (var step in ControlsTour.Steps)
                {
                    Assert.LessOrEqual(table[step.BodyKey].Length, 200, code + ": " + step.BodyKey);
                    Assert.LessOrEqual(table[step.TitleKey].Length, 30, code + ": " + step.TitleKey);
                }
            }
        }

        static void CollectionAssertDistinct(List<string> keys)
        {
            Assert.AreEqual(keys.Count, keys.Distinct().Count(), "no step is listed twice");
        }
    }
}
