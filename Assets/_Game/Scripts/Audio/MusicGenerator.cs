using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// The music, in the style of the country the streets are in (<see cref="MusicCountry"/>): for the original
    /// town (Kamakura, Japan) bright Japanese city pop and J-pop on the "royal road" chords, with pentatonic
    /// (yonanuki) tunes on a koto-like pluck, a breathy bamboo flute, Rhodes and a glockenspiel (see
    /// <see cref="JapanStyleOf"/>); for the California add-on the sunny, upbeat Californian West Coast styles
    /// below. One 16-bar loop for each soundscape, every one original. Jangly clean electric guitars and strummed acoustics, a twangy surf guitar through spring
    /// reverb, a combo organ, Rhodes, the West Coast synth whistle, soft "ooh" harmonies, a picked bass, and
    /// live-feeling drums with claps, tambourine and a crash to open each half. Per place: a laid-back
    /// fingerpicked sunset for the menu, jangly beach pop on Home Street, West Coast funk in the market,
    /// driving surf rock at the beach, a smooth West Coast groove in the underpass, garage surf on the
    /// building site, and sunny folk-pop in the park. Each loop has two halves (A and B) with their own chords
    /// and lead, a melody built from motifs that come back, and a fill into each half; the mix stays warm
    /// (no distortion, the highs gently rolled off). Deterministic, seamless when looped (notes and the
    /// reverb's tail wrap round), pure C#: safe on a worker thread. Output: interleaved stereo at
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
            return Generate(scape, MusicCountry.Japan);
        }

        /// <summary>The loop for a place, in the style of the country its streets are in.</summary>
        public static float[] Generate(Soundscape scape, MusicCountry country)
        {
            return Arrange(country == MusicCountry.California ? StyleOf(scape) : JapanStyleOf(scape));
        }

        // ================= Styles =================

        enum Comp { None, Jangle, Acoustic, Fingerpick, Palm, Funk, Rhodes, RhodesHeld, Organ }
        enum Lead { Surf, Whistle, Glock, Guitar, Acoustic, Rhodes, Koto, Flute }
        enum Kit { Pop, Surf, Funk, WestCoast, Folk }
        enum Bass { Pick, Sub }

        sealed class Style
        {
            public double bpm, swing;
            public int key, seed;
            public Mode mode;
            public string[] chords;
            public Comp comp, comp2;
            public bool comp2OnlyInB;
            public Lead leadA, leadB;
            public int leadLo = 69, leadHi = 83;
            public float leadSend = 0.35f;
            public Bass bass;
            public Kit kit;
            public bool oohs, claps, tambourine;
            public float room = 0.55f, wet = 0.22f, vinyl;
            public double tone = 7000;
        }

        /// <summary>
        /// The original town's music (Kamakura, a seaside town south of Tokyo): Japanese city pop and J-pop.
        /// Most of it turns on the "royal road" (IVmaj7 - V7 - iiim7 - vim7) and its relatives, with
        /// pentatonic yonanuki tunes (no fourth, no seventh) on a koto-like pluck or a breathy bamboo flute.
        /// </summary>
        static Style JapanStyleOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street:
                    // A bright J-pop morning: jangly guitars on the royal road, a koto tune, then a glockenspiel over "ooh"s.
                    return new Style
                    {
                        bpm = 122, swing = 0, key = 62, mode = Mode.Yona, seed = 111,
                        chords = new[] { "Gmaj7", "A7", "F#m7", "Bm7", "Gmaj7", "A7", "D", "D",
                                         "Gmaj7", "A7", "F#m7", "Bm7", "Em7", "F#m7", "Gmaj7", "A7sus4" },
                        comp = Comp.Jangle, comp2 = Comp.Rhodes, comp2OnlyInB = true, leadA = Lead.Koto, leadB = Lead.Glock,
                        leadLo = 69, leadHi = 86, bass = Bass.Pick, kit = Kit.Pop, oohs = true, claps = true, tambourine = true,
                    };
                case Soundscape.Market:
                    // Shopping-street city pop: Rhodes and sixteenth guitar chops, a slinky bass, a synth lead.
                    return new Style
                    {
                        bpm = 112, swing = 0.04, key = 65, mode = Mode.Yona, seed = 122,
                        chords = new[] { "Bbmaj7", "A7", "Dm7", "Dm7", "Bbmaj7", "C7", "Am7", "Dm7",
                                         "Gm7", "C7", "Fmaj7", "Dm7", "Bbmaj7", "C7", "Am7", "A7" },
                        comp = Comp.Rhodes, comp2 = Comp.Funk, leadA = Lead.Koto, leadB = Lead.Whistle,
                        leadLo = 67, leadHi = 84, bass = Bass.Pick, kit = Kit.Funk, claps = true,
                        room = 0.45f, wet = 0.18f,
                    };
                case Soundscape.Beach:
                    // Shonan summer: a driving beach pop on the royal road, an organ in the second half, guitar then flute.
                    return new Style
                    {
                        bpm = 130, swing = 0, key = 64, mode = Mode.Yona, seed = 133,
                        chords = new[] { "Amaj7", "B7", "G#m7", "C#m7", "Amaj7", "B7", "E", "E",
                                         "Amaj7", "B7", "G#m7", "C#m7", "F#m7", "B7", "E", "B7" },
                        comp = Comp.Jangle, comp2 = Comp.Organ, comp2OnlyInB = true, leadA = Lead.Guitar, leadB = Lead.Flute,
                        leadLo = 66, leadHi = 83, leadSend = 0.5f, bass = Bass.Pick, kit = Kit.Pop, tambourine = true, claps = true,
                        room = 0.7f, wet = 0.24f,
                    };
                case Soundscape.Underpass:
                    // Night city pop under the railway: held Rhodes, a deep sub, a gliding synth then the flute, the tunnel's echo.
                    return new Style
                    {
                        bpm = 96, swing = 0.06, key = 57, mode = Mode.YonaMinor, seed = 144,
                        chords = new[] { "Fmaj9", "E7", "Am9", "Am9", "Dm9", "G13", "Cmaj9", "E7",
                                         "Fmaj9", "E7", "Am9", "Gm7", "Fmaj9", "Em9", "Dm9", "E7" },
                        comp = Comp.RhodesHeld, comp2 = Comp.Funk, comp2OnlyInB = true, leadA = Lead.Whistle, leadB = Lead.Flute,
                        leadLo = 69, leadHi = 84, leadSend = 0.45f, bass = Bass.Sub, kit = Kit.WestCoast, claps = true,
                        room = 0.85f, wet = 0.3f, tone = 6000, vinyl = 0.4f,
                    };
                case Soundscape.Site:
                    // Busy and upbeat: palm-muted eighths, an organ, a twangy guitar tune then the koto.
                    return new Style
                    {
                        bpm = 126, swing = 0, key = 62, mode = Mode.Yona, seed = 155,
                        chords = new[] { "Bm7", "Gmaj7", "A7", "D", "Bm7", "Gmaj7", "Em7", "A7",
                                         "Gmaj7", "A7", "F#m7", "Bm7", "Gmaj7", "A7", "D", "A7" },
                        comp = Comp.Palm, comp2 = Comp.Organ, comp2OnlyInB = true, leadA = Lead.Guitar, leadB = Lead.Koto,
                        leadLo = 66, leadHi = 83, leadSend = 0.5f, bass = Bass.Pick, kit = Kit.Surf, claps = true,
                        room = 0.6f, wet = 0.22f,
                    };
                case Soundscape.Park:
                    // A gentle J-pop afternoon: strummed acoustic, the flute's tune then the koto, "ooh"s, claps and a shaker.
                    return new Style
                    {
                        bpm = 104, swing = 0, key = 67, mode = Mode.Yona, seed = 166,
                        chords = new[] { "Cmaj7", "D7", "Bm7", "Em7", "Cmaj7", "D7", "G", "G",
                                         "Am7", "Bm7", "Cmaj7", "D7", "Cmaj7", "D7", "G", "D7sus4" },
                        comp = Comp.Acoustic, comp2 = Comp.Fingerpick, comp2OnlyInB = true, leadA = Lead.Flute, leadB = Lead.Koto,
                        leadLo = 69, leadHi = 86, bass = Bass.Pick, kit = Kit.Folk, oohs = true, claps = true, tambourine = true,
                        room = 0.6f, wet = 0.24f,
                    };
                default:
                    // The menu: evening by the sea in Kamakura. Fingerpicked guitar and Rhodes, a laid-back beat, the koto then the flute.
                    return new Style
                    {
                        bpm = 92, swing = 0.06, key = 57, mode = Mode.Yona, seed = 107,
                        chords = new[] { "Dmaj7", "E7", "C#m7", "F#m7", "Dmaj7", "E7", "A", "A",
                                         "Bm7", "C#m7", "Dmaj7", "E7", "Dmaj7", "C#m7", "Bm7", "E7sus4" },
                        comp = Comp.Fingerpick, comp2 = Comp.RhodesHeld, leadA = Lead.Koto, leadB = Lead.Flute,
                        leadLo = 69, leadHi = 84, bass = Bass.Pick, kit = Kit.Folk, oohs = true,
                        room = 0.65f, wet = 0.26f, tone = 6500,
                    };
            }
        }

        /// <summary>The California add-on's music: West Coast styles.</summary>
        static Style StyleOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street:
                    // Jangly beach pop on a bright morning: strummed clean guitars, claps and tambourine, a clean
                    // guitar tune, then a glockenspiel over "ooh"s and an organ.
                    return new Style
                    {
                        bpm = 118, swing = 0, key = 62, mode = Mode.Major, seed = 11,
                        chords = new[] { "D", "A", "Bm", "G", "D", "A", "G", "A",
                                         "G", "A", "F#m", "Bm", "G", "A", "Em7", "A" },
                        comp = Comp.Jangle, comp2 = Comp.Organ, comp2OnlyInB = true, leadA = Lead.Guitar, leadB = Lead.Glock,
                        bass = Bass.Pick, kit = Kit.Pop, oohs = true, claps = true, tambourine = true,
                    };
                case Soundscape.Market:
                    // West Coast funk: Rhodes stabs, sixteenth guitar chops, a picked bass, a tight kit.
                    return new Style
                    {
                        bpm = 106, swing = 0.06, key = 65, mode = Mode.Major, seed = 22,
                        chords = new[] { "Gm7", "C7", "Fmaj7", "Dm7", "Gm7", "C7", "Am7", "D7",
                                         "Bbmaj7", "Am7", "Gm7", "C7", "Bbmaj7", "A7", "Dm7", "C7" },
                        comp = Comp.Rhodes, comp2 = Comp.Funk, leadA = Lead.Guitar, leadB = Lead.Whistle,
                        leadLo = 67, leadHi = 81, bass = Bass.Pick, kit = Kit.Funk, claps = true, tambourine = true,
                        room = 0.45f, wet = 0.18f,
                    };
                case Soundscape.Beach:
                    // Surf rock: palm-muted rhythm guitar driving the eighths, a twangy tremolo-picked lead through
                    // spring reverb, an organ in the second half, the kit pounding along.
                    return new Style
                    {
                        bpm = 132, swing = 0, key = 64, mode = Mode.Major, seed = 33,
                        chords = new[] { "E", "A", "B", "A", "E", "C#m", "A", "B",
                                         "A", "B", "G#m", "C#m", "A", "B", "E", "B" },
                        comp = Comp.Palm, comp2 = Comp.Organ, comp2OnlyInB = true, leadA = Lead.Surf, leadB = Lead.Surf,
                        leadLo = 64, leadHi = 79, leadSend = 0.75f, bass = Bass.Pick, kit = Kit.Surf, tambourine = true,
                        room = 0.75f, wet = 0.26f,
                    };
                case Soundscape.Underpass:
                    // A smooth West Coast groove: held Rhodes chords, a gliding synth whistle, a deep sub, claps on
                    // the snare and swung sixteenth hats, the tunnel's echo.
                    return new Style
                    {
                        bpm = 94, swing = 0.08, key = 57, mode = Mode.Minor, seed = 44,
                        chords = new[] { "Am9", "Am9", "Fmaj9", "E7", "Am9", "Dm9", "Bm7b5", "E7",
                                         "Fmaj9", "G13", "Em9", "Am9", "Dm9", "G13", "Cmaj9", "E7" },
                        comp = Comp.RhodesHeld, comp2 = Comp.Funk, comp2OnlyInB = true, leadA = Lead.Whistle, leadB = Lead.Whistle,
                        leadLo = 72, leadHi = 86, leadSend = 0.45f, bass = Bass.Sub, kit = Kit.WestCoast, claps = true,
                        room = 0.85f, wet = 0.3f, tone = 6000, vinyl = 0.5f,
                    };
                case Soundscape.Site:
                    // Garage surf for the building site: palm-muted eighths, jangly chords in the second half, an organ,
                    // a twangy lead then a glockenspiel, the kit driving.
                    return new Style
                    {
                        bpm = 126, swing = 0, key = 62, mode = Mode.Mixolydian, seed = 55,
                        chords = new[] { "D", "C", "G", "D", "D", "C", "G", "A",
                                         "Bm", "G", "D", "A", "Bm", "G", "Em7", "A" },
                        comp = Comp.Palm, comp2 = Comp.Jangle, comp2OnlyInB = true, leadA = Lead.Surf, leadB = Lead.Guitar,
                        leadLo = 66, leadHi = 81, leadSend = 0.6f, bass = Bass.Pick, kit = Kit.Surf, claps = true,
                        room = 0.6f, wet = 0.22f,
                    };
                case Soundscape.Park:
                    // Sunny folk-pop: strummed acoustic, "ooh"s, a glockenspiel tune then a clean guitar, claps and a shaker.
                    return new Style
                    {
                        bpm = 112, swing = 0, key = 67, mode = Mode.Major, seed = 66,
                        chords = new[] { "G", "D/F#", "Em", "C", "G", "D", "C", "D",
                                         "C", "D", "Bm", "Em", "C", "D", "G", "D" },
                        comp = Comp.Acoustic, comp2 = Comp.Fingerpick, comp2OnlyInB = true, leadA = Lead.Glock, leadB = Lead.Guitar,
                        leadLo = 71, leadHi = 86, bass = Bass.Pick, kit = Kit.Folk, oohs = true, claps = true, tambourine = true,
                        room = 0.6f, wet = 0.24f,
                    };
                default:
                    // The menu: a sunset on the pier. Fingerpicked acoustic, an organ underneath, a laid-back beat,
                    // an acoustic tune then the whistle.
                    return new Style
                    {
                        bpm = 96, swing = 0.06, key = 57, mode = Mode.Major, seed = 7,
                        chords = new[] { "A", "E/G#", "F#m", "D", "A", "E", "D", "E",
                                         "D", "E", "C#m", "F#m", "D", "E", "Bm7", "E" },
                        comp = Comp.Fingerpick, comp2 = Comp.Organ, leadA = Lead.Acoustic, leadB = Lead.Whistle,
                        leadLo = 69, leadHi = 83, bass = Bass.Pick, kit = Kit.Folk, oohs = true,
                        room = 0.65f, wet = 0.26f, tone = 6500,
                    };
            }
        }

        // ================= The arranger =================

        static float[] Arrange(Style st)
        {
            var s = new Song(st.bpm, st.swing, st.key, st.mode, st.seed, st.chords);
            var rng = new Random(st.seed * 31);
            var mix = new Mixdown(s.Length)
            {
                roomSize = st.room, damping = 0.55f, wet = st.wet, tone = st.tone, drive = 0.08f,
            };
            var gtr = mix.Add(-0.4f, 0.3f, 0.7f);
            var gtr2 = mix.Add(0.42f, 0.3f, 0.55f);
            var organ = mix.Add(0.15f, 0.35f, 0.5f);
            var oohs = mix.Add(0f, 0.55f, 0.4f);
            var bass = mix.Add(0f, 0.04f, 0.9f);
            var lead = mix.Add(0.12f, st.leadSend, 0.5f);
            var kick = mix.Add(0f, 0.04f, 1f);
            var snare = mix.Add(0.04f, 0.18f, 0.7f);
            var hats = mix.Add(0.3f, 0.06f, 0.3f);
            var perc = mix.Add(-0.45f, 0.12f, 0.35f);
            var vinyl = mix.Add(0f, 0f, 0.5f * st.vinyl);
            gtr.duck = gtr2.duck = organ.duck = oohs.duck = 0.15f;

            for (int bar = 0; bar < Bars; bar++)
            {
                bool inB = bar >= Bars / 2;
                bool fill = bar == Bars / 2 - 1 || bar == Bars - 1;
                foreach (var ch in s.ChordsIn(bar))
                {
                    Play(st.comp, st.comp == Comp.Organ ? organ : gtr, s, bar, ch, rng, 1f);
                    if (st.comp2 != Comp.None && (!st.comp2OnlyInB || inB))
                        Play(st.comp2, st.comp2 == Comp.Organ ? organ : gtr2, s, bar, ch, rng, 0.75f);
                    if (st.oohs && (inB || st.comp2 == Comp.None || !st.comp2OnlyInB))
                        Instruments.Oohs(oohs, s.T(bar, ch.beat), ch.chord.Voice(60, 72, 3), s.Beats(ch.length), 0.6f, bar * 7 + 1);
                    BassLine(st, bass, s, bar, ch, fill);
                }
                Drums(st, s, mix, kick, snare, hats, perc, bar, inB, fill, rng);
            }
            if (st.vinyl > 0f) Instruments.Vinyl(vinyl, 1f, st.seed);

            double prev = Synth.MidiToHz(st.leadLo + 5);
            foreach (var n in s.Melody(0, st.leadLo, st.leadHi, new Random(st.seed * 10), Rhythms.Bouncy))
                prev = PlayLead(st.leadA, lead, s, n, prev);
            foreach (var n in s.Melody(8, st.leadLo + 2, st.leadHi + 2, new Random(st.seed * 10 + 1), Rhythms.Singing))
                prev = PlayLead(st.leadB, lead, s, n, prev);
            return mix.Render(Loudness);
        }

        static void BassNote(Style st, Track bass, Song s, int bar, double beat, int midi, double beats, float vel, int seed)
        {
            if (st.bass == Bass.Sub) Instruments.SubBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel);
            else Instruments.PickBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel, seed);
        }

        /// <summary>The bass line for one chord, in the kit's style: pop's root-and-fifth push, surf's driving
        /// eighths, funk's syncopated octaves; and a step into the next chord at the end of every other bar.</summary>
        static void BassLine(Style st, Track bass, Song s, int bar, ChordAt ch, bool fill)
        {
            int root = ch.chord.Bass(36);
            if (root > 43) root -= 12;
            double[] at;
            int[] line;
            double len;
            switch (st.kit)
            {
                case Kit.Surf:
                    at = new[] { 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5 };
                    line = new[] { root, root, root, root, root + 7, root + 7, root + 12, root + 7 };
                    len = 0.45;
                    break;
                case Kit.Funk:
                case Kit.WestCoast:
                    at = new[] { 0, 0.75, 1.5, 2.5, 2.75, 3.5 };
                    line = new[] { root, root + 12, root, root, root + 12, root + 7 };
                    len = 0.4;
                    break;
                default:
                    at = new[] { 0, 1.5, 2, 3, 3.5 };
                    line = new[] { root, root, root + 7, root, root + 7 };
                    len = 0.7;
                    break;
            }
            for (int k = 0; k < at.Length; k++)
            {
                if (at[k] >= ch.length) break;
                BassNote(st, bass, s, bar, ch.beat + at[k], line[k], k == 0 ? len * 1.3 : len, k == 0 ? 0.9f : 0.7f, bar * 8 + k);
            }
            if (ch.length >= 4 && bar % 2 == 1 && !fill)
            {
                int next = s.ChordsIn(bar + 1)[0].chord.Bass(36);
                if (next > 43) next -= 12;
                BassNote(st, bass, s, bar, ch.beat + 3.75, next + (next > root ? -2 : 2), 0.25, 0.55f, bar * 8 + 7);
            }
        }

        static void Play(Comp comp, Track tr, Song s, int bar, ChordAt ch, Random rng, float level)
        {
            double span = ch.length;
            switch (comp)
            {
                case Comp.Jangle:
                case Comp.Acoustic:
                {
                    // Down, down-up, up-down-up: the strum every sunny pop song is built on.
                    var v = ch.chord.Voice(52, 69, 5);
                    double[] at = { 0, 1, 1.5, 2.5, 3, 3.5 };
                    bool[] down = { true, true, false, false, true, false };
                    for (int i = 0; i < at.Length; i++)
                    {
                        if (at[i] >= span) break;
                        double next = i + 1 < at.Length ? at[i + 1] : 4;
                        var notes = down[i] ? v : Top(v, 3);
                        if (comp == Comp.Jangle)
                            Instruments.Jangle(tr, s.T(bar, ch.beat + at[i]), notes, s.Beats(next - at[i] + 0.1), (down[i] ? 0.6f : 0.42f) * level, bar * 40 + i * 5, down[i]);
                        else
                            Instruments.Strum(tr, s.T(bar, ch.beat + at[i]), down[i] ? notes : Reverse(notes), s.Beats(next - at[i] + 0.2), (down[i] ? 0.65f : 0.45f) * level, bar * 40 + i * 5, down[i] ? 0.013 : 0.009, 0.45f);
                    }
                    break;
                }
                case Comp.Fingerpick:
                {
                    // Travis picking: the thumb alternating bass notes on the beat, the fingers on the off-beats.
                    var v = ch.chord.Voice(55, 74, 4);
                    int low = ch.chord.Bass(45);
                    for (int b = 0; b < span; b++)
                    {
                        int thumb = b % 2 == 0 ? low : low + 7;
                        Instruments.Pluck(tr, s.T(bar, ch.beat + b), Synth.MidiToHz(thumb), s.Beats(1), 0.5f * level, bar * 30 + b, 0.35f);
                        if (v.Length > 0)
                            Instruments.Pluck(tr, s.T(bar, ch.beat + b + 0.5), Synth.MidiToHz(v[(b * 2 + 1) % v.Length]), s.Beats(1), 0.42f * level, bar * 30 + b + 9, 0.45f);
                        if (b % 2 == 1 && v.Length > 1)
                            Instruments.Pluck(tr, s.T(bar, ch.beat + b), Synth.MidiToHz(v[v.Length - 1]), s.Beats(1), 0.36f * level, bar * 30 + b + 17, 0.45f);
                    }
                    break;
                }
                case Comp.Palm:
                {
                    // Palm-muted power chords chugging on the eighths, an open accent on the one and the "and" of two.
                    int root = ch.chord.Bass(40);
                    var power = new[] { root, root + 7, root + 12 };
                    for (int e = 0; e < span * 2; e++)
                    {
                        bool accent = e == 0 || e == 3;
                        Instruments.Jangle(tr, s.T(bar, ch.beat + e * 0.5), power, s.Beats(accent ? 0.45 : 0.2), (accent ? 0.62f : 0.48f) * level, bar * 20 + e, true, !accent);
                    }
                    break;
                }
                case Comp.Funk:
                {
                    // Sixteenth-note chops high on the neck: short, muted, pushing the groove.
                    var v = ch.chord.Voice(64, 79, 3, true);
                    double[] at = { 0.5, 0.75, 1.5, 2.25, 2.5, 3.5, 3.75 };
                    foreach (double b in at)
                    {
                        if (b >= span || rng.NextDouble() < 0.12) continue;
                        Instruments.Jangle(tr, s.T(bar, ch.beat + b), v, s.Beats(0.15), 0.5f * level, bar * 50 + (int)(b * 4), true, true);
                    }
                    break;
                }
                case Comp.Rhodes:
                {
                    var v = ch.chord.Voice(55, 74, 4, true);
                    double[] at = bar % 2 == 0 ? new[] { 0, 1.5, 2.75, 3.5 } : new[] { 0, 0.75, 2, 3.5 };
                    for (int k = 0; k < at.Length; k++)
                        if (at[k] < span)
                            Instruments.RhodesChord(tr, s.T(bar, ch.beat + at[k]), v, s.Beats(k == 0 ? 0.9 : 0.45), (k == 0 ? 0.55f : 0.42f) * level, 0.008);
                    break;
                }
                case Comp.RhodesHeld:
                    Instruments.RhodesChord(tr, s.T(bar, ch.beat), ch.chord.Voice(55, 74, 4, true), s.Beats(span - 0.1), 0.55f * level, 0.018);
                    break;
                case Comp.Organ:
                    Instruments.Organ(tr, s.T(bar, ch.beat), ch.chord.Voice(55, 70, 3), s.Beats(span - 0.05), 0.75f * level);
                    break;
            }
        }

        static double PlayLead(Lead lead, Track tr, Song s, Note n, double prevFreq)
        {
            double t = s.T(n), d = s.Beats(n.len);
            double f = Synth.MidiToHz(n.midi);
            float v = n.vel;
            switch (lead)
            {
                case Lead.Surf: Instruments.SurfLead(tr, t, f, d, v, n.midi * 5 + (int)(n.beat * 4)); break;
                case Lead.Whistle: Instruments.Whistle(tr, t, f, prevFreq, d * 0.95, v * 0.85f); break;
                case Lead.Glock: Instruments.Glock(tr, t, f, v * 0.9f); break;
                case Lead.Guitar: Instruments.CleanGuitar(tr, t, f, d + 0.1, v * 0.9f, n.midi * 3 + (int)(n.beat * 4)); break;
                case Lead.Acoustic: Instruments.Pluck(tr, t, f, d + 0.2, v * 0.75f, n.midi * 3, 0.45f); break;
                // A koto-like pluck: bright and quick to fade, like a plucked silk string.
                case Lead.Koto: Instruments.Pluck(tr, t, f, d + 0.35, v * 0.8f, n.midi * 7 + (int)(n.beat * 4), 0.72f, 0.993f); break;
                // A breathy bamboo flute (shakuhachi-like).
                case Lead.Flute: Instruments.Flute(tr, t, f, d * 0.95, v * 0.8f, n.midi * 5 + (int)(n.beat * 4)); break;
                default: Instruments.Rhodes(tr, t, f, d, v * 0.65f); break;
            }
            return f;
        }

        /// <summary>
        /// A live-feeling kit in the place's style. Pop: four-to-the-bar feel with claps on the backbeat and
        /// tambourine on the off-beats. Surf: driving, the hats on every quaver, toms in the fill. Funk and West
        /// Coast: syncopated kicks, sixteenth hats (swung for the West Coast), ghost notes, an open hat. Folk:
        /// light in the first half (a side-stick and shaker), the full backbeat in the second. A crash opens
        /// each half, and a fill leads into it.
        /// </summary>
        static void Drums(Style st, Song s, Mixdown mix, Track kick, Track snare, Track hats, Track perc, int bar, bool inB, bool fill, Random rng)
        {
            double[] kicks;
            switch (st.kit)
            {
                case Kit.Surf: kicks = new[] { 0, 1.5, 2, 3.5 }; break;
                case Kit.Funk: kicks = bar % 2 == 0 ? new[] { 0, 0.75, 2.5, 2.75 } : new[] { 0, 1.75, 2.5 }; break;
                case Kit.WestCoast: kicks = bar % 2 == 0 ? new[] { 0, 0.75, 2.5 } : new[] { 0, 1.5, 2.75 }; break;
                case Kit.Folk: kicks = new[] { 0, 2, 2.5 }; break;
                default: kicks = bar % 2 == 0 ? new[] { 0, 1.5, 2 } : new[] { 0, 2, 2.5 }; break;
            }
            foreach (double k in kicks)
            {
                if (fill && k >= 3) continue;
                double t = s.T(bar, k);
                Instruments.Kick(kick, t, k == 0 ? 1f : 0.82f);
                mix.Duck(t, 0.5f, 0.1);
            }

            bool softFolk = st.kit == Kit.Folk && !inB;
            foreach (double b in new[] { 1.0, 3.0 })
            {
                if (fill && b >= 3) continue;
                double t = s.T(bar, b);
                if (softFolk) Instruments.Rim(snare, t, 0.75f);
                else Instruments.Snare(snare, t, 0.78f, bar * 4 + (int)b);
                if (st.claps && !softFolk) Instruments.Clap(perc, t + 0.004, 0.55f, bar * 4 + (int)b);
            }
            if ((st.kit == Kit.Funk || st.kit == Kit.WestCoast) && rng.NextDouble() < 0.7)
                Instruments.Snare(snare, s.T(bar, 3.75), 0.16f, 900 + bar);

            if (fill)
            {
                if (st.kit == Kit.Surf)
                    for (int k = 0; k < 4; k++) Instruments.Conga(perc, s.T(bar, 3 + k * 0.25), 0.7f, k < 2);   // toms rolling down
                else
                    for (int k = 0; k < 4; k++) Instruments.Snare(snare, s.T(bar, 3 + k * 0.25), 0.3f + k * 0.12f, 1100 + bar * 4 + k);
            }
            if (bar == 0 || bar == Bars / 2) Instruments.Crash(hats, s.T(bar, 0), 0.7f, bar);

            bool sixteenths = st.kit == Kit.Funk || st.kit == Kit.WestCoast || st.kit == Kit.Folk;
            int steps = sixteenths ? 16 : 8;
            for (int e = 0; e < steps; e++)
            {
                double b = e * 4.0 / steps;
                if (fill && b >= 3) break;
                bool onBeat = Math.Abs(b - Math.Round(b)) < 1e-6;
                float vel = onBeat ? 0.5f : (sixteenths && e % 2 == 1 ? 0.2f : 0.36f);
                vel *= (float)(0.85 + rng.NextDouble() * 0.3);
                if (st.kit == Kit.Folk) Instruments.Shaker(perc, s.T(bar, b), vel * 0.9f, bar * 16 + e);
                else Instruments.Hat(hats, s.T(bar, b), vel, bar * 16 + e);
                if (st.tambourine && !onBeat && Math.Abs(b * 2 - Math.Round(b * 2)) < 1e-6 && (inB || st.kit != Kit.Folk))
                    Instruments.Tambourine(perc, s.T(bar, b), 0.35f, bar * 16 + e);
            }
            if ((st.kit == Kit.Funk || st.kit == Kit.WestCoast || st.kit == Kit.Pop) && inB && !fill)
                Instruments.OpenHat(hats, s.T(bar, 3.5), 0.4f, bar);
        }

        /// <summary>The highest <paramref name="count"/> notes of a voicing (an up-strum catches the top strings).</summary>
        static int[] Top(int[] voicing, int count)
        {
            if (voicing.Length <= count) return voicing;
            var top = new int[count];
            Array.Copy(voicing, voicing.Length - count, top, 0, count);
            return top;
        }

        static int[] Reverse(int[] notes)
        {
            var r = (int[])notes.Clone();
            Array.Reverse(r);
            return r;
        }

        // ================= Theory =================

        /// <summary>Yona and YonaMinor: the Japanese pentatonic "yonanuki" scales (no fourth, no seventh), for the tunes.</summary>
        enum Mode { Major, Minor, Dorian, Mixolydian, Yona, YonaMinor }

        static readonly int[] YonaScale = { 0, 2, 4, 7, 9 };
        static readonly int[] YonaMinorScale = { 0, 2, 3, 7, 8 };

        static readonly int[] MajorScale = { 0, 2, 4, 5, 7, 9, 11 };
        static readonly int[] MinorScale = { 0, 2, 3, 5, 7, 8, 10 };
        static readonly int[] DorianScale = { 0, 2, 3, 5, 7, 9, 10 };
        static readonly int[] MixolydianScale = { 0, 2, 4, 5, 7, 9, 10 };

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
                scale = mode == Mode.Major ? MajorScale : mode == Mode.Minor ? MinorScale : mode == Mode.Dorian ? DorianScale
                    : mode == Mode.Yona ? YonaScale : mode == Mode.YonaMinor ? YonaMinorScale : MixolydianScale;
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
