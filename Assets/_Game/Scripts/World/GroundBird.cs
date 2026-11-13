using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A bird on the ground (Animals kit): a pigeon pecking about the pavement with its friends, or
    /// a gull standing on the sand. It potters a few steps at a time (the pigeon nodding, the gull
    /// hopping), turns, pecks, and when the kid runs close it takes off: the standing model gives
    /// way to the flying one, which flaps up and away from the kid in an arc until it is out of
    /// sight. A while later, once its spot is out of sight too, it is back there on the ground.
    ///
    /// A model with jointed legs (LegR, LegL, each with a Shin and a Foot: the Kamakura kit's) steps them as it walks,
    /// crouches, springs and lands on them as it hops, and keeps its feet planted while a peck tips its body forward
    /// (World/LegGait; the asset review renders the same).
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
        [Tooltip("How far the head thrusts forward and holds with each step (metres; the original kit's pigeon: 0.018): it " +
                 "holds still in the air while the body walks under it, then thrusts forward (HeadBob).")]
        public float headSlide = 0.018f;
        [Tooltip("How far the head nods forward and back with each step (degrees): a photo cut-out's head nods, as one that slides shows its cut edge.")]
        public float headNod;
        [Tooltip("A peck: the head's turn beak-down (degrees) and the body's tip forward on its feet (degrees). The original kit's: 62 and 0; a photo cut-out's: 25 and 30, so the neck never folds.")]
        public float peckTurn = 62f, peckTip;
        [Tooltip("Optional: a tail that pumps up and down all the while it is on the ground (a wagtail's; in links, so the pump runs down it).")]
        public Part tail;
        [Tooltip("Optional: a crest's long plumes (an egret's), hanging from the head: turned back by most of the head's and the body's turn, as plumes hang.")]
        public Part plume;
        [Tooltip("The tail's pump either side (degrees) and pumps per second.")]
        public float tailPump = 14f, tailPumpRate = 3f;
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
        LegGait.Rig rig;        // jointed legs (LegR, LegL with ShinR.. and FootR..): stepped, hopped and planted

        protected override float Reach { get { return roam + 1f; } }

        protected override void Awake()
        {
            base.Awake();
            head.Capture();
            wingA.Capture();
            wingB.Capture();
            tail.Capture();
            plume.Capture();
            if (standing != null)
            {
                rig = LegGait.Rig.Find(standing, transform);
                if (rig.Count == 0) rig = null;
            }
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
                // a hopper's lift is |sin| (two hops a turn); with jointed legs, one crouch-spring-land a turn, so twice as fast
                phase += dt * (hopper ? (rig != null ? 18f : 9f) : 15f) * Mathf.Clamp01(speed / Mathf.Max(0.05f, walkSpeed) + 0.2f);
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

        /// <summary>A walking bird's head against its body at walk phase phase (radians; a step every 2 pi), -1 back to
        /// +1 forward (D21): for most of the step it holds still in the air, so it slides back as the body walks under
        /// it, then thrusts forward in a quick eased move early in the next foot's swing. The asset review moves the same
        /// (tools/blender/asset_review.py: head_bob).</summary>
        public static float HeadBob(float phase)
        {
            float u = phase / (2f * Mathf.PI);
            u -= Mathf.Floor(u);
            float v = u - 0.45f;
            v -= Mathf.Floor(v);
            return v < 0.7f ? 1f - 2f * v / 0.7f : -1f + 2f * Ease((v - 0.7f) / 0.3f);
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
            float lift = 0f, tip = 0f;
            float pace = Mathf.Clamp01(speed / Mathf.Max(0.05f, walkSpeed));
            float k = (Time.time - peckStart) / 0.22f;
            float peck = state == State.Idle && k >= 0f && k <= 1f ? Mathf.Sin(k * Mathf.PI) : 0f;
            if (state == State.Walk)
            {
                if (hopper && rig != null)
                {
                    // crouch, spring, tuck the feet, land (the review's hop): up 5 cm, down into the knees between
                    float sh = Mathf.Sin(phase);
                    lift = (sh > 0f ? 0.05f * sh : 0.12f * rig.Length * sh) * pace;
                }
                else if (hopper) lift = Mathf.Abs(Mathf.Sin(phase)) * 0.05f * pace;
                else if (rig != null)       // two nods a stride; the body as low as a foot needs to reach the ground
                    lift = rig.Pose(phase / (4f * Mathf.PI), 0f, pace, rig.BodyLift(phase / (4f * Mathf.PI), LegGait.Kind.Step) * pace);
                else lift = Mathf.Abs(Mathf.Sin(phase)) * 0.006f;
            }
            else if (state == State.Idle)
            {
                tip = peckTip * peck;
                // no further than the legs can keep both feet planted
                if (rig != null) tip = -rig.Reach(-tip * Mathf.Deg2Rad) * Mathf.Rad2Deg;
            }
            // A peck tips the body forward on its feet (nose down: a negative turn about the model's side axis).
            transform.SetPositionAndRotation(new Vector3(x, y + lift, z), Quaternion.Euler(0f, yaw, pitch - tip));
            if (rig != null && state != State.Fly && state != State.Gone)
            {
                if (state == State.Walk && hopper) rig.Hop(Mathf.Sin(phase) * pace, lift);
                else if (state != State.Walk) rig.Plant(-tip * Mathf.Deg2Rad);
            }
            if (state != State.Fly && state != State.Gone) tail.Set(Mathf.Sin((Time.time + seed) * tailPumpRate * Mathf.PI * 2f) * tailPump);
            if (state == State.Fly || !head.ready) return;
            // The head: nodding back and forth as it walks, quick pecks when it stops.
            if (state == State.Walk)
            {
                head.Set(6f + headNod * Mathf.Sin(phase));
                head.Slide(new Vector3(HeadBob(phase) * headSlide, 0f, 0f));
                plume.Set(-0.8f * headNod * Mathf.Sin(phase));
                return;
            }
            float look = Mathf.Sin(Time.time * 1.3f + seed) * 6f;
            head.Set(8f + peckTurn * peck + look);
            head.Slide(Vector3.zero);
            plume.Set(-0.8f * (peckTurn * peck + look + tip));
        }
    }
}
