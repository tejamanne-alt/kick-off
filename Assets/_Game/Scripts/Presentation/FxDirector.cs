using System.Collections;
using DribbleToSchool.CameraRig;
using DribbleToSchool.Core;
using DribbleToSchool.Holiday;
using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Turns gameplay events into visual feedback: dust, sparkles, splashes,
    /// feathers, confetti, camera shake and the slow-motion goal moment, and the slide (a wave of dust
    /// and grit thrown up as the feet kick out, speed streaks left hanging in the air, dust along the
    /// whole slide, the camera lunging in, then a puff as the kid springs up). The double jump has no
    /// effect of its own: it is a second push of the body in the air (KidAnimator), and lands with the
    /// ordinary landing's dust.
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

        static readonly Color Pebble = new Color(0.62f, 0.55f, 0.46f, 1f);

        Coroutine slideTrail;
        KidController kidRef;
        float nextTurboFx;

        /// <summary>A Holiday Run's turbo: speed streaks hung behind the kid and sparks flicked off the heels.</summary>
        void Update()
        {
            var run = HolidayRunDirector.Current;
            if (run == null || pool == null || run.Phase != RunPhase.Running || run.TurboLeft <= 0f || Time.time < nextTurboFx) return;
            var kid = Kid();
            if (kid == null) return;
            nextTurboFx = Time.time + 0.035f;
            Vector2 feet = kid.FeetPosition;
            pool.EmitShaped(ProceduralSprites.Streak, feet + new Vector2(-0.3f, Random.Range(0.1f, 1.4f)), new Vector2(-5f, 0f),
                new Color(1f, 0.78f, 0.35f, 0.7f), 0.9f, 1.7f, 0.3f, 0.22f, -0.12f, 0f);
            pool.Burst(spark, feet + new Vector2(-0.15f, 0.08f), 1, new Vector2(-1f, 0.35f), 40f, 2.5f, 5f, new Color(1f, 0.62f, 0.22f), 0.2f, 0f, 0.3f);
        }

        void Awake()
        {
            // The shock ring and the speed streak are drawn in code: make them now, not mid-slide.
            if (ProceduralSprites.Ring == null || ProceduralSprites.Streak == null) Debug.LogWarning("[FX] Could not draw the effect sprites.");
        }

        void OnEnable() { GameEvents.Raised += OnEvent; }
        void OnDisable() { GameEvents.Raised -= OnEvent; slideTrail = null; }

        KidController Kid()
        {
            if (kidRef != null) return kidRef;
            var level = LevelManager.Current;
            kidRef = level != null && level.kid != null ? level.kid : FindAnyObjectByType<KidController>();
            return kidRef;
        }

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
                case GameEventType.Slide:
                    SlideStart(p, k);
                    if (slideTrail == null) slideTrail = StartCoroutine(SlideTrail());
                    break;
                case GameEventType.SlideEnd:
                    GetUp(p);
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

        // ---------- Slide ----------

        /// <summary>
        /// The feet kick out: a wave of dust thrown ahead and up, grit flicked up behind, and three speed
        /// streaks left hanging in the air at leg, hip and chest height as the kid lunges away from them.
        /// </summary>
        void SlideStart(Vector2 p, float k)
        {
            var kid = Kid();
            float dir = kid != null ? kid.Facing : 1f;
            Vector2 feet = p + new Vector2(dir * 0.35f, 0.05f);
            pool.Burst(puff, feet, 7, new Vector2(dir, 0.3f), 40f, 2.4f, 6f, dustColor, 0.3f, 0.75f, 0.5f, -0.4f, 3f, 80f, 0.1f);
            pool.Burst(puff, p + Vector2.up * 0.05f, 4, Vector2.up, 100f, 1f, 2.4f, dustColor, 0.28f, 0.6f, 0.45f, -0.4f, 3f, 80f, 0.1f);
            for (int i = 0; i < 6; i++)
            {
                Vector2 v = new Vector2(-dir * Random.Range(0.4f, 3f), Random.Range(1.6f, 4.2f));
                pool.EmitShaped(drop, feet + Random.insideUnitCircle * 0.12f, v, Pebble, 0.12f, 0.05f, 0.5f, 1f, 0f, 0f, false, 15f, 0.4f, 0f);
            }
            for (int i = 0; i < 3; i++)
            {
                float y = 0.28f + i * 0.32f;
                pool.EmitShaped(ProceduralSprites.Streak, p + new Vector2(-dir * (0.15f + 0.3f * i), y), new Vector2(-dir * 1.2f, 0f),
                    new Color(1f, 1f, 1f, 0.6f), 0.9f + 0.2f * i, 1.4f, 0.4f, 0.3f, -0.12f, dir > 0f ? 0f : 180f);
            }
            Punch(-0.032f, 0.32f);    // a lunge: the view pushes in
            Shake(0.025f + k * 0.03f, 0.12f);
        }

        /// <summary>Dust and grit from the leading foot all along a slide, with a streak now and then.</summary>
        IEnumerator SlideTrail()
        {
            var kid = Kid();
            float next = 0f, nextStreak = 0f;
            while (kid != null && kid.IsSliding)
            {
                if (kid.IsGrounded)
                {
                    float pace = Mathf.Clamp01(kid.SlideSpeed / 7f);
                    if (Time.time >= next)
                    {
                        next = Time.time + 0.045f;
                        Vector2 foot = kid.FeetPosition + new Vector2(kid.Facing * 0.45f, 0.03f);
                        pool.Burst(puff, foot, 1, new Vector2(-kid.Facing * 0.4f, 1f), 70f, 0.5f, 1.5f + pace, dustColor, 0.24f, 0.55f, 0.42f, -0.4f, 3f, 90f, 0.06f);
                        if (Random.value < 0.35f)
                            pool.EmitShaped(drop, foot, new Vector2(-kid.Facing * Random.Range(0.5f, 2.5f), Random.Range(1.2f, 3f)), Pebble,
                                0.1f, 0.05f, 0.4f, 1f, 0f, 0f, false, 15f, 0.4f, 0f);
                    }
                    if (Time.time >= nextStreak && pace > 0.35f)
                    {
                        nextStreak = Time.time + 0.11f;
                        Vector2 hip = kid.FeetPosition + new Vector2(-kid.Facing * 0.5f, Random.Range(0.12f, 0.5f));
                        pool.EmitShaped(ProceduralSprites.Streak, hip, new Vector2(-kid.Facing * 1f, 0f), new Color(1f, 1f, 1f, 0.4f * pace + 0.1f),
                            0.7f, 1.1f, 0.3f, 0.26f, -0.12f, kid.Facing > 0 ? 0f : 180f);
                    }
                }
                yield return null;
            }
            slideTrail = null;
        }

        /// <summary>Back on their feet: a puff at the heels and two quick streaks as the stride picks up.</summary>
        void GetUp(Vector2 p)
        {
            var kid = Kid();
            if (kid != null && !kid.IsGrounded) return;
            float dir = kid != null ? kid.Facing : 1f;
            Dust(p + new Vector2(dir * 0.1f, 0f), 4, 1.7f);
            for (int i = 0; i < 2; i++)
                pool.EmitShaped(ProceduralSprites.Streak, p + new Vector2(-dir * 0.3f, 0.35f + i * 0.4f), new Vector2(-dir * 1f, 0f),
                    new Color(1f, 1f, 1f, 0.45f), 0.7f, 1.1f, 0.28f, 0.26f, -0.12f, dir > 0f ? 0f : 180f);
            pool.Burst(spark, p + Vector2.up * 0.5f, 3, Vector2.up, 100f, 1.2f, 2.4f, Color.white, 0.14f, 0.02f, 0.3f);
        }

        void Dust(Vector2 p, int count, float speed)
        {
            pool.Burst(puff, p, count, Vector2.up, 150f, speed * 0.4f, speed, dustColor, 0.3f, 0.55f, 0.45f, -0.5f, 3f, 90f, 0.1f);
        }

        void Shake(float amount, float duration)
        {
            if (cameraFollow != null && GameSettings.ScreenShakeEnabled) cameraFollow.Shake(amount, duration);
        }

        void Punch(float amount, float seconds)
        {
            if (cameraFollow != null) cameraFollow.Punch(amount, seconds);
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
