using System.Collections.Generic;
using DribbleToSchool.Tuning;
using UnityEngine;

namespace DribbleToSchool.Ball
{
    /// <summary>
    /// Dotted preview of the first part of a kick's flight.
    /// Only the first ~0.5 s is shown so landing a chip still takes skill.
    /// </summary>
    public class TrajectoryPreview : MonoBehaviour
    {
        public BallTuning tuning;
        public Sprite dotSprite;
        public float dotSize = 0.13f;
        public Color validColor = new Color(1f, 1f, 1f, 0.95f);
        [Tooltip("Shown when the ball is out of kick reach.")]
        public Color invalidColor = new Color(1f, 0.35f, 0.3f, 0.8f);
        public int sortingOrder = 50;

        readonly List<SpriteRenderer> dots = new List<SpriteRenderer>();

        void Awake()
        {
            EnsureDots(tuning != null ? tuning.previewDots : 12);
            Hide();
        }

        void EnsureDots(int count)
        {
            while (dots.Count < count)
            {
                var go = new GameObject("Dot" + dots.Count);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = dotSprite;
                sr.sortingOrder = sortingOrder;
                go.SetActive(false);
                dots.Add(sr);
            }
        }

        /// <summary>Draw the arc from <paramref name="origin"/> with launch velocity and gravity (world units).</summary>
        public void Show(Vector2 origin, Vector2 velocity, Vector2 gravity, bool valid)
        {
            int count = tuning.previewDots;
            EnsureDots(count);
            Color baseColor = valid ? validColor : invalidColor;

            for (int i = 0; i < dots.Count; i++)
            {
                SpriteRenderer dot = dots[i];
                if (i >= count)
                {
                    dot.gameObject.SetActive(false);
                    continue;
                }

                float k = (i + 1f) / count;
                float t = k * tuning.previewDuration;
                Vector2 p = origin + velocity * t + 0.5f * gravity * t * t;

                dot.gameObject.SetActive(true);
                dot.transform.position = new Vector3(p.x, p.y, 0f);
                dot.transform.localScale = Vector3.one * dotSize * Mathf.Lerp(1f, 0.55f, k);
                Color c = baseColor;
                c.a *= Mathf.Lerp(1f, 0.25f, k);
                dot.color = c;
            }
        }

        public void Hide()
        {
            for (int i = 0; i < dots.Count; i++) dots[i].gameObject.SetActive(false);
        }
    }
}
