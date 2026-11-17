using DribbleToSchool.Audio;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A level crossing over the Enoden's track (Kamakura's first level, LevelBuildKit.TrackBuilder.RailCrossing). As the kid
    /// comes up to it the bells ring and the red lamps flash; the barrier arms come down across the footpath and the road on
    /// both sides of the tracks; the tram goes through without stopping, toward the camera and on past it; the arms go up and
    /// the lamps stop. While it is closed a barrier a step back from the near arm stops the kid and the ball, as a real
    /// crossing's arm does, so the kid waits; open, the way over is free.
    ///
    /// It closes once for each approach: only when the kid is coming up to it with the ball still on this side of the arm (a
    /// kid or a ball already over is never shut in), and again after a restart from a checkpoint before it.
    /// </summary>
    public class LevelCrossing : HazardBase
    {
        [Tooltip("Where the kid waits while the crossing is closed (x): the barrier's middle, a step back from the near arm.")]
        public float stopX;
        [Tooltip("The far arm's x: a kid past it is over the crossing.")]
        public float farX;
        [Tooltip("How far before the barrier (m) the kid sets the bells off.")]
        public float warnDistance = 9f;
        [Tooltip("No closing on a kid nearer the barrier than this (m): they are let over.")]
        public float tooClose = 1.2f;

        [Header("The cycle (seconds from the bells)")]
        public float lowerStart = 0.6f;
        public float lowerTime = 1.8f;
        [Tooltip("When the tram's front reaches the crossing's far side.")]
        public float tramAtCrossing = 4.5f;
        public float raiseDelay = 0.5f;
        public float raiseTime = 1.6f;

        [Header("Parts")]
        [Tooltip("The barrier arms, upright at rest, each turning down about its own x (toward -z) by armDrop degrees.")]
        public Transform[] arms;
        public float armDrop = 90f;
        [Tooltip("The signals' red lamps, flashed in turn while the bells ring.")]
        public Renderer[] lights;
        [Tooltip("Stops the kid and the ball at the near arm while the crossing is closed.")]
        public Collider2D barrier;
        [Tooltip("The tram (its root's z is the middle of its length), hidden until it comes.")]
        public Transform tram;
        [Tooltip("The tram's speed through the crossing (m/s): 12.5 is the Enoden's 45 km/h.")]
        public float tramSpeed = 12.5f;
        [Tooltip("Where the tram's front is when the bells start (z), far up the track in the haze; it brakes evenly to tramSpeed by the crossing.")]
        public float tramStartZ = 140f;
        public float tramLength = 12.7f;
        [Tooltip("The street's depth the tram crosses: from the far side of the footpath (z) to the near side of the road.")]
        public float crossingFarZ = 2.45f, crossingNearZ = -8.3f;
        [Tooltip("Once its back end is nearer than this (z), past the camera, the tram is put away.")]
        public float tramGoneZ = -40f;
        [Tooltip("How near (m, along the street) the kid must be to hear the bells.")]
        public float hearing = 26f;

        /// <summary>The crossing's state at a moment of its cycle.</summary>
        public struct State
        {
            /// <summary>How far down the arms are (0 up, 1 down).</summary>
            public float arm;
            /// <summary>The bells ring and the lamps flash.</summary>
            public bool warning;
            /// <summary>The barrier stops the kid and the ball.</summary>
            public bool closed;
            /// <summary>The tram is in sight, its front end at <see cref="tramFrontZ"/>.</summary>
            public bool tramShown;
            public float tramFrontZ;
        }

        /// <summary>When the tram's back end has cleared the near side of the street (seconds from the bells).</summary>
        public float ClearTime { get { return tramAtCrossing + (crossingFarZ - crossingNearZ + tramLength) / Mathf.Max(0.1f, tramSpeed); } }

        /// <summary>When the arms are all the way up again and the lamps stop: the end of the cycle.</summary>
        public float OpenTime { get { return ClearTime + raiseDelay + raiseTime; } }

        /// <summary>The crossing at <paramref name="t"/> seconds from the bells (before 0: open, the tram not yet coming).</summary>
        public State At(float t)
        {
            var s = new State();
            if (t < 0f || t >= OpenTime)
            {
                s.tramFrontZ = TramFrontZ(0f);
                return s;
            }
            s.warning = true;
            s.closed = true;
            float raise = ClearTime + raiseDelay;
            if (t < lowerStart) s.arm = 0f;
            else if (t < lowerStart + lowerTime) s.arm = Ease((t - lowerStart) / lowerTime);
            else if (t < raise) s.arm = 1f;
            else s.arm = 1f - Ease((t - raise) / raiseTime);
            s.tramFrontZ = TramFrontZ(t);
            s.tramShown = s.tramFrontZ + tramLength > tramGoneZ;
            return s;
        }

        /// <summary>
        /// The tram's front (z) at t: from <see cref="tramStartZ"/> it comes on braking evenly, to reach the crossing's far side
        /// at <see cref="tramAtCrossing"/> at <see cref="tramSpeed"/>, and goes on through at that speed.
        /// </summary>
        public float TramFrontZ(float t)
        {
            float T = Mathf.Max(0.1f, tramAtCrossing);
            if (t >= T) return crossingFarZ - tramSpeed * (t - T);
            float d = T - Mathf.Max(0f, t);
            float brake = Mathf.Max(0f, (tramStartZ - crossingFarZ - tramSpeed * T) / (T * T));
            return crossingFarZ + tramSpeed * d + brake * d * d;
        }

        float time = -1f;
        bool running, finished;
        float lastBell = -10f;
        Quaternion[] armRest;
        int shownFlash = -2;
        float tramX, tramY;

        void Awake()
        {
            if (arms != null)
            {
                armRest = new Quaternion[arms.Length];
                for (int i = 0; i < arms.Length; i++) if (arms[i] != null) armRest[i] = arms[i].localRotation;
            }
            if (tram != null)
            {
                tramX = tram.position.x;
                tramY = tram.position.y;
            }
            ResetState();
        }

        /// <summary>A restart: open, the tram away, ready to close again for a kid coming up to it.</summary>
        public override void ResetState()
        {
            time = -1f;
            running = false;
            finished = false;
            Pose(At(-1f));
        }

        void Update()
        {
            if (running)
            {
                time += Time.deltaTime;
                var s = At(time);
                Pose(s);
                if (s.warning && Time.time - lastBell > 0.45f && Near())
                {
                    lastBell = Time.time;
                    AudioDirector.Play(Sfx.Beep, 0.3f, 1.45f);
                }
                if (time >= OpenTime) { running = false; finished = true; }
                return;
            }
            if (finished || !IsLive) return;
            var kid = Kid;
            if (kid == null) return;
            float kx = kid.transform.position.x;
            if (kx >= stopX - tooClose)
            {
                // Over, or too near to close on: no tram for this approach.
                finished = true;
                return;
            }
            var ball = Ball;
            bool ballThisSide = ball == null || ball.transform.position.x < stopX - 0.3f;
            if (kx > stopX - warnDistance && ballThisSide)
            {
                running = true;
                time = 0f;
                Pose(At(0f));
            }
        }

        void Pose(State s)
        {
            if (arms != null && armRest != null)
                for (int i = 0; i < arms.Length; i++)
                    if (arms[i] != null) arms[i].localRotation = armRest[i] * Quaternion.Euler(-armDrop * s.arm, 0f, 0f);
            if (barrier != null && barrier.enabled != s.closed) barrier.enabled = s.closed;

            // The lamps flash in turn, left and right, about twice a second.
            int flash = s.warning ? (Mathf.FloorToInt(Mathf.Max(0f, time) * 2.2f) % 2) : -1;
            if (flash != shownFlash && lights != null)
            {
                for (int i = 0; i < lights.Length; i++)
                    if (lights[i] != null) lights[i].enabled = s.warning && (i % 2) == flash;
                shownFlash = flash;
            }

            if (tram == null) return;
            if (tram.gameObject.activeSelf != s.tramShown) tram.gameObject.SetActive(s.tramShown);
            if (s.tramShown) tram.position = new Vector3(tramX, tramY, s.tramFrontZ + tramLength * 0.5f);
        }

        bool Near()
        {
            var kid = Kid;
            return kid != null && Mathf.Abs(kid.transform.position.x - (stopX + farX) * 0.5f) < hearing;
        }

        static float Ease(float t)
        {
            t = Mathf.Clamp01(t);
            return t * t * (3f - 2f * t);
        }
    }
}
