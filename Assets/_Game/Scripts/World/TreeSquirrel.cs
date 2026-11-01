using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A squirrel on the park lawn (Animals kit): it forages in little hops, sits up with its tail
    /// flicking, and every so often (or when the kid comes close) it dashes off in long bounds to
    /// a tree, scampers up the trunk and is gone into the crown. A while later, out of sight, it is
    /// back on the lawn.
    /// </summary>
    public class TreeSquirrel : AmbientAgent
    {
        public Transform model;
        [Tooltip("The bushy tail, flicked about its axis.")]
        public Part tail;
        [Tooltip("Ground height where there is no baked ground strip.")]
        public float baseY;
        public float homeX, homeZ;
        public float roam = 2.5f;
        public float zMin = 3f, zMax = 7.5f;
        [Tooltip("Trees it may run up: (x, ground height, z, trunk radius).")]
        public Vector4[] trees = new Vector4[0];
        public float startle = 3f;

        enum State { Forage, Hop, Dash, Climb, Gone }

        State state;
        float until, started;
        float x, y, z;
        Vector3 hopFrom, hopTo;
        float hopTime, hopHeight;
        int tree = -1;
        float treeSide = 1f, climbTop;
        float yaw, yawVelocity, targetYaw, pitch, pitchVelocity, targetPitch;
        float flickStart = -10f, nextFlick;

        protected override float Reach { get { return roam + 10f; } }

        protected override void Awake()
        {
            base.Awake();
            tail.Capture();
            yaw = targetYaw = transform.eulerAngles.y;
            Home();
        }

        void Home()
        {
            x = homeX + Range(-roam, roam) * 0.5f;
            z = Mathf.Clamp(homeZ + Range(-0.6f, 0.6f), zMin, zMax);
            y = GroundY(x, baseY);
            pitch = targetPitch = 0f;
            state = State.Forage;
            until = Time.time + Range(1f, 3f);
            if (model != null) model.gameObject.SetActive(true);
            Apply();
        }

        protected override void Sleep()
        {
            if (state == State.Dash || state == State.Climb) Away();
            else if (state == State.Gone && Time.time >= until && AmbientView.OutsideBy(homeX, homeZ) > 2f) Home();
        }

        protected override void Tick(float dt)
        {
            if (state == State.Gone)
            {
                if (Time.time >= until && AmbientView.OutsideBy(homeX, homeZ) > 2f) Home();
                return;
            }
            bool scared = AmbientView.ThreatDistance(x, z) < startle;
            switch (state)
            {
                case State.Forage:
                    targetPitch = Mathf.Sin(Time.time * 0.9f + seed) > 0.6f ? -12f : 0f;   // sits up now and then
                    if (scared || (Time.time >= until && Chance(0.18f) && trees.Length > 0)) { if (!StartDash()) until = Time.time + 1f; }
                    else if (Time.time >= until) StartHop();
                    if (Time.time >= nextFlick)
                    {
                        flickStart = Time.time;
                        nextFlick = Time.time + Range(1.2f, 4f);
                    }
                    break;
                case State.Hop:
                case State.Dash:
                {
                    float k = (Time.time - started) / hopTime;
                    Vector3 p = Vector3.Lerp(hopFrom, hopTo, Mathf.Clamp01(k));
                    x = p.x;
                    z = p.z;
                    float ground = GroundY(x, baseY);
                    y = ground + Mathf.Sin(Mathf.Clamp01(k) * Mathf.PI) * hopHeight;
                    targetPitch = Mathf.Lerp(12f, -12f, Mathf.Clamp01(k));
                    if (k < 1f) break;
                    y = ground;
                    if (state == State.Hop)
                    {
                        state = State.Forage;
                        until = Time.time + Range(0.4f, 2.2f);
                        flickStart = Time.time;
                    }
                    else NextBound();
                    break;
                }
                case State.Climb:
                {
                    // Up the trunk in quick scampers.
                    float t = Time.time - started;
                    y += dt * (1.3f + Mathf.Abs(Mathf.Sin(t * 11f)) * 1.2f);
                    if (y >= climbTop) Away();
                    break;
                }
            }
            Apply();
        }

        void StartHop()
        {
            float dx = Range(-0.55f, 0.55f), dz = Range(-0.3f, 0.3f);
            float nx = Mathf.Clamp(x + dx, homeX - roam, homeX + roam);
            float lo = homeX - roam, hi = homeX + roam;
            GroundRange(ref lo, ref hi);
            nx = Mathf.Clamp(nx, lo, hi);
            float nz = Mathf.Clamp(z + dz, zMin, zMax);
            hopFrom = new Vector3(x, y, z);
            hopTo = new Vector3(nx, y, nz);
            hopTime = 0.22f;
            hopHeight = 0.07f;
            started = Time.time;
            state = State.Hop;
            if (Mathf.Abs(nx - x) + Mathf.Abs(nz - z) > 0.05f) targetYaw = SideYaw(nx - x, nz - z, 14f);
        }

        /// <summary>Off to the nearest tree in long bounds; false if there is none near enough.</summary>
        bool StartDash()
        {
            float best = 14f;
            tree = -1;
            for (int i = 0; i < trees.Length; i++)
            {
                float dx = trees[i].x - x, dz = trees[i].z - z;
                float d = Mathf.Sqrt(dx * dx + dz * dz);
                if (d < best) { best = d; tree = i; }
            }
            if (tree < 0) return false;
            treeSide = trees[tree].x >= x ? 1f : -1f;   // it ends up on the near side of the trunk
            state = State.Dash;
            NextBound();
            return true;
        }

        Vector3 TrunkFoot()
        {
            var t = trees[tree];
            return new Vector3(t.x - treeSide * (t.w + 0.03f), t.y, t.z);
        }

        void NextBound()
        {
            Vector3 foot = TrunkFoot();
            Vector3 from = new Vector3(x, y, z);
            Vector3 to = foot - from;
            to.y = 0f;
            float dist = to.magnitude;
            if (dist < 0.05f)
            {
                // At the trunk: turn nose-up and climb.
                state = State.Climb;
                started = Time.time;
                x = foot.x;
                z = foot.z;
                y = trees[tree].y + 0.05f;
                climbTop = trees[tree].y + Range(2.3f, 3.2f);
                targetYaw = treeSide > 0f ? 0f : 180f;
                targetPitch = 90f;
                return;
            }
            float len = Mathf.Min(dist, Range(0.55f, 0.75f));
            hopFrom = from;
            hopTo = from + to / dist * len;
            hopTo.y = from.y;
            hopTime = len / 3.6f;
            hopHeight = 0.12f;
            started = Time.time;
            targetYaw = YawToward(to.x, to.z);
        }

        void Away()
        {
            state = State.Gone;
            until = Time.time + Range(10f, 25f);
            if (model != null) model.gameObject.SetActive(false);
        }

        void Apply()
        {
            float smooth = state == State.Dash ? 0.08f : 0.15f;
            yaw = Mathf.SmoothDampAngle(yaw, targetYaw, ref yawVelocity, smooth);
            pitch = Mathf.SmoothDamp(pitch, targetPitch, ref pitchVelocity, state == State.Climb ? 0.08f : 0.1f);
            transform.position = new Vector3(x, y, z);
            transform.rotation = Quaternion.Euler(0f, yaw, pitch);
            // Flicks of the tail: up and back, then settling.
            float k = (Time.time - flickStart) / 0.35f;
            float flick = k >= 0f && k <= 1f ? Mathf.Sin(k * Mathf.PI) * 24f : 0f;
            tail.Set(state == State.Dash ? -8f : 4f + flick);
        }
    }
}
