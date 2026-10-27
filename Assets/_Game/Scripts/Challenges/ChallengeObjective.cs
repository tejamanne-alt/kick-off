using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// A ball-skill challenge replaces "reach the school gate". It keeps a score,
    /// runs its own clock, and turns the score into 0-3 stars.
    /// </summary>
    public abstract class ChallengeObjective : MonoBehaviour, IResettable
    {
        public string challengeName = "Challenge";
        [TextArea] public string instructions = "";
        [Tooltip("Seconds available. 0 = no limit (finish by completing the task).")]
        public float timeLimit = 45f;
        [Tooltip("Score needed for 1, 2 and 3 stars.")]
        public int[] starThresholds = { 3, 6, 10 };
        [Tooltip("For timed runs: smaller scores are better.")]
        public bool lowerIsBetter;

        public float Elapsed { get; private set; }
        public float TimeLeft { get { return timeLimit > 0f ? Mathf.Max(0f, timeLimit - Elapsed) : 0f; } }
        public bool Finished { get; private set; }

        /// <summary>The score that counts for stars.</summary>
        public abstract int Score { get; }
        /// <summary>One line for the HUD, e.g. "Juggles 4 (best 7)".</summary>
        public abstract string StatusText { get; }
        /// <summary>How the score reads on the results screen.</summary>
        public virtual string FormatScore(int score) { return score.ToString(); }

        public int StarsFor(int score)
        {
            int stars = 0;
            for (int i = 0; i < starThresholds.Length && i < 3; i++)
            {
                bool met = lowerIsBetter ? score <= starThresholds[i] : score >= starThresholds[i];
                if (met) stars = i + 1;
            }
            return stars;
        }

        protected virtual void Update()
        {
            var level = LevelManager.Current;
            if (Finished || level == null) return;
            if (level.State != LevelState.Playing && level.State != LevelState.Respawning) return;
            Elapsed += Time.deltaTime;
            if (timeLimit > 0f && Elapsed >= timeLimit) Finish();
        }

        /// <summary>End the challenge now and show the results.</summary>
        protected void Finish()
        {
            if (Finished) return;
            Finished = true;
            if (LevelManager.Current != null) LevelManager.Current.CompleteChallenge(this);
        }

        /// <summary>Called by LevelManager when the ball reaches a GoalZone (slalom finish).</summary>
        public virtual void OnGoalReached() { }

        public virtual void ResetState()
        {
            Elapsed = 0f;
            Finished = false;
        }
    }
}
