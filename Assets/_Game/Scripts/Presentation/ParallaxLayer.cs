using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Moves a background layer by a fraction of the camera's movement.
    /// factor 1 = glued to the camera (sky), 0 = part of the world.
    /// </summary>
    public class ParallaxLayer : MonoBehaviour
    {
        [Range(0f, 1f)] public float factorX = 0.5f;
        [Range(0f, 1f)] public float factorY = 0.8f;
        public Transform cameraTransform;

        Vector3 startPosition;
        Vector3 cameraStart;
        bool initialised;

        void LateUpdate()
        {
            if (cameraTransform == null)
            {
                if (Camera.main == null) return;
                cameraTransform = Camera.main.transform;
            }
            if (!initialised)
            {
                startPosition = transform.position;
                cameraStart = cameraTransform.position;
                initialised = true;
            }
            Vector3 delta = cameraTransform.position - cameraStart;
            transform.position = new Vector3(startPosition.x + delta.x * factorX, startPosition.y + delta.y * factorY, startPosition.z);
        }
    }
}
