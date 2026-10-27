using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Puddles, sand, mud: the ball drags and the kid wades. Not deadly, just slow.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class SlowZone : HazardBase
    {
        [Tooltip("Horizontal ball slow-down per second while rolling through.")]
        public float ballDrag = 2.5f;
        [Range(0.1f, 1f)] public float kidSpeedMultiplier = 0.6f;
        public string surfaceName = "Puddle";

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            Player.KidController kid;
            if (TryGetKid(other, out kid)) kid.AddSpeedModifier(this, kidSpeedMultiplier);
        }

        void OnTriggerExit2D(Collider2D other)
        {
            Player.KidController kid;
            if (TryGetKid(other, out kid)) kid.RemoveSpeedModifier(this);
        }

        void OnTriggerStay2D(Collider2D other)
        {
            Ball.BallController ball;
            if (!TryGetBall(other, out ball)) return;
            Vector2 v = ball.Body.linearVelocity;
            v.x *= Mathf.Clamp01(1f - ballDrag * Time.fixedDeltaTime);
            ball.Body.linearVelocity = v;
        }
    }
}
