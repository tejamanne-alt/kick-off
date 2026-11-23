using System.Collections.Generic;
using System.Text;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Nothing the ball can see is a ghost (docs/LEARNINGS.md E18): once a level is laid, every surface of every piece that crosses
    /// the ball's plane (|z| &lt;= 0.17 m round z 0) is found from its mesh, and wherever it is not already on one of the level's
    /// colliders, ball-only colliders (World/BallShell) are added there, as thin boxes along it. The sweeper's cab, a golf cart's
    /// body, a canopy's thickness, a scooter's handlebar, a crane load's beams: the ball bounces off what it sees. They go on the
    /// piece's own moving body when it has one (the sweeper's cab rides with the sweeper; a drawbridge leaf's turns with it).
    ///
    /// Left alone, by design: pickups and zones (a trigger is their only collider), animals, plants and people (the ball goes past
    /// them), water, rain and the street's own slabs; a surface lying within 0.12 m above a collider (a kerb's lip, a table's
    /// cloth, a base plate: the ball rolls over those); anything that moves on its own without a body (a crossing's bars, a crane's
    /// trolley: a collider left where it was built would be an invisible wall); and decoration with no collider at all unless it
    /// is a kit model. The kid's colliders are the designed ones, so no jump, slide or ride changes.
    ///
    /// Each level's build logs what was shelled and what was left out (the strict audit of the pass-through, every level, both
    /// cities). Cost: thin static boxes (or a few more shapes on a moving body), only where a surface lacked one.
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            /// <summary>A surface this close to a collider counts as on it (the ball meets the collider first).</summary>
            const float ShellMargin = 0.06f;
            /// <summary>A surface lying this little above a collider is a lip the ball rolls over.</summary>
            const float ShellLip = 0.12f;
            /// <summary>Wider than this along the street, a mesh is the street itself (its slabs, walls, hills), not a piece.</summary>
            const float ShellMaxWidth = 40f;

            /// <summary>Components of things that only look and never move: a mesh under one of these may be shelled.</summary>
            static readonly HashSet<string> StillTypes = new HashSet<string>
            {
                "KitInstance", "StaticBatcher", "ModelTint", "Tint", "Box3D", "PatchShape", "CylinderShape", "SphereShape", "ConeShape",
                "BlobShape", "ParasolShape", "SpireShape", "ProceduralShape", "LazyRenderer", "CarPaint", "WheelSpin", "ResettableBody",
                "OneWayBody", "BallTrap", "MovingPlatform",
            };

            /// <summary>Things the ball goes past, or that are not solid: never shelled.</summary>
            static readonly HashSet<string> PassTypes = new HashSet<string>
            {
                "Pedestrian", "CritterIdle", "GroundBird", "SkyFlock", "FlitButterfly", "AmbientAgent", "AmbientView", "WallCat",
                "ShoreCrab", "PondDuck", "TreeSquirrel", "Lapping", "TideWash", "RainCurtain", "PuddleShape", "CloudShape", "Shoreline",
                "WavyStrip", "StreetSlab", "SandField", "SandDunes", "SkinBuilder", "Animator",
            };

            /// <summary>Kit models the ball goes past: foliage hung over the lane.</summary>
            static readonly HashSet<string> PassModels = new HashSet<string> { "SwingTree" };

            sealed class ShellGroup
            {
                public Transform parent;
                public readonly HashSet<Vector2Int> cells = new HashSet<Vector2Int>();
                public readonly List<string> pieces = new List<string>();
                public PhysicsMaterial2D material;
            }

            void BuildBallShells()
            {
                Physics2D.SyncTransforms();
                var groups = new Dictionary<Transform, ShellGroup>();
                var leftOut = new List<string>();
                var filter = new ContactFilter2D { useTriggers = false };
                var hits = new Collider2D[4];
                var rayHits = new RaycastHit2D[4];
                int examined = 0;

                foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true))
                {
                    var mr = mf.GetComponent<MeshRenderer>();
                    var mesh = mf.sharedMesh;
                    if (mr == null || !mr.enabled || mesh == null || !mf.gameObject.activeInHierarchy) continue;
                    Bounds b = mr.bounds;
                    if (b.min.z > BallShellGeometry.Slab || b.max.z < -BallShellGeometry.Slab) continue;
                    if (b.size.x > ShellMaxWidth) continue;
                    if (mf.GetComponent<TextMesh>() != null) continue;
                    var mat = mr.sharedMaterial;
                    if (mat != null && mat.shader != null && mat.shader.name.Contains("Water")) continue;

                    string why;
                    Transform parent = ShellParent(mf.transform, out why);
                    if (parent == null)
                    {
                        if (why != null) leftOut.Add(Name(mf.transform) + " (" + why + ")");
                        continue;
                    }
                    examined++;
                    var cells = SlabCells(mf, mesh, parent);
                    if (cells.Count == 0) continue;

                    ShellGroup group;
                    if (!groups.TryGetValue(parent, out group))
                    {
                        group = new ShellGroup { parent = parent };
                        var designed = parent.GetComponent<Collider2D>();
                        group.material = designed != null && designed.sharedMaterial != null ? designed.sharedMaterial : GroundMat;
                        groups[parent] = group;
                    }
                    int before = group.cells.Count;
                    foreach (var c in cells)
                    {
                        Vector2 world = parent.TransformPoint(new Vector3((c.x + 0.5f) * BallShellGeometry.Cell, (c.y + 0.5f) * BallShellGeometry.Cell, 0f));
                        // On a designed collider already (or within the ball's reach of one): nothing to add.
                        if (Physics2D.OverlapCircle(world, ShellMargin, filter, hits) > 0) continue;
                        // A lip lying on something: the ball rolls over it.
                        if (Physics2D.Raycast(world, Vector2.down, filter, rayHits, ShellLip) > 0) continue;
                        group.cells.Add(c);
                    }
                    if (group.cells.Count > before) group.pieces.Add(Name(mf.transform));
                }

                int boxes = 0, pieces = 0;
                var report = new StringBuilder();
                foreach (var group in groups.Values)
                {
                    if (group.cells.Count == 0) continue;
                    var go = new GameObject("BallShell");
                    go.transform.SetParent(group.parent, false);
                    foreach (var box in BallShellGeometry.Merge(group.cells))
                    {
                        var col = go.AddComponent<BoxCollider2D>();
                        float c = BallShellGeometry.Cell;
                        col.offset = new Vector2((box.x0 + box.x1 + 1) * 0.5f * c, (box.y0 + box.y1 + 1) * 0.5f * c);
                        col.size = new Vector2((box.x1 - box.x0 + 1) * c, (box.y1 - box.y0 + 1) * c);
                        col.sharedMaterial = group.material;
                        boxes++;
                    }
                    go.AddComponent<BallShell>();
                    pieces += group.pieces.Count;
                    report.Append(report.Length > 0 ? "; " : "").Append(group.parent.name).Append(": ").Append(string.Join(", ", Distinct(group.pieces)));
                }
                Debug.Log("[Kick Off] " + LevelId + ": ball shells on " + pieces + " surfaces of the " + examined + " meshes in the ball's plane, "
                    + boxes + " boxes" + (report.Length > 0 ? " (" + report + ")" : "") + (leftOut.Count > 0 ? ". Left as they are: "
                    + string.Join(", ", Distinct(leftOut)) : "") + " (docs/LEARNINGS.md E18)");
            }

            /// <summary>
            /// What a mesh's shell belongs to: the nearest moving body above it, else the nearest piece with a solid collider, else the
            /// level (a kit model standing alone). Null, with the reason, for anything the ball goes past or that moves without a body.
            /// </summary>
            Transform ShellParent(Transform t, out string why)
            {
                why = null;
                Transform parent = null;
                bool kitModel = false;
                var chain = new List<Transform>();
                for (var a = t; a != null && a != root; a = a.parent)
                {
                    if (a.GetComponent<KitInstance>() != null)
                    {
                        kitModel = true;
                        string model = a.name;
                        if (PassModels.Contains(model) || HasKitModel("Plants", model) || HasKitModel("Animals", model)) return null;
                    }
                    if (a.GetComponent<Rigidbody2D>() != null) { parent = a; break; }
                    var cols = a.GetComponents<Collider2D>();
                    if (cols.Length > 0)
                    {
                        bool solid = false;
                        foreach (var c in cols) if (!c.isTrigger) solid = true;
                        if (!solid) return null;               // a pickup or a zone: the ball goes through, as it should
                        parent = a;
                        break;
                    }
                    chain.Add(a);
                }
                foreach (var a in chain)
                    foreach (var mb in a.GetComponents<MonoBehaviour>())
                    {
                        if (mb == null) continue;
                        string type = mb.GetType().Name;
                        if (PassTypes.Contains(type)) return null;
                        if (!StillTypes.Contains(type) && !(mb is ProceduralShape))
                        {
                            why = "moves with its " + type;
                            return null;
                        }
                    }
                if (parent == null)
                {
                    if (!kitModel) return null;                // a builder's own decoration with no collider: posts, chains, markers
                    parent = root;
                }
                Vector3 e = parent.rotation.eulerAngles;
                if (Mathf.Abs(Mathf.DeltaAngle(e.x, 0f)) > 0.5f || Mathf.Abs(Mathf.DeltaAngle(e.y, 0f)) > 0.5f)
                {
                    why = "on a piece turned out of the street's plane";
                    return null;
                }
                return parent;
            }

            /// <summary>The cells (in <paramref name="parent"/>'s x and y) where the mesh's triangles cross the ball's plane.</summary>
            static HashSet<Vector2Int> SlabCells(MeshFilter mf, Mesh mesh, Transform parent)
            {
                var cells = new HashSet<Vector2Int>();
                var verts = mesh.vertices;
                var tris = mesh.triangles;
                if (verts == null || verts.Length == 0) return cells;
                var toWorld = mf.transform.localToWorldMatrix;
                var world = new Vector3[verts.Length];
                for (int i = 0; i < verts.Length; i++) world[i] = toWorld.MultiplyPoint3x4(verts[i]);
                var flat = new List<Vector2>(6);
                float s = BallShellGeometry.Slab;
                for (int i = 0; i + 2 < tris.Length; i += 3)
                {
                    Vector3 a = world[tris[i]], b = world[tris[i + 1]], c = world[tris[i + 2]];
                    if ((a.z > s && b.z > s && c.z > s) || (a.z < -s && b.z < -s && c.z < -s)) continue;
                    var poly = BallShellGeometry.ClipToSlab(a, b, c);
                    if (poly.Count == 0) continue;
                    flat.Clear();
                    foreach (var p in poly) flat.Add(parent.InverseTransformPoint(p));
                    BallShellGeometry.Rasterize(flat, cells);
                }
                return cells;
            }

            string Name(Transform t)
            {
                for (var a = t; a != null && a != root; a = a.parent)
                    if (a.GetComponent<KitInstance>() != null) return a.name;
                return t.parent != null && t.parent != root ? t.parent.name + "/" + t.name : t.name;
            }

            static List<string> Distinct(List<string> names)
            {
                var seen = new HashSet<string>();
                var list = new List<string>();
                foreach (var n in names) if (seen.Add(n)) list.Add(n);
                return list;
            }
        }
    }
}
