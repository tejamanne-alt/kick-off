using System;
using DribbleToSchool.Holiday;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The rules of the lead-in: every story level starts at a stop on its route and walks <see cref="Length"/> metres
    /// before the level's own street begins (docs/WORLD_MAP.md, "Every route is one trip, a level is a leg of it"). The
    /// first level of a route starts on the doorstep of the kid's house and its lead-in is the home street (a seam joins it
    /// to the route's own street if that is another chapter's); every other level starts at the stop where the level before
    /// it on the route ended (the bus stop, granny's house, the station...), and its lead-in is already the route's street.
    /// The track builder shifts the start, the walls and the ground back by that much, so a layout keeps its own coordinates
    /// (its start is still x = 0, its hints, signs and obstacles are where they were) and its feasibility audit is unchanged.
    /// Pure arithmetic and text, so the tests and the offline audit harness run the same code as the builder.
    /// </summary>
    public static class HomeLeadInRules
    {
        /// <summary>
        /// Metres of home street before a story level's own start. Change it here (and rebuild): the bells follow. L01's first hint and
        /// walk sign (GreyboxLevels.OutTheDoor, at x = -10.5 and -8) stand in the lead-in 1.5 m and 4 m from the doorstep: move them if it
        /// gets shorter than 11 m (a test and the offline audit say so).
        /// </summary>
        public const float Length = 12f;

        /// <summary>The chapter the lead-in looks like, whatever the level's own chapter: lawns, houses, garden walls and poles.</summary>
        public const int HomeChapter = 1;

        /// <summary>How far before the seam the middle of the route sign stands.</summary>
        public const float SignBeforeSeam = 2.3f;

        /// <summary>
        /// Seconds the walk from the stop the level starts at takes at the kid's walking speed (rounded up), added to every story
        /// level's bell so the bell and the stars mean what they did before the lead-in.
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
        /// The text of the route sign where the lead-in ends: where this level goes ("School ->", "Granny's house ->") and the
        /// route's name ("via Seaside Road"). Signs in the levels are English in every language (see StringTables), so this is
        /// built from the English names (Levels/RouteTable's <c>Stop.signName</c>).
        /// </summary>
        public static string SignText(string destination, string routeName)
        {
            return (string.IsNullOrEmpty(destination) ? "School" : destination) + " ->\nvia " + routeName;
        }

        /// <summary>
        /// Story levels start at a stop (home, or the stop the level before ended at) with a lead-in. The ball-skill challenges
        /// (arenas of their own) and the test track keep their own starts.
        /// </summary>
        public static bool HasLeadIn(bool isLevel, bool isChallenge)
        {
            return isLevel && !isChallenge;
        }
    }
}
