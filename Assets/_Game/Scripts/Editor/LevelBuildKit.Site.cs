using UnityEngine;
using Object = UnityEngine.Object;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// The building site's own hazards (they replace the rolling pipes): its vehicle gate on the footpath, where a banksman
    /// in hi-vis holds a STOP / GO board while the site's digger and pickup come out across the footpath to the road, and its
    /// builders walking the footpath in hi-vis and hard hats.
    /// </summary>
    public static partial class LevelBuildKit
    {
        static readonly Color HiVis = new Color(1f, 0.55f, 0.12f);
        static readonly Color HardHatYellow = new Color(1f, 0.85f, 0.15f);

        public partial class TrackBuilder
        {
            /// <summary>
            /// The site's vehicle gate across the footpath from <paramref name="fromX"/> to <paramref name="toX"/>: a concrete
            /// access road comes out of the site (behind the footpath) to the road in front, the sliding gate stands open beside
            /// it, and the banksman at the far gatepost shows GO (walk across), GO flashing (hurry) and STOP (the digger and the
            /// pickup come out across the footpath; the kid or the ball in the gateway loses the ball). It works as a crossing
            /// (Hazards.Crossing), with longer, slower vehicle turns.
            /// </summary>
            public void SiteExit(float fromX, float toX, float phaseOffset = 0f, float groundTop = 0f)
            {
                float width = toX - fromX;
                float center = (fromX + toX) * 0.5f;
                Coaching.Mark("siteexit", fromX, toX);

                // The access road: concrete, no zebra (StreetBuilder's side street without its stripes), with yellow and black
                // hatching where it meets the footpath.
                OpenAreas.Add(new Vector2(fromX - 0.8f, toX + 0.8f));
                StreetBuilder.CrossingStreet(root, fromX - 0.8f, toX + 0.8f, groundTop, false);
                var hatch = new GameObject("GateHatching").transform;
                hatch.SetParent(root, false);
                bool yellow = true;
                for (float x = fromX - 0.6f; x < toX + 0.6f; x += 0.45f, yellow = !yellow)
                    StreetBuilder.Solid(hatch, "Hatch", new Vector3(x + 0.22f, groundTop + 0.012f, StreetBuilder.PathHalf + 0.25f), new Vector3(0.44f, 0.02f, 0.4f),
                        yellow ? new Color(0.98f, 0.8f, 0.15f) : new Color(0.12f, 0.12f, 0.13f));

                var go = new GameObject("SiteExit");
                go.transform.SetParent(root, false);
                go.transform.position = new Vector2(center, groundTop + 1.25f);
                var trigger = go.AddComponent<BoxCollider2D>();
                trigger.isTrigger = true;
                trigger.size = new Vector2(width, 2.5f);
                var gate = go.AddComponent<Hazards.Crossing>();
                gate.phaseOffset = phaseOffset;
                gate.loseKey = "lose.digger";
                // Walkers get a good while; the vehicles come out slowly and take longer to clear.
                gate.greenTime = 4f;
                gate.amberTime = 1.4f;
                gate.redTime = 4.6f;
                gate.queueGap = 7.5f;

                // The gateposts and the sliding gate, pushed open along the fence on the near side.
                float postZ = StreetBuilder.PathHalf + 0.45f;
                StreetBuilder.Model(root, "Works", "GatePillar", fromX - 0.5f, groundTop, postZ);
                StreetBuilder.Model(root, "Works", "GatePillar", toX + 0.5f, groundTop, postZ);
                StreetBuilder.Model(root, "Works", "SlidingGate", fromX - 2.4f, groundTop, postZ + 0.35f);

                // The banksman at the far gatepost, facing the kid, with the board on its pole held up beside him.
                float bx = toX + 1.1f, bz = StreetBuilder.PathHalf + 0.2f;
                Person(root, "Banksman", "Courier", bx, groundTop, bz, -20f, HiVis, new Color(0.22f, 0.26f, 0.4f), HardHatYellow, 1.02f);   // (the courier in hi-vis, his cap a hard hat's yellow)
                var board = new GameObject("BanksmanBoard");
                board.transform.SetParent(go.transform, false);
                board.transform.position = new Vector3(bx - 0.45f, groundTop, bz - 0.25f);
                var pole = new GameObject("Pole").transform;
                pole.SetParent(board.transform, false);
                Cylinder(pole, "Pole", board.transform.position + new Vector3(0f, 0.9f, 0f), board.transform.position + new Vector3(0f, 2.05f, 0f), 0.025f, new Color(0.3f, 0.3f, 0.32f));
                var banksman = go.AddComponent<Hazards.BanksmanBoard>();
                banksman.crossing = gate;
                banksman.board = board.transform;
                Vector3 head = board.transform.position + new Vector3(0f, 2.3f, 0f);
                banksman.stopFace = BoardFace(board.transform, "Stop", head, "STOP", new Color(0.86f, 0.16f, 0.14f));
                banksman.goFace = BoardFace(board.transform, "Go", head, "GO", new Color(0.12f, 0.62f, 0.26f));

                // The site's vehicles: the digger, then the site pickup, coming out of the site toward the camera.
                gate.cars = new Transform[2];
                var digger = new GameObject("Digger").transform;
                digger.SetParent(go.transform, false);
                digger.position = new Vector3(center, groundTop, 30f);
                var model = KitModel(digger, "Works", "Digger", digger.position, 90f);
                if (model == null) Object.DestroyImmediate(digger.gameObject);
                gate.cars[0] = model != null ? digger : Car(go.transform, "SiteVan", new Vector3(center, groundTop, 30f), 90f, Color.white, "Van");
                gate.cars[1] = Car(go.transform, "SitePickup", new Vector3(center, groundTop, 30f), 90f, Color.white, "Pickup");
                gate.groundY = groundTop;
                gate.stopLineZ = StreetBuilder.PathHalf + 3.6f;
            }

            /// <summary>One face of the banksman's board: a disc in <paramref name="colour"/> with its word in white, facing the camera.</summary>
            GameObject BoardFace(Transform board, string name, Vector3 centre, string word, Color colour)
            {
                var face = new GameObject(name);
                face.transform.SetParent(board, false);
                Cylinder(face.transform, "Disc", centre, centre + new Vector3(0f, 0f, 0.03f), 0.34f, colour);
                Cylinder(face.transform, "Rim", centre + new Vector3(0f, 0f, 0.005f), centre + new Vector3(0f, 0f, 0.025f), 0.37f, Color.white);
                var textGo = new GameObject("Word");
                textGo.transform.SetParent(face.transform, false);
                textGo.transform.position = centre + new Vector3(0f, 0f, -0.02f);
                var mesh = textGo.AddComponent<TextMesh>();
                mesh.text = word;
                mesh.font = signFont;
                mesh.fontSize = 48;
                mesh.characterSize = word.Length > 2 ? 0.045f : 0.06f;
                mesh.anchor = TextAnchor.MiddleCenter;
                mesh.alignment = TextAlignment.Center;
                mesh.color = Color.white;
                var renderer = textGo.GetComponent<MeshRenderer>();
                if (signFont != null) renderer.sharedMaterial = signFont.material;
                renderer.sortingOrder = 7;
                return face;
            }

            /// <summary>
            /// A builder walking the footpath between <paramref name="minX"/> and <paramref name="maxX"/> in hi-vis and a hard
            /// hat (a passer-by of the site: the ball bounces off them, the kid slips past; chip it over or wait for a gap).
            /// </summary>
            public void Builder(float minX, float maxX, float groundTop = 0f, float speed = 0.9f)
            {
                Walker(minX, maxX, HiVis, groundTop, speed, true);
            }
        }
    }
}
