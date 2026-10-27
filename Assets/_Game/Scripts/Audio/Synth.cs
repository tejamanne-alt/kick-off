using System;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// Small offline synthesizer: oscillators, envelopes, filters and a
    /// Karplus-Strong pluck. Pure C# (no Unity calls) so it can run on a
    /// background thread.
    /// </summary>
    public static class Synth
    {
        public const int SampleRate = 22050;
        const double TwoPi = Math.PI * 2.0;

        public static float[] Buffer(float seconds) { return new float[(int)(seconds * SampleRate)]; }

        public static float Sine(double phase) { return (float)Math.Sin(phase * TwoPi); }
        public static float Triangle(double phase) { double p = phase - Math.Floor(phase); return (float)(4.0 * Math.Abs(p - 0.5) - 1.0); }
        public static float Saw(double phase) { double p = phase - Math.Floor(phase); return (float)(2.0 * p - 1.0); }
        public static float Square(double phase, double duty = 0.5) { double p = phase - Math.Floor(phase); return p < duty ? 1f : -1f; }

        public static double MidiToHz(double midi) { return 440.0 * Math.Pow(2.0, (midi - 69.0) / 12.0); }

        /// <summary>Attack then exponential decay.</summary>
        public static float Env(double t, double attack, double decayRate)
        {
            if (t < 0) return 0f;
            if (t < attack) return (float)(t / attack);
            return (float)Math.Exp(-(t - attack) * decayRate);
        }

        /// <summary>Tone with an exponential pitch sweep from f0 to f1 over the buffer, shaped by Env.</summary>
        public static void Sweep(float[] buf, int start, float seconds, double f0, double f1, double attack, double decay, float gain,
            Func<double, float> wave = null)
        {
            if (wave == null) wave = Sine;
            int n = (int)(seconds * SampleRate);
            double phase = 0;
            for (int i = 0; i < n && start + i < buf.Length; i++)
            {
                double t = i / (double)SampleRate;
                double k = t / seconds;
                double f = f0 * Math.Pow(f1 / f0, k);
                phase += f / SampleRate;
                buf[start + i] += wave(phase) * Env(t, attack, decay) * gain;
            }
        }

        /// <summary>Filtered noise burst (lowpass 0..1 = brightness).</summary>
        public static void Noise(float[] buf, int start, float seconds, double attack, double decay, float gain, float brightness, int seed)
        {
            var rng = new Random(seed);
            int n = (int)(seconds * SampleRate);
            float lp = 0f;
            for (int i = 0; i < n && start + i < buf.Length; i++)
            {
                double t = i / (double)SampleRate;
                float white = (float)(rng.NextDouble() * 2.0 - 1.0);
                lp += (white - lp) * brightness;
                buf[start + i] += lp * Env(t, attack, decay) * gain;
            }
        }

        /// <summary>Bell-ish tone made of inharmonic partials.</summary>
        public static void Bell(float[] buf, int start, double freq, float seconds, float gain, double decay = 4.0)
        {
            double[] ratios = { 1.0, 2.0, 2.76, 5.4 };
            float[] amps = { 1f, 0.5f, 0.35f, 0.15f };
            for (int p = 0; p < ratios.Length; p++)
                Sweep(buf, start, seconds, freq * ratios[p], freq * ratios[p], 0.002, decay * (1 + p * 0.6), gain * amps[p]);
        }

        /// <summary>Plucked string (Karplus-Strong).</summary>
        public static void Pluck(float[] buf, int start, double freq, float seconds, float gain, int seed, float damping = 0.996f)
        {
            int period = Math.Max(2, (int)(SampleRate / freq));
            var line = new float[period];
            var rng = new Random(seed);
            for (int i = 0; i < period; i++) line[i] = (float)(rng.NextDouble() * 2.0 - 1.0);
            int n = (int)(seconds * SampleRate);
            int idx = 0;
            float prev = 0f;
            for (int i = 0; i < n; i++)
            {
                int j = (start + i) % buf.Length;   // wraps so loops stay seamless
                float v = line[idx];
                float next = line[(idx + 1) % period];
                line[idx] = (v + next) * 0.5f * damping;
                // Soften with a one-pole lowpass for a mellow, nylon-ish tone.
                prev += (v - prev) * 0.5f;
                buf[j] += prev * gain * Env(i / (double)SampleRate, 0.002, 1.5);
                idx = (idx + 1) % period;
            }
        }

        /// <summary>Normalize to a peak and gently soft-clip.</summary>
        public static void Master(float[] buf, float peak = 0.85f)
        {
            float max = 0.0001f;
            for (int i = 0; i < buf.Length; i++) max = Math.Max(max, Math.Abs(buf[i]));
            float k = peak / max;
            for (int i = 0; i < buf.Length; i++) buf[i] = (float)Math.Tanh(buf[i] * k * 1.1) * 0.95f;
        }

        /// <summary>Scale down (never up) so the peak stays at or under <paramref name="ceiling"/>.</summary>
        public static void Limit(float[] buf, float ceiling = 0.9f)
        {
            float max = 0f;
            for (int i = 0; i < buf.Length; i++) max = Math.Max(max, Math.Abs(buf[i]));
            if (max <= ceiling) return;
            float k = ceiling / max;
            for (int i = 0; i < buf.Length; i++) buf[i] *= k;
        }

        /// <summary>Short fade at the very end to avoid clicks on one-shots.</summary>
        public static void FadeTail(float[] buf, float seconds = 0.01f)
        {
            int n = Math.Min(buf.Length, (int)(seconds * SampleRate));
            for (int i = 0; i < n; i++) buf[buf.Length - 1 - i] *= i / (float)n;
        }
    }
}
