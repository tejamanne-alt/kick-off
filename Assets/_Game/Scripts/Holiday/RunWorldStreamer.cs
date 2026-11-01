using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Holiday
{
    /// <summary>
    /// Keeps the stages near the kid loaded. Each stage is its own scene, built at its place in the
    /// world (see <see cref="HolidayStages"/>), with an inactive root carrying a <see cref="RunChunk"/>;
    /// a stage is loaded additively a good way ahead of the kid, given a random layout variant, switched
    /// on one per frame (so the cost of waking a stage is never piled onto one frame), and unloaded
    /// once well behind. Only about three stages exist at a time, however long the run.
    /// </summary>
    public class RunWorldStreamer : MonoBehaviour
    {
        public static RunWorldStreamer Current { get; private set; }

        [Tooltip("The kid whose x decides what to load.")]
        public Transform follow;
        [Tooltip("Stages that begin within this far ahead of the kid are loaded.")]
        public float loadAhead = 190f;
        [Tooltip("Stages that end further behind the kid than this are unloaded.")]
        public float keepBehind = 80f;
        [Tooltip("Stages loading at once (more stages ahead are asked for as these finish).")]
        public int loadsAtOnce = 1;

        class Slot
        {
            public int stage;
            public string scene;
            public AsyncOperation load;
            public RunChunk chunk;
            public bool active;
            public bool unloading;
            public AsyncOperation unload;
        }

        readonly Dictionary<int, Slot> slots = new Dictionary<int, Slot>();
        readonly List<Slot> going = new List<Slot>();
        readonly System.Random rng = new System.Random();
        float focusX;
        bool dayStarted;

        /// <summary>The stages around the kid's feet are loaded and switched on, so it is safe to run.</summary>
        public bool IsReady
        {
            get
            {
                if (!dayStarted) return false;
                float x = follow != null ? follow.position.x : focusX;
                for (int stage = 0; stage < HolidayStages.Count; stage++)
                {
                    // Anything the kid could be standing on or looking at in the next few seconds.
                    bool near = HolidayStages.StartOf(stage) < x + 60f && HolidayStages.EndOf(stage) > x - 20f;
                    if (!near) continue;
                    Slot slot;
                    if (!slots.TryGetValue(stage, out slot) || !slot.active) return false;
                }
                return true;
            }
        }

        public int LoadedCount
        {
            get
            {
                int n = 0;
                foreach (var s in slots.Values) if (s.active) n++;
                return n;
            }
        }

        void Awake() { Current = this; }

        void OnDestroy()
        {
            if (Current == this) Current = null;
        }

        /// <summary>
        /// A new day (or a fresh run): throw away every stage that is loaded and start from
        /// <paramref name="firstStage"/> (the kid stands at the start of it).
        /// </summary>
        public void StartDay(int firstStage)
        {
            focusX = HolidayStages.SpawnX + (firstStage > 0 ? HolidayStages.StartOf(firstStage) : 0f);
            foreach (var slot in slots.Values)
                if (!slot.unloading) BeginUnload(slot);
            dayStarted = true;
        }

        void Update()
        {
            if (!dayStarted) return;
            float x = follow != null ? follow.position.x : focusX;

            // Wake loaded stages, one a frame.
            bool woke = false;
            foreach (var slot in slots.Values)
            {
                if (slot.unloading) continue;
                if (slot.chunk == null && slot.load != null && slot.load.isDone) Adopt(slot);
                if (!slot.active && slot.chunk != null && !woke)
                {
                    Activate(slot);
                    woke = true;
                }
            }

            // Unload what is far behind; load what is coming (nearest first, a few at a time).
            int loading = 0;
            foreach (var slot in slots.Values)
                if (!slot.unloading && slot.load != null && !slot.load.isDone) loading++;

            going.Clear();
            foreach (var slot in slots.Values)
                if (!slot.unloading && HolidayStages.EndOf(slot.stage) < x - keepBehind) going.Add(slot);
            foreach (var slot in going) BeginUnload(slot);

            int first = Mathf.Max(0, HolidayStages.StageAt(x - 20f));
            for (int stage = first; stage < HolidayStages.Count && loading < loadsAtOnce; stage++)
            {
                if (HolidayStages.StartOf(stage) > x + loadAhead) break;
                if (HolidayStages.EndOf(stage) < x - keepBehind) continue;
                Slot slot;
                if (slots.TryGetValue(stage, out slot)) continue;
                if (StillUnloading(stage)) continue;
                BeginLoad(stage);
                loading++;
            }

            // A stage that was asked to unload while it was still loading is unloaded as soon as it has arrived;
            // once its scene is gone the slot is forgotten and the stage may load again.
            going.Clear();
            foreach (var slot in slots.Values)
            {
                if (!slot.unloading) continue;
                if (slot.unload == null && slot.load != null && slot.load.isDone)
                {
                    Scene scene = SceneManager.GetSceneByName(slot.scene);
                    if (scene.IsValid() && scene.isLoaded) slot.unload = SceneManager.UnloadSceneAsync(scene);
                }
                if (UnloadFinished(slot)) going.Add(slot);
            }
            foreach (var slot in going) slots.Remove(slot.stage);
        }

        static bool UnloadFinished(Slot slot)
        {
            if (slot.load == null) return true;
            if (!slot.load.isDone) return false;
            if (slot.unload != null) return slot.unload.isDone;
            Scene scene = SceneManager.GetSceneByName(slot.scene);
            return !scene.IsValid() || !scene.isLoaded;
        }

        bool StillUnloading(int stage)
        {
            Slot slot;
            return slots.TryGetValue(stage, out slot) && slot.unloading;
        }

        void BeginLoad(int stage)
        {
            string scene = HolidayStages.SceneName(stage);
            var slot = new Slot { stage = stage, scene = scene };
            slots[stage] = slot;
            try
            {
                slot.load = SceneManager.LoadSceneAsync(scene, LoadSceneMode.Additive);
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Holiday Run] Could not load " + scene + ": " + e.Message);
            }
            if (slot.load == null)
            {
                // Not in the build: nothing will ever arrive, so don't hold the run up for it.
                Debug.LogError("[Holiday Run] Stage scene " + scene + " is not in the build: rebuild the Holiday Run (Kick Off > Rebuild Holiday Run).");
                slot.active = true;
            }
        }

        /// <summary>Find the stage's root in its freshly loaded scene.</summary>
        void Adopt(Slot slot)
        {
            Scene scene = SceneManager.GetSceneByName(slot.scene);
            if (!scene.IsValid() || !scene.isLoaded) return;
            foreach (var root in scene.GetRootGameObjects())
            {
                var chunk = root.GetComponent<RunChunk>();
                if (chunk != null) { slot.chunk = chunk; return; }
            }
            Debug.LogWarning("[Holiday Run] " + slot.scene + " has no Stage root with a RunChunk.");
            slot.active = true;   // nothing to wake; don't hold the run up
        }

        void Activate(Slot slot)
        {
            try
            {
                slot.chunk.Prepare(rng);
                slot.chunk.gameObject.SetActive(true);
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Holiday Run] Could not start " + slot.scene + ": " + e.Message);
            }
            slot.active = true;
        }

        void BeginUnload(Slot slot)
        {
            if (slot.unloading) return;
            slot.unloading = true;
            slot.active = false;
            slot.chunk = null;
            if (slot.load == null || !slot.load.isDone) return;   // unloaded as soon as it has arrived (see Update)
            Scene scene = SceneManager.GetSceneByName(slot.scene);
            if (scene.IsValid() && scene.isLoaded) slot.unload = SceneManager.UnloadSceneAsync(scene);
        }
    }
}
