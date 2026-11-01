using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Keeps a full-screen rect inside the screen's safe area (clear of a notch or rounded
    /// corners in landscape), updating when the phone turns round. Put the menus' buttons in it;
    /// backgrounds stay full screen.
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class UISafeArea : MonoBehaviour
    {
        Rect applied;
        Vector2Int screen;

        void OnEnable() { Apply(); }

        void Update()
        {
            if (Screen.safeArea != applied || screen.x != Screen.width || screen.y != Screen.height) Apply();
        }

        void Apply()
        {
            applied = Screen.safeArea;
            screen = new Vector2Int(Screen.width, Screen.height);
            if (Screen.width <= 0 || Screen.height <= 0) return;
            var rt = (RectTransform)transform;
            rt.anchorMin = new Vector2(applied.xMin / Screen.width, applied.yMin / Screen.height);
            rt.anchorMax = new Vector2(applied.xMax / Screen.width, applied.yMax / Screen.height);
            rt.offsetMin = rt.offsetMax = Vector2.zero;
        }
    }
}
