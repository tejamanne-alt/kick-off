using DribbleToSchool.Hazards;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Stroll animation for pedestrians and the company they keep: the stride follows their
    /// walking speed (easing into a stop and out of it), older walkers stoop a little, and when
    /// they stop they do something: read their phone, look in a shop window, chat with a friend
    /// (hands going, nodding), or wait at the kerb shifting their weight. A dog walker keeps the
    /// lead hand steady.
    /// </summary>
    [RequireComponent(typeof(CharacterRig))]
    public class WalkerAnimator : MonoBehaviour
    {
        public Pedestrian pedestrian;
        [Tooltip("This is the friend or child walking along with the pedestrian, not the pedestrian.")]
        public bool companion;
        [Tooltip("Stride rate: a child's shorter legs go quicker.")]
        public float cadence = 1f;
        public float swing = 25f;

        CharacterRig rig;
        float phase, gestureWeight, offset;
        Pedestrian.Gesture shown;

        void Awake()
        {
            rig = GetComponent<CharacterRig>();
            offset = Random.value * 10f;
        }

        void LateUpdate()
        {
            float dt = Time.deltaTime;
            float speed = pedestrian == null ? 1f : companion ? pedestrian.CompanionSpeed : pedestrian.Speed;
            var wanted = pedestrian == null ? Pedestrian.Gesture.None : companion ? pedestrian.CompanionGesture : pedestrian.CurrentGesture;
            float stoop = pedestrian != null && !companion ? pedestrian.Stoop : 0f;

            // The stride grows and quickens with speed, and settles as they stop.
            float amp = Mathf.Clamp01(speed / 0.9f);
            if (stoop > 0f) amp *= 0.8f;
            phase += dt * (speed * 4.8f + (speed > 0.05f ? 0.5f : 0f)) * cadence;
            float s = Mathf.Sin(phase);
            var p = RigPose.Neutral;
            p.bob = Mathf.Abs(Mathf.Cos(phase)) * 0.03f * amp;
            p.legF = s * swing * amp;
            p.legB = -s * swing * amp;
            p.armF = -s * swing * 0.7f * amp;
            p.armB = s * swing * 0.7f * amp;
            // A gentle stroll: knees lift a little in the swing, elbows stay soft.
            p.kneeF = Mathf.Lerp(-4f, -Knee(phase), amp);
            p.kneeB = Mathf.Lerp(-4f, -Knee(phase + Mathf.PI), amp);
            p.elbowF = 12f + (4f + 12f * Mathf.Max(0f, -s)) * amp;
            p.elbowB = 12f + (4f + 12f * Mathf.Max(0f, s)) * amp;
            p.lean = 2f * amp + stoop;
            if (stoop > 0f) p.headTilt = stoop * 0.4f;   // looking up a little from the stoop

            if (!companion && pedestrian != null && pedestrian.HoldsLead)
            {
                // The hand on the dog's side (the far one) holds the lead out a little, steady.
                bool frontFar = rig.armFront != null && rig.armBack != null && rig.armFront.position.z > rig.armBack.position.z;
                if (frontFar) { p.armF = 14f + s * 3f; p.elbowF = 34f; }
                else { p.armB = 14f + s * 3f; p.elbowB = 34f; }
            }

            // What they do when they stop, blended in (and out before the next one).
            if (wanted != shown)
            {
                gestureWeight = Mathf.MoveTowards(gestureWeight, 0f, dt * 3f);
                if (gestureWeight <= 0f) shown = wanted;
            }
            else gestureWeight = Mathf.MoveTowards(gestureWeight, shown == Pedestrian.Gesture.None ? 0f : 1f, dt * 2.5f);
            if (gestureWeight > 0f) Perform(ref p, shown, Ease(gestureWeight));
            rig.Pose(p);
        }

        void Perform(ref RigPose p, Pedestrian.Gesture g, float w)
        {
            float t = Time.time + offset;
            switch (g)
            {
                case Pedestrian.Gesture.Phone:
                    // Phone held up in front, head bowed over it; a thumb's twitch now and then.
                    p.armF = Mathf.Lerp(p.armF, 26f, w);
                    p.elbowF = Mathf.Lerp(p.elbowF, 118f + Mathf.Sin(t * 3.1f) * 3f, w);
                    p.armB = Mathf.Lerp(p.armB, 4f, w);
                    p.headTilt = Mathf.Lerp(p.headTilt, -16f, w);
                    break;
                case Pedestrian.Gesture.Look:
                    // Window shopping: head up a touch, weight shifting, a hand at the chin now and then.
                    float chin = Mathf.Max(0f, Mathf.Sin(t * 0.31f));
                    p.headTilt = Mathf.Lerp(p.headTilt, 5f + Mathf.Sin(t * 0.5f) * 4f, w);
                    p.armF = Mathf.Lerp(p.armF, 18f * chin, w);
                    p.elbowF = Mathf.Lerp(p.elbowF, 12f + 110f * chin, w);
                    p.lean = Mathf.Lerp(p.lean, 1f + Mathf.Sin(t * 0.7f), w);
                    break;
                case Pedestrian.Gesture.Chat:
                    // Talking: hands going, nodding along.
                    p.armF = Mathf.Lerp(p.armF, 10f + Mathf.Sin(t * 1.3f) * 9f, w);
                    p.elbowF = Mathf.Lerp(p.elbowF, 40f + 30f * Mathf.Max(0f, Mathf.Sin(t * 2.2f)), w);
                    p.armB = Mathf.Lerp(p.armB, 4f + Mathf.Sin(t * 0.9f + 1f) * 5f, w);
                    p.elbowB = Mathf.Lerp(p.elbowB, 20f + 18f * Mathf.Max(0f, Mathf.Sin(t * 1.7f + 2f)), w);
                    p.headTilt = Mathf.Lerp(p.headTilt, Mathf.Sin(t * 1.9f) * 6f, w);
                    break;
                case Pedestrian.Gesture.Wait:
                    // At the kerb: standing easy, a little sway.
                    p.lean = Mathf.Lerp(p.lean, Mathf.Sin(t * 0.6f) * 1.5f, w);
                    p.headTilt = Mathf.Lerp(p.headTilt, Mathf.Sin(t * 0.4f) * 4f, w);
                    break;
            }
        }

        static float Ease(float t) { return t * t * (3f - 2f * t); }

        static float Knee(float legPhase)
        {
            float swing = Mathf.Max(0f, Mathf.Cos(legPhase + 0.9f));
            return 5f + 35f * swing * swing;
        }
    }
}
