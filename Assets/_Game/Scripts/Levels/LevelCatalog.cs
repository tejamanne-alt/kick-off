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

        /// <summary>The level after <paramref name="current"/>, or null if it is the last one.</summary>
        public LevelDefinition NextAfter(LevelDefinition current)
        {
            int index = levels.IndexOf(current);
            if (index < 0 || index + 1 >= levels.Count) return null;
            return levels[index + 1];
        }
    }
}
