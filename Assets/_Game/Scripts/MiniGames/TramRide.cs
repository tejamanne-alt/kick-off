using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// KM1-2 Ride the Enoden's ride (docs/CITIES.md M1): where the kid reaches Hase's ticket gate, the ride opens over the level
    /// (<see cref="RideOverlay"/>); when the car reaches Kamakura, the leg is done (the kid gets off at the stop).
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class TramRide : MonoBehaviour, IResettable
    {
        bool started;

        void OnTriggerEnter2D(Collider2D other)
        {
            if (started) return;
            var body = other.attachedRigidbody;
            if (body == null || body.GetComponent<KidController>() == null) return;
            var level = LevelManager.Current;
            if (level == null || level.State != LevelState.Playing) return;
            started = true;
            var ride = gameObject.AddComponent<RideOverlay>();
            ride.Finished = done =>
            {
                if (level != null) level.ReachGoal();
            };
        }

        public void ResetState()
        {
            started = false;
            var open = GetComponent<RideOverlay>();
            if (open != null) Destroy(open);
        }
    }
}
