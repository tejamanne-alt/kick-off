using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// A tropical cloudburst over downtown Miami (FL2-3, Downpour to School): the rain comes in bursts, heavy for a few seconds,
    /// then easing. Before each burst the sky darkens and a warning shows; under an arcade or an awning (the <see cref="shelters"/>,
    /// stretches of the street with a roof) the kid stays dry, and out in a burst the rain drives into the kid's face: a slower run
    /// (<see cref="burstPace"/>) until the burst passes. It never stops the kid. After the last burst the sun comes back (the bursts
    /// stop past <see cref="clearsAtX"/>). The rain itself is a <see cref="World.RainCurtain"/>; the light dims with the storm
    /// through the camera's <see cref="World.WorldLook"/>. The gusts and the flooded gutters are the level's own (WindArea, Puddle).
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
        [Tooltip("The storm passes: no bursts once the kid is past here.")]
        public float clearsAtX = float.PositiveInfinity;
        [Tooltip("The rain: steady between bursts, heavy in them.")]
        public World.RainCurtain rain;
        [Tooltip("The rain's strength between bursts, and in one.")]
        [Range(0f, 1f)] public float steadyRain = 0.3f, burstRain = 1f;
        [Tooltip("The kid's pace out in a burst (under a roof, or between bursts, the usual pace).")]
        [Range(0.5f, 1f)] public float burstPace = 0.8f;

        [Header("The storm's light")]
        [Tooltip("How dark and grey the light goes in a burst (0 none, 1 all the way to the storm colours below).")]
        [Range(0f, 1f)] public float stormDim = 0.85f;
        public Color stormSun = new Color(0.7f, 0.74f, 0.8f);
        public Color stormAmbient = new Color(0.47f, 0.5f, 0.56f);
        public Color stormZenith = new Color(0.3f, 0.34f, 0.41f);
        public Color stormHorizon = new Color(0.5f, 0.54f, 0.59f);
        public Color stormHaze = new Color(0.54f, 0.58f, 0.63f);

        float time;
        Text meter;
        GameObject meterRoot;
        bool slowed;

        World.WorldLook look;
        bool lookSaved;
        Color sun0, ambientSky0, ambientGround0, zenith0, horizon0, haze0;
        float hazeStrength0, shadow0, storm, stormShown = -1f;

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
            var card = UIKit.Glass(canvas.transform, "Warning");
            meterRoot = card.transform.parent.gameObject;
            // Under the HUD's info card (top-left, 30 px in, its foot about 264 px down), not across its edge.
            UIKit.Place((RectTransform)meterRoot.transform, new Vector2(0f, 1f), new Vector2(30f, -284f), new Vector2(520f, 72f), new Vector2(0f, 1f));
            meter = UIKit.GlassText(UIKit.Label(card.transform, "Text", "", 30, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
            UIKit.Stretch(meter.rectTransform, 8f);
            UIKit.Fit(meter, 20);
            var cam = Camera.main;
            look = cam != null ? cam.GetComponent<World.WorldLook>() : null;
            if (look != null)
            {
                sun0 = look.sunColor; ambientSky0 = look.ambientSky; ambientGround0 = look.ambientGround;
                zenith0 = look.skyZenith; horizon0 = look.skyHorizon; haze0 = look.hazeColor;
                hazeStrength0 = look.hazeStrength; shadow0 = look.shadowStrength;
                lookSaved = true;
            }
            ResetState();
        }

        void OnDestroy()
        {
            storm = 0f;
            ApplyStorm(true);
            Slow(false);
        }

        public override void ResetState()
        {
            time = phaseOffset;
            storm = Target();
            ApplyStorm(true);
            Slow(false);
            Show();
        }

        void Update()
        {
            if (IsLive) time += Time.deltaTime;
            float target = Target();
            storm = Mathf.MoveTowards(storm, target, Time.deltaTime * (target > storm ? 1.1f : 0.6f));
            ApplyStorm(false);
            var kid = Kid;
            Slow(IsLive && Bursting && kid != null && !Sheltered(kid.transform.position.x));
            Show();
        }

        /// <summary>How stormy it should be now: dark and pouring in a burst (from its warning), grey between bursts, clear once past.</summary>
        float Target()
        {
            if (Kid != null && Kid.transform.position.x > clearsAtX) return 0f;
            return Coming || Bursting ? 1f : 0.35f;
        }

        void Slow(bool on)
        {
            var kid = Kid;
            if (kid == null || on == slowed) return;
            if (on) kid.AddSpeedModifier(this, burstPace);
            else kid.RemoveSpeedModifier(this);
            slowed = on;
        }

        /// <summary>The rain's strength and the light, eased with the storm (the light is only rewritten while it changes).</summary>
        void ApplyStorm(bool snap)
        {
            if (rain != null)
            {
                bool clear = Kid != null && Kid.transform.position.x > clearsAtX;
                rain.intensity = clear ? 0f : Bursting ? burstRain : Coming ? Mathf.Lerp(steadyRain, burstRain, 0.4f) : steadyRain;
                rain.clearsAtX = clearsAtX;
            }
            if (!lookSaved || look == null) return;
            if (!snap && Mathf.Abs(storm - stormShown) < 0.004f) return;
            stormShown = storm;
            float k = storm * stormDim;
            look.sunColor = Color.Lerp(sun0, stormSun, k);
            look.ambientSky = Color.Lerp(ambientSky0, stormAmbient, k);
            look.ambientGround = Color.Lerp(ambientGround0, stormAmbient * 0.9f, k);
            look.skyZenith = Color.Lerp(zenith0, stormZenith, k);
            look.skyHorizon = Color.Lerp(horizon0, stormHorizon, k);
            look.hazeColor = Color.Lerp(haze0, stormHaze, k);
            look.hazeStrength = Mathf.Lerp(hazeStrength0, Mathf.Min(1f, hazeStrength0 + 0.25f), k);
            look.shadowStrength = Mathf.Lerp(shadow0, 0.25f, k);
            look.Apply();
        }

        int shown = -1;

        void Show()
        {
            bool heavy = Bursting;
            if (meter == null) return;
            // What the pill says: the warning or the rain (only rewritten when that changes).
            int state = Coming ? 1 : heavy ? 2 : 0;
            if (state == shown) return;
            shown = state;
            string line = state == 1 ? Loc.T("hazard.downpour.coming") : state == 2 ? Loc.T("hazard.downpour.burst") : "";
            meter.text = line;
            meterRoot.SetActive(!string.IsNullOrEmpty(line));
        }
    }
}
