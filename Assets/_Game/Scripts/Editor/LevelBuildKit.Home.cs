using System;
using System.Collections.Generic;
using DribbleToSchool.Art;
using DribbleToSchool.Levels;
using DribbleToSchool.Localization;
using DribbleToSchool.Presentation;
using DribbleToSchool.World;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The home lead-in's side of the builder kit: every story level starts on the doorstep of the kid's house and walks
    /// <see cref="HomeLeadIn"/> metres of home street (the first chapter's look, whatever the level's own) to a sign with the
    /// route's name, where the level's own street begins (docs/WORLD_MAP.md, "Every level starts at home"). The layouts do not
    /// change: the track builder shifts the walls, the start and the ground back by the lead-in, so a layout's own coordinates,
    /// its hints, signs and obstacles, and its feasibility audit stay as they were.
    /// </summary>
    public static partial class LevelBuildKit
    {
        /// <summary>Metres of home street before a story level's own start (HomeLeadInRules.Length: about three seconds of walking).</summary>
        public const float HomeLeadIn = HomeLeadInRules.Length;

        /// <summary>
        /// Does this level start at a stop with a lead-in? Every story level does (the first of each route at home, the others at
        /// the stop where the level before them ended); the ball-skill challenges and the test track (no definition) keep their own
        /// starts. Read it before the new scene is made: creating a scene can unload a definition nothing references.
        /// </summary>
        public static bool HasLeadIn(LevelDefinition def)
        {
            return HomeLeadInRules.HasLeadIn(def != null, def != null && def.isChallenge);
        }

        /// <summary>Does this level start on the kid's doorstep (the first level of its route)?</summary>
        public static bool StartsAtHome(LevelDefinition def)
        {
            if (!HasLeadIn(def)) return false;
            var from = RouteTable.From(def.levelId);
            return from == null || from.IsHome;
        }

        /// <summary>The English name of the route a level is on ("Seaside Road"), or null if it is on none.</summary>
        public static string RouteNameOf(LevelDefinition def)
        {
            var route = def != null ? RouteTable.Of(def.levelId) : null;
            string name;
            return route != null && StringTables.For("en").TryGetValue(route.NameKey, out name) ? name : null;
        }

        /// <summary>
        /// Builds with another chapter's look and puts the level's own back afterwards: <see cref="Chapter"/> and <see cref="Theme"/>
        /// are statics that the street builders read in about fifteen places (surfaces, scenery, side streets, poles...).
        /// </summary>
        public static void AsChapter(int chapter, Action build)
        {
            int savedChapter = Chapter;
            ChapterTheme savedTheme = Theme;
            Chapter = chapter;
            Theme = ThemeFor(chapter);
            try { build(); }
            finally
            {
                Chapter = savedChapter;
                Theme = savedTheme;
            }
        }

        /// <summary>The font of the sign boards (the house number plate uses it too); null before the shared assets are loaded.</summary>
        internal static Font SignFont { get { return signFont; } }

        public partial class TrackBuilder
        {
            /// <summary>
            /// Metres of home street before the layout's own start. 0 (the default) for the challenges, the test track, the Holiday
            /// Run's stages and the menu's street; <see cref="HomeLeadIn"/> for a story level (BuildScene sets it before the layout runs).
            /// </summary>
            public float LeadIn { get; set; }

            /// <summary>The English name of the route the level is on ("Seaside Road"), for the sign where the lead-in ends; null: no sign.</summary>
            public string RouteName { get; set; }

            /// <summary>
            /// The stop the level starts at (Levels/RouteTable.From): home for the first level of a route, else the stop the level
            /// before it ended at. Null (as home) for a level on no route.
            /// </summary>
            public Stop From { get; set; }

            /// <summary>
            /// The stop the level ends at (Levels/RouteTable.To): the school for the last level of a route, else the stop the next
            /// level starts at; <see cref="Goal"/> builds the one it is. Null (as the school) for a level on no route.
            /// </summary>
            public Stop To { get; set; }

            /// <summary>Does the level start on the kid's doorstep (its lead-in is the home street)?</summary>
            public bool StartsAtHome { get { return From == null || From.IsHome; } }

            /// <summary>Does the level end at the school's arch (else at a stop on the way)?</summary>
            public bool EndsAtSchool { get { return To == null || To.IsSchool; } }

            /// <summary>Where the home street ends and the route's own street begins: the layout's start (known once Start has been called).</summary>
            public float SeamX { get; private set; }

            bool seamKnown;

            /// <summary>Where the layout put its back wall (Walls), before the lead-in moved the real one: the first ground span starts there.</summary>
            float layoutMinX = float.NaN;

            /// <summary>
            /// True for a level that starts at home and whose own street is another chapter's: the home street (chapter 1) runs to the
            /// seam, with its own slabs and scenery, and the route's street begins there. A chapter-1 level is one street with no seam.
            /// </summary>
            public bool HasSeam { get { return LeadIn > 0f && seamKnown && StartsAtHome && Chapter != HomeLeadInRules.HomeChapter; } }

            /// <summary>
            /// Called by Start for a level that begins at home: the kid's house and garden at the doorstep, the route sign
            /// before the seam, and (where the home street meets another chapter's) a kerb and a pair of bollards across the way.
            /// </summary>
            void BeginAtHome(float layoutStart, float doorX, float groundTop)
            {
                SeamX = HomeLeadInRules.SeamX(layoutStart);
                seamKnown = true;
                Attempt("the home front", () => HomeFront(doorX, groundTop));
                RouteSign(groundTop);
                if (HasSeam) Attempt("the seam's kerb and bollards", () => SeamDressing(SeamX, groundTop));
            }

            /// <summary>The route sign before the level's own street begins: where the level goes, and by which route.</summary>
            void RouteSign(float groundTop)
            {
                if (string.IsNullOrEmpty(RouteName)) return;
                string destination = To != null ? To.signName : null;
                Sign(HomeLeadInRules.SignText(destination, RouteName), new Vector2(SeamX - HomeLeadInRules.SignBeforeSeam, groundTop + 2.9f));
            }

            /// <summary>Builds one piece of the lead-in; if it fails the level is still built without it and the problem is logged (as the Holiday Run's stages do).</summary>
            void Attempt(string what, Action build)
            {
                try
                {
                    build();
                }
                catch (Exception e)
                {
                    Debug.LogError("[Kick Off] " + AuditName + ": couldn't build " + what + ": " + e);
                }
            }

            /// <summary>
            /// The kid's house and its front garden, the same in every level and in the same first-chapter look in all of them: the
            /// Buildings kit's HouseGable with a warm red front door, a garden gate between two pillars with its number, a picket
            /// fence and hedges, a path, flower beds and pots, a bike, the bins, a post box, and a parent standing at the door.
            /// <paramref name="x"/> is the gate and the doorstep, where the kid starts, facing the street.
            /// </summary>
            public void HomeFront(float x, float groundTop = 0f)
            {
                var holder = new GameObject("HomeFront").transform;
                holder.SetParent(root, false);
                holder.gameObject.AddComponent<StaticBatcher>();
                // The street's own houses, walls and poles stay out of the plot.
                QuietAreas.Add(new Vector2(x, x) + StreetBuilder.HomePlot);
                AsChapter(HomeLeadInRules.HomeChapter, () =>
                {
                    StreetBuilder.HomeFront(holder, x, groundTop);
                    HomeParent(holder, x, groundTop);
                });
            }

            /// <summary>
            /// A parent standing on the top step at the front door, turned a little toward the street: Mom (LevelBuildKit.Passersby)
            /// in her rest pose (arms down), dressed in the quiet colours of the house; skipped if the model or its bones are missing.
            /// </summary>
            void HomeParent(Transform parent, float gateX, float groundTop)
            {
                Passerby mom = PasserbyNamed("Mom");
                string model;
                Material look;
                float neck;
                GrownUpLook(ref mom, out model, out look, out neck);
                const float topStep = 0.30f;                            // the HouseGable's door sill and top step
                var holder = new GameObject("Parent").transform;
                holder.SetParent(parent, false);
                holder.position = new Vector3(gateX, groundTop + topStep + 0.6f * neck / 1.3f, StreetBuilder.HomeHouseZ - 0.16f);
                var parts = BuildModelCharacter(holder, model, look, neck, Vector3.zero, false);
                if (parts.rig == null)
                {
                    Object.DestroyImmediate(holder.gameObject);
                    return;
                }
                // The model faces +x whatever its parent's turn (BuildModelCharacter works in world axes): turn the visual afterwards,
                // toward the camera and a little toward the street.
                parts.visual.localRotation = Quaternion.Euler(0f, 55f, 0f);
                var dress = (ModelOutfit)parts.outfit;
                dress.dressOnStart = true;
                dress.shirt = new Color(0.92f, 0.66f, 0.34f);
                dress.legwear = new Color(0.27f, 0.32f, 0.46f);
                dress.hair = new Color(0.2f, 0.13f, 0.09f);
            }

            /// <summary>
            /// Where the home street meets the route's own: a kerb stone across the footpath over the joint of the two streets' ground, and a
            /// pair of bollards either side of the post line (visual only; the kid walks straight through at z = 0).
            /// </summary>
            void SeamDressing(float x, float groundTop)
            {
                var holder = new GameObject("RouteSeam").transform;
                holder.SetParent(root, false);
                float lane = StreetBuilder.PathHalf * 2f;
                StreetBuilder.Solid(holder, "SeamKerb", new Vector3(x, groundTop + 0.015f, 0.1f), new Vector3(0.45f, 0.03f, lane + 0.2f),
                    new Color(0.86f, 0.84f, 0.8f), Art.surfaces[ProceduralArt.Surface.Kerb]);
                foreach (float dx in new[] { -0.55f, 0.55f })
                    StreetBuilder.Model(holder, "Street", "Bollard", x + dx, groundTop, StreetBuilder.PathHalf + 0.22f);
                holder.gameObject.AddComponent<StaticBatcher>();
            }

            /// <summary>
            /// The safety net for the lead-in's ground. A layout's first ground span starts at its walls, and Ground puts the lead-in on that
            /// span (HomeLeadInRules.GroundFrom: one piece of ground, no joint); should a layout's first span start anywhere else, the stretch
            /// from the walls to it is flat ground here, at that span's height. Called first by Finish, before the signs are planted.
            /// </summary>
            void AddLeadInGround()
            {
                if (LeadIn <= 0f || groundSpans.Count == 0) return;
                float first = float.MaxValue, top = 0f;
                foreach (var g in groundSpans)
                    if (g.from < first) { first = g.from; top = g.top; }
                float to;
                if (HomeLeadInRules.GroundBefore(MinX, first, out to)) Ground(MinX, to, top);
            }

            /// <summary>The ground spans (sorted) from <paramref name="x"/> on: those wholly before it dropped, the one that crosses it cut there.</summary>
            static List<GroundSpan> ClippedFrom(List<GroundSpan> spans, float x)
            {
                var clipped = new List<GroundSpan>();
                foreach (var s in spans)
                {
                    if (s.to <= x + 0.01f) continue;
                    var c = s;
                    c.from = Mathf.Max(s.from, x);
                    clipped.Add(c);
                }
                return clipped;
            }

            /// <summary>
            /// The home street's slabs from <paramref name="from"/> to the seam: chapter 1's road, footpath and the strip behind it, level
            /// at <paramref name="top"/>, open at the world's end and closed at the seam, where the route's own slabs begin.
            /// </summary>
            void BuildHomeSlabs(Transform slabs, float from, float seam, float top, float roadTop)
            {
                StreetBuilder.Slab(slabs, "HomeRoad", from, seam, roadTop, false, true, StreetBuilder.Part.Front);
                SlabAvoidingSideStreets(slabs, "HomeFootpath", from, seam, top, false, true, StreetBuilder.Part.Lane);
                SlabAvoidingSideStreets(slabs, "HomeVerge", from, seam, top, false, true, StreetBuilder.Part.Back);
            }
        }
    }
}
