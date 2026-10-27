using UnityEngine;

namespace DribbleToSchool.Core
{
    /// <summary>
    /// A respawn point. LevelManager activates it once the kid passes it with
    /// the ball close by, so a lost ball never sends you back too far.
    /// </summary>
    public class Checkpoint : MonoBehaviour
    {
        public Transform kidSpawn;
        public Transform ballSpawn;
        [Tooltip("The level start: active from the beginning, no flag or toast.")]
        public bool isStart;
        [Tooltip("Optional flag that changes colour when reached.")]
        public SpriteRenderer flag;
        public Color inactiveColor = new Color(0.75f, 0.75f, 0.75f);
        public Color activeColor = new Color(0.30f, 0.80f, 0.40f);

        public bool IsActive { get; private set; }

        public Vector2 KidSpawnPosition { get { return kidSpawn != null ? (Vector2)kidSpawn.position : (Vector2)transform.position; } }
        public Vector2 BallSpawnPosition { get { return ballSpawn != null ? (Vector2)ballSpawn.position : (Vector2)transform.position + Vector2.right; } }

        void Awake()
        {
            SetActive(isStart);
        }

        public void SetActive(bool active)
        {
            IsActive = active;
            if (flag != null) flag.color = active ? activeColor : inactiveColor;
        }
    }
}
