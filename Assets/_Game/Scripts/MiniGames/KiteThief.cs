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
    /// KM2-4 The Kite Thief's twist (docs/CITIES.md M4): past <see cref="triggerX"/> a black kite swoops on the kid, takes the
    /// rice ball off the bento and drops it on the rocks at <see cref="dropX"/>, behind; the wave comes in over it in
    /// <see cref="KiteRules.TimeToGetBack"/> seconds. Dribble back and reach it in time and it is saved (coins, and the bento
    /// stays whole for the Delivered badge); else the wave takes it. Either way the leg goes on to the great torii.
    /// </summary>
    public class KiteThief : MonoBehaviour, IResettable
    {
        public float triggerX = 40f;
        public float dropX = 26f;
        public float groundY;
        [Tooltip("The kite (its model, head toward +x), flown on the swoop.")]
        public Transform kite;
        [Tooltip("The kite's wings (flapped).")]
        public Transform[] wings;
        [Tooltip("The rice ball as it is carried and dropped.")]
        public Transform rice;
        [Tooltip("The wave that comes in over the rice ball (moved in from the sea).")]
        public Transform wave;

        enum Phase { Waiting, Swoop, Carry, Fall, Back, Done }

        Phase phase;
        float t, limit, flap;
        Vector3 from, to;
        Canvas canvas;
        Text banner;
        Quaternion[] wingRest;
        Vector3 waveStart;

        void Awake()
        {
            wingRest = new Quaternion[wings != null ? wings.Length : 0];
            for (int i = 0; i < wingRest.Length; i++) wingRest[i] = wings[i] != null ? wings[i].localRotation : Quaternion.identity;
            if (wave != null) waveStart = wave.position;
            ResetState();
        }

        public void ResetState()
        {
            phase = Phase.Waiting;
            t = 0f;
            if (kite != null) kite.gameObject.SetActive(false);
            if (rice != null) rice.gameObject.SetActive(false);
            if (wave != null) wave.position = waveStart;
            if (canvas != null) Destroy(canvas.gameObject);
            canvas = null;
        }

        void Update()
        {
            var level = LevelManager.Current;
            if (level == null || level.kid == null) return;
            float dt = Time.deltaTime;
            t += dt;
            Vector3 kid = level.kid.transform.position;
            Flap(dt);
            switch (phase)
            {
                case Phase.Waiting:
                    if (level.State == LevelState.Playing && kid.x > triggerX) Begin();
                    break;
                case Phase.Swoop:
                    Fly(from, kid + new Vector3(0f, 1.2f, 0f), t / 1.1f);
                    if (t >= 1.1f)
                    {
                        BentoOnBack.RiceBallShown(false);
                        if (rice != null) rice.gameObject.SetActive(true);
                        from = kite.position;
                        to = new Vector3(dropX, groundY + 4.5f, kite.position.z);
                        Next(Phase.Carry);
                    }
                    break;
                case Phase.Carry:
                    Fly(from, to, t / 1.8f);
                    if (rice != null) rice.position = kite.position + new Vector3(0f, -0.25f, 0f);
                    if (t >= 1.8f)
                    {
                        from = kite.position;
                        to = new Vector3(dropX - 18f, groundY + 12f, kite.position.z);
                        limit = KiteRules.TimeToGetBack(kid.x - dropX);
                        Show(Loc.T("mini.kite.snatch"));
                        Next(Phase.Fall);
                    }
                    break;
                case Phase.Fall:
                    Fly(from, to, t / 2.5f);
                    if (rice != null)
                        rice.position = Vector3.Lerp(rice.position, new Vector3(dropX, groundY + 0.12f, 0f), Mathf.Clamp01(dt * 6f));
                    if (t >= 0.5f) Next(Phase.Back);
                    break;
                case Phase.Back:
                    if (kite != null && t < 2.5f) Fly(from, to, (t + 0.5f) / 3f);
                    else if (kite != null) kite.gameObject.SetActive(false);
                    float left = Mathf.Max(0f, limit - t);
                    if (banner != null) banner.text = Loc.F("mini.kite.back", Mathf.CeilToInt(left));
                    // the wave comes in from the sea behind, over the rice ball's place on the rocks
                    if (wave != null) wave.position = Vector3.Lerp(waveStart, new Vector3(dropX, waveStart.y, 0.3f), Mathf.Clamp01(t / limit));
                    if (KiteRules.Reached(kid.x, dropX))
                    {
                        if (rice != null) rice.gameObject.SetActive(false);
                        if (Errands.SavedRiceBall(SaveSystem.Data)) SaveSystem.Save();
                        BentoOnBack.RiceBallShown(Errands.CarriesBento(SaveSystem.Data));
                        level.CollectBonus(KiteRules.SavedCoins, KiteRules.SavedCoins);
                        Show(Loc.T("mini.kite.got"));
                        Next(Phase.Done);
                    }
                    else if (t >= limit)
                    {
                        if (rice != null) rice.gameObject.SetActive(false);
                        if (Errands.LostRiceBall(SaveSystem.Data)) SaveSystem.Save();
                        level.CollectBonus(0, KiteRules.SavedCoins);
                        Show(Loc.T("mini.kite.lost"));
                        Next(Phase.Done);
                    }
                    break;
                case Phase.Done:
                    if (wave != null) wave.position = Vector3.Lerp(wave.position, waveStart, Mathf.Clamp01(dt * 0.6f));
                    if (t > 2.4f && canvas != null)
                    {
                        Destroy(canvas.gameObject);
                        canvas = null;
                    }
                    break;
            }
        }

        void Begin()
        {
            if (kite == null)
            {
                phase = Phase.Done;
                return;
            }
            kite.gameObject.SetActive(true);
            from = new Vector3(triggerX + 9f, groundY + 7f, 0f);
            kite.position = from;
            Next(Phase.Swoop);
        }

        void Fly(Vector3 a, Vector3 b, float k)
        {
            if (kite == null) return;
            k = Mathf.Clamp01(k);
            Vector3 p = Vector3.Lerp(a, b, k) + Vector3.up * Mathf.Sin(k * Mathf.PI) * 0.8f;
            Vector3 d = p - kite.position;
            kite.position = p;
            if (Mathf.Abs(d.x) > 0.0001f) kite.localScale = new Vector3(Mathf.Abs(kite.localScale.x) * (d.x < 0f ? -1f : 1f), kite.localScale.y, kite.localScale.z);
        }

        void Flap(float dt)
        {
            if (wings == null || kite == null || !kite.gameObject.activeSelf) return;
            flap += dt * 9f;
            for (int i = 0; i < wings.Length; i++)
                if (wings[i] != null) wings[i].localRotation = wingRest[i] * Quaternion.Euler(Mathf.Sin(flap) * 35f * (i == 0 ? -1f : 1f), 0f, 0f);
        }

        void Next(Phase p)
        {
            phase = p;
            t = 0f;
        }

        void Show(string text)
        {
            if (canvas == null)
            {
                canvas = UIKit.CreateCanvas("KiteThief", 20);
                var root = UIKit.Stretch(UIKit.Rect(canvas.transform, "Root"));
                banner = UIKit.Label(root, "Banner", "", 46, Color.white, TextAnchor.MiddleCenter, true);
                UIKit.Place(banner.rectTransform, new Vector2(0.5f, 1f), new Vector2(0f, -190f), new Vector2(1300f, 70f));   // within 4:3's 1440
                UIKit.Fit(banner, 28);
                var outline = banner.gameObject.AddComponent<Outline>();
                outline.effectColor = new Color(0.05f, 0.07f, 0.16f, 0.9f);
                outline.effectDistance = new Vector2(3f, -3f);
            }
            banner.text = text;
        }

        void OnDestroy()
        {
            if (canvas != null) Destroy(canvas.gameObject);
        }
    }
}
