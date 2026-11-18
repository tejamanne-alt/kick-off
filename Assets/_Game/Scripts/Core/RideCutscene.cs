using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// A ride between two legs of a route (Levels/Rides: Florida's people mover), played by itself: the car glides along its
    /// guideway with the camera beside it, the city slides past, and after <see cref="duration"/> seconds (or Skip) the next leg
    /// loads where the ride arrives. The trip's clock doesn't run during it. Built by Editor/RideBuilder; nothing in it takes
    /// input but Skip. Opened without a leg to go on to (from the editor), it ends on the map.
    /// </summary>
    public class RideCutscene : MonoBehaviour
    {
        static string nextScene;

        /// <summary>The scene to load when the ride ends (LevelManager.LoadNextLevel sets it before loading the ride).</summary>
        public static void Then(string scene) { nextScene = scene; }

        [Tooltip("The car, moved along x from startX to endX over the ride.")]
        public Transform car;
        public float startX = -10f, endX = 160f;
        [Tooltip("The camera, kept beside the car at this offset.")]
        public Transform cameraRig;
        public Vector3 cameraOffset = new Vector3(2.5f, 1.2f, -14f);
        [Tooltip("Things that turn as the ride goes (the car's wheels, a boat's wake): spun about their own x.")]
        public Transform[] spinners;
        public float duration = Levels.Rides.Seconds;
        [Tooltip("The ride's id (Levels/Rides), for the line its card shows.")]
        public string ride = Levels.Rides.PeopleMover;

        float time;
        bool leaving;

        void Start()
        {
            TimeControl.ResetTime();
            BuildCard();
            Place(0f);
        }

        void Update()
        {
            if (leaving) return;
            time += Time.deltaTime;
            float t = Mathf.Clamp01(time / Mathf.Max(1f, duration));
            Place(t);
            if (t >= 1f) Leave();
        }

        /// <summary>The car and the camera at <paramref name="t"/> (0 to 1) of the ride: eased away from the station and into the next.</summary>
        void Place(float t)
        {
            float eased = t * t * (3f - 2f * t);
            float x = Mathf.Lerp(startX, endX, eased);
            if (car != null) car.position = new Vector3(x, car.position.y, car.position.z);
            if (cameraRig != null && car != null) cameraRig.position = car.position + cameraOffset;
            if (spinners != null)
                foreach (var s in spinners)
                    if (s != null) s.localRotation = Quaternion.Euler(x * 90f, 0f, 0f);
        }

        void BuildCard()
        {
            var canvas = UIKit.CreateCanvas("RideCanvas", 10);
            var card = UIKit.Glass(canvas.transform, "Card");
            UIKit.Place((RectTransform)card.transform.parent, new Vector2(0.5f, 1f), new Vector2(0f, -70f), new Vector2(900f, 110f));
            var line = UIKit.GlassText(UIKit.Label(card.transform, "Line", Loc.T(Levels.Rides.NameKey(ride)), 40, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
            UIKit.Stretch(line.rectTransform, 12f);
            var skip = UIKit.GlassButton(canvas.transform, "Skip", Loc.T("ride.skip"), UITheme.Accent, Leave);
            UIKit.Place((RectTransform)skip.transform, new Vector2(1f, 0f), new Vector2(-170f, 90f), new Vector2(260f, 110f));
        }

        void Leave()
        {
            if (leaving) return;
            leaving = true;
            string scene = nextScene;
            nextScene = null;
            if (!string.IsNullOrEmpty(scene) && Application.CanStreamedLevelBeLoaded(scene)) SceneManager.LoadScene(scene);
            else FrontEnd.FrontEndController.Open(FrontEnd.FrontEndScreenId.Map, Levels.RouteTable.FloridaChapter);
        }
    }
}
