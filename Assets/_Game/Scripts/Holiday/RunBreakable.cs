using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// A crate, sandcastle or cone stack that a kicked ball smashes (see BallSmasher): it bursts, shedding
    /// coins, and is no longer in the way.
    /// </summary>
    public class RunBreakable : RunSolid
    {
        [Tooltip("Coins it is worth when smashed.")]
        public int coins = 3;

        public bool Smashed { get; private set; }

        protected override void OnEnable()
        {
            base.OnEnable();
            Smashed = false;
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
