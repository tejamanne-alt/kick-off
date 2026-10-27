using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Levels
{
    /// <summary>Ordered list of every level, used for "Next level" and the chapter map later.</summary>
    [CreateAssetMenu(menuName = "Dribble To School/Level Catalog", fileName = "LevelCatalog")]
    public class LevelCatalog : ScriptableObject
    {
        public List<LevelDefinition> levels = new List<LevelDefinition>();

        /// <summary>The level after <paramref name="current"/>, or null if it is the last one.</summary>
        public LevelDefinition NextAfter(LevelDefinition current)
        {
            int index = levels.IndexOf(current);
            if (index < 0 || index + 1 >= levels.Count) return null;
            return levels[index + 1];
        }
    }
}
