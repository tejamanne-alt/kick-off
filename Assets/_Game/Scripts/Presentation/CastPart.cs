using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// One renderer's mesh and material, kept under a Resources folder (Resources/Cast/&lt;Model&gt;/&lt;Renderer&gt;) so
    /// that a scene does not load them with itself: the playable kids' bodies and their Locker Room bags. Every scene
    /// holds all six kids and their bags, but shows one kid and at most one bag; with the meshes here, only those are
    /// ever loaded (<see cref="LazyRenderer"/>). Written by the level builder (LevelBuildKit.BuildCast).
    /// </summary>
    public class CastPart : ScriptableObject
    {
        public Mesh mesh;
        public Material material;
    }
}
