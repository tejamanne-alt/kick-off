using DribbleToSchool.Localization;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>First-launch splash: the title pops in over a warm wash, a ball bounces, then it fades away.</summary>
    public class Splash : MonoBehaviour
    {
        const float Hold = 1.4f;
        const float FadeTime = 0.5f;

        CanvasGroup group;
        float start;

        public static void Show(RectTransform canvas)
        {
            var root = UIKit.Stretch(UIKit.Rect(canvas, "Splash"));
            root.SetAsLastSibling();
            var bg = root.gameObject.AddComponent<Image>();
            bg.color = new Color(0.99f, 0.9f, 0.76f);
            var title = UIKit.Title(root, "Title", Loc.T("menu.title"), UITheme.SizeHero, Color.white);
            UIKit.Place(title.rectTransform, new Vector2(0.5f, 0.55f), Vector2.zero, new Vector2(1400f, 320f));
            UIKit.PopIn(title.gameObject, 0.1f);
            var ball = UIKit.Icon(root, "Ball", ProceduralSprites.Circle, Color.white, 110f);
            UIKit.Place(ball.rectTransform, new Vector2(0.5f, 0.28f), Vector2.zero, new Vector2(110f, 110f));
            var outline = ball.gameObject.AddComponent<Outline>();
            outline.effectColor = UITheme.Ink;
            outline.effectDistance = new Vector2(4f, -4f);
            ball.gameObject.AddComponent<UIBounce>();
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
