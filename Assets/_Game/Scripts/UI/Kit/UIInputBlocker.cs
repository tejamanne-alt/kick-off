using DribbleToSchool.InputHandling;
using UnityEngine;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Keeps game touches off a UI element while it is on screen: its rect joins GameInput.UIBlockers every frame (the HUDs
    /// clear that list in their Update; this adds to it afterwards). For a card over a level, such as a challenge's guide.
    /// </summary>
    public class UIInputBlocker : MonoBehaviour
    {
        readonly Vector3[] corners = new Vector3[4];

        void LateUpdate()
        {
            var rt = transform as RectTransform;
            if (rt == null) return;
            rt.GetWorldCorners(corners);   // overlay canvas: world space == screen pixels
            GameInput.UIBlockers.Add(Rect.MinMaxRect(corners[0].x, corners[0].y, corners[2].x, corners[2].y));
        }
    }
}
