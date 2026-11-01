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
        void LateUpdate()
        {
            var stage = MenuStage.Current;
            var rt = (RectTransform)transform;
            var parent = rt.parent as RectTransform;
            if (stage == null || parent == null)
            {
                rt.sizeDelta = Vector2.zero;
                return;
            }
            Rect screen = stage.TeenScreenRect();
            Vector2 a, b;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(parent, screen.min, null, out a);
            RectTransformUtility.ScreenPointToLocalPointInRectangle(parent, screen.max, null, out b);
            rt.anchorMin = rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = (a + b) * 0.5f - parent.rect.center;
            rt.sizeDelta = new Vector2(Mathf.Abs(b.x - a.x), Mathf.Abs(b.y - a.y));
        }
    }
}
