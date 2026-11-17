using KickOffTales.Ball;
using KickOffTales.Core;
using KickOffTales.Player;
using UnityEngine;

namespace KickOffTales.Hazards
{
    /// <summary>
    /// Shared plumbing for hazards and interactables: access to the level, kid
    /// and ball, collider identification, and restart support.
    /// </summary>
    public abstract class HazardBase : MonoBehaviour, IResettable
    {
        protected static LevelManager Level { get { return LevelManager.Current; } }
        protected static BallController Ball { get { return Level != null ? Level.ball : null; } }
        protected static KidController Kid { get { return Level != null ? Level.kid : null; } }

        /// <summary>True while the level is actually being played (not paused, intro or finished).</summary>
        protected static bool IsLive { get { return Level != null && Level.State == LevelState.Playing; } }

        public virtual void ResetState() { }

        protected static bool TryGetBall(Collider2D col, out BallController ball)
        {
            ball = col.attachedRigidbody != null ? col.attachedRigidbody.GetComponent<BallController>() : null;
            return ball != null;
        }

        protected static bool TryGetKid(Collider2D col, out KidController kid)
        {
            kid = col.attachedRigidbody != null ? col.attachedRigidbody.GetComponent<KidController>() : null;
            return kid != null;
        }

        protected static void Lose(string reason)
        {
            if (Level != null) Level.LoseBall(reason);
        }
    }
}
