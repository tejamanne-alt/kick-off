using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Recolours a sprite or a 3D part the same way: a sprite's colour, or the tint of a
    /// toon material through a property block (so the shared material is left alone).
    /// </summary>
    public static class Tint
    {
        static readonly int ColorId = Shader.PropertyToID("_Color");
        static MaterialPropertyBlock block;

        public static void Set(Renderer renderer, Color color)
        {
            if (renderer == null) return;
            var sprite = renderer as SpriteRenderer;
            if (sprite != null)
            {
                sprite.color = color;
                return;
            }
            if (block == null) block = new MaterialPropertyBlock();
            renderer.GetPropertyBlock(block);
            block.SetColor(ColorId, color);
            renderer.SetPropertyBlock(block);
        }
    }
}
