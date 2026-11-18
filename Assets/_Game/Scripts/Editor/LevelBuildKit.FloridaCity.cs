using DribbleToSchool.Art;
using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.Challenges;
using DribbleToSchool.Core;
using DribbleToSchool.Player;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Florida's own play (docs/CITIES.md, "Florida (Miami), USA"), for the city's own routes (Editor/FloridaLevels): Little
    /// Havana's roosters and hens, the iguanas on the seawalls, the rental scooters left across the sidewalk, the pelicans, the
    /// downtown arcades and the downpour, the street sweeper, and the sets of the three mini-games (the Metrobus, Uncle Rey's boat
    /// at his dock, the corner drugstore), on the Miami kit (tools/blender/kit_buildings_mia.py). Each thing falls back to a
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
                    Audit.AddRoof(cx - wide * 0.5f, cx + wide * 0.5f, groundTop + 3.05f);
                    var block = KitModel(root, "Miami", deco, new Vector3(cx, groundTop, StreetBuilder.PathHalf + 0.05f));
                    if (block != null)
                    {
                        float native = KitSize("Miami", deco).x;
                        if (native > 1f) block.localScale = new Vector3(wide / native, 1f, 1f);
                        return;
                    }
                }
                shelters.Add(new Vector2(fromX, toX));
                Audit.AddRoof(fromX, toX, groundTop + 3.1f);
                var t = new GameObject("Arcade").transform;
                t.SetParent(root, false);
                t.position = new Vector3((fromX + toX) * 0.5f, groundTop, 0f);
                float w = toX - fromX, zc = 0.4f;
                Color c = colour ?? Stucco;
                Part(t, "Roof", new Vector3(0f, 3.15f, zc), new Vector3(w, 0.18f, StreetBuilder.PathHalf * 2f + 0.8f), c);
                Part(t, "Fascia", new Vector3(0f, 2.95f, -StreetBuilder.PathHalf - 0.35f), new Vector3(w, 0.3f, 0.08f), Color.Lerp(c, Coral, 0.4f));
                for (float x = -w * 0.5f; x <= w * 0.5f + 0.01f; x += Mathf.Max(1.5f, w / Mathf.Max(1, Mathf.Round(w / 2.6f))))
                    Part(t, "Column", new Vector3(x, 1.5f, StreetBuilder.PathHalf + 0.3f), new Vector3(0.28f, 3f, 0.28f), c);
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
                rain.heavyRain = RainSheet(go.transform, "HeavyRain", fromX, clearsAtX, 0.55f, 0.5f);
                rain.lightRain = RainSheet(go.transform, "LightRain", fromX, clearsAtX, 0.25f, 1.4f);
                pendingDownpour = rain;
            }

            Hazards.Downpour pendingDownpour;

            /// <summary>Streaks of rain over a stretch of street: thin see-through quads, slanted by the wind.</summary>
            GameObject RainSheet(Transform parent, string name, float fromX, float toX, float alpha, float spacing)
            {
                var sheet = new GameObject(name);
                sheet.transform.SetParent(parent, false);
                var rng = new System.Random(Mathf.RoundToInt(fromX * 7f) + name.Length);
                for (float x = fromX; x < toX; x += spacing)
                {
                    float y = 1f + (float)rng.NextDouble() * 5f;
                    var streak = FlatDecor("Streak", new Vector2(x + (float)rng.NextDouble() * spacing, y), new Vector2(0.03f, 0.9f), new Color(0.82f, 0.88f, 0.95f, alpha));
                    streak.transform.SetParent(sheet.transform, true);
                    streak.transform.rotation = Quaternion.Euler(0f, 0f, -12f);
                }
                return sheet;
            }

            /// <summary>
            /// A street sweeper truck working slowly up and down the kerb lane from <paramref name="fromX"/> to <paramref name="toX"/>:
            /// a moving platform (its flat back 1.3 m up) to ride, or to wait for.
            /// </summary>
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
                if (KitModel(go.transform, "Miami", "SweeperMIA", new Vector3(center.x, groundTop, 0.1f)) != null) return;
                Color white = new Color(0.95f, 0.95f, 0.93f);
                // (local to the block's middle, 0.75 m up: the body down to the wheels, the cab over the front, the brush under it)
                Part(go.transform, "Body", new Vector3(0f, -0.1f, 0.1f), new Vector3(width, 1.1f, 1.9f), white);
                Part(go.transform, "Cab", new Vector3(width * 0.5f - 0.45f, 0.95f, 0.1f), new Vector3(0.9f, 1.1f, 1.9f), white);
                Part(go.transform, "Stripe", new Vector3(0f, 0f, -0.86f), new Vector3(width, 0.12f, 0.02f), new Color(0.95f, 0.6f, 0.1f));
                Part(go.transform, "Brush", new Vector3(-width * 0.3f, -0.6f, -0.6f), new Vector3(0.6f, 0.3f, 0.6f), new Color(0.3f, 0.3f, 0.32f));
            }

            /// <summary>The finishing touches a Florida layout asks for once it has laid everything (the downpour's shelters).</summary>
            public void FloridaDone()
            {
                if (pendingDownpour != null) pendingDownpour.shelters = shelters.ToArray();
                pendingDownpour = null;
            }

            // ------------------------------------------------------------------ the mini-games' sets

            /// <summary>
            /// FL1-2's Metrobus at its stop on Calle Ocho (Challenges/BusRide): the Miami kit's 12 m city bus (its far side with the
            /// windows, the seats, the poles and the stop cord, the next-stop sign, the card reader by the driver), facing on along
            /// the street with its front door's middle at <paramref name="doorX"/> and the stop to its right, where the kid waits. Its
            /// near side (BusNearMIA: the doors and the windows toward the camera) is a separate model the ride takes away as the kid
            /// comes to the door, so the inside shows (nothing tall between the camera and the kid, LEARNINGS E10). It kneels at the
            /// stop (its floor at the footpath). Outside, the leg's district from the Miami plan (Calle Ocho's shops, then Brickell's
            /// towers) on a strip that slides past the windows as it drives, with the stop's shelter and sign, which it leaves behind.
            /// </summary>
            public BusRide Metrobus(float doorX)
            {
                const float length = 12f, kneel = 0.3f, stripFrom = -60f, stripLength = 310f;   // (tools/blender/miami_plan.py: BUS_STRIP)
                float nose = doorX + 1.65f, mid = nose - length * 0.5f;
                var ride = Challenge<BusRide>("The Metrobus", "Tap your card, ride with the ball at your feet, and pull the cord at your stop.", 0f, 1, 2, 3);
                var bus = new GameObject("Bus").transform;
                bus.SetParent(root, false);
                var body = new GameObject("Body").transform;
                body.SetParent(bus, false);
                var shell = KitModel(body, "Miami", "BusMIA", new Vector3(mid, -kneel, 0f));
                var near = KitModel(body, "Miami", "BusNearMIA", new Vector3(mid, -kneel, 0f));
                if (shell == null || near == null) Debug.LogWarning("[Kick Off] FL1-2: the Miami kit's bus is missing (Art/Models/Miami); the ride has no bus.");
                // The reader's screen (on the model by the driver), lit by the ride: red, then green when a card can be tapped.
                float readerX = nose - 0.86f;
                var light = new GameObject("ReaderLight");
                light.transform.SetParent(body, false);
                light.transform.localPosition = new Vector3(readerX, 1.315f - kneel, -0.885f);
                var box = light.AddComponent<Box3D>();
                box.size = new Vector3(0.18f, 0.15f, 0.02f);
                box.color = Color.white;
                light.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                box.Rebuild();

                // The doorway, shut while the bus rides (a collider only: the bus's own doors are its near side's).
                var door = new GameObject("BusDoor");
                door.transform.SetParent(root, false);
                door.transform.position = new Vector3(doorX + 0.25f, 1.5f, 0f);
                door.AddComponent<BoxCollider2D>().size = new Vector2(0.2f, 3f);

                // The street outside: the plan's Calle Ocho and Brickell on a strip that wraps, and the stop the bus leaves.
                var strip = new GameObject("Outside").transform;
                strip.SetParent(root, false);
                int placed = StreetBuilder.MiamiStreetStrip(strip, stripFrom, stripLength, 0f);
                for (int copy = 0; copy < 2; copy++)
                {
                    float dx = copy * stripLength;
                    StreetBuilder.Model(strip, "Florida", "BusShelterFL", doorX + 4.4f + dx, 0f, 2.7f);
                    StreetBuilder.Model(strip, "Miami", "StopSignMIA", doorX + 2.6f + dx, 0f, 1.75f);
                }
                if (placed == 0) Debug.LogWarning("[Kick Off] FL1-2: no street outside the bus (is Art/Models/Miami/MiamiDistricts.json there?)");

                ride.busBody = body;
                ride.busColliders = new Collider2D[0];
                ride.door = door.GetComponent<Collider2D>();
                ride.doorX = doorX;
                ride.readerX = readerX;
                ride.readerLight = light.GetComponent<MeshRenderer>();
                ride.inward = -1f;
                ride.nearSide = near != null ? near.gameObject : null;
                ride.pullOutZ = -4.6f;
                ride.street = strip;
                ride.stripLength = stripLength;
                return ride;
            }

            /// <summary>
            /// FL2-2's dock on the Miami River with Uncle Rey's fishing boat drifting off it (Challenges/MooringLine): the dock's
            /// timber deck to <paramref name="dockEnd"/>, a bollard behind the kid that the line pays out from, the river beyond, and
            /// the boat with its two cleats, its cabin and the science project on its roof. The ball becomes the line's knot.
            /// </summary>
            public MooringLine ReysDock(float dockEnd, float riverEnd, float boatX)
            {
                var line = Challenge<MooringLine>("Uncle Rey's Boat", "Throw the line onto both of the boat's cleats with KICK's aim.", 0f, 1, 2, 3);
                Color timber = new Color(0.55f, 0.42f, 0.3f), hull = new Color(0.95f, 0.95f, 0.93f), stripe = new Color(0.15f, 0.35f, 0.7f);
                // The river past the dock: its water, and falling in loses the line (back at the dock).
                float water = -1.1f;
                LoseZone("River", dockEnd, riverEnd, 0f, "lose.splash");
                SplashSurface("River", dockEnd, riverEnd, water, 0f);
                var river = new GameObject("River").transform;
                river.SetParent(root, false);
                var sea = Art.surfaces[ProceduralArt.Surface.Sea];
                var waterBox = StreetBuilder.Solid(river, "RiverWater", new Vector3((dockEnd + riverEnd) * 0.5f, water - 0.05f, 20f),
                    new Vector3(riverEnd - dockEnd + 8f, 0.1f, 44f), Color.white, sea);
                waterBox.faces = MeshBuilder.Faces.Top;
                waterBox.Rebuild();
                // The dock's deck planks and its piles, the bollard near its end.
                var dock = new GameObject("Dock").transform;
                dock.SetParent(root, false);
                Part(dock, "Deck", new Vector3(dockEnd - 6f, -0.08f, 0f), new Vector3(12f, 0.16f, StreetBuilder.PathHalf * 2f + 0.6f), timber);
                for (float x = dockEnd - 11.5f; x <= dockEnd; x += 2.5f)
                    foreach (float z in new[] { -StreetBuilder.PathHalf - 0.2f, StreetBuilder.PathHalf + 0.2f })
                        Part(dock, "Pile", new Vector3(x, -0.9f, z), new Vector3(0.25f, 1.8f, 0.25f), new Color(0.4f, 0.32f, 0.24f));
                var bollardGo = new GameObject("Bollard");
                bollardGo.transform.SetParent(dock, false);
                bollardGo.transform.position = new Vector3(dockEnd - 3.5f, 0.45f, 0.6f);
                if (KitModel(bollardGo.transform, "Miami", "BollardMIA", new Vector3(dockEnd - 3.5f, 0f, 0.6f)) == null)
                    Part(bollardGo.transform, "Post", new Vector3(0f, -0.2f, 0f), new Vector3(0.3f, 0.5f, 0.3f), new Color(0.2f, 0.2f, 0.22f));
                KitModel(dock, "Miami", "LineCoilMIA", new Vector3(dockEnd - 5.2f, 0f, 1.0f), 30f);

                // The boat: a kinematic body drifting off the dock, its deck and wheelhouse, its cleats at bow and stern.
                var boatGo = new GameObject("Boat");
                boatGo.transform.SetParent(root, false);
                boatGo.transform.position = new Vector2(boatX, water + 0.55f);
                var boatBody = boatGo.AddComponent<Rigidbody2D>();
                boatBody.bodyType = RigidbodyType2D.Kinematic;
                var deck = boatGo.AddComponent<BoxCollider2D>();
                deck.size = new Vector2(5.2f, 0.25f);
                deck.sharedMaterial = GroundMat;
                var bt = boatGo.transform;
                // The kit's fishing boat: its deck (0.95 m over its keel) level with the deck collider's top, so it draws 0.28 m;
                // its cabin forward of the open deck, outriggers up. The science project rides on the cabin's roof.
                float cabinX = -0.4f, roofY = 1.48f;
                if (KitModel(bt, "Miami", "FishingBoatMIA", boatGo.transform.position + new Vector3(0f, 0.125f - 0.95f, 0.4f)) != null)
                {
                    cabinX = 0.25f;
                    roofY = 0.125f + 1.3f + 0.04f;
                }
                else
                {
                    Part(bt, "Hull", new Vector3(0f, -0.35f, 0.4f), new Vector3(5.6f, 0.8f, 2f), hull);
                    Part(bt, "Stripe", new Vector3(0f, -0.2f, -0.61f), new Vector3(5.6f, 0.14f, 0.02f), stripe);
                    Part(bt, "Cabin", new Vector3(-0.4f, 0.75f, 0.9f), new Vector3(1.8f, 1.3f, 1.2f), hull);
                    Part(bt, "Outrigger", new Vector3(-0.4f, 2.2f, 1.2f), new Vector3(0.06f, 2.2f, 0.06f), Steel);
                }
                var project = new GameObject("Project");
                project.transform.SetParent(bt, false);
                project.transform.localPosition = new Vector3(cabinX, roofY, 0.4f);
                Part(project.transform, "Board", Vector3.zero, new Vector3(1f, 0.06f, 0.7f), new Color(0.9f, 0.88f, 0.8f));
                Part(project.transform, "Marsh", new Vector3(0f, 0.07f, 0f), new Vector3(0.8f, 0.08f, 0.5f), new Color(0.45f, 0.62f, 0.3f));
                Part(project.transform, "Water", new Vector3(0.15f, 0.08f, 0.05f), new Vector3(0.35f, 0.07f, 0.3f), new Color(0.3f, 0.6f, 0.75f));
                var cleats = new List<ChallengeTarget>();
                foreach (float dx in new[] { -2.2f, 2.2f })
                {
                    var cleat = new GameObject("Cleat");
                    cleat.transform.SetParent(bt, false);
                    cleat.transform.localPosition = new Vector3(dx, 0.25f, 0f);
                    var trigger = cleat.AddComponent<CircleCollider2D>();
                    trigger.isTrigger = true;
                    trigger.radius = 0.42f;
                    var face = new GameObject("Face");
                    face.transform.SetParent(cleat.transform, false);
                    face.transform.localPosition = new Vector3(0f, -0.08f, -0.5f);     // on the gunwale toward the camera
                    var shape = face.AddComponent<Box3D>();
                    shape.size = new Vector3(0.45f, 0.14f, 0.18f);
                    shape.color = Color.white;
                    face.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    shape.Rebuild();
                    var target = cleat.AddComponent<ChallengeTarget>();
                    target.face = face.GetComponent<MeshRenderer>();
                    target.idleColor = new Color(1f, 0.82f, 0.25f);
                    cleats.Add(target);
                }
                // Uncle Rey on deck by the wheelhouse: the cast's grown-up in his fishing shirt and cap (a stand-in figure without it).
                var uncle = new GameObject("UncleRey").transform;
                uncle.SetParent(bt, false);
                uncle.localPosition = new Vector3(1f, 0.1f, 0.9f);
                if (PasserbyNamed("Courier") != null)
                    Person(bt, "UncleReyFigure", "Courier", boatX + 1.3f, boatGo.transform.position.y + 0.125f, 0.9f, -60f,
                        new Color(0.95f, 0.6f, 0.45f), new Color(0.25f, 0.3f, 0.4f), new Color(0.1f, 0.25f, 0.5f), 1f);
                else
                {
                Part(uncle, "Legs", new Vector3(0f, 0.45f, 0f), new Vector3(0.32f, 0.9f, 0.25f), new Color(0.25f, 0.3f, 0.4f));
                Part(uncle, "Shirt", new Vector3(0f, 1.2f, 0f), new Vector3(0.45f, 0.6f, 0.3f), new Color(0.95f, 0.6f, 0.45f));
                Part(uncle, "Head", new Vector3(0f, 1.66f, 0f), new Vector3(0.24f, 0.28f, 0.24f), new Color(0.72f, 0.52f, 0.38f));
                Part(uncle, "Cap", new Vector3(0f, 1.83f, 0f), new Vector3(0.28f, 0.08f, 0.3f), new Color(0.1f, 0.25f, 0.5f));
                }

                // The line: a rope from the bollard to the knot at its end.
                var rope = line.gameObject.AddComponent<LineRenderer>();
                rope.sharedMaterial = Art.solid;
                rope.widthMultiplier = 0.045f;
                rope.startColor = rope.endColor = new Color(0.9f, 0.85f, 0.7f);
                rope.useWorldSpace = true;
                rope.positionCount = 3;

                line.boat = boatBody;
                line.cleats = cleats.ToArray();
                line.driftX = boatX;
                line.tiedX = dockEnd + 2.9f;
                line.dockEdgeX = dockEnd;
                line.bollard = bollardGo.transform;
                line.line = rope;
                line.project = project;
                // Once the ball exists: it becomes the line's knot (a monkey's fist), and the football's own look is hidden here.
                AfterRig = (kid, ball, ballLook) =>
                {
                    var knot = new GameObject("MonkeysFist");
                    knot.transform.SetParent(ball.transform, false);
                    var sphere = knot.AddComponent<SphereShape>();
                    sphere.radius = BallRadius * 0.85f;
                    sphere.color = new Color(0.88f, 0.8f, 0.6f);
                    knot.GetComponent<MeshRenderer>().sharedMaterial = Art.solid;
                    sphere.Rebuild();
                    knot.SetActive(false);
                    line.ballLook = ballLook;
                    line.knot = knot;
                };
                return line;
            }

            /// <summary>
            /// FL2-4's corner drugstore (Challenges/DrugstoreShopping): one long aisle of shelves along the back with poster boards,
            /// glue, markers and the rest, the counter and its till at the right, strip lights overhead. The shopping is played on the
            /// screen; the kid stands in the aisle.
            /// </summary>
            public DrugstoreShopping Drugstore(float fromX, float toX)
            {
                var shop = Challenge<DrugstoreShopping>("The Drugstore", "Find what's on the list, then pay with the fewest notes and coins.", 75f, 1, 2, 3);
                var t = new GameObject("Drugstore").transform;
                t.SetParent(root, false);
                float w = toX - fromX, cx = (fromX + toX) * 0.5f;
                // The kit's aisle (22 m: its shelves of painted goods along the back wall, the counter and till at the right end, the
                // terrazzo floor, the strip lights, the bright door), its front at the camera's side of the lane.
                var aisle = KitModel(t, "Miami", "DrugstoreAisleMIA", new Vector3(cx, 0f, -0.6f));
                if (aisle != null)
                {
                    float native = KitSize("Miami", "DrugstoreAisleMIA").x;
                    if (native > 1f) aisle.localScale = new Vector3(w / native, 1f, 1f);
                    return shop;
                }
                Part(t, "BackWall", new Vector3(cx, 1.6f, 2.6f), new Vector3(w, 3.2f, 0.2f), new Color(0.93f, 0.94f, 0.92f));
                Part(t, "Ceiling", new Vector3(cx, 3.25f, 0.8f), new Vector3(w, 0.1f, 3.8f), new Color(0.96f, 0.96f, 0.95f));
                for (float x = fromX + 1f; x < toX - 1f; x += 3f)
                    Part(t, "Lights", new Vector3(x, 3.17f, 0.6f), new Vector3(1.8f, 0.05f, 0.25f), new Color(1f, 1f, 0.97f));
                var rng = new System.Random(2024);
                Color[] goods = { Coral, Seafoam, new Color(0.95f, 0.85f, 0.3f), new Color(0.3f, 0.5f, 0.85f), Color.white, new Color(0.7f, 0.4f, 0.8f) };
                for (float x = fromX + 0.5f; x < toX - 4.5f; x += 2.4f)
                {
                    Part(t, "Shelf", new Vector3(x + 1.1f, 1f, 2.1f), new Vector3(2.2f, 2f, 0.7f), new Color(0.82f, 0.84f, 0.86f));
                    for (int row = 0; row < 4; row++)
                        for (int k = 0; k < 4; k++)
                            Part(t, "Goods", new Vector3(x + 0.35f + k * 0.5f, 0.3f + row * 0.48f, 1.78f), new Vector3(0.38f, 0.32f, 0.12f),
                                goods[rng.Next(goods.Length)]);
                }
                Part(t, "Counter", new Vector3(toX - 2.4f, 0.5f, 1.5f), new Vector3(2.6f, 1f, 1f), new Color(0.7f, 0.55f, 0.4f));
                Part(t, "Till", new Vector3(toX - 2.6f, 1.15f, 1.5f), new Vector3(0.5f, 0.3f, 0.4f), new Color(0.2f, 0.2f, 0.22f));
                return shop;
            }
        }
    }
}
