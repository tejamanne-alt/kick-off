using UnityEngine;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// The root of a stage's scene (inactive in the scene file; the streamer prepares it and switches
    /// it on when the kid gets near). Everything of the stage hangs under it. Obstacle and pickup
    /// layouts can come in several <see cref="variants"/>: one is chosen at random each time the stage
    /// loads, so a day never plays the same twice, while the scenery stays put.
    /// </summary>
    public class RunChunk : MonoBehaviour
    {
        public int stage;
        public float startX, endX;
        [Tooltip("Alternative layers of obstacles and pickups (children of this object, inactive in the file). " +
            "One is switched on at random when the stage loads. Empty: everything stays as built.")]
        public GameObject[] variants = new GameObject[0];

        /// <summary>Which variant is on (-1: none to choose from).</summary>
        public int ChosenVariant { get; private set; }

        /// <summary>Choose and switch on one variant; call while the stage is still inactive.</summary>
        public void Prepare(System.Random rng)
        {
            ChosenVariant = -1;
            if (variants == null || variants.Length == 0) return;
            ChosenVariant = rng.Next(variants.Length);
            for (int i = 0; i < variants.Length; i++)
                if (variants[i] != null) variants[i].SetActive(i == ChosenVariant);
        }
    }
}
