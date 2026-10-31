using UnityEditor;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Import settings for the models made in Blender (tools/blender: characters, cars and the
    /// asset kits): metres, no materials or animation clips (the game poses the bones in code and
    /// assigns its toon material), readable meshes so outfits, paint and ModelTint can recolour
    /// them, and the full hierarchy kept (a car's single root "Body" must not be folded into the
    /// asset root, and kit models keep their Attach markers). Kit models have no bones, so they
    /// get no Animator.
    /// </summary>
    public class ModelImportSettings : AssetPostprocessor
    {
        // Bump to re-import the models when these settings change.
        public override uint GetVersion() { return 4; }

        void OnPreprocessModel()
        {
            if (!assetPath.Replace('\\', '/').Contains("/_Game/Art/Models/")) return;
            var importer = (ModelImporter)assetImporter;
            importer.useFileScale = true;
            importer.globalScale = 1f;
            importer.materialImportMode = ModelImporterMaterialImportMode.None;
            importer.importAnimation = false;
            importer.animationType = InKit(assetPath) ? ModelImporterAnimationType.None : ModelImporterAnimationType.Generic;
            importer.optimizeGameObjects = false;   // keep the bones as transforms the game can pose
            importer.isReadable = true;
            importer.importBlendShapes = false;
            importer.importCameras = false;
            importer.importLights = false;
            importer.importNormals = ModelImporterNormals.Import;
            importer.preserveHierarchy = true;
        }

        /// <summary>
        /// The models' atlases (painted detail plus a plain white corner the flat-coloured parts
        /// sample): clamped, so filtering never bleeds the far edge into the white corner.
        /// </summary>
        void OnPreprocessTexture()
        {
            string path = assetPath.Replace('\\', '/');
            if (!path.Contains("/_Game/Art/Models/") || !path.EndsWith("Atlas.png")) return;
            var importer = (TextureImporter)assetImporter;
            importer.textureType = TextureImporterType.Default;
            importer.sRGBTexture = true;
            importer.mipmapEnabled = true;
            importer.wrapMode = UnityEngine.TextureWrapMode.Clamp;
            importer.filterMode = UnityEngine.FilterMode.Trilinear;
            importer.anisoLevel = 2;
            // The plants' leaf sprites are cut out at alpha 0.5: keep that coverage in every mip so
            // far trees don't thin out, and keep colour under the transparent texels.
            if (path.EndsWith("/PlantsAtlas.png"))
            {
                importer.alphaIsTransparency = true;
                importer.mipMapsPreserveCoverage = true;
                importer.alphaTestReferenceValue = 0.5f;
            }
        }

        /// <summary>Is the model in one of the asset kits' folders (Art/Models/&lt;kit&gt;/)?</summary>
        static bool InKit(string path)
        {
            path = path.Replace('\\', '/');
            foreach (var kit in LevelBuildKit.Kits)
                if (path.Contains("/_Game/Art/Models/" + kit + "/")) return true;
            return false;
        }
    }
}
