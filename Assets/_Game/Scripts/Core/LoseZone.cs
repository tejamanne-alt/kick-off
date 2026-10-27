using DribbleToSchool.Ball;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Trigger that loses the ball: pits, water, traffic lanes. Touching it with
    /// the ball or the kid sends you back to the last checkpoint.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class LoseZone : MonoBehaviour
    {
        [Tooltip("Localization key shown to the player, e.g. lose.gap or lose.splash.")]
        public string message = "lose.ball";

        void Reset()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            var level = LevelManager.Current;
            if (level == null) return;
            Rigidbody2D rb = other.attachedRigidbody;
            if (rb == null) return;
            if (rb.GetComponent<BallController>() != null || rb.GetComponent<KidController>() != null)
            {
                if (message == "lose.splash" || message == "lose.tide") GameEvents.Raise(GameEventType.Splash, rb.position);
                level.LoseBall(message);
            }
        }
    }
}
