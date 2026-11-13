using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// A butterfly (Animals kit) flitting about a garden or the park lawn: it flies on a wandering,
    /// curving path (its heading drifts and swerves), bobbing up and down with its wingbeats, now and
    /// then hanging in the air a moment, and always turning back before it strays far from its patch
    /// or out over the footpath.
    /// </summary>
    public class FlitButterfly : AmbientAgent
    {
        public Part wingL, wingR;
        [Tooltip("Optional: hind wings that beat apart from the forewings (a dragonfly's), hindLead radians ahead of them.")]
        public Part hindL, hindR;
        public float hindLead = 1.6f;
        public float homeX, homeY, homeZ;
        [Tooltip("How far it wanders from home along the street, and in height.")]
        public float roam = 2.5f, rise = 0.6f;
        [Tooltip("Depths it keeps between (clear of the footpath, in front of the hedges or walls).")]
        public float zMin = 2.3f, zMax = 3.6f;
        public float speed = 0.7f;
        [Tooltip("The wingbeat, degrees: beatMid + beatSwing sin. A butterfly claps its wings from flat to 76 up (38, 38); " +
                 "a dragonfly beats them about flat (4, 24). The asset review renders the same (tools/blender/asset_review.py fly).")]
        public float beatMid = 38f, beatSwing = 38f;

        float x, y, z, heading, turn, turnTarget, nextSwerve;
        float flap, hover, nextHover, climb;
        float yaw, yawVelocity;

        protected override float Reach { get { return roam + 1f; } }

        protected override void Awake()
        {
            base.Awake();
            wingL.Capture();
            wingR.Capture();
            hindL.Capture();
            hindR.Capture();
            x = homeX + Range(-roam, roam) * 0.5f;
            y = homeY;
            z = Mathf.Clamp(homeZ, zMin, zMax);
            heading = Range(0f, Mathf.PI * 2f);
            flap = Range(0f, 10f);
            nextHover = Time.time + Range(3f, 8f);
            yaw = YawToward(Mathf.Cos(heading), Mathf.Sin(heading));
        }

        protected override void Tick(float dt)
        {
            // The heading drifts on a turn rate that swerves every so often: loops and S-bends.
            if (Time.time >= nextSwerve)
            {
                turnTarget = Range(-2.4f, 2.4f);
                nextSwerve = Time.time + Range(0.4f, 1.6f);
            }
            // Pulled back toward home (and between its depths) when it strays.
            float hx = homeX - x, hz = (homeZ - z) * 0.3f;
            float stray = Mathf.Abs(hx) / Mathf.Max(0.5f, roam);
            if (stray > 0.7f || z < zMin + 0.15f || z > zMax - 0.15f)
            {
                float want = Mathf.Atan2(z < zMin + 0.15f ? 1f : z > zMax - 0.15f ? -1f : hz, hx);
                float diff = Mathf.DeltaAngle(heading * Mathf.Rad2Deg, want * Mathf.Rad2Deg) * Mathf.Deg2Rad;
                turnTarget = Mathf.Clamp(diff * 3f, -3f, 3f);
            }
            turn = Mathf.MoveTowards(turn, turnTarget, 6f * dt);
            heading += turn * dt;

            // Hang in the air a moment now and then.
            if (Time.time >= nextHover)
            {
                hover = Range(0.6f, 1.6f);
                nextHover = Time.time + hover + Range(3f, 9f);
            }
            hover -= dt;
            float pace = hover > 0f ? 0.15f : 1f;

            float v = speed * pace;
            x += Mathf.Cos(heading) * v * dt;
            z += Mathf.Sin(heading) * v * dt;
            z = Mathf.Clamp(z, zMin, zMax);
            // Rise and fall: a slow drift between the heights plus a flutter with each beat.
            climb = Mathf.MoveTowards(climb, Mathf.Sin(Time.time * 0.37f + seed) * rise, 0.4f * dt);
            flap += dt * (hover > 0f ? 30f : 50f);
            y = homeY + climb + Mathf.Sin(flap * 0.5f) * 0.04f;

            float wantYaw = YawToward(Mathf.Cos(heading), Mathf.Sin(heading));
            yaw = Mathf.SmoothDampAngle(yaw, wantYaw, ref yawVelocity, 0.12f);
            // Banking into its turns, the body pitching a little with each beat.
            transform.SetPositionAndRotation(new Vector3(x, y, z), Quaternion.Euler(Mathf.Clamp(-turn * 7f, -16f, 16f), yaw, Mathf.Sin(flap * 0.5f) * 5f));
            // Wings: a butterfly's from flat to 76 degrees up, fast; a dragonfly's about flat (beatMid, beatSwing).
            float beat = beatMid + beatSwing * Mathf.Sin(flap);
            wingL.Set(beat);
            wingR.Set(-beat);
            // a dragonfly's hind wings lead its forewings, so its four wings never move as one (D21)
            float hind = beatMid + beatSwing * Mathf.Sin(flap + hindLead);
            hindL.Set(hind);
            hindR.Set(-hind);
        }
    }
}
