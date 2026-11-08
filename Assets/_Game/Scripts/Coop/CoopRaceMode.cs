using DribbleToSchool.Core;
using DribbleToSchool.FrontEnd;
using DribbleToSchool.Levels;
using DribbleToSchool.Progression;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Coop
{
    /// <summary>
    /// This phone's run in a co-op race: the whole route from the front door to the school gate, one leg (one level) after
    /// another, in the location the lobby chose. Every phone runs its own kid in its own copy of each leg; the session
    /// shares where everyone is. The first leg waits for the shared GO; each later leg loads as soon as the last one is done
    /// (its scene load is part of the race, as it is for everyone). At the school gate the time is taken from the shared race
    /// clock and the others carry on. As <see cref="ILevelRace"/> it is what the level and the HUD see
    /// (<see cref="LevelManager.Race"/>).
    /// </summary>
    public sealed class CoopRaceMode : ILevelRace
    {
        /// <summary>How long a stop's "Made it to the bus stop!" shows before the next leg loads.</summary>
        public const float StopPause = 1.3f;
        /// <summary>The coins added to what was collected, by place (1st, 2nd, 3rd, 4th); a run that doesn't count earns only its coins.</summary>
        public static readonly int[] PlaceBonus = { 40, 25, 15, 10 };

        readonly CoopService service;
        float nextLegAt = -1f;

        public CoopRaceMode(CoopService service)
        {
            this.service = service;
        }

        CoopSession Session { get { return service.Session; } }

        public byte RaceId { get; private set; }
        /// <summary>The route being raced (the stage), and its location (an add-on).</summary>
        public Route Route { get; private set; }
        public AddOn Location { get; private set; }
        /// <summary>The leg this phone is on (0 starts at home).</summary>
        public int Leg { get; private set; }
        public int LegCount { get { return Route != null ? Route.levels.Length : 1; } }
        /// <summary>This phone's kid got to school.</summary>
        public bool Finished { get; private set; }
        public uint FinishMs { get; private set; }
        /// <summary>The coins collected on every leg so far, and what the finish earned (coins and the place's bonus).</summary>
        public int Coins { get; private set; }
        public int CoinsEarned { get; private set; }
        /// <summary>Between two legs (the stop's message, then the next scene).</summary>
        public bool BetweenLegs { get { return nextLegAt >= 0f; } }
        /// <summary>Where the last leg ended ("the bus stop"), for the message between legs.</summary>
        public Stop ReachedStop { get; private set; }

        // ---------- ILevelRace ----------

        public bool HoldsIntro { get { return Leg == 0 && !Session.RaceStarted; } }

        public string IntroText
        {
            get
            {
                if (!HoldsIntro) return null;
                if (Session.Phase == SessionPhase.Loading || !Session.RaceClockKnown) return Localization.Loc.T("coop.waiting");
                int seconds = Mathf.CeilToInt((float)Session.CountdownMs / 1000f);
                return seconds > 0 ? seconds.ToString() : Localization.Loc.T("hud.go");
            }
        }

        public float RaceSeconds { get { return (float)System.Math.Max(0, Session.RaceTimeMs) / 1000f; } }

        public void LegFinished(LevelManager level)
        {
            Coins += level.CoinsCollected;
            if (Route == null) return;
            if (Leg + 1 < LegCount)
            {
                ReachedStop = RouteTable.To(Route.levels[Leg]);
                Session.ReportLeg(Leg + 1, (Leg + 1f) / LegCount);
                nextLegAt = Time.unscaledTime + StopPause;
                return;
            }
            // The school gate: the time is taken now, from the shared clock.
            if (Session.MyStatus == PlayerStatus.Racing)
            {
                FinishMs = Session.ReportFinished();
                Finished = true;
                Bank();
            }
            else Finished = true;   // (a run that no longer counts still gets to the gate)
        }

        public void Leave()
        {
            service.Leave();
            FrontEndController.Open(FrontEndScreenId.Coop);
        }

        // ---------- The race's course ----------

        /// <summary>The host started race <paramref name="raceId"/>: load its first leg.</summary>
        public void Begin(byte raceId, CoopSelection selection)
        {
            if (raceId == RaceId && Route != null) return;   // (a repeat: already on it)
            RaceId = raceId;
            Route = RouteTable.All[Mathf.Clamp(selection.route, 0, RouteTable.All.Length - 1)];
            Location = CoopLocations.At(selection.addOn);
            Leg = 0;
            Finished = false;
            FinishMs = 0;
            Coins = 0;
            CoinsEarned = 0;
            nextLegAt = -1f;
            ReachedStop = null;
            LevelManager.Race = this;
            LoadLeg(0);
        }

        public void Tick()
        {
            if (nextLegAt >= 0f && Time.unscaledTime >= nextLegAt)
            {
                nextLegAt = -1f;
                LoadLeg(Leg + 1);
            }
            // A phone that came back after the race moved on (it missed Loading): catch up with the race.
            if (Route == null && Session.InSession && (Session.Phase == SessionPhase.Loading || Session.Phase == SessionPhase.Racing)
                && Session.MyStatus == PlayerStatus.Racing && Session.RaceId != 0)
                Begin(Session.RaceId, Session.RaceSelection);
        }

        void LoadLeg(int leg)
        {
            Leg = Mathf.Clamp(leg, 0, LegCount - 1);
            var catalog = service.Catalog;
            var def = catalog != null ? catalog.FindById(Route.levels[Leg]) : null;
            if (def == null)
            {
                Debug.LogError("[Co-op] Level " + Route.levels[Leg] + " is not in the catalog.");
                return;
            }
            Session.ReportLeg(Leg, (float)Leg / LegCount);
            TimeControl.ResetTime();
            SceneManager.LoadScene(AddOns.SceneFor(def.sceneName, Location));
        }

        /// <summary>How far along the whole route the kid is: the legs behind, and this one's share.</summary>
        public float Progress(float legFraction)
        {
            return Mathf.Clamp01((Leg + Mathf.Clamp01(legFraction)) / Mathf.Max(1, LegCount));
        }

        /// <summary>Coins: what was collected, and the place's bonus. Saved once, at the gate.</summary>
        void Bank()
        {
            int place = 1;
            foreach (var p in Session.Players)
                if (p.uid != Session.Uid && p.status == PlayerStatus.Finished && p.finishMs < FinishMs) place++;
            CoinsEarned = Coins + PlaceBonus[Mathf.Clamp(place - 1, 0, PlaceBonus.Length - 1)];
            SaveSystem.AddCoins(CoinsEarned);
            var data = SaveSystem.Data;
            data.coopRaces++;
            if (place == 1) data.coopWins++;
            SaveSystem.Save();
        }

        /// <summary>The host is back in the lobby (a new race to come): the race is over on this phone too.</summary>
        public void BackInLobby()
        {
            if (LevelManager.Race == this) LevelManager.Race = null;
            Route = null;
            nextLegAt = -1f;
            // A phone still in a level goes back to the lobby with everyone.
            if (LevelManager.Current != null) FrontEndController.Open(FrontEndScreenId.Coop);
        }

        /// <summary>The session is gone (the lobby closed before the race): out of any leg, back to the menu.</summary>
        public void SessionEnded()
        {
            bool inLevel = LevelManager.Current != null && LevelManager.Race == this;
            Reset();
            if (inLevel) FrontEndController.Open(FrontEndScreenId.Coop);
        }

        /// <summary>Back to the lobby screen from a finished (or no longer counting) run; the session stays.</summary>
        public void ToLobby()
        {
            if (LevelManager.Race == this) LevelManager.Race = null;
            FrontEndController.Open(FrontEndScreenId.Coop);
        }

        public void Reset()
        {
            if (LevelManager.Race == this) LevelManager.Race = null;
            Route = null;
            RaceId = 0;
            Leg = 0;
            Finished = false;
            nextLegAt = -1f;
        }
    }
}
