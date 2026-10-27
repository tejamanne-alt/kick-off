using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A zebra crossing with a pedestrian light. Green: cross. Amber: hurry.
    /// Red: traffic flows, and the kid or the ball on the road loses the ball.
    /// Brake and wait for green!
    /// </summary>
    [RequireComponent(typeof(BoxCollider2D))]
    public class Crossing : HazardBase
    {
        public enum Light { Green, Amber, Red }

        public float greenTime = 3.5f;
        public float amberTime = 1.2f;
        public float redTime = 3f;
        [Tooltip("Seconds into the cycle at level start, to vary crossings.")]
        public float phaseOffset;

        [Header("Visuals")]
        public SpriteRenderer greenLamp;
        public SpriteRenderer amberLamp;
        public SpriteRenderer redLamp;
        [Tooltip("Car that drives across while the light is red.")]
        public Transform car;
        public float carTravel = 8f;
        public Color lampOff = new Color(0.2f, 0.2f, 0.2f);

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
            if (greenLamp != null) greenLamp.color = Current == Light.Green ? new Color(0.3f, 1f, 0.4f) : lampOff;
            if (amberLamp != null) amberLamp.color = Current == Light.Amber ? new Color(1f, 0.75f, 0.2f) : lampOff;
            if (redLamp != null) redLamp.color = Current == Light.Red ? new Color(1f, 0.3f, 0.25f) : lampOff;

            if (car != null)
            {
                bool driving = Current == Light.Red;
                car.gameObject.SetActive(driving);
                if (driving)
                {
                    float c = Mathf.Repeat(time, CycleLength) - greenTime - amberTime;
                    float k = Mathf.Clamp01(c / redTime);
                    Vector3 p = car.localPosition;
                    p.x = Mathf.Lerp(carTravel * 0.5f, -carTravel * 0.5f, k);
                    car.localPosition = p;
                }
            }
        }

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
