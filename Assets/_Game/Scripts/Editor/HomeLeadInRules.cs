using System;
using DribbleToSchool.Holiday;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The rules of the home lead-in: every story level starts on the doorstep of the kid's house and walks
    /// <see cref="Length"/> metres of home street before the level's own street begins (docs/WORLD_MAP.md, "Every
    /// level starts at home"). The track builder shifts the start, the walls and the ground back by that much, so a
    /// layout keeps its own coordinates (its start is still x = 0, its hints, signs and obstacles are where they were)
    /// and its feasibility audit is unchanged. Pure arithmetic and text, so the tests and the offline audit harness run
    /// the same code as the builder.
    /// </summary>
    public static class HomeLeadInRules
    {
        /// <summary>Metres of home street before a story level's own start. Change it here (and rebuild): the bells follow.</summary>
        public const float Length = 12f;

        /// <summary>The chapter the lead-in looks like, whatever the level's own chapter: lawns, houses, garden walls and poles.</summary>
        public const int HomeChapter = 1;

        /// <summary>How far before the seam the middle of the route sign stands.</summary>
        public const float SignBeforeSeam = 2.3f;

        /// <summary>
        /// Seconds the walk from the front door takes at the kid's walking speed (rounded up), added to every story level's
        /// bell so the school bell and the stars mean what they did before the lead-in.
        /// </summary>
        public static float BellSeconds
        {
            get { return (float)Math.Ceiling(Length / JumpReach.Defaults.runSpeed); }
        }

        /// <summary>
        /// Where the home street ends and the route's own street begins: the layout's start, on the half-unit lattice the
        /// beach's sand is built on (the sand starts exactly there, so its mesh meets the home street's slabs without a gap).
        /// </summary>
        public static float SeamX(float layoutStart)
        {
            return (float)Math.Floor(layoutStart / 0.5 + 0.5) * 0.5f;
        }

        /// <summary>
        /// Where a ground span starts. A layout's first span starts at its walls (x = -8, at the start's back): the lead-in goes on
        /// that span, one piece of ground from the new back wall, so there is no joint in the ground the kid and the ball roll over.
        /// </summary>
        public static float GroundFrom(float spanFrom, bool firstSpan, float layoutMinX, float lead)
        {
            return lead > 0f && firstSpan && spanFrom <= layoutMinX + 0.01f ? spanFrom - lead : spanFrom;
        }

        /// <summary>
        /// Does the lead-in still need ground of its own? True when the layout's first ground span does not start at its walls: the
        /// lead-in is then flat ground from the walls to that span (<paramref name="to"/>), at the first span's height. (Every
        /// story layout starts its ground at its walls, so this is the safety net, and the audit checks that it stays one.)
        /// </summary>
        public static bool GroundBefore(float minX, float firstSpanFrom, out float to)
        {
            to = firstSpanFrom;
            return firstSpanFrom > minX + 0.01f;
        }

        /// <summary>
        /// The text of the route sign where the lead-in ends: "School ->" and the route's name ("via Seaside Road"). Signs in the
        /// levels are English in every language (see StringTables), so this is built from the English route name.
        /// </summary>
        public static string SignText(string routeName)
        {
            return "School ->\nvia " + routeName;
        }

        /// <summary>
        /// Story levels start at home. The ball-skill challenges (arenas of their own) and the test track keep their own starts.
        /// </summary>
        public static bool StartsAtHome(bool isLevel, bool isChallenge)
        {
            return isLevel && !isChallenge;
        }
    }
}
