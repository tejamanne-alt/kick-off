using DribbleToSchool.Audio;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// The look of an on-screen game control (walk, kick, jump): a see-through disc of
    /// frosted glass with a soft white icon, no border and only a hint of colour, so the
    /// game shows through and the controls stay out of the way. Holding it brightens the
    /// glass a little, shrinks it slightly and fires a crisp haptic click; letting go eases
    /// it back with a soft tap. A faint ripple spreads on each press, and a soft halo can
    /// pulse to say "now" (the kick button while the ball is in reach).
    /// GameInput reads the touches; GameHud tells this component when it is held.
    /// </summary>
    public class TouchButton : MonoBehaviour
    {
        [Tooltip("Main actions (kick, jump) click harder than the walk buttons.")]
        public bool primary = true;
        [Tooltip("Opacity of the glass at rest and while held.")]
        public float restAlpha = 0.14f;
        public float heldAlpha = 0.3f;

        public RectTransform Content { get; private set; }

        Image glass, ripple, halo;
        RectTransform discRect, rippleRect;
        Color tint;
        float press, pressVelocity;
        float rippleTime = -10f;
        bool held, highlighted;
        Graphic[] contentGraphics;
        float[] contentAlpha;

        /// <summary>
        /// Builds the button under <paramref name="parent"/>. Place the returned object's
        /// RectTransform with anchors; the button keeps itself round inside that area.
        /// <paramref name="color"/> only tints the glass faintly.
        /// </summary>
        public static TouchButton Create(Transform parent, string name, Color color, bool primary)
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

            // Mostly white with a touch of the button's colour: reads on bright and dark scenes.
            button.tint = Color.Lerp(Color.white, color, 0.25f);

            button.halo = Layer(square, "Halo", ProceduralSprites.SoftDisc, new Color(1f, 1f, 1f, 0f), -0.2f);
            button.discRect = UIKit.Rect(square, "Disc");
            UIKit.Stretch(button.discRect);
            button.glass = Layer(button.discRect, "Glass", ProceduralSprites.SoftEdgeDisc, new Color(button.tint.r, button.tint.g, button.tint.b, button.restAlpha), 0f);
            button.ripple = Layer(square, "Ripple", ProceduralSprites.Ring, new Color(1f, 1f, 1f, 0f), 0f);
            button.rippleRect = button.ripple.rectTransform;

            button.Content = UIKit.Rect(button.discRect, "Content");
            UIKit.Stretch(button.Content);
            return button;
        }

        /// <summary>A layer filling the square, inset by <paramref name="inset"/> (fraction of size).</summary>
        static Image Layer(RectTransform parent, string name, Sprite sprite, Color color, float inset)
        {
            var image = UIKit.Icon(parent, name, sprite, color, 10f);
            var rt = image.rectTransform;
            rt.anchorMin = new Vector2(inset, inset);
            rt.anchorMax = new Vector2(1f - inset, 1f - inset);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            image.preserveAspect = false;
            return image;
        }

        /// <summary>A soft white icon centred on the disc, sized as a fraction of the button, optionally turned.</summary>
        public Image AddIcon(Sprite sprite, float size, float angle = 0f, float y = 0.5f, Color? color = null)
        {
            var icon = UIKit.Icon(Content, "Icon", sprite, color ?? new Color(1f, 1f, 1f, 0.8f), 10f);
            var rt = icon.rectTransform;
            float h = size * 0.5f;
            rt.anchorMin = new Vector2(0.5f - h, y - h);
            rt.anchorMax = new Vector2(0.5f + h, y + h);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            rt.localRotation = Quaternion.Euler(0f, 0f, angle);
            // A faint shadow keeps it legible over bright sky and pavement.
            var sh = icon.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0f, 0.18f);
            sh.effectDistance = new Vector2(0f, -2f);
            contentGraphics = null;
            return icon;
        }

        /// <summary>A small, quiet label across the lower part of the disc.</summary>
        public Text AddLabel(string text, int size)
        {
            var label = UIKit.Label(Content, "Label", text, size, new Color(1f, 1f, 1f, 0.7f), TextAnchor.MiddleCenter, true);
            var rt = label.rectTransform;
            rt.anchorMin = new Vector2(0f, 0.1f);
            rt.anchorMax = new Vector2(1f, 0.32f);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            var sh = label.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0f, 0.18f);
            sh.effectDistance = new Vector2(0f, -2f);
            contentGraphics = null;
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

        /// <summary>Faint tint for the glass and halo (e.g. green while the ball is in reach).</summary>
        public void SetColor(Color color)
        {
            tint = Color.Lerp(Color.white, color, 0.35f);
        }

        void OnDisable()
        {
            held = false;
            press = 0f;
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            // Down fast, back up softly.
            if (held) press = Mathf.MoveTowards(press, 1f, dt * 22f);
            else press = Mathf.SmoothDamp(press, 0f, ref pressVelocity, 0.07f, Mathf.Infinity, dt);

            if (discRect != null)
            {
                discRect.localScale = Vector3.one * (1f - 0.07f * press);
                glass.color = new Color(tint.r, tint.g, tint.b, Mathf.Lerp(restAlpha, heldAlpha, press));
                FadeContent(Mathf.Lerp(1f, 1.2f, press));
            }

            float rt = (Time.unscaledTime - rippleTime) / 0.4f;
            if (rt >= 0f && rt <= 1f)
            {
                rippleRect.localScale = Vector3.one * Mathf.Lerp(0.9f, 1.3f, 1f - (1f - rt) * (1f - rt));
                ripple.color = new Color(1f, 1f, 1f, 0.35f * (1f - rt));
            }
            else if (ripple != null)
            {
                ripple.color = new Color(1f, 1f, 1f, 0f);
            }

            if (halo != null)
            {
                float pulse = highlighted ? 0.22f + 0.12f * Mathf.Sin(Time.unscaledTime * 6f) : 0f;
                halo.color = new Color(tint.r, tint.g, tint.b, Mathf.MoveTowards(halo.color.a, pulse, dt * 3f));
            }
        }

        /// <summary>Icons and labels brighten a little while held.</summary>
        void FadeContent(float k)
        {
            if (contentGraphics == null)
            {
                contentGraphics = Content.GetComponentsInChildren<Graphic>();
                contentAlpha = new float[contentGraphics.Length];
                for (int i = 0; i < contentGraphics.Length; i++) contentAlpha[i] = contentGraphics[i].color.a;
            }
            for (int i = 0; i < contentGraphics.Length; i++)
            {
                var g = contentGraphics[i];
                if (g == null || g.name == "AimKnob") continue;
                Color c = g.color;
                c.a = Mathf.Min(1f, contentAlpha[i] * k);
                g.color = c;
            }
        }
    }
}
