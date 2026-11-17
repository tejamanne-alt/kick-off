using System.Collections.Generic;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Presentation;
using DribbleToSchool.Progression;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.MiniGames
{
    /// <summary>
    /// The bento on the kid's backpack (Progression/Errands): a little wrapped box, built with the level (hidden), set on the
    /// kid's bag while the trip carries it. <see cref="ShowAll"/> puts it on as soon as the errand is done.
    /// </summary>
    public class BentoOnBack : MonoBehaviour, IResettable
    {
        [Tooltip("The wrapped bento's model (hidden until the kid carries it).")]
        public GameObject bento;
        [Tooltip("The rice ball on top of it (hidden while the kite has it, or once the wave took it).")]
        public GameObject riceBall;

        static readonly List<BentoOnBack> live = new List<BentoOnBack>();

        void OnEnable() { live.Add(this); }
        void OnDisable() { live.Remove(this); }

        void Start() { Apply(); }

        public void ResetState() { Apply(); }

        /// <summary>Show or hide the bento on every kid in the level, by what the save says is carried.</summary>
        public static void ShowAll()
        {
            foreach (var b in live) b.Apply();
        }

        /// <summary>Hide or show just the rice ball (the kite took it; it was got back).</summary>
        public static void RiceBallShown(bool shown)
        {
            foreach (var b in live)
                if (b.riceBall != null) b.riceBall.SetActive(shown);
        }

        void Apply()
        {
            if (bento == null) return;
            bool carried = Errands.CarriesBento(SaveSystem.Data);
            bento.SetActive(carried);
            if (riceBall != null) riceBall.SetActive(Errands.BentoWhole(SaveSystem.Data));
            if (!carried) return;
            var level = LevelManager.Current;
            var rig = level != null && level.kid != null ? level.kid.GetComponentInChildren<CharacterRig>() : null;
            Transform at = rig != null ? (rig.bag != null ? rig.bag : rig.chest) : null;
            if (at == null || bento.transform.parent == at) return;
            Vector3 scale = bento.transform.lossyScale;
            bento.transform.SetParent(at, true);
            bento.transform.position = at.position + Vector3.up * 0.26f;
            var parentScale = at.lossyScale;
            bento.transform.localScale = new Vector3(scale.x / Mathf.Max(0.001f, parentScale.x), scale.y / Mathf.Max(0.001f, parentScale.y),
                scale.z / Mathf.Max(0.001f, parentScale.z));
        }
    }
}
