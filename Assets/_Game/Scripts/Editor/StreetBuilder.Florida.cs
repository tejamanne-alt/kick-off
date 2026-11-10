using System.Collections.Generic;
using DribbleToSchool.Art;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The Florida add-on's beach (chapter 3 only, &lt;scene&gt;_FL scenes built with <see cref="LevelBuildKit.Florida"/> set): a Space
    /// Coast beach strip on the A1A after the user's references (review/florida/refs, F3-1 to F3-6), on the Florida kit
    /// (tools/blender/kit_buildings_fl.py). The kid's beach stays exactly as it is (the sand, the tides, the channels, the dunes
    /// and the sea a few metres behind the lane): the town stands behind it on seawall terraces that run from the sand out into
    /// the sea, as the oceanfront motels and shops of a Florida beach town do, and leaves the beach open wherever the tide washes
    /// up, a channel runs out, a dune rises or a stop stands, so the sea shows between them and the beach's own things (parasols,
    /// lifeguard towers, rocks, palms) keep to those gaps. The strip runs in the references' order and each level takes it up
    /// where the one before left it: the beach front (the restroom with its showers, the snack shack and its kayaks), the diner,
    /// the motel with its pool, the rental shop, the Art Deco shops; and toward the school the bus stop, the school-zone beacon
    /// and the school itself (LevelBuildKit.FloridaSchool).
    /// </summary>
    public static partial class StreetBuilder
    {
        /// <summary>True while a level's Florida scene is being built (and the Florida kit is there).</summary>
        static bool FL { get { return LevelBuildKit.Florida && LevelBuildKit.HasKitModel("Florida", "MotelFL"); } }

        /// <summary>How far the terraces' front stands behind the lane (the promenade runs from there to the buildings).</summary>
        public const float TerraceFront = 2.5f;
        /// <summary>The buildings' front walls on the terraces, and how far back the terraces run (out over the sea).</summary>
        const float FrontageZ = 5.0f, TerraceBack = 18f;
        /// <summary>How high the terraces' top stands above the beach.</summary>
        const float TerraceRise = 0.22f;

        /// <summary>One lot of the strip: its frontage and what stands on it (x from the lot's left end, the terrace's top).</summary>
        sealed class FloridaLot
        {
            public string name;
            public float width;
            public System.Action<Transform, float, float, System.Random> build;
        }

        /// <summary>The strip's lots in the references' order (F3-1 to F3-4); a level's strip starts where its level picks it up.</summary>
        static readonly FloridaLot[] FloridaLots =
        {
            new FloridaLot { name = "Restroom", width = 8.8f, build = (p, s, y, r) =>
            {
                Model(p, "Florida", "RestroomFL", s + 4.2f, y, FrontageZ + 0.4f);
                Model(p, "Florida", "SignTurtleFL", s + 0.6f, y, 3.3f);
            } },
            new FloridaLot { name = "Shack", width = 10.2f, build = (p, s, y, r) =>
            {
                Model(p, "Florida", "ShackFL", s + 2.6f, y, FrontageZ);
                Model(p, "Florida", "KayakRackFL", s + 7.1f, y, FrontageZ + 0.8f);
                Model(p, "Florida", "SignAccessFL", s + 9.4f, y, 3.4f);
            } },
            new FloridaLot { name = "Diner", width = 17.4f, build = (p, s, y, r) =>
            {
                Model(p, "Florida", "DinerSignFL", s + 1.4f, y, 3.7f);
                Model(p, "Florida", "DinerFL", s + 10f, y, FrontageZ + 0.6f);
                Model(p, "Florida", "SignHurricaneFL", s + 3.6f, y, 3.3f);
            } },
            new FloridaLot { name = "Motel", width = 22.4f, build = (p, s, y, r) =>
            {
                Model(p, "Florida", "MotelSignFL", s + 1.9f, y, 3.7f);
                Model(p, "Florida", "MotelPoolFL", s + 12.2f, y, 3.3f);
                Model(p, "Florida", "MotelFL", s + 12.6f, y, 8.4f);
            } },
            new FloridaLot { name = "Rentals", width = 13.2f, build = (p, s, y, r) =>
            {
                Model(p, "Florida", "PoleSignalFL", s + 0.4f, y, 3.2f);
                Model(p, "Florida", "RentalsFL", s + 5.6f, y, FrontageZ);
                Model(p, "Florida", "HydrantFL", s + 11.9f, y, 3.4f);
            } },
            new FloridaLot { name = "DecoSurf", width = 7.8f, build = (p, s, y, r) => Model(p, "Florida", "DecoSurfFL", s + 3.9f, y, FrontageZ) },
            new FloridaLot { name = "DecoCafe", width = 6.5f, build = (p, s, y, r) => Model(p, "Florida", "DecoCafeFL", s + 3.25f, y, FrontageZ) },
            new FloridaLot { name = "DecoBait", width = 6.5f, build = (p, s, y, r) => Model(p, "Florida", "DecoBaitFL", s + 3.25f, y, FrontageZ) },
            new FloridaLot { name = "DecoIce", width = 8.3f, build = (p, s, y, r) => Model(p, "Florida", "DecoIceFL", s + 4.5f, y, FrontageZ) },
            new FloridaLot { name = "DecoShut", width = 7.2f, build = (p, s, y, r) => Model(p, "Florida", "DecoShutFL", s + 3.6f, y, FrontageZ) },
        };

        /// <summary>Every Florida kit model the street and the school place (the tests check the kit has each one).</summary>
        public static readonly string[] FloridaModelsUsed =
        {
            "RestroomFL", "SignTurtleFL", "ShackFL", "KayakRackFL", "SignAccessFL", "DinerSignFL", "DinerFL", "SignHurricaneFL",
            "MotelSignFL", "MotelPoolFL", "MotelFL", "PoleSignalFL", "RentalsFL", "HydrantFL", "DecoSurfFL", "DecoCafeFL", "DecoBaitFL",
            "DecoIceFL", "DecoShutFL", "LampFL", "BenchFL", "TrashFL", "SchoolZoneFL", "BusShelterFL", "MailboxFL", "SignAccessUpFL",
            "LifeguardFL", "SchoolGateFL", "FenceAluFL", "MarqueeFL", "SchoolFL", "WalkwayFL", "FlagpoleFL", "PortableFL",
        };

        /// <summary>Where each level's stretch of the strip starts (L11 at the beach front, then the diner, the motel, the shops).</summary>
        static int FloridaStart(string levelId)
        {
            switch (levelId)
            {
                case "L12": return 2;
                case "L13": return 3;
                case "L14": return 5;
                default: return 0;
            }
        }

        /// <summary>The x stretches the town's terraces fill along this beach (the beach's own things keep out of them).</summary>
        static bool InStrip(List<Vector2> strip, float a, float b)
        {
            if (strip == null) return false;
            foreach (var s in strip)
                if (b > s.x && a < s.y) return true;
            return false;
        }

        /// <summary>
        /// Builds the Florida strip between x0 and x1 and returns the stretches its terraces fill. The beach stays open over the
        /// tides (with the 3 m their wash curls back, and a little more), the channels, the dunes and their slopes, the stops' plots
        /// and the pier, so the sea shows there and the tide still runs up to the lane from it.
        /// </summary>
        static List<Vector2> FloridaStrip(LevelBuildKit.TrackBuilder track, Transform root, float x0, float x1, float pierX, float pierReach)
        {
            var strip = new List<Vector2>();
            var rng = new System.Random(Mathf.RoundToInt(x0 * 7f) + 311);
            var field = track.BeachSand;
            float baseTop = track.LowestGroundTop;
            // What has to stay open beach.
            var open = new List<Vector2>();
            foreach (var t in track.TideStretches) open.Add(new Vector2(t.x - 1.5f, t.y + 1.5f));
            foreach (var g in field.Gaps) open.Add(new Vector2(g.l - 2.5f, g.r + 2.5f));
            // (a dune's top carries the town as the flat beach does; only its slopes stay open)
            foreach (var step in field.Steps)
            {
                float s0 = Mathf.Min(step.edge, step.edge + step.run), s1 = Mathf.Max(step.edge, step.edge + step.run);
                open.Add(new Vector2(s0 - 2f, s1 + 2f));
            }
            if (!float.IsNaN(pierX)) open.Add(new Vector2(pierX - pierReach - 2f, pierX + pierReach + 2f));
            float skip;
            for (float x = x0; x < x1; x += 1f)
                if (Blocked(track, x, x + 1f, out skip)) open.Add(new Vector2(x - 1f, Mathf.Max(x + 2f, skip + 1f)));
            open.Sort((p, q) => p.x.CompareTo(q.x));

            var town = new GameObject("FloridaStrip").transform;
            town.SetParent(root, false);
            int next = FloridaStart(LevelBuildKit.LevelId);
            float a = x0 + 1.5f;
            for (int guard = 0; a < x1 - 6f && guard < 400; guard++)
            {
                // Out of any open beach that covers a; then the free stretch runs to the next one.
                bool moved = false;
                foreach (var o in open)
                    if (o.x <= a && o.y > a) { a = o.y; moved = true; }
                if (moved) continue;
                float b = x1 - 1f;
                foreach (var o in open)
                    if (o.x > a && o.x < b) b = o.x;
                // The terrace's top: a little over the highest sand along its front (on a dune, the dune's top).
                float y = baseTop;
                for (float sx = a; sx <= b; sx += 0.5f)
                    y = Mathf.Max(y, Mathf.Max(field.Height(sx, TerraceFront), field.Height(sx, TerraceFront + 0.25f)));
                y += TerraceRise;
                // Lots in the strip's order while they fit (one that doesn't is passed over for the next); the rest stays beach.
                float x = a;
                for (int tries = 0; tries < FloridaLots.Length; )
                {
                    var lot = FloridaLots[next % FloridaLots.Length];
                    next++;
                    if (x + lot.width > b) { tries++; continue; }
                    var lotRoot = new GameObject(lot.name).transform;
                    lotRoot.SetParent(town, false);
                    lot.build(lotRoot, x, y, rng);
                    x += lot.width;
                    tries = 0;
                }
                if (x - a > 1f)
                {
                    Terrace(town, a - 0.3f, x + 0.3f, baseTop, y, track.LowestGroundTop - 0.3f);
                    Promenade(town, rng, a, x, y);
                    strip.Add(new Vector2(a - 0.5f, x + 0.5f));
                }
                a = b + 0.01f;
            }
            town.gameObject.AddComponent<StaticBatcher>();
            return strip;
        }

        /// <summary>A seawall terrace: a concrete deck a little above the sand, its front a low kerb, running out over the sea.</summary>
        static void Terrace(Transform parent, float a, float b, float sand, float top, float sea)
        {
            var concrete = Art.surfaces[ProceduralArt.Surface.Concrete];
            var paving = Art.surfaces[ProceduralArt.Surface.Paving];
            float bottom = sea - 1.2f;
            Solid(parent, "Seawall", new Vector3((a + b) * 0.5f, (top - 0.06f + bottom) * 0.5f, (TerraceFront + 0.25f + TerraceBack) * 0.5f),
                new Vector3(b - a, top - 0.06f - bottom, TerraceBack - TerraceFront - 0.25f), new Color(0.82f, 0.8f, 0.76f), concrete);
            // The promenade's paving on top, and its kerb along the beach.
            Solid(parent, "Promenade", new Vector3((a + b) * 0.5f, top - 0.03f, (TerraceFront + TerraceBack) * 0.5f),
                new Vector3(b - a, 0.06f, TerraceBack - TerraceFront), new Color(0.86f, 0.84f, 0.81f), paving);
            Solid(parent, "Kerb", new Vector3((a + b) * 0.5f, (sand - 0.2f + top) * 0.5f, TerraceFront + 0.12f),
                new Vector3(b - a, top - sand + 0.2f, 0.25f), new Color(0.78f, 0.77f, 0.74f), concrete);
        }

        /// <summary>The promenade's things in front of the buildings: sabal palms, lamps, benches, bins; tall old sabals behind.</summary>
        static void Promenade(Transform parent, System.Random rng, float a, float b, float y)
        {
            for (float x = a + Rand(rng, 1.5f, 4f); x < b - 1f; x += Rand(rng, 9f, 14f))
                Plant(parent, "PalmSabal", null, x, y, Rand(rng, 3.2f, 3.6f), Rand(rng, 0.85f, 1.1f), 1f, -60, rng);
            int k = 0;
            for (float x = a + Rand(rng, 5f, 8f); x < b - 2f; x += Rand(rng, 14f, 19f), k++)
            {
                Model(parent, "Florida", "LampFL", x, y, 3.0f);
                if (k % 2 == 0)
                {
                    Model(parent, "Florida", "BenchFL", x + 2.2f, y, 4.3f);
                    Model(parent, "Florida", "TrashFL", x + 3.8f, y, 4.2f);
                }
            }
            // Old sabals standing up over the roofs at the back of the terraces.
            for (float x = a + Rand(rng, 2f, 6f); x < b - 1f; x += Rand(rng, 10f, 16f))
                Plant(parent, "PalmSabalTall", null, x, y, Rand(rng, TerraceBack - 2.4f, TerraceBack - 0.8f), Rand(rng, 0.9f, 1.15f), 1f, -60, rng);
        }

        /// <summary>
        /// Toward the school (the route's last level, and the challenge that ends there): the last block's bus stop, a mailbox and
        /// the school-zone beacon on the sand before the gate.
        /// </summary>
        static void FloridaSchoolApproach(LevelBuildKit.TrackBuilder track, Transform root, float goalX)
        {
            var p = new GameObject("FloridaSchoolApproach").transform;
            p.SetParent(root, false);
            float gy(float x, float z) { return GroundAt(track, x, z); }
            Model(p, "Florida", "SchoolZoneFL", goalX - 9f, gy(goalX - 9f, 2.4f), 2.4f);
            Model(p, "Florida", "BusShelterFL", goalX - 15f, gy(goalX - 15f, 3.4f), 3.4f);
            Model(p, "Florida", "MailboxFL", goalX - 18.5f, gy(goalX - 18.5f, 2.9f), 2.9f);
            Model(p, "Florida", "SignAccessUpFL", goalX - 21f, gy(goalX - 21f, 3.0f), 3.0f);
            p.gameObject.AddComponent<StaticBatcher>();
        }

        /// <summary>California's palms in Florida: the sabal for the date palm, the tall old sabal for the very tall fan palm.</summary>
        static string FloridaPalm(string model)
        {
            if (!FL) return model;
            switch (model)
            {
                case "PalmDate": return LevelBuildKit.HasKitModel("Plants", "PalmSabal") ? "PalmSabal" : model;
                case "PalmFan": return LevelBuildKit.HasKitModel("Plants", "PalmSabalTall") ? "PalmSabalTall" : model;
                default: return model;
            }
        }
    }
}
