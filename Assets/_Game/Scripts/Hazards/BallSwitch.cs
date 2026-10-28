using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A target the ball must hit hard enough (a doorbell, a sign, a button).
    /// Opens its gates once and stays pressed.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class BallSwitch : HazardBase
    {
        public Gate[] gates;
        [Tooltip("Minimum impact speed. Low values let a dribble press it.")]
        public float minImpactSpeed = 3f;
        public Renderer indicator;
        public Color offColor = new Color(0.9f, 0.3f, 0.3f);
        public Color onColor = new Color(0.3f, 0.9f, 0.4f);

        public bool IsPressed { get; private set; }
        public event System.Action<BallSwitch> Pressed;

        void Awake()
        {
            ApplyVisual();
        }

        void OnCollisionEnter2D(Collision2D collision)
        {
            if (IsPressed) return;
            Ball.BallController ball;
            if (!TryGetBall(collision.collider, out ball)) return;
            if (collision.relativeVelocity.magnitude < minImpactSpeed) return;

            IsPressed = true;
            ApplyVisual();
            Core.GameEvents.Raise(Core.GameEventType.SwitchPressed, transform.position);
            if (gates != null)
            {
                foreach (var g in gates)
                {
                    if (g != null) g.Open();
                }
            }
            if (Pressed != null) Pressed(this);
        }

        public override void ResetState()
        {
            IsPressed = false;
            ApplyVisual();
        }

        void ApplyVisual()
        {
            World.Tint.Set(indicator, IsPressed ? onColor : offColor);
        }
    }
}
