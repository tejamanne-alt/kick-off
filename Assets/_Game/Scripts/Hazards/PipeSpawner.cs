using System.Collections.Generic;
using UnityEngine;

namespace DribbleToSchool.Hazards
{
    /// <summary>
    /// Building-site pipes rolling down toward the kid every few seconds.
    /// They shove the ball and the kid; jump them or let them pass.
    /// </summary>
    public class PipeSpawner : HazardBase
    {
        public float interval = 4f;
        public float firstDelay = 1.5f;
        public float startSpeed = 3f;
        public float radius = 0.45f;
        public float lifeTime = 9f;
        public Sprite sprite;
        public Color color = new Color(0.55f, 0.55f, 0.6f);
        [Tooltip("Pipes are removed when they roll left of this x.")]
        public float despawnX = -20f;

        readonly List<GameObject> pipes = new List<GameObject>();
        readonly List<float> spawnTimes = new List<float>();
        float nextSpawn;

        void Start()
        {
            nextSpawn = Time.time + firstDelay;
        }

        public override void ResetState()
        {
            foreach (var p in pipes) if (p != null) Destroy(p);
            pipes.Clear();
            spawnTimes.Clear();
            nextSpawn = Time.time + firstDelay;
        }

        void Update()
        {
            if (Level == null || Level.State == Core.LevelState.Paused) return;

            if (Time.time >= nextSpawn)
            {
                Spawn();
                nextSpawn = Time.time + interval;
            }

            for (int i = pipes.Count - 1; i >= 0; i--)
            {
                var p = pipes[i];
                if (p == null || p.transform.position.x < despawnX || Time.time - spawnTimes[i] > lifeTime)
                {
                    if (p != null) Destroy(p);
                    pipes.RemoveAt(i);
                    spawnTimes.RemoveAt(i);
                }
            }
        }

        void Spawn()
        {
            var go = new GameObject("Pipe");
            go.transform.position = transform.position;
            var body = go.AddComponent<Rigidbody2D>();
            body.mass = 6f;
            body.gravityScale = 2f;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            body.linearVelocity = new Vector2(-startSpeed, 0f);
            body.angularVelocity = startSpeed / radius * Mathf.Rad2Deg;
            var col = go.AddComponent<CircleCollider2D>();
            col.radius = radius;

            var visual = new GameObject("Visual");
            visual.transform.SetParent(go.transform, false);
            visual.transform.localScale = Vector3.one * radius * 2f;
            var sr = visual.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.color = color;
            sr.sortingOrder = 9;
            var hole = new GameObject("Hole");
            hole.transform.SetParent(visual.transform, false);
            hole.transform.localScale = Vector3.one * 0.55f;
            var hsr = hole.AddComponent<SpriteRenderer>();
            hsr.sprite = sprite;
            hsr.color = Color.Lerp(color, Color.black, 0.6f);
            hsr.sortingOrder = 10;
            var mark = new GameObject("Mark");
            mark.transform.SetParent(visual.transform, false);
            mark.transform.localPosition = new Vector3(0.36f, 0f, 0f);
            mark.transform.localScale = Vector3.one * 0.12f;
            var msr = mark.AddComponent<SpriteRenderer>();
            msr.sprite = sprite;
            msr.color = new Color(1f, 0.8f, 0.3f);
            msr.sortingOrder = 11;

            pipes.Add(go);
            spawnTimes.Add(Time.time);
        }
    }
}
