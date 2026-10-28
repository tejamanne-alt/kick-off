using DribbleToSchool.Ball;
using DribbleToSchool.Core;
using DribbleToSchool.Player;
using UnityEngine;

namespace DribbleToSchool.Pickups
{
    /// <summary>
    /// A coin collected by the kid or the ball. Spins, bobs, and pops when taken.
    /// Restored when the level restarts.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class Coin : MonoBehaviour, IResettable
    {
        public int value = 1;
        public Transform visual;

        public bool Collected { get; private set; }

        Vector3 basePosition;
        float phase;
        float collectedAt;

        void Awake()
        {
            GetComponent<Collider2D>().isTrigger = true;
            basePosition = visual != null ? visual.localPosition : Vector3.zero;
            phase = transform.position.x * 0.7f;
        }

        void OnTriggerEnter2D(Collider2D other)
        {
            if (Collected) return;
            var rb = other.attachedRigidbody;
            if (rb == null) return;
            if (rb.GetComponent<KidController>() == null && rb.GetComponent<BallController>() == null) return;

            var level = LevelManager.Current;
            if (level == null || (level.State != LevelState.Playing && level.State != LevelState.Respawning)) return;

            Collected = true;
            collectedAt = Time.time;
            GetComponent<Collider2D>().enabled = false;
            level.CollectCoin(this);
            GameEvents.Raise(GameEventType.Coin, transform.position);
        }

        void Update()
        {
            if (visual == null) return;
            if (Collected)
            {
                // Quick pop up and shrink away.
                float t = Mathf.Clamp01((Time.time - collectedAt) / 0.3f);
                visual.localPosition = basePosition + Vector3.up * t * 0.6f;
                visual.localScale = Vector3.one * (1f - t);
                visual.localRotation = Quaternion.Euler(0f, Time.time * 900f + phase * 57f, 0f);
                if (t >= 1f) visual.gameObject.SetActive(false);
                return;
            }
            // A real 3D spin about the vertical axis.
            visual.localRotation = Quaternion.Euler(0f, (Time.time * 4f + phase) * Mathf.Rad2Deg, 0f);
            visual.localScale = Vector3.one;
            visual.localPosition = basePosition + Vector3.up * Mathf.Sin(Time.time * 2f + phase) * 0.06f;
        }

        public void ResetState()
        {
            Collected = false;
            GetComponent<Collider2D>().enabled = true;
            if (visual != null)
            {
                visual.gameObject.SetActive(true);
                visual.localPosition = basePosition;
            }
        }
    }
}
