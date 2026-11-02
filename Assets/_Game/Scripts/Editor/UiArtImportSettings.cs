using UnityEditor;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Import settings for pictures the menus load from Resources/UI: the teens' portraits (from
    /// tools/blender/portrait_teen.py) are sprites with clean transparent edges, full size, no mipmaps (they're
    /// shown near their own size), compressed in high quality. The town map (UI/TownMap, a 3200 x 1800 rendered
    /// picture the map screen shows on a RawImage) is the exception: a plain opaque texture, up to 4096 across,
    /// kept at its own size, no mipmaps, compressed in high quality.
    /// </summary>
    public class UiArtImportSettings : AssetPostprocessor
    {
        /// <summary>The town map's picture (Resources/UI/TownMap.jpg): the one picture here that is not a sprite.</summary>
        const string TownMapPath = "/_Game/Resources/UI/TownMap";

        // Bump to re-import the pictures when these settings change.
        public override uint GetVersion() { return 2; }

        void OnPreprocessTexture()
        {
            string path = assetPath.Replace('\\', '/');
            if (!path.Contains("/_Game/Resources/UI/")) return;
            var importer = (TextureImporter)assetImporter;

            if (path.Contains(TownMapPath))
            {
                importer.textureType = TextureImporterType.Default;
                importer.textureShape = TextureImporterShape.Texture2D;
                importer.alphaSource = TextureImporterAlphaSource.None;
                importer.alphaIsTransparency = false;
                importer.mipmapEnabled = false;
                importer.isReadable = false;
                importer.sRGBTexture = true;
                importer.wrapMode = UnityEngine.TextureWrapMode.Clamp;
                importer.filterMode = UnityEngine.FilterMode.Bilinear;
                importer.npotScale = TextureImporterNPOTScale.None;     // 3200 x 1800 as it is, not stretched to 4096 x 2048
                importer.maxTextureSize = 4096;
                importer.textureCompression = TextureImporterCompression.CompressedHQ;
                importer.crunchedCompression = false;
                return;
            }

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
