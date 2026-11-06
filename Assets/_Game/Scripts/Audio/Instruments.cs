using System;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// The band the music is played by, all synthesized: an electric piano, a warm pad and strings,
    /// plucked guitar and harp, a mandolin, a ukulele, marimba, steel pan, glockenspiel, accordion, flute,
    /// a soft square lead, three basses, and a kit (kick, snare, brush, clap, rim, hats, shaker, tambourine,
    /// congas, an anvil). Each writes one note into a <see cref="Track"/> at a time in seconds; notes wrap
    /// round the loop. Pure C#.
    /// </summary>
    public static class Instruments
    {
        const double TwoPi = Math.PI * 2.0;
        static int Sr { get { return Synth.SampleRate; } }

        static int Index(double seconds) { return (int)Math.Round(seconds * Synth.SampleRate); }

        /// <summary>Attack, exponential decay, and a short release at the note's end.</summary>
        static float Adr(double t, double dur, double attack, double decay, double release)
        {
            if (t < 0) return 0f;
            double a = t < attack ? t / attack : Math.Exp(-(t - attack) * decay);
            if (t > dur) a *= Math.Max(0, 1 - (t - dur) / release);
            return (float)a;
        }

        /// <summary>A 10 ms fade at the very end of a fixed-length sound, so cutting it off never clicks.</summary>
        static float Tail(int i, int n)
        {
            int left = n - i, fade = Sr / 100;
            return left >= fade ? 1f : left / (float)fade;
        }

        // ---------- Keys ----------

        /// <summary>Electric piano: a two-operator FM tone whose bark fades into a round sine, and a faint tine.</summary>
        public static void EPiano(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.25;
            int n = (int)((dur + rel) * Sr);
            double pc = 0, pm = 0, pt = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                pm += freq / Sr;
                pt += freq * 7.0 / Sr;
                double index = (0.25 + 1.4 * vel) * Math.Exp(-t * 5.0) + 0.12;
                pc += freq / Sr;
                double v = Math.Sin(TwoPi * pc + index * Math.Sin(TwoPi * pm));
                v += 0.12 * vel * Math.Sin(TwoPi * pt) * Math.Exp(-t * 28.0);
                tr.Add(start + i, (float)v * Adr(t, dur, 0.003, 1.1, rel) * vel);
            }
        }

        /// <summary>A chord on the electric piano, the notes rolled a few milliseconds apart.</summary>
        public static void EPianoChord(Track tr, double time, int[] midi, double dur, float vel, double roll = 0.008)
        {
            for (int i = 0; i < midi.Length; i++)
                EPiano(tr, time + i * roll, Synth.MidiToHz(midi[i]), dur, vel * (i == 0 ? 0.9f : 0.75f));
        }

        /// <summary>Warm pad: three detuned saws per note through a soft low-pass, slow to swell and fade.</summary>
        public static void Pad(Track tr, double time, int[] midi, double dur, float vel, double cutoff, int seed, double attack = 0.5)
        {
            int start = Index(time);
            double rel = 0.8;
            int n = (int)((dur + rel) * Sr);
            var rng = new Random(seed);
            foreach (int m in midi)
            {
                double f = Synth.MidiToHz(m);
                double[] det = { 1.0, 1.0 + 0.0045 + rng.NextDouble() * 0.002, 1.0 - 0.004 - rng.NextDouble() * 0.002 };
                double[] ph = { rng.NextDouble(), rng.NextDouble(), rng.NextDouble() };
                var flt = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double t = i / (double)Sr;
                    double s = 0;
                    for (int k = 0; k < 3; k++)
                    {
                        ph[k] += f * det[k] / Sr;
                        double p = ph[k] - Math.Floor(ph[k]);
                        s += 2.0 * p - 1.0;
                    }
                    float env = (float)(Math.Min(1.0, t / attack) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                    float y = flt.Process((float)(s / 3.0), cutoff * (0.8 + 0.2 * Math.Sin(t * 0.7 + m)), 0.7);
                    tr.Add(start + i, y * env * vel / midi.Length * 1.6f);
                }
            }
        }

        /// <summary>A string section: like the pad, with vibrato and a slower bow.</summary>
        public static void Strings(Track tr, double time, int[] midi, double dur, float vel, int seed)
        {
            int start = Index(time);
            double rel = 0.9;
            int n = (int)((dur + rel) * Sr);
            var rng = new Random(seed);
            foreach (int m in midi)
            {
                double f = Synth.MidiToHz(m);
                var flt = new Svf();
                double[] ph = { rng.NextDouble(), rng.NextDouble(), rng.NextDouble(), rng.NextDouble() };
                double[] det = { 1.0, 1.003, 0.997, 1.0065 };
                double vibRate = 5.0 + rng.NextDouble();
                for (int i = 0; i < n; i++)
                {
                    double t = i / (double)Sr;
                    double vib = 1.0 + 0.0035 * Math.Sin(TwoPi * vibRate * t) * Math.Min(1, t / 0.6);
                    double s = 0;
                    for (int k = 0; k < 4; k++)
                    {
                        ph[k] += f * det[k] * vib / Sr;
                        double p = ph[k] - Math.Floor(ph[k]);
                        s += 2.0 * p - 1.0;
                    }
                    float env = (float)(Math.Min(1.0, t / 0.35) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                    float y = flt.Process((float)(s * 0.25), 1900 + 500 * env, 0.6);
                    tr.Add(start + i, y * env * vel / midi.Length * 1.5f);
                }
            }
        }

        /// <summary>Accordion: two reeds a little apart (the musette's shimmer) and a bellows swell.</summary>
        public static void Accordion(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.06;
            int n = (int)((dur + rel) * Sr);
            double p1 = 0, p2 = 0, p3 = 0;
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += freq / Sr;
                p2 += freq * 1.006 / Sr;
                p3 += freq * 0.5 / Sr;
                double a = p1 - Math.Floor(p1), b = p2 - Math.Floor(p2), c = p3 - Math.Floor(p3);
                double s = (a < 0.35 ? 1 : -1) * 0.5 + (b < 0.4 ? 1 : -1) * 0.5 + (c < 0.5 ? 1 : -1) * 0.25;
                float env = (float)(Math.Min(1.0, t / 0.03) * (0.85 + 0.15 * Math.Min(1, t / 0.3)) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                tr.Add(start + i, flt.Process((float)s, 2600, 0.8) * env * vel * 0.55f);
            }
        }

        /// <summary>A soft square lead (the building site's whistle-while-you-work tune).</summary>
        public static void SquareLead(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.08;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double vib = 1.0 + 0.004 * Math.Sin(TwoPi * 5.5 * t) * Math.Min(1, t / 0.25);
                ph += freq * vib / Sr;
                double p = ph - Math.Floor(ph);
                double s = p < 0.42 ? 1 : -1;
                float env = Adr(t, dur, 0.008, 1.2, rel);
                tr.Add(start + i, flt.Process((float)s, 1400 + 1800 * Math.Exp(-t * 8), 0.9) * env * vel * 0.4f);
            }
        }

        /// <summary>Flute: a near-sine with a breath of noise around its pitch and a vibrato that blooms on long notes.</summary>
        public static void Flute(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            int start = Index(time);
            double rel = 0.12;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            var noise = new NoiseSource(seed);
            var breath = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double vib = 1.0 + 0.006 * Math.Sin(TwoPi * 5.2 * t) * Math.Max(0, Math.Min(1, (t - 0.18) / 0.3));
                ph += freq * vib / Sr;
                double tone = Math.Sin(TwoPi * ph) + 0.18 * Math.Sin(TwoPi * ph * 2) + 0.05 * Math.Sin(TwoPi * ph * 3);
                breath.Process(noise.White(), freq * 2, 6.0);
                float env = (float)(Math.Min(1.0, t / 0.05) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                float chiff = (float)Math.Exp(-t * 30) * 0.12f;
                tr.Add(start + i, (float)(tone * 0.8 + breath.band * (0.025 + chiff)) * env * vel * 0.5f);
            }
        }

        // ---------- Plucked ----------

        /// <summary>A plucked string (Karplus-Strong) with a pick position and brightness: guitar, harp, ukulele, mandolin.</summary>
        public static void Pluck(Track tr, double time, double freq, double dur, float vel, int seed, float brightness = 0.5f, float sustain = 0.996f)
        {
            int start = Index(time);
            int period = Math.Max(2, (int)Math.Round(Sr / freq));
            var line = new float[period];
            var rng = new Random(seed);
            float lp = 0f;
            for (int i = 0; i < period; i++)
            {
                float w = (float)(rng.NextDouble() * 2.0 - 1.0);
                lp += (w - lp) * (0.2f + brightness * 0.8f);
                line[i] = lp;
            }
            double rel = 0.05;
            int n = (int)((dur + rel) * Sr);
            int idx = 0;
            float prev = 0f;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                float v = line[idx];
                float next = line[(idx + 1) % period];
                line[idx] = (v * (0.5f + brightness * 0.15f) + next * (0.5f - brightness * 0.15f)) * sustain;
                prev += (v - prev) * 0.6f;
                float env = t > dur ? (float)Math.Max(0, 1 - (t - dur) / rel) : 1f;
                tr.Add(start + i, prev * env * vel);
                idx = (idx + 1) % period;
            }
        }

        /// <summary>A strummed chord: the strings caught one after another, down (low to high) or up.</summary>
        public static void Strum(Track tr, double time, int[] midi, double dur, float vel, int seed, bool down = true, double spread = 0.012, float brightness = 0.55f)
        {
            for (int i = 0; i < midi.Length; i++)
            {
                int k = down ? i : midi.Length - 1 - i;
                Pluck(tr, time + i * spread, Synth.MidiToHz(midi[k]), dur, vel * (0.7f + 0.3f * (i == 0 ? 1f : 0.8f)) / (float)Math.Sqrt(midi.Length), seed + i * 7, brightness);
            }
        }

        /// <summary>Mandolin tremolo: one note picked fast and evenly for as long as it lasts.</summary>
        public static void Tremolo(Track tr, double time, double freq, double dur, float vel, int seed, double rate = 13)
        {
            int count = Math.Max(1, (int)(dur * rate));
            for (int i = 0; i < count; i++)
                Pluck(tr, time + i / rate, freq, 1.0 / rate + 0.06, vel * (i % 2 == 0 ? 0.9f : 0.7f), seed + i, 0.7f, 0.993f);
        }

        // ---------- Mallets and bells ----------

        /// <summary>Marimba: a wooden bar's fundamental and its fourth-harmonic overtone, and a mallet's knock.</summary>
        public static void Marimba(Track tr, double time, double freq, float vel)
        {
            int start = Index(time);
            int n = (int)(1.1 * Sr);
            double p1 = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += freq / Sr;
                p2 += freq * 3.93 / Sr;
                double v = Math.Sin(TwoPi * p1) * Math.Exp(-t * 4.5) + 0.35 * Math.Sin(TwoPi * p2) * Math.Exp(-t * 22);
                v *= Math.Min(1, t / 0.0015);
                tr.Add(start + i, ((float)v * vel * 0.7f) * Tail(i, n));
            }
        }

        /// <summary>Steel pan: a bright FM ring that settles, with the slight pitch sag of a struck pan.</summary>
        public static void SteelPan(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            int n = (int)((Math.Max(dur, 0.25) + 0.6) * Sr);
            double pc = 0, pm = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double f = freq * (1.0 + 0.006 * Math.Exp(-t * 18));
                pc += f / Sr;
                pm += f * 2.0 / Sr;
                p2 += f * 2.98 / Sr;
                double index = 1.6 * Math.Exp(-t * 7) + 0.35;
                double v = Math.Sin(TwoPi * pc + index * Math.Sin(TwoPi * pm)) + 0.25 * Math.Sin(TwoPi * p2) * Math.Exp(-t * 6);
                float env = (float)(Math.Min(1, t / 0.002) * Math.Exp(-t * 2.6) * (t > dur + 0.3 ? Math.Max(0, 1 - (t - dur - 0.3) / 0.3) : 1));
                tr.Add(start + i, ((float)v * env * vel * 0.55f) * Tail(i, n));
            }
        }

        /// <summary>Glockenspiel / celesta: a bright, bell-like ping.</summary>
        public static void Glock(Track tr, double time, double freq, float vel, double decay = 3.5)
        {
            int start = Index(time);
            int n = (int)(1.4 * Sr);
            double[] ratio = { 1.0, 2.76, 5.4, 8.93 };
            double[] amp = { 1.0, 0.32, 0.12, 0.05 };
            double[] ph = new double[4];
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double v = 0;
                for (int k = 0; k < 4; k++)
                {
                    double f = freq * ratio[k];
                    if (f > Sr * 0.45) continue;
                    ph[k] += f / Sr;
                    v += amp[k] * Math.Sin(TwoPi * ph[k]) * Math.Exp(-t * decay * (1 + k * 1.2));
                }
                v *= Math.Min(1, t / 0.001);
                tr.Add(start + i, ((float)v * vel * 0.5f) * Tail(i, n));
            }
        }

        // ---------- Bass ----------

        /// <summary>A round, finger-played bass: triangle and sine, a soft pluck at the start.</summary>
        public static void RoundBass(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.05;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += freq / Sr;
                double p = ph - Math.Floor(ph);
                double tri = 4.0 * Math.Abs(p - 0.5) - 1.0;
                double v = Math.Sin(TwoPi * ph) * 0.8 + tri * 0.45;
                float y = flt.Process((float)v, 380 + 1400 * Math.Exp(-t * 18), 0.8);
                tr.Add(start + i, (y * Adr(t, dur, 0.004, 1.4, rel) * vel) * Tail(i, n));
            }
        }

        /// <summary>A synth bass: a saw through a resonant low-pass that snaps shut.</summary>
        public static void SynthBass(Track tr, double time, double freq, double dur, float vel, double bite = 1.0)
        {
            int start = Index(time);
            double rel = 0.04;
            int n = (int)((dur + rel) * Sr);
            double ph = 0, ph2 = 0;
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += freq / Sr;
                ph2 += freq * 0.5 / Sr;
                double p = ph - Math.Floor(ph);
                double v = (2.0 * p - 1.0) * 0.7 + Math.Sin(TwoPi * ph2) * 0.6;
                float y = flt.Process((float)v, 180 + 1500 * bite * Math.Exp(-t * 14), 2.2);
                tr.Add(start + i, (y * Adr(t, dur, 0.003, 1.8, rel) * vel * 0.85f) * Tail(i, n));
            }
        }

        /// <summary>A plucked upright-ish bass from a damped string.</summary>
        public static void PluckBass(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            Pluck(tr, time, freq, dur, vel * 1.4f, seed, 0.25f, 0.994f);
            int start = Index(time);
            int n = (int)(Math.Min(dur, 0.4) * Sr);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += freq / Sr;
                tr.Add(start + i, ((float)Math.Sin(TwoPi * ph) * (float)Math.Exp(-t * 6) * vel * 0.5f) * Tail(i, n));
            }
        }

        // ---------- Drums ----------

        public static void Kick(Track tr, double time, float vel, double tone = 1.0)
        {
            int start = Index(time);
            int n = (int)(0.32 * Sr);
            double ph = 0;
            var noise = new NoiseSource(start);
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double f = (48 + 110 * Math.Exp(-t * 32)) * tone;
                ph += f / Sr;
                double v = Math.Sin(TwoPi * ph) * Math.Exp(-t * 9) + noise.White() * 0.25 * Math.Exp(-t * 300);
                tr.Add(start + i, ((float)v * vel) * Tail(i, n));
            }
        }

        public static void Snare(Track tr, double time, float vel, int seed, double tone = 1.0)
        {
            int start = Index(time);
            int n = (int)(0.25 * Sr);
            double p1 = 0, p2 = 0;
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += 185 * tone / Sr;
                p2 += 330 * tone / Sr;
                double body = (Math.Sin(TwoPi * p1) * 0.6 + Math.Sin(TwoPi * p2) * 0.3) * Math.Exp(-t * 30);
                flt.Process(noise.White(), 4200, 0.7);
                double snares = (flt.high * 0.5 + flt.band * 0.8) * Math.Exp(-t * 17);
                tr.Add(start + i, ((float)(body + snares) * vel) * Tail(i, n));
            }
        }

        /// <summary>A brush on the snare: a soft slap, or a long swish.</summary>
        public static void Brush(Track tr, double time, float vel, int seed, double length = 0.12)
        {
            int start = Index(time);
            int n = (int)((length + 0.1) * Sr);
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                flt.Process(noise.White(), 3500, 0.6);
                double env = Math.Min(1, t / 0.006) * (t < length ? Math.Exp(-t * 6) : Math.Exp(-length * 6) * Math.Exp(-(t - length) * 40));
                tr.Add(start + i, ((flt.band + flt.high * 0.4f) * (float)env * vel * 0.8f) * Tail(i, n));
            }
        }

        public static void Clap(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.3 * Sr);
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                flt.Process(noise.White(), 1300, 1.4);
                double env = 0;
                for (int k = 0; k < 3; k++)
                {
                    double tk = t - k * 0.011;
                    if (tk >= 0 && tk < 0.011) env = Math.Max(env, Math.Exp(-tk * 260));
                }
                double tail = t > 0.022 ? Math.Exp(-(t - 0.022) * 18) : 0;
                tr.Add(start + i, (flt.band * (float)Math.Max(env, tail) * vel * 1.6f) * Tail(i, n));
            }
        }

        public static void Rim(Track tr, double time, float vel)
        {
            int start = Index(time);
            int n = (int)(0.06 * Sr);
            double p1 = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += 820.0 / Sr;
                p2 += 1690.0 / Sr;
                double v = (Math.Sin(TwoPi * p1) + 0.6 * Math.Sin(TwoPi * p2)) * Math.Exp(-t * 90);
                tr.Add(start + i, ((float)v * vel * 0.6f) * Tail(i, n));
            }
        }

        public static void Hat(Track tr, double time, float vel, int seed, bool open = false)
        {
            int start = Index(time);
            double decay = open ? 9 : 55;
            int n = (int)((open ? 0.45 : 0.08) * Sr);
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            double[] ph = new double[4];
            double[] fr = { 3150, 4460, 5310, 6890 };
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double metal = 0;
                for (int k = 0; k < 4; k++)
                {
                    ph[k] += fr[k] / Sr;
                    metal += (ph[k] - Math.Floor(ph[k])) < 0.5 ? 1 : -1;
                }
                flt.Process((float)(noise.White() * 0.7 + metal * 0.12), 7000, 0.7);
                tr.Add(start + i, (flt.high * (float)Math.Exp(-t * decay) * vel * 0.7f) * Tail(i, n));
            }
        }

        public static void Shaker(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.09 * Sr);
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                flt.Process(noise.White(), 5200, 1.2);
                double env = Math.Min(1, t / 0.018) * Math.Exp(-t * 32);
                tr.Add(start + i, (flt.band * (float)env * vel * 1.2f) * Tail(i, n));
            }
        }

        public static void Tambourine(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.22 * Sr);
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            double[] fr = { 4120, 5630, 7180 };
            double[] ph = new double[3];
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double jingle = 0;
                for (int k = 0; k < 3; k++)
                {
                    ph[k] += fr[k] * (1 + 0.01 * Math.Sin(t * 90 + k)) / Sr;
                    jingle += Math.Sin(TwoPi * ph[k]);
                }
                flt.Process(noise.White(), 6000, 1);
                double env = Math.Min(1, t / 0.003) * Math.Exp(-t * 16);
                tr.Add(start + i, ((float)((flt.high * 0.6 + jingle * 0.12) * env) * vel) * Tail(i, n));
            }
        }

        /// <summary>A hand drum: high (open slap) or low (tumba).</summary>
        public static void Conga(Track tr, double time, float vel, bool high)
        {
            int start = Index(time);
            int n = (int)(0.35 * Sr);
            double ph = 0;
            double f0 = high ? 330 : 210;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += f0 * (1 + 0.25 * Math.Exp(-t * 40)) / Sr;
                double v = Math.Sin(TwoPi * ph) * Math.Exp(-t * (high ? 14 : 10)) + Math.Sin(TwoPi * ph * 2.3) * 0.2 * Math.Exp(-t * 60);
                tr.Add(start + i, ((float)v * vel * 0.7f) * Tail(i, n));
            }
        }

        /// <summary>A hammer on a steel pipe: a short inharmonic ting.</summary>
        public static void Anvil(Track tr, double time, float vel, double pitch = 1.0)
        {
            int start = Index(time);
            int n = (int)(0.6 * Sr);
            double[] fr = { 1180, 2710, 3970, 5340 };
            double[] amp = { 1, 0.6, 0.4, 0.25 };
            double[] ph = new double[4];
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double v = 0;
                for (int k = 0; k < 4; k++)
                {
                    ph[k] += fr[k] * pitch / Sr;
                    v += amp[k] * Math.Sin(TwoPi * ph[k]) * Math.Exp(-t * (9 + k * 6));
                }
                tr.Add(start + i, ((float)v * vel * 0.35f) * Tail(i, n));
            }
        }

        /// <summary>Old vinyl: a soft hiss and a scatter of crackles, over the whole loop.</summary>
        public static void Vinyl(Track tr, float vel, int seed)
        {
            var noise = new NoiseSource(seed);
            var flt = new Svf();
            for (int i = 0; i < tr.Length; i++)
            {
                flt.Process(noise.White(), 3000, 0.6);
                float v = flt.band * 0.05f;
                if (noise.Value() < 0.0009) v += (float)(noise.White() * 0.8);
                tr.buf[i] += v * vel;
            }
        }
    }
}
