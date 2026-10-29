using UnityEditor;

namespace DribbleToSchool.EditorTools
{
    /// <summary>
    /// Import settings for the models made in Blender (tools/blender: characters and cars):
    /// metres, no materials or animation clips (the game poses the bones in code and assigns
    /// its toon material), readable meshes so outfits and paint can recolour them, and the
    /// full hierarchy kept (a car's single root "Body" must not be folded into the asset root).
    /// </summary>
    public class ModelImportSettings : AssetPostprocessor
    {
        // Bump to re-import the models when these settings change.
        public override uint GetVersion() { return 2; }

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
            importer.preserveHierarchy = true;
        }
    }
}
