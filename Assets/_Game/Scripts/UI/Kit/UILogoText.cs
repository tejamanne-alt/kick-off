using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Game-logo lettering on a uGUI Text (or any Graphic): leaned forward like italics, a
    /// vertical gradient on the face, a thin ink line round the face, a solid extrusion below
    /// it, a thick ink outline round the whole extruded shape, and a soft drop shadow. All of
    /// it is copies of the glyph quads in one mesh, drawn back to front, so it costs one draw.
    /// The face is the gradient times the Text's colour, so tinted titles keep their colour.
    /// </summary>
    [ExecuteAlways]
    public class UILogoText : BaseMeshEffect
    {
        [Tooltip("Lean: x moves by this much per unit of height (0.15 is a sporty italic).")]
        public float skew = 0.14f;
        public Color faceTop = Color.white;
        public Color faceBottom = new Color(0.8f, 0.9f, 1f);
        [Tooltip("Thin ink line round the face, in canvas pixels.")]
        public float innerLine = 4f;
        public Color extrudeColor = new Color(0.14f, 0.2f, 0.4f);
        [Tooltip("How far the extrusion drops below the face, in canvas pixels.")]
        public float extrude = 12f;
        public Color outlineColor = new Color(0.08f, 0.09f, 0.15f);
        [Tooltip("The outer outline round the face and extrusion, in canvas pixels.")]
        public float outline = 7f;
        public Color shadowColor = new Color(0.03f, 0.06f, 0.2f, 0.35f);
        public Vector2 shadowOffset = new Vector2(6f, -20f);

        const int RingSteps = 12;
        static readonly List<UIVertex> source = new List<UIVertex>();
        static readonly List<UIVertex> output = new List<UIVertex>();

        public override void ModifyMesh(VertexHelper vh)
        {
            if (!IsActive() || vh.currentVertCount == 0) return;
            source.Clear();
            output.Clear();
            vh.GetUIVertexStream(source);

            float minY = float.MaxValue, maxY = float.MinValue;
            foreach (var v in source)
            {
                minY = Mathf.Min(minY, v.position.y);
                maxY = Mathf.Max(maxY, v.position.y);
            }
            float midY = (minY + maxY) * 0.5f;

            // Back to front: shadow, the outer outline swept down the extrusion, the extrusion,
            // the thin line round the face, then the face.
            Copy(shadowOffset + new Vector2(0f, -extrude), shadowColor, midY);   // one copy: overlapping see-through copies would darken
            int sweep = Mathf.Max(1, Mathf.CeilToInt(extrude / Mathf.Max(2f, outline)));
            for (int s = 0; s <= sweep; s++)
                Ring(new Vector2(0f, -extrude * s / sweep), innerLine + outline, outlineColor, midY);
            int layers = Mathf.Max(1, Mathf.CeilToInt(extrude / 1.5f));
            for (int k = layers; k >= 1; k--)
                Ring(new Vector2(0f, -extrude * k / layers), innerLine, extrudeColor, midY);
            Ring(Vector2.zero, innerLine, outlineColor, midY);
            for (int i = 0; i < source.Count; i++)
            {
                var v = source[i];
                float t = Mathf.InverseLerp(minY, maxY, v.position.y);
                // The gradient times the text's own colour (white for the logo, gold for a toast).
                v.color = Color.Lerp(faceBottom, faceTop, t) * (Color)v.color;
                v.position = Lean(v.position, midY);
                output.Add(v);
            }

            vh.Clear();
            vh.AddUIVertexTriangleStream(output);
        }

        /// <summary>The glyphs copied round a circle of <paramref name="radius"/>, flat coloured.</summary>
        void Ring(Vector2 offset, float radius, Color color, float midY)
        {
            if (radius <= 0.01f)
            {
                Copy(offset, color, midY);
                return;
            }
            for (int r = 0; r < RingSteps; r++)
            {
                float a = r * Mathf.PI * 2f / RingSteps;
                Copy(offset + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * radius, color, midY);
            }
        }

        void Copy(Vector2 offset, Color color, float midY)
        {
            for (int i = 0; i < source.Count; i++)
            {
                var v = source[i];
                Color c = color;
                c.a *= StackedAlpha(v.color.a / 255f);
                v.color = c;
                v.position = Lean(v.position, midY) + (Vector3)offset;
                output.Add(v);
            }
        }

        /// <summary>
        /// The alpha for one of the copies when the text fades: about a dozen copies overlap at
        /// any point, so each gets the alpha that stacks up to <paramref name="a"/> rather than
        /// <paramref name="a"/> itself (or the outline would stay dark while the face fades).
        /// </summary>
        static float StackedAlpha(float a)
        {
            return a >= 0.999f ? 1f : 1f - Mathf.Pow(1f - a, 1f / RingSteps);
        }

        Vector3 Lean(Vector3 p, float midY)
        {
            p.x += (p.y - midY) * skew;
            return p;
        }
    }
}
