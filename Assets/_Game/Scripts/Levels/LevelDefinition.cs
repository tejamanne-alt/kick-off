using UnityEngine;

namespace DribbleToSchool.Levels
{
    /// <summary>Data for one level: which scene, how long until the bell, star targets.</summary>
    [CreateAssetMenu(menuName = "Kick Off/Level Definition", fileName = "Level")]
    public class LevelDefinition : ScriptableObject
    {
        public string levelId = "L01";
        public string displayName = "Out the Door";
        public int chapter = 1;
        [Tooltip("Scene name as listed in Build Profiles / Build Settings.")]
        public string sceneName = "L01_OutTheDoor";
        [Tooltip("Optional ball-skill challenge: unlocked by the chapter's first level, skipped by Next level.")]
        public bool isChallenge;
        [Tooltip("The city whose level this is (Progression.Cities' id: \"original\" for Kamakura). Each city has its own routes and levels.")]
        public string city = "original";
        /// <summary>The level has a sticker to find (and a slot in the album): every story level; not a challenge.</summary>
        public bool HasStickerSlot { get { return !isChallenge; } }

        [Header("Bell")]
        [Tooltip("Seconds until the school bell rings. Finishing before it earns a star.")]
        public float bellTime = 45f;

        [Header("Stars")]
        [Tooltip("A perfect-touch streak to aim for. Not a star goal any more: the third star is every coin and the sticker (Progression/StarRules).")]
        public int perfectStreakTarget = 3;
    }
}
