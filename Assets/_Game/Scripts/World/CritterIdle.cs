using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Little idle motions for the animals around the street (Animals kit): each listed part swings
    /// from its rest pose about an axis in its own space (a pigeon pecking, a cat swishing its tail,
    /// a butterfly's wings), and the whole animal can drift and bob a little (a butterfly flitting,
    /// a duck on the water). Phases start at random, so a group never moves in step.
    /// </summary>
    public class CritterIdle : MonoBehaviour
    {
        [System.Serializable]
        public struct Motion
        {
            public Transform part;
            [Tooltip("Rotation axis in the part's own space.")]
            public Vector3 axis;
            [Tooltip("Swing in degrees either side of offset.")]
            public float amplitude;
            [Tooltip("Radians per second.")]
            public float speed;
            [Tooltip("Degrees the swing is centred on.")]
            public float offset;
            [Tooltip("Radians, added to the random start phase.")]
            public float phase;
            [Tooltip("A bird looking about: quick turns to a new direction, each held a while (Look), not a smooth sway.")]
            public bool snap;
        }

        public Motion[] motions = new Motion[0];
        [Tooltip("How far the whole animal wanders from its start (x, y, z amplitudes in metres).")]
        public Vector3 drift;
        public float driftSpeed = 1f;

        Quaternion[] rest;
        PartChain[] chains;     // a part in links (a Tail with Tail2, Tail3) bends link by link
        Vector3 home;
        float start;

        void Awake()
        {
            rest = new Quaternion[motions.Length];
            chains = new PartChain[motions.Length];
            for (int i = 0; i < motions.Length; i++)
            {
                rest[i] = motions[i].part != null ? motions[i].part.localRotation : Quaternion.identity;
                if (motions[i].part != null)
                {
                    var c = PartChain.Find(motions[i].part, motions[i].axis);
                    if (c.Links > 1) chains[i] = c;
                }
            }
            home = transform.localPosition;
            start = Random.value * 100f;
        }

        static readonly float[] Looks = { 0f, 0.85f, 0.35f, -0.6f, -0.15f, 0.55f, -0.9f, -0.35f };

        /// <summary>A bird's look about at x (radians; the pattern repeats every 2 pi), -1..1 (D21): it turns its head
        /// quickly to a new direction (a fifth of each spell, eased) and holds it, eight spells a turn, as a perched bird
        /// does, where a smooth sway read as a toy's. The asset review moves the same (asset_review.py: look_about).</summary>
        public static float Look(float x)
        {
            float u = x / (2f * Mathf.PI);
            u -= Mathf.Floor(u);
            int n = Looks.Length;
            float f = u * n;
            int i = Mathf.Min(n - 1, (int)f);
            float k = Mathf.Clamp01((f - i) / 0.2f);
            k = k * k * (3f - 2f * k);
            return Mathf.Lerp(Looks[(i + n - 1) % n], Looks[i], k);
        }

        void Update()
        {
            float t = Time.time + start;
            for (int i = 0; i < motions.Length; i++)
            {
                var m = motions[i];
                if (m.part == null) continue;
                // A pecking or swishing rhythm: mostly sine, with a sharper return so it reads as a gesture; a bird's
                // look about in quick turns and holds.
                float s = Mathf.Sin(t * m.speed + m.phase);
                float angle = m.snap ? m.offset + m.amplitude * Look(t * m.speed + m.phase)
                                     : m.offset + m.amplitude * (s + 0.25f * Mathf.Sin(2f * (t * m.speed + m.phase)));
                if (chains[i] != null) chains[i].Set(angle, Time.deltaTime);
                else m.part.localRotation = rest[i] * Quaternion.AngleAxis(angle, m.axis);
            }
            if (drift != Vector3.zero)
            {
                float d = t * driftSpeed;
                transform.localPosition = home + new Vector3(drift.x * Mathf.Sin(d * 0.7f), drift.y * Mathf.Sin(d * 1.9f), drift.z * Mathf.Sin(d * 0.5f + 1f));
            }
        }
    }
}
