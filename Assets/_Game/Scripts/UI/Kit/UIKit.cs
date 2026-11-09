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
    /// layouts, in the game's clean anime look: slightly see-through white panels and
    /// bold buttons, each with a thin dark line round it like the characters' ink line,
    /// and titles lettered like the logo. Reference resolution is 1920x1080 matched on
    /// height, so layouts hold on any landscape phone (the canvas is 1440 wide at 4:3
    /// and about 2520 at 21:9).
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

        /// <summary>
        /// A row across the top of the parent: <paramref name="top"/> pixels down from its top
        /// edge, <paramref name="height"/> tall, inset <paramref name="left"/> and <paramref name="right"/>
        /// from its sides. Rows built this way stretch with the parent, so columns can be any width.
        /// </summary>
        public static RectTransform Row(Transform parent, string name, float top, float height, float left = 0f, float right = 0f)
        {
            var rt = Rect(parent, name);
            rt.anchorMin = new Vector2(0f, 1f);
            rt.anchorMax = new Vector2(1f, 1f);
            rt.pivot = new Vector2(0.5f, 1f);
            rt.offsetMin = new Vector2(left, -top - height);
            rt.offsetMax = new Vector2(-right, -top);
            return rt;
        }

        /// <summary>Let a label shrink (down to <paramref name="minSize"/>) rather than overflow its rect, e.g. for longer translations.</summary>
        public static Text Fit(Text text, int minSize)
        {
            text.resizeTextForBestFit = true;
            text.resizeTextMaxSize = text.fontSize;
            text.resizeTextMinSize = Mathf.Min(minSize, text.fontSize);
            text.verticalOverflow = VerticalWrapMode.Truncate;
            return text;
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

        /// <summary>
        /// A clean card: a face with a thin dark line round it over a soft drop shadow.
        /// Returns the face; put content on it.
        /// </summary>
        public static Image Card(Transform parent, string name, Color color)
        {
            var root = Rect(parent, name);
            var shadow = Panel(root, "Shadow", UITheme.Shadow);
            Stretch(shadow.rectTransform);
            shadow.rectTransform.offsetMin += new Vector2(6f, -10f);
            shadow.rectTransform.offsetMax += new Vector2(6f, -10f);
            shadow.raycastTarget = false;
            var face = Panel(root, "Face", color, ProceduralSprites.RoundedEdge);
            Stretch(face.rectTransform);
            return face;
        }

        /// <summary>
        /// A pane of frosted glass like the touch controls (UITheme.Glass under a thin bright rim, no
        /// shadow), for the in-play HUD: the street shows through it. Returns the face; put content on it,
        /// lettered with <see cref="GlassText"/>.
        /// </summary>
        public static Image Glass(Transform parent, string name, bool round = false, Color? tint = null)
        {
            var root = Rect(parent, name);
            var face = Panel(root, "Face", tint ?? UITheme.Glass, round ? ProceduralSprites.SoftEdgeDisc : ProceduralSprites.Rounded);
            if (round) face.type = Image.Type.Simple;
            Stretch(face.rectTransform);
            var rim = Panel(face.transform, "Rim", UITheme.GlassRim, round ? ProceduralSprites.ThinRing : ProceduralSprites.RoundedRim);
            if (round) rim.type = Image.Type.Simple;
            Stretch(rim.rectTransform);
            rim.raycastTarget = false;
            return face;
        }

        /// <summary>White lettering for glass: a soft dark drop so it reads over a bright sky or a white wall.</summary>
        public static Text GlassText(Text t)
        {
            if (t.GetComponent<Shadow>() == null)
            {
                var sh = t.gameObject.AddComponent<Shadow>();
                sh.effectColor = new Color(0f, 0.02f, 0.1f, 0.55f);
                sh.effectDistance = new Vector2(0f, -2.5f);
            }
            return t;
        }

        /// <summary>
        /// A glass button (a <see cref="Glass"/> pane tinted with <paramref name="color"/>, white lettering)
        /// that squishes when pressed, for buttons over the game: the tour's Next and Skip, "Stuck?", pause.
        /// </summary>
        public static Button GlassButton(Transform parent, string name, string label, Color color, UnityAction onClick,
            int fontSize = UITheme.SizeButton, bool round = false)
        {
            var face = Glass(parent, name, round, new Color(color.r, color.g, color.b, 0.42f));
            var root = face.transform.parent;
            if (!string.IsNullOrEmpty(label))
            {
                var text = GlassText(Label(face.transform, "Label", label, fontSize, UITheme.GlassInk, TextAnchor.MiddleCenter, true));
                Stretch(text.rectTransform, 8f);
                text.rectTransform.offsetMin = new Vector2(14f, 6f);
                text.rectTransform.offsetMax = new Vector2(-14f, -4f);
                Fit(text, Mathf.RoundToInt(fontSize * 0.7f));
            }
            var button = root.gameObject.AddComponent<UnityEngine.UI.Button>();
            button.targetGraphic = face;
            var colors = button.colors;
            colors.highlightedColor = new Color(1.1f, 1.1f, 1.1f);
            colors.pressedColor = new Color(1.3f, 1.3f, 1.3f);
            colors.disabledColor = new Color(0.7f, 0.7f, 0.7f, 0.5f);
            button.colors = colors;
            if (onClick != null) button.onClick.AddListener(onClick);
            root.gameObject.AddComponent<UIButtonFx>();
            return button;
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

        /// <summary>
        /// Big title text lettered like the logo (upright): a white face shading to pale sky,
        /// a navy extrusion and a dark outline, so it reads on any background. Tinting the
        /// Text's colour tints the face.
        /// </summary>
        public static Text Title(Transform parent, string name, string text, int size, Color color)
        {
            var t = Label(parent, name, text, size, color, TextAnchor.MiddleCenter, true);
            var fx = t.gameObject.AddComponent<UILogoText>();
            fx.skew = 0f;
            fx.faceTop = Color.white;
            fx.faceBottom = new Color(0.86f, 0.92f, 1f);
            float k = Mathf.Clamp(size / 64f, 0.6f, 2f);
            fx.innerLine = 2.5f * k;
            fx.extrude = 5f * k;
            fx.outline = 2.5f * k;
            fx.extrudeColor = UITheme.Navy;
            fx.outlineColor = UITheme.Ink;
            fx.shadowColor = new Color(0.03f, 0.06f, 0.2f, 0.25f);
            fx.shadowOffset = new Vector2(0f, -6f * k);
            return t;
        }

        /// <summary>
        /// A modal's heading: white lettering on a slanted navy ribbon with an orange stripe
        /// behind it, straddling the top edge of <paramref name="card"/>.
        /// </summary>
        public static Text Header(Transform card, string text, float width = 560f)
        {
            var ribbon = Rect(card, "Header");
            Place(ribbon, new Vector2(0.5f, 1f), new Vector2(0f, 6f), new Vector2(width, 96f), new Vector2(0.5f, 0.5f));
            var stripe = Panel(ribbon, "Stripe", UITheme.Accent, ProceduralSprites.RoundedEdgeSmall);
            Stretch(stripe.rectTransform);
            stripe.rectTransform.offsetMin += new Vector2(14f, -10f);
            stripe.rectTransform.offsetMax += new Vector2(14f, -10f);
            stripe.gameObject.AddComponent<UISkew>().skew = 0.32f;
            stripe.raycastTarget = false;
            var band = Panel(ribbon, "Band", UITheme.Navy, ProceduralSprites.RoundedEdgeSmall);
            Stretch(band.rectTransform);
            band.gameObject.AddComponent<UISkew>().skew = 0.32f;
            band.raycastTarget = false;
            var label = Label(band.transform, "Title", text, 58, Color.white, TextAnchor.MiddleCenter, true);
            Stretch(label.rectTransform, 6f);
            label.rectTransform.offsetMin = new Vector2(40f, 4f);
            label.rectTransform.offsetMax = new Vector2(-40f, -4f);
            Fit(label, 36);
            var sh = label.gameObject.AddComponent<Shadow>();
            sh.effectColor = new Color(0f, 0f, 0.1f, 0.45f);
            sh.effectDistance = new Vector2(0f, -4f);
            return label;
        }

        /// <summary>A small section heading: navy capitals after a short orange bar, left aligned in <paramref name="row"/>.</summary>
        public static Text SectionLabel(Transform row, string text)
        {
            var bar = Panel(row, "Bar", UITheme.Accent, ProceduralSprites.RoundedSmall);
            bar.rectTransform.anchorMin = new Vector2(0f, 0.2f);
            bar.rectTransform.anchorMax = new Vector2(0f, 0.8f);
            bar.rectTransform.pivot = new Vector2(0f, 0.5f);
            bar.rectTransform.sizeDelta = new Vector2(10f, 0f);
            bar.rectTransform.anchoredPosition = Vector2.zero;
            bar.gameObject.AddComponent<UISkew>().skew = 0.3f;
            bar.raycastTarget = false;
            var label = Label(row, "Label", text.ToUpperInvariant(), 30, UITheme.Navy, TextAnchor.MiddleLeft, true);
            Stretch(label.rectTransform);
            label.rectTransform.offsetMin = new Vector2(26f, 0f);
            Fit(label, 22);
            return label;
        }

        /// <summary>
        /// A bold rounded button with a thin dark line, standing on a darker lip like a key
        /// (it pushes down onto it), with a shine, a label and a squishy press.
        /// </summary>
        public static Button Button(Transform parent, string name, string label, Color color, UnityAction onClick,
            int fontSize = UITheme.SizeButton, Color? textColor = null)
        {
            var root = Rect(parent, name);

            var shadow = Panel(root, "Shadow", UITheme.Shadow);
            Stretch(shadow.rectTransform);
            shadow.rectTransform.offsetMin += new Vector2(4f, -UIButtonFx.Depth - 8f);
            shadow.rectTransform.offsetMax += new Vector2(4f, -UIButtonFx.Depth - 8f);
            shadow.raycastTarget = false;

            // The classic cartoon filter's ink rim round the whole key (hidden until CartoonButton turns it on).
            var inkRim = Panel(root, "Ink", CartoonButton.InkColor);
            Stretch(inkRim.rectTransform);
            inkRim.rectTransform.offsetMin += new Vector2(-4f, -UIButtonFx.Depth - 4f);
            inkRim.rectTransform.offsetMax += new Vector2(4f, 4f);
            inkRim.raycastTarget = false;
            inkRim.enabled = false;

            // A darker base under the face: the button stands like a key and pushes down onto it.
            var keyBase = Panel(root, "Base", UIButtonFx.BaseColor(color), ProceduralSprites.RoundedEdge);
            Stretch(keyBase.rectTransform);
            keyBase.rectTransform.offsetMin += new Vector2(0f, -UIButtonFx.Depth);
            keyBase.rectTransform.offsetMax += new Vector2(0f, -UIButtonFx.Depth);
            keyBase.raycastTarget = false;

            var face = Panel(root, "Face", color, ProceduralSprites.RoundedEdge);
            Stretch(face.rectTransform);

            // A soft band of light across the top half (a lit upper face, as in the cel shading).
            var shine = Panel(face.transform, "Shine", new Color(1f, 1f, 1f, 0.2f), ProceduralSprites.RoundedSmall);
            shine.rectTransform.anchorMin = new Vector2(0f, 0.52f);
            shine.rectTransform.anchorMax = new Vector2(1f, 1f);
            shine.rectTransform.offsetMin = new Vector2(9f, 0f);
            shine.rectTransform.offsetMax = new Vector2(-9f, -7f);
            shine.raycastTarget = false;

            if (!string.IsNullOrEmpty(label))
            {
                Color ink = textColor ?? Color.white;
                var text = Label(face.transform, "Label", label, fontSize, ink, TextAnchor.MiddleCenter, true);
                Stretch(text.rectTransform, 8f);
                text.rectTransform.offsetMin = new Vector2(14f, 6f);
                text.rectTransform.offsetMax = new Vector2(-14f, -4f);
                Fit(text, Mathf.RoundToInt(fontSize * 0.7f));
                var sh = text.gameObject.AddComponent<Shadow>();
                // White lettering gets a dark drop; dark lettering on white buttons a faint one.
                sh.effectColor = ink.grayscale > 0.5f ? new Color(0f, 0.02f, 0.12f, 0.35f) : new Color(0f, 0f, 0f, 0.1f);
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
            root.gameObject.AddComponent<CartoonButton>().Set(shadow, inkRim);
            return button;
        }

        /// <summary>Make a UIKit button round (circle faces with their dark line).</summary>
        public static void MakeRound(UnityEngine.UI.Button button)
        {
            foreach (var img in button.GetComponentsInChildren<Image>(true))
            {
                if (img.name == "Face" || img.name == "Base") { img.sprite = ProceduralSprites.CircleEdge; img.type = Image.Type.Simple; }
                else if (img.name == "Shadow" || img.name == "Ink") { img.sprite = ProceduralSprites.Circle; img.type = Image.Type.Simple; }
                if (img.name == "Shine") img.gameObject.SetActive(false);
            }
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
                var star = Icon(row, "Star" + i, ProceduralSprites.Star, i < filled ? UITheme.Gold : new Color(0.1f, 0.15f, 0.3f, 0.2f), size);
                Place(star.rectTransform, new Vector2(0f, 0.5f), new Vector2(i * (size + spacing), 0f), new Vector2(size, size), new Vector2(0f, 0.5f));
                if (i < filled)
                {
                    var o = star.gameObject.AddComponent<Outline>();
                    o.effectColor = new Color(0.45f, 0.28f, 0.02f, 0.9f);
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

        /// <summary>A slider (0..1): a grey track filling with the sky's blue, and a white knob with a dark line.</summary>
        public static Slider Slider(Transform parent, string name, float value, UnityAction<float> onChanged)
        {
            var root = Rect(parent, name);
            var track = Panel(root, "Track", UITheme.PaperDark, ProceduralSprites.RoundedEdgeSmall);
            track.rectTransform.anchorMin = new Vector2(0f, 0.34f);
            track.rectTransform.anchorMax = new Vector2(1f, 0.66f);
            track.rectTransform.offsetMin = track.rectTransform.offsetMax = Vector2.zero;

            var fillArea = Rect(root, "FillArea");
            fillArea.anchorMin = new Vector2(0f, 0.34f);
            fillArea.anchorMax = new Vector2(1f, 0.66f);
            fillArea.offsetMin = new Vector2(0f, 0f);
            fillArea.offsetMax = new Vector2(0f, 0f);
            var fill = Panel(fillArea, "Fill", UITheme.Blue, ProceduralSprites.RoundedEdgeSmall);
            fill.rectTransform.sizeDelta = Vector2.zero;

            var handleArea = Rect(root, "HandleArea");
            Stretch(handleArea);
            handleArea.offsetMin = new Vector2(28f, 0f);
            handleArea.offsetMax = new Vector2(-28f, 0f);
            var handle = Icon(handleArea, "Handle", ProceduralSprites.CircleEdge, Color.white, 64f);
            handle.raycastTarget = true;
            handle.rectTransform.sizeDelta = new Vector2(64f, 0f);
            handle.rectTransform.anchorMin = new Vector2(0f, 0.04f);
            handle.rectTransform.anchorMax = new Vector2(0f, 0.96f);
            var shadow = handle.gameObject.AddComponent<Shadow>();
            shadow.effectColor = UITheme.Shadow;
            shadow.effectDistance = new Vector2(0f, -4f);

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
            }, 34);
            return button;
        }

        /// <summary>
        /// Full-screen dimmer with a centred white card. Returns the card face; destroy the root
        /// to close. The card is never taller than the screen or wider than a 4:3 one.
        /// </summary>
        public static Image Modal(Transform parent, string name, Vector2 size, out GameObject root)
        {
            var dimRect = Stretch(Rect(parent, name));
            var dim = dimRect.gameObject.AddComponent<Image>();
            dim.color = UITheme.Dim;
            root = dimRect.gameObject;
            var card = Card(dimRect, "Card", UITheme.Panel);
            size = new Vector2(Mathf.Min(size.x, ReferenceResolution.y * 4f / 3f - 60f), Mathf.Min(size.y, ReferenceResolution.y - 80f));
            Place((RectTransform)card.transform.parent, new Vector2(0.5f, 0.5f), new Vector2(0f, -14f), size);
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
