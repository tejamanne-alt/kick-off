using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Tutorial
{
    /// <summary>
    /// The first time the kid reaches this spot, the HUD shows a short hint card
    /// for the mechanic introduced here. Each hint shows once per player.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class TutorialHint : MonoBehaviour
    {
        [Tooltip("Hint id; text key is tut.<id>.")]
        public string hintId = "dribble";

        /// <summary>Every hint id used by the levels (for resetting).</summary>
        public static readonly string[] AllIds =
        {
            "dribble", "brake", "jump", "kick", "juggle", "gate", "puddle", "pedestrian", "crossing", "springboard",
            "tide", "seagull", "tunnel", "pipes", "platform", "dog", "fountain", "swing", "slide", "doublejump",
        };

        /// <summary>Raised with the hint id when a hint should be displayed.</summary>
        public static event System.Action<string> Shown;

        static string Key(string id) { return "tutorial.seen." + id; }

        public static bool Seen(string id) { return PlayerPrefs.GetInt(Key(id), 0) == 1; }

        /// <summary>Forget all hints (Settings > Reset progress).</summary>
        public static void ResetAll(System.Collections.Generic.IEnumerable<string> ids)
        {
            foreach (var id in ids) PlayerPrefs.DeleteKey(Key(id));
        }

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (other.attachedRigidbody == null || other.attachedRigidbody.GetComponent<KidController>() == null) return;
            if (Seen(hintId)) return;
            PlayerPrefs.SetInt(Key(hintId), 1);
            PlayerPrefs.Save();
            if (Shown != null) Shown(hintId);
        }
    }
}
