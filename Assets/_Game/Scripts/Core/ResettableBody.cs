using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Puts a pushable physics object (crate, barrel) back where it started on restart, and when the kid goes back to a
    /// checkpoint behind where it started (so a crate knocked into the way is out of it again).
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class ResettableBody : MonoBehaviour, IResettable, IResetAhead
    {
        Rigidbody2D body;
        Vector2 startPosition;
        float startRotation;

        void Awake()
        {
            body = GetComponent<Rigidbody2D>();
            startPosition = body.position;
            startRotation = body.rotation;
        }

        public void ResetAhead(float checkpointX)
        {
            if (startPosition.x >= checkpointX - 1f) ResetState();
        }

        public void ResetState()
        {
            body.position = startPosition;
            body.rotation = startRotation;
            transform.SetPositionAndRotation(startPosition, Quaternion.Euler(0f, 0f, startRotation));
            body.linearVelocity = Vector2.zero;
            body.angularVelocity = 0f;
        }
    }
}
