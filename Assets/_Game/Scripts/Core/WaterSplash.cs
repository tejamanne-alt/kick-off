using DribbleToSchool.Ball;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// The surface of a stretch of water (a flooded trench, a park stream, a tidal channel): the ball or the kid going in
    /// raises the splash where they break the surface, as they go in. The water's LoseZone lies two metres under it, so a
    /// splash raised there came as the screen faded, out of sight under the water (docs/LEARNINGS.md C23).
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class WaterSplash : MonoBehaviour
    {
        [Tooltip("World height of the water's surface.")]
        public float surfaceY;

        void Reset()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            Rigidbody2D rb = other.attachedRigidbody;
            if (rb == null) return;
            bool ball = rb.GetComponent<BallController>() != null;
            if (!ball && rb.GetComponent<KidController>() == null) return;
            // How hard it hits the water: a kid's fall is a bigger splash than a ball's.
            float hit = Mathf.Clamp01(-rb.linearVelocity.y / 9f) * (ball ? 0.7f : 1f) + (ball ? 0.15f : 0.4f);
            GameEvents.Raise(GameEventType.Splash, new Vector2(rb.position.x, surfaceY), Mathf.Clamp01(hit));
        }
    }
}
