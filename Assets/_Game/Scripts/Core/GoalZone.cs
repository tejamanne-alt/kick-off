using DribbleToSchool.Ball;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>The school gate. Finishes the level when the ball arrives.</summary>
    [RequireComponent(typeof(Collider2D))]
    public class GoalZone : MonoBehaviour
    {
        void Reset()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            var level = LevelManager.Current;
            if (level == null) return;
            if (other.attachedRigidbody != null && other.attachedRigidbody.GetComponent<BallController>() != null)
                level.ReachGoal();
        }
    }
}
