using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A playful dog that wanders its patch and chases a low ball, nosing it back
    /// toward the kid. Chip the ball over its head! It never hurts anyone.
    ///
    /// Left to itself it behaves like a dog off its lead: it ambles or trots to somewhere else on
    /// its patch (anywhere, in depth too), stops to sniff the ground or look about with its tail
    /// going, and now and then dashes off in a happy burst. The chase is as it always was: a low
    /// ball near its patch gets chased (along the street, inside the patch) and nosed back.
    /// </summary>
    public class Dog : HazardBase
    {
        public float minX = -3f;
        public float maxX = 3f;
        [Tooltip("Ambling speed; it trots and dashes faster.")]
        public float wanderSpeed = 1f;
        public float trotSpeed = 2f;
        public float chaseSpeed = 4.5f;
        [Tooltip("How far the dog notices the ball.")]
        public float noticeRange = 4f;
        [Tooltip("Only chases a ball lower than this above the dog's feet.")]
        public float maxBallHeight = 1f;
        public float stealDistance = 0.55f;
        public Vector2 stealVelocity = new Vector2(-4.5f, 3.5f);
        public float stealCooldown = 1.2f;
        public Transform visual;
        [Tooltip("Leg pivots (at the hips and shoulders), swung whole while trotting; a model with jointed legs (ShinFR.., FootFR.. under them) walks them with planted feet instead (World/LegGait).")]
        public Transform[] legs;
        [Tooltip("The axis, in each leg's own space, the legs swing about (the kit's dog: up).")]
        public Vector3 legAxis = Vector3.forward;
        [Tooltip("Optional tail pivot, wagged (faster when chasing) about tailAxis in its own space.")]
        public Transform tail;
        public Vector3 tailAxis = Vector3.forward;
        [Tooltip("Optional head (at the neck): nods about headNodAxis (sniffing), turns about headTurnAxis (looking about).")]
        public Transform head;
        public Vector3 headNodAxis = Vector3.up;
        public Vector3 headTurnAxis = Vector3.forward;
        [Tooltip("Depths (the visual's z) it roams between, beside the kid's line and behind it.")]
        public float nearZ = 0.45f, farZ = 0.9f;

        public bool IsChasing { get; private set; }
        public event System.Action<Dog> StoleBall;

        enum Mode { Sniff, Look, Walk, Trot, Dash }

        Vector3 startPosition;
        Vector3 visualBase;
        int direction = 1;
        float nextStealTime;
        Vector3 visualBaseScale = Vector3.one;
        Quaternion[] legRest;
        Quaternion tailRest, headRest;
        float stride, wagPhase;
        World.LegGait.Rig rig;      // jointed legs (LegFR.. with ShinFR.. and FootFR..): walked with planted feet
        World.PartChain tailChain;  // a tail in links (Tail, Tail2, Tail3): wagged link by link
        float legPhase, gaitWeight;

        Mode mode;
        float modeUntil, targetX, targetZ, depth;
        Vector2 velocity;   // along the street (x) and in depth (z)
        float yaw, yawVelocity;
        float nod, turn;
        uint rng = 2463534242u;

        void Awake()
        {
            startPosition = transform.position;
            if (visual != null)
            {
                visualBaseScale = visual.localScale;
                visualBase = visual.localPosition;
            }
            // Swing each part from its rest pose (model parts may come in rotated).
            legRest = new Quaternion[legs != null ? legs.Length : 0];
            for (int i = 0; i < legRest.Length; i++) legRest[i] = legs[i] != null ? legs[i].localRotation : Quaternion.identity;
            if (tail != null)
            {
                tailRest = tail.localRotation;
                tailChain = World.PartChain.Find(tail, tailAxis);
                if (tailChain.Links < 2) tailChain = null;
            }
            if (head != null) headRest = head.localRotation;
            // A model with jointed legs (the Kamakura kit's) walks them with its feet planted (World/LegGait); the
            // original kit's dog, legs in one piece, swings them whole as before.
            if (visual != null)
            {
                rig = World.LegGait.Rig.Find(visual, visual);
                if (rig.Count == 0) rig = null;
            }
            rng ^= (uint)Mathf.Abs(Mathf.RoundToInt(minX * 131f + maxX * 17f)) + 1u;
            Pedestrian.ClaimLane(this, minX, maxX);
            ResetState();
        }

        void OnDestroy()
        {
            Pedestrian.ReleaseLane(this);
        }

        public override void ResetState()
        {
            transform.position = startPosition;
            direction = 1;
            IsChasing = false;
            nextStealTime = 0f;
            depth = visualBase.z != 0f ? visualBase.z : 0.55f;
            velocity = Vector2.zero;
            yaw = Presentation.CharacterRig.FacingYaw(1f);
            yawVelocity = 0f;
            Begin(Mode.Sniff, Range(0.5f, 2f));
        }

        float Rand01()
        {
            rng ^= rng << 13;
            rng ^= rng >> 17;
            rng ^= rng << 5;
            return (rng & 0xFFFFFF) / 16777216f;
        }

        float Range(float a, float b) { return a + (b - a) * Rand01(); }

        void Begin(Mode m, float time)
        {
            mode = m;
            modeUntil = Time.time + time;
        }

        void Update()
        {
            if (Level == null || Level.State == Core.LevelState.Paused) return;
            float dt = Time.deltaTime;
            var ball = Ball;
            Vector3 p = transform.position;
            float prevX = p.x;

            IsChasing = false;
            if (ball != null && Time.time >= nextStealTime)
            {
                Vector2 b = ball.transform.position;
                bool low = b.y - p.y <= maxBallHeight;
                bool inPatch = b.x >= minX - 1f && b.x <= maxX + 1f;
                if (low && inPatch && Mathf.Abs(b.x - p.x) <= noticeRange)
                {
                    IsChasing = true;
                    direction = b.x > p.x ? 1 : -1;
                    p.x = Mathf.MoveTowards(p.x, Mathf.Clamp(b.x, minX, maxX), chaseSpeed * Time.deltaTime);
                    if (Mathf.Abs(b.x - p.x) <= stealDistance && IsLive) Steal(ball);
                }
            }

            if (IsChasing)
            {
                // Straight at the ball along the street, coming in beside the kid's line.
                depth = Mathf.MoveTowards(depth, visualBase.z != 0f ? visualBase.z : 0.55f, 2.5f * dt);
                velocity = new Vector2(dt > 0f ? (p.x - prevX) / dt : 0f, 0f);
                targetX = p.x;
                Begin(Mode.Look, Range(0.6f, 1.5f));   // a moment's pause when the chase is over
            }
            else Wander(ref p, dt);

            transform.position = p;
            Animate(dt);
        }

        void Wander(ref Vector3 p, float dt)
        {
            bool moving = mode == Mode.Walk || mode == Mode.Trot || mode == Mode.Dash;
            if (!moving && Time.time >= modeUntil) PickDestination(p.x);
            moving = mode == Mode.Walk || mode == Mode.Trot || mode == Mode.Dash;

            Vector2 want = Vector2.zero;
            if (moving)
            {
                float top = mode == Mode.Walk ? wanderSpeed : mode == Mode.Trot ? trotSpeed : trotSpeed * 1.7f;
                Vector2 to = new Vector2(targetX - p.x, targetZ - depth);
                float dist = to.magnitude;
                // Slowing into its stop over the last stretch.
                if (dist > 0.03f) want = to / dist * top * Mathf.Clamp01(dist / (0.25f + top * 0.35f));
                if (dist < 0.06f && velocity.sqrMagnitude < 0.04f)
                {
                    float r = Rand01();
                    if (r < 0.6f) Begin(Mode.Sniff, Range(1.5f, 4f));
                    else Begin(Mode.Look, Range(1f, 3f));
                }
            }
            float accel = mode == Mode.Walk ? 2.5f : 5f;
            velocity = Vector2.MoveTowards(velocity, want, accel * dt);
            p.x = Mathf.Clamp(p.x + velocity.x * dt, minX, maxX);
            depth = Mathf.Clamp(depth + velocity.y * dt, nearZ, farZ);
            if (Mathf.Abs(velocity.x) > 0.05f) direction = velocity.x > 0f ? 1 : -1;
        }

        void PickDestination(float x)
        {
            // Somewhere else on its patch, at least a couple of steps away, often carrying on the
            // way it faces; now and then a dash right across.
            float lo = minX + 0.2f, hi = maxX - 0.2f;
            if (hi < lo) { lo = hi = (minX + maxX) * 0.5f; }
            float r = Rand01();
            Mode m = r < 0.55f ? Mode.Walk : r < 0.88f ? Mode.Trot : Mode.Dash;
            float tx;
            if (m == Mode.Dash) tx = x - lo > hi - x ? lo + Range(0f, 0.8f) : hi - Range(0f, 0.8f);
            else
            {
                tx = Range(lo, hi);
                if (Mathf.Abs(tx - x) < 1.2f) tx = Mathf.Clamp(x + (Rand01() < 0.7f ? direction : -direction) * Range(1.2f, 2.5f), lo, hi);
            }
            targetX = Mathf.Clamp(tx, lo, hi);
            targetZ = Range(nearZ, farZ);
            mode = m;
            modeUntil = Time.time + 20f;
        }

        void Animate(float dt)
        {
            if (visual == null) return;
            float speed = velocity.magnitude;
            // Turn to face the way it goes (a little toward the camera), through facing the camera
            // when it turns round; while chasing, toward the ball.
            float want;
            if (IsChasing) want = Presentation.CharacterRig.FacingYaw(direction);
            else if (speed > 0.08f) want = World.AmbientAgent.SideYaw(velocity.x, velocity.y, 22f);
            else want = yaw;
            yaw = Mathf.SmoothDampAngle(yaw, want, ref yawVelocity, IsChasing ? 0.08f : 0.2f);
            visual.localRotation = Quaternion.Euler(0f, yaw, 0f);
            visual.localPosition = new Vector3(visualBase.x, visualBase.y, depth);

            float run = IsChasing ? chaseSpeed : speed;
            float gait = Mathf.Clamp01(run / 0.6f);
            stride += dt * run * 9f;
            if (rig != null)
            {
                // A walk, turning into a trot from 1 to 1.8 m/s. The cycle runs as fast as the feet must step for the
                // planted ones not to skate: the body covers stride / duty of a leg's length each cycle.
                float trot = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(1f, 1.8f, run));
                float duty = Mathf.Lerp(World.LegGait.Duty(World.LegGait.Kind.Walk), World.LegGait.Duty(World.LegGait.Kind.Trot), trot);
                float reach = Mathf.Lerp(World.LegGait.Stride(World.LegGait.Kind.Walk), World.LegGait.Stride(World.LegGait.Kind.Trot), trot) * rig.Length;
                legPhase += dt * run * duty / Mathf.Max(0.01f, reach);
                legPhase -= Mathf.Floor(legPhase);
                gaitWeight = Mathf.MoveTowards(gaitWeight, gait, 4f * dt);
                float lift = gaitWeight * Mathf.Lerp(rig.BodyLift(legPhase, World.LegGait.Kind.Walk), rig.BodyLift(legPhase, World.LegGait.Kind.Trot), trot);
                lift = rig.Pose(legPhase, trot, gaitWeight, lift);       // lowered where a foot must reach the ground
                visual.localPosition = new Vector3(visualBase.x, visualBase.y + lift * visualBaseScale.y, depth);
                visual.localScale = visualBaseScale;
            }
            else
            {
                Vector3 s = visualBaseScale;
                s.y = visualBaseScale.y * (1f + Mathf.Sin(stride * 2f) * 0.04f * gait);
                visual.localScale = s;
            }
            if (rig == null && legs != null)
                for (int i = 0; i < legs.Length && i < legRest.Length; i++)
                    if (legs[i] != null)
                        legs[i].localRotation = legRest[i] * Quaternion.AngleAxis(Mathf.Sin(stride + (i == 0 || i == 3 ? 0f : Mathf.PI)) * 28f * gait, legAxis);

            // The tail: always going, faster when it plays.
            wagPhase += dt * (IsChasing ? 16f : mode == Mode.Dash ? 13f : mode == Mode.Sniff ? 5f : 8f);
            float wag = Mathf.Sin(wagPhase) * (mode == Mode.Sniff && !IsChasing ? 14f : 25f);
            if (tailChain != null) tailChain.Set(wag, dt);
            else if (tail != null) tail.localRotation = tailRest * Quaternion.AngleAxis(wag, tailAxis);

            if (head == null) return;
            // Nose down to sniff, glancing about when it stops to look, up when chasing.
            float wantNod = IsChasing ? -6f : mode == Mode.Sniff ? 26f + Mathf.Sin(Time.time * 13f) * 3f : 4f * gait;
            float wantTurn = !IsChasing && mode == Mode.Look ? Mathf.Sin(Time.time * 0.9f + minX) * 32f : 0f;
            nod = Mathf.MoveTowards(nod, wantNod, 90f * dt);
            turn = Mathf.MoveTowards(turn, wantTurn, 70f * dt);
            head.localRotation = headRest * Quaternion.AngleAxis(nod, headNodAxis) * Quaternion.AngleAxis(turn, headTurnAxis);
        }

        void Steal(Ball.BallController ball)
        {
            nextStealTime = Time.time + stealCooldown;
            Vector2 v = stealVelocity;
            // Always nose it back toward the kid.
            var kid = Kid;
            if (kid != null && kid.transform.position.x > transform.position.x) v.x = Mathf.Abs(v.x);
            else v.x = -Mathf.Abs(v.x);
            ball.Kick(v);
            Core.GameEvents.Raise(Core.GameEventType.DogSteal, transform.position);
            if (StoleBall != null) StoleBall(this);
        }
    }
}
