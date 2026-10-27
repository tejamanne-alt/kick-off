using DribbleToSchool.Ball;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>The school gate. Finishes the run when the ball arrives.</summary>
    [RequireComponent(typeof(Collider2D))]
    public class GoalZone : MonoBehaviour
    {
        public TestTrackSession session;

        void Reset()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (session == null) return;
            if (other.attachedRigidbody != null && other.attachedRigidbody.GetComponent<BallController>() != null)
                session.ReachGoal();
        }
    }
}
