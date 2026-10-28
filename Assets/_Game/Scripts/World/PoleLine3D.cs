using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A row of concrete utility poles along the street with crossarms, the odd transformer,
    /// a yellow-and-black guard sleeve, and power lines that sag from pole to pole.
    /// Poles are one mesh; each wire is a LineRenderer built at load time.
    /// </summary>
    public class PoleLine3D : ProceduralShape
    {
        [Tooltip("Base of each pole (world space, on the pavement).")]
        public List<Vector3> poles = new List<Vector3>();
        public float height = 10f;
        public float wireSag = 0.9f;
        public float wireWidth = 0.035f;
        public Material wireMaterial;
        public Color poleColor = new Color(0.74f, 0.73f, 0.7f);

        static readonly Vector2[] WireAnchors = { new Vector2(-0.75f, -0.35f), new Vector2(0.75f, -0.35f), new Vector2(-0.55f, -1.15f), new Vector2(0f, 0f) };
        readonly List<LineRenderer> wires = new List<LineRenderer>();

        protected override void Build(MeshBuilder b)
        {
            var dark = new Color(0.45f, 0.45f, 0.48f);
            for (int i = 0; i < poles.Count; i++)
            {
                Vector3 p = poles[i] - transform.position;
                float h = height;
                b.Box(0, p + new Vector3(-0.15f, 0f, -0.15f), p + new Vector3(0.15f, h, 0.15f), poleColor);
                b.Box(0, p + new Vector3(-0.95f, h - 0.4f, -0.08f), p + new Vector3(0.95f, h - 0.28f, 0.08f), dark);   // crossarms
                b.Box(0, p + new Vector3(-0.7f, h - 1.2f, -0.08f), p + new Vector3(0.7f, h - 1.1f, 0.08f), dark);
                if (i % 2 == 0)
                    b.Box(0, p + new Vector3(0.18f, h - 3.4f, -0.25f), p + new Vector3(0.62f, h - 2.4f, 0.2f), new Color(0.66f, 0.68f, 0.7f));   // transformer
                for (int s = 0; s < 6; s++)   // guard sleeve
                {
                    Color c = s % 2 == 0 ? new Color(0.95f, 0.78f, 0.2f) : new Color(0.15f, 0.15f, 0.15f);
                    b.Box(0, p + new Vector3(-0.17f, 0.4f + s * 0.18f, -0.17f), p + new Vector3(0.17f, 0.58f + s * 0.18f, 0.17f), c);
                }
            }
            BuildWires();
        }

        void BuildWires()
        {
            var holder = transform.Find("Wires");
            if (holder == null)
            {
                holder = new GameObject("Wires").transform;
                holder.SetParent(transform, false);
                holder.gameObject.hideFlags = HideFlags.DontSave;
            }
            wires.Clear();
            holder.GetComponentsInChildren(true, wires);
            while (wires.Count < WireAnchors.Length)
            {
                var go = new GameObject("Wire");
                go.hideFlags = HideFlags.DontSave;
                go.transform.SetParent(holder, false);
                wires.Add(go.AddComponent<LineRenderer>());
            }
            if (poles.Count < 2) return;

            const int perSpan = 10;
            var points = new List<Vector3>();
            for (int w = 0; w < WireAnchors.Length; w++)
            {
                points.Clear();
                Vector2 a = WireAnchors[w];
                for (int i = 0; i < poles.Count - 1; i++)
                {
                    Vector3 p0 = poles[i] + new Vector3(a.x, height + a.y, 0f);
                    Vector3 p1 = poles[i + 1] + new Vector3(a.x, height + a.y, 0f);
                    for (int k = 0; k < perSpan; k++)
                    {
                        float t = k / (float)perSpan;
                        points.Add(Vector3.Lerp(p0, p1, t) + Vector3.down * wireSag * 4f * t * (1f - t));
                    }
                }
                points.Add(poles[poles.Count - 1] + new Vector3(a.x, height + a.y, 0f));

                var lr = wires[w];
                lr.useWorldSpace = true;
                lr.positionCount = points.Count;
                lr.SetPositions(points.ToArray());
                lr.widthMultiplier = wireWidth;
                lr.sharedMaterial = wireMaterial;
                lr.startColor = lr.endColor = new Color(0.12f, 0.12f, 0.15f);
                lr.numCapVertices = 0;
                lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                lr.receiveShadows = false;
            }
        }
    }
}
