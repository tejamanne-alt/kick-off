using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A loose flock of birds crossing the sky (gulls over the beach, pigeons over the town): they
    /// come in from beyond one side of the view, glide across in an untidy line (each bird beating
    /// its wings in bursts, then gliding, drifting up and down and closing and opening the gaps)
    /// and fly out the other side. After a pause another crossing begins, from either side, at its
    /// own height and depth, wherever the camera is by then, so there are always birds about.
    /// </summary>
    public class SkyFlock : AmbientAgent
    {
        [Tooltip("The birds' flying models (head toward +x), each with its two wings in Wings.")]
        public Transform[] birds = new Transform[0];
        [Tooltip("Two per bird: the wing flapped with a negative angle, then its mirror.")]
        public Part[] wings = new Part[0];
        [Tooltip("A real bird's beat in the bursts (WingStroke, D21): raised wingUp, beaten wingDown, folded wingFold at the " +
                 "wrist and swept wingSweep back on the upstroke about wingSweepAxis. wingFold and wingSweep 0: the original " +
                 "kit's even beat.")]
        public float wingUp = 40f, wingDown = 40f, wingFold, wingSweep;
        public Vector3 wingSweepAxis = Vector3.up;
        [Tooltip("Depths the flock (every bird in it) keeps between.")]
        public float zMin = 1f, zMax = 3f;
        [Tooltip("Heights in the view: 0 is the view's middle, 1 its top edge.")]
        public float heightMin = 0.5f, heightMax = 0.8f;
        public float speedMin = 3.5f, speedMax = 6f;
        [Tooltip("Seconds between one crossing and the next.")]
        public float gapMin = 3f, gapMax = 12f;
        [Tooltip("Bird size, for how far apart they fly.")]
        public float spacing = 1.2f;

        bool flying;
        float until, dir, speed, cx, cy, cz, started;
        int count;
        Vector3[] offsets = new Vector3[0];
        float[] phases = new float[0], flapUntil = new float[0], flapAngle = new float[0], yaws = new float[0];
        float[] wingNow = new float[0], flapNow = new float[0], foldNow = new float[0], sweepNow = new float[0];
        bool[] flapping = new bool[0];

        protected override float Reach { get { return 100000f; } }   // tied to the view: never rests

        protected override void Awake()
        {
            base.Awake();
            Capture(wings);
            count = birds.Length;
            offsets = new Vector3[count];
            phases = new float[count];
            flapUntil = new float[count];
            flapAngle = new float[count];
            yaws = new float[count];
            flapping = new bool[count];
            wingNow = new float[count];
            foldNow = new float[count];
            flapNow = new float[count];
            sweepNow = new float[count];
            Show(false);
            until = Time.time + Range(0.5f, gapMax * 0.5f);
        }

        void Show(bool on)
        {
            for (int i = 0; i < birds.Length; i++)
                if (birds[i] != null && birds[i].gameObject.activeSelf != on) birds[i].gameObject.SetActive(on);
        }

        protected override void Tick(float dt)
        {
            if (!flying)
            {
                if (Time.time >= until) Begin();
                return;
            }
            float t = Time.time - started;
            cx += dir * speed * dt;
            cy += Mathf.Sin(t * 0.35f + seed) * 0.25f * dt;
            float span = spacing * (count + 1);
            float halfW = AmbientView.HalfWidthAt(cz), camX = AmbientView.CameraX;
            // Done once the whole flock is past the far side (or the view has jumped away from it).
            float trailing = cx - dir * span;
            bool past = dir > 0f ? trailing > camX + halfW + 3f : trailing < camX - halfW - 3f;
            bool lost = Mathf.Abs(cx - camX) > halfW + span + 40f;
            if (past || lost)
            {
                flying = false;
                Show(false);
                until = Time.time + Range(gapMin, gapMax);
                return;
            }
            for (int i = 0; i < count; i++)
            {
                var b = birds[i];
                if (b == null) continue;
                float ph = phases[i];
                // Each bird drifts about its place in the line.
                Vector3 o = offsets[i];
                float bx = cx + o.x + Mathf.Sin(t * 0.5f + ph) * spacing * 0.5f;
                float by = cy + o.y + Mathf.Sin(t * 0.8f + ph * 1.3f) * 0.35f;
                float bz = Mathf.Clamp(cz + o.z + Mathf.Sin(t * 0.3f + ph * 0.7f) * 0.6f, zMin, zMax);
                float climb = Mathf.Cos(t * 0.8f + ph * 1.3f) * 0.8f * 0.35f;   // d(by)/dt
                b.position = new Vector3(bx, by, bz);
                yaws[i] = Mathf.MoveTowardsAngle(yaws[i], (dir > 0f ? 0f : 180f) + Mathf.Sin(t * 0.4f + ph) * 8f, 60f * dt);
                b.rotation = Quaternion.Euler(Mathf.Sin(t * 0.6f + ph) * 10f, yaws[i], Mathf.Clamp(climb * 20f, -12f, 12f));

                // Wings: a burst of beats, then a glide with the wings held a little up.
                if (Time.time >= flapUntil[i])
                {
                    flapping[i] = !flapping[i];
                    flapUntil[i] = Time.time + (flapping[i] ? Range(0.8f, 2f) : Range(1f, 3f));
                    // Pick the beat up from where the wings are, so they never jump.
                    if (flapping[i]) flapAngle[i] = Mathf.Asin(Mathf.Clamp(wingNow[i] / 36f, -1f, 1f));
                }
                if (flapping[i])
                {
                    flapAngle[i] += dt * 11f;
                    wingNow[i] = Mathf.Sin(flapAngle[i]) * 36f;
                }
                else wingNow[i] = Mathf.MoveTowards(wingNow[i], 8f + Mathf.Sin(t * 1.5f + ph) * 4f, 90f * dt);
                int w = i * 2;
                if (wingFold > 0f || wingSweep > 0f)
                {
                    // spread down, folded and swept back up; in a glide spread, a little swept, eased in and out of it
                    // its own state (wingNow is the even beat's): spread in the glide at the even beat's hold
                    float fl = wingNow[i], fo = 0f, sw = 0.3f * wingSweep;
                    if (flapping[i])
                    {
                        Vector4 st = WingStroke.At(flapAngle[i], wingUp, wingDown, wingFold, wingSweep);
                        fl = st.x; fo = st.y; sw = st.z;
                    }
                    flapNow[i] = Mathf.MoveTowards(flapNow[i], fl, 900f * dt);
                    foldNow[i] = Mathf.MoveTowards(foldNow[i], fo, 900f * dt);
                    sweepNow[i] = Mathf.MoveTowards(sweepNow[i], sw, 400f * dt);
                    if (w + 1 < wings.Length)
                    {
                        wings[w].SetWing(-flapNow[i], -foldNow[i], -sweepNow[i], wingSweepAxis);
                        wings[w + 1].SetWing(flapNow[i], foldNow[i], sweepNow[i], wingSweepAxis);
                    }
                }
                else if (w + 1 < wings.Length)
                {
                    float a = wingNow[i];
                    wings[w].Set(-a);
                    wings[w + 1].Set(a);
                }
            }
        }

        void Begin()
        {
            if (!AmbientView.Valid || count == 0)
            {
                until = Time.time + 1f;
                return;
            }
            flying = true;
            started = Time.time;
            dir = Chance(0.5f) ? 1f : -1f;
            speed = Range(speedMin, speedMax);
            cz = Range(zMin, zMax);
            float halfW = AmbientView.HalfWidthAt(cz);
            // In from just beyond the near side, heading across.
            cx = AmbientView.CameraX - dir * (halfW + 2f);
            cy = AmbientView.CenterYAt(cz) + AmbientView.HalfHeightAt(cz) * Range(heightMin, heightMax);
            for (int i = 0; i < count; i++)
            {
                // A loose, uneven line trailing back from the leader.
                offsets[i] = new Vector3(-dir * (i * spacing * Range(0.7f, 1.4f)), Range(-0.5f, 0.5f) * spacing, Range(-1.2f, 1.2f));
                phases[i] = Range(0f, 6.3f);
                flapping[i] = Chance(0.5f);
                flapUntil[i] = Time.time + Range(0.2f, 1.5f);
                flapAngle[i] = Range(0f, 6f);
                yaws[i] = dir > 0f ? 0f : 180f;
            }
            Show(true);
            Tick(0f);
        }
    }
}
