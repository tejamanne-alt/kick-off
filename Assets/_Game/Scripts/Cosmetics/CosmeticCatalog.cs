using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Cosmetics
{
    /// <summary>Every cosmetic in the game, in shop order.</summary>
    [CreateAssetMenu(menuName = "Dribble To School/Cosmetic Catalog", fileName = "CosmeticCatalog")]
    public class CosmeticCatalog : ScriptableObject
    {
        public List<CosmeticItem> items = new List<CosmeticItem>();

        public CosmeticItem Find(string id)
        {
            foreach (var item in items)
            {
                if (item != null && item.id == id) return item;
            }
            return null;
        }

        public List<CosmeticItem> InCategory(CosmeticCategory category)
        {
            var list = new List<CosmeticItem>();
            foreach (var item in items)
            {
                if (item != null && item.category == category) list.Add(item);
            }
            return list;
        }
    }
}
