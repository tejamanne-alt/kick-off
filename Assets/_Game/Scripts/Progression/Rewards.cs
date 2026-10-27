namespace DribbleToSchool.Progression
{
    /// <summary>Coin economy constants in one place so balancing is easy.</summary>
    public static class Rewards
    {
        /// <summary>Bonus coins for every perfect touch during a run.</summary>
        public const int PerPerfectTouch = 1;
        /// <summary>Bonus for each star earned for the first time.</summary>
        public const int PerNewStar = 10;
        /// <summary>Bonus for finding a sticker you didn't have.</summary>
        public const int NewSticker = 15;
        /// <summary>Bonus for collecting every coin in a level.</summary>
        public const int AllCoinsBonus = 10;
    }
}
