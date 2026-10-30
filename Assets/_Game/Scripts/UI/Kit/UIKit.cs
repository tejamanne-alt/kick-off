using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.UI;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem.UI;
#endif

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Builds uGUI from code: canvases, panels, labels, buttons, icons and simple
    /// layouts, all in the storybook theme. Reference resolution is 1920x1080
    /// matched on height, so layouts hold on any landscape phone.
    /// </summary>
    public static class UIKit
    {
        public static readonly Vector2 ReferenceResolution = new Vector2(1920f, 1080f);

        public static Canvas CreateCanvas(string name, int sortingOrder)
        {
            EnsureEventSystem();
            var go = new GameObject(name, typeof(RectTransform));
            var canvas = go.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = sortingOrder;
            var scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = ReferenceResolution;
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 1f;
            go.AddComponent<GraphicRaycaster>();
            return canvas;
        }

        public static void EnsureEventSystem()
        {
            if (Object.FindAnyObjectByType<EventSystem>() != null) return;
            var go = new GameObject("EventSystem");
            go.AddComponent<EventSystem>();
#if ENABLE_INPUT_SYSTEM
            // Added at runtime, the module has no UI actions until we give it the defaults.
            go.AddComponent<InputSystemUIInputModule>().AssignDefaultActions();
#else
            go.AddComponent<StandaloneInputModule>();
#endif
        }

        // ---------- Layout primitives ----------

        public static RectTransform Rect(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            return (RectTransform)go.transform;
        }

        /// <summary>Fill the parent, inset by <paramref name="inset"/> pixels.</summary>
        public static RectTransform Stretch(RectTransform rt, float inset = 0f)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = new Vector2(inset, inset);
            rt.offsetMax = new Vector2(-inset, -inset);
            return rt;
        }

        /// <summary>Anchor to a normalized point of the parent with a fixed size.</summary>
        public static RectTransform Place(RectTransform rt, Vector2 anchor, Vector2 position, Vector2 size, Vector2? pivot = null)
        {
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = pivot ?? anchor;
            rt.anchoredPosition = position;
            rt.sizeDelta = size;
            return rt;
        }

        // ---------- Visual elements ----------

        public static Image Panel(Transform parent, string name, Color color, Sprite sprite = null)
        {
            var rt = Rect(parent, name);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sprite != null ? sprite : ProceduralSprites.Rounded;
            img.type = Image.Type.Sliced;
            img.color = color;
            return img;
        }

        /// <summary>A paper card with a soft drop shadow. Returns the face; put content on it.</summary>
        public static Image Card(Transform parent, string name, Color color)
        {
            var root = Rect(parent, name);
            var shadow = Panel(root, "Shadow", UITheme.Shadow);
            Stretch(shadow.rectTransform);
            shadow.rectTransform.offsetMin += new Vector2(0f, -10f);
            shadow.rectTransform.offsetMax += new Vector2(0f, -10f);
            shadow.raycastTarget = false;
            var face = Panel(root, "Face", color);
            Stretch(face.rectTransform);
            return face;
        }

        public static Image Icon(Transform parent, string name, Sprite sprite, Color color, float size)
        {
            var rt = Rect(parent, name);
            rt.sizeDelta = new Vector2(size, size);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sprite;
            img.color = color;
            img.preserveAspect = true;
            img.raycastTarget = false;
            return img;
        }

        public static Text Label(Transform parent, string name, string text, int size, Color color,
            TextAnchor align = TextAnchor.MiddleCenter, bool bold = false)
        {
            var rt = Rect(parent, name);
            var t = rt.gameObject.AddComponent<Text>();
            // "Bold" text uses the display face rather than a faked bold of the body face.
            t.font = bold ? UITheme.Display : UITheme.Font;
            t.text = text;
            t.fontSize = size;
            t.color = color;
            t.alignment = align;
            t.fontStyle = FontStyle.Normal;
            t.lineSpacing = bold ? 0.95f : 1.05f;
            t.horizontalOverflow = HorizontalWrapMode.Wrap;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        /// <summary>Big title text with a soft ink outline so it reads on any background.</summary>
        public static Text Title(Transform parent, string name, string text, int size, Color color)
        {
            var t = Label(parent, name, text, size, color, TextAnchor.MiddleCenter, true);
            var outline = t.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(UITheme.Ink.r, UITheme.Ink.g, UITheme.Ink.b, 0.85f);
            outline.effectDistance = new Vector2(3f, -3f);
            var shadow = t.gameObject.AddComponent<Shadow>();
            shadow.effectColor = UITheme.Shadow;
            shadow.effectDistance = new Vector2(0f, -8f);
            return t;
        }

        /// <summary>A chunky rounded button with a shadow, label and squishy press.</summary>
        public static Button Button(Transform parent, string name, string label, Color color, UnityAction onClick,
            int fontSize = UITheme.SizeButton, Color? textColor = null)
        {
            var root = Rect(parent, name);

            var shadow = Panel(root, "Shadow", UITheme.Shadow);
            Stretch(shadow.rectTransform);
            shadow.rectTransform.offsetMin += new Vector2(0f, -15f);
            shadow.rectTransform.offsetMax += new Vector2(0f, -15f);
            shadow.raycastTarget = false;

            // A darker base under the face: the button stands like a key and pushes down onto it.
            var keyBase = Panel(root, "Base", UIButtonFx.BaseColor(color));
            Stretch(keyBase.rectTransform);
            keyBase.rectTransform.offsetMin += new Vector2(0f, -UIButtonFx.Depth);
            keyBase.rectTransform.offsetMax += new Vector2(0f, -UIButtonFx.Depth);
            keyBase.raycastTarget = false;

            var face = Panel(root, "Face", color);
            Stretch(face.rectTransform);

            var shine = Panel(face.transform, "Shine", new Color(1f, 1f, 1f, 0.18f));
            shine.rectTransform.anchorMin = new Vector2(0f, 0.55f);
            shine.rectTransform.anchorMax = new Vector2(1f, 1f);
            shine.rectTransform.offsetMin = new Vector2(10f, 0f);
            shine.rectTransform.offsetMax = new Vector2(-10f, -8f);
            shine.raycastTarget = false;

            if (!string.IsNullOrEmpty(label))
            {
                var text = Label(face.transform, "Label", label, fontSize, textColor ?? Color.white, TextAnchor.MiddleCenter, true);
                Stretch(text.rectTransform, 8f);
                var sh = text.gameObject.AddComponent<Shadow>();
                sh.effectColor = new Color(0f, 0f, 0f, 0.25f);
                sh.effectDistance = new Vector2(0f, -3f);
            }

            var button = root.gameObject.AddComponent<UnityEngine.UI.Button>();
            button.targetGraphic = face;
            var colors = button.colors;
            colors.highlightedColor = new Color(1.05f, 1.05f, 1.05f);
            colors.pressedColor = new Color(0.88f, 0.88f, 0.88f);
            colors.disabledColor = new Color(0.7f, 0.7f, 0.7f, 0.6f);
            button.colors = colors;
            if (onClick != null) button.onClick.AddListener(onClick);
            root.gameObject.AddComponent<UIButtonFx>();
            return button;
        }

        /// <summary>Coin icon followed by a number, e.g. for prices and the wallet.</summary>
        public static Text CoinAmount(Transform parent, string name, int amount, int size, Color color)
        {
            var row = Rect(parent, name);
            var layout = row.gameObject.AddComponent<HorizontalLayoutGroup>();
            layout.childAlignment = TextAnchor.MiddleCenter;
            layout.spacing = size * 0.25f;
            layout.childForceExpandWidth = false;
            layout.childForceExpandHeight = false;
            layout.childControlWidth = true;
            layout.childControlHeight = true;

            var icon = Icon(row, "Coin", ProceduralSprites.Coin, Color.white, size);
            var le = icon.gameObject.AddComponent<LayoutElement>();
            le.preferredWidth = size;
            le.preferredHeight = size;

            var text = Label(row, "Amount", amount.ToString(), size, color, TextAnchor.MiddleLeft, true);
            var fitter = text.gameObject.AddComponent<ContentSizeFitter>();
            fitter.horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
            return text;
        }

        /// <summary>Row of three stars, the first <paramref name="filled"/> golden.</summary>
        public static RectTransform Stars(Transform parent, string name, int filled, float size, float spacing = 6f)
        {
            var row = Rect(parent, name);
            row.sizeDelta = new Vector2(size * 3f + spacing * 2f, size);
            for (int i = 0; i < 3; i++)
            {
                var star = Icon(row, "Star" + i, ProceduralSprites.Star, i < filled ? UITheme.Gold : new Color(0f, 0f, 0f, 0.18f), size);
                Place(star.rectTransform, new Vector2(0f, 0.5f), new Vector2(i * (size + spacing), 0f), new Vector2(size, size), new Vector2(0f, 0.5f));
                if (i < filled)
                {
                    var o = star.gameObject.AddComponent<Outline>();
                    o.effectColor = new Color(0.6f, 0.4f, 0.05f, 0.8f);
                    o.effectDistance = new Vector2(2f, -2f);
                }
            }
            return row;
        }

        /// <summary>Make <paramref name="child"/> pop in when shown.</summary>
        public static UIPopIn PopIn(GameObject child, float delay = 0f)
        {
            if (child.GetComponent<CanvasGroup>() == null) child.AddComponent<CanvasGroup>();
            var pop = child.AddComponent<UIPopIn>();
            pop.delay = delay;
            return pop;
        }

        /// <summary>A chunky slider (0..1) in the storybook style.</summary>
        public static Slider Slider(Transform parent, string name, float value, UnityAction<float> onChanged)
        {
            var root = Rect(parent, name);
            var track = Panel(root, "Track", UITheme.PaperDark, ProceduralSprites.RoundedSmall);
            track.rectTransform.anchorMin = new Vector2(0f, 0.35f);
            track.rectTransform.anchorMax = new Vector2(1f, 0.65f);
            track.rectTransform.offsetMin = track.rectTransform.offsetMax = Vector2.zero;

            var fillArea = Rect(root, "FillArea");
            fillArea.anchorMin = new Vector2(0f, 0.35f);
            fillArea.anchorMax = new Vector2(1f, 0.65f);
            fillArea.offsetMin = new Vector2(0f, 0f);
            fillArea.offsetMax = new Vector2(0f, 0f);
            var fill = Panel(fillArea, "Fill", UITheme.Accent, ProceduralSprites.RoundedSmall);
            fill.rectTransform.sizeDelta = Vector2.zero;

            var handleArea = Rect(root, "HandleArea");
            Stretch(handleArea);
            handleArea.offsetMin = new Vector2(30f, 0f);
            handleArea.offsetMax = new Vector2(-30f, 0f);
            var handle = Icon(handleArea, "Handle", ProceduralSprites.Circle, Color.white, 70f);
            handle.raycastTarget = true;
            handle.rectTransform.sizeDelta = new Vector2(70f, 0f);
            handle.rectTransform.anchorMin = new Vector2(0f, 0f);
            handle.rectTransform.anchorMax = new Vector2(0f, 1f);
            var outline = handle.gameObject.AddComponent<Outline>();
            outline.effectColor = UITheme.Ink;
            outline.effectDistance = new Vector2(3f, -3f);

            var slider = root.gameObject.AddComponent<UnityEngine.UI.Slider>();
            slider.fillRect = fill.rectTransform;
            slider.handleRect = handle.rectTransform;
            slider.targetGraphic = handle;
            slider.direction = UnityEngine.UI.Slider.Direction.LeftToRight;
            slider.minValue = 0f;
            slider.maxValue = 1f;
            slider.value = value;
            if (onChanged != null) slider.onValueChanged.AddListener(onChanged);
            return slider;
        }

        /// <summary>On/Off pill. Calls <paramref name="onChanged"/> with the new state and updates itself.</summary>
        public static Button Toggle(Transform parent, string name, bool value, System.Func<bool, string> label, UnityAction<bool> onChanged)
        {
            bool state = value;
            Button button = null;
            button = Button(parent, name, label(state), state ? UITheme.Green : UITheme.Locked, () =>
            {
                state = !state;
                button.targetGraphic.color = state ? UITheme.Green : UITheme.Locked;
                button.GetComponentInChildren<Text>().text = label(state);
                if (onChanged != null) onChanged(state);
            }, 36);
            return button;
        }

        /// <summary>Full-screen dimmer with a centred paper card. Returns the card face; destroy the root to close.</summary>
        public static Image Modal(Transform parent, string name, Vector2 size, out GameObject root)
        {
            var dimRect = Stretch(Rect(parent, name));
            var dim = dimRect.gameObject.AddComponent<Image>();
            dim.color = UITheme.Dim;
            root = dimRect.gameObject;
            var card = Card(dimRect, "Card", UITheme.Paper);
            Place((RectTransform)card.transform.parent, new Vector2(0.5f, 0.5f), Vector2.zero, size);
            PopIn(card.transform.parent.gameObject);
            return card;
        }

        /// <summary>Scrollable area. Returns the content rect to fill.</summary>
        public static RectTransform ScrollArea(Transform parent, string name, bool vertical, out ScrollRect scroll)
        {
            var root = Rect(parent, name);
            var viewport = Rect(root, "Viewport");
            Stretch(viewport);
            viewport.gameObject.AddComponent<RectMask2D>();
            var hit = viewport.gameObject.AddComponent<Image>();
            hit.color = Color.clear;

            var content = Rect(viewport, "Content");
            if (vertical)
            {
                content.anchorMin = new Vector2(0f, 1f);
                content.anchorMax = new Vector2(1f, 1f);
                content.pivot = new Vector2(0.5f, 1f);
            }
            else
            {
                content.anchorMin = new Vector2(0f, 0f);
                content.anchorMax = new Vector2(0f, 1f);
                content.pivot = new Vector2(0f, 0.5f);
            }
            content.sizeDelta = Vector2.zero;

            scroll = root.gameObject.AddComponent<ScrollRect>();
            scroll.viewport = viewport;
            scroll.content = content;
            scroll.horizontal = !vertical;
            scroll.vertical = vertical;
            scroll.movementType = ScrollRect.MovementType.Elastic;
            scroll.scrollSensitivity = 40f;
            return content;
        }
    }
}
