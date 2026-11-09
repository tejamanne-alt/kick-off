using System.Collections.Generic;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The pier on the course (California's beach): its stairs stand across the kid's lane, so the kid dribbles the ball up
    /// one flight onto the landing in front of the pier's deck and down the other. The track builder lays the ground the kid
    /// and the ball really move on (one smooth slope up, the landing, one down: the steps' nosings, which is what a foot or a
    /// ball rides over); StreetBuilder.Coast builds the pier and the stairs over it (World/PierStairs, on the course).
    /// The flights are gentler than the pier's other stairs (about 21 degrees: risers of 13.5 cm on 35 cm treads), as the
    /// game's ramps and dunes are, so a run keeps its pace up them and a kid can stop on them and go on.
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            /// <summary>A pier the course climbs: from the first step's foot, up to the landing (top to topEnd), down to the last step's foot (end).</summary>
            public struct PierClimbSpec
            {
                public float foot, top, topEnd, end, groundTop, rise, going, riserAim;
                public float Centre { get { return (top + topEnd) * 0.5f; } }
                public float Landing { get { return topEnd - top; } }
            }

            /// <summary>The deck over the lane, a tread's depth, the riser aimed for, and the landing's length along the lane.</summary>
            public const float ClimbRise = 2.3f, ClimbGoing = 0.35f, ClimbRiser = 0.135f, ClimbLanding = 2f;
            /// <summary>No mid-landing on the course: one even slope each way.</summary>
            public const int ClimbSplitOver = 99;

            readonly List<PierClimbSpec> pierClimbs = new List<PierClimbSpec>();

            /// <summary>The piers the course climbs (StreetBuilder.Coast builds them).</summary>
            public IList<PierClimbSpec> PierClimbs { get { return pierClimbs; } }

            /// <summary>True when the level has a pier behind its lane (<see cref="SeasidePier"/>).</summary>
            public bool HasSeasidePier { get; private set; }

            /// <summary>
            /// A pier out to sea behind the lane, somewhere along this level's beach (California only; StreetBuilder.Coast puts it
            /// clear of the stops, with its stairs down to the sand on either side). Only a few levels have one, so the seaside
            /// walk passes two piers, not one on every leg: this one and Low Tide's, which the course climbs (<see cref="PierClimb"/>).
            /// The original levels have none, so it changes nothing there.
            /// </summary>
            public void SeasidePier()
            {
                HasSeasidePier = true;
            }

            /// <summary>True where a level can put a pier on its course: the California beach, with the Coast kit's pier.</summary>
            public bool CanClimbPier { get { return California && Chapter == 3 && HasKitModel("Coast", "PierSpan"); } }

            /// <summary>One flight's run along the lane, from its foot to the landing (the nosings' line meets the sand a tread past the last step).</summary>
            public static float ClimbRun
            {
                get { return PierStairs.PlanFor(ClimbRise, ClimbGoing, ClimbRiser, ClimbSplitOver).risers * ClimbGoing; }
            }

            /// <summary>How far a pier climb runs along the lane: up, over the landing, down.</summary>
            public static float PierClimbLength { get { return 2f * ClimbRun + ClimbLanding; } }

            /// <summary>
            /// The pier across the lane from <paramref name="foot"/>: up its stairs, over the landing, down to the sand. Returns
            /// where the last step's foot meets the sand. The lane must be flat there (at <paramref name="groundTop"/>) and clear.
            /// </summary>
            public float PierClimb(float foot, float groundTop = 0f)
            {
                float run = ClimbRun, top = foot + run, topEnd = top + ClimbLanding, end = topEnd + run, deck = groundTop + ClimbRise;
                Audit.AddRamp(foot, groundTop, top, deck);
                Audit.AddLedge(top, topEnd, deck, groundTop);
                Audit.AddRamp(topEnd, deck, end, groundTop);
                // One collider, so nothing catches on a seam: up the nosings, across the landing, down; solid underneath.
                var go = new GameObject("PierClimb");
                go.transform.SetParent(root, false);
                var poly = go.AddComponent<PolygonCollider2D>();
                float under = groundTop - 0.6f;
                poly.points = new[]
                {
                    new Vector2(foot, groundTop), new Vector2(top, deck), new Vector2(topEnd, deck), new Vector2(end, groundTop),
                    new Vector2(end, under), new Vector2(foot, under),
                };
                poly.sharedMaterial = GroundMat;
                pierClimbs.Add(new PierClimbSpec
                {
                    foot = foot, top = top, topEnd = topEnd, end = end, groundTop = groundTop, rise = ClimbRise,
                    going = ClimbGoing, riserAim = ClimbRiser,
                });
                return end;
            }

            /// <summary>The height of the climb's walking line (the nosings) at x: what the kid's feet and the ball ride on.</summary>
            public static float ClimbLine(PierClimbSpec climb, float x)
            {
                if (x <= climb.foot || x >= climb.end) return climb.groundTop;
                if (x < climb.top) return climb.groundTop + climb.rise * (x - climb.foot) / (climb.top - climb.foot);
                if (x <= climb.topEnd) return climb.groundTop + climb.rise;
                return climb.groundTop + climb.rise * (climb.end - x) / (climb.end - climb.topEnd);
            }
        }
    }
}
