using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A zebra crossing over a side street that runs away from the camera, with a
    /// pedestrian signal. Green man: cross. Flashing green man: hurry, it is about to
    /// change. Red man: the side street's traffic goes, and cars drive toward the camera
    /// across the crossing; the kid or the ball on the road loses the ball.
    ///
    /// While the man is green, cars queue at the stop line up the side street. Cars are
    /// drawn front-on and drive along the side street in real depth (z): far up the street,
    /// through the crossing at z = 0, and past the camera.
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
        [Tooltip("Half the car sprite's height, so the wheels sit on the road.")]
        public float carHalfHeight = 0.82f;
        [Tooltip("Where the lead car waits, up the side street (world z).")]
        public float stopLineZ = 7f;
        public float queueGap = 6f;
        [Tooltip("Where cars come from, far up the side street.")]
        public float farZ = 60f;
        [Tooltip("Where cars leave, past the camera.")]
        public float exitZ = -24f;
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
                float queueZ = stopLineZ + i * queueGap;
                float z;
                if (c < waitTime)
                {
                    // Pull up to the stop line from further up the street, then wait.
                    float u = Mathf.Clamp01((c / waitTime - i * 0.15f) / 0.5f);
                    z = Mathf.Lerp(farZ + i * queueGap, queueZ, Smooth(u));
                }
                else
                {
                    // Red man: drive through the crossing toward the camera, lead car first.
                    float k = (c - waitTime) / redTime;
                    float u = Mathf.Clamp01((k - i * 0.3f) / 0.65f);
                    z = Mathf.Lerp(queueZ, exitZ, u * u);
                }
                PlaceCar(cars[i], z);
            }
        }

        void PlaceCar(SpriteRenderer car, float z)
        {
            car.transform.localScale = Vector3.one;
            car.transform.position = new Vector3(transform.position.x, groundY + carHalfHeight, z);
            // Behind the kid while up the street, in front once past the crossing.
            car.sortingOrder = z > 0f ? behindOrder : frontOrder;
            car.enabled = true;
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
