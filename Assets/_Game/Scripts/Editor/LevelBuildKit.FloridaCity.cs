using DribbleToSchool.Art;
using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Florida's own play (docs/CITIES.md, "Florida (Miami), USA"), for the city's own routes (Editor/FloridaLevels): Little
    /// Havana's roosters and hens, the iguanas on the seawalls, the rental scooters left across the sidewalk, the pelicans, the
    /// downtown arcades and the downpour, and the street sweeper, on the Miami kit (tools/blender/kit_buildings_mia.py). Each thing falls back to a
    /// stand-in of boxes in Florida's colours only when the kit isn't imported (the tests check the kit has every model).
    /// </summary>
    public static partial class LevelBuildKit
    {
        public partial class TrackBuilder
        {
            static readonly Color Stucco = new Color(0.96f, 0.92f, 0.84f);
            static readonly Color Seafoam = new Color(0.62f, 0.86f, 0.78f);
            static readonly Color Coral = new Color(0.96f, 0.56f, 0.46f);
            static readonly Color Teal = new Color(0.13f, 0.6f, 0.6f);
            static readonly Color Steel = new Color(0.62f, 0.64f, 0.67f);

            /// <summary>The underside of an arcade's canopy: clear of a double jump's head (3.3 m, LevelFeasibility's roof check).</summary>
            const float ArcadeCanopy = 3.4f;

            /// <summary>The roofed stretches laid so far (Arcade): the downpour's shelters.</summary>
            readonly List<Vector2> shelters = new List<Vector2>();

            // ------------------------------------------------------------------ animals

            /// <summary>A rooster (or a hen) loose about <paramref name="minX"/> to <paramref name="maxX"/> (Hazards/Rooster).</summary>
            public void Rooster(float minX, float maxX, bool hen = false, float groundTop = 0f, float phase = 0f)
            {
                Coaching.Mark("chickens", minX - 1.5f, maxX + 1.5f);
                var go = new GameObject(hen ? "Hen" : "Rooster");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2((minX + maxX) * 0.5f, groundTop);
                go.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<BoxCollider2D>();
                col.isTrigger = true;
                col.size = new Vector2(0.45f, 0.5f);
                col.offset = new Vector2(0f, 0.25f);
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                visual.localPosition = new Vector3(0f, 0f, 0.35f);
                Color feathers = hen ? new Color(0.72f, 0.45f, 0.24f) : new Color(0.62f, 0.2f, 0.12f);
                Color tail = hen ? new Color(0.55f, 0.32f, 0.16f) : new Color(0.08f, 0.22f, 0.18f);
                // (the visual is turned by the hazard so its +z leads: the kit's birds head toward +x, so a quarter turn)
                if (KitModel(visual, "Miami", hen ? "HenMIA" : "RoosterMIA", visual.position, -90f) == null)
                Blobs(visual, "Bird", Vector3.zero,
                    new BlobShape.Blob(new Vector3(0f, 0.24f, 0f), new Vector3(0.17f, 0.12f, 0.1f), feathers),
                    new BlobShape.Blob(new Vector3(0f, 0.42f, 0.12f), new Vector3(0.06f, 0.07f, 0.06f), feathers),
                    new BlobShape.Blob(new Vector3(0f, 0.5f, 0.13f), new Vector3(0.015f, 0.035f, 0.045f), new Color(0.9f, 0.12f, 0.1f)),
                    new BlobShape.Blob(new Vector3(0f, 0.43f, 0.19f), new Vector3(0.012f, 0.012f, 0.03f), new Color(1f, 0.75f, 0.2f)),
                    new BlobShape.Blob(new Vector3(0f, 0.33f, -0.16f), new Vector3(0.04f, hen ? 0.06f : 0.13f, 0.08f), tail),
                    new BlobShape.Blob(new Vector3(0.05f, 0.07f, 0f), new Vector3(0.012f, 0.07f, 0.012f), new Color(0.95f, 0.75f, 0.3f)),
                    new BlobShape.Blob(new Vector3(-0.05f, 0.07f, 0f), new Vector3(0.012f, 0.07f, 0.012f), new Color(0.95f, 0.75f, 0.3f)));
                var bird = go.AddComponent<Hazards.Rooster>();
                bird.minX = minX;
                bird.maxX = maxX;
                bird.groundY = groundTop;
                bird.visual = visual;
                bird.phaseOffset = phase;
            }

            /// <summary>A green iguana basking at <paramref name="spotA"/> that dashes to <paramref name="spotB"/> when the kid comes (Hazards/Iguana).</summary>
            public void Iguana(float spotA, float spotB, float groundTop = 0f)
            {
                Coaching.Mark("iguana", Mathf.Min(spotA, spotB) - 3f, Mathf.Max(spotA, spotB));
                var go = new GameObject("Iguana");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(spotA, groundTop);
                go.AddComponent<Rigidbody2D>().bodyType = RigidbodyType2D.Kinematic;
                var col = go.AddComponent<BoxCollider2D>();
                col.isTrigger = true;
                col.size = new Vector2(0.9f, 0.3f);
                col.offset = new Vector2(0f, 0.15f);
                var visual = new GameObject("Visual").transform;
                visual.SetParent(go.transform, false);
                visual.localPosition = new Vector3(0f, 0f, 0.5f);
                Color green = new Color(0.36f, 0.6f, 0.25f), dark = new Color(0.2f, 0.38f, 0.16f);
                if (KitModel(visual, "Miami", "IguanaMIA", visual.position, -90f) == null)
                Blobs(visual, "Lizard", Vector3.zero,
                    new BlobShape.Blob(new Vector3(0f, 0.09f, 0f), new Vector3(0.07f, 0.06f, 0.22f), green),
                    new BlobShape.Blob(new Vector3(0f, 0.11f, 0.26f), new Vector3(0.05f, 0.05f, 0.07f), green),
                    new BlobShape.Blob(new Vector3(0f, 0.05f, -0.4f), new Vector3(0.025f, 0.025f, 0.24f), dark),
                    new BlobShape.Blob(new Vector3(0f, 0.15f, 0.02f), new Vector3(0.012f, 0.03f, 0.18f), dark),
                    new BlobShape.Blob(new Vector3(0.08f, 0.03f, 0.12f), new Vector3(0.05f, 0.02f, 0.02f), green),
                    new BlobShape.Blob(new Vector3(-0.08f, 0.03f, 0.12f), new Vector3(0.05f, 0.02f, 0.02f), green),
                    new BlobShape.Blob(new Vector3(0.08f, 0.03f, -0.12f), new Vector3(0.05f, 0.02f, 0.02f), green),
                    new BlobShape.Blob(new Vector3(-0.08f, 0.03f, -0.12f), new Vector3(0.05f, 0.02f, 0.02f), green));
                var lizard = go.AddComponent<Hazards.Iguana>();
                lizard.spotA = spotA;
                lizard.spotB = spotB;
                lizard.groundY = groundTop;
                lizard.visual = visual;
            }

            /// <summary>A brown pelican: a gull's swoop (Hazards/Seagull) on the Animals kit's pelican, bigger and slower.</summary>
            public void Pelican(float fromX, float toX, float baseY, float phaseOffset = 0f)
            {
                bool own = HasKitModel("Animals", "Pelican");
                Seagull(fromX, toX, baseY, phaseOffset, "Pelican");
                var go = root.GetChild(root.childCount - 1);
                go.name = "Pelican";
                var gull = go.GetComponent<Hazards.Seagull>();
                if (gull != null)
                {
                    gull.flightTime *= 1.35f;
                    gull.knockVelocity = new Vector2(-3.5f, 4.5f);
                    // (its own model is pelican-sized, 1.4 m across; the gull stand-in is scaled up)
                    if (gull.visual != null) gull.visual.localScale = Vector3.one * (own ? 1.15f : 1.6f);
                }
            }

            // ------------------------------------------------------------------ the street's own things

            /// <summary>A rental scooter left lying across the sidewalk: a low thing to hop (and chip the ball over).</summary>
            public void Scooter(float x, float groundTop = 0f, bool standing = false)
            {
                float h = standing ? 0.9f : 0.32f, w = standing ? 0.35f : 1.1f;
                Audit.AddWall(x, w, h, "scooter");
                var go = Block("Scooter", new Vector2(x, groundTop + h * 0.5f), new Vector2(w, h), Teal, GroundMat, false);
                var t = go.transform;
                // The kit's rental scooter, lying on its side across the sidewalk or up on its kickstand (its handlebar's end stands
                // a little over the collider: a thin bar the ball may clip).
                if (KitModel(t, "Miami", standing ? "ScooterUpMIA" : "ScooterMIA", new Vector3(x, groundTop, standing ? 0.1f : 0f), standing ? 15f : 0f) != null)
                {
                    go.AddComponent<StaticBatcher>();
                    return;
                }
                if (standing)
                {
                    Part(t, "Stem", new Vector3(0f, 0f, 0f), new Vector3(0.06f, 0.9f, 0.06f), new Color(0.15f, 0.16f, 0.18f));
                    Part(t, "Deck", new Vector3(0.25f, -0.4f, 0f), new Vector3(0.7f, 0.08f, 0.16f), Teal);
                }
                else
                {
                    Part(t, "Deck", new Vector3(0f, -0.08f, 0f), new Vector3(1f, 0.08f, 0.16f), Teal);
                    Part(t, "Stem", new Vector3(0.45f, 0.02f, 0.2f), new Vector3(0.9f, 0.05f, 0.05f), new Color(0.15f, 0.16f, 0.18f));
                    Part(t, "WheelA", new Vector3(-0.48f, -0.08f, 0f), new Vector3(0.16f, 0.16f, 0.06f), new Color(0.1f, 0.1f, 0.1f));
                    Part(t, "WheelB", new Vector3(0.48f, -0.08f, 0f), new Vector3(0.16f, 0.16f, 0.06f), new Color(0.1f, 0.1f, 0.1f));
                }
            }

            /// <summary>
            /// A domino table under a pergola in a Little Havana park, or any table-height thing in the way: a solid table top to hop
            /// onto (0.75 m) with its stools.
            /// </summary>
            public void DominoTable(float x, float groundTop = 0f)
            {
                Platform(x - 0.6f, x + 0.6f, groundTop + 0.75f, groundTop);
                var t = new GameObject("DominoTable").transform;
                t.SetParent(root, false);
                t.position = new Vector3(x, groundTop, 0f);
                // The kit's concrete table with its game laid out and its stools (no pergola: the domino park stands behind).
                if (KitModel(t, "Miami", "DominoTableMIA", t.position) != null) return;
                Part(t, "Leg", new Vector3(0f, 0.35f, 0f), new Vector3(0.12f, 0.7f, 0.12f), new Color(0.3f, 0.3f, 0.32f));
                foreach (float dx in new[] { -1f, 1f })
                    Part(t, "Stool", new Vector3(dx * 0.95f, 0.22f, 0.4f), new Vector3(0.3f, 0.44f, 0.3f), Coral);
                // The pergola behind, over the far half of the footpath only (nothing tall in front of the lane).
                foreach (float dx in new[] { -1.6f, 1.6f })
                    Part(t, "Post", new Vector3(dx, 1.35f, StreetBuilder.PathHalf + 0.2f), new Vector3(0.14f, 2.7f, 0.14f), Stucco);
                Part(t, "Beams", new Vector3(0f, 2.75f, StreetBuilder.PathHalf - 0.6f), new Vector3(3.6f, 0.12f, 1.8f), Stucco);
            }

            /// <summary>
            /// An arcade or a deep awning over the footpath from <paramref name="fromX"/> to <paramref name="toX"/>: a roof 3.1 m up
            /// on posts along the back of the footpath. The downpour can't reach the kid under it (<see cref="DowntownDownpour"/>).
            /// </summary>
            public void Arcade(float fromX, float toX, float groundTop = 0f, Color? colour = null)
            {
                // The Miami kit's Deco block with its canvas arcade over the sidewalk (cantilevered from its front wall, which stands
                // just behind the lane): the shelter is the model's 10 m, centred on the stretch asked for.
                string deco = shelters.Count % 2 == 0 ? "DecoArcade2MIA" : "DecoArcadeMIA";
                if (HasKitModel("Miami", deco))
                {
                    const float wide = 10f;
                    float cx = (fromX + toX) * 0.5f;
                    shelters.Add(new Vector2(cx - wide * 0.5f, cx + wide * 0.5f));
                    Audit.AddRoof(cx - wide * 0.5f, cx + wide * 0.5f, groundTop + ArcadeCanopy);
                    var block = KitModel(root, "Miami", deco, new Vector3(cx, groundTop, StreetBuilder.PathHalf + 0.05f));
                    if (block != null)
                    {
                        float native = KitSize("Miami", deco).x;
                        // (Raised a little: the model's canopy is at 3.05 m, under a double jump's head, LevelFeasibility.)
                        if (native > 1f) block.localScale = new Vector3(wide / native, ArcadeCanopy / 3.05f, 1f);
                        CanopyCollider("ArcadeCanopy", cx - wide * 0.5f, cx + wide * 0.5f, groundTop + ArcadeCanopy);
                        return;
                    }
                }
                shelters.Add(new Vector2(fromX, toX));
                Audit.AddRoof(fromX, toX, groundTop + ArcadeCanopy);
                CanopyCollider("ArcadeRoof", fromX, toX, groundTop + ArcadeCanopy);
                var t = new GameObject("Arcade").transform;
                t.SetParent(root, false);
                t.position = new Vector3((fromX + toX) * 0.5f, groundTop, 0f);
                float w = toX - fromX, zc = 0.4f;
                Color c = colour ?? Stucco;
                Part(t, "Roof", new Vector3(0f, ArcadeCanopy + 0.09f, zc), new Vector3(w, 0.18f, StreetBuilder.PathHalf * 2f + 0.8f), c);
                Part(t, "Fascia", new Vector3(0f, ArcadeCanopy - 0.11f, -StreetBuilder.PathHalf - 0.35f), new Vector3(w, 0.3f, 0.08f), Color.Lerp(c, Coral, 0.4f));
                for (float x = -w * 0.5f; x <= w * 0.5f + 0.01f; x += Mathf.Max(1.5f, w / Mathf.Max(1, Mathf.Round(w / 2.6f))))
                    Part(t, "Column", new Vector3(x, ArcadeCanopy * 0.5f, StreetBuilder.PathHalf + 0.3f), new Vector3(0.28f, ArcadeCanopy, 0.28f), c);
            }

            /// <summary>
            /// The canopy over the footpath, as the ball meets it: kicked up into it from below the ball bounces back down (it went
            /// through the canvas), and one landing on top rolls off an end (a low ridge along it) instead of staying there out of
            /// reach (docs/LEARNINGS.md E16). Its underside is the roof the feasibility audit already counts.
            /// </summary>
            void CanopyCollider(string name, float fromX, float toX, float underside)
            {
                var go = new GameObject(name);
                go.transform.SetParent(root, false);
                var edge = go.AddComponent<EdgeCollider2D>();
                float mid = (fromX + toX) * 0.5f, rise = Mathf.Clamp((toX - fromX) * 0.05f, 0.15f, 0.35f);
                edge.points = new[] { new Vector2(fromX, underside), new Vector2(mid, underside + rise), new Vector2(toX, underside) };
                edge.sharedMaterial = GroundMat;
            }

            /// <summary>
            /// The downpour over this street (Hazards/Downpour): bursts every few seconds until <paramref name="clearsAtX"/>, with the
            /// arcades laid so far (and any laid after it, in the same layout) as its shelters.
            /// </summary>
            public void DowntownDownpour(float fromX, float toX, float clearsAtX, float phase = 0f)
            {
                Coaching.Mark("downpour", fromX, Mathf.Min(fromX + 10f, toX));
                var go = new GameObject("Downpour");
                go.transform.SetParent(root, false);
                var rain = go.AddComponent<Hazards.Downpour>();
                rain.clearsAtX = clearsAtX;
                rain.phaseOffset = phase;
                // The rain: streaks falling round the camera, splashes and puddle ripples, in one mesh (World/RainCurtain).
                var curtainGo = new GameObject("Rain");
                curtainGo.transform.SetParent(go.transform, false);
                var curtain = curtainGo.AddComponent<World.RainCurtain>();
                curtain.groundY = 0f;
                curtain.clearsAtX = clearsAtX;
                curtain.zNear = StreetBuilder.RoadNear - 0.9f;      // (from the road's near half back: closer streaks would be blurs)
                curtain.zFar = StreetBuilder.PathHalf + 0.25f;
                curtain.shelterZFrom = -StreetBuilder.PathHalf - 0.2f;
                curtain.puddleZ = StreetBuilder.PathHalf - 0.15f;
                curtainGo.GetComponent<MeshRenderer>().sharedMaterial = Art.wire;
                rain.rain = curtain;
                pendingDownpour = rain;
            }

            Hazards.Downpour pendingDownpour;

            /// <summary>
            /// A street sweeper truck working slowly up and down the kerb lane from <paramref name="fromX"/> to <paramref name="toX"/>:
            /// a moving platform (its flat back 1.3 m up) to ride, or to wait for.
            /// </summary>
            /// <summary>The kit sweeper's cab (SweeperMIA, from the middle of its 3.4 m back, and up from the street): x and its roof.</summary>
            public const float SweeperCabFrom = 0.92f, SweeperCabTo = 1.86f, SweeperCabTop = 2.43f;

            public void Sweeper(float fromX, float toX, float groundTop = 0f, float speed = 1f)
            {
                // Solid from 0.3 m up to its flat back at 1.2 m (a jump reaches it): it can't be walked through, only ridden or waited for.
                const float width = 3.4f, bed = 1.2f, bottom = 0.3f;
                var center = new Vector2(fromX + width * 0.5f, groundTop + (bed + bottom) * 0.5f);
                Audit.AddSliding(center.x, groundTop + bed - 0.175f, width, toX - fromX - width, 0f);
                Coaching.Mark("sweeper", fromX, toX);
                var go = Block("Sweeper", center, new Vector2(width, bed - bottom), PlatformColor, GroundMat, false);
                var body = go.AddComponent<Rigidbody2D>();
                body.bodyType = RigidbodyType2D.Kinematic;
                var mp = go.AddComponent<Hazards.MovingPlatform>();
                mp.travel = new Vector2(toX - fromX - width, 0f);
                mp.speed = speed;
                mp.waitTime = 1.5f;
                // The kit's sweeper truck: its hopper's flat top is the 1.2 m back the kid rides, its cab over the front.
                bool kit = KitModel(go.transform, "Miami", "SweeperMIA", new Vector3(center.x, groundTop, 0.1f)) != null;
                // The cab is solid for the kid too, up to its roof (v140: the kid walked from the back into the cab; the ball shells,
                // docs/LEARNINGS.md E18, are the ball's only). From the 1.2 m back a double jump clears it (2.07 m against its
                // 1.23 m); from the street it is too tall, so the way past is up onto the back and over the cab (E20).
                var cab = go.AddComponent<BoxCollider2D>();
                cab.sharedMaterial = GroundMat;
                // (local to the block's middle, 0.75 m up: the kit's cab from x 0.92 to 1.86 and up to 2.43 m; the stand-in's below)
                float cabFrom = kit ? SweeperCabFrom : width * 0.5f - 0.9f, cabTo = kit ? SweeperCabTo : width * 0.5f;
                float cabTop = kit ? SweeperCabTop : 2.25f;
                cab.offset = new Vector2((cabFrom + cabTo) * 0.5f, (bottom + cabTop) * 0.5f - (bed + bottom) * 0.5f);
                cab.size = new Vector2(cabTo - cabFrom, cabTop - bottom);
                if (kit) return;
                Color white = new Color(0.95f, 0.95f, 0.93f);
                // (local to the block's middle, 0.75 m up: the body down to the wheels, the cab over the front, the brush under it)
                Part(go.transform, "Body", new Vector3(0f, -0.1f, 0.1f), new Vector3(width, 1.1f, 1.9f), white);
                Part(go.transform, "Cab", new Vector3(width * 0.5f - 0.45f, 0.95f, 0.1f), new Vector3(0.9f, 1.1f, 1.9f), white);
                Part(go.transform, "Stripe", new Vector3(0f, 0f, -0.86f), new Vector3(width, 0.12f, 0.02f), new Color(0.95f, 0.6f, 0.1f));
                Part(go.transform, "Brush", new Vector3(-width * 0.3f, -0.6f, -0.6f), new Vector3(0.6f, 0.3f, 0.6f), new Color(0.3f, 0.3f, 0.32f));
            }

            /// <summary>The finishing touches a Florida layout asks for once it has laid everything (the downpour's shelters and puddles).</summary>
            public void FloridaDone()
            {
                if (pendingDownpour != null)
                {
                    pendingDownpour.shelters = shelters.ToArray();
                    if (pendingDownpour.rain != null)
                    {
                        pendingDownpour.rain.shelters = shelters.ToArray();
                        pendingDownpour.rain.puddles = PuddleSpans.ToArray();
                    }
                }
                pendingDownpour = null;
            }
        }
    }
}
