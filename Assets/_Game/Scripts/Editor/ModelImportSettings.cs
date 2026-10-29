using UnityEditor;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Import settings for the character models made in Blender (tools/blender): metres, no
    /// materials or animation clips (the game poses the bones in code and assigns its toon
    /// material), and readable meshes so outfits can recolour them.
    /// </summary>
    public class ModelImportSettings : AssetPostprocessor
    {
        void OnPreprocessModel()
        {
            if (!assetPath.Replace('\\', '/').Contains("/_Game/Art/Models/")) return;
            var importer = (ModelImporter)assetImporter;
            importer.useFileScale = true;
            importer.globalScale = 1f;
            importer.materialImportMode = ModelImporterMaterialImportMode.None;
            importer.importAnimation = false;
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.optimizeGameObjects = false;   // keep the bones as transforms the game can pose
            importer.isReadable = true;
            importer.importBlendShapes = false;
            importer.importCameras = false;
            importer.importLights = false;
            importer.importNormals = ModelImporterNormals.Import;
        }
    }
}
