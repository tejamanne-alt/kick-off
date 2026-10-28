using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A zebra crossing over a side street that runs away from the camera, with a
    /// pedestrian signal. Green man: cross. Flashing green man: hurry, it is about to
    /// change. Red man: the side street's traffic goes, and cars drive toward the camera
    /// across the crossing; the kid or the ball on the road loses the ball.
    ///
    /// While the man is green, cars queue at the stop line further up the side street.
    /// Cars are drawn front-on and placed by a depth value: negative is up the street
    /// (smaller, higher, behind the kid), 0 is the crossing, positive is between the
    /// crossing and the camera (bigger, lower, in front of everything).
    /// </summary>
    [RequireComponent(typeof(BoxCollider2D))]
    public class Crossing : HazardBase
    {
        public enum Light { Green, Amber, Red }

        public float greenTime = 3.5f;
        [Tooltip("The green man flashes for this long before the red man.")]
        public float amberTime = 1.2f;
        public float redTime = 3f;
        [Tooltip("Seconds into the cycle at level start, to vary crossings.")]
        public float phaseOffset;

        [Header("Signal")]
        public SpriteRenderer greenFigure;
        public SpriteRenderer redFigure;
        public Color figureOff = new Color(0.22f, 0.22f, 0.24f);

        [Header("Traffic")]
        [Tooltip("Front-view cars, lead car first.")]
        public SpriteRenderer[] cars;
        [Tooltip("World y of the crossing's road surface.")]
        public float groundY;
        [Tooltip("Half the car sprite's height at depth 0, so the wheels sit on the road.")]
        public float carHalfHeight = 0.82f;
        [Tooltip("How much higher on screen a car sits per unit of depth up the side street.")]
        public float depthRise = 0.35f;
        public float stopLineDepth = -1.3f;
        public float queueGap = 1.4f;
        public float farDepth = -4.6f;
        public float exitDepth = 3f;
        [Tooltip("Sorting order for cars up the street (behind the kid) and in front of the crossing.")]
        public int behindOrder = -35;
        public int frontOrder = 40;

        public Light Current { get; private set; }
        public float CycleLength { get { return greenTime + amberTime + redTime; } }
        public event System.Action<Light> LightChanged;

        float time;

        void Awake()
        {
            GetComponent<BoxCollider2D>().isTrigger = true;
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            Current = Evaluate(time);
            ApplyVisuals();
        }

        void Update()
        {
            time += Time.deltaTime;
            Light next = Evaluate(time);
            if (next != Current)
            {
                Current = next;
                Core.GameEvents.Raise(Core.GameEventType.LightChange, transform.position, next == Light.Red ? 1f : 0f);
                if (LightChanged != null) LightChanged(next);
            }
            ApplyVisuals();
        }

        Light Evaluate(float t)
        {
            float c = Mathf.Repeat(t, CycleLength);
            if (c < greenTime) return Light.Green;
            if (c < greenTime + amberTime) return Light.Amber;
            return Light.Red;
        }

        void ApplyVisuals()
        {
            bool flashOn = Mathf.Repeat(time * 3f, 1f) < 0.55f;
            if (greenFigure != null)
                greenFigure.color = Current == Light.Green || (Current == Light.Amber && flashOn) ? new Color(0.35f, 1f, 0.5f) : figureOff;
            if (redFigure != null)
                redFigure.color = Current == Light.Red ? new Color(1f, 0.32f, 0.28f) : figureOff;

            if (cars == null) return;
            float c = Mathf.Repeat(time, CycleLength);
            float waitTime = greenTime + amberTime;
            for (int i = 0; i < cars.Length; i++)
            {
                if (cars[i] == null) continue;
                float queueDepth = stopLineDepth - i * queueGap;
                float depth;
                if (c < waitTime)
                {
                    // Pull up to the stop line from further up the street, then wait.
                    float u = Mathf.Clamp01((c / waitTime - i * 0.15f) / 0.5f);
                    depth = Mathf.Lerp(farDepth - i * queueGap, queueDepth, Smooth(u));
                }
                else
                {
                    // Red man: drive through the crossing toward the camera, lead car first.
                    float k = (c - waitTime) / redTime;
                    float u = Mathf.Clamp01((k - i * 0.3f) / 0.65f);
                    depth = Mathf.Lerp(queueDepth, exitDepth, u * u);
                }
                PlaceCar(cars[i], depth);
            }
        }

        void PlaceCar(SpriteRenderer car, float depth)
        {
            float scale = Mathf.Pow(1.45f, depth);
            car.transform.localScale = new Vector3(scale, scale, 1f);
            car.transform.position = new Vector3(transform.position.x, groundY - depth * depthRise + carHalfHeight * scale, 0f);
            car.sortingOrder = depth < 0f ? behindOrder : frontOrder;
            float alpha = 1f;
            if (depth > exitDepth - 0.8f) alpha = Mathf.Clamp01((exitDepth - depth) / 0.8f);
            if (depth < farDepth + 0.6f) alpha = Mathf.Clamp01((depth - farDepth + 0.2f) / 0.8f);
            Color col = car.color;
            col.a = alpha;
            car.color = col;
            car.enabled = alpha > 0.01f;
        }

        static float Smooth(float u) { return u * u * (3f - 2f * u); }

        void OnTriggerStay2D(Collider2D other)
        {
            if (Current != Light.Red || !IsLive) return;
            Ball.BallController ball;
            Player.KidController kid;
            if (TryGetBall(other, out ball)) Lose("lose.honk");
            else if (TryGetKid(other, out kid)) Lose("lose.honk");
        }
    }
}
