using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Swoops across its stretch of beach on a wavy path every few seconds.
    /// Clipping the ball knocks it back and up. Watch the sky and time your kicks.
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

        public event System.Action<Seagull> HitBall;

        float time;
        float lastHit = -10f;

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Place();
        }

        void Update()
        {
            time += Time.deltaTime;
            Place();
        }

        void Place()
        {
            float cycle = flightTime + restTime;
            float c = Mathf.Repeat(time, cycle);
            bool flying = c < flightTime;
            if (visual != null) visual.gameObject.SetActive(flying);
            GetComponent<Collider2D>().enabled = flying;
            if (!flying) return;

            float k = c / flightTime;
            float x = Mathf.Lerp(fromX, toX, k);
            float y = baseY + Mathf.Sin(k * Mathf.PI * 3f) * waveHeight;
            transform.position = new Vector3(x, y, 0f);

            if (visual != null)
            {
                // Face the direction of flight and flap.
                float dir = Mathf.Sign(toX - fromX);
                float flap = 0.7f + Mathf.Abs(Mathf.Sin(time * 12f)) * 0.3f;
                visual.localScale = new Vector3(dir * 1f, flap, 1f);
            }
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
