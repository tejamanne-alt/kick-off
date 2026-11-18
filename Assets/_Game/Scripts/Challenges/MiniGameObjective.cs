using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// A leg of a route played as a mini-game instead of a street (docs/CITIES.md, "The mini-games: five systems, skinned per
    /// city"): the bus ride (M1, BusRide), the errand for a relative (M2, MooringLine), shopping for classwork (M3,
    /// DrugstoreShopping). It is short, played with the game's own controls, retried at once if it isn't passed, and its time
    /// counts in the trip to school like a street leg's (LevelManager.CompleteLeg). The score is the stars it earned: one for
    /// doing it, a second and a third for doing it well (<see cref="StarText"/> says how), 0 when it wasn't done.
    /// </summary>
    public abstract class MiniGameObjective : ChallengeObjective
    {
        public override bool IsRouteLeg { get { return true; } }

        int stars;
        public override int Score { get { return stars; } }

        /// <summary>The score on the results card: "2 of 3".</summary>
        public override string FormatScore(int score) { return Loc.F("mini.score", score); }

        /// <summary>What the <paramref name="star"/>-th star (1 to 3) is for, as the guide and the results list it.</summary>
        public abstract string StarText(int star);

        /// <summary>The string-table key of the line the HUD shows under the level's name while it runs.</summary>
        protected string status = "";
        public override string StatusText { get { return status; } }

        protected LevelManager Level { get { return LevelManager.Current; } }

        /// <summary>True while the leg is being played (not paused, held by a guide or the tour, or over).</summary>
        protected bool Running
        {
            get
            {
                var level = Level;
                return !Finished && level != null && level.State == LevelState.Playing && !level.Held;
            }
        }

        /// <summary>Done, with the stars it earned (1 to 3).</summary>
        protected void Pass(int earned)
        {
            stars = Mathf.Clamp(earned, 1, 3);
            Finish();
        }

        /// <summary>Not done (time ran out): the results offer Retry.</summary>
        protected void Fail()
        {
            stars = 0;
            Finish();
        }

        public override void ResetState()
        {
            base.ResetState();
            stars = 0;
            status = "";
        }

        // ------------------------------------------------------------------ the mini-game's own HUD (built from code, UIKit)

        Canvas hud;

        /// <summary>The mini-game's canvas over the level's HUD (built on first use).</summary>
        protected Canvas Hud
        {
            get
            {
                if (hud == null)
                {
                    hud = UIKit.CreateCanvas(name + "Hud", 6);
                    hud.transform.SetParent(transform, false);
                }
                return hud;
            }
        }

        /// <summary>The prompt across the top: what to do now (shown under the level's HUD card).</summary>
        protected Text Prompt
        {
            get
            {
                if (prompt == null)
                {
                    var card = UIKit.Glass(Hud.transform, "Prompt");
                    UIKit.Place((RectTransform)card.transform.parent, new Vector2(0.5f, 1f), new Vector2(0f, -250f), new Vector2(1100f, 96f));
                    prompt = UIKit.GlassText(UIKit.Label(card.transform, "Text", "", 38, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
                    UIKit.Stretch(prompt.rectTransform, 10f);
                    UIKit.Fit(prompt, 24);
                }
                return prompt;
            }
        }

        Text prompt;
        string promptKey;

        /// <summary>Show the prompt with this string's text (only rewritten when it changes).</summary>
        protected void Say(string key, params object[] args)
        {
            string text = args.Length > 0 ? Loc.F(key, args) : Loc.T(key);
            if (key == promptKey && Prompt.text == text) return;
            promptKey = key;
            Prompt.text = text;
            Prompt.transform.parent.parent.gameObject.SetActive(!string.IsNullOrEmpty(text));
        }

        /// <summary>A big glass button on the mini-game's canvas.</summary>
        protected Button BigButton(string name, string key, Vector2 anchor, Vector2 position, Vector2 size, Color colour, UnityEngine.Events.UnityAction onClick)
        {
            var button = UIKit.GlassButton(Hud.transform, name, Loc.T(key), colour, onClick, 44);
            UIKit.Place((RectTransform)button.transform, anchor, position, size);
            return button;
        }

        protected virtual void OnDestroy()
        {
            if (hud != null) Destroy(hud.gameObject);
        }
    }
}
