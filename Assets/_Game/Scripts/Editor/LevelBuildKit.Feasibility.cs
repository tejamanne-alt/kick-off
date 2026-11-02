using System.Collections.Generic;
using DribbleToSchool.Holiday;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    public static partial class LevelBuildKit
    {
        /// <summary>
        /// Warns if the PlayerTuning asset the scenes use makes the kid jump differently from the numbers the gaps, walls and
        /// layouts were designed for (JumpReach.Defaults): every pit and wall would then be easier or impossible. Called when the
        /// shared assets are loaded.
        /// </summary>
        public static void CheckJumpTuning()
        {
            if (playerTuning == null) return;
            var design = Holiday.JumpReach.Defaults;
            var now = Holiday.JumpReach.From(playerTuning);
            var differences = new List<string>();
            Compare(differences, "runSpeed", design.runSpeed, now.runSpeed);
            Compare(differences, "gravityScale", design.gravityScale, now.gravityScale);
            Compare(differences, "fallGravityMultiplier", design.fallGravityMultiplier, now.fallGravityMultiplier);
            Compare(differences, "jumpVelocity", design.jumpVelocity, now.jumpVelocity);
            Compare(differences, "airJumpVelocity", design.airJumpVelocity, now.airJumpVelocity);
            Compare(differences, "airJumps", design.airJumps, now.airJumps);
            Compare(differences, "coyoteTime", design.coyoteTime, now.coyoteTime);
            Compare(differences, "slideDuration", design.slideDuration, now.slideDuration);
            Compare(differences, "slideHeight", design.slideHeight, now.slideHeight);
            if (differences.Count == 0) return;
            Debug.LogWarning("[Kick Off] The PlayerTuning asset differs from the numbers the levels were designed for (" + string.Join(", ", differences.ToArray())
                + "). The kid now jumps " + Holiday.JumpReach.SingleJump(now).distance.ToString("0.0") + " m (" + Holiday.JumpReach.DoubleJump(now).distance.ToString("0.0")
                + " m with a double jump), so a plain gap may be up to " + Holiday.JumpReach.SafePlainGap(now).ToString("0.0") + " m and a wide one up to "
                + Holiday.JumpReach.SafeWideGap(now).ToString("0.0") + " m (the layouts are made for " + Holiday.JumpReach.SafePlainGap(design).ToString("0.0") + " and "
                + Holiday.JumpReach.SafeWideGap(design).ToString("0.0") + "): update JumpReach.Defaults, then rebuild and read the warnings.");
        }

        static void Compare(List<string> into, string name, float design, float now)
        {
            if (Mathf.Abs(design - now) > 1e-3f) into.Add(name + " " + now + " against " + design);
        }

        public partial class TrackBuilder
        {
            /// <summary>
            /// What this builder laid, for the feasibility check (LevelFeasibility): the ground, the pits and water, the bridges over
            /// them, the walls, platforms, ramps, trampolines, barriers and tunnels. <see cref="Finish"/> reads it back and warns.
            /// </summary>
            public readonly LevelFeasibility Audit = new LevelFeasibility();

            /// <summary>What the warnings call this level or stage ("L05 Puddle Lane", "Holiday Run stage 3").</summary>
            public string AuditName = "";

            /// <summary>
            /// Logs a warning for every hole, step, wall, barrier or roof that the kid cannot get past (see JumpReach for what they can do):
            /// the build-time check that a level is still possible after its layout (or the kid's jump) has been changed.
            /// </summary>
            public void ReportFeasibility()
            {
                var notes = new List<string>();
                foreach (string problem in Audit.Check(notes))
                    Debug.LogWarning("[Kick Off] " + (string.IsNullOrEmpty(AuditName) ? "A level" : AuditName) + " can't be done: " + problem);
            }
        }
    }
}
