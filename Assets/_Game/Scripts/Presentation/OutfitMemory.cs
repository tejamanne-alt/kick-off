using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Remembers the outfit a character choice was last dressed in, so that a kid who was hidden
    /// at the time can be put in the same clothes when they are shown (CharacterChoice dresses
    /// only the kid on screen: every kid's mesh is recoloured on a copy, and a copy for each of
    /// six kids at every level start would be wasted memory and time).
    /// </summary>
    public sealed class OutfitMemory
    {
        bool dressed, accented;
        Color shirt, legwear, accent;

        public bool Dressed { get { return dressed; } }
        public bool Accented { get { return accented; } }

        public void SetOutfit(Color shirt, Color legwear)
        {
            this.shirt = shirt;
            this.legwear = legwear;
            dressed = true;
        }

        public void SetAccent(Color accent)
        {
            this.accent = accent;
            accented = true;
        }

        public void Reset()
        {
            dressed = accented = false;
        }

        /// <summary>
        /// Puts <paramref name="target"/> (an IOutfit, if it is one) in the remembered clothes: the
        /// clothes it was made with if none were chosen, else the chosen shirt, legwear and accent.
        /// </summary>
        public void ReplayOn(object target)
        {
            var outfit = target as IOutfit;
            if (outfit != null)
            {
                outfit.ResetOutfit();
                if (dressed) outfit.SetOutfit(shirt, legwear);
            }
            var accentOutfit = target as IAccentOutfit;
            if (accentOutfit != null && accented) accentOutfit.SetAccent(accent);
        }
    }
}
