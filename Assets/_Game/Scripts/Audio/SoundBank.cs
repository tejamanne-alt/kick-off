using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    public enum Sfx
    {
        Kick, Touch, Perfect, Juggle, Trap, Jump, Land, Bounce, Coin, Sticker, Checkpoint, Bell, Goal, Lose,
        Splash, Woof, Squawk, Oof, Boing, Switch, Gate, Beep, Click, Purchase, Whistle, Respawn,
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
                    b = Synth.Buffer(0.25f);
                    Synth.Noise(b, 0, 0.22f, 0.04, 12, 0.35f, 0.15f, 3);
                    Synth.Sweep(b, 0, 0.18f, 300, 520, 0.01, 14, 0.18f);
                    break;
                case Sfx.Land:
                    b = Synth.Buffer(0.2f);
                    Synth.Sweep(b, 0, 0.18f, 95, 50, 0.002, 18, 0.7f);
                    Synth.Noise(b, 0, 0.08f, 0.001, 35, 0.3f, 0.2f, 4);
                    break;
                case Sfx.Bounce:
                    b = Synth.Buffer(0.14f);
                    Synth.Sweep(b, 0, 0.12f, 190, 95, 0.002, 28, 0.55f);
                    break;
                case Sfx.Coin:
                    b = Synth.Buffer(0.32f);
                    Synth.Sweep(b, 0, 0.07f, 987.8, 987.8, 0.002, 10, 0.3f, p => Synth.Square(p, 0.3) * 0.5f + Synth.Sine(p));
                    Synth.Sweep(b, (int)(0.07f * Synth.SampleRate), 0.24f, 1318.5, 1318.5, 0.002, 9, 0.3f, p => Synth.Square(p, 0.3) * 0.5f + Synth.Sine(p));
                    break;
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
                    Synth.Noise(b, (int)(0.36f * Synth.SampleRate), 1f, 0.15, 3, 0.15f, 0.25f, 5);   // crowd "yay"
                    break;
                }
                case Sfx.Lose:
                    b = Synth.Buffer(0.6f);
                    Synth.Sweep(b, 0, 0.55f, 420, 160, 0.01, 4, 0.5f, p => Synth.Triangle(p));
                    break;
                case Sfx.Splash:
                    b = Synth.Buffer(0.6f);
                    Synth.Noise(b, 0, 0.55f, 0.005, 7, 0.6f, 0.25f, 6);
                    for (int i = 0; i < 4; i++) Synth.Sweep(b, (int)((0.08 + i * 0.07) * Synth.SampleRate), 0.06f, 600 + i * 120, 1200 + i * 150, 0.002, 30, 0.12f);
                    break;
                case Sfx.Woof:
                    b = Synth.Buffer(0.45f);
                    for (int i = 0; i < 2; i++)
                    {
                        int at = (int)(i * 0.2f * Synth.SampleRate);
                        Synth.Sweep(b, at, 0.13f, 320, 210, 0.005, 16, 0.5f, p => Synth.Saw(p) * 0.6f + Synth.Sine(p));
                        Synth.Noise(b, at, 0.1f, 0.003, 25, 0.25f, 0.3f, 7 + i);
                    }
                    break;
                case Sfx.Squawk:
                {
                    b = Synth.Buffer(0.4f);
                    double phase = 0;
                    for (int i = 0; i < b.Length; i++)
                    {
                        double t = i / (double)Synth.SampleRate;
                        double f = 1300 - t * 1500 + Math.Sin(t * 2 * Math.PI * 35) * 260;
                        phase += f / Synth.SampleRate;
                        b[i] += Synth.Saw(phase) * Synth.Env(t, 0.01, 6) * 0.3f;
                    }
                    break;
                }
                case Sfx.Oof:
                    b = Synth.Buffer(0.2f);
                    Synth.Sweep(b, 0, 0.18f, 210, 140, 0.01, 14, 0.45f, p => Synth.Triangle(p));
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
                    // Referee whistle: bright tone with a pea-trill.
                    b = Synth.Buffer(0.5f);
                    double phase = 0;
                    for (int i = 0; i < b.Length; i++)
                    {
                        double t = i / (double)Synth.SampleRate;
                        double f = 2600 + Math.Sin(t * 2 * Math.PI * 32) * 120;
                        phase += f / Synth.SampleRate;
                        float env = (float)(Math.Min(1, t / 0.02) * Math.Min(1, (0.5 - t) / 0.08));
                        b[i] += Synth.Sine(phase) * env * 0.25f;
                    }
                    Synth.Noise(b, 0, 0.5f, 0.02, 3, 0.05f, 0.9f, 12);
                    break;
                }
                case Sfx.Respawn:
                    b = Synth.Buffer(0.35f);
                    Synth.Sweep(b, 0, 0.3f, 300, 900, 0.02, 8, 0.25f);
                    Synth.Noise(b, 0, 0.3f, 0.05, 8, 0.15f, 0.2f, 13);
                    break;
                default:
                    b = Synth.Buffer(0.05f);
                    break;
            }
            Synth.Limit(b, 0.9f);
            Synth.FadeTail(b);
            return b;
        }
    }
}
