using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>A surface that carries whoever stands on it (moving platforms, swings).</summary>
    public interface IMovingSurface
    {
        Vector2 SurfaceVelocity { get; }
    }
}
