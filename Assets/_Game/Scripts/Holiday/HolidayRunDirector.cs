using System;
using System.Collections;
using System.Collections.Generic;
using DribbleToSchool.Ball;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Analytics;
using DribbleToSchool.Core;
using DribbleToSchool.FrontEnd;
using DribbleToSchool.Localization;
using DribbleToSchool.Pickups;
using DribbleToSchool.Player;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    public enum RunPhase { Ready, Running, Paused, Crashed, Results }

    /// <summary>What a run did, counted as it goes. The missions read these when the run ends.</summary>
    [Serializable]
    public struct RunStats
    {
        public int jumps, doubleJumps, slides, nearMisses, smashes, powerUps, coins, obstacles;
        /// <summary>Stages passed over the whole run (23 to a day): "reach stage 30".</summary>
        public int stagesReached;
        /// <summary>Days finished (school gates reached).</summary>
        public int days;
        public int maxMultiplier;
        /// <summary>Metres run.</summary>
        public int distance;
        public int score;
    }

    /// <summary>The outcome of a finished run, for the results screen.</summary>
    public struct RunResult
    {
        public int score, distance, coins;
        /// <summary>The 0-based stage the run ended in.</summary>
        public int stage;
        /// <summary>The 1-based day it ended on.</summary>
        public int day;
        public int bestScoreBefore, bestDistanceBefore;
        public bool newBestScore, newBestDistance;
        /// <summary>A localization key (lose.*).</summary>
        public string reason;
        public RunStats stats;
    }

    /// <summary>
    /// Runs a Holiday Run: the countdown, the pace that builds through each day, the score and its
    /// multiplier, the power-ups, crashes and the revive, the day's end at the school gate and the
    /// result. The HUD reads its properties and events; the world streamer and the atmosphere follow
    /// it. Everything the story's hazards need (the hosting level) lives in the LevelManager beside it.
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

        [Header("Pace (metres per second)")]
        [Tooltip("Speed at the start of the first day, and at its school gate.")]
        public float firstDaySpeed = 6.5f;
        public float firstDayTopSpeed = 11f;
        [Tooltip("Each further day starts and ends this much faster, up to the caps.")]
        public float perDayGain = 1f;
        public float startSpeedCap = 10f;
        public float topSpeedCap = 14f;
        [Tooltip("How quickly the pace follows its target (m/s per second).")]
        public float acceleration = 4f;
        public float turboFactor = 1.4f;

        [Header("Score")]
        public int pointsPerCoin = 10;
        public int nearMissPoints = 40;
        public int dayPoints = 500;
        [Tooltip("Obstacles cleared in a row for each step of the multiplier.")]
        public int streakPerStep = 6;
        public int maxMultiplier = 5;
        [Tooltip("Passing an obstacle closer than this (and not touching it) is a near miss.")]
        public float nearMissGap = 0.3f;
        public int dayBonusCoins = 40;

        [Header("Pick-ups and revive")]
        public float magnetRadius = 6f;
        public int firstReviveCost = 40;
        public int maxRevives = 3;

        // ---- live state, read by the HUD ----
        public RunPhase Phase { get; private set; }
        /// <summary>Metres run so far.</summary>
        public float Distance { get; private set; }
        public int Score { get { return (int)scoreExact + bonusScore; } }
        public int Coins { get { return (level != null ? level.CoinsCollected : 0) + bonusCoins; } }
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
        /// <summary>This run is already past the best score (so far).</summary>
        public bool NewBest { get { return Score > BestScore; } }
        public float MagnetLeft { get; private set; }
        public float ShieldLeft { get; private set; }
        public float TurboLeft { get; private set; }
        public RunStats Stats { get { var s = stats; s.coins = Coins; s.distance = (int)Distance; s.score = Score; return s; } }
        public RunResult Result { get; private set; }
        public bool CanRevive { get { return revivesUsed < maxRevives; } }
        public int ReviveCost { get { return firstReviveCost * (revivesUsed + 1); } }
        /// <summary>0..1 white fade drawn over the screen as the day changes.</summary>
        public float Fade { get; private set; }
        /// <summary>While Ready: seconds of the countdown left (0 once going).</summary>
        public float IntroTimeLeft { get { return level != null && level.State == LevelState.Intro ? level.IntroTimeLeft : 0f; } }
        /// <summary>The world is still loading, so the countdown waits.</summary>
        public bool Loading { get { return streamer != null && !streamer.IsReady; } }

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

        static readonly Color Gold = new Color(1f, 0.82f, 0.2f);
        static readonly Color Mint = new Color(0.55f, 1f, 0.7f);

        RunStats stats;
        float scoreExact;
        int bonusScore, bonusCoins, lastLevelCoins;
        int streak, revivesUsed, lastMultiplier;
        float lastX;
        float crashTime, crashX, invulnerableUntil;
        string crashReason;
        RunSolid lastHit;
        bool committed, dayChanging;
        CapsuleCollider2D kidCollider;
        readonly List<RunSolid> solids = new List<RunSolid>();
        readonly List<Coin> pulled = new List<Coin>();
        readonly Collider2D[] hits = new Collider2D[48];
        ContactFilter2D triggerFilter;
        float magnetScan;
        SpriteRenderer shieldAura, turboAura, magnetAura;

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

        void Awake()
        {
            Current = this;
            triggerFilter = new ContactFilter2D();
            triggerFilter.useTriggers = true;
        }

        void OnDestroy()
        {
            if (Current == this) Current = null;
            if (level != null)
            {
                level.StateChanged -= OnLevelState;
                level.Crashed -= OnCrashed;
                level.IntroHold = null;
            }
            if (kid != null)
            {
                kid.Collided -= OnKidCollided;
                kid.Jumped -= OnJumped;
                kid.DoubleJumped -= OnDoubleJumped;
                kid.Slid -= OnSlid;
            }
            Commit();
        }

        void OnApplicationPause(bool paused)
        {
            if (paused && Phase == RunPhase.Results) Commit();
        }

        void Start()
        {
            if (level == null || kid == null)
            {
                Debug.LogError("[Holiday Run] The director needs its level and kid: rebuild the Holiday Run (Kick Off > Rebuild Holiday Run).");
                enabled = false;
                return;
            }
            kidCollider = kid.GetComponent<CapsuleCollider2D>();
            level.StateChanged += OnLevelState;
            level.Crashed += OnCrashed;
            level.IntroHold = () => Loading;
            kid.Collided += OnKidCollided;
            kid.Jumped += OnJumped;
            kid.DoubleJumped += OnDoubleJumped;
            kid.Slid += OnSlid;

            var data = SaveSystem.Data;
            BestScore = data.holidayBestScore;
            BestDistance = data.holidayBestDistance;
            ResetRun();
            SetPhase(level.State == LevelState.Playing ? RunPhase.Running : RunPhase.Ready);
        }

        // ================================================================ run state

        /// <summary>Everything back to the start of day 1 (the level itself is reset by LevelManager.BeginRun).</summary>
        void ResetRun()
        {
            StopAllCoroutines();
            dayChanging = false;
            Fade = 0f;
            stats = new RunStats();
            scoreExact = 0f;
            bonusScore = 0;
            bonusCoins = 0;
            lastLevelCoins = 0;
            streak = 0;
            revivesUsed = 0;
            Multiplier = lastMultiplier = 1;
            MultiplierProgress = 0f;
            Distance = 0f;
            Day = 1;
            StageIndex = 0;
            StageProgress = 0f;
            MagnetLeft = ShieldLeft = TurboLeft = 0f;
            invulnerableUntil = 0f;
            committed = false;
            lastHit = null;
            pulled.Clear();
            solids.Clear();
            Speed = DayStartSpeed(1);
            kid.autoRunSpeed = Speed;
            lastX = kid.transform.position.x;
            stats.maxMultiplier = 1;
            stats.stagesReached = 1;
            if (streamer != null)
            {
                streamer.StartDay(0);
                FreezeKid(true);
            }
        }

        /// <summary>Hold the kid and ball still (no physics) while the ground they stand on is being loaded.</summary>
        void FreezeKid(bool freeze)
        {
            if (kid == null || kid.Body == null) return;
            if (freeze) kid.Body.linearVelocity = Vector2.zero;
            kid.Body.simulated = !freeze;
        }

        void PlaceAtStart()
        {
            kid.ResetTo(new Vector2(HolidayStages.SpawnX, 0.6f));
            if (endlessBall != null) endlessBall.ResetAt(kid.transform.position);
            lastX = kid.transform.position.x;
            if (cameraFollow != null) cameraFollow.SnapToTarget();
        }

        float DayStartSpeed(int day) { return Mathf.Min(startSpeedCap, firstDaySpeed + perDayGain * (day - 1)); }
        float DayTopSpeed(int day) { return Mathf.Min(topSpeedCap, firstDayTopSpeed + perDayGain * (day - 1)); }

        void SetPhase(RunPhase phase)
        {
            if (Phase == phase) return;
            Phase = phase;
            if (PhaseChanged != null) PhaseChanged(phase);
        }

        void OnLevelState(LevelState state)
        {
            switch (state)
            {
                case LevelState.Intro:
                    // The level was restarted (Restart, or the R key): everything starts over with it.
                    if (Phase != RunPhase.Ready)
                    {
                        Commit();
                        TimeControl.ResetTime();
                        ResetRun();
                        if (endlessBall != null) endlessBall.ResetAt(kid.transform.position);
                        if (cameraFollow != null) cameraFollow.SnapToTarget();
                    }
                    SetPhase(RunPhase.Ready);
                    break;
                case LevelState.Playing:
                    if (Phase == RunPhase.Ready)
                    {
                        lastX = kid.transform.position.x;
                        SetPhase(RunPhase.Running);
                        // GO: the first stage's banner.
                        if (StageChanged != null) StageChanged(StageIndex, Day);
                        AnalyticsService.Track("holiday_run_start", "character", GameSettings.Character);
                    }
                    else
                    {
                        SetPhase(RunPhase.Running);
                    }
                    break;
                case LevelState.Paused:
                    SetPhase(RunPhase.Paused);
                    break;
            }
        }

        // ================================================================ the run

        void Update()
        {
            if (Phase == RunPhase.Crashed)
            {
                if (Time.unscaledTime - crashTime > 1f) EnterResults();
                return;
            }
            if (Phase == RunPhase.Ready)
            {
                kid.autoRunSpeed = Speed;
                // The kid has nothing to stand on until the first stage has loaded: hold them still, and put
                // them back on their feet at the start once it has.
                if (Loading) FreezeKid(true);
                else if (!kid.Body.simulated) { FreezeKid(false); PlaceAtStart(); }
                return;
            }
            if (Phase != RunPhase.Running) return;

            float dt = Time.deltaTime;
            float x = kid.transform.position.x;

            // Distance, and the points that come with it.
            float dx = x - lastX;
            lastX = x;
            if (dx > 0f && dx < 4f)
            {
                Distance += dx;
                scoreExact += dx * Multiplier * (TurboLeft > 0f ? 2f : 1f);
            }

            UpdateSpeed(dt, x);
            UpdateStage(x);
            UpdateTimers(dt);
            UpdateSolids(x);
            UpdateCoins();
            UpdateMultiplier();
            if (MagnetLeft > 0f) MagnetStep(dt);

            if (x >= HolidayStages.GateX && !dayChanging) StartCoroutine(DayRoutine());
        }

        void LateUpdate()
        {
            UpdateAuras();
        }

        void UpdateSpeed(float dt, float x)
        {
            float t = Mathf.SmoothStep(0f, 1f, HolidayStages.LapProgress(x));
            float target = Mathf.Lerp(DayStartSpeed(Day), DayTopSpeed(Day), t);
            if (TurboLeft > 0f) target *= turboFactor;
            Speed = Mathf.MoveTowards(Speed, target, acceleration * dt * (TurboLeft > 0f ? 3f : 1f));
            kid.autoRunSpeed = Speed;
        }

        void UpdateStage(float x)
        {
            int stage = HolidayStages.StageAt(x);
            StageProgress = Mathf.Clamp01((x - HolidayStages.StartOf(stage)) / HolidayStages.StageLength);
            if (stage == StageIndex) return;
            StageIndex = stage;
            stats.stagesReached = Mathf.Max(stats.stagesReached, (Day - 1) * HolidayStages.Count + stage + 1);
            if (StageChanged != null) StageChanged(stage, Day);
        }

        void UpdateTimers(float dt)
        {
            MagnetLeft = Mathf.Max(0f, MagnetLeft - dt);
            ShieldLeft = Mathf.Max(0f, ShieldLeft - dt);
            TurboLeft = Mathf.Max(0f, TurboLeft - dt);
        }

        /// <summary>Obstacles passed count toward the combo; passing one close without touching it is a near miss.</summary>
        void UpdateSolids(float x)
        {
            for (int i = solids.Count - 1; i >= 0; i--)
            {
                var solid = solids[i];
                if (solid == null) { solids.RemoveAt(i); continue; }
                if (solid.Cleared) continue;
                float left = solid.LeftX, right = solid.RightX;
                if (x > left - 1.5f && x < right + 1.5f && kidCollider != null)
                {
                    foreach (var c in solid.Colliders)
                    {
                        if (c == null || !c.enabled) continue;
                        var d = kidCollider.Distance(c);
                        solid.Closest = Mathf.Min(solid.Closest, d.distance);
                    }
                }
                if (x > right + 0.4f)
                {
                    solid.Cleared = true;
                    streak++;
                    stats.obstacles++;
                    if (solid.deadly && solid.Closest > 0.02f && solid.Closest < nearMissGap)
                    {
                        stats.nearMisses++;
                        Award(nearMissPoints, "holiday.nearMiss", Gold);
                    }
                }
            }
        }

        void UpdateCoins()
        {
            int now = level.CoinsCollected;
            if (now > lastLevelCoins)
            {
                int gained = now - lastLevelCoins;
                scoreExact += gained * pointsPerCoin * Multiplier * (TurboLeft > 0f ? 2 : 1);
                lastLevelCoins = now;
            }
        }

        void UpdateMultiplier()
        {
            int steps = streak / Mathf.Max(1, streakPerStep);
            Multiplier = Mathf.Clamp(1 + steps, 1, maxMultiplier);
            MultiplierProgress = Multiplier >= maxMultiplier ? 1f : (streak % Mathf.Max(1, streakPerStep)) / (float)Mathf.Max(1, streakPerStep);
            stats.maxMultiplier = Mathf.Max(stats.maxMultiplier, Multiplier);
            if (Multiplier > lastMultiplier && Toast != null) Toast(Loc.F("holiday.multiplier", Multiplier), Gold);
            lastMultiplier = Multiplier;
        }

        /// <summary>Bonus points (times the multiplier) with a message; <paramref name="key"/> is formatted with the points.</summary>
        void Award(int points, string key, Color color)
        {
            int gained = points * Multiplier;
            bonusScore += gained;
            if (Toast != null) Toast(Loc.F(key, gained), color);
        }

        // ================================================================ magnet

        void MagnetStep(float dt)
        {
            magnetScan -= dt;
            if (magnetScan <= 0f)
            {
                magnetScan = 0.1f;
                int n = Physics2D.OverlapCircle(kid.transform.position, magnetRadius, triggerFilter, hits);
                for (int i = 0; i < n; i++)
                {
                    var coin = hits[i].GetComponent<Coin>();
                    if (coin != null && !coin.Collected && !pulled.Contains(coin)) pulled.Add(coin);
                }
            }
            Vector3 target = kid.transform.position + Vector3.up * 0.15f;
            for (int i = pulled.Count - 1; i >= 0; i--)
            {
                var coin = pulled[i];
                if (coin == null || coin.Collected) { pulled.RemoveAt(i); continue; }
                coin.transform.position = Vector3.MoveTowards(coin.transform.position, target, (Speed + 9f) * dt);
            }
        }

        // ================================================================ markers call these

        public void Register(RunSolid solid)
        {
            if (solid != null && !solids.Contains(solid)) solids.Add(solid);
        }

        public void Unregister(RunSolid solid)
        {
            solids.Remove(solid);
        }

        /// <summary>A crate or target was smashed (by the ball, the shield or the turbo).</summary>
        public void OnSmashed(RunBreakable crate, Vector2 point)
        {
            stats.smashes++;
            streak++;
            bonusCoins += crate.coins;
            int gained = crate.coins * pointsPerCoin * Multiplier;
            bonusScore += gained;
            if (Toast != null) Toast(Loc.F("holiday.smash", gained), Gold);
        }

        public void CollectPowerUp(PowerUpKind kind, Vector2 position)
        {
            float seconds = Duration(kind);
            switch (kind)
            {
                case PowerUpKind.Magnet: MagnetLeft = seconds; break;
                case PowerUpKind.Shield: ShieldLeft = seconds; break;
                default: TurboLeft = seconds; break;
            }
            stats.powerUps++;
            GameEvents.Raise(GameEventType.Checkpoint, position, 0.8f);
            if (Toast != null) Toast(Loc.T("holiday.powerup." + kind.ToString().ToLowerInvariant()), PowerUp.ColorOf(kind));
            if (PowerUpCollected != null) PowerUpCollected(kind);
        }

        // ================================================================ kid events

        void OnJumped() { stats.jumps++; }
        void OnDoubleJumped() { stats.doubleJumps++; }
        void OnSlid() { stats.slides++; }

        /// <summary>Hitting something solid head-on ends the run; a shield or the turbo breaks through instead.</summary>
        void OnKidCollided(Collision2D collision)
        {
            if (Phase != RunPhase.Running || dayChanging) return;
            var solid = collision.collider != null ? collision.collider.GetComponentInParent<RunSolid>() : null;
            if (solid == null || !solid.deadly) return;

            bool headOn = false;
            Vector2 point = kid.transform.position;
            for (int i = 0; i < collision.contactCount; i++)
            {
                var contact = collision.GetContact(i);
                // The normal points from the obstacle toward the kid: back along the run when it is head-on.
                if (contact.normal.x < -0.55f)
                {
                    headOn = true;
                    point = contact.point;
                    break;
                }
            }
            if (!headOn) return;

            if (Time.time < invulnerableUntil || TurboLeft > 0f || ShieldLeft > 0f)
            {
                BreakThrough(solid, point);
                return;
            }
            lastHit = solid;
            level.LoseBall("lose.crash");
        }

        /// <summary>The kid passes through <paramref name="solid"/>: it bursts, or just stops being in the way.</summary>
        void BreakThrough(RunSolid solid, Vector2 point)
        {
            var crate = solid as RunBreakable;
            if (crate != null)
            {
                crate.Smash(point);
            }
            else
            {
                if (kidCollider != null)
                    foreach (var c in solid.Colliders) if (c != null) Physics2D.IgnoreCollision(kidCollider, c, true);
                solid.Cleared = true;
                streak++;
                GameEvents.Raise(GameEventType.Kick, point, 0.9f);
                if (cameraFollow != null) cameraFollow.Shake(0.12f, 0.2f);
            }
            if (TurboLeft <= 0f && Time.time >= invulnerableUntil && ShieldLeft > 0f)
            {
                // The shield takes the knock and is spent.
                ShieldLeft = 0f;
                invulnerableUntil = Time.time + 1.2f;
                streak = Mathf.Max(0, streak - 2);
                if (Toast != null) Toast(Loc.T("holiday.shieldSaved"), PowerUp.ColorOf(PowerUpKind.Shield));
            }
        }

        // ================================================================ crash, results, revive

        void OnCrashed(string reason)
        {
            if (Phase == RunPhase.Crashed || Phase == RunPhase.Results) return;
            crashReason = reason;
            crashX = kid.transform.position.x;
            crashTime = Time.unscaledTime;
            streak = 0;
            SetPhase(RunPhase.Crashed);
            // Bonked back off the obstacle, and a shake to go with it.
            if (reason != "lose.fell" && reason != "lose.gap" && reason != "lose.splash")
                kid.Body.linearVelocity = new Vector2(-3f, 5f);
            if (cameraFollow != null) cameraFollow.Shake(0.22f, 0.35f);
        }

        void EnterResults()
        {
            var data = SaveSystem.Data;
            var r = new RunResult
            {
                score = Score,
                distance = (int)Distance,
                coins = Coins,
                stage = StageIndex,
                day = Day,
                bestScoreBefore = data.holidayBestScore,
                bestDistanceBefore = data.holidayBestDistance,
                reason = crashReason,
                stats = Stats,
            };
            r.newBestScore = r.score > r.bestScoreBefore;
            r.newBestDistance = r.distance > r.bestDistanceBefore;
            Result = r;
            AnalyticsService.Track("holiday_run_end", "score", r.score, "distance", r.distance, "coins", r.coins, "stage", r.stage + 1,
                "day", r.day, "reason", r.reason, "x", crashX.ToString("0"), "revives", revivesUsed, "near_misses", stats.nearMisses);
            SetPhase(RunPhase.Results);
            if (Ended != null) Ended(r);
        }

        /// <summary>Saves the run once (bests, coins, missions); the results screen's every way out comes through here.</summary>
        void Commit()
        {
            if (committed) return;
            if (Phase != RunPhase.Results && Phase != RunPhase.Crashed) return;
            committed = true;
            try
            {
                var data = SaveSystem.Data;
                var s = Stats;
                data.holidayRuns++;
                data.holidayDays += s.days;
                data.holidayTotalDistance += s.distance;
                data.holidayBestScore = Mathf.Max(data.holidayBestScore, s.score);
                data.holidayBestDistance = Mathf.Max(data.holidayBestDistance, s.distance);
                int missionCoins = HolidayMissions.Commit(s, new List<MissionView>());
                SaveSystem.AddCoins(Coins + missionCoins);
                SaveSystem.Save();
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Holiday Run] Could not save the run: " + e.Message);
            }
        }

        /// <summary>Spend coins to carry on from just past what was hit, with a moment of shield.</summary>
        public void Revive()
        {
            if ((Phase != RunPhase.Results && Phase != RunPhase.Crashed) || !CanRevive) return;
            int cost = ReviveCost;
            if (!SaveSystem.TrySpend(cost)) return;
            revivesUsed++;
            SaveSystem.Save();
            AnalyticsService.Track("holiday_revive", "cost", cost, "stage", StageIndex + 1, "day", Day);

            float x = lastHit != null ? lastHit.RightX + 1.8f : crashX + 6f;
            x = Mathf.Min(x, HolidayStages.StartOf(HolidayStages.Count) - 6f);
            kid.ResetTo(new Vector2(x, 0.6f));
            if (endlessBall != null) endlessBall.ResetAt(kid.transform.position);
            Speed = Mathf.Max(DayStartSpeed(Day), Speed * 0.7f);
            kid.autoRunSpeed = Speed;
            streak = 0;
            lastX = x;
            lastHit = null;
            ShieldLeft = Mathf.Max(ShieldLeft, 3f);
            invulnerableUntil = Time.time + 3f;
            if (cameraFollow != null) cameraFollow.SnapToTarget();
            level.ResumeAfterCrash();
            if (Toast != null) Toast(Loc.T("holiday.revived"), Mint);
        }

        public void TogglePause()
        {
            if (level != null) level.TogglePause();
        }

        /// <summary>A fresh run from the start of day 1 (saves the one that just ended).</summary>
        public void Restart()
        {
            // BeginRun puts the level back at its start; OnLevelState then starts the run over.
            level.BeginRun();
        }

        public void QuitToMenu()
        {
            Commit();
            FrontEndController.Open(FrontEndScreenId.Title);
        }

        // ================================================================ the day changes at the school gate

        IEnumerator DayRoutine()
        {
            dayChanging = true;
            stats.days++;
            bonusCoins += dayBonusCoins;
            bonusScore += dayPoints * Day;
            if (Toast != null) Toast(Loc.F("holiday.dayDone", Day), Gold);
            GameEvents.Raise(GameEventType.Goal, kid.transform.position, 1f);

            yield return FadeTo(1f, 0.5f);

            Day++;
            StageIndex = 0;
            StageProgress = 0f;
            streak = Mathf.Max(0, streak / 2);
            // Back to the start of the street while the screen is white: first the kid (so the world loads
            // round them, not round the school gate), then the stages, holding the kid still until they are in.
            FreezeKid(true);
            PlaceAtStart();
            if (streamer != null)
            {
                streamer.StartDay(0);
                float waited = 0f;
                while (!streamer.IsReady && waited < 10f) { waited += Time.unscaledDeltaTime; yield return null; }
            }
            Speed = DayStartSpeed(Day);
            kid.autoRunSpeed = Speed;
            FreezeKid(false);
            PlaceAtStart();
            if (DayStarted != null) DayStarted(Day);
            if (StageChanged != null) StageChanged(0, Day);

            yield return FadeTo(0f, 0.6f);
            dayChanging = false;
        }

        IEnumerator FadeTo(float target, float seconds)
        {
            float from = Fade, t = 0f;
            while (t < seconds)
            {
                if (!TimeControl.IsPaused) t += Time.unscaledDeltaTime;
                Fade = Mathf.Lerp(from, target, t / seconds);
                yield return null;
            }
            Fade = target;
        }

        // ================================================================ power-up auras

        /// <summary>Soft glows round the kid while a shield, the turbo or the magnet is on.</summary>
        void UpdateAuras()
        {
            bool live = Phase == RunPhase.Running || Phase == RunPhase.Paused;
            Vector3 centre = kid != null ? kid.transform.position + new Vector3(0f, 0.05f, -0.35f) : Vector3.zero;

            // The shield blinks over its last three seconds.
            float shield = live && ShieldLeft > 0f ? (ShieldLeft > 3f || Mathf.Repeat(Time.time * 6f, 1f) > 0.35f ? 1f : 0.25f) : 0f;
            Aura(ref shieldAura, "ShieldAura", ProceduralSprites.SoftEdgeDisc, PowerUp.ColorOf(PowerUpKind.Shield), 2.5f, 0.5f * shield, centre, 0f);
            Aura(ref turboAura, "TurboAura", ProceduralSprites.SoftDisc, PowerUp.ColorOf(PowerUpKind.Turbo), 3.1f, live && TurboLeft > 0f ? 0.6f : 0f, centre + new Vector3(0f, 0f, 0.1f), 0.1f);
            float pulse = 1f + Mathf.Repeat(Time.time * 1.6f, 1f) * 0.5f;
            Aura(ref magnetAura, "MagnetAura", ProceduralSprites.Ring, PowerUp.ColorOf(PowerUpKind.Magnet), magnetRadius * 0.9f * pulse * 0.5f,
                live && MagnetLeft > 0f ? 0.35f * (1.6f - pulse) : 0f, centre, 0f);
        }

        void Aura(ref SpriteRenderer aura, string name, Sprite sprite, Color color, float size, float alpha, Vector3 position, float wobble)
        {
            if (aura == null)
            {
                if (alpha <= 0.01f) return;
                var go = new GameObject(name);
                aura = go.AddComponent<SpriteRenderer>();
                aura.sprite = sprite;
                aura.sortingOrder = 44;
            }
            aura.enabled = alpha > 0.01f;
            if (!aura.enabled) return;
            float w = 1f + Mathf.Sin(Time.time * 9f) * wobble;
            aura.color = new Color(color.r, color.g, color.b, alpha);
            aura.transform.position = position;
            aura.transform.localScale = Vector3.one * size * w;
        }
    }
}
