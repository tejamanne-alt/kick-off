using DribbleToSchool.Core;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// The player can be any kid of the <see cref="PlayerRoster"/> (Settings, the picker). All of
    /// them are built into the level; this shows the one chosen, live. The shop's outfits go to
    /// the kid on screen and are remembered (<see cref="OutfitMemory"/>), so a kid who is picked
    /// later comes out in the same clothes without every kid having been dressed up front.
    /// </summary>
    public class CharacterChoice : MonoBehaviour, IOutfit, IAccentOutfit
    {
        [Tooltip("The roster id of each kid below (PlayerRoster).")]
        public string[] ids;
        [Tooltip("Each kid's visual: shown when the player is that kid, hidden otherwise.")]
        public GameObject[] characters;
        [Tooltip("Each kid's IOutfit (a ModelOutfit or CharacterBody3D).")]
        public MonoBehaviour[] outfits;

        readonly OutfitMemory look = new OutfitMemory();
        int shown = -1;

        void OnEnable()
        {
            GameSettings.Changed += Show;
            Show();
        }

        void OnDisable()
        {
            GameSettings.Changed -= Show;
        }

        /// <summary>The position of the chosen kid in the arrays: the one picked, else the first.</summary>
        int Chosen()
        {
            if (ids != null && characters != null)
            {
                string id = GameSettings.Character;
                for (int i = 0; i < ids.Length && i < characters.Length; i++)
                    if (ids[i] == id && characters[i] != null) return i;
            }
            return 0;
        }

        /// <summary>The outfit of kid <paramref name="i"/>, or null.</summary>
        object OutfitOf(int i)
        {
            return outfits != null && i >= 0 && i < outfits.Length ? outfits[i] : null;
        }

        void Show()
        {
            if (characters == null) return;
            int chosen = Chosen();
            for (int i = 0; i < characters.Length; i++)
                if (characters[i] != null) characters[i].SetActive(i == chosen);
            if (chosen == shown) return;
            shown = chosen;
            look.ReplayOn(OutfitOf(chosen));
        }

        public void SetOutfit(Color shirt, Color legwear)
        {
            look.SetOutfit(shirt, legwear);
            var outfit = OutfitOf(shown) as IOutfit;
            if (outfit != null) outfit.SetOutfit(shirt, legwear);
        }

        public void SetAccent(Color accent)
        {
            look.SetAccent(accent);
            var outfit = OutfitOf(shown) as IAccentOutfit;
            if (outfit != null) outfit.SetAccent(accent);
        }

        public void ResetOutfit()
        {
            look.Reset();
            var outfit = OutfitOf(shown) as IOutfit;
            if (outfit != null) outfit.ResetOutfit();
        }
    }
}
