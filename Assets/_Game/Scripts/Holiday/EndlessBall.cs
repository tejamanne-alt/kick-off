using DribbleToSchool.Ball;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// The ball of a Holiday Run: dribbled along at the kid's feet by itself, and shot ahead on KICK to
    /// smash crates and targets, then called back. Drives the scene's BallController (switched off) body.
    /// </summary>
    public class EndlessBall : MonoBehaviour
    {
        public BallController ball;
        public KidController kid;

        /// <summary>Back at the kid's feet (a restart, a revive, a new day).</summary>
        public void ResetAt(Vector3 kidPosition)
        {
        }
    }
}
