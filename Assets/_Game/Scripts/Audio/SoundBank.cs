using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    public enum Sfx
    {
        Kick, Touch, Perfect, Juggle, Trap, Jump, Land, Bounce, Coin, Sticker, Checkpoint, Bell, Goal, Lose,
        Splash, Woof, Squawk, Oof, Boing, Switch, Gate, Beep, Click, Purchase, Whistle, Respawn,
        DoubleJump, Slide, GetUp,
    }

    /// <summary>Recipes for every sound effect, synthesized at startup (a few ms each).</summary>
    public static class SoundBank
    {
        public static Dictionary<Sfx, float[]> BuildAll()
        {
            var d = new Dictionary<Sfx, float[]>();
            foreach (Sfx s in Enum.GetValues(typeof(Sfx))) d[s] = Build(s);
            return d;
        }

        static float[] Build(Sfx s)
        {
            float[] b;
            switch (s)
            {
                case Sfx.Kick:
                    b = Synth.Buffer(0.3f);
                    Synth.Sweep(b, 0, 0.25f, 150, 50, 0.002, 14, 0.9f);
                    Synth.Noise(b, 0, 0.06f, 0.001, 50, 0.5f, 0.35f, 1);
                    break;
                case Sfx.Touch:
                    b = Synth.Buffer(0.14f);
                    Synth.Sweep(b, 0, 0.12f, 230, 120, 0.002, 30, 0.6f);
                    Synth.Noise(b, 0, 0.03f, 0.001, 80, 0.2f, 0.4f, 2);
                    break;
                case Sfx.Perfect:
                    b = Synth.Buffer(0.6f);
                    Synth.Sweep(b, 0, 0.12f, 230, 120, 0.002, 30, 0.5f);
                    Synth.Bell(b, 400, 1318.5, 0.5f, 0.28f, 6);
                    Synth.Bell(b, 1500, 1975.5, 0.45f, 0.2f, 7);
                    break;
                case Sfx.Juggle:
                    b = Synth.Buffer(0.18f);
                    Synth.Sweep(b, 0, 0.15f, 520, 760, 0.002, 22, 0.55f);
                    Synth.Sweep(b, 0, 0.12f, 1040, 1520, 0.002, 30, 0.15f);
                    break;
                case Sfx.Trap:
                    b = Synth.Buffer(0.12f);
                    Synth.Sweep(b, 0, 0.1f, 160, 100, 0.002, 35, 0.5f);
                    break;
                case Sfx.Jump:
                    // A trainer pushing off: a soft thud through the sole, a scuff of grit and a swish of clothes.
                    b = Synth.Buffer(0.3f);
                    Thud(b, 0, 0.09f, 105, 62, 0.4f);
                    Band(b, 0, 0.06f, 2600, 1.2, 0.0008, 70, 0.22f, 3);
                    Swish(b, 0.015f, 0.2f, 700, 1600, 0.16f, 31);
                    break;
                case Sfx.Land:
                    // Both feet coming down, a hair apart: heel thuds, grit under the soles, clothes settling.
                    b = Synth.Buffer(0.3f);
                    Thud(b, 0, 0.12f, 120, 52, 0.75f);
                    Thud(b, (int)(0.022f * Synth.SampleRate), 0.1f, 105, 50, 0.42f);
                    Band(b, 0, 0.1f, 2100, 1.0, 0.001, 38, 0.24f, 4);
                    Swish(b, 0.02f, 0.14f, 1200, 800, 0.06f, 41);
                    break;
                case Sfx.Bounce:
                    // A football on the pavement: a hollow thump with the ball's own ring and the slap of its panel.
                    b = Synth.Buffer(0.2f);
                    Thud(b, 0, 0.14f, 240, 135, 0.55f);
                    Synth.Sweep(b, 0, 0.12f, 410, 380, 0.001, 32, 0.1f);
                    Band(b, 0, 0.03f, 1700, 1.0, 0.0005, 120, 0.25f, 18);
                    break;
                case Sfx.Coin:
                {
                    // An endless runner's coin: a crisp, bright arcade "bling", short so a string of coins
                    // reads as a quick run of pings. A tiny blip up to the note (a triangle, the "game"
                    // edge), then a clean high bell an octave and a fifth up that rings out fast, with a
                    // faint sparkle of shimmer on top.
                    b = Synth.Buffer(0.32f);
                    Synth.Sweep(b, 0, 0.045f, 1760, 2349, 0.0008, 60, 0.2f, Synth.Triangle);
                    int ring = (int)(0.035f * Synth.SampleRate);
                    double[] ratio = { 1.0, 2.0, 2.76 };   // (all under the 11 kHz the 22 kHz synth can make)
                    float[] amp = { 1f, 0.32f, 0.14f };
                    for (int p = 0; p < ratio.Length; p++)
                    {
                        Synth.Sweep(b, ring, 0.28f, 2637 * ratio[p], 2637 * ratio[p], 0.0008, 16 * (1 + p * 0.7), 0.3f * amp[p]);
                        Synth.Sweep(b, ring, 0.28f, 2637 * ratio[p] * 1.003, 2637 * ratio[p] * 1.003, 0.0008, 16 * (1 + p * 0.7), 0.12f * amp[p]);
                    }
                    Band(b, ring, 0.06f, 8500, 1.2, 0.0005, 60, 0.05f, 21);
                    break;
                }
                case Sfx.Sticker:
                    b = Synth.Buffer(0.9f);
                    double[] arp = { 1046.5, 1318.5, 1568, 2093 };
                    for (int i = 0; i < arp.Length; i++) Synth.Bell(b, (int)(i * 0.07f * Synth.SampleRate), arp[i], 0.6f, 0.22f, 5);
                    break;
                case Sfx.Checkpoint:
                    b = Synth.Buffer(0.8f);
                    Synth.Bell(b, 0, 784, 0.6f, 0.3f, 5);
                    Synth.Bell(b, (int)(0.12f * Synth.SampleRate), 1046.5, 0.6f, 0.3f, 5);
                    break;
                case Sfx.Bell:
                {
                    // School bell: a hammer ringing fast against a bell.
                    b = Synth.Buffer(1.6f);
                    for (int i = 0; i < 26; i++)
                        Synth.Bell(b, (int)(i * 0.055f * Synth.SampleRate), 1760, 0.4f, 0.22f, 9);
                    break;
                }
                case Sfx.Goal:
                {
                    b = Synth.Buffer(1.6f);
                    double[] notes = { 523.25, 659.25, 783.99, 1046.5 };
                    for (int i = 0; i < notes.Length; i++)
                    {
                        int at = (int)(i * 0.12f * Synth.SampleRate);
                        float len = i == notes.Length - 1 ? 1f : 0.3f;
                        Synth.Sweep(b, at, len, notes[i], notes[i], 0.01, i == notes.Length - 1 ? 2.5 : 8, 0.38f, p => Synth.Saw(p) * 0.4f + Synth.Sine(p));
                        Synth.Bell(b, at, notes[i] * 2, len, 0.08f, 4);
                    }
                    // The crowd: a cheer swelling under the fanfare and a patter of applause.
                    var crowd = new Random(5);
                    for (int i = 0; i < 6; i++)
                        Voice(b, 0.3f + (float)crowd.NextDouble() * 0.15f, 1.1f, 260 + crowd.Next(200), 300 + crowd.Next(220), 700 + crowd.Next(300), 1300 + crowd.Next(500), 0.07f, 0.45f, 50 + i, 0.1f);
                    for (int i = 0; i < 70; i++)
                    {
                        float t = 0.3f + (float)crowd.NextDouble() * 1.15f;
                        float fade = 1f - (t - 0.3f) / 1.25f;
                        Band(b, (int)(t * Synth.SampleRate), 0.03f, 1100 + crowd.Next(900), 1.2, 0.0005, 140, 0.1f * fade, 100 + i);
                    }
                    break;
                }
                case Sfx.Lose:
                    b = Synth.Buffer(0.6f);
                    Synth.Sweep(b, 0, 0.55f, 420, 160, 0.01, 4, 0.5f, p => Synth.Triangle(p));
                    break;
                case Sfx.Splash:
                {
                    // Into a puddle: a slap, a spray that falls away, and a few bubbles popping.
                    b = Synth.Buffer(0.7f);
                    Thud(b, 0, 0.1f, 160, 70, 0.4f);
                    Band(b, 0, 0.6f, 1800, 0.6, 0.003, 7, 0.55f, 6);
                    Band(b, 0, 0.2f, 4200, 0.8, 0.001, 18, 0.25f, 61);
                    var rng = new Random(62);
                    for (int i = 0; i < 6; i++)
                    {
                        int at = (int)((0.06 + i * 0.06 + rng.NextDouble() * 0.04) * Synth.SampleRate);
                        double f = 700 + rng.NextDouble() * 800;
                        Synth.Sweep(b, at, 0.05f, f, f * 1.8, 0.002, 40, 0.1f);
                    }
                    break;
                }
                case Sfx.Woof:
                    // A dog's bark, twice: a voiced yelp shaped by its mouth, rough at the start.
                    b = Synth.Buffer(0.5f);
                    for (int i = 0; i < 2; i++)
                        Voice(b, i * 0.21f, 0.16f, 470 - i * 30, 330 - i * 20, 820, 1650, 0.3f, 0.25f, 7 + i, 0.25f);
                    break;
                case Sfx.Squawk:
                    // A gull, cross: a harsh rising-then-falling "kyaa".
                    b = Synth.Buffer(0.45f);
                    Voice(b, 0f, 0.4f, 1350, 900, 1900, 3200, 0.24f, 0.2f, 21, 0.4f, 1700);
                    break;
                case Sfx.Oof:
                    // Someone bumped: a short, low "oof".
                    b = Synth.Buffer(0.26f);
                    Voice(b, 0f, 0.22f, 175, 125, 450, 850, 0.36f, 0.35f, 22, 0.1f);
                    Thud(b, 0, 0.08f, 140, 70, 0.25f);
                    break;
                case Sfx.Boing:
                {
                    b = Synth.Buffer(0.45f);
                    double phase = 0;
                    for (int i = 0; i < b.Length; i++)
                    {
                        double t = i / (double)Synth.SampleRate;
                        double f = 180 + 520 * Math.Min(1, t / 0.2) + Math.Sin(t * 2 * Math.PI * 14) * 40;
                        phase += f / Synth.SampleRate;
                        b[i] += Synth.Sine(phase) * Synth.Env(t, 0.003, 6) * 0.5f;
                    }
                    break;
                }
                case Sfx.Switch:
                    b = Synth.Buffer(0.4f);
                    Synth.Noise(b, 0, 0.02f, 0.001, 200, 0.4f, 0.8f, 9);
                    Synth.Bell(b, 300, 1568, 0.35f, 0.25f, 7);
                    break;
                case Sfx.Gate:
                    b = Synth.Buffer(0.6f);
                    Synth.Noise(b, 0, 0.55f, 0.05, 4, 0.5f, 0.05f, 10);
                    Synth.Sweep(b, 0, 0.5f, 70, 110, 0.05, 4, 0.2f);
                    break;
                case Sfx.Beep:
                    b = Synth.Buffer(0.3f);
                    Synth.Sweep(b, 0, 0.08f, 880, 880, 0.002, 4, 0.25f, p => Synth.Square(p));
                    Synth.Sweep(b, (int)(0.14f * Synth.SampleRate), 0.08f, 880, 880, 0.002, 4, 0.25f, p => Synth.Square(p));
                    break;
                case Sfx.Click:
                    b = Synth.Buffer(0.05f);
                    Synth.Sweep(b, 0, 0.04f, 1500, 900, 0.001, 80, 0.4f);
                    break;
                case Sfx.Purchase:
                    b = Synth.Buffer(0.7f);
                    Synth.Noise(b, 0, 0.05f, 0.001, 60, 0.3f, 0.7f, 11);
                    Synth.Bell(b, 600, 1318.5, 0.5f, 0.25f, 5);
                    Synth.Bell(b, 2600, 1975.5, 0.5f, 0.25f, 5);
                    break;
                case Sfx.Whistle:
                {
                    // Referee whistle, blown short and from across the pitch: a softer, lower tone with its
                    // pea-trill, and less breath (it was a long, piercing 2.6 kHz blast).
                    b = Synth.Buffer(0.38f);
                    double phase = 0;
                    for (int i = 0; i < b.Length; i++)
                    {
                        double t = i / (double)Synth.SampleRate;
                        double f = 2250 + Math.Sin(t * 2 * Math.PI * 30) * 90;
                        phase += f / Synth.SampleRate;
                        float env = (float)(Math.Min(1, t / 0.025) * Math.Min(1, (0.38 - t) / 0.1));
                        b[i] += Synth.Sine(phase) * env * 0.25f;
                    }
                    Synth.Noise(b, 0, 0.38f, 0.02, 4, 0.03f, 0.6f, 12);
                    break;
                }
                case Sfx.Respawn:
                    b = Synth.Buffer(0.35f);
                    Synth.Sweep(b, 0, 0.3f, 300, 900, 0.02, 8, 0.25f);
                    Synth.Noise(b, 0, 0.3f, 0.05, 8, 0.15f, 0.2f, 13);
                    break;
                case Sfx.DoubleJump:
                    // A second, harder push in the air: no sparkle, just the body. Arms and jacket whipping
                    // up in a quick rush of air, and a short breath of effort.
                    b = Synth.Buffer(0.42f);
                    Swish(b, 0f, 0.3f, 500, 2100, 0.62f, 14);
                    Swish(b, 0.06f, 0.22f, 900, 1500, 0.26f, 15);
                    Breath(b, 0.01f, 0.13f, 750, 1250, 0.16f, 16);
                    break;
                case Sfx.Slide:
                    // Feet going out: a low thump and a bright rush of air, then shoes scuffing along the
                    // ground, a soft hiss that wavers as it fades.
                    b = Synth.Buffer(0.7f);
                    Synth.Sweep(b, 0, 0.14f, 130, 62, 0.002, 26, 0.4f);
                    Synth.Noise(b, 0, 0.18f, 0.01, 14, 0.28f, 0.55f, 15);
                    Synth.Noise(b, (int)(0.04f * Synth.SampleRate), 0.64f, 0.05, 4.0, 0.3f, 0.16f, 16);
                    for (int i = 0; i < b.Length; i++)
                        b[i] *= 0.8f + 0.2f * (float)Math.Sin(i / (double)Synth.SampleRate * 2 * Math.PI * 23);
                    break;
                case Sfx.GetUp:
                    // Springing up out of a slide: feet planted with a soft thump and a quick breath of air.
                    b = Synth.Buffer(0.24f);
                    Synth.Sweep(b, 0, 0.12f, 170, 95, 0.002, 28, 0.38f);
                    Synth.Noise(b, 0, 0.16f, 0.02, 16, 0.2f, 0.35f, 17);
                    Synth.Sweep(b, 0, 0.12f, 420, 760, 0.004, 22, 0.1f);
                    break;
                default:
                    b = Synth.Buffer(0.05f);
                    break;
            }
            Synth.Limit(b, 0.9f);
            Synth.FadeTail(b);
            return b;
        }

        // ---------- Building blocks ----------

        /// <summary>A thud: a sine dropping in pitch with a fast decay (a foot, a ball, a body).</summary>
        static void Thud(float[] b, int start, float seconds, double f0, double f1, float gain)
        {
            Synth.Sweep(b, start, seconds, f0, f1, 0.0015, 4.5 / seconds, gain);
        }

        /// <summary>A burst of band-passed noise (grit, slaps, claps, spray).</summary>
        static void Band(float[] b, int start, float seconds, double centre, double q, double attack, double decay, float gain, int seed)
        {
            var f = new Svf();
            var n = new NoiseSource(seed);
            int len = (int)(seconds * Synth.SampleRate);
            for (int i = 0; i < len && start + i < b.Length; i++)
            {
                double t = i / (double)Synth.SampleRate;
                f.Process(n.White(), centre, q);
                float tail = Math.Min(1f, (len - i) / (0.005f * Synth.SampleRate));
                b[start + i] += f.band * Synth.Env(t, attack, decay) * tail * gain;
            }
        }

        /// <summary>A swish of air or cloth: noise whose band sweeps from one pitch to another, swelling and fading.</summary>
        static void Swish(float[] b, float at, float seconds, double f0, double f1, float gain, int seed)
        {
            var f = new Svf();
            var n = new NoiseSource(seed);
            int start = (int)(at * Synth.SampleRate), len = (int)(seconds * Synth.SampleRate);
            for (int i = 0; i < len && start + i < b.Length; i++)
            {
                double u = i / (double)len;
                f.Process(n.White(), f0 * Math.Pow(f1 / f0, u), 0.9);
                double env = Math.Sin(Math.PI * Math.Pow(u, 0.6));
                b[start + i] += f.band * (float)(env * env) * gain;
            }
        }

        /// <summary>A breath: noise through two vowel formants, quick in and out.</summary>
        static void Breath(float[] b, float at, float seconds, double f1, double f2, float gain, int seed)
        {
            var a = new Svf();
            var c = new Svf();
            var n = new NoiseSource(seed);
            int start = (int)(at * Synth.SampleRate), len = (int)(seconds * Synth.SampleRate);
            for (int i = 0; i < len && start + i < b.Length; i++)
            {
                double u = i / (double)len;
                float x = n.White();
                a.Process(x, f1, 3);
                c.Process(x, f2, 4);
                double env = Math.Min(1, u * 8) * Math.Pow(1 - u, 1.5);
                b[start + i] += (a.band + c.band * 0.6f) * (float)env * gain;
            }
        }

        /// <summary>A voiced call (a bark, a gull, a grunt, a cheer): a buzz gliding in pitch through two formants.</summary>
        static void Voice(float[] b, float at, float seconds, double pitch0, double pitch1, double f1, double f2, float gain, float noise, int seed,
            float rough = 0f, double peakPitch = 0)
        {
            var fa = new Svf();
            var fb = new Svf();
            var n = new NoiseSource(seed);
            int start = (int)(at * Synth.SampleRate), len = (int)(seconds * Synth.SampleRate);
            double ph = 0;
            for (int i = 0; i < len && start + i < b.Length; i++)
            {
                double u = i / (double)len, t = i / (double)Synth.SampleRate;
                double pitch = peakPitch > 0
                    ? (u < 0.3 ? pitch0 + (peakPitch - pitch0) * (u / 0.3) : peakPitch + (pitch1 - peakPitch) * ((u - 0.3) / 0.7))
                    : pitch0 + (pitch1 - pitch0) * u;
                ph += pitch / Synth.SampleRate;
                double p = ph - Math.Floor(ph);
                double src = (2 * p - 1) * (1 - noise) + n.White() * noise;
                if (rough > 0f) src *= 1 - rough * (0.5 + 0.5 * Math.Sin(2 * Math.PI * 70 * t));
                fa.Process((float)src, f1, 4);
                fb.Process((float)src, f2, 5);
                double env = Math.Min(1, t / 0.01) * Math.Pow(1 - u, 1.3);
                b[start + i] += (float)((fa.band + fb.band * 0.7) * env) * gain;
            }
        }
    }
}
