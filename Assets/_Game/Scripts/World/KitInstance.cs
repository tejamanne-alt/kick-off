using UnityEngine;

namespace DribbleToSchool.World
{
    /// <summary>
    /// Marks a placed asset-kit model (tools/blender kit_*.py). Its mesh is shared with every other
    /// copy, so <see cref="StaticBatcher"/> leaves it out rather than duplicating its geometry into
    /// a combined mesh; GPU instancing on the kit's material draws the repeats together instead.
    /// </summary>
    public class KitInstance : MonoBehaviour
    {
    }
}
