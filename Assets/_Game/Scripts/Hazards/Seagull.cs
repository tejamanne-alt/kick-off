using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Swoops across its stretch of beach on a wavy path every few seconds.
    /// Clipping the ball knocks it back and up. Watch the sky and time your kicks.
    ///
    /// Between swoops the gull never just vanishes: at the end of its run it pulls up and away out
    /// of the top of the view, and it comes back diving in from high up behind the start of its run,
    /// so it is always somewhere in the sky. Only the swoop itself (the same path and timing as
    /// ever) can touch the ball.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Seagull : HazardBase
    {
        public float fromX = 10f;
        public float toX = -10f;
        public float baseY = 2.5f;
        public float waveHeight = 0.8f;
        public float flightTime = 3.5f;
        public float restTime = 2f;
        public float phaseOffset;
        public Vector2 knockVelocity = new Vector2(-3f, 4f);
        public Transform visual;
        [Tooltip("Wing pivots at the shoulders, flapped about the body's long axis.")]
        public Transform[] wings;
        [Tooltip("How high above its run the gull climbs between swoops (out of the top of the view).")]
        public float climb = 5.2f;

        public event System.Action<Seagull> HitBall;

        float time;
        float lastHit = -10f;
        float flap, flapWeight = 1f;
        Quaternion[] wingRest;
        Collider2D trigger;

        /// <summary>True while the gull is on its run, low enough to hit the ball.</summary>
        public bool IsSwooping { get; private set; }

        void Awake()
        {
            // Flap each wing from its rest pose (model parts may come in rotated).
            wingRest = new Quaternion[wings != null ? wings.Length : 0];
            for (int i = 0; i < wingRest.Length; i++) wingRest[i] = wings[i] != null ? wings[i].localRotation : Quaternion.identity;
            trigger = GetComponent<Collider2D>();
            trigger.isTrigger = true;
            if (visual != null) visual.gameObject.SetActive(true);
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Place(0f);
        }

        void Update()
        {
            time += Time.deltaTime;
            Place(Time.deltaTime);
        }

        float Direction { get { float d = Mathf.Sign(toX - fromX); return d == 0f ? -1f : d; } }

        /// <summary>The swoop (k from 0 to 1): the path the ball has to dodge.</summary>
        Vector2 Swoop(float k)
        {
            return new Vector2(Mathf.Lerp(fromX, toX, k), baseY + Mathf.Sin(k * Mathf.PI * 3f) * waveHeight);
        }

        /// <summary>The swoop's velocity (per second) at k.</summary>
        Vector2 SwoopVelocity(float k)
        {
            float t = Mathf.Max(0.05f, flightTime);
            return new Vector2((toX - fromX) / t, Mathf.Cos(k * Mathf.PI * 3f) * Mathf.PI * 3f * waveHeight / t);
        }

        /// <summary>A cubic Hermite curve from p0 to p1 with the given end velocities (per unit of s).</summary>
        static Vector2 Hermite(Vector2 p0, Vector2 m0, Vector2 p1, Vector2 m1, float s, out Vector2 velocity)
        {
            float s2 = s * s, s3 = s2 * s;
            velocity = (6f * s2 - 6f * s) * p0 + (3f * s2 - 4f * s + 1f) * m0 + (-6f * s2 + 6f * s) * p1 + (3f * s2 - 2f * s) * m1;
            return (2f * s3 - 3f * s2 + 1f) * p0 + (s3 - 2f * s2 + s) * m0 + (-2f * s3 + 3f * s2) * p1 + (s3 - s2) * m1;
        }

        void Place(float dt)
        {
            float cycle = flightTime + restTime;
            float c = Mathf.Repeat(time, cycle);
            IsSwooping = c < flightTime;
            trigger.enabled = IsSwooping;

            Vector2 pos, vel;
            bool climbing = false;
            if (IsSwooping)
            {
                float k = c / flightTime;
                pos = Swoop(k);
                vel = SwoopVelocity(k);
            }
            else
            {
                // Away and back: half the rest climbing out past the end of the run, half diving
                // back in from high up behind its start (the swap happens out of sight, up high).
                float half = Mathf.Max(0.05f, restTime * 0.5f);
                float r = c - flightTime, dir = Direction;
                float across = Mathf.Abs(toX - fromX) / Mathf.Max(0.05f, flightTime) * half;
                Vector2 high = new Vector2(0f, climb);
                if (r < half)
                {
                    Vector2 p0 = Swoop(1f), p1 = p0 + new Vector2(dir * across, 0f) + high;
                    pos = Hermite(p0, SwoopVelocity(1f) * half, p1, new Vector2(dir * across * 0.8f, climb * 0.6f), r / half, out vel);
                    climbing = true;
                }
                else
                {
                    Vector2 p1 = Swoop(0f), p0 = p1 - new Vector2(dir * across, 0f) + high;
                    pos = Hermite(p0, new Vector2(dir * across * 0.8f, -climb * 0.6f), p1, SwoopVelocity(0f) * half, (r - half) / half, out vel);
                    pos.y = Mathf.Max(pos.y, baseY - waveHeight * 1.2f);
                }
                vel /= half;
            }
            transform.position = new Vector3(pos.x, pos.y, 0f);

            if (visual == null) return;
            // Face the way it flies, nose up as it climbs and down as it dives; flap, or glide on
            // the way down.
            float facing = Direction;
            float pitch = Mathf.Clamp(Mathf.Atan2(vel.y, Mathf.Abs(vel.x) + 0.01f) * Mathf.Rad2Deg, -40f, 40f) * 0.7f;
            visual.localRotation = Quaternion.Euler(0f, Presentation.CharacterRig.FacingYaw(facing), pitch);
            bool gliding = !IsSwooping && !climbing;
            flap += dt * (climbing ? 14f : 11f);
            flapWeight = Mathf.MoveTowards(flapWeight, gliding ? 0f : 1f, dt * 2.5f);
            float angle = Mathf.Lerp(10f + Mathf.Sin(time * 2f) * 3f, Mathf.Sin(flap) * 38f, flapWeight);
            if (wings != null)
                for (int i = 0; i < wings.Length && i < wingRest.Length; i++)
                    if (wings[i] != null)
                        wings[i].localRotation = wingRest[i] * Quaternion.Euler((i == 0 ? -1f : 1f) * angle, 0f, 0f);
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            Ball.BallController ball;
            if (!TryGetBall(other, out ball) || Time.time - lastHit < 0.6f || !IsLive) return;
            lastHit = Time.time;
            Vector2 v = knockVelocity;
            v.x = Mathf.Sign(toX - fromX) * Mathf.Abs(v.x);   // pushed along the bird's flight
            ball.Kick(v);
            Core.GameEvents.Raise(Core.GameEventType.SeagullHit, transform.position);
            if (HitBall != null) HitBall(this);
        }
    }
}
