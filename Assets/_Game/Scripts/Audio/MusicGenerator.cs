using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// The music, one 16-bar loop for each soundscape, each in its own style and with its own band:
    /// a lo-fi electric piano for the menu, a sunny strummed-guitar pop tune for Home Street, an
    /// accordion oom-pah with a mandolin for the market, steel pan and marimba calypso at the beach,
    /// a dark, echoing groove in the underpass, a bouncy work-song with a clanking anvil on the
    /// building site, and harp, strings and flute in the park. Each loop has two halves (A and B) with
    /// their own chords and lead, a melody built from motifs that come back, a drum fill into each
    /// half, stereo placement and a shared reverb sized for the place. Deterministic, seamless when
    /// looped (notes and the reverb's tail wrap round), pure C#: safe on a worker thread.
    /// Output: interleaved stereo at <see cref="Synth.SampleRate"/>.
    /// </summary>
    public static class MusicGenerator
    {
        public const int Channels = 2;
        /// <summary>The loops' loudness (RMS of the mix): every soundscape plays equally loud.</summary>
        public const float Loudness = 0.16f;
        const int Bars = 16;

        /// <summary>The music for a chapter (0 = the menu), for code that only knows the chapter.</summary>
        public static float[] Generate(int chapter)
        {
            return Generate(chapter <= 0 ? Soundscape.Menu : Soundscapes.For(null, chapter));
        }

        public static float[] Generate(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street: return Street();
                case Soundscape.Market: return Market();
                case Soundscape.Beach: return Beach();
                case Soundscape.Underpass: return Underpass();
                case Soundscape.Site: return Site();
                case Soundscape.Park: return Park();
                default: return Menu();
            }
        }

        // ================= Songs =================

        static float[] Menu()
        {
            // Lo-fi: rolled electric-piano sevenths, a lazy round bass, soft swung drums and vinyl crackle.
            var s = new Song(78, 0.09, 60, Mode.Major, 7,
                "Fmaj7", "Em7", "Dm7", "Cmaj7", "Fmaj7", "Em7", "Dm7", "G7sus4",
                "Am7", "Dm7", "G7", "Cmaj7", "Fmaj7", "Em7", "Am7", "Dm7 G7");
            var mix = new Mixdown(s.Length) { roomSize = 0.7f, damping = 0.55f, wet = 0.32f };
            var keys = mix.Add(-0.2f, 0.4f, 0.55f);
            var pad = mix.Add(0.45f, 0.6f, 0.22f);
            var bass = mix.Add(0f, 0.05f, 0.85f);
            var lead = mix.Add(0.25f, 0.5f, 0.42f);
            var glock = mix.Add(0.35f, 0.55f, 0.22f);
            var drums = mix.Add(0f, 0.12f, 0.7f);
            var hats = mix.Add(0.3f, 0.1f, 0.3f);
            var vinyl = mix.Add(0f, 0f, 0.5f);

            for (int bar = 0; bar < Bars; bar++)
            {
                foreach (var ch in s.ChordsIn(bar))
                {
                    var v = ch.chord.Voice(55, 70);
                    double half = ch.length;
                    Instruments.EPianoChord(keys, s.T(bar, ch.beat), v, s.Beats(Math.Min(half, 1.6)), 0.5f, 0.018);
                    if (half >= 4) Instruments.EPianoChord(keys, s.T(bar, ch.beat + 2.5), v, s.Beats(1.2), 0.38f, 0.014);
                    Instruments.Pad(pad, s.T(bar, ch.beat), ch.chord.Voice(48, 62), s.Beats(half), 0.5f, 900, bar * 3 + 1, 0.6);
                    int root = ch.chord.Bass(36);
                    Instruments.RoundBass(bass, s.T(bar, ch.beat), Synth.MidiToHz(root), s.Beats(half >= 4 ? 1.6 : 1.4), 0.8f);
                    if (half >= 4)
                    {
                        Instruments.RoundBass(bass, s.T(bar, ch.beat + 2.5), Synth.MidiToHz(root + 7), s.Beats(0.45), 0.55f);
                        Instruments.RoundBass(bass, s.T(bar, ch.beat + 3), Synth.MidiToHz(root + 12), s.Beats(0.8), 0.5f);
                    }
                }

                for (int b = 0; b < 4; b++)
                {
                    if (b == 0 || (b == 2 && bar % 2 == 1)) Instruments.Kick(drums, s.T(bar, b), 0.75f, 0.9);
                    if (b == 2 && bar % 2 == 0) Instruments.Kick(drums, s.T(bar, 2.5), 0.6f, 0.9);
                    if (b == 1 || b == 3) Instruments.Snare(drums, s.T(bar, b), 0.32f, bar * 4 + b, 0.85);
                    Instruments.Hat(hats, s.T(bar, b), 0.32f, bar * 8 + b);
                    Instruments.Hat(hats, s.T(bar, b + 0.5), 0.22f, bar * 8 + b + 100);
                }
                if (bar == 7 || bar == 15)
                {
                    Instruments.Snare(drums, s.T(bar, 3.5), 0.2f, 999, 0.85);
                    Instruments.Snare(drums, s.T(bar, 3.75), 0.26f, 998, 0.85);
                }
            }
            Instruments.Vinyl(vinyl, 1f, 5);

            var melody = s.Melody(0, 72, 86, new Random(70), Rhythms.Sparse);
            foreach (var n in melody) Instruments.EPiano(lead, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len), n.vel * 0.7f);
            var answer = s.Melody(8, 74, 88, new Random(71), Rhythms.Sparse);
            foreach (var n in answer) Instruments.Glock(glock, s.T(n), Synth.MidiToHz(n.midi), n.vel * 0.8f, 2.6);
            return mix.Render(Loudness);
        }

        static float[] Street()
        {
            // Home Street on a sunny morning: a strummed acoustic guitar, a glockenspiel tune and then a
            // whistled flute one, a picked bass, claps and a shaker.
            var s = new Song(104, 0, 62, Mode.Major, 11,
                "D", "A", "Bm", "G", "D", "A", "G", "A",
                "G", "A", "F#m", "Bm", "G", "A", "Em7", "A7");
            var mix = new Mixdown(s.Length) { roomSize = 0.5f, damping = 0.45f, wet = 0.22f };
            var guitar = mix.Add(-0.4f, 0.2f, 0.8f);
            var uke = mix.Add(0.45f, 0.2f, 0.5f);
            var bass = mix.Add(0f, 0.05f, 0.9f);
            var glock = mix.Add(0.2f, 0.35f, 0.55f);
            var flute = mix.Add(0.1f, 0.35f, 0.6f);
            var pad = mix.Add(-0.1f, 0.5f, 0.16f);
            var drums = mix.Add(0f, 0.12f, 0.75f);
            var shaker = mix.Add(0.5f, 0.1f, 0.35f);
            var claps = mix.Add(-0.15f, 0.25f, 0.35f);

            double[] strum = { 0, 1, 1.5, 2.5, 3, 3.5 };
            bool[] down = { true, true, false, false, true, false };
            for (int bar = 0; bar < Bars; bar++)
            {
                var ch = s.ChordsIn(bar)[0];
                var gv = ch.chord.Voice(50, 67, 5);
                for (int i = 0; i < strum.Length; i++)
                    Instruments.Strum(guitar, s.T(bar, strum[i]), down[i] ? gv : Top(gv, 4), s.Beats(down[i] ? 0.9 : 0.45), down[i] ? 0.55f : 0.38f,
                        bar * 40 + i * 6, down[i], down[i] ? 0.011 : 0.007, 0.6f);
                if (bar >= 8)
                    for (int b = 0; b < 4; b++)
                        Instruments.Strum(uke, s.T(bar, b + 0.5), ch.chord.Voice(67, 79, 4), s.Beats(0.25), 0.35f, bar * 31 + b, true, 0.006, 0.8f);
                Instruments.Pad(pad, s.T(bar, 0), ch.chord.Voice(57, 69), s.Beats(4), 0.4f, 1300, bar + 3);

                int root = ch.chord.Bass(38);
                double[] bassAt = { 0, 1.5, 2, 3, 3.5 };
                int[] bassNote = { root, root, root + 7, root + 12, root + 7 };
                for (int i = 0; i < bassAt.Length; i++)
                    Instruments.PluckBass(bass, s.T(bar, bassAt[i]), Synth.MidiToHz(bassNote[i]), s.Beats(i == 0 ? 1.3 : 0.45), i == 0 ? 0.85f : 0.6f, bar * 9 + i);

                Instruments.Kick(drums, s.T(bar, 0), 0.8f);
                Instruments.Kick(drums, s.T(bar, 1.5), 0.45f);
                Instruments.Kick(drums, s.T(bar, 2), 0.7f);
                Instruments.Snare(drums, s.T(bar, 1), 0.36f, bar * 2);
                Instruments.Snare(drums, s.T(bar, 3), 0.4f, bar * 2 + 1);
                Instruments.Clap(claps, s.T(bar, 1), 0.5f, bar * 3);
                Instruments.Clap(claps, s.T(bar, 3), 0.55f, bar * 3 + 1);
                for (int e = 0; e < 8; e++) Instruments.Shaker(shaker, s.T(bar, e * 0.5), e % 2 == 1 ? 0.55f : 0.32f, bar * 16 + e);
                if (bar == 7 || bar == 15)
                    for (int k = 0; k < 4; k++) Instruments.Snare(drums, s.T(bar, 3 + k * 0.25), 0.2f + k * 0.07f, 500 + bar + k);
            }

            foreach (var n in s.Melody(0, 74, 88, new Random(110), Rhythms.Bouncy))
                Instruments.Glock(glock, s.T(n), Synth.MidiToHz(n.midi), n.vel, 3.2);
            foreach (var n in s.Melody(8, 71, 86, new Random(111), Rhythms.Singing))
                Instruments.Flute(flute, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.92, n.vel, n.midi * 13);
            return mix.Render(Loudness);
        }

        static float[] Market()
        {
            // Market Street: an accordion oom-pah (bass on one and three, chords on two and four), a
            // swung accordion tune and then a tremolo mandolin, tambourine and brushes.
            var s = new Song(112, 0.12, 65, Mode.Major, 22,
                "F", "C7", "F", "Bb", "F", "C7", "F", "F",
                "Bb", "F", "Gm", "C7", "Am", "Dm", "Gm7", "C7");
            var mix = new Mixdown(s.Length) { roomSize = 0.45f, damping = 0.5f, wet = 0.2f };
            var bass = mix.Add(0f, 0.05f, 0.85f);
            var comp = mix.Add(-0.35f, 0.2f, 0.45f);
            var lead = mix.Add(0.25f, 0.25f, 0.5f);
            var mandolin = mix.Add(0.3f, 0.3f, 0.6f);
            var guitar = mix.Add(-0.5f, 0.2f, 0.45f);
            var drums = mix.Add(0f, 0.15f, 0.6f);
            var tamb = mix.Add(0.5f, 0.15f, 0.35f);

            for (int bar = 0; bar < Bars; bar++)
            {
                var ch = s.ChordsIn(bar)[0];
                int root = ch.chord.Bass(41);
                int fifth = root + 7 > 52 ? root - 5 : root + 7;
                Instruments.RoundBass(bass, s.T(bar, 0), Synth.MidiToHz(root), s.Beats(0.8), 0.85f);
                Instruments.RoundBass(bass, s.T(bar, 2), Synth.MidiToHz(fifth), s.Beats(0.8), 0.75f);
                if (bar % 4 == 3) Instruments.RoundBass(bass, s.T(bar, 3.5), Synth.MidiToHz(root + 2), s.Beats(0.4), 0.5f);
                var v = ch.chord.Voice(57, 70);
                foreach (double b in new[] { 1.0, 3.0 })
                    foreach (int m in v) Instruments.Accordion(comp, s.T(bar, b), Synth.MidiToHz(m), s.Beats(0.42), 0.32f);
                // A nylon guitar picks the chord on the off-beats in the second half.
                if (bar >= 8)
                    for (int e = 0; e < 4; e++)
                        Instruments.Pluck(guitar, s.T(bar, e + 0.5), Synth.MidiToHz(v[e % v.Length] + 12), s.Beats(0.5), 0.42f, bar * 17 + e, 0.45f);

                Instruments.Kick(drums, s.T(bar, 0), 0.55f, 1.1);
                Instruments.Kick(drums, s.T(bar, 2), 0.45f, 1.1);
                Instruments.Brush(drums, s.T(bar, 1), 0.6f, bar * 2);
                Instruments.Brush(drums, s.T(bar, 3), 0.65f, bar * 2 + 1);
                for (int e = 0; e < 8; e++) Instruments.Tambourine(tamb, s.T(bar, e * 0.5), e % 2 == 1 ? 0.5f : 0.3f, bar * 8 + e);
                if (bar == 7 || bar == 15)
                    for (int k = 0; k < 3; k++) Instruments.Brush(drums, s.T(bar, 3 + k / 3.0), 0.4f + k * 0.15f, 700 + bar + k, 0.06);
            }

            foreach (var n in s.Melody(0, 72, 86, new Random(220), Rhythms.Dance))
                Instruments.Accordion(lead, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.85, n.vel * 0.85f);
            foreach (var n in s.Melody(8, 74, 89, new Random(221), Rhythms.Singing))
                Instruments.Tremolo(mandolin, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.95, n.vel * 0.5f, n.midi * 7, 14);
            return mix.Render(Loudness);
        }

        static float[] Beach()
        {
            // The beach: calypso. Marimba chords skanking on the off-beats, a steel pan tune, a
            // syncopated bass, congas, a rim and a shaker, a ukulele joining in the second half.
            var s = new Song(96, 0.08, 67, Mode.Major, 33,
                "G", "C", "D", "G", "Em", "C", "D", "G",
                "C", "D", "Bm7", "Em", "C", "Am7", "D", "D7");
            var mix = new Mixdown(s.Length) { roomSize = 0.55f, damping = 0.35f, wet = 0.24f };
            var marimba = mix.Add(-0.35f, 0.2f, 0.65f);
            var pan = mix.Add(0.2f, 0.35f, 0.6f);
            var uke = mix.Add(0.45f, 0.2f, 0.45f);
            var bass = mix.Add(0f, 0.05f, 0.9f);
            var pad = mix.Add(0f, 0.5f, 0.15f);
            var drums = mix.Add(0f, 0.12f, 0.6f);
            var congas = mix.Add(-0.4f, 0.2f, 0.55f);
            var shaker = mix.Add(0.5f, 0.1f, 0.35f);

            for (int bar = 0; bar < Bars; bar++)
            {
                var ch = s.ChordsIn(bar)[0];
                var v = ch.chord.Voice(60, 74);
                for (int e = 0; e < 4; e++)
                    foreach (int m in v) Instruments.Marimba(marimba, s.T(bar, e + 0.5), Synth.MidiToHz(m), (e % 2 == 0 ? 0.4f : 0.32f));
                if (bar >= 8)
                    for (int e = 0; e < 4; e++)
                        Instruments.Strum(uke, s.T(bar, e + 0.5), ch.chord.Voice(67, 79, 4), s.Beats(0.3), 0.3f, bar * 13 + e, e % 2 == 0, 0.006, 0.75f);
                Instruments.Pad(pad, s.T(bar, 0), ch.chord.Voice(55, 67), s.Beats(4), 0.4f, 1100, bar + 7);

                int root = ch.chord.Bass(43);
                if (root > 50) root -= 12;
                Instruments.RoundBass(bass, s.T(bar, 0), Synth.MidiToHz(root), s.Beats(1.0), 0.85f);
                Instruments.RoundBass(bass, s.T(bar, 1.5), Synth.MidiToHz(root + 7), s.Beats(0.45), 0.65f);
                Instruments.RoundBass(bass, s.T(bar, 2), Synth.MidiToHz(root + 12), s.Beats(0.7), 0.7f);
                Instruments.RoundBass(bass, s.T(bar, 3.5), Synth.MidiToHz(root + 7), s.Beats(0.45), 0.6f);

                Instruments.Kick(drums, s.T(bar, 0), 0.6f);
                Instruments.Kick(drums, s.T(bar, 2.5), 0.45f);
                Instruments.Rim(drums, s.T(bar, 1), 0.5f);
                Instruments.Rim(drums, s.T(bar, 3), 0.55f);
                Instruments.Conga(congas, s.T(bar, 0.75), 0.4f, true);
                Instruments.Conga(congas, s.T(bar, 1.5), 0.55f, true);
                Instruments.Conga(congas, s.T(bar, 2.75), 0.5f, false);
                Instruments.Conga(congas, s.T(bar, 3.5), 0.55f, true);
                for (int e = 0; e < 8; e++) Instruments.Shaker(shaker, s.T(bar, e * 0.5), e % 2 == 1 ? 0.5f : 0.3f, bar * 8 + e);
                if (bar == 7 || bar == 15)
                    for (int k = 0; k < 4; k++) Instruments.Conga(congas, s.T(bar, 3 + k * 0.25), 0.4f + k * 0.08f, k % 2 == 0);
            }

            foreach (var n in s.Melody(0, 71, 86, new Random(330), Rhythms.Bouncy))
                Instruments.SteelPan(pan, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len), n.vel);
            foreach (var n in s.Melody(8, 74, 88, new Random(331), Rhythms.Dance))
            {
                Instruments.SteelPan(pan, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len), n.vel * 0.9f);
                Instruments.Marimba(marimba, s.T(n) + 0.004, Synth.MidiToHz(n.midi - 12), n.vel * 0.35f);
            }
            return mix.Render(Loudness);
        }

        static float[] Underpass()
        {
            // The railway underpass: dark and echoing. A pulsing synth bass, electric-piano stabs that ring
            // round the tunnel, a low pad, sixteenth hats and a rim, and a soft lead in the second half.
            var s = new Song(98, 0.05, 57, Mode.Minor, 44,
                "Am7", "Am7", "Fmaj7", "G", "Am7", "Am7", "Dm7", "E7",
                "Fmaj7", "G", "Em7", "Am7", "Dm7", "G", "Cmaj7", "E7");
            var mix = new Mixdown(s.Length) { roomSize = 0.88f, damping = 0.3f, wet = 0.34f };
            var bass = mix.Add(0f, 0.08f, 0.85f);
            var keys = mix.Add(-0.3f, 0.65f, 0.5f);
            var padL = mix.Add(-0.6f, 0.6f, 0.2f);
            var padR = mix.Add(0.6f, 0.6f, 0.2f);
            var lead = mix.Add(0.25f, 0.6f, 0.45f);
            var drums = mix.Add(0f, 0.2f, 0.7f);
            var hats = mix.Add(0.35f, 0.15f, 0.3f);

            for (int bar = 0; bar < Bars; bar++)
            {
                var ch = s.ChordsIn(bar)[0];
                int root = ch.chord.Bass(33);
                if (root < 31) root += 12;
                double[] at = { 0, 0.5, 1.5, 2, 2.75, 3.5 };
                int[] note = { root, root + 12, root, root, root + 12, root + 10 };
                for (int i = 0; i < at.Length; i++)
                    Instruments.SynthBass(bass, s.T(bar, at[i]), Synth.MidiToHz(note[i]), s.Beats(i == 0 ? 0.45 : 0.3), i == 0 ? 0.85f : 0.62f, i == 0 ? 1.0 : 0.6);
                var v = ch.chord.Voice(57, 72);
                Instruments.EPianoChord(keys, s.T(bar, 1.5), v, s.Beats(0.35), 0.5f, 0.006);
                Instruments.EPianoChord(keys, s.T(bar, 3), v, s.Beats(0.6), 0.42f, 0.006);
                Instruments.Pad(padL, s.T(bar, 0), ch.chord.Voice(45, 60), s.Beats(4), 0.45f, 650, bar * 2 + 1, 0.8);
                Instruments.Pad(padR, s.T(bar, 0), ch.chord.Voice(52, 64), s.Beats(4), 0.45f, 700, bar * 2 + 2, 0.8);

                Instruments.Kick(drums, s.T(bar, 0), 0.85f);
                Instruments.Kick(drums, s.T(bar, 1.75), 0.5f);
                Instruments.Kick(drums, s.T(bar, 2.5), 0.65f);
                Instruments.Snare(drums, s.T(bar, 1), 0.38f, bar * 2, 1.1);
                Instruments.Snare(drums, s.T(bar, 3), 0.42f, bar * 2 + 1, 1.1);
                for (int sx = 0; sx < 16; sx++)
                {
                    bool open = sx == 14 && bar % 2 == 1;
                    Instruments.Hat(hats, s.T(bar, sx * 0.25), sx % 4 == 2 ? 0.45f : sx % 2 == 0 ? 0.3f : 0.18f, bar * 16 + sx, open);
                }
                if (bar % 2 == 0) Instruments.Rim(drums, s.T(bar, 3.75), 0.3f);
                if (bar == 7 || bar == 15)
                    for (int k = 0; k < 4; k++) Instruments.Snare(drums, s.T(bar, 3 + k * 0.25), 0.18f + k * 0.08f, 400 + bar + k, 1.1);
            }

            foreach (var n in s.Melody(0, 69, 81, new Random(440), Rhythms.Sparse))
                Instruments.EPiano(lead, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len), n.vel * 0.6f);
            foreach (var n in s.Melody(8, 69, 84, new Random(441), Rhythms.Singing))
                Instruments.SquareLead(lead, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.9, n.vel * 0.8f);
            return mix.Render(Loudness);
        }

        static float[] Site()
        {
            // The building site: a bouncy work-song in D dorian. A busy picked bass, clavinet-like
            // stabs, a square-wave whistling tune (doubled on glockenspiel in the second half), claps,
            // a shaker and an anvil ringing on the off-beats like a hammer on steel.
            var s = new Song(112, 0, 62, Mode.Dorian, 55,
                "Dm7", "G", "Dm7", "G", "F", "C", "G", "Dm7",
                "Bb", "C", "Dm7", "Dm7", "Bb", "C", "A7sus4", "A7");
            var mix = new Mixdown(s.Length) { roomSize = 0.45f, damping = 0.5f, wet = 0.18f };
            var bass = mix.Add(0f, 0.05f, 0.9f);
            var clav = mix.Add(-0.35f, 0.15f, 0.55f);
            var lead = mix.Add(0.2f, 0.25f, 0.55f);
            var glock = mix.Add(0.4f, 0.3f, 0.35f);
            var pad = mix.Add(0f, 0.45f, 0.14f);
            var drums = mix.Add(0f, 0.12f, 0.75f);
            var anvil = mix.Add(0.5f, 0.35f, 0.4f);
            var shaker = mix.Add(-0.45f, 0.1f, 0.3f);

            for (int bar = 0; bar < Bars; bar++)
            {
                var ch = s.ChordsIn(bar)[0];
                int root = ch.chord.Bass(38);
                if (root > 45) root -= 12;
                int[] line = { root, root, root + 12, root, root + 7, root, root + 10, root + 12 };
                for (int e = 0; e < 8; e++)
                {
                    if (e == 3) continue;   // a breath in the line
                    Instruments.PluckBass(bass, s.T(bar, e * 0.5), Synth.MidiToHz(line[e]), s.Beats(0.38), e % 2 == 0 ? 0.8f : 0.6f, bar * 8 + e);
                }
                var v = ch.chord.Voice(60, 74);
                foreach (double b in new[] { 0.5, 1.5, 2.75, 3.5 })
                    Instruments.Strum(clav, s.T(bar, b), v, s.Beats(0.18), 0.45f, bar * 21 + (int)(b * 4), true, 0.003, 0.95f);
                Instruments.Pad(pad, s.T(bar, 0), ch.chord.Voice(50, 62), s.Beats(4), 0.4f, 900, bar + 11);

                Instruments.Kick(drums, s.T(bar, 0), 0.85f);
                Instruments.Kick(drums, s.T(bar, 2), 0.75f);
                Instruments.Kick(drums, s.T(bar, 2.5), 0.5f);
                Instruments.Clap(drums, s.T(bar, 1), 0.55f, bar * 2);
                Instruments.Clap(drums, s.T(bar, 3), 0.6f, bar * 2 + 1);
                Instruments.Anvil(anvil, s.T(bar, 1.5), 0.5f, 1.0);
                Instruments.Anvil(anvil, s.T(bar, 3.75), 0.38f, bar % 2 == 0 ? 1.19 : 1.12);
                for (int e = 0; e < 8; e++) Instruments.Shaker(shaker, s.T(bar, e * 0.5), e % 2 == 1 ? 0.5f : 0.3f, bar * 8 + e);
                if (bar == 7 || bar == 15)
                    for (int k = 0; k < 4; k++) Instruments.Anvil(anvil, s.T(bar, 3 + k * 0.25), 0.25f + k * 0.08f, 1.0 + k * 0.06);
            }

            foreach (var n in s.Melody(0, 69, 83, new Random(550), Rhythms.Bouncy))
                Instruments.SquareLead(lead, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.7, n.vel);
            foreach (var n in s.Melody(8, 69, 84, new Random(551), Rhythms.Dance))
            {
                Instruments.SquareLead(lead, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.7, n.vel * 0.85f);
                Instruments.Glock(glock, s.T(n), Synth.MidiToHz(n.midi + 12), n.vel * 0.6f, 4);
            }
            return mix.Render(Loudness);
        }

        static float[] Park()
        {
            // The park, the last stretch to school: harp arpeggios, a string section, a flute melody,
            // celesta joining the flute in the second half, a warm bass and soft brushes.
            var s = new Song(88, 0, 63, Mode.Major, 66,
                "Eb", "Bb/D", "Cm", "Ab", "Eb", "Bb", "Ab", "Bb",
                "Ab", "Bb", "Gm", "Cm", "Ab", "Bb", "Eb/G", "Ab Bb");
            var mix = new Mixdown(s.Length) { roomSize = 0.78f, damping = 0.45f, wet = 0.3f };
            var harp = mix.Add(-0.35f, 0.4f, 0.6f);
            var stringsL = mix.Add(-0.55f, 0.55f, 0.32f);
            var stringsR = mix.Add(0.55f, 0.55f, 0.32f);
            var flute = mix.Add(0.15f, 0.4f, 0.6f);
            var celesta = mix.Add(0.4f, 0.45f, 0.3f);
            var bass = mix.Add(0f, 0.1f, 0.8f);
            var drums = mix.Add(0f, 0.2f, 0.5f);
            var shaker = mix.Add(0.45f, 0.15f, 0.28f);

            for (int bar = 0; bar < Bars; bar++)
            {
                var chords = s.ChordsIn(bar);
                foreach (var ch in chords)
                {
                    var arp = ch.chord.Voice(55, 79, 7);
                    int steps = (int)(ch.length * 2);
                    for (int e = 0; e < steps; e++)
                    {
                        int k = e % (2 * arp.Length - 2 > 0 ? 2 * arp.Length - 2 : 1);
                        int idx = k < arp.Length ? k : 2 * arp.Length - 2 - k;
                        Instruments.Pluck(harp, s.T(bar, ch.beat + e * 0.5), Synth.MidiToHz(arp[idx]), s.Beats(1.5), 0.42f, bar * 50 + e, 0.65f, 0.998f);
                    }
                    Instruments.Strings(stringsL, s.T(bar, ch.beat), ch.chord.Voice(51, 65), s.Beats(ch.length), 0.55f, bar * 2 + 1);
                    Instruments.Strings(stringsR, s.T(bar, ch.beat), ch.chord.Voice(58, 72), s.Beats(ch.length), 0.5f, bar * 2 + 2);
                    int root = ch.chord.Bass(39);
                    if (root > 46) root -= 12;
                    Instruments.RoundBass(bass, s.T(bar, ch.beat), Synth.MidiToHz(root), s.Beats(Math.Min(ch.length, 2) - 0.2), 0.8f);
                    if (ch.length >= 4) Instruments.RoundBass(bass, s.T(bar, ch.beat + 2), Synth.MidiToHz(root + 7), s.Beats(1.6), 0.6f);
                }

                Instruments.Kick(drums, s.T(bar, 0), 0.5f, 0.9);
                Instruments.Kick(drums, s.T(bar, 2.5), 0.35f, 0.9);
                Instruments.Brush(drums, s.T(bar, 1), 0.5f, bar * 2, 0.2);
                Instruments.Brush(drums, s.T(bar, 3), 0.55f, bar * 2 + 1, 0.2);
                if (bar >= 8)
                    for (int e = 0; e < 8; e++) Instruments.Shaker(shaker, s.T(bar, e * 0.5), e % 2 == 1 ? 0.45f : 0.25f, bar * 8 + e);
                if (bar == 7 || bar == 15) Instruments.Brush(drums, s.T(bar, 3.5), 0.5f, 900 + bar, 0.3);
            }

            foreach (var n in s.Melody(0, 70, 84, new Random(660), Rhythms.Singing))
                Instruments.Flute(flute, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.95, n.vel, n.midi * 11);
            foreach (var n in s.Melody(8, 72, 87, new Random(661), Rhythms.Singing))
            {
                Instruments.Flute(flute, s.T(n), Synth.MidiToHz(n.midi), s.Beats(n.len) * 0.95, n.vel, n.midi * 17);
                if (n.beat % 1.0 == 0) Instruments.Glock(celesta, s.T(n), Synth.MidiToHz(n.midi + 12), n.vel * 0.5f, 3);
            }
            return mix.Render(Loudness);
        }

        /// <summary>The highest <paramref name="count"/> notes of a voicing (an up-strum catches the top strings).</summary>
        static int[] Top(int[] voicing, int count)
        {
            if (voicing.Length <= count) return voicing;
            var top = new int[count];
            Array.Copy(voicing, voicing.Length - count, top, 0, count);
            return top;
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

            /// <summary>Every chord tone between <paramref name="lo"/> and <paramref name="hi"/>, at most <paramref name="max"/> of them (from the bottom).</summary>
            public int[] Voice(int lo, int hi, int max = 4)
            {
                var list = new List<int>();
                for (int m = lo; m <= hi && list.Count < max; m++)
                    if (Has(m)) list.Add(m);
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
