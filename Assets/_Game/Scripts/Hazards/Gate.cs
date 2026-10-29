using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A solid gate opened by a switch. With a sliding panel it rolls the panel aside (by
    /// <see cref="slide"/>) and stops blocking once it is half open; otherwise the whole gate
    /// slides up out of the way.
    /// </summary>
    public class Gate : HazardBase, Core.IBallStrander
    {
        public float openHeight = 2.5f;
        public float openDuration = 0.6f;
        [Tooltip("Optional: the visible gate, rolled aside by 'slide' while the collider simply switches off.")]
        public Transform slidingPanel;
        public Vector3 slide = new Vector3(0f, 0f, 3.4f);

        public bool IsOpen { get; private set; }
        public event System.Action<Gate> Opened;

        Vector3 closedPosition, panelClosed;
        float openAmount;
        Collider2D[] colliders;

        void Awake()
        {
            closedPosition = transform.position;
            if (slidingPanel != null) panelClosed = slidingPanel.localPosition;
            colliders = GetComponents<Collider2D>();
        }

        public void Open()
        {
            if (IsOpen) return;
            IsOpen = true;
            Core.GameEvents.Raise(Core.GameEventType.GateOpened, transform.position);
            if (Opened != null) Opened(this);
        }

        /// <summary>The ball has gone over the closed gate while the kid is still on this side:
        /// the switch that opens it is on this side too, so the ball can't be fetched.</summary>
        public bool Strands(Vector2 ball, Vector2 kid)
        {
            float x = closedPosition.x;
            return !IsOpen && ball.x > x + 0.35f && kid.x < x - 0.1f;
        }

        public override void ResetState()
        {
            IsOpen = false;
            openAmount = 0f;
            transform.position = closedPosition;
            Apply(0f);
        }

        void Update()
        {
            float target = IsOpen ? 1f : 0f;
            if (Mathf.Approximately(openAmount, target)) return;
            openAmount = Mathf.MoveTowards(openAmount, target, Time.deltaTime / Mathf.Max(openDuration, 0.01f));
            Apply(openAmount * openAmount * (3f - 2f * openAmount));
        }

        void Apply(float eased)
        {
            if (slidingPanel == null)
            {
                transform.position = closedPosition + Vector3.up * openHeight * eased;
                return;
            }
            slidingPanel.localPosition = panelClosed + slide * eased;
            if (colliders != null)
                foreach (var c in colliders) c.enabled = eased < 0.5f;
        }
    }
}
