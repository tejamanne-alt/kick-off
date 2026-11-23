using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Rain that falls (Hazards/Downpour sets how hard): thin streaks slanted by the wind, falling through the view from in front of
    /// the lane back to the shopfronts, each landing as a little splash on the paving or a ripple ring on a puddle. The streaks
    /// live in a window that follows the camera, so it rains wherever the kid is, and none fall in the lane's band under a shelter
    /// (the arcades). Everything is one mesh rewritten each frame: one draw call, about 2,000 vertices at full strength.
    /// It replaced still streaks that hung in the air and read as scratches on the screen (docs/LEARNINGS.md E15).
    /// </summary>
    [RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class RainCurtain : MonoBehaviour
    {
        [Header("How much")]
        [Tooltip("Streaks at full strength (intensity 1).")]
        public int streaks = 240;
        [Tooltip("0 dry, about 0.3 a steady rain, 1 a cloudburst. Set by the downpour; the rain eases toward it.")]
        [Range(0f, 1f)] public float intensity;
        [Tooltip("How fast the rain follows a change of intensity (per second).")]
        public float ease = 1.2f;

        [Header("How it falls")]
        public float fallSpeed = 13f;
        [Tooltip("Sideways drift for each metre it falls (the wind): negative blows it to the left.")]
        public float slant = -0.2f;
        public float streakLength = 0.55f;
        public float streakWidth = 0.022f;
        public Color streakColor = new Color(0.8f, 0.86f, 0.94f, 0.42f);

        [Header("Where")]
        [Tooltip("The ground the drops land on.")]
        public float groundY;
        [Tooltip("The depth band it falls in: from in front of the lane back to the shopfronts.")]
        public float zNear = -4f, zFar = 1.7f;
        [Tooltip("The lane's band (depth) that the shelters cover.")]
        public float shelterZFrom = -1.7f;
        [Tooltip("Stretches of street (x from, x to) under a roof: no rain falls in the lane's band there.")]
        public Vector2[] shelters;
        [Tooltip("Puddles (x from, x to) on the lane: a drop landing in one makes a ripple, not a splash.")]
        public Vector2[] puddles;
        public float puddleZ = 1.3f;
        [Tooltip("No rain past here (the storm has passed).")]
        public float clearsAtX = float.PositiveInfinity;

        [Header("Landing")]
        public int splashes = 48;
        public int ripples = 28;
        public Color splashColor = new Color(0.86f, 0.9f, 0.96f, 0.5f);

        const int RippleSegments = 8;

        struct Drop { public Vector3 p; public float speed, length; }
        struct Mark { public Vector3 p; public float age, life; }

        Drop[] drops;
        Mark[] splashMarks, rippleMarks;
        int nextSplash, nextRipple;
        float shown;
        Mesh mesh;
        Vector3[] verts;
        Color[] colors;
        Camera cam;
        System.Random rng;

        void Awake()
        {
            rng = new System.Random(1931);
            drops = new Drop[Mathf.Max(1, streaks)];
            splashMarks = new Mark[Mathf.Max(1, splashes)];
            rippleMarks = new Mark[Mathf.Max(1, ripples)];
            int quads = drops.Length + splashMarks.Length * 2 + rippleMarks.Length * RippleSegments;
            verts = new Vector3[quads * 4];
            colors = new Color[quads * 4];
            var tris = new int[quads * 6];
            var uv = new Vector2[quads * 4];
            for (int q = 0; q < quads; q++)
            {
                int v = q * 4, t = q * 6;
                tris[t] = v; tris[t + 1] = v + 1; tris[t + 2] = v + 2;
                tris[t + 3] = v; tris[t + 4] = v + 2; tris[t + 5] = v + 3;
                uv[v] = new Vector2(0f, 0f); uv[v + 1] = new Vector2(0f, 1f); uv[v + 2] = new Vector2(1f, 1f); uv[v + 3] = new Vector2(1f, 0f);
            }
            mesh = new Mesh { name = "Rain" };
            mesh.MarkDynamic();
            mesh.vertices = verts;
            mesh.colors = colors;
            mesh.uv = uv;
            mesh.triangles = tris;
            GetComponent<MeshFilter>().sharedMesh = mesh;
            var r = GetComponent<MeshRenderer>();
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            r.receiveShadows = false;
            transform.position = Vector3.zero;
            transform.rotation = Quaternion.identity;
            transform.localScale = Vector3.one;
        }

        void OnDestroy()
        {
            if (mesh != null) Destroy(mesh);
        }

        /// <summary>The window of street the camera sees, widened a little: x from and to, and the top of the fall.</summary>
        bool Window(out float x0, out float x1, out float top)
        {
            x0 = x1 = top = 0f;
            if (cam == null) cam = Camera.main;
            if (cam == null) return false;
            var c = cam.transform.position;
            float depth = Mathf.Max(1f, zFar - c.z);
            float halfH = depth * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
            float halfW = halfH * cam.aspect;
            x0 = c.x - halfW - 1.5f;
            x1 = c.x + halfW + 1.5f;
            top = c.y + halfH + 1f;
            return true;
        }

        bool Sheltered(float x, float z)
        {
            if (z < shelterZFrom || shelters == null) return false;
            for (int i = 0; i < shelters.Length; i++)
                if (x >= shelters[i].x && x <= shelters[i].y) return true;
            return false;
        }

        bool InPuddle(float x, float z)
        {
            if (puddles == null || Mathf.Abs(z) > puddleZ) return false;
            for (int i = 0; i < puddles.Length; i++)
                if (x >= puddles[i].x && x <= puddles[i].y) return true;
            return false;
        }

        float Rand(float a, float b) { return a + (float)rng.NextDouble() * (b - a); }

        void Spawn(ref Drop d, float x0, float x1, float top, bool anywhere)
        {
            d.p = new Vector3(Rand(x0, x1), anywhere ? Rand(groundY, top) : top + Rand(0f, 2f), Rand(zNear, zFar));
            d.speed = fallSpeed * Rand(0.85f, 1.15f);
            d.length = streakLength * Rand(0.75f, 1.25f);
        }

        void Start()
        {
            float x0, x1, top;
            if (!Window(out x0, out x1, out top)) { x0 = -10f; x1 = 10f; top = 8f; }
            for (int i = 0; i < drops.Length; i++) Spawn(ref drops[i], x0, x1, top, true);
        }

        void LateUpdate()
        {
            float dt = Mathf.Min(Time.deltaTime, 0.05f);
            shown = Mathf.MoveTowards(shown, Mathf.Clamp01(intensity), ease * dt);
            float x0, x1, top;
            if (!Window(out x0, out x1, out top)) return;
            float width = x1 - x0;
            int active = Mathf.RoundToInt(drops.Length * shown);
            Vector3 dir = new Vector3(slant, -1f, 0f).normalized;
            float alpha = Mathf.Lerp(0.55f, 1f, shown);

            for (int i = 0; i < drops.Length; i++)
            {
                ref Drop d = ref drops[i];
                int v = i * 4;
                // Keep every drop in the window as the camera moves (they wrap round it), falling or not, so the rain is
                // already spread through the view when it starts.
                if (d.p.x < x0) d.p.x += width; else if (d.p.x > x1) d.p.x -= width;
                if (i >= active) { Hide(v); continue; }
                d.p += dir * d.speed * dt;
                if (d.p.y <= groundY)
                {
                    if (d.p.x < clearsAtX && !Sheltered(d.p.x, d.p.z))
                    {
                        if (InPuddle(d.p.x, d.p.z)) Land(rippleMarks, ref nextRipple, d.p, Rand(0.45f, 0.65f), i % 3 == 0);
                        else Land(splashMarks, ref nextSplash, d.p, Rand(0.12f, 0.2f), i % 2 == 0);
                    }
                    Spawn(ref d, x0, x1, top, false);
                }
                if (d.p.x >= clearsAtX || Sheltered(d.p.x, d.p.z)) { Hide(v); continue; }
                Streak(v, d.p, d.p - dir * d.length, streakWidth, new Color(streakColor.r, streakColor.g, streakColor.b, streakColor.a * alpha));
            }

            int q = drops.Length;
            for (int i = 0; i < splashMarks.Length; i++, q += 2)
            {
                ref Mark m = ref splashMarks[i];
                if (m.life <= 0f) { Hide(q * 4); Hide(q * 4 + 4); continue; }
                m.age += dt;
                if (m.age >= m.life) { m.life = 0f; Hide(q * 4); Hide(q * 4 + 4); continue; }
                float k = m.age / m.life, h = 0.05f + 0.07f * k;
                var c = new Color(splashColor.r, splashColor.g, splashColor.b, splashColor.a * (1f - k));
                // A crown: two little jets flicking up and out.
                Streak(q * 4, m.p, m.p + new Vector3(-0.45f * h, h, 0f), 0.012f, c);
                Streak(q * 4 + 4, m.p, m.p + new Vector3(0.45f * h, h, 0f), 0.012f, c);
            }

            for (int i = 0; i < rippleMarks.Length; i++, q += RippleSegments)
            {
                ref Mark m = ref rippleMarks[i];
                bool on = m.life > 0f;
                if (on) { m.age += dt; if (m.age >= m.life) { m.life = 0f; on = false; } }
                if (!on)
                {
                    for (int s = 0; s < RippleSegments; s++) Hide((q + s) * 4);
                    continue;
                }
                float k = m.age / m.life, r = 0.03f + 0.2f * k;
                var c = new Color(splashColor.r, splashColor.g, splashColor.b, splashColor.a * 0.9f * (1f - k));
                // A ring on the water: eight short segments round a circle, flat on the puddle.
                for (int s = 0; s < RippleSegments; s++)
                {
                    float a0 = s / (float)RippleSegments * Mathf.PI * 2f, a1 = (s + 1) / (float)RippleSegments * Mathf.PI * 2f;
                    var p0 = m.p + new Vector3(Mathf.Cos(a0) * r, 0.015f, Mathf.Sin(a0) * r);
                    var p1 = m.p + new Vector3(Mathf.Cos(a1) * r, 0.015f, Mathf.Sin(a1) * r);
                    FlatSegment((q + s) * 4, p0, p1, 0.012f, c);
                }
            }

            mesh.vertices = verts;
            mesh.colors = colors;
            var cpos = cam.transform.position;
            mesh.bounds = new Bounds(new Vector3(cpos.x, (groundY + top) * 0.5f, (zNear + zFar) * 0.5f), new Vector3(width + 4f, top - groundY + 4f, zFar - zNear + 4f));
        }

        void Land(Mark[] marks, ref int next, Vector3 at, float life, bool keep)
        {
            if (!keep) return;     // not every drop leaves a mark: enough to read as rain landing
            marks[next] = new Mark { p = new Vector3(at.x, groundY + 0.01f, at.z), age = 0f, life = life };
            next = (next + 1) % marks.Length;
        }

        void Hide(int v)
        {
            verts[v] = verts[v + 1] = verts[v + 2] = verts[v + 3] = Vector3.zero;
            colors[v] = colors[v + 1] = colors[v + 2] = colors[v + 3] = Color.clear;
        }

        /// <summary>A thin quad facing the camera (the view is side-on: the quad stands in the x-y plane) from a to b.</summary>
        void Streak(int v, Vector3 a, Vector3 b, float w, Color c)
        {
            Vector2 along = new Vector2(b.x - a.x, b.y - a.y);
            Vector2 n = along.sqrMagnitude > 1e-8f ? new Vector2(-along.y, along.x).normalized * (w * 0.5f) : new Vector2(w * 0.5f, 0f);
            var side = new Vector3(n.x, n.y, 0f);
            verts[v] = a - side; verts[v + 1] = b - side; verts[v + 2] = b + side; verts[v + 3] = a + side;
            colors[v] = colors[v + 3] = c;
            colors[v + 1] = colors[v + 2] = new Color(c.r, c.g, c.b, c.a * 0.25f);   // the streak's tail fades
        }

        /// <summary>A thin quad lying flat on the ground (x-z plane) from a to b.</summary>
        void FlatSegment(int v, Vector3 a, Vector3 b, float w, Color c)
        {
            Vector2 along = new Vector2(b.x - a.x, b.z - a.z);
            Vector2 n = along.sqrMagnitude > 1e-8f ? new Vector2(-along.y, along.x).normalized * (w * 0.5f) : new Vector2(0f, w * 0.5f);
            var side = new Vector3(n.x, 0f, n.y);
            verts[v] = a - side; verts[v + 1] = b - side; verts[v + 2] = b + side; verts[v + 3] = a + side;
            colors[v] = colors[v + 1] = colors[v + 2] = colors[v + 3] = c;
        }
    }
}
