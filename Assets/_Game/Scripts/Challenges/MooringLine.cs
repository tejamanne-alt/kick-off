using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using UnityEngine;

namespace DribbleToSchool.Challenges
{
    /// <summary>
    /// M2, the errand (docs/CITIES.md), as Miami's "Throw the line" (FL2-2, Uncle Rey's Boat): his fishing boat drifts in to the
    /// dock, rising and falling on the river's chop. Throw the mooring line onto its cleats with KICK's drag-aim, the same as
    /// aiming a kick: the line's weighted end (a monkey's fist, the knot sailors throw) is the ball, and the line pays out from the
    /// bollard on the dock behind the kid. A throw that lands on a cleat makes that end fast; the line comes back to the kid
    /// after each throw, and one that falls in the river is pulled in (a lost ball, back at the dock). Two cleats tied, and the
    /// boat is warped in alongside: Uncle Rey hands over the science project (a model of the Everglades on a board), which rides
    /// on the backpack for the rest of the trip (Progression/Errands). Stars: the boat tied; in five throws or fewer; in two.
    /// </summary>
    public class MooringLine : MiniGameObjective
    {
        [Header("The boat (built by Editor/LevelBuildKit.FloridaCity)")]
        public Rigidbody2D boat;
        [Tooltip("The boat's cleats, bow and stern: a throw that touches one ties it.")]
        public ChallengeTarget[] cleats;
        [Tooltip("Where the boat drifts about (its x), how far either way, and where it lies once tied alongside.")]
        public float driftX = 15f, driftReach = 1.6f, tiedX = 11.4f;
        [Tooltip("The dock's end: past it, a throw that hit nothing comes back after a moment.")]
        public float dockEdgeX = 10f;
        [Tooltip("The bollard the line pays out from, and the line itself.")]
        public Transform bollard;
        public LineRenderer line;
        [Tooltip("The football's own look, hidden here: the ball is the line's knot.")]
        public Renderer ballLook;
        public GameObject knot;
        [Tooltip("The project Uncle Rey hands over, shown on the boat's cabin until then.")]
        public GameObject project;
        public string errand = Progression.Errands.ScienceProject;

        int throws, ties;
        bool tied, outThere;
        float tiedFor, outFor, time;
        Vector2 boatStart;
        BallController ball;

        public override string StarText(int star)
        {
            if (star == 1) return Loc.T("mini.line.star1");
            if (star == 2) return Loc.F("mini.line.star2", 5);
            return Loc.F("mini.line.star3", 2);
        }

        void Start()
        {
            if (boat != null) boatStart = boat.position;
            if (cleats != null) foreach (var c in cleats) if (c != null) c.Hit += OnCleat;
            var level = Level;
            ball = level != null ? level.ball : null;
            if (ball != null) ball.Kicked += OnThrow;
            if (ballLook != null) ballLook.enabled = false;
            if (knot != null) knot.SetActive(true);
        }

        protected override void OnDestroy()
        {
            base.OnDestroy();
            if (ball != null) ball.Kicked -= OnThrow;
            if (cleats != null) foreach (var c in cleats) if (c != null) c.Hit -= OnCleat;
        }

        public override void ResetState()
        {
            base.ResetState();
            throws = ties = 0;
            tied = outThere = false;
            tiedFor = outFor = time = 0f;
            if (boat != null && boatStart != Vector2.zero) boat.position = boatStart;
            if (project != null) project.SetActive(true);
        }

        void OnThrow()
        {
            if (!Running || tied) return;
            throws++;
            outThere = true;
            outFor = 0f;
        }

        void OnCleat(ChallengeTarget cleat)
        {
            if (tied) return;
            ties++;
            Say(ties >= 2 ? "mini.line.tied" : "mini.line.hit");
            if (ties >= 2) tied = true;
            Invoke("LineBack", 0.6f);
        }

        /// <summary>The line comes back to the kid's feet (pulled in) for the next throw.</summary>
        void LineBack()
        {
            outThere = false;
            var level = Level;
            if (level == null || level.ball == null || level.kid == null || Finished) return;
            level.ball.ResetTo(level.kid.FeetPosition + new Vector2(0.6f * level.kid.Facing, 0.3f));
        }

        protected override void Update()
        {
            base.Update();
            DrawLine();
            if (!Running) return;
            time += Time.deltaTime;
            if (!tied)
            {
                Say(throws == 0 ? "mini.line.aim" : "mini.line.again", 2 - ties);
                if (outThere)
                {
                    outFor += Time.deltaTime;
                    // A throw that came down on the boat or the dock past the edge and hit no cleat: pulled back in.
                    if (outFor > 2.6f && ball != null && ball.transform.position.x > dockEdgeX - 0.5f) LineBack();
                    else if (outFor > 4f) outThere = false;
                }
            }
            else
            {
                tiedFor += Time.deltaTime;
                Say(tiedFor < 2.2f ? "mini.line.tied" : "mini.line.project");
                if (tiedFor > 2.2f && project != null && project.activeSelf) project.SetActive(false);
                if (tiedFor > 3.6f)
                {
                    Progression.Errands.Pick(Progression.SaveSystem.Data, errand);
                    Pass(1 + (throws <= 5 ? 1 : 0) + (throws <= 2 ? 1 : 0));
                }
            }
        }

        void FixedUpdate()
        {
            if (boat == null) return;
            var level = Level;
            bool still = level == null || level.State == LevelState.Paused || level.Held;
            if (still) return;
            float t = time;
            // Adrift: in and out along the dock and up and down on the chop; tied, warped in alongside and only bobbing.
            float x = tied ? Mathf.MoveTowards(boat.position.x, tiedX, 1.5f * Time.fixedDeltaTime)
                           : driftX + driftReach * Mathf.Sin(t * 0.55f) + 0.4f * Mathf.Sin(t * 1.3f);
            float y = boatStart.y + 0.12f * Mathf.Sin(t * 1.7f);
            boat.MovePosition(new Vector2(x, y));
        }

        void DrawLine()
        {
            if (line == null || bollard == null || ball == null) return;
            Vector3 a = bollard.position, b = ball.transform.position;
            // A sag halfway along, less as it pulls tight.
            float sag = Mathf.Clamp(Vector3.Distance(a, b) * 0.08f, 0.05f, 0.6f);
            line.positionCount = 3;
            line.SetPosition(0, a);
            line.SetPosition(1, (a + b) * 0.5f + Vector3.down * sag);
            line.SetPosition(2, b);
        }
    }
}
