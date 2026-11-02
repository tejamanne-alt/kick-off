using System;
using System.Collections.Generic;
using DribbleToSchool.Tuning;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// How far and how high the kid really gets, worked out from the numbers that move them (PlayerTuning,
    /// the Physics2D gravity, the fixed time step, the trampoline's launch speed), and the limits the Holiday
    /// Run's gaps and walls are held to. Pure arithmetic: no Unity objects are touched, so the level builders,
    /// the pattern harness and the edit-mode tests all use it, and a retuned jump moves the limits (or fails
    /// <c>JumpReachTests</c>) instead of silently making a trench impossible.
    ///
    /// The flights replay <c>KidController</c> one fixed step at a time: the take-off sets the upward speed, the
    /// physics step then adds gravity (stronger once falling) and moves the body, and the air jump is a second
    /// "set the upward speed" in mid-air. Horizontal speed is held in the air (airControl lets the kid keep it).
    /// At the defaults and 4.2 m/s a single jump flies 2.3 m and peaks 1.30 m up; a double jump pressed at the
    /// top flies 3.6 m and peaks 2.07 m up.
    ///
    /// The SAFE limits are what a level may ask of a player, not what an expert can just manage: they leave room
    /// for the take-off being a little early, the second press being a little off the top, and the feet box and
    /// the 0.1 s coyote time at the edges. They are for the WALKING speed; the turbo (x1.35) only adds reach.
    /// </summary>
    public static class JumpReach
    {
        /// <summary>The numbers a flight depends on. <see cref="Defaults"/> mirrors PlayerTuning's defaults; <see cref="From"/> reads an asset.</summary>
        public struct Motion
        {
            /// <summary>Magnitude of Physics2D.gravity.y (m/s squared).</summary>
            public float gravity;
            /// <summary>Time.fixedDeltaTime (s): the game's physics step, TimeControl.BaseFixedDeltaTime (1/60).</summary>
            public float step;
            public float gravityScale, fallGravityMultiplier;
            public float jumpVelocity, airJumpVelocity;
            public int airJumps;
            public float coyoteTime;
            /// <summary>Walking speed (m/s): what the levels are designed for.</summary>
            public float runSpeed;
            public float slideDuration, slideSpeedBoost, slideFriction, slideMinSpeed, slideHeight;
            /// <summary>Hazards.Springboard.kidLaunchSpeed (m/s).</summary>
            public float springboardSpeed;
            /// <summary>The kid's capsule (m).</summary>
            public float bodyWidth, bodyHeight;
        }

        /// <summary>PlayerTuning's defaults, the engine's default gravity and step, and the trampoline's launch.</summary>
        public static readonly Motion Defaults = new Motion
        {
            gravity = 9.81f,
            step = 1f / 60f,
            gravityScale = 3f,
            fallGravityMultiplier = 1.4f,
            jumpVelocity = 9f,
            airJumpVelocity = 7f,
            airJumps = 1,
            coyoteTime = 0.1f,
            runSpeed = 4.2f,
            slideDuration = 0.7f,
            slideSpeedBoost = 1.3f,
            slideFriction = 3.5f,
            slideMinSpeed = 2.2f,
            slideHeight = 0.5f,
            springboardSpeed = 13f,
            bodyWidth = 0.5f,
            bodyHeight = 1.2f,
        };

        /// <summary>The motion a PlayerTuning asset gives (the rest as in <see cref="Defaults"/>).</summary>
        public static Motion From(PlayerTuning t)
        {
            Motion m = Defaults;
            m.gravityScale = t.gravityScale;
            m.fallGravityMultiplier = t.fallGravityMultiplier;
            m.jumpVelocity = t.jumpVelocity;
            m.airJumpVelocity = t.airJumpVelocity;
            m.airJumps = t.airJumps;
            m.coyoteTime = t.coyoteTime;
            m.runSpeed = t.runSpeed;
            m.slideDuration = t.slideDuration;
            m.slideSpeedBoost = t.slideSpeedBoost;
            m.slideFriction = t.slideFriction;
            m.slideMinSpeed = t.slideMinSpeed;
            m.slideHeight = t.slideHeight;
            return m;
        }

        // ----------------------------------------------------------------------------------------------- flights

        /// <summary>One flight from the ground to the ground: how long, how far along (at the speed asked), how high, and when the top was.</summary>
        public struct Flight
        {
            public float time, distance, apex, apexTime;
        }

        public enum JumpKind
        {
            /// <summary>One jump.</summary>
            Single,
            /// <summary>A jump and the air jump pressed at the top of it (the best height).</summary>
            Double,
            /// <summary>A jump and the air jump pressed as late as the game allows (the longest flight, but low).</summary>
            LongestDouble,
            /// <summary>Thrown by a trampoline.</summary>
            Spring,
            /// <summary>Thrown by a trampoline, and the air jump (which a trampoline gives back) pressed at the top.</summary>
            SpringDouble,
        }

        const int MaxSteps = 600;

        /// <summary>
        /// Replays a flight from y = 0 with upward speed <paramref name="vy0"/>. Each of <paramref name="jumps"/> air jumps is
        /// pressed at the first step where the upward speed is below <paramref name="pressBelow"/> (and below the air jump's own
        /// speed, as KidController demands), or, when <paramref name="pressAfter"/> is not negative, at the first step at least
        /// that many seconds in. The path (x along, y up of the feet) is added to <paramref name="path"/> if given.
        /// </summary>
        static Flight Fly(Motion m, float speed, float vy0, int jumps, float pressBelow, float pressAfter, List<float> pathX, List<float> pathY)
        {
            float y = 0f, vy = vy0, t = 0f, apex = 0f, apexTime = 0f;
            int used = 0;
            bool first = true;
            if (pathX != null) { pathX.Add(0f); pathY.Add(0f); }
            for (int i = 0; i < MaxSteps; i++)
            {
                if (!first && used < jumps && vy < m.airJumpVelocity)
                {
                    bool press = pressAfter >= 0f ? t >= pressAfter : vy < pressBelow;
                    if (press) { vy = m.airJumpVelocity; used++; }
                }
                first = false;
                float g = (vy < 0f ? m.gravityScale * m.fallGravityMultiplier : m.gravityScale) * m.gravity;
                vy -= g * m.step;
                float ny = y + vy * m.step;
                if (ny <= 0f && vy < 0f)
                {
                    float f = y / Math.Max(1e-6f, y - ny);
                    t += m.step * f;
                    if (pathX != null) { pathX.Add(speed * t); pathY.Add(0f); }
                    y = 0f;
                    break;
                }
                y = ny;
                t += m.step;
                if (y > apex) { apex = y; apexTime = t; }
                if (pathX != null) { pathX.Add(speed * t); pathY.Add(y); }
            }
            return new Flight { time = t, distance = speed * t, apex = apex, apexTime = apexTime };
        }

        static Flight Fly(Motion m, float speed, JumpKind kind, List<float> pathX, List<float> pathY)
        {
            switch (kind)
            {
                case JumpKind.Single: return Fly(m, speed, m.jumpVelocity, 0, 0f, -1f, pathX, pathY);
                case JumpKind.Double: return Fly(m, speed, m.jumpVelocity, m.airJumps, 0f, -1f, pathX, pathY);
                // 0.5 s in: the kid is falling and about to land; the game turns a press any closer into an ordinary jump on landing.
                case JumpKind.LongestDouble: return Fly(m, speed, m.jumpVelocity, m.airJumps, 0f, 0.5f, pathX, pathY);
                case JumpKind.Spring: return Fly(m, speed, m.springboardSpeed, 0, 0f, -1f, pathX, pathY);
                default: return Fly(m, speed, m.springboardSpeed, m.airJumps, 0f, -1f, pathX, pathY);
            }
        }

        /// <summary>A flight of the given kind at <paramref name="speed"/> over flat ground.</summary>
        public static Flight Of(Motion m, float speed, JumpKind kind)
        {
            return Fly(m, speed, kind, null, null);
        }

        /// <summary>A single jump at the walking speed: 2.3 m long, 1.30 m high at the defaults.</summary>
        public static Flight SingleJump(Motion m) { return Of(m, m.runSpeed, JumpKind.Single); }

        /// <summary>A double jump pressed at the top, at the walking speed: 3.6 m long, 2.07 m high at the defaults.</summary>
        public static Flight DoubleJump(Motion m) { return Of(m, m.runSpeed, JumpKind.Double); }

        /// <summary>The longest flight there is with the walking speed (an expert, a late second press): about 4.1 m, but low.</summary>
        public static Flight LongestJump(Motion m) { return Of(m, m.runSpeed, JumpKind.LongestDouble); }

        /// <summary>A trampoline throw at the walking speed, the air jump left unused.</summary>
        public static Flight SpringThrow(Motion m) { return Of(m, m.runSpeed, JumpKind.Spring); }

        /// <summary>The path of a flight, feet height against distance along, at <paramref name="count"/> evenly spaced points (not the ends).</summary>
        public static void Path(Motion m, float speed, JumpKind kind, int count, out float[] xs, out float[] ys)
        {
            var px = new List<float>();
            var py = new List<float>();
            Flight f = Fly(m, speed, kind, px, py);
            xs = new float[count];
            ys = new float[count];
            for (int i = 0; i < count; i++)
            {
                float x = f.distance * (i + 1) / (count + 1);
                xs[i] = x;
                ys[i] = HeightAt(px, py, x);
            }
        }

        static float HeightAt(List<float> px, List<float> py, float x)
        {
            for (int i = 1; i < px.Count; i++)
            {
                if (px[i] < x) continue;
                float span = px[i] - px[i - 1];
                float k = span <= 1e-6f ? 0f : (x - px[i - 1]) / span;
                return py[i - 1] + (py[i] - py[i - 1]) * k;
            }
            return 0f;
        }

        // ----------------------------------------------------------------------------------------------- slide

        /// <summary>How far the slide itself carries the kid (m): it starts at the boost speed, loses speed to friction, and lasts <c>slideDuration</c>.</summary>
        public static float SlideDistance(Motion m)
        {
            float v = m.runSpeed * m.slideSpeedBoost, dist = 0f;
            for (float t = 0f; t < m.slideDuration - 1e-4f; t += m.step)
            {
                v = Math.Max(m.slideMinSpeed, v - m.slideFriction * m.step);
                dist += v * m.step;
            }
            return dist;
        }

        /// <summary>
        /// The longest barrier to slide under (m along the street): the slide's own distance plus about a second of the low
        /// shuffle the kid keeps up at <c>slideMinSpeed</c> while something is still overhead. (A longer one is no trap, only slow.)
        /// </summary>
        public static float MaxSlideBarrier(Motion m)
        {
            return SlideDistance(m) + m.slideMinSpeed * 0.7f;
        }

        /// <summary>The least clear height under a barrier to slide under: the sliding body and room to spare.</summary>
        public static float MinSlideClearance(Motion m) { return m.slideHeight + 0.3f; }

        // ----------------------------------------------------------------------------------------------- the safe limits

        /// <summary>How much of a single jump's flight a plain gap must leave unused (an early take-off, the feet box at the edge).</summary>
        public const float PlainSlack = 0.30f;
        /// <summary>The same for a gap crossed with a double jump (the second press is off the top as well).</summary>
        public const float WideSlack = 0.42f;

        /// <summary>Ground a gap needs clear before it (run-up and room to kick the ball across) and after it (landing and room to collect the ball).</summary>
        public const float RunUp = 6f, Landing = 4f;

        static float FloorTo(float v, float q) { return (float)Math.Floor(v / q + 1e-3f) * q; }
        static float RoundTo(float v, float q) { return (float)Math.Round(v / q) * q; }

        /// <summary>The widest plain gap (a single jump): 2.0 m at the defaults.</summary>
        public static float SafePlainGap(Motion m) { return FloorTo(SingleJump(m).distance - PlainSlack, 0.1f); }

        /// <summary>The widest wide gap (a double jump): 3.2 m at the defaults. The ball can be chipped over this (a chip carries 3 to 6 m).</summary>
        public static float SafeWideGap(Motion m) { return FloorTo(DoubleJump(m).distance - WideSlack, 0.1f); }

        /// <summary>The narrowest gap worth calling wide, clearly past what one jump asks: 2.6 m at the defaults.</summary>
        public static float MinWideGap(Motion m) { return RoundTo(SafePlainGap(m) * 1.3f, 0.1f); }

        /// <summary>A plain gap is made 1.4 to 1.9 m wide.</summary>
        public static float ComfortablePlainMin(Motion m) { return RoundTo(SafePlainGap(m) * 0.7f, 0.1f); }
        public static float ComfortablePlainMax(Motion m) { return SafePlainGap(m) - 0.1f; }
        /// <summary>A wide gap is made 2.7 to 3.1 m wide.</summary>
        public static float ComfortableWideMin(Motion m) { return MinWideGap(m) + 0.1f; }
        public static float ComfortableWideMax(Motion m) { return SafeWideGap(m) - 0.1f; }

        /// <summary>How far the kid runs on after leaving the edge while the coyote time still lets them jump (m): 0.42 at the defaults.</summary>
        public static float CoyoteRun(Motion m) { return m.coyoteTime * m.runSpeed; }

        /// <summary>The highest low thing (kerb, step, border): 0.5 m.</summary>
        public static float SafeLowWall(Motion m) { return FloorTo(SingleJump(m).apex * 0.4f, 0.05f); }

        /// <summary>The highest mid thing a single jump gets over or onto, with room to spare: 1.0 m.</summary>
        public static float SafeMidWall(Motion m) { return FloorTo(SingleJump(m).apex - 0.28f, 0.05f); }

        /// <summary>The highest tall thing, which wants a double jump: 1.7 m (the double jump peaks 2.07 m up).</summary>
        public static float SafeTallWall(Motion m) { return FloorTo(DoubleJump(m).apex - 0.34f, 0.05f); }

        /// <summary>Nothing the kid has to get over is higher than this: 1.8 m. (Parked cars, 1.55 m, are climbed in two hops.)</summary>
        public static float MaxWall(Motion m) { return SafeTallWall(m) + 0.1f; }

        /// <summary>The highest wall the BALL can be asked to go over without a kick: the mid limit. Taller ones are chipped.</summary>
        public static float MaxWallWithoutKick(Motion m) { return SafeMidWall(m); }

        /// <summary>The highest a coin may hang and still be reached (by the head of a kid at the top of a double jump): 3.5 m.</summary>
        public static float HighestCoin(Motion m) { return DoubleJump(m).apex + m.bodyHeight + 0.28f; }

        /// <summary>The ceiling a double jump needs clear above the ground: the head of a kid at the top of it.</summary>
        public static float DoubleJumpHeadroom(Motion m) { return DoubleJump(m).apex + m.bodyHeight; }

        /// <summary>The ceiling a trampoline throw with the air jump needs clear above the ground.</summary>
        public static float SpringHeadroom(Motion m) { return Of(m, m.runSpeed, JumpKind.SpringDouble).apex + m.bodyHeight; }

        /// <summary>Where the kid is thrown from, relative to the pad's middle (the capsule touches the pad's trigger a little before it).</summary>
        public const float SpringLaunchOffset = -0.8f;

        /// <summary>The ground a trampoline's throw needs clear after the pad's middle: the longest throw (with the air jump) and a metre to land and settle.</summary>
        public static float SpringLanding(Motion m)
        {
            return SpringLaunchOffset + Of(m, m.runSpeed, JumpKind.SpringDouble).distance + 1f;
        }
    }
}
