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
        /// <summary>The second star's timing: the leg's pace kept, or on a timed last leg the whole trip at school before the bell.</summary>
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
        /// <summary>The level has a sticker to find.</summary>
        public bool hasSticker;
        /// <summary>The third star's goal: every coin, and the sticker if there is one (Progression/StarRules).</summary>
        public bool collectedAll;

        // Challenges
        public bool isChallenge;
        public int score;
        public string scoreText;

        // Rewards (filled when the result is saved)
        public int newStars;
        public int coinsEarned;

        // The way to school (a story level is one leg of a route; Progression/SchoolTrips)
        /// <summary>A story level on one of the routes (not a challenge or the test track).</summary>
        public bool onRoute;
        /// <summary>The route's last leg: it ends at the school.</summary>
        public bool lastLeg;
        /// <summary>Cozy mode (the bell turned off): no pace, no bell, the trip not judged.</summary>
        public bool cozy;
        /// <summary>This leg's own target in seconds (its bell time), and whether it was kept.</summary>
        public float paceTarget;
        public bool paceMet;
        /// <summary>Every leg before this one was walked in this trip, so <see cref="tripTime"/> counts from the front door.</summary>
        public bool tripContinuous;
        /// <summary>The trip from home so far, this leg included (-1 when it is not continuous).</summary>
        public float tripTime;
        /// <summary>The legs' targets added up from home to the end of this leg: a trip within it is on track for the bell.</summary>
        public float tripTarget;
        /// <summary>The school bell of the whole trip: the sum of the route's legs' targets.</summary>
        public float tripBell;
        /// <summary>The last leg of a continuous trip: the whole trip was judged against the bell.</summary>
        public bool timedTrip;
        /// <summary>A timed trip got to school before the bell.</summary>
        public bool tripOnTime;
        /// <summary>The next story level is still locked (a stage whose trip has never been on time).</summary>
        public bool nextLocked;
    }

    /// <summary>
    /// Runs one level: countdown, the pace and the bell, checkpoints, losing the ball
    /// and respawning, pause, and the finish with a star rating. A story level is one leg of a
    /// route's trip from home to school (Progression/SchoolTrips): every leg has its own target (its
    /// bell time), and only the last leg of a trip walked from home without a break has the school
    /// bell, which rings when the whole trip's time reaches the sum of the legs' targets.
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
        /// <summary>The school bell is running: the last leg of a trip walked from home without a break, outside cozy mode.</summary>
        public bool BellEnabled { get; private set; }
        public bool BellRung { get; private set; }
        /// <summary>This leg's own target is shown instead of the bell (every other leg, outside cozy mode). It never rings.</summary>
        public bool PaceEnabled { get; private set; }
        /// <summary>The school bell turned off in the settings (read at the start and after the pause menu).</summary>
        public bool Cozy { get; private set; }
        /// <summary>The route this story level is a leg of, or null (a challenge, the test track, the Holiday Run).</summary>
        public Route TripRoute { get; private set; }
        /// <summary>The leg's place on its route (0 = it starts at home), or -1.</summary>
        public int LegIndex { get; private set; }
        /// <summary>This leg ends at the school.</summary>
        public bool IsLastLeg { get; private set; }
        /// <summary>Every leg before this one was walked in the trip being walked (always true for a route's first leg).</summary>
        public bool TripContinuous { get; private set; }
        /// <summary>The time the legs before this one took in the trip (0 when it is not continuous).</summary>
        public float TripBefore { get; private set; }
        /// <summary>The school bell of the whole trip in seconds: the sum of the route's legs' targets (this level's own bell off a route).</summary>
        public float TripBell { get; private set; }
        /// <summary>The legs' targets added up from home to the end of this leg.</summary>
        public float TripTarget { get; private set; }
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

        /// <summary>When the school bell rings, in seconds of the whole trip (<see cref="TripBell"/>).</summary>
        public float BellTime { get { return TripBell; } }
        public float BellTimeLeft { get { return Mathf.Max(0f, TripBell - TripBefore - ElapsedTime); } }
        /// <summary>This leg's own target: its bell time.</summary>
        public float PaceTarget { get { return level != null ? level.bellTime : 0f; } }
        public float PaceTimeLeft { get { return Mathf.Max(0f, PaceTarget - ElapsedTime); } }
        /// <summary>Slower than this leg's target so far.</summary>
        public bool PaceBehind { get { return PaceEnabled && ElapsedTime > PaceTarget; } }
        /// <summary>The trip from home so far, this leg's time included (meaningful when <see cref="TripContinuous"/>).</summary>
        public float TripTime { get { return TripBefore + ElapsedTime; } }
        /// <summary>The HUD shows the trip so far: a later leg of a trip walked from home without a break, outside cozy mode.</summary>
        public bool ShowsTrip { get { return TripRoute != null && LegIndex > 0 && TripContinuous && !Cozy && Objective == null; } }

        /// <summary>
        /// Where Next goes: the next leg of this route when it can be played (in chapter 4 the two routes' levels alternate in the
        /// story, and a trip is walked along one route), else the next story level of the catalog.
        /// </summary>
        public LevelDefinition NextLevel
        {
            get
            {
                if (catalog == null) return null;
                if (TripRoute != null && !IsLastLeg && LegIndex >= 0)
                {
                    var leg = catalog.FindById(TripRoute.levels[LegIndex + 1]);
                    if (leg != null && LevelUnlocks.IsUnlocked(catalog, leg)) return leg;
                }
                return catalog.NextAfter(level);
            }
        }

        /// <summary>The first leg of this level's route: where a trip to school starts again from home (null off a route).</summary>
        public LevelDefinition TripStart { get { return TripRoute != null && catalog != null ? catalog.FindById(TripRoute.levels[0]) : null; } }

        public event Action<LevelState> StateChanged;
        public event Action<Checkpoint> CheckpointReached;
        public event Action<string> BallLost;
        public event Action BellRang;
        public event Action<LevelResult> Completed;

        LevelState stateBeforePause;
        Coroutine respawnRoutine;
        readonly List<IResettable> resettables = new List<IResettable>();
        readonly List<IResetAhead> resetAhead = new List<IResetAhead>();
        readonly List<IBallStrander> stranders = new List<IBallStrander>();
        float strandedFor;

        [Tooltip("How long the ball must stay out of the kid's reach before the run goes back to the checkpoint.")]
        public float strandedDelay = 1.2f;

        [Header("Endless mode (Holiday Run)")]
        [Tooltip("The campaign with no destination: the same rules (losing the ball sends you back to the last checkpoint), " +
            "but no bell and no goal, and the checkpoints come and go with the stages that hold them. " +
            "The run only ends when RunOver says so (the Holiday Run's last ball).")]
        public bool endless;
        /// <summary>Endless mode only: the run is over; the reason is a localization key (lose.*).</summary>
        public event Action<string> Crashed;
        /// <summary>Endless mode: asked after each lost ball: true ends the run (Crashed) instead of going back to the checkpoint.</summary>
        public Func<bool> RunOver;
        /// <summary>The countdown waits (at Ready) while this returns true: the Holiday Run's first stages are still loading.</summary>
        public Func<bool> IntroHold;

        /// <summary>
        /// True while the controls tour holds the run where it is (<see cref="Hold"/>): the clock and the world stop, the
        /// countdown waits, the kid takes no input and the run cannot be paused, but the touch controls stay live so the
        /// player can try them.
        /// </summary>
        public bool Held { get; private set; }

        void Awake()
        {
            Current = this;
            Application.targetFrameRate = 60;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            TimeControl.ResetTime();
            checkpoints.RemoveAll(c => c == null);
            checkpoints.Sort((a, b) => a.transform.position.x.CompareTo(b.transform.position.x));

            // Every behaviour on the level's active objects (walking the scene works the same on
            // every Unity 6 version; FindObjectsByType's overloads change between them).
            var behaviours = new List<MonoBehaviour>();
            foreach (var rootObject in gameObject.scene.GetRootGameObjects())
                behaviours.AddRange(rootObject.GetComponentsInChildren<MonoBehaviour>());
            foreach (var behaviour in behaviours)
            {
                var r = behaviour as IResettable;
                if (r != null) resettables.Add(r);
                var ahead = behaviour as IResetAhead;
                if (ahead != null) resetAhead.Add(ahead);
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
            SetUpTrip();
            RefreshTimers();
            FadeAmount = 0f;
            foreach (var r in resettables) r.ResetState();

            ResetCheckpoints();
            PlaceAtCheckpoint();
            IntroTimeLeft = introDuration;
            SetState(LevelState.Intro);
        }

        /// <summary>
        /// Works out at the start of a run which leg of which route this is and what the trip so far is (from the save: a restart after
        /// the bell rang finds the trip forgotten and is untimed). A level on no route keeps its own bell as a trip of one leg.
        /// </summary>
        void SetUpTrip()
        {
            TripRoute = null;
            LegIndex = -1;
            IsLastLeg = false;
            TripContinuous = false;
            TripBefore = 0f;
            TripBell = 0f;
            TripTarget = 0f;
            if (level == null || endless || Objective != null || level.isChallenge) return;

            Route route;
            int leg = RouteTable.LegIndex(level.levelId, out route);
            if (leg < 0)
            {
                IsLastLeg = true;
                TripContinuous = true;
                TripBell = TripTarget = level.bellTime;
                return;
            }
            TripRoute = route;
            LegIndex = leg;
            IsLastLeg = leg == route.levels.Length - 1;
            Func<string, float> bellOf = BellOf;
            TripBell = SchoolTrips.TripBell(route, bellOf);
            TripTarget = SchoolTrips.TargetUpTo(route, leg, bellOf);
            float before;
            TripContinuous = SchoolTrips.TimeBefore(SaveSystem.Data, route, leg, out before);
            TripBefore = TripContinuous ? before : 0f;
        }

        /// <summary>A level's own bell time from the catalog (this level's from its definition), 0 if it is unknown.</summary>
        float BellOf(string levelId)
        {
            if (level != null && level.levelId == levelId) return level.bellTime;
            var def = catalog != null ? catalog.FindById(levelId) : null;
            return def != null ? def.bellTime : 0f;
        }

        /// <summary>
        /// The bell or the pace, from the settings as they are now (the start of a run, and back from the pause menu, where cozy
        /// mode can be switched): the bell only on the last leg of a trip walked from home without a break, the pace on any other leg.
        /// </summary>
        void RefreshTimers()
        {
            Cozy = !GameSettings.BellTimerEnabled;
            bool timing = !Cozy && Objective == null && !endless;
            BellEnabled = timing && IsLastLeg && TripContinuous && TripBell > 0f;
            PaceEnabled = timing && !BellEnabled && TripRoute != null && PaceTarget > 0f;
        }

        /// <summary>Back to the start checkpoint alone: a new run, or (endless) a new day.</summary>
        public void ResetCheckpoints()
        {
            ActiveCheckpoint = null;
            foreach (var cp in checkpoints)
            {
                cp.SetActive(cp.isStart);
                if (cp.isStart && ActiveCheckpoint == null) ActiveCheckpoint = cp;
            }
            if (ActiveCheckpoint == null && checkpoints.Count > 0) ActiveCheckpoint = checkpoints[0];
        }

        /// <summary>A checkpoint came into the world (a Holiday Run stage loaded): it joins the others, in order along the street.</summary>
        public void RegisterCheckpoint(Checkpoint cp)
        {
            if (cp == null || checkpoints.Contains(cp)) return;
            checkpoints.Add(cp);
            checkpoints.Sort((a, b) => a.transform.position.x.CompareTo(b.transform.position.x));
        }

        /// <summary>A checkpoint went (its stage unloaded). If it was the one to go back to, the nearest reached one still standing takes over.</summary>
        public void UnregisterCheckpoint(Checkpoint cp)
        {
            if (!checkpoints.Remove(cp) || ActiveCheckpoint != cp) return;
            Checkpoint best = null;
            foreach (var other in checkpoints)
                if (other != null && other.IsActive && (best == null || other.transform.position.x > best.transform.position.x)) best = other;
            if (best == null && checkpoints.Count > 0) best = checkpoints[0];
            ActiveCheckpoint = best;
        }

        void Update()
        {
            if (Held) return;
            var input = GameInput.Instance;
            if (input != null)
            {
                if (input.PausePressed) TogglePause();
                if (input.ResetPressed) BeginRun();
            }

            switch (State)
            {
                case LevelState.Intro:
                    if (IntroHold != null && IntroHold()) { IntroTimeLeft = introDuration; break; }
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
            if (BellEnabled && !BellRung && TripBefore + ElapsedTime >= TripBell)
            {
                BellRung = true;
                // Late for school: the trip is over, and starting this leg again cannot save it (it is walked again from home).
                if (TripRoute != null)
                {
                    SchoolTrips.MissBell(SaveSystem.Data, TripRoute);
                    SaveSystem.Save();
                }
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
            if (endless && RunOver != null && RunOver())
            {
                // The last ball: the run is over where it stands (the Holiday Run shows its results).
                SetState(LevelState.Complete);
                if (Crashed != null) Crashed(reason);
                return;
            }
            respawnRoutine = StartCoroutine(RespawnRoutine());
        }

        /// <summary>Endless mode: carry on after the run ended (a revive): back at the last checkpoint with the ball, playing.</summary>
        public void ResumeAfterCrash()
        {
            if (!endless || State != LevelState.Complete) return;
            PlaceAtCheckpoint();
            SetState(LevelState.Playing);
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
            ResetAhead();
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

        /// <summary>
        /// Carry on from the checkpoint at <paramref name="index"/> (in order along the level), as
        /// if the kid had just reached it. For tools such as the store screenshot tour.
        /// </summary>
        public void StartFromCheckpoint(int index)
        {
            if (checkpoints.Count == 0) return;
            index = Mathf.Clamp(index, 0, checkpoints.Count - 1);
            for (int i = 0; i < checkpoints.Count; i++) checkpoints[i].SetActive(i <= index);
            ActiveCheckpoint = checkpoints[index];
            PlaceAtCheckpoint();
        }

        /// <summary>How many checkpoints the level has, start included.</summary>
        public int CheckpointCount { get { return checkpoints.Count; } }

        /// <summary>Kid and ball back at the checkpoint to go back to (without losing the ball: a new day, or the first moments of a run).</summary>
        public void PlaceAtActiveCheckpoint() { PlaceAtCheckpoint(); }

        void PlaceAtCheckpoint()
        {
            if (ActiveCheckpoint == null) return;
            kid.ResetTo(ActiveCheckpoint.KidSpawnPosition);
            ball.ResetTo(ActiveCheckpoint.BallSpawnPosition);
            if (cameraFollow != null) cameraFollow.SnapToTarget();
        }

        /// <summary>
        /// Back at a checkpoint after losing the ball (or going back to it): what was moved ahead of it (a crate knocked into
        /// the way) goes back to where the level put it, and rolling pipes are cleared, so the way on is never left blocked.
        /// </summary>
        void ResetAhead()
        {
            if (ActiveCheckpoint == null) return;
            float x = ActiveCheckpoint.transform.position.x;
            foreach (var item in resetAhead)
            {
                var behaviour = item as MonoBehaviour;
                if (behaviour == null) continue;     // gone with an unloaded stage (the Holiday Run)
                item.ResetAhead(x);
            }
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
                bestPerfectStreak = BestPerfectStreak,
                ballsLost = BallsLost,
                coins = CoinsCollected,
                totalCoins = TotalCoins,
                allCoins = CoinsCollected >= TotalCoins,
                perfectTouches = PerfectTouches,
                stickerFound = StickerCollected,
            };
            RecordTrip(ref result);
            // The second star: the leg's pace, or on a timed last leg the whole trip before the bell. The third: every coin and
            // the level's sticker. Each goal is a star of its own (Progression/StarRules).
            result.beforeBell = result.timedTrip ? result.tripOnTime : result.paceMet;
            result.hasSticker = HasSticker;
            result.collectedAll = StarRules.CollectedEverything(CoinsCollected, TotalCoins, HasSticker, StickerCollected);
            result.stars = StarRules.Stars(result.beforeBell, result.collectedAll);
            if (level != null) SaveResult(ref result);
            // After a route's last leg, is the next stage still shut (a trip that has never got to school on time)?
            var next = result.onRoute && result.lastLeg && catalog != null ? catalog.NextAfter(level) : null;
            result.nextLocked = next != null && !LevelUnlocks.StoryOpen(next.levelId, level.levelId, SaveSystem.Data, Cozy);
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

        /// <summary>
        /// Fills in the way to school for a finished story level and records the leg in the save's trip (written with the rest of the
        /// result): the pace, the trip so far and, on the last leg of a trip walked from home without a break, the verdict. Nothing
        /// is recorded in cozy mode or off a route (a challenge, the test track).
        /// </summary>
        void RecordTrip(ref LevelResult r)
        {
            r.onRoute = TripRoute != null;
            r.lastLeg = IsLastLeg;
            r.cozy = Cozy;
            r.paceTarget = PaceTarget;
            r.paceMet = Cozy || PaceTarget <= 0f || ElapsedTime <= PaceTarget;
            r.tripContinuous = TripContinuous && !Cozy;
            r.tripTime = TripContinuous ? TripTime : -1f;
            r.tripTarget = TripTarget;
            r.tripBell = TripBell;
            r.timedTrip = !Cozy && IsLastLeg && TripContinuous && TripBell > 0f;
            r.tripOnTime = r.timedTrip && !BellRung && TripTime <= TripBell;
            if (Cozy || TripRoute == null) return;

            var data = SaveSystem.Data;
            if (r.timedTrip && BellRung)
            {
                // The trip was forgotten when the bell rang.
                SchoolTrips.MissBell(data, TripRoute);
                return;
            }
            float tripTime;
            var verdict = SchoolTrips.RecordLeg(data, TripRoute, LegIndex, ElapsedTime, TripBell, out tripTime);
            if (r.timedTrip) r.tripOnTime = verdict == TripVerdict.OnTime;
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
            if (Held) return;
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
            RefreshTimers();
            SetState(stateBeforePause);
        }

        public void LoadNextLevel()
        {
            LevelDefinition next = NextLevel;
            if (next == null) QuitToMap();
            else LoadLevel(next);
        }

        /// <summary>Walk the trip to school again from home: this route's first leg.</summary>
        public void LoadTripStart()
        {
            LevelDefinition start = TripStart;
            if (start == null) QuitToMap();
            else LoadLevel(start);
        }

        /// <summary>Back to the chapter map, showing this level's chapter.</summary>
        public void QuitToMap()
        {
            FrontEnd.FrontEndController.Open(FrontEnd.FrontEndScreenId.Map, level != null ? level.chapter : 0);
        }

        public static void LoadLevel(LevelDefinition def)
        {
            TimeControl.ResetTime();
            // The level's scene for the add-on chosen in Settings (Progression/AddOns: California...).
            SceneManager.LoadScene(Progression.AddOns.SceneFor(def.sceneName));
        }

        void SetState(LevelState next)
        {
            State = next;
            ApplyHold();
            if (StateChanged != null) StateChanged(next);
        }

        /// <summary>
        /// Holds the run where it is, or lets it go on (the controls tour, a challenge's guide; see <see cref="Held"/>). Holds are
        /// counted: the run goes on when every one that held it has let go.
        /// </summary>
        public void Hold(bool held)
        {
            holds = Mathf.Max(0, holds + (held ? 1 : -1));
            if (Held == holds > 0) return;
            Held = holds > 0;
            ApplyHold();
        }

        int holds;

        /// <summary>Time, the kid's input and the touch controls for the state and the hold.</summary>
        void ApplyHold()
        {
            TimeControl.SetPaused(State == LevelState.Paused || Held);
            bool playing = State == LevelState.Playing && !Held;
            kid.InputEnabled = playing;
            if (GameInput.Instance != null) GameInput.Instance.Blocked = !(playing || Held);
        }
    }
}
