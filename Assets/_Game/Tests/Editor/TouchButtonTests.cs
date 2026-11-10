using DribbleToSchool.UI.Kit;
using NUnit.Framework;
using UnityEngine;

namespace DribbleToSchool.Tests
{
    /// <summary>The text on a touch button (KICK's name and its "hold to control" line) stays inside the round disc.</summary>
    public class TouchButtonTests
    {
        static void AssertInsideDisc(Rect area, string what)
        {
            var centre = new Vector2(0.5f, 0.5f);
            foreach (var corner in new[] { area.min, area.max, new Vector2(area.xMin, area.yMax), new Vector2(area.xMax, area.yMin) })
                Assert.LessOrEqual((corner - centre).magnitude, TouchButton.TextReach + 1e-4f, what + "'s corner " + corner + " reaches the rim");
            Assert.Less(TouchButton.TextReach, 0.5f, "the reach must stay inside the circle");
        }

        [Test]
        public void TheLabelAndTheHintStayInsideTheCircle()
        {
            AssertInsideDisc(TouchButton.HintLabelArea, "the label");
            AssertInsideDisc(TouchButton.HintArea, "the hint");
            Assert.LessOrEqual(TouchButton.HintArea.yMax, TouchButton.HintLabelArea.yMin + 1e-4f, "the hint sits under the label");
        }
    }
}
