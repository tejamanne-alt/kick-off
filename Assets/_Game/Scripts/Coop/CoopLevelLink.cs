using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Presentation;
using UnityEngine;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// Hooks one leg's scene up to the co-op race (added by Coop/CoopService as the scene loads, before anything in it has
    /// started): the countdown is short (and the first leg's waits for the shared GO, Core/ILevelRace), the other players
    /// appear as ghosts (Coop/CoopGhost), the race's HUD goes over the level's (Coop/CoopHud), and this phone's kid is
    /// reported to the session every frame (the session sends it ten times a second). The ghosts' kids are copied from the
    /// level's own models of those kids now, while they still stand in their rest pose.
    /// </summary>
    public class CoopLevelLink : MonoBehaviour
    {
        public static CoopLevelLink Current { get; private set; }

        /// <summary>How far behind the kid's lane each ghost runs (a lane each, toward the houses, inside the footpath).</summary>
        static readonly float[] Lanes = { 0.12f, 0.22f, 0.32f };
        /// <summary>Ghosts are drawn this far in the past, so there is always a sample after the moment drawn.</summary>
        public const double InterpolationDelayMs = 160;

        CoopService service;
        CoopRaceMode race;
        LevelManager level;
        readonly Dictionary<uint, CoopGhost> ghosts = new Dictionary<uint, CoopGhost>();
        readonly Dictionary<string, GameObject> templates = new Dictionary<string, GameObject>();
        // Where each kid's model stands under the kid (each kid's feet are placed for their own height).
        readonly Dictionary<string, Pose> placements = new Dictionary<string, Pose>();
        Transform ghostRoot;
        GameObject ballShell;
        bool reportedLoaded;

        /// <summary>Where this leg starts (the kid's spawn at home or the stop) and where its goal is, along the street.</summary>
        public float StartX { get; private set; }
        public float StartY { get; private set; }
        public float GoalX { get; private set; }
        public float LegLength { get { return Mathf.Max(10f, GoalX - StartX); } }
        public LevelManager Level { get { return level; } }
        /// <summary>(the collection itself, not an IEnumerable: walked every frame by the HUD without allocating)</summary>
        public Dictionary<uint, CoopGhost>.ValueCollection Ghosts { get { return ghosts.Values; } }

        public void Attach(CoopService service, CoopRaceMode race, LevelManager level)
        {
            this.service = service;
            this.race = race;
            this.level = level;
            Current = this;

            // The first leg waits for GO (the race's hold) and then goes at once; later legs flash GO.
            level.introDuration = race.Leg == 0 ? 0.05f : 0.3f;

            Checkpoint start = null;
            foreach (var cp in level.checkpoints) if (cp != null && cp.isStart) { start = cp; break; }
            if (start == null && level.checkpoints.Count > 0) start = level.checkpoints[0];
            Vector2 spawn = start != null ? start.KidSpawnPosition : (Vector2)level.kid.transform.position;
            StartX = spawn.x;
            StartY = spawn.y;
            var goal = FindAnyObjectByType<GoalZone>();
            GoalX = goal != null ? goal.transform.position.x : StartX + 150f;

            // (under this object, which is in the leg's scene: they go when the scene goes)
            ghostRoot = new GameObject("CoopGhosts").transform;
            ghostRoot.SetParent(transform, false);
            PrepareTemplates();
            var players = service.Session.Players;
            for (int i = 0; i < players.Count; i++) if (players[i].uid != service.Session.Uid) Ghost(players[i]);

            var hudObject = new GameObject("CoopHud");
            hudObject.transform.SetParent(transform, false);
            hudObject.AddComponent<CoopHud>().Attach(service, race, this);
        }

        void OnDestroy()
        {
            if (Current == this) Current = null;
            foreach (var t in templates.Values) if (t != null) Destroy(t);
        }

        /// <summary>
        /// A copy of the model of every kid the others play (and of the ball's mesh), kept out of sight, taken before the
        /// level's animation first poses its kid: each ghost is copied from these, whenever it is made. (Only the kids in
        /// the race: copying the whole roster at every leg would cost a hitch and memory for nothing. A kid nobody had when
        /// the leg loaded, a latecomer's, borrows one of these.)
        /// </summary>
        void PrepareTemplates()
        {
            var store = new GameObject("GhostTemplates");
            store.SetActive(false);
            store.transform.SetParent(ghostRoot, false);
            var wanted = new HashSet<string>();
            var players = service.Session.Players;
            for (int i = 0; i < players.Count; i++)
                if (players[i].uid != service.Session.Uid) wanted.Add(CoopProfile.CharacterId(players[i].character));
            var choice = level.kid.GetComponent<CharacterChoice>();
            if (choice != null && choice.characters != null && choice.ids != null)
            {
                for (int i = 0; i < choice.characters.Length && i < choice.ids.Length; i++)
                {
                    var source = choice.characters[i];
                    if (source == null) continue;
                    // (the first kid is always kept, so a latecomer has someone to borrow)
                    if (!wanted.Contains(choice.ids[i]) && templates.Count > 0) continue;
                    placements[choice.ids[i]] = new Pose(source.transform.localPosition, source.transform.localRotation);
                    var copy = Instantiate(source, store.transform);
                    copy.SetActive(true);
                    templates[choice.ids[i]] = copy;
                }
            }
            else
            {
                // A level with one kid only: everyone's ghost is that kid.
                var rig = level.kid.GetComponentInChildren<CharacterRig>(true);
                var visual = rig != null && rig.transform.parent != null ? rig.transform.parent.gameObject : null;
                if (visual != null)
                {
                    placements[""] = new Pose(visual.transform.localPosition, visual.transform.localRotation);
                    var copy = Instantiate(visual, store.transform);
                    copy.SetActive(true);
                    templates[""] = copy;
                }
            }
            var shell = level.ball.transform.Find("SquashRoot/Ball3D");
            if (shell != null)
            {
                ballShell = Instantiate(shell.gameObject, store.transform);
                ballShell.transform.localScale = shell.lossyScale;
            }
        }

        /// <summary>The copy of a kid's model to make a ghost from (any kid's, if that one is missing), and where it stands.</summary>
        GameObject TemplateFor(string characterId, out Pose placement)
        {
            GameObject t;
            if (templates.TryGetValue(characterId, out t)) { placement = placements[characterId]; return t; }
            foreach (var kv in templates) { placement = placements[kv.Key]; return kv.Value; }
            placement = new Pose(Vector3.zero, Quaternion.identity);
            return null;
        }

        CoopGhost Ghost(CoopPlayer p)
        {
            CoopGhost ghost;
            if (ghosts.TryGetValue(p.uid, out ghost)) return ghost;
            var go = new GameObject("Ghost P" + (p.slot + 1));
            go.transform.SetParent(ghostRoot, false);
            ghost = go.AddComponent<CoopGhost>();
            ghost.uid = p.uid;
            ghost.slot = p.slot;
            int lane = LaneOf(p);
            Pose placement;
            var template = TemplateFor(CoopProfile.CharacterId(p.character), out placement);
            ghost.Build(template, placement.position, placement.rotation, ballShell, CoopPalette.Of(p.slot), Lanes[lane], level.kid.RunSpeed);
            ghosts[p.uid] = ghost;
            return ghost;
        }

        /// <summary>The other players' lanes, in slot order (this phone's kid has the front one).</summary>
        int LaneOf(CoopPlayer p)
        {
            int lane = 0;
            foreach (var other in service.Session.Players)
                if (other.uid != service.Session.Uid && other.slot < p.slot) lane++;
            return Mathf.Clamp(lane, 0, Lanes.Length - 1);
        }

        void Update()
        {
            var session = service.Session;
            if (!reportedLoaded && race.Leg == 0)
            {
                reportedLoaded = true;
                session.ReportLoaded(race.RaceId);
            }

            // This phone's kid, for the others' ghosts.
            var kid = level.kid;
            if (level.State != LevelState.Complete && session.RaceStarted)
            {
                Vector2 k = kid.transform.position;
                Vector2 b = level.ball.transform.position;
                var v = kid.Body != null ? kid.Body.linearVelocity : Vector2.zero;
                int flags = CoopMotion.InPlay;
                if (kid.IsGrounded) flags |= CoopMotion.Grounded;
                if (kid.IsLow) flags |= CoopMotion.Low;
                if (kid.Facing >= 0) flags |= CoopMotion.FacingRight;
                session.ReportMotion(new CoopMotion
                {
                    x = k.x, y = k.y, vx = v.x, vy = v.y,
                    ballDx = b.x - k.x, ballDy = b.y - k.y,
                    flags = (byte)flags,
                    progress = race.Progress((k.x - StartX) / LegLength),
                });
            }

            // The others, a moment in the past. (Real time: the race doesn't stop for this phone's pause menu.)
            double t = session.RaceTimeMs - InterpolationDelayMs;
            float dt = Time.unscaledDeltaTime;
            var players = session.Players;
            for (int i = 0; i < players.Count; i++)
            {
                var p = players[i];
                if (p.uid == session.Uid) continue;
                var ghost = Ghost(p);
                var m = new CoopMotion();
                bool have = p.track.Count > 0 && p.track.Sample(t, out m);
                bool here = have && m.leg == race.Leg && p.status == PlayerStatus.Racing && session.RaceStarted
                    && t - p.track.Latest.raceMs < 3000;   // nothing heard for a while: don't leave a statue standing
                ghost.Show(m, here, dt);
            }
            // (a player no longer in the lobby leaves no ghost behind)
            foreach (var kv in ghosts)
                if (session.Find(kv.Key) == null) kv.Value.Show(new CoopMotion(), false, dt);
        }
    }
}
