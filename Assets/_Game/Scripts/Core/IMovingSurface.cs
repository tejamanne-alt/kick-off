using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// A surface that carries whoever stands on it (moving platforms, swings). It sits on the same object as the
    /// Rigidbody2D its colliders attach to: the kid finds it through the ground collider's attachedRigidbody
    /// (KidController.CheckGround), so give every new one [RequireComponent(typeof(Rigidbody2D))], as these have.
    /// </summary>
    public interface IMovingSurface
    {
        Vector2 SurfaceVelocity { get; }
    }
}
