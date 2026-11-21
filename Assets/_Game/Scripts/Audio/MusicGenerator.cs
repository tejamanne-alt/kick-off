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
            // Florida's own places play the music of the kind of place they are (Soundscapes.MusicOf).
            scape = Soundscapes.MusicOf(scape);
            // (the mix's work buffers are reused as it renders: Mixdown's Scratch)
            Scratch.Begin();
            try
            {
                switch (country)
                {
                    case MusicCountry.California: return Arrange(StyleOf(scape));
                    case MusicCountry.Florida: return Arrange(FloridaStyleOf(scape));
                    default: return Arrange(JapanStyleOf(scape));
                }
            }
            finally { Scratch.End(); }
        }

        // ================= Styles =================

        enum Comp { None, Jangle, Acoustic, Fingerpick, Palm, Funk, Rhodes, RhodesHeld, Organ, Skank, Montuno, OrganBubble, Chop, Pulse, Phaser }
        enum Lead { Surf, Whistle, Glock, Guitar, Acoustic, Rhodes, Koto, Flute, SteelPan, Marimba, Vibes, Saw, Psych, Pluck }
        enum Kit { Pop, Surf, Funk, WestCoast, Folk, Calypso, Son, OneDrop, Electro, Psych }
        enum Bass { Pick, Sub, Upright, Electro, Fuzz }

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
            /// <summary>How far the chords (and the bass) dip under each kick: the sidechain "pump" of dance music.</summary>
            public float pump = 0.15f, bassPump;
            /// <summary>The master's tape drive, and its wow (cents).</summary>
            public float drive = 0.08f, wow;
            /// <summary>The first half's tune on the dance rhythms (quavers, repeated notes) rather than the bouncy pop ones.</summary>
            public bool dance;
            /// <summary>
            /// A written tune instead of a made-up one: four bars each, sixteen semiquaver steps a bar ("A4", "C#5": a note
            /// starts; "_" holds it; "." rests). The first half plays <see cref="hookA"/> twice, the second <see cref="hookB"/> twice.
            /// </summary>
            public string[] hookA, hookB;
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

        /// <summary>
        /// The Florida add-on's music (v133): bright, driving Miami dance music in two flavours, all of it original. French
        /// electro and filter house (in the spirit of Justice) on the busy streets: four on the floor with a kick that pumps
        /// the mix, a growling bass on rolling octaves, filtered disco chord stabs and pumping quaver chords. Psychedelic
        /// synth-pop (in the spirit of Tame Impala) in the calmer places: a phased pad on warm major-seventh chords, a fuzzy
        /// melodic bass, big laid-back drums with a tambourine. Every loop is two four-bar chord cycles under a written hook
        /// (<see cref="Style.hookA"/>, <see cref="Style.hookB"/>): a riff that repeats, its strong beats on the chord's own
        /// notes, on synths that hold their pitch. All in major keys, 112 to 126 BPM. (v132's random tunes on gliding,
        /// wobbling leads were "still bad", and v122's Caribbean styles "sad": docs/LEARNINGS.md G3, G4.)
        /// </summary>
        static Style FloridaStyleOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street:
                    // Home Street, filter house on a sunny morning: a bouncing riff down the chords over a falling bass, the
                    // stabs opening up; then a sing-along line over the pumping chords.
                    return new Style
                    {
                        bpm = 122, swing = 0, key = 62, mode = Mode.Major, seed = 311,
                        chords = new[] { "D", "A/C#", "Bm7", "G", "D", "A/C#", "Bm7", "G",
                                         "G", "A", "Bm7", "D", "G", "A", "Bm7", "D" },
                        hookA = new[]
                        {
                            "A4 _ _ D5 _ _ F#5 _ _ E5 _ _ D5 _ A4 _",
                            "A4 _ _ C#5 _ _ E5 _ _ D5 _ _ C#5 _ A4 _",
                            "B4 _ _ D5 _ _ F#5 _ _ E5 _ _ D5 _ B4 _",
                            "B4 _ _ D5 _ _ G5 _ _ F#5 _ _ E5 _ D5 _",
                        },
                        hookB = new[]
                        {
                            "D5 _ _ _ _ _ B4 _ D5 _ E5 _ _ _ D5 _",
                            "C#5 _ _ _ _ _ A4 _ C#5 _ E5 _ _ _ C#5 _",
                            "D5 _ _ _ _ _ B4 _ D5 _ F#5 _ _ _ E5 _",
                            "D5 _ _ _ _ _ _ _ A4 _ _ _ . . . .",
                        },
                        comp = Comp.Chop, comp2 = Comp.Pulse, comp2OnlyInB = true, leadA = Lead.Pluck, leadB = Lead.Saw,
                        leadSend = 0.3f, bass = Bass.Electro, kit = Kit.Electro, claps = true,
                        room = 0.5f, wet = 0.18f, tone = 9000, pump = 0.4f, bassPump = 0.3f, drive = 0.2f,
                    };
                case Soundscape.Market:
                    // Disco-funk in the market: a chopped octave riff on I and ii-V, guitar chops in the second half under a
                    // long, climbing line.
                    return new Style
                    {
                        bpm = 118, swing = 0.03, key = 65, mode = Mode.Major, seed = 322,
                        chords = new[] { "Fmaj7", "Gm7 C", "Fmaj7", "Gm7 C", "Fmaj7", "Gm7 C", "Fmaj7", "Gm7 C",
                                         "Bbmaj7", "C", "Am7", "Dm7", "Bbmaj7", "C", "Am7", "Dm7" },
                        hookA = new[]
                        {
                            "C5 _ . C5 . A4 . C5 _ . D5 . C5 _ A4 _",
                            "Bb4 _ . Bb4 . G4 . Bb4 _ . C5 . E5 _ C5 _",
                            "C5 _ . C5 . A4 . C5 _ . D5 . C5 _ A4 _",
                            "Bb4 _ . Bb4 . G4 . Bb4 _ . C5 _ _ _ . .",
                        },
                        hookB = new[]
                        {
                            "D5 _ _ _ F5 _ _ _ A5 _ _ _ F5 _ D5 _",
                            "E5 _ _ _ G5 _ _ _ E5 _ _ _ D5 _ C5 _",
                            "C5 _ _ _ E5 _ _ _ A5 _ _ _ G5 _ E5 _",
                            "F5 _ _ _ _ _ _ _ D5 _ _ _ C5 _ A4 _",
                        },
                        comp = Comp.Chop, comp2 = Comp.Funk, comp2OnlyInB = true, leadA = Lead.Pluck, leadB = Lead.Saw,
                        leadSend = 0.3f, bass = Bass.Electro, kit = Kit.Electro, claps = true,
                        room = 0.45f, wet = 0.16f, tone = 9000, pump = 0.4f, bassPump = 0.25f, drive = 0.18f,
                    };
                case Soundscape.Beach:
                    // A beach anthem: a bouncing riff over pumping chords and "ooh"s, then a soaring line with the stabs.
                    return new Style
                    {
                        bpm = 124, swing = 0, key = 69, mode = Mode.Major, seed = 333,
                        chords = new[] { "A", "E", "F#m7", "D", "A", "E", "F#m7", "D",
                                         "D", "E", "C#m7 F#m7", "E", "D", "E", "C#m7 F#m7", "E" },
                        hookA = new[]
                        {
                            "E5 _ . E5 . C#5 _ . A4 _ . B4 C#5 _ E5 _",
                            "E5 _ . E5 . B4 _ . G#4 _ . A4 B4 _ E5 _",
                            "F#5 _ . F#5 . C#5 _ . A4 _ . B4 C#5 _ E5 _",
                            "F#5 _ . F#5 . D5 _ . A4 _ . B4 C#5 _ D5 _",
                        },
                        hookB = new[]
                        {
                            "A5 _ _ _ _ _ F#5 _ _ _ D5 _ E5 _ F#5 _",
                            "G#5 _ _ _ _ _ E5 _ _ _ B4 _ C#5 _ E5 _",
                            "E5 _ _ _ G#5 _ _ _ A5 _ _ _ F#5 _ E5 _",
                            "E5 _ _ _ _ _ _ _ B4 _ _ _ . . . .",
                        },
                        comp = Comp.Pulse, comp2 = Comp.Chop, comp2OnlyInB = true, leadA = Lead.Pluck, leadB = Lead.Saw,
                        leadSend = 0.35f, bass = Bass.Electro, kit = Kit.Electro, claps = true, oohs = true,
                        room = 0.6f, wet = 0.2f, tone = 9500, pump = 0.45f, bassPump = 0.3f, drive = 0.18f,
                    };
                case Soundscape.Site:
                    // The building site, the hardest of them: a stabbing repeated-note riff, then a line falling through the
                    // chords over the pump.
                    return new Style
                    {
                        bpm = 126, swing = 0, key = 67, mode = Mode.Major, seed = 355,
                        chords = new[] { "G", "G/F#", "Em7", "C", "G", "G/F#", "Em7", "C",
                                         "Am7", "C", "G", "D", "Am7", "C", "G", "D" },
                        hookA = new[]
                        {
                            "D5 . D5 . B4 . D5 . G5 _ . D5 . B4 . .",
                            "D5 . D5 . B4 . D5 . G5 _ . F#5 . D5 . .",
                            "E5 . E5 . B4 . E5 . G5 _ . E5 . D5 . .",
                            "E5 . E5 . C5 . E5 . G5 _ . E5 . D5 . .",
                        },
                        hookB = new[]
                        {
                            "C5 _ _ _ E5 _ _ _ A5 _ _ _ G5 _ E5 _",
                            "G5 _ _ _ E5 _ _ _ C5 _ _ _ D5 _ E5 _",
                            "D5 _ _ _ B4 _ _ _ G4 _ _ _ A4 _ B4 _",
                            "A4 _ _ _ _ _ _ _ D5 _ _ _ F#5 _ _ _",
                        },
                        comp = Comp.Chop, comp2 = Comp.Pulse, comp2OnlyInB = true, leadA = Lead.Pluck, leadB = Lead.Saw,
                        leadSend = 0.3f, bass = Bass.Electro, kit = Kit.Electro, claps = true,
                        room = 0.45f, wet = 0.16f, tone = 9000, pump = 0.45f, bassPump = 0.35f, drive = 0.24f,
                    };
                case Soundscape.Underpass:
                    // The tunnel at night, a psychedelic disco groove: a laid-back riff climbing each chord, guitar chops in
                    // the second half under a smooth line, in the tunnel's long echo.
                    return new Style
                    {
                        bpm = 116, swing = 0.02, key = 65, mode = Mode.Major, seed = 344,
                        chords = new[] { "Fmaj7", "Am7", "Bbmaj7", "C", "Fmaj7", "Am7", "Bbmaj7", "C",
                                         "Gm7", "C", "Am7", "Bbmaj7 C", "Gm7", "C", "Am7", "Bbmaj7 C" },
                        hookA = new[]
                        {
                            "C5 _ _ C5 _ _ A4 _ _ _ C5 _ E5 _ F5 _",
                            "E5 _ _ E5 _ _ C5 _ _ _ E5 _ G5 _ A5 _",
                            "D5 _ _ D5 _ _ Bb4 _ _ _ D5 _ F5 _ A5 _",
                            "G5 _ _ _ _ _ E5 _ _ _ C5 _ D5 _ E5 _",
                        },
                        hookB = new[]
                        {
                            "Bb4 _ _ _ D5 _ _ _ F5 _ _ _ D5 _ Bb4 _",
                            "C5 _ _ _ E5 _ _ _ G5 _ _ _ E5 _ C5 _",
                            "C5 _ _ _ E5 _ _ _ A5 _ _ _ G5 _ E5 _",
                            "D5 _ _ _ F5 _ _ _ E5 _ _ _ G5 _ _ _",
                        },
                        comp = Comp.Phaser, comp2 = Comp.Funk, comp2OnlyInB = true, leadA = Lead.Psych, leadB = Lead.Saw,
                        leadSend = 0.45f, bass = Bass.Fuzz, kit = Kit.Psych, claps = true, tambourine = true,
                        room = 0.8f, wet = 0.26f, tone = 7500, pump = 0.25f, bassPump = 0.1f, drive = 0.14f,
                    };
                case Soundscape.Park:
                    // An afternoon under the live oaks, psychedelic synth-pop: a bouncing riff rocking between Cmaj7 and
                    // Fmaj7, then a singing line over jangly guitars.
                    return new Style
                    {
                        bpm = 114, swing = 0.02, key = 60, mode = Mode.Major, seed = 366,
                        chords = new[] { "Cmaj7", "Fmaj7", "Cmaj7", "Fmaj7", "Cmaj7", "Fmaj7", "Cmaj7", "Fmaj7",
                                         "Am7", "D7", "Fmaj7", "G", "Am7", "D7", "Fmaj7", "G" },
                        hookA = new[]
                        {
                            "G4 _ . C5 . E5 _ . G5 _ . E5 . D5 _ .",
                            "A4 _ . C5 . F5 _ . A5 _ . G5 . E5 _ .",
                            "G4 _ . C5 . E5 _ . G5 _ . E5 . D5 _ .",
                            "A4 _ . C5 . F5 _ . E5 _ _ _ C5 _ _ _",
                        },
                        hookB = new[]
                        {
                            "E5 _ _ _ _ _ C5 _ E5 _ _ _ G5 _ _ _",
                            "F#5 _ _ _ _ _ D5 _ A4 _ _ _ C5 _ _ _",
                            "A5 _ _ _ _ _ F5 _ C5 _ _ _ E5 _ _ _",
                            "D5 _ _ _ _ _ _ _ B4 _ _ _ G4 _ _ _",
                        },
                        comp = Comp.Phaser, comp2 = Comp.Jangle, comp2OnlyInB = true, leadA = Lead.Pluck, leadB = Lead.Psych,
                        leadSend = 0.4f, bass = Bass.Fuzz, kit = Kit.Psych, tambourine = true,
                        room = 0.7f, wet = 0.24f, tone = 8000, pump = 0.25f, bassPump = 0.1f, drive = 0.12f,
                    };
                default:
                    // The menu, a warm sunset over the Atlantic: a dreamy line on the phased pad's major sevenths, then a
                    // higher one with a Rhodes.
                    return new Style
                    {
                        bpm = 112, swing = 0.02, key = 64, mode = Mode.Major, seed = 307,
                        chords = new[] { "Emaj7", "C#m7", "Amaj7", "B", "Emaj7", "C#m7", "Amaj7", "B",
                                         "Amaj7", "B", "G#m7 C#m7", "B7sus4", "Amaj7", "B", "G#m7 C#m7", "B7sus4" },
                        hookA = new[]
                        {
                            "B4 _ _ _ _ _ D#5 _ E5 _ _ _ F#5 _ G#5 _",
                            "G#5 _ _ _ _ _ E5 _ _ _ _ _ C#5 _ B4 _",
                            "C#5 _ _ _ _ _ E5 _ G#5 _ _ _ F#5 _ E5 _",
                            "D#5 _ _ _ _ _ _ _ F#5 _ _ _ D#5 _ B4 _",
                        },
                        hookB = new[]
                        {
                            "E5 _ _ _ G#5 _ _ _ A5 _ _ _ G#5 _ E5 _",
                            "F#5 _ _ _ D#5 _ _ _ B4 _ _ _ C#5 _ D#5 _",
                            "D#5 _ _ _ B4 _ _ _ E5 _ _ _ G#5 _ _ _",
                            "F#5 _ _ _ _ _ _ _ E5 _ _ _ . . . .",
                        },
                        comp = Comp.Phaser, comp2 = Comp.Rhodes, comp2OnlyInB = true, leadA = Lead.Psych, leadB = Lead.Psych,
                        leadSend = 0.45f, bass = Bass.Fuzz, kit = Kit.Psych, tambourine = true,
                        room = 0.75f, wet = 0.26f, tone = 7500, pump = 0.25f, bassPump = 0.1f, drive = 0.12f,
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
                roomSize = st.room, damping = 0.55f, wet = st.wet, tone = st.tone, drive = st.drive, wowCents = st.wow,
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
            gtr.duck = gtr2.duck = organ.duck = oohs.duck = st.pump;
            bass.duck = st.bassPump;

            for (int bar = 0; bar < Bars; bar++)
            {
                bool inB = bar >= Bars / 2;
                bool fill = bar == Bars / 2 - 1 || bar == Bars - 1;
                foreach (var ch in s.ChordsIn(bar))
                {
                    Play(st.comp, OnOrgan(st.comp) ? organ : gtr, s, bar, ch, rng, 1f);
                    if (st.comp2 != Comp.None && (!st.comp2OnlyInB || inB))
                        Play(st.comp2, OnOrgan(st.comp2) ? organ : gtr2, s, bar, ch, rng, 0.75f);
                    if (st.oohs && (inB || st.comp2 == Comp.None || !st.comp2OnlyInB))
                        Instruments.Oohs(oohs, s.T(bar, ch.beat), ch.chord.Voice(60, 72, 3), s.Beats(ch.length), 0.6f, bar * 7 + 1);
                    BassLine(st, bass, s, bar, ch, fill);
                }
                Drums(st, s, mix, kick, snare, hats, perc, bar, inB, fill, rng);
            }
            if (st.vinyl > 0f) Instruments.Vinyl(vinyl, 1f, st.seed);

            double prev = Synth.MidiToHz(st.leadLo + 5);
            if (st.hookA != null && st.hookB != null)
            {
                // A written hook: each half's riff twice; a note glides only from one it is tied to.
                double prevEnd = -1;
                foreach (var half in new[] { Hook(st.hookA, 0), Hook(st.hookB, Bars / 2) })
                    foreach (var n in half)
                    {
                        bool legato = Math.Abs(n.beat - prevEnd) < 1e-6;
                        prev = PlayLead(n.beat < Bars * 2 ? st.leadA : st.leadB, lead, s, n, legato ? prev : 0);
                        prevEnd = n.beat + n.len;
                    }
                return mix.Render(Loudness);
            }
            foreach (var n in s.Melody(0, st.leadLo, st.leadHi, new Random(st.seed * 10), st.dance ? Rhythms.Dance : Rhythms.Bouncy))
                prev = PlayLead(st.leadA, lead, s, n, prev);
            foreach (var n in s.Melody(8, st.leadLo + 2, st.leadHi + 2, new Random(st.seed * 10 + 1), Rhythms.Singing))
                prev = PlayLead(st.leadB, lead, s, n, prev);
            return mix.Render(Loudness);
        }

        /// <summary>
        /// A written four-bar hook, played twice from <paramref name="firstBar"/>: each bar sixteen semiquaver steps, a note name
        /// ("A4", "C#5", "Bb4") starting a note, "_" holding it, "." a rest. A step's downbeat is accented.
        /// </summary>
        static List<Note> Hook(string[] bars, int firstBar)
        {
            var notes = new List<Note>();
            for (int rep = 0; rep < 2; rep++)
            {
                int current = -1;
                for (int b = 0; b < bars.Length; b++)
                {
                    var steps = bars[b].Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                    for (int i = 0; i < steps.Length; i++)
                    {
                        string t = steps[i];
                        if (t == "_")
                        {
                            if (current >= 0) { var n = notes[current]; n.len += 0.25; notes[current] = n; }
                            continue;
                        }
                        if (t == ".") { current = -1; continue; }
                        double beat = (firstBar + rep * bars.Length + b) * 4 + i * 0.25;
                        notes.Add(new Note { beat = beat, len = 0.25, midi = NoteNumber(t), vel = i % 4 == 0 ? 0.9f : i % 2 == 0 ? 0.78f : 0.7f });
                        current = notes.Count - 1;
                    }
                }
            }
            return notes;
        }

        /// <summary>A note's MIDI number from its name and octave ("A4" is 69, "C#5" 73, "Bb4" 70).</summary>
        static int NoteNumber(string name)
        {
            int used;
            int pc = Chord.PitchClassOf(name, out used);
            return 12 * (int.Parse(name.Substring(used)) + 1) + pc;
        }

        /// <summary>The organ's own track takes the organ's parts (its chords and its reggae bubble).</summary>
        static bool OnOrgan(Comp comp) { return comp == Comp.Organ || comp == Comp.OrganBubble; }

        static void BassNote(Style st, Track bass, Song s, int bar, double beat, int midi, double beats, float vel, int seed)
        {
            if (st.bass == Bass.Sub) Instruments.SubBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel);
            else if (st.bass == Bass.Upright) Instruments.UprightBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel, seed);
            else if (st.bass == Bass.Electro) Instruments.ElectroBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel);
            else if (st.bass == Bass.Fuzz) Instruments.FuzzBass(bass, s.T(bar, beat), Synth.MidiToHz(midi), s.Beats(beats), vel);
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
                case Kit.Son:
                    // The tumbao: nothing on the one, the root anticipated on the "and" of two, the fifth on four.
                    at = new[] { 1.5, 3 };
                    line = new[] { root, root + 7 };
                    len = 1.3;
                    break;
                case Kit.Calypso:
                    // Soca's bounce: root, a push, the fifth, the octave and back down.
                    at = new[] { 0, 0.75, 1.5, 2, 2.75, 3.5 };
                    line = new[] { root, root, root + 7, root + 12, root + 7, root };
                    len = 0.4;
                    break;
                case Kit.Electro:
                    // French electro's rolling octaves: the root on the beat, the octave on every "and", a fifth pushing
                    // into the next beat; short, so the pump breathes between them.
                    at = new[] { 0, 0.5, 1, 1.5, 1.75, 2, 2.5, 3, 3.5, 3.75 };
                    line = new[] { root, root + 12, root, root + 12, root + 7, root, root + 12, root, root + 12, root + 7 };
                    len = 0.22;
                    break;
                case Kit.Psych:
                {
                    // A melodic, syncopated line that sings over the chord: root, octave, fifth, then up through the
                    // chord's third and back.
                    int third = ch.chord.tones.Length > 1 ? ch.chord.tones[1] : 7;
                    at = new[] { 0, 0.75, 1.5, 2.5, 3, 3.5 };
                    line = new[] { root, root + 12, root + 7, root, root + 12 + third, root + 7 };
                    len = 0.42;
                    break;
                }
                case Kit.OneDrop:
                    // A round reggae line, leaving space: the root held, a lift to the fifth, an octave pickup.
                    at = new[] { 0, 1.5, 2.5, 3 };
                    line = new[] { root, root + 7, root + 12, root + 7 };
                    len = 0.9;
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
                case Comp.Skank:
                {
                    // The off-beat chop of calypso, ska and reggae: a short, bright chord on every "and".
                    var v = ch.chord.Voice(60, 76, 3);
                    for (double b = 0.5; b < span; b += 1)
                        Instruments.Jangle(tr, s.T(bar, ch.beat + b), v, s.Beats(0.22), 0.55f * level, bar * 60 + (int)(b * 4), true, true);
                    break;
                }
                case Comp.Montuno:
                {
                    // A piano-style montuno on the marimba: the chord broken into a syncopated eighth-note figure,
                    // the top note doubled an octave down, the last eighth pushing into the next chord.
                    var v = ch.chord.Voice(60, 79, 4);
                    if (v.Length == 0) break;
                    double[] at = { 0, 0.5, 1.5, 2, 2.5, 3.5 };
                    int[] pick = { 0, 2, 1, 3, 2, 1 };
                    for (int k = 0; k < at.Length; k++)
                    {
                        if (at[k] >= span) break;
                        int m = v[pick[k] % v.Length];
                        float vel = (k == 0 || k == 3 ? 0.62f : 0.48f) * level;
                        Instruments.Marimba(tr, s.T(bar, ch.beat + at[k]), Synth.MidiToHz(m), vel);
                        if (k == 0 || k == 3) Instruments.Marimba(tr, s.T(bar, ch.beat + at[k]), Synth.MidiToHz(m - 12), vel * 0.6f);
                    }
                    break;
                }
                case Comp.Chop:
                {
                    // Filter house: chopped disco chord stabs on a syncopated figure, the filter opening over the first
                    // half, wide open in the second.
                    var v = ch.chord.Voice(57, 76, 4);
                    double sweep = bar < Bars / 2 ? (bar + ch.beat / 4.0) / (Bars / 2) : 1.0;
                    double cutoff = 1600 + 3400 * sweep;   // (from 1.6 kHz: v132 began at 0.7 kHz, muffled)
                    double[] at = bar % 2 == 0 ? new[] { 0, 0.75, 1.5, 2.5, 3.25 } : new[] { 0.5, 1.25, 2, 2.75, 3.5 };
                    for (int k = 0; k < at.Length; k++)
                        if (at[k] < span)
                            Instruments.SawStab(tr, s.T(bar, ch.beat + at[k]), v, s.Beats(0.3), (k == 0 ? 0.62f : 0.5f) * level, cutoff, bar * 70 + k);
                    break;
                }
                case Comp.Pulse:
                {
                    // Pumping synth chords on every quaver, the off-beats leaning in (the sidechain does the rest).
                    var v = ch.chord.Voice(60, 76, 3);
                    for (double b = 0; b < span; b += 0.5)
                    {
                        bool off = Math.Abs(b - Math.Floor(b) - 0.5) < 1e-6;
                        Instruments.SawStab(tr, s.T(bar, ch.beat + b), v, s.Beats(0.32), (off ? 0.48f : 0.32f) * level, 2600, bar * 80 + (int)(b * 2));
                    }
                    break;
                }
                case Comp.Phaser:
                    // A lush phased pad held through the chord, its sweep turning once every two bars.
                    Instruments.PhaserPad(tr, s.T(bar, ch.beat), ch.chord.Voice(55, 74, 4), s.Beats(span - 0.05), 0.5f * level, s.Beats(8), bar * 90 + (int)ch.beat);
                    break;
                case Comp.OrganBubble:
                {
                    // Reggae's organ "bubble": short chords on the off-beats, the "and" of each beat pushed by a ghost.
                    var v = ch.chord.Voice(55, 70, 3);
                    for (double b = 0.5; b < span; b += 1)
                        Instruments.Organ(tr, s.T(bar, ch.beat + b), v, s.Beats(0.3), 0.5f * level);
                    for (double b = 0.75; b < span; b += 2)
                        Instruments.Organ(tr, s.T(bar, ch.beat + b), v, s.Beats(0.15), 0.28f * level);
                    break;
                }
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
                // Florida's: a steel pan, a marimba (a soft roll on the long notes) and the vibraphone.
                case Lead.SteelPan: Instruments.SteelPan(tr, t, f, d, v * 1.05f); break;
                case Lead.Marimba:
                    Instruments.Marimba(tr, t, f, v * 1.1f);
                    for (double r = 0.25; r < n.len - 0.2; r += 0.25)
                        Instruments.Marimba(tr, s.T(n) + s.Beats(r), f, v * 0.55f);
                    break;
                case Lead.Vibes: Instruments.Vibes(tr, t, f, d, v * 1.05f); break;
                // Florida's synths: the electro saw lead and the dreamy psychedelic one, both gliding from the last note.
                case Lead.Saw: Instruments.SawLead(tr, t, f, prevFreq, d * 0.92, v * 0.95f); break;
                case Lead.Psych: Instruments.PsychLead(tr, t, f, prevFreq, d * 0.95, v * 0.9f); break;
                case Lead.Pluck: Instruments.SynthPluck(tr, t, f, d, v); break;
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
            if (st.kit == Kit.Calypso || st.kit == Kit.Son || st.kit == Kit.OneDrop)
            {
                TropicalDrums(st, s, mix, kick, snare, hats, perc, bar, inB, fill, rng);
                return;
            }
            if (st.kit == Kit.Electro || st.kit == Kit.Psych)
            {
                SynthDrums(st, s, mix, kick, snare, hats, perc, bar, inB, fill, rng);
                return;
            }
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

        /// <summary>
        /// Florida's kits. Calypso: soca's four on the floor, the backbeat with claps, open off-beat hats, congas
        /// and a tambourine. Son: no backbeat at all, the 3-2 son clave over two bars, bongos playing the martillo,
        /// the congas' tumbao (open tones on four and its "and"), a guiro scraping each half bar, a soft kick and a
        /// side-stick. One-drop: the kick and the side-stick together on the third beat only, swung hats and a
        /// shaker. A crash opens each half; the fill is the hand drums rolling down.
        /// </summary>
        static void TropicalDrums(Style st, Song s, Mixdown mix, Track kick, Track snare, Track hats, Track perc, int bar, bool inB, bool fill, Random rng)
        {
            double[] kicks = st.kit == Kit.Calypso ? new[] { 0.0, 1, 2, 3 } : st.kit == Kit.Son ? new[] { 0.0, 2.5 } : new[] { 2.0 };
            foreach (double k in kicks)
            {
                if (fill && k >= 3) continue;
                double t = s.T(bar, k);
                Instruments.Kick(kick, t, st.kit == Kit.Son ? 0.6f : (k == 0 || k == 2 ? 0.95f : 0.8f));
                mix.Duck(t, st.kit == Kit.Son ? 0.25f : 0.45f, 0.1);
            }

            switch (st.kit)
            {
                case Kit.Calypso:
                    foreach (double b in new[] { 1.0, 3.0 })
                    {
                        if (fill && b >= 3) continue;
                        Instruments.Snare(snare, s.T(bar, b), 0.72f, bar * 4 + (int)b);
                        if (st.claps) Instruments.Clap(perc, s.T(bar, b) + 0.004, 0.5f, bar * 4 + (int)b);
                    }
                    for (int e = 0; e < 8; e++)
                    {
                        double b = e * 0.5;
                        if (fill && b >= 3) break;
                        if (e % 2 == 1) Instruments.OpenHat(hats, s.T(bar, b), 0.32f, bar * 8 + e);
                        else Instruments.Hat(hats, s.T(bar, b), 0.3f, bar * 8 + e);
                        if (st.tambourine && e % 2 == 1 && inB) Instruments.Tambourine(perc, s.T(bar, b + 0.25), 0.25f, bar * 8 + e);
                    }
                    if (!fill)
                        foreach (double b in new[] { 1.5, 3.0, 3.5 }) Instruments.Conga(perc, s.T(bar, b), 0.45f, b != 3.0);
                    break;
                case Kit.Son:
                {
                    // The 3-2 son clave: three strokes in the first bar of each pair, two in the second.
                    double[] clave = bar % 2 == 0 ? new[] { 0, 1.5, 3 } : new[] { 1.0, 2 };
                    foreach (double b in clave) Instruments.Clave(perc, s.T(bar, b), 0.5f);
                    for (int e = 0; e < 8; e++)
                    {
                        double b = e * 0.5;
                        if (fill && b >= 3) break;
                        Instruments.Bongo(perc, s.T(bar, b), e % 2 == 0 ? 0.42f : 0.26f, e % 4 != 2, bar * 8 + e);
                    }
                    if (!fill)
                    {
                        Instruments.Conga(perc, s.T(bar, 1), 0.3f, true);
                        Instruments.Conga(perc, s.T(bar, 3), 0.55f, true);
                        Instruments.Conga(perc, s.T(bar, 3.5), 0.5f, false);
                    }
                    Instruments.Guiro(perc, s.T(bar, 0), s.Beats(0.6), 0.32f, bar * 4);
                    Instruments.Guiro(perc, s.T(bar, 2), s.Beats(0.6), 0.32f, bar * 4 + 2);
                    if (inB) Instruments.Rim(snare, s.T(bar, 3), 0.45f);
                    if (st.claps && inB) Instruments.Clap(perc, s.T(bar, 3) + 0.004, 0.3f, bar * 4);
                    break;
                }
                default:
                    // One-drop: the side-stick lands with the kick on three.
                    Instruments.Rim(snare, s.T(bar, 2), 0.8f);
                    if (inB) Instruments.Snare(snare, s.T(bar, 2), 0.35f, bar * 4);
                    for (int e = 0; e < 8; e++)
                    {
                        double b = e * 0.5;
                        if (fill && b >= 3) break;
                        Instruments.Hat(hats, s.T(bar, b), (e % 2 == 0 ? 0.36f : 0.22f) * (float)(0.85 + rng.NextDouble() * 0.3), bar * 8 + e);
                        Instruments.Shaker(perc, s.T(bar, b + 0.25), 0.18f, bar * 8 + e);
                    }
                    break;
            }

            if (fill)
                for (int k = 0; k < 4; k++) Instruments.Conga(perc, s.T(bar, 3 + k * 0.25), 0.6f, k < 2);
            if (bar == 0 || bar == Bars / 2) Instruments.Crash(hats, s.T(bar, 0), 0.6f, bar);
        }

        /// <summary>
        /// Florida's dance kits (v132). Electro: French filter house, four on the floor with a hard kick that pumps the
        /// whole mix, a crunchy snare and claps on the backbeat, the open hat on every off-beat, sixteenth hats, a
        /// shaker in the second half, and a snare roll building into each half. Psych: big, squashed, laid-back
        /// psychedelic-pop drums, a syncopated kick, the fat snare on the backbeat, quaver hats, a tambourine on the
        /// sixteenths in the second half and a rolling tom fill; it pumps too, but gently.
        /// </summary>
        static void SynthDrums(Style st, Song s, Mixdown mix, Track kick, Track snare, Track hats, Track perc, int bar, bool inB, bool fill, Random rng)
        {
            bool electro = st.kit == Kit.Electro;
            double[] kicks = electro ? new[] { 0.0, 1, 2, 3 } : bar % 2 == 0 ? new[] { 0.0, 1.5, 2.5 } : new[] { 0.0, 0.75, 2, 2.75 };
            foreach (double k in kicks)
            {
                if (fill && k >= 3 && !electro) continue;
                double t = s.T(bar, k);
                Instruments.PunchKick(kick, t, electro ? (k == 0 ? 1f : 0.92f) : (k == 0 ? 0.95f : 0.78f));
                mix.Duck(t, electro ? 1f : 0.6f, electro ? 0.13 : 0.11);
            }
            foreach (double b in new[] { 1.0, 3.0 })
            {
                if (fill && b >= 3) continue;
                double t = s.T(bar, b);
                Instruments.CrunchSnare(snare, t, electro ? 0.72f : 0.82f, bar * 4 + (int)b);
                if (st.claps) Instruments.Clap(perc, t + 0.003, electro ? 0.6f : 0.4f, bar * 4 + (int)b);
            }
            if (fill)
            {
                if (electro)
                    for (int k = 0; k < 8; k++) Instruments.CrunchSnare(snare, s.T(bar, 3 + k * 0.125), 0.22f + k * 0.07f, 1300 + bar * 8 + k);
                else
                    for (int k = 0; k < 6; k++) Instruments.Tom(perc, s.T(bar, 3 + k * 1.0 / 6), 190 - k * 18, 0.6f + k * 0.04f);
            }
            if (bar == 0 || bar == Bars / 2) Instruments.Crash(hats, s.T(bar, 0), 0.65f, bar);

            int steps = electro ? 16 : 8;
            for (int e = 0; e < steps; e++)
            {
                double b = e * 4.0 / steps;
                if (fill && b >= 3) break;
                bool onBeat = Math.Abs(b - Math.Round(b)) < 1e-6;
                bool offEighth = !onBeat && Math.Abs(b * 2 - Math.Round(b * 2)) < 1e-6;
                float jitter = (float)(0.85 + rng.NextDouble() * 0.3);
                if (electro && offEighth) Instruments.OpenHat(hats, s.T(bar, b), 0.5f, bar * 16 + e);
                else Instruments.Hat(hats, s.T(bar, b), (onBeat ? 0.42f : electro ? 0.22f : 0.34f) * jitter, bar * 16 + e);
                if (inB && electro && !onBeat) Instruments.Shaker(perc, s.T(bar, b), 0.22f, bar * 16 + e);
            }
            if (!electro && st.tambourine && inB && !fill)
                for (double b = 0.25; b < 4; b += 0.5) Instruments.Tambourine(perc, s.T(bar, b), 0.28f, bar * 16 + (int)(b * 4));
            if (!electro && inB && !fill) Instruments.OpenHat(hats, s.T(bar, 3.5), 0.4f, bar);
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

            public static int PitchClassOf(string s, out int used) { return PitchClass(s, out used); }

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
