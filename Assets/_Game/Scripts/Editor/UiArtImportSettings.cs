using UnityEditor;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Import settings for pictures the menus load from Resources/UI (the teens' portraits from
    /// tools/blender/portrait_teen.py): sprites with clean transparent edges, full size, no
    /// mipmaps (they're shown near their own size), compressed in high quality.
    /// </summary>
    public class UiArtImportSettings : AssetPostprocessor
    {
        // Bump to re-import the pictures when these settings change.
        public override uint GetVersion() { return 1; }

        void OnPreprocessTexture()
        {
            if (!assetPath.Replace('\\', '/').Contains("/_Game/Resources/UI/")) return;
            var importer = (TextureImporter)assetImporter;
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 100f;
            importer.alphaIsTransparency = true;
            importer.mipmapEnabled = false;
            importer.sRGBTexture = true;
            importer.wrapMode = UnityEngine.TextureWrapMode.Clamp;
            importer.filterMode = UnityEngine.FilterMode.Bilinear;
            importer.maxTextureSize = 1024;
            importer.textureCompression = TextureImporterCompression.CompressedHQ;
        }
    }
}
