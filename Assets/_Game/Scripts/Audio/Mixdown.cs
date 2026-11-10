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
        float[] data;
        readonly int length;

        /// <summary>The samples, made when the part is first written: one the arrangement never plays costs nothing.</summary>
        public float[] buf { get { return data ?? (data = Scratch.Rent(length)); } }
        /// <summary>The samples if anything was written, else null (an empty part adds nothing to the mix).</summary>
        internal float[] Written { get { return data; } }
        /// <summary>-1 (left) to 1 (right).</summary>
        public float pan;
        /// <summary>How much goes to the shared reverb (0 dry, 1 very wet).</summary>
        public float send;
        public float gain = 1f;
        /// <summary>How far it dips under each kick drum (0 none, 1 to silence): the breathing "pump" of lo-fi beats.</summary>
        public float duck;

        public Track(int length, float pan, float send, float gain)
        {
            this.length = length;
            this.pan = pan;
            this.send = send;
            this.gain = gain;
        }

        public int Length { get { return length; } }

        /// <summary>Add a sample at any index: wraps round the loop.</summary>
        public void Add(int index, float v)
        {
            int n = length;
            index %= n;
            if (index < 0) index += n;
            buf[index] += v;
        }
    }

    /// <summary>
    /// Work buffers reused within one synthesis on this thread: a place's bed (AmbienceGenerator) or its music loop
    /// (MusicGenerator), between <see cref="Begin"/> and <see cref="End"/>. A bed's voices and layers each needed
    /// whole-loop buffers of the same length, thrown away one after another: 40 to 118 MB of garbage a place, made
    /// every time a place is entered (six times a Holiday Run lap). Outside a synthesis Rent just allocates and Return
    /// drops. Only buffers thrown away inside are returned, never one that is kept or played, and each comes back
    /// cleared, so the sound is exactly the same, sample for sample.
    /// </summary>
    static class Scratch
    {
        [ThreadStatic] static List<float[]> free;
        /// <summary>At most this many are kept for reuse (a bed's busiest step, a crowd voice, needs five at once).</summary>
        const int MaxKept = 8;

        public static void Begin() { if (free == null) free = new List<float[]>(MaxKept + 1); }
        public static void End() { free = null; }

        /// <summary>A buffer of exactly <paramref name="length"/> floats, all zero.</summary>
        public static float[] Rent(int length)
        {
            var f = free;
            if (f != null)
                for (int i = f.Count - 1; i >= 0; i--)
                {
                    var b = f[i];
                    if (b.Length != length) continue;
                    f.RemoveAt(i);
                    Array.Clear(b, 0, b.Length);
                    return b;
                }
            return new float[length];
        }

        /// <summary>Hand back a buffer nothing will read or write again.</summary>
        public static void Return(float[] b)
        {
            var f = free;
            if (f == null || b == null) return;
            f.Add(b);
            if (f.Count > MaxKept) f.RemoveAt(0);
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
        /// <summary>The master's warmth: a gentle two-pole low-pass at this frequency (0 = off).</summary>
        public double tone;
        /// <summary>Tape saturation (0 = clean): rounds off peaks and thickens the low end.</summary>
        public float drive;
        /// <summary>Tape wow: a slow wobble of pitch, in cents, cycling <see cref="wowCycles"/> times round the loop.</summary>
        public float wowCents;
        public int wowCycles = 8;
        readonly float[] duckEnv;

        /// <summary>Note a kick drum at a time (seconds): tracks with <see cref="Track.duck"/> dip under it.</summary>
        public void Duck(double seconds, float depth = 1f, double recover = 0.16)
        {
            int start = (int)(seconds * Synth.SampleRate);
            int n = (int)(recover * 3 * Synth.SampleRate);
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Synth.SampleRate;
                float a = (float)(depth * Math.Min(1.0, t / 0.008) * Math.Exp(-t / recover));
                if (t < 0.008) a = (float)(depth * (t / 0.008));
                int j = ((start + i) % length + length) % length;
                duckEnv[j] = Math.Max(duckEnv[j], a);
            }
        }

        public Mixdown(int length)
        {
            this.length = length;
            duckEnv = Scratch.Rent(length);
        }

        public int Length { get { return length; } }

        public Track Add(float pan, float send, float gain = 1f)
        {
            var t = new Track(length, pan, send, gain);
            tracks.Add(t);
            return t;
        }

        /// <summary>
        /// Mix every track down to interleaved stereo with the loudness at <paramref name="targetRms"/>
        /// (or, when that is 0, with the loudest peak at the ceiling: for one-shots). A mixdown renders once: its
        /// tracks' buffers are handed back for reuse as they are mixed in.
        /// </summary>
        public float[] Render(float targetRms, float ceiling = 0.98f)
        {
            if (rendered) throw new InvalidOperationException("A Mixdown renders once.");
            rendered = true;
            var left = Scratch.Rent(length);
            var right = Scratch.Rent(length);
            var send = Scratch.Rent(length);
            foreach (var t in tracks)
            {
                double a = (Math.Max(-1f, Math.Min(1f, t.pan)) + 1.0) * Math.PI * 0.25;
                float gl = (float)Math.Cos(a) * t.gain * 1.414f, gr = (float)Math.Sin(a) * t.gain * 1.414f;
                float gs = t.send * t.gain;
                var b = t.Written;
                if (b == null) continue;
                for (int i = 0; i < length; i++)
                {
                    float v = b[i];
                    if (v == 0f) continue;
                    if (t.duck > 0f) v *= 1f - t.duck * duckEnv[i];
                    left[i] += v * gl;
                    right[i] += v * gr;
                    send[i] += v * gs;
                }
            }
            foreach (var t in tracks) Scratch.Return(t.Written);
            Scratch.Return(duckEnv);

            if (wet > 0f) Reverb(send, left, right);
            Scratch.Return(send);

            HighPass(left, 28f);
            HighPass(right, 28f);
            if (tone > 0)
            {
                LowPass(left, tone);
                LowPass(right, tone);
            }
            if (drive > 0f)
            {
                Saturate(left, drive);
                Saturate(right, drive);
            }
            if (wowCents > 0f)
            {
                var wowLeft = Wow(left, wowCents, wowCycles, 0.0);
                Scratch.Return(left);
                left = wowLeft;
                var wowRight = Wow(right, wowCents, wowCycles, 0.25);
                Scratch.Return(right);
                right = wowRight;
            }
            var mixed = Finish(left, right, targetRms, ceiling);
            Scratch.Return(left);
            Scratch.Return(right);
            return mixed;
        }

        bool rendered;

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

        /// <summary>A gentle two-pole low-pass (Butterworth), run twice round the loop so it starts settled.</summary>
        public static void LowPass(float[] buf, double hz)
        {
            var f = new Svf();
            for (int pass = 0; pass < 2; pass++)
                for (int i = 0; i < buf.Length; i++)
                {
                    float y = f.Process(buf[i], hz, 0.707);
                    if (pass == 1) buf[i] = y;
                }
        }

        /// <summary>Tape-like saturation: a soft, slightly uneven curve, level-matched so it warms without getting louder.</summary>
        static void Saturate(float[] buf, float drive)
        {
            double peak = 1e-6;
            for (int i = 0; i < buf.Length; i++) peak = Math.Max(peak, Math.Abs(buf[i]));
            double k = (1.0 + drive * 3.0) / peak;
            double norm = 1.0 / Math.Tanh(k * peak);
            for (int i = 0; i < buf.Length; i++)
            {
                double x = buf[i] * k;
                buf[i] = (float)(Math.Tanh(x + 0.08 * drive * x * x / (1 + x * x)) * norm * peak);
            }
        }

        /// <summary>Tape wow: read the loop back with a slowly wavering delay (a whole number of cycles, so it stays seamless).</summary>
        static float[] Wow(float[] buf, float cents, int cycles, double phase)
        {
            int n = buf.Length;
            var outBuf = Scratch.Rent(n);
            // A sine delay of depth D samples at f Hz bends pitch by 2*pi*f*D/sr; solve D for the cents asked.
            double hz = cycles * Synth.SampleRate / (double)n;
            double ratio = Math.Pow(2, cents / 1200.0) - 1;
            double depth = ratio * Synth.SampleRate / (2 * Math.PI * hz);
            for (int i = 0; i < n; i++)
            {
                double d = depth * (1 + Math.Sin(2 * Math.PI * (cycles * i / (double)n + phase))) + 1;
                double pos = i - d;
                int a = (int)Math.Floor(pos);
                double frac = pos - a;
                int ia = ((a % n) + n) % n, ib = (ia + 1) % n;
                outBuf[i] = (float)(buf[ia] * (1 - frac) + buf[ib] * frac);
            }
            return outBuf;
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
