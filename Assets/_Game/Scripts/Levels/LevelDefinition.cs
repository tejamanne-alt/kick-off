using UnityEngine;

namespace DribbleToSchool.Levels
{
    /// <summary>Data for one level: which scene, how long until the bell, star targets.</summary>
    [CreateAssetMenu(menuName = "Dribble To School/Level Definition", fileName = "Level")]
    public class LevelDefinition : ScriptableObject
    {
        public string levelId = "L01";
        public string displayName = "Out the Door";
        public int chapter = 1;
        [Tooltip("Scene name as listed in Build Profiles / Build Settings.")]
        public string sceneName = "L01_OutTheDoor";
        [Tooltip("Optional ball-skill challenge: unlocked by the chapter's first level, skipped by Next level.")]
        public bool isChallenge;

        [Header("Bell")]
        [Tooltip("Seconds until the school bell rings. Finishing before it earns a star.")]
        public float bellTime = 45f;

        [Header("Stars")]
        [Tooltip("Third star: best perfect-touch streak needed (coins join this in Phase 4).")]
        public int perfectStreakTarget = 3;
    }
}
