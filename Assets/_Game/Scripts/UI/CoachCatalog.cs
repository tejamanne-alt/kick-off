using UnityEngine;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// What the coach at the top of the HUD (<see cref="ActionCoach"/>) can say: a how-to for each special action in the
    /// levels (the ids the level builder gives its ActionSpots, Editor/CoachPlan) and the steps of the challenges (keepy-uppy,
    /// targets, the slalom), each with the Controls page's picture of the control it uses and two strings,
    /// coach.&lt;id&gt;.title (short: it is all the coach shows once the move is learned) and coach.&lt;id&gt;.text.
    /// </summary>
    public static class CoachCatalog
    {
        public struct Entry
        {
            public readonly string id;
            public readonly ControlsGuide.Picture picture;

            public Entry(string id, ControlsGuide.Picture picture)
            {
                this.id = id;
                this.picture = picture;
            }

            public string TitleKey { get { return "coach." + id + ".title"; } }
            public string TextKey { get { return "coach." + id + ".text"; } }
        }

        /// <summary>The levels' special actions (ActionSpot.action).</summary>
        public static readonly Entry[] Actions =
        {
            new Entry("slide", ControlsGuide.Picture.Slide),
            new Entry("kerb", ControlsGuide.Picture.Jump),
            new Entry("stepup", ControlsGuide.Picture.Kick),
            new Entry("chip", ControlsGuide.Picture.Kick),
            new Entry("chiphigh", ControlsGuide.Picture.Kick),
            new Entry("gap", ControlsGuide.Picture.Kick),
            new Entry("gapdouble", ControlsGuide.Picture.Jump),
            new Entry("crates", ControlsGuide.Picture.Kick),
            new Entry("car", ControlsGuide.Picture.Kick),
            new Entry("highwall", ControlsGuide.Picture.Kick),
            new Entry("springboard", ControlsGuide.Picture.Walk),
            new Entry("bounce", ControlsGuide.Picture.Walk),
            new Entry("platform", ControlsGuide.Picture.Kick),
            new Entry("lift", ControlsGuide.Picture.Kick),
            new Entry("swing", ControlsGuide.Picture.Jump),
            new Entry("gate", ControlsGuide.Picture.Kick),
            new Entry("crossing", ControlsGuide.Picture.Wait),
            new Entry("siteexit", ControlsGuide.Picture.Wait),
            new Entry("tide", ControlsGuide.Picture.Wait),
            new Entry("dog", ControlsGuide.Picture.Kick),
            new Entry("people", ControlsGuide.Picture.Kick),
            new Entry("seagull", ControlsGuide.Picture.Walk),
            new Entry("fountain", ControlsGuide.Picture.Walk),
            // the Florida add-on's own (LevelBuildKit.FloridaPlay)
            new Entry("drawbridge", ControlsGuide.Picture.Wait),
            new Entry("sprinkler", ControlsGuide.Picture.Walk),
            new Entry("golfcart", ControlsGuide.Picture.Jump),
        };

        /// <summary>The challenges' steps: what to do now, shown all the way through a challenge.</summary>
        public static readonly Entry[] Steps =
        {
            new Entry("juggle1", ControlsGuide.Picture.Kick),
            new Entry("juggle2", ControlsGuide.Picture.Touch),
            new Entry("jugglemove", ControlsGuide.Picture.Walk),
            new Entry("jugglefetch", ControlsGuide.Picture.Walk),
            new Entry("aim", ControlsGuide.Picture.Kick),
            new Entry("targetfetch", ControlsGuide.Picture.Walk),
            new Entry("low", ControlsGuide.Picture.Walk),
            new Entry("hoop", ControlsGuide.Picture.Kick),
            new Entry("finish", ControlsGuide.Picture.Slide),
        };

        /// <summary>The entry for <paramref name="id"/> (an action or a step), or false if there is none.</summary>
        public static bool TryFind(string id, out Entry entry)
        {
            foreach (var e in Actions) if (e.id == id) { entry = e; return true; }
            foreach (var e in Steps) if (e.id == id) { entry = e; return true; }
            entry = default(Entry);
            return false;
        }

        /// <summary>How far to the side of the kid's feet (world units) the coach still says "tap" rather than "get under it".</summary>
        public const float JuggleUnder = 1.2f;

        /// <summary>
        /// The keepy-uppy step for where the ball is: in the air near the kid, tap (juggle2); in the air off to the side, get
        /// under it; on the ground at the feet, pop it up from KICK (juggle1); on the ground further away, fetch it.
        /// </summary>
        public static string JuggleStep(bool ballGrounded, Vector2 offsetFromFeet, bool inKickReach)
        {
            if (!ballGrounded) return Mathf.Abs(offsetFromFeet.x) <= JuggleUnder ? "juggle2" : "jugglemove";
            return inKickReach ? "juggle1" : "jugglefetch";
        }

        /// <summary>The targets' step: aim and kick when the ball is at the feet, else fetch it.</summary>
        public static string TargetStep(bool inKickReach) { return inKickReach ? "aim" : "targetfetch"; }

        /// <summary>The slalom's step for the next gate still to pass (none left: slide under the boardwalk to the finish).</summary>
        public static string SlalomStep(bool hasNextGate, bool nextIsHoop)
        {
            if (!hasNextGate) return "finish";
            return nextIsHoop ? "hoop" : "low";
        }

        /// <summary>The picture for a first-time tip (tut.&lt;id&gt;), where one of the controls fits it.</summary>
        public static bool HintPicture(string hintId, out ControlsGuide.Picture picture)
        {
            switch (hintId)
            {
                case "dribble": case "brake": case "puddle": case "tunnel": picture = ControlsGuide.Picture.Walk; return true;
                case "jump": case "doublejump": picture = ControlsGuide.Picture.Jump; return true;
                case "kick": case "gate": case "dog": case "pedestrian": case "platform": case "swing": picture = ControlsGuide.Picture.Kick; return true;
                case "juggle": picture = ControlsGuide.Picture.Touch; return true;
                case "slide": picture = ControlsGuide.Picture.Slide; return true;
                case "crossing": case "siteexit": case "tide": picture = ControlsGuide.Picture.Wait; return true;
                default: picture = ControlsGuide.Picture.Walk; return false;
            }
        }
    }
}
