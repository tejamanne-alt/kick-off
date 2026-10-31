using System.Collections.Generic;
using System.Threading.Tasks;
using DribbleToSchool.Core;
using Unity.Profiling;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Plays the synthesized sound effects for gameplay events (with a little
    /// pitch variety), crossfades chapter music between scenes, ducks music in
    /// the pause menu, and fires haptics. Lives across scenes.
    /// </summary>
    public class AudioDirector : MonoBehaviour
    {
        const int VoiceCount = 12;
        const float CrossfadeTime = 1.2f;

        static AudioDirector instance;
        static readonly ProfilerMarker MusicUploadMarker = new ProfilerMarker("DTS.Audio.MusicUpload");

        readonly Dictionary<Sfx, AudioClip> clips = new Dictionary<Sfx, AudioClip>();
        readonly Dictionary<int, AudioClip> musicClips = new Dictionary<int, AudioClip>();
        readonly Dictionary<int, Task<float[]>> musicJobs = new Dictionary<int, Task<float[]>>();
        readonly Dictionary<Sfx, float> lastPlayed = new Dictionary<Sfx, float>();
        AudioSource[] voices;
        int nextVoice;
        AudioSource musicA, musicB;
        bool aIsCurrent = true;
        float fade = 1f;
        int wantedMusic = -1;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            Ensure();
        }

        public static AudioDirector Ensure()
        {
            if (instance != null) return instance;
            var go = new GameObject("AudioDirector");
            DontDestroyOnLoad(go);
            instance = go.AddComponent<AudioDirector>();
            return instance;
        }

        /// <summary>Play a sound from code that isn't driven by a GameEvent.</summary>
        public static void Play(Sfx sfx, float volume = 1f, float pitch = 1f)
        {
            if (instance != null) instance.PlayInternal(sfx, volume, pitch);
        }

        void Awake()
        {
            foreach (var kv in SoundBank.BuildAll())
            {
                var clip = AudioClip.Create("sfx_" + kv.Key, kv.Value.Length, 1, Synth.SampleRate, false);
                clip.SetData(kv.Value, 0);
                clips[kv.Key] = clip;
            }

            voices = new AudioSource[VoiceCount];
            for (int i = 0; i < VoiceCount; i++)
            {
                voices[i] = gameObject.AddComponent<AudioSource>();
                voices[i].playOnAwake = false;
            }
            musicA = MakeMusicSource();
            musicB = MakeMusicSource();

            GameEvents.Raised += OnEvent;
            SceneManager.sceneLoaded += OnSceneLoaded;
            OnSceneLoaded(SceneManager.GetActiveScene(), LoadSceneMode.Single);
        }

        void OnDestroy()
        {
            GameEvents.Raised -= OnEvent;
            SceneManager.sceneLoaded -= OnSceneLoaded;
        }

        AudioSource MakeMusicSource()
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.loop = true;
            s.playOnAwake = false;
            s.volume = 0f;
            return s;
        }

        // ---------- Music ----------

        void OnSceneLoaded(Scene scene, LoadSceneMode mode)
        {
            int chapter = 0;   // menu theme
            var level = LevelManager.Current;
            if (level != null) chapter = level.level != null ? Mathf.Clamp(level.level.chapter, 1, 5) : 1;
            RequestMusic(chapter);
        }

        void RequestMusic(int chapter)
        {
            wantedMusic = chapter;
            if (musicClips.ContainsKey(chapter) || musicJobs.ContainsKey(chapter)) return;
            // Synthesizing a loop takes a fraction of a second: do it off the main thread.
            musicJobs[chapter] = Task.Run(() => MusicGenerator.Generate(chapter));
        }

        void Update()
        {
            // Finish any music jobs.
            List<int> done = null;
            foreach (var kv in musicJobs)
            {
                if (!kv.Value.IsCompleted) continue;
                if (done == null) done = new List<int>();
                done.Add(kv.Key);
                if (kv.Value.Status == TaskStatus.RanToCompletion)
                {
                    using (MusicUploadMarker.Auto())
                    {
                        float[] data = kv.Value.Result;
                        var clip = AudioClip.Create("music_" + kv.Key, data.Length, 1, Synth.SampleRate, false);
                        clip.SetData(data, 0);
                        musicClips[kv.Key] = clip;
                    }
                }
            }
            if (done != null) foreach (int k in done) musicJobs.Remove(k);

            // Start the wanted track when ready.
            AudioClip wanted;
            AudioSource current = aIsCurrent ? musicA : musicB;
            if (wantedMusic >= 0 && musicClips.TryGetValue(wantedMusic, out wanted) && current.clip != wanted)
            {
                aIsCurrent = !aIsCurrent;
                var next = aIsCurrent ? musicA : musicB;
                next.clip = wanted;
                next.time = 0f;
                next.Play();
                fade = 0f;
            }

            fade = Mathf.MoveTowards(fade, 1f, Time.unscaledDeltaTime / CrossfadeTime);
            bool paused = LevelManager.Current != null && LevelManager.Current.State == LevelState.Paused;
            float master = GameSettings.MusicVolume * (paused ? 0.35f : 1f) * 0.6f;
            var cur = aIsCurrent ? musicA : musicB;
            var old = aIsCurrent ? musicB : musicA;
            cur.volume = master * fade;
            old.volume = master * (1f - fade);
            if (fade >= 1f && old.isPlaying) old.Stop();
        }

        // ---------- Sound effects ----------

        void PlayInternal(Sfx sfx, float volume, float pitch)
        {
            AudioClip clip;
            if (!clips.TryGetValue(sfx, out clip)) return;

            // Avoid machine-gunning the same sound in one frame.
            float last;
            if (lastPlayed.TryGetValue(sfx, out last) && Time.unscaledTime - last < 0.03f) return;
            lastPlayed[sfx] = Time.unscaledTime;

            var v = voices[nextVoice];
            nextVoice = (nextVoice + 1) % VoiceCount;
            v.clip = clip;
            v.volume = Mathf.Clamp01(volume) * GameSettings.SfxVolume;
            v.pitch = pitch;
            v.Play();
        }

        static float Vary(float amount = 0.06f)
        {
            return 1f + Random.Range(-amount, amount);
        }

        void OnEvent(GameEventType type, Vector2 position, float k)
        {
            switch (type)
            {
                case GameEventType.Kick:
                    PlayInternal(Sfx.Kick, 0.6f + k * 0.4f, Vary() * (1.1f - k * 0.2f));
                    Haptics.Impact(k > 0.6f ? Haptics.Strength.Medium : Haptics.Strength.Light);
                    break;
                case GameEventType.Touch: PlayInternal(Sfx.Touch, 0.5f, Vary(0.1f)); break;
                case GameEventType.Trap: PlayInternal(Sfx.Trap, 0.5f, Vary()); break;
                case GameEventType.PerfectTouch:
                    // Rising chime with the streak.
                    PlayInternal(Sfx.Perfect, 0.7f, 1f + k * 0.5f);
                    Haptics.Impact(Haptics.Strength.Light);
                    break;
                case GameEventType.Juggle:
                    PlayInternal(Sfx.Juggle, 0.6f, 0.9f + k * 0.8f);
                    Haptics.Impact(Haptics.Strength.Light);
                    break;
                case GameEventType.Jump: PlayInternal(Sfx.Jump, 0.4f, Vary()); break;
                case GameEventType.DoubleJump:
                    PlayInternal(Sfx.DoubleJump, 0.45f, Vary());
                    Haptics.Impact(Haptics.Strength.Light);
                    break;
                case GameEventType.Slide:
                    PlayInternal(Sfx.Slide, 0.4f + k * 0.2f, Vary());
                    Haptics.Impact(Haptics.Strength.Soft);
                    break;
                case GameEventType.Land:
                    PlayInternal(Sfx.Land, 0.3f + k * 0.5f, Vary());
                    if (k > 0.6f) Haptics.Impact(Haptics.Strength.Light);
                    break;
                case GameEventType.BallBounce:
                    if (k > 0.15f) PlayInternal(Sfx.Bounce, 0.2f + k * 0.6f, Vary(0.1f) * (1.2f - k * 0.3f));
                    break;
                case GameEventType.Coin: PlayInternal(Sfx.Coin, 0.5f, Vary(0.03f)); break;
                case GameEventType.Sticker: PlayInternal(Sfx.Sticker, 0.8f, 1f); Haptics.Success(); break;
                case GameEventType.Checkpoint: PlayInternal(Sfx.Checkpoint, 0.6f, 1f); break;
                case GameEventType.Bell: PlayInternal(Sfx.Bell, 0.8f, 1f); Haptics.Impact(Haptics.Strength.Heavy); break;
                case GameEventType.Goal: PlayInternal(Sfx.Goal, 0.9f, 1f); Haptics.Success(); break;
                case GameEventType.BallLost: PlayInternal(Sfx.Lose, 0.6f, 1f); Haptics.Impact(Haptics.Strength.Heavy); break;
                case GameEventType.Respawn: PlayInternal(Sfx.Respawn, 0.5f, 1f); break;
                case GameEventType.LevelStart: PlayInternal(Sfx.Whistle, 0.6f, 1f); break;
                case GameEventType.Splash: PlayInternal(Sfx.Splash, 0.7f, Vary()); break;
                case GameEventType.DogSteal: PlayInternal(Sfx.Woof, 0.7f, Vary(0.1f)); break;
                case GameEventType.SeagullHit: PlayInternal(Sfx.Squawk, 0.7f, Vary(0.1f)); break;
                case GameEventType.PedestrianBump: PlayInternal(Sfx.Oof, 0.6f, Vary(0.15f)); break;
                case GameEventType.Springboard: PlayInternal(Sfx.Boing, 0.7f, Vary()); Haptics.Impact(Haptics.Strength.Light); break;
                case GameEventType.SwitchPressed: PlayInternal(Sfx.Switch, 0.7f, 1f); break;
                case GameEventType.GateOpened: PlayInternal(Sfx.Gate, 0.6f, 1f); break;
                case GameEventType.LightChange: if (k > 0.5f) PlayInternal(Sfx.Beep, 0.35f, 1f); break;
                case GameEventType.UIClick: PlayInternal(Sfx.Click, 0.5f, Vary(0.05f)); Haptics.Release(); break;
                case GameEventType.Purchase: PlayInternal(Sfx.Purchase, 0.8f, 1f); Haptics.Success(); break;
            }
        }
    }
}
