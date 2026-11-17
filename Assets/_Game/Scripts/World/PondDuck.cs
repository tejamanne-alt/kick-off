using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A duck on the park pond (Animals kit): it paddles round the pond in slow, loose loops, each
    /// duck on its own line and at its own pace, now and then easing to a stop to dabble or look
    /// about before it paddles on, bobbing on the water and turning along its way.
    /// </summary>
    public class PondDuck : AmbientAgent
    {
        public Part head;
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
            transform.SetPositionAndRotation(new Vector3(p.x, waterY + bob, p.z), Quaternion.Euler(Mathf.Sin(Time.time * 1.3f + seed) * 2f, yaw, Mathf.Sin(Time.time * 1.1f) * 1.5f));

            // The head: dabbling (bill down) while stopped, glancing about as it paddles.
            float k = (Time.time - dabbleStart) / 1.4f;
            float dabble = k >= 0f && k <= 1f ? Mathf.Sin(k * Mathf.PI) * 40f : 0f;
            head.Set(4f + dabble, Vector3.forward, Mathf.Sin(Time.time * 0.7f + seed) * 18f * (1f - rate * 0.5f));
            if (stopped && k > 1.2f && Chance(0.01f)) dabbleStart = Time.time;
        }
    }
}
