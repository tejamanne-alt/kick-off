using System.Collections.Generic;
using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Someone out on the footpath, in the ball's way: the ball bounces off them (the kid slips
    /// past). Hit by the ball, they hop in surprise.
    ///
    /// They are passers-by, not sentries. Each walks one way along the footpath at their own pace,
    /// through their stretch of street (the beat the level gives them) and on, as far as the
    /// footpath is clear, and out of sight; then (out of sight) the next passer-by comes along,
    /// from beyond one side of the view or the other, in other clothes and at another pace: an
    /// older person a little stooped and slower, someone with a friend, a parent with a child, a
    /// dog walker. Some stop a moment on the way (a look at the shops, a glance at a phone, a chat
    /// with their friend), they wait at the kerb for the green man at a crossing, and where the
    /// footpath ahead is blocked in view (a crate stack, the steps, a puddle) they step aside off
    /// the ball's line to look in a shop window rather than turn back. They never turn round in
    /// view.
    ///
    /// Gameplay contract: only the walker on the ball's line (collider at z = 0) blocks the ball,
    /// as before; the company walks a step behind and never touches anything, and a walker who
    /// has stepped aside or gone is out of the ball's way.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class Pedestrian : HazardBase
    {
        public enum Company { None, Friend, Child, Dog }
        public enum Gesture { None, Phone, Look, Chat, Wait }

        public float minX = -2f;
        public float maxX = 2f;
        [Tooltip("Their usual walking pace; each passer-by walks a little faster or slower.")]
        public float walkSpeed = 1.1f;
        [Tooltip("How long they stand startled when the ball hits them.")]
        public float pauseTime = 0.8f;
        [Tooltip("Optional visual root that hops and turns around.")]
        public Transform visual;

        [Header("Coming and going")]
        [Tooltip("How far past their beat they may walk, where the footpath is clear.")]
        public float reach = 9f;
        [Tooltip("The visual's depth when stepped aside, behind the ball's line.")]
        public float asideZ = 1.1f;
        [Tooltip("Seed for this walker's choices (set by the level builder).")]
        public int seed = 1;
        [Tooltip("Coats the next passers-by wear.")]
        public Color[] coats = new Color[0];
        [Tooltip("Their trousers, skirts or shorts (empty: each coat's own colour, darker).")]
        public Color[] legwears = new Color[0];
        [Tooltip("What recolours their clothes (IOutfit).")]
        public MonoBehaviour outfit;

        [Header("Company")]
        public Company company;
        [Tooltip("The friend's, child's or dog's visual root, a child of this object.")]
        public Transform companion;
        public MonoBehaviour companionOutfit;
        [Tooltip("The companion's own tops and legwear to change into (empty: the walker's coats, the legwear darker).")]
        public Color[] companionCoats = new Color[0];
        public Color[] companionLegwears = new Color[0];
        [Tooltip("The dog's leg pivots (diagonal pairs swing together) and its tail.")]
        public Transform[] companionLegs = new Transform[0];
        public Vector3 companionLegAxis = Vector3.up;
        public Transform companionTail;
        public Vector3 companionTailAxis = Vector3.forward;
        [Tooltip("The dog's lead: a thin box one unit long along its own z, laid from hand to collar.")]
        public Transform lead;
        [Tooltip("The walker's rig (for the hand holding the lead).")]
        public Presentation.CharacterRig rig;

        /// <summary>Raised when the ball bumps into this pedestrian.</summary>
        public event System.Action<Pedestrian> Bumped;

        enum State { Hidden, Walking, Stopped, Waiting, Aside }

        const float Accel = 1.2f, Decel = 1f;
        /// <summary>How far past the view's edge they must be to come or go unseen.</summary>
        const float Margin = 1.4f;
        /// <summary>How far past the view's edge a walker (and their company) is wholly out of sight.</summary>
        const float HiddenBeyond = 1.1f;

        Rigidbody2D body;
        Collider2D[] own = new Collider2D[0];
        Vector2 startPosition;
        float feetY;
        State state;
        int direction = 1;
        float x, speed, cruise, stoop;
        float stopAt = float.NaN, stopUntil, hiddenUntil, nextGestureChange;
        Gesture gesture, companionGesture;
        Gesture stopGesture;
        float hopTime = -10f;
        Vector3 visualBasePosition;
        float depth, yaw, yawVelocity, companionYaw, companionYawVelocity;
        Vector3 companionOffset, companionVelocity;
        Quaternion[] companionLegRest = new Quaternion[0];
        Quaternion companionTailRest;
        Renderer leadRenderer;
        float dogStride, wagPhase;
        bool firstPass = true, routeReady;
        float routeMin, routeMax;
        // The footpath's height either side of the beat, every ProbeStep out from it (ramps, raised
        // walkways); the beat itself is level.
        float[] groundLeft = new float[0], groundRight = new float[0];
        const float ProbeStep = 0.25f;
        uint rng = 2463534242u;

        // Crossings on the way, where they wait for the green man.
        readonly Crossing[] crossings = new Crossing[4];
        readonly float[] crossFrom = new float[4], crossTo = new float[4];
        int crossingCount;

        static readonly RaycastHit2D[] rayHits = new RaycastHit2D[6];
        static readonly Collider2D[] boxHits = new Collider2D[12];

        public bool IsWalking { get { return state != State.Hidden && speed > 0.05f; } }
        public int Direction { get { return direction; } }
        /// <summary>Walking speed right now (m/s), easing in and out of stops.</summary>
        public float Speed { get { return state == State.Hidden ? 0f : speed; } }
        /// <summary>How fast their company is walking (keeping up, or shuffling round to chat).</summary>
        public float CompanionSpeed { get { return state == State.Hidden ? 0f : Mathf.Max(speed, new Vector2(companionVelocity.x, companionVelocity.z).magnitude); } }
        public Gesture CurrentGesture { get { return gesture; } }
        public Gesture CompanionGesture { get { return companionGesture; } }
        /// <summary>Forward stoop (degrees): the older passers-by.</summary>
        public float Stoop { get { return stoop; } }
        public bool HoldsLead { get { return company == Company.Dog && lead != null; } }
        public bool IsVisible { get { return state != State.Hidden; } }

        // ---------------------------------------------------------------- lane claims

        struct Claim { public Object owner; public float min, max; public bool walks; }
        static readonly List<Claim> claims = new List<Claim>();

        /// <summary>
        /// Marks a stretch of the footpath as someone's (a pedestrian's beat, a dog's patch), so
        /// passers-by share the footpath out between them instead of walking through each other.
        /// </summary>
        public static void ClaimLane(Object owner, float min, float max, bool walks = false)
        {
            ReleaseLane(owner);
            claims.Add(new Claim { owner = owner, min = Mathf.Min(min, max), max = Mathf.Max(min, max), walks = walks });
        }

        public static void ReleaseLane(Object owner)
        {
            for (int i = claims.Count - 1; i >= 0; i--)
                if (claims[i].owner == null || claims[i].owner == owner) claims.RemoveAt(i);
        }

        // ---------------------------------------------------------------- set-up

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            startPosition = body.position;
            own = GetComponentsInChildren<Collider2D>(true);
            var capsule = GetComponent<CapsuleCollider2D>();
            feetY = startPosition.y - (capsule != null ? capsule.size.y * 0.5f - capsule.offset.y : 0.925f);
            if (visual != null) visualBasePosition = visual.localPosition;
            depth = visualBasePosition.z;
            if (companion != null) companionOffset = companion.localPosition;
            companionLegRest = new Quaternion[companionLegs != null ? companionLegs.Length : 0];
            for (int i = 0; i < companionLegRest.Length; i++)
                companionLegRest[i] = companionLegs[i] != null ? companionLegs[i].localRotation : Quaternion.identity;
            if (companionTail != null) companionTailRest = companionTail.localRotation;
            if (lead != null) leadRenderer = lead.GetComponent<Renderer>();
            rng ^= (uint)(seed * 747796405) + 1u;
            if (rng == 0) rng = 1;
            ClaimLane(this, minX, maxX, true);
        }

        Player.KidController ignoredKid;

        void Start()
        {
            // People only get in the ball's way; the kid slips past in front of them (again
            // whenever the kid's collider changes shape for a slide, to be sure it holds).
            ignoredKid = Kid;
            if (ignoredKid != null)
            {
                IgnoreKid();
                ignoredKid.ShapeChanged += IgnoreKid;
            }
            BuildRoute();
            if (state == State.Hidden && firstPass) TrySpawn();
        }

        void OnDestroy()
        {
            if (ignoredKid != null) ignoredKid.ShapeChanged -= IgnoreKid;
            ReleaseLane(this);
        }

        void IgnoreKid()
        {
            if (ignoredKid == null) return;
            foreach (var kc in ignoredKid.GetComponentsInChildren<Collider2D>())
                foreach (var c in own) Physics2D.IgnoreCollision(c, kc, true);
        }

        float Rand01()
        {
            rng ^= rng << 13;
            rng ^= rng >> 17;
            rng ^= rng << 5;
            return (rng & 0xFFFFFF) / 16777216f;
        }

        float Range(float a, float b) { return a + (b - a) * Rand01(); }

        // ---------------------------------------------------------------- the route

        /// <summary>
        /// How far either way from the beat the footpath is clear to walk on at the beat's level:
        /// up to whatever is in the way (crates, a wall, steps, a car, the stall, a hole, a puddle
        /// to cross, the school gate), short of the checkpoints and the start (where the ball is put
        /// down), and sharing the gaps between beats with the other walkers and dogs.
        /// </summary>
        void BuildRoute()
        {
            routeReady = true;
            float lo = Mathf.Min(minX, maxX), hi = Mathf.Max(minX, maxX);
            float leftLimit = lo - reach, rightLimit = hi + reach;
            var level = Level;
            if (level != null)
            {
                if (!float.IsInfinity(level.startBoundaryX)) leftLimit = Mathf.Max(leftLimit, level.startBoundaryX + 4f);
                foreach (var cp in level.checkpoints)
                {
                    if (cp == null) continue;
                    float cx = cp.transform.position.x;
                    // The kid and ball are set down here (the ball a little ahead): keep clear.
                    if (cx <= lo) leftLimit = Mathf.Max(leftLimit, cx + 4f);
                    else if (cx >= hi) rightLimit = Mathf.Min(rightLimit, cx - 2.5f);
                }
            }
            foreach (var c in claims)
            {
                if (c.owner == this || c.owner == null) continue;
                // Another walker's beat: split the footpath between halfway; a dog's patch is its own.
                if (c.max <= lo) leftLimit = Mathf.Max(leftLimit, c.walks ? (c.max + lo) * 0.5f + 0.6f : c.max + 1.5f);
                else if (c.min >= hi) rightLimit = Mathf.Min(rightLimit, c.walks ? (hi + c.min) * 0.5f - 0.6f : c.min - 1.5f);
            }
            crossingCount = 0;
            var heights = new List<float>();
            routeMin = Probe(lo, -1, leftLimit, heights);
            groundLeft = heights.ToArray();
            heights.Clear();
            routeMax = Probe(hi, 1, rightLimit, heights);
            groundRight = heights.ToArray();
            // The beat itself is the level's to say (it is clear and level); check it for crossings too.
            float g;
            for (float px = lo; px <= hi; px += 0.5f) Clear(px, feetY, out g);
        }

        float Probe(float from, int d, float limit, List<float> heights)
        {
            float px = from, ground = feetY;
            while ((limit - px) * d > ProbeStep)
            {
                float next = px + d * ProbeStep, nextGround;
                if (!Clear(next, ground, out nextGround)) break;
                px = next;
                ground = nextGround;
                heights.Add(nextGround);
            }
            // Short of whatever stopped it, by about half a body.
            if ((px - from) * d > 0.4f) px -= d * 0.35f;
            else px = from;
            return px;
        }

        /// <summary>The footpath's height under x along the route.</summary>
        float GroundAt(float px)
        {
            float lo = Mathf.Min(minX, maxX), hi = Mathf.Max(minX, maxX);
            float[] side;
            float f;
            if (px < lo) { side = groundLeft; f = (lo - px) / ProbeStep; }
            else if (px > hi) { side = groundRight; f = (px - hi) / ProbeStep; }
            else return feetY;
            if (side.Length == 0) return feetY;
            // side[k] is the height (k + 1) steps out from the beat; step 0 is the beat's own.
            int k = Mathf.FloorToInt(f);
            float a = k <= 0 ? feetY : side[Mathf.Min(k - 1, side.Length - 1)];
            float b = side[Mathf.Clamp(k, 0, side.Length - 1)];
            return Mathf.Lerp(a, b, f - k);
        }

        /// <summary>Where the walker's body (its capsule's centre) is at x.</summary>
        Vector2 BodyAt(float px)
        {
            return new Vector2(px, GroundAt(px) + (startPosition.y - feetY));
        }

        bool Ignored(Collider2D c)
        {
            if (c == null) return true;
            var rb = c.attachedRigidbody;
            if (rb == null) return false;
            if (rb == body) return true;
            return rb.GetComponent<Ball.BallController>() != null || rb.GetComponent<Player.KidController>() != null || rb.GetComponent<Pedestrian>() != null;
        }

        /// <summary>
        /// Can someone stand at x: ground under foot no more than a gentle slope from the last step's
        /// (a ramp, not a kerb or a step), nothing solid from the ankles to well above the head?
        /// The ground's height there comes out as ground.
        /// </summary>
        bool Clear(float px, float lastGround, out float ground)
        {
            ground = lastGround;
            var solid = new ContactFilter2D { useTriggers = false };
            int n = Physics2D.Raycast(new Vector2(px, lastGround + 0.5f), Vector2.down, solid, rayHits, 1f);
            bool found = false;
            for (int i = 0; i < n; i++)
            {
                if (Ignored(rayHits[i].collider)) continue;
                float y = rayHits[i].point.y;
                if (rayHits[i].distance > 0.001f && Mathf.Abs(y - lastGround) <= 0.12f) { ground = y; found = true; }
                break;
            }
            if (!found) return false;
            // Up to well over the head: awnings, the stall, a platform or the tunnel stop the walk too
            // (their posts and legs have no colliders of their own).
            n = Physics2D.OverlapBox(new Vector2(px, ground + 0.2f + 1.6f), new Vector2(0.6f, 3.2f), 0f, solid, boxHits);
            for (int i = 0; i < n; i++)
                if (!Ignored(boxHits[i])) return false;
            var all = new ContactFilter2D { useTriggers = true };
            n = Physics2D.OverlapBox(new Vector2(px, ground + 1f), new Vector2(0.3f, 1.6f), 0f, all, boxHits);
            for (int i = 0; i < n; i++)
            {
                var c = boxHits[i];
                if (c == null || !c.isTrigger) continue;
                var crossing = c.GetComponent<Crossing>();
                if (crossing != null)
                {
                    AddCrossing(crossing, c.bounds);
                    continue;
                }
                if (c.GetComponent<Core.GoalZone>() != null || c.GetComponent<Core.LoseZone>() != null) return false;
            }
            return true;
        }

        void AddCrossing(Crossing crossing, Bounds b)
        {
            for (int i = 0; i < crossingCount; i++) if (crossings[i] == crossing) return;
            if (crossingCount >= crossings.Length) return;
            crossings[crossingCount] = crossing;
            crossFrom[crossingCount] = b.min.x;
            crossTo[crossingCount] = b.max.x;
            crossingCount++;
        }

        // ---------------------------------------------------------------- coming and going

        public override void ResetState()
        {
            if (body == null) return;
            // A fresh start: whoever is about is placed out of sight again on the way in.
            Hide(0f);
            firstPass = true;
            stopAt = float.NaN;
            if (routeReady) TrySpawn();
        }

        void Hide(float delay)
        {
            state = State.Hidden;
            speed = 0f;
            gesture = companionGesture = Gesture.None;
            hiddenUntil = Time.time + delay;
            SetSolid(false);
            if (visual != null) visual.gameObject.SetActive(false);
            if (companion != null) companion.gameObject.SetActive(false);
            if (leadRenderer != null) leadRenderer.enabled = false;   // (kept active: its mesh is built on enable)
        }

        void SetSolid(bool solid)
        {
            for (int i = 0; i < own.Length; i++) if (own[i] != null) own[i].enabled = solid;
            if (solid) IgnoreKid();
        }

        /// <summary>
        /// The next passer-by comes along: from just beyond whichever side of the view the
        /// footpath allows, walking in, or from the far end of the route while it is out of sight.
        /// </summary>
        void TrySpawn()
        {
            float lo = routeMin, hi = routeMax;
            if (hi - lo < 0.5f) { hiddenUntil = Time.time + 1f; return; }
            float z = visualBasePosition.z;
            float px;
            int d;
            if (!AmbientView.Valid)
            {
                px = Range(lo, hi);
                d = Rand01() < 0.5f ? 1 : -1;
            }
            else
            {
                float left = AmbientView.LeftEdge(z) - Margin, right = AmbientView.RightEdge(z) + Margin;
                if (lo > right)
                {
                    // All of it lies ahead, out of sight: someone already on their way toward the kid.
                    px = firstPass ? Range(lo + (hi - lo) * 0.3f, hi) : hi;
                    d = -1;
                }
                else if (hi < left)
                {
                    // All of it lies behind the kid: no one there would ever come into view (unless
                    // the kid goes back, and then they come in from the side as below). Rest.
                    hiddenUntil = Time.time + 1f;
                    return;
                }
                else
                {
                    // In view: come in from just beyond a side of the view.
                    bool fromRight = right <= hi - 0.5f && right >= lo + 1f;
                    bool fromLeft = left >= lo + 0.5f && left <= hi - 1f;
                    if (fromRight && fromLeft) { if (Rand01() < 0.6f) fromLeft = false; else fromRight = false; }
                    if (fromRight) { px = right; d = -1; }
                    else if (fromLeft) { px = left; d = 1; }
                    else { hiddenUntil = Time.time + 0.5f; return; }   // both ends of the walk are in view: wait
                }
                // Never step out on top of the ball.
                if (AmbientView.HasBall)
                {
                    Vector3 b = AmbientView.BallPosition;
                    if (Mathf.Abs(b.x - px) < 1.2f && b.y - GroundAt(px) < 2.2f) { hiddenUntil = Time.time + 0.5f; return; }
                }
            }
            Spawn(px, d);
        }

        void Spawn(float px, int d)
        {
            x = px;
            direction = d;
            // Who this is: their pace, maybe a little stooped, maybe in other clothes.
            cruise = walkSpeed * Range(0.88f, 1.14f);
            stoop = 0f;
            bool older = company != Company.Child && Rand01() < 0.18f;
            if (older)
            {
                cruise *= 0.78f;
                stoop = Range(5f, 9f);
            }
            if (company == Company.Child) cruise = Mathf.Min(cruise, 1.05f);
            if (company == Company.Dog) cruise *= 0.95f;
            cruise = Mathf.Clamp(cruise, 0.7f, 1.65f);
            if (!firstPass) Redress();
            firstPass = false;

            // Some stop on the way for a moment.
            stopAt = float.NaN;
            if (Rand01() < (company == Company.Friend ? 0.55f : 0.35f))
            {
                float at = px + d * Range(2.5f, 8f);
                if (at > routeMin + 0.5f && at < routeMax - 0.5f) stopAt = at;
            }
            stopGesture = company == Company.Friend ? Gesture.Chat : Rand01() < 0.5f ? Gesture.Phone : Gesture.Look;

            state = State.Walking;
            speed = cruise;
            gesture = companionGesture = Gesture.None;
            depth = visualBasePosition.z;
            yaw = Presentation.CharacterRig.FacingYaw(d);
            yawVelocity = 0f;
            companionYaw = yaw;
            companionYawVelocity = 0f;
            companionVelocity = Vector3.zero;
            if (companion != null)
            {
                Vector3 at = CompanionTarget();
                at.y = companionOffset.y + GroundAt(x + at.x) - GroundAt(x);
                companion.localPosition = at;
            }
            Vector2 p = BodyAt(x);
            body.position = p;
            transform.position = new Vector3(p.x, p.y, transform.position.z);
            if (visual != null) visual.gameObject.SetActive(true);
            if (companion != null) companion.gameObject.SetActive(true);
            if (leadRenderer != null) leadRenderer.enabled = true;
            SetSolid(true);
            ApplyVisual(0f);
        }

        void Redress()
        {
            if (coats == null || coats.Length == 0) return;
            var dress = outfit as Presentation.IOutfit;
            if (dress != null) Dress(dress, coats, legwears, Rand01(), Rand01());
            var other = companionOutfit as Presentation.IOutfit;
            if (other != null)
                Dress(other, companionCoats != null && companionCoats.Length > 0 ? companionCoats : coats, companionLegwears, Rand01(), Rand01());
        }

        /// <summary>
        /// A change of clothes from a wardrobe, by two draws (the same two whatever it holds, so the walk that follows is the
        /// same): a top, and legwear from <paramref name="legwear"/>s, or with none the top's own colour, darker.
        /// </summary>
        static void Dress(Presentation.IOutfit dress, Color[] tops, Color[] legwear, float topPick, float legPick)
        {
            Color top = tops[(int)(topPick * tops.Length) % tops.Length];
            dress.SetOutfit(top, legwear != null && legwear.Length > 0 ? legwear[(int)(legPick * legwear.Length) % legwear.Length]
                : Color.Lerp(top, Color.black, 0.35f + 0.25f * legPick));
        }

        /// <summary>Gone out of sight: hidden until the next passer-by comes along.</summary>
        void Recycle()
        {
            Hide(Range(1.5f, 5f));
        }

        void StepAside()
        {
            state = State.Aside;
            speed = Mathf.Min(speed, 0.35f);
            SetSolid(false);
            gesture = company == Company.Friend ? Gesture.Chat : Rand01() < 0.6f ? Gesture.Look : Gesture.Phone;
            companionGesture = company == Company.Friend ? Gesture.Chat : Gesture.Look;
            nextGestureChange = Time.time + Range(5f, 9f);
        }

        // ---------------------------------------------------------------- walking

        void FixedUpdate()
        {
            if (!routeReady) return;
            float dt = Time.fixedDeltaTime;
            switch (state)
            {
                case State.Hidden:
                    if (Time.time >= hiddenUntil) TrySpawn();
                    return;
                case State.Walking:
                    Walk(dt);
                    break;
                case State.Stopped:
                    speed = Mathf.MoveTowards(speed, 0f, Decel * 2f * dt);
                    if (Time.time >= stopUntil) Resume();
                    break;
                case State.Waiting:
                {
                    speed = Mathf.MoveTowards(speed, 0f, Decel * 2f * dt);
                    int c = CrossingAhead();
                    if (c < 0 || MayCross(c)) Resume();
                    break;
                }
                case State.Aside:
                    speed = Mathf.MoveTowards(speed, 0f, Decel * 2f * dt);
                    if (AmbientView.OutsideBy(x, depth) > HiddenBeyond) { Recycle(); return; }
                    if (Time.time >= nextGestureChange && company != Company.Friend)
                    {
                        gesture = gesture == Gesture.Look ? Gesture.Phone : Gesture.Look;
                        nextGestureChange = Time.time + Range(5f, 10f);
                    }
                    x += direction * speed * dt;
                    break;
            }
            if (state == State.Hidden) return;
            body.MovePosition(BodyAt(x));
        }

        /// <summary>How far to where they wait for crossing c (just short of its near kerb); negative once on it.</summary>
        float KerbDistance(int c)
        {
            float near = direction > 0 ? crossFrom[c] : crossTo[c];
            return (near - x) * direction - 0.45f;
        }

        /// <summary>
        /// Is the green man showing, with time enough left to be past the side street's traffic
        /// (it drives through the middle of the crossing) before the red man?
        /// </summary>
        bool MayCross(int c)
        {
            var crossing = crossings[c];
            if (crossing == null) return true;
            if (crossing.Current != Crossing.Light.Green) return false;
            float centre = (crossFrom[c] + crossTo[c]) * 0.5f;
            float pastTraffic = (centre - x) * direction + 1.3f;
            float need = Mathf.Max(0f, pastTraffic) / Mathf.Max(0.5f, cruise) + (speed < 0.3f ? 0.7f : 0f);
            return crossing.WalkTimeLeft + 0.3f >= need;
        }

        void Resume()
        {
            state = State.Walking;
            gesture = companionGesture = Gesture.None;
        }

        /// <summary>The next crossing ahead (or the one they are on), or -1.</summary>
        int CrossingAhead()
        {
            int best = -1;
            float bestDist = float.MaxValue;
            for (int i = 0; i < crossingCount; i++)
            {
                // Distance to its near kerb; negative once on it, until past its far kerb.
                float near = direction > 0 ? crossFrom[i] : crossTo[i];
                float far = direction > 0 ? crossTo[i] : crossFrom[i];
                float toFar = (far - x) * direction;
                if (toFar < 0f) continue;
                float toNear = (near - x) * direction;
                if (toNear < bestDist) { bestDist = toNear; best = i; }
            }
            return best;
        }

        void Walk(float dt)
        {
            float target = cruise;
            float end = direction > 0 ? routeMax : routeMin;
            float toEnd = (end - x) * direction;
            float z = depth;
            // Where they must be stopped by: the end of the walk if it is in view (they step
            // aside there), the kerb at a red man, or where they mean to stop for a moment.
            float stopDist = float.MaxValue;
            int reason = 0;   // 1 end in view, 2 kerb, 3 a moment's stop
            bool endInView = AmbientView.Valid && AmbientView.OutsideBy(end, z) <= HiddenBeyond;
            if (endInView) { stopDist = toEnd - 0.1f; reason = 1; }
            int c = CrossingAhead();
            if (c >= 0 && crossings[c] != null)
            {
                float kerb = KerbDistance(c);
                if (kerb > -0.3f)
                {
                    // Not on it yet: stop at the kerb unless the green man gives time to get over.
                    if (!MayCross(c) && kerb < stopDist) { stopDist = Mathf.Max(0f, kerb); reason = 2; }
                }
                else if (crossings[c].Current != Crossing.Light.Green) target *= 1.4f;   // the man is flashing: hurry
            }
            if (!float.IsNaN(stopAt))
            {
                float toStop = (stopAt - x) * direction;
                if (toStop < -0.5f) stopAt = float.NaN;
                else if (toStop < stopDist) { stopDist = Mathf.Max(0f, toStop); reason = 3; }
            }

            // Ease off so as to stop right there; ease back up to pace.
            float allowed = Mathf.Sqrt(2f * Decel * Mathf.Max(0f, stopDist));
            float want = Mathf.Min(target, allowed);
            speed = Mathf.MoveTowards(speed, want, (want > speed ? Accel : Decel * 1.6f) * dt);
            x += direction * speed * dt;

            if ((end - x) * direction <= 0f)
            {
                x = end;
                // At the end of the walk: gone if no one sees, else off the ball's line.
                if (!AmbientView.Valid || AmbientView.OutsideBy(x, z) > HiddenBeyond) Recycle();
                else StepAside();
                return;
            }
            if (reason != 0 && stopDist <= 0.03f && speed < 0.12f)
            {
                if (reason == 1) { StepAside(); return; }
                if (reason == 2)
                {
                    state = State.Waiting;
                    gesture = companionGesture = Gesture.Wait;
                    return;
                }
                stopAt = float.NaN;
                state = State.Stopped;
                stopUntil = Time.time + Range(1.6f, 3.6f);
                gesture = stopGesture;
                companionGesture = company == Company.Friend ? Gesture.Chat : Gesture.Wait;
                return;
            }

            // Walked well out of sight, going away (or left far behind the kid): the next one
            // comes along. Out of sight ahead and walking this way, they simply walk on.
            if (AmbientView.Valid)
            {
                float outside = AmbientView.OutsideBy(x, z);
                float fromCamera = x - AmbientView.CameraX;
                bool goingAway = fromCamera * direction > 0f;
                if ((outside > Margin && goingAway) || (outside > Margin + 8f && fromCamera < 0f)) Recycle();
            }
        }

        // ---------------------------------------------------------------- the look

        void Update()
        {
            if (state == State.Hidden) return;
            ApplyVisual(Time.deltaTime);
        }

        void LateUpdate()
        {
            if (state == State.Hidden || lead == null || rig == null || companion == null) return;
            LayLead();
        }

        /// <summary>Where the company walks (or stands), relative to the walker's root.</summary>
        Vector3 CompanionTarget()
        {
            float side = direction;
            float baseY = companionOffset.y;
            if (GroundAt(x) > feetY + 0.05f)
            {
                // Up a ramp or on a raised walkway (no deeper than the lane): single file.
                switch (company)
                {
                    case Company.Friend: return new Vector3(-side * 0.8f, baseY, depth);
                    case Company.Child: return new Vector3(-side * 0.6f, baseY, depth);
                    case Company.Dog: return new Vector3(side * 0.85f, baseY, depth);
                }
            }
            switch (company)
            {
                case Company.Friend:
                    if (state == State.Aside) return new Vector3(side * 0.75f, baseY, asideZ + 0.05f);
                    return new Vector3(side * 0.2f, baseY, depth + 0.45f);
                case Company.Child:
                    if (state == State.Aside) return new Vector3(-side * 0.55f, baseY, asideZ + 0.1f);
                    return new Vector3(side * 0.05f, baseY, depth + 0.4f);
                case Company.Dog:
                    if (state == State.Aside || state == State.Waiting || state == State.Stopped) return new Vector3(side * 0.55f, baseY, depth + 0.35f);
                    return new Vector3(side * 0.8f, baseY, depth + 0.4f);
            }
            return companionOffset;
        }

        void ApplyVisual(float dt)
        {
            if (visual == null) return;
            // Stepping aside (or back): a gentle sidestep in depth.
            // Up a ramp or on a raised walkway they keep to its middle (it is no deeper than the lane).
            bool raised = GroundAt(x) > feetY + 0.05f;
            float wantDepth = raised ? Mathf.Min(visualBasePosition.z, 0.55f) : state == State.Aside ? asideZ : visualBasePosition.z;
            depth = Mathf.MoveTowards(depth, wantDepth, 0.7f * dt);

            // Facing: the way they walk; toward the shops to look in a window; down at a phone a
            // little toward the camera; toward their friend to chat.
            float walkYaw = Presentation.CharacterRig.FacingYaw(direction);
            float want = walkYaw;
            Vector3 comp = companion != null ? companion.localPosition : Vector3.zero;
            switch (gesture)
            {
                case Gesture.Look: want = direction > 0 ? -55f : 235f; break;
                case Gesture.Phone: want = Presentation.CharacterRig.FacingYaw(direction * 0.45f); break;
                case Gesture.Chat:
                    if (companion != null) want = AmbientAgent.SideYaw(comp.x, comp.z - depth, 10f);
                    break;
            }
            yaw = Mathf.SmoothDampAngle(yaw, want, ref yawVelocity, 0.3f);
            visual.localRotation = Quaternion.Euler(0f, yaw, 0f);
            float hop = Mathf.Max(0f, Mathf.Sin(Mathf.Clamp01((Time.time - hopTime) / 0.35f) * Mathf.PI)) * 0.3f;
            visual.localPosition = new Vector3(visualBasePosition.x, visualBasePosition.y + hop, depth);

            if (companion == null) return;
            // The company keeps alongside, a step behind the walker's line.
            Vector3 target = CompanionTarget();
            Vector3 next = Vector3.SmoothDamp(comp, target, ref companionVelocity, 0.35f, 3f, Mathf.Max(dt, 1e-4f));
            next.y = companionOffset.y + GroundAt(x + next.x) - GroundAt(x);   // feet on the ramp where they are
            companion.localPosition = next;
            float cWant = walkYaw;
            if (companionGesture == Gesture.Chat) cWant = AmbientAgent.SideYaw(-comp.x, depth - comp.z, 10f);
            else if (companionGesture == Gesture.Look) cWant = direction > 0 ? -60f : 240f;
            else if (company == Company.Dog)
            {
                Vector3 v = companionVelocity;
                if (speed > 0.1f) cWant = AmbientAgent.SideYaw(direction, 0f, 20f);
                else if (v.sqrMagnitude > 0.01f) cWant = AmbientAgent.SideYaw(v.x, v.z, 20f);
                else cWant = companionYaw;
            }
            companionYaw = Mathf.SmoothDampAngle(companionYaw, cWant, ref companionYawVelocity, 0.25f);
            companion.localRotation = Quaternion.Euler(0f, companionYaw, 0f);

            if (company != Company.Dog) return;
            // The dog trots along: legs in diagonal pairs, tail going.
            float trot = Mathf.Max(speed, companionVelocity.magnitude);
            float gait = Mathf.Clamp01(trot / 0.5f);
            dogStride += dt * trot * 10f;
            for (int i = 0; i < companionLegs.Length && i < companionLegRest.Length; i++)
                if (companionLegs[i] != null)
                    companionLegs[i].localRotation = companionLegRest[i] * Quaternion.AngleAxis(Mathf.Sin(dogStride + (i == 0 || i == 3 ? 0f : Mathf.PI)) * 26f * gait, companionLegAxis);
            wagPhase += dt * (gait > 0.2f ? 9f : 6f);
            if (companionTail != null)
                companionTail.localRotation = companionTailRest * Quaternion.AngleAxis(Mathf.Sin(wagPhase) * 22f, companionTailAxis);
        }

        /// <summary>The lead, from the hand on the dog's side to its collar.</summary>
        void LayLead()
        {
            Transform shoulder = rig.armBack, elbow = rig.elbowBack;
            if (rig.armFront != null && rig.armBack != null && rig.armFront.position.z > rig.armBack.position.z)
            {
                shoulder = rig.armFront;
                elbow = rig.elbowFront;
            }
            if (shoulder == null || elbow == null) return;
            Vector3 hand = elbow.position + (elbow.position - shoulder.position) * 0.95f;
            Vector3 collar = companion.TransformPoint(new Vector3(0.12f, 0.31f, 0f));   // the kit dog's neck, at 0.85 scale
            Vector3 along = collar - hand;
            float len = along.magnitude;
            if (len < 0.05f) return;
            lead.position = (hand + collar) * 0.5f;
            lead.rotation = Quaternion.LookRotation(along / len, Vector3.up);
            lead.localScale = new Vector3(1f, 1f, len);
        }

        // ---------------------------------------------------------------- the ball

        void OnCollisionEnter2D(Collision2D collision)
        {
            Ball.BallController ball;
            if (!TryGetBall(collision.collider, out ball)) return;
            hopTime = Time.time;
            if (state == State.Walking || state == State.Stopped)
            {
                // Startled: they stop dead for a moment, then walk on.
                speed = 0f;
                state = State.Stopped;
                stopUntil = Time.time + pauseTime;
                gesture = Gesture.None;
            }
            Core.GameEvents.Raise(Core.GameEventType.PedestrianBump, transform.position, collision.relativeVelocity.magnitude / 10f);
            if (Bumped != null) Bumped(this);
        }
    }
}
