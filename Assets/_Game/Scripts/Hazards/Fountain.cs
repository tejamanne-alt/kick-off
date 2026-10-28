using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A plaza floor fountain: water jets shoot up from a grate set flush in the paving,
    /// so you can dribble straight through it. The jets pulse up and down, and the lift
    /// on the ball follows the visible jet: only inside the water column and only up to
    /// the jet's current height. Splash droplets arc out and fall back onto the grate.
    /// </summary>
    [RequireComponent(typeof(BoxCollider2D))]
    public class Fountain : HazardBase
    {
        [Tooltip("Tallest the main jet gets (world units).")]
        public float maxHeight = 4f;
        [Tooltip("Upward acceleration on the ball inside the jet at full height.")]
        public float strength = 18f;
        [Range(0f, 1f)] public float kidFactor = 0.1f;
        [Tooltip("Seconds per rise and fall of the jets.")]
        public float pulsePeriod = 3.2f;
        [Range(0f, 1f)] public float lowestFraction = 0.45f;
        public float phaseOffset;

        [Header("Visuals")]
        [Tooltip("Main jet first; the rest are the smaller outer jets.")]
        public Transform[] jets;
        public float[] jetHeightFactors = { 1f, 0.55f, 0.55f };
        [Tooltip("Height in world units of a jet sprite at scale 1.")]
        public float jetSpriteHeight = 4f;
        public Transform[] droplets;

        /// <summary>Current height of the main jet above the paving (world units).</summary>
        public float CurrentHeight { get; private set; }

        float time;
        float baseY;
        float[] nozzleX;

        void Awake()
        {
            GetComponent<BoxCollider2D>().isTrigger = true;
            baseY = transform.position.y;
            nozzleX = new float[jets != null ? jets.Length : 0];
            for (int i = 0; i < nozzleX.Length; i++) nozzleX[i] = jets[i] != null ? jets[i].position.x : transform.position.x;
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Animate();
        }

        void Update()
        {
            time += Time.deltaTime;
            Animate();
        }

        void Animate()
        {
            float wave = 0.5f + 0.5f * Mathf.Sin(time / Mathf.Max(pulsePeriod, 0.1f) * Mathf.PI * 2f);
            float k = Mathf.Lerp(lowestFraction, 1f, wave);
            CurrentHeight = maxHeight * k;

            if (jets != null)
            {
                for (int i = 0; i < jets.Length; i++)
                {
                    if (jets[i] == null) continue;
                    float f = i < jetHeightFactors.Length ? jetHeightFactors[i] : 0.5f;
                    // Outer jets pulse against the main one, so the fountain always looks alive.
                    float kk = i == 0 ? k : Mathf.Lerp(lowestFraction, 1f, 1f - wave);
                    float h = maxHeight * f * kk;
                    Vector3 s = jets[i].localScale;
                    jets[i].localScale = new Vector3(s.x, h / Mathf.Max(jetSpriteHeight, 0.01f), s.z);
                    // Grow from the nozzle along the jet's own lean.
                    Vector3 up = jets[i].up;
                    jets[i].position = new Vector3(nozzleX[i], baseY, jets[i].position.z) + up * h * 0.5f;
                }
            }

            if (droplets != null)
            {
                // Each droplet leaves the top of the jets and falls in an arc to one side.
                for (int i = 0; i < droplets.Length; i++)
                {
                    if (droplets[i] == null) continue;
                    float cycle = 1.1f;
                    float t = Mathf.Repeat(time + i * cycle / droplets.Length, cycle) / cycle;
                    float side = i % 2 == 0 ? 1f : -1f;
                    float spread = 0.5f + (i % 3) * 0.25f;
                    float startY = CurrentHeight * (0.55f + 0.1f * (i % 3));
                    float x = side * spread * t;
                    float y = startY * (1f - t * t) + 0.05f;
                    droplets[i].position = new Vector3(transform.position.x + x, baseY + y, droplets[i].position.z);
                }
            }
        }

        void OnTriggerStay2D(Collider2D other)
        {
            Ball.BallController ball;
            Player.KidController kid;
            if (TryGetBall(other, out ball))
            {
                float above = ball.Body.position.y - baseY;
                if (above < CurrentHeight)
                {
                    // Strongest low in the jet, easing off toward the top so the ball bobs near the
                    // crest (with strength 18 it balances the ball's gravity about 85% of the way up).
                    float push = strength * Mathf.Lerp(1.25f, 0.8f, above / Mathf.Max(CurrentHeight, 0.01f));
                    ball.Body.AddForce(Vector2.up * push * ball.Body.mass);
                }
            }
            else if (TryGetKid(other, out kid))
            {
                kid.Body.AddForce(Vector2.up * strength * kidFactor * kid.Body.mass);
            }
        }
    }
}
