using DribbleToSchool.Ball;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.CameraRig
{
    /// <summary>
    /// Keeps the kid on the left third of the screen with room to see what's
    /// coming, leaning toward the ball when it flies off after a kick.
    /// (Phase 2 swaps this for Cinemachine.)
    /// </summary>
    public class CameraFollow2D : MonoBehaviour
    {
        public KidController kid;
        public BallController ball;
        [Tooltip("How much the camera leans toward the ball (0 = kid only).")]
        [Range(0f, 1f)] public float ballWeight = 0.35f;
        [Tooltip("Offset from the focus point. Positive x = look ahead to the right.")]
        public Vector2 offset = new Vector2(3f, 1.8f);
        public float smoothTimeX = 0.2f;
        public float smoothTimeY = 0.35f;
        [Tooltip("Camera never goes below this height.")]
        public float minY = 2f;

        float velocityX;
        float velocityY;

        void LateUpdate()
        {
            if (kid == null) return;

            Vector2 focus = kid.transform.position;
            if (ball != null) focus = Vector2.Lerp(focus, ball.transform.position, ballWeight);
            Vector2 target = focus + offset;

            Vector3 pos = transform.position;
            pos.x = Mathf.SmoothDamp(pos.x, target.x, ref velocityX, smoothTimeX);
            pos.y = Mathf.Max(minY, Mathf.SmoothDamp(pos.y, target.y, ref velocityY, smoothTimeY));
            transform.position = pos;
        }

        public void SnapToTarget()
        {
            if (kid == null) return;
            Vector2 target = (Vector2)kid.transform.position + offset;
            transform.position = new Vector3(target.x, Mathf.Max(minY, target.y), transform.position.z);
            velocityX = velocityY = 0f;
        }
    }
}
