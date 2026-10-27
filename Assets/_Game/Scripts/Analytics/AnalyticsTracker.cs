using DribbleToSchool.Core;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Analytics
{
    /// <summary>
    /// Hooks gameplay into analytics: level start / complete / quit, where the
    /// ball gets lost (for balancing), challenge scores and purchases.
    /// </summary>
    public class AnalyticsTracker : MonoBehaviour
    {
        static AnalyticsTracker instance;
        LevelManager hooked;
        string levelId;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (instance != null) return;
            var go = new GameObject("AnalyticsTracker");
            DontDestroyOnLoad(go);
            instance = go.AddComponent<AnalyticsTracker>();
            AnalyticsService.Track("app_open", "version", Application.version, "platform", Application.platform.ToString());
        }

        void Awake()
        {
            SceneManager.sceneLoaded += OnSceneLoaded;
            GameEvents.Raised += OnEvent;
            OnSceneLoaded(SceneManager.GetActiveScene(), LoadSceneMode.Single);
        }

        void OnDestroy()
        {
            SceneManager.sceneLoaded -= OnSceneLoaded;
            GameEvents.Raised -= OnEvent;
            Unhook();
        }

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            Unhook();
            var level = LevelManager.Current;
            if (level == null) return;
            hooked = level;
            levelId = level.level != null ? level.level.levelId : "test";
            level.BallLost += OnBallLost;
            level.Completed += OnCompleted;
        }

        void Unhook()
        {
            if (hooked == null) return;
            if (hooked.State != LevelState.Complete)
                AnalyticsService.Track("level_quit", "level", levelId, "time", hooked.ElapsedTime.ToString("0.0"), "lost", hooked.BallsLost);
            hooked.BallLost -= OnBallLost;
            hooked.Completed -= OnCompleted;
            hooked = null;
        }

        void OnEvent(GameEventType type, Vector2 position, float intensity)
        {
            if (type == GameEventType.LevelStart)
                AnalyticsService.Track("level_start", "level", levelId);
        }

        void OnBallLost(string reason)
        {
            float x = hooked != null ? hooked.ball.transform.position.x : 0f;
            AnalyticsService.Track("ball_lost", "level", levelId, "reason", reason, "x", x.ToString("0.0"),
                "time", hooked != null ? hooked.ElapsedTime.ToString("0.0") : "0");
        }

        void OnCompleted(LevelResult r)
        {
            AnalyticsService.Track("level_complete", "level", levelId, "stars", r.stars, "time", r.time.ToString("0.0"),
                "coins", r.coins + "/" + r.totalCoins, "lost", r.ballsLost, "streak", r.bestPerfectStreak,
                "challenge", r.isChallenge, "score", r.score, "bell", GameSettings.BellTimerEnabled);
        }
    }
}
