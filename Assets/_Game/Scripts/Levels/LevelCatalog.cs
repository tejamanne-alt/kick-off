using System;
using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Levels
{
    /// <summary>Display info for a chapter on the map.</summary>
    [Serializable]
    public class ChapterInfo
    {
        public int number = 1;
        public string title = "Home Street";
        public string subtitle = "";
        public Color color = new Color(0.97f, 0.55f, 0.27f);
    }

    /// <summary>Ordered list of every level, used for "Next level" and the chapter map later.</summary>
    [CreateAssetMenu(menuName = "Dribble To School/Level Catalog", fileName = "LevelCatalog")]
    public class LevelCatalog : ScriptableObject
    {
        public List<ChapterInfo> chapters = new List<ChapterInfo>();
        public List<LevelDefinition> levels = new List<LevelDefinition>();

        public ChapterInfo Chapter(int number)
        {
            foreach (var c in chapters)
            {
                if (c.number == number) return c;
            }
            return null;
        }

        public List<LevelDefinition> LevelsInChapter(int number)
        {
            var list = new List<LevelDefinition>();
            foreach (var l in levels)
            {
                if (l != null && l.chapter == number) list.Add(l);
            }
            return list;
        }

        public LevelDefinition FindById(string levelId)
        {
            foreach (var l in levels)
            {
                if (l != null && l.levelId == levelId) return l;
            }
            return null;
        }

        /// <summary>
        /// The story level after <paramref name="current"/>, skipping optional challenges.
        /// Null after the last level, and after a challenge (those return to the map).
        /// </summary>
        public LevelDefinition NextAfter(LevelDefinition current)
        {
            if (current == null || current.isChallenge) return null;
            int index = levels.IndexOf(current);
            if (index < 0) return null;
            for (int i = index + 1; i < levels.Count; i++)
            {
                if (levels[i] != null && !levels[i].isChallenge) return levels[i];
            }
            return null;
        }
    }
}
