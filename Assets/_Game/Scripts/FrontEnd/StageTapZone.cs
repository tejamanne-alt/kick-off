using UnityEngine;

namespace DribbleToSchool.FrontEnd
{
    /// <summary>
    /// Keeps an invisible button over the menu's 3D teen (wherever the camera has them), so a
    /// tap on the character opens the player picker.
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class StageTapZone : MonoBehaviour
    {
        // The menu camera sways all the time, so the teen's box drifts by fractions of a pixel every frame. Moving
        // the zone each time rebuilds its (clear) image and re-batches the whole menu canvas every frame, so it only
        // follows once it is off by more than this many canvas units: far less than a fingertip.
        const float Slack = 1f;

        void LateUpdate()
        {
            var stage = MenuStage.Current;
            var rt = (RectTransform)transform;
            var parent = rt.parent as RectTransform;
            if (stage == null || parent == null)
            {
                if (rt.sizeDelta != Vector2.zero) rt.sizeDelta = Vector2.zero;
                return;
            }
            Rect screen = stage.TeenScreenRect();
            Vector2 a, b;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(parent, screen.min, null, out a);
            RectTransformUtility.ScreenPointToLocalPointInRectangle(parent, screen.max, null, out b);
            Vector2 middle = new Vector2(0.5f, 0.5f);
            if (rt.anchorMin != middle || rt.anchorMax != middle) rt.anchorMin = rt.anchorMax = middle;
            if (rt.pivot != middle) rt.pivot = middle;
            Vector2 position = (a + b) * 0.5f - parent.rect.center;
            Vector2 size = new Vector2(Mathf.Abs(b.x - a.x), Mathf.Abs(b.y - a.y));
            if (Moved(rt.anchoredPosition, position)) rt.anchoredPosition = position;
            if (Moved(rt.sizeDelta, size)) rt.sizeDelta = size;
        }

        static bool Moved(Vector2 from, Vector2 to)
        {
            return Mathf.Abs(from.x - to.x) > Slack || Mathf.Abs(from.y - to.y) > Slack;
        }
    }
}
