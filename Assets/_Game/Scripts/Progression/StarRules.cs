namespace DribbleToSchool.Progression
{
    /// <summary>
    /// A story level's three stars, one per goal, each earned on its own: getting there with the ball, the time (the leg's
    /// pace, or on a route's last leg walked from home the whole trip before the school bell), and collecting everything
    /// (every coin, and the level's sticker if it has one). Challenges score their own stars.
    /// </summary>
    public static class StarRules
    {
        /// <summary>The third goal: every coin in the level, and its sticker if it has one.</summary>
        public static bool CollectedEverything(int coins, int totalCoins, bool hasSticker, bool stickerFound)
        {
            return coins >= totalCoins && (!hasSticker || stickerFound);
        }

        /// <summary>Stars for a finished story level: one for getting there, one for the time goal, one for collecting everything.</summary>
        public static int Stars(bool timeGoal, bool collectedEverything)
        {
            return 1 + (timeGoal ? 1 : 0) + (collectedEverything ? 1 : 0);
        }
    }
}
