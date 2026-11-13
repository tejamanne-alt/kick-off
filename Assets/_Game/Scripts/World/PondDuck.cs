using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A duck on the park pond (Animals kit): it paddles round the pond in slow, loose loops, each
    /// duck on its own line and at its own pace, now and then easing to a stop to dabble or look
    /// about before it paddles on, bobbing on the water and turning along its way.
    ///
    /// The same loop serves the Kamakura kit's koi and swimming turtle: a koi sweeps its tail (a Tail in links, so the
    /// sweep runs down it), a turtle paddles its flippers in turn; both settle as it slows to a stop (D19).
    /// </summary>
    public class PondDuck : AmbientAgent
    {
        public Part head;
        [Tooltip("Optional: a fish's tail (a Tail in links), swept side to side while it swims.")]
        public Part tail;
        [Tooltip("The tail's sweep either side (degrees) and beats per second.")]
        public float tailSweep = 22f, tailBeat = 1.6f;
        [Tooltip("A fish's head swinging against its tail (a share of the tail's sweep, degrees of the whole body's yaw): " +
                 "a real fish's body waves, its head recoiling as its tail sweeps.")]
        public float headRecoil;
        [Tooltip("Optional: a fish's pectoral fins (left then right), sculling in turn, most when it hangs still.")]
        public Part[] fins = new Part[0];
        [Tooltip("The fins' scull either side (degrees) and strokes per second.")]
        public float finSweep = 25f, finBeat = 0.8f;
        [Tooltip("Optional: a turtle's flippers, paddled in turn (front right and back left together, then the others).")]
        public Part[] flippers = new Part[0];
        [Tooltip("The flippers' sweep either side (degrees) and strokes per second.")]
        public float flipperSweep = 28f, flipperStroke = 0.9f;
        [Tooltip("The pond's centre (x, z), and the water's height.")]
        public float centerX, centerZ, waterY;
        [Tooltip("The pond's turn (degrees): its long axis runs along x at 0.")]
        public float pondYaw;
        [Tooltip("Half the loop's length and width (metres), well inside the water's edge.")]
        public float radiusX = 1.2f, radiusZ = 0.7f;
        [Tooltip("Paddling speed along the loop (metres per second); negative goes the other way round.")]
        public float paddle = 0.18f;

        float angle, rate, wobblePhase, wobbleRate;
        float stopUntil, nextStop;
        float yaw, yawVelocity;
        float dabbleStart = -10f;
        Vector3 last;

        protected override float Reach { get { return radiusX + 1f; } }

        protected override void Awake()
        {
            base.Awake();
            head.Capture();
            tail.Capture();
            Capture(flippers);
            Capture(fins);
            angle = Range(0f, Mathf.PI * 2f);
            wobblePhase = Range(0f, 10f);
            wobbleRate = Range(0.12f, 0.22f);
            nextStop = Time.time + Range(4f, 12f);
            rate = 1f;
            last = Position(angle);
            yaw = transform.eulerAngles.y;
        }

        Vector3 Position(float a)
        {
            // A loose loop: the radius breathes slowly so each lap takes a slightly different line.
            float breathe = 1f + 0.12f * Mathf.Sin(wobblePhase);
            float lx = Mathf.Cos(a) * radiusX * breathe, lz = Mathf.Sin(a) * radiusZ * breathe;
            float r = pondYaw * Mathf.Deg2Rad, c = Mathf.Cos(r), s = Mathf.Sin(r);
            // The pond's long axis is its own x, turned by pondYaw about the vertical (Unity yaw).
            return new Vector3(centerX + lx * c + lz * s, waterY, centerZ - lx * s + lz * c);
        }

        protected override void Tick(float dt)
        {
            // Now and then slow to a stop to dabble, then paddle on.
            bool stopped = Time.time < stopUntil;
            if (!stopped && Time.time >= nextStop)
            {
                stopUntil = Time.time + Range(2f, 5f);
                nextStop = stopUntil + Range(6f, 16f);
                dabbleStart = Time.time + 0.6f;
            }
            rate = Mathf.MoveTowards(rate, stopped ? 0f : 1f, 0.6f * dt);
            float perimeter = Mathf.PI * (radiusX + radiusZ);
            angle += paddle * rate * dt * Mathf.PI * 2f / Mathf.Max(0.5f, perimeter);
            wobblePhase += wobbleRate * dt;

            Vector3 p = Position(angle);
            Vector3 move = p - last;
            last = p;
            if (move.sqrMagnitude > 1e-8f)
            {
                float want = YawToward(move.x, move.z);
                yaw = Mathf.SmoothDampAngle(yaw, want, ref yawVelocity, 0.6f);
            }
            float bob = Mathf.Sin(Time.time * 1.7f + seed) * 0.006f;
            // a fish's head recoiling against its tail's sweep (the tail is set below from the same wave)
            float wave = Mathf.Sin((Time.time + seed) * tailBeat * Mathf.PI * 2f) * tailSweep * (0.25f + 0.75f * rate);
            float recoil = tail.ready ? -headRecoil * wave : 0f;
            transform.SetPositionAndRotation(new Vector3(p.x, waterY + bob, p.z), Quaternion.Euler(Mathf.Sin(Time.time * 1.3f + seed) * 2f, yaw + recoil, Mathf.Sin(Time.time * 1.1f) * 1.5f));

            // The head: dabbling (bill down) while stopped, glancing about as it paddles.
            float k = (Time.time - dabbleStart) / 1.4f;
            float dabble = k >= 0f && k <= 1f ? Mathf.Sin(k * Mathf.PI) * 40f : 0f;
            head.Set(4f + dabble, Vector3.forward, Mathf.Sin(Time.time * 0.7f + seed) * 18f * (1f - rate * 0.5f));
            if (stopped && k > 1.2f && Chance(0.01f)) dabbleStart = Time.time;
            // A fish's tail sweeping, a turtle's flippers paddling: full while it swims, a slow drift when it stops.
            float t = Time.time + seed;
            tail.Set(Mathf.Sin(t * tailBeat * Mathf.PI * 2f) * tailSweep * (0.25f + 0.75f * rate));
            for (int i = 0; i < flippers.Length; i++)
                flippers[i].Set(Mathf.Sin(t * flipperStroke * Mathf.PI * 2f + (i == 0 || i == 3 ? 0f : Mathf.PI)) * flipperSweep * rate);
            // a fish's pectoral fins sculling in turn, out from the body and back (left positive, right mirrored),
            // fullest as it hangs still, folded in a little as it swims fast
            for (int i = 0; i < fins.Length; i++)
                fins[i].Set((i == 0 ? 1f : -1f) * (0.5f + 0.5f * Mathf.Sin(t * finBeat * Mathf.PI * 2f + i * Mathf.PI)) * finSweep * (1f - 0.5f * rate));
        }
    }
}
