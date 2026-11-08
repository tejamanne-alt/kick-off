namespace DribbleToSchool.Core
{
    /// <summary>
    /// A race other phones are running at the same time (Co-op, Coop/CoopRaceMode), as the level sees it. While one is set
    /// (<see cref="LevelManager.Race"/>), a level is one leg of the race: there is no bell or pace, nothing is saved as story
    /// progress, the first leg's countdown waits for the shared GO, and reaching the goal hands over to the race (the next
    /// leg, or the finish) instead of the results card. The HUD shows the race's clock and the race's pause menu.
    /// </summary>
    public interface ILevelRace
    {
        /// <summary>The level's countdown waits (the first leg, until every phone's GO).</summary>
        bool HoldsIntro { get; }

        /// <summary>What the big text says during the countdown ("3", "2", "1", or a waiting line); null for the level's own.</summary>
        string IntroText { get; }

        /// <summary>The race's clock in seconds (since GO, the same on every phone).</summary>
        float RaceSeconds { get; }

        /// <summary>The kid and the ball reached this leg's goal.</summary>
        void LegFinished(LevelManager level);

        /// <summary>The player chose to leave the race (pause menu): the others are told; back to the menu.</summary>
        void Leave();
    }
}
