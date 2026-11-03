using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Pan and zoom for a big picture (the town map) shown in this rect, the view: drag with one finger (or the mouse) to move
    /// it, pinch with two (or the mouse wheel) to zoom about the fingers, and <see cref="ZoomBy"/> / <see cref="Fit"/> for the
    /// screen's + / - and fit buttons, which glide there. At zoom 1 the part of the picture that matters (<see cref="fitRect"/>)
    /// fits the room the view leaves between the screen's bars (<see cref="insets"/>); it can be zoomed in to
    /// <see cref="maxZoom"/> times that, and the picture (<see cref="coverRect"/>) never slides off the view where it is big enough
    /// to cover it. A drag that starts on a button of the picture (a level's node) moves the map and does not press the button; a
    /// tap still presses it. <see cref="Changed"/> tells the screen the zoom, so the things drawn on the picture can keep a size
    /// that suits it (<see cref="MapViewMath.ItemScale"/>). Follows the view's size when the screen turns.
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class UIMapView : MonoBehaviour, IInitializePotentialDragHandler, IBeginDragHandler, IDragHandler, IEndDragHandler, IScrollHandler
    {
        [Tooltip("The picture's block: centred anchors and pivot, sized to the design, a child of this view.")]
        public RectTransform content;
        public Vector2 designSize = new Vector2(3200f, 1800f);
        [Tooltip("The part of the picture fitted at zoom 1 (design pixels, y down).")]
        public Rect fitRect = new Rect(0f, 0f, 3200f, 1800f);
        [Tooltip("The part of the picture that keeps covering the view where it can (design pixels, y down).")]
        public Rect coverRect = new Rect(0f, 0f, 3200f, 1800f);
        [Tooltip("The room the fit leaves for the screen's bars, in canvas units: left, bottom, right, top.")]
        public Vector4 insets;
        [Tooltip("How far in the view zooms, as a multiple of the fitted scale.")]
        public float maxZoom = 3f;
        [Tooltip("Never more than this many canvas units a picture pixel (the picture gets soft beyond it), unless the fit is already near it.")]
        public float maxScale = 1.6f;
        [Tooltip("Seconds a button's zoom or a fit takes to glide there.")]
        public float glide = 0.22f;
        [Tooltip("How much bigger than the fit (a fraction) the fitted view may be so that the picture fills the screen to its edges.")]
        public float coverSlack = 0.05f;

        /// <summary>The zoom against the fitted scale (1 = fitted) and the scale itself, whenever either changes.</summary>
        public event Action<float, float> Changed;

        public float Zoom { get { return fitScale > 0f ? scale / fitScale : 1f; } }
        public float FitScale { get { return fitScale; } }
        public float Scale { get { return scale; } }
        /// <summary>How far in the view can zoom now, as a multiple of the fitted scale.</summary>
        public float MaxZoom { get { return fitScale > 0f ? MaxScaleNow / fitScale : maxZoom; } }

        float scale = 1f, fitScale = 1f;
        Vector2 position;
        Vector2 lastView;
        bool fitted;
        // A glide toward a target view (buttons, fit), and the drift after a fling.
        bool gliding;
        float glideFrom, glideTo, glideT;
        Vector2 glideFromPos, glideToPos;
        Vector2 velocity;
        float reportedZoom = -1f, reportedScale = -1f;
        readonly Dictionary<int, Vector2> pointers = new Dictionary<int, Vector2>();
        float pinchDistance;
        Vector2 pinchMiddle;

        RectTransform View { get { return (RectTransform)transform; } }

        float MaxScaleNow { get { return Mathf.Max(fitScale * Mathf.Min(1.5f, maxZoom), Mathf.Min(fitScale * maxZoom, maxScale)); } }

        /// <summary>The middle of the room left between the bars, in the view (canvas units, y up from the view's middle).</summary>
        Vector2 RoomCentre { get { return new Vector2((insets.x - insets.z) * 0.5f, (insets.y - insets.w) * 0.5f); } }

        Vector2 Room(Vector2 view) { return new Vector2(view.x - insets.x - insets.z, view.y - insets.y - insets.w); }

        void OnEnable()
        {
            fitted = false;
            pointers.Clear();
            velocity = Vector2.zero;
        }

        void LateUpdate()
        {
            Vector2 view = View.rect.size;
            if (view.x <= 1f || view.y <= 1f || content == null) return;
            if (!fitted || (view - lastView).sqrMagnitude > 1f)
            {
                // A first size, or the screen turned: fit again, keeping the zoom the player had.
                float zoom = fitted ? Zoom : 1f;
                lastView = view;
                fitScale = MapViewMath.FitScale(Room(view), fitRect, view, coverRect, coverSlack);
                Vector2 keep = fitted ? MapViewMath.ToDesign(designSize, RoomCentre, scale, position) : fitRect.center;
                scale = Mathf.Clamp(fitScale * zoom, fitScale, MaxScaleNow);
                position = MapViewMath.PositionFor(designSize, keep, RoomCentre, scale);
                fitted = true;
                gliding = false;
            }
            float dt = Time.unscaledDeltaTime;
            if (gliding)
            {
                glideT += dt / Mathf.Max(0.01f, glide);
                float t = Mathf.Clamp01(glideT);
                t = t * t * (3f - 2f * t);
                // The scale eases in its own measure (a zoom feels even when the scale moves by the same ratio each frame).
                scale = Mathf.Exp(Mathf.Lerp(Mathf.Log(glideFrom), Mathf.Log(glideTo), t));
                position = Vector2.Lerp(glideFromPos, glideToPos, t);
                if (glideT >= 1f) gliding = false;
            }
            else if (pointers.Count == 0 && velocity.sqrMagnitude > 1f)
            {
                // The drift after a fling, slowing to a stop.
                position += velocity * dt;
                velocity *= Mathf.Exp(-5f * dt);
            }
            position = MapViewMath.ClampPosition(designSize, coverRect, view, scale, position, MapViewMath.PositionFor(designSize, coverRect.center, RoomCentre, scale));
            Apply();
        }

        void Apply()
        {
            if (content == null) return;
            if (!Mathf.Approximately(content.localScale.x, scale)) content.localScale = new Vector3(scale, scale, 1f);
            if (content.anchoredPosition != position) content.anchoredPosition = position;
            float zoom = Zoom;
            if (Mathf.Abs(zoom - reportedZoom) > 1e-4f || Mathf.Abs(scale - reportedScale) > 1e-5f)
            {
                reportedZoom = zoom;
                reportedScale = scale;
                if (Changed != null) Changed(zoom, scale);
            }
        }

        // ------------------------------------------------------------------ the buttons

        /// <summary>Zoom in (factor above 1) or out about the middle of the room, gliding there.</summary>
        public void ZoomBy(float factor)
        {
            if (!fitted) return;
            float to = Mathf.Clamp((gliding ? glideTo : scale) * factor, fitScale, MaxScaleNow);
            Vector2 from = gliding ? glideToPos : position;
            float fromScale = gliding ? glideTo : scale;
            GlideTo(to, MapViewMath.ZoomAbout(from, fromScale, to, RoomCentre));
        }

        /// <summary>Back to the fitted view, gliding there (or at once, when the screen is opened).</summary>
        public void Fit(bool instant = false)
        {
            if (instant || !fitted)
            {
                // Fitted afresh at the next frame (the view may not have its size yet).
                fitted = false;
                gliding = false;
                velocity = Vector2.zero;
                return;
            }
            GlideTo(fitScale, MapViewMath.PositionFor(designSize, fitRect.center, RoomCentre, fitScale));
        }

        /// <summary>Glide so that a point of the picture (design pixels) comes to the middle of the room, at least at <paramref name="zoom"/>.</summary>
        public void Show(Vector2 designPoint, float zoom)
        {
            if (!fitted) return;
            float to = Mathf.Clamp(Mathf.Max(scale, fitScale * zoom), fitScale, MaxScaleNow);
            GlideTo(to, MapViewMath.PositionFor(designSize, designPoint, RoomCentre, to));
        }

        void GlideTo(float toScale, Vector2 toPosition)
        {
            velocity = Vector2.zero;
            glideFrom = Mathf.Max(scale, 1e-4f);
            glideTo = Mathf.Max(toScale, 1e-4f);
            glideFromPos = position;
            glideToPos = MapViewMath.ClampPosition(designSize, coverRect, View.rect.size, toScale, toPosition, MapViewMath.PositionFor(designSize, coverRect.center, RoomCentre, toScale));
            glideT = 0f;
            gliding = true;
        }

        // ------------------------------------------------------------------ fingers, mouse and wheel

        public void OnInitializePotentialDrag(PointerEventData eventData)
        {
            eventData.useDragThreshold = true;
            velocity = Vector2.zero;
        }

        public void OnBeginDrag(PointerEventData eventData)
        {
            Vector2 p;
            if (!Local(eventData, out p)) return;
            gliding = false;
            velocity = Vector2.zero;
            pointers[eventData.pointerId] = p;
            StartPinch();
        }

        public void OnDrag(PointerEventData eventData)
        {
            Vector2 p;
            if (!pointers.ContainsKey(eventData.pointerId) || !Local(eventData, out p)) return;
            Vector2 before = pointers[eventData.pointerId];
            pointers[eventData.pointerId] = p;
            if (pointers.Count >= 2)
            {
                // Two fingers: zoom by how much they spread, about their middle, and follow the middle.
                Vector2 middle;
                float distance = Spread(out middle);
                if (pinchDistance > 1f && distance > 1f)
                {
                    float to = Mathf.Clamp(scale * distance / pinchDistance, fitScale, MaxScaleNow);
                    position = MapViewMath.ZoomAbout(position, scale, to, middle) + (middle - pinchMiddle);
                    scale = to;
                }
                pinchDistance = distance;
                pinchMiddle = middle;
            }
            else
            {
                Vector2 delta = p - before;
                position += delta;
                float dt = Mathf.Max(Time.unscaledDeltaTime, 1f / 120f);
                velocity = Vector2.Lerp(velocity, delta / dt, 0.5f);
            }
        }

        public void OnEndDrag(PointerEventData eventData)
        {
            pointers.Remove(eventData.pointerId);
            if (pointers.Count >= 1)
            {
                // From a pinch back to one finger: no fling, and the remaining finger pans from here.
                velocity = Vector2.zero;
                StartPinch();
            }
            else if (velocity.magnitude < 200f) velocity = Vector2.zero;
        }

        public void OnScroll(PointerEventData eventData)
        {
            Vector2 p;
            if (!fitted || !Local(eventData, out p)) return;
            gliding = false;
            float to = Mathf.Clamp(scale * Mathf.Pow(1.12f, eventData.scrollDelta.y), fitScale, MaxScaleNow);
            position = MapViewMath.ZoomAbout(position, scale, to, p);
            scale = to;
        }

        void StartPinch()
        {
            pinchDistance = pointers.Count >= 2 ? Spread(out pinchMiddle) : 0f;
        }

        /// <summary>The distance between the first two fingers down and their middle.</summary>
        float Spread(out Vector2 middle)
        {
            Vector2 a = Vector2.zero, b = Vector2.zero;
            int i = 0;
            foreach (var p in pointers.Values)
            {
                if (i == 0) a = p; else if (i == 1) b = p;
                if (++i >= 2) break;
            }
            middle = (a + b) * 0.5f;
            return Vector2.Distance(a, b);
        }

        /// <summary>The pointer's place in the view (canvas units from its middle, y up).</summary>
        bool Local(PointerEventData eventData, out Vector2 p)
        {
            Camera cam = eventData.pressEventCamera != null ? eventData.pressEventCamera : eventData.enterEventCamera;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(View, eventData.position, cam, out p)) return false;
            p -= View.rect.center;
            return true;
        }
    }
}
