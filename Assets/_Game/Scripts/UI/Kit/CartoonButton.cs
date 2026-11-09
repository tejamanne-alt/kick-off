using DribbleToSchool.Progression;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// A UIKit button's look with the classic cartoon filter (Settings, Add-ons &amp; Filters): a warm-black ink rim round
    /// the whole key and a hard ink shadow, as a cartoon's buttons are drawn. Off, the button is as it always was (the
    /// rim hidden, the soft shadow). It follows the filter at once (AddOns.FilterChanged).
    /// </summary>
    public class CartoonButton : MonoBehaviour
    {
        /// <summary>The ink: the filter's warm black.</summary>
        public static readonly Color InkColor = new Color(0.07f, 0.055f, 0.13f, 1f);
        /// <summary>How much further the hard shadow falls than the soft one.</summary>
        static readonly Vector2 HardShift = new Vector2(2f, -2f);

        Image shadow, ink;
        Color softColor;
        Vector2 softMin, softMax;

        /// <summary>The button's soft shadow (its colour and place are kept to come back to) and its hidden ink rim.</summary>
        public void Set(Image shadowImage, Image inkImage)
        {
            shadow = shadowImage;
            ink = inkImage;
            if (shadow != null)
            {
                softColor = shadow.color;
                softMin = shadow.rectTransform.offsetMin;
                softMax = shadow.rectTransform.offsetMax;
            }
            Refresh();
        }

        void OnEnable()
        {
            AddOns.FilterChanged += Refresh;
            Refresh();
        }

        void OnDisable()
        {
            AddOns.FilterChanged -= Refresh;
        }

        void Refresh()
        {
            if (shadow == null || ink == null) return;
            bool on = AddOns.ClassicOn;
            ink.enabled = on;
            shadow.color = on ? InkColor : softColor;
            shadow.rectTransform.offsetMin = softMin + (on ? HardShift : Vector2.zero);
            shadow.rectTransform.offsetMax = softMax + (on ? HardShift : Vector2.zero);
        }
    }
}
