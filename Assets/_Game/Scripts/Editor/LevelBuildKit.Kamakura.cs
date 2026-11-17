using System.Collections.Generic;
using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's first level (L01 in the original town), built in Kamakura's look while <see cref="KamakuraLane"/> is set: the
    /// street is the Kamakura kit's (StreetBuilder.Kamakura), and the layout adds the lane's set pieces after the user's KM1-1
    /// pictures: the vending corner, the neighbourhood shrine and its torii, and the Enoden's level crossing by Hase station,
    /// where the kid waits for the tram (Hazards/LevelCrossing).
    /// </summary>
    public static partial class LevelBuildKit
    {
        /// <summary>
        /// True while the original town's L01 is built and the Kamakura kit is there (not its Florida scene): its street is
        /// Kamakura's lane. (The kid's own house stays the one every level starts at and the map draws: HomeInfo.)
        /// </summary>
        public static bool KamakuraLane
        {
            get { return LevelId == "L01" && !Florida && !California && HasKitModel("Kamakura", "HouseKM"); }
        }

        public partial class TrackBuilder
        {
            /// <summary>True while Kamakura's lane is built: the layout adds its set pieces.</summary>
            public bool InKamakuraLane { get { return KamakuraLane; } }

            /// <summary>The railway's corridor across the street (its track and platform): no building stands on it, front or back.</summary>
            public readonly List<Vector2> Railways = new List<Vector2>();

            /// <summary>The rails' gauge: half the distance between their centres (1,067 mm between the rails, plus a rail head).</summary>
            public const float RailHalfGauge = 0.5675f;
            /// <summary>The rails' tops, the same through the street and beyond it, just proud of the crossing's deck.</summary>
            public const float RailTop = 0.03f;

            /// <summary>
            /// The vending corner at x (KM1-1b): a red and a blue drinks machine and the recycling bins against a garden wall at the
            /// back of the footpath, a pine over the wall, the orange corner mirror at the kerb.
            /// </summary>
            public void VendingCorner(float x)
            {
                QuietAreas.Add(new Vector2(x - 3.2f, x + 3.4f));
                var p = new GameObject("VendingCorner").transform;
                p.SetParent(root, false);
                float back = StreetBuilder.PropertyZ;
                StreetBuilder.Row(p, "Street", "BlockWall2", x - 3.0f, x + 3.2f, 0f, back + 1.3f);
                KitModel(p, "Street", "VendingRed", new Vector3(x - 1.7f, 0f, back + 0.5f));
                KitModel(p, "Street", "VendingBlue", new Vector3(x - 0.6f, 0f, back + 0.5f));
                KitModel(p, "Kamakura", "RecycleKM", new Vector3(x + 0.9f, 0f, back + 0.6f));
                KitModel(p, "Kamakura", "MirrorKM", new Vector3(x + 2.6f, 0f, StreetBuilder.PoleZ + 0.1f));
                KitModel(p, "Plants", "GardenPine", new Vector3(x + 1.6f, 0f, back + 3.2f), 30f, 0.9f);
            }

            /// <summary>
            /// The neighbourhood shrine at x (KM1-1c): its torii at the back of the footpath, steps up to the stone base with its
            /// lanterns and the wooden hall; a ginkgo and black pines in its grounds behind.
            /// </summary>
            public void KamakuraShrine(float x)
            {
                QuietAreas.Add(new Vector2(x - 4.8f, x + 4.8f));
                var p = new GameObject("Shrine").transform;
                p.SetParent(root, false);
                float back = StreetBuilder.PropertyZ;
                KitModel(p, "Kamakura", "ShrineKM", new Vector3(x, 0f, back + 1.6f));
                KitModel(p, "Kamakura", "ToriiKM", new Vector3(x, 0f, back + 0.05f));
                KitModel(p, "Plants", "Ginkgo", new Vector3(x - 4.0f, 0f, 11.5f), 40f, 1f);
                KitModel(p, "Plants", "BlackPine", new Vector3(x + 4.6f, 0f, 10.5f), 200f, 1f);
                KitModel(p, "Plants", "BlackPine", new Vector3(x - 1.8f, 0f, 13.5f), 110f, 0.9f);
                KitModel(p, "Plants", "Ginkgo", new Vector3(x + 2.6f, 0f, 14.5f), 300f, 0.95f);
            }

            /// <summary>
            /// The Enoden's level crossing with its track across the street at <paramref name="trackX"/> (KM1-1d and e), and Hase
            /// station's platform beside it beyond the footpath. The track: rails 1,067 mm apart with their tops at one height
            /// all along (<see cref="RailTop"/>), through the street on a deck level with the footpaths (the road rising to it),
            /// beyond it on ballast and sleepers, under its overhead line. On both sides of the tracks a barrier closes the
            /// footpath from behind it and another the road from its kerb; the warning signals stand at the corners. The tram
            /// comes down the track toward the camera, through the crossing and on past the camera, without stopping
            /// (Hazards/LevelCrossing runs it all and stops the kid at the near arm while it is closed).
            /// </summary>
            public void RailCrossing(float trackX)
            {
                float tx = trackX, w = tx - 2.6f, e = tx + 2.6f;
                Coaching.Mark("railcrossing", w - 9f, e);
                QuietAreas.Add(new Vector2(tx - 6.5f, tx + 6.5f));
                Railways.Add(new Vector2(tx - 3f, tx + 5.5f));

                // What never moves, batched; the arms and the tram move.
                var still = new GameObject("RailCrossing").transform;
                still.SetParent(root, false);
                var moving = new GameObject("RailCrossingMoving").transform;
                moving.SetParent(root, false);

                // (the track runs on past the street's ground to where the tram comes from, far up it in the haze)
                float front = StreetBuilder.FrontZ, behind = StreetBuilder.PropertyZ + 0.6f, far = 160f;
                var asphalt = Art.surfaces[ProceduralArt.Surface.Asphalt];
                var gravel = Art.surfaces[ProceduralArt.Surface.Gravel];
                var concrete = Art.surfaces[ProceduralArt.Surface.Concrete];
                Color deckColor = new Color(0.36f, 0.36f, 0.37f), steel = new Color(0.68f, 0.68f, 0.7f);
                const float deckTop = 0.008f;

                // The deck through the street, level with the footpaths (the road's 14 cm rise to it a ramp either side).
                StreetBuilder.Solid(still, "CrossingDeck", new Vector3(tx, deckTop - 0.1f, (front + behind) * 0.5f), new Vector3(3.2f, 0.2f, behind - front), deckColor, asphalt);
                foreach (float s in new[] { -1f, 1f })
                {
                    const float run = 1.5f, drop = 0.14f + deckTop;
                    float edge = tx + s * 1.6f;
                    var ramp = StreetBuilder.Solid(still, "RoadRamp", new Vector3(edge + s * run * 0.5f, -0.14f + drop * 0.5f - 0.05f, (StreetBuilder.RoadNear + StreetBuilder.RoadFar) * 0.5f),
                        new Vector3(run + 0.04f, 0.1f, StreetBuilder.RoadNear - StreetBuilder.RoadFar), new Color(0.5f, 0.5f, 0.52f), asphalt);
                    ramp.transform.rotation = Quaternion.Euler(0f, 0f, -s * Mathf.Atan2(drop, run) * Mathf.Rad2Deg);
                }
                // Beyond the street: the ballast bed and the sleepers as far as the eye picks them out, then the ballast alone.
                StreetBuilder.Patch(still, "Ballast", tx - 1.9f, tx + 1.9f, 0f, behind, far, new Color(0.58f, 0.55f, 0.5f), gravel, 0.006f);
                for (float z = behind + 0.35f; z < 46f; z += 0.65f)
                    StreetBuilder.Solid(still, "Sleeper", new Vector3(tx, 0.012f, z), new Vector3(2f, 0.02f, 0.2f), new Color(0.44f, 0.4f, 0.36f));
                // The rails, end to end.
                foreach (float s in new[] { -1f, 1f })
                    StreetBuilder.Solid(still, "Rail", new Vector3(tx + s * RailHalfGauge, RailTop - 0.04f, (front - 30f + far) * 0.5f), new Vector3(0.07f, 0.08f, far - front + 30f), steel);

                // The overhead line: masts beside the track away from the platform, their arms over it, the contact wire at the
                // tram's pan (4.86 m over its origin) and the catenary wire above.
                float wire = RailTop - 0.03f + 4.86f;
                Color mastGrey = new Color(0.56f, 0.58f, 0.6f), wireDark = new Color(0.22f, 0.2f, 0.19f);
                for (float z = 8f; z < far; z += 22f)
                {
                    float mx = tx - 2.3f;
                    StreetBuilder.Solid(still, "Mast", new Vector3(mx, (wire + 1.2f) * 0.5f, z), new Vector3(0.22f, wire + 1.2f, 0.22f), mastGrey);
                    StreetBuilder.Solid(still, "MastArm", new Vector3((mx + tx + 0.25f) * 0.5f, wire + 0.94f, z), new Vector3(tx + 0.25f - mx, 0.08f, 0.08f), mastGrey);
                    StreetBuilder.Solid(still, "Hanger", new Vector3(tx, wire + 0.45f, z), new Vector3(0.04f, 0.9f, 0.04f), wireDark);
                }
                StreetBuilder.Solid(still, "ContactWire", new Vector3(tx, wire + 0.012f, (front - 30f + far) * 0.5f), new Vector3(0.024f, 0.024f, far - front + 30f), wireDark);
                StreetBuilder.Solid(still, "CatenaryWire", new Vector3(tx, wire + 0.91f, (front - 30f + far) * 0.5f), new Vector3(0.02f, 0.02f, far - front + 30f), wireDark);

                // Hase station's low platform beside the track (its edge 0.1 m from the tram's side), its yellow edge line, the
                // steps up from the footpath with the IC gate at their top, the name board.
                float p0 = tx + 1.25f, p1 = tx + 4.8f, top = RailTop + 0.82f, pz0 = 4.6f, pz1 = 60f;
                StreetBuilder.Solid(still, "Platform", new Vector3((p0 + p1) * 0.5f, top * 0.5f, (pz0 + pz1) * 0.5f), new Vector3(p1 - p0, top, pz1 - pz0), new Color(0.8f, 0.78f, 0.74f), concrete);
                StreetBuilder.Solid(still, "PlatformEdge", new Vector3(p0 + 0.2f, top + 0.004f, (pz0 + pz1) * 0.5f), new Vector3(0.3f, 0.01f, pz1 - pz0), new Color(0.96f, 0.84f, 0.26f));
                for (int k = 0; k < 4; k++)
                {
                    float h = top * (k + 1) / 4f, z0 = 3.4f + 0.3f * k;
                    StreetBuilder.Solid(still, "PlatformStep", new Vector3(p1 - 0.85f, h * 0.5f, (z0 + pz0) * 0.5f), new Vector3(1.7f, h, pz0 - z0), new Color(0.76f, 0.74f, 0.7f), concrete);
                }
                KitModel(still, "Kamakura", "TicketGateKM", new Vector3(p1 - 0.85f, top, 4.9f));
                KitModel(still, "Kamakura", "StationSignKM", new Vector3(p0 + 1.2f, top, 7.2f));

                // The warning signals at the corners behind the footpath, turned toward their road's traffic (and the camera), their
                // lamps to flash. (None on the near side of the road: so close to the camera, they would sweep across the view and
                // hide the lane, docs/LEARNINGS.md E10.)
                var lights = new List<Renderer>();
                CrossingSignal(still, new Vector3(w - 1.6f, 0f, StreetBuilder.PropertyZ + 0.3f), 45f, lights);
                CrossingSignal(still, new Vector3(e + 1.6f, 0f, StreetBuilder.PropertyZ + 0.3f), -45f, lights);

                // The barriers on both sides of the tracks: behind the footpath (its arm closes the footpath to the road's near
                // kerb) and at that kerb (its arm closes the road to its far kerb). Each arm turns on its machine's hub, 0.95 m up.
                var arms = new List<Transform>();
                foreach (float x in new[] { w, e })
                {
                    arms.Add(Barrier(still, moving, new Vector3(x, 0f, StreetBuilder.PropertyZ + 0.75f), "CrossingArmKM"));
                    arms.Add(Barrier(still, moving, new Vector3(x, 0f, StreetBuilder.RoadNear + 0.15f), "CrossingArmRoadKM"));
                }

                // The tram, its middle on the track's centre line and its wheels' treads on the rails (0.03 m above its origin).
                var tram = KitModel(moving, "Kamakura", "TramKM", new Vector3(tx - 1.15f, RailTop - 0.03f, 60f), 90f);

                // Where the kid waits while the crossing is closed: an invisible barrier a step back from the near arm (as people
                // stand back from a crossing's arm; the camera then sees the arms come down across the way, not end on).
                float stopX = w - 1.3f;
                var barrier = Block("CrossingBarrier", new Vector2(stopX, 4f), new Vector2(0.3f, 8f), GroundColor, GroundMat, false).GetComponent<Collider2D>();
                barrier.enabled = false;

                var control = new GameObject("LevelCrossing");
                control.transform.SetParent(root, false);
                control.transform.position = new Vector2(tx, 0f);
                var crossing = control.AddComponent<Hazards.LevelCrossing>();
                crossing.stopX = stopX;
                crossing.farX = e;
                crossing.arms = arms.ToArray();
                crossing.lights = lights.ToArray();
                crossing.barrier = barrier;
                crossing.tram = tram;
                crossing.crossingFarZ = behind;
                crossing.crossingNearZ = StreetBuilder.RoadFar - 0.2f;
                still.gameObject.AddComponent<StaticBatcher>();
            }

            /// <summary>A crossing signal at <paramref name="at"/>, turned <paramref name="yaw"/>, with a red lamp over each of its two lenses.</summary>
            void CrossingSignal(Transform parent, Vector3 at, float yaw, List<Renderer> lights)
            {
                var signal = KitModel(parent, "Kamakura", "CrossingSignalKM", at, yaw);
                if (signal == null) return;
                // (the lenses face the street at 2.53 m, 0.36 m either side of the post, 0.2 m in front of its origin)
                foreach (float sx in new[] { -0.36f, 0.36f })
                {
                    var go = new GameObject("WarningLight");
                    go.transform.SetParent(signal, false);
                    go.transform.localPosition = new Vector3(sx, 2.53f, 0.185f);
                    go.transform.localRotation = Quaternion.identity;
                    var shape = go.AddComponent<CylinderShape>();
                    shape.axis = Vector3.forward;
                    shape.radius = 0.115f;
                    shape.length = 0.03f;
                    shape.sideColor = shape.endColor = new Color(1f, 0.24f, 0.18f);
                    shape.segments = 14;
                    var r = go.GetComponent<MeshRenderer>();
                    r.sharedMaterial = Art.solid;
                    r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                    shape.Rebuild();
                    r.enabled = false;
                    lights.Add(r);
                }
            }

            /// <summary>A barrier machine at <paramref name="at"/> facing the camera, and its arm (upright) on its hub; the arm's pivot.</summary>
            Transform Barrier(Transform still, Transform moving, Vector3 at, string arm)
            {
                KitModel(still, "Kamakura", "CrossingBarrierKM", at);
                var pivot = new GameObject("BarrierArm").transform;
                pivot.SetParent(moving, false);
                pivot.position = at + new Vector3(0f, 0.95f, 0f);
                KitModel(pivot, "Kamakura", arm, pivot.position);
                return pivot;
            }
        }
    }
}
