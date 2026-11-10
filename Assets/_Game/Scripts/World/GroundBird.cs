using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A bird on the ground (Animals kit): a pigeon pecking about the pavement with its friends, or
    /// a gull standing on the sand. It potters a few steps at a time (the pigeon nodding, the gull
    /// hopping), turns, pecks, and when the kid runs close it takes off: the standing model gives
    /// way to the flying one, which flaps up and away from the kid in an arc until it is out of
    /// sight. A while later, once its spot is out of sight too, it is back there on the ground.
    /// </summary>
    public class GroundBird : AmbientAgent
    {
        [Tooltip("The bird on the ground.")]
        public Transform standing;
        [Tooltip("The same bird in flight (wings out), hidden while it is on the ground.")]
        public Transform flying;
        [Tooltip("The head, pecking about its axis (positive: beak down). Optional.")]
        public Part head;
        [Tooltip("The flying model's wings, flapped about their axis (the first one mirrored).")]
        public Part wingA, wingB;
        [Tooltip("Ground height where there is no baked ground strip.")]
        public float baseY;
        public float homeX, homeZ;
        [Tooltip("How far along the street it potters from home.")]
        public float roam = 0.8f;
        public float zMin = 0.9f, zMax = 1.4f;
        public float walkSpeed = 0.3f;
        [Tooltip("Gulls hop; pigeons walk nodding their heads.")]
        public bool hopper;
        [Tooltip("The kid this close (metres) makes it fly off.")]
        public float startle = 2.6f;
        public float flightSpeed = 3.5f;
        [Tooltip("Speed in depth as it flies off (+ away from the camera): out to sea for a gull, out over the street from under the awnings for a pigeon.")]
        public float flightZMin = 0.6f, flightZMax = 1.8f;

        enum State { Idle, Walk, Fly, Gone }

        State state;
        float until;
        float x, y, z, tx, tz;
        float speed;
        float yaw, yawVelocity, targetYaw;
        float phase, flap, pitch;
        float peckStart = -10f, nextPeck;
        float flownAt;
        Vector3 velocity;

        protected override float Reach { get { return roam + 1f; } }

        protected override void Awake()
        {
            base.Awake();
            head.Capture();
            wingA.Capture();
            wingB.Capture();
            yaw = targetYaw = transform.eulerAngles.y;
            Land(homeX, homeZ);
            until = Time.time + Range(0.5f, 3f);
        }

        void Land(float atX, float atZ)
        {
            x = tx = atX;
            z = tz = atZ;
            y = GroundY(x, baseY);
            speed = 0f;
            pitch = 0f;
            state = State.Idle;
            if (standing != null) standing.gameObject.SetActive(true);
            if (flying != null) flying.gameObject.SetActive(false);
            Apply();
        }

        void Hide()
        {
            state = State.Gone;
            until = Time.time + Range(9f, 22f);
            if (standing != null) standing.gameObject.SetActive(false);
            if (flying != null) flying.gameObject.SetActive(false);
        }

        protected override void Sleep()
        {
            // Out of sight: a bird in the air is gone; one that has been gone a while comes home.
            if (state == State.Fly) Hide();
            else if (state == State.Gone && Time.time >= until && AmbientView.OutsideBy(homeX, homeZ) > 1.5f) Land(homeX + Range(-roam, roam) * 0.5f, homeZ);
        }

        protected override void Tick(float dt)
        {
            switch (state)
            {
                case State.Idle:
                case State.Walk:
                    OnGround(dt);
                    break;
                case State.Fly:
                    Fly(dt);
                    break;
                case State.Gone:
                    if (Time.time >= until && AmbientView.OutsideBy(homeX, homeZ) > 1.5f) Land(homeX + Range(-roam, roam) * 0.5f, homeZ);
                    return;
            }
            Apply();
        }

        void OnGround(float dt)
        {
            // Startled: the kid running close (or standing right by it), or a ball flying in.
            float reach = AmbientView.KidSpeed > 0.6f ? startle : startle * 0.55f;
            if (AmbientView.ThreatDistance(x, z) < reach)
            {
                TakeOff();
                return;
            }

            if (state == State.Walk)
            {
                float dx = tx - x, dz = tz - z, dist = Mathf.Sqrt(dx * dx + dz * dz);
                // Ease into the stop over the last few centimetres (never quite to a standstill short of it).
                float want = walkSpeed * Mathf.Clamp01(dist / 0.12f + 0.15f);
                speed = Mathf.MoveTowards(speed, want, (want > speed ? 2.5f : 4f) * dt);
                if (dist > 1e-3f)
                {
                    float step = Mathf.Min(dist, speed * dt);
                    x += dx / dist * step;
                    z += dz / dist * step;
                    targetYaw = SideYaw(dx, dz, 10f);
                }
                phase += dt * (hopper ? 9f : 15f) * Mathf.Clamp01(speed / Mathf.Max(0.05f, walkSpeed) + 0.2f);
                if (dist <= 0.005f)
                {
                    speed = 0f;
                    state = State.Idle;
                    until = Time.time + Range(1.2f, 4.5f);
                    nextPeck = Time.time + Range(0.1f, 0.8f);
                }
            }
            else
            {
                speed = 0f;
                // Pecks in little runs, now and then.
                if (Time.time >= nextPeck)
                {
                    peckStart = Time.time;
                    nextPeck = Time.time + (Chance(0.6f) ? Range(0.28f, 0.4f) : Range(0.9f, 2.4f));
                }
                if (Time.time >= until) Decide();
            }
            y = GroundY(x, baseY);
        }

        void Decide()
        {
            float r = Rand01();
            if (r < 0.62f)
            {
                // A few steps somewhere near, staying round home.
                float ang = Range(0f, Mathf.PI * 2f), len = Range(0.2f, 0.7f);
                float nx = Mathf.Clamp(x + Mathf.Cos(ang) * len, homeX - roam, homeX + roam);
                float nz = Mathf.Clamp(z + Mathf.Sin(ang) * len * 0.5f, zMin, zMax);
                float lo = homeX - roam, hi = homeX + roam;
                GroundRange(ref lo, ref hi);
                tx = Mathf.Clamp(nx, lo, hi);
                tz = nz;
                state = State.Walk;
            }
            else
            {
                // Turn to look about, then stay a little longer.
                targetYaw = Chance(0.5f) ? Range(-35f, 35f) : 180f + Range(-35f, 35f);
                until = Time.time + Range(1f, 3f);
            }
        }

        void TakeOff()
        {
            state = State.Fly;
            flownAt = Time.time;
            if (standing != null) standing.gameObject.SetActive(false);
            if (flying != null) flying.gameObject.SetActive(true);
            float away = x - AmbientView.ThreatX;
            float side = Mathf.Abs(away) > 0.3f ? Mathf.Sign(away) : (Chance(0.5f) ? 1f : -1f);
            velocity = new Vector3(side * flightSpeed * Range(0.75f, 1.2f), Range(1.2f, 2f), Range(flightZMin, flightZMax));
            flap = Range(0f, 6f);
            yaw = targetYaw = YawToward(velocity.x, velocity.z);
        }

        void Fly(float dt)
        {
            // Climb away in an arc, wings beating hard at first, then steadier.
            velocity.y = Mathf.MoveTowards(velocity.y, 3.2f, 2.5f * dt);
            velocity.x *= 1f + 0.15f * dt;
            x += velocity.x * dt;
            y += velocity.y * dt;
            z += velocity.z * dt;
            targetYaw = YawToward(velocity.x, velocity.z);
            pitch = Mathf.Lerp(pitch, Mathf.Atan2(velocity.y, Mathf.Abs(velocity.x) + Mathf.Abs(velocity.z)) * Mathf.Rad2Deg * 0.6f, 4f * dt);
            float age = Time.time - flownAt;
            flap += dt * Mathf.Lerp(19f, 12f, Mathf.Clamp01(age / 1.5f));
            float a = Mathf.Sin(flap) * 40f;
            wingA.Set(-a);
            wingB.Set(a);
            if ((age > 0.5f && !AmbientView.InView(x, y, z, 1.5f)) || age > 8f) Hide();
        }

        void Apply()
        {
            yaw = Mathf.SmoothDampAngle(yaw, targetYaw, ref yawVelocity, state == State.Fly ? 0.12f : 0.18f);
            float lift = 0f;
            if (state == State.Walk)
            {
                if (hopper) lift = Mathf.Abs(Mathf.Sin(phase)) * 0.05f * Mathf.Clamp01(speed / Mathf.Max(0.05f, walkSpeed));
                else lift = Mathf.Abs(Mathf.Sin(phase)) * 0.006f;
            }
            transform.SetPositionAndRotation(new Vector3(x, y + lift, z), Quaternion.Euler(0f, yaw, pitch));
            if (state == State.Fly || !head.ready) return;
            // The pigeon's head: nodding back and forth as it walks, quick pecks when it stops.
            if (state == State.Walk)
            {
                head.Set(6f);
                head.Slide(new Vector3(Mathf.Sin(phase) * 0.018f, 0f, 0f));
                return;
            }
            float k = (Time.time - peckStart) / 0.22f;
            float peck = k >= 0f && k <= 1f ? Mathf.Sin(k * Mathf.PI) * 62f : 0f;
            head.Set(8f + peck + Mathf.Sin(Time.time * 1.3f + seed) * 6f);
            head.Slide(Vector3.zero);
        }
    }
}
