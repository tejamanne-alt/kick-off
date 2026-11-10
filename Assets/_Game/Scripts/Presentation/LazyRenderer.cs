using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// A renderer whose mesh and material are loaded only while it is shown (docs/PERFORMANCE.md, "Budgets").
    ///
    /// Every scene (the menu, every level, the Holiday Run) is built with all six playable kids and the five Locker Room
    /// bags fitted to each, and CharacterChoice and BagWear show one kid and the bag they wear. Saved with their meshes,
    /// the scene loaded all of them, 36 skinned meshes and their atlases, for one kid on screen. The level builder now
    /// saves those renderers without a mesh or a material and puts both in a <see cref="CastPart"/> under Resources
    /// (<see cref="resource"/>); this loads them as its object becomes active and lets them go as it is hidden, so only
    /// the chosen kid and the bag they wear are in memory. What is let go is freed at the next scene load, or when the
    /// menu switches kids (CharacterChoice asks Unity to unload unused assets then).
    ///
    /// It runs before every other script (execution order -1000), so whatever reads the mesh as the kid appears
    /// (ModelOutfit dressing the kid, the coins measuring the drawn kid) finds it there. Co-op ghosts keep this
    /// component when they are stripped, so a ghost loads its kid as it appears. In the editor, outside play, the
    /// kids show without their meshes: the scenes are generated, never edited by hand.
    /// </summary>
    [DefaultExecutionOrder(-1000)]
    [DisallowMultipleComponent]
    public class LazyRenderer : MonoBehaviour
    {
        [Tooltip("The CastPart to load, as a Resources path (Cast/<Model>/<Renderer>).")]
        public string resource;
        [Tooltip("The renderer's local bounds as built (a skinned renderer keeps its bounds when its mesh is set in code).")]
        public Bounds bounds;

        CastPart part;

        /// <summary>Is the mesh in?</summary>
        public bool Loaded { get { return part != null; } }

        void OnEnable() { Load(); }

        void OnDisable() { Release(); }

        /// <summary>Puts the mesh and material on the renderer (a no-op if they are already on).</summary>
        public void Load()
        {
            if (part != null || string.IsNullOrEmpty(resource)) return;
            part = Resources.Load<CastPart>(resource);
            if (part == null)
            {
                Debug.LogWarning("[Kick Off] " + name + ": Resources/" + resource + " is missing; rebuild the generated content.");
                return;
            }
            var skinned = GetComponent<SkinnedMeshRenderer>();
            if (skinned != null)
            {
                skinned.sharedMesh = part.mesh;
                skinned.localBounds = bounds;
            }
            else
            {
                var filter = GetComponent<MeshFilter>();
                if (filter != null) filter.sharedMesh = part.mesh;
            }
            var r = GetComponent<Renderer>();
            if (r != null) r.sharedMaterial = part.material;
        }

        /// <summary>Takes the mesh and material off again (with any recoloured copy of the mesh: ModelOutfit).</summary>
        public void Release()
        {
            if (part == null) return;
            part = null;
            var outfit = GetComponent<ModelOutfit>();
            if (outfit != null) outfit.ForgetMesh();
            var skinned = GetComponent<SkinnedMeshRenderer>();
            if (skinned != null) skinned.sharedMesh = null;
            else
            {
                var filter = GetComponent<MeshFilter>();
                if (filter != null) filter.sharedMesh = null;
            }
            var r = GetComponent<Renderer>();
            if (r != null) r.sharedMaterial = null;
        }
    }
}
