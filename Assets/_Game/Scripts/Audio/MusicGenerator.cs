using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// The music: upbeat chillhop, one 16-bar loop for each soundscape (92 to 104 bpm), every one original.
    /// They share the genre's sound: jazzy seventh and ninth chords on a Rhodes-style piano or a mellow
    /// guitar, a bouncing sub or upright bass, a punchy, lightly swung kit (sixteenth hats, ghost notes,
    /// fills, an open hat lifting the second half), rhythmic chord stabs and chops breathing under the kick, a soft lead (vibraphone, flute, melodica, kalimba...), vinyl
    /// crackle, and a tape-warm master (rolled-off highs, gentle saturation, a slight wow). Each place has
    /// its own key, tempo, groove and band: a cosy menu, a sunny Home Street with guitar, a jazzy market
    /// with melodica, a tropical beach with marimba and steel pan, a dark, echoing underpass, a head-nodding
    /// building site with kalimba, and a dreamy park with harp, strings and flute. Each loop has two halves
    /// (A and B) with their own chords and lead, a melody built from motifs that come back, and a snare fill
    /// into each half. Deterministic, seamless when looped (notes, the reverb's tail and
    /// the tape's wow all wrap round), pure C#: safe on a worker thread. Output: interleaved stereo at
    /// <see cref="Synth.SampleRate"/>.
    /// </summary>
    public static class MusicGenerator
    {
        public const int Channels = 2;
        /// <summary>The loops' loudness (RMS of the mix): every soundscape plays equally loud.</summary>
        public const float Loudness = 0.14f;
        const int Bars = 16;

        /// <summary>The music for a chapter (0 = the menu), for code that only knows the chapter.</summary>
        public static float[] Generate(int chapter)
        {
            return Generate(chapter <= 0 ? Soundscape.Menu : Soundscapes.For(null, chapter));
        }

        public static float[] Generate(Soundscape scape)
        {
            return Chill(StyleOf(scape));
        }

        // ================= Styles =================

        enum Comp { None, Rhodes, Guitar, Marimba, Kalimba, Harp }
        enum Lead { Vibes, Flute, Melodica, Kalimba, SteelPan, Rhodes, Guitar }

        sealed class Style
        {
            public double bpm, swing;
            public int key, seed;
            public Mode mode;
            public string[] chords;
            public Comp comp, comp2;
            public bool comp2OnlyInB;
            public Lead leadA, leadB;
            public int leadLo = 67, leadHi = 81;
            public bool upright, pad, strings, shaker, congas, rimInsteadOfSnare;
            public int groove;
            public float room = 0.6f, wet = 0.25f, vinyl = 1f;
            public double tone = 5200;
        }

        static Style StyleOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street:
                    // A sunny morning walk: major ninths on a warm guitar and Rhodes, a whistled flute.
                    return new Style
                    {
                        bpm = 100, swing = 0.1, key = 62, mode = Mode.Major, seed = 11,
                        chords = new[] { "Gmaj9", "F#m7", "Em9", "A13", "Gmaj9", "F#m7", "Bm9", "A7sus4",
                                         "Gmaj9", "A13", "F#m7", "Bm9", "Em9", "A13", "Dmaj9", "Dmaj9" },
                        comp = Comp.Guitar, comp2 = Comp.Rhodes, leadA = Lead.Flute, leadB = Lead.Vibes,
                        leadLo = 69, leadHi = 83, upright = false, pad = true, shaker = true, groove = 0,
                        room = 0.55f, wet = 0.22f, tone = 5600,
                    };
                case Soundscape.Market:
                    // Jazzy and bouncy: a ii-V-I market cafe, upright bass, muted guitar, melodica.
                    return new Style
                    {
                        bpm = 104, swing = 0.13, key = 65, mode = Mode.Major, seed = 22,
                        chords = new[] { "Gm9", "C13", "Fmaj9", "Dm9", "Gm9", "C13", "Am7", "D7",
                                         "Bbmaj9", "Am7", "Gm9", "C13", "Bbmaj9", "A7", "Dm9", "C13" },
                        comp = Comp.Rhodes, comp2 = Comp.Guitar, comp2OnlyInB = true, leadA = Lead.Melodica, leadB = Lead.Vibes,
                        leadLo = 67, leadHi = 81, upright = true, shaker = true, groove = 1,
                        room = 0.5f, wet = 0.2f, tone = 5200,
                    };
                case Soundscape.Beach:
                    // Tropical chillhop: soft marimba off-beats, a gentle steel pan, congas and a shaker.
                    return new Style
                    {
                        bpm = 100, swing = 0.1, key = 67, mode = Mode.Major, seed = 33,
                        chords = new[] { "Cmaj9", "Bm7", "Am9", "D13", "Cmaj9", "Bm7", "Em9", "D7sus4",
                                         "Am9", "D13", "Gmaj9", "Em9", "Am9", "Bm7", "Cmaj9", "D13" },
                        comp = Comp.Rhodes, comp2 = Comp.Marimba, leadA = Lead.SteelPan, leadB = Lead.Kalimba,
                        leadLo = 69, leadHi = 83, pad = true, shaker = true, congas = true, rimInsteadOfSnare = true, groove = 0,
                        room = 0.6f, wet = 0.24f, tone = 5600,
                    };
                case Soundscape.Underpass:
                    // Late-night and echoing: minor ninths, a dark pad, a slow, half-time beat, vibes in the reverb.
                    return new Style
                    {
                        bpm = 94, swing = 0.08, key = 57, mode = Mode.Minor, seed = 44,
                        chords = new[] { "Am9", "Am9", "Fmaj9", "E7", "Am9", "Dm9", "Bm7b5", "E7",
                                         "Fmaj9", "G13", "Em9", "Am9", "Dm9", "G13", "Cmaj9", "E7" },
                        comp = Comp.Rhodes, leadA = Lead.Vibes, leadB = Lead.Rhodes,
                        leadLo = 64, leadHi = 79, pad = true, groove = 1,
                        room = 0.88f, wet = 0.36f, tone = 4300, vinyl = 1.3f,
                    };
                case Soundscape.Site:
                    // A head-nodding boom-bap work-song: dorian minor, punchier drums, guitar and kalimba.
                    return new Style
                    {
                        bpm = 102, swing = 0.12, key = 62, mode = Mode.Dorian, seed = 55,
                        chords = new[] { "Dm9", "G13", "Dm9", "G13", "Fmaj9", "Em7", "Am9", "A7",
                                         "Bbmaj9", "C13", "Am9", "Dm9", "Bbmaj9", "C13", "Em7b5", "A7" },
                        comp = Comp.Guitar, comp2 = Comp.Kalimba, leadA = Lead.Kalimba, leadB = Lead.Vibes,
                        leadLo = 67, leadHi = 81, upright = true, shaker = true, groove = 1,
                        room = 0.45f, wet = 0.18f, tone = 5000,
                    };
                case Soundscape.Park:
                    // Dreamy, the last stretch to school: harp arpeggios, soft strings, a flute.
                    return new Style
                    {
                        bpm = 96, swing = 0.08, key = 63, mode = Mode.Major, seed = 66,
                        chords = new[] { "Abmaj9", "Gm7", "Fm9", "Bb13", "Abmaj9", "Gm7", "Cm9", "Bb7sus4",
                                         "Abmaj9", "Bb13", "Gm7", "Cm9", "Fm9", "Bb13", "Ebmaj9", "Ebmaj9" },
                        comp = Comp.Harp, comp2 = Comp.Rhodes, leadA = Lead.Flute, leadB = Lead.Vibes,
                        leadLo = 68, leadHi = 82, strings = true, groove = 1,
                        room = 0.78f, wet = 0.3f, tone = 5800,
                    };
                default:
                    // The menu: a cup of tea before school. Rhodes ninths, vinyl, a lazy beat, vibes.
                    return new Style
                    {
                        bpm = 92, swing = 0.12, key = 60, mode = Mode.Major, seed = 7,
                        chords = new[] { "Fmaj9", "Em7", "Dm9", "G13", "Fmaj9", "Em7", "Am9", "G7sus4",
                                         "Dm9", "G13", "Cmaj9", "Am9", "Dm9", "Em7", "Fmaj9", "G13" },
                        comp = Comp.Rhodes, leadA = Lead.Vibes, leadB = Lead.Rhodes,
                        leadLo = 67, leadHi = 81, pad = true, groove = 0,
                        room = 0.7f, wet = 0.28f, tone = 4800, vinyl = 1.3f,
                    };
            }
        }

        // ================= The arranger =================

        static float[] Chill(Style st)
        {
            var s = new Song(st.bpm, st.swing, st.key, st.mode, st.seed, st.chords);
            var rng = new Random(st.seed * 31);
            var mix = new Mixdown(s.Length)
            {
                roomSize = st.room, damping = 0.6f, wet = st.wet,
                tone = st.tone + 1300, drive = 0.15f, wowCents = 4f, wowCycles = 8,
            };
            var keys = mix.Add(-0.18f, 0.35f, 0.62f);
            keys.duck = 0.3f;
            var keys2 = mix.Add(0.32f, 0.3f, 0.5f);
            keys2.duck = 0.25f;
            var padL = mix.Add(-0.6f, 0.55f, 0.18f);
            var padR = mix.Add(0.6f, 0.55f, 0.18f);
            padL.duck = padR.duck = 0.55f;
            var bass = mix.Add(0f, 0.04f, 0.9f);
            bass.duck = 0.2f;
            var lead = mix.Add(0.2f, 0.45f, 0.42f);
            var kick = mix.Add(0f, 0.04f, 1f);
            var snare = mix.Add(0.04f, 0.16f, 0.68f);
            var hats = mix.Add(0.28f, 0.06f, 0.3f);
            var perc = mix.Add(-0.4f, 0.15f, 0.3f);
            var vinyl = mix.Add(0f, 0f, 0.55f * st.vinyl);

            for (int bar = 0; bar < Bars; bar++)
            {
                bool breakBar = bar == Bars - 1;   // the last bar: a fill back to the top
                bool inB = bar >= Bars / 2;
                foreach (var ch in s.ChordsIn(bar))
                {
                    var voicing = ch.chord.Voice(55, 74, 4, true);
                    Play(st.comp, keys, s, bar, ch, voicing, rng, 1f);
                    if (st.comp2 != Comp.None && (!st.comp2OnlyInB || inB))
                        Play(st.comp2, keys2, s, bar, ch, ch.chord.Voice(62, 79, 4, true), rng, 0.7f);
                    if (st.pad) Instruments.Pad(padL, s.T(bar, ch.beat), ch.chord.Voice(48, 62, 3), s.Beats(ch.length), 0.5f, 700, bar * 3 + 1);
                    if (st.pad) Instruments.Pad(padR, s.T(bar, ch.beat), ch.chord.Voice(55, 67, 3, true), s.Beats(ch.length), 0.5f, 750, bar * 3 + 2);
                    if (st.strings) Instruments.Strings(padL, s.T(bar, ch.beat), ch.chord.Voice(53, 67, 3), s.Beats(ch.length), 0.55f, bar * 5 + 1);
                    if (st.strings) Instruments.Strings(padR, s.T(bar, ch.beat), ch.chord.Voice(60, 74, 3, true), s.Beats(ch.length), 0.5f, bar * 5 + 2);

                    // Bass: a bouncing line, root on the one, the octave popping up on the off-beats, a push
                    // before the three, and a walk up into the next chord at the end of every other bar.
                    int root = ch.chord.Bass(36);
                    if (root > 43) root -= 12;
                    int fifth = root + 7;
                    double[] at = { 0, 0.75, 1.5, 2, 2.75, 3.25 };
                    int[] line = { root, root + 12, root, fifth, root + 12, fifth };
                    double[] len = { 0.65, 0.35, 0.4, 0.6, 0.35, 0.4 };
                    for (int k = 0; k < at.Length; k++)
                    {
                        if (at[k] >= ch.length) break;
                        if (breakBar && ch.beat + at[k] >= 3) break;
                        BassNote(st, bass, s, bar, ch.beat + at[k], line[k], len[k], k == 0 ? 0.9f : 0.68f, bar * 8 + k);
                    }
                    if (ch.length >= 4 && bar % 2 == 1 && !breakBar)
                    {
                        int next = s.ChordsIn(bar + 1)[0].chord.Bass(36);
                        if (next > 43) next -= 12;
                        BassNote(st, bass, s, bar, ch.beat + 3.75, next + (next > root ? -1 : 1), 0.25, 0.55f, bar * 8 + 7);
                    }
                }

                Drums(st, s, mix, kick, snare, hats, perc, bar, breakBar, rng);
            }
            Instruments.Vinyl(vinyl, 1f, st.seed);

            // The tunes: a soft lead in each half, the second a little higher.
            foreach (var n in s.Melody(0, st.leadLo, st.leadHi, new Random(st.seed * 10), Rhythms.Bouncy))
                PlayLead(st.leadA, lead, s, n);
            foreach (var n in s.Melody(8, st.leadLo + 2, st.leadHi + 2, new Random(st.seed * 10 + 1), Rhythms.Dance))
                PlayLead(st.leadB, lead, s, n);
            return mix.Render(Loudness);
        }

        static void BassNote(Style st, Track bass, Song s, int bar, double beat, int midi, double beats, float vel, int seed)
        {
            if (st.upright) Instruments.UprightBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel, seed);
            else Instruments.SubBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel);
        }

        static void Play(Comp comp, Track tr, Song s, int bar, ChordAt ch, int[] v, Random rng, float level)
        {
            if (v.Length == 0) return;
            double span = ch.length;
            switch (comp)
            {
                case Comp.Rhodes:
                {
                    // Short, rhythmic stabs that push the groove along: the one, off-beats, a pickup into the next bar.
                    double[] at = bar % 2 == 0 ? new[] { 0, 1.5, 2.75, 3.5 } : new[] { 0, 0.75, 2, 3.5 };
                    for (int k = 0; k < at.Length; k++)
                        if (at[k] < span)
                            Instruments.RhodesChord(tr, s.T(bar, ch.beat + at[k]), v, s.Beats(k == 0 ? 0.9 : 0.45), (k == 0 ? 0.52f : 0.4f) * level, 0.008);
                    break;
                }
                case Comp.Guitar:
                {
                    // Picked through the chord, low to high and back, letting the notes ring into each other.
                    // Funky muted chops on the sixteenths, the notes caught in turn.
                    double[] at = { 0, 0.5, 0.75, 1.5, 2, 2.5, 2.75, 3.5 };
                    int[] order = { 0, 2, 1, 3, 0, 2, 1, 3 };
                    for (int i = 0; i < at.Length; i++)
                    {
                        if (at[i] >= span) break;
                        if (i > 0 && rng.NextDouble() < 0.15) continue;
                        Instruments.Pluck(tr, s.T(bar, ch.beat + at[i]), Synth.MidiToHz(v[order[i] % v.Length]), s.Beats(0.35), 0.55f * level, bar * 40 + i, 0.3f);
                    }
                    break;
                }
                case Comp.Marimba:
                    for (double b = 0.5; b < span; b += 1)
                        for (int k = Math.Max(0, v.Length - 2); k < v.Length; k++)
                            Instruments.Marimba(tr, s.T(bar, ch.beat + b), Synth.MidiToHz(v[k]), 0.32f * level);
                    break;
                case Comp.Kalimba:
                {
                    double[] at = { 0.5, 1.5, 1.75, 3, 3.5 };
                    for (int i = 0; i < at.Length; i++)
                        if (at[i] < span) Instruments.Kalimba(tr, s.T(bar, ch.beat + at[i]), Synth.MidiToHz(v[(i * 2 + bar) % v.Length] + 12), 0.36f * level);
                    break;
                }
                case Comp.Harp:
                {
                    int steps = (int)(span * 2);
                    int len = v.Length * 2 - 2;
                    for (int e = 0; e < steps; e++)
                    {
                        int k = len > 0 ? e % len : 0;
                        int idx = k < v.Length ? k : len - k;
                        Instruments.Pluck(tr, s.T(bar, ch.beat + e * 0.5), Synth.MidiToHz(v[idx] + 12), s.Beats(2), 0.4f * level, bar * 50 + e, 0.35f, 0.997f);
                    }
                    break;
                }
            }
        }

        static void PlayLead(Lead lead, Track tr, Song s, Note n)
        {
            double t = s.T(n), d = s.Beats(n.len);
            double f = Synth.MidiToHz(n.midi);
            float v = n.vel;
            switch (lead)
            {
                case Lead.Vibes: Instruments.Vibes(tr, t, f, d, v * 0.9f); break;
                case Lead.Flute: Instruments.Flute(tr, t, f, d * 0.95, v, n.midi * 13); break;
                case Lead.Melodica: Instruments.Melodica(tr, t, f, d * 0.9, v, n.midi * 7); break;
                case Lead.Kalimba: Instruments.Kalimba(tr, t, f, v); break;
                case Lead.SteelPan: Instruments.SteelPan(tr, t, f, d, v * 0.9f); break;
                case Lead.Rhodes: Instruments.Rhodes(tr, t, f, d, v * 0.65f); break;
                default: Instruments.Pluck(tr, t, f, d, v * 0.7f, n.midi * 3, 0.3f); break;
            }
        }

        /// <summary>
        /// An upbeat, head-nodding kit: the kick on the one with a syncopated second and third kick, a punchy
        /// snare on two and four (a hair late, with ghost notes), sixteenth hats with their accents on the
        /// beat and the off-beat, an open hat lifting the second half, a snare fill into each half. The chords
        /// dip under each kick.
        /// </summary>
        static void Drums(Style st, Song s, Mixdown mix, Track kick, Track snare, Track hats, Track perc, int bar, bool breakBar, Random rng)
        {
            double late = 0.02;   // beats: the snare sits just behind the beat
            bool inB = bar >= Bars / 2;
            bool fill = bar == Bars / 2 - 1 || breakBar;
            double[] kicks = st.groove == 1
                ? (bar % 2 == 0 ? new[] { 0, 0.75, 1.75, 2.5 } : new[] { 0, 1.5, 2.25, 2.75 })
                : (bar % 2 == 0 ? new[] { 0, 1.75, 2.5 } : new[] { 0, 0.75, 2.5, 3.25 });
            foreach (double k in kicks)
            {
                if (fill && k >= 3) continue;
                double t = s.T(bar, k);
                Instruments.Kick(kick, t, k == 0 ? 1f : 0.8f);
                mix.Duck(t, k == 0 ? 0.9f : 0.65f, 0.12);
            }
            foreach (double b in new[] { 1.0, 3.0 })
            {
                if (fill && b >= 3) continue;
                double t = s.T(bar, b) + s.Beats(late);
                if (st.rimInsteadOfSnare && !inB) Instruments.Rim(snare, t, 0.8f);
                else Instruments.Snare(snare, t, 0.75f, bar * 4 + (int)b);
            }
            // Ghost notes around the backbeat.
            if (rng.NextDouble() < 0.6) Instruments.Snare(snare, s.T(bar, 1.75) + s.Beats(late), 0.14f, 700 + bar);
            if (!fill && rng.NextDouble() < 0.7) Instruments.Snare(snare, s.T(bar, 3.75) + s.Beats(late), 0.18f, 900 + bar);
            // The fill: a little roll on the last beat, rising.
            if (fill)
                for (int k = 0; k < 4; k++) Instruments.Snare(snare, s.T(bar, 3 + k * 0.25), 0.3f + k * 0.12f, 1100 + bar * 4 + k);

            for (int e = 0; e < 16; e++)
            {
                double b = e * 0.25;
                if (fill && b >= 3) break;
                float vel = e % 4 == 0 ? 0.55f : e % 4 == 2 ? 0.45f : 0.2f;
                vel *= (float)(0.85 + rng.NextDouble() * 0.3);
                Instruments.Hat(hats, s.T(bar, b), vel, bar * 16 + e);
                if (st.shaker && e % 2 == 1) Instruments.Shaker(perc, s.T(bar, b), e % 4 == 3 ? 0.4f : 0.25f, bar * 16 + e);
            }
            if (inB && !fill) Instruments.OpenHat(hats, s.T(bar, 3.5), 0.4f, bar);
            if (st.congas && !fill)
            {
                Instruments.Conga(perc, s.T(bar, 0.75), 0.4f, true);
                Instruments.Conga(perc, s.T(bar, 1.5), 0.5f, true);
                Instruments.Conga(perc, s.T(bar, 2.75), 0.45f, false);
                Instruments.Conga(perc, s.T(bar, 3.25), 0.4f, true);
            }
        }

        // ================= Theory =================

        enum Mode { Major, Minor, Dorian }

        static readonly int[] MajorScale = { 0, 2, 4, 5, 7, 9, 11 };
        static readonly int[] MinorScale = { 0, 2, 3, 5, 7, 8, 10 };
        static readonly int[] DorianScale = { 0, 2, 3, 5, 7, 9, 10 };

        struct Note
        {
            public double beat, len;
            public int midi;
            public float vel;
        }

        struct ChordAt
        {
            public double beat, length;
            public Chord chord;
        }

        /// <summary>A chord from its name: a root (C, F#, Bb...), a quality (m, 7, maj7, m7, sus4, 7sus4, 6) and an optional bass ("/D").</summary>
        sealed class Chord
        {
            public readonly int root;       // pitch class
            public readonly int bass;       // pitch class
            public readonly int[] tones;    // intervals from the root

            public Chord(string name)
            {
                string bassName = null;
                int slash = name.IndexOf('/');
                if (slash >= 0) { bassName = name.Substring(slash + 1); name = name.Substring(0, slash); }
                int i;
                root = PitchClass(name, out i);
                string q = name.Substring(i);
                switch (q)
                {
                    case "m": tones = new[] { 0, 3, 7 }; break;
                    case "7": tones = new[] { 0, 4, 7, 10 }; break;
                    case "maj7": tones = new[] { 0, 4, 7, 11 }; break;
                    case "m7": tones = new[] { 0, 3, 7, 10 }; break;
                    case "sus4": tones = new[] { 0, 5, 7 }; break;
                    case "7sus4": tones = new[] { 0, 5, 7, 10 }; break;
                    case "6": tones = new[] { 0, 4, 7, 9 }; break;
                    case "maj9": tones = new[] { 0, 4, 7, 11, 14 }; break;
                    case "m9": tones = new[] { 0, 3, 7, 10, 14 }; break;
                    case "9": tones = new[] { 0, 4, 7, 10, 14 }; break;
                    case "13": tones = new[] { 0, 4, 10, 14, 21 }; break;
                    case "m7b5": tones = new[] { 0, 3, 6, 10 }; break;
                    default: tones = new[] { 0, 4, 7 }; break;
                }
                int dummy;
                bass = bassName != null ? PitchClass(bassName, out dummy) : root;
            }

            static int PitchClass(string s, out int used)
            {
                int[] letters = { 9, 11, 0, 2, 4, 5, 7 };   // A B C D E F G
                int pc = letters[s[0] - 'A'];
                used = 1;
                if (s.Length > 1 && s[1] == '#') { pc++; used = 2; }
                else if (s.Length > 1 && s[1] == 'b') { pc--; used = 2; }
                return (pc + 12) % 12;
            }

            public bool Has(int midi)
            {
                int pc = ((midi % 12) + 12) % 12;
                foreach (int t in tones) if ((root + t) % 12 == pc) return true;
                return false;
            }

            /// <summary>The bass note: the lowest note of the bass's pitch class at or above <paramref name="floor"/>.</summary>
            public int Bass(int floor)
            {
                int m = floor;
                while (((m % 12) + 12) % 12 != bass) m++;
                return m;
            }

            /// <summary>
            /// Chord tones between <paramref name="lo"/> and <paramref name="hi"/>, at most <paramref name="max"/> of them
            /// from the bottom; rootless (as a jazz pianist leaves the root to the bass) when asked, and never two a
            /// semitone apart low down, where they would rub.
            /// </summary>
            public int[] Voice(int lo, int hi, int max = 4, bool rootless = false)
            {
                var list = new List<int>();
                for (int m = lo; m <= hi && list.Count < max; m++)
                {
                    if (!Has(m)) continue;
                    if (rootless && ((m % 12) + 12) % 12 == root && tones.Length > 3) continue;
                    if (list.Count > 0 && m - list[list.Count - 1] < 2 && m < 64) continue;
                    list.Add(m);
                }
                return list.ToArray();
            }
        }

        /// <summary>A loop's tempo, swing, key and chords (one or two a bar), and the clock that places notes in it.</summary>
        sealed class Song
        {
            readonly double bpm, swing;
            readonly int key;
            readonly int[] scale;
            readonly List<ChordAt>[] bars;
            readonly Random human;
            public readonly int Length;

            public Song(double bpm, double swing, int key, Mode mode, int seed, params string[] chords)
            {
                this.bpm = bpm;
                this.swing = swing;
                this.key = key;
                scale = mode == Mode.Major ? MajorScale : mode == Mode.Minor ? MinorScale : DorianScale;
                human = new Random(seed);
                bars = new List<ChordAt>[chords.Length];
                for (int b = 0; b < chords.Length; b++)
                {
                    var names = chords[b].Split(' ');
                    bars[b] = new List<ChordAt>();
                    double each = 4.0 / names.Length;
                    for (int k = 0; k < names.Length; k++)
                        bars[b].Add(new ChordAt { beat = k * each, length = each, chord = new Chord(names[k]) });
                }
                Length = (int)Math.Round(chords.Length * 4 * 60.0 / bpm * Synth.SampleRate);
            }

            public List<ChordAt> ChordsIn(int bar) { return bars[((bar % bars.Length) + bars.Length) % bars.Length]; }

            public Chord ChordAtBeat(double absBeat)
            {
                int bar = (int)Math.Floor(absBeat / 4.0);
                double inBar = absBeat - bar * 4.0;
                var list = ChordsIn(bar);
                for (int i = list.Count - 1; i >= 0; i--)
                    if (inBar >= list[i].beat - 1e-6) return list[i].chord;
                return list[0].chord;
            }

            public double Beats(double beats) { return beats * 60.0 / bpm; }

            /// <summary>Seconds from the loop's start to a beat of a bar, with swing on the off-beat quavers and a hair of human timing.</summary>
            public double T(int bar, double beat)
            {
                double frac = beat - Math.Floor(beat);
                double b = bar * 4 + beat;
                if (Math.Abs(frac - 0.5) < 1e-6) b += swing;
                else if (Math.Abs(frac - 0.75) < 1e-6) b += swing * 0.5;
                return b * 60.0 / bpm + (human.NextDouble() - 0.5) * 0.006;
            }

            public double T(Note n)
            {
                int bar = (int)Math.Floor(n.beat / 4.0);
                return T(bar, n.beat - bar * 4.0);
            }

            bool InScale(int midi)
            {
                int pc = (((midi - key) % 12) + 12) % 12;
                return Array.IndexOf(scale, pc) >= 0;
            }

            /// <summary>
            /// An eight-bar tune from bar <paramref name="firstBar"/>: a two-bar motif, its answer, the motif
            /// again (re-fitted to the chords) and a cadence; strong beats land on chord tones, the rest step
            /// through the scale, the line climbs through the first half of the phrase and settles at its end.
            /// </summary>
            public List<Note> Melody(int firstBar, int lo, int hi, Random rng, double[][] bank)
            {
                var notes = new List<Note>();
                double[] motifA = bank[rng.Next(bank.Length)];
                double[] motifB = bank[rng.Next(bank.Length)];
                double[] cadenceHalf = Rhythms.HalfCadence;
                double[] cadenceEnd = Rhythms.FullCadence;
                int cur = (lo + hi) / 2;
                var firstPitches = new List<int>[2];

                for (int b = 0; b < 8; b++)
                {
                    double[] rhythm;
                    int copyFrom = -1;
                    switch (b)
                    {
                        case 0: rhythm = motifA; break;
                        case 1: rhythm = motifB; break;
                        case 2: rhythm = motifA; break;
                        case 3: rhythm = cadenceHalf; break;
                        case 4: rhythm = motifA; copyFrom = 0; break;
                        case 5: rhythm = motifB; copyFrom = 1; break;
                        case 6: rhythm = motifA; break;
                        default: rhythm = cadenceEnd; break;
                    }
                    // The contour: up through each half phrase, down into its cadence.
                    double arc = (b % 4) / 3.0;
                    int target = (int)Math.Round(b % 4 == 3 ? lo + (hi - lo) * 0.35 : lo + (hi - lo) * (0.45 + 0.4 * Math.Sin(arc * Math.PI)));
                    var pitches = new List<int>();
                    for (int i = 0; i + 1 < rhythm.Length; i += 2)
                    {
                        double beat = (firstBar + b) * 4 + rhythm[i];
                        double len = rhythm[i + 1];
                        var chord = ChordAtBeat(beat);
                        bool strong = Math.Abs(rhythm[i] - Math.Round(rhythm[i])) < 1e-6 && ((int)Math.Round(rhythm[i]) % 2 == 0 || len >= 1.5);
                        int midi;
                        int k = i / 2;
                        if (copyFrom >= 0 && firstPitches[copyFrom] != null && k < firstPitches[copyFrom].Count)
                        {
                            midi = firstPitches[copyFrom][k];
                            if (strong && !chord.Has(midi)) midi = Nearest(midi, lo, hi, m => chord.Has(m));
                            else if (!InScale(midi)) midi = Nearest(midi, lo, hi, InScale);
                        }
                        else if (b == 7 && i + 2 >= rhythm.Length)
                            midi = Nearest(cur, lo, hi, m => ((m % 12 + 12) % 12) == chord.root);   // home on the root
                        else
                            midi = Pick(cur, target, chord, strong, lo, hi, rng);
                        pitches.Add(midi);
                        cur = midi;
                        float vel = (float)((strong ? 0.85 : 0.68) + rng.NextDouble() * 0.12);
                        notes.Add(new Note { beat = beat, len = len, midi = midi, vel = vel });
                    }
                    if (b < 2) firstPitches[b] = pitches;
                }
                return notes;
            }

            int Pick(int cur, int target, Chord chord, bool strong, int lo, int hi, Random rng)
            {
                int best = cur;
                double bestScore = double.MaxValue;
                for (int m = lo; m <= hi; m++)
                {
                    if (strong ? !chord.Has(m) : !InScale(m)) continue;
                    int leap = Math.Abs(m - cur);
                    if (!strong && leap > 5) continue;
                    double score = leap * 1.0 + Math.Abs(m - target) * 0.4 + (m == cur ? 2.0 : 0) + rng.NextDouble() * 2.2;
                    if (leap > 7) score += 4;
                    if (score < bestScore) { bestScore = score; best = m; }
                }
                return best;
            }

            static int Nearest(int from, int lo, int hi, Func<int, bool> ok)
            {
                for (int d = 0; d <= 12; d++)
                {
                    if (from - d >= lo && ok(from - d)) return from - d;
                    if (from + d <= hi && ok(from + d)) return from + d;
                }
                return Math.Max(lo, Math.Min(hi, from));
            }
        }

        /// <summary>One-bar rhythms for the tunes, as (beat, length) pairs.</summary>
        static class Rhythms
        {
            public static readonly double[][] Sparse =
            {
                new double[] { 0, 1.5, 1.5, 0.5, 2, 2 },
                new double[] { 0.5, 1, 1.5, 1, 2.5, 1.5 },
                new double[] { 0, 2, 2.5, 1.5 },
                new double[] { 1, 1, 2, 0.5, 2.5, 1.5 },
            };

            public static readonly double[][] Bouncy =
            {
                new double[] { 0, 0.5, 0.5, 0.5, 1, 1, 2, 0.5, 2.5, 0.5, 3, 1 },
                new double[] { 0, 1, 1, 0.5, 1.5, 1, 2.5, 0.5, 3, 1 },
                new double[] { 0, 0.5, 0.5, 1, 1.5, 0.5, 2, 1.5, 3.5, 0.5 },
                new double[] { 0, 1.5, 1.5, 0.5, 2, 0.5, 2.5, 0.5, 3, 1 },
            };

            public static readonly double[][] Singing =
            {
                new double[] { 0, 1.5, 1.5, 0.5, 2, 2 },
                new double[] { 0, 1, 1, 1, 2, 1.5, 3.5, 0.5 },
                new double[] { 0, 2, 2, 1, 3, 1 },
                new double[] { 0, 1.5, 1.5, 1.5, 3, 1 },
            };

            public static readonly double[][] Dance =
            {
                new double[] { 0, 0.5, 0.5, 0.5, 1, 0.5, 1.5, 0.5, 2, 1, 3, 1 },
                new double[] { 0, 1, 1, 0.5, 1.5, 0.5, 2, 0.5, 2.5, 0.5, 3, 1 },
                new double[] { 0, 0.5, 0.5, 0.5, 1, 1, 2, 0.5, 2.5, 0.5, 3, 0.5, 3.5, 0.5 },
            };

            public static readonly double[] HalfCadence = { 0, 0.5, 0.5, 0.5, 1, 3 };
            public static readonly double[] FullCadence = { 0, 1, 1, 3 };
        }
    }
}
