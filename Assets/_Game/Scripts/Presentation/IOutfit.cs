using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>Something that can be dressed in an outfit's shirt and shorts colours (the shop's outfits).</summary>
    public interface IOutfit
    {
        void SetOutfit(Color shirt, Color legwear);
    }
}
