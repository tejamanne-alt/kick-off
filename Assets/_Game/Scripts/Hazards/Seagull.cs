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
        [Tooltip("Wing pivots at the shoulders, flapped about the body's long axis.")]
        public Transform[] wings;

        public event System.Action<Seagull> HitBall;

        float time;
        float lastHit = -10f;
        Quaternion[] wingRest;

        void Awake()
        {
            // Flap each wing from its rest pose (model parts may come in rotated).
            wingRest = new Quaternion[wings != null ? wings.Length : 0];
            for (int i = 0; i < wingRest.Length; i++) wingRest[i] = wings[i] != null ? wings[i].localRotation : Quaternion.identity;
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
                // Face the direction of flight, bank with the swoop and flap.
                float dir = Mathf.Sign(toX - fromX);
                float bank = Mathf.Cos(k * Mathf.PI * 3f) * 12f * dir;
                visual.localRotation = Quaternion.Euler(0f, Presentation.CharacterRig.FacingYaw(dir), bank);
                float flap = Mathf.Sin(time * 11f) * 38f;
                if (wings != null)
                    for (int i = 0; i < wings.Length && i < wingRest.Length; i++)
                        if (wings[i] != null)
                            wings[i].localRotation = wingRest[i] * Quaternion.Euler((i == 0 ? -1f : 1f) * flap, 0f, 0f);
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
