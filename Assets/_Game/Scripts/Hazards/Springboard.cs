using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A springy pad set into the ground (a trampoline, a fruit-crate lid):
    /// launches the kid or the ball straight up when they come down onto it.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Springboard : HazardBase
    {
        public float kidLaunchSpeed = 13f;
        public float ballLaunchSpeed = 11f;
        public float cooldown = 0.3f;
        public Transform visual;

        public event System.Action<Springboard> Bounced;

        readonly Dictionary<Rigidbody2D, float> lastLaunch = new Dictionary<Rigidbody2D, float>();
        float squashTime = -10f;
        Vector3 visualBaseScale = Vector3.one;

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
            if (visual != null) visualBaseScale = visual.localScale;
        }

        void OnTriggerStay2D(Collider2D other)
        {
            Rigidbody2D rb = other.attachedRigidbody;
            if (rb == null || rb.linearVelocity.y > 0.5f) return;
            float last;
            if (lastLaunch.TryGetValue(rb, out last) && Time.time - last < cooldown) return;

            Ball.BallController ball;
            Player.KidController kid;
            if (TryGetBall(other, out ball))
                ball.Body.linearVelocity = new Vector2(ball.Body.linearVelocity.x, ballLaunchSpeed);
            else if (TryGetKid(other, out kid))
                kid.Launch(kidLaunchSpeed);
            else
                return;

            lastLaunch[rb] = Time.time;
            squashTime = Time.time;
            Core.GameEvents.Raise(Core.GameEventType.Springboard, transform.position);
            if (Bounced != null) Bounced(this);
        }

        void Update()
        {
            if (visual == null) return;
            float t = Mathf.Clamp01((Time.time - squashTime) / 0.3f);
            float squash = Mathf.Sin(t * Mathf.PI) * 0.35f * (1f - t);
            visual.localScale = new Vector3(visualBaseScale.x * (1f + squash), visualBaseScale.y * (1f - squash), visualBaseScale.z);
        }
    }
}
