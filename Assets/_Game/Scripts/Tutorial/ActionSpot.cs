using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Tutorial
{
    /// <summary>
    /// A stretch of a level where something special has to be done (slide under, chip it over a wall, wait for the green
    /// man...): <see cref="action"/> names the how-to the HUD's coach shows at the top of the screen as the kid comes up to
    /// it (UI/ActionCoach, UI/CoachCatalog). The level builder places one for each obstacle and hazard (Editor/CoachPlan).
    /// </summary>
    public class ActionSpot : MonoBehaviour
    {
        [Tooltip("The how-to to show: an id of UI/CoachCatalog (slide, chip, gap, crossing...).")]
        public string action = "slide";
        [Tooltip("Where it starts and ends along the level (world x).")]
        public float fromX, toX;

        static readonly List<ActionSpot> all = new List<ActionSpot>();

        /// <summary>The spots in the loaded level that are switched on.</summary>
        public static IList<ActionSpot> All { get { return all; } }

        void OnEnable() { if (!all.Contains(this)) all.Add(this); }

        void OnDisable() { all.Remove(this); }
    }
}
