using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// A slalom gate. Low gates: the ball must pass underneath the bar (keep it
    /// on the ground). Hoops: the ball must fly through above the given height.
    /// </summary>
    public class SlalomGate : MonoBehaviour, IResettable
    {
        public enum Kind { Low, Hoop }

        public Kind kind = Kind.Low;
        [Tooltip("Low: the ball must be below this height. Hoop: between this and +hoopSize.")]
        public float height = 0.7f;
        public float hoopSize = 1.2f;
        public SpriteRenderer[] flags;

        public bool Done { get; private set; }
        public bool Passed { get; private set; }
        public event System.Action<SlalomGate, bool> Crossed;

        float lastBallX = float.NegativeInfinity;

        void Update()
        {
            var level = LevelManager.Current;
            if (level == null || Done) return;
            Vector2 b = level.ball.transform.position;
            float x = transform.position.x;
            if (lastBallX < x && b.x >= x)
            {
                float rel = b.y - transform.position.y;
                bool ok = kind == Kind.Low ? rel <= height : rel >= height && rel <= height + hoopSize;
                Done = true;
                Passed = ok;
                Paint(ok ? new Color(0.4f, 0.9f, 0.45f) : new Color(0.95f, 0.35f, 0.3f));
                GameEvents.Raise(ok ? GameEventType.PerfectTouch : GameEventType.BallBounce, transform.position, ok ? 0.6f : 0.3f);
                if (Crossed != null) Crossed(this, ok);
            }
            lastBallX = b.x;
        }

        void Paint(Color c)
        {
            if (flags == null) return;
            foreach (var f in flags) if (f != null) f.color = c;
        }

        public void ResetState()
        {
            Done = false;
            Passed = false;
            lastBallX = float.NegativeInfinity;
            Paint(new Color(1f, 0.85f, 0.3f));
        }
    }
}
