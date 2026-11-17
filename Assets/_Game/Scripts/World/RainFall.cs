using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Rain over a leg in the June rains (Kamakura's route 3, KM3-1 to KM3-3: the lane pictures are wet, the hydrangeas out):
    /// thin streaks falling, slanted by the wind, between the camera and the lane's pictures (behind the pictures they would
    /// only be hidden). One mesh of streaks is built once: a tile repeated along the street and up, moved whole every frame
    /// and snapped to the tile under the camera, so no vertex is touched after it is built. One draw call with the game's
    /// vertex-coloured material (Sprites/Default, the wires'); each streak a few pixels wide, so little overdraw; half as many
    /// on the Low tier (docs/PERFORMANCE.md).
    /// </summary>
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class RainFall : MonoBehaviour
    {
        [Tooltip("One tile of streaks: its width along the street and its height (metres). Four tiles across, three up.")]
        public float tileWidth = 14f, tileHeight = 6f;
        [Tooltip("The depth the streaks fall in: from in front of the camera to just before the lane's pictures.")]
        public float nearZ = -5f, farZ = 2.2f;
        public int streaksPerTile = 60;
        [Tooltip("Metres a second down, and along the street (the wind).")]
        public float fallSpeed = 9f, wind = -1.2f;
        public float length = 0.42f, width = 0.014f;
        public Color colour = new Color(0.82f, 0.86f, 0.92f, 0.3f);
        [Tooltip("The lowest the tiles reach, a little under the ground.")]
        public float baseY = -0.4f;
        [Tooltip("It rains only while the camera is over this stretch (a Holiday Run stage); unbounded in a level.")]
        public float fromX = float.NegativeInfinity, toX = float.PositiveInfinity;

        const int Across = 4, Up = 3;
        float fallen, blown;
        MeshRenderer view;

        void Awake()
        {
            var filter = GetComponent<MeshFilter>();
            filter.sharedMesh = Build(GraphicsQuality.Tier == GraphicsTier.Low ? streaksPerTile / 2 : streaksPerTile);
            var r = view = GetComponent<MeshRenderer>();
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
        }

        /// <summary>The streaks of every tile (the same pattern in each, so the tiles meet unseen), round the mesh's origin.</summary>
        Mesh Build(int perTile)
        {
            var rng = new System.Random(5309);
            var pattern = new Vector3[perTile];
            var shade = new float[perTile];
            for (int i = 0; i < perTile; i++)
            {
                pattern[i] = new Vector3((float)rng.NextDouble() * tileWidth, (float)rng.NextDouble() * tileHeight,
                    Mathf.Lerp(nearZ, farZ, (float)rng.NextDouble()));
                shade[i] = 0.55f + 0.45f * (float)rng.NextDouble();
            }
            Vector3 down = new Vector3(wind, -fallSpeed, 0f).normalized;
            Vector3 side = new Vector3(-down.y, down.x, 0f) * (width * 0.5f);
            int n = perTile * Across * Up;
            var vertices = new Vector3[n * 4];
            var colours = new Color[n * 4];
            var triangles = new int[n * 6];
            int k = 0;
            for (int tx = 0; tx < Across; tx++)
                for (int ty = 0; ty < Up; ty++)
                    for (int i = 0; i < perTile; i++, k++)
                    {
                        // tiles from two widths behind the camera's tile to two ahead, and up from the base
                        Vector3 top = pattern[i] + new Vector3((tx - 2) * tileWidth, ty * tileHeight, 0f);
                        Vector3 foot = top + down * length;
                        Color head = colour, tail = colour;
                        head.a *= shade[i];
                        tail.a = 0f;                      // the streak fades out up its length
                        vertices[k * 4] = foot - side;
                        vertices[k * 4 + 1] = foot + side;
                        vertices[k * 4 + 2] = top + side;
                        vertices[k * 4 + 3] = top - side;
                        colours[k * 4] = colours[k * 4 + 1] = head;
                        colours[k * 4 + 2] = colours[k * 4 + 3] = tail;
                        triangles[k * 6] = k * 4;
                        triangles[k * 6 + 1] = k * 4 + 2;
                        triangles[k * 6 + 2] = k * 4 + 1;
                        triangles[k * 6 + 3] = k * 4;
                        triangles[k * 6 + 4] = k * 4 + 3;
                        triangles[k * 6 + 5] = k * 4 + 2;
                    }
            var mesh = new Mesh { name = "Rain" };
            mesh.vertices = vertices;
            mesh.colors = colours;
            mesh.triangles = triangles;
            // it moves with the camera: never culled
            mesh.bounds = new Bounds(new Vector3(0f, tileHeight * Up * 0.5f, (nearZ + farZ) * 0.5f),
                new Vector3(tileWidth * (Across + 1), tileHeight * (Up + 1), Mathf.Abs(farZ - nearZ) + 2f));
            return mesh;
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            if (cam == null) return;
            // one stage's rain at a time in the Holiday Run, however many stages are loaded
            float cx = cam.transform.position.x;
            view.enabled = cx >= fromX && cx < toX;
            if (!view.enabled) return;
            // falls and blows on scaled time (still while the game is paused); one tile's worth and it starts over unseen
            fallen = Mathf.Repeat(fallen + Time.deltaTime * fallSpeed, tileHeight);
            blown = Mathf.Repeat(blown + Time.deltaTime * wind, tileWidth);
            float x = Mathf.Floor(cx / tileWidth) * tileWidth + blown;
            transform.position = new Vector3(x, baseY - fallen, 0f);
        }
    }
}
