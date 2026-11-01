using DribbleToSchool.World;
using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// Carries the light and the atmosphere from one chapter's mood to the next as the kid runs from
    /// the home street to the market, the beach, the building site and the park (ChapterTheme.mood).
    /// </summary>
    public class HolidayAtmosphere : MonoBehaviour
    {
        public WorldLook look;
        public Transform follow;
    }
}
