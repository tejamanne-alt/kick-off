using DribbleToSchool.Audio;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// The look of the walk stick (GameInput reads it): a see-through ring of frosted glass with a knob on it, in the
    /// same quiet glass as the touch buttons. Small marks inside the ring say what it does: a chevron left and right
    /// (walk back, dribble forward) and the slide glyph at the bottom (pull down to slide). The ring comes to the thumb
    /// and the knob follows it; the mark the stick points to lights up. A light click when the thumb takes the stick,
    /// a firmer one when it slides. GameHud and the Holiday Run's HUD call <see cref="Show"/> every frame.
    /// </summary>
    public class StickView : MonoBehaviour
    {
        [Tooltip("Opacity of the ring's glass and rim at rest and while held.")]
        public float restGlass = 0.06f, heldGlass = 0.16f;
        public float restRim = 0.28f, heldRim = 0.6f;
        [Tooltip("Opacity of the knob at rest and while held.")]
        public float restKnob = 0.2f, heldKnob = 0.5f;
        [Tooltip("Opacity of the direction marks at rest, and of the one the stick points to.")]
        public float restMark = 0.26f, litMark = 0.85f;
        [Tooltip("How far the knob's centre travels from the ring's, as a part of the ring's size.")]
        public float knobTravel = 0.34f;

        RectTransform root, knobRect;
        Image glass, rim, knob, knobRim, left, right, down;
        float held, knobSize = 0.44f;
        bool wasActive, wasDown;

        /// <summary>Builds the stick under <paramref name="parent"/>; place it with <see cref="Show"/>.</summary>
        public static StickView Create(Transform parent, string name)
        {
            var rt = UIKit.Rect(parent, name);
            var view = rt.gameObject.AddComponent<StickView>();
            view.root = rt;
            view.glass = Layer(rt, "Glass", ProceduralSprites.SoftEdgeDisc, 0f);
            view.rim = Layer(rt, "Rim", ProceduralSprites.Ring, 0f);
            view.knobRect = UIKit.Rect(rt, "Knob");
            view.knob = Layer(view.knobRect, "Glass", ProceduralSprites.SoftEdgeDisc, 0f);
            view.knobRim = Layer(view.knobRect, "Rim", ProceduralSprites.Ring, 0.04f);
            // The marks go over the knob, so the one it is pushed onto still shows lit through the thumb's side of it.
            view.left = Mark(rt, "Left", ProceduralSprites.Chevron, new Vector2(0.15f, 0.5f), 0.13f, 180f);
            view.right = Mark(rt, "Right", ProceduralSprites.Chevron, new Vector2(0.85f, 0.5f), 0.13f, 0f);
            view.down = Mark(rt, "Down", ProceduralSprites.SlideIcon, new Vector2(0.5f, 0.15f), 0.17f, 0f);
            return view;
        }

        static Image Layer(RectTransform parent, string name, Sprite sprite, float inset)
        {
            var image = UIKit.Icon(parent, name, sprite, new Color(1f, 1f, 1f, 0f), 10f);
            var rt = image.rectTransform;
            rt.anchorMin = new Vector2(inset, inset);
            rt.anchorMax = new Vector2(1f - inset, 1f - inset);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            image.preserveAspect = false;
            image.raycastTarget = false;
            return image;
        }

        static Image Mark(RectTransform parent, string name, Sprite sprite, Vector2 at, float size, float angle)
        {
            var image = UIKit.Icon(parent, name, sprite, new Color(1f, 1f, 1f, 0f), 10f);
            var rt = image.rectTransform;
            rt.anchorMin = at - Vector2.one * size * 0.5f;
            rt.anchorMax = at + Vector2.one * size * 0.5f;
            rt.offsetMin = rt.offsetMax = Vector2.zero;
            rt.localRotation = Quaternion.Euler(0f, 0f, angle);
            image.raycastTarget = false;
            var sh = image.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0f, 0.18f);
            sh.effectDistance = new Vector2(0f, -2f);
            return image;
        }

        /// <summary>
        /// Puts the ring at <paramref name="ring"/> (a normalized screen rect, origin bottom-left) with the knob at
        /// <paramref name="stick"/> (a part of the radius each way) and lights the mark it points to:
        /// <paramref name="move"/> -1 / 0 / 1 and <paramref name="pulledDown"/> for the slide.
        /// </summary>
        public void Show(Rect ring, Vector2 stick, float knobScale, bool active, float move, bool pulledDown)
        {
            if (root == null) return;
            root.anchorMin = new Vector2(ring.xMin, ring.yMin);
            root.anchorMax = new Vector2(ring.xMax, ring.yMax);
            root.offsetMin = root.offsetMax = Vector2.zero;
            knobSize = knobScale;

            if (active && !wasActive) Haptics.Press(false);
            else if (!active && wasActive) Haptics.Release();
            if (pulledDown && !wasDown) Haptics.Press(true);
            wasActive = active;
            wasDown = pulledDown;

            Vector2 c = new Vector2(0.5f, 0.5f) + (active ? stick : Vector2.zero) * knobTravel;
            knobRect.anchorMin = c - Vector2.one * knobSize * 0.5f;
            knobRect.anchorMax = c + Vector2.one * knobSize * 0.5f;
            knobRect.offsetMin = knobRect.offsetMax = Vector2.zero;

            float dt = Time.unscaledDeltaTime;
            held = Mathf.MoveTowards(held, active ? 1f : 0f, dt * (active ? 14f : 5f));
            SetAlpha(glass, Mathf.Lerp(restGlass, heldGlass, held));
            SetAlpha(rim, Mathf.Lerp(restRim, heldRim, held));
            SetAlpha(knob, Mathf.Lerp(restKnob, heldKnob, held));
            SetAlpha(knobRim, Mathf.Lerp(restRim * 0.7f, heldRim, held));
            Light(left, active && move < 0f && !pulledDown);
            Light(right, active && move > 0f && !pulledDown);
            Light(down, active && pulledDown);
        }

        void Light(Image mark, bool lit)
        {
            float target = lit ? litMark : restMark;
            SetAlpha(mark, Mathf.MoveTowards(mark.color.a, target, Time.unscaledDeltaTime * 6f));
        }

        static void SetAlpha(Image image, float alpha)
        {
            Color c = image.color;
            c.a = alpha;
            image.color = c;
        }

        /// <summary>Lets go: a run that ended with a thumb on the stick must not leave it looking held.</summary>
        public void Release()
        {
            wasActive = wasDown = false;
            held = 0f;
        }
    }
}
