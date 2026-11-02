using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// Something a kicked ball bursts for coins (see BallSmasher): a crate, a sandcastle or a stack of cones, which bursts and
    /// is no longer in the way; or a floating target (<see cref="floating"/>: a balloon, a paper lantern, a beach ball hanging
    /// 2 to 4 m up) that bursts into coins when the ball flies through it.
    /// </summary>
    public class RunBreakable : RunSolid
    {
        [Tooltip("Coins it is worth when smashed.")]
        public int coins = 3;

        [Tooltip("A target hanging in the air, not an obstacle: the director does not count it as one, the kid passes through it and only the ball bursts it. " +
            "Its collider is a trigger.")]
        public bool floating;

        [Tooltip("How fast (m/s) the ball must be going to burst it. 0: BallSmasher's own limit (a crate wants a hard kick; a balloon only a ball flying at it).")]
        public float minSpeed;

        public bool Smashed { get; private set; }

        Vector3 basePosition;
        float phase;

        protected override void OnEnable()
        {
            Smashed = false;
            if (floating)
            {
                // Not an obstacle: nothing for the director to count, and nothing to crash into.
                basePosition = transform.position;
                phase = basePosition.x * 0.37f;
                return;
            }
            base.OnEnable();
        }

        void Update()
        {
            if (!floating || Smashed) return;
            // Bobbing and swaying on its string.
            float t = Time.time + phase;
            transform.position = basePosition + new Vector3(Mathf.Sin(t * 0.9f) * 0.12f, Mathf.Sin(t * 1.7f) * 0.14f, 0f);
        }

        /// <summary>Burst it. <paramref name="point"/> is where it was hit.</summary>
        public void Smash(Vector2 point)
        {
            if (Smashed) return;
            Smashed = true;
            foreach (var c in GetComponentsInChildren<Collider2D>(true)) c.enabled = false;
            foreach (var r in GetComponentsInChildren<Renderer>(true)) r.enabled = false;
            GameEvents.Raise(GameEventType.Kick, point, 0.8f);
            GameEvents.Raise(GameEventType.Coin, point, 0.6f);
            var director = HolidayRunDirector.Current;
            if (director != null) director.OnSmashed(this, point);
        }
    }
}
