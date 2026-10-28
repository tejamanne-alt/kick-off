using DribbleToSchool.Audio;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// The look of an on-screen game control (walk, kick, jump): a glossy round key cap
    /// standing on a darker base, with a soft drop shadow. Holding it pushes the cap down
    /// onto its base, darkens it and fires a crisp haptic click; letting go springs it
    /// back with a soft tap. A ripple ring spreads on each press, and a glow can pulse to
    /// say "now" (the kick button while the ball is in reach).
    /// GameInput reads the touches; GameHud tells this component when it is held.
    /// </summary>
    public class TouchButton : MonoBehaviour
    {
        [Tooltip("How far the cap travels when pressed, as a fraction of the button size.")]
        public float travel = 0.075f;
        [Tooltip("Main actions (kick, jump) click harder than the walk buttons.")]
        public bool primary = true;

        public RectTransform Content { get; private set; }

        Image shadow, rim, cap, gloss, ripple, glow;
        RectTransform capRect, rippleRect, glowRect;
        Color capColor, rimColor;
        float press, pressVelocity;
        float rippleTime = -10f;
        bool held, highlighted;

        /// <summary>
        /// Builds the button under <paramref name="parent"/>. Place the returned object's
        /// RectTransform with anchors; the button keeps itself round inside that area.
        /// </summary>
        public static TouchButton Create(Transform parent, string name, Color color, float alpha, bool primary)
        {
            var root = UIKit.Rect(parent, name);
            var button = root.gameObject.AddComponent<TouchButton>();
            button.primary = primary;

            // A square area that fits inside whatever rect the root is given.
            var square = UIKit.Rect(root, "Square");
            UIKit.Stretch(square);
            var fitter = square.gameObject.AddComponent<AspectRatioFitter>();
            fitter.aspectMode = AspectRatioFitter.AspectMode.FitInParent;
            fitter.aspectRatio = 1f;

            button.capColor = new Color(color.r, color.g, color.b, alpha);
            button.rimColor = new Color(color.r * 0.62f, color.g * 0.62f, color.b * 0.7f, Mathf.Min(1f, alpha + 0.1f));

            button.glow = Layer(square, "Glow", ProceduralSprites.SoftDisc, new Color(1f, 1f, 1f, 0f), -0.22f, 0f);
            button.glowRect = button.glow.rectTransform;
            button.shadow = Layer(square, "Shadow", ProceduralSprites.SoftDisc, new Color(0f, 0f, 0.05f, 0.35f * alpha + 0.1f), -0.06f, -0.09f);
            button.rim = Layer(square, "Rim", ProceduralSprites.Circle, button.rimColor, 0f, -0.075f);
            button.cap = Layer(square, "Cap", ProceduralSprites.Circle, button.capColor, 0f, 0f);
            button.capRect = button.cap.rectTransform;
            var edge = Layer(button.capRect, "Edge", ProceduralSprites.Ring, new Color(1f, 1f, 1f, 0.45f * alpha + 0.15f), 0f, 0f);
            edge.rectTransform.localScale = Vector3.one * 1.02f;
            button.gloss = Layer(button.capRect, "Gloss", ProceduralSprites.Gloss, new Color(1f, 1f, 1f, 0.5f), 0.08f, 0f);
            button.ripple = Layer(square, "Ripple", ProceduralSprites.Ring, new Color(1f, 1f, 1f, 0f), 0f, 0f);
            button.rippleRect = button.ripple.rectTransform;

            button.Content = UIKit.Rect(button.capRect, "Content");
            UIKit.Stretch(button.Content);
            return button;
        }

        /// <summary>A layer filling the square, inset by <paramref name="inset"/> (fraction of size), shifted down by <paramref name="drop"/>.</summary>
        static Image Layer(RectTransform parent, string name, Sprite sprite, Color color, float inset, float drop)
        {
            var image = UIKit.Icon(parent, name, sprite, color, 10f);
            var rt = image.rectTransform;
            rt.anchorMin = new Vector2(inset, inset + drop);
            rt.anchorMax = new Vector2(1f - inset, 1f - inset + drop);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            image.preserveAspect = false;
            return image;
        }

        /// <summary>An icon centred on the cap, sized as a fraction of the button, optionally turned.</summary>
        public Image AddIcon(Sprite sprite, Color color, float size, float angle = 0f, float y = 0.5f)
        {
            var icon = UIKit.Icon(Content, "Icon", sprite, color, 10f);
            var rt = icon.rectTransform;
            float h = size * 0.5f;
            rt.anchorMin = new Vector2(0.5f - h, y - h);
            rt.anchorMax = new Vector2(0.5f + h, y + h);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            rt.localRotation = Quaternion.Euler(0f, 0f, angle);
            var sh = icon.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0f, 0.3f);
            sh.effectDistance = new Vector2(0f, -4f);
            return icon;
        }

        /// <summary>A label across the lower part of the cap.</summary>
        public Text AddLabel(string text, int size)
        {
            var label = UIKit.Label(Content, "Label", text, size, Color.white, TextAnchor.MiddleCenter, true);
            var rt = label.rectTransform;
            rt.anchorMin = new Vector2(0f, 0.08f);
            rt.anchorMax = new Vector2(1f, 0.34f);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            var outline = label.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(0f, 0f, 0f, 0.35f);
            outline.effectDistance = new Vector2(2f, -2f);
            return label;
        }

        /// <summary>Called every frame by the HUD with the button's input state.</summary>
        public void SetState(bool isHeld, bool isHighlighted)
        {
            if (isHeld && !held)
            {
                rippleTime = Time.unscaledTime;
                Haptics.Press(primary);
            }
            else if (!isHeld && held)
            {
                Haptics.Release();
            }
            held = isHeld;
            highlighted = isHighlighted;
        }

        /// <summary>Tint for the cap (e.g. green while the ball is in reach).</summary>
        public void SetColor(Color color)
        {
            capColor = new Color(color.r, color.g, color.b, capColor.a);
            rimColor = new Color(color.r * 0.62f, color.g * 0.62f, color.b * 0.7f, rimColor.a);
        }

        void OnDisable()
        {
            held = false;
            press = 0f;
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            // Down fast, up with a little springy overshoot.
            float target = held ? 1f : 0f;
            if (held) press = Mathf.MoveTowards(press, 1f, dt * 22f);
            else press = Mathf.SmoothDamp(press, target, ref pressVelocity, 0.06f, Mathf.Infinity, dt);

            if (capRect != null)
            {
                float t = travel * press;
                capRect.anchorMin = new Vector2(0f, -t);
                capRect.anchorMax = new Vector2(1f, 1f - t);
                capRect.localScale = Vector3.one * (1f - 0.035f * press);
                cap.color = Color.Lerp(capColor, new Color(capColor.r * 0.82f, capColor.g * 0.82f, capColor.b * 0.86f, Mathf.Min(1f, capColor.a + 0.1f)), press);
                rim.color = rimColor;
                gloss.color = new Color(1f, 1f, 1f, Mathf.Lerp(0.5f, 0.28f, press));
                shadow.rectTransform.localScale = Vector3.one * (1f - 0.08f * press);
            }

            float rt = (Time.unscaledTime - rippleTime) / 0.38f;
            if (rt >= 0f && rt <= 1f)
            {
                rippleRect.localScale = Vector3.one * Mathf.Lerp(0.95f, 1.45f, 1f - (1f - rt) * (1f - rt));
                ripple.color = new Color(1f, 1f, 1f, 0.7f * (1f - rt));
            }
            else if (ripple != null)
            {
                ripple.color = new Color(1f, 1f, 1f, 0f);
            }

            if (glow != null)
            {
                float pulse = highlighted ? 0.35f + 0.25f * Mathf.Sin(Time.unscaledTime * 7f) : 0f;
                Color g = Color.Lerp(capColor, Color.white, 0.4f);
                glow.color = new Color(g.r, g.g, g.b, Mathf.MoveTowards(glow.color.a, pulse, dt * 4f));
                glowRect.localScale = Vector3.one * (1f + 0.04f * Mathf.Sin(Time.unscaledTime * 7f));
            }
        }
    }
}
