using System;
using System.Collections.Generic;

namespace DribbleToSchool.Audio
{
    /// <summary>A sound of the place that comes now and then: a car going by, a gull, a reversing truck.</summary>
    public sealed class AmbientCue
    {
        public string name;
        /// <summary>Interleaved stereo at <see cref="Synth.SampleRate"/>, its loudest peak at 0.6.</summary>
        public float[] clip;
        /// <summary>Seconds between one and the next (picked at random in this range).</summary>
        public float minGap, maxGap;
        public float volume;
        /// <summary>Where it is heard, -1 left to 1 right, and how far either side of that it may land.</summary>
        public float pan, panSpread;
        /// <summary>Random pitch either way (0.1 = up to 10 %), so it never repeats exactly.</summary>
        public float pitchVariance;
        /// <summary>Passes across: the pan travels from one side to the other while it plays.</summary>
        public bool sweep;
    }

    /// <summary>The ambience of one soundscape: a seamless stereo bed, and the cues that come and go over it.</summary>
    public sealed class AmbiencePack
    {
        public Soundscape scape;
        public float[] bed;
        public AmbientCue[] cues;
    }

    /// <summary>
    /// The sound of each place, synthesized: a bed that loops (traffic hum and cars going by on Home
    /// Street; a murmuring crowd, cups and pigeons in the market; waves breaking and drawing back on the
    /// beach; the hollow rumble and hum of the underpass; a diesel generator and wind on the building site;
    /// leaves and a fountain in the park; a soft breeze and birds for the menu), and the cues that come now
    /// and then over it (car horns, bicycle bells, a church bell, dogs; a shop's door bell, a clock, a cart on
    /// the cobbles; gulls, a buoy's bell, a ship; dripping water, a train overhead, footsteps; a reversing
    /// truck, a jackhammer, hammering, a digger, a drill, an air brake, dropped pipes; robins, tits, a
    /// blackbird, wood pigeons, ducks and a woodpecker). Florida's places have their own, nothing shared with
    /// Kamakura's: Little Havana (a lively street, a cafe's radio playing a son, dominoes, roosters, hens, a moped),
    /// the Miami River (water on the seawall, halyards, an outboard, a tug's horn, the drawbridge's bell, laughing
    /// gulls), the bay (small waves, palms in the sea breeze, a cruise ship's horn, laughing gulls, a pelican diving),
    /// downtown (traffic, air conditioners, buses' air brakes, a crane's beeps, a jackhammer far off, wild parrots, a
    /// horn), the Underline (the Metrorail overhead, bicycle bells, joggers, cicadas, a mockingbird) and Museum Park
    /// (palms and banyans, small waves, children far off, a mockingbird, grackles, a sprinkler). Played well under the
    /// music (AudioDirector). Pure C#: safe on a worker thread.
    /// </summary>
    public static class AmbienceGenerator
    {
        public const int Channels = 2;
        /// <summary>
        /// Each place's bed loudness (RMS), well under the music's <see cref="MusicGenerator.Loudness"/> and in
        /// proportion to how loud the place really is: the surf and the building site's generators the
        /// loudest, a road of passing cars and the echoing underpass next, then a quiet residential street,
        /// a small market square with a few people about, and the park and the menu quietest. Florida's: downtown's
        /// traffic between the towers and the waves on the bay's seawall loudest, the Underline's highway and trains
        /// next, then the river and Little Havana's busy street, and Museum Park quietest.
        /// </summary>
        public static float BedLoudness(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Beach: return 0.06f;
                case Soundscape.Site: return 0.055f;
                case Soundscape.Underpass: return 0.048f;
                case Soundscape.Street: return 0.045f;
                case Soundscape.Market: return 0.035f;
                case Soundscape.Park: return 0.035f;
                case Soundscape.Downtown: return 0.05f;
                case Soundscape.Bay: return 0.05f;
                case Soundscape.Underline: return 0.045f;
                case Soundscape.MiamiRiver: return 0.042f;
                case Soundscape.Havana: return 0.04f;
                case Soundscape.MuseumPark: return 0.037f;
                default: return 0.03f;
            }
        }
        const double BedSeconds = 30.0;
        const double Fold = 2.0;
        const double TwoPi = Math.PI * 2.0;
        static int Sr { get { return Synth.SampleRate; } }

        public static AmbiencePack Generate(Soundscape scape)
        {
            var pack = new AmbiencePack { scape = scape };
            var cues = new List<AmbientCue>();
            // The bed's layers and voices are all as long as the loop: their work buffers are reused one to the next
            // (a cue's are each its own length, so there is nothing to reuse there).
            Scratch.Begin();
            try { pack.bed = Bed(scape); }
            finally { Scratch.End(); }
            switch (scape)
            {
                case Soundscape.Street: StreetCues(cues); break;
                case Soundscape.Market: MarketCues(cues); break;
                case Soundscape.Beach: BeachCues(cues); break;
                case Soundscape.Underpass: UnderpassCues(cues); break;
                case Soundscape.Site: SiteCues(cues); break;
                case Soundscape.Park: ParkCues(cues); break;
                case Soundscape.Havana: HavanaCues(cues); break;
                case Soundscape.MiamiRiver: MiamiRiverCues(cues); break;
                case Soundscape.Bay: BayCues(cues); break;
                case Soundscape.Downtown: DowntownCues(cues); break;
                case Soundscape.Underline: UnderlineCues(cues); break;
                case Soundscape.MuseumPark: MuseumParkCues(cues); break;
                default: MenuCues(cues); break;
            }
            // The cues follow their place's loudness (a little less steeply, so a quiet place's birdsong
            // or shop bell still carries): against the old common bed level, 0.075.
            float cueScale = (float)Math.Sqrt(BedLoudness(scape) / 0.075);
            foreach (var cue in cues) cue.volume *= cueScale;
            pack.cues = cues.ToArray();
            return pack;
        }

        // ================= Beds =================

        static float[] Bed(Soundscape scape)
        {
            switch (scape)
            {
                case Soundscape.Street: return StreetBed();
                case Soundscape.Market: return MarketBed();
                case Soundscape.Beach: return BeachBed();
                case Soundscape.Underpass: return UnderpassBed();
                case Soundscape.Site: return SiteBed();
                case Soundscape.Park: return ParkBed();
                case Soundscape.Havana: return HavanaBed();
                case Soundscape.MiamiRiver: return MiamiRiverBed();
                case Soundscape.Bay: return BayBed();
                case Soundscape.Downtown: return DowntownBed();
                case Soundscape.Underline: return UnderlineBed();
                case Soundscape.MuseumPark: return MuseumParkBed();
                default: return MenuBed();
            }
        }

        static int BedLength { get { return (int)(BedSeconds * Sr); } }

        /// <summary>A continuous layer made a little longer than the loop, then folded so its end crossfades into its start.</summary>
        static void Layer(Track into, Func<int, float> sample)
        {
            int len = into.Length, fold = (int)(Fold * Sr);
            var raw = Scratch.Rent(len + fold);
            for (int i = 0; i < raw.Length; i++) raw[i] = sample(i);
            for (int i = 0; i < len; i++)
            {
                float v = raw[i];
                if (i < fold)
                {
                    double a = i / (double)fold * Math.PI * 0.5;
                    v = (float)(raw[i] * Math.Sin(a) + raw[len + i] * Math.Cos(a));
                }
                into.buf[i] += v;
            }
            Scratch.Return(raw);
        }

        /// <summary>Low-passed noise with a slow swell: traffic, a city's hum, room tone, surf.</summary>
        static void Rumble(Track t, int seed, double cutoff, double driftHz, float depth, bool brown = true)
        {
            var n = new NoiseSource(seed);
            var f = new Svf();
            var d = new Drift(seed + 1, driftHz);
            Layer(t, i => f.Process(brown ? n.Brown() : n.Pink(), cutoff, 0.6) * (1f - depth + depth * d.Next()));
        }

        /// <summary>Band-passed noise that gusts: wind, leaves, a fountain.</summary>
        static void Airy(Track t, int seed, double centre, double q, double gustHz, float flutter, double flutterHz)
        {
            var n = new NoiseSource(seed);
            var f = new Svf();
            var gust = new Drift(seed + 2, gustHz);
            var fl = new Drift(seed + 3, flutterHz);
            Layer(t, i =>
            {
                float g = gust.Next();
                f.Process(n.Pink(), centre * (0.8 + 0.4 * g), q);
                return f.band * (0.25f + 0.75f * g * g) * (1f - flutter + flutter * fl.Next());
            });
        }

        static float[] Finish(Mixdown mix, Soundscape scape) { return mix.Render(BedLoudness(scape)); }

        static float[] MenuBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.5f, wet = 0.15f };
            Airy(mix.Add(-0.6f, 0f), 11, 900, 0.5, 0.07, 0.2f, 3);
            Airy(mix.Add(0.6f, 0f), 12, 1100, 0.5, 0.06, 0.2f, 3);
            Rumble(mix.Add(0f, 0f, 0.4f), 13, 200, 0.05, 0.4f);
            var birds = mix.Add(0.3f, 0.3f, 0.25f);
            var rng = new Random(14);
            for (double t = 1; t < BedSeconds - 2; t += 3 + rng.NextDouble() * 4)
                Birds.Sparrow(birds, t, rng);
            return Finish(mix, Soundscape.Menu);
        }

        static float[] StreetBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.55f, damping = 0.6f, wet = 0.2f };
            Rumble(mix.Add(-0.7f, 0.1f), 21, 180, 0.07, 0.5f);
            Rumble(mix.Add(0.7f, 0.1f), 22, 200, 0.06, 0.5f);
            Rumble(mix.Add(0f, 0.2f, 0.35f), 23, 650, 0.1, 0.4f, false);
            Airy(mix.Add(0.4f, 0f, 0.35f), 24, 1300, 0.6, 0.08, 0.3f, 4);
            // Cars further off, going by both ways, and the odd chirp from the hedges.
            var cars = mix.Add(0f, 0.25f, 0.6f);
            double[] at = { 2, 9.5, 17, 24 };
            for (int i = 0; i < at.Length; i++) Vehicle.Pass(cars, at[i], 5 + i % 2, 0.35f, 30 + i, 0.7);
            var birds = mix.Add(-0.4f, 0.3f, 0.2f);
            var rng = new Random(25);
            for (double t = 3; t < BedSeconds - 2; t += 4 + rng.NextDouble() * 5) Birds.Sparrow(birds, t, rng);
            return Finish(mix, Soundscape.Street);
        }

        static float[] MarketBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.28f };
            // A few people about the square (the street has only a handful): two or three
            // conversations across it, soft and off in the reverb, too far to make out a word, with
            // the town's hum and the breeze between them, not a crowd's wall of chatter.
            var rng = new Random(31);
            for (int v = 0; v < 4; v++)
            {
                float pan = (float)(rng.NextDouble() * 1.6 - 0.8);
                var voice = mix.Add(pan, 0.65f, (float)(0.14 + rng.NextDouble() * 0.12));
                Voices.Chatter(voice, 100 + v * 7, 95 + rng.NextDouble() * 140);
            }
            Airy(mix.Add(0f, 0.3f, 0.5f), 32, 700, 0.5, 0.15, 0.4f, 6);
            Rumble(mix.Add(0f, 0.1f, 0.5f), 33, 190, 0.06, 0.4f);
            // Spoons and cups at the cafe tables, now and then.
            var cafe = mix.Add(0.5f, 0.3f, 0.22f);
            for (double t = 1.3; t < BedSeconds - 1; t += 2.5 + rng.NextDouble() * 4) Things.Clink(cafe, t, rng);
            return Finish(mix, Soundscape.Market);
        }

        static float[] BeachBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.7f, damping = 0.6f, wet = 0.12f };
            // The surf further out never stops; the waves on the sand come in one by one.
            Rumble(mix.Add(-0.5f, 0.1f, 0.7f), 41, 320, 0.09, 0.5f, false);
            Rumble(mix.Add(0.5f, 0.1f, 0.7f), 42, 340, 0.08, 0.5f, false);
            Waves(mix.Add(-0.35f, 0.15f), 43, 0.0);
            Waves(mix.Add(0.35f, 0.15f), 44, 0.35);
            Airy(mix.Add(0f, 0f, 0.4f), 45, 600, 0.5, 0.1, 0.35f, 5);
            return Finish(mix, Soundscape.Beach);
        }

        /// <summary>Waves breaking and running up the sand, then drawing back with a hiss, every seven to ten seconds.</summary>
        static void Waves(Track t, int seed, double offset)
        {
            var n = new NoiseSource(seed);
            var lowpass = new Svf();
            var foam = new Svf();
            var rng = new Random(seed);
            int total = t.Length + (int)(Fold * Sr);
            var env = Scratch.Rent(total);
            var bright = Scratch.Rent(total);
            double at = offset * 7;
            while (at < total / (double)Sr)
            {
                double rise = 1.6 + rng.NextDouble() * 1.2, wash = 3.2 + rng.NextDouble() * 2.2;
                float size = (float)(0.6 + rng.NextDouble() * 0.4);
                int s0 = (int)(at * Sr), len = (int)((rise + wash) * Sr);
                for (int i = 0; i < len && s0 + i < total; i++)
                {
                    double tt = i / (double)Sr;
                    double e = tt < rise ? Math.Pow(tt / rise, 2.2) : Math.Exp(-(tt - rise) / (wash * 0.38));
                    double b = tt < rise ? Math.Pow(tt / rise, 3) : Math.Exp(-(tt - rise) / (wash * 0.22));
                    env[s0 + i] = Math.Max(env[s0 + i], (float)(e * size));
                    bright[s0 + i] = Math.Max(bright[s0 + i], (float)(b * size));
                }
                at += 6.5 + rng.NextDouble() * 3.5;
            }
            Layer(t, i =>
            {
                float x = n.Pink();
                float body = lowpass.Process(x, 250 + 2600 * bright[i], 0.7) * (0.15f + env[i]);
                foam.Process(x, 3800, 0.5);
                return body + foam.high * 0.5f * bright[i] * env[i];
            });
            Scratch.Return(env);
            Scratch.Return(bright);
        }

        static float[] UnderpassBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.92f, damping = 0.25f, wet = 0.45f };
            Rumble(mix.Add(-0.6f, 0.4f), 51, 140, 0.05, 0.4f);
            Rumble(mix.Add(0.6f, 0.4f), 52, 150, 0.05, 0.4f);
            Rumble(mix.Add(0f, 0.5f, 0.3f), 53, 420, 0.12, 0.6f, false);
            // The strip lights' hum and buzz.
            var hum = mix.Add(-0.5f, 0.2f, 0.06f);
            var d = new Drift(54, 0.3);
            Layer(hum, i =>
            {
                double t = i / (double)Sr;
                double v = Math.Sin(TwoPi * 100 * t) + 0.5 * Math.Sin(TwoPi * 200 * t) + 0.35 * Math.Sin(TwoPi * 300 * t) + 0.15 * Math.Sin(TwoPi * 500 * t);
                return (float)v * (0.7f + 0.3f * d.Next());
            });
            // Cars on the road above, muffled through the deck.
            var above = mix.Add(0f, 0.6f, 0.4f);
            for (int i = 0; i < 3; i++) Vehicle.Pass(above, 3 + i * 9.5, 6, 0.3f, 55 + i, 0.25);
            return Finish(mix, Soundscape.Underpass);
        }

        static float[] SiteBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.2f };
            Machines.Diesel(mix.Add(-0.55f, 0.2f, 0.8f), 61, 29, 0.0);
            Machines.Diesel(mix.Add(0.6f, 0.35f, 0.35f), 62, 36, 0.4);
            Airy(mix.Add(-0.3f, 0f, 0.5f), 63, 700, 0.5, 0.09, 0.3f, 4);
            Airy(mix.Add(0.3f, 0f, 0.45f), 64, 950, 0.5, 0.08, 0.3f, 4);
            Rumble(mix.Add(0f, 0.1f, 0.4f), 65, 200, 0.05, 0.4f);
            return Finish(mix, Soundscape.Site);
        }

        static float[] ParkBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.65f, damping = 0.5f, wet = 0.2f };
            // Leaves: a soft, low rustle that comes and goes with the breeze, well behind the music, the
            // fountain and the birds (a bright, fluttering hiss here drowned everything else out).
            Airy(mix.Add(-0.65f, 0f, 0.3f), 71, 1300, 0.7, 0.08, 0.2f, 3.5);
            Airy(mix.Add(0.65f, 0f, 0.3f), 72, 1500, 0.7, 0.07, 0.2f, 3.5);
            // The fountain by the pond: a steady splash with a trickle in it.
            var fountain = mix.Add(0.55f, 0.3f, 0.35f);
            var n = new NoiseSource(73);
            var f = new Svf();
            var trickle = new Drift(74, 14);
            Layer(fountain, i => { f.Process(n.White(), 1700, 0.7); return f.band * (0.6f + 0.4f * trickle.Next()); });
            Rumble(mix.Add(0f, 0.1f, 0.3f), 75, 180, 0.05, 0.4f);
            var birds = mix.Add(-0.3f, 0.35f, 0.5f);
            var rng = new Random(76);
            for (double t = 1; t < BedSeconds - 2; t += 2.5 + rng.NextDouble() * 3) Birds.Sparrow(birds, t, rng);
            return Finish(mix, Soundscape.Park);
        }

        // ---------- Florida's places (Miami): their own beds, nothing shared with Kamakura's ----------

        static float[] HavanaBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.55f, damping = 0.55f, wet = 0.22f };
            // A warm street of low houses, cafes and shops: the town's hum and a light breeze under it all.
            Rumble(mix.Add(-0.6f, 0.1f, 0.6f), 801, 190, 0.06, 0.4f);
            Rumble(mix.Add(0.6f, 0.1f, 0.6f), 802, 210, 0.07, 0.4f);
            Airy(mix.Add(0f, 0f, 0.3f), 803, 750, 0.5, 0.1, 0.3f, 4);
            // A lively murmur along the pavement and at the cafe's window counter: more people about than in
            // Kamakura's market, talking over each other, still too far off to make out a word.
            var rng = new Random(804);
            for (int v = 0; v < 5; v++)
            {
                float pan = (float)(rng.NextDouble() * 1.8 - 0.9);
                var voice = mix.Add(pan, 0.5f, (float)(0.18 + rng.NextDouble() * 0.12));
                Voices.Chatter(voice, 810 + v * 7, 105 + rng.NextDouble() * 150);
            }
            // The cafe's radio through its window: a son, quiet and muffled.
            CafeRadio(mix.Add(0.45f, 0.3f, 0.5f), 820);
            // The old men's dominoes on a table along the pavement: a tile clicked down now and then, or slammed.
            var table = mix.Add(-0.35f, 0.25f, 0.45f);
            for (double t = 0.8; t < BedSeconds - 1; t += 1.8 + rng.NextDouble() * 3.5) Things.Domino(table, t, rng);
            return Finish(mix, Soundscape.Havana);
        }

        /// <summary>
        /// A son on a radio inside a cafe, heard through its window: the tres's guajeo (its doubled strings an octave
        /// apart), the bass's tumbao, the 3-2 son clave, the bongos' martillo and the conga's open tones, through a small
        /// speaker and the wall (only the middle of the sound gets out). At 96 beats a minute a bar is 2.5 seconds, so
        /// twelve bars fill the loop exactly and it never jumps.
        /// </summary>
        static void CafeRadio(Track into, int seed)
        {
            double beat = 60.0 / 96, eighth = beat / 2, bar = beat * 4;
            int bars = (int)Math.Round(BedSeconds / bar);
            var rng = new Random(seed);
            var band = new Track(into.Length, 0f, 0f, 1f);
            // C, F, G7, F: the son's I-IV-V-IV, a chord a bar, voiced as the tres plays them.
            int[][] chords = { new[] { 60, 64, 67 }, new[] { 60, 65, 69 }, new[] { 59, 62, 65 }, new[] { 60, 65, 69 } };
            int[] roots = { 48, 53, 43, 53 };
            // The guajeo's eighths: it skips the downbeat and its last note pushes into the next bar's chord.
            bool[] tres = { false, true, true, false, true, true, false, true };
            bool[] bongoHigh = { true, true, true, false, true, true, true, false };
            for (int b = 0; b < bars; b++)
            {
                double t0 = b * bar;
                int c = b % 4, next = (b + 1) % 4;
                for (int e = 0; e < 8; e++)
                {
                    double t = t0 + e * eighth;
                    if (tres[e])
                    {
                        var notes = e == 7 ? chords[next] : chords[c];
                        double f = Synth.MidiToHz(notes[(e + b) % 3] + 12);
                        float vel = (float)(0.3 + rng.NextDouble() * 0.1);
                        Instruments.Pluck(band, t, f, eighth * 0.9, vel, rng.Next(), 0.6f, 0.993f);
                        Instruments.Pluck(band, t + 0.008, f * 2, eighth * 0.8, vel * 0.5f, rng.Next(), 0.6f, 0.99f);
                    }
                    Instruments.Bongo(band, t, (float)((e % 2 == 0 ? 0.3 : 0.18) + rng.NextDouble() * 0.06), bongoHigh[e], rng.Next());
                }
                // The tumbao: the fifth on the "and" of two, then the next chord's root on four, ahead of its bar.
                Instruments.UprightBass(band, t0 + 3 * eighth, Synth.MidiToHz(roots[c] + 7), beat * 1.4, 0.5f, rng.Next());
                Instruments.UprightBass(band, t0 + 6 * eighth, Synth.MidiToHz(roots[next]), beat * 1.9, 0.55f, rng.Next());
                // The conga's open tones on four and its "and".
                Instruments.Conga(band, t0 + 6 * eighth, 0.35f, false);
                Instruments.Conga(band, t0 + 7 * eighth, 0.3f, true);
                // The 3-2 son clave over each pair of bars: three strokes in the first (one, the "and" of two, four),
                // two in the second (two, three).
                if (b % 2 == 0) { Instruments.Clave(band, t0, 0.35f); Instruments.Clave(band, t0 + 3 * eighth, 0.35f); Instruments.Clave(band, t0 + 6 * eighth, 0.35f); }
                else { Instruments.Clave(band, t0 + 2 * eighth, 0.35f); Instruments.Clave(band, t0 + 4 * eighth, 0.35f); }
            }
            // Through the radio's small speaker and the wall: no deep bass and no sparkle. Filtered twice round the
            // loop, so the filters start settled and the loop stays seamless.
            var src = band.buf;
            var dst = into.buf;
            var hp = new Svf();
            var lp = new Svf();
            var wall = new Svf();
            for (int pass = 0; pass < 2; pass++)
                for (int i = 0; i < src.Length; i++)
                {
                    hp.Process(src[i], 320, 0.7);
                    lp.Process(hp.high, 1900, 0.9);
                    wall.Process(lp.low, 2300, 0.6);
                    if (pass == 1) dst[i] += wall.low;
                }
            Scratch.Return(src);
        }

        static float[] MiamiRiverBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.2f };
            // The river between its seawalls, never still: the water slopping against the wall below, and its body
            // rocking under it.
            Rumble(mix.Add(-0.3f, 0.15f, 0.45f), 831, 260, 0.5, 0.6f, false);
            Lapping(mix.Add(-0.45f, 0.2f, 1.8f), 832, 1.0, 1f);
            Lapping(mix.Add(0.4f, 0.2f, 1.5f), 833, 0.9, 1f);
            // The city across the water, a low hum, and the breeze down the river.
            Rumble(mix.Add(0.3f, 0.1f, 0.3f), 834, 170, 0.05, 0.4f);
            Airy(mix.Add(0f, 0f, 0.3f), 835, 650, 0.5, 0.09, 0.3f, 4);
            // The boats tied up along the wall: a halyard tinking on a mast now and then.
            var masts = mix.Add(0.5f, 0.3f, 0.25f);
            var rng = new Random(836);
            for (double t = 2; t < BedSeconds - 1; t += 3 + rng.NextDouble() * 5) Things.Halyard(masts, t, rng, 1 + rng.Next(2));
            return Finish(mix, Soundscape.MiamiRiver);
        }

        static float[] BayBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.65f, damping = 0.55f, wet = 0.14f };
            // The bay's small waves: a soft wash of chop further out, and the waves slapping the seawall one by one
            // (a sheltered bay: no surf breaking, as on Kamakura's beach).
            Rumble(mix.Add(-0.5f, 0.1f, 0.6f), 851, 300, 0.12, 0.5f, false);
            Rumble(mix.Add(0.5f, 0.1f, 0.6f), 852, 330, 0.1, 0.5f, false);
            Lapping(mix.Add(-0.3f, 0.15f, 1.4f), 853, 0.8, 1.3f);
            Lapping(mix.Add(0.35f, 0.15f, 1.4f), 854, 0.7, 1.3f);
            // The sea breeze in the palms along Bayfront: their fronds' dry rattle, swelling with each gust.
            Palms(mix.Add(-0.55f, 0.1f, 0.35f), 855, 0.09);
            Palms(mix.Add(0.6f, 0.1f, 0.3f), 856, 0.08);
            Airy(mix.Add(0f, 0f, 0.3f), 857, 520, 0.5, 0.08, 0.3f, 4);
            return Finish(mix, Soundscape.Bay);
        }

        static float[] DowntownBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.7f, damping = 0.45f, wet = 0.24f };
            // The city's traffic between the towers: a steady hum, busier and more echoing than Kamakura's street.
            Rumble(mix.Add(-0.7f, 0.15f), 871, 190, 0.07, 0.45f);
            Rumble(mix.Add(0.7f, 0.15f), 872, 210, 0.06, 0.45f);
            Rumble(mix.Add(0f, 0.3f, 0.4f), 873, 700, 0.1, 0.4f, false);
            // The air conditioners' condensers on the walls and the roofs.
            Condenser(mix.Add(0.45f, 0.25f, 0.12f), 874);
            // Cars and a bus going by on the avenue.
            var cars = mix.Add(0f, 0.3f, 0.6f);
            double[] at = { 1.5, 6.5, 12, 17.5, 23, 27 };
            for (int i = 0; i < at.Length; i++) Vehicle.Pass(cars, at[i], 4.5 + i % 3, 0.35f, 875 + i, i == 3 ? 0.45 : 0.75);
            return Finish(mix, Soundscape.Downtown);
        }

        static float[] UnderlineBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.2f };
            // A path and gardens under the Metrorail's guideway, beside the highway: traffic beyond the trees, the breeze.
            Rumble(mix.Add(-0.6f, 0.1f, 0.7f), 891, 180, 0.06, 0.4f);
            Rumble(mix.Add(0.6f, 0.1f, 0.6f), 892, 200, 0.07, 0.4f);
            Airy(mix.Add(0f, 0f, 0.35f), 893, 900, 0.6, 0.08, 0.25f, 3.5);
            // Cicadas in the trees in the heat, coming and going, soft (a loud, high buzz would drown the music).
            Cicadas(mix.Add(0.4f, 0.15f, 0.2f), 894);
            var cars = mix.Add(-0.3f, 0.3f, 0.4f);
            for (int i = 0; i < 4; i++) Vehicle.Pass(cars, 2 + i * 7.5, 5.5, 0.3f, 895 + i, 0.7);
            return Finish(mix, Soundscape.Underline);
        }

        static float[] MuseumParkBed()
        {
            var mix = new Mixdown(BedLength) { roomSize = 0.6f, damping = 0.5f, wet = 0.2f };
            // A park on the bay: the breeze in the palms and the big banyans, soft (the old park's bright hiss drowned
            // the music, LEARNINGS G2).
            Palms(mix.Add(-0.6f, 0.1f, 0.4f), 911, 0.07);
            Airy(mix.Add(0.6f, 0f, 0.3f), 912, 1100, 0.7, 0.07, 0.2f, 3);
            // Small waves on the bay's edge beyond the lawn, and the city's hum behind.
            Lapping(mix.Add(0.5f, 0.25f, 0.9f), 913, 0.6, 0.8f);
            Rumble(mix.Add(0f, 0.1f, 0.35f), 914, 180, 0.05, 0.4f);
            // Children playing far across the lawn.
            var rng = new Random(915);
            for (int v = 0; v < 2; v++)
                Voices.Chatter(mix.Add((float)(rng.NextDouble() * 1.2 - 0.6), 0.75f, 0.05f), 916 + v * 7, 290 + rng.NextDouble() * 60);
            return Finish(mix, Soundscape.MuseumPark);
        }

        /// <summary>A seawall's water for the whole loop: a slap every one to three seconds (fewer at a lower rate), each its own size.</summary>
        static void Lapping(Track t, int seed, double rate, float size)
        {
            var r = new Random(seed);
            for (double at = r.NextDouble(); at < BedSeconds; at += (0.8 + r.NextDouble() * 1.7) / rate)
                Things.Slap(t, at, size * (float)(0.45 + r.NextDouble() * 0.55), r);
        }

        /// <summary>
        /// Palm fronds in the breeze: their stiff leaflets knocking together, a scatter of dry clicks that thickens
        /// with each gust, over a soft swish. Sparse clicks rather than a steady hiss, so it stays behind the music.
        /// </summary>
        static void Palms(Track t, int seed, double gustHz)
        {
            var n = new NoiseSource(seed);
            var gust = new Drift(seed + 1, gustHz);
            var flutter = new Drift(seed + 2, 6);
            var rattle = new Svf();
            var swish = new Svf();
            float tick = 0f;
            Layer(t, i =>
            {
                float g = gust.Next(), gg = g * g;
                if (n.Value() < 0.001 + 0.012 * gg * gg) tick = (float)(0.4 + 0.6 * n.Value());
                tick *= 0.93f;
                rattle.Process(n.White() * tick, 2200, 1.4);
                swish.Process(n.Pink(), 800 + 400 * g, 0.8);
                return rattle.band * (0.5f + 0.5f * flutter.Next()) + swish.band * (0.1f + 0.5f * gg);
            });
        }

        /// <summary>
        /// Air-conditioner condensers on the walls: the compressors' hum at 120 Hz (twice America's 60 Hz mains) and
        /// its harmonics, and their fans' low whoosh beating with the blades. Every frequency is a whole number of
        /// cycles in the loop, so it folds seamlessly.
        /// </summary>
        static void Condenser(Track t, int seed)
        {
            var n = new NoiseSource(seed);
            var fan = new Svf();
            var d = new Drift(seed + 1, 0.2);
            Layer(t, i =>
            {
                double tt = i / (double)Sr;
                double hum = Math.Sin(TwoPi * 120 * tt) + 0.6 * Math.Sin(TwoPi * 180 * tt) + 0.35 * Math.Sin(TwoPi * 240 * tt) + 0.2 * Math.Sin(TwoPi * 360 * tt);
                fan.Process(n.Pink(), 450, 0.7);
                double blades = 1 - 0.3 * (0.5 + 0.5 * Math.Sin(TwoPi * 17 * tt));
                return (float)(hum * 0.25 + fan.band * 1.2 * blades) * (0.85f + 0.15f * d.Next());
            });
        }

        /// <summary>Cicadas in the trees: a soft buzz of tymbal clicks that swells and fades as they take it up and leave off.</summary>
        static void Cicadas(Track t, int seed)
        {
            var n = new NoiseSource(seed);
            var f = new Svf();
            var swell = new Drift(seed + 1, 0.06);
            var pulse = new Drift(seed + 2, 5);
            double ph = 0;
            Layer(t, i =>
            {
                float s = 0.25f + 0.75f * swell.Next();
                ph += (170 + 40 * s) / Sr;
                double p = ph - Math.Floor(ph);
                f.Process(n.White() * (float)Math.Exp(-p * 10), 3900, 3);
                return f.band * s * s * (0.6f + 0.4f * pulse.Next());
            });
        }

        // ================= Cues =================

        /// <summary>Render a one-shot through a small mix (a touch of the place's reverb), padded for its tail.</summary>
        static AmbientCue Cue(string name, double seconds, float reverb, float room, Action<Track, Random> draw, int seed,
            float minGap, float maxGap, float volume, float pan, float panSpread, float pitchVariance = 0.06f, bool sweep = false)
        {
            int len = (int)((seconds + (reverb > 0f ? 0.4 + room * 2.2 : 0.05)) * Sr);
            var mix = new Mixdown(len) { roomSize = room, damping = 0.4f, wet = reverb };
            var tr = mix.Add(0f, 1f);
            draw(tr, new Random(seed));
            var clip = mix.Render(0f, 0.6f);
            FadeEdges(clip);
            return new AmbientCue
            {
                name = name, clip = clip, minGap = minGap, maxGap = maxGap, volume = volume,
                pan = pan, panSpread = panSpread, pitchVariance = pitchVariance, sweep = sweep,
            };
        }

        static void FadeEdges(float[] stereo)
        {
            int frames = stereo.Length / 2, fade = Math.Min(frames / 4, (int)(0.03 * Sr));
            for (int i = 0; i < fade; i++)
            {
                float k = i / (float)fade;
                stereo[2 * (frames - 1 - i)] *= k;
                stereo[2 * (frames - 1 - i) + 1] *= k;
            }
        }

        static void MenuCues(List<AmbientCue> c)
        {
            c.Add(Cue("robin", 2.4, 0.2f, 0.5f, (t, r) => Birds.Robin(t, 0.1, r), 101, 7, 16, 0.32f, 0.3f, 0.6f));
            c.Add(Cue("tit", 2.2, 0.2f, 0.5f, (t, r) => Birds.Tit(t, 0.1, r), 102, 10, 22, 0.26f, -0.3f, 0.6f));
        }

        static void StreetCues(List<AmbientCue> c)
        {
            c.Add(Cue("car", 6, 0.15f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 1.0), 201, 7, 15, 0.55f, 0f, 0f, 0.08f, true));
            c.Add(Cue("van", 7, 0.15f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 6.5, 1f, r.Next(), 0.75), 202, 18, 34, 0.5f, 0f, 0f, 0.06f, true));
            c.Add(Cue("horn", 1.2, 0.3f, 0.6f, (t, r) => Vehicle.Horn(t, 0.1, r), 203, 25, 50, 0.22f, 0.4f, 0.5f));
            c.Add(Cue("bicycle", 1.4, 0.2f, 0.5f, (t, r) => Things.BicycleBell(t, 0.05), 204, 28, 55, 0.24f, -0.3f, 0.5f));
            c.Add(Cue("dog", 1.5, 0.35f, 0.6f, (t, r) => Animals.Bark(t, 0.1, r, 2), 205, 22, 45, 0.2f, 0.5f, 0.4f, 0.1f));
            c.Add(Cue("church", 7.5, 0.4f, 0.8f, (t, r) => Things.ChurchBell(t, 0.05, 3), 206, 50, 90, 0.2f, -0.5f, 0.2f, 0f));
            c.Add(Cue("sparrows", 2.5, 0.2f, 0.5f, (t, r) => { Birds.Sparrow(t, 0.1, r); Birds.Sparrow(t, 1.2, r); }, 207, 6, 13, 0.24f, 0f, 0.8f));
            c.Add(Cue("pigeon", 3, 0.2f, 0.5f, (t, r) => Birds.WoodPigeon(t, 0.1), 208, 26, 48, 0.2f, 0.5f, 0.4f, 0.04f));
        }

        static void MarketCues(List<AmbientCue> c)
        {
            c.Add(Cue("shopBell", 1.6, 0.25f, 0.5f, (t, r) => Things.ShopBell(t, 0.05, r), 301, 12, 24, 0.26f, 0f, 0.8f));
            c.Add(Cue("cart", 3.2, 0.2f, 0.5f, (t, r) => Things.Cart(t, 0.05, 3, r), 302, 18, 34, 0.32f, 0f, 0f, 0.06f, true));
            c.Add(Cue("pigeons", 3, 0.2f, 0.5f, (t, r) => { Birds.Pigeon(t, 0.1); Animals.Wings(t, 1.6, r); }, 303, 14, 28, 0.3f, 0f, 0.7f));
            c.Add(Cue("clock", 6, 0.45f, 0.8f, (t, r) => Things.ClockChime(t, 0.05), 304, 55, 95, 0.18f, 0.4f, 0.3f, 0f));
            c.Add(Cue("bicycle", 1.4, 0.2f, 0.5f, (t, r) => Things.BicycleBell(t, 0.05), 305, 26, 50, 0.22f, 0f, 0.7f));
            c.Add(Cue("laugh", 1.2, 0.35f, 0.6f, (t, r) => Voices.Laugh(t, 0.05, r), 306, 35, 70, 0.08f, 0f, 0.8f, 0.12f));
            c.Add(Cue("van", 6, 0.2f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 0.6), 307, 28, 50, 0.35f, 0f, 0f, 0.06f, true));
        }

        static void BeachCues(List<AmbientCue> c)
        {
            c.Add(Cue("gull", 1.6, 0.2f, 0.6f, (t, r) => Birds.Gull(t, 0.05, r, 1 + r.Next(3)), 401, 4, 10, 0.32f, 0f, 0.8f, 0.08f));
            c.Add(Cue("gullLaugh", 2.2, 0.2f, 0.6f, (t, r) => Birds.GullLaugh(t, 0.05, r), 402, 9, 20, 0.28f, 0f, 0.8f, 0.08f));
            c.Add(Cue("gullFar", 1.6, 0.45f, 0.8f, (t, r) => Birds.Gull(t, 0.05, r, 2), 403, 6, 14, 0.14f, 0f, 0.9f, 0.1f));
            c.Add(Cue("buoy", 6, 0.35f, 0.8f, (t, r) => Things.BuoyBell(t, 0.05, r), 404, 35, 65, 0.16f, -0.6f, 0.3f, 0.03f));
            c.Add(Cue("ship", 5, 0.5f, 0.9f, (t, r) => Things.ShipHorn(t, 0.1), 405, 70, 130, 0.14f, 0.6f, 0.3f, 0.02f));
            c.Add(Cue("splash", 1.2, 0.15f, 0.5f, (t, r) => Things.Splash(t, 0.05, r), 406, 15, 32, 0.18f, 0f, 0.8f));
        }

        static void UnderpassCues(List<AmbientCue> c)
        {
            c.Add(Cue("drip", 0.5, 0.6f, 0.9f, (t, r) => Things.Drip(t, 0.02, r), 501, 2.5f, 7, 0.3f, 0f, 0.9f, 0.15f));
            c.Add(Cue("train", 9, 0.4f, 0.9f, (t, r) => Vehicle.Train(t, 0.1, 8.5, r), 502, 30, 55, 0.6f, 0f, 0f, 0.04f, true));
            c.Add(Cue("steps", 4, 0.55f, 0.9f, (t, r) => Things.Footsteps(t, 0.1, 6, r), 503, 18, 34, 0.24f, 0f, 0.8f, 0.06f));
            c.Add(Cue("flutter", 1.5, 0.5f, 0.9f, (t, r) => Animals.Wings(t, 0.05, r), 504, 30, 60, 0.2f, 0f, 0.8f));
            c.Add(Cue("hornEcho", 1.2, 0.6f, 0.95f, (t, r) => Vehicle.Horn(t, 0.1, r), 505, 35, 70, 0.14f, 0f, 0.8f));
            c.Add(Cue("car", 6, 0.55f, 0.9f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 0.6), 506, 12, 24, 0.35f, 0f, 0f, 0.06f, true));
        }

        static void SiteCues(List<AmbientCue> c)
        {
            c.Add(Cue("reversing", 6.5, 0.25f, 0.6f, (t, r) => Machines.Reversing(t, 0.05, 7), 601, 22, 40, 0.24f, 0.5f, 0.4f, 0.02f));
            c.Add(Cue("jackhammer", 3, 0.25f, 0.6f, (t, r) => Machines.Jackhammer(t, 0.05, 1.6 + r.NextDouble() * 1.2, r), 602, 10, 22, 0.32f, -0.4f, 0.5f, 0.05f));
            c.Add(Cue("hammer", 3.6, 0.3f, 0.6f, (t, r) => Machines.Hammering(t, 0.05, 4 + r.Next(4), r), 603, 8, 17, 0.32f, 0f, 0.8f, 0.06f));
            c.Add(Cue("digger", 5, 0.25f, 0.6f, (t, r) => Machines.Digger(t, 0.05), 604, 25, 45, 0.38f, 0.3f, 0.5f, 0.05f));
            c.Add(Cue("drill", 3, 0.25f, 0.6f, (t, r) => Machines.Drill(t, 0.05, r), 605, 20, 40, 0.18f, 0f, 0.8f, 0.06f));
            c.Add(Cue("airBrake", 1.4, 0.3f, 0.6f, (t, r) => Machines.AirBrake(t, 0.05, r), 606, 35, 70, 0.22f, 0f, 0.8f));
            c.Add(Cue("pipes", 2.2, 0.3f, 0.6f, (t, r) => Machines.Pipes(t, 0.05, r), 607, 40, 75, 0.28f, 0f, 0.8f, 0.05f));
            c.Add(Cue("truck", 7, 0.2f, 0.6f, (t, r) => Vehicle.Pass(t, 0, 6.5, 1f, r.Next(), 0.55), 608, 25, 45, 0.45f, 0f, 0f, 0.04f, true));
        }

        static void ParkCues(List<AmbientCue> c)
        {
            c.Add(Cue("robin", 2.4, 0.2f, 0.6f, (t, r) => Birds.Robin(t, 0.1, r), 701, 4, 9, 0.3f, 0f, 0.9f));
            c.Add(Cue("tit", 2.2, 0.2f, 0.6f, (t, r) => Birds.Tit(t, 0.1, r), 702, 5, 12, 0.26f, 0f, 0.9f));
            c.Add(Cue("blackbird", 3, 0.25f, 0.6f, (t, r) => Birds.Blackbird(t, 0.1, r), 703, 8, 18, 0.3f, 0f, 0.9f));
            c.Add(Cue("woodpigeon", 3, 0.25f, 0.6f, (t, r) => Birds.WoodPigeon(t, 0.1), 704, 16, 32, 0.24f, 0f, 0.8f, 0.04f));
            c.Add(Cue("ducks", 1.6, 0.2f, 0.6f, (t, r) => Animals.Quacks(t, 0.05, r), 705, 15, 30, 0.24f, 0.5f, 0.4f, 0.08f));
            c.Add(Cue("woodpecker", 1.4, 0.35f, 0.7f, (t, r) => Birds.Woodpecker(t, 0.05, r), 706, 30, 60, 0.18f, -0.5f, 0.4f, 0.06f));
            c.Add(Cue("dog", 1.5, 0.35f, 0.6f, (t, r) => Animals.Bark(t, 0.1, r, 1 + r.Next(2)), 707, 25, 50, 0.16f, 0f, 0.8f, 0.1f));
            c.Add(Cue("bicycle", 1.4, 0.2f, 0.5f, (t, r) => Things.BicycleBell(t, 0.05), 708, 30, 60, 0.2f, 0f, 0.8f));
        }

        // ---------- Florida's places ----------

        static void HavanaCues(List<AmbientCue> c)
        {
            c.Add(Cue("rooster", 2.0, 0.3f, 0.6f, (t, r) => Birds.Rooster(t, 0.05, r), 1101, 30, 60, 0.22f, -0.5f, 0.4f, 0.05f));
            c.Add(Cue("hens", 2.4, 0.2f, 0.5f, (t, r) => Birds.Hen(t, 0.05, r), 1102, 12, 26, 0.22f, 0f, 0.8f, 0.08f));
            c.Add(Cue("dominoes", 2.6, 0.2f, 0.5f, (t, r) => Things.DominoShuffle(t, 0.05, 2.2, r), 1103, 20, 40, 0.28f, -0.35f, 0.3f, 0.04f));
            c.Add(Cue("moped", 6, 0.15f, 0.5f, (t, r) => Vehicle.Moped(t, 0, 5.5, r), 1104, 20, 40, 0.35f, 0f, 0f, 0.08f, true));
            c.Add(Cue("car", 7, 0.15f, 0.5f, (t, r) => Vehicle.Pass(t, 0, 6.5, 1f, r.Next(), 0.9), 1105, 14, 28, 0.45f, 0f, 0f, 0.06f, true));
            c.Add(Cue("call", 1.0, 0.35f, 0.6f, (t, r) => Voices.Call(t, 0.05, r), 1106, 30, 60, 0.1f, 0f, 0.8f, 0.1f));
        }

        static void MiamiRiverCues(List<AmbientCue> c)
        {
            c.Add(Cue("outboard", 10, 0.15f, 0.6f, (t, r) => Vehicle.Outboard(t, 0, 9, r), 1201, 22, 45, 0.4f, 0f, 0f, 0.06f, true));
            c.Add(Cue("tugHorn", 4, 0.5f, 0.9f, (t, r) => Things.TugHorn(t, 0.1), 1202, 60, 120, 0.14f, 0.5f, 0.3f, 0.03f));
            c.Add(Cue("bridgeBell", 7, 0.35f, 0.8f, (t, r) => Things.BridgeBell(t, 0.05, 6), 1203, 70, 130, 0.14f, -0.5f, 0.3f, 0.01f));
            c.Add(Cue("halyard", 2.5, 0.25f, 0.6f, (t, r) => Things.Halyard(t, 0.05, r, 3 + r.Next(3)), 1204, 9, 20, 0.2f, 0f, 0.8f, 0.08f));
            c.Add(Cue("laughingGull", 3.2, 0.2f, 0.6f, (t, r) => Birds.LaughingGull(t, 0.05, r), 1205, 8, 18, 0.28f, 0f, 0.8f, 0.06f));
            c.Add(Cue("laughingGullFar", 3.2, 0.45f, 0.8f, (t, r) => Birds.LaughingGull(t, 0.05, r), 1206, 10, 22, 0.13f, 0f, 0.9f, 0.08f));
        }

        static void BayCues(List<AmbientCue> c)
        {
            c.Add(Cue("laughingGull", 3.2, 0.2f, 0.6f, (t, r) => Birds.LaughingGull(t, 0.05, r), 1301, 6, 14, 0.28f, 0f, 0.8f, 0.06f));
            c.Add(Cue("laughingGullFar", 3.2, 0.45f, 0.8f, (t, r) => Birds.LaughingGull(t, 0.05, r), 1302, 8, 16, 0.13f, 0f, 0.9f, 0.08f));
            c.Add(Cue("cruiseHorn", 5.5, 0.5f, 0.9f, (t, r) => Things.CruiseHorn(t, 0.1), 1303, 80, 140, 0.14f, 0.5f, 0.3f, 0.02f));
            c.Add(Cue("pelican", 2, 0.15f, 0.5f, (t, r) => Things.PelicanDive(t, 0.05, r), 1304, 18, 36, 0.2f, 0f, 0.8f, 0.06f));
            c.Add(Cue("seawall", 1.8, 0.2f, 0.5f, (t, r) => { Things.Slap(t, 0.05, 1f, r); Things.Slap(t, 0.6, 0.6f, r); }, 1305, 8, 16, 0.26f, 0f, 0.6f, 0.06f));
        }

        static void DowntownCues(List<AmbientCue> c)
        {
            c.Add(Cue("car", 6, 0.2f, 0.6f, (t, r) => Vehicle.Pass(t, 0, 5.5, 1f, r.Next(), 0.9), 1401, 6, 14, 0.5f, 0f, 0f, 0.08f, true));
            c.Add(Cue("busBrakes", 2.6, 0.3f, 0.7f, (t, r) => Vehicle.BusBrakes(t, 0.05, r), 1402, 18, 36, 0.2f, 0f, 0.8f, 0.04f));
            c.Add(Cue("horn", 1.2, 0.35f, 0.7f, (t, r) => Vehicle.Horn(t, 0.1, r), 1403, 18, 40, 0.2f, 0f, 0.8f));
            c.Add(Cue("crane", 4.2, 0.45f, 0.85f, (t, r) => Machines.CraneBeeps(t, 0.05, 6 + r.Next(5)), 1404, 30, 60, 0.13f, 0.5f, 0.4f, 0.02f));
            c.Add(Cue("jackhammerFar", 3, 0.5f, 0.85f, (t, r) => Machines.Jackhammer(t, 0.05, 1.4 + r.NextDouble() * 1.4, r), 1405, 22, 45, 0.15f, -0.5f, 0.4f, 0.05f));
            c.Add(Cue("parrots", 5, 0.25f, 0.7f, (t, r) => Birds.Parrots(t, 0.05, r), 1406, 35, 70, 0.26f, 0f, 0f, 0.06f, true));
        }

        static void UnderlineCues(List<AmbientCue> c)
        {
            c.Add(Cue("metrorail", 12, 0.35f, 0.8f, (t, r) => Vehicle.Metrorail(t, 0.1, 11.5, r), 1501, 35, 60, 0.5f, 0f, 0f, 0.03f, true));
            c.Add(Cue("bicycle", 1.8, 0.2f, 0.5f, (t, r) => Things.RingBell(t, 0.05, r), 1502, 16, 32, 0.2f, 0f, 0.8f));
            c.Add(Cue("jogger", 5, 0.15f, 0.5f, (t, r) => Things.Jogger(t, 0.1, 12, r), 1503, 14, 28, 0.24f, 0f, 0f, 0.05f, true));
            c.Add(Cue("cicada", 8, 0.2f, 0.6f, (t, r) => Animals.Cicada(t, 0.1, 7.5, r), 1504, 20, 40, 0.14f, 0f, 0.8f, 0.05f));
            c.Add(Cue("mockingbird", 5, 0.2f, 0.6f, (t, r) => Birds.Mockingbird(t, 0.1, r), 1505, 8, 16, 0.26f, 0f, 0.9f, 0.04f));
        }

        static void MuseumParkCues(List<AmbientCue> c)
        {
            c.Add(Cue("mockingbird", 5, 0.2f, 0.6f, (t, r) => Birds.Mockingbird(t, 0.1, r), 1601, 6, 14, 0.28f, 0f, 0.9f, 0.04f));
            c.Add(Cue("grackle", 2.4, 0.2f, 0.6f, (t, r) => Birds.Grackle(t, 0.05, r), 1602, 10, 22, 0.22f, 0f, 0.9f, 0.05f));
            c.Add(Cue("sprinkler", 8, 0.15f, 0.5f, (t, r) => Things.Sprinkler(t, 0.05, 7.5, r), 1603, 25, 50, 0.22f, 0.5f, 0.4f, 0.03f));
            c.Add(Cue("kids", 2.5, 0.45f, 0.8f, (t, r) => Voices.Kids(t, 0.05, r), 1604, 15, 30, 0.1f, 0f, 0.8f, 0.08f));
            c.Add(Cue("laughingGullFar", 3.2, 0.45f, 0.8f, (t, r) => Birds.LaughingGull(t, 0.05, r), 1605, 12, 25, 0.13f, 0f, 0.9f, 0.08f));
        }

        // ================= Sound makers =================

        static int At(double seconds) { return (int)(seconds * Sr); }

        /// <summary>A whistled note sliding from one pitch to another, with an optional trill.</summary>
        static void Whistle(Track t, double at, double dur, double f0, double f1, float amp, double trillHz = 0, double trillDepth = 0, double curve = 1)
        {
            int s = At(at), n = At(dur);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double u = i / (double)n;
                double f = f0 + (f1 - f0) * Math.Pow(u, curve);
                if (trillHz > 0) f *= 1 + trillDepth * Math.Sin(TwoPi * trillHz * i / Sr);
                f = Math.Min(f, Sr * 0.45);
                ph += f / Sr;
                double env = Math.Sin(Math.PI * u);
                t.Add(s + i, (float)(Math.Sin(TwoPi * ph) * env * env) * amp);
            }
        }

        /// <summary>A buzzy, voiced sound shaped by two formants: barks, quacks, gulls, voices.</summary>
        static void Formant(Track t, double at, double dur, Func<double, double> pitch, double f1, double f2, float amp, double noise, int seed,
            double attack = 0.01, double releaseShape = 1.5, double rough = 0)
        {
            int s = At(at), n = At(dur);
            var a = new Svf();
            var b = new Svf();
            var ns = new NoiseSource(seed);
            double ph = 0;
            for (int i = 0; i < n; i++)
            {
                double u = i / (double)n, tt = i / (double)Sr;
                ph += pitch(u) / Sr;
                double p = ph - Math.Floor(ph);
                double src = (2 * p - 1) * (1 - noise) + ns.White() * noise;
                if (rough > 0) src *= 1 - rough * (0.5 + 0.5 * Math.Sin(TwoPi * 75 * tt));
                a.Process((float)src, f1, 4);
                b.Process((float)src, f2, 5);
                double env = Math.Min(1, tt / attack) * Math.Pow(1 - u, releaseShape);
                t.Add(s + i, (float)((a.band + b.band * 0.7) * env) * amp);
            }
        }

        static void NoiseBurst(Track t, double at, double dur, double centre, double q, float amp, int seed, double attack = 0.002, double decay = 30, bool high = false)
        {
            int s = At(at), n = At(dur);
            var f = new Svf();
            var ns = new NoiseSource(seed);
            for (int i = 0; i < n; i++)
            {
                double tt = i / (double)Sr;
                f.Process(ns.White(), centre, q);
                double env = Math.Min(1, tt / attack) * Math.Exp(-tt * decay) * Math.Min(1, (n - i) / (0.01 * Sr));
                t.Add(s + i, (float)((high ? f.high : f.band) * env) * amp);
            }
        }

        /// <summary>A struck metal or bell: inharmonic partials, each with its own decay.</summary>
        static void Strike(Track t, double at, double freq, double[] ratios, double[] amps, double decay, float gain, double dur)
        {
            int s = At(at), n = At(dur);
            for (int k = 0; k < ratios.Length; k++)
            {
                double f = freq * ratios[k];
                if (f > Sr * 0.45) continue;
                double ph = 0, d = decay * (1 + k * 0.5);
                for (int i = 0; i < n; i++)
                {
                    double tt = i / (double)Sr;
                    ph += f / Sr;
                    double fade = Math.Min(1, (n - i) / (0.03 * Sr));
                    t.Add(s + i, (float)(Math.Sin(TwoPi * ph) * Math.Exp(-tt * d) * Math.Min(1, tt / 0.001) * fade * amps[k]) * gain);
                }
            }
        }

        static class Birds
        {
            public static void Sparrow(Track t, double at, Random r)
            {
                int chirps = 2 + r.Next(4);
                for (int i = 0; i < chirps; i++)
                {
                    double f = 3600 + r.NextDouble() * 1400;
                    Whistle(t, at + i * (0.11 + r.NextDouble() * 0.06), 0.05 + r.NextDouble() * 0.03, f, f * (0.75 + r.NextDouble() * 0.15), 0.5f, 0, 0, 0.6);
                }
            }

            /// <summary>A robin's wistful warble: quick runs of high slides and trills, rising and falling.</summary>
            public static void Robin(Track t, double at, Random r)
            {
                double time = at;
                int notes = 8 + r.Next(6);
                for (int i = 0; i < notes; i++)
                {
                    double f = 2800 + r.NextDouble() * 3200;
                    double d = 0.04 + r.NextDouble() * 0.09;
                    bool trill = r.NextDouble() < 0.3;
                    Whistle(t, time, d, f, f * (0.7 + r.NextDouble() * 0.6), 0.45f, trill ? 60 : 0, trill ? 0.06 : 0);
                    time += d + 0.02 + r.NextDouble() * 0.05;
                }
            }

            /// <summary>A great tit's "tea-cher, tea-cher, tea-cher".</summary>
            public static void Tit(Track t, double at, Random r)
            {
                double hi = 5200 + r.NextDouble() * 600, lo = hi * 0.72;
                int reps = 3 + r.Next(2);
                for (int i = 0; i < reps; i++)
                {
                    double s = at + i * 0.38;
                    Whistle(t, s, 0.11, hi, hi * 0.97, 0.45f);
                    Whistle(t, s + 0.14, 0.13, lo, lo * 0.9, 0.4f);
                }
            }

            /// <summary>A blackbird's fluting phrase: low, mellow whistles with glides, and a squeaky flourish.</summary>
            public static void Blackbird(Track t, double at, Random r)
            {
                double time = at;
                int notes = 4 + r.Next(3);
                for (int i = 0; i < notes; i++)
                {
                    double f = 1600 + r.NextDouble() * 1100;
                    double d = 0.12 + r.NextDouble() * 0.2;
                    Whistle(t, time, d, f, f * (0.85 + r.NextDouble() * 0.35), 0.5f, 7, 0.015, 0.8);
                    time += d + 0.04;
                }
                for (int i = 0; i < 3; i++) Whistle(t, time + i * 0.05, 0.04, 5200 + i * 500, 4400, 0.25f);
            }

            /// <summary>A wood pigeon's soft "coo-COO-coo, coo-coo".</summary>
            public static void WoodPigeon(Track t, double at)
            {
                double[] times = { 0, 0.42, 1.0, 1.45, 1.8 };
                double[] durs = { 0.35, 0.5, 0.3, 0.28, 0.28 };
                double[] amps = { 0.6, 1, 0.7, 0.6, 0.6 };
                for (int i = 0; i < times.Length; i++)
                    Formant(t, at + times[i], durs[i], u => 430 + 40 * Math.Sin(Math.PI * u), 450, 900, (float)amps[i] * 0.5f, 0.02, 7 + i, 0.05, 0.6);
            }

            /// <summary>A town pigeon's throaty "croo-croo-croooo".</summary>
            public static void Pigeon(Track t, double at)
            {
                for (int i = 0; i < 3; i++)
                    Formant(t, at + i * 0.45, i == 2 ? 0.6 : 0.32, u => 360 + 60 * Math.Sin(Math.PI * u) - (i == 2 ? 60 * u : 0), 420, 850, 0.5f, 0.05, 30 + i, 0.04, 0.8, 0.4);
            }

            /// <summary>A herring gull's "kyow": a harsh, falling cry, one to three times.</summary>
            public static void Gull(Track t, double at, Random r, int calls)
            {
                for (int i = 0; i < calls; i++)
                {
                    double peak = 1400 + r.NextDouble() * 400, d = 0.32 + r.NextDouble() * 0.15;
                    Formant(t, at + i * (d + 0.08), d, u => u < 0.25 ? peak * (0.75 + u) : peak * (1.0 - 0.45 * (u - 0.25)), 1900, 3300, 0.55f, 0.18, r.Next(), 0.02, 0.9, 0.35);
                }
            }

            /// <summary>A gull's laugh: "ha-ha-ha-ha-haa", quick and falling.</summary>
            public static void GullLaugh(Track t, double at, Random r)
            {
                int n = 5 + r.Next(4);
                double f = 1600 + r.NextDouble() * 300;
                for (int i = 0; i < n; i++)
                {
                    double ff = f * (1 - i * 0.03);
                    Formant(t, at + i * 0.17, 0.12, u => ff * (1 - 0.15 * u), 1800, 3100, 0.5f, 0.2, r.Next(), 0.01, 1.2, 0.3);
                }
            }

            /// <summary>A woodpecker drumming on a trunk: a fast roll of knocks, slowing as it fades.</summary>
            public static void Woodpecker(Track t, double at, Random r)
            {
                double time = at, gap = 0.045;
                for (int i = 0; i < 18; i++)
                {
                    NoiseBurst(t, time, 0.03, 1100, 3, 0.8f * (float)Math.Pow(0.95, i), r.Next(), 0.0008, 120);
                    time += gap;
                    gap *= 1.02;
                }
            }

            /// <summary>A rooster crowing from a yard (Little Havana's roosters roam its streets): "cock-a-doodle-doooo",
            /// three short syllables climbing, then the long call that rises, holds and falls away.</summary>
            public static void Rooster(Track t, double at, Random r)
            {
                double f = 520 + r.NextDouble() * 120;
                Formant(t, at, 0.13, u => f * (0.9 + 0.2 * u), 1100, 2400, 0.5f, 0.25, r.Next(), 0.01, 1.0, 0.4);
                Formant(t, at + 0.17, 0.1, u => f * 1.05, 1200, 2500, 0.45f, 0.25, r.Next(), 0.01, 1.0, 0.4);
                Formant(t, at + 0.31, 0.2, u => f * (1.1 + 0.15 * Math.Sin(Math.PI * u)), 1300, 2600, 0.55f, 0.25, r.Next(), 0.01, 0.8, 0.4);
                Formant(t, at + 0.56, 0.95, u => f * (1.25 + 0.15 * Math.Sin(Math.PI * Math.Min(1, u * 1.6)) - 0.45 * u * u), 1250, 2500, 0.6f, 0.3, r.Next(), 0.04, 0.35, 0.45);
            }

            /// <summary>A hen clucking about a yard: "buk, buk, buk", and now and then a "ba-GAWK".</summary>
            public static void Hen(Track t, double at, Random r)
            {
                int clucks = 3 + r.Next(4);
                double time = at, f = 330 + r.NextDouble() * 80;
                for (int i = 0; i < clucks; i++)
                {
                    Formant(t, time, 0.07, u => f * (1.1 - 0.2 * u), 800, 1900, 0.5f, 0.3, r.Next(), 0.005, 1.5, 0.3);
                    time += 0.16 + r.NextDouble() * 0.12;
                }
                if (r.NextDouble() < 0.5)
                    Formant(t, time + 0.05, 0.3, u => f * (1.3 + 0.5 * Math.Sin(Math.PI * u)), 1000, 2300, 0.55f, 0.3, r.Next(), 0.02, 1.2, 0.35);
            }

            /// <summary>A laughing gull, Florida's commonest gull: a long, nasal "kee-ah" or two, then a run of "ha"s,
            /// quick at first, slowing and falling as it laughs itself out (Kamakura's herring gulls cry "kyow").</summary>
            public static void LaughingGull(Track t, double at, Random r)
            {
                double f = 900 + r.NextDouble() * 200, time = at;
                int longs = 1 + r.Next(2);
                for (int i = 0; i < longs; i++)
                {
                    Formant(t, time, 0.32, u => f * (u < 0.3 ? 1.1 + u : 1.4 - 0.5 * (u - 0.3)), 1500, 2900, 0.55f, 0.12, r.Next(), 0.02, 0.9, 0.25);
                    time += 0.42;
                }
                int has = 6 + r.Next(5);
                double gap = 0.13, d = 0.08;
                for (int i = 0; i < has; i++)
                {
                    double ff = f * (1.25 - i * 0.025);
                    Formant(t, time, d, u => ff * (u < 0.3 ? 0.9 + u : 1.2 - 0.3 * u), 1500, 2900, 0.5f, 0.12, r.Next(), 0.008, 1.1, 0.25);
                    time += gap;
                    gap *= 1.09;
                    d *= 1.08;
                }
            }

            /// <summary>A flock of wild parrots (Miami's conures and parakeets) flying over: harsh, screeching squawks
            /// from several birds at once, calling over each other.</summary>
            public static void Parrots(Track t, double at, Random r)
            {
                int birds = 4 + r.Next(4);
                for (int b = 0; b < birds; b++)
                {
                    double f = 1000 + r.NextDouble() * 500, time = at + r.NextDouble() * 0.6;
                    int calls = 3 + r.Next(4);
                    for (int i = 0; i < calls && time < at + 4.2; i++)
                    {
                        double d = 0.1 + r.NextDouble() * 0.14, ff = f * (0.9 + r.NextDouble() * 0.2);
                        Formant(t, time, d, u => ff * (1 + 0.25 * Math.Sin(Math.PI * u)) * (1 + 0.06 * Math.Sin(TwoPi * 30 * u * d)), 2100, 3400, 0.4f, 0.3, r.Next(), 0.005, 1.0, 0.5);
                        time += d + 0.12 + r.NextDouble() * 0.35;
                    }
                }
            }

            /// <summary>A northern mockingbird singing from a lamp post: a phrase repeated two to four times, then
            /// another, each made up fresh (a slide, a quick triplet, a trill or a harsh "chek").</summary>
            public static void Mockingbird(Track t, double at, Random r)
            {
                double time = at;
                int phrases = 2 + r.Next(2);
                for (int p = 0; p < phrases && time < at + 3.6; p++)
                {
                    int kind = r.Next(4), reps = 2 + r.Next(3);
                    double f = 1800 + r.NextDouble() * 2400, f2 = f * (0.6 + r.NextDouble() * 0.9), d = 0.06 + r.NextDouble() * 0.1;
                    for (int k = 0; k < reps && time < at + 4.2; k++)
                    {
                        switch (kind)
                        {
                            case 0:
                                Whistle(t, time, d, f, f2, 0.45f);
                                time += d;
                                break;
                            case 1:
                                for (int j = 0; j < 3; j++) Whistle(t, time + j * 0.055, 0.04, f, f * 1.1, 0.4f);
                                time += 0.17;
                                break;
                            case 2:
                                Whistle(t, time, d + 0.08, f, f, 0.4f, 38, 0.08);
                                time += d + 0.08;
                                break;
                            default:
                                Formant(t, time, 0.07, u => 1100, 2200, 3600, 0.45f, 0.4, r.Next(), 0.003, 1.2, 0.3);
                                time += 0.07;
                                break;
                        }
                        time += 0.06;
                    }
                    time += 0.2 + r.NextDouble() * 0.2;
                }
            }

            /// <summary>A boat-tailed grackle: a couple of "chuck"s, a dry rattle, then its creaking, rising squeal,
            /// like a rusty gate.</summary>
            public static void Grackle(Track t, double at, Random r)
            {
                for (int i = 0; i < 2; i++)
                    Formant(t, at + i * 0.18, 0.06, u => 700, 1500, 2700, 0.4f, 0.35, r.Next(), 0.002, 1.5, 0.3);
                double time = at + 0.45;
                for (int j = 0; j < 8; j++) NoiseBurst(t, time + j * 0.035, 0.03, 1800, 2.5, 0.3f, r.Next(), 0.0005, 120);
                time += 0.35;
                Whistle(t, time, 0.5, 1200, 5200, 0.4f, 55, 0.05, 2.0);
                Whistle(t, time + 0.62, 0.22, 2400, 4600, 0.3f, 70, 0.04, 1.5);
            }
        }

        static class Animals
        {
            public static void Bark(Track t, double at, Random r, int barks)
            {
                for (int i = 0; i < barks; i++)
                {
                    double f = 380 + r.NextDouble() * 120;
                    Formant(t, at + i * (0.28 + r.NextDouble() * 0.1), 0.17, u => f * (1.15 - 0.35 * u), 800, 1700, 0.7f, 0.25, r.Next(), 0.008, 1.4, 0.2);
                }
            }

            public static void Quacks(Track t, double at, Random r)
            {
                int n = 2 + r.Next(3);
                for (int i = 0; i < n; i++)
                {
                    double f = 260 + r.NextDouble() * 60;
                    Formant(t, at + i * (0.2 + r.NextDouble() * 0.12), 0.16, u => f * (1.1 - 0.3 * u), 1150, 2200, 0.6f, 0.15, r.Next(), 0.01, 1.0, 0.5);
                }
            }

            /// <summary>Wings clapping as a bird takes off.</summary>
            public static void Wings(Track t, double at, Random r)
            {
                int flaps = 7 + r.Next(4);
                for (int i = 0; i < flaps; i++)
                    NoiseBurst(t, at + i * 0.1, 0.09, 900 + r.NextDouble() * 500, 0.8, (float)(0.6 * Math.Pow(0.9, i)), r.Next(), 0.01, 28);
            }

            /// <summary>A cicada in a tree, buzzing in the heat: a rattle of tymbal clicks that swells up, holds and winds down.</summary>
            public static void Cicada(Track t, double at, double dur, Random r)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(r.Next());
                var f = new Svf();
                double ph = 0, centre = 3600 + r.NextDouble() * 600;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n, tt = i / (double)Sr;
                    double rise = Math.Min(1, u / 0.3);
                    double env = rise * rise * Math.Min(1, (1 - u) / 0.25);
                    ph += (160 + 60 * env) / Sr;
                    double p = ph - Math.Floor(ph);
                    f.Process((float)(ns.White() * Math.Exp(-p * 10)), centre * (0.9 + 0.1 * env), 3);
                    double am = 0.7 + 0.3 * Math.Sin(TwoPi * 7 * tt);
                    t.Add(s + i, (float)(f.band * env * am) * 0.5f);
                }
            }
        }

        static class Voices
        {
            /// <summary>One person talking on and off for the whole loop: phrases of syllables (a buzz shaped into
            /// vowels) with the rise and fall of speech, and pauses between. Muffled: a crowd, not words.</summary>
            public static void Chatter(Track t, int seed, double f0)
            {
                var r = new Random(seed);
                var n = new NoiseSource(seed);
                var fa = new Svf();
                var fb = new Svf();
                var lp = new Svf();
                int total = t.Length + (int)(Fold * Sr);
                var amp = Scratch.Rent(total);
                var form1 = Scratch.Rent(total);
                var form2 = Scratch.Rent(total);
                var pitch = Scratch.Rent(total);
                double time = r.NextDouble() * 2;
                while (time < total / (double)Sr)
                {
                    double phrase = 1.2 + r.NextDouble() * 2.5;
                    double end = time + phrase;
                    double inflect = r.NextDouble() < 0.5 ? 1.15 : 0.9;
                    while (time < end)
                    {
                        double syl = 0.09 + r.NextDouble() * 0.16;
                        double v1 = 300 + r.NextDouble() * 500, v2 = 900 + r.NextDouble() * 1300;
                        int s0 = (int)(time * Sr), len = (int)(syl * Sr);
                        double pf = f0 * (1 + (inflect - 1) * ((time - (end - phrase)) / phrase)) * (0.95 + r.NextDouble() * 0.1);
                        float loud = (float)(0.5 + r.NextDouble() * 0.5);
                        for (int i = 0; i < len && s0 + i < total; i++)
                        {
                            double u = i / (double)len;
                            amp[s0 + i] = (float)(Math.Sin(Math.PI * u) * loud);
                            form1[s0 + i] = (float)v1;
                            form2[s0 + i] = (float)v2;
                            pitch[s0 + i] = (float)pf;
                        }
                        time += syl + r.NextDouble() * 0.03;
                    }
                    time += 0.4 + r.NextDouble() * 2.2;
                }
                double ph = 0;
                Layer(t, i =>
                {
                    if (amp[i] <= 0f) { lp.Process(0f, 1500, 0.7); return lp.low; }
                    ph += pitch[i] / Sr;
                    double p = ph - Math.Floor(ph);
                    float src = (float)((2 * p - 1) * 0.7 + n.White() * 0.3);
                    fa.Process(src, Math.Round(form1[i] / 50) * 50, 5);
                    fb.Process(src, Math.Round(form2[i] / 50) * 50, 6);
                    return lp.Process((fa.band + fb.band * 0.5f) * amp[i], 1500, 0.7);
                });
                Scratch.Return(amp);
                Scratch.Return(form1);
                Scratch.Return(form2);
                Scratch.Return(pitch);
            }

            public static void Laugh(Track t, double at, Random r)
            {
                int n = 4 + r.Next(3);
                double f = 220 + r.NextDouble() * 120;
                for (int i = 0; i < n; i++)
                {
                    double ff = f * (1.1 - i * 0.04);
                    Formant(t, at + i * 0.15, 0.1, u => ff, 750, 1250, 0.6f, 0.4, r.Next(), 0.01, 1.2);
                }
            }

            /// <summary>A neighbour calling out across the street: "o-YE!", a man's voice or a woman's.</summary>
            public static void Call(Track t, double at, Random r)
            {
                double f = r.NextDouble() < 0.5 ? 140 + r.NextDouble() * 40 : 230 + r.NextDouble() * 50;
                Formant(t, at, 0.16, u => f * (1 + 0.1 * u), 500, 900, 0.5f, 0.1, r.Next(), 0.02, 0.5);
                Formant(t, at + 0.17, 0.42, u => f * (1.35 + 0.15 * Math.Sin(Math.PI * u) - 0.3 * u), 600, 1900, 0.6f, 0.1, r.Next(), 0.02, 0.9);
            }

            /// <summary>Children playing far off: two or three shouts and calls, rising or falling, one after another.</summary>
            public static void Kids(Track t, double at, Random r)
            {
                int calls = 2 + r.Next(2);
                double time = at;
                for (int i = 0; i < calls; i++)
                {
                    double f = 300 + r.NextDouble() * 160, d = 0.25 + r.NextDouble() * 0.25;
                    bool rise = r.NextDouble() < 0.5;
                    Formant(t, time, d, u => f * (rise ? 1 + 0.35 * Math.Sin(Math.PI * u * 0.8) : 1.25 - 0.3 * u), 850 + r.NextDouble() * 300, 2200 + r.NextDouble() * 500, 0.5f, 0.15, r.Next(), 0.03, 0.8);
                    time += d + 0.1 + r.NextDouble() * 0.25;
                }
            }
        }

        static class Vehicle
        {
            /// <summary>A car (or with a lower engine, a van or truck) going by: tyres on the road and an engine,
            /// both loudest and brightest as it passes, the engine's note dropping as it goes (the Doppler shift).</summary>
            public static void Pass(Track t, double at, double dur, float gain, int seed, double engine)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(seed);
                var tyres = new Svf();
                var eng = new Svf();
                double ph = 0;
                double baseHz = 38 + 22 * engine;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double x = (u - 0.5) * 6;
                    double near = 1.0 / (1 + x * x);
                    double doppler = 1 + 0.08 * Math.Tanh(-x * 1.5);
                    ph += baseHz * doppler / Sr;
                    double p = ph - Math.Floor(ph);
                    double e = eng.Process((float)((p < 0.3 ? 1 : -1) + ns.White() * 0.3), 220 + 500 * near, 1.2);
                    double tyre = tyres.Process(ns.Pink(), 380 + 1500 * near, 0.6);
                    double env = near * Math.Min(1, u * 8) * Math.Min(1, (1 - u) * 8);
                    t.Add(s + i, (float)((tyre * 1.4 + e * 0.45 * engine) * env) * gain);
                }
            }

            /// <summary>Two short honks on a car's horn.</summary>
            public static void Horn(Track t, double at, Random r)
            {
                int honks = 1 + r.Next(2);
                for (int h = 0; h < honks; h++)
                {
                    int s = At(at + h * 0.32), n = At(h == honks - 1 ? 0.38 : 0.18);
                    var f = new Svf();
                    double p1 = 0, p2 = 0;
                    for (int i = 0; i < n; i++)
                    {
                        double tt = i / (double)Sr;
                        p1 += 415.0 / Sr;
                        p2 += 523.0 / Sr;
                        double sq = ((p1 - Math.Floor(p1)) < 0.5 ? 1 : -1) + ((p2 - Math.Floor(p2)) < 0.5 ? 1 : -1);
                        double env = Math.Min(1, tt / 0.01) * Math.Min(1, (n - i) / (0.02 * Sr));
                        t.Add(s + i, f.Process((float)sq, 1800, 0.9) * (float)env * 0.5f);
                    }
                }
            }

            /// <summary>A train crossing the bridge overhead: a swelling rumble, and the wheels' clack-clack over the rail joints.</summary>
            public static void Train(Track t, double at, double dur, Random r)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(r.Next());
                var lp = new Svf();
                var mid = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double env = Math.Pow(Math.Sin(Math.PI * u), 0.8);
                    double rumble = lp.Process(ns.Brown(), 110, 0.8) * 1.6;
                    mid.Process(ns.Pink(), 500 + 300 * env, 0.7);
                    t.Add(s + i, (float)((rumble + mid.band * 0.6) * env) * 0.8f);
                }
                // A pair of bogies at each end of every carriage: clack-clack ... clack-clack.
                double time = at + 0.6;
                while (time < at + dur - 0.5)
                {
                    double u = (time - at) / dur;
                    float g = (float)Math.Pow(Math.Sin(Math.PI * u), 1.2) * 0.9f;
                    NoiseBurst(t, time, 0.08, 600, 1.5, g, r.Next(), 0.001, 45);
                    NoiseBurst(t, time + 0.13, 0.08, 560, 1.5, g * 0.9f, r.Next(), 0.001, 45);
                    time += 0.85 + r.NextDouble() * 0.1;
                }
            }

            /// <summary>A moped buzzing by: a small two-stroke's high, rasping note through its little exhaust,
            /// wavering with the throttle and dropping as it passes.</summary>
            public static void Moped(Track t, double at, double dur, Random r)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(r.Next());
                var exhaust = new Svf();
                var tyres = new Svf();
                var rev = new Drift(r.Next(), 1.5);
                double ph = 0, baseHz = 105 + r.NextDouble() * 25;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n, x = (u - 0.5) * 6;
                    double near = 1.0 / (1 + x * x);
                    double doppler = 1 + 0.07 * Math.Tanh(-x * 1.5);
                    ph += baseHz * doppler * (0.94 + 0.12 * rev.Next()) / Sr;
                    double p = ph - Math.Floor(ph);
                    double pulse = Math.Exp(-p * 7) - 0.15 + ns.White() * 0.08;
                    exhaust.Process((float)pulse, 650 + 900 * near, 2.2);
                    double tyre = tyres.Process(ns.Pink(), 400 + 900 * near, 0.6);
                    double env = near * Math.Min(1, u * 8) * Math.Min(1, (1 - u) * 8);
                    t.Add(s + i, (float)((exhaust.band + exhaust.low * 0.5 + tyre * 0.2) * env));
                }
            }

            /// <summary>An outboard motor going by on the river: the engine's buzz and its gears' whine, dropping as it
            /// passes, over the hull's hiss through the water; then its wake slaps the seawall.</summary>
            public static void Outboard(Track t, double at, double dur, Random r)
            {
                int s = At(at), n = At(dur * 0.8);
                var ns = new NoiseSource(r.Next());
                var eng = new Svf();
                var hull = new Svf();
                double ph = 0, wph = 0, baseHz = 78 + r.NextDouble() * 18;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n, x = (u - 0.5) * 5;
                    double near = 1.0 / (1 + x * x);
                    double doppler = 1 + 0.06 * Math.Tanh(-x * 1.5);
                    ph += baseHz * doppler / Sr;
                    wph += baseHz * doppler * 7 / Sr;
                    double p = ph - Math.Floor(ph);
                    double e = eng.Process((float)((p < 0.25 ? 1 : -0.33) + ns.White() * 0.2), 400 + 900 * near, 1.4);
                    hull.Process(ns.Pink(), 900 + 1200 * near, 0.6);
                    double env = near * Math.Min(1, u * 6) * Math.Min(1, (1 - u) * 6);
                    t.Add(s + i, (float)((e * 0.7 + Math.Sin(TwoPi * wph) * 0.08 * near + hull.band * 0.9) * env));
                }
                for (int i = 0; i < 3; i++) Things.Slap(t, at + dur * 0.8 + i * (0.5 + r.NextDouble() * 0.2), 0.5f - i * 0.1f, r);
            }

            /// <summary>A Metrobus pulling in at a stop: its brakes' squeal, the air brakes' hiss as they set, and the
            /// sigh as it kneels to the kerb.</summary>
            public static void BusBrakes(Track t, double at, Random r)
            {
                Whistle(t, at, 0.5, 2300 + r.NextDouble() * 300, 2150, 0.12f, 6, 0.01);
                NoiseBurst(t, at + 0.45, 0.6, 3300, 0.6, 0.5f, r.Next(), 0.004, 5, true);
                NoiseBurst(t, at + 1.15, 1.2, 1300, 0.7, 0.3f, r.Next(), 0.06, 2.5);
            }

            /// <summary>The Metrorail going over on its concrete guideway: the deck's deep rumble, the wheels' hiss on
            /// the welded rail, a soft knock at each expansion joint, and the motors' whine rising as it pulls away from
            /// a station (or falling as it slows into one).</summary>
            public static void Metrorail(Track t, double at, double dur, Random r)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(r.Next());
                var deck = new Svf();
                var rail = new Svf();
                bool pulling = r.NextDouble() < 0.5;
                double ph = 0;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double env = Math.Pow(Math.Sin(Math.PI * u), 0.9);
                    double rumble = deck.Process(ns.Brown(), 95, 0.9) * 1.8;
                    rail.Process(ns.Pink(), 1100 + 600 * env, 0.8);
                    double k = pulling ? u : 1 - u;
                    ph += (420 + 700 * k * k) / Sr;
                    double whine = (Math.Sin(TwoPi * ph) + 0.4 * Math.Sin(TwoPi * 2 * ph)) * 0.3;
                    t.Add(s + i, (float)((rumble + rail.band * 0.5 + whine) * env) * 0.8f);
                }
                for (double time = at + 0.8; time < at + dur - 0.5; time += 1.2 + r.NextDouble() * 0.2)
                {
                    float g = (float)Math.Pow(Math.Sin(Math.PI * (time - at) / dur), 1.2) * 0.5f;
                    NoiseBurst(t, time, 0.1, 300, 1.2, g, r.Next(), 0.002, 30);
                    NoiseBurst(t, time + 0.11, 0.1, 280, 1.2, g * 0.8f, r.Next(), 0.002, 30);
                }
            }
        }

        static class Things
        {
            public static void Clink(Track t, double at, Random r)
            {
                double f = 2600 + r.NextDouble() * 1400;
                Strike(t, at, f, new[] { 1.0, 1.52, 2.4 }, new[] { 1.0, 0.5, 0.3 }, 18, 0.25f, 0.3);
                if (r.NextDouble() < 0.5) Strike(t, at + 0.09, f * 1.07, new[] { 1.0, 1.52 }, new[] { 1.0, 0.4 }, 22, 0.15f, 0.25);
            }

            public static void BicycleBell(Track t, double at)
            {
                for (int i = 0; i < 2; i++)
                {
                    double s = at + i * 0.32;
                    Strike(t, s, 2650, new[] { 1.0, 1.48, 2.1 }, new[] { 1.0, 0.6, 0.3 }, 3.5, 0.3f, 1.0);
                    Strike(t, s + 0.06, 2650, new[] { 1.0, 1.48, 2.1 }, new[] { 1.0, 0.6, 0.3 }, 3.5, 0.22f, 0.9);
                }
            }

            /// <summary>A church bell tolling in the distance (hum, prime, minor third, fifth and nominal partials).</summary>
            public static void ChurchBell(Track t, double at, int strokes)
            {
                double[] ratio = { 0.5, 1.0, 1.2, 1.5, 2.0, 2.5 };
                double[] amp = { 0.6, 1.0, 0.7, 0.4, 0.5, 0.2 };
                for (int i = 0; i < strokes; i++) Strike(t, at + i * 2.2, 311, ratio, amp, 0.9, 0.3f, 4.5);
            }

            /// <summary>A market clock striking the quarter: four notes.</summary>
            public static void ClockChime(Track t, double at)
            {
                double[] notes = { 659, 523, 587, 392 };
                for (int i = 0; i < notes.Length; i++)
                    Strike(t, at + i * 0.9, notes[i], new[] { 1.0, 2.0, 2.4, 3.0, 4.2 }, new[] { 1.0, 0.5, 0.3, 0.2, 0.1 }, 1.4, 0.3f, 2.6);
            }

            /// <summary>The little bell on a shop's door, swinging as the door opens.</summary>
            public static void ShopBell(Track t, double at, Random r)
            {
                int hits = 4 + r.Next(3);
                for (int i = 0; i < hits; i++)
                    Strike(t, at + i * (0.07 + r.NextDouble() * 0.03), 1960 + r.NextDouble() * 60, new[] { 1.0, 2.6, 4.1 }, new[] { 1.0, 0.4, 0.2 }, 5, 0.25f * (float)Math.Pow(0.82, i), 0.8);
            }

            /// <summary>A trolley rattling over the cobbles.</summary>
            public static void Cart(Track t, double at, double dur, Random r)
            {
                double time = at;
                while (time < at + dur)
                {
                    double u = (time - at) / dur;
                    float g = (float)Math.Sin(Math.PI * u);
                    NoiseBurst(t, time, 0.05, 700 + r.NextDouble() * 400, 1.0, g * (0.4f + (float)r.NextDouble() * 0.4f), r.Next(), 0.001, 70);
                    time += 0.05 + r.NextDouble() * 0.05;
                }
            }

            /// <summary>A buoy's bell rocking on the swell: irregular strokes.</summary>
            public static void BuoyBell(Track t, double at, Random r)
            {
                double time = at;
                for (int i = 0; i < 3; i++)
                {
                    Strike(t, time, 520, new[] { 1.0, 2.0, 2.76, 3.9 }, new[] { 1.0, 0.5, 0.4, 0.2 }, 1.3, 0.3f, 3);
                    time += 1.1 + r.NextDouble() * 0.9;
                }
            }

            public static void ShipHorn(Track t, double at)
            {
                int s = At(at), n = At(3.6);
                double p = 0;
                var f = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double tt = i / (double)Sr;
                    p += 98.0 / Sr;
                    double saw = 2 * (p - Math.Floor(p)) - 1;
                    double env = Math.Min(1, tt / 0.3) * Math.Min(1, (n - i) / (0.6 * Sr));
                    t.Add(s + i, f.Process((float)saw, 500, 1.0) * (float)env * 0.6f);
                }
            }

            public static void Splash(Track t, double at, Random r)
            {
                NoiseBurst(t, at, 0.8, 1400, 0.6, 0.6f, r.Next(), 0.005, 6);
                for (int i = 0; i < 5; i++)
                    Whistle(t, at + 0.08 + i * 0.06 + r.NextDouble() * 0.04, 0.04, 900 + r.NextDouble() * 900, 1800 + r.NextDouble() * 900, 0.2f);
            }

            /// <summary>A drop of water falling into a puddle: a quick rising "plink".</summary>
            public static void Drip(Track t, double at, Random r)
            {
                double f = 900 + r.NextDouble() * 700;
                Whistle(t, at, 0.06, f, f * 1.9, 0.6f, 0, 0, 0.5);
                NoiseBurst(t, at, 0.02, 3000, 1, 0.15f, r.Next(), 0.0005, 200);
            }

            /// <summary>Someone's shoes walking by: heel then toe on concrete.</summary>
            public static void Footsteps(Track t, double at, int steps, Random r)
            {
                for (int i = 0; i < steps; i++)
                {
                    double s = at + i * (0.5 + r.NextDouble() * 0.05);
                    float g = (float)Math.Sin(Math.PI * (i + 0.5) / steps);
                    NoiseBurst(t, s, 0.05, 2200, 1.2, 0.5f * g, r.Next(), 0.0008, 90);
                    NoiseBurst(t, s, 0.08, 250, 1.0, 0.6f * g, r.Next(), 0.002, 50);
                    NoiseBurst(t, s + 0.07, 0.04, 1500, 1.2, 0.25f * g, r.Next(), 0.001, 100);
                }
            }

            /// <summary>Water slopping against a seawall: a hollow clop, the slap on the stone and the water running back off it.</summary>
            public static void Slap(Track t, double at, float size, Random r)
            {
                NoiseBurst(t, at, 0.3, 200 + r.NextDouble() * 180, 2.2, 0.9f * size, r.Next(), 0.012, 12);
                NoiseBurst(t, at + 0.015, 0.14, 850 + r.NextDouble() * 500, 1.1, 0.35f * size, r.Next(), 0.004, 28);
                NoiseBurst(t, at + 0.1, 0.8, 1300 + r.NextDouble() * 700, 0.8, 0.1f * size, r.Next(), 0.12, 5);
                if (r.NextDouble() < 0.35) Whistle(t, at + 0.06, 0.07, 260 + r.NextDouble() * 120, 480 + r.NextDouble() * 200, 0.2f * size);
            }

            /// <summary>A domino played on a cafe table: the tile clicked down, or slammed with a knock on the wood.</summary>
            public static void Domino(Track t, double at, Random r)
            {
                bool slam = r.NextDouble() < 0.35;
                NoiseBurst(t, at, 0.04, 3000 + r.NextDouble() * 800, 2.0, slam ? 0.55f : 0.35f, r.Next(), 0.0004, 160);
                NoiseBurst(t, at, 0.1, 550 + r.NextDouble() * 200, 1.6, slam ? 0.7f : 0.25f, r.Next(), 0.0008, 50);
                if (!slam && r.NextDouble() < 0.5) NoiseBurst(t, at + 0.06 + r.NextDouble() * 0.03, 0.03, 3200, 2.0, 0.18f, r.Next(), 0.0004, 180);
            }

            /// <summary>The dominoes washed face down on the table before a game: a long clatter of tiles knocking together.</summary>
            public static void DominoShuffle(Track t, double at, double dur, Random r)
            {
                for (double time = at; time < at + dur; time += 0.025 + r.NextDouble() * 0.07)
                {
                    float g = (float)Math.Sin(Math.PI * (time - at) / dur);
                    NoiseBurst(t, time, 0.03, 2600 + r.NextDouble() * 1400, 1.8, g * (0.2f + (float)r.NextDouble() * 0.3f), r.Next(), 0.0004, 170);
                    if (r.NextDouble() < 0.2) NoiseBurst(t, time, 0.06, 600 + r.NextDouble() * 200, 1.4, g * 0.25f, r.Next(), 0.0008, 60);
                }
            }

            /// <summary>A halyard slapping a boat's aluminium mast in the breeze: a few hollow tinks, never in time.</summary>
            public static void Halyard(Track t, double at, Random r, int tinks)
            {
                double time = at, f = 1500 + r.NextDouble() * 700;
                for (int i = 0; i < tinks; i++)
                {
                    float g = (float)(0.6 + r.NextDouble() * 0.4);
                    Strike(t, time, f * (0.98 + r.NextDouble() * 0.04), new[] { 1.0, 2.45, 4.1 }, new[] { 1.0, 0.45, 0.2 }, 9, 0.22f * g, 0.5);
                    NoiseBurst(t, time, 0.02, 1200, 1.0, 0.15f * g, r.Next(), 0.0004, 150);
                    time += 0.25 + r.NextDouble() * 0.5;
                }
            }

            /// <summary>A tugboat's air horn down the river: a long blast and a short one, two notes a third apart.</summary>
            public static void TugHorn(Track t, double at)
            {
                double[] start = { 0, 2.4 };
                double[] len = { 1.9, 0.9 };
                for (int b = 0; b < 2; b++)
                {
                    int s = At(at + start[b]), n = At(len[b]);
                    double p1 = 0, p2 = 0;
                    var f = new Svf();
                    for (int i = 0; i < n; i++)
                    {
                        double tt = i / (double)Sr;
                        double bend = 1 - 0.04 * Math.Exp(-tt * 6);
                        p1 += 172 * bend / Sr;
                        p2 += 172 * 1.26 * bend / Sr;
                        double saw = (2 * (p1 - Math.Floor(p1)) - 1) + 0.8 * (2 * (p2 - Math.Floor(p2)) - 1);
                        double env = Math.Min(1, tt / 0.12) * Math.Min(1, (n - i) / (0.25 * Sr));
                        t.Add(s + i, f.Process((float)saw, 750, 0.9) * (float)env * 0.5f);
                    }
                }
            }

            /// <summary>The drawbridge's warning bell as its gates come down to raise the bridge: quick, steady strokes, three a second.</summary>
            public static void BridgeBell(Track t, double at, double seconds)
            {
                for (double time = at; time < at + seconds - 0.9; time += 0.3)
                    Strike(t, time, 1180, new[] { 1.0, 2.0, 2.76, 4.1 }, new[] { 1.0, 0.4, 0.3, 0.15 }, 3.5, 0.3f, 0.9);
            }

            /// <summary>A cruise ship's horn far across the bay, leaving the port: a deep, long chord that swells and dies away.</summary>
            public static void CruiseHorn(Track t, double at)
            {
                int s = At(at), n = At(4.8);
                double p = 0, q = 0;
                var f = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double tt = i / (double)Sr;
                    p += 73.0 / Sr;
                    q += 110.0 / Sr;
                    double saw = (2 * (p - Math.Floor(p)) - 1) + 0.6 * (2 * (q - Math.Floor(q)) - 1);
                    double env = Math.Min(1, tt / 0.5) * Math.Min(1, (n - i) / (0.9 * Sr));
                    t.Add(s + i, f.Process((float)saw, 380, 1.1) * (float)env * 0.5f);
                }
            }

            /// <summary>A brown pelican diving for fish: the rush of its fall, a heavy plunge, the spray and the drops falling back.</summary>
            public static void PelicanDive(Track t, double at, Random r)
            {
                int s = At(at), n = At(0.35);
                var ns = new NoiseSource(r.Next());
                var f = new Svf();
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    f.Process(ns.White(), 500 + 1300 * u, 1.2);
                    t.Add(s + i, f.band * (float)(u * u) * 0.25f);
                }
                double hit = at + 0.35;
                int s2 = At(hit), n2 = At(0.25);
                double ph = 0;
                for (int i = 0; i < n2; i++)
                {
                    double tt = i / (double)Sr;
                    ph += (150 * Math.Exp(-tt * 9) + 55) / Sr;
                    t.Add(s2 + i, (float)(Math.Sin(TwoPi * ph) * Math.Exp(-tt * 14) * Math.Min(1, tt / 0.003)) * 0.7f);
                }
                NoiseBurst(t, hit, 0.9, 1100, 0.5, 0.55f, r.Next(), 0.004, 5);
                for (int i = 0; i < 7; i++)
                    Whistle(t, hit + 0.15 + i * 0.07 + r.NextDouble() * 0.05, 0.035, 800 + r.NextDouble() * 800, 1600 + r.NextDouble() * 900, 0.15f);
            }

            /// <summary>A bicycle's ringing bell: its clapper whirring against the dome, "brrring", once or twice.</summary>
            public static void RingBell(Track t, double at, Random r)
            {
                int rings = 1 + r.Next(2);
                for (int k = 0; k < rings; k++)
                    for (int j = 0; j < 10; j++)
                        Strike(t, at + k * 0.7 + j * 0.045, 2300, new[] { 1.0, 1.52, 2.73 }, new[] { 1.0, 0.5, 0.25 }, 6, 0.18f, 0.6);
            }

            /// <summary>A jogger running by on the path: light, quick steps and a breath out every other one.</summary>
            public static void Jogger(Track t, double at, int steps, Random r)
            {
                for (int i = 0; i < steps; i++)
                {
                    double s = at + i * (0.36 + r.NextDouble() * 0.02);
                    float g = (float)Math.Sin(Math.PI * (i + 0.5) / steps);
                    NoiseBurst(t, s, 0.04, 1800, 1.0, 0.35f * g, r.Next(), 0.0008, 110);
                    NoiseBurst(t, s, 0.07, 200, 1.0, 0.5f * g, r.Next(), 0.002, 60);
                    if (i % 2 == 0) NoiseBurst(t, s + 0.05, 0.18, 1000, 0.7, 0.12f * g, r.Next(), 0.03, 14);
                }
            }

            /// <summary>An impact sprinkler on the lawn: "tch, tch, tch" as it steps round its arc, then the quick
            /// rattle as it swings back.</summary>
            public static void Sprinkler(Track t, double at, double dur, Random r)
            {
                double back = at + dur - 1.1, time = at;
                for (; time < back; time += 0.15 + r.NextDouble() * 0.02)
                {
                    NoiseBurst(t, time, 0.05, 2000 + r.NextDouble() * 300, 1.5, 0.35f, r.Next(), 0.0005, 90);
                    NoiseBurst(t, time + 0.005, 0.12, 3200, 0.7, 0.1f, r.Next(), 0.002, 25);
                }
                for (; time < at + dur; time += 0.04)
                    NoiseBurst(t, time, 0.04, 2100, 1.5, 0.22f, r.Next(), 0.0005, 110);
            }
        }

        static class Machines
        {
            /// <summary>A diesel engine ticking over: a pulse for every firing, a low throb and a rattle.</summary>
            public static void Diesel(Track t, int seed, double hz, double phaseOffset)
            {
                var ns = new NoiseSource(seed);
                var body = new Svf();
                var rattle = new Svf();
                var wander = new Drift(seed + 9, 0.2);
                double ph = phaseOffset;
                Layer(t, i =>
                {
                    double f = hz * (0.97 + 0.06 * wander.Next());
                    ph += f / Sr;
                    double p = ph - Math.Floor(ph);
                    double pulse = Math.Exp(-p * 9) * (0.8 + 0.4 * ns.Value());
                    body.Process((float)pulse, 160, 1.5);
                    rattle.Process((float)(ns.White() * pulse), 1200, 1.0);
                    return body.low * 1.2f + body.band * 0.6f + rattle.band * 0.25f;
                });
            }

            /// <summary>A lorry backing up: the reversing alarm beeping over its engine.</summary>
            public static void Reversing(Track t, double at, int beeps)
            {
                for (int b = 0; b < beeps; b++)
                {
                    int s = At(at + b * 0.9), n = At(0.45);
                    double p = 0;
                    for (int i = 0; i < n; i++)
                    {
                        double tt = i / (double)Sr;
                        p += 1050.0 / Sr;
                        double sq = (p - Math.Floor(p)) < 0.5 ? 1 : -1;
                        double env = Math.Min(1, tt / 0.01) * Math.Min(1, (n - i) / (0.01 * Sr));
                        t.Add(s + i, (float)(sq * 0.25 + Math.Sin(TwoPi * p) * 0.4) * (float)env * 0.6f);
                    }
                }
                Engine(t, at, beeps * 0.9, 34, 34, 0.35f, 4);
            }

            static void Engine(Track t, double at, double dur, double hz0, double hz1, float gain, int seed)
            {
                int s = At(at), n = At(dur);
                var ns = new NoiseSource(seed);
                var f = new Svf();
                double ph = 0;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double hz = hz0 + (hz1 - hz0) * Math.Sin(Math.PI * u);
                    ph += hz / Sr;
                    double p = ph - Math.Floor(ph);
                    double pulse = Math.Exp(-p * 8) * (0.8 + 0.4 * ns.Value());
                    double env = Math.Min(1, u * 10) * Math.Min(1, (1 - u) * 10);
                    t.Add(s + i, f.Process((float)pulse, 300 + hz * 4, 1.2) * (float)env * gain * 2f);
                }
            }

            /// <summary>A jackhammer: a fast hammering of hard knocks on concrete, rattling the steel.</summary>
            public static void Jackhammer(Track t, double at, double dur, Random r)
            {
                double time = at, rate = 21 + r.NextDouble() * 4;
                while (time < at + dur)
                {
                    NoiseBurst(t, time, 0.04, 1800, 0.9, 0.55f, r.Next(), 0.0005, 110);
                    NoiseBurst(t, time, 0.05, 180, 1.2, 0.7f, r.Next(), 0.001, 70);
                    time += 1.0 / rate;
                }
                Strike(t, at, 1900, new[] { 1.0, 1.7, 2.9 }, new[] { 0.6, 0.4, 0.3 }, 6, 0.05f, dur);
            }

            /// <summary>Hammering: a hammer driving a nail into a plank, the last blows ringing the steel.</summary>
            public static void Hammering(Track t, double at, int blows, Random r)
            {
                double time = at;
                for (int i = 0; i < blows; i++)
                {
                    bool metal = i >= blows - 2 || r.NextDouble() < 0.3;
                    NoiseBurst(t, time, 0.08, 900 + r.NextDouble() * 300, 1.4, 0.7f, r.Next(), 0.0006, 55);
                    NoiseBurst(t, time, 0.1, 160, 1.0, 0.5f, r.Next(), 0.001, 40);
                    if (metal) Strike(t, time, 1350 + r.NextDouble() * 200, new[] { 1.0, 2.3, 3.7 }, new[] { 1.0, 0.5, 0.3 }, 7, 0.25f, 0.6);
                    time += 0.42 + r.NextDouble() * 0.15;
                }
            }

            /// <summary>A digger revving up to lift, the hydraulics whining, then settling back to idle.</summary>
            public static void Digger(Track t, double at)
            {
                Engine(t, at, 4.5, 30, 52, 0.55f, 5);
                int s = At(at + 0.8), n = At(2.8);
                double p = 0;
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double f = 520 + 260 * Math.Sin(Math.PI * u * 0.8);
                    p += f / Sr;
                    t.Add(s + i, (float)(Math.Sin(TwoPi * p) * Math.Sin(Math.PI * u) * 0.08));
                }
            }

            /// <summary>A power drill spinning up into the wall and back down.</summary>
            public static void Drill(Track t, double at, Random r)
            {
                int s = At(at), n = At(2.2 + r.NextDouble() * 0.6);
                double p = 0;
                var f = new Svf();
                var ns = new NoiseSource(r.Next());
                for (int i = 0; i < n; i++)
                {
                    double u = i / (double)n;
                    double ramp = Math.Min(1, u * 5) * Math.Min(1, (1 - u) * 4);
                    double hz = 250 + 900 * ramp;
                    p += hz / Sr;
                    double saw = 2 * (p - Math.Floor(p)) - 1;
                    double chatter = 1 - 0.3 * ns.Value() * ramp;
                    t.Add(s + i, f.Process((float)(saw * chatter), 2400, 1.1) * (float)ramp * 0.5f);
                }
            }

            /// <summary>A lorry's air brakes: a sharp hiss of air, then a puff.</summary>
            public static void AirBrake(Track t, double at, Random r)
            {
                NoiseBurst(t, at, 0.9, 4200, 0.6, 0.6f, r.Next(), 0.003, 4, true);
                NoiseBurst(t, at + 0.75, 0.3, 1600, 0.7, 0.3f, r.Next(), 0.005, 12);
            }

            /// <summary>Steel pipes dropped on a pile: a clatter of ringing knocks, bouncing to rest.</summary>
            public static void Pipes(Track t, double at, Random r)
            {
                double time = at, gap = 0.16;
                for (int i = 0; i < 9; i++)
                {
                    double f = 700 + r.NextDouble() * 900;
                    Strike(t, time, f, new[] { 1.0, 2.76, 5.4 }, new[] { 1.0, 0.5, 0.25 }, 5, 0.35f * (float)Math.Pow(0.85, i), 1.2);
                    NoiseBurst(t, time, 0.03, 2000, 1.0, 0.3f * (float)Math.Pow(0.85, i), r.Next(), 0.0005, 120);
                    time += gap * (0.6 + r.NextDouble() * 0.6);
                    gap *= 0.85;
                }
            }

            /// <summary>A tower crane's warning as it swings its load over the street: quick, high beeps, far up.</summary>
            public static void CraneBeeps(Track t, double at, int beeps)
            {
                for (int b = 0; b < beeps; b++)
                {
                    int s = At(at + b * 0.4), n = At(0.2);
                    double p = 0;
                    for (int i = 0; i < n; i++)
                    {
                        double tt = i / (double)Sr;
                        p += 1450.0 / Sr;
                        double sq = (p - Math.Floor(p)) < 0.5 ? 1 : -1;
                        double env = Math.Min(1, tt / 0.008) * Math.Min(1, (n - i) / (0.008 * Sr));
                        t.Add(s + i, (float)(sq * 0.15 + Math.Sin(TwoPi * p) * 0.5) * (float)env * 0.6f);
                    }
                }
            }
        }
    }
}
