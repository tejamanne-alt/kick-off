using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI
{
    /// <summary>
    /// Comic sound-effect lettering on a Text (UI/ComicPops): a hard drop shadow and a thick ink stroke
    /// (copies of the glyphs pushed out in a ring, in ink), then the letters filled with a gradient from
    /// <see cref="top"/> to <see cref="bottom"/>. With <see cref="sketch"/> (the pencil sketch filter) it is
    /// pencil lettering instead: a thin graphite line drawn twice and a faint smudge. The fill's lower part is marked for the halftone dots of
    /// Resources/Shaders/ComicLettering (uv1.x how much, uv1.y 1 on the fill, 0 on the ink).
    /// </summary>
    [RequireComponent(typeof(Text))]
    public class ComicLettering : BaseMeshEffect
    {
        public Color top = new Color(1f, 0.93f, 0.33f);
        public Color bottom = new Color(0.97f, 0.41f, 0.14f);
        public Color ink = new Color(0.09f, 0.05f, 0.16f);
        [Tooltip("Stroke width as a fraction of the font size.")]
        public float stroke = 0.09f;
        [Tooltip("The drop shadow's offset, in stroke widths, down and to the right.")]
        public float shadow = 2f;
        [Tooltip("How far down the letters the dots start (0 top, 1 bottom) and how dense they get.")]
        public float dotsFrom = 0.45f, dotsMax = 0.9f;
        [Tooltip("Pencil lettering for the sketch filter: a thin graphite line drawn twice (a second, offset stroke), a faint smudge for a shadow; the material hatches the fill instead of dotting it.")]
        public bool sketch;

        static readonly List<UIVertex> glyphs = new List<UIVertex>();
        static readonly List<UIVertex> output = new List<UIVertex>();
        const int Ring = 12;

        public override void ModifyMesh(VertexHelper vh)
        {
            if (!IsActive()) return;
            glyphs.Clear();
            vh.GetUIVertexStream(glyphs);
            if (glyphs.Count == 0) return;

            float yMin = float.MaxValue, yMax = float.MinValue;
            for (int i = 0; i < glyphs.Count; i++)
            {
                float y = glyphs[i].position.y;
                if (y < yMin) yMin = y;
                if (y > yMax) yMax = y;
            }
            float height = Mathf.Max(yMax - yMin, 1f);
            var text = (Text)graphic;
            float w = text.fontSize * stroke;

            output.Clear();
            Vector3 drop = new Vector3(w * shadow, -w * shadow, 0f);
            if (sketch)
            {
                // A faint graphite smudge for a shadow, the line drawn once more a little off (the sketcher's
                // second go), then the line itself: thin, all round.
                for (int k = 0; k < 6; k++)
                {
                    float a = k * Mathf.PI * 2f / 6f;
                    AddInk(drop + new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * w * 1.6f, 0.22f);
                }
                Vector3 second = new Vector3(w * 1.2f, w * 0.8f, 0f);
                for (int k = 0; k < 8; k++)
                {
                    float a = k * Mathf.PI * 2f / 8f;
                    AddInk(second + new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * w * 0.7f, 0.55f);
                }
                for (int k = 0; k < 8; k++)
                {
                    float a = k * Mathf.PI * 2f / 8f;
                    AddInk(new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * w, 1f);
                }
            }
            else
            {
                // The drop shadow: a ring at the shadow's offset, so it is as bold as the stroke.
                for (int k = 0; k < 8; k++)
                {
                    float a = k * Mathf.PI * 2f / 8f;
                    AddInk(drop + new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * w, 1f);
                }
                // The ink stroke.
                for (int k = 0; k < Ring; k++)
                {
                    float a = k * Mathf.PI * 2f / Ring;
                    AddInk(new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0f) * w, 1f);
                }
            }
            // The fill: the gradient top to bottom, the dots on its lower part.
            for (int i = 0; i < glyphs.Count; i++)
            {
                var v = glyphs[i];
                float t = (yMax - v.position.y) / height;
                Color c = Color.Lerp(top, bottom, Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(0.15f, 0.85f, t)));
                c.a *= v.color.a / 255f;
                v.color = c;
                v.uv1 = new Vector4(Mathf.Clamp01((t - dotsFrom) * 1.4f) * dotsMax, 1f, 0f, 0f);
                output.Add(v);
            }
            vh.Clear();
            vh.AddUIVertexTriangleStream(output);
        }

        void AddInk(Vector3 offset, float alpha)
        {
            for (int i = 0; i < glyphs.Count; i++)
            {
                var v = glyphs[i];
                v.position += offset;
                Color c = ink;
                c.a *= alpha * v.color.a / 255f;
                v.color = c;
                v.uv1 = Vector4.zero;
                output.Add(v);
            }
        }
    }
}
