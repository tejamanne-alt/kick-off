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
        /// <summary>How long a scene load may keep this phone quiet (the others are told, so they don't take it for a lost connection).</summary>
        const double LoadSilenceMs = 8000;

        readonly CoopService service;
        float nextLegAt = -1f;
        /// <summary>A leg's scene is loading (in the background: the session keeps talking meanwhile).</summary>
        string loadingScene;
        /// <summary>The place bonus (and the race's count and win) waits for the result to be final.</summary>
        bool bonusPending;

        public CoopRaceMode(CoopService service)
        {
            this.service = service;
        }

        CoopSession Session { get { return service.Session; } }

        public byte RaceId { get; private set; }
        /// <summary>The route being raced (the stage), and its location (an add-on).</summary>
        public Route Route { get; private set; }
        public City Location { get; private set; }
        /// <summary>The leg this phone is on (0 starts at home).</summary>
        public int Leg { get; private set; }
        public int LegCount { get { return Route != null ? Route.levels.Length : 1; } }
        /// <summary>This phone's kid got to school.</summary>
        public bool Finished { get; private set; }
        public uint FinishMs { get; private set; }
        /// <summary>The coins collected on every leg so far, and what the finish earned (coins and the place's bonus).</summary>
        public int Coins { get; private set; }
        public int CoinsEarned { get; private set; }
        /// <summary>The next leg's scene is loading (the kid on screen is still the last leg's).</summary>
        public bool LoadingLeg { get { return loadingScene != null; } }
        /// <summary>Between two legs (the stop's message, then the next scene while it loads).</summary>
        public bool BetweenLegs { get { return nextLegAt >= 0f || (loadingScene != null && Leg > 0); } }
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
                if (seconds > 3) return Localization.Loc.T("hud.ready");   // (3, 2, 1, GO: the countdown's first moments say "Ready...")
                return seconds > 0 ? seconds.ToString() : Localization.Loc.T("hud.go");
            }
        }

        /// <summary>The race clock, stopped at this phone's time once its kid is at school.</summary>
        public float RaceSeconds
        {
            get
            {
                if (Finished && FinishMs > 0) return FinishMs / 1000f;
                return (float)System.Math.Max(0, Session.RaceTimeMs) / 1000f;
            }
        }

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
            else
            {
                Finished = true;   // (a run that no longer counts still gets to the gate, and keeps its coins)
                BankCoins();
            }
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
            bonusPending = false;
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
            if (bonusPending && ResultIsFinal()) SettleBonus();
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
            string scene = def != null ? Cities.SceneFor(def.sceneName, Location) : null;
            if (scene == null || !Application.CanStreamedLevelBeLoaded(scene))
            {
                // (every phone in the race has the same content, CoopService.ContentHash: this is a broken build. Out of the
                // race, so the others aren't kept waiting for a run that can't go on.)
                Debug.LogError("[Co-op] Level " + Route.levels[Leg] + " (" + scene + ") can't be loaded: leaving the race.");
                Leave();
                return;
            }
            Session.ReportLeg(Leg, (float)Leg / LegCount);
            TimeControl.ResetTime();
            // In the background, so the session keeps talking while the scene loads; the moment the new scene starts still
            // stalls a frame or two, so the others are told to expect a short silence.
            Session.ExpectSilence(LoadSilenceMs);
            loadingScene = scene;
            var load = SceneManager.LoadSceneAsync(scene);
            if (load == null) { loadingScene = null; SceneManager.LoadScene(scene); }
        }

        /// <summary>A scene finished loading (CoopService). False when it is a leg this race no longer wants.</summary>
        public bool SceneLoaded(Scene scene)
        {
            if (loadingScene == null || scene.name != loadingScene) return true;
            loadingScene = null;
            return LevelManager.Race == this && Route != null;
        }

        /// <summary>To the co-op screen (a scene load: the others are told to expect a short silence).</summary>
        void OpenCoopScreen()
        {
            if (Session.InSession) Session.ExpectSilence(LoadSilenceMs);
            FrontEndController.Open(FrontEndScreenId.Coop);
        }

        /// <summary>How far along the whole route the kid is: the legs behind, and this one's share.</summary>
        public float Progress(float legFraction)
        {
            return Mathf.Clamp01((Leg + Mathf.Clamp01(legFraction)) / Mathf.Max(1, LegCount));
        }

        /// <summary>
        /// At the gate: the coins collected are saved at once (whatever happens next, they are the player's). The place's
        /// bonus, and the race counted as raced (and won), wait until the result is final: a finish heard late (a phone that
        /// was out of range) can still come before this one.
        /// </summary>
        void Bank()
        {
            BankCoins();
            bonusPending = true;
            if (ResultIsFinal()) SettleBonus();
        }

        void BankCoins()
        {
            CoinsEarned = Coins;
            SaveSystem.AddCoins(Coins);
            SaveSystem.Save();
        }

        /// <summary>Nobody is still on the way (the host says the race is over, or every other run has ended).</summary>
        bool ResultIsFinal()
        {
            if (Session.Phase == SessionPhase.Over || Session.Phase == SessionPhase.Lobby || !Session.InSession) return true;
            var players = Session.Players;
            for (int i = 0; i < players.Count; i++)
                if (players[i].uid != Session.Uid && players[i].status == PlayerStatus.Racing) return false;
            return true;
        }

        /// <summary>The place's bonus and the race's count, from the place as it stands now (called once per finish).</summary>
        void SettleBonus()
        {
            if (!bonusPending) return;
            bonusPending = false;
            var me = Session.Me;
            int place;
            if (me != null && me.status == PlayerStatus.Finished && me.place > 0) place = me.place;
            else
            {
                place = 1;
                var players = Session.Players;
                for (int i = 0; i < players.Count; i++)
                {
                    var p = players[i];
                    if (p.uid != Session.Uid && p.status == PlayerStatus.Finished && p.finishMs < FinishMs) place++;
                }
            }
            int bonus = PlaceBonus[Mathf.Clamp(place - 1, 0, PlaceBonus.Length - 1)];
            CoinsEarned = Coins + bonus;
            SaveSystem.AddCoins(bonus);
            var data = SaveSystem.Data;
            data.coopRaces++;
            if (place == 1) data.coopWins++;
            SaveSystem.Save();
        }

        /// <summary>The host is back in the lobby (a new race to come): the race is over on this phone too.</summary>
        public void BackInLobby()
        {
            SettleBonus();
            bool inLevel = LevelManager.Current != null && LevelManager.Race == this;
            if (LevelManager.Race == this) LevelManager.Race = null;
            Route = null;
            nextLegAt = -1f;
            // A phone still in a level goes back to the lobby with everyone.
            if (inLevel || loadingScene != null) OpenCoopScreen();
        }

        /// <summary>The session is gone (the lobby closed before the race): out of any leg, back to the menu.</summary>
        public void SessionEnded()
        {
            bool inLevel = (LevelManager.Current != null && LevelManager.Race == this) || loadingScene != null;
            Reset();
            if (inLevel) FrontEndController.Open(FrontEndScreenId.Coop);
        }

        /// <summary>Back to the lobby screen from a finished (or no longer counting) run; the session stays.</summary>
        public void ToLobby()
        {
            SettleBonus();
            if (LevelManager.Race == this) LevelManager.Race = null;
            nextLegAt = -1f;   // (no next leg loading behind the lobby)
            OpenCoopScreen();
        }

        public void Reset()
        {
            SettleBonus();
            if (LevelManager.Race == this) LevelManager.Race = null;
            Route = null;
            RaceId = 0;
            Leg = 0;
            Finished = false;
            nextLegAt = -1f;
        }
    }
}
