using DribbleToSchool.Art;
using DribbleToSchool.Core;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The Florida add-on's own set pieces (so its levels don't just repeat the original's in new streets; GreyboxLevels picks
    /// them while <see cref="LevelBuildKit.Florida"/> is set): a bascule drawbridge over a canal that the kid waits for
    /// (Hazards/Drawbridge), a lawn sprinkler whose spray throws the ball up (the fountain's jets from a sprinkler head), and a
    /// groundskeeper's golf cart driving back and forth that the kid hops on and rides (a moving platform with a cart under it).
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            /// <summary>True while a Florida scene is built: the layouts swap in Florida's set pieces.</summary>
            public bool InFlorida { get { return Florida; } }

            bool sprinklerLook;

            /// <summary>A lawn sprinkler at x: its jets lift the ball as a fountain's do, from a pop-up head on the verge.</summary>
            public void Sprinkler(float x, float groundTop = 0f, float height = 2.8f, float strength = 17f)
            {
                sprinklerLook = true;
                try { Fountain(x, groundTop, height, strength); }
                finally { sprinklerLook = false; }
            }

            /// <summary>
            /// A groundskeeper's golf cart driving between <paramref name="fromX"/> and <paramref name="toX"/> along the street: its
            /// flat bed is a moving platform (0.95 m up) the kid hops onto and rides, with the cart under it. It blocks the way like a
            /// parked car, so the kid times a pass, or chips the ball onto the bed and rides.
            /// </summary>
            public void GolfCart(float fromX, float toX, float groundTop = 0f, float speed = 1.3f)
            {
                const float width = 2.3f, bed = 0.95f;
                var center = new Vector2(fromX + width * 0.5f, groundTop + bed - 0.175f);
                Audit.AddSliding(center.x, center.y, width, toX - fromX - width, 0f);
                Coaching.Mark("golfcart", fromX, toX);
                var go = Block("GolfCart", center, new Vector2(width, 0.35f), PlatformColor, GroundMat, false);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var mp = go.AddComponent<Hazards.MovingPlatform>();
                mp.travel = new Vector2(toX - fromX - width, 0f);
                mp.speed = speed;
                mp.waitTime = 1.2f;
                // The cart itself rides with the platform (a child of it): body, wheels, the bed's sides; no canopy over the bed.
                if (KitModel(go.transform, "Florida", "GolfCartFL", new Vector3(center.x, groundTop, 0f)) == null)
                {
                    Part(go.transform, "CartBody", new Vector3(0f, -0.35f, 0f), new Vector3(width, 0.7f, 1.2f), new Color(0.95f, 0.95f, 0.93f));
                    Part(go.transform, "CartBed", new Vector3(0f, 0.12f, 0f), new Vector3(width, 0.1f, 1.2f), new Color(0.3f, 0.55f, 0.4f));
                }
            }

            /// <summary>
            /// A canal across the street with a bascule drawbridge over it, from <paramref name="fromX"/> to <paramref name="toX"/>
            /// (wider than a double jump, so the kid waits for the bridge): the canal's lose zone and splash, its water and seawalls
            /// running away behind the street (it goes under the road in front through a culvert, its rail along the road's edge),
            /// the two leaves on their hinges, a control tower on each bank, the gate arms and flashing lights on the road.
            /// </summary>
            public void Drawbridge(float fromX, float toX, float top = 0f, float phase = 0f)
            {
                Audit.AddHole(fromX, toX, top, "Canal");
                Audit.AddDrawbridge(fromX, toX, top);
                // No house over the canal, in front or behind (and not as an open area: those get a side street's road).
                Canals.Add(new Vector2(fromX - 0.3f, toX + 0.3f));
                QuietAreas.Add(new Vector2(fromX - 2.8f, toX + 2.8f));
                Coaching.Mark("drawbridge", fromX - 3f, toX);
                float water = top - 1.25f;
                LoseZone("Canal", fromX, toX, top, "lose.splash");
                SplashSurface("Canal", fromX, toX, water, top);

                var canal = new GameObject("Canal").transform;
                canal.SetParent(root, false);
                float cx = (fromX + toX) * 0.5f, w = toX - fromX;
                var concrete = Art.surfaces[ProceduralArt.Surface.Concrete];
                var sea = Art.surfaces[ProceduralArt.Surface.Sea];
                Color wall = new Color(0.8f, 0.78f, 0.74f);
                // The water and the canal's seawalls, from the road's edge back to the far end of the street's ground; the concrete
                // balustrades along its banks behind the street (none on the road: between the camera and the lane it would hide the
                // ball and the kid's legs on the bridge, docs/LEARNINGS.md E10).
                float z0 = StreetBuilder.RoadNear - 0.3f, z1 = StreetBuilder.BackZ, zc = (z0 + z1) * 0.5f, zd = z1 - z0;
                var waterBox = StreetBuilder.Solid(canal, "CanalWater", new Vector3(cx, water - 0.05f, zc), new Vector3(w + 0.6f, 0.1f, zd), Color.white, sea);
                waterBox.faces = MeshBuilder.Faces.Top;
                waterBox.Rebuild();
                foreach (float x in new[] { fromX - 0.15f, toX + 0.15f })
                    StreetBuilder.Solid(canal, "Seawall", new Vector3(x, (top - 0.02f + water - 1f) * 0.5f, zc), new Vector3(0.3f, top - 0.02f - water + 1f, zd), wall, concrete);
                StreetBuilder.Solid(canal, "CanalBed", new Vector3(cx, water - 1.2f, zc), new Vector3(w, 0.2f, zd), new Color(0.2f, 0.3f, 0.3f));
                // Up the canal: a neighbour's dock with a boat on its lift on each bank, and the No Wake sign on its pile.
                float dockY = water + 0.3f;
                if (w >= 4f)
                {
                    KitModel(canal, "Florida", "DockFL", new Vector3(fromX + 1.5f, dockY, 12f));
                    KitModel(canal, "Florida", "DockFL", new Vector3(toX - 1.5f, dockY, 24f), 180f);
                }
                KitModel(canal, "Florida", "SignNoWakeFL", new Vector3(cx + 0.6f, water - 0.35f, 6.2f));
                KitModel(canal, "Florida", "CanalRailFL", new Vector3(fromX - 0.35f, top, 8.6f), -90f);
                KitModel(canal, "Florida", "CanalRailFL", new Vector3(toX + 0.35f, top, 8.6f), 90f);

                // The leaves: each a kinematic body turned about its hinge at a bank, its deck reaching to the middle.
                float leafLen = w * 0.5f - 0.03f;
                Rigidbody2D left = Leaf("LeafLeft", fromX, top, leafLen, 1f);
                Rigidbody2D right = Leaf("LeafRight", toX, top, leafLen, -1f);

                // The control towers on the banks behind the street, their lights; the footpath's gates a little back from each bank,
                // their posts at the back of the lane and their arms swinging down ACROSS the path, toward the camera, as a real
                // bridge's gates cross the road (they used to fall along the street behind the kid, so they read as a fence the kid
                // walked in front of, and stopped nothing: docs/LEARNINGS.md E15). An arm ends at the lane's front edge (nothing tall
                // between the camera and the lane, E10), and while it is down a blocker at its post holds the kid and the ball back
                // from the hinge, where the rising leaf would pass through them.
                var lights = new System.Collections.Generic.List<Renderer>();
                var arms = new System.Collections.Generic.List<Transform>();
                var blocks = new System.Collections.Generic.List<Collider2D>();
                float armLength = StreetBuilder.PathHalf * 2f + 0.4f;
                foreach (float bank in new[] { fromX - 1.6f, toX + 1.6f })
                {
                    if (KitModel(canal, "Florida", "DrawTowerFL", new Vector3(bank, top, StreetBuilder.PathHalf + 1.4f)) == null)
                        StreetBuilder.Solid(canal, "Tower", new Vector3(bank, top + 2f, StreetBuilder.PathHalf + 2.4f), new Vector3(2.2f, 4f, 2.2f), new Color(0.92f, 0.9f, 0.84f));
                    // The traffic signal for the path: a mast just before the gate (on the side the kid comes from), its black head
                    // with two red lamps side by side facing the street, which flash in turn while the bridge is not down. (The
                    // lamps used to be loose red discs on the tender's tower wall.)
                    float side = bank < cx ? -1f : 1f;
                    float mastX = bank + side * 1.35f, mastZ = StreetBuilder.PathHalf + 0.35f;
                    Color black = new Color(0.08f, 0.08f, 0.09f), steel = new Color(0.42f, 0.43f, 0.45f);
                    StreetBuilder.Solid(canal, "SignalMast", new Vector3(mastX, top + 1.45f, mastZ), new Vector3(0.1f, 2.9f, 0.1f), steel);
                    StreetBuilder.Solid(canal, "SignalHead", new Vector3(mastX, top + 2.7f, mastZ - 0.1f), new Vector3(0.66f, 0.34f, 0.18f), black);
                    StreetBuilder.Solid(canal, "SignalBackplate", new Vector3(mastX, top + 2.7f, mastZ - 0.01f), new Vector3(0.86f, 0.5f, 0.03f), black);
                    foreach (float dx in new[] { -0.16f, 0.16f })
                    {
                        var lens = new Vector3(mastX + dx, top + 2.7f, mastZ - 0.2f);
                        StreetBuilder.Solid(canal, "SignalVisor", lens + new Vector3(0f, 0.12f, -0.07f), new Vector3(0.24f, 0.03f, 0.16f), black);
                        Lens(canal, lens + new Vector3(0f, 0f, 0.004f), new Color(0.28f, 0.06f, 0.05f), true);
                        lights.Add(Lens(canal, lens, new Color(1f, 0.22f, 0.18f), false));
                    }
                    // The gate's post, and its arm pivoting at the post's top (turned so that its fall, about its own x, is along the street).
                    var post = new Vector3(bank + (bank < cx ? -0.8f : 0.8f), top, StreetBuilder.PathHalf + 0.3f);
                    if (KitModel(canal, "Florida", "GatePostFL", post) == null)
                        StreetBuilder.Solid(canal, "GatePost", post + new Vector3(0f, 0.45f, 0f), new Vector3(0.36f, 0.9f, 0.36f), new Color(0.35f, 0.36f, 0.38f));
                    // (Upright at rest; the drawbridge turns it about its own x, which sends its tip toward the camera, -z.)
                    var armRoot = new GameObject("GateArm");
                    armRoot.transform.SetParent(canal, false);
                    armRoot.transform.position = post + new Vector3(0f, 0.9f, 0f);
                    armRoot.transform.rotation = Quaternion.identity;
                    float native = KitSize("Florida", "GateArmFL").y;
                    if (KitModel(armRoot.transform, "Florida", "GateArmFL", armRoot.transform.position, 0f, native > 1f ? armLength / native : 1f) == null)
                        Part(armRoot.transform, "Arm", new Vector3(0f, armLength * 0.5f, 0f), new Vector3(0.12f, armLength, 0.12f), new Color(0.95f, 0.95f, 0.93f));
                    arms.Add(armRoot.transform);
                    // The blocker: taller than a double jump reaches, so the way on while the lights flash is to wait. One-way: it
                    // stops what comes toward the canal from its own side, never what is leaving the bridge (a kid already over when
                    // the arms fall walks out past the far gate).
                    var block = new GameObject("GateBlock");
                    block.transform.SetParent(canal, false);
                    block.transform.position = new Vector2(post.x, top + 1.3f);
                    var wallCol = block.AddComponent<BoxCollider2D>();
                    wallCol.size = new Vector2(0.24f, 2.6f);
                    wallCol.sharedMaterial = GroundMat;
                    wallCol.usedByEffector = true;
                    var oneWay = block.AddComponent<PlatformEffector2D>();
                    oneWay.useOneWay = true;
                    oneWay.surfaceArc = 160f;
                    oneWay.rotationalOffset = bank < cx ? 90f : -90f;     // its face toward the street it guards (left gate: the left)
                    wallCol.enabled = false;
                    blocks.Add(wallCol);
                }

                var bridgeGo = new GameObject("Drawbridge");
                bridgeGo.transform.SetParent(root, false);
                bridgeGo.transform.position = new Vector2(cx, top);
                var bridge = bridgeGo.AddComponent<Hazards.Drawbridge>();
                bridge.leftLeaf = left;
                bridge.rightLeaf = right;
                bridge.arms = arms.ToArray();
                bridge.gateBlocks = blocks.ToArray();
                bridge.lights = lights.ToArray();
                bridge.phaseOffset = phase;
            }

            /// <summary>One leaf of the drawbridge: its hinge at (hingeX, top), reaching <paramref name="length"/> toward the other bank.</summary>
            Rigidbody2D Leaf(string name, float hingeX, float top, float length, float toward)
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(hingeX, top);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<BoxCollider2D>();
                col.size = new Vector2(length, 0.3f);
                col.offset = new Vector2(toward * length * 0.5f, -0.15f);
                col.sharedMaterial = GroundMat;
                // Its deck (the kit's leaf, 2.5 m long, scaled to fit), or a plain slab. The right one is mirrored along its length,
                // not turned round: turned, its railing came round to the front of the deck, between the camera and the kid
                // (docs/LEARNINGS.md E10, E15).
                var leaf = KitModel(go.transform, "Florida", "DrawLeafFL", new Vector3(hingeX, top, 0f));
                if (leaf != null) leaf.localScale = new Vector3(toward * length / 2.5f, 1f, 1f);
                else Part(go.transform, "Deck", new Vector3(toward * length * 0.5f, -0.15f, 0f), new Vector3(length, 0.3f, 3.6f), new Color(0.62f, 0.64f, 0.66f));
                return body;
            }

            /// <summary>
            /// A signal lens facing the street: the dark one is always there (the lamp when off); the lit one is switched on and off by
            /// the drawbridge.
            /// </summary>
            static Renderer Lens(Transform parent, Vector3 at, Color color, bool on)
            {
                var go = new GameObject(on ? "SignalLens" : "WarningLight");
                go.transform.SetParent(parent, false);
                go.transform.position = at;
                var shape = go.AddComponent<CylinderShape>();
                shape.axis = Vector3.forward;
                shape.radius = 0.1f;
                shape.length = 0.03f;
                shape.sideColor = shape.endColor = color;
                shape.segments = 14;
                var r = go.GetComponent<MeshRenderer>();
                // (The lit lens is unlit, Sprites/Default with the lens's own colour: a lamp, not a red plastic disc in the shade.)
                r.sharedMaterial = on ? Art.solid : (Art.wire != null ? Art.wire : Art.solid);
                shape.Rebuild();
                r.enabled = on;
                return r;
            }
        }
    }
}
