using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>A target (window, tyre, bin lid) that pops when the ball hits it.</summary>
    [RequireComponent(typeof(Collider2D))]
    public class ChallengeTarget : MonoBehaviour, IResettable
    {
        public SpriteRenderer face;
        public Color idleColor = new Color(1f, 0.85f, 0.3f);
        public Color hitColor = new Color(0.4f, 0.9f, 0.5f);

        public bool IsHit { get; private set; }
        public event System.Action<ChallengeTarget> Hit;

        float hitTime = -10f;
        Vector3 baseScale = Vector3.one;

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
            baseScale = transform.localScale;
            ApplyLook();
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (IsHit || other.attachedRigidbody == null || other.attachedRigidbody.GetComponent<BallController>() == null) return;
            IsHit = true;
            hitTime = Time.time;
            ApplyLook();
            GameEvents.Raise(GameEventType.SwitchPressed, transform.position);
            if (Hit != null) Hit(this);
        }

        void Update()
        {
            float t = Mathf.Clamp01((Time.time - hitTime) / 0.3f);
            float pop = IsHit ? Mathf.Sin(t * Mathf.PI) * 0.35f : Mathf.Sin(Time.time * 3f + transform.position.x) * 0.04f;
            transform.localScale = baseScale * (1f + pop);
        }

        void ApplyLook()
        {
            if (face != null) face.color = IsHit ? hitColor : idleColor;
        }

        public void ResetState()
        {
            IsHit = false;
            transform.localScale = baseScale;
            ApplyLook();
        }
    }
}
