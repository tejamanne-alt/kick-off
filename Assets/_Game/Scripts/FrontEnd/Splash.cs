using DribbleToSchool.UI;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>First-launch splash: the Kick Off logo pops in over the deep blue sky, then it all fades to the menu.</summary>
    public class Splash : MonoBehaviour
    {
        const float Hold = 1.5f;
        const float FadeTime = 0.5f;

        CanvasGroup group;
        float start;

        public static void Show(RectTransform canvas)
        {
            var root = UIKit.Stretch(UIKit.Rect(canvas, "Splash"));
            root.SetAsLastSibling();
            var bg = root.gameObject.AddComponent<Image>();
            bg.color = UITheme.SkyBottom;
            var top = UIKit.Icon(root, "SkyTop", ProceduralSprites.VerticalGradient, UITheme.SkyTop, 10f);
            top.preserveAspect = false;
            UIKit.Stretch(top.rectTransform);
            var logo = KickOffLogo.Build(root, 1.15f);
            UIKit.Place(logo, new Vector2(0.5f, 0.5f), new Vector2(0f, 10f), logo.sizeDelta);
            UIKit.PopIn(logo.gameObject, 0.1f);
            var splash = root.gameObject.AddComponent<Splash>();
            splash.group = root.gameObject.AddComponent<CanvasGroup>();
            splash.start = Time.unscaledTime;
        }

        void Update()
        {
            float t = Time.unscaledTime - start - Hold;
            if (t <= 0f) return;
            group.alpha = 1f - Mathf.Clamp01(t / FadeTime);
            group.blocksRaycasts = group.alpha > 0.5f;
            if (t >= FadeTime) Destroy(gameObject);
        }
    }
}
