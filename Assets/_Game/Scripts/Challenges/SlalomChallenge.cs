using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// Dribble the course as fast as possible. Missed gates add a time penalty.
    /// Score is tenths of a second (lower is better); finish at the goal.
    /// </summary>
    public class SlalomChallenge : ChallengeObjective
    {
        public SlalomGate[] gates;
        public float missPenalty = 3f;

        int missed;
        int passed;
        float finishTime;

        public override int Score { get { return Mathf.RoundToInt((Finished ? finishTime : Elapsed + missed * missPenalty) * 10f); } }

        public override string StatusText
        {
            get { return "Gates " + passed + " / " + (gates != null ? gates.Length : 0) + "   Missed " + missed + "   " + FormatScore(Score); }
        }

        public override string FormatScore(int score)
        {
            return (score / 10f).ToString("0.0") + "s";
        }

        void Awake()
        {
            lowerIsBetter = true;
            timeLimit = 0f;
            if (gates == null) return;
            foreach (var g in gates)
            {
                if (g != null) g.Crossed += OnCrossed;
            }
        }

        void OnCrossed(SlalomGate gate, bool ok)
        {
            if (ok) passed++;
            else missed++;
        }

        public override void OnGoalReached()
        {
            // Gates the ball never reached count as missed.
            if (gates != null)
            {
                foreach (var g in gates)
                {
                    if (g != null && !g.Done) missed++;
                }
            }
            finishTime = Elapsed + missed * missPenalty;
            Finish();
        }

        public override void ResetState()
        {
            base.ResetState();
            missed = 0;
            passed = 0;
            finishTime = 0f;
        }
    }
}
