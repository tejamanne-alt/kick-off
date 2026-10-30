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
        }

        public Motion[] motions = new Motion[0];
        [Tooltip("How far the whole animal wanders from its start (x, y, z amplitudes in metres).")]
        public Vector3 drift;
        public float driftSpeed = 1f;

        Quaternion[] rest;
        Vector3 home;
        float start;

        void Awake()
        {
            rest = new Quaternion[motions.Length];
            for (int i = 0; i < motions.Length; i++)
                rest[i] = motions[i].part != null ? motions[i].part.localRotation : Quaternion.identity;
            home = transform.localPosition;
            start = Random.value * 100f;
        }

        void Update()
        {
            float t = Time.time + start;
            for (int i = 0; i < motions.Length; i++)
            {
                var m = motions[i];
                if (m.part == null) continue;
                // A pecking or swishing rhythm: mostly sine, with a sharper return so it reads as a gesture.
                float s = Mathf.Sin(t * m.speed + m.phase);
                float angle = m.offset + m.amplitude * (s + 0.25f * Mathf.Sin(2f * (t * m.speed + m.phase)));
                m.part.localRotation = rest[i] * Quaternion.AngleAxis(angle, m.axis);
            }
            if (drift != Vector3.zero)
            {
                float d = t * driftSpeed;
                transform.localPosition = home + new Vector3(drift.x * Mathf.Sin(d * 0.7f), drift.y * Mathf.Sin(d * 1.9f), drift.z * Mathf.Sin(d * 0.5f + 1f));
            }
        }
    }
}
