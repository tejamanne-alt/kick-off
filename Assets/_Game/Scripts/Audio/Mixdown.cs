using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// One instrument's part in a loop: a mono buffer as long as the loop (notes wrap round its end,
    /// so the loop stays seamless), where it sits left to right, and how much of it goes to the reverb.
    /// </summary>
    public sealed class Track
    {
        public readonly float[] buf;
        /// <summary>-1 (left) to 1 (right).</summary>
        public float pan;
        /// <summary>How much goes to the shared reverb (0 dry, 1 very wet).</summary>
        public float send;
        public float gain = 1f;

        public Track(int length, float pan, float send, float gain)
        {
            buf = new float[length];
            this.pan = pan;
            this.send = send;
            this.gain = gain;
        }

        public int Length { get { return buf.Length; } }

        /// <summary>Add a sample at any index: wraps round the loop.</summary>
        public void Add(int index, float v)
        {
            int n = buf.Length;
            index %= n;
            if (index < 0) index += n;
            buf[index] += v;
        }
    }

    /// <summary>
    /// A stereo mixdown of tracks for a seamless loop: constant-power panning, a shared stereo reverb
    /// (Freeverb-style: eight damped combs and four all-passes a side) whose tail wraps round into the
    /// loop's start, a gentle high-pass, then loudness matched to an RMS target and soft-clipped. Pure C#,
    /// safe on a worker thread. Output is interleaved stereo (L, R, L, R...).
    /// </summary>
    public sealed class Mixdown
    {
        readonly int length;
        readonly List<Track> tracks = new List<Track>();

        public float roomSize = 0.6f;
        public float damping = 0.4f;
        public float wet = 0.3f;
        /// <summary>Extra width of the reverb (0 mono, 1 wide).</summary>
        public float width = 1f;

        public Mixdown(int length) { this.length = length; }

        public int Length { get { return length; } }

        public Track Add(float pan, float send, float gain = 1f)
        {
            var t = new Track(length, pan, send, gain);
            tracks.Add(t);
            return t;
        }

        /// <summary>
        /// Mix every track down to interleaved stereo with the loudness at <paramref name="targetRms"/>
        /// (or, when that is 0, with the loudest peak at the ceiling: for one-shots).
        /// </summary>
        public float[] Render(float targetRms, float ceiling = 0.98f)
        {
            var left = new float[length];
            var right = new float[length];
            var send = new float[length];
            foreach (var t in tracks)
            {
                double a = (Math.Max(-1f, Math.Min(1f, t.pan)) + 1.0) * Math.PI * 0.25;
                float gl = (float)Math.Cos(a) * t.gain * 1.414f, gr = (float)Math.Sin(a) * t.gain * 1.414f;
                float gs = t.send * t.gain;
                var b = t.buf;
                for (int i = 0; i < length; i++)
                {
                    float v = b[i];
                    if (v == 0f) continue;
                    left[i] += v * gl;
                    right[i] += v * gr;
                    send[i] += v * gs;
                }
            }

            if (wet > 0f) Reverb(send, left, right);

            HighPass(left, 28f);
            HighPass(right, 28f);
            return Finish(left, right, targetRms, ceiling);
        }

        /// <summary>Interleave, match the loudness, soft-clip any peaks and keep under the ceiling.</summary>
        public static float[] Finish(float[] left, float[] right, float targetRms, float ceiling)
        {
            int n = left.Length;
            double sum = 0;
            for (int i = 0; i < n; i++) sum += left[i] * left[i] + right[i] * right[i];
            float rms = (float)Math.Sqrt(sum / Math.Max(1, 2 * n));
            float k = rms > 1e-6f ? targetRms / rms : 1f;
            if (targetRms <= 0f)
            {
                float peak = 1e-6f;
                for (int i = 0; i < n; i++) peak = Math.Max(peak, Math.Max(Math.Abs(left[i]), Math.Abs(right[i])));
                k = 0.6f / peak;   // the top of the soft clip's linear range
            }
            var outBuf = new float[n * 2];
            float max = 0f;
            for (int i = 0; i < n; i++)
            {
                float l = SoftClip(left[i] * k), r = SoftClip(right[i] * k);
                outBuf[2 * i] = l;
                outBuf[2 * i + 1] = r;
                max = Math.Max(max, Math.Max(Math.Abs(l), Math.Abs(r)));
            }
            if (max > ceiling)
            {
                float s = ceiling / max;
                for (int i = 0; i < outBuf.Length; i++) outBuf[i] *= s;
            }
            return outBuf;
        }

        /// <summary>Linear below 0.6, then a smooth knee that never passes 1.</summary>
        static float SoftClip(float x)
        {
            float a = Math.Abs(x);
            if (a <= 0.6f) return x;
            float over = (a - 0.6f) / 0.4f;
            float y = 0.6f + 0.4f * (float)Math.Tanh(over);
            return x < 0f ? -y : y;
        }

        /// <summary>One-pole high-pass, run twice round the loop so it starts settled.</summary>
        public static void HighPass(float[] buf, float hz)
        {
            float a = (float)Math.Exp(-2.0 * Math.PI * hz / Synth.SampleRate);
            float prevIn = 0f, prevOut = 0f;
            for (int pass = 0; pass < 2; pass++)
                for (int i = 0; i < buf.Length; i++)
                {
                    float x = buf[i];
                    float y = a * (prevOut + x - prevIn);
                    prevIn = x;
                    prevOut = y;
                    if (pass == 1) buf[i] = y;
                }
        }

        // ---------- Reverb ----------

        static readonly int[] CombTuning = { 1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617 };
        static readonly int[] AllPassTuning = { 556, 441, 341, 225 };
        const int StereoSpread = 23;

        void Reverb(float[] input, float[] left, float[] right)
        {
            double scale = Synth.SampleRate / 44100.0;
            float feedback = roomSize * 0.28f + 0.7f;
            float damp = damping * 0.4f;
            var l = new Channel(scale, 0, feedback, damp);
            var r = new Channel(scale, StereoSpread, feedback, damp);
            float wet1 = wet * (width * 0.5f + 0.5f) * 3f;
            float wet2 = wet * ((1f - width) * 0.5f) * 3f;
            // Twice round: the second pass carries the first pass's tail across the seam.
            for (int pass = 0; pass < 2; pass++)
                for (int i = 0; i < length; i++)
                {
                    float x = input[i] * 0.015f;
                    float ol = l.Process(x), or = r.Process(x);
                    if (pass == 1)
                    {
                        left[i] += ol * wet1 + or * wet2;
                        right[i] += or * wet1 + ol * wet2;
                    }
                }
        }

        sealed class Channel
        {
            readonly float[][] comb;
            readonly int[] combIdx;
            readonly float[] combStore;
            readonly float[][] all;
            readonly int[] allIdx;
            readonly float feedback, damp;

            public Channel(double scale, int spread, float feedback, float damp)
            {
                this.feedback = feedback;
                this.damp = damp;
                comb = new float[CombTuning.Length][];
                combIdx = new int[CombTuning.Length];
                combStore = new float[CombTuning.Length];
                for (int i = 0; i < comb.Length; i++) comb[i] = new float[Math.Max(1, (int)((CombTuning[i] + spread) * scale))];
                all = new float[AllPassTuning.Length][];
                allIdx = new int[AllPassTuning.Length];
                for (int i = 0; i < all.Length; i++) all[i] = new float[Math.Max(1, (int)((AllPassTuning[i] + spread) * scale))];
            }

            public float Process(float x)
            {
                float output = 0f;
                for (int c = 0; c < comb.Length; c++)
                {
                    var b = comb[c];
                    int i = combIdx[c];
                    float y = b[i];
                    combStore[c] = y * (1f - damp) + combStore[c] * damp;
                    b[i] = x + combStore[c] * feedback;
                    combIdx[c] = (i + 1) % b.Length;
                    output += y;
                }
                for (int a = 0; a < all.Length; a++)
                {
                    var b = all[a];
                    int i = allIdx[a];
                    float buffered = b[i];
                    float y = -output + buffered;
                    b[i] = output + buffered * 0.5f;
                    allIdx[a] = (i + 1) % b.Length;
                    output = y;
                }
                return output;
            }
        }
    }

    /// <summary>A state-variable filter (topology-preserving: stable at any cutoff): low, band and high pass at once.</summary>
    public sealed class Svf
    {
        float ic1, ic2;
        double lastCutoff = -1, lastQ = -1, g, k, a1, a2, a3;
        public float low, band, high;

        public void Reset() { ic1 = ic2 = 0f; }

        public float Process(float x, double cutoff, double q)
        {
            if (cutoff != lastCutoff || q != lastQ)
            {
                lastCutoff = cutoff;
                lastQ = q;
                double fc = Math.Max(10.0, Math.Min(cutoff, Synth.SampleRate * 0.45));
                g = Math.Tan(Math.PI * fc / Synth.SampleRate);
                k = 1.0 / Math.Max(0.1, q);
                a1 = 1.0 / (1.0 + g * (g + k));
                a2 = g * a1;
                a3 = g * a2;
            }
            double v3 = x - ic2;
            double v1 = a1 * ic1 + a2 * v3;
            double v2 = ic2 + a2 * ic1 + a3 * v3;
            ic1 = (float)(2.0 * v1 - ic1);
            ic2 = (float)(2.0 * v2 - ic2);
            low = (float)v2;
            band = (float)v1;
            high = (float)(x - k * v1 - v2);
            return low;
        }
    }

    /// <summary>Noise sources: white, pink (Paul Kellet's filter) and brown, from a seeded generator.</summary>
    public sealed class NoiseSource
    {
        readonly Random rng;
        float b0, b1, b2, b3, b4, b5, b6, brown;

        public NoiseSource(int seed) { rng = new Random(seed); }

        public float White() { return (float)(rng.NextDouble() * 2.0 - 1.0); }

        public float Pink()
        {
            float w = White();
            b0 = 0.99886f * b0 + w * 0.0555179f;
            b1 = 0.99332f * b1 + w * 0.0750759f;
            b2 = 0.96900f * b2 + w * 0.1538520f;
            b3 = 0.86650f * b3 + w * 0.3104856f;
            b4 = 0.55000f * b4 + w * 0.5329522f;
            b5 = -0.7616f * b5 - w * 0.0168980f;
            float p = b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362f;
            b6 = w * 0.115926f;
            return p * 0.11f;
        }

        public float Brown()
        {
            brown = (brown + White() * 0.02f) * 0.998f;
            return brown * 3.5f;
        }

        public double Range(double a, double b) { return a + rng.NextDouble() * (b - a); }
        public int Next(int a, int b) { return rng.Next(a, b); }
        public double Value() { return rng.NextDouble(); }
    }

    /// <summary>A slow, smooth random wobble (0..1) for drifting textures: interpolated random points.</summary>
    public sealed class Drift
    {
        readonly Random rng;
        readonly double rate;
        double t, a, b;

        public Drift(int seed, double hz)
        {
            rng = new Random(seed);
            rate = hz;
            a = rng.NextDouble();
            b = rng.NextDouble();
        }

        public float Next()
        {
            t += rate / Synth.SampleRate;
            if (t >= 1.0) { t -= 1.0; a = b; b = rng.NextDouble(); }
            double s = t * t * (3 - 2 * t);
            return (float)(a + (b - a) * s);
        }
    }
}
