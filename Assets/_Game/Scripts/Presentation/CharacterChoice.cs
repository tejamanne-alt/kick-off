using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// The kid can be the boy or the girl (Settings). Both are built into the level; this shows
    /// the one chosen, live, and passes the shop's outfits on to both so a switch keeps the look.
    /// </summary>
    public class CharacterChoice : MonoBehaviour, IOutfit
    {
        public GameObject boy;
        public GameObject girl;
        [Tooltip("Each character's IOutfit (a ModelOutfit or CharacterBody3D).")]
        public MonoBehaviour boyOutfit;
        public MonoBehaviour girlOutfit;

        void OnEnable()
        {
            GameSettings.Changed += Show;
            Show();
        }

        void OnDisable()
        {
            GameSettings.Changed -= Show;
        }

        void Show()
        {
            bool isGirl = GameSettings.Character == "girl" && girl != null;
            if (boy != null) boy.SetActive(!isGirl);
            if (girl != null) girl.SetActive(isGirl);
        }

        public void SetOutfit(Color shirt, Color legwear)
        {
            var a = boyOutfit as IOutfit;
            var b = girlOutfit as IOutfit;
            if (a != null) a.SetOutfit(shirt, legwear);
            if (b != null) b.SetOutfit(shirt, legwear);
        }

        public void ResetOutfit()
        {
            var a = boyOutfit as IOutfit;
            var b = girlOutfit as IOutfit;
            if (a != null) a.ResetOutfit();
            if (b != null) b.ResetOutfit();
        }
    }
}
