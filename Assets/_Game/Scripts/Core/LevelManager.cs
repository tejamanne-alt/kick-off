using System;
using System.Collections;
using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Challenges;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Levels;
using DribbleToSchool.Pickups;
using DribbleToSchool.Player;
using DribbleToSchool.Progression;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Core
{
    public enum LevelState { Intro, Playing, Respawning, Paused, Complete }

    /// <summary>Outcome of a finished run.</summary>
    public struct LevelResult
    {
        public float time;
        public bool beforeBell;
        public int bestPerfectStreak;
        public int ballsLost;
        public int stars;
        public int coins;
        public int totalCoins;
        public bool allCoins;
        public int perfectTouches;
        public bool stickerFound;
        public bool stickerIsNew;

        // Challenges
        public bool isChallenge;
        public int score;
        public string scoreText;

        // Rewards (filled when the result is saved)
        public int newStars;
        public int coinsEarned;
    }

    /// <summary>
    /// Runs one level: countdown, the bell timer, checkpoints, losing the ball
    /// and respawning, pause, and the finish with a star rating.
    /// </summary>
    [DefaultExecutionOrder(-50)]
    public class LevelManager : MonoBehaviour
    {
        public static LevelManager Current { get; private set; }

        [Header("Level")]
        public LevelDefinition level;
        public LevelCatalog catalog;

        [Header("Scene References")]
        public KidController kid;
        public BallController ball;
        public CameraFollow2D cameraFollow;
        [Tooltip("Respawn points. Sorted by x at start; one should be marked as the start.")]
        public List<Checkpoint> checkpoints = new List<Checkpoint>();

        [Header("Rules")]
        [Tooltip("Falling below this height loses the ball.")]
        public float killY = -6f;
        [Tooltip("Ball this far behind the kid counts as lost (0 = never; the kid can walk back for it).")]
        public float maxBallBehindDistance = 0f;
        [Tooltip("Where the level starts. A ball kicked back past this line is lost.")]
        public float startBoundaryX = float.NegativeInfinity;
        [Tooltip("Wall at the start that stops the kid but lets the ball through.")]
        public Collider2D startWall;
        [Tooltip("A checkpoint only activates if the ball is no further behind the kid than this.")]
        public float checkpointBallTolerance = 3f;
        public float introDuration = 1.1f;
        public float respawnFadeDuration = 0.35f;

        public LevelState State { get; private set; }
        public float ElapsedTime { get; private set; }
        public bool BellEnabled { get; private set; }
        public bool BellRung { get; private set; }
        public int BallsLost { get; private set; }
        public int BestPerfectStreak { get; private set; }
        public int PerfectTouches { get; private set; }
        public int Juggles { get; private set; }
        public int CoinsCollected { get; private set; }
        public int TotalCoins { get; private set; }
        public bool StickerCollected { get; private set; }
        public bool HasSticker { get; private set; }
        /// <summary>The ball-skill challenge in this level, if any (replaces the bell and the gate).</summary>
        public ChallengeObjective Objective { get; private set; }
        public LevelResult Result { get; private set; }
        public Checkpoint ActiveCheckpoint { get; private set; }
        /// <summary>0 = clear, 1 = fully faded to black. Driven during respawn.</summary>
        public float FadeAmount { get; private set; }
        public float IntroTimeLeft { get; private set; }

        public float BellTime { get { return level != null ? level.bellTime : 0f; } }
        public float BellTimeLeft { get { return Mathf.Max(0f, BellTime - ElapsedTime); } }
        public LevelDefinition NextLevel { get { return catalog != null ? catalog.NextAfter(level) : null; } }

        public event Action<LevelState> StateChanged;
        public event Action<Checkpoint> CheckpointReached;
        public event Action<string> BallLost;
        public event Action BellRang;
        public event Action<LevelResult> Completed;

        LevelState stateBeforePause;
        Coroutine respawnRoutine;
        readonly List<IResettable> resettables = new List<IResettable>();
        readonly List<IBallStrander> stranders = new List<IBallStrander>();
        float strandedFor;

        [Tooltip("How long the ball must stay out of the kid's reach before the run goes back to the checkpoint.")]
        public float strandedDelay = 1.2f;

        void Awake()
        {
            Current = this;
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            TimeControl.ResetTime();
            checkpoints.RemoveAll(c => c == null);
            checkpoints.Sort((a, b) => a.transform.position.x.CompareTo(b.transform.position.x));

            foreach (var behaviour in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
            {
                var r = behaviour as IResettable;
                if (r != null) resettables.Add(r);
                var strander = behaviour as IBallStrander;
                if (strander != null) stranders.Add(strander);
                if (behaviour is Coin) TotalCoins += ((Coin)behaviour).value;
                if (behaviour is Sticker) HasSticker = true;
                if (behaviour is ChallengeObjective) Objective = (ChallengeObjective)behaviour;
            }
        }

        void OnDestroy()
        {
            if (Current == this) Current = null;
            TimeControl.ResetTime();
        }

        void OnEnable()
        {
            ball.PerfectTouch += OnPerfectTouch;
            ball.Juggled += OnJuggled;
        }

        void OnDisable()
        {
            ball.PerfectTouch -= OnPerfectTouch;
            ball.Juggled -= OnJuggled;
        }

        void OnJuggled(int count)
        {
            Juggles++;
        }

        public void CollectCoin(Coin coin)
        {
            CoinsCollected += coin.value;
        }

        public void CollectSticker()
        {
            StickerCollected = true;
        }

        void Start()
        {
            if (startWall != null)
            {
                foreach (var c in ball.GetComponentsInChildren<Collider2D>())
                    Physics2D.IgnoreCollision(c, startWall, true);
            }
            BeginRun();
        }

        void OnPerfectTouch(int streak)
        {
            PerfectTouches++;
            if (streak > BestPerfectStreak) BestPerfectStreak = streak;
        }

        /// <summary>Start (or restart) the level from the very beginning.</summary>
        public void BeginRun()
        {
            if (respawnRoutine != null) StopCoroutine(respawnRoutine);
            respawnRoutine = null;
            TimeControl.ResetTime();

            ElapsedTime = 0f;
            BallsLost = 0;
            BestPerfectStreak = 0;
            PerfectTouches = 0;
            Juggles = 0;
            CoinsCollected = 0;
            StickerCollected = false;
            BellRung = false;
            BellEnabled = GameSettings.BellTimerEnabled && BellTime > 0f && Objective == null;
            FadeAmount = 0f;
            foreach (var r in resettables) r.ResetState();

            ActiveCheckpoint = null;
            foreach (var cp in checkpoints)
            {
                cp.SetActive(cp.isStart);
                if (cp.isStart && ActiveCheckpoint == null) ActiveCheckpoint = cp;
            }
            if (ActiveCheckpoint == null && checkpoints.Count > 0) ActiveCheckpoint = checkpoints[0];

            PlaceAtCheckpoint();
            IntroTimeLeft = introDuration;
            SetState(LevelState.Intro);
        }

        void Update()
        {
            var input = GameInput.Instance;
            if (input != null)
            {
                if (input.PausePressed) TogglePause();
                if (input.ResetPressed) BeginRun();
            }

            switch (State)
            {
                case LevelState.Intro:
                    IntroTimeLeft -= Time.unscaledDeltaTime;
                    if (IntroTimeLeft <= 0f)
                    {
                        SetState(LevelState.Playing);
                        GameEvents.Raise(GameEventType.LevelStart, kid.transform.position);
                    }
                    break;

                case LevelState.Playing:
                    Tick(Time.deltaTime);
                    UpdateCheckpoints();
                    CheckBallLost();
                    break;

                case LevelState.Respawning:
                    Tick(Time.deltaTime);
                    break;
            }
        }

        void Tick(float dt)
        {
            ElapsedTime += dt;
            if (BellEnabled && !BellRung && ElapsedTime >= BellTime)
            {
                BellRung = true;
                GameEvents.Raise(GameEventType.Bell, kid.transform.position);
                if (BellRang != null) BellRang();
            }
        }

        void UpdateCheckpoints()
        {
            float kidX = kid.transform.position.x;
            float ballX = ball.transform.position.x;
            foreach (var cp in checkpoints)
            {
                if (cp.IsActive) continue;
                float x = cp.transform.position.x;
                if (kidX >= x && ballX >= x - checkpointBallTolerance)
                {
                    cp.SetActive(true);
                    GameEvents.Raise(GameEventType.Checkpoint, cp.transform.position);
                    if (ActiveCheckpoint == null || x > ActiveCheckpoint.transform.position.x)
                        ActiveCheckpoint = cp;
                    if (CheckpointReached != null) CheckpointReached(cp);
                }
            }
        }

        void CheckBallLost()
        {
            if (ball.transform.position.y < killY || kid.transform.position.y < killY)
                LoseBall("lose.fell");
            else if (ball.transform.position.x < startBoundaryX)
                LoseBall("lose.offStart");
            else if (maxBallBehindDistance > 0f && kid.transform.position.x - ball.transform.position.x > maxBallBehindDistance)
                LoseBall("lose.behind");
            else if (BallStranded())
                LoseBall("lose.unreachable");
        }

        /// <summary>True once the ball has been somewhere the kid can't reach (over a closed
        /// gate, on a ledge too high to climb) for <see cref="strandedDelay"/> seconds.</summary>
        bool BallStranded()
        {
            Vector2 b = ball.transform.position, k = kid.transform.position;
            bool now = false;
            foreach (var s in stranders)
            {
                if (s != null && s.Strands(b, k)) { now = true; break; }
            }
            strandedFor = now ? strandedFor + Time.deltaTime : 0f;
            if (strandedFor < strandedDelay) return false;
            strandedFor = 0f;
            return true;
        }

        /// <summary>Lose the ball and respawn at the last checkpoint. Ignored unless playing. <paramref name="reason"/> is a localization key.</summary>
        public void LoseBall(string reason)
        {
            if (State != LevelState.Playing) return;
            BallsLost++;
            GameEvents.Raise(GameEventType.BallLost, ball.transform.position);
            if (BallLost != null) BallLost(reason);
            respawnRoutine = StartCoroutine(RespawnRoutine());
        }

        /// <summary>Manually go back to the last checkpoint (e.g. ball stuck). Counts as a lost ball.</summary>
        public void RespawnAtCheckpoint()
        {
            LoseBall("lose.checkpoint");
        }

        IEnumerator RespawnRoutine()
        {
            SetState(LevelState.Respawning);
            yield return Fade(0f, 1f);
            PlaceAtCheckpoint();
            GameEvents.Raise(GameEventType.Respawn, kid.transform.position);
            yield return Fade(1f, 0f);
            respawnRoutine = null;
            SetState(LevelState.Playing);
        }

        IEnumerator Fade(float from, float to)
        {
            float t = 0f;
            while (t < respawnFadeDuration)
            {
                // Unscaled so a slow-motion aim or pause can't stretch the fade.
                if (!TimeControl.IsPaused) t += Time.unscaledDeltaTime;
                FadeAmount = Mathf.Lerp(from, to, t / respawnFadeDuration);
                yield return null;
            }
            FadeAmount = to;
        }

        void PlaceAtCheckpoint()
        {
            if (ActiveCheckpoint == null) return;
            kid.ResetTo(ActiveCheckpoint.KidSpawnPosition);
            ball.ResetTo(ActiveCheckpoint.BallSpawnPosition);
            if (cameraFollow != null) cameraFollow.SnapToTarget();
        }

        public void ReachGoal()
        {
            if (State != LevelState.Playing && State != LevelState.Respawning) return;
            if (respawnRoutine != null)
            {
                StopCoroutine(respawnRoutine);
                respawnRoutine = null;
                FadeAmount = 0f;
            }
            if (Objective != null)
            {
                // A slalom finishes at the gate; the objective decides the result.
                Objective.OnGoalReached();
                return;
            }

            var result = new LevelResult
            {
                time = ElapsedTime,
                beforeBell = !BellEnabled || BellTime <= 0f || ElapsedTime <= BellTime,
                bestPerfectStreak = BestPerfectStreak,
                ballsLost = BallsLost,
                coins = CoinsCollected,
                totalCoins = TotalCoins,
                allCoins = CoinsCollected >= TotalCoins,
                perfectTouches = PerfectTouches,
                stickerFound = StickerCollected,
            };
            int target = level != null ? level.perfectStreakTarget : 0;
            bool thirdStar = result.beforeBell && BestPerfectStreak >= target && result.allCoins;
            result.stars = 1 + (result.beforeBell ? 1 : 0) + (thirdStar ? 1 : 0);
            if (level != null) SaveResult(ref result);
            Result = result;

            SetState(LevelState.Complete);
            GameEvents.Raise(GameEventType.Goal, ball.transform.position, result.stars / 3f);
            if (Completed != null) Completed(result);
        }

        /// <summary>Called by a challenge when it ends (time up, target reached, or finish line).</summary>
        public void CompleteChallenge(ChallengeObjective objective)
        {
            if (State == LevelState.Complete) return;
            if (respawnRoutine != null)
            {
                StopCoroutine(respawnRoutine);
                respawnRoutine = null;
                FadeAmount = 0f;
            }

            int score = objective.Score;
            var result = new LevelResult
            {
                isChallenge = true,
                score = score,
                scoreText = objective.FormatScore(score),
                time = ElapsedTime,
                beforeBell = true,
                bestPerfectStreak = BestPerfectStreak,
                ballsLost = BallsLost,
                coins = CoinsCollected,
                totalCoins = TotalCoins,
                allCoins = CoinsCollected >= TotalCoins,
                perfectTouches = PerfectTouches,
                stickerFound = StickerCollected,
                stars = objective.StarsFor(score),
            };
            if (level != null && result.stars > 0) SaveResult(ref result);
            Result = result;

            SetState(LevelState.Complete);
            GameEvents.Raise(GameEventType.Goal, ball.transform.position, result.stars / 3f);
            if (Completed != null) Completed(result);
        }

        /// <summary>Persist the run and work out the coin rewards.</summary>
        void SaveResult(ref LevelResult result)
        {
            result.newStars = SaveSystem.RecordLevel(level.levelId, result.stars, result.time, result.coins, result.allCoins);
            result.stickerIsNew = result.stickerFound && SaveSystem.AddSticker(level.levelId);

            result.coinsEarned = result.coins
                + result.perfectTouches * Rewards.PerPerfectTouch
                + result.newStars * Rewards.PerNewStar
                + (result.stickerIsNew ? Rewards.NewSticker : 0)
                + (result.allCoins && result.totalCoins > 0 ? Rewards.AllCoinsBonus : 0);
            SaveSystem.AddCoins(result.coinsEarned);

            var data = SaveSystem.Data;
            data.totalPerfectTouches += result.perfectTouches;
            data.totalJuggles += Juggles;
            SaveSystem.Save();
        }

        public void TogglePause()
        {
            if (State == LevelState.Paused) Resume();
            else if (State != LevelState.Complete) Pause();
        }

        public void Pause()
        {
            if (State == LevelState.Paused || State == LevelState.Complete) return;
            stateBeforePause = State;
            SetState(LevelState.Paused);
        }

        public void Resume()
        {
            if (State != LevelState.Paused) return;
            BellEnabled = GameSettings.BellTimerEnabled && BellTime > 0f;
            SetState(stateBeforePause);
        }

        public void LoadNextLevel()
        {
            LevelDefinition next = NextLevel;
            if (next == null) QuitToMap();
            else LoadLevel(next);
        }

        /// <summary>Back to the chapter map, showing this level's chapter.</summary>
        public void QuitToMap()
        {
            FrontEnd.FrontEndController.Open(FrontEnd.FrontEndScreenId.Map, level != null ? level.chapter : 0);
        }

        public static void LoadLevel(LevelDefinition def)
        {
            TimeControl.ResetTime();
            SceneManager.LoadScene(def.sceneName);
        }

        void SetState(LevelState next)
        {
            State = next;
            TimeControl.SetPaused(next == LevelState.Paused);

            bool playing = next == LevelState.Playing;
            kid.InputEnabled = playing;
            if (GameInput.Instance != null) GameInput.Instance.Blocked = !playing;

            if (StateChanged != null) StateChanged(next);
        }
    }
}
