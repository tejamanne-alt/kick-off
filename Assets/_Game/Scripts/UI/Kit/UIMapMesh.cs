using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Draws what a <see cref="MapPainter"/> collected (one triangle list, map units with y down) as a single UI mesh with
    /// vertex colours: a whole layer of the town map in one draw. The graphic's rect should be the map's rect (centred
    /// pivot); the colour tints it. It never takes taps.
    /// </summary>
    [RequireComponent(typeof(CanvasRenderer))]
    public class UIMapMesh : MaskableGraphic
    {
        /// <summary>The size of the drawing space the painter's coordinates live in.</summary>
        public Vector2 designSize = new Vector2(1600f, 900f);

        MapPainter painter;
        static readonly List<UIVertex> scratch = new List<UIVertex>();

        public MapPainter Painter { get { return painter; } }

        /// <summary>A mesh child of <paramref name="parent"/> that fills it and draws <paramref name="painter"/>.</summary>
        public static UIMapMesh Create(Transform parent, string name, MapPainter painter, Vector2 designSize)
        {
            var rt = UIKit.Stretch(UIKit.Rect(parent, name));
            rt.pivot = new Vector2(0.5f, 0.5f);
            var mesh = rt.gameObject.AddComponent<UIMapMesh>();
            mesh.designSize = designSize;
            mesh.raycastTarget = false;
            mesh.Show(painter);
            return mesh;
        }

        public void Show(MapPainter p)
        {
            painter = p;
            SetVerticesDirty();
        }

        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            if (painter == null || painter.VertexCount == 0) return;
            scratch.Clear();
            float ox = designSize.x * 0.5f, oy = designSize.y * 0.5f;
            Color tint = color;
            for (int i = 0; i < painter.positions.Count; i++)
            {
                Vector2 p = painter.positions[i];
                Color32 c = painter.colors[i];
                UIVertex v = UIVertex.simpleVert;
                v.position = new Vector3(p.x - ox, oy - p.y, 0f);
                v.color = new Color32((byte)(c.r * tint.r), (byte)(c.g * tint.g), (byte)(c.b * tint.b), (byte)(c.a * tint.a));
                scratch.Add(v);
            }
            vh.AddUIVertexStream(scratch, painter.indices);
        }
    }
}
