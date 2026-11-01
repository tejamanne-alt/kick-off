using System;
using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    public enum RunPhase { Ready, Running, Paused, Crashed, Results }

    /// <summary>What a run did, counted as it goes. The missions read these when the run ends.</summary>
    [Serializable]
    public struct RunStats
    {
        public int jumps, doubleJumps, slides, nearMisses, smashes, powerUps, coins, obstacles;
        public int stagesReached;       // the furthest stage (1-based) of the furthest day
        public int days;                // days finished (school gates reached)
        public int maxMultiplier;
        public int distance;            // metres
        public int score;
    }

    /// <summary>The outcome of a finished run, for the results screen.</summary>
    public struct RunResult
    {
        public int score, distance, coins;
        public int stage;               // 0-based stage the run ended in
        public int day;                 // 1-based day it ended on
        public int bestScoreBefore, bestDistanceBefore;
        public bool newBestScore, newBestDistance;
        public int coinsEarned;         // what the run added to the wallet
        public int missionCoins;        // of which from missions
        public string reason;           // localization key (lose.*)
        public RunStats stats;
    }

    /// <summary>
    /// Runs a Holiday Run: the countdown, the speed that builds through the day, the score and its
    /// multiplier, the power-ups, crashes and the revive, the day's end at the school gate, and the
    /// result. The HUD reads its properties and events; the world streamer and the atmosphere follow it.
    /// </summary>
    [DefaultExecutionOrder(-40)]
    public class HolidayRunDirector : MonoBehaviour
    {
        public static HolidayRunDirector Current { get; private set; }

        [Header("Scene wiring (set by the editor's builder)")]
        public LevelManager level;
        public KidController kid;
        public BallController ball;
        public EndlessBall endlessBall;
        public CameraFollow2D cameraFollow;
        public RunWorldStreamer streamer;
        public HolidayAtmosphere atmosphere;

        // ---- live state, read by the HUD ----
        public RunPhase Phase { get; private set; }
        public float Distance { get; private set; }
        public int Score { get; private set; }
        public int Coins { get; private set; }
        public int Multiplier { get; private set; }
        /// <summary>0..1 toward the next multiplier step.</summary>
        public float MultiplierProgress { get; private set; }
        public float Speed { get; private set; }
        /// <summary>1-based: which day (lap) this is.</summary>
        public int Day { get; private set; }
        /// <summary>0-based stage the kid is in.</summary>
        public int StageIndex { get; private set; }
        /// <summary>0..1 through the current stage.</summary>
        public float StageProgress { get; private set; }
        public int BestScore { get; private set; }
        public int BestDistance { get; private set; }
        public bool NewBest { get; private set; }
        public float MagnetLeft { get; private set; }
        public float ShieldLeft { get; private set; }
        public float TurboLeft { get; private set; }
        public RunStats Stats { get { return stats; } }
        public RunResult Result { get; private set; }
        public bool CanRevive { get; private set; }
        public int ReviveCost { get; private set; }

        // ---- events ----
        public event Action<RunPhase> PhaseChanged;
        /// <summary>A new stage began (0-based) on this day (1-based).</summary>
        public event Action<int, int> StageChanged;
        /// <summary>The school gate was reached: a new day begins (the number given).</summary>
        public event Action<int> DayStarted;
        /// <summary>A short message for the screen (localized text) and its colour.</summary>
        public event Action<string, Color> Toast;
        public event Action<PowerUpKind> PowerUpCollected;
        public event Action<RunResult> Ended;

        RunStats stats;

        /// <summary>How long a power-up lasts, in seconds.</summary>
        public static float Duration(PowerUpKind kind)
        {
            switch (kind)
            {
                case PowerUpKind.Shield: return 15f;
                case PowerUpKind.Turbo: return 5.5f;
                default: return 9f;
            }
        }

        void Awake() { Current = this; }
        void OnDestroy() { if (Current == this) Current = null; }

        // ---- called by the markers ----
        public void Register(RunSolid solid) { }
        public void Unregister(RunSolid solid) { }
        public void OnSmashed(RunBreakable crate, Vector2 point) { }
        public void CollectPowerUp(PowerUpKind kind, Vector2 position) { }

        // ---- actions (HUD buttons) ----
        public void TogglePause() { }
        /// <summary>Spend <see cref="ReviveCost"/> coins to carry on from just past what was hit.</summary>
        public void Revive() { }
        public void Restart() { }
        public void QuitToMenu() { }
    }
}
