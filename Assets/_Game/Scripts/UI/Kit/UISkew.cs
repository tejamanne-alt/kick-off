using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace DribbleToSchool.UI.Kit
{
    /// <summary>
    /// Leans a graphic forward (a parallelogram for ribbons, tabs and speed lines), about the
    /// middle of its rect, so it stays in place. Hit testing still uses the upright rect.
    /// </summary>
    [ExecuteAlways]
    public class UISkew : BaseMeshEffect
    {
        [Tooltip("x moves by this much per unit of height above the rect's middle.")]
        public float skew = 0.2f;

        static readonly List<UIVertex> verts = new List<UIVertex>();

        public override void ModifyMesh(VertexHelper vh)
        {
            if (!IsActive()) return;
            float mid = graphic.rectTransform.rect.center.y;
            verts.Clear();
            vh.GetUIVertexStream(verts);
            for (int i = 0; i < verts.Count; i++)
            {
                var v = verts[i];
                v.position.x += (v.position.y - mid) * skew;
                verts[i] = v;
            }
            vh.Clear();
            vh.AddUIVertexTriangleStream(verts);
        }
    }
}
