using System.Collections;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Turns gameplay events into visual feedback: dust, sparkles, splashes,
    /// feathers, confetti, a puff of air under a double jump, a dust trail behind
    /// a slide, camera shake and the slow-motion goal moment.
    /// </summary>
    public class FxDirector : MonoBehaviour
    {
        public FxPool pool;
        public CameraFollow2D cameraFollow;
        public Sprite puff, spark, drop;
        public Color dustColor = new Color(0.85f, 0.78f, 0.68f, 0.9f);

        static readonly Color Gold = new Color(1f, 0.85f, 0.3f);
        static readonly Color[] Confetti =
        {
            new Color(0.95f, 0.4f, 0.4f), new Color(1f, 0.82f, 0.3f), new Color(0.4f, 0.65f, 0.95f),
            new Color(0.45f, 0.8f, 0.45f), new Color(0.85f, 0.5f, 0.9f),
        };

        Coroutine slideTrail;

        void OnEnable() { GameEvents.Raised += OnEvent; }
        void OnDisable() { GameEvents.Raised -= OnEvent; slideTrail = null; }

        void OnEvent(GameEventType type, Vector2 p, float k)
        {
            if (pool == null) return;
            switch (type)
            {
                case GameEventType.Kick:
                    Dust(p + Vector2.down * 0.15f, 4 + Mathf.RoundToInt(k * 5f), 1.6f + k * 2f);
                    if (k > 0.6f) pool.Burst(spark, p, 5, Vector2.up, 360f, 2f, 4f, Color.white, 0.18f, 0.02f, 0.3f);
                    Shake(0.05f + k * 0.12f, 0.15f);
                    break;
                case GameEventType.Touch:
                case GameEventType.Trap:
                    Dust(p + Vector2.down * 0.15f, 2, 1.2f);
                    break;
                case GameEventType.PerfectTouch:
                    pool.Burst(spark, p, 7, Vector2.up, 200f, 1.5f, 3.5f, Gold, 0.22f, 0.04f, 0.45f, 2f, 1f, 200f);
                    break;
                case GameEventType.Juggle:
                    pool.Burst(spark, p, 4, Vector2.up, 120f, 1f, 2.5f, Color.white, 0.16f, 0.03f, 0.35f);
                    break;
                case GameEventType.Land:
                    Dust(p, 3 + Mathf.RoundToInt(k * 5f), 1.2f + k * 1.5f);
                    if (k > 0.6f) Shake(k * 0.08f, 0.12f);
                    break;
                case GameEventType.Jump:
                    Dust(p, 3, 1.2f);
                    break;
                case GameEventType.DoubleJump:
                    // A puff of air kicked away under the feet, and a glint.
                    pool.Burst(puff, p, 7, Vector2.down, 220f, 1.4f, 3f, new Color(1f, 1f, 1f, 0.8f), 0.2f, 0.5f, 0.35f, -0.5f, 4f, 120f, 0.12f);
                    pool.Burst(spark, p + Vector2.up * 0.3f, 4, Vector2.up, 140f, 1.5f, 3f, Color.white, 0.14f, 0.02f, 0.3f);
                    break;
                case GameEventType.Slide:
                    Dust(p, 4 + Mathf.RoundToInt(k * 3f), 1.6f);
                    if (slideTrail == null) slideTrail = StartCoroutine(SlideTrail());
                    break;
                case GameEventType.BallBounce:
                    if (k > 0.25f) Dust(p + Vector2.down * 0.15f, 2, 1f + k);
                    break;
                case GameEventType.Coin:
                    pool.Burst(spark, p, 8, Vector2.up, 360f, 1.5f, 3.5f, Gold, 0.2f, 0.02f, 0.4f, 0f, 2f, 300f);
                    break;
                case GameEventType.Sticker:
                    for (int i = 0; i < Confetti.Length; i++)
                        pool.Burst(spark, p, 4, Vector2.up, 360f, 2f, 5f, Confetti[i], 0.25f, 0.05f, 0.7f, 3f, 1f, 400f);
                    Shake(0.06f, 0.15f);
                    break;
                case GameEventType.Checkpoint:
                    pool.Burst(spark, p + Vector2.up * 1.8f, 10, Vector2.up, 360f, 1.5f, 3f, new Color(0.5f, 1f, 0.6f), 0.22f, 0.03f, 0.6f, 1f, 1f, 200f);
                    break;
                case GameEventType.Splash:
                    pool.Burst(drop, p, 14, Vector2.up, 70f, 3f, 7f, new Color(0.55f, 0.8f, 1f, 0.95f), 0.16f, 0.08f, 0.7f, 18f, 0.5f);
                    break;
                case GameEventType.BallLost:
                    Dust(p, 6, 2f);
                    break;
                case GameEventType.DogSteal:
                    Dust(p, 5, 2f);
                    break;
                case GameEventType.SeagullHit:
                    pool.Burst(puff, p, 6, Vector2.down, 160f, 0.5f, 1.5f, Color.white, 0.18f, 0.12f, 1.2f, 1.5f, 1f, 180f);
                    break;
                case GameEventType.Springboard:
                    Dust(p, 5, 2f);
                    pool.Burst(spark, p, 5, Vector2.up, 60f, 3f, 5f, Color.white, 0.18f, 0.02f, 0.35f);
                    break;
                case GameEventType.SwitchPressed:
                    pool.Burst(spark, p, 10, Vector2.up, 360f, 2f, 4f, new Color(0.5f, 1f, 0.6f), 0.22f, 0.03f, 0.5f);
                    break;
                case GameEventType.GateOpened:
                    Dust(p, 6, 1.5f);
                    break;
                case GameEventType.Bell:
                    Shake(0.08f, 0.4f);
                    break;
                case GameEventType.Goal:
                    for (int i = 0; i < Confetti.Length; i++)
                        pool.Burst(puff, p + Vector2.up * 2f, 12, Vector2.up, 140f, 4f, 9f, Confetti[i], 0.14f, 0.12f, 1.8f, 6f, 1.5f, 500f);
                    StartCoroutine(GoalSlowMo());
                    break;
            }
        }

        /// <summary>Dust thrown up from the heels all along a slide.</summary>
        IEnumerator SlideTrail()
        {
            var level = LevelManager.Current;
            var kid = level != null ? level.kid : null;
            float next = 0f;
            while (kid != null && kid.IsSliding)
            {
                if (Time.time >= next && kid.IsGrounded)
                {
                    next = Time.time + 0.06f;
                    Vector2 heel = kid.FeetPosition + new Vector2(kid.Facing * 0.45f, 0.03f);
                    pool.Burst(puff, heel, 1, new Vector2(-kid.Facing * 0.4f, 1f), 70f, 0.5f, 1.5f, dustColor, 0.2f, 0.45f, 0.4f, -0.4f, 3f, 90f, 0.06f);
                }
                yield return null;
            }
            slideTrail = null;
        }

        void Dust(Vector2 p, int count, float speed)
        {
            pool.Burst(puff, p, count, Vector2.up, 150f, speed * 0.4f, speed, dustColor, 0.3f, 0.55f, 0.45f, -0.5f, 3f, 90f, 0.1f);
        }

        void Shake(float amount, float duration)
        {
            if (cameraFollow != null && GameSettings.ScreenShakeEnabled) cameraFollow.Shake(amount, duration);
        }

        IEnumerator GoalSlowMo()
        {
            TimeControl.SetSlowMotion(0.35f);
            float end = Time.unscaledTime + 0.7f;
            while (Time.unscaledTime < end) yield return null;
            TimeControl.SetSlowMotion(1f);
        }
    }
}
