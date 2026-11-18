using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A tropical cloudburst over downtown Miami (FL2-5, Downpour to School): the rain comes in bursts, heavy for a few seconds,
    /// then easing. Before each burst the sky darkens and a warning shows; under an arcade or an awning (the <see cref="shelters"/>,
    /// stretches of the street with a roof) the kid stays dry. Out in a burst, the science project on the backpack gets wetter
    /// (Progression/Errands): soaked, and the trip's Delivered badge is lost. It never stops the kid: the badge is the stake.
    /// After the last burst the sun comes back (the bursts stop past <see cref="clearsAtX"/>).
    /// The gusts and the flooded gutters are the level's own (WindArea, Puddle).
    /// </summary>
    public class Downpour : HazardBase
    {
        [Tooltip("Seconds of easing rain between bursts, and of a burst.")]
        public float calm = 6.5f, burst = 4f;
        [Tooltip("Seconds of warning before a burst (the sky goes dark first).")]
        public float warning = 1.6f;
        public float phaseOffset;
        [Tooltip("Stretches of the street with a roof over the footpath (x from, x to): no rain reaches the kid there.")]
        public Vector2[] shelters;
        [Tooltip("Seconds out in a burst that soak the project through.")]
        public float soakSeconds = 4f;
        [Tooltip("The storm passes: no bursts once the kid is past here.")]
        public float clearsAtX = float.PositiveInfinity;
        [Tooltip("The heavy rain's streaks (shown in a burst), and the light rain's (shown between bursts).")]
        public GameObject heavyRain, lightRain;

        float time, wet;
        bool spoiled;
        Text meter;
        GameObject meterRoot;

        /// <summary>0 dry to 1 soaked through.</summary>
        public float Wetness { get { return wet; } }

        /// <summary>A burst is falling now.</summary>
        public bool Bursting
        {
            get
            {
                if (Kid != null && Kid.transform.position.x > clearsAtX) return false;
                return Mathf.Repeat(time, calm + burst) >= calm;
            }
        }

        /// <summary>A burst is about to fall: get under cover.</summary>
        public bool Coming
        {
            get
            {
                if (Kid != null && Kid.transform.position.x > clearsAtX) return false;
                float c = Mathf.Repeat(time, calm + burst);
                return c < calm && c >= calm - warning;
            }
        }

        /// <summary>Is <paramref name="x"/> under one of the roofs?</summary>
        public bool Sheltered(float x)
        {
            if (shelters == null) return false;
            foreach (var s in shelters)
                if (x >= s.x && x <= s.y) return true;
            return false;
        }

        void Start()
        {
            var canvas = UIKit.CreateCanvas("DownpourHud", 4);
            canvas.transform.SetParent(transform, false);
            var card = UIKit.Glass(canvas.transform, "Project");
            meterRoot = card.transform.parent.gameObject;
            UIKit.Place((RectTransform)meterRoot.transform, new Vector2(0f, 1f), new Vector2(330f, -250f), new Vector2(520f, 80f));
            meter = UIKit.GlassText(UIKit.Label(card.transform, "Text", "", 30, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
            UIKit.Stretch(meter.rectTransform, 8f);
            UIKit.Fit(meter, 20);
            ResetState();
        }

        public override void ResetState()
        {
            time = phaseOffset;
            wet = 0f;
            spoiled = false;
            Show();
        }

        void Update()
        {
            if (!IsLive) return;
            time += Time.deltaTime;
            var kid = Kid;
            if (Bursting && kid != null && !Sheltered(kid.transform.position.x))
            {
                wet = Mathf.Min(1f, wet + Time.deltaTime / Mathf.Max(0.5f, soakSeconds));
                if (wet >= 1f && !spoiled)
                {
                    spoiled = true;
                    Progression.Errands.Spoil(Progression.SaveSystem.Data);
                }
            }
            Show();
        }

        int shown = -1;

        void Show()
        {
            bool heavy = Bursting;
            if (heavyRain != null && heavyRain.activeSelf != heavy) heavyRain.SetActive(heavy);
            if (lightRain != null && lightRain.activeSelf == heavy) lightRain.SetActive(!heavy);
            if (meter == null) return;
            var data = Progression.SaveSystem.Data;
            bool carrying = Progression.Errands.CarryingUnharmed(data, Progression.Errands.ScienceProject) || spoiled;
            // What the pill says: the warning, the rain, or how the project is doing (only rewritten when that changes).
            int state = Coming ? 1 : heavy ? 2 : 0;
            int key = state * 10 + (carrying ? Mathf.Min(4, Mathf.FloorToInt(wet * 4f)) : 9);
            if (key == shown) return;
            shown = key;
            string line = state == 1 ? Loc.T("hazard.downpour.coming") : state == 2 ? Loc.T("hazard.downpour.burst") : "";
            if (carrying)
            {
                string how = Loc.T(spoiled ? "hazard.downpour.soaked" : wet > 0.5f ? "hazard.downpour.damp" : "hazard.downpour.dry");
                line = string.IsNullOrEmpty(line) ? how : line + "  " + how;
            }
            meter.text = line;
            meterRoot.SetActive(!string.IsNullOrEmpty(line));
        }
    }
}
