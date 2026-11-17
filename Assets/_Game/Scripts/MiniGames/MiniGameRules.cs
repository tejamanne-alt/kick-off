using UnityEngine;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// The ride (docs/CITIES.md M1; KM1-2 Ride the Enoden): tap the IC card in time at the gate, keep the ball steady at your
    /// feet against the car's sway (lean with the stick, hold KICK through a hard brake), give your seat to the grandmother who
    /// boards at Yuigahama, and press STOP when the next-stop display says Kamakura. Kept apart from the overlay, so the
    /// rules are tested without a scene.
    /// </summary>
    public static class RideRules
    {
        /// <summary>The three stops the car makes, in order; the kid gets off at the last (Kamakura, the end of the line).</summary>
        public static readonly string[] Stations = { "yuigahama", "wadazuka", "kamakura" };
        public const int Destination = 2;
        /// <summary>Where the grandmother boards (a seat to give up there).</summary>
        public const int GrandmaBoards = 0;

        /// <summary>The card reader's ring closes over this many seconds; a tap while it is in the green part opens the gate.</summary>
        public const float CardTime = 1.6f, CardGoodFrom = 0.6f, CardGoodTo = 0.95f;

        /// <summary>Seconds between two stops, the hard brake at the end of each, and the doors open at a stop.</summary>
        public const float Between = 8f, Brake = 1.6f, Dwell = 3.4f;

        /// <summary>The coins the ride can pay: steadiness, STOP at the right stop, the seat given up.</summary>
        public const int SteadyCoins = 5, StopCoins = 2, SeatCoins = 3;
        public const int PossibleCoins = SteadyCoins + StopCoins + SeatCoins;

        /// <summary>A tap on the card reader at <paramref name="progress"/> (0 when the ring starts closing, 1 when it has closed).</summary>
        public static bool CardTapGood(float progress)
        {
            return progress >= CardGoodFrom && progress <= CardGoodTo;
        }

        /// <summary>STOP pressed while the display shows the stop <paramref name="next"/>: the right one only for the destination.</summary>
        public static bool StopIsRight(int next)
        {
            return next == Destination;
        }

        /// <summary>The ball at the kid's feet: its offset in the steady zone (-1 to 1 is the zone's width), and its speed.</summary>
        public struct Ball
        {
            public float offset, velocity;
        }

        /// <summary>The car's sway at time <paramref name="t"/> into a stretch: two slow sways and a jolt, as an old tram rides.</summary>
        public static float Sway(float t)
        {
            return 0.9f * Mathf.Sin(t * 1.3f) + 0.45f * Mathf.Sin(t * 2.9f + 1.1f) + (Mathf.Repeat(t, 3.7f) < 0.15f ? 1.2f : 0f);
        }

        /// <summary>
        /// One step of the ball against the sway: the car pushes it by <paramref name="sway"/> (and forward hard while it
        /// brakes), the kid leans against it with the stick (<paramref name="lean"/>, -1 to 1) and steadies it under the foot
        /// with KICK held (most of a brake's push taken out); it settles back slowly by itself.
        /// </summary>
        public static void Step(ref Ball ball, float sway, float lean, bool braking, bool kickHeld, float dt)
        {
            float push = sway * 1.6f + (braking ? 4.2f * (kickHeld ? 0.15f : 1f) : 0f);
            float accel = push - Mathf.Clamp(lean, -1f, 1f) * 3.2f - ball.offset * 1.4f - ball.velocity * 1.8f;
            ball.velocity += accel * dt;
            ball.offset += ball.velocity * dt;
            if (Mathf.Abs(ball.offset) > 1.2f)
            {
                ball.offset = Mathf.Sign(ball.offset) * 1.2f;
                ball.velocity = 0f;
            }
        }

        /// <summary>The ball counts as steady while it stays in the middle half of the zone.</summary>
        public static bool Steady(Ball ball)
        {
            return Mathf.Abs(ball.offset) <= 0.5f;
        }

        /// <summary>The steadiness coins for the share of the ride the ball stayed steady (all of them from 90 % up, none under 40 %).</summary>
        public static int SteadyPay(float steadyShare)
        {
            return Mathf.RoundToInt(SteadyCoins * Mathf.Clamp01((steadyShare - 0.4f) / 0.5f));
        }
    }

    /// <summary>
    /// The errand (docs/CITIES.md M2; KM2-3 Grandma's Whitebait Shop): Grandma shows the order of the furoshiki's four corners,
    /// the kid folds them in that order (a wrong corner and she shows it again: never a fail), then ties the knot in two timed
    /// taps. The near and far corners come first, then the two side corners that are tied, as a real furoshiki is wrapped.
    /// </summary>
    public static class ErrandRules
    {
        public enum Corner { Near, Far, Left, Right }

        /// <summary>The knot's marker sweeps across and back in this many seconds; a tap with it in the gold part is a good pull.</summary>
        public const float KnotPeriod = 1.5f, KnotFrom = 0.4f, KnotTo = 0.6f;
        public const int KnotPulls = 2;
        public const int PossibleCoins = 6;

        /// <summary>The order Grandma shows (from <paramref name="seed"/>): near and far in either order, then left and right in either order.</summary>
        public static Corner[] Order(int seed)
        {
            var rng = new System.Random(seed);
            bool farFirst = rng.Next(2) == 1, rightFirst = rng.Next(2) == 1;
            return new[]
            {
                farFirst ? Corner.Far : Corner.Near, farFirst ? Corner.Near : Corner.Far,
                rightFirst ? Corner.Right : Corner.Left, rightFirst ? Corner.Left : Corner.Right,
            };
        }

        /// <summary>A fold of <paramref name="tapped"/> at step <paramref name="step"/> of <paramref name="order"/> is right.</summary>
        public static bool FoldIsRight(Corner[] order, int step, Corner tapped)
        {
            return order != null && step >= 0 && step < order.Length && order[step] == tapped;
        }

        /// <summary>The knot's marker (0 to 1 and back) <paramref name="t"/> seconds after it starts.</summary>
        public static float KnotMarker(float t)
        {
            return Mathf.PingPong(t * 2f / KnotPeriod, 1f);
        }

        /// <summary>A tap with the marker at <paramref name="marker"/> pulls the knot tight.</summary>
        public static bool PullIsGood(float marker)
        {
            return marker >= KnotFrom && marker <= KnotTo;
        }

        /// <summary>The coins for the wrapping: all of them for no wrong corner and no missed pull, one fewer for each, at least one.</summary>
        public static int Pay(int wrongFolds, int missedPulls)
        {
            return Mathf.Clamp(PossibleCoins - wrongFolds - missedPulls, 1, PossibleCoins);
        }
    }

    /// <summary>
    /// Drop and come back (docs/CITIES.md M4; KM2-4 The Kite Thief): a black kite snatches the rice ball off the bento and drops
    /// it on the rocks behind; the kid has a few seconds to dribble back to it before the wave covers it.
    /// </summary>
    public static class KiteRules
    {
        /// <summary>The seconds before the wave covers the rice ball <paramref name="distance"/> metres back: time to turn and run there, and some.</summary>
        public static float TimeToGetBack(float distance)
        {
            return 3.5f + Mathf.Abs(distance) / 2.4f;
        }

        /// <summary>The kid is close enough to pick the rice ball up.</summary>
        public static bool Reached(float kidX, float riceX)
        {
            return Mathf.Abs(kidX - riceX) <= 0.9f;
        }

        /// <summary>The coins for the rice ball saved (a bonus; none if the wave took it).</summary>
        public const int SavedCoins = 4;
    }
}
