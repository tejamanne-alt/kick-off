using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A shore crab at the water's edge (Animals kit, facing the camera, walking sideways along
    /// x): it scuttles in short bursts and stops, claws up, sidles round a little, and now and then
    /// digs itself into the sand and is gone for a while before it pops up again nearby.
    /// </summary>
    public class ShoreCrab : AmbientAgent
    {
        public Transform model;
        public Part clawL, clawR;
        [Tooltip("Ground height where there is no baked ground strip.")]
        public float baseY;
        public float homeX;
        public float roam = 2.2f;

        enum State { Pause, Scuttle, Burrow, Buried, Emerge }

        State state;
        float until, started;
        float x, target, speed, dir = 1f;
        float sink;
        float yaw, yawVelocity, targetYaw;
        float clawPhase;

        protected override float Reach { get { return roam + 1f; } }

        protected override void Awake()
        {
            base.Awake();
            clawL.Capture();
            clawR.Capture();
            x = transform.position.x;
            yaw = targetYaw = transform.eulerAngles.y;
            clawPhase = Range(0f, 10f);
            Pause(Range(0.5f, 2f));
        }

        void Pause(float time)
        {
            state = State.Pause;
            until = Time.time + time;
        }

        protected override void Tick(float dt)
        {
            float lift = 0f, rock = 0f;
            switch (state)
            {
                case State.Pause:
                    speed = Mathf.MoveTowards(speed, 0f, 6f * dt);
                    if (Time.time >= until) Decide();
                    break;
                case State.Scuttle:
                {
                    float left = target - x;
                    // Quick to get going and quick to stop, as crabs are.
                    float want = 1.1f * Mathf.Clamp01(Mathf.Abs(left) / 0.08f + 0.2f);
                    speed = Mathf.MoveTowards(speed, want, 7f * dt);
                    float step = Mathf.Min(Mathf.Abs(left), speed * dt);
                    x += Mathf.Sign(left) * step;
                    lift = Mathf.Abs(Mathf.Sin(Time.time * 32f)) * 0.006f * speed;
                    rock = Mathf.Sin(Time.time * 32f) * 3f * speed;
                    if (Mathf.Abs(target - x) <= 0.002f)
                    {
                        speed = 0f;
                        Pause(Range(0.6f, 3f));
                    }
                    break;
                }
                case State.Burrow:
                {
                    // Wriggling down into the sand.
                    float k = (Time.time - started) / 0.9f;
                    sink = Mathf.Lerp(0f, 0.16f, Ease(k));
                    rock = Mathf.Sin(Time.time * 40f) * 6f * (1f - k);
                    if (k >= 1f)
                    {
                        state = State.Buried;
                        until = Time.time + Range(4f, 12f);
                        if (model != null) model.gameObject.SetActive(false);
                    }
                    break;
                }
                case State.Buried:
                    if (Time.time >= until)
                    {
                        // Up again, a little way off.
                        float lo = homeX - roam, hi = homeX + roam;
                        GroundRange(ref lo, ref hi);
                        x = Mathf.Clamp(x + Range(-0.8f, 0.8f), lo, hi);
                        state = State.Emerge;
                        started = Time.time;
                        if (model != null) model.gameObject.SetActive(true);
                    }
                    break;
                case State.Emerge:
                {
                    float k = (Time.time - started) / 0.6f;
                    sink = Mathf.Lerp(0.16f, 0f, Ease(k));
                    rock = Mathf.Sin(Time.time * 36f) * 5f * (1f - k);
                    if (k >= 1f) Pause(Range(1f, 2.5f));
                    break;
                }
            }

            yaw = Mathf.SmoothDampAngle(yaw, targetYaw, ref yawVelocity, 0.25f);
            float y = GroundY(x, baseY) - sink + lift;
            transform.SetPositionAndRotation(new Vector3(x, y, transform.position.z), Quaternion.Euler(0f, yaw, rock));
            // Claws: a lazy wave while it waits, snapping as it runs.
            clawPhase += dt * (state == State.Scuttle ? 9f : 2.6f);
            float wave = state == State.Scuttle ? 12f : 22f;
            clawL.Set(8f + wave * Mathf.Sin(clawPhase));
            clawR.Set(8f + wave * Mathf.Sin(clawPhase + Mathf.PI * 0.6f));
        }

        void Decide()
        {
            float r = Rand01();
            if (r < 0.62f)
            {
                // A burst sideways, mostly carrying on the way it was going, back toward home if far.
                float lo = homeX - roam, hi = homeX + roam;
                GroundRange(ref lo, ref hi);
                if (Chance(0.3f)) dir = -dir;
                if (x > hi - 0.3f) dir = -1f;
                else if (x < lo + 0.3f) dir = 1f;
                target = Mathf.Clamp(x + dir * Range(0.25f, 0.9f), lo, hi);
                state = State.Scuttle;
            }
            else if (r < 0.75f)
            {
                state = State.Burrow;
                started = Time.time;
            }
            else
            {
                // Turn a little this way or that and wait.
                targetYaw = Range(-25f, 25f);
                Pause(Range(1f, 3f));
            }
        }
    }
}
