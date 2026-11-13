using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A cat on a garden wall (the Animals kit's sitting cat): it sits looking about with its tail
    /// swishing, washes now and then, pads a few bounds along the wall top, and sometimes jumps
    /// down into the garden behind, out of sight. Some time later it is sitting on a wall again
    /// (any wall top along the street that is out of view at the time).
    /// </summary>
    public class WallCat : AmbientAgent
    {
        [Tooltip("The cat model, hidden while the cat is away.")]
        public Transform model;
        [Tooltip("The tail, swished about its axis.")]
        public Part tail;
        LegGait.Rig rig;        // a walking model's jointed legs (the Kamakura kit's), tucked through a bound
        [Tooltip("Wall tops it may sit on: (from x, to x, top height, depth z).")]
        public Vector4[] walls = new Vector4[0];
        [Tooltip("The wall top it starts on.")]
        public int wall;
        [Tooltip("How far behind the wall the garden it jumps into is.")]
        public float gardenDrop = 1.6f;

        enum State { Sit, Groom, Bound, Leave, Gone }

        State state;
        float until, started;
        float x, side = 1f;
        float yaw, yawVelocity, targetYaw;
        int bounds;
        float boundFrom, boundTo;
        Vector3 leaveFrom, leaveTo;
        float swishPhase;

        Vector4 Wall { get { return walls.Length > 0 ? walls[Mathf.Clamp(wall, 0, walls.Length - 1)] : new Vector4(transform.position.x, transform.position.x, transform.position.y, transform.position.z); } }

        protected override float Reach { get { return 2f; } }

        protected override void Awake()
        {
            base.Awake();
            tail.Capture();
            rig = LegGait.Rig.Find(transform, transform);
            if (rig.Count == 0) rig = null;
            x = transform.position.x;
            yaw = targetYaw = transform.eulerAngles.y;
            side = Mathf.Cos(yaw * Mathf.Deg2Rad) >= 0f ? 1f : -1f;
            swishPhase = Range(0f, 10f);
            Sit(Range(2f, 6f));
        }

        void Sit(float time)
        {
            state = State.Sit;
            until = Time.time + time;
        }

        protected override void Sleep()
        {
            if (state == State.Leave) Away();
            if (state == State.Gone && Time.time >= until) TryReturn();
        }

        protected override void Tick(float dt)
        {
            var w = Wall;
            float y = w.z, depth = w.w;
            Vector3 pos = new Vector3(x, y, depth);
            float pitchRock = 0f, roll = 0f;
            switch (state)
            {
                case State.Sit:
                    if (Time.time >= until) Decide(w);
                    break;
                case State.Groom:
                {
                    // Washing: little dips of the head and shoulders.
                    float t = Time.time - started;
                    pitchRock = -Mathf.Abs(Mathf.Sin(t * 7f)) * 7f;
                    roll = Mathf.Sin(t * 2.3f) * 3f;
                    if (Time.time >= until) Sit(Range(2f, 5f));
                    break;
                }
                case State.Bound:
                {
                    // Padding along the wall top in soft bounds.
                    float k = (Time.time - started) / 0.34f;
                    if (k >= 1f)
                    {
                        x = boundTo;
                        if (--bounds > 0 && StartBound(w)) break;
                        targetYaw = side > 0f ? Range(-15f, 25f) : 180f + Range(-25f, 15f);
                        Sit(Range(2f, 5f));
                        break;
                    }
                    x = Mathf.Lerp(boundFrom, boundTo, Ease(k));
                    pos.x = x;
                    pos.y += Mathf.Sin(k * Mathf.PI) * 0.09f;
                    pitchRock = Mathf.Sin(k * Mathf.PI * 2f) * 8f;
                    // a model with jointed legs tucks them through the bound and lands on them (LegGait.Rig.Hop)
                    if (rig != null) rig.Hop(Mathf.Sin(k * Mathf.PI), 0f);
                    break;
                }
                case State.Leave:
                {
                    // Up a little, then down into the garden behind the wall.
                    float k = Mathf.Clamp01((Time.time - started) / 0.6f);
                    pos = Vector3.Lerp(leaveFrom, leaveTo, k);
                    pos.y += Mathf.Sin(k * Mathf.PI) * 0.35f - (1f - Mathf.Cos(k * Mathf.PI * 0.5f)) * 0.1f;
                    pitchRock = Mathf.Lerp(10f, -35f, k);
                    if (k >= 1f) Away();
                    break;
                }
                case State.Gone:
                    if (Time.time >= until) TryReturn();
                    return;
            }

            yaw = Mathf.SmoothDampAngle(yaw, targetYaw, ref yawVelocity, 0.35f);
            transform.SetPositionAndRotation(pos, Quaternion.Euler(roll, yaw, pitchRock));
            // The tail: a lazy swish, quicker while it is on the move.
            swishPhase += dt * (state == State.Sit ? 1.6f : 3.2f);
            tail.Set(3f + 17f * (Mathf.Sin(swishPhase) + 0.25f * Mathf.Sin(2.1f * swishPhase)));
        }

        void Decide(Vector4 w)
        {
            float r = Rand01();
            if (r < 0.22f)
            {
                state = State.Groom;
                started = Time.time;
                until = Time.time + Range(2f, 4.5f);
            }
            else if (r < 0.42f)
            {
                // A few bounds along the wall, toward the side with more room.
                side = (w.y - x) > (x - w.x) ? 1f : -1f;
                bounds = 1 + (int)Range(1f, 4f);
                if (!StartBound(w)) Sit(Range(1f, 3f));
            }
            else if (r < 0.52f && AmbientView.InViewX(x, w.w, 0f))
            {
                // Off into the garden.
                state = State.Leave;
                started = Time.time;
                float dir = Chance(0.5f) ? 1f : -1f;
                leaveFrom = new Vector3(x, w.z, w.w);
                leaveTo = new Vector3(x + dir * 0.45f, w.z - gardenDrop, w.w + 0.85f);
                targetYaw = YawToward(dir * 0.4f, 1f);
            }
            else
            {
                // Look about a little.
                targetYaw = side > 0f ? Range(-30f, 35f) : 180f + Range(-35f, 30f);
                Sit(Range(2.5f, 6f));
            }
        }

        bool StartBound(Vector4 w)
        {
            float step = Range(0.28f, 0.4f) * side;
            float to = x + step;
            if (to < w.x || to > w.y) return false;
            state = State.Bound;
            started = Time.time;
            boundFrom = x;
            boundTo = to;
            targetYaw = side > 0f ? 12f : 168f;
            return true;
        }

        void Away()
        {
            state = State.Gone;
            until = Time.time + Range(12f, 30f);
            if (model != null) model.gameObject.SetActive(false);
        }

        /// <summary>Back on a wall top that is out of view (it jumped up while nobody looked).</summary>
        void TryReturn()
        {
            if (walls.Length == 0) return;
            int pick = (int)(Rand01() * walls.Length) % walls.Length;
            var w = walls[pick];
            float at = Range(w.x, w.y);
            if (AmbientView.OutsideBy(at, w.w) < 1.5f)
            {
                until = Time.time + 2f;   // try again shortly
                return;
            }
            wall = pick;
            x = at;
            side = Chance(0.5f) ? 1f : -1f;
            yaw = targetYaw = side > 0f ? Range(-20f, 20f) : 180f + Range(-20f, 20f);
            if (model != null) model.gameObject.SetActive(true);
            transform.SetPositionAndRotation(new Vector3(x, w.z, w.w), Quaternion.Euler(0f, yaw, 0f));
            Sit(Range(3f, 8f));
        }
    }
}
