using System;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Gentle lo-fi loops, one per chapter (0 = menu): soft keys chords, round
    /// bass, a plucked melody built from a repeating motif, and light swung
    /// drums. Deterministic per chapter, seamless when looped. Pure C#, safe to
    /// run on a worker thread.
    /// </summary>
    public static class MusicGenerator
    {
        struct Style
        {
            public int bpm, root;
            public bool minor;
            public int[] progression;   // scale degrees (0-based) per bar
            public float drums, melodyDensity;
            public int seed;
        }

        static Style For(int chapter)
        {
            switch (chapter)
            {
                case 1: return new Style { bpm = 92, root = 62, progression = new[] { 0, 5, 3, 4, 0, 5, 3, 4 }, drums = 0.8f, melodyDensity = 0.55f, seed = 11 };
                case 2: return new Style { bpm = 100, root = 65, progression = new[] { 0, 4, 5, 3, 0, 4, 3, 4 }, drums = 1f, melodyDensity = 0.65f, seed = 22 };
                case 3: return new Style { bpm = 96, root = 67, progression = new[] { 0, 3, 0, 4, 5, 3, 1, 4 }, drums = 0.85f, melodyDensity = 0.6f, seed = 33 };
                case 4: return new Style { bpm = 104, root = 57, minor = true, progression = new[] { 0, 5, 2, 6, 0, 5, 2, 6 }, drums = 1f, melodyDensity = 0.55f, seed = 44 };
                case 5: return new Style { bpm = 110, root = 64, progression = new[] { 0, 4, 5, 3, 0, 4, 3, 4 }, drums = 1f, melodyDensity = 0.7f, seed = 55 };
                default: return new Style { bpm = 86, root = 60, progression = new[] { 0, 3, 5, 4, 0, 3, 1, 4 }, drums = 0.5f, melodyDensity = 0.45f, seed = 7 };
            }
        }

        static readonly int[] Major = { 0, 2, 4, 5, 7, 9, 11 };
        static readonly int[] Minor = { 0, 2, 3, 5, 7, 8, 10 };
        static readonly int[] PentaMajor = { 0, 2, 4, 7, 9 };
        static readonly int[] PentaMinor = { 0, 3, 5, 7, 10 };

        /// <summary>Mono samples at Synth.SampleRate, 8 bars long.</summary>
        public static float[] Generate(int chapter)
        {
            var st = For(chapter);
            var rng = new Random(st.seed);
            int[] scale = st.minor ? Minor : Major;
            int[] penta = st.minor ? PentaMinor : PentaMajor;

            double beat = 60.0 / st.bpm;
            int bars = st.progression.Length;
            double length = bars * 4 * beat;
            var buf = new float[(int)(length * Synth.SampleRate)];
            Func<double, int> at = t => (int)(t * Synth.SampleRate) % buf.Length;

            // Motif: 8 eighth-note slots, reused with variation every bar.
            var motif = new int[8];
            var rhythm = new bool[8];
            for (int i = 0; i < 8; i++)
            {
                motif[i] = rng.Next(0, penta.Length + 2);
                rhythm[i] = rng.NextDouble() < st.melodyDensity || i == 0;
            }

            for (int bar = 0; bar < bars; bar++)
            {
                double barStart = bar * 4 * beat;
                int degree = st.progression[bar];
                int chordRoot = st.root + scale[degree % 7];
                int third = st.root + scale[(degree + 2) % 7] + ((degree + 2) >= 7 ? 12 : 0);
                int fifth = st.root + scale[(degree + 4) % 7] + ((degree + 4) >= 7 ? 12 : 0);
                int[] chord = { chordRoot, third, fifth };

                // Keys: soft chord stabs on beats 1 and 3 (a little strum).
                for (int hit = 0; hit < 2; hit++)
                {
                    double t0 = barStart + hit * 2 * beat;
                    for (int n = 0; n < chord.Length; n++)
                        Keys(buf, at(t0 + n * 0.012), Synth.MidiToHz(chord[n]), (float)(beat * 1.9), 0.07f);
                }

                // Bass: root on 1, a passing note on the "and" of 2, root again on 3.
                Bass(buf, at(barStart), Synth.MidiToHz(chordRoot - 24), (float)(beat * 1.4), 0.32f);
                Bass(buf, at(barStart + 1.5 * beat), Synth.MidiToHz(fifth - 24), (float)(beat * 0.5), 0.2f);
                Bass(buf, at(barStart + 2 * beat), Synth.MidiToHz(chordRoot - 24), (float)(beat * 1.6), 0.28f);

                // Melody: the motif transposed onto this chord, varied in the second half.
                bool vary = bar >= bars / 2;
                for (int i = 0; i < 8; i++)
                {
                    if (!rhythm[i]) continue;
                    if (vary && rng.NextDouble() < 0.25) continue;
                    int step = motif[i] + (vary && i % 3 == 0 ? 1 : 0);
                    int octave = step / penta.Length;
                    int note = st.root + 12 + penta[step % penta.Length] + 12 * octave;
                    // Nudge melody toward chord tones on strong beats.
                    if (i % 4 == 0) note = chord[rng.Next(chord.Length)] + 12;
                    double swing = i % 2 == 1 ? beat * 0.08 : 0;
                    Synth.Pluck(buf, at(barStart + i * beat * 0.5 + swing), Synth.MidiToHz(note), (float)(beat * 1.2), 0.22f, st.seed * 100 + bar * 8 + i);
                }

                // Drums
                if (st.drums > 0f)
                {
                    for (int b = 0; b < 4; b++)
                    {
                        double t = barStart + b * beat;
                        if (b == 0 || b == 2) Kick(buf, at(t), 0.4f * st.drums);
                        if (b == 1 || b == 3) Snare(buf, at(t), 0.11f * st.drums, bar * 4 + b);
                        Hat(buf, at(t), 0.05f * st.drums, bar * 8 + b * 2);
                        Hat(buf, at(t + beat * 0.5 + beat * 0.08), 0.035f * st.drums, bar * 8 + b * 2 + 1);
                    }
                }
            }

            Synth.Master(buf, 0.8f);
            return buf;
        }

        static void Keys(float[] buf, int start, double freq, float seconds, float gain)
        {
            int n = (int)(seconds * Synth.SampleRate);
            double phase = 0;
            for (int i = 0; i < n; i++)
            {
                int j = (start + i) % buf.Length;
                double t = i / (double)Synth.SampleRate;
                phase += freq / Synth.SampleRate;
                float tone = Synth.Sine(phase) + 0.25f * Synth.Sine(phase * 2) + 0.08f * Synth.Sine(phase * 3);
                float trem = 1f - 0.12f * (float)(0.5 + 0.5 * Math.Sin(t * 2 * Math.PI * 4.5));
                float env = Synth.Env(t, 0.01, 1.6) * (float)Math.Min(1, (seconds - t) / 0.05);
                buf[j] += tone * trem * env * gain;
            }
        }

        static void Bass(float[] buf, int start, double freq, float seconds, float gain)
        {
            int n = (int)(seconds * Synth.SampleRate);
            double phase = 0;
            for (int i = 0; i < n; i++)
            {
                int j = (start + i) % buf.Length;
                double t = i / (double)Synth.SampleRate;
                phase += freq / Synth.SampleRate;
                float env = Synth.Env(t, 0.005, 2.5) * (float)Math.Min(1, (seconds - t) / 0.03);
                buf[j] += (Synth.Triangle(phase) * 0.8f + Synth.Sine(phase) * 0.4f) * env * gain;
            }
        }

        static void Kick(float[] buf, int start, float gain)
        {
            double phase = 0;
            int n = (int)(0.25 * Synth.SampleRate);
            for (int i = 0; i < n; i++)
            {
                int j = (start + i) % buf.Length;
                double t = i / (double)Synth.SampleRate;
                double f = 45 + 90 * Math.Exp(-t * 30);
                phase += f / Synth.SampleRate;
                buf[j] += Synth.Sine(phase) * Synth.Env(t, 0.002, 14) * gain;
            }
        }

        static void Snare(float[] buf, int start, float gain, int seed)
        {
            var rng = new Random(seed);
            int n = (int)(0.18 * Synth.SampleRate);
            float lp = 0, hp = 0, prev = 0;
            double phase = 0;
            for (int i = 0; i < n; i++)
            {
                int j = (start + i) % buf.Length;
                double t = i / (double)Synth.SampleRate;
                float white = (float)(rng.NextDouble() * 2 - 1);
                lp += (white - lp) * 0.5f;
                hp = lp - prev;
                prev = lp;
                phase += 185.0 / Synth.SampleRate;
                buf[j] += (hp * 0.9f + Synth.Sine(phase) * 0.3f * Synth.Env(t, 0.001, 40)) * Synth.Env(t, 0.001, 22) * gain;
            }
        }

        static void Hat(float[] buf, int start, float gain, int seed)
        {
            var rng = new Random(seed + 999);
            int n = (int)(0.05 * Synth.SampleRate);
            float prev = 0;
            for (int i = 0; i < n; i++)
            {
                int j = (start + i) % buf.Length;
                double t = i / (double)Synth.SampleRate;
                float white = (float)(rng.NextDouble() * 2 - 1);
                float hp = white - prev;
                prev = white;
                buf[j] += hp * Synth.Env(t, 0.0005, 70) * gain;
            }
        }
    }
}
