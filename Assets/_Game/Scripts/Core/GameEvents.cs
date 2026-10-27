using System;
using UnityEngine;

namespace DribbleToSchool.Core
{
    public enum GameEventType
    {
        Kick, Touch, PerfectTouch, Juggle, Trap,
        Jump, Land, BallBounce,
        BallLost, Respawn, Checkpoint, Bell, Goal, LevelStart,
        Coin, Sticker,
        PedestrianBump, DogSteal, SeagullHit, Springboard, SwitchPressed, GateOpened, Splash, LightChange,
        UIClick, Purchase,
    }

    /// <summary>
    /// One hub for "something happened at this spot". Gameplay raises events;
    /// audio, particles, haptics and analytics listen. Keeps hazards free of
    /// presentation code.
    /// </summary>
    public static class GameEvents
    {
        /// <summary>Type, world position, and an intensity (0..1, e.g. kick power or impact speed).</summary>
        public static event Action<GameEventType, Vector2, float> Raised;

        public static void Raise(GameEventType type, Vector2 position, float intensity = 1f)
        {
            if (Raised != null) Raised(type, position, Mathf.Clamp01(intensity));
        }
    }
}
