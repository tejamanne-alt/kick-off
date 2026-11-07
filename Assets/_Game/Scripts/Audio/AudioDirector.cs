using System.Collections.Generic;
using System.Threading.Tasks;
using DribbleToSchool.Core;
using DribbleToSchool.Holiday;
using DribbleToSchool.Levels;
using Unity.Profiling;
using UnityEngine;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Plays the synthesized sound effects for gameplay events (with a little pitch variety), the
    /// music and the ambience of the place the kid is in (Soundscape: each route to school has its own
    /// music and its own sounds, crossfaded as the scene or the Holiday Run's stage changes), and fires
    /// haptics. The ambience is a looping bed (traffic, a crowd, waves, a generator...) with cues played
    /// over it at random times, places and pitches (a car going by, a gull, a reversing truck...), mixed
    /// well under the music. Music, ambience and sound effects each have a volume in Settings; all are
    /// turned down in the pause menu. Lives across scenes.
    /// </summary>
    public class AudioDirector : MonoBehaviour
    {
        const int VoiceCount = 12;
        const int CueVoiceCount = 4;
        const float CrossfadeTime = 1.2f;
        const float AmbienceFadeTime = 2f;
        /// <summary>Overall levels at full volume: the music on top, the place's sounds under it.</summary>
        const float MusicGain = 0.6f, AmbienceGain = 0.45f;
        /// <summary>How many soundscapes' music and ambience to keep ready (the rest are let go).</summary>
        const int Keep = 3;

        static AudioDirector instance;
        static readonly ProfilerMarker MusicUploadMarker = new ProfilerMarker("DTS.Audio.MusicUpload");

        sealed class Ambience
        {
            public AudioClip bed;
            public AmbientCue[] cues;
            public AudioClip[] cueClips;
            public float[] next;
        }

        sealed class CueVoice
        {
            public AudioSource source;
            public bool sweep;
            public float from, to, start, length, loudness;
        }

        readonly Dictionary<Sfx, AudioClip> clips = new Dictionary<Sfx, AudioClip>();
        // The music by place and country (MusicKey): each add-on's streets have their own country's music.
        readonly Dictionary<int, AudioClip> musicClips = new Dictionary<int, AudioClip>();
        readonly Dictionary<int, Task<float[]>> musicJobs = new Dictionary<int, Task<float[]>>();
        readonly Dictionary<Soundscape, Ambience> ambiences = new Dictionary<Soundscape, Ambience>();
        readonly Dictionary<Soundscape, Task<AmbiencePack>> ambienceJobs = new Dictionary<Soundscape, Task<AmbiencePack>>();
        readonly List<Soundscape> recent = new List<Soundscape>();
        readonly Dictionary<Sfx, float> lastPlayed = new Dictionary<Sfx, float>();
        AudioSource[] voices;
        int nextVoice;
        AudioSource musicA, musicB, bedA, bedB;
        CueVoice[] cueVoices;
        int nextCueVoice;
        bool aIsCurrent = true, bedAIsCurrent = true;
        float fade = 1f, bedFade = 1f;
        Soundscape wanted = Soundscape.Menu;
        MusicCountry wantedCountry = MusicCountry.Japan;

        static int MusicKey(Soundscape scape, MusicCountry country) { return (int)country * 32 + (int)scape; }

        /// <summary>
        /// Whose music: in a level, the country of the streets on screen (the loaded scene's add-on); in the
        /// menu, the add-on chosen in Settings. The Holiday Run is the original town.
        /// </summary>
        static MusicCountry WantedCountry()
        {
            var level = LevelManager.Current;
            if (level == null) return Progression.AddOns.Active.music;
            if (level.endless) return MusicCountry.Japan;
            return Progression.AddOns.OfScene(level.gameObject.scene.name).music;
        }
        Ambience playingAmbience;

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
            musicA = MakeLoopSource();
            musicB = MakeLoopSource();
            bedA = MakeLoopSource();
            bedB = MakeLoopSource();
            cueVoices = new CueVoice[CueVoiceCount];
            for (int i = 0; i < CueVoiceCount; i++)
            {
                var s = gameObject.AddComponent<AudioSource>();
                s.playOnAwake = false;
                cueVoices[i] = new CueVoice { source = s };
            }

            GameEvents.Raised += OnEvent;
            Want(WantedSoundscape(), WantedCountry());
        }

        void OnDestroy()
        {
            GameEvents.Raised -= OnEvent;
        }

        AudioSource MakeLoopSource()
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.loop = true;
            s.playOnAwake = false;
            s.volume = 0f;
            return s;
        }

        // ---------- Where are we ----------

        /// <summary>
        /// The soundscape of the level being played (its route's), of the Holiday Run's current stage, or the
        /// menu's outside a level. (Read every frame: the Holiday Run streams its stages in additively, so the
        /// place changes without a new scene.)
        /// </summary>
        static Soundscape WantedSoundscape()
        {
            var level = LevelManager.Current;
            if (level == null) return Soundscape.Menu;
            if (level.endless)
            {
                var run = HolidayRunDirector.Current;
                if (run != null)
                {
                    var stage = HolidayStages.All[Mathf.Clamp(run.StageIndex, 0, HolidayStages.Count - 1)];
                    var stageRoute = RouteTable.Of(stage.levelId);
                    return Soundscapes.For(stageRoute != null ? stageRoute.id : null, stage.chapter);
                }
            }
            if (level.level == null) return Soundscape.Street;
            var route = RouteTable.Of(level.level.levelId);
            return Soundscapes.For(route != null ? route.id : null, Mathf.Clamp(level.level.chapter, 1, 5));
        }

        void Want(Soundscape scape, MusicCountry country)
        {
            wanted = scape;
            wantedCountry = country;
            int key = MusicKey(scape, country);
            recent.Remove(scape);
            recent.Insert(0, scape);
            // Synthesizing takes a second or so: do it off the main thread.
            if (!musicClips.ContainsKey(key) && !musicJobs.ContainsKey(key))
                musicJobs[key] = Task.Run(() => MusicGenerator.Generate(scape, country));
            if (!ambiences.ContainsKey(scape) && !ambienceJobs.ContainsKey(scape))
                ambienceJobs[scape] = Task.Run(() => AmbienceGenerator.Generate(scape));
        }

        // ---------- Music and ambience ----------

        void Update()
        {
            var scape = WantedSoundscape();
            var country = WantedCountry();
            if (scape != wanted || country != wantedCountry) Want(scape, country);

            FinishJobs();
            bool paused = LevelManager.Current != null && LevelManager.Current.State == LevelState.Paused;
            float duck = paused ? 0.35f : 1f;

            // Music: start the wanted track when it's ready, crossfading from the last.
            AudioClip music;
            AudioSource current = aIsCurrent ? musicA : musicB;
            if (musicClips.TryGetValue(MusicKey(wanted, wantedCountry), out music) && current.clip != music)
            {
                aIsCurrent = !aIsCurrent;
                var next = aIsCurrent ? musicA : musicB;
                next.clip = music;
                next.time = 0f;
                next.Play();
                fade = 1f - fade;
            }
            fade = Mathf.MoveTowards(fade, 1f, Time.unscaledDeltaTime / CrossfadeTime);
            float musicLevel = GameSettings.MusicVolume * duck * MusicGain;
            var cur = aIsCurrent ? musicA : musicB;
            var old = aIsCurrent ? musicB : musicA;
            cur.volume = musicLevel * fade;
            old.volume = musicLevel * (1f - fade);
            if (fade >= 1f && old.isPlaying) { old.Stop(); old.clip = null; }

            // Ambience: the bed the same way, a slower fade; the new place's cues start once it's in.
            Ambience amb;
            AudioSource bed = bedAIsCurrent ? bedA : bedB;
            if (ambiences.TryGetValue(wanted, out amb) && bed.clip != amb.bed)
            {
                bedAIsCurrent = !bedAIsCurrent;
                var next = bedAIsCurrent ? bedA : bedB;
                next.clip = amb.bed;
                next.time = Random.Range(0f, amb.bed.length * 0.9f);
                next.Play();
                bedFade = 1f - bedFade;
                StartCues(amb);
            }
            bedFade = Mathf.MoveTowards(bedFade, 1f, Time.unscaledDeltaTime / AmbienceFadeTime);
            float ambienceLevel = GameSettings.AmbienceVolume * duck * AmbienceGain;
            var curBed = bedAIsCurrent ? bedA : bedB;
            var oldBed = bedAIsCurrent ? bedB : bedA;
            curBed.volume = ambienceLevel * bedFade;
            oldBed.volume = ambienceLevel * (1f - bedFade);
            if (bedFade >= 1f && oldBed.isPlaying) { oldBed.Stop(); oldBed.clip = null; }

            UpdateCues(ambienceLevel, paused);
            ForgetOld();
        }

        void FinishJobs()
        {
            List<int> doneMusic = null;
            foreach (var kv in musicJobs)
            {
                if (!kv.Value.IsCompleted) continue;
                if (doneMusic == null) doneMusic = new List<int>();
                doneMusic.Add(kv.Key);
                if (kv.Value.Status != TaskStatus.RanToCompletion) continue;
                using (MusicUploadMarker.Auto())
                    musicClips[kv.Key] = Stereo("music_" + kv.Key, kv.Value.Result);
            }
            if (doneMusic != null) foreach (var k in doneMusic) musicJobs.Remove(k);

            List<Soundscape> done = null;
            foreach (var kv in ambienceJobs)
            {
                if (!kv.Value.IsCompleted) continue;
                if (done == null) done = new List<Soundscape>();
                done.Add(kv.Key);
                if (kv.Value.Status != TaskStatus.RanToCompletion) continue;
                using (MusicUploadMarker.Auto())
                {
                    var pack = kv.Value.Result;
                    var a = new Ambience
                    {
                        bed = Stereo("ambience_" + kv.Key, pack.bed),
                        cues = pack.cues,
                        cueClips = new AudioClip[pack.cues.Length],
                        next = new float[pack.cues.Length],
                    };
                    for (int i = 0; i < pack.cues.Length; i++) a.cueClips[i] = Stereo("cue_" + pack.cues[i].name, pack.cues[i].clip);
                    ambiences[kv.Key] = a;
                }
            }
            if (done != null) foreach (var k in done) ambienceJobs.Remove(k);
        }

        static AudioClip Stereo(string name, float[] interleaved)
        {
            var clip = AudioClip.Create(name, interleaved.Length / 2, 2, Synth.SampleRate, false);
            clip.SetData(interleaved, 0);
            return clip;
        }

        /// <summary>Let go of the clips of places left behind, keeping the few most recent (a Holiday Run goes back and forth).</summary>
        void ForgetOld()
        {
            if (recent.Count <= Keep) return;
            var scape = recent[recent.Count - 1];
            bool musicLeft = false;
            foreach (MusicCountry c in System.Enum.GetValues(typeof(MusicCountry)))
            {
                AudioClip clip;
                int key = MusicKey(scape, c);
                if (!musicClips.TryGetValue(key, out clip)) continue;
                if (musicA.clip != clip && musicB.clip != clip)
                {
                    musicClips.Remove(key);
                    Destroy(clip);
                }
                else musicLeft = true;
            }
            Ambience amb;
            if (ambiences.TryGetValue(scape, out amb) && bedA.clip != amb.bed && bedB.clip != amb.bed && playingAmbience != amb)
            {
                ambiences.Remove(scape);
                Destroy(amb.bed);
                foreach (var c in amb.cueClips) Destroy(c);
            }
            if (!musicLeft && !ambiences.ContainsKey(scape)) recent.RemoveAt(recent.Count - 1);
        }

        // ---------- Ambient cues ----------

        void StartCues(Ambience amb)
        {
            playingAmbience = amb;
            float now = Time.unscaledTime;
            // Staggered, so the first few seconds of a place aren't all its cues at once.
            for (int i = 0; i < amb.cues.Length; i++)
                amb.next[i] = now + 1.5f + Random.Range(0.1f, 0.8f) * Random.Range(amb.cues[i].minGap, amb.cues[i].maxGap);
        }

        void UpdateCues(float level, bool paused)
        {
            float now = Time.unscaledTime;
            foreach (var v in cueVoices)
            {
                if (!v.source.isPlaying) continue;
                if (v.sweep)
                {
                    float u = Mathf.Clamp01((now - v.start) / Mathf.Max(0.1f, v.length));
                    v.source.panStereo = Mathf.Lerp(v.from, v.to, Mathf.SmoothStep(0f, 1f, u));
                }
                v.source.volume = v.loudness * level;   // follows the Ambience slider and the pause menu
            }

            var amb = playingAmbience;
            if (amb == null || paused || level <= 0.001f || bedFade < 0.5f) return;
            for (int i = 0; i < amb.cues.Length; i++)
            {
                if (now < amb.next[i]) continue;
                var cue = amb.cues[i];
                amb.next[i] = now + Random.Range(cue.minGap, cue.maxGap);
                var v = cueVoices[nextCueVoice];
                nextCueVoice = (nextCueVoice + 1) % cueVoices.Length;
                float pitch = 1f + Random.Range(-cue.pitchVariance, cue.pitchVariance);
                v.source.clip = amb.cueClips[i];
                v.source.pitch = pitch;
                v.loudness = cue.volume * Random.Range(0.75f, 1.1f);
                v.source.volume = v.loudness * level;
                v.sweep = cue.sweep;
                if (cue.sweep)
                {
                    float dir = Random.value < 0.5f ? -1f : 1f;
                    v.from = -0.85f * dir;
                    v.to = 0.85f * dir;
                    v.start = now;
                    v.length = amb.cueClips[i].length / pitch;
                    v.source.panStereo = v.from;
                }
                else v.source.panStereo = Mathf.Clamp(cue.pan + Random.Range(-cue.panSpread, cue.panSpread), -1f, 1f);
                v.source.Play();
                break;   // one new cue a frame at most
            }
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
                case GameEventType.SlideEnd:
                    PlayInternal(Sfx.GetUp, 0.34f, Vary());
                    break;
                case GameEventType.Land:
                    PlayInternal(Sfx.Land, 0.3f + k * 0.5f, Vary());
                    if (k > 0.6f) Haptics.Impact(Haptics.Strength.Light);
                    break;
                case GameEventType.BallBounce:
                    if (k > 0.15f) PlayInternal(Sfx.Bounce, 0.2f + k * 0.6f, Vary(0.1f) * (1.2f - k * 0.3f));
                    break;
                case GameEventType.Coin: PlayInternal(Sfx.Coin, 0.26f, Vary(0.02f)); break;
                case GameEventType.Sticker: PlayInternal(Sfx.Sticker, 0.8f, 1f); Haptics.Success(); break;
                case GameEventType.Checkpoint: PlayInternal(Sfx.Checkpoint, 0.6f, 1f); break;
                case GameEventType.Bell: PlayInternal(Sfx.Bell, 0.8f, 1f); Haptics.Impact(Haptics.Strength.Heavy); break;
                case GameEventType.Goal: PlayInternal(Sfx.Goal, 0.9f, 1f); Haptics.Success(); break;
                case GameEventType.BallLost: PlayInternal(Sfx.Lose, 0.6f, 1f); Haptics.Impact(Haptics.Strength.Heavy); break;
                case GameEventType.Respawn: PlayInternal(Sfx.Respawn, 0.5f, 1f); break;
                case GameEventType.LevelStart: PlayInternal(Sfx.Whistle, 0.28f, 1f); break;
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
