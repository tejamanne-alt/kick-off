using DribbleToSchool.Core;
using DribbleToSchool.Cosmetics;
using DribbleToSchool.Progression;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// The Locker Room's bags on one kid (a kid modelled without a bag of their own: PlayerInfo.wearsBags). Each bag is a
    /// mesh of the kid's own model, fitted to them (tools/blender/meshy_bag.py); this shows the one the kid wears
    /// (Cosmetics/Bags), or none, with the shop's pennant only when there is a bag to clip it to, and recolours the
    /// bag's cloth to the colour chosen in Settings (ToonCharacter's _MaskTint: the texture's alpha marks the cloth).
    /// </summary>
    public class BagWear : MonoBehaviour
    {
        [Tooltip("The roster id of the kid who wears these bags.")]
        public string playerId;
        [Tooltip("The bag items' ids (Cosmetics/Bags), one for each mesh below.")]
        public string[] bagIds;
        [Tooltip("Each bag's mesh, fitted to this kid.")]
        public Renderer[] bags;
        [Tooltip("Shown only while a bag is worn: the pennant's pole and flag.")]
        public GameObject[] onBag;

        static readonly int MaskTintId = Shader.PropertyToID("_MaskTint");
        MaterialPropertyBlock block;
        string previewing;

        void OnEnable()
        {
            Bags.Changed += Apply;
            GameSettings.Changed += Apply;
            SaveSystem.Changed += Apply;
            Apply();
        }

        void OnDisable()
        {
            Bags.Changed -= Apply;
            GameSettings.Changed -= Apply;
            SaveSystem.Changed -= Apply;
        }

        /// <summary>The bag this kid wears, as saved (ends a try-on).</summary>
        public void Apply()
        {
            previewing = null;
            Show(Bags.For(playerId));
        }

        /// <summary>Try a bag on without choosing it (the Locker Room); <see cref="Apply"/> puts the chosen one back.</summary>
        public void Preview(string bagId)
        {
            previewing = bagId;
            Show(bagId);
        }

        /// <summary>The bag on show: the one being tried on, else the one worn.</summary>
        public string Shown { get { return previewing ?? Bags.For(playerId); } }

        void Show(string bagId)
        {
            bool any = false;
            var swatch = Bags.Colour();
            if (block == null) block = new MaterialPropertyBlock();
            for (int i = 0; i < bags.Length; i++)
            {
                if (bags[i] == null) continue;
                bool on = bagIds != null && i < bagIds.Length && bagIds[i] == bagId;
                bags[i].gameObject.SetActive(on);
                any |= on;
                if (!on) continue;
                bags[i].GetPropertyBlock(block);
                Color tint = swatch.color;
                tint.a = swatch.tints ? 1f : 0f;
                block.SetColor(MaskTintId, tint);
                bags[i].SetPropertyBlock(block);
            }
            if (onBag != null)
                foreach (var go in onBag)
                    if (go != null) go.SetActive(any);
        }
    }
}
