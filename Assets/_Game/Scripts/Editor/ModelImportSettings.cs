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
        public override uint GetVersion() { return 3; }

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
