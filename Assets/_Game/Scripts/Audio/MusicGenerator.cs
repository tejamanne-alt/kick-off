using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>
    /// The music, in the style of the country the streets are in (<see cref="MusicCountry"/>): for the original
    /// town (Kamakura, Japan) cozy Japanese music on the "royal road" chords, with pentatonic (yonanuki) tunes on
    /// bamboo flutes, a kalimba and a music box, and no string sounds (see <see cref="KamakuraStyleOf"/>); for
    /// Florida tropical house (<see cref="FloridaStyleOf"/>); for the California add-on the sunny, upbeat Californian West Coast styles
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
                    case MusicCountry.Florida: return ArrangeFlorida(FloridaStyleOf(scape));
                    default: return ArrangeKamakura(KamakuraStyleOf(scape));
                }
            }
            finally { Scratch.End(); }
        }

        // ================= Styles =================

        enum Comp { None, Jangle, Acoustic, Fingerpick, Palm, Funk, Rhodes, RhodesHeld, Organ, Skank, Montuno, OrganBubble, Chop, Pulse, Phaser }
        enum Lead { Surf, Whistle, Glock, Guitar, Acoustic, Rhodes, Koto, Flute, SteelPan, Marimba, Vibes, Saw, Psych, Pluck, Kalimba, PanFlute }
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
            /// <summary>Florida's (v144): the voice of the opening's and the breakdown's quieter hook, and of the arpeggio.</summary>
            public Lead leadSoft = Lead.Marimba, arp = Lead.Marimba;
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
            public float drive = 0.08f, wow = 0f;
            /// <summary>The first half's tune on the dance rhythms (quavers, repeated notes) rather than the bouncy pop ones.</summary>
            public bool dance = false;
            /// <summary>
            /// A written tune instead of a made-up one: four bars each, sixteen semiquaver steps a bar ("A4", "C#5": a note
            /// starts; "_" holds it; "." rests). The first half plays <see cref="hookA"/> twice, the second <see cref="hookB"/> twice.
            /// </summary>
            public string[] hookA, hookB;
            /// <summary>The loop's loudness (RMS). Florida's sits under the others' (v138: "too loud"): its synths are brighter.</summary>
            public float loudness = Loudness;
        }

        /// <summary>
        /// Kamakura's music (v145): cozy Japanese, the user's brief ("cozy music but in Japanese style"), with no string sounds
        /// (no koto, guitar, piano or string pad) and Florida's round synth bass, the one thing it shares with Florida's music.
        /// Its own gentle kit (a soft swung groove, a side-stick, a woodblock, soft taiko in the fills, a little vinyl), a sho-like
        /// mouth-organ chord breathing under it, wind chimes and a temple bowl at the sections' turns, and the tunes on the
        /// shakuhachi, the shinobue (a high bamboo flute), the kalimba, a music box, the vibes and the marimba, written on the
        /// yonanuki pentatonic (no fourth, no seventh) over the "royal road" (IVmaj7-V7-iiim7-vim7) and ii-V-I-vi, at 84 to 100
        /// BPM. ArrangeKamakura lays each place's two hooks out over a minute and more (tools/music_hooks/check.py checks them).
        /// </summary>
        static Style KamakuraStyleOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street:
                    // The home street in the morning: a music-box tune in D on the royal road (IV-V-iii-vi), the shinobue's chorus; a kalimba to open.
                    return new Style
                    {
                        bpm = 92, swing = 0.06, key = 62, mode = Mode.Yona, seed = 711,
                        chords = new[] { "Gmaj7", "A7", "F#m7", "Bm7", "Gmaj7", "A7", "F#m7", "Bm7",
                                         "Gmaj7", "A7", "F#m7 Bm7", "Em7 A7", "Gmaj7", "A7", "F#m7 Bm7", "Em7 A7" },
                        hookA = new[]
                        {
                            "D5 _ B4 _ A4 _ F#4 _ A4 _ _ _ B4 _ D5 _",
                            "E5 _ D5 _ B4 _ A4 _ A4 _ _ _ . . E4 _",
                            "F#5 _ E5 _ D5 _ B4 _ A4 _ _ _ F#4 _ A4 _",
                            "B4 _ _ _ A4 _ F#4 _ D4 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "B5 . A5 . F#5 _ E5 _ D5 _ _ _ B4 _ A4 _",
                            "A4 _ _ _ B4 _ D5 _ E5 _ _ _ D5 _ B4 _",
                            "F#5 _ _ _ E5 _ D5 _ D5 _ _ _ B4 _ A4 _",
                            "E5 _ _ _ D5 _ B4 _ A4 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Kalimba, leadA = Lead.Glock, leadB = Lead.PanFlute, arp = Lead.Kalimba, oohs = true,
                        leadSend = 0.38f, room = 0.6f, wet = 0.24f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
                    };
                case Soundscape.Market:
                    // The shop lane: a bouncy kalimba tune in F, the shinobue's chorus on ii-V-I-vi; a music box to open.
                    return new Style
                    {
                        bpm = 96, swing = 0.06, key = 65, mode = Mode.Yona, seed = 722,
                        chords = new[] { "Bbmaj7", "C7", "Am7", "Dm7", "Bbmaj7", "C7", "Am7", "Dm7",
                                         "Gm7", "C7", "Fmaj7", "Dm7", "Gm7", "C7", "Fmaj7", "Dm7" },
                        hookA = new[]
                        {
                            "C5 . D5 . F5 . D5 . C5 . A4 . C5 _ . .",
                            "C5 . D5 . G5 . F5 . G5 . D5 . C5 _ . .",
                            "A4 . C5 . D5 . C5 . A4 . G4 . A4 _ . .",
                            "F4 _ _ _ A4 _ _ _ D5 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "D5 _ _ _ F5 _ G5 _ A5 _ _ _ G5 _ F5 _",
                            "G5 _ _ _ F5 _ D5 _ C5 _ _ _ D5 _ C5 _",
                            "A4 _ _ _ C5 _ D5 _ F5 _ _ _ D5 _ C5 _",
                            "D5 _ _ _ C5 _ A4 _ F4 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Glock, leadA = Lead.Kalimba, leadB = Lead.PanFlute, arp = Lead.Glock, oohs = false,
                        leadSend = 0.38f, room = 0.55f, wet = 0.22f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
                    };
                case Soundscape.Beach:
                    // Shonan's beach: the shinobue's tune in G, a music box's chorus over "ooh"s; vibes to open.
                    return new Style
                    {
                        bpm = 94, swing = 0.05, key = 67, mode = Mode.Yona, seed = 733,
                        chords = new[] { "Cmaj7", "D7", "Bm7", "Em7", "Cmaj7", "D7", "Bm7", "Em7",
                                         "Am7", "D7", "Gmaj7", "Em7", "Am7", "D7", "Gmaj7", "Em7" },
                        hookA = new[]
                        {
                            "B5 _ _ _ A5 _ G5 _ E5 _ _ _ D5 _ E5 _",
                            "D5 _ _ _ . . E5 _ A5 _ _ _ G5 _ E5 _",
                            "D5 _ _ _ B4 _ A4 _ B4 _ _ _ D5 _ E5 _",
                            "E5 _ _ _ _ _ D5 _ B4 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "G5 . A5 . B5 _ . A5 . G5 . E5 _ . D5 .",
                            "A5 . G5 . E5 _ . D5 . E5 . A5 _ . G5 .",
                            "B5 . A5 . G5 _ . E5 . D5 . E5 _ . G5 .",
                            "E5 _ _ _ D5 _ _ _ E5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Vibes, leadA = Lead.PanFlute, leadB = Lead.Glock, arp = Lead.Kalimba, oohs = true,
                        leadSend = 0.38f, room = 0.65f, wet = 0.26f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
                    };
                case Soundscape.Site:
                    // The building site, the liveliest: a marimba tune in C with repeated notes, the shinobue's chorus; a kalimba to open.
                    return new Style
                    {
                        bpm = 100, swing = 0.04, key = 60, mode = Mode.Yona, seed = 755,
                        chords = new[] { "Fmaj7", "G7", "Em7", "Am7", "Fmaj7", "G7", "Em7", "Am7",
                                         "Dm7", "G7", "Cmaj7", "Am7", "Dm7", "G7", "Cmaj7", "Am7" },
                        hookA = new[]
                        {
                            "C5 . C5 . A4 . G4 . A4 . C5 . D5 _ . .",
                            "D5 . D5 . C5 . A4 . G4 . A4 . G4 _ . .",
                            "E5 . E5 . D5 . C5 . D5 . E5 . G5 _ . .",
                            "A4 _ _ _ G4 _ _ _ E4 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "D5 _ _ _ E5 _ D5 _ C5 _ _ _ A4 _ _ _",
                            "G4 _ _ _ A4 _ G4 _ D4 _ _ _ G4 _ _ _",
                            "E5 _ _ _ G5 _ E5 _ D5 _ _ _ C5 _ _ _",
                            "C5 _ _ _ A4 _ _ _ A4 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Kalimba, leadA = Lead.Marimba, leadB = Lead.PanFlute, arp = Lead.Kalimba, oohs = true,
                        leadSend = 0.38f, room = 0.55f, wet = 0.22f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
                    };
                case Soundscape.Underpass:
                    // The tunnel at night, the slowest: the shakuhachi's tune in Eb, long notes in the echo, then the vibes; a music box to open.
                    return new Style
                    {
                        bpm = 86, swing = 0.08, key = 63, mode = Mode.Yona, seed = 744,
                        chords = new[] { "Abmaj7", "Bb7", "Gm7", "Cm7", "Abmaj7", "Bb7", "Gm7", "Cm7",
                                         "Fm7", "Bb7", "Ebmaj7", "Cm7", "Fm7", "Bb7", "Ebmaj7", "Cm7" },
                        hookA = new[]
                        {
                            "Bb4 _ _ _ _ _ G4 _ F4 _ _ _ Eb4 _ _ _",
                            "F4 _ _ _ _ _ Eb4 _ Bb3 _ _ _ . . . .",
                            "G4 _ _ _ Bb4 _ C5 _ Bb4 _ _ _ G4 _ _ _",
                            "C5 _ _ _ _ _ Bb4 _ G4 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "Eb5 _ _ _ C5 _ _ _ F5 _ _ _ Eb5 _ _ _",
                            "F5 _ _ _ _ _ Eb5 _ Bb4 _ _ _ F5 _ _ _",
                            "G5 _ _ _ F5 _ Eb5 _ C5 _ _ _ Bb4 _ _ _",
                            "Bb4 _ _ _ G4 _ _ _ Eb4 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Glock, leadA = Lead.Flute, leadB = Lead.Vibes, arp = Lead.Glock, oohs = false,
                        leadSend = 0.38f, room = 0.8f, wet = 0.3f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
                    };
                case Soundscape.Park:
                    // The temple ground: the shakuhachi's tune in E, the shinobue's chorus over "ooh"s; a kalimba to open.
                    return new Style
                    {
                        bpm = 88, swing = 0.06, key = 64, mode = Mode.Yona, seed = 766,
                        chords = new[] { "Amaj7", "B7", "G#m7", "C#m7", "Amaj7", "B7", "G#m7", "C#m7",
                                         "F#m7", "B7", "Emaj7", "C#m7", "F#m7", "B7", "Emaj7", "C#m7" },
                        hookA = new[]
                        {
                            "C#5 _ _ _ B4 _ C#5 _ E5 _ _ _ C#5 _ B4 _",
                            "B4 _ _ _ F#5 _ E5 _ F#5 _ _ _ . . . .",
                            "G#5 _ _ _ F#5 _ E5 _ F#5 _ _ _ G#5 _ B5 _",
                            "C#5 _ _ _ _ _ _ _ B4 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "G#5 . F#5 . E5 _ _ . C#5 . E5 . F#5 _ _ .",
                            "F#5 . E5 . C#5 _ _ . B4 . C#5 . B4 _ _ .",
                            "E5 . F#5 . G#5 _ _ . B5 . G#5 . F#5 _ _ .",
                            "E5 _ _ _ C#5 _ _ _ B4 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Kalimba, leadA = Lead.Flute, leadB = Lead.PanFlute, arp = Lead.Kalimba, oohs = true,
                        leadSend = 0.38f, room = 0.75f, wet = 0.28f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
                    };
                default:
                    // The menu, a lullaby in Bb: the kalimba's tune, then the shakuhachi's; vibes to open.
                    return new Style
                    {
                        bpm = 84, swing = 0.06, key = 70, mode = Mode.Yona, seed = 707,
                        chords = new[] { "Ebmaj7", "F7", "Dm7", "Gm7", "Ebmaj7", "F7", "Dm7", "Gm7",
                                         "Cm7", "F7", "Bbmaj7", "Gm7", "Cm7", "F7", "Bbmaj7", "Gm7" },
                        hookA = new[]
                        {
                            "D5 _ F5 _ G5 _ F5 _ D5 _ _ _ C5 _ Bb4 _",
                            "C5 _ _ _ F4 _ _ _ C5 _ _ _ . . . .",
                            "D5 _ F5 _ G5 _ F5 _ F5 _ _ _ D5 _ C5 _",
                            "Bb4 _ _ _ G4 _ _ _ F4 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "G5 _ _ _ F5 _ D5 _ C5 _ _ _ Bb4 _ _ _",
                            "C5 _ _ _ _ _ D5 _ F5 _ _ _ _ _ _ _",
                            "G5 _ _ _ F5 _ D5 _ F5 _ _ _ G5 _ Bb5 _",
                            "Bb5 _ _ _ G5 _ _ _ F5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Vibes, leadA = Lead.Kalimba, leadB = Lead.Flute, arp = Lead.Glock, oohs = false,
                        leadSend = 0.38f, room = 0.75f, wet = 0.3f, tone = 6500, pump = 0.12f, bassPump = 0.1f, drive = 0.05f, vinyl = 0.25f, loudness = 0.12f,
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
        /// The Florida add-on's music (v144): tropical house, the user's pick (docs/LEARNINGS.md G8), with no string sounds at
        /// all (no guitar, tres, piano, string pad or plucked bass) and its own new drums. A soft four-on-the-floor kit with
        /// finger snaps, shakers and off-beat hats; a warm synth pad breathing under the kick; a round synth bass; marimba,
        /// steel pan, kalimba, vibes, glockenspiel, a synth pluck and a pan flute on the tunes; an arpeggio under the groove and
        /// vocal "ooh"s in the drop; sunny major keys at 100 to 118 BPM. Each place has two four-bar chord cycles and two written
        /// hooks (tools/music_hooks/check.py); ArrangeFlorida lays them out over a minute in four sections.
        /// </summary>
        static Style FloridaStyleOf(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street:
                    // Downtown (Brickell, Biscayne, the Downpour), the busiest: a pluck riff in A over I-V-vi-IV, the pan flute's
                    // chorus in the drop.
                    return new Style
                    {
                        bpm = 116, swing = 0, key = 69, mode = Mode.Major, seed = 611,
                        chords = new[] { "A", "E", "F#m", "D", "A", "E", "F#m", "D",
                                         "D", "E", "C#m F#m", "Bm E", "D", "E", "C#m F#m", "Bm E" },
                        hookA = new[]
                        {
                            "E5 . . C#5 . . A4 . C#5 . E5 . . F#5 E5 .",
                            "E5 . . B4 . . G#4 . B4 . E5 . . F#5 E5 .",
                            "C#5 . . A4 . . F#4 . A4 . C#5 . . E5 C#5 .",
                            "D5 . . F#5 . . A5 _ _ _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "F#5 _ . A5 _ . D6 _ . A5 _ . F#5 _ A5 _",
                            "G#5 _ . B5 _ . E5 _ . B5 _ . G#5 _ B5 _",
                            "C#6 _ _ _ B5 _ G#5 _ A5 _ _ _ F#5 _ C#5 _",
                            "B5 _ _ _ F#5 _ D5 _ E5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Marimba, leadA = Lead.Pluck, leadB = Lead.PanFlute, arp = Lead.Marimba, oohs = true,
                        leadSend = 0.35f, room = 0.6f, wet = 0.24f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.11f,
                    };
                case Soundscape.Market:
                    // Little Havana: a bouncy marimba tune in C (vi-IV-I-V), the steel pan's chorus; a kalimba to open.
                    return new Style
                    {
                        bpm = 112, swing = 0, key = 60, mode = Mode.Major, seed = 622,
                        chords = new[] { "Am", "F", "C", "G", "Am", "F", "C", "G",
                                         "F", "G", "Em7 Am7", "Dm7 G", "F", "G", "Em7 Am7", "Dm7 G" },
                        hookA = new[]
                        {
                            "A5 . E5 . C5 . E5 . A5 . . G5 . E5 . .",
                            "A5 . F5 . C5 . F5 . A5 . . G5 . F5 . .",
                            "G5 . E5 . C5 . E5 . G5 . . A5 . G5 . .",
                            "B5 _ _ _ D6 _ _ _ B5 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "C6 _ . A5 . F5 _ . A5 _ . C6 . A5 _ .",
                            "D6 _ . B5 . G5 _ . B5 _ . D6 . B5 _ .",
                            "B5 _ _ _ G5 _ E5 _ C6 _ _ _ A5 _ E5 _",
                            "A5 _ _ _ F5 _ D5 _ D5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Kalimba, leadA = Lead.Marimba, leadB = Lead.SteelPan, arp = Lead.Pluck,
                        leadSend = 0.35f, room = 0.6f, wet = 0.24f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.11f,
                    };
                case Soundscape.Beach:
                    // The bay and the river: a steel pan tune in G, the pan flute's chorus over "ooh"s; marimba arpeggios.
                    return new Style
                    {
                        bpm = 110, swing = 0, key = 67, mode = Mode.Major, seed = 633,
                        chords = new[] { "G", "C", "Em", "D", "G", "C", "Em", "D",
                                         "C", "D", "G/B Em", "Am7 D", "C", "D", "G/B Em", "Am7 D" },
                        hookA = new[]
                        {
                            "D5 . . G5 . . B5 . D6 . B5 . . G5 . .",
                            "E5 . . G5 . . C6 . G5 . E5 . . C5 . .",
                            "B4 . . E5 . . G5 . B5 . G5 . . E5 . .",
                            "F#5 _ _ _ A5 _ _ _ D5 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "G5 _ _ _ E5 _ G5 _ C6 _ _ _ G5 _ E5 _",
                            "A5 _ _ _ F#5 _ A5 _ D6 _ _ _ A5 _ F#5 _",
                            "B5 _ _ _ D6 _ B5 _ G5 _ _ _ E5 _ B4 _",
                            "C6 _ _ _ A5 _ _ _ A5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Marimba, leadA = Lead.SteelPan, leadB = Lead.PanFlute, arp = Lead.Marimba, oohs = true,
                        leadSend = 0.4f, room = 0.65f, wet = 0.26f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.11f,
                    };
                case Soundscape.Site:
                    // The building site, the liveliest: a bright pluck riff in D, the steel pan's chorus; vibes to open.
                    return new Style
                    {
                        bpm = 118, swing = 0, key = 62, mode = Mode.Major, seed = 655,
                        chords = new[] { "D", "A", "Bm", "G", "D", "A", "Bm", "G",
                                         "G", "D/F#", "Em7", "A", "G", "D/F#", "Em7", "A" },
                        hookA = new[]
                        {
                            "F#5 . A5 . D6 . A5 . F#5 . . A5 . D6 . .",
                            "E5 . A5 . C#6 . A5 . E5 . . A5 . C#6 . .",
                            "F#5 . B5 . D6 . B5 . F#5 . . B5 . D6 . .",
                            "G5 _ _ _ B5 _ _ _ D6 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "B5 _ _ _ A5 _ G5 _ D5 _ _ _ G5 _ _ _",
                            "A5 _ _ _ F#5 _ _ _ D5 _ _ _ F#5 _ A5 _",
                            "G5 _ _ _ E5 _ _ _ B4 _ _ _ D5 _ E5 _",
                            "C#6 _ _ _ A5 _ _ _ E5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Vibes, leadA = Lead.Pluck, leadB = Lead.SteelPan, arp = Lead.Pluck, oohs = true,
                        leadSend = 0.35f, room = 0.55f, wet = 0.22f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.11f,
                    };
                case Soundscape.Underpass:
                    // The Underline, mellow: the pan flute's tune in F over vi-IV-I-V, the vibes' chorus; a kalimba to open.
                    return new Style
                    {
                        bpm = 108, swing = 0, key = 65, mode = Mode.Major, seed = 644,
                        chords = new[] { "Dm", "Bb", "F", "C", "Dm", "Bb", "F", "C",
                                         "Bb", "C", "F/A Dm", "Gm7 C", "Bb", "C", "F/A Dm", "Gm7 C" },
                        hookA = new[]
                        {
                            "A5 _ _ _ _ _ F5 _ D5 _ _ _ F5 _ _ _",
                            "D5 _ _ _ _ _ F5 _ Bb5 _ _ _ F5 _ _ _",
                            "C6 _ _ _ _ _ A5 _ F5 _ _ _ A5 _ _ _",
                            "G5 _ _ _ E5 _ _ _ C5 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "F5 . Bb5 . D6 _ . Bb5 . F5 . Bb5 _ . D5 .",
                            "E5 . G5 . C6 _ . G5 . E5 . G5 _ . C5 .",
                            "A5 _ _ _ C6 _ A5 _ F5 _ _ _ D5 _ F5 _",
                            "Bb5 _ _ _ G5 _ _ _ G5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Kalimba, leadA = Lead.PanFlute, leadB = Lead.Vibes, arp = Lead.Kalimba,
                        leadSend = 0.42f, room = 0.75f, wet = 0.28f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.105f,
                    };
                case Soundscape.Park:
                    // Museum Park's lawns: a marimba climbing the chords in E, the pan flute's chorus over "ooh"s; a glockenspiel to open.
                    return new Style
                    {
                        bpm = 106, swing = 0, key = 64, mode = Mode.Major, seed = 666,
                        chords = new[] { "E", "G#m", "A", "B", "E", "G#m", "A", "B",
                                         "C#m", "A", "E", "B", "C#m", "A", "E", "B" },
                        hookA = new[]
                        {
                            "E5 . G#5 . B5 . G#5 . E5 . G#5 . B5 . . .",
                            "D#5 . G#5 . B5 . G#5 . D#5 . G#5 . B5 . . .",
                            "C#5 . E5 . A5 . E5 . C#5 . E5 . A5 . . .",
                            "D#5 _ _ _ F#5 _ _ _ B5 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "E5 _ _ _ G#5 _ _ _ C#6 _ _ _ B5 _ G#5 _",
                            "A5 _ _ _ E5 _ _ _ C#5 _ _ _ E5 _ A5 _",
                            "G#5 _ _ _ B5 _ _ _ E5 _ _ _ G#5 _ B5 _",
                            "B5 _ _ _ F#5 _ _ _ D#5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Glock, leadA = Lead.Marimba, leadB = Lead.PanFlute, arp = Lead.Kalimba, oohs = true,
                        leadSend = 0.4f, room = 0.7f, wet = 0.26f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.105f,
                    };
                default:
                    // The menu, a warm evening on the bay: the kalimba's tune in Bb, the pan flute's chorus; vibes to open.
                    return new Style
                    {
                        bpm = 100, swing = 0, key = 70, mode = Mode.Major, seed = 607,
                        chords = new[] { "Bb", "Gm", "Eb", "F", "Bb", "Gm", "Eb", "F",
                                         "Eb", "F", "Dm Gm", "Cm7 F", "Eb", "F", "Dm Gm", "Cm7 F" },
                        hookA = new[]
                        {
                            "D5 . F5 . Bb5 _ _ . F5 . D5 . Bb4 _ _ .",
                            "D5 . G5 . Bb5 _ _ . G5 . D5 . G4 _ _ .",
                            "Eb5 . G5 . Bb5 _ _ . G5 . Eb5 . Bb4 _ _ .",
                            "C5 _ _ _ F5 _ _ _ A5 _ _ _ . . . .",
                        },
                        hookB = new[]
                        {
                            "G5 _ _ _ Bb5 _ G5 _ Eb5 _ _ _ G5 _ _ _",
                            "A5 _ _ _ C6 _ A5 _ F5 _ _ _ A5 _ _ _",
                            "F5 _ _ _ A5 _ F5 _ G5 _ _ _ Bb5 _ _ _",
                            "Eb5 _ _ _ G5 _ _ _ F5 _ _ _ _ _ _ _",
                        },
                        leadSoft = Lead.Vibes, leadA = Lead.Kalimba, leadB = Lead.PanFlute, arp = Lead.Marimba,
                        leadSend = 0.42f, room = 0.75f, wet = 0.28f, tone = 7500, pump = 0.3f, bassPump = 0.25f, drive = 0.06f, loudness = 0.105f,
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
        /// Florida's arranger (v144, tropical house; the four sections are v138's, so the music develops through a level and
        /// sits back behind the play): a 32-bar loop in four sections of eight.
        ///   1. Bars 1-8, the opening: the pad, the bass, the soft kick, snaps and shaker; the first hook once on the soft voice,
        ///      then the arpeggio for four bars.
        ///   2. Bars 9-16, the groove: the full kit, the arpeggio; the first hook twice.
        ///   3. Bars 17-24, the drop: the second chord cycle, the second hook twice, "ooh"s, claps, open hats.
        ///   4. Bars 25-32, the breakdown: the kick out, the pad and the first hook on the soft voice; the groove comes back for
        ///      the last four bars and a clap roll leads into the loop's start.
        /// The style's 16 chords are its two four-bar cycles twice (A A B B); the sections use A, A, B, A. No string sound plays.
        /// </summary>
        static float[] ArrangeFlorida(Style st)
        {
            const int FlBars = 32;
            var chords = new string[FlBars];
            for (int b = 0; b < FlBars; b++)
            {
                int section = b / 8;
                chords[b] = st.chords[(section == 2 ? 8 : 0) + b % 8];
            }
            var s = new Song(st.bpm, st.swing, st.key, st.mode, st.seed, chords);
            var rng = new Random(st.seed * 31);
            var mix = new Mixdown(s.Length)
            {
                roomSize = st.room, damping = 0.6f, wet = st.wet, tone = st.tone, drive = st.drive, wowCents = st.wow,
            };
            var pad = mix.Add(0f, 0.45f, 0.5f);
            var oohs = mix.Add(0f, 0.55f, 0.3f);
            var arp = mix.Add(0.3f, 0.35f, 0.32f);
            var bass = mix.Add(0f, 0.04f, 0.8f);
            var lead = mix.Add(0.08f, st.leadSend, 0.62f);
            var soft = mix.Add(-0.15f, 0.42f, 0.55f);
            var kick = mix.Add(0f, 0.04f, 0.85f);
            var snaps = mix.Add(0.08f, 0.22f, 0.45f);
            var hats = mix.Add(0.32f, 0.08f, 0.2f);
            var perc = mix.Add(-0.4f, 0.14f, 0.3f);
            pad.duck = oohs.duck = arp.duck = st.pump;
            bass.duck = st.bassPump;

            for (int bar = 0; bar < FlBars; bar++)
            {
                int section = bar / 8, inSection = bar % 8;
                bool fill = bar == FlBars - 1;
                bool breakdown = section == 3 && inSection < 4;
                int level = section == 0 || (section == 3 && !breakdown) ? 1 : breakdown ? 0 : 2;
                foreach (var ch in s.ChordsIn(bar))
                {
                    Instruments.SoftPad(pad, s.T(bar, ch.beat), ch.chord.Voice(57, 72, 4), s.Beats(ch.length - 0.05), breakdown ? 0.6f : 0.5f);
                    if (st.oohs && section == 2)
                        Instruments.Oohs(oohs, s.T(bar, ch.beat), ch.chord.Voice(60, 72, 3), s.Beats(ch.length), 0.5f, bar * 7 + 1);
                    if (breakdown)
                    {
                        int root = ch.chord.Bass(36);
                        if (root > 43) root -= 12;
                        Instruments.SynthBass(bass, s.T(bar, ch.beat), Synth.MidiToHz(root), s.Beats(ch.length - 0.2), 0.6f);
                    }
                    else TropicalBass(bass, s, bar, ch);
                }
                bool arpHere = (section == 0 && inSection >= 4) || section == 1 || section == 2 || (section == 3 && !breakdown);
                if (arpHere) Arpeggio(st.arp, arp, s, bar, ArpLevel(st.arp) * (section == 2 ? 0.8f : 1f));
                TropicalDrums(s, mix, kick, snaps, hats, perc, bar, section, level, fill, rng);
            }

            // The tunes: the first hook once on the soft voice in the opening, twice in the groove; the second hook twice in the
            // drop; the first once more on the soft voice in the breakdown. A note glides only from one it is tied to.
            var parts = new List<KeyValuePair<Lead, List<Note>>>
            {
                new KeyValuePair<Lead, List<Note>>(st.leadSoft, Hook(st.hookA, 0, 1, 0, 0.85f * LeadLevel(st.leadSoft))),
                new KeyValuePair<Lead, List<Note>>(st.leadA, Hook(st.hookA, 8, 2, 0, LeadLevel(st.leadA))),
                new KeyValuePair<Lead, List<Note>>(st.leadB, Hook(st.hookB, 16, 2, 0, LeadLevel(st.leadB))),
                new KeyValuePair<Lead, List<Note>>(st.leadSoft, Hook(st.hookA, 24, 1, 0, 0.8f * LeadLevel(st.leadSoft))),
            };
            for (int p = 0; p < parts.Count; p++)
            {
                double prev = 0, prevEnd = -1;
                var into = p == 0 || p == 3 ? soft : lead;
                foreach (var n in parts[p].Value)
                {
                    bool legato = Math.Abs(n.beat - prevEnd) < 1e-6;
                    prev = PlayLead(parts[p].Key, into, s, n, legato ? prev : 0);
                    prevEnd = n.beat + n.len;
                }
            }
            return mix.Render(st.loudness);
        }

        /// <summary>The tropical bass: the root on the one, pushed on the "and" of two and of three, the octave lifting on four.</summary>
        static void TropicalBass(Track bass, Song s, int bar, ChordAt ch)
        {
            int root = ch.chord.Bass(36);
            if (root > 43) root -= 12;
            double[] at = ch.length >= 4 ? new[] { 0, 1.5, 2.5, 3 } : new[] { 0, 1.5 };
            int[] line = ch.length >= 4 ? new[] { root, root, root + 7, root + 12 } : new[] { root, root + 12 };
            double[] len = ch.length >= 4 ? new[] { 1.2, 0.6, 0.4, 0.8 } : new[] { 1.2, 0.4 };
            for (int k = 0; k < at.Length; k++)
                if (at[k] < ch.length)
                    Instruments.SynthBass(bass, s.T(bar, ch.beat + at[k]), Synth.MidiToHz(line[k]), s.Beats(len[k]), k == 0 ? 0.85f : 0.7f);
        }

        /// <summary>The arpeggio under the groove: the chord's tones up and back in eighths, soft, on the style's mallet or pluck.</summary>
        static void Arpeggio(Lead voice, Track tr, Song s, int bar, float level)
        {
            foreach (var ch in s.ChordsIn(bar))
            {
                var v = ch.chord.Voice(64, 81, 4);
                if (v.Length == 0) continue;
                int[] order = { 0, 1, 2, 3, 2, 1, 2, 3 };
                for (int e = 0; e < ch.length * 2; e++)
                {
                    int m = v[order[e % order.Length] % v.Length];
                    float vel = (e % 2 == 0 ? 0.5f : 0.38f) * level;
                    var n = new Note { beat = bar * 4 + ch.beat + e * 0.5, len = 0.45, midi = m, vel = vel };
                    PlayLead(voice, tr, s, n, 0);
                }
            }
        }

        /// <summary>
        /// Florida's tropical-house kit (v144, new): a soft round kick four to the floor that the pad and bass breathe under, finger
        /// snaps on two and four (with claps in the drop), a shaker on the sixteenths, closed hats on the off-beats (open ones in
        /// the drop), and a rim on the 3-3-2 of the groove. level 0 the shaker and soft snaps alone, 1 a light groove, 2 the full
        /// kit; the last bar's clap roll leads into the loop's start.
        /// </summary>
        static void TropicalDrums(Song s, Mixdown mix, Track kick, Track snaps, Track hats, Track perc, int bar, int section, int level, bool fill, Random rng)
        {
            if (level >= 1)
                for (int b = 0; b < 4; b++)
                {
                    double t = s.T(bar, b);
                    Instruments.SoftKick(kick, t, (b == 0 ? 0.95f : 0.85f) * (level == 1 ? 0.85f : 1f));
                    mix.Duck(t, 0.55f, 0.16);
                }
            foreach (double b in new[] { 1.0, 3.0 })
            {
                if (fill && b >= 3) continue;
                Instruments.Snap(snaps, s.T(bar, b), level == 0 ? 0.35f : level == 1 ? 0.5f : 0.6f, bar * 4 + (int)b);
                if (section == 2) Instruments.Clap(snaps, s.T(bar, b) + 0.004, 0.32f, bar * 4 + (int)b + 1);
            }
            for (int e = 0; e < 16; e++)
            {
                double b = e * 0.25;
                if (fill && b >= 3) break;
                float jitter = (float)(0.85 + rng.NextDouble() * 0.3);
                Instruments.Shaker(perc, s.T(bar, b), (e % 2 == 1 ? 0.2f : 0.12f) * jitter * (level == 0 ? 0.7f : 1f), bar * 16 + e);
                if (level == 2 && e % 4 == 2)
                {
                    if (section == 2) Instruments.OpenHat(hats, s.T(bar, b), 0.22f, bar * 16 + e);
                    else Instruments.Hat(hats, s.T(bar, b), 0.3f * jitter, bar * 16 + e);
                }
            }
            if (level == 2 && !fill)
                foreach (double b in new[] { 0.75, 1.5, 2.5 })
                    Instruments.Rim(perc, s.T(bar, b), 0.3f);
            if (fill)
                for (int k = 0; k < 8; k++) Instruments.Clap(snaps, s.T(bar, 3 + k * 0.125), 0.12f + k * 0.05f, 1700 + k);
            if (bar == 16) Instruments.Crash(hats, s.T(bar, 0), 0.32f, bar);
        }

        /// <summary>
        /// Florida's tune voices brought to one loudness (a note's level measured on its own, RMS, against the steel pan's): set
        /// from the measurements in docs/LEARNINGS.md G8.
        /// </summary>
        static float LeadLevel(Lead lead)
        {
            // (per half-second note, RMS: the steel pan 0.23, the vibes 0.22, the marimba and the kalimba 0.18, the
            // glockenspiel and the synth pluck 0.11, the pan flute 0.25, the shakuhachi 0.17); Florida's and Kamakura's tunes
            switch (lead)
            {
                case Lead.Marimba: return 1.25f;
                case Lead.Kalimba: return 1.25f;
                case Lead.Vibes: return 1.05f;
                case Lead.Glock: return 2.1f;
                case Lead.Pluck: return 2.1f;
                case Lead.PanFlute: return 0.92f;
                case Lead.Flute: return 1.35f;     // (Kamakura's shakuhachi, v145: 0.17)
                default: return 1f;
            }
        }

        /// <summary>The arpeggio's voice, levelled as the tunes are (its track sits under the tune's).</summary>
        static float ArpLevel(Lead voice) { return LeadLevel(voice); }

        /// <summary>
        /// Kamakura's arranger (v145, cozy Japanese): a 32-bar loop in four sections of eight, so it develops through a level.
        ///   1. Bars 1-8, the opening: a temple bowl and wind chimes, the sho's chords, the synth bass, the light groove; the first
        ///      hook once on the soft voice, then the arpeggio for four bars.
        ///   2. Bars 9-16, the groove: the full kit and the arpeggio; the first hook twice.
        ///   3. Bars 17-24, the lift: the second chord cycle, the second hook twice, chimes, "ooh"s (some places), the shaker.
        ///   4. Bars 25-32, the rest: the bowl again, the kit out but the woodblock, the bass held, the first hook on the soft
        ///      voice; the groove comes back for the last four bars and soft taiko lead into the loop's start.
        /// No string sound plays; the bass is Florida's synth bass. The style's 16 chords are its two cycles twice (A A B B).
        /// </summary>
        static float[] ArrangeKamakura(Style st)
        {
            const int KmBars = 32;
            var chords = new string[KmBars];
            for (int b = 0; b < KmBars; b++)
                chords[b] = st.chords[(b / 8 == 2 ? 8 : 0) + b % 8];
            var s = new Song(st.bpm, st.swing, st.key, st.mode, st.seed, chords);
            var rng = new Random(st.seed * 31);
            var mix = new Mixdown(s.Length)
            {
                roomSize = st.room, damping = 0.65f, wet = st.wet, tone = st.tone, drive = st.drive, wowCents = st.wow,
            };
            var sho = mix.Add(0f, 0.45f, 0.45f);
            var oohs = mix.Add(0f, 0.55f, 0.28f);
            var arp = mix.Add(0.3f, 0.35f, 0.3f);
            var bass = mix.Add(0f, 0.04f, 0.8f);
            var lead = mix.Add(0.08f, st.leadSend, 0.62f);
            var soft = mix.Add(-0.15f, 0.42f, 0.55f);
            var bells = mix.Add(-0.3f, 0.6f, 0.35f);     // the bowl and the chimes
            var kick = mix.Add(0f, 0.04f, 0.75f);
            var snare = mix.Add(0.05f, 0.2f, 0.5f);
            var hats = mix.Add(0.3f, 0.08f, 0.2f);
            var perc = mix.Add(-0.35f, 0.18f, 0.38f);
            var vinyl = mix.Add(0f, 0f, 0.5f * st.vinyl);
            sho.duck = oohs.duck = arp.duck = st.pump;
            bass.duck = st.bassPump;

            for (int bar = 0; bar < KmBars; bar++)
            {
                int section = bar / 8, inSection = bar % 8;
                bool fill = bar == KmBars - 1;
                bool rest = section == 3 && inSection < 4;
                int level = section == 0 || (section == 3 && !rest) ? 1 : rest ? 0 : 2;
                foreach (var ch in s.ChordsIn(bar))
                {
                    Instruments.ShoPad(sho, s.T(bar, ch.beat), ch.chord.Voice(60, 76, 4), s.Beats(ch.length - 0.05), rest ? 0.6f : 0.5f);
                    if (st.oohs && section == 2)
                        Instruments.Oohs(oohs, s.T(bar, ch.beat), ch.chord.Voice(60, 72, 3), s.Beats(ch.length), 0.5f, bar * 7 + 1);
                    if (rest)
                    {
                        int root = ch.chord.Bass(36);
                        if (root > 43) root -= 12;
                        Instruments.SynthBass(bass, s.T(bar, ch.beat), Synth.MidiToHz(root), s.Beats(ch.length - 0.2), 0.6f);
                    }
                    else CozyBass(bass, s, bar, ch);
                }
                bool arpHere = (section == 0 && inSection >= 4) || section == 1 || section == 2 || (section == 3 && !rest);
                if (arpHere) Arpeggio(st.arp, arp, s, bar, 0.8f * ArpLevel(st.arp));
                if (inSection == 0)
                {
                    // a temple bowl at the opening and the rest (on the key's root), wind chimes at every section's turn
                    if (section == 0 || section == 3) Instruments.TempleBowl(bells, s.T(bar, 0), Synth.MidiToHz(st.key + 12), 0.55f);
                    int[] penta = { 0, 2, 4, 7, 9 };
                    for (int k = 0; k < 5; k++)
                        Instruments.WindChime(bells, s.T(bar, 0.5 + k * 0.37 + rng.NextDouble() * 0.15),
                            Synth.MidiToHz(st.key + 24 + penta[rng.Next(penta.Length)] + (rng.NextDouble() < 0.4 ? 12 : 0)), 0.3f - k * 0.04f);
                }
                CozyDrums(s, mix, kick, snare, hats, perc, bar, section, level, fill, rng);
            }
            if (st.vinyl > 0f) Instruments.Vinyl(vinyl, 1f, st.seed);

            var parts = new List<KeyValuePair<Lead, List<Note>>>
            {
                new KeyValuePair<Lead, List<Note>>(st.leadSoft, Hook(st.hookA, 0, 1, 0, 0.85f * LeadLevel(st.leadSoft))),
                new KeyValuePair<Lead, List<Note>>(st.leadA, Hook(st.hookA, 8, 2, 0, LeadLevel(st.leadA))),
                new KeyValuePair<Lead, List<Note>>(st.leadB, Hook(st.hookB, 16, 2, 0, LeadLevel(st.leadB))),
                new KeyValuePair<Lead, List<Note>>(st.leadSoft, Hook(st.hookA, 24, 1, 0, 0.8f * LeadLevel(st.leadSoft))),
            };
            for (int p = 0; p < parts.Count; p++)
            {
                double prev = 0, prevEnd = -1;
                var into = p == 0 || p == 3 ? soft : lead;
                foreach (var n in parts[p].Value)
                {
                    bool legato = Math.Abs(n.beat - prevEnd) < 1e-6;
                    prev = PlayLead(parts[p].Key, into, s, n, legato ? prev : 0);
                    prevEnd = n.beat + n.len;
                }
            }
            return mix.Render(st.loudness);
        }

        /// <summary>Kamakura's bass line (Florida's synth bass, played laid back): the root held, a push on the "and" of two, the fifth on three.</summary>
        static void CozyBass(Track bass, Song s, int bar, ChordAt ch)
        {
            int root = ch.chord.Bass(36);
            if (root > 43) root -= 12;
            double[] at = ch.length >= 4 ? new[] { 0, 1.75, 2.5 } : new[] { 0, 1.5 };
            int[] line = ch.length >= 4 ? new[] { root, root, root + 7 } : new[] { root, root + 7 };
            double[] len = ch.length >= 4 ? new[] { 1.5, 0.5, 1.2 } : new[] { 1.3, 0.4 };
            for (int k = 0; k < at.Length; k++)
                if (at[k] < ch.length)
                    Instruments.SynthBass(bass, s.T(bar, ch.beat + at[k]), Synth.MidiToHz(line[k]), s.Beats(len[k]), k == 0 ? 0.8f : 0.65f);
        }

        /// <summary>
        /// Kamakura's cozy kit (v145, its own): a soft, swung groove. The boomy kick on the one and the "and" of three (and two's
        /// "and" every other bar), a soft snare with a side-stick on two and four, swung hats, the shaker in the lift, a woodblock
        /// (the temple's mokugyo) on the last "and" of every other bar; in the rest only the woodblock on two and four and quiet
        /// hats; soft taiko in the loop's last bar.
        /// </summary>
        static void CozyDrums(Song s, Mixdown mix, Track kick, Track snare, Track hats, Track perc, int bar, int section, int level, bool fill, Random rng)
        {
            if (level >= 1)
            {
                double[] kicks = bar % 2 == 0 ? new[] { 0, 2.5 } : new[] { 0, 1.5, 2.5 };
                foreach (double k in kicks)
                {
                    double t = s.T(bar, k);
                    Instruments.Kick(kick, t, (k == 0 ? 0.85f : 0.7f) * (level == 1 ? 0.85f : 1f));
                    mix.Duck(t, 0.3f, 0.12);
                }
                foreach (double b in new[] { 1.0, 3.0 })
                {
                    if (fill && b >= 3) continue;
                    if (level == 2) Instruments.Snare(snare, s.T(bar, b), 0.45f, bar * 4 + (int)b);
                    Instruments.Rim(snare, s.T(bar, b), level == 2 ? 0.35f : 0.5f);
                }
            }
            else
                foreach (double b in new[] { 1.0, 3.0 }) Instruments.Woodblock(perc, s.T(bar, b), 0.4f, b == 1.0);
            for (int e = 0; e < 8; e++)
            {
                double b = e * 0.5;
                if (fill && b >= 3) break;
                float jitter = (float)(0.85 + rng.NextDouble() * 0.3);
                Instruments.Hat(hats, s.T(bar, b), (e % 2 == 0 ? 0.3f : 0.2f) * jitter * (level == 0 ? 0.6f : 1f), bar * 8 + e);
            }
            if (section == 2)
                for (double b = 0.25; b < 4; b += 0.5) Instruments.Shaker(perc, s.T(bar, b), 0.16f, bar * 16 + (int)(b * 4));
            if (level >= 1 && bar % 2 == 1 && !fill) Instruments.Woodblock(perc, s.T(bar, 3.5), 0.35f, true);
            if (fill)
                for (int k = 0; k < 4; k++) Instruments.Tom(perc, s.T(bar, 3 + k * 0.25), 120 - k * 10, 0.45f + k * 0.08f);
        }

        /// <summary>
        /// A written four-bar hook, played twice from <paramref name="firstBar"/>: each bar sixteen semiquaver steps, a note name
        /// ("A4", "C#5", "Bb4") starting a note, "_" holding it, "." a rest. A step's downbeat is accented.
        /// </summary>
        static List<Note> Hook(string[] bars, int firstBar, int reps = 2, int transpose = 0, float gain = 1f)
        {
            var notes = new List<Note>();
            for (int rep = 0; rep < reps; rep++)
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
                        notes.Add(new Note { beat = beat, len = 0.25, midi = NoteNumber(t) + transpose, vel = (i % 4 == 0 ? 0.9f : i % 2 == 0 ? 0.78f : 0.7f) * gain });
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
                    double cutoff = 1200 + 1600 * sweep;   // (v138: 1.2 to 2.8 kHz: brighter grated)
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
                        Instruments.SawStab(tr, s.T(bar, ch.beat + b), v, s.Beats(0.3), (off ? 0.38f : 0.22f) * level, 1700, bar * 80 + (int)(b * 2));
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
                // (a written hook passes 0 for a note not tied to the last: it starts on its own pitch, not a slide up from 0 Hz)
                case Lead.Whistle: Instruments.Whistle(tr, t, f, prevFreq > 0 ? prevFreq : f, d * 0.95, v * 0.85f); break;
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
                // Florida's tropical house (v144): the kalimba and the pan flute.
                case Lead.Kalimba: Instruments.Kalimba(tr, t, f, v); break;
                case Lead.PanFlute: Instruments.PanFlute(tr, t, f, d * 0.95, v, n.midi * 5 + (int)(n.beat * 4)); break;
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
                SynthDrums(st, s, mix, kick, snare, hats, perc, bar, inB, fill, rng, 2, bar == 0 || bar == Bars / 2);
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
        static void SynthDrums(Style st, Song s, Mixdown mix, Track kick, Track snare, Track hats, Track perc, int bar, bool inB, bool fill, Random rng,
            int level = 2, bool crash = false)
        {
            // level: 0 the hats alone (a breakdown), 1 a light groove (kick, a soft backbeat, closed hats), 2 the full kit.
            // Since v138 the kit sits back (the user: "grating", "too loud"): softer hats and claps, the open hat lighter, the
            // pump shallower.
            bool electro = st.kit == Kit.Electro;
            if (level >= 1)
            {
                double[] kicks = electro ? new[] { 0.0, 1, 2, 3 } : bar % 2 == 0 ? new[] { 0.0, 1.5, 2.5 } : new[] { 0.0, 0.75, 2, 2.75 };
                foreach (double k in kicks)
                {
                    if (fill && k >= 3 && !electro) continue;
                    double t = s.T(bar, k);
                    float v = electro ? (k == 0 ? 0.95f : 0.85f) : (k == 0 ? 0.9f : 0.72f);
                    Instruments.PunchKick(kick, t, level == 1 ? v * 0.8f : v);
                    mix.Duck(t, electro ? 0.7f : 0.45f, electro ? 0.12 : 0.1);
                }
                foreach (double b in new[] { 1.0, 3.0 })
                {
                    if (fill && b >= 3) continue;
                    double t = s.T(bar, b);
                    Instruments.CrunchSnare(snare, t, (electro ? 0.6f : 0.68f) * (level == 1 ? 0.75f : 1f), bar * 4 + (int)b);
                    if (st.claps && level == 2) Instruments.Clap(perc, t + 0.003, electro ? 0.38f : 0.28f, bar * 4 + (int)b);
                }
            }
            if (fill)
            {
                if (electro)
                    for (int k = 0; k < 8; k++) Instruments.CrunchSnare(snare, s.T(bar, 3 + k * 0.125), 0.16f + k * 0.05f, 1300 + bar * 8 + k);
                else
                    for (int k = 0; k < 6; k++) Instruments.Tom(perc, s.T(bar, 3 + k * 1.0 / 6), 190 - k * 18, 0.5f + k * 0.04f);
            }
            if (crash) Instruments.Crash(hats, s.T(bar, 0), 0.5f, bar);

            int steps = electro && level == 2 ? 16 : 8;
            for (int e = 0; e < steps; e++)
            {
                double b = e * 4.0 / steps;
                if (fill && b >= 3) break;
                bool onBeat = Math.Abs(b - Math.Round(b)) < 1e-6;
                bool offEighth = !onBeat && Math.Abs(b * 2 - Math.Round(b * 2)) < 1e-6;
                float jitter = (float)(0.85 + rng.NextDouble() * 0.3);
                float soft = level == 0 ? 0.6f : 1f;
                if (electro && offEighth && level == 2) Instruments.OpenHat(hats, s.T(bar, b), 0.3f, bar * 16 + e);
                else Instruments.Hat(hats, s.T(bar, b), (onBeat ? 0.32f : electro ? 0.16f : 0.26f) * jitter * soft, bar * 16 + e);
                if (inB && electro && level == 2 && !onBeat) Instruments.Shaker(perc, s.T(bar, b), 0.15f, bar * 16 + e);
            }
            if (!electro && st.tambourine && inB && level == 2 && !fill)
                for (double b = 0.25; b < 4; b += 0.5) Instruments.Tambourine(perc, s.T(bar, b), 0.2f, bar * 16 + (int)(b * 4));
            if (!electro && inB && level == 2 && !fill) Instruments.OpenHat(hats, s.T(bar, 3.5), 0.28f, bar);
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
