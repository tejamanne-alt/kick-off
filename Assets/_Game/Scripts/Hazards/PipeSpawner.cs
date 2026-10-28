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
        /// <summary>
        /// A concrete-grey pipe lying across the street (along z) with a dark hollow and a
        /// yellow stripe, as a child of <paramref name="go"/>. Used for rolling and stacked pipes.
        /// </summary>
        public static void BuildPipe(GameObject go, float radius, Color color, Material material)
        {
            var visual = new GameObject("Visual");
            visual.transform.SetParent(go.transform, false);
            var pipe = visual.AddComponent<World.CylinderShape>();
            pipe.radius = radius;
            pipe.length = 1.5f;
            pipe.sideColor = color;
            pipe.endColor = Color.Lerp(color, Color.white, 0.15f);
            pipe.innerRadius = radius * 0.72f;
            pipe.innerColor = Color.Lerp(color, Color.black, 0.65f);
            visual.GetComponent<MeshRenderer>().sharedMaterial = material;
            pipe.Rebuild();

            // A painted stripe shows the pipe rolling.
            var stripe = new GameObject("Stripe");
            stripe.transform.SetParent(visual.transform, false);
            stripe.transform.localPosition = new Vector3(0f, radius * 0.98f, -0.4f);
            var box = stripe.AddComponent<World.Box3D>();
            box.size = new Vector3(0.12f, 0.04f, 0.5f);
            box.color = new Color(1f, 0.8f, 0.3f);
            stripe.GetComponent<MeshRenderer>().sharedMaterial = material;
            box.Rebuild();
        }

        public float interval = 4f;
        public float firstDelay = 1.5f;
        public float startSpeed = 3f;
        public float radius = 0.45f;
        public float lifeTime = 9f;
        public Material material;
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

            BuildPipe(go, radius, color, material);
            pipes.Add(go);
            spawnTimes.Add(Time.time);
        }
    }
}
