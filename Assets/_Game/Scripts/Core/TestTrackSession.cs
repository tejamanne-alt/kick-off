using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// Minimal Phase 1 run loop for the grey-box test track: timer, reset when
    /// the ball is lost, and a finish line. Checkpoints and the real level flow
    /// arrive in Phase 2.
    /// </summary>
    public class TestTrackSession : MonoBehaviour
    {
        public KidController kid;
        public BallController ball;
        public CameraFollow2D cameraFollow;
        [Tooltip("Falling below this height resets the run.")]
        public float killY = -6f;
        [Tooltip("Ball this far behind the kid counts as lost.")]
        public float maxBallBehindDistance = 9f;

        public float ElapsedTime { get; private set; }
        public bool Finished { get; private set; }
        public int Resets { get; private set; }
        public int BestPerfectStreak { get; private set; }

        Vector2 kidStart;
        Vector2 ballStart;

        void Awake()
        {
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            TimeControl.ResetTime();
            kidStart = kid.transform.position;
            ballStart = ball.transform.position;
        }

        void OnEnable()
        {
            ball.PerfectTouch += OnPerfectTouch;
        }

        void OnDisable()
        {
            ball.PerfectTouch -= OnPerfectTouch;
        }

        void OnPerfectTouch(int streak)
        {
            if (streak > BestPerfectStreak) BestPerfectStreak = streak;
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input != null && input.ResetPressed)
            {
                ResetRun();
                return;
            }

            if (Finished)
            {
                if (input != null && input.TouchPressed) ResetRun();
                return;
            }

            ElapsedTime += Time.deltaTime;

            bool fell = kid.transform.position.y < killY || ball.transform.position.y < killY;
            bool leftBehind = kid.transform.position.x - ball.transform.position.x > maxBallBehindDistance;
            if (fell || leftBehind)
            {
                Resets++;
                ResetRun();
            }
        }

        public void ReachGoal()
        {
            if (Finished) return;
            Finished = true;
            kid.InputEnabled = false;
            TimeControl.ResetTime();
        }

        public void ResetRun()
        {
            TimeControl.ResetTime();
            Finished = false;
            ElapsedTime = 0f;
            kid.ResetTo(kidStart);
            ball.ResetTo(ballStart);
            if (cameraFollow != null) cameraFollow.SnapToTarget();
        }
    }
}
