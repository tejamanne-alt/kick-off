using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// KM2-3 Grandma's Whitebait Shop's errand (docs/CITIES.md M2): where the kid reaches Grandma's counter, the errand opens
    /// over the level (<see cref="ErrandOverlay"/>); once the bento is wrapped it rides on the backpack
    /// (Progression/Errands) and the kid goes on along the promenade.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class BentoErrand : MonoBehaviour, IResettable
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
            var errand = gameObject.AddComponent<ErrandOverlay>();
            errand.Finished = done =>
            {
                Errands.Wrapped(SaveSystem.Data);
                SaveSystem.Save();
                BentoOnBack.ShowAll();
            };
        }

        public void ResetState()
        {
            started = false;
            var open = GetComponent<ErrandOverlay>();
            if (open != null) Destroy(open);
        }
    }
}
