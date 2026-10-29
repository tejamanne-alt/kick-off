using DribbleToSchool.Ball;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// The school gate. Finishes the level once the kid and the ball are both through it
    /// (both inside the zone at the same time).
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class GoalZone : MonoBehaviour
    {
        int kidInside, ballInside;

        void Reset()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            Count(other, 1);
            TryFinish();
        }

        void OnTriggerExit2D(Collider2D other)
        {
            Count(other, -1);
        }

        void Count(Collider2D other, int delta)
        {
            var body = other.attachedRigidbody;
            if (body == null) return;
            if (body.GetComponent<BallController>() != null) ballInside = Mathf.Max(0, ballInside + delta);
            else if (body.GetComponent<KidController>() != null) kidInside = Mathf.Max(0, kidInside + delta);
        }

        void TryFinish()
        {
            if (kidInside == 0 || ballInside == 0) return;
            var level = LevelManager.Current;
            if (level != null) level.ReachGoal();
        }

        void OnDisable()
        {
            kidInside = ballInside = 0;
        }
    }
}
