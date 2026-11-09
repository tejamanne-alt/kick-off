using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Levels;
using DribbleToSchool.Presentation;
using DribbleToSchool.World;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The stops' side of the track builder (docs/WORLD_MAP.md, "Every route is one trip, a level is a leg of it"): a level that
    /// is not the first on its route starts at the stop where the level before it ended, and a level that is not the last ends
    /// at the stop where the next one starts. Both build that stop's set piece (StreetBuilder.Stops.cs) at the door the kid starts
    /// from or finishes at, with the people who belong there; a level ending at a stop ends on a chalk line across the footpath in
    /// front of it instead of at the school's arch.
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            struct PendingStop { public Stop stop; public float x, groundTop; public bool goal; }

            /// <summary>
            /// The stops to build once the whole layout (and so the ground, and the beach's sand) is known: a set piece put down
            /// at Start or Goal would read the sand's height from a half-made layout.
            /// </summary>
            readonly List<PendingStop> pendingStops = new List<PendingStop>();

            /// <summary>Where the level that ends at a stop ends: the chalk line in front of the stop (float.MinValue: it ends at the school, see GoalX).</summary>
            public float StopGoalX { get; private set; } = float.MinValue;

            /// <summary>
            /// Called by Start for a level that starts at a stop on its route (not home): the stop's set piece at the door the kid
            /// starts from, and the route sign before the level's own street. The lead-in is the route's own street, so there is no seam.
            /// </summary>
            void BeginAtStop(float layoutStart, float doorX, float groundTop)
            {
                SeamX = HomeLeadInRules.SeamX(layoutStart);
                seamKnown = true;
                ReserveStop(From, doorX, groundTop, false);
                RouteSign(groundTop);
            }

            /// <summary>
            /// The end of a level that stops on the way: the stop's set piece with its door at <paramref name="x"/>, a chalk line
            /// across the footpath just past it, and the goal zone from there on (the kid and the ball both have to cross it).
            /// </summary>
            void StopGoal(float x, float groundTop)
            {
                StopGoalX = x;
                ReserveStop(To, x, groundTop, true);

                const float grounds = 40f;
                var goalGo = new GameObject("GoalZone");
                goalGo.transform.SetParent(root, false);
                goalGo.transform.position = new Vector3(x + 0.4f + grounds * 0.5f, groundTop + 8f, 0f);
                var trigger = goalGo.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(grounds, 20f);
                goalGo.AddComponent<GoalZone>();
            }

            /// <summary>Keeps the street's own lots out of the stop's plot now (the scenery reads the quiet areas) and builds the stop in Finish.</summary>
            void ReserveStop(Stop stop, float x, float groundTop, bool goal)
            {
                if (stop == null) return;
                Vector2 plot = StreetBuilder.StopPlot(stop);
                QuietAreas.Add(new Vector2(x + plot.x, x + plot.y));
                pendingStops.Add(new PendingStop { stop = stop, x = x, groundTop = groundTop, goal = goal });
            }

            /// <summary>Builds the stops the layout reserved (called last by Finish); a failure is logged and the level is still built.</summary>
            void BuildPendingStops()
            {
                foreach (var pending in pendingStops)
                {
                    var p = pending;
                    Attempt("the stop " + p.stop.id, () =>
                    {
                        var holder = new GameObject("Stop_" + p.stop.id).transform;
                        holder.SetParent(root, false);
                        StreetBuilder.StopFront(this, holder, p.stop, p.x, p.groundTop);
                        if (p.goal) FinishLine(holder, p.x + 0.4f, p.groundTop);
                        holder.gameObject.AddComponent<StaticBatcher>();
                        // The people stand outside the static batch (their rigs are posed when the scene starts).
                        StopPeople(root, p.stop, p.x, p.groundTop);
                    });
                }
                pendingStops.Clear();
            }

            /// <summary>A chalk line across the footpath where the level ends, the kind kids draw for a race.</summary>
            void FinishLine(Transform parent, float x, float groundTop)
            {
                float y = Chapter == 3 ? SandHeight(x, 0f) : groundTop;
                Color chalk = new Color(0.97f, 0.97f, 0.95f);
                for (float z = -StreetBuilder.PathHalf + 0.2f; z < StreetBuilder.PathHalf - 0.1f; z += 0.5f)
                    StreetBuilder.Solid(parent, "Chalk", new Vector3(x, y + 0.006f, z + 0.18f), new Vector3(0.1f, 0.012f, 0.36f), chalk);
            }

            /// <summary>
            /// Who waits at a stop: granny at her gate, Sam ready for school at his, a lifeguard by the tower, a builder at the site
            /// gate, grandpa in his allotment, someone at the bus stop and someone off a train at the station. The Pedestrians' adult
            /// and the younger kid's model in their rest pose, dressed for the part; skipped if a model is missing.
            /// </summary>
            void StopPeople(Transform parent, Stop stop, float gx, float groundTop)
            {
                switch (stop.id)
                {
                    case "granny":
                        // (the shopkeeper's model: a woman of about sixty, in a soft grey headscarf)
                        Person(parent, "Granny", "Shopkeeper", gx + 0.2f, groundTop, 2.75f, 60f, new Color(0.72f, 0.58f, 0.82f), new Color(0.36f, 0.32f, 0.46f), new Color(0.78f, 0.78f, 0.82f), 1f);
                        break;
                    case "samsHouse":
                        Person(parent, "Sam", null, gx - 0.15f, groundTop, 2.7f, 40f, new Color(0.3f, 0.66f, 0.42f), new Color(0.22f, 0.24f, 0.4f), new Color(0.32f, 0.2f, 0.12f), 1f);
                        break;
                    case "lifeguard":
                        // (the courier's model: a red polo, yellow shorts, a red cap)
                        Person(parent, "Lifeguard", "Courier", gx + 0.4f, groundTop, 3.2f, 70f, new Color(0.9f, 0.2f, 0.18f), new Color(1f, 0.82f, 0.2f), new Color(0.86f, 0.18f, 0.16f), 1f);
                        break;
                    case "siteOffice":
                        // The courier's model in hi-vis, as the builders on the footpath: the cap in a hard hat's yellow.
                        Person(parent, "Builder", "Courier", gx + 0.3f, groundTop, 2.8f, 55f, new Color(1f, 0.55f, 0.12f), new Color(0.22f, 0.26f, 0.4f), new Color(1f, 0.85f, 0.15f), 1.02f);
                        break;
                    case "allotment":
                        // (Grandad's model: a green cardigan, brown cords, a tweed cap)
                        Person(parent, "Grandpa", "Grandad", gx + 0.9f, groundTop, 2.8f, 50f, new Color(0.45f, 0.58f, 0.38f), new Color(0.45f, 0.36f, 0.28f), new Color(0.46f, 0.42f, 0.32f), 0.98f);
                        break;
                    case "busStop":
                        // (the office worker's model, on his way in: a blue blazer, dark trousers)
                        Person(parent, "Waiting", "OfficeWorker", gx + 2.4f, groundTop, 2.45f, 35f, new Color(0.3f, 0.45f, 0.7f), new Color(0.25f, 0.25f, 0.3f), new Color(0.2f, 0.13f, 0.09f), 1f);
                        break;
                    case "station":
                        // (Mom's model, off on a trip: a sand-coloured jumper, grey trousers)
                        Person(parent, "Traveller", "Mom", gx - 2.2f, groundTop, 2.4f, 25f, new Color(0.85f, 0.75f, 0.55f), new Color(0.3f, 0.3f, 0.36f), new Color(0.15f, 0.1f, 0.08f), 1f);
                        break;
                }
            }

            /// <summary>
            /// A person standing at (x, z), turned <paramref name="yaw"/> degrees from facing along the street toward the camera:
            /// one of the rigged passers-by (<paramref name="grownUp"/>, its model: LevelBuildKit.Passersby, its own height scaled
            /// by <paramref name="scale"/>), or the younger kid's model if that is null. <paramref name="hair"/> is the passer-by's
            /// third part: its hair, cap or headscarf.
            /// </summary>
            void Person(Transform parent, string name, string grownUp, float x, float groundTop, float z, float yaw, Color shirt, Color legwear, Color hair, float scale)
            {
                bool child = grownUp == null;
                Passerby who = child ? null : PasserbyNamed(grownUp);
                string model = "Kid";
                Material look = Art.kid;
                float neck = 0.98f;
                if (!child) GrownUpLook(ref who, out model, out look, out neck);
                neck *= scale;
                float y = Chapter == 3 ? SandHeight(x, z) : groundTop;
                var holder = new GameObject(name).transform;
                holder.SetParent(parent, false);
                holder.position = new Vector3(x, y + 0.6f * neck / 1.3f, z);
                var parts = BuildModelCharacter(holder, model, look, neck, Vector3.zero, false);
                if (parts.rig == null)
                {
                    Object.DestroyImmediate(holder.gameObject);
                    return;
                }
                // The model faces +x whatever its parent's turn (BuildModelCharacter works in world axes): turn the visual afterwards.
                parts.visual.localRotation = Quaternion.Euler(0f, yaw, 0f);
                var dress = parts.outfit as ModelOutfit;
                if (dress == null) return;
                dress.dressOnStart = true;
                dress.shirt = shirt;
                dress.legwear = legwear;
                dress.hair = hair;
            }
        }
    }
}
