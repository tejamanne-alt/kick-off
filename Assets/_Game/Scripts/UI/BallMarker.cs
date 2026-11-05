using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.Localization;
using DribbleToSchool.Player;
using DribbleToSchool.UI.Kit;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Where the ball is when it is off the side of the screen: the camera stays on the kid (CameraFollow2D), so a ball kicked
    /// far ahead or back goes out of view, and a marker at that side of the screen shows it: the ball in a white disc, an arrow
    /// pointing out toward it and how far away it is ("12 m"). It sits between the info card and the buttons, at the ball's
    /// height as far as it can, takes no touches, and shows only while the run is being played. GameHud and the Holiday Run's
    /// HUD each make one.
    /// </summary>
    public class BallMarker : MonoBehaviour
    {
        /// <summary>The ball counts as off the screen this far (fraction of its width) past a side.</summary>
        public const float Edge = 0.02f;
        /// <summary>The marker keeps between these heights (fractions of the screen): above the buttons, below the info card.</summary>
        public const float LowY = 0.52f, HighY = 0.74f;

        const float Size = 92f, Inset = 76f;

        LevelManager level;
        KidController kid;
        BallController ball;
        RectTransform marker, arrow;
        Text distance;
        int shownMetres = -1;

        /// <summary>The (hidden) marker under <paramref name="root"/> for <paramref name="ball"/>, measured from <paramref name="kid"/>.</summary>
        public static BallMarker Create(RectTransform root, LevelManager level, KidController kid, BallController ball)
        {
            var holder = UIKit.Stretch(UIKit.Rect(root, "BallMarker"));
            var m = holder.gameObject.AddComponent<BallMarker>();
            m.level = level;
            m.kid = kid;
            m.ball = ball;
            m.marker = UIKit.Rect(holder, "Marker");
            m.marker.sizeDelta = new Vector2(Size, Size);
            var disc = UIKit.Icon(m.marker, "Disc", ProceduralSprites.SoftEdgeDisc, new Color(1f, 1f, 1f, 0.92f), Size);
            UIKit.Stretch(disc.rectTransform);
            var rim = UIKit.Icon(m.marker, "Rim", ProceduralSprites.ThinRing, UITheme.Navy, Size);
            UIKit.Stretch(rim.rectTransform);
            UIKit.Icon(m.marker, "Ball", ProceduralSprites.BallIcon, Color.white, Size * 0.62f);
            m.arrow = UIKit.Icon(m.marker, "Arrow", ProceduralSprites.PlayIcon, UITheme.Navy, 34f).rectTransform;
            m.distance = UIKit.Label(m.marker, "Distance", "", 28, Color.white, TextAnchor.MiddleCenter, true);
            UIKit.Place(m.distance.rectTransform, new Vector2(0.5f, 0f), new Vector2(0f, -22f), new Vector2(160f, 40f), new Vector2(0.5f, 0.5f));
            var outline = m.distance.gameObject.AddComponent<Outline>();
            outline.effectColor = new Color(0.05f, 0.08f, 0.2f, 0.85f);
            outline.effectDistance = new Vector2(2f, -2f);
            foreach (var g in holder.GetComponentsInChildren<Graphic>(true)) g.raycastTarget = false;
            m.marker.gameObject.SetActive(false);
            return m;
        }

        void LateUpdate()
        {
            var cam = Camera.main;
            bool playing = level == null || level.State == LevelState.Playing;
            if (cam == null || ball == null || kid == null || !playing)
            {
                Show(false);
                return;
            }
            Vector3 v = cam.WorldToViewportPoint(ball.transform.position);
            int side = Side(v.x, v.z);
            if (side == 0)
            {
                Show(false);
                return;
            }
            Show(true);
            float y = Mathf.Clamp(v.y, LowY, HighY);
            marker.anchorMin = marker.anchorMax = new Vector2(side < 0 ? 0f : 1f, y);
            marker.pivot = new Vector2(0.5f, 0.5f);
            marker.anchoredPosition = new Vector2(side < 0 ? Inset : -Inset, 0f);
            // The arrow on the outer side of the disc, pointing out toward the ball.
            arrow.anchorMin = arrow.anchorMax = new Vector2(side < 0 ? 0f : 1f, 0.5f);
            arrow.anchoredPosition = new Vector2(side < 0 ? -8f : 8f, 0f);
            arrow.localRotation = Quaternion.Euler(0f, 0f, side < 0 ? 180f : 0f);
            int metres = Mathf.RoundToInt(Mathf.Abs(ball.transform.position.x - kid.transform.position.x));
            if (metres != shownMetres)
            {
                shownMetres = metres;
                distance.text = Loc.F("hud.ballAway", metres);
            }
        }

        /// <summary>Which side of the screen a ball at viewport <paramref name="x"/> is off (-1 left, +1 right, 0 on the screen or behind the camera).</summary>
        public static int Side(float x, float depth)
        {
            if (depth <= 0f) return 0;
            if (x < -Edge) return -1;
            if (x > 1f + Edge) return 1;
            return 0;
        }

        void Show(bool on)
        {
            if (marker.gameObject.activeSelf == on) return;
            marker.gameObject.SetActive(on);
            if (on)
            {
                var pop = marker.GetComponent<UIPopIn>();
                if (pop == null) pop = UIKit.PopIn(marker.gameObject);
                pop.Play();
            }
        }
    }
}
