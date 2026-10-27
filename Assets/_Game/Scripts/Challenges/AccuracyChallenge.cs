using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>Hit as many targets as possible before time is up. Hitting them all ends it early.</summary>
    public class AccuracyChallenge : ChallengeObjective
    {
        public ChallengeTarget[] targets;

        int hits;

        public override int Score { get { return hits; } }

        public override string StatusText
        {
            get { return "Targets " + hits + " / " + (targets != null ? targets.Length : 0) + "   " + Mathf.CeilToInt(TimeLeft) + "s"; }
        }

        void Awake()
        {
            if (targets == null) return;
            foreach (var t in targets)
            {
                if (t != null) t.Hit += OnHit;
            }
        }

        void OnHit(ChallengeTarget target)
        {
            hits++;
            if (targets != null && hits >= targets.Length) Finish();
        }

        public override void ResetState()
        {
            base.ResetState();
            hits = 0;
        }
    }
}
