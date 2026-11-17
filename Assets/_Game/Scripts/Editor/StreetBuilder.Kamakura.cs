using System.Linq;
using DribbleToSchool.Levels;
using DribbleToSchool.World;
using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Kamakura's street (LevelBuildKit.Kamakura): what its levels' layouts don't place themselves. The layouts (KamakuraLevels)
    /// place the Kamakura kit's models along the lane by the proposed layouts in review/kamakura/levels; this adds the ground
    /// behind the footpath they stand on, the green hills behind Hase, the cat on the block wall, the kid's home at the door
    /// (KM-B01) and Hase Station at the stop (its ticket gate, platform and name board). Nothing of the original town's street
    /// (its houses, gardens, poles and birds) is built in a Kamakura level.
    /// </summary>
    public static partial class StreetBuilder
    {
        static bool KM { get { return LevelBuildKit.Kamakura; } }

        /// <summary>The stops of the cities' routes (Levels/CityRoutes) that <see cref="StopFront"/> has a set piece for, beside <see cref="SetPieces"/> (the original town's).</summary>
        public static readonly string[] CitySetPieces =
        {
            "hase", "kamakuraStation", "shrineSideGate", "boardwalk", "grandmasShop", "lifeguardTower", "greatTorii", "trailSign",
            "genjiyama",
        };

        /// <summary>The street of a Kamakura level, in place of the chapter's (see <see cref="Scenery"/>).</summary>
        static void KamakuraStreet(LevelBuildKit.TrackBuilder track, Transform root)
        {
            float x0 = track.MinX - 50f, x1 = track.MaxX + 50f, mid = (x0 + x1) * 0.5f;
            critters = new GameObject("Critters").transform;
            wallTops.Clear();
            // the ground behind the footpath, paving and gravel, that the houses, walls and plants stand on
            Solid(root, "Frontage", new Vector3(mid, -0.02f, PropertyZ + 20f), new Vector3(x1 - x0, 0.04f, 40f), new Color(0.6f, 0.58f, 0.55f));
            // the wooded hills behind Hase, far back, and the sky's haze over them
            Solid(root, "Hills", new Vector3(mid, 7f, 75f), new Vector3(x1 - x0 + 120f, 14f, 6f), new Color(0.3f, 0.42f, 0.3f));
            Solid(root, "HillsFar", new Vector3(mid + 20f, 11f, 110f), new Vector3(x1 - x0 + 200f, 22f, 6f), new Color(0.46f, 0.56f, 0.52f));

            // the ginger cat on the block wall (KM1-1's hazard in the reference: WallCat, the Animals kit's cat until Kamakura's
            // own animals are in the game), facing the way the kid comes
            var walls = track.KamakuraWalls.ToArray();
            if (walls.Length > 0 && LevelBuildKit.HasKitModel("Animals", "Cat"))
            {
                var rng = new System.Random(1101);
                var w = walls[0];
                var holder = Holder("Cat", Mathf.Lerp(w.x, w.y, 0.25f), w.z, w.w, 180f + Rand(rng, -10f, 10f));
                var model = Animal(holder, "Cat", 1f, new Color(0.86f, 0.52f, 0.22f), new Color(0.97f, 0.93f, 0.86f));
                if (model == null) Object.DestroyImmediate(holder.gameObject);
                else
                {
                    var cat = holder.gameObject.AddComponent<WallCat>();
                    cat.seed = rng.Next();
                    cat.model = model;
                    cat.tail = PartOf(model, "Tail", Vector3.up);
                    cat.walls = walls;
                    cat.wall = 0;
                }
            }
        }

        /// <summary>The kid's home in Kamakura (KM-B01, the photographic KM1-1's house and its fence), its entrance at the gate.</summary>
        static void HomeFrontKM(Transform parent, float gx, float gy)
        {
            LevelBuildKit.KitModel(parent, "Kamakura", "KmHome", new Vector3(gx, gy, LevelBuildKit.KamakuraZ("KmHome", 1.6f)));
        }

        /// <summary>
        /// Hase Station (KM1-1's stop, review/kamakura/levels/KM1-1/layout.json): its ticket gate at the stop's door, where the kid
        /// finishes, the platform beyond it along the tracks' side and the station's name board at its far end.
        /// </summary>
        static void HaseStation(Transform parent, float gx, float gy)
        {
            Kamakura(parent, "KmTicketGate", gx, gy, 1.3f);
            Kamakura(parent, "KmStationPlatform", gx + 5.4f, gy, 2.3f);
            Kamakura(parent, "KmStationSign", gx + 11.4f, gy, 1.4f);
        }

        /// <summary>A Kamakura kit model at x, its street face at a layout's <paramref name="front"/>.</summary>
        static Transform Kamakura(Transform parent, string model, float x, float gy, float front)
        {
            if (!LevelBuildKit.HasKitModel("Kamakura", model)) return null;
            return LevelBuildKit.KitModel(parent, "Kamakura", model, new Vector3(x, gy, LevelBuildKit.KamakuraZ(model, front)));
        }
    }
}
