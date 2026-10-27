using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>A solid gate that slides up out of the way when opened by a switch.</summary>
    public class Gate : HazardBase
    {
        public float openHeight = 2.5f;
        public float openDuration = 0.6f;

        public bool IsOpen { get; private set; }
        public event System.Action<Gate> Opened;

        Vector3 closedPosition;
        float openAmount;

        void Awake()
        {
            closedPosition = transform.position;
        }

        public void Open()
        {
            if (IsOpen) return;
            IsOpen = true;
            Core.GameEvents.Raise(Core.GameEventType.GateOpened, transform.position);
            if (Opened != null) Opened(this);
        }

        public override void ResetState()
        {
            IsOpen = false;
            openAmount = 0f;
            transform.position = closedPosition;
        }

        void Update()
        {
            float target = IsOpen ? 1f : 0f;
            if (Mathf.Approximately(openAmount, target)) return;
            openAmount = Mathf.MoveTowards(openAmount, target, Time.deltaTime / Mathf.Max(openDuration, 0.01f));
            float eased = openAmount * openAmount * (3f - 2f * openAmount);
            transform.position = closedPosition + Vector3.up * openHeight * eased;
        }
    }
}
