using Unity.Profiling;
using UnityEngine;

namespace DribbleToSchool.Presentation
{
    /// <summary>
    /// Lightweight pooled sprite particles (no ParticleSystem setup needed):
    /// velocity, gravity, drag, spin, size and fade over life.
    /// </summary>
    public class FxPool : MonoBehaviour
    {
        public int capacity = 220;
        public int sortingOrder = 40;

        struct Particle
        {
            public bool alive;
            public Vector2 position, velocity;
            public float gravity, drag, life, maxLife, size0, size1, rotation, spin;
            public Color color;
        }

        static readonly ProfilerMarker UpdateMarker = new ProfilerMarker("DTS.FxPool.Update");

        Particle[] particles;
        SpriteRenderer[] renderers;
        int next;

        void Awake()
        {
            particles = new Particle[capacity];
            renderers = new SpriteRenderer[capacity];
            for (int i = 0; i < capacity; i++)
            {
                var go = new GameObject("p");
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = sortingOrder;
                sr.enabled = false;
                renderers[i] = sr;
            }
        }

        public void Emit(Sprite sprite, Vector2 position, Vector2 velocity, Color color, float size0, float size1,
            float life, float gravity = 0f, float drag = 0f, float spin = 0f)
        {
            int i = next;
            next = (next + 1) % capacity;
            particles[i] = new Particle
            {
                alive = true, position = position, velocity = velocity, gravity = gravity, drag = drag,
                life = 0f, maxLife = Mathf.Max(0.01f, life), size0 = size0, size1 = size1,
                rotation = Random.Range(0f, 360f), spin = spin, color = color,
            };
            var sr = renderers[i];
            sr.sprite = sprite;
            sr.enabled = true;
        }

        /// <summary>Burst of particles spread in a cone around <paramref name="direction"/> (degrees of spread).</summary>
        public void Burst(Sprite sprite, Vector2 position, int count, Vector2 direction, float spreadDegrees, float speedMin, float speedMax,
            Color color, float size0, float size1, float life, float gravity = 0f, float drag = 0f, float spin = 0f, float jitter = 0.05f)
        {
            float baseAngle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
            for (int i = 0; i < count; i++)
            {
                float a = (baseAngle + Random.Range(-spreadDegrees, spreadDegrees) * 0.5f) * Mathf.Deg2Rad;
                Vector2 v = new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * Random.Range(speedMin, speedMax);
                Vector2 p = position + Random.insideUnitCircle * jitter;
                Emit(sprite, p, v, color, size0 * Random.Range(0.8f, 1.2f), size1, life * Random.Range(0.8f, 1.2f), gravity, drag, spin * Random.Range(-1f, 1f));
            }
        }

        void Update()
        {
            using (UpdateMarker.Auto()) Step(Time.deltaTime);
        }

        void Step(float dt)
        {
            for (int i = 0; i < capacity; i++)
            {
                if (!particles[i].alive) continue;
                var p = particles[i];
                p.life += dt;
                if (p.life >= p.maxLife)
                {
                    p.alive = false;
                    particles[i] = p;
                    renderers[i].enabled = false;
                    continue;
                }
                p.velocity.y -= p.gravity * dt;
                p.velocity *= Mathf.Clamp01(1f - p.drag * dt);
                p.position += p.velocity * dt;
                p.rotation += p.spin * dt;
                particles[i] = p;

                float t = p.life / p.maxLife;
                var sr = renderers[i];
                sr.transform.SetPositionAndRotation(p.position, Quaternion.Euler(0f, 0f, p.rotation));
                sr.transform.localScale = Vector3.one * Mathf.Lerp(p.size0, p.size1, t);
                Color c = p.color;
                c.a *= 1f - t * t;
                sr.color = c;
            }
        }
    }
}
