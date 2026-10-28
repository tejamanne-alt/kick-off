using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>Keepy-uppy: the best juggling run before time is up. Hitting the 3-star mark ends it early.</summary>
    public class JuggleChallenge : ChallengeObjective
    {
        int best;

        public override int Score { get { return best; } }

        public override string StatusText
        {
            get
            {
                var level = LevelManager.Current;
                int now = level != null ? level.ball.JuggleCount : 0;
                return "Juggles " + now + "   Best " + best + "   " + Mathf.CeilToInt(TimeLeft) + "s";
            }
        }

        void OnEnable()
        {
            var level = LevelManager.Current;
            if (level == null) return;
            level.ball.Juggled += OnJuggled;
        }

        void OnDisable()
        {
            var level = LevelManager.Current;
            if (level == null) return;
            level.ball.Juggled -= OnJuggled;
        }

        void OnJuggled(int count)
        {
            if (count > best) best = count;
            if (starThresholds.Length >= 3 && best >= starThresholds[2]) Finish();
        }

        public override void ResetState()
        {
            base.ResetState();
            best = 0;
        }
    }
}
