using System;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// The band the music is played by, all synthesized and all soft-edged, for chill lo-fi beats: a
    /// Rhodes-style electric piano with a slow tremolo, a warm pad and strings, a mellow jazz guitar, a
    /// soft harp, vibraphone, kalimba, a gentle marimba and steel pan, flute and melodica, a round sub bass,
    /// and a dusty kit (a boomy kick, a laid-back snare, a side-stick, closed hats, a shaker, congas) with
    /// vinyl crackle. Each writes one note into a <see cref="Track"/> at a time in seconds; notes wrap round
    /// the loop. Pure C#.
    /// </summary>
    public static class Instruments
    {
        const double TwoPi = Math.PI * 2.0;
        static int Sr { get { return Synth.SampleRate; } }

        static int Index(double seconds) { return (int)Math.Round(seconds * Synth.SampleRate); }

        /// <summary>A 10 ms fade at the very end of a fixed-length sound, so cutting it off never clicks.</summary>
        static float Tail(int i, int n)
        {
            int left = n - i, fade = Sr / 100;
            return left >= fade ? 1f : left / (float)fade;
        }

        /// <summary>Attack, exponential decay, and a short release at the note's end.</summary>
        static float Adr(double t, double dur, double attack, double decay, double release)
        {
            if (t < 0) return 0f;
            double a = t < attack ? t / attack : Math.Exp(-(t - attack) * decay);
            if (t > dur) a *= Math.Max(0, 1 - (t - dur) / release);
            return (float)a;
        }

        // ---------- Keys ----------

        /// <summary>
        /// A Rhodes-style electric piano: a sine with a little FM bark that fades in a moment into a round,
        /// bell-ish tone, a slow tremolo, a soft felt attack. Mellow at low velocity.
        /// </summary>
        public static void Rhodes(Track tr, double time, double freq, double dur, float vel, double tremolo = 4.2)
        {
            int start = Index(time);
            double rel = 0.35;
            int n = (int)((dur + rel) * Sr);
            double pc = 0, pm = 0;
            double trPhase = (freq * 0.013) % 1.0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                pc += freq / Sr;
                pm += freq / Sr;
                double index = (0.15 + 0.55 * vel) * Math.Exp(-t * 7.0) + 0.05;
                double v = Math.Sin(TwoPi * pc + index * Math.Sin(TwoPi * pm));
                v += 0.04 * Math.Sin(TwoPi * pc * 2) * Math.Exp(-t * 3);
                double trem = 1 - 0.18 * (0.5 + 0.5 * Math.Sin(TwoPi * (tremolo * t + trPhase)));
                float env = Adr(t, dur, 0.006, 0.9, rel);
                tr.Add(start + i, (float)(v * trem) * env * vel);
            }
        }

        /// <summary>A chord on the Rhodes, rolled a few milliseconds apart, the top note a touch louder.</summary>
        public static void RhodesChord(Track tr, double time, int[] midi, double dur, float vel, double roll = 0.012)
        {
            for (int i = 0; i < midi.Length; i++)
                Rhodes(tr, time + i * roll, Synth.MidiToHz(midi[i]), dur, vel * (i == midi.Length - 1 ? 0.8f : 0.62f));
        }

        /// <summary>Warm pad: three gently detuned saws per note through a low low-pass, slow to swell and fade.</summary>
        public static void Pad(Track tr, double time, int[] midi, double dur, float vel, double cutoff, int seed, double attack = 0.8)
        {
            int start = Index(time);
            double rel = 1.0;
            int n = (int)((dur + rel) * Sr);
            var rng = new Random(seed);
            foreach (int m in midi)
            {
                double f = Synth.MidiToHz(m);
                double[] det = { 1.0, 1.0 + 0.003 + rng.NextDouble() * 0.002, 1.0 - 0.003 - rng.NextDouble() * 0.002 };
                double[] ph = { rng.NextDouble(), rng.NextDouble(), rng.NextDouble() };
                var flt = new Svf();
                var flt2 = new Svf();
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
                    float y = flt2.Process(flt.Process((float)(s / 3.0), cutoff, 0.6), cutoff * 1.2, 0.6);
                    tr.Add(start + i, y * env * vel / midi.Length * 1.8f);
                }
            }
        }

        /// <summary>Soft strings: like the pad, with vibrato and a slow bow.</summary>
        public static void Strings(Track tr, double time, int[] midi, double dur, float vel, int seed)
        {
            int start = Index(time);
            double rel = 1.0;
            int n = (int)((dur + rel) * Sr);
            var rng = new Random(seed);
            foreach (int m in midi)
            {
                double f = Synth.MidiToHz(m);
                var flt = new Svf();
                var flt2 = new Svf();
                double[] ph = { rng.NextDouble(), rng.NextDouble(), rng.NextDouble() };
                double[] det = { 1.0, 1.0025, 0.9975 };
                double vibRate = 4.8 + rng.NextDouble();
                for (int i = 0; i < n; i++)
                {
                    double t = i / (double)Sr;
                    double vib = 1.0 + 0.003 * Math.Sin(TwoPi * vibRate * t) * Math.Min(1, t / 0.8);
                    double s = 0;
                    for (int k = 0; k < 3; k++)
                    {
                        ph[k] += f * det[k] * vib / Sr;
                        double p = ph[k] - Math.Floor(ph[k]);
                        s += 2.0 * p - 1.0;
                    }
                    float env = (float)(Math.Min(1.0, t / 0.6) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                    float y = flt2.Process(flt.Process((float)(s / 3.0), 1200, 0.6), 1500, 0.6);
                    tr.Add(start + i, y * env * vel / midi.Length * 1.8f);
                }
            }
        }

        // ---------- Leads ----------

        /// <summary>Vibraphone: a pure bar tone with its soft fourth-harmonic overtone and the motor's slow tremolo.</summary>
        public static void Vibes(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            double len = Math.Max(dur, 0.4) + 0.9;
            int n = (int)(len * Sr);
            double p1 = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += freq / Sr;
                p2 += freq * 4.0 / Sr;
                double v = Math.Sin(TwoPi * p1) + 0.12 * Math.Sin(TwoPi * p2) * Math.Exp(-t * 9);
                double trem = 1 - 0.22 * (0.5 + 0.5 * Math.Sin(TwoPi * 5.2 * t));
                double env = Math.Min(1, t / 0.004) * Math.Exp(-t * 1.6) * (t > dur + 0.25 ? Math.Max(0, 1 - (t - dur - 0.25) / 0.5) : 1);
                tr.Add(start + i, (float)(v * trem * env) * vel * 0.6f * Tail(i, n));
            }
        }

        /// <summary>Kalimba: a thumb-plucked tine, round and quick to fade, with a faint metallic overtone.</summary>
        public static void Kalimba(Track tr, double time, double freq, float vel)
        {
            int start = Index(time);
            int n = (int)(1.2 * Sr);
            double p1 = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += freq / Sr;
                p2 += freq * 5.9 / Sr;
                double v = Math.Sin(TwoPi * p1) * Math.Exp(-t * 3.2) + 0.1 * Math.Sin(TwoPi * p2) * Math.Exp(-t * 30);
                v *= Math.Min(1, t / 0.003);
                tr.Add(start + i, (float)v * vel * 0.6f * Tail(i, n));
            }
        }

        /// <summary>Flute: a near-sine with a faint breath and a vibrato that blooms on long notes.</summary>
        public static void Flute(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            int start = Index(time);
            double rel = 0.15;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            var noise = new NoiseSource(seed);
            var breath = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double vib = 1.0 + 0.005 * Math.Sin(TwoPi * 5.0 * t) * Math.Max(0, Math.Min(1, (t - 0.2) / 0.3));
                ph += freq * vib / Sr;
                double tone = Math.Sin(TwoPi * ph) + 0.12 * Math.Sin(TwoPi * ph * 2);
                breath.Process(noise.White(), freq * 2, 6.0);
                float env = (float)(Math.Min(1.0, t / 0.07) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                tr.Add(start + i, (float)(tone * 0.8 + breath.band * 0.02) * env * vel * 0.5f);
            }
        }

        /// <summary>Melodica: a soft reed, hollow and breathy, swelling in.</summary>
        public static void Melodica(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            int start = Index(time);
            double rel = 0.1;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            var flt = new Svf();
            var noise = new NoiseSource(seed);
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += freq * (1 + 0.003 * Math.Sin(TwoPi * 4.5 * t)) / Sr;
                double p = ph - Math.Floor(ph);
                double tri = 4.0 * Math.Abs(p - 0.5) - 1.0;
                double v = Math.Sin(TwoPi * ph) * 0.6 + tri * 0.5 + Math.Sin(TwoPi * ph * 3) * 0.08 + noise.White() * 0.015;
                float env = (float)(Math.Min(1.0, t / 0.05) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1.0));
                tr.Add(start + i, flt.Process((float)v, 1800, 0.7) * env * vel * 0.5f);
            }
        }

        // ---------- Plucked ----------

        /// <summary>A plucked string (Karplus-Strong) with a brightness: soft guitar, harp, nylon.</summary>
        public static void Pluck(Track tr, double time, double freq, double dur, float vel, int seed, float brightness = 0.3f, float sustain = 0.996f)
        {
            int start = Index(time);
            int period = Math.Max(2, (int)Math.Round(Sr / freq));
            var line = new float[period];
            var rng = new Random(seed);
            float lp = 0f;
            // A soft pick: the excitation is smoothed, so the attack is round rather than a burst of noise.
            for (int pass = 0; pass < 2; pass++)
                for (int i = 0; i < period; i++)
                {
                    float w = pass == 0 ? (float)(rng.NextDouble() * 2.0 - 1.0) : line[i];
                    lp += (w - lp) * (0.15f + brightness * 0.6f);
                    line[i] = lp;
                }
            double rel = 0.06;
            int n = (int)((dur + rel) * Sr);
            int idx = 0;
            float prev = 0f;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                float v = line[idx];
                float next = line[(idx + 1) % period];
                line[idx] = (v + next) * 0.5f * sustain;
                prev += (v - prev) * (0.3f + brightness * 0.4f);
                float env = (float)Math.Min(1, t / 0.002) * (t > dur ? (float)Math.Max(0, 1 - (t - dur) / rel) : 1f);
                tr.Add(start + i, prev * env * vel);
                idx = (idx + 1) % period;
            }
        }

        /// <summary>A chord picked on a mellow jazz guitar, the strings a few milliseconds apart.</summary>
        public static void Strum(Track tr, double time, int[] midi, double dur, float vel, int seed, double spread = 0.016, float brightness = 0.25f)
        {
            for (int i = 0; i < midi.Length; i++)
                Pluck(tr, time + i * spread, Synth.MidiToHz(midi[i]), dur, vel * 0.8f / (float)Math.Sqrt(midi.Length), seed + i * 7, brightness);
        }

        // ---------- Mallets ----------

        /// <summary>Marimba, played softly with yarn mallets: the bar's fundamental and a faint overtone.</summary>
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
                double v = Math.Sin(TwoPi * p1) * Math.Exp(-t * 4) + 0.12 * Math.Sin(TwoPi * p2) * Math.Exp(-t * 25);
                v *= Math.Min(1, t / 0.004);
                tr.Add(start + i, (float)v * vel * 0.6f * Tail(i, n));
            }
        }

        /// <summary>A steel pan played gently: a round FM ring with only a little shimmer.</summary>
        public static void SteelPan(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            int n = (int)((Math.Max(dur, 0.25) + 0.7) * Sr);
            double pc = 0, pm = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                pc += freq / Sr;
                pm += freq * 2.0 / Sr;
                double index = 0.7 * Math.Exp(-t * 9) + 0.15;
                double v = Math.Sin(TwoPi * pc + index * Math.Sin(TwoPi * pm));
                double env = Math.Min(1, t / 0.004) * Math.Exp(-t * 2.4);
                tr.Add(start + i, (float)(v * env) * vel * 0.55f * Tail(i, n));
            }
        }

        // ---------- Bass ----------

        /// <summary>A round sub bass: a sine with a whisper of second harmonic, soft at the start and the end.</summary>
        public static void SubBass(Track tr, double time, double freq, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.08;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += freq / Sr;
                double v = Math.Sin(TwoPi * ph) + 0.18 * Math.Sin(TwoPi * ph * 2) * Math.Exp(-t * 4) + 0.06 * Math.Sin(TwoPi * ph * 3) * Math.Exp(-t * 8);
                float env = Adr(t, dur, 0.012, 0.5, rel);
                tr.Add(start + i, (float)v * env * vel);
            }
        }

        /// <summary>A plucked upright bass: a thumb on a fat string, the note blooming then settling.</summary>
        public static void UprightBass(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            Pluck(tr, time, freq, dur, vel * 0.9f, seed, 0.12f, 0.995f);
            SubBass(tr, time, freq, dur * 0.9, vel * 0.7f);
        }

        // ---------- Drums ----------

        /// <summary>A dusty boom-bap kick: a round thump that drops in pitch, its click softened.</summary>
        public static void Kick(Track tr, double time, float vel)
        {
            int start = Index(time);
            int n = (int)(0.42 * Sr);
            double ph = 0;
            var click = new Svf();
            var noise = new NoiseSource(start);
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double f = 52 + 95 * Math.Exp(-t * 34);
                ph += f / Sr;
                click.Process(noise.White(), 1200, 0.7);
                double v = Math.Sin(TwoPi * ph) * Math.Exp(-t * 9) * Math.Min(1, t / 0.002) + click.low * 0.45 * Math.Exp(-t * 160);
                tr.Add(start + i, (float)v * vel * Tail(i, n));
            }
        }

        /// <summary>A laid-back snare: a warm body and dull, short wires, like one sampled off an old record.</summary>
        public static void Snare(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.3 * Sr);
            double p1 = 0;
            var noise = new NoiseSource(seed);
            var wires = new Svf();
            var dull = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += (190 + 30 * Math.Exp(-t * 40)) / Sr;
                double body = Math.Sin(TwoPi * p1) * Math.Exp(-t * 22) * 0.55;
                wires.Process(noise.White(), 1900, 0.8);
                double w = dull.Process(wires.band + wires.high * 0.5f, 5500, 0.6) * Math.Exp(-t * 15);
                tr.Add(start + i, (float)((body + w * 1.2) * Math.Min(1, t / 0.0015)) * vel * Tail(i, n));
            }
        }

        /// <summary>A side-stick on the rim: a short woody knock.</summary>
        public static void Rim(Track tr, double time, float vel)
        {
            int start = Index(time);
            int n = (int)(0.08 * Sr);
            double p1 = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += 560.0 / Sr;
                p2 += 1250.0 / Sr;
                double v = (Math.Sin(TwoPi * p1) + 0.35 * Math.Sin(TwoPi * p2)) * Math.Exp(-t * 70) * Math.Min(1, t / 0.001);
                tr.Add(start + i, (float)v * vel * 0.5f * Tail(i, n));
            }
        }

        /// <summary>A closed hi-hat, dark and short (the tape takes its fizz off).</summary>
        public static void Hat(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.07 * Sr);
            var noise = new NoiseSource(seed);
            var hp = new Svf();
            var lp = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                hp.Process(noise.White(), 5000, 0.7);
                float v = lp.Process(hp.high, 8000, 0.7);
                tr.Add(start + i, v * (float)(Math.Exp(-t * 60) * Math.Min(1, t / 0.001)) * vel * 0.6f * Tail(i, n));
            }
        }

        /// <summary>An open hi-hat: a longer, softer wash, the lift on the off-beat.</summary>
        public static void OpenHat(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.32 * Sr);
            var noise = new NoiseSource(seed + 77);
            var hp = new Svf();
            var lp = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                hp.Process(noise.White(), 5200, 0.7);
                float v = lp.Process(hp.high, 8500, 0.7);
                tr.Add(start + i, v * (float)(Math.Exp(-t * 9) * Math.Min(1, t / 0.002)) * vel * 0.5f * Tail(i, n));
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
                flt.Process(noise.White(), 4200, 1.0);
                double env = Math.Min(1, t / 0.02) * Math.Exp(-t * 34);
                tr.Add(start + i, flt.band * (float)env * vel * Tail(i, n));
            }
        }

        /// <summary>A hand drum, muffled: high (open tone) or low.</summary>
        public static void Conga(Track tr, double time, float vel, bool high)
        {
            int start = Index(time);
            int n = (int)(0.35 * Sr);
            double ph = 0;
            double f0 = high ? 300 : 200;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                ph += f0 * (1 + 0.15 * Math.Exp(-t * 40)) / Sr;
                double v = Math.Sin(TwoPi * ph) * Math.Exp(-t * (high ? 13 : 9)) * Math.Min(1, t / 0.002);
                tr.Add(start + i, (float)v * vel * 0.6f * Tail(i, n));
            }
        }

        /// <summary>Old vinyl over the whole loop: a soft, dark hiss and a scatter of gentle crackles.</summary>
        public static void Vinyl(Track tr, float vel, int seed)
        {
            var noise = new NoiseSource(seed);
            var hiss = new Svf();
            var pop = new Svf();
            for (int i = 0; i < tr.Length; i++)
            {
                hiss.Process(noise.White(), 2500, 0.5);
                float v = hiss.band * 0.04f;
                float crackle = noise.Value() < 0.0012 ? noise.White() * 0.7f : 0f;
                v += pop.Process(crackle, 3000, 0.7) * 1.5f;
                tr.buf[i] += v * vel;
            }
        }

        // ---------- West Coast ----------

        /// <summary>
        /// A clean electric guitar: a plucked string with a bright pick, a little body resonance and a gentle
        /// chorus (a second string a few cents off), the sound of a sunny Californian pop or surf guitar
        /// through a clean amp. Muted (palm on the strings) it is short and dark.
        /// </summary>
        public static void CleanGuitar(Track tr, double time, double freq, double dur, float vel, int seed, bool muted = false)
        {
            float bright = muted ? 0.25f : 0.62f;
            double d = muted ? Math.Min(dur, 0.16) : dur;
            Pluck(tr, time, freq, d, vel * 0.75f, seed, bright, muted ? 0.985f : 0.9975f);
            if (!muted) Pluck(tr, time + 0.004, freq * 1.0035, d, vel * 0.35f, seed + 101, bright * 0.8f, 0.997f);
        }

        /// <summary>A strummed chord on the clean guitar, down (low to high) or up, the strings 7 to 14 ms apart.</summary>
        public static void Jangle(Track tr, double time, int[] midi, double dur, float vel, int seed, bool down, bool muted = false)
        {
            double spread = muted ? 0.006 : down ? 0.012 : 0.008;
            for (int i = 0; i < midi.Length; i++)
            {
                int k = down ? i : midi.Length - 1 - i;
                float v = vel / (float)Math.Sqrt(midi.Length) * (down ? 1f : 0.75f);
                CleanGuitar(tr, time + i * spread, Synth.MidiToHz(midi[k]), dur, v, seed + i * 13, muted);
            }
        }

        /// <summary>
        /// The surf guitar's twang: a bright plucked note through a lot of spring reverb (the track's send), with
        /// a slow whammy-bar vibrato; long notes are tremolo-picked (picked fast and evenly, the surf sound).
        /// </summary>
        public static void SurfLead(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            if (dur > 0.35)
            {
                double rate = 14;
                int count = (int)(dur * rate);
                for (int i = 0; i < count; i++)
                {
                    double wobble = 1 + 0.004 * Math.Sin(i * 0.9);
                    Pluck(tr, time + i / rate, freq * wobble, 1.0 / rate + 0.05, vel * (i % 2 == 0 ? 0.62f : 0.5f), seed + i, 0.55f, 0.995f);
                }
                return;
            }
            Pluck(tr, time, freq, dur + 0.15, vel * 0.8f, seed, 0.6f, 0.997f);
            Pluck(tr, time + 0.003, freq * 1.004, dur + 0.1, vel * 0.3f, seed + 7, 0.5f, 0.996f);
        }

        /// <summary>A combo organ: soft drawbars (the fundamental, octave and twelfth) and a rotating speaker's slow swirl.</summary>
        public static void Organ(Track tr, double time, int[] midi, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.08;
            int n = (int)((dur + rel) * Sr);
            foreach (int m in midi)
            {
                double f = Synth.MidiToHz(m);
                double ph = 0;
                for (int i = 0; i < n; i++)
                {
                    double t = i / (double)Sr;
                    double vib = 1 + 0.002 * Math.Sin(TwoPi * 5.8 * t);
                    ph += f * vib / Sr;
                    double v = Math.Sin(TwoPi * ph) + 0.5 * Math.Sin(TwoPi * ph * 2) + 0.25 * Math.Sin(TwoPi * ph * 3);
                    double swirl = 1 - 0.15 * (0.5 + 0.5 * Math.Sin(TwoPi * 6.2 * t + m));
                    float env = (float)(Math.Min(1, t / 0.01) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1));
                    tr.Add(start + i, (float)(v * swirl) * env * vel * 0.3f / midi.Length);
                }
            }
        }

        /// <summary>The West Coast synth whistle: a pure, high sine that glides into each note, with a lazy vibrato.</summary>
        public static void Whistle(Track tr, double time, double freq, double fromFreq, double dur, float vel)
        {
            int start = Index(time);
            double rel = 0.12;
            int n = (int)((dur + rel) * Sr);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                double glide = Math.Min(1, t / 0.06);
                double f = fromFreq + (freq - fromFreq) * glide;
                f *= 1 + 0.008 * Math.Sin(TwoPi * 5.5 * t) * Math.Min(1, t / 0.25);
                ph += f / Sr;
                float env = (float)(Math.Min(1, t / 0.03) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1));
                tr.Add(start + i, (float)Math.Sin(TwoPi * ph) * env * vel * 0.45f);
            }
        }

        /// <summary>Backing "ooh"s: a soft choir, a buzz through the formants of an "oo" with a slow swell, the beach-pop harmony.</summary>
        public static void Oohs(Track tr, double time, int[] midi, double dur, float vel, int seed)
        {
            int start = Index(time);
            double rel = 0.5;
            int n = (int)((dur + rel) * Sr);
            var rng = new Random(seed);
            foreach (int m in midi)
            {
                double f = Synth.MidiToHz(m);
                var f1 = new Svf();
                var f2 = new Svf();
                double[] ph = { rng.NextDouble(), rng.NextDouble() };
                double[] det = { 1.0, 1.004 };
                double vibRate = 4.6 + rng.NextDouble();
                for (int i = 0; i < n; i++)
                {
                    double t = i / (double)Sr;
                    double vib = 1 + 0.004 * Math.Sin(TwoPi * vibRate * t);
                    double src = 0;
                    for (int k = 0; k < 2; k++)
                    {
                        ph[k] += f * det[k] * vib / Sr;
                        double p = ph[k] - Math.Floor(ph[k]);
                        src += 2 * p - 1;
                    }
                    f1.Process((float)src, 330, 4);
                    f2.Process((float)src, 800, 5);
                    float env = (float)(Math.Min(1, t / 0.35) * (t > dur ? Math.Max(0, 1 - (t - dur) / rel) : 1));
                    tr.Add(start + i, (f1.band + f2.band * 0.4f) * env * vel * 0.25f / midi.Length);
                }
            }
        }

        /// <summary>A glockenspiel played softly, for a sparkle on the top of a sunny tune.</summary>
        public static void Glock(Track tr, double time, double freq, float vel)
        {
            int start = Index(time);
            int n = (int)(1.2 * Sr);
            double p1 = 0, p2 = 0;
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                p1 += freq / Sr;
                p2 += freq * 2.76 / Sr;
                double v = Math.Sin(TwoPi * p1) * Math.Exp(-t * 3.5) + 0.15 * Math.Sin(TwoPi * p2) * Math.Exp(-t * 12);
                tr.Add(start + i, (float)(v * Math.Min(1, t / 0.002)) * vel * 0.4f * Tail(i, n));
            }
        }

        /// <summary>Hand claps, a few people at once, warm rather than snappy.</summary>
        public static void Clap(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.25 * Sr);
            var noise = new NoiseSource(seed);
            var bp = new Svf();
            var lp = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                bp.Process(noise.White(), 1400, 1.2);
                double env = 0;
                for (int k = 0; k < 3; k++)
                {
                    double tk = t - k * 0.009;
                    if (tk >= 0) env = Math.Max(env, Math.Exp(-tk * (k == 2 ? 22 : 200)));
                }
                tr.Add(start + i, lp.Process(bp.band, 4500, 0.7) * (float)env * vel * 1.3f * Tail(i, n));
            }
        }

        /// <summary>A tambourine shaken on the off-beat: its jingles, rounded off.</summary>
        public static void Tambourine(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(0.18 * Sr);
            var noise = new NoiseSource(seed);
            var bp = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                bp.Process(noise.White(), 5800, 1.5);
                double env = Math.Min(1, t / 0.004) * Math.Exp(-t * 20);
                tr.Add(start + i, bp.band * (float)env * vel * 0.8f * Tail(i, n));
            }
        }

        /// <summary>A soft crash cymbal to open a section: a long, dark wash.</summary>
        public static void Crash(Track tr, double time, float vel, int seed)
        {
            int start = Index(time);
            int n = (int)(1.8 * Sr);
            var noise = new NoiseSource(seed);
            var hp = new Svf();
            var lp = new Svf();
            for (int i = 0; i < n; i++)
            {
                double t = i / (double)Sr;
                hp.Process(noise.White(), 3500, 0.7);
                float v = lp.Process(hp.high, 7500, 0.7);
                tr.Add(start + i, v * (float)(Math.Exp(-t * 2.2) * Math.Min(1, t / 0.003)) * vel * 0.4f * Tail(i, n));
            }
        }

        /// <summary>A picked electric bass: a round string with a little pick at the front.</summary>
        public static void PickBass(Track tr, double time, double freq, double dur, float vel, int seed)
        {
            Pluck(tr, time, freq, dur, vel * 0.8f, seed, 0.3f, 0.994f);
            SubBass(tr, time, freq, dur * 0.95, vel * 0.75f);
        }
    }
}
