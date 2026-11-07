using DribbleToSchool.Core;
using DribbleToSchool.InputHandling;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// A way out if the kid is ever wedged somewhere: when the player has been trying to move (the stick pushed, or the kid
    /// low under something) for a few seconds without getting anywhere, a button comes up, "Stuck? Back to the checkpoint",
    /// that sends the kid back to the last checkpoint (where what lies ahead is put back as the level built it). It goes again
    /// as soon as the kid moves on. GameHud and the Holiday Run's HUD each make one.
    /// </summary>
    public class StuckHelper : MonoBehaviour
    {
        [Tooltip("Seconds of trying without getting anywhere before the button comes up.")]
        public float after = 5f;
        [Tooltip("How far (m) the kid has to get to count as moving on.")]
        public float distance = 0.75f;

        LevelManager level;
        KidController kid;
        System.Action rescue;
        GameObject button;
        RectTransform buttonRect;
        float anchorX, stuckFor;
        readonly Vector3[] corners = new Vector3[4];

        /// <summary>True while the button is up (the coach keeps out of its way on a narrow screen).</summary>
        public bool Showing { get { return button != null && button.activeSelf; } }

        /// <summary>Builds the (hidden) button under <paramref name="root"/>; <paramref name="rescue"/> is what it does (back to the checkpoint).</summary>
        public static StuckHelper Create(RectTransform root, LevelManager level, KidController kid, System.Action rescue)
        {
            var holder = UIKit.Rect(root, "StuckHelper");
            UIKit.Place(holder, new Vector2(0.5f, 1f), new Vector2(0f, -200f), new Vector2(640f, 100f), new Vector2(0.5f, 1f));
            var helper = holder.gameObject.AddComponent<StuckHelper>();
            helper.level = level;
            helper.kid = kid;
            helper.rescue = rescue;
            var b = UIKit.GlassButton(holder, "Button", Loc.T("hud.stuck"), UITheme.Accent, helper.Rescue, 34);
            UIKit.Stretch((RectTransform)b.transform);
            b.gameObject.AddComponent<UIPulse>().amount = 0.04f;
            helper.button = b.gameObject;
            helper.buttonRect = (RectTransform)b.transform;
            helper.button.SetActive(false);
            return helper;
        }

        void Rescue()
        {
            stuckFor = 0f;
            if (kid != null) anchorX = kid.transform.position.x;
            button.SetActive(false);
            if (rescue != null) rescue();
        }

        void Update()
        {
            if (level == null || kid == null || button == null) return;
            float x = kid.transform.position.x;
            bool playing = level.State == LevelState.Playing && !level.Held;
            if (!playing || Mathf.Abs(x - anchorX) > distance)
            {
                anchorX = x;
                stuckFor = 0f;
            }
            else
            {
                var input = GameInput.Instance;
                bool trying = (input != null && Mathf.Abs(input.MoveAxis) > 0.1f) || kid.IsLow;
                if (trying) stuckFor += Time.deltaTime;
            }
            bool show = playing && stuckFor > after;
            if (button.activeSelf != show)
            {
                button.SetActive(show);
                if (show)
                {
                    var pop = button.GetComponent<UIPopIn>();
                    if (pop == null) pop = UIKit.PopIn(button);
                    pop.Play();
                }
            }
        }

        void LateUpdate()
        {
            // A tap on the button is the button's, not a touch in the game.
            if (button == null || !button.activeInHierarchy) return;
            buttonRect.GetWorldCorners(corners);   // overlay canvas: world space == screen pixels
            GameInput.UIBlockers.Add(Rect.MinMaxRect(corners[0].x, corners[0].y, corners[2].x, corners[2].y));
        }
    }
}
